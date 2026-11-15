"""Lectura de los puntos de una curva desde un archivo .csv o .xlsx (US 6.6, research R8).

`leer_archivo` devuelve la tabla como textos; `detectar_columnas` busca las columnas de
concentración y absorbancia por sus encabezados; `extraer_puntos` lee las filas con la misma regla
que las mediciones (`leer_valor`). Cualquier problema es `ArchivoInvalido` con el motivo que ve el
usuario, y entonces no se carga ningún punto. El archivo no se guarda: solo su nombre.
"""

import csv
import io
import unicodedata
import zipfile
from decimal import ROUND_HALF_UP, Decimal

from django.core.exceptions import ValidationError

from estudios.mediciones import leer_valor

from .curvas import MAXIMO_PUNTOS, MINIMO_PUNTOS

EXTENSIONES = (".csv", ".xlsx")
TAMANO_MAXIMO = 1024 * 1024  # 1 MB
MAXIMO_FILAS = 1000
FILAS_VISTA_PREVIA = 5
SEIS_DECIMALES = Decimal("1E-6")
SEPARADORES = ";,\t"
PLANTILLA = [("0", "0,000"), ("0,1", "0,052"), ("0,2", "0,101"), ("0,3", "0,153"), ("0,4", "0,199")]


class ArchivoInvalido(Exception):
    """El archivo no se puede usar; el mensaje es el motivo que ve el usuario."""


def leer_archivo(archivo):
    """La tabla del archivo subido: lista de filas, cada una lista de textos."""
    nombre = (archivo.name or "").lower()
    if not nombre.endswith(EXTENSIONES):
        raise ArchivoInvalido("Solo se aceptan archivos .csv o .xlsx.")
    if archivo.size > TAMANO_MAXIMO:
        raise ArchivoInvalido("El archivo supera 1 MB.")
    contenido = archivo.read()
    if not contenido:
        raise ArchivoInvalido("El archivo está vacío.")
    try:
        filas = _leer_csv(contenido) if nombre.endswith(".csv") else _leer_xlsx(contenido)
    except ArchivoInvalido:
        raise
    except Exception as exc:  # openpyxl y csv lanzan errores muy variados ante un archivo roto
        raise ArchivoInvalido("No se pudo leer el archivo.") from exc
    if not any(any(celda for celda in fila) for fila in filas):
        raise ArchivoInvalido("El archivo está vacío.")
    return filas


def _leer_csv(contenido):
    try:
        texto = contenido.decode("utf-8-sig")
    except UnicodeDecodeError:
        texto = contenido.decode("latin-1")
    try:
        dialecto = csv.Sniffer().sniff(texto[:4096], delimiters=SEPARADORES)
        separador = dialecto.delimiter
    except csv.Error:
        separador = ";"
    filas = []
    for fila in csv.reader(io.StringIO(texto), delimiter=separador):
        filas.append([celda.strip() for celda in fila])
        if len(filas) > MAXIMO_FILAS + 1:
            break
    return _limitar(filas)


def _leer_xlsx(contenido):
    from openpyxl import load_workbook

    if not zipfile.is_zipfile(io.BytesIO(contenido)):
        raise ArchivoInvalido("No se pudo leer el archivo.")
    libro = load_workbook(io.BytesIO(contenido), read_only=True, data_only=True)
    try:
        hoja = libro.worksheets[0]
        filas = []
        for fila in hoja.iter_rows(values_only=True):
            filas.append([_texto_celda(celda) for celda in fila])
            if len(filas) > MAXIMO_FILAS + 1:
                break
    finally:
        libro.close()
    return _limitar(filas)


def _texto_celda(celda):
    """Texto de una celda de Excel. Los números llegan como `float`: es el único `float` de la
    historia y se pasa a `Decimal` (6 decimales) antes de cualquier cálculo (principio IV)."""
    if celda is None:
        return ""
    if isinstance(celda, bool):
        return str(celda)
    if isinstance(celda, int):
        return str(celda)
    if isinstance(celda, float):
        valor = Decimal(repr(celda)).quantize(SEIS_DECIMALES, ROUND_HALF_UP).normalize()
        return f"{valor:f}"
    return str(celda).strip()


def _limitar(filas):
    while filas and not any(filas[-1]):
        filas.pop()
    if len(filas) > MAXIMO_FILAS:
        raise ArchivoInvalido("El archivo tiene más de 1000 filas.")
    return filas


def _normalizado(texto):
    sin_tildes = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return sin_tildes.strip().lower()


def detectar_columnas(tabla):
    """(columna de concentración, columna de absorbancia) según los encabezados, o None si no se
    pueden identificar sin dudas (no hay encabezados reconocibles o hay más de una candidata)."""
    for fila in tabla:
        textos = [_normalizado(celda) for celda in fila]
        concentraciones = [i for i, t in enumerate(textos) if t.startswith("conc")]
        absorbancias = [i for i, t in enumerate(textos) if t.startswith("abs")]
        if concentraciones and absorbancias:
            if len(concentraciones) == 1 and len(absorbancias) == 1:
                return concentraciones[0], absorbancias[0]
            return None
    return None


def vista_previa(tabla):
    """Columnas («Columna A»…) y las primeras filas con contenido, para elegir las columnas."""
    ancho = max((len(fila) for fila in tabla), default=0)
    columnas = [(i, f"Columna {_letra(i)}") for i in range(ancho)]
    filas = [fila + [""] * (ancho - len(fila)) for fila in tabla if any(fila)]
    return {"columnas": columnas, "filas": filas[:FILAS_VISTA_PREVIA]}


def _letra(indice):
    letras = ""
    indice += 1
    while indice:
        indice, resto = divmod(indice - 1, 26)
        letras = chr(65 + resto) + letras
    return letras


def extraer_puntos(tabla, columnas):
    """Los puntos [(concentración, absorbancia)] como textos de `Decimal` ("0.052").

    Ignora las filas sin ningún número en esas dos columnas (títulos, vacías, textos). Una fila
    con un solo valor, o con un valor que no es un número válido o es negativo, es un error con
    el número de fila del archivo.
    """
    concentracion, absorbancia = columnas
    if concentracion == absorbancia:
        raise ArchivoInvalido("Elegí dos columnas distintas.")
    puntos = []
    for numero, fila in enumerate(tabla, start=1):
        textos = [fila[i].strip() if i < len(fila) else "" for i in (concentracion, absorbancia)]
        valores = [_numero(t) for t in textos]
        if all(v is None for v in valores):
            continue  # título, fila vacía o celdas con texto
        for texto, valor, falta in zip(
            textos, valores, ("concentración", "absorbancia"), strict=True
        ):
            if not texto:
                raise ArchivoInvalido(f"La fila {numero} no tiene {falta}.")
            if valor is None or valor < 0:
                raise ArchivoInvalido(f"La fila {numero} tiene un valor inválido: «{texto}».")
        puntos.append(tuple(str(v) for v in valores))
        if len(puntos) > MAXIMO_PUNTOS:
            raise ArchivoInvalido(f"El archivo trae más de {MAXIMO_PUNTOS} puntos.")
    if len(puntos) < MINIMO_PUNTOS:
        raise ArchivoInvalido(
            f"El archivo trae {len(puntos)} puntos válidos: hacen falta al menos {MINIMO_PUNTOS}."
        )
    return puntos


def _numero(texto):
    """El número escrito (coma o punto), o None si la celda está vacía o no es un número."""
    if not texto:
        return None
    try:
        return leer_valor(texto)
    except ValidationError:
        return None


def plantilla():
    """CSV de ejemplo: UTF-8 con BOM, punto y coma y coma decimal (abre bien en Excel)."""
    lineas = ["Concentración;Absorbancia"] + [f"{c};{a}" for c, a in PLANTILLA]
    return "﻿" + "\r\n".join(lineas) + "\r\n"
