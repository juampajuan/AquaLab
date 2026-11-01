import pytest
from django.contrib.messages import get_messages
from django.urls import reverse

from estudios.models import EstadoEstudio, Estudio
from estudios.tests.utiles import cargar, validar
from informes.models import Informe

pytestmark = pytest.mark.django_db


def url(estudio):
    return reverse("informes:vista_previa", args=[estudio.pk])


def mensajes(respuesta):
    return [str(m) for m in get_messages(respuesta.wsgi_request)]


@pytest.fixture
def estudio_listo(estudio_de, empleado, bioquimico):
    estudio = estudio_de("PH", "CL-", "ECOLI", "SS10")
    # Cloruro es fórmula x*10: 40 → 400 mg/l (fuera de norma). SS10 0,05 < LD 0,1.
    cargar(estudio, empleado, PH="7.4", CL_="40", ECOLI="0", SS10="0.05")
    validar(estudio, bioquimico, "PH", "CL-", "ECOLI", "SS10")
    return estudio


def test_vista_previa_muestra_documento(cliente_bioquimico, estudio_listo):
    respuesta = cliente_bioquimico.get(url(estudio_listo))
    assert respuesta.status_code == 200
    html = respuesta.content.decode()
    muestra = estudio_listo.muestra
    for texto in (
        "Vista previa: este informe todavía no fue emitido.",
        "BORRADOR",
        "Laboratorio de Análisis de Agua (DEMO)",
        "Habilitación N° 0000 (DEMO)",
        muestra.cliente.nombre_completo,
        muestra.cliente.numero_documento,
        f"N° PI {muestra.numero_pi}",
        muestra.origen.nombre,
        muestra.sitio_extraccion,
        estudio_listo.tipo_nombre_snapshot,
        "7,4",
        "6.4 a 8.5",
        "400",
        "máx. 350.0",
        "Ausente",
        "&lt; 0,1",
        "Fuera de norma",
        "Responsable técnico",
    ):
        assert texto in html, texto
    assert 'data-evaluacion="fuera_de_norma"' in html


def test_vista_previa_no_cambia_nada(cliente_bioquimico, estudio_listo):
    antes = Estudio.objects.get(pk=estudio_listo.pk).estado
    cliente_bioquimico.get(url(estudio_listo))
    assert not Informe.objects.exists()
    assert Estudio.objects.get(pk=estudio_listo.pk).estado == antes


@pytest.mark.parametrize("caso", ["incompleto", "con_informe"])
def test_vista_previa_rechaza_no_listo(cliente_bioquimico, estudio_de, empleado, emitir, caso):
    estudio = estudio_de("PH", "CL-")
    cargar(estudio, empleado, PH="7.4")
    motivo = "Hay 2 pruebas sin completar."
    if caso == "con_informe":
        emitir(estudio)
        motivo = "El informe de este estudio ya fue generado."
    respuesta = cliente_bioquimico.get(url(estudio))
    assert respuesta.status_code == 302
    assert respuesta["Location"] == reverse("informes:control", args=[estudio.pk])
    assert mensajes(respuesta) == [motivo]


def test_vista_previa_emitir_solo_con_permiso(cliente_bioquimico, estudio_listo, django_user_model):
    accion = reverse("informes:generar", args=[estudio_listo.pk])
    html = cliente_bioquimico.get(url(estudio_listo)).content.decode()
    assert f'action="{accion}"' in html
    assert "data-enviado" in html or "dataset.enviado" in html
    comun = django_user_model.objects.create_user(
        email="comun-informes@ejemplo.com", password="Clave-Valida-123", is_active=True
    )
    from django.test import Client

    cliente = Client()
    cliente.force_login(comun)
    html = cliente.get(url(estudio_listo)).content.decode()
    assert f'action="{accion}"' not in html
    assert "Solo un integrante del grupo Bioquímicos puede emitir el informe." in html


def test_vista_previa_404(cliente_http):
    assert cliente_http.get(reverse("informes:vista_previa", args=[999999])).status_code == 404


def test_estado_estudio_finalizado_en_la_vista_previa(estudio_listo):
    assert Estudio.objects.get(pk=estudio_listo.pk).estado == EstadoEstudio.FINALIZADO
