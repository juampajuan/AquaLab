from django.db import transaction

from .models import TipoEstudio


class CatalogoNoDisponible(Exception):
    pass


def configuracion_bloqueada(tipo):
    """Llamar solo manteniendo el lock de la fila TipoEstudio dentro de atomic."""
    pruebas = list(tipo.pruebas.order_by("codigo", "pk").values("id", "codigo", "nombre"))
    if not tipo.activo or not pruebas:
        raise CatalogoNoDisponible("El tipo de estudio no está disponible o no tiene pruebas.")
    return {
        "id": tipo.pk,
        "nombre": tipo.nombre,
        "descripcion": tipo.descripcion,
        "version": tipo.version,
        "pruebas": pruebas,
    }


def leer_configuracion(tipo_id):
    with transaction.atomic():
        tipo = TipoEstudio.objects.select_for_update().filter(pk=tipo_id).first()
        if tipo is None:
            raise CatalogoNoDisponible("El tipo de estudio no está disponible.")
        return configuracion_bloqueada(tipo)
