import pytest
from django.contrib.auth.models import Permission
from django.urls import reverse

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "nombre",
    [
        "tipos_listar",
        "tipos_crear",
        "tipos_editar",
        "tipos_desactivar",
        "tipos_reactivar",
        "tipos_eliminar",
        "tipos_confirmar",
    ],
)
@pytest.mark.parametrize("metodo", ["get", "post"])
def test_panel_sin_permiso_de_tipos_403(cliente_panel, nombre, metodo):
    url = reverse(
        "estudios:" + nombre,
        args=[999999]
        if nombre in {"tipos_editar", "tipos_desactivar", "tipos_reactivar", "tipos_eliminar"}
        else [],
    )
    assert getattr(cliente_panel, metodo)(url).status_code == 403


def test_gestor_solo_permiso_conserva_acceso(client, usuario_aprobado):
    permiso = Permission.objects.get(
        content_type__app_label="estudios", codename="gestionar_catalogo"
    )
    usuario_aprobado.user_permissions.add(permiso)
    client.force_login(usuario_aprobado)
    assert client.get(reverse("estudios:tipos_listar")).status_code == 200
    assert client.get(reverse("administracion:solicitudes")).status_code == 403
