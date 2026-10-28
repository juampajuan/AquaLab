"""Estructura de la interfaz de estudios (SCRUM-67, US2)."""

import pytest
from django.urls import reverse

from config.tests.ayudas_diseno import tiene_componentes_de_confirmacion

pytestmark = pytest.mark.django_db


def test_confirmacion_usa_los_componentes_comunes(cliente_http, muestra, tipo):
    respuesta = cliente_http.post(
        reverse("estudios:crear"), {"muestra": muestra.pk, "tipo": tipo.pk}
    )
    html = cliente_http.get(respuesta.url).content.decode()

    assert tiene_componentes_de_confirmacion(html)
    assert f"PI {muestra.numero_pi}" in html
    assert 'data-estado="warning">Pendiente de análisis' in html
