"""Ayuda en formularios (US 9.1): Mi firma."""

import re

import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


def test_mi_firma_explica_la_firma_y_la_matricula(cliente_bioquimico):
    html = cliente_bioquimico.get(reverse("informes:mi_firma")).content.decode()

    assert re.search(r'<span role="tooltip" id="id_matricula_helptext"[^>]*>\S', html)
    assert re.search(r'<span role="tooltip" id="ayuda-firma"[^>]*>\S', html)
    assert re.search(r'<canvas[^>]*data-firma[^>]*aria-describedby="ayuda-firma"', html)
    assert "Firmá con el mouse o con el dedo" in html
