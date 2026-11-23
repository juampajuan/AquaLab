"""Historial del laboratorio para el sitio publicado (estudios/historial.py)."""

import io

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError

from clientes.models import Cliente
from estudios import historial
from estudios.models import EstadoEstudio, Estudio
from informes.models import FirmaProfesional

pytestmark = pytest.mark.django_db


@pytest.fixture
def contrasena(monkeypatch):
    monkeypatch.setenv("AQUALAB_HISTORIAL_CONTRASENA", "Laboratorio-2026")
    monkeypatch.setenv("AQUALAB_HISTORIAL_CORREO", "grupo7@gmail.com")


def test_carga_un_laboratorio_sin_rastros_de_demo(catalogo, contrasena):
    call_command("cargar_historial", stdout=io.StringIO())
    usuarios = get_user_model().objects.all()
    assert {u.first_name for u in usuarios} == {"Lucía", "Martín", "Diego"}
    assert not usuarios.filter(email__icontains="demo").exists()
    assert Cliente.objects.count() == 6
    assert not Cliente.objects.filter(email__icontains="demo").exists()
    estudios = historial.estudios_del_historial()
    assert estudios.filter(estado=EstadoEstudio.INFORME_GENERADO).count() > 40
    assert FirmaProfesional.objects.get().matricula == historial.MATRICULA
    nitritos = Estudio.objects.get(tipo__nombre="Nitritos")
    assert nitritos.muestra.origen.nombre == "Pozo 1"
    assert nitritos.estado == EstadoEstudio.EN_PROCESO


def test_no_carga_dos_veces(catalogo, contrasena):
    call_command("cargar_historial", stdout=io.StringIO())
    salida = io.StringIO()
    call_command("cargar_historial", stdout=salida)
    assert salida.getvalue().startswith("El historial ya está cargado.")
    assert Cliente.objects.count() == 6


def test_todos_los_correos_son_alias_de_la_casilla(catalogo, contrasena):
    call_command("cargar_historial", stdout=io.StringIO())
    correos = [u.email for u in get_user_model().objects.all()]
    correos += [c.email for c in Cliente.objects.all()]
    assert all(c.startswith("grupo7+") and c.endswith("@gmail.com") for c in correos), correos
    assert Cliente.objects.get(razon_social="Lácteos del Sur S.A.").email == (
        "grupo7+lacteos@gmail.com"
    )


def test_pide_la_casilla(catalogo, contrasena, monkeypatch):
    monkeypatch.delenv("AQUALAB_HISTORIAL_CORREO", raising=False)
    with pytest.raises(CommandError):
        call_command("cargar_historial", stdout=io.StringIO())
    assert not Cliente.objects.exists()


def test_pide_la_contrasena(catalogo, monkeypatch):
    monkeypatch.delenv("AQUALAB_HISTORIAL_CONTRASENA", raising=False)
    with pytest.raises(CommandError):
        call_command("cargar_historial", stdout=io.StringIO())
    assert not Cliente.objects.exists()
