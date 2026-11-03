import pytest
from django.contrib.auth.models import Permission
from django.urls import reverse

pytestmark = pytest.mark.django_db


def test_tipos_solo_en_administracion_con_ambos_permisos(cliente_panel, administrador_panel):
    permiso = Permission.objects.get(
        content_type__app_label="estudios", codename="gestionar_catalogo"
    )
    url = reverse("estudios:tipos_listar")
    html = cliente_panel.get(reverse("administracion:solicitudes")).content.decode()
    assert url not in html
    administrador_panel.user_permissions.add(permiso)
    html = cliente_panel.get(reverse("administracion:solicitudes")).content.decode()
    assert html.count('href="' + url + '"') == 1
    assert html.index('data-seccion="administracion"') < html.index('href="' + url + '"')


def test_gestor_conserva_tarjeta_sin_panel(client, usuario_aprobado):
    permiso = Permission.objects.get(
        content_type__app_label="estudios", codename="gestionar_catalogo"
    )
    usuario_aprobado.user_permissions.add(permiso)
    client.force_login(usuario_aprobado)
    html = client.get(reverse("inicio")).content.decode()
    assert reverse("estudios:tipos_listar") in html
    assert 'data-seccion="administracion"' not in html
    nav = html.split("data-menu-navegacion>")[1].split("</nav>")[0]
    assert reverse("estudios:tipos_listar") not in nav
