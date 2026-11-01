from django import forms

from muestras.models import Muestra
from pruebas.models import Prueba

from .mediciones import leer_valor
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


class CargarMedicionesForm(forms.Form):
    """Un campo opcional `medicion_<asignacion_pk>` por prueba del estudio."""

    def __init__(self, *args, asignaciones, **kwargs):
        super().__init__(*args, **kwargs)
        self.asignaciones = list(asignaciones)
        self._valores = {}
        for asignacion in self.asignaciones:
            campo = forms.CharField(required=False, max_length=40, label=str(asignacion.prueba))
            campo.widget.attrs.update(
                {"inputmode": "decimal", "autocomplete": "off", "class": "form-control"}
            )
            self.fields[self.nombre(asignacion)] = campo

    @staticmethod
    def nombre(asignacion):
        return f"medicion_{asignacion.pk}"

    def clean(self):
        datos = super().clean()
        self._valores = {}
        for asignacion in self.asignaciones:
            nombre = self.nombre(asignacion)
            if nombre not in datos:
                continue
            try:
                valor = leer_valor(datos[nombre])
            except forms.ValidationError as exc:
                self.add_error(nombre, exc)
                attrs = self.fields[nombre].widget.attrs
                attrs["class"] += " is-invalid"
                attrs["aria-describedby"] = f"{self[nombre].auto_id}_error"
                continue
            if valor is not None:
                self._valores[asignacion.pk] = valor
        if not self._valores and not self.errors:
            raise forms.ValidationError("Ingresá al menos una medición.")
        return datos

    def pruebas_quitadas(self):
        """Valores enviados para asignaciones que ya no son del estudio (pruebas quitadas)."""
        propios = set(self.fields)
        return sum(
            1
            for nombre, texto in self.data.items()
            if nombre.startswith("medicion_") and nombre not in propios and texto.strip()
        )

    def filas(self):
        return [(a, self[self.nombre(a)]) for a in self.asignaciones]

    def valores(self):
        return dict(self._valores)

    def resumen(self):
        """`(asignacion, nombre, texto)` de las pruebas con valor, para revisar y reenviar."""
        return [
            (a, self.nombre(a), self.cleaned_data[self.nombre(a)].strip())
            for a in self.asignaciones
            if a.pk in self._valores
        ]


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
