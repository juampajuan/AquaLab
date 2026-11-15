"""`pruebas_del_detalle` (US 10.1, research R4): la consulta del detalle del estudio, compartida
con el asistente. Debe dar exactamente lo mismo que el contexto de `estudios:detalle`."""

import pytest
from django.urls import reverse

from estudios.tests.utiles import cargar, validar
from estudios.views import pruebas_del_detalle

pytestmark = pytest.mark.django_db

ATRIBUTOS = (
    "motivo_sin_resultado",
    "fuera_de_rango",
    "evaluacion",
    "limite_texto",
    "limite_norma",
    "limite_origen",
    "deteccion",
)


def test_pruebas_del_detalle_igual_a_la_vista(cliente_http, estudio_de, empleado, bioquimico):
    estudio = estudio_de("PH", "CL-", "COND", "ECOLI", "TEMPERATURA")
    cargar(estudio, empleado, {"PH": "7.2", "CL-": "40", "COND": "500", "ECOLI": "1"})
    validar(estudio, bioquimico, "PH")
    contexto = cliente_http.get(reverse("estudios:detalle", args=[estudio.pk])).context
    de_la_vista = contexto["pruebas_asignadas"]
    compartidas = pruebas_del_detalle(estudio)
    assert [a.pk for a in compartidas] == [a.pk for a in de_la_vista]
    for propia, vista in zip(compartidas, de_la_vista, strict=True):
        for atributo in ATRIBUTOS:
            assert getattr(propia, atributo, None) == getattr(vista, atributo, None), atributo
