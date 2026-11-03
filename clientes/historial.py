"""Historial del cliente (US 3.3): sus muestras con sus estudios e informes.

`muestras_del_historial` es la única consulta del historial. Solo lee: no modifica nada.
"""

from django.db.models import Prefetch

from estudios.models import Estudio
from muestras.models import Muestra


def muestras_del_historial(cliente, desde=None, hasta=None, estado=""):
    """Muestras del cliente, de la fecha de ingreso más reciente a la más antigua.

    Cada muestra trae en `estudios_historial` sus estudios (del más reciente al más antiguo), con
    el informe ya cargado. Con `estado`, quedan solo las muestras con algún estudio en ese estado y
    de cada una solo esos estudios. Se paginan muestras: los estudios de una muestra no se cortan.
    """
    estudios = Estudio.objects.select_related("informe").order_by("-pk")
    muestras = Muestra.objects.filter(cliente=cliente)
    if desde:
        muestras = muestras.filter(fecha_ingreso__gte=desde)
    if hasta:
        muestras = muestras.filter(fecha_ingreso__lte=hasta)
    if estado:
        muestras = muestras.filter(estudios__estado=estado).distinct()
        estudios = estudios.filter(estado=estado)
    return (
        muestras.select_related("origen")
        .prefetch_related(Prefetch("estudios", queryset=estudios, to_attr="estudios_historial"))
        .order_by("-fecha_ingreso", "-numero_pi")
    )
