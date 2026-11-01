from unittest import mock

import pytest
from django.contrib.messages import get_messages
from django.db import DatabaseError
from django.urls import reverse

from estudios.models import EstadoEstudio, EstadoPruebaEstudio, Estudio, Validacion
from estudios.tests.utiles import asignacion_de, cargar, validar

pytestmark = pytest.mark.django_db


def url_detalle(estudio):
    return reverse("estudios:detalle", args=[estudio.pk])


def url_validar(estudio):
    return reverse("estudios:validar_resultados", args=[estudio.pk])


def mensajes(respuesta):
    return [str(m) for m in get_messages(respuesta.wsgi_request)]


def envio(accion, estudio, *codigos, vistos=None):
    """Las pruebas dadas marcadas, con el valor de su resultado (o el de `vistos`)."""
    vistos = vistos or {}
    datos = {"accion": accion}
    for codigo in codigos:
        asignacion = asignacion_de(estudio, codigo)
        datos[f"validar_{asignacion.pk}"] = "on"
        datos[f"resultado_{asignacion.pk}"] = vistos.get(codigo, str(asignacion.resultado.valor))
    return datos


@pytest.fixture
def estudio_mixto(estudio_de, empleado):
    """pH cumple, Cloruro fuera de norma, E. coli Ausente cumple y Olor sin límite comparable."""
    estudio = estudio_de("PH", "CL-", "ECOLI", "OLOR")
    cargar(estudio, empleado, PH="7.4", CL_="40", ECOLI="0", OLOR="2")  # Cloruro x*10 → 400
    return estudio


def casilla(html, asignacion):
    inicio = html.index(f'name="validar_{asignacion.pk}"')
    etiqueta = html[html.rindex("<input", 0, inicio) : html.index(">", inicio)]
    return "checked" in etiqueta


def test_detalle_ofrece_validar(cliente_bioquimico, estudio_mixto):
    html = cliente_bioquimico.get(url_detalle(estudio_mixto)).content.decode()
    assert f'href="{url_validar(estudio_mixto)}"' in html


@pytest.mark.parametrize("caso", ["sin_resultados", "informe_emitido", "todo_validado"])
def test_detalle_no_ofrece_validar(cliente_bioquimico, estudio_de, empleado, bioquimico, caso):
    estudio = estudio_de("PH")
    if caso != "sin_resultados":
        cargar(estudio, empleado, PH="7.4")
    if caso == "informe_emitido":
        Estudio.objects.filter(pk=estudio.pk).update(estado=EstadoEstudio.INFORME_GENERADO)
    if caso == "todo_validado":
        validar(estudio, bioquimico, "PH")
    html = cliente_bioquimico.get(url_detalle(estudio)).content.decode()
    assert f'href="{url_validar(estudio)}"' not in html


def test_formulario_lista_y_marca_las_que_cumplen(cliente_bioquimico, estudio_mixto):
    respuesta = cliente_bioquimico.get(url_validar(estudio_mixto))
    assert respuesta.status_code == 200
    html = respuesta.content.decode()
    marcadas = {
        c: casilla(html, asignacion_de(estudio_mixto, c)) for c in ("PH", "CL-", "ECOLI", "OLOR")
    }
    assert marcadas == {"PH": True, "CL-": False, "ECOLI": True, "OLOR": False}
    ph = asignacion_de(estudio_mixto, "PH")
    assert f'name="resultado_{ph.pk}" value="{ph.resultado.valor}"' in html
    assert "Hay 1 resultado fuera de norma: revisalo antes de marcarlo." in html
    for texto in ("Cumple", "Fuera de norma", "Sin límite comparable", "6.4 a 8.5", "máx. SOE"):
        assert texto in html


def test_sin_resultados_estado_vacio(cliente_bioquimico, estudio_de):
    estudio = estudio_de("PH")
    html = cliente_bioquimico.get(url_validar(estudio)).content.decode()
    assert "No hay resultados para validar en este estudio." in html


def test_marcar_todas(cliente_bioquimico, estudio_mixto):
    respuesta = cliente_bioquimico.post(url_validar(estudio_mixto), {"accion": "marcar_todas"})
    html = respuesta.content.decode()
    assert all(
        casilla(html, asignacion_de(estudio_mixto, c)) for c in ("PH", "CL-", "ECOLI", "OLOR")
    )
    assert not Validacion.objects.exists()


def test_revisar_sin_elegir_rechaza(cliente_bioquimico, estudio_mixto):
    respuesta = cliente_bioquimico.post(url_validar(estudio_mixto), envio("revisar", estudio_mixto))
    assert respuesta.status_code == 200
    assert "Elegí al menos un resultado para validar." in respuesta.content.decode()
    assert "estudios/validar_resultados.html" in [t.name for t in respuesta.templates]


def test_revisar_muestra_resumen(cliente_bioquimico, estudio_mixto):
    respuesta = cliente_bioquimico.post(
        url_validar(estudio_mixto), envio("revisar", estudio_mixto, "PH", "CL-")
    )
    assert "estudios/validar_resultados_confirmar.html" in [t.name for t in respuesta.templates]
    html = respuesta.content.decode()
    assert (
        f"Se validarán 2 resultados en el estudio {estudio_mixto.pk} "
        f"(muestra PI {estudio_mixto.muestra.numero_pi})." in html
    )
    assert "No cumplen: CL- · Cloruro. Se validarán igual." in html
    assert "El estudio quedará Finalizado." not in html
    assert not Validacion.objects.exists()


def test_revisar_avisa_que_finaliza(cliente_bioquimico, estudio_de, empleado):
    estudio = estudio_de("PH")
    cargar(estudio, empleado, PH="7.4")
    html = cliente_bioquimico.post(url_validar(estudio), envio("revisar", estudio, "PH"))
    html = html.content.decode()
    assert f"Se validará 1 resultado en el estudio {estudio.pk}" in html
    assert "El estudio quedará Finalizado." in html


def test_editar_conserva_seleccion(cliente_bioquimico, estudio_mixto):
    respuesta = cliente_bioquimico.post(
        url_validar(estudio_mixto), envio("editar", estudio_mixto, "CL-")
    )
    html = respuesta.content.decode()
    assert casilla(html, asignacion_de(estudio_mixto, "CL-"))
    assert not casilla(html, asignacion_de(estudio_mixto, "PH"))


def test_confirmar_valida_y_redirige(cliente_bioquimico, estudio_de, empleado):
    estudio = estudio_de("PH", "CL-")
    cargar(estudio, empleado, PH="7.4", CL_="12")  # Cloruro x*10 → 120
    respuesta = cliente_bioquimico.post(
        url_validar(estudio), envio("confirmar", estudio, "PH", "CL-")
    )
    assert respuesta.status_code == 302
    assert respuesta.url == url_detalle(estudio)
    assert mensajes(respuesta) == [
        f"Se validaron 2 resultados del estudio {estudio.pk}: CL-, PH.",
        f"El estudio {estudio.pk} quedó Finalizado.",
    ]
    assert asignacion_de(estudio, "PH").estado == EstadoPruebaEstudio.COMPLETADA


def test_confirmar_uno_usa_singular(cliente_bioquimico, estudio_mixto):
    respuesta = cliente_bioquimico.post(
        url_validar(estudio_mixto), envio("confirmar", estudio_mixto, "PH")
    )
    assert mensajes(respuesta) == [f"Se validó 1 resultado del estudio {estudio_mixto.pk}: PH."]


def test_confirmar_informa_omitidas(cliente_bioquimico, estudio_mixto, bioquimico):
    validar(estudio_mixto, bioquimico, "PH")
    respuesta = cliente_bioquimico.post(
        url_validar(estudio_mixto),
        envio("confirmar", estudio_mixto, "PH", "CL-", vistos={"CL-": "999"}),
    )
    assert mensajes(respuesta) == [
        "CL-: cambió mientras se revisaba.",
        "PH: ya estaba validada.",
    ]


def test_vista_informe_emitido_rechaza(cliente_bioquimico, estudio_mixto):
    Estudio.objects.filter(pk=estudio_mixto.pk).update(estado=EstadoEstudio.INFORME_GENERADO)
    mensaje = "El estudio ya tiene el informe emitido: sus resultados no se pueden validar."
    respuesta = cliente_bioquimico.get(url_validar(estudio_mixto))
    assert respuesta.status_code == 302
    assert mensajes(respuesta) == [mensaje]
    respuesta = cliente_bioquimico.post(
        url_validar(estudio_mixto), envio("confirmar", estudio_mixto, "PH")
    )
    # El mensaje del GET sigue en la sesión porque el test no siguió la redirección.
    assert mensajes(respuesta) == [mensaje, mensaje]
    assert not Validacion.objects.exists()


def test_accion_invalida(cliente_bioquimico, estudio_mixto):
    respuesta = cliente_bioquimico.post(url_validar(estudio_mixto), {"accion": "otra"})
    assert respuesta.status_code == 302
    assert mensajes(respuesta) == ["La acción no es válida."]


def test_estudio_inexistente_404(cliente_bioquimico):
    respuesta = cliente_bioquimico.get(reverse("estudios:validar_resultados", args=[999999]))
    assert respuesta.status_code == 404


def test_error_de_base_al_validar(cliente_bioquimico, estudio_mixto):
    with mock.patch("estudios.servicios.validar_resultados", side_effect=DatabaseError):
        respuesta = cliente_bioquimico.post(
            url_validar(estudio_mixto), envio("confirmar", estudio_mixto, "PH")
        )
    assert mensajes(respuesta) == ["No se pudieron validar los resultados. Intentá nuevamente."]
    assert not Validacion.objects.exists()
