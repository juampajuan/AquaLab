"""«Volver» de las fichas (SCRUM-82): recuerda de qué pantalla se llegó a cada ficha.

Se toma el Referer cuando es una pantalla de navegación (listas, fichas, inicio, dashboard).
Las pantallas propias de la ficha (cargar, validar, editar, comparación, informe…) y los
formularios de alta no cuentan: al volver de ellas se mantiene el origen ya recordado.
Excepción: los enlaces del informe (borrador o emitido) llevan `?desde=informe`, y entonces
«Volver» regresa a ese informe.
"""

from urllib.parse import urlsplit

CLAVE_SESION = "volver"
MAXIMO_RECORDADOS = 50

# Pantallas que no son un origen: formularios, confirmaciones y subpantallas de una ficha.
PARTES_EXCLUIDAS = (
    "/crear",
    "/registrar",
    "/confirmar",
    "/editar",
    "/comparacion/",
    "/informes/estudios/",
    "/mediciones/",
    "/resultados/",
    "/pruebas/agregar",
    "/quitar/",
)


def _es_origen(ruta, ficha):
    if ruta.startswith(ficha):
        return False
    return not any(parte in ruta for parte in PARTES_EXCLUIDAS)


def _guardar(request, recordados):
    while len(recordados) > MAXIMO_RECORDADOS:
        recordados.pop(next(iter(recordados)))
    request.session[CLAVE_SESION] = recordados


def url_volver(request, por_defecto):
    """Devuelve a dónde lleva «Volver» desde esta ficha y recuerda el origen en la sesión."""
    ficha = request.path
    anterior = f"{ficha}|anterior"
    recordados = request.session.get(CLAVE_SESION, {})
    referer = urlsplit(request.META.get("HTTP_REFERER", ""))
    if referer.netloc == request.get_host() and referer.path:
        ruta = referer.path
        destino = ruta + (f"?{referer.query}" if referer.query else "")
        actual = recordados.get(ficha, "")
        # Si se llega con «Volver» desde una ficha cuyo origen es esta, no se pisa el origen.
        es_regreso = urlsplit(recordados.get(ruta, "")).path == ficha
        desde_informe = request.GET.get("desde") == "informe" and ruta.startswith(
            "/informes/estudios/"
        )
        if desde_informe and urlsplit(actual).path != ruta:
            # Se entra desde un enlace del informe: «Volver» regresa al informe y se guarda el
            # origen que tenía la ficha para retomarlo después.
            recordados.pop(anterior, None)
            if actual:
                recordados[anterior] = actual
            recordados.pop(ficha, None)
            recordados[ficha] = destino
            _guardar(request, recordados)
        elif not desde_informe and urlsplit(actual).path == ruta and "/informes/" in ruta:
            # Se vuelve a la ficha desde ese mismo informe: se retoma el origen anterior.
            if anterior in recordados:
                recordados[ficha] = recordados.pop(anterior)
            else:
                recordados.pop(ficha)
            _guardar(request, recordados)
        elif not desde_informe and _es_origen(ruta, ficha) and not es_regreso:
            recordados.pop(anterior, None)
            recordados.pop(ficha, None)
            recordados[ficha] = destino
            _guardar(request, recordados)
    return recordados.get(ficha, por_defecto)
