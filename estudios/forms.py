from django import forms

from muestras.models import Muestra
from pruebas.models import Prueba

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


class AgregarPruebaForm(forms.Form):
    def __init__(self, *args, estudio, **kwargs):
        super().__init__(*args, **kwargs)
        self.estudio = estudio
        self.fields["prueba"] = forms.ModelChoiceField(
            queryset=Prueba.objects.exclude(pk__in=estudio.pruebas_asignadas.values("prueba")),
            label="Prueba",
            empty_label="Elegí una prueba",
        )
        self.fields["prueba"].widget.attrs["class"] = "form-select"

    def full_clean(self):
        super().full_clean()
        if "prueba" in self.errors:
            self.fields["prueba"].widget.attrs["class"] += " is-invalid"

    def prueba_ya_asignada(self):
        """Prueba enviada que ya forma parte del estudio (reenvío), o `None`."""
        asignadas = Prueba.objects.filter(pk__in=self.estudio.pruebas_asignadas.values("prueba"))
        try:
            return forms.ModelChoiceField(queryset=asignadas).clean(self.data.get("prueba"))
        except forms.ValidationError:
            return None


class BuscarEstudioForm(forms.Form):
    """Texto de búsqueda de estudios (por GET): identificador, muestra, cliente o tipo."""

    q = forms.CharField(
        label="Identificador, muestra, cliente o tipo de estudio",
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
            return ""
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
