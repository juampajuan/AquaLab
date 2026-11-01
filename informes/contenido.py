"""Armado del informe de un estudio (US 7.2): lo usan la vista previa y la emisión.

El resultado es un diccionario solo de textos, listo para mostrar y para guardar como copia en
`Informe.contenido`: el informe emitido se dibuja siempre desde esa copia (FR-010), con el mismo
template que la vista previa, así se ven idénticos.
"""

from django.conf import settings
from django.db.models import Prefetch

from estudios import calculo
from estudios.mediciones import es_presencia, texto_presencia
from estudios.models import EstadoPruebaEstudio, Validacion
from pruebas.limites import (
    Evaluacion,
    LimitesAplicables,
    bajo_deteccion,
    evaluar,
    limites_aplicables,
    texto_limite,
)

FORMATO_FECHA = "%d/%m/%Y"


def con_coma(numero):
    return str(numero).replace(".", ",")


def texto_resultado(resultado, limites):
    """«Ausente»/«Presente» en las pruebas A/P, «< LD» por debajo del límite de detección y si no
    el valor como se muestra en pantalla, con coma decimal."""
    if es_presencia(resultado.unidad):
        return texto_presencia(resultado.valor)
    if bajo_deteccion(resultado.valor, limites):
        return f"< {con_coma(limites.deteccion.strip())}"
    return con_coma(resultado.valor_mostrado)


def limites_y_evaluacion(asignacion, tipo_vertido):
    """Los límites y la evaluación guardados en la validación vigente (US 6.4). Sin validación
    (atajo de algunos tests) se evalúa con el catálogo, como el detalle del estudio."""
    prueba = asignacion.prueba
    vigentes = asignacion.validaciones_vigentes
    if vigentes and asignacion.estado == EstadoPruebaEstudio.COMPLETADA:
        v = vigentes[0]
        limites = LimitesAplicables(
            v.limite_min, v.limite_max, v.norma, v.origen_limites, prueba.limite_deteccion
        )
        return limites, Evaluacion(v.evaluacion)
    limites = limites_aplicables(prueba, tipo_vertido)
    return limites, evaluar(asignacion.resultado.valor, limites)


def armar_prueba(asignacion, tipo_vertido):
    prueba, resultado = asignacion.prueba, asignacion.resultado
    limites, evaluacion = limites_y_evaluacion(asignacion, tipo_vertido)
    return {
        "codigo": prueba.codigo,
        "nombre": prueba.nombre,
        "unidad": resultado.unidad,
        "resultado": str(resultado.valor),
        "resultado_texto": texto_resultado(resultado, limites),
        "limite_texto": texto_limite(limites),
        "limite_min": limites.minimo,
        "limite_max": limites.maximo,
        "norma": limites.norma,
        "origen_limites": limites.origen,
        "limite_deteccion": limites.deteccion,
        "evaluacion": str(evaluacion),
        "evaluacion_texto": str(evaluacion.label),
    }


def armar_contenido(estudio):
    """Datos del laboratorio, del cliente, de la muestra, del estudio y de cada prueba."""
    muestra = estudio.muestra
    cliente = muestra.cliente
    asignaciones = (
        estudio.pruebas_asignadas.select_related("prueba", "resultado")
        .prefetch_related(
            "prueba__limites_vertido",
            Prefetch(
                "validaciones",
                queryset=Validacion.objects.filter(anulada=False),
                to_attr="validaciones_vigentes",
            ),
        )
        .order_by("prueba__codigo", "pk")
    )
    return {
        "laboratorio": {clave: str(valor) for clave, valor in settings.AQUALAB_LABORATORIO.items()},
        "cliente": {
            "nombre_completo": cliente.nombre_completo,
            "tipo_documento": cliente.tipo_documento,
            "numero_documento": cliente.numero_documento,
            "domicilio": cliente.domicilio,
            "email": cliente.email,
        },
        "muestra": {
            "numero_pi": str(muestra.numero_pi),
            "nombre": muestra.nombre,
            "origen": muestra.origen.nombre,
            "fecha_muestreo": muestra.fecha_muestreo.strftime(FORMATO_FECHA),
            "fecha_ingreso": muestra.fecha_ingreso.strftime(FORMATO_FECHA),
            "sitio_extraccion": muestra.sitio_extraccion,
            "responsable_muestreo": muestra.responsable_muestreo,
            "tipo_vertido": muestra.get_tipo_vertido_display(),
        },
        "estudio": {"numero": str(estudio.pk), "tipo": estudio.tipo_nombre_snapshot},
        "pruebas": [
            armar_prueba(a, muestra.tipo_vertido)
            for a in asignaciones
            if calculo.tiene_resultado(a)
        ],
    }
