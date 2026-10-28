from django import forms

from muestras.models import Muestra

from .models import TipoEstudio

MAX_LONGITUD_BUSQUEDA = 100
MAX_ENTERO_BUSQUEDA = 9_223_372_036_854_775_807


class MuestraChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return f"PI {obj.numero_pi} · {obj.cliente.nombre_completo} · {obj.origen.nombre}"


class CrearEstudioForm(forms.Form):
    muestra = MuestraChoiceField(
        queryset=Muestra.objects.select_related("cliente", "origen"),
        label="Muestra",
        empty_label="Elegí una muestra",
    )
    tipo = forms.ModelChoiceField(
        queryset=TipoEstudio.objects.filter(activo=True),
        label="Tipo de estudio",
        empty_label="Elegí un tipo",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in self.fields.values():
            campo.widget.attrs["class"] = "form-select"


class BuscarEstudioForm(forms.Form):
    """Texto de búsqueda de estudios (por GET): identificador, muestra o cliente."""

    q = forms.CharField(
        label="Identificador, muestra (N° PI / nombre) o cliente",
        required=False,
        max_length=MAX_LONGITUD_BUSQUEDA,
        strip=True,
        error_messages={
            "max_length": "Ingresá como máximo 100 caracteres para buscar.",
        },
    )

    def clean_q(self):
        valor = (self.cleaned_data.get("q") or "").strip()
        if not valor:
            raise forms.ValidationError(
                "Ingresá un identificador de estudio, N° PI, muestra o cliente para buscar."
            )
        if valor.isdigit():
            try:
                if not valor.isascii():
                    raise ValueError
                numero = int(valor)
            except ValueError as exc:
                raise forms.ValidationError("Ingresá un número válido para buscar.") from exc
            if numero < 1 or numero > MAX_ENTERO_BUSQUEDA:
                raise forms.ValidationError("Ingresá un número válido para buscar.")
            return valor
        if len(valor) < 2:
            raise forms.ValidationError("Ingresá al menos 2 caracteres para buscar.")
        return valor
