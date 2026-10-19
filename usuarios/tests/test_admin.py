import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from .conftest import PASSWORD_EXISTENTE

pytestmark = pytest.mark.django_db

URL_LISTADO = "admin:usuarios_usuario_changelist"


def test_accion_aprobar_activa_cuentas(cliente_admin, usuario_pendiente):
    otra_pendiente = get_user_model().objects.create_user(
        email="otra@lab.com",
        password=PASSWORD_EXISTENTE,
        first_name="Laura",
        last_name="Díaz",
        is_active=False,
    )

    respuesta = cliente_admin.post(
        reverse(URL_LISTADO),
        {
            "action": "aprobar_cuentas",
            "_selected_action": [usuario_pendiente.pk, otra_pendiente.pk],
        },
        follow=True,
    )

    usuario_pendiente.refresh_from_db()
    otra_pendiente.refresh_from_db()
    assert usuario_pendiente.is_active
    assert otra_pendiente.is_active
    assert "Se aprobaron 2 cuenta(s)." in respuesta.content.decode()


def test_accion_aprobar_es_idempotente(cliente_admin, usuario_aprobado):
    antes = get_user_model().objects.values().get(pk=usuario_aprobado.pk)

    respuesta = cliente_admin.post(
        reverse(URL_LISTADO),
        {"action": "aprobar_cuentas", "_selected_action": [usuario_aprobado.pk]},
        follow=True,
    )

    assert respuesta.status_code == 200
    assert get_user_model().objects.values().get(pk=usuario_aprobado.pk) == antes
    assert "Se aprobaron 0 cuenta(s)." in respuesta.content.decode()


def test_filtro_aprobada_lista_pendientes(cliente_admin, usuario_pendiente, usuario_aprobado):
    respuesta = cliente_admin.get(reverse(URL_LISTADO), {"is_active__exact": "0"})

    contenido = respuesta.content.decode()
    assert respuesta.status_code == 200
    assert usuario_pendiente.email in contenido
    assert usuario_aprobado.email not in contenido
    assert "Aprobada" in contenido
    assert "Aprobar cuentas seleccionadas" in contenido
