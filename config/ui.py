from django import template

register = template.Library()


@register.filter
def iniciales(texto):
    """Iniciales de las dos primeras palabras con mayúscula: "Aguas del Sur S.A." → "AS"."""
    palabras = [p for p in str(texto or "").split() if p[:1].isalpha()]
    importantes = [p for p in palabras if p[0].isupper()] or palabras
    return "".join(p[0] for p in importantes[:2]).upper()
