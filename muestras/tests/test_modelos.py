import datetime

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from muestras.models import Muestra, Origen

pytestmark = pytest.mark.django_db


def test_constraint_origen_unico_por_cliente(cliente_a, cliente_b):
    Origen.objects.create(cliente=cliente_a, nombre="Pozo N°2")

    with pytest.raises(IntegrityError), transaction.atomic():
        Origen.objects.create(cliente=cliente_a, nombre="pozo n°2")

    Origen.objects.create(cliente=cliente_b, nombre="Pozo N°2")
    assert Origen.objects.filter(nombre__iexact="pozo n°2").count() == 2


def test_constraint_fechas_muestra(crear_muestra, hoy):
    ayer = hoy - datetime.timedelta(days=1)

    with pytest.raises(IntegrityError), transaction.atomic():
        crear_muestra(200001, fecha_muestreo=hoy, fecha_ingreso=ayer)

    muestra = Muestra(fecha_muestreo=hoy, fecha_ingreso=ayer)
    with pytest.raises(ValidationError) as error:
        muestra.clean()
    assert error.value.message_dict["fecha_muestreo"] == [
        "La fecha de muestreo no puede ser posterior a la fecha de ingreso."
    ]


def test_constraint_numero_pi_minimo_y_unico(crear_muestra):
    with pytest.raises(IntegrityError), transaction.atomic():
        crear_muestra(200000)

    crear_muestra(200001)
    with pytest.raises(IntegrityError), transaction.atomic():
        crear_muestra(200001)


def test_muestra_clean_rechaza_origen_de_otro_cliente(cliente_a, origen_b, hoy):
    muestra = Muestra(cliente=cliente_a, origen=origen_b, fecha_muestreo=hoy, fecha_ingreso=hoy)

    with pytest.raises(ValidationError) as error:
        muestra.clean()

    assert error.value.message_dict["origen"] == ["El origen no pertenece al cliente seleccionado."]


def test_valores_por_defecto_muestra(crear_muestra):
    muestra = crear_muestra(200001)
    muestra.refresh_from_db()

    assert muestra.tipo_vertido == "agua"
    assert muestra.estado == "ingresada"
