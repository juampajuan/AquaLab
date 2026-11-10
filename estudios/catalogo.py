from django.db import transaction

from .models import TipoEstudio


class CatalogoNoDisponible(Exception):
    pass


def configuracion_bloqueada(tipo):
    """Llamar solo manteniendo el lock de la fila TipoEstudio dentro de atomic."""
    # Los estudios nuevos toman solo las pruebas activas del tipo (SCRUM-73).
    pruebas = list(
        tipo.pruebas.filter(activa=True).order_by("codigo", "pk").values("id", "codigo", "nombre")
    )
    if not tipo.activo:
        raise CatalogoNoDisponible("El tipo de estudio no está disponible o no tiene pruebas.")
    if not pruebas:
        raise CatalogoNoDisponible("El tipo de estudio no tiene pruebas activas.")
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
