from decimal import Decimal
from unittest import mock

import pytest
from django.contrib.messages import get_messages
from django.db import DatabaseError
from django.urls import reverse
from django.utils import timezone

from estudios.models import EstadoEstudio, Estudio, Medicion

pytestmark = pytest.mark.django_db


def url_detalle(estudio):
    return reverse("estudios:detalle", args=[estudio.pk])


def url_cargar(estudio):
    return reverse("estudios:cargar_mediciones", args=[estudio.pk])


def mensajes(respuesta):
    return [str(m) for m in get_messages(respuesta.wsgi_request)]


def campo(asignacion):
    return f"medicion_{asignacion.pk}"


def envio(accion, asignaciones, **por_codigo):
    datos = {"accion": accion}
    for codigo, texto in por_codigo.items():
        datos[campo(asignaciones[codigo.replace("_", "-")])] = texto
    return datos


def test_detalle_ofrece_cargar_mediciones(cliente_http, estudio_mediciones):
    respuesta = cliente_http.get(url_detalle(estudio_mediciones))
    assert f'href="{url_cargar(estudio_mediciones)}"' in respuesta.content.decode()


def test_formulario_lista_pendientes_con_unidad(
    cliente_http, estudio_mediciones, asignaciones_medicion
):
    respuesta = cliente_http.get(url_cargar(estudio_mediciones))
    assert respuesta.status_code == 200
    html = respuesta.content.decode()
    posiciones = [
        html.index(f'name="{campo(asignaciones_medicion[c])}"')
        for c in ("TEST-PH", "TEST-SIN", "TEST-VOL")
    ]
    assert posiciones == sorted(posiciones)
    assert html.count('inputmode="decimal"') == 3
    for texto in ("UpH", "mL", "Sin unidad"):
        assert texto in html
    assert f'name="{campo(asignaciones_medicion["TEST-CALC"])}"' not in html


def test_revisar_muestra_resumen_sin_guardar(
    cliente_http, estudio_mediciones, asignaciones_medicion
):
    respuesta = cliente_http.post(
        url_cargar(estudio_mediciones),
        envio("revisar", asignaciones_medicion, TEST_PH="7,20", TEST_VOL="", TEST_SIN=""),
    )
    assert respuesta.status_code == 200
    assert "estudios/cargar_mediciones_confirmar.html" in [t.name for t in respuesta.templates]
    html = respuesta.content.decode()
    assert (
        f"Se guardará 1 medición en el estudio {estudio_mediciones.pk} (muestra PI 200001)." in html
    )
    assert "TEST-PH" in html and "UpH" in html
    assert f'name="{campo(asignaciones_medicion["TEST-PH"])}" value="7,20"' in html
    assert f'name="{campo(asignaciones_medicion["TEST-VOL"])}"' not in html
    assert f'href="{url_detalle(estudio_mediciones)}"' in html
    assert not Medicion.objects.exists()


def test_editar_conserva_valores(cliente_http, estudio_mediciones, asignaciones_medicion):
    respuesta = cliente_http.post(
        url_cargar(estudio_mediciones), envio("editar", asignaciones_medicion, TEST_PH="7,20")
    )
    assert respuesta.status_code == 200
    assert "estudios/cargar_mediciones.html" in [t.name for t in respuesta.templates]
    assert 'value="7,20"' in respuesta.content.decode()
    assert not Medicion.objects.exists()


def test_confirmar_guarda_mediciones(cliente_http, estudio_mediciones, asignaciones_medicion):
    respuesta = cliente_http.post(
        url_cargar(estudio_mediciones),
        envio("confirmar", asignaciones_medicion, TEST_PH="7,20", TEST_VOL="18.5", TEST_SIN=""),
    )
    assert respuesta.status_code == 302
    assert respuesta.url == url_detalle(estudio_mediciones)
    assert mensajes(respuesta) == [
        f"Se guardaron 2 mediciones del estudio {estudio_mediciones.pk}: TEST-PH, TEST-VOL."
    ]
    assert Medicion.objects.count() == 2
    estudio_mediciones.refresh_from_db()
    assert estudio_mediciones.estado == EstadoEstudio.EN_PROCESO


def test_confirmar_una_medicion_usa_singular(
    cliente_http, estudio_mediciones, asignaciones_medicion
):
    respuesta = cliente_http.post(
        url_cargar(estudio_mediciones), envio("confirmar", asignaciones_medicion, TEST_PH="7")
    )
    assert mensajes(respuesta) == [
        f"Se guardó 1 medición del estudio {estudio_mediciones.pk}: TEST-PH."
    ]


def test_formulario_no_ofrece_cargadas(cliente_http, estudio_mediciones, asignaciones_medicion):
    cliente_http.post(
        url_cargar(estudio_mediciones), envio("confirmar", asignaciones_medicion, TEST_PH="7")
    )
    html = cliente_http.get(url_cargar(estudio_mediciones)).content.decode()
    assert f'name="{campo(asignaciones_medicion["TEST-PH"])}"' not in html
    for codigo in ("TEST-VOL", "TEST-SIN"):
        assert f'name="{campo(asignaciones_medicion[codigo])}"' in html


def test_detalle_muestra_medicion(cliente_http, estudio_mediciones, asignaciones_medicion):
    cliente_http.post(
        url_cargar(estudio_mediciones), envio("confirmar", asignaciones_medicion, TEST_PH="7,20")
    )
    medicion = Medicion.objects.get()
    html = cliente_http.get(url_detalle(estudio_mediciones)).content.decode()
    assert "7,20 UpH" in html
    assert "Test" in html
    assert timezone.localtime(medicion.fecha_carga).strftime("%d/%m/%Y %H:%M") in html
    assert "Se calcula" in html
    assert "—" in html


def test_estudio_en_proceso_no_ofrece_agregar_ni_quitar(
    cliente_http, estudio_mediciones, asignaciones_medicion
):
    cliente_http.post(
        url_cargar(estudio_mediciones), envio("confirmar", asignaciones_medicion, TEST_PH="7")
    )
    html = cliente_http.get(url_detalle(estudio_mediciones)).content.decode()
    assert reverse("estudios:agregar_prueba", args=[estudio_mediciones.pk]) not in html
    assert "/quitar/" not in html
    assert f'href="{url_cargar(estudio_mediciones)}"' in html


@pytest.mark.parametrize("estado", [EstadoEstudio.FINALIZADO, EstadoEstudio.INFORME_GENERADO])
def test_estudio_cerrado_rechaza_carga(
    cliente_http, estudio_mediciones, asignaciones_medicion, estado
):
    Estudio.objects.filter(pk=estudio_mediciones.pk).update(estado=estado)
    for pedir in (
        lambda: cliente_http.get(url_cargar(estudio_mediciones)),
        lambda: cliente_http.post(
            url_cargar(estudio_mediciones), envio("revisar", asignaciones_medicion, TEST_PH="7")
        ),
    ):
        respuesta = pedir()
        assert respuesta.status_code == 302
        assert respuesta.url == url_detalle(estudio_mediciones)
        assert set(mensajes(respuesta)) == {"Este estudio ya no admite carga de mediciones."}
    assert not Medicion.objects.exists()


def test_error_de_base_al_cargar_no_guarda(cliente_http, estudio_mediciones, asignaciones_medicion):
    with mock.patch("estudios.servicios.cargar_mediciones", side_effect=DatabaseError):
        respuesta = cliente_http.post(
            url_cargar(estudio_mediciones), envio("confirmar", asignaciones_medicion, TEST_PH="7")
        )
    assert respuesta.status_code == 302
    assert respuesta.url == url_detalle(estudio_mediciones)
    assert mensajes(respuesta) == ["No se pudieron guardar las mediciones. Intentá nuevamente."]
    assert not Medicion.objects.exists()


FORMATO_INVALIDO = "Ingresá un número válido (usá coma o punto para los decimales)."


def test_revisar_con_valor_invalido_no_guarda(
    cliente_http, estudio_mediciones, asignaciones_medicion
):
    respuesta = cliente_http.post(
        url_cargar(estudio_mediciones),
        envio("revisar", asignaciones_medicion, TEST_PH="7,25", TEST_VOL="abc", TEST_SIN="1.234,5"),
    )
    assert respuesta.status_code == 200
    assert "estudios/cargar_mediciones.html" in [t.name for t in respuesta.templates]
    html = respuesta.content.decode()
    for codigo in ("TEST-VOL", "TEST-SIN"):
        nombre = campo(asignaciones_medicion[codigo])
        bloque = html.split(f'id="id_{nombre}_error"')[1].split("</div></div>")[0]
        assert FORMATO_INVALIDO in bloque
        assert f'aria-describedby="id_{nombre}_error"' in html
    assert html.count("is-invalid") == 2
    assert f'name="{campo(asignaciones_medicion["TEST-PH"])}" value="7,25"' in html
    assert not Medicion.objects.exists()


def test_confirmar_con_valor_invalido_no_guarda(
    cliente_http, estudio_mediciones, asignaciones_medicion
):
    with mock.patch("estudios.servicios.cargar_mediciones") as servicio:
        respuesta = cliente_http.post(
            url_cargar(estudio_mediciones),
            envio("confirmar", asignaciones_medicion, TEST_PH="7,25", TEST_VOL="abc"),
        )
    assert respuesta.status_code == 200
    assert FORMATO_INVALIDO in respuesta.content.decode()
    servicio.assert_not_called()
    assert not Medicion.objects.exists()


@pytest.mark.parametrize("texto", ["", "   "])
def test_revisar_sin_valores_pide_al_menos_uno(
    cliente_http, estudio_mediciones, asignaciones_medicion, texto
):
    respuesta = cliente_http.post(
        url_cargar(estudio_mediciones),
        envio("revisar", asignaciones_medicion, TEST_PH=texto, TEST_VOL=texto, TEST_SIN=texto),
    )
    assert respuesta.status_code == 200
    assert "Ingresá al menos una medición." in respuesta.content.decode()
    assert not Medicion.objects.exists()


def test_valor_con_espacios_y_decimales_se_guarda_como_se_escribio(
    cliente_http, estudio_mediciones, asignaciones_medicion
):
    cliente_http.post(
        url_cargar(estudio_mediciones),
        envio("confirmar", asignaciones_medicion, TEST_VOL=" 0,4180 "),
    )
    medicion = Medicion.objects.get()
    assert medicion.valor_ingresado == Decimal("0.4180")
    assert medicion.valor_ingresado.as_tuple().exponent == -4
    assert "0,4180 mL" in cliente_http.get(url_detalle(estudio_mediciones)).content.decode()


def test_cargar_mediciones_requiere_sesion(estudio_mediciones, asignaciones_medicion):
    from django.test import Client

    cliente = Client()
    for respuesta in (
        cliente.get(url_cargar(estudio_mediciones)),
        cliente.post(
            url_cargar(estudio_mediciones), envio("confirmar", asignaciones_medicion, TEST_PH="7")
        ),
    ):
        assert respuesta.status_code == 302
        assert respuesta.url.startswith(reverse("usuarios:login"))
    assert not Medicion.objects.exists()


def test_cargar_mediciones_estudio_inexistente_404(cliente_http):
    url = reverse("estudios:cargar_mediciones", args=[999999])
    assert cliente_http.get(url).status_code == 404
    assert cliente_http.post(url, {"accion": "revisar"}).status_code == 404


def test_formulario_muestra_calculadas_sin_campo(
    cliente_http, estudio_mediciones, asignaciones_medicion
):
    html = cliente_http.get(url_cargar(estudio_mediciones)).content.decode()
    assert "Se calculan a partir de otras pruebas" in html
    assert "Calculada de test" in html
    assert f'name="{campo(asignaciones_medicion["TEST-CALC"])}"' not in html


def test_formulario_sin_pruebas_para_medir(cliente_http, estudio_mediciones, asignaciones_medicion):
    cliente_http.post(
        url_cargar(estudio_mediciones),
        envio("confirmar", asignaciones_medicion, TEST_PH="1", TEST_VOL="2", TEST_SIN="3"),
        follow=True,
    )
    html = cliente_http.get(url_cargar(estudio_mediciones)).content.decode()
    assert "No hay mediciones para cargar en este estudio." in html
    assert "Revisar mediciones" not in html
    detalle = cliente_http.get(url_detalle(estudio_mediciones)).content.decode()
    assert f'href="{url_cargar(estudio_mediciones)}"' not in detalle


@pytest.mark.parametrize("caso", ["finalizado", "informe_generado", "solo_calculadas"])
def test_detalle_no_ofrece_cargar_mediciones(
    cliente_http, estudio_mediciones, asignaciones_medicion, caso
):
    from estudios.models import EstadoPruebaEstudio, PruebaEstudio

    if caso == "solo_calculadas":
        PruebaEstudio.objects.filter(estudio=estudio_mediciones, prueba__es_calculada=False).update(
            estado=EstadoPruebaEstudio.CARGADA
        )
    else:
        Estudio.objects.filter(pk=estudio_mediciones.pk).update(estado=caso)
    html = cliente_http.get(url_detalle(estudio_mediciones)).content.decode()
    assert f'href="{url_cargar(estudio_mediciones)}"' not in html


def test_reenvio_informa_ya_cargada(cliente_http, estudio_mediciones, asignaciones_medicion):
    datos = envio("confirmar", asignaciones_medicion, TEST_PH="7,20")
    cliente_http.post(url_cargar(estudio_mediciones), datos, follow=True)
    respuesta = cliente_http.post(url_cargar(estudio_mediciones), datos)
    assert respuesta.status_code == 302
    assert mensajes(respuesta) == ["TEST-PH: ya tenía una medición cargada."]
    medicion = Medicion.objects.get()
    assert medicion.valor_ingresado == Decimal("7.20")


def test_confirmar_prueba_quitada_se_informa(
    cliente_http, estudio_mediciones, asignaciones_medicion, empleado
):
    from estudios.servicios import quitar_prueba

    sin = asignaciones_medicion["TEST-SIN"]
    quitar_prueba(estudio_mediciones.pk, sin.pk, empleado)
    respuesta = cliente_http.post(
        url_cargar(estudio_mediciones),
        envio("confirmar", asignaciones_medicion, TEST_PH="7", TEST_SIN="3"),
    )
    assert respuesta.status_code == 302
    assert mensajes(respuesta) == [
        f"Se guardó 1 medición del estudio {estudio_mediciones.pk}: TEST-PH.",
        "1 prueba(s) ya no forman parte del estudio; su medición no se guardó.",
    ]
    assert [m.asignacion.prueba.codigo for m in Medicion.objects.all()] == ["TEST-PH"]
