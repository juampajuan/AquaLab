import uuid
from dataclasses import dataclass, field

from django.db import IntegrityError, connection, transaction
from django.db.models.deletion import ProtectedError

from muestras.models import Muestra
from pruebas.models import Prueba

from . import calculo
from .catalogo import CatalogoNoDisponible, configuracion_bloqueada
from .models import (
    EstadoEstudio,
    EstadoPruebaEstudio,
    Estudio,
    Medicion,
    PruebaEstudio,
    TipoEstudio,
)

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


class PruebaYaQuitada(GestionPruebasError):
    pass


class UltimaPrueba(GestionPruebasError):
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


def motivo_para_no_quitar(estudio, asignacion):
    """Error que impide quitar la asignación del estudio, o `None` si se puede."""
    if not estudio.admite_modificaciones:
        return GestionPruebasError("Este estudio ya no admite cambios en sus pruebas.")
    if estudio.pruebas_asignadas.count() <= 1:
        return UltimaPrueba("El estudio debe conservar al menos una prueba.")
    if not asignacion.puede_quitarse():
        return GestionPruebasError(
            "La prueba tiene mediciones o resultados cargados y no se puede quitar."
        )
    return None


def quitar_prueba(estudio_pk, asignacion_pk, usuario):
    if not usuario.is_authenticated or not usuario.is_active:
        raise GestionPruebasError("Se requiere una sesión activa.")
    with transaction.atomic():
        estudio = Estudio.objects.select_for_update().filter(pk=estudio_pk).first()
        if estudio is None:
            raise GestionPruebasError("El estudio no está disponible.")
        asignacion = (
            estudio.pruebas_asignadas.select_for_update()
            .select_related("prueba")
            .filter(pk=asignacion_pk)
            .first()
        )
        if asignacion is None:
            raise PruebaYaQuitada("La prueba ya no forma parte del estudio.")
        if motivo := motivo_para_no_quitar(estudio, asignacion):
            raise motivo
        try:
            with transaction.atomic():
                asignacion.delete()
        except ProtectedError as exc:
            raise GestionPruebasError(
                "La prueba tiene mediciones o resultados cargados y no se puede quitar."
            ) from exc
        return asignacion.prueba


class CargarMedicionesError(Exception):
    pass


@dataclass
class ResultadoCarga:
    guardadas: list = field(default_factory=list)
    omitidas: list = field(default_factory=list)  # pares (prueba, motivo)
    sin_calcular: list = field(default_factory=list)  # pares (prueba, motivo)


def cargar_mediciones(estudio_pk, valores, usuario):
    """Guarda las mediciones `{asignacion_pk: Decimal}` de las pruebas pendientes del estudio.

    Bloquea el estudio, como agregar_prueba y quitar_prueba, así una carga y una quita
    simultáneas se serializan y cada prueba recibe una sola medición.
    """
    if not usuario.is_authenticated or not usuario.is_active:
        raise CargarMedicionesError("Se requiere una sesión activa.")
    resultado = ResultadoCarga()
    with transaction.atomic():
        estudio = Estudio.objects.select_for_update().filter(pk=estudio_pk).first()
        if estudio is None:
            raise CargarMedicionesError("El estudio no está disponible.")
        if not estudio.admite_mediciones:
            raise CargarMedicionesError("Este estudio ya no admite carga de mediciones.")
        asignaciones = (
            estudio.pruebas_asignadas.select_for_update(of=("self",))
            .select_related("prueba")
            .filter(pk__in=valores)
            .order_by("prueba__codigo", "pk")
        )
        # Los pk que no son del estudio (pruebas quitadas o ajenas) no se cargan: la vista
        # informa las quitadas.
        for asignacion in asignaciones:
            if asignacion.estado != EstadoPruebaEstudio.PENDIENTE:
                resultado.omitidas.append((asignacion.prueba, "ya tenía una medición cargada"))
                continue
            if asignacion.prueba.es_calculada:
                resultado.omitidas.append(
                    (asignacion.prueba, "se calcula a partir de otras pruebas")
                )
                continue
            valor = valores[asignacion.pk]
            resultado.guardadas.append(
                Medicion.objects.create(
                    asignacion=asignacion,
                    valor=valor,
                    decimales=max(0, -valor.as_tuple().exponent),
                    unidad=asignacion.prueba.unidad_medicion,
                    cargada_por=usuario,
                )
            )
            asignacion.estado = EstadoPruebaEstudio.CARGADA
            asignacion.save(update_fields=["estado"])
        if resultado.guardadas:
            resultado.sin_calcular = calculo.recalcular(
                estudio, [m.asignacion for m in resultado.guardadas]
            )
        if resultado.guardadas and estudio.estado == EstadoEstudio.PENDIENTE_ANALISIS:
            estudio.estado = EstadoEstudio.EN_PROCESO
            estudio.save(update_fields=["estado"])
    return resultado


class RecalculoError(Exception):
    pass


def recalcular_resultados(estudio_pk, asignacion_pks, usuario):
    """Recalcula los resultados de esas asignaciones y de las calculadas que dependen de ellas.

    US 6.3 lo llama en la misma transacción en que actualiza la medición: si se rechaza porque
    el informe ya se emitió, también se deshace el cambio de la medición.
    """
    if not usuario.is_authenticated or not usuario.is_active:
        raise RecalculoError("Se requiere una sesión activa.")
    with transaction.atomic():
        estudio = Estudio.objects.select_for_update().filter(pk=estudio_pk).first()
        if estudio is None:
            raise RecalculoError("El estudio no está disponible.")
        if not estudio.admite_correcciones:
            raise RecalculoError(
                "El estudio ya tiene el informe emitido: sus mediciones y resultados no se "
                "pueden cambiar."
            )
        asignaciones = estudio.pruebas_asignadas.select_related("prueba").filter(
            pk__in=asignacion_pks
        )
        return calculo.recalcular(estudio, list(asignaciones))
