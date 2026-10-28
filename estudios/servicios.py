import uuid

from django.db import IntegrityError, connection, transaction

from muestras.models import Muestra
from pruebas.models import Prueba

from .catalogo import CatalogoNoDisponible, configuracion_bloqueada
from .models import Estudio, PruebaEstudio, TipoEstudio

CLAVE_LOCK_ESTUDIOS = 5_100_001


class CrearEstudioError(Exception):
    pass


class VersionDesactualizada(CrearEstudioError):
    def __init__(self, configuracion):
        super().__init__(
            "Cambió la configuración del tipo. Revisá y confirmá el resumen actualizado."
        )
        self.configuracion = configuracion


def normalizar_solicitud(datos):
    try:
        return {
            "clave": uuid.UUID(str(datos["clave"])),
            "muestra": int(datos["muestra"]),
            "tipo": int(datos["tipo"]),
            "version": int(datos["version"]),
        }
    except (KeyError, TypeError, ValueError, OverflowError) as exc:
        raise CrearEstudioError("La solicitud no es válida. Volvé a revisar los datos.") from exc


def comprobar_identidad(estudio, datos, usuario):
    if (estudio.creado_por_id, estudio.muestra_id, estudio.tipo_id) != (
        usuario.pk,
        datos["muestra"],
        datos["tipo"],
    ):
        raise CrearEstudioError("La clave de solicitud no corresponde a esta operación.")
    return estudio


def crear_estudio(datos, usuario, *, pendiente=True):
    if not usuario.is_authenticated or not usuario.is_active:
        raise CrearEstudioError("Se requiere una sesión activa.")
    datos = normalizar_solicitud(datos)
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_advisory_xact_lock(%s)", [CLAVE_LOCK_ESTUDIOS])
        existente = Estudio.objects.filter(clave_idempotencia=datos["clave"]).first()
        if existente is not None:
            return comprobar_identidad(existente, datos, usuario)
        if not pendiente:
            raise CrearEstudioError("La solicitud ya no está pendiente. Iniciá otra operación.")
        tipo = TipoEstudio.objects.select_for_update().filter(pk=datos["tipo"]).first()
        if tipo is None:
            raise CrearEstudioError("El tipo de estudio no está disponible.")
        try:
            config = configuracion_bloqueada(tipo)
        except CatalogoNoDisponible as exc:
            raise CrearEstudioError(str(exc)) from exc
        if config["version"] != datos["version"]:
            raise VersionDesactualizada(config)
        if not Muestra.objects.filter(pk=datos["muestra"]).exists():
            raise CrearEstudioError("La muestra no está disponible.")
        estudio = Estudio.objects.create(
            muestra_id=datos["muestra"],
            tipo=tipo,
            creado_por=usuario,
            tipo_nombre_snapshot=config["nombre"],
            tipo_descripcion_snapshot=config["descripcion"],
            tipo_version_snapshot=config["version"],
            clave_idempotencia=datos["clave"],
        )
        PruebaEstudio.objects.bulk_create(
            [PruebaEstudio(estudio=estudio, prueba_id=p["id"]) for p in config["pruebas"]]
        )
        return estudio


class GestionPruebasError(Exception):
    pass


class PruebaYaAsignada(GestionPruebasError):
    pass


def agregar_prueba(estudio_pk, prueba_pk, usuario):
    if not usuario.is_authenticated or not usuario.is_active:
        raise GestionPruebasError("Se requiere una sesión activa.")
    with transaction.atomic():
        estudio = Estudio.objects.select_for_update().filter(pk=estudio_pk).first()
        if estudio is None:
            raise GestionPruebasError("El estudio no está disponible.")
        if not estudio.admite_modificaciones:
            raise GestionPruebasError("Este estudio ya no admite cambios en sus pruebas.")
        prueba = Prueba.objects.filter(pk=prueba_pk).first()
        if prueba is None:
            raise GestionPruebasError("La prueba no está disponible.")
        ya_asignada = PruebaYaAsignada(f"La prueba {prueba.codigo} ya forma parte del estudio.")
        if estudio.pruebas_asignadas.filter(prueba_id=prueba.pk).exists():
            raise ya_asignada
        try:
            with transaction.atomic():
                return PruebaEstudio.objects.create(estudio=estudio, prueba=prueba)
        except IntegrityError as exc:
            raise ya_asignada from exc
