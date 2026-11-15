"""Entrada del asistente (data-model.md): la pregunta y el historial que manda el navegador."""

from django import forms

MAX_PREGUNTA = 500
MAX_HISTORIAL = 6
MAX_TEXTO_HISTORIAL = 4000
ROLES = ("usuario", "asistente")
MENSAJE_INVALIDA = "Escribí una pregunta de hasta 500 caracteres."


class PreguntaForm(forms.Form):
    """Recibe el JSON ya decodificado (`datos`). Cualquier problema da el mismo mensaje."""

    pregunta = forms.CharField(max_length=MAX_PREGUNTA)

    def __init__(self, datos):
        datos = datos if isinstance(datos, dict) else {}
        pregunta = datos.get("pregunta")
        super().__init__({"pregunta": pregunta if isinstance(pregunta, str) else ""})
        self.historial_recibido = datos.get("historial", [])

    def clean(self):
        datos = super().clean()
        historial = self.historial_recibido
        if not isinstance(historial, list) or len(historial) > MAX_HISTORIAL:
            raise forms.ValidationError(MENSAJE_INVALIDA)
        limpio = []
        for mensaje in historial:
            if not isinstance(mensaje, dict) or set(mensaje) != {"rol", "texto"}:
                raise forms.ValidationError(MENSAJE_INVALIDA)
            rol, texto = mensaje["rol"], mensaje["texto"]
            if rol not in ROLES or not isinstance(texto, str) or len(texto) > MAX_TEXTO_HISTORIAL:
                raise forms.ValidationError(MENSAJE_INVALIDA)
            limpio.append({"rol": rol, "texto": texto})
        datos["historial"] = limpio
        return datos
