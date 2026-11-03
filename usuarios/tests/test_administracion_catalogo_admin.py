import pytest
from django.urls import reverse

from pruebas.models import Prueba

pytestmark = pytest.mark.django_db


def test_enlace_no_concede_edicion(cliente_panel, administrador_panel):
    prueba = Prueba.objects.create(codigo="CONS", nombre="Consulta")
    url = reverse("admin:pruebas_prueba_change", args=[prueba.pk])
    assert url in cliente_panel.get(reverse("administracion:pruebas")).content.decode()
    assert cliente_panel.get(url).status_code == 302
    administrador_panel.is_staff = True
    administrador_panel.save(update_fields=["is_staff"])
    assert cliente_panel.get(url).status_code == 403
    assert not administrador_panel.user_permissions.exists()
