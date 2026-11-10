import pytest
from django.urls import reverse

from pruebas.models import Prueba

pytestmark = pytest.mark.django_db


def test_enlace_no_concede_edicion(cliente_panel, administrador_panel):
    prueba = Prueba.objects.create(codigo="CONS", nombre="Consulta")
    url = reverse("admin:pruebas_prueba_change", args=[prueba.pk])
    # Desde SCRUM-73 el listado enlaza a la ficha propia; el admin de Django queda como respaldo.
    listado = cliente_panel.get(reverse("administracion:pruebas")).content.decode()
    assert url not in listado
    assert reverse("catalogo:ficha", args=[prueba.pk]) in listado
    assert cliente_panel.get(url).status_code == 302
    administrador_panel.is_staff = True
    administrador_panel.save(update_fields=["is_staff"])
    assert cliente_panel.get(url).status_code == 403
    assert not administrador_panel.user_permissions.exists()
