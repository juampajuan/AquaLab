"""Corrección de la matrícula desde el admin (SCRUM-81)."""

import pytest
from django.urls import reverse

from informes.models import FirmaProfesional

pytestmark = pytest.mark.django_db


def test_admin_corrige_la_matricula_y_conserva_la_imagen(admin_client, bioquimico):
    firma = bioquimico.firma_profesional
    imagen = bytes(firma.imagen)
    url = reverse("admin:informes_firmaprofesional_change", args=[firma.pk])

    html = admin_client.get(url).content.decode()
    assert firma.data_url in html
    assert 'name="matricula"' in html
    assert 'name="imagen"' not in html

    respuesta = admin_client.post(url, {"matricula": "MP 4321"})
    assert respuesta.status_code == 302
    firma.refresh_from_db()
    assert firma.matricula == "MP 4321"
    assert bytes(firma.imagen) == imagen
    assert firma.usuario == bioquimico


def test_admin_no_crea_ni_borra_firmas(admin_client, bioquimico):
    firma = bioquimico.firma_profesional
    assert admin_client.get(reverse("admin:informes_firmaprofesional_add")).status_code == 403
    borrar = reverse("admin:informes_firmaprofesional_delete", args=[firma.pk])
    assert admin_client.post(borrar, {"post": "yes"}).status_code == 403
    assert FirmaProfesional.objects.filter(pk=firma.pk).exists()


def test_admin_lista_las_firmas(admin_client, bioquimico):
    html = admin_client.get(reverse("admin:informes_firmaprofesional_changelist")).content.decode()
    assert "MP 1234" in html
