from datetime import datetime, time, timedelta

from django.db.models import Q
from django.utils import timezone

from clientes.models import normalizar_numero_documento

MAX_NUMERO_PI_SQL = 2_147_483_647


def filtro_busqueda(q):
    """Filtro de la búsqueda de estudios: muestra, cliente, tipo, N° de estudio, N° PI o documento.

    Lo usan `estudios:buscar` (US 5.2) e `informes:listar` (US 7.1).
    """
    filtro = (
        Q(muestra__nombre__unaccent__icontains=q)
        | Q(muestra__cliente__nombre__unaccent__icontains=q)
        | Q(muestra__cliente__razon_social__unaccent__icontains=q)
        | Q(tipo_nombre_snapshot__unaccent__icontains=q)
    )
    if q.isascii() and q.isdigit():
        numero = int(q)
        filtro |= Q(pk=numero)
        if numero <= MAX_NUMERO_PI_SQL:
            filtro |= Q(muestra__numero_pi=numero)
    q_doc = normalizar_numero_documento(q)
    if len(q_doc) >= 4 and q_doc.isascii() and q_doc.isdigit():
        filtro |= Q(muestra__cliente__numero_documento__contains=q_doc)
    return filtro


def filtro_estado_fechas(desde=None, hasta=None, estado=""):
    """Filtro por estado actual y días completos de `fecha_creacion` en la zona del laboratorio
    (SCRUM-74). Sin criterios no restringe."""
    filtro = Q()
    if estado:
        filtro &= Q(estado=estado)
    if desde:
        filtro &= Q(fecha_creacion__gte=inicio_del_dia(desde))
    if hasta:
        filtro &= Q(fecha_creacion__lt=inicio_del_dia(hasta + timedelta(days=1)))
    return filtro


def inicio_del_dia(fecha):
    """00:00 de `fecha` en la zona del laboratorio (`TIME_ZONE`), con zona."""
    return timezone.make_aware(datetime.combine(fecha, time.min), timezone.get_default_timezone())
