import pytest
from django.urls import reverse

from clientes.models import Cliente

from .conftest import PASSWORD_EMPLEADO

pytestmark = pytest.mark.django_db


def test_revalidar_conserva_borrador_logout_conserva_filas(
    cliente_autenticado, datos_cliente_persona, cliente_existente
):
    cliente_autenticado.post(reverse("clientes:registrar"), datos_cliente_persona)
    borrador = dict(cliente_autenticado.session["cliente_pendiente"])
    huella = cliente_autenticado.get(reverse("inicio")).context["huella_sesion"]
    respuesta = cliente_autenticado.get(reverse("usuarios:sesion"), HTTP_X_AQUALAB_SESION=huella)
    assert respuesta.status_code == 204
    assert cliente_autenticado.session["cliente_pendiente"] == borrador
    cliente_autenticado.post(reverse("usuarios:logout"))
    assert "cliente_pendiente" not in cliente_autenticado.session
    assert Cliente.objects.filter(pk=cliente_existente.pk).exists()
    assert cliente_autenticado.get(reverse("clientes:registrar_confirmar")).status_code == 302


def test_otro_usuario_no_recupera_borrador(
    cliente_autenticado, datos_cliente_persona, django_user_model
):
    cliente_autenticado.post(reverse("clientes:registrar"), datos_cliente_persona)
    assert "cliente_pendiente" in cliente_autenticado.session
    cliente_autenticado.post(reverse("usuarios:logout"))
    otro = django_user_model.objects.create_user(
        email="otra@lab.com",
        password=PASSWORD_EMPLEADO,
        first_name="Otra",
        is_active=True,
    )
    assert cliente_autenticado.login(email=otro.email, password=PASSWORD_EMPLEADO)
    assert "cliente_pendiente" not in cliente_autenticado.session
    respuesta = cliente_autenticado.get(reverse("clientes:registrar_confirmar"))
    assert respuesta.status_code == 302
    assert respuesta.url == reverse("clientes:registrar")
