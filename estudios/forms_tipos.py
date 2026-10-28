from django import forms

from pruebas.models import Prueba

from .models import TipoEstudio


class TipoEstudioForm(forms.Form):
    nombre = forms.CharField(label="Nombre", max_length=150, strip=True)
    descripcion = forms.CharField(
        label="Descripción", required=False, strip=False, widget=forms.Textarea
    )
    pruebas = forms.ModelMultipleChoiceField(
        label="Pruebas predeterminadas", queryset=Prueba.objects.order_by("codigo", "pk")
    )

    def __init__(self, *args, tipo_id=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.tipo_id = tipo_id
        for campo in self.fields.values():
            campo.widget.attrs["class"] = (
                "form-select"
                if isinstance(campo, forms.ModelMultipleChoiceField)
                else "form-control"
            )

    def clean_nombre(self):
        nombre = self.cleaned_data["nombre"]
        if TipoEstudio.objects.filter(nombre__iexact=nombre).exclude(pk=self.tipo_id).exists():
            raise forms.ValidationError("Ya existe un tipo con ese nombre.")
        return nombre

    def datos_servicio(self):
        return {
            "nombre": self.cleaned_data["nombre"],
            "descripcion": self.cleaned_data["descripcion"],
            "prueba_ids": [p.pk for p in self.cleaned_data["pruebas"]],
        }
