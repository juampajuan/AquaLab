"""Importación del catálogo de pruebas y sus límites por tipo de vertido (SCRUM-64).

Primero se valida todo sin escribir; si no hay errores, se guarda en una sola transacción.
"""

import csv
from dataclasses import dataclass, field

from django.core.exceptions import ValidationError
from django.db import transaction

from estudios.models import PruebaEstudio, TipoEstudioPrueba

from .models import LimiteVertido, Prueba, TipoCalculo, TipoVertido, referencias_formula

COLUMNAS_CATALOGO = (
    "codigo",
    "nombre",
    "unidad",
    "unidad_medicion",
    "tipo_calculo",
    "formula",
    "es_calculada",
    "norma",
    "limite_min",
    "limite_max",
    "limite_deteccion",
    "activa",
    "observacion",
)
COLUMNAS_LIMITES = ("codigo", "tipo_vertido", "limite_min", "limite_max", "norma")
CAMPOS_PRUEBA = tuple(c for c in COLUMNAS_CATALOGO if c not in ("codigo", "es_calculada", "activa"))
CAMPOS_LIMITE = ("limite_min", "limite_max", "norma")


class ErrorImportacion(Exception):
    def __init__(self, errores):
        super().__init__("\n".join(errores))
        self.errores = errores


@dataclass
class Resumen:
    pruebas_creadas: int = 0
    pruebas_actualizadas: int = 0
    limites_creados: int = 0
    limites_actualizados: int = 0
    avisos: list[str] = field(default_factory=list)


def leer(ruta, columnas, errores):
    """Filas del CSV como (número de línea, valores sin espacios laterales)."""
    try:
        with open(ruta, encoding="utf-8-sig", newline="") as archivo:
            lector = csv.DictReader(archivo)
            faltantes = [c for c in columnas if c not in (lector.fieldnames or ())]
            if faltantes:
                errores.append(f"{ruta.name}: faltan las columnas: {', '.join(faltantes)}.")
                return []
            return [
                (lector.line_num, {c: (fila[c] or "").strip() for c in columnas}) for fila in lector
            ]
    except (OSError, UnicodeDecodeError, csv.Error):
        errores.append(f"no se puede leer {ruta}.")
        return []


def anotar(errores, ruta, linea, motivo):
    errores.append(f"{ruta.name}, línea {linea}: {motivo}.")


def motivos(error):
    return "; ".join(mensaje.rstrip(".") for mensaje in error.messages)


def preparar_pruebas(filas, ruta, existentes, en_uso, errores, avisos):
    pruebas = {}
    lineas = {}
    for linea, fila in filas:
        codigo = fila["codigo"]
        if codigo in lineas:
            anotar(
                errores,
                ruta,
                linea,
                f"el código «{codigo}» está repetido (también en la línea {lineas[codigo]})",
            )
            continue
        lineas[codigo] = linea
        validos = True
        if fila["tipo_calculo"] not in TipoCalculo.values:
            anotar(
                errores,
                ruta,
                linea,
                f"tipo de cálculo «{fila['tipo_calculo']}» inválido (DIRECTO o FORMULA)",
            )
            validos = False
        for columna in ("es_calculada", "activa"):
            if fila[columna].lower() not in ("si", "no"):
                anotar(errores, ruta, linea, f"{columna}: «{fila[columna]}» inválido (si o no)")
                validos = False
        if not validos:
            continue

        prueba = existentes.get(codigo) or Prueba(codigo=codigo)
        guardado = prueba.nombre
        for campo in CAMPOS_PRUEBA:
            setattr(prueba, campo, fila[campo])
        prueba.es_calculada = fila["es_calculada"].lower() == "si"
        prueba.activa = fila["activa"].lower() == "si"
        if prueba.pk in en_uso and prueba.nombre != guardado:
            avisos.append(
                f"Aviso: la prueba {codigo} está en uso; se conserva el nombre «{guardado}» "
                f"(el archivo dice «{prueba.nombre}»)."
            )
            prueba.nombre = guardado
        try:
            prueba.full_clean(validate_unique=False)
        except ValidationError as e:
            anotar(errores, ruta, linea, motivos(e))
            continue
        pruebas[codigo] = (linea, prueba)
    return pruebas


def preparar_limites(filas, ruta, codigos, actuales, errores):
    limites = []
    vistos = set()
    for linea, fila in filas:
        codigo, tipo = fila["codigo"], fila["tipo_vertido"]
        if tipo not in TipoVertido.values:
            anotar(errores, ruta, linea, f"tipo de vertido «{tipo}» inválido (cloacal o canal)")
            continue
        if codigo not in codigos:
            anotar(errores, ruta, linea, f"la prueba «{codigo}» no existe en el catálogo")
            continue
        if (codigo, tipo) in vistos:
            anotar(errores, ruta, linea, f"límite repetido para «{codigo}» ({tipo})")
            continue
        vistos.add((codigo, tipo))
        limite = actuales.get((codigo, tipo)) or LimiteVertido(tipo_vertido=tipo)
        for campo in CAMPOS_LIMITE:
            setattr(limite, campo, fila[campo])
        try:
            limite.full_clean(exclude=["prueba"], validate_unique=False)
        except ValidationError as e:
            anotar(errores, ruta, linea, motivos(e))
            continue
        limites.append((codigo, limite))
    return limites


def importar(ruta_catalogo, ruta_limites):
    errores = []
    filas_catalogo = leer(ruta_catalogo, COLUMNAS_CATALOGO, errores)
    filas_limites = leer(ruta_limites, COLUMNAS_LIMITES, errores)
    existentes = {p.codigo: p for p in Prueba.objects.all()}
    en_uso = set(TipoEstudioPrueba.objects.values_list("prueba_id", flat=True)) | set(
        PruebaEstudio.objects.values_list("prueba_id", flat=True)
    )
    resumen = Resumen()

    pruebas = preparar_pruebas(
        filas_catalogo, ruta_catalogo, existentes, en_uso, errores, resumen.avisos
    )
    # Catálogo resultante: lo que ya hay en la base más lo que trae el archivo.
    codigos = set(existentes) | {fila["codigo"] for _linea, fila in filas_catalogo}
    for linea, prueba in pruebas.values():
        for codigo in sorted(referencias_formula(prueba.formula) - codigos):
            anotar(
                errores,
                ruta_catalogo,
                linea,
                f"la fórmula referencia «{codigo}», que no existe en el catálogo",
            )
    actuales = {
        (limite.prueba.codigo, limite.tipo_vertido): limite
        for limite in LimiteVertido.objects.select_related("prueba")
    }
    limites = preparar_limites(filas_limites, ruta_limites, codigos, actuales, errores)

    if errores:
        raise ErrorImportacion(errores)

    with transaction.atomic():
        for _linea, prueba in pruebas.values():
            nueva = prueba.pk is None
            prueba.save()
            if nueva:
                resumen.pruebas_creadas += 1
            else:
                resumen.pruebas_actualizadas += 1
        for codigo, limite in limites:
            nuevo = limite.pk is None
            limite.prueba = pruebas[codigo][1] if codigo in pruebas else existentes[codigo]
            limite.save()
            if nuevo:
                resumen.limites_creados += 1
            else:
                resumen.limites_actualizados += 1
    return resumen
