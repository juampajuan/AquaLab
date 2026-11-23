"""Enlaces de las respuestas (research R8). Los arma AquaLab con `reverse` a partir de lo que
devolvieron las herramientas; el modelo nunca escribe URLs."""

import re
import unicodedata
from dataclasses import dataclass
from urllib.parse import urlencode

from django.urls import reverse

VISTAS = {
    "muestra": "muestras:detalle",
    "estudio": "estudios:detalle",
    "cliente": "clientes:detalle",
    "historial": "clientes:historial",
    "informe": "informes:ver",  # con el pk del estudio
    # Formularios precargados (US 10.3): sin pk, con `parametros` como valores iniciales.
    "registrar_muestra": "muestras:registrar",
    "crear_estudio": "estudios:crear",
    "registrar_cliente": "clientes:registrar",
    # Opción para elegir que no tiene pantalla (un origen, un tipo): un botón sin URL.
    "opcion": None,
}
MAX_ENLACES = 10


@dataclass(frozen=True)
class Referencia:
    tipo: str
    pk: int | None
    etiqueta: str
    # Textos que, si aparecen en la respuesta, la mencionan («PI 200417», «200417»). Por
    # defecto, la etiqueta.
    claves: tuple = ()
    # Expresión regular sobre el texto normalizado (sin acentos, minúsculas) para menciones con
    # formas variables, como «estudio n.º 42» o «#42».
    patron: str = ""
    # Opción para elegir entre coincidencias (T053): el panel la muestra como un botón que manda
    # esta pregunta de seguimiento, con «Ver ficha» para abrir la pantalla. La pone AquaLab.
    pregunta: str = ""
    # Querystring del formulario precargado (US 10.3): pares (nombre, valor).
    parametros: tuple = ()
    # El panel se minimiza al seguir el enlace, para no tapar el formulario (US 10.3, R7).
    minimizar: bool = False

    def __post_init__(self):
        if self.tipo not in VISTAS:
            raise ValueError(f"Tipo de referencia desconocido: {self.tipo}")

    @property
    def clave(self):
        return (self.tipo, self.pk, self.parametros, self.pregunta if self.pk is None else "")

    def url(self):
        vista = VISTAS[self.tipo]
        if vista is None:
            return None
        url = reverse(vista) if self.pk is None else reverse(vista, args=[self.pk])
        return f"{url}?{urlencode(self.parametros)}" if self.parametros else url

    def enlace(self):
        enlace = {"etiqueta": self.etiqueta}
        if (url := self.url()) is not None:
            enlace["url"] = url
        if self.pregunta:
            enlace["pregunta"] = self.pregunta
        if self.minimizar:
            enlace["minimizar"] = True
        return enlace


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
    if referencia.patron and (encontrada := re.search(referencia.patron, normal)):
        posiciones.append(encontrada.start())
    return min(posiciones) if posiciones else None


def sin_duplicados(referencias):
    vistas, unicas = set(), []
    for referencia in referencias:
        if referencia.clave not in vistas:
            vistas.add(referencia.clave)
            unicas.append(referencia)
    return unicas


def elegir_enlaces(texto, referencias, ultimas, primeras=(), opciones=()):
    """Las referencias mencionadas en `texto`, en orden de aparición; si ninguna, las de la última
    herramienta. Adelante, siempre, `primeras` y después las `opciones` para elegir de la última
    herramienta. Sin duplicados (gana la primera aparición) y como mucho 10."""
    mencionadas = [
        (pos, i, r)
        for i, r in enumerate(sin_duplicados(referencias))
        if (pos := posicion(texto, r)) is not None
    ]
    elegidas = [r for _, _, r in sorted(mencionadas, key=lambda t: (t[0], t[1]))]
    if not elegidas:
        elegidas = list(ultimas)
    return [r.enlace() for r in sin_duplicados([*primeras, *opciones, *elegidas])[:MAX_ENLACES]]
