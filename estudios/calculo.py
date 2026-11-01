"""Cálculo de los resultados de un estudio a partir de sus mediciones y del catálogo."""

from collections import defaultdict
from decimal import ROUND_HALF_UP, Decimal

from pruebas.formulas import CalculoImposible, evaluar_formula
from pruebas.models import Prueba, TipoCalculo, referencias_formula

from .models import EstadoPruebaEstudio, Resultado

DECIMALES = Decimal("1E-10")
MAX_ENTEROS = 18
CIRCULARES = "referencias circulares"


class FaltanDatos(Exception):
    """La prueba todavía no se puede calcular; el mensaje es el motivo que ve el empleado."""


def por_codigo(estudio):
    asignaciones = estudio.pruebas_asignadas.select_related("prueba", "medicion", "resultado")
    return {a.prueba.codigo: a for a in asignaciones}


def tiene_medicion(asignacion):
    return hasattr(asignacion, "medicion")


def tiene_resultado(asignacion):
    return hasattr(asignacion, "resultado")


def listado(codigos):
    nombres = dict(Prueba.objects.filter(codigo__in=codigos).values_list("codigo", "nombre"))
    return ", ".join(f"{c} · {nombres[c]}" if c in nombres else c for c in sorted(codigos))


def calcular(asignacion, todas, valores):
    """Valor del resultado con los resultados `valores` ya obtenidos en el estudio.

    FaltanDatos si espera una medición u otros resultados; CalculoImposible si la fórmula no se
    puede evaluar.
    """
    prueba = asignacion.prueba
    if not prueba.es_calculada and not tiene_medicion(asignacion):
        raise FaltanDatos("Falta la medición.")
    referencias = referencias_formula(prueba.formula)
    if ausentes := referencias - todas.keys():
        raise FaltanDatos(f"No forma parte del estudio: {listado(ausentes)}.")
    if faltantes := referencias - valores.keys():
        raise FaltanDatos(f"Faltan resultados de: {listado(faltantes)}.")
    x = asignacion.medicion.valor if tiene_medicion(asignacion) else None
    if prueba.tipo_calculo == TipoCalculo.DIRECTO:
        valor = x
    else:
        valor = evaluar_formula(prueba.formula, x, {c: valores[c] for c in referencias})
    if valor and valor.adjusted() >= MAX_ENTEROS:
        raise CalculoImposible("el resultado es demasiado grande")
    return valor.quantize(DECIMALES, ROUND_HALF_UP)


def dependientes(todas):
    """Para cada código, las pruebas del estudio cuya fórmula lo referencia."""
    grafo = defaultdict(set)
    for codigo, asignacion in todas.items():
        for referencia in referencias_formula(asignacion.prueba.formula):
            grafo[referencia].add(codigo)
    return grafo


def afectadas(todas, codigos):
    """Los códigos dados y las pruebas del estudio que dependen de ellos, directa o
    indirectamente: lo que cambia si cambian esas mediciones."""
    grafo = dependientes(todas)
    resultado, por_revisar = set(), list(codigos)
    while por_revisar:
        codigo = por_revisar.pop()
        if codigo not in resultado:
            resultado.add(codigo)
            por_revisar.extend(grafo[codigo])
    return resultado


def en_orden(codigos, todas):
    """Orden topológico (Kahn) de `codigos`; devuelve también los que quedan en un ciclo."""
    pendientes = {c: referencias_formula(todas[c].prueba.formula) & codigos for c in codigos}
    orden = []
    listos = sorted(c for c, refs in pendientes.items() if not refs)
    while listos:
        codigo = listos.pop(0)
        orden.append(codigo)
        for otro, refs in pendientes.items():
            if codigo in refs:
                refs.discard(codigo)
                if not refs and otro not in orden and otro not in listos:
                    listos.append(otro)
        listos.sort()
    return orden, sorted(codigos - set(orden))


def en_ciclo(codigo, todas):
    visitados, por_visitar = set(), [codigo]
    while por_visitar:
        actual = por_visitar.pop()
        for referencia in referencias_formula(todas[actual].prueba.formula) & todas.keys():
            if referencia == codigo:
                return True
            if referencia not in visitados:
                visitados.add(referencia)
                por_visitar.append(referencia)
    return False


def recalcular(estudio, asignaciones):
    """Calcula el resultado de las asignaciones dadas y de las calculadas que dependen de ellas.

    Solo toca las afectadas por el cambio, en orden de dependencia. El llamador debe tener el
    estudio bloqueado (select_for_update) dentro de su transacción. Devuelve las pruebas cuya
    fórmula no se pudo evaluar, como pares (prueba, motivo); las que solo esperan otros
    resultados no se informan.
    """
    todas = por_codigo(estudio)
    valores = {c: a.resultado.valor for c, a in todas.items() if tiene_resultado(a)}
    orden, ciclo = en_orden(afectadas(todas, {a.prueba.codigo for a in asignaciones}), todas)
    fallas = []
    for codigo in orden + ciclo:
        asignacion = todas[codigo]
        try:
            if codigo in ciclo:
                raise CalculoImposible(CIRCULARES)
            valor = calcular(asignacion, todas, valores)
        except (FaltanDatos, CalculoImposible) as exc:
            if isinstance(exc, CalculoImposible):
                fallas.append((asignacion.prueba, exc.motivo))
            valores.pop(codigo, None)
            descartar(asignacion)
            continue
        valores[codigo] = valor
        Resultado.objects.update_or_create(
            asignacion=asignacion,
            defaults={
                "valor": valor,
                "unidad": asignacion.prueba.unidad,
                "formula": asignacion.prueba.formula,
            },
        )
        # Un resultado recalculado pierde la validación (excepción al principio IV, plan.md).
        if asignacion.estado != EstadoPruebaEstudio.CARGADA:
            cambiar_estado(asignacion, EstadoPruebaEstudio.CARGADA)
    return fallas


def descartar(asignacion):
    """Una prueba que ya no se puede calcular pierde su resultado; sin medición, vuelve a
    Pendiente."""
    if tiene_resultado(asignacion):
        asignacion.resultado.delete()
    if tiene_medicion(asignacion):
        estado = EstadoPruebaEstudio.CARGADA
    else:
        estado = EstadoPruebaEstudio.PENDIENTE
    if asignacion.estado != estado:
        cambiar_estado(asignacion, estado)


def cambiar_estado(asignacion, estado):
    asignacion.estado = estado
    asignacion.save(update_fields=["estado"])


def motivo_sin_resultado(asignacion, todas):
    """Por qué la prueba no tiene resultado, o None si lo tiene. No escribe nada."""
    if tiene_resultado(asignacion):
        return None
    if en_ciclo(asignacion.prueba.codigo, todas):
        return f"No se pudo calcular: {CIRCULARES}."
    valores = {c: a.resultado.valor for c, a in todas.items() if tiene_resultado(a)}
    try:
        calcular(asignacion, todas, valores)
    except FaltanDatos as exc:
        return str(exc)
    except CalculoImposible as exc:
        return f"No se pudo calcular: {exc.motivo}."
    return None
