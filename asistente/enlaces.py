"""Enlaces de las respuestas (research R8). Los arma AquaLab con `reverse` a partir de lo que
devolvieron las herramientas; el modelo nunca escribe URLs."""

import re
import unicodedata
from dataclasses import dataclass

from django.urls import reverse

VISTAS = {
    "muestra": "muestras:detalle",
    "estudio": "estudios:detalle",
    "cliente": "clientes:detalle",
    "historial": "clientes:historial",
    "informe": "informes:ver",  # con el pk del estudio
}
MAX_ENLACES = 10


@dataclass(frozen=True)
class Referencia:
    tipo: str
    pk: int
    etiqueta: str
    # Textos que, si aparecen en la respuesta, la mencionan («PI 200417», «200417»). Por
    # defecto, la etiqueta.
    claves: tuple = ()

    def __post_init__(self):
        if self.tipo not in VISTAS:
            raise ValueError(f"Tipo de referencia desconocido: {self.tipo}")

    @property
    def clave(self):
        return (self.tipo, self.pk)

    def url(self):
        return reverse(VISTAS[self.tipo], args=[self.pk])

    def enlace(self):
        return {"etiqueta": self.etiqueta, "url": self.url()}


def normalizar(texto):
    sin_acentos = unicodedata.normalize("NFKD", texto or "")
    return "".join(c for c in sin_acentos if not unicodedata.combining(c)).casefold()


def posicion(texto, referencia):
    """Primera aparición de alguna clave de la referencia en el texto, o None."""
    normal = normalizar(texto)
    posiciones = []
    for clave in referencia.claves or (referencia.etiqueta,):
        clave = normalizar(clave).strip()
        if not clave:
            continue
        # Bordes de palabra: «200417» no coincide dentro de «2004170».
        encontrada = re.search(rf"(?<!\w){re.escape(clave)}(?!\w)", normal)
        if encontrada:
            posiciones.append(encontrada.start())
    return min(posiciones) if posiciones else None


def sin_duplicados(referencias):
    vistas, unicas = set(), []
    for referencia in referencias:
        if referencia.clave not in vistas:
            vistas.add(referencia.clave)
            unicas.append(referencia)
    return unicas


def elegir_enlaces(texto, referencias, ultimas, primeras=()):
    """Las referencias mencionadas en `texto`, en orden de aparición; si ninguna, las de la última
    herramienta. `primeras` van adelante siempre. Sin duplicados y como mucho 10."""
    mencionadas = [
        (pos, i, r)
        for i, r in enumerate(sin_duplicados(referencias))
        if (pos := posicion(texto, r)) is not None
    ]
    elegidas = [r for _, _, r in sorted(mencionadas, key=lambda t: (t[0], t[1]))]
    if not elegidas:
        elegidas = list(ultimas)
    return [r.enlace() for r in sin_duplicados([*primeras, *elegidas])[:MAX_ENLACES]]
