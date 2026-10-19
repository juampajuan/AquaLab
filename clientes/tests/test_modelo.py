import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from clientes.models import Cliente, es_cuit_valido

pytestmark = pytest.mark.django_db


def test_normaliza_campos_y_documento():
    from clientes.forms import RegistroClienteForm

    cliente = Cliente(
        nombre="  Juan Pérez ",
        razon_social="  ",
        tipo_documento="CUIT",
        numero_documento=" 20-12345678-6 ",
        email="  Juan@Lab.COM ",
        telefono=" +54 11 4321-5678 ",
        domicilio=" Calle 123 ",
    )
    cliente.clean()

    assert cliente.nombre == "Juan Pérez"
    assert cliente.razon_social == ""
    assert cliente.numero_documento == "20123456786"
    assert cliente.email == "juan@lab.com"
    assert cliente.telefono == "+54 11 4321-5678"
    assert cliente.domicilio == "Calle 123"

    form = RegistroClienteForm(
        data={
            "nombre": "  Juan Pérez ",
            "razon_social": "  ",
            "tipo_documento": "CUIT",
            "numero_documento": " 20.123.456.786 ",
            "email": "  Juan@Lab.COM ",
            "telefono": " +54 11 4321-5678 ",
            "domicilio": " Calle 123 ",
        }
    )
    assert form.is_valid(), form.errors
    assert form.cleaned_data["nombre"] == "Juan Pérez"
    assert form.cleaned_data["razon_social"] == ""
    assert form.cleaned_data["numero_documento"] == "20123456786"
    assert form.cleaned_data["email"] == "juan@lab.com"
    assert form.cleaned_data["telefono"] == "+54 11 4321-5678"
    assert form.cleaned_data["domicilio"] == "Calle 123"


@pytest.mark.parametrize("cuit", ["20123456786", "27234567891", "30712345620"])
def test_validador_cuit_modulo_11_validos(cuit):
    assert es_cuit_valido(cuit)


@pytest.mark.parametrize(
    "cuit",
    ["20123456780", "2012345678", "201234567860", "2012345678A", ""],
)
def test_validador_cuit_modulo_11_invalidos(cuit):
    assert not es_cuit_valido(cuit)


def test_constraint_documento_unico(cliente_existente):
    with pytest.raises(IntegrityError), transaction.atomic():
        Cliente(
            razon_social="Otra Empresa",
            tipo_documento="CUIT",
            numero_documento="20123456786",
            email="otra@lab.com",
        ).save()


def test_constraint_nombre_o_razon_social_obligatorio():
    cliente = Cliente(
        nombre="",
        razon_social="",
        tipo_documento="DNI",
        numero_documento="30123456",
        email="a@b.com",
    )
    with pytest.raises(ValidationError):
        cliente.full_clean()

    with pytest.raises(IntegrityError), transaction.atomic():
        cliente.save()
