"""Administración del catálogo compartido; toda escritura pasa por un único servicio."""

from dataclasses import dataclass

from django.db import transaction

from .models import TipoEstudio

PERMISO = "estudios.gestionar_catalogo"


class GestionTipoError(Exception):
    pass


class NoAutorizado(GestionTipoError):
    pass


class TipoNoExiste(GestionTipoError):
    pass


class DatosTipoInvalidos(GestionTipoError):
    def __init__(self, errores):
        self.errores = errores
        super().__init__("Revisá los datos del tipo de estudio.")


class VersionTipoDesactualizada(GestionTipoError):
    def __init__(self, configuracion):
        self.configuracion = configuracion
        super().__init__(
            "Cambió la configuración. Revisá la versión vigente y confirmá nuevamente."
        )


class TipoUtilizado(GestionTipoError):
    def __init__(self):
        super().__init__(
            "El tipo tiene estudios asociados. Podés desactivarlo en lugar de eliminarlo."
        )


class FalloPersistencia(GestionTipoError):
    pass


@dataclass(frozen=True)
class ResultadoTipo:
    estado: str
    tipo_id: int
    version_final: int | None


def autorizar(usuario):
    if not (
        usuario is not None
        and usuario.is_authenticated
        and usuario.is_active
        and usuario.has_perm(PERMISO)
    ):
        raise NoAutorizado("Se requiere permiso de gestión del catálogo.")


def entero_positivo(valor):
    if isinstance(valor, bool) or not isinstance(valor, (int, str)):
        raise DatosTipoInvalidos({"__all__": "La solicitud no es válida."})
    try:
        numero = int(valor)
    except (ValueError, TypeError, OverflowError) as exc:
        raise DatosTipoInvalidos({"__all__": "La solicitud no es válida."}) from exc
    if not 0 < numero <= 9223372036854775807:
        raise DatosTipoInvalidos({"__all__": "La solicitud no es válida."})
    return numero


def _copiar_configuracion(tipo):
    """Solo bajo lock de fila, también para tipos inactivos o legados vacíos."""
    return {
        "id": tipo.pk,
        "nombre": tipo.nombre,
        "descripcion": tipo.descripcion,
        "activo": tipo.activo,
        "version": tipo.version,
        "pruebas": list(tipo.pruebas.order_by("codigo", "pk").values("id", "codigo", "nombre")),
        "uso": tipo.estudios.count(),
    }


def leer_tipo_administrativo(*, usuario, tipo_id):
    autorizar(usuario)
    tipo_id = entero_positivo(tipo_id)
    with transaction.atomic():
        tipo = TipoEstudio.objects.select_for_update().filter(pk=tipo_id).first()
        if tipo is None:
            raise TipoNoExiste("El tipo de estudio no existe.")
        return _copiar_configuracion(tipo)


def normalizar_datos(datos):
    if not isinstance(datos, dict):
        raise DatosTipoInvalidos({"__all__": "La solicitud no es válida."})
    nombre, descripcion, ids = (
        datos.get("nombre"),
        datos.get("descripcion", ""),
        datos.get("prueba_ids"),
    )
    errores = {}
    if not isinstance(nombre, str) or not nombre.strip() or len(nombre.strip()) > 150:
        errores["nombre"] = "Ingresá un nombre de hasta 150 caracteres."
    if not isinstance(descripcion, str):
        errores["descripcion"] = "Ingresá una descripción válida."
    if not isinstance(ids, (list, tuple, set)):
        errores["pruebas"] = "Seleccioná al menos una prueba existente."
    else:
        try:
            ids = sorted({entero_positivo(i) for i in ids})
        except DatosTipoInvalidos:
            errores["pruebas"] = "La selección de pruebas no es válida."
        if not ids:
            errores["pruebas"] = "Seleccioná al menos una prueba existente."
    if errores:
        raise DatosTipoInvalidos(errores)
    return {"nombre": nombre.strip(), "descripcion": descripcion, "prueba_ids": ids}


def validar_datos(datos, tipo_id=None):
    from pruebas.models import Prueba

    datos = normalizar_datos(datos)
    if TipoEstudio.objects.filter(nombre__iexact=datos["nombre"]).exclude(pk=tipo_id).exists():
        raise DatosTipoInvalidos({"nombre": "Ya existe un tipo con ese nombre."})
    if Prueba.objects.filter(pk__in=datos["prueba_ids"]).count() != len(datos["prueba_ids"]):
        raise DatosTipoInvalidos({"pruebas": "Alguna prueba seleccionada ya no existe."})
    return datos


def _actualizar_bloqueado(tipo, operacion, datos, actual):
    """Tipo bloqueado y versión comprobada por el único escritor público."""
    if operacion == "eliminar":
        if tipo.estudios.exists():
            raise TipoUtilizado()
        pk = tipo.pk
        tipo.delete()
        return ResultadoTipo("eliminado", pk, None)
    if operacion == "editar":
        propuesta = validar_datos(datos, tipo.pk)
        igual = (
            tipo.nombre == propuesta["nombre"]
            and tipo.descripcion == propuesta["descripcion"]
            and sorted(p["id"] for p in actual["pruebas"]) == propuesta["prueba_ids"]
        )
        if igual:
            return ResultadoTipo("sin_cambios", tipo.pk, tipo.version)
        tipo.nombre = propuesta["nombre"]
        tipo.descripcion = propuesta["descripcion"]
        tipo.version += 1
        tipo.save(update_fields=["nombre", "descripcion", "version"])
        tipo.pruebas.set(propuesta["prueba_ids"])
        return ResultadoTipo("actualizado", tipo.pk, tipo.version)
    destino = operacion == "reactivar"
    if destino and not actual["pruebas"]:
        raise DatosTipoInvalidos(
            {"pruebas": "El tipo necesita al menos una prueba válida para reactivarse."}
        )
    if tipo.activo == destino:
        return ResultadoTipo("sin_cambios", tipo.pk, tipo.version)
    tipo.activo = destino
    tipo.version += 1
    tipo.save(update_fields=["activo", "version"])
    return ResultadoTipo("reactivado" if destino else "desactivado", tipo.pk, tipo.version)


def gestionar_tipo_estudio(*, usuario, operacion, tipo_id=None, version_esperada=None, datos=None):
    from django.db import DatabaseError, IntegrityError
    from django.db.models.deletion import ProtectedError

    autorizar(usuario)
    if operacion not in ("crear", "editar", "desactivar", "reactivar", "eliminar"):
        raise DatosTipoInvalidos({"__all__": "La operación no es válida."})
    if operacion == "crear":
        if tipo_id is not None or version_esperada is not None:
            raise DatosTipoInvalidos({"__all__": "La solicitud no es válida."})
    else:
        tipo_id = entero_positivo(tipo_id)
        version_esperada = entero_positivo(version_esperada)
    try:
        with transaction.atomic():
            if operacion == "crear":
                propuesta = validar_datos(datos)
                tipo = TipoEstudio.objects.create(
                    nombre=propuesta["nombre"], descripcion=propuesta["descripcion"]
                )
                tipo.pruebas.set(propuesta["prueba_ids"])
                resultado = ResultadoTipo("creado", tipo.pk, tipo.version)
            else:
                tipo = TipoEstudio.objects.select_for_update().filter(pk=tipo_id).first()
                if tipo is None:
                    raise TipoNoExiste("El tipo de estudio no existe.")
                actual = _copiar_configuracion(tipo)
                if version_esperada != tipo.version:
                    raise VersionTipoDesactualizada(actual)
                resultado = _actualizar_bloqueado(tipo, operacion, datos, actual)
        return resultado
    except ProtectedError as exc:
        raise TipoUtilizado() from exc
    except IntegrityError as exc:
        diagnostico = getattr(getattr(exc, "__cause__", None), "diag", None)
        if diagnostico and diagnostico.constraint_name == "tipo_estudio_nombre_unico_ci":
            raise DatosTipoInvalidos({"nombre": "Ya existe un tipo con ese nombre."}) from exc
        raise FalloPersistencia(
            "No se guardó ningún cambio. Revisá los datos e intentá nuevamente."
        ) from exc
    except DatabaseError as exc:
        raise FalloPersistencia("No se guardó ningún cambio. Intentá nuevamente.") from exc
