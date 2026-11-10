"""Pruebas inactivas en tipos, agregar prueba y creación de estudios (SCRUM-73)."""

import uuid
from decimal import Decimal

import pytest

from estudios.forms import AgregarPruebaForm
from estudios.forms_tipos import TipoEstudioForm
from estudios.gestion_tipos import DatosTipoInvalidos, validar_datos
from estudios.models import EstadoEstudio, Estudio, TipoEstudio
from estudios.servicios import (
    CrearEstudioError,
    GestionPruebasError,
    VersionDesactualizada,
    agregar_prueba,
    crear_estudio,
)
from estudios.tests.utiles import asignacion_de, cargar, validar
from informes.servicios import emitir_informe
from pruebas.models import Prueba

pytestmark = pytest.mark.django_db


def datos_estudio(muestra, tipo):
    return {
        "clave": str(uuid.uuid4()),
        "muestra": muestra.pk,
        "tipo": tipo.pk,
        "version": tipo.version,
    }


def test_inactiva_no_se_ofrece(catalogo, estudio, muestra):
    Prueba.objects.filter(codigo="PH").update(activa=False)
    ph = Prueba.objects.get(codigo="PH")
    assert ph not in TipoEstudioForm().fields["pruebas"].queryset
    tipo = TipoEstudio.objects.create(nombre="Con PH")
    tipo.pruebas.set([ph, Prueba.objects.get(codigo="CL-")])
    campo = TipoEstudioForm(tipo_id=tipo.pk).fields["pruebas"]
    assert ph in campo.queryset and "(inactiva)" in campo.label_from_instance(ph)
    datos = {"nombre": "Con PH", "descripcion": "", "prueba_ids": [ph.pk]}
    assert validar_datos(datos, tipo.pk)  # la que ya tenía se conserva
    with pytest.raises(DatosTipoInvalidos):
        validar_datos({**datos, "nombre": "Otro tipo"})
    assert ph not in AgregarPruebaForm(estudio=estudio).fields["prueba"].queryset
    with pytest.raises(GestionPruebasError):
        agregar_prueba(estudio.pk, ph.pk, estudio.creado_por)


def test_estudio_nuevo_solo_activas(catalogo, muestra, empleado):
    ph, cl = Prueba.objects.get(codigo="PH"), Prueba.objects.get(codigo="CL-")
    tipo = TipoEstudio.objects.create(nombre="Dos pruebas")
    tipo.pruebas.set([ph, cl])
    Prueba.objects.filter(pk=ph.pk).update(activa=False)
    estudio = crear_estudio(datos_estudio(muestra, tipo), empleado)
    assert list(estudio.pruebas_asignadas.values_list("prueba__codigo", flat=True)) == ["CL-"]
    Prueba.objects.filter(pk=cl.pk).update(activa=False)
    with pytest.raises(CrearEstudioError, match="no tiene pruebas activas"):
        crear_estudio(datos_estudio(muestra, tipo), empleado)
    from estudios.gestion_tipos import _actualizar_bloqueado

    tipo.activo = False
    tipo.save()
    with pytest.raises(DatosTipoInvalidos):
        _actualizar_bloqueado(tipo, "reactivar", {}, {"pruebas": []})


def test_estudio_existente_sigue(estudio_de, empleado, bioquimico):
    estudio = estudio_de("PH", "CL-")
    Prueba.objects.filter(codigo__in=["PH", "CL-"]).update(activa=False)
    cargar(estudio, empleado, PH="7.4", CL_="40")
    assert asignacion_de(estudio, "CL-").resultado.valor == Decimal("400")
    validar(estudio, bioquimico, "PH", "CL-")
    informe = emitir_informe(estudio.pk, bioquimico)
    assert informe.numero >= 1
    assert Estudio.objects.get(pk=estudio.pk).estado == EstadoEstudio.INFORME_GENERADO


def test_confirmacion_vieja_se_rechaza(catalogo, muestra, empleado, django_user_model):
    from pruebas import gestion

    tipo = TipoEstudio.objects.create(nombre="Para confirmar")
    tipo.pruebas.set(Prueba.objects.filter(codigo__in=["PH", "CL-"]))
    abierta = datos_estudio(muestra, tipo)  # la confirmación se abrió con esta versión
    admin = _admin(django_user_model)
    ph = Prueba.objects.get(codigo="PH")
    gestion.gestionar_prueba(
        usuario=admin, operacion="desactivar", prueba_id=ph.pk, version_esperada=ph.version
    )
    tipo.refresh_from_db()
    assert tipo.version == abierta["version"] + 1
    with pytest.raises(VersionDesactualizada):
        crear_estudio(abierta, empleado)
    assert not Estudio.objects.filter(tipo=tipo).exists()


def _admin(django_user_model):
    from django.contrib.auth.models import Group, Permission

    grupo, _ = Group.objects.get_or_create(name="Administradores")
    grupo.permissions.add(Permission.objects.get(codename="administrar_panel"))
    usuario = django_user_model.objects.create_user(email="adm@x.com", password="Clave-Valida-123")
    usuario.groups.add(grupo)
    return usuario
