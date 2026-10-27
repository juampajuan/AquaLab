import datetime

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.urls import reverse

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


def test_origen_con_muestras_no_cambia_de_cliente(crear_muestra, origen_a, cliente_b):
    crear_muestra(200001)

    origen_a.cliente = cliente_b
    with pytest.raises(ValidationError) as error:
        origen_a.full_clean()
    assert error.value.message_dict["cliente"] == [
        "No se puede cambiar el cliente de un origen que ya tiene muestras."
    ]


def test_origen_sin_muestras_puede_cambiar_de_cliente(origen_a, cliente_b):
    origen_a.cliente = cliente_b
    origen_a.full_clean()


def test_admin_no_permite_reasignar_origen_con_muestras(
    admin_client, crear_muestra, origen_a, cliente_b
):
    crear_muestra(200001)
    url = reverse("admin:muestras_origen_change", args=[origen_a.pk])

    assert 'name="cliente"' not in admin_client.get(url).content.decode()
    respuesta = admin_client.post(url, {"cliente": cliente_b.pk, "nombre": origen_a.nombre})

    assert respuesta.status_code == 302
    origen_a.refresh_from_db()
    assert origen_a.cliente_id != cliente_b.pk


def test_admin_permite_reasignar_origen_sin_muestras(admin_client, origen_a, cliente_b):
    url = reverse("admin:muestras_origen_change", args=[origen_a.pk])

    respuesta = admin_client.post(url, {"cliente": cliente_b.pk, "nombre": origen_a.nombre})

    assert respuesta.status_code == 302
    origen_a.refresh_from_db()
    assert origen_a.cliente_id == cliente_b.pk
