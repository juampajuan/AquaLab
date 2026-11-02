import pytest
from django.urls import reverse

from estudios.tests.utiles import cargar, validar
from informes.servicios import emitir_informe
from pruebas.models import Prueba

pytestmark = pytest.mark.django_db


def documento(html):
    """El bloque del documento, sin la marca de borrador ni el encabezado de la página."""
    inicio = html.index('data-componente="informe"')
    cuerpo = html[html.index("<section", inicio) : html.index("<footer", inicio)]
    return cuerpo


@pytest.fixture
def estudio_listo(estudio_de, empleado, bioquimico):
    estudio = estudio_de("PH", "CL-")
    cargar(estudio, empleado, PH="7.4", CL_="40")
    validar(estudio, bioquimico, "PH", "CL-")
    return estudio


def test_emitido_igual_a_vista_previa(cliente_bioquimico, estudio_listo, bioquimico):
    previa = cliente_bioquimico.get(reverse("informes:vista_previa", args=[estudio_listo.pk]))
    emitir_informe(estudio_listo.pk, bioquimico)
    emitido = cliente_bioquimico.get(reverse("informes:ver", args=[estudio_listo.pk]))
    assert emitido.status_code == 200
    html = emitido.content.decode()
    assert documento(html) == documento(previa.content.decode())
    assert "Informe N° INF-000001" in html
    assert "BORRADOR" not in html
    assert "Emitido por " in html


def test_informe_no_cambia_al_editar(cliente_http, estudio_listo, bioquimico):
    cliente = estudio_listo.muestra.cliente
    domicilio_original = "Calle Original 123"
    cliente.domicilio = domicilio_original
    cliente.save(update_fields=["domicilio"])
    emitir_informe(estudio_listo.pk, bioquimico)
    cliente.domicilio = "Otra calle 999"
    cliente.save(update_fields=["domicilio"])
    Prueba.objects.filter(codigo="CL-").update(limite_max="500")
    html = cliente_http.get(reverse("informes:ver", args=[estudio_listo.pk])).content.decode()
    assert domicilio_original in html and "Otra calle 999" not in html
    assert "máx. 350.0" in html and "máx. 500" not in html


def test_ver_sin_informe_404(cliente_http, estudio_listo):
    assert cliente_http.get(reverse("informes:ver", args=[estudio_listo.pk])).status_code == 404


def test_control_y_detalle_ofrecen_ver_informe(cliente_http, estudio_listo, bioquimico):
    ver = reverse("informes:ver", args=[estudio_listo.pk])
    control = reverse("informes:control", args=[estudio_listo.pk])
    detalle = reverse("estudios:detalle", args=[estudio_listo.pk])
    assert ver not in cliente_http.get(control).content.decode()
    assert ver not in cliente_http.get(detalle).content.decode()
    emitir_informe(estudio_listo.pk, bioquimico)
    assert ver in cliente_http.get(control).content.decode()
    assert ver in cliente_http.get(detalle).content.decode()
