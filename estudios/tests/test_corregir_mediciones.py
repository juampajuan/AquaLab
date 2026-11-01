from decimal import Decimal
from unittest import mock

import pytest
from django.contrib.messages import get_messages
from django.db import DatabaseError
from django.test import Client
from django.urls import reverse
from django.utils import timezone

from estudios.models import EstadoEstudio, Estudio, Medicion
from estudios.tests.utiles import asignacion_de, cargar

pytestmark = pytest.mark.django_db

INFORME_EMITIDO = (
    "El estudio ya tiene el informe emitido: sus mediciones y resultados no se pueden cambiar."
)


def url_detalle(estudio):
    return reverse("estudios:detalle", args=[estudio.pk])


def url_corregir(estudio):
    return reverse("estudios:corregir_mediciones", args=[estudio.pk])


def mensajes(respuesta):
    return [str(m) for m in get_messages(respuesta.wsgi_request)]


def medicion(estudio, codigo):
    return Medicion.objects.get(asignacion=asignacion_de(estudio, codigo))


def envio(accion, estudio, borrar=(), **por_codigo):
    """Todas las filas con su valor vigente; las indicadas con el texto dado y las de `borrar`
    marcadas para borrar."""
    datos = {"accion": accion}
    for m in Medicion.objects.filter(asignacion__estudio=estudio).select_related("asignacion"):
        codigo = m.asignacion.prueba.codigo
        datos[f"original_{m.asignacion_id}"] = str(m.valor_ingresado)
        datos[f"medicion_{m.asignacion_id}"] = por_codigo.get(
            codigo.replace("-", "_"), str(m.valor_ingresado).replace(".", ",")
        )
        if codigo in borrar:
            datos[f"borrar_{m.asignacion_id}"] = "on"
    return datos


@pytest.fixture
def estudio_cargado(estudio_de, empleado):
    estudio = estudio_de("CL-", "PH")
    cargar(estudio, empleado, CL_="2.35", PH="7.20")
    return estudio


def test_detalle_ofrece_corregir(cliente_http, estudio_cargado):
    html = cliente_http.get(url_detalle(estudio_cargado)).content.decode()
    assert f'href="{url_corregir(estudio_cargado)}"' in html


@pytest.mark.parametrize("caso", ["sin_mediciones", "informe_emitido"])
def test_detalle_no_ofrece_corregir(cliente_http, estudio_de, empleado, caso):
    estudio = estudio_de("CL-")
    if caso == "informe_emitido":
        cargar(estudio, empleado, CL_="2.35")
        Estudio.objects.filter(pk=estudio.pk).update(estado=EstadoEstudio.INFORME_GENERADO)
    html = cliente_http.get(url_detalle(estudio)).content.decode()
    assert f'href="{url_corregir(estudio)}"' not in html


def test_formulario_precargado(cliente_http, estudio_cargado):
    respuesta = cliente_http.get(url_corregir(estudio_cargado))
    assert respuesta.status_code == 200
    html = respuesta.content.decode()
    cl, ph = (asignacion_de(estudio_cargado, c) for c in ("CL-", "PH"))
    assert f'name="medicion_{cl.pk}" value="2,35"' in html
    assert f'name="medicion_{ph.pk}" value="7,20"' in html
    assert f'name="original_{cl.pk}" value="2.35"' in html
    assert f'name="original_{ph.pk}" value="7.20"' in html
    assert "ml" in html and "UpH" in html
    assert "Test" in html
    fecha = timezone.localtime(medicion(estudio_cargado, "CL-").fecha_carga)
    assert fecha.strftime("%d/%m/%Y %H:%M") in html


def test_revisar_muestra_solo_cambios(cliente_http, estudio_cargado):
    respuesta = cliente_http.post(
        url_corregir(estudio_cargado), envio("revisar", estudio_cargado, CL_="2,53")
    )
    assert respuesta.status_code == 200
    assert "estudios/corregir_mediciones_confirmar.html" in [t.name for t in respuesta.templates]
    html = respuesta.content.decode()
    assert (
        f"Se corregirá 1 medición en el estudio {estudio_cargado.pk} (muestra PI 200001)." in html
    )
    tabla = html.split("<tbody>")[1].split("</tbody>")[0]
    assert "2,35" in tabla and "2,53" in tabla
    assert "PH" not in tabla
    assert f'href="{url_detalle(estudio_cargado)}"' in html
    assert medicion(estudio_cargado, "CL-").valor == Decimal("2.35")


def test_editar_conserva_valores(cliente_http, estudio_cargado):
    respuesta = cliente_http.post(
        url_corregir(estudio_cargado), envio("editar", estudio_cargado, CL_="2,53")
    )
    assert "estudios/corregir_mediciones.html" in [t.name for t in respuesta.templates]
    assert 'value="2,53"' in respuesta.content.decode()


def test_confirmar_corrige_y_recalcula(cliente_http, estudio_cargado):
    respuesta = cliente_http.post(
        url_corregir(estudio_cargado), envio("confirmar", estudio_cargado, CL_="2,53")
    )
    assert respuesta.status_code == 302
    assert respuesta.url == url_detalle(estudio_cargado)
    assert mensajes(respuesta) == [f"Se corrigió 1 medición del estudio {estudio_cargado.pk}: CL-."]
    html = cliente_http.get(url_detalle(estudio_cargado)).content.decode()
    assert "2,53 ml" in html
    assert "25,3 mg/l" in html
    assert "Corregida por" in html


def test_otro_empleado_puede_corregir(estudio_cargado, django_user_model):
    otro = django_user_model.objects.create_user(
        email="otro-vista@ejemplo.com", password="Clave-Valida-123", is_active=True
    )
    cliente = Client()
    cliente.force_login(otro)
    cliente.post(url_corregir(estudio_cargado), envio("confirmar", estudio_cargado, CL_="2,53"))
    assert medicion(estudio_cargado, "CL-").corregida_por == otro


def test_vista_informe_emitido_rechaza(cliente_http, estudio_cargado):
    Estudio.objects.filter(pk=estudio_cargado.pk).update(estado=EstadoEstudio.INFORME_GENERADO)
    for pedir in (
        lambda: cliente_http.get(url_corregir(estudio_cargado)),
        lambda: cliente_http.post(
            url_corregir(estudio_cargado), envio("revisar", estudio_cargado, CL_="2,53")
        ),
    ):
        respuesta = pedir()
        assert respuesta.status_code == 302
        assert respuesta.url == url_detalle(estudio_cargado)
        assert INFORME_EMITIDO in mensajes(respuesta)


def test_corregir_requiere_sesion(estudio_cargado):
    cliente = Client()
    for respuesta in (
        cliente.get(url_corregir(estudio_cargado)),
        cliente.post(url_corregir(estudio_cargado), envio("confirmar", estudio_cargado, CL_="3")),
    ):
        assert respuesta.status_code == 302
        assert respuesta.url.startswith(reverse("usuarios:login"))
    assert medicion(estudio_cargado, "CL-").valor == Decimal("2.35")


def test_corregir_estudio_inexistente_404(cliente_http):
    url = reverse("estudios:corregir_mediciones", args=[999999])
    assert cliente_http.get(url).status_code == 404
    assert cliente_http.post(url, {"accion": "revisar"}).status_code == 404


def test_sin_mediciones_estado_vacio(cliente_http, estudio_de):
    estudio = estudio_de("CL-")
    html = cliente_http.get(url_corregir(estudio)).content.decode()
    assert "Este estudio no tiene mediciones para corregir." in html


def test_reenvio_informa_ya_tenia_ese_valor(cliente_http, estudio_cargado):
    datos = envio("confirmar", estudio_cargado, CL_="2,53")
    cliente_http.post(url_corregir(estudio_cargado), datos, follow=True)
    fecha = medicion(estudio_cargado, "CL-").fecha_correccion
    respuesta = cliente_http.post(url_corregir(estudio_cargado), datos)
    assert mensajes(respuesta) == ["CL-: ya tenía ese valor."]
    assert medicion(estudio_cargado, "CL-").fecha_correccion == fecha


@pytest.mark.parametrize(
    "ajeno,mensaje",
    [("2.60", "CL-: cambió mientras se editaba."), ("2.53", "CL-: ya tenía ese valor.")],
)
def test_confirmar_con_cambio_ajeno_se_informa(cliente_http, estudio_cargado, ajeno, mensaje):
    datos = envio("confirmar", estudio_cargado, CL_="2,53")
    Medicion.objects.filter(pk=medicion(estudio_cargado, "CL-").pk).update(valor=Decimal(ajeno))
    respuesta = cliente_http.post(url_corregir(estudio_cargado), datos)
    assert respuesta.status_code == 302
    assert mensajes(respuesta) == [mensaje]
    assert medicion(estudio_cargado, "CL-").valor == Decimal(ajeno)


def test_error_de_base_al_corregir(cliente_http, estudio_cargado):
    with mock.patch("estudios.servicios.corregir_mediciones", side_effect=DatabaseError):
        respuesta = cliente_http.post(
            url_corregir(estudio_cargado), envio("confirmar", estudio_cargado, CL_="2,53")
        )
    assert respuesta.status_code == 302
    assert mensajes(respuesta) == ["No se pudieron guardar las correcciones. Intentá nuevamente."]
    assert medicion(estudio_cargado, "CL-").valor == Decimal("2.35")


FORMATO_INVALIDO = "Ingresá un número válido (usá coma o punto para los decimales)."


def bloque_error(html, estudio, codigo):
    pk = asignacion_de(estudio, codigo).pk
    return html.split(f'id="id_medicion_{pk}_error"')[1].split("</div></div>")[0]


def test_revisar_con_valor_invalido_no_guarda(cliente_http, estudio_cargado):
    respuesta = cliente_http.post(
        url_corregir(estudio_cargado),
        envio("revisar", estudio_cargado, CL_="abc", PH="0,1234567"),
    )
    assert respuesta.status_code == 200
    html = respuesta.content.decode()
    assert FORMATO_INVALIDO in bloque_error(html, estudio_cargado, "CL-")
    assert "Ingresá como máximo 6 decimales." in bloque_error(html, estudio_cargado, "PH")
    assert 'value="abc"' in html and 'value="0,1234567"' in html
    assert medicion(estudio_cargado, "CL-").valor == Decimal("2.35")


def test_confirmar_con_valor_invalido_no_guarda(cliente_http, estudio_cargado):
    with mock.patch("estudios.servicios.corregir_mediciones") as servicio:
        respuesta = cliente_http.post(
            url_corregir(estudio_cargado), envio("confirmar", estudio_cargado, CL_="abc")
        )
    assert respuesta.status_code == 200
    servicio.assert_not_called()


@pytest.mark.parametrize("texto", ["", "   "])
def test_campo_vacio_rechazado(cliente_http, estudio_cargado, texto):
    respuesta = cliente_http.post(
        url_corregir(estudio_cargado), envio("revisar", estudio_cargado, CL_=texto)
    )
    html = respuesta.content.decode()
    assert "La medición no puede quedar vacía." in bloque_error(html, estudio_cargado, "CL-")
    assert medicion(estudio_cargado, "CL-").valor == Decimal("2.35")


def test_sin_cambios(cliente_http, estudio_cargado):
    respuesta = cliente_http.post(url_corregir(estudio_cargado), envio("revisar", estudio_cargado))
    assert respuesta.status_code == 200
    assert "No hay cambios para guardar." in respuesta.content.decode()


def test_cambio_de_decimales_es_cambio(cliente_http, estudio_cargado):
    respuesta = cliente_http.post(
        url_corregir(estudio_cargado), envio("revisar", estudio_cargado, PH="7,2")
    )
    tabla = respuesta.content.decode().split("<tbody>")[1].split("</tbody>")[0]
    assert "PH" in tabla and "7,20" in tabla and "7,2" in tabla
    cliente_http.post(url_corregir(estudio_cargado), envio("confirmar", estudio_cargado, PH="7,2"))
    assert medicion(estudio_cargado, "PH").decimales == 1


def test_revisar_avisa_perdida_de_validacion(cliente_http, estudio_de, empleado):
    from estudios.models import EstadoPruebaEstudio, PruebaEstudio

    estudio = estudio_de("CA", "DUREZA-T", "MG")
    cargar(estudio, empleado, CA="80", DUREZA_T="15")
    html = cliente_http.post(
        url_corregir(estudio), envio("revisar", estudio, CA="40")
    ).content.decode()
    assert "Perderán la validación" not in html
    PruebaEstudio.objects.filter(estudio=estudio, prueba__codigo__in=["CA", "MG"]).update(
        estado=EstadoPruebaEstudio.COMPLETADA
    )
    html = cliente_http.post(
        url_corregir(estudio), envio("revisar", estudio, CA="40")
    ).content.decode()
    assert "Perderán la validación: CA · Calcio (Ca), MG · Magnesio (Mg)." in html


def test_correccion_a_division_por_cero_advierte(
    cliente_http, estudio_de, empleado, pruebas_division
):
    estudio = estudio_de("DIV-A", "DIV-B", "DIV")
    cargar(estudio, empleado, DIV_A="6", DIV_B="2")
    respuesta = cliente_http.post(url_corregir(estudio), envio("confirmar", estudio, DIV_B="0"))
    assert "DIV: no se pudo calcular el resultado (división por cero)." in mensajes(respuesta)
    html = cliente_http.get(url_detalle(estudio)).content.decode()
    assert "No se pudo calcular: división por cero." in html


def test_formulario_ofrece_borrar(cliente_http, estudio_cargado):
    html = cliente_http.get(url_corregir(estudio_cargado)).content.decode()
    for codigo in ("CL-", "PH"):
        pk = asignacion_de(estudio_cargado, codigo).pk
        assert f'type="checkbox" name="borrar_{pk}"' in html
        assert f'for="id_borrar_{pk}"' in html
    assert "Para quitar una medición cargada por error, marcá Borrar." in html


def test_revisar_muestra_borrado(cliente_http, estudio_cargado):
    respuesta = cliente_http.post(
        url_corregir(estudio_cargado), envio("revisar", estudio_cargado, borrar=("CL-",))
    )
    html = respuesta.content.decode()
    assert f"Se aplicará 1 cambio en el estudio {estudio_cargado.pk} (muestra PI 200001)." in html
    tabla = html.split("<tbody>")[1].split("</tbody>")[0]
    assert "2,35" in tabla
    # El valor nuevo de un borrado se ve como «—», igual que una prueba sin medición; el texto
    # «se borra» queda para lectores de pantalla.
    assert '<span aria-hidden="true">—</span><span class="sr-only">se borra</span>' in tabla
    pk = asignacion_de(estudio_cargado, "CL-").pk
    assert f'name="borrar_{pk}"' in html
    assert medicion(estudio_cargado, "CL-").valor == Decimal("2.35")


def test_confirmar_borra_y_vuelve_a_ofrecerse(cliente_http, estudio_cargado):
    respuesta = cliente_http.post(
        url_corregir(estudio_cargado), envio("confirmar", estudio_cargado, borrar=("CL-",))
    )
    assert respuesta.status_code == 302
    assert mensajes(respuesta) == [f"Se borró 1 medición del estudio {estudio_cargado.pk}: CL-."]
    pk = asignacion_de(estudio_cargado, "CL-").pk
    html = cliente_http.get(
        reverse("estudios:cargar_mediciones", args=[estudio_cargado.pk])
    ).content.decode()
    assert f'name="medicion_{pk}"' in html


@pytest.mark.parametrize("texto", ["", "abc", "9", "1" * 50])
def test_borrado_prevalece_sobre_el_valor(cliente_http, estudio_cargado, texto):
    respuesta = cliente_http.post(
        url_corregir(estudio_cargado),
        envio("revisar", estudio_cargado, borrar=("CL-",), CL_=texto),
    )
    assert "estudios/corregir_mediciones_confirmar.html" in [t.name for t in respuesta.templates]
    assert "se borra" in respuesta.content.decode()


def test_solo_borrados_no_es_sin_cambios(cliente_http, estudio_cargado):
    respuesta = cliente_http.post(
        url_corregir(estudio_cargado), envio("revisar", estudio_cargado, borrar=("CL-",))
    )
    assert "No hay cambios para guardar." not in respuesta.content.decode()


def test_mensajes_borrado_y_correccion(cliente_http, estudio_cargado):
    respuesta = cliente_http.post(
        url_corregir(estudio_cargado),
        envio("confirmar", estudio_cargado, borrar=("CL-",), PH="7,30"),
    )
    assert mensajes(respuesta) == [
        f"Se corrigió 1 medición del estudio {estudio_cargado.pk}: PH.",
        f"Se borró 1 medición del estudio {estudio_cargado.pk}: CL-.",
    ]


def test_otro_empleado_puede_borrar(estudio_cargado, django_user_model):
    otro = django_user_model.objects.create_user(
        email="otro-borrado@ejemplo.com", password="Clave-Valida-123", is_active=True
    )
    cliente = Client()
    cliente.force_login(otro)
    cliente.post(
        url_corregir(estudio_cargado), envio("confirmar", estudio_cargado, borrar=("CL-",))
    )
    assert not Medicion.objects.filter(asignacion=asignacion_de(estudio_cargado, "CL-")).exists()


def test_reenvio_de_borrado(cliente_http, estudio_cargado):
    datos = envio("confirmar", estudio_cargado, borrar=("CL-",))
    cliente_http.post(url_corregir(estudio_cargado), datos, follow=True)
    respuesta = cliente_http.post(url_corregir(estudio_cargado), datos)
    assert respuesta.status_code == 302
    assert mensajes(respuesta) == ["CL-: ya no tenía medición."]


def test_revisar_avisa_validacion_por_borrado(cliente_http, estudio_de, empleado):
    from estudios.models import EstadoPruebaEstudio, PruebaEstudio

    estudio = estudio_de("CA", "DUREZA-T", "MG")
    cargar(estudio, empleado, CA="80", DUREZA_T="15")
    PruebaEstudio.objects.filter(estudio=estudio, prueba__codigo__in=["CA", "MG"]).update(
        estado=EstadoPruebaEstudio.COMPLETADA
    )
    html = cliente_http.post(
        url_corregir(estudio), envio("revisar", estudio, borrar=("CA",))
    ).content.decode()
    assert "Perderán la validación: CA · Calcio (Ca), MG · Magnesio (Mg)." in html


def test_detalle_tras_borrar_todo(cliente_http, estudio_de, empleado):
    estudio = estudio_de("CA", "DUREZA-T", "MG")
    cargar(estudio, empleado, CA="80", DUREZA_T="15")
    cliente_http.post(url_corregir(estudio), envio("confirmar", estudio, borrar=("CA", "DUREZA-T")))
    html = cliente_http.get(url_detalle(estudio)).content.decode()
    assert reverse("estudios:agregar_prueba", args=[estudio.pk]) in html
    assert "/quitar/" in html
    assert f'href="{url_corregir(estudio)}"' not in html
    assert "Faltan resultados de:" in html or "Falta la medición." in html
