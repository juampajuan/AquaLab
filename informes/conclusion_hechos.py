import hashlib
import json

from django.core.exceptions import ObjectDoesNotExist

from estudios.models import EstadoPruebaEstudio, validaciones_vigentes
from pruebas.limites import Evaluacion, LimitesAplicables, texto_limite

from .contenido import con_coma, texto_resultado

MOTIVOS = {
    "sin_validacion": "sin validación vigente",
    "sin_resultado": "sin resultado disponible",
    "sin_limite_comparable": "sin límite comparable",
    "sin_norma": "sin norma registrada",
}


class FuentesAmbiguas(Exception):
    pass


def asignaciones(estudio):
    return (
        estudio.pruebas_asignadas.select_related("prueba", "resultado")
        .prefetch_related(validaciones_vigentes())
        .order_by("prueba__codigo", "pk")
    )


def recolectar(estudio):
    return desde_asignaciones(estudio.pk, asignaciones(estudio))


def desde_asignaciones(estudio_id, filas):
    pruebas = [hechos_de_prueba(fila) for fila in filas]
    pruebas.sort(key=lambda p: (p["codigo"], int(p["asignacion_id"])))
    if not pruebas or any(p["motivos"] for p in pruebas):
        clase = "parcial"
    elif any(p["evaluacion"] == Evaluacion.FUERA_DE_NORMA for p in pruebas):
        clase = "con_incumplimientos"
    else:
        clase = "todas_cumplen"
    return {"schema": "1", "estudio_id": str(estudio_id), "pruebas": pruebas, "clase": clase}


def hechos_de_prueba(asignacion):
    prueba = asignacion.prueba
    vigentes = asignacion.validaciones_vigentes
    if len(vigentes) > 1:
        raise FuentesAmbiguas("Hay más de una validación vigente para una prueba.")
    vigente = (
        vigentes[0] if vigentes and asignacion.estado == EstadoPruebaEstudio.COMPLETADA else None
    )
    try:
        resultado = asignacion.resultado
    except ObjectDoesNotExist:
        resultado = None
    hechos = {
        "asignacion_id": str(asignacion.pk),
        "prueba_id": str(prueba.pk),
        "codigo": prueba.codigo,
        "nombre": prueba.nombre,
        "estado_asignacion": asignacion.estado,
        "resultado_id": str(resultado.pk) if resultado else "",
        "fecha_calculo": resultado.fecha_calculo.isoformat() if resultado else "",
        "valor": str(resultado.valor) if resultado else "",
        "unidad": resultado.unidad if resultado else "",
        "formula": resultado.formula if resultado else "",
        "curva_id": str(resultado.curva_id) if resultado and resultado.curva_id else "",
        "validacion_id": str(vigente.pk) if vigente else "",
        "fecha_validacion": vigente.fecha_validacion.isoformat() if vigente else "",
        "limite_min": vigente.limite_min if vigente else "",
        "limite_max": vigente.limite_max if vigente else "",
        "norma": vigente.norma if vigente else "",
        "origen_limites": vigente.origen_limites if vigente else "",
        "evaluacion": vigente.evaluacion if vigente else "",
        "ld_auxiliar": prueba.limite_deteccion if vigente else "",
        "resultado_texto": con_coma(resultado.valor_mostrado) if resultado else "",
        "limite_texto": "",
    }
    motivos = []
    if vigente is None:
        motivos.append("sin_validacion")
    if resultado is None:
        motivos.append("sin_resultado")
    if vigente:
        limites = LimitesAplicables(
            vigente.limite_min,
            vigente.limite_max,
            vigente.norma,
            vigente.origen_limites,
            prueba.limite_deteccion,
        )
        hechos["limite_texto"] = texto_limite(limites)
        if resultado:
            hechos["resultado_texto"] = texto_resultado(resultado, limites)
        if vigente.evaluacion == Evaluacion.SIN_LIMITE:
            motivos.append("sin_limite_comparable")
        if not vigente.norma.strip():
            motivos.append("sin_norma")
    hechos["motivos"] = motivos
    hechos["clase_conclusion"] = "no_evaluable" if motivos else hechos["evaluacion"]
    return hechos


def huella(hechos):
    serializado = json.dumps(hechos, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(serializado.encode("utf-8")).hexdigest()


def advertencias(hechos):
    textos = []
    for prueba in hechos["pruebas"]:
        if not prueba["motivos"]:
            continue
        conocidos = []
        for etiqueta, valor in (
            (
                "valor obtenido",
                " ".join(filter(None, (prueba["resultado_texto"], prueba["unidad"]))),
            ),
            ("límite aplicado", prueba["limite_texto"]),
            ("norma", prueba["norma"]),
            ("evaluación registrada", prueba["evaluacion"]),
        ):
            if valor:
                conocidos.append(f"{etiqueta}: {valor}")
        motivo = ", ".join(MOTIVOS[m] for m in prueba["motivos"])
        texto = f"{prueba['codigo']} — {prueba['nombre']}: no evaluable ({motivo})."
        if conocidos:
            texto += " Hechos disponibles: " + "; ".join(conocidos) + "."
        textos.append(texto)
    return textos


def texto_final(editorial, avisos):
    if not avisos:
        return editorial
    bloque = "Advertencias de información insuficiente:\n" + "\n".join(avisos)
    return editorial + "\n\n" + bloque if editorial else bloque
