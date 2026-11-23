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


def test_carga_un_laboratorio_sin_rastros_de_demo(catalogo, contrasena):
    call_command("cargar_historial", stdout=io.StringIO())
    usuarios = get_user_model().objects.all()
    assert {u.first_name for u in usuarios} == {"Lucía", "Martín", "Diego", "Juan Pablo"}
    assert not usuarios.filter(email__icontains="demo").exists()
    assert Cliente.objects.count() == 6
    assert not Cliente.objects.filter(email__icontains="demo").exists()
    estudios = historial.estudios_del_historial()
    assert estudios.filter(estado=EstadoEstudio.INFORME_GENERADO).count() > 40
    martin = usuarios.get(first_name="Martín")
    assert FirmaProfesional.objects.get(usuario=martin).matricula == historial.MATRICULA
    juan_pablo = usuarios.get(first_name="Juan Pablo")
    assert juan_pablo.groups.filter(name="Bioquímicos").exists()
    assert FirmaProfesional.objects.filter(usuario=juan_pablo).exists()
    nitritos = Estudio.objects.get(tipo__nombre="Nitritos")
    assert nitritos.muestra.origen.nombre == "Pozo 1"
    assert nitritos.estado == EstadoEstudio.EN_PROCESO


def test_no_carga_dos_veces(catalogo, contrasena):
    call_command("cargar_historial", stdout=io.StringIO())
    salida = io.StringIO()
    call_command("cargar_historial", stdout=salida)
    assert salida.getvalue().startswith("El historial ya está cargado.")
    assert Cliente.objects.count() == 6


def test_correos_de_gmail(catalogo, contrasena):
    call_command("cargar_historial", stdout=io.StringIO())
    correos = [u.email for u in get_user_model().objects.all()]
    correos += [c.email for c in Cliente.objects.all()]
    assert all(c.endswith("@gmail.com") for c in correos), correos
    assert Cliente.objects.get(razon_social="Lácteos del Sur S.A.").email == (
        "aqualab.real@gmail.com"
    )


def test_bioquimico_extra_existente_solo_se_suma(catalogo, contrasena, django_user_model):
    previo = django_user_model.objects.create_user(
        email="juanpidominguez03@gmail.com", password="x-Previa-123", first_name="Juan Pablo"
    )
    call_command("cargar_historial", stdout=io.StringIO())
    previo.refresh_from_db()
    assert previo.check_password("x-Previa-123")
    assert previo.groups.filter(name="Bioquímicos").exists()


def test_pide_la_contrasena(catalogo, monkeypatch):
    monkeypatch.delenv("AQUALAB_HISTORIAL_CONTRASENA", raising=False)
    with pytest.raises(CommandError):
        call_command("cargar_historial", stdout=io.StringIO())
    assert not Cliente.objects.exists()


def test_muestras_con_nombres_como_los_cargaria_el_laboratorio(catalogo, contrasena):
    import re

    from muestras.models import Muestra

    call_command("cargar_historial", stdout=io.StringIO())
    nombres = list(Muestra.objects.values_list("nombre", flat=True))
    assert nombres
    assert not [n for n in nombres if re.fullmatch(r"Muestra [0-9]+", n)]
    efluente = Muestra.objects.filter(origen__nombre="Salida a colectora").first()
    assert efluente.nombre.startswith("Vuelco de efluente de ")
    escuela = Muestra.objects.filter(origen__nombre="Escuela N° 12").first()
    assert escuela.nombre.startswith("Control bacteriológico de ")
    pozo = Muestra.objects.filter(origen__nombre="Pozo 1").first()
    assert pozo.nombre.startswith("Control físico-químico de ")


def test_corrige_un_historial_ya_cargado(catalogo, contrasena):
    from muestras.models import Muestra

    call_command("cargar_historial", stdout=io.StringIO())
    lacteos = Cliente.objects.get(razon_social="Lácteos del Sur S.A.")
    Cliente.objects.filter(pk=lacteos.pk).update(
        numero_documento="30712458903", email="viejo@ejemplo.com"
    )
    muestra = Muestra.objects.filter(cliente=lacteos).first()
    Muestra.objects.filter(pk=muestra.pk).update(nombre="Muestra 5")

    salida = io.StringIO()
    call_command("cargar_historial", stdout=salida)
    assert "corrección(es) aplicada(s)" in salida.getvalue()
    lacteos.refresh_from_db()
    muestra.refresh_from_db()
    assert lacteos.numero_documento == "30712458905"
    assert lacteos.email == historial.correo("lacteos")
    assert muestra.nombre == historial.nombre_de_muestra(
        muestra.origen.nombre, muestra.fecha_muestreo
    )

    assert historial.corregir_historial() == 0
