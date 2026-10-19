import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction

pytestmark = pytest.mark.django_db


def test_normaliza_email_y_nombres():
    from usuarios.forms import RegistroForm

    Usuario = get_user_model()

    usuario = Usuario.objects.create_user(
        email="  Ana@Lab.COM ",
        password="clave-segura-123",
        first_name="Ana",
        last_name="Pérez",
    )
    assert usuario.email == "ana@lab.com"
    assert usuario.check_password("clave-segura-123")

    sin_guardar = Usuario(email="  Ana@Lab.COM ", first_name="Ana", last_name="Pérez")
    sin_guardar.clean()
    assert sin_guardar.email == "ana@lab.com"

    usuario.delete()
    form = RegistroForm(
        data={
            "first_name": "  Ana ",
            "last_name": " Pérez  ",
            "email": "  Ana@Lab.com ",
            "password1": "Clave-Secreta-Unica-987",
            "password2": "Clave-Secreta-Unica-987",
        }
    )
    assert form.is_valid(), form.errors
    assert form.cleaned_data["first_name"] == "Ana"
    assert form.cleaned_data["last_name"] == "Pérez"
    assert form.cleaned_data["email"] == "ana@lab.com"


def test_constraint_email_case_insensitive():
    Usuario = get_user_model()
    Usuario.objects.create_user(
        email="ana@lab.com", password="clave-segura-123", first_name="Ana", last_name="Pérez"
    )

    with pytest.raises(IntegrityError), transaction.atomic():
        Usuario(email="ANA@lab.com", first_name="X", last_name="Y").save()


def test_create_superuser_activo_y_staff():
    admin = get_user_model().objects.create_superuser(
        email="admin@ejemplo.com",
        password="clave-segura-123",
        first_name="Admin",
        last_name="AquaLab",
    )

    assert admin.is_active
    assert admin.is_staff
    assert admin.is_superuser
