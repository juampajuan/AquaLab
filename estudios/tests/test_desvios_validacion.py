"""Constancia del desvío en la validación (US 8.2): `Validacion.observacion`, `desvio_referencia` y
`desvio_umbral`."""

import datetime as dt
from decimal import Decimal

import pytest
from django.db import IntegrityError, transaction

from estudios.models import Validacion
from muestras.models import Origen

pytestmark = pytest.mark.django_db

DIA = dt.date(2026, 3, 1)


def dia(n):
    return DIA + dt.timedelta(days=n)


@pytest.fixture
def origen(cliente_a):
    return Origen.objects.create(cliente=cliente_a, nombre="Pozo de desvíos")


def test_restriccion_desvio_completo(origen, estudio_en_origen):
    estudio = estudio_en_origen(origen, dia(0), 300201, {"CL-": "10"})
    validacion = Validacion.objects.get(asignacion__estudio=estudio)
    assert validacion.observacion == ""
    assert validacion.desvio_referencia is None and validacion.desvio_umbral is None
    assert not validacion.con_desvio

    for campos in ({"desvio_referencia": Decimal(110)}, {"desvio_umbral": Decimal(30)}):
        with pytest.raises(IntegrityError), transaction.atomic():
            Validacion.objects.filter(pk=validacion.pk).update(**campos)

    Validacion.objects.filter(pk=validacion.pk).update(
        desvio_referencia=Decimal(110), desvio_umbral=Decimal(30), observacion="Repetida"
    )
    validacion.refresh_from_db()
    assert validacion.con_desvio
