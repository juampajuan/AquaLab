from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.urls import reverse

from estudios.mediciones import leer_valor
from estudios.models import EstadoPruebaEstudio, Medicion
from estudios.tests.utiles import asignacion_de, cargar

pytestmark = pytest.mark.django_db


def url(nombre, estudio):
    return reverse(f"estudios:{nombre}", args=[estudio.pk])


@pytest.fixture
def estudio_ap(estudio_de):
    return estudio_de("ECOLI", "PH")


@pytest.mark.parametrize(
    ("texto", "valor"),
    [("Ausente", Decimal(0)), ("presente", Decimal(1)), (" AUSENTE ", Decimal(0)), ("", None)],
)
def test_leer_valor_presencia(texto, valor):
    assert leer_valor(texto, presencia=True) == valor


@pytest.mark.parametrize("texto", ["0", "1", "Ausencia", "Positivo"])
def test_leer_valor_presencia_rechaza_otros_textos(texto):
    with pytest.raises(ValidationError, match="Elegí Ausente o Presente."):
        leer_valor(texto, presencia=True)


def test_leer_valor_numerico_sigue_rechazando_texto():
    with pytest.raises(ValidationError):
        leer_valor("Ausente")


def test_carga_ofrece_selector_solo_para_ap(cliente_http, estudio_ap):
    html = cliente_http.get(url("cargar_mediciones", estudio_ap)).content.decode()
    ecoli, ph = (asignacion_de(estudio_ap, c) for c in ("ECOLI", "PH"))
    assert f'<select name="medicion_{ecoli.pk}"' in html
    assert '<option value="Ausente">Ausente</option>' in html
    assert '<option value="Presente">Presente</option>' in html
    assert f'name="medicion_{ph.pk}"' in html and html.count('inputmode="decimal"') == 1


def test_carga_guarda_ausente_como_cero(cliente_http, estudio_ap):
    ecoli = asignacion_de(estudio_ap, "ECOLI")
    respuesta = cliente_http.post(
        url("cargar_mediciones", estudio_ap),
        {"accion": "confirmar", f"medicion_{ecoli.pk}": "Ausente"},
    )
    assert respuesta.status_code == 302
    medicion = Medicion.objects.get(asignacion=ecoli)
    assert medicion.valor == 0 and medicion.decimales == 0
    ecoli.refresh_from_db()
    assert ecoli.estado == EstadoPruebaEstudio.CARGADA


def test_carga_rechaza_numero_en_prueba_ap(cliente_http, estudio_ap):
    ecoli = asignacion_de(estudio_ap, "ECOLI")
    respuesta = cliente_http.post(
        url("cargar_mediciones", estudio_ap),
        {"accion": "revisar", f"medicion_{ecoli.pk}": "1"},
    )
    assert respuesta.status_code == 200
    assert "Elegí Ausente o Presente." in respuesta.content.decode()
    assert not Medicion.objects.exists()


def test_detalle_muestra_texto_sin_unidad(cliente_http, estudio_ap, empleado):
    cargar(estudio_ap, empleado, ECOLI="1")
    html = cliente_http.get(url("detalle", estudio_ap)).content.decode()
    assert html.count(">Presente</span>") == 2  # medición y resultado
    assert "A/P" not in html


def test_corregir_precarga_texto_y_guarda_cambio(cliente_http, estudio_ap, empleado):
    cargar(estudio_ap, empleado, ECOLI="0")
    ecoli = asignacion_de(estudio_ap, "ECOLI")
    html = cliente_http.get(url("corregir_mediciones", estudio_ap)).content.decode()
    assert '<option value="Ausente" selected>Ausente</option>' in html
    assert f'name="original_{ecoli.pk}" value="0"' in html

    datos = {f"original_{ecoli.pk}": "0", f"medicion_{ecoli.pk}": "Presente"}
    revisar = cliente_http.post(
        url("corregir_mediciones", estudio_ap), {"accion": "revisar", **datos}
    )
    resumen = revisar.content.decode()
    assert ">Ausente</td>" in resumen and "Presente</td>" in resumen

    cliente_http.post(url("corregir_mediciones", estudio_ap), {"accion": "confirmar", **datos})
    assert Medicion.objects.get(asignacion=ecoli).valor == 1
    ecoli.refresh_from_db()
    assert ecoli.resultado.valor == 1
