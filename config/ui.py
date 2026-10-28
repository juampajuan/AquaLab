from django import template

register = template.Library()


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
