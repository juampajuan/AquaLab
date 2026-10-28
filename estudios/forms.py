from django import forms

from muestras.models import Muestra

from .models import TipoEstudio


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
