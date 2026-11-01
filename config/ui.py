from django import template

register = template.Library()

# Color de la etiqueta de cada estado del dominio (FR-009 de la spec 013): un único lugar para
# que el mismo estado se vea igual en todas las pantallas. Valores de ui/estado.html.
TIPOS_DE_ESTADO = {
    # Muestra
    "ingresada": "info",
    # Estudio
    "pendiente_analisis": "warning",
    "en_proceso": "info",
    "finalizado": "success",
    "informe_generado": "success",
    # Prueba de un estudio
    "pendiente": "neutral",
    "cargada": "info",
    "completada": "success",
}


@register.filter
def tipo_estado(valor):
    """Tipo de etiqueta de un estado. Uso: tipo=objeto.estado|tipo_estado en ui/estado.html."""
    return TIPOS_DE_ESTADO.get(valor, "neutral")


@register.filter
def iniciales(texto):
    """Iniciales de dos palabras: "Aguas del Sur S.A." → "AS", "Juan pablo dominguez" → "JP".

    Prefiere las palabras con mayúscula (salta "del", "de", "la"); si hay menos de dos, usa las
    dos primeras palabras.
    """
    palabras = [p for p in str(texto or "").split() if p[:1].isalpha()]
    importantes = [p for p in palabras if p[0].isupper()]
    elegidas = importantes if len(importantes) >= 2 else palabras
    return "".join(p[0] for p in elegidas[:2]).upper()


@register.filter
def unidad(texto):
    """Unidad de una medición o resultado; el catálogo escribe «--» cuando no tiene."""
    texto = (texto or "").strip()
    return "Sin unidad" if texto in ("", "--") else texto
