import pytest
from django.urls import resolve, reverse

from .conftest import PASSWORD_EXISTENTE

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "nombre",
    [
        "inicio",
        "clientes:registrar",
        "clientes:registrar_confirmar",
        "usuarios:sesion",
        "admin:index",
    ],
)
@pytest.mark.parametrize("metodo", ["get", "post"])
def test_protegida_sin_sesion(client, nombre, metodo):
    respuesta = getattr(client, metodo)(reverse(nombre))
    assert respuesta.status_code == 302
    assert "<form" not in respuesta.content.decode()


def test_alias_logout_no_concede_staff(client, usuario_aprobado):
    from usuarios.views import CerrarSesionView

    assert resolve(reverse("admin:logout")).func.view_class is CerrarSesionView
    assert client.login(email=usuario_aprobado.email, password=PASSWORD_EXISTENTE)
    respuesta = client.get(reverse("admin:index"))
    assert respuesta.status_code == 302
    usuario_aprobado.refresh_from_db()
    assert not usuario_aprobado.is_staff
