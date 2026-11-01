from decimal import Decimal

from estudios.servicios import cargar_mediciones


def asignacion_de(estudio, codigo):
    return estudio.pruebas_asignadas.select_related("prueba").get(prueba__codigo=codigo)


def cargar(estudio, usuario, valores=None, **por_nombre):
    """Carga mediciones por código: `{"CL-": "2.35"}` o `CL_="2.35"` (los _ se leen como -)."""
    por_codigo = {**(valores or {}), **{n.replace("_", "-"): v for n, v in por_nombre.items()}}
    return cargar_mediciones(
        estudio.pk,
        {asignacion_de(estudio, c).pk: Decimal(v) for c, v in por_codigo.items()},
        usuario,
    )


def validar(estudio, usuario, *codigos):
    """Valida por código las pruebas del estudio con el valor de su resultado vigente (US 6.4)."""
    from estudios.servicios import validar_resultados

    elegidas = {}
    for codigo in codigos:
        asignacion = asignacion_de(estudio, codigo)
        elegidas[asignacion.pk] = str(asignacion.resultado.valor)
    return validar_resultados(estudio.pk, elegidas, usuario)
