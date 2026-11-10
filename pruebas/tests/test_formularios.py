"""Validación de límites del formulario de pruebas (SCRUM-73, FR-002a)."""

import pytest

from pruebas.formularios import PruebaForm

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    ("minimo", "maximo", "valido"),
    [
        ("", "", True),
        ("", "350", True),
        ("0,5", "1.5", True),
        ("", "Ausente", True),
        ("", "ausencia", True),
        ("Ausente", "10", True),
        ("", "NE", False),
        ("", "SOE", False),
        ("", "35O", False),
        ("Ph-0,2", "", False),
        ("10", "5", False),
    ],
)
def test_limites_validos(datos_prueba, minimo, maximo, valido):
    form = PruebaForm(datos_prueba(limite_min=minimo, limite_max=maximo))
    assert form.is_valid() is valido, form.errors


def test_bloquear_metodo_ignora_cambios(datos_prueba):
    inicial = datos_prueba()
    form = PruebaForm(
        datos_prueba(codigo="CAMBIADO", limite_max="20"), initial=inicial, bloquear_metodo=True
    )
    assert form.is_valid(), form.errors
    assert form.datos_servicio()["codigo"] == "TEST-DIR"
    assert form.datos_servicio()["limite_max"] == "20"
