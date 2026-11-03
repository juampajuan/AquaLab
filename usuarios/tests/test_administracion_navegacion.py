import pytest
from django.urls import reverse

pytestmark = pytest.mark.django_db


def test_menu_autorizado_y_diseno(client, administrador_panel):
    client.force_login(administrador_panel)
    respuesta = client.get(reverse("administracion:solicitudes"))
    assert respuesta.status_code == 200
    html = respuesta.content.decode()
    assert "Administración" in html
    assert 'aria-current="page"' in html
    assert "data-menu-navegacion" in html
    for nombre in ["solicitudes", "usuarios", "pruebas"]:
        assert reverse("administracion:" + nombre) in html


def test_menu_oculto_sin_autorizacion(client, usuario_aprobado):
    client.force_login(usuario_aprobado)
    assert "Administración" not in client.get(reverse("inicio")).content.decode()


def test_anonimo_solicita_login(client):
    url = reverse("administracion:solicitudes")
    respuesta = client.get(url)
    assert respuesta.status_code == 302
    assert reverse("usuarios:login") in respuesta.url


def test_get_no_modifica_dominio(cliente_panel, usuario_pendiente, usuario_aprobado, mailoutbox):
    from usuarios.models import Usuario

    antes = list(Usuario.objects.order_by("pk").values())
    for nombre in [
        "solicitudes",
        "usuarios",
        "pruebas",
        "aprobar",
        "rechazar",
        "cambiar_rol",
        "desactivar",
        "reactivar",
    ]:
        args = (
            []
            if nombre in {"solicitudes", "usuarios", "pruebas"}
            else [
                usuario_pendiente.pk if nombre in {"aprobar", "rechazar"} else usuario_aprobado.pk
            ]
        )
        assert cliente_panel.get(reverse("administracion:" + nombre, args=args)).status_code == 200
    assert list(Usuario.objects.order_by("pk").values()) == antes
    assert not mailoutbox
