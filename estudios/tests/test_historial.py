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
    assert not [n for n in nombres if n.startswith(("Control ", "Vuelco de efluente de "))]
    for muestra in Muestra.objects.select_related("origen"):
        nombre_origen = muestra.origen.nombre
        if nombre_origen in historial.NOMBRES_POR_ORIGEN:
            assert muestra.nombre == historial.nombre_de_muestra(
                nombre_origen, muestra.fecha_muestreo
            )
    escuela = set(
        Muestra.objects.filter(origen__nombre="Escuela N° 12").values_list("nombre", flat=True)
    )
    assert len(escuela) > 1
    assert escuela <= set(historial.NOMBRES_POR_ORIGEN["Escuela N° 12"])


def test_corrige_un_historial_ya_cargado(catalogo, contrasena):
    from muestras.models import Muestra

    call_command("cargar_historial", stdout=io.StringIO())
    lacteos = Cliente.objects.get(razon_social="Lácteos del Sur S.A.")
    Cliente.objects.filter(pk=lacteos.pk).update(
        numero_documento="30712458903", email="viejo@ejemplo.com"
    )
    muestra = Muestra.objects.filter(cliente=lacteos).first()
    Muestra.objects.filter(pk=muestra.pk).update(nombre="Control físico-químico de mayo")
    otra = Muestra.objects.filter(cliente=lacteos).exclude(pk=muestra.pk).first()
    Muestra.objects.filter(pk=otra.pk).update(nombre="Muestra 5")

    salida = io.StringIO()
    call_command("cargar_historial", stdout=salida)
    assert "corrección(es) aplicada(s)" in salida.getvalue()
    lacteos.refresh_from_db()
    muestra.refresh_from_db()
    assert lacteos.numero_documento == "30712458905"
    assert lacteos.email == historial.correo("lacteos")
    otra.refresh_from_db()
    for corregida in (muestra, otra):
        assert corregida.nombre == historial.nombre_de_muestra(
            corregida.origen.nombre, corregida.fecha_muestreo
        )

    assert historial.corregir_historial() == 0


def test_nombre_de_muestra_por_punto_de_toma():
    import datetime as dt

    mayo = dt.date(2026, 5, 10)
    junio = dt.date(2026, 6, 10)
    assert (
        historial.nombre_de_muestra("Escuela N° 12", mayo)
        in historial.NOMBRES_POR_ORIGEN["Escuela N° 12"]
    )
    assert historial.nombre_de_muestra("Escuela N° 12", mayo) != historial.nombre_de_muestra(
        "Escuela N° 12", junio
    )
    assert "{lote}" not in "".join(
        historial.nombre_de_muestra("Línea de envasado", dt.date(2026, m, 1)) for m in range(1, 13)
    )
    assert historial.nombre_de_muestra("Origen nuevo", mayo) == "Toma de rutina"
