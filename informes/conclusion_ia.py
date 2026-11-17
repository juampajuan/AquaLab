import json
import threading
import time
from dataclasses import dataclass
from queue import Empty, Queue

from asistente import cliente_ia, configuracion

LIMITE_BYTES = 64 * 1024
_capacidad = threading.BoundedSemaphore(2)
CIERRES = {
    "T1": "Todas las pruebas del estudio son evaluables y cumplen según sus validaciones vigentes.",
    "T2": "Las validaciones vigentes de todas las pruebas evaluables del estudio indican "
    "cumplimiento; no hay pruebas no evaluables.",
    "I1": "Se identifican las pruebas fuera de norma detalladas en esta conclusión.",
    "I2": "Las validaciones vigentes registran los incumplimientos indicados.",
    "P1": "Conclusión parcial: existen pruebas no evaluables por la información insuficiente "
    "indicada en las advertencias.",
    "P2": "La información disponible permite una conclusión parcial; las pruebas no evaluables "
    "y sus motivos se detallan en las advertencias.",
}
POR_CLASE = {
    "todas_cumplen": ("T1", "T2"),
    "con_incumplimientos": ("I1", "I2"),
    "parcial": ("P1", "P2"),
}


@dataclass(frozen=True)
class Propuesta:
    texto: str
    origen: str
    motivo: str = ""


def incumplimientos(hechos):
    return [p for p in hechos["pruebas"] if p["clase_conclusion"] == "fuera_de_norma"]


def frase(prueba, patron):
    valor = " ".join(filter(None, (prueba["resultado_texto"], prueba["unidad"])))
    identidad = f"{prueba['codigo']} — {prueba['nombre']}"
    if patron == "F1":
        return (
            f"{identidad}: {valor}; límite aplicado: {prueba['limite_texto']}; "
            f"norma: {prueba['norma']}. La validación vigente indica fuera de norma."
        )
    return (
        f"La prueba {identidad} está fuera de norma según su validación vigente: "
        f"valor obtenido {valor}, límite aplicado {prueba['limite_texto']}, "
        f"norma {prueba['norma']}."
    )


def plantilla(hechos):
    return "\n\n".join(
        [*(frase(p, "F1") for p in incumplimientos(hechos)), CIERRES[POR_CLASE[hechos["clase"]][0]]]
    )


def mensajes_para(hechos):
    datos = {
        "version": "1",
        "clase": hechos["clase"],
        "hechos": [f"h{i}" for i, _ in enumerate(incumplimientos(hechos), 1)],
    }
    return [
        {
            "role": "system",
            "content": (
                'Seleccioná variantes de redacción. Respondé solo JSON de claves version="1", '
                'bloques=[{"hecho":"h1","redaccion":"F1"}] y cierre. Incluí cada referencia '
                "exactamente una vez; redaccion F1 o F2. Cierre T1/T2 para todas_cumplen, "
                "I1/I2 para con_incumplimientos, P1/P2 para parcial. "
                "Sin datos ni claves adicionales."
            ),
        },
        {"role": "user", "content": json.dumps(datos, ensure_ascii=False)},
    ]


def interpretar(mensaje, hechos):
    if not isinstance(mensaje, dict) or set(mensaje) - {"role", "content", "refusal"}:
        raise ValueError
    if mensaje.get("refusal"):
        raise ValueError
    contenido = mensaje.get("content")
    if not isinstance(contenido, str):
        raise ValueError
    if len(contenido.encode("utf-8")) > LIMITE_BYTES:
        raise OverflowError
    datos = json.loads(contenido)
    if not isinstance(datos, dict) or set(datos) != {"version", "bloques", "cierre"}:
        raise ValueError
    if datos["version"] != "1" or datos["cierre"] not in POR_CLASE[hechos["clase"]]:
        raise ValueError
    pruebas = incumplimientos(hechos)
    if not isinstance(datos["bloques"], list) or len(datos["bloques"]) != len(pruebas):
        raise ValueError
    patrones = {}
    referencias = {f"h{i}" for i in range(1, len(pruebas) + 1)}
    for bloque in datos["bloques"]:
        if not isinstance(bloque, dict) or set(bloque) != {"hecho", "redaccion"}:
            raise ValueError
        ref, patron = bloque["hecho"], bloque["redaccion"]
        if (
            not isinstance(ref, str)
            or ref not in referencias
            or ref in patrones
            or patron not in ("F1", "F2")
        ):
            raise ValueError
        patrones[ref] = patron
    return "\n\n".join(
        [*(frase(p, patrones[f"h{i}"]) for i, p in enumerate(pruebas, 1)), CIERRES[datos["cierre"]]]
    )


def proponer(hechos, *, config=None):
    config = config or configuracion.actual()

    def respaldo(motivo):
        return Propuesta(plantilla(hechos), "plantilla", motivo)

    if not config.habilitado:
        return respaldo("sin_configuracion")
    mensajes = mensajes_para(hechos)
    if len(json.dumps(mensajes, ensure_ascii=False).encode("utf-8")) > LIMITE_BYTES:
        return respaldo("tamano")
    limite = time.monotonic() + config.presupuesto
    if config.presupuesto <= 0:
        return respaldo("plazo")
    capacidad = _capacidad
    if not capacidad.acquire(blocking=False):
        return respaldo("capacidad")
    resultados = Queue(maxsize=1)
    timeout = min(config.timeout, config.presupuesto)

    def llamar():
        try:
            resultados.put((cliente_ia.enviar(mensajes, [], timeout, config=config), ""))
        except cliente_ia.CuotaAgotada:
            resultados.put((None, "cuota"))
        except Exception:
            resultados.put((None, "no_disponible"))
        finally:
            capacidad.release()

    try:
        threading.Thread(target=llamar, daemon=True).start()
    except RuntimeError:
        capacidad.release()
        return respaldo("capacidad")
    try:
        mensaje, motivo = resultados.get(timeout=max(0, limite - time.monotonic()))
    except Empty:
        return respaldo("plazo")
    if motivo:
        return respaldo(motivo)
    try:
        return Propuesta(interpretar(mensaje, hechos), "ia")
    except OverflowError:
        return respaldo("tamano")
    except (ValueError, TypeError, KeyError):
        return respaldo("respuesta_invalida")
