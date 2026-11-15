"""Configuración del asistente (US 10.1, data-model.md), desde `settings.ASISTENTE`.

Se lee en cada pedido (`actual()`) para que los tests la cambien con `settings`.
"""

from dataclasses import dataclass

from django.conf import settings

URL_GROQ = "https://api.groq.com/openai/v1/chat/completions"
MODELO_POR_DEFECTO = "openai/gpt-oss-120b"


@dataclass(frozen=True)
class Configuracion:
    clave: str
    url: str
    modelo: str
    timeout: float = 15  # segundos por llamada, recortado a lo que queda del presupuesto
    presupuesto: float = 20  # segundos por pregunta (SC-007)
    max_vueltas: int = 6  # vueltas con herramientas, más la llamada final de texto
    max_herramientas: int = 8  # ejecuciones por pregunta

    @property
    def habilitado(self):
        return bool(self.clave)


def actual():
    datos = getattr(settings, "ASISTENTE", {}) or {}
    return Configuracion(
        clave=datos.get("clave") or "",
        url=datos.get("url") or URL_GROQ,
        modelo=datos.get("modelo") or MODELO_POR_DEFECTO,
    )
