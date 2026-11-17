"""Fechas dichas en lenguaje natural (US 10.3, research R4).

Las interpreta AquaLab con la fecha del laboratorio, nunca el modelo: «ayer» depende de qué día
es hoy en el laboratorio. Solo se lee la fecha; las reglas (no futura, muestreo ≤ ingreso) son de
`RegistroMuestraForm`.
"""

import datetime
import re

from .enlaces import normalizar

RELATIVAS = {"hoy": 0, "ayer": 1, "anteayer": 2}
MESES = {
    "enero": 1,
    "febrero": 2,
    "marzo": 3,
    "abril": 4,
    "mayo": 5,
    "junio": 6,
    "julio": 7,
    "agosto": 8,
    "septiembre": 9,
    "setiembre": 9,
    "octubre": 10,
    "noviembre": 11,
    "diciembre": 12,
}
NUMERICA = re.compile(r"(\d{1,2})/(\d{1,2})(?:/(\d{4}))?")
ISO = re.compile(r"(\d{4})-(\d{1,2})-(\d{1,2})")
CON_MES = re.compile(rf"(\d{{1,2}}) de ({'|'.join(MESES)})(?: de (\d{{4}}))?")


def _fecha(anio, mes, dia):
    try:
        return datetime.date(int(anio), int(mes), int(dia))
    except ValueError:
        return None


def leer_fecha(texto, hoy):
    """La fecha que expresa `texto`, o `None` si no se entiende. Sin año, el de `hoy`."""
    normal = normalizar(texto or "").strip()
    normal = re.sub(r"^(el|la)\s+", "", normal).rstrip(" .,;:!?")
    if normal in RELATIVAS:
        return hoy - datetime.timedelta(days=RELATIVAS[normal])
    if encontrada := NUMERICA.fullmatch(normal):
        dia, mes, anio = encontrada.groups()
        return _fecha(anio or hoy.year, mes, dia)
    if encontrada := ISO.fullmatch(normal):
        anio, mes, dia = encontrada.groups()
        return _fecha(anio, mes, dia)
    if encontrada := CON_MES.fullmatch(normal):
        dia, mes, anio = encontrada.groups()
        return _fecha(anio or hoy.year, MESES[mes], dia)
    return None
