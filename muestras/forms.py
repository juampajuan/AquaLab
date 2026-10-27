from django import forms
from django.utils import timezone

from clientes.models import Cliente

from .models import Origen, TipoVertido

CAMPOS_MUESTRA = (
    "cliente",
    "origen",
    "origen_nuevo",
    "fecha_muestreo",
    "fecha_ingreso",
    "sitio_extraccion",
    "tipo_vertido",
    "nombre",
    "responsable_muestreo",
)


class ClienteChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return f"{obj.nombre_completo} · {obj.tipo_documento} {obj.numero_documento}"


class SelectorFecha(forms.DateInput):
    input_type = "date"

    def __init__(self):
        super().__init__(format="%Y-%m-%d")


class RegistroMuestraForm(forms.Form):
    """Paso 1 del registro: valida y normaliza los datos sin guardar en la base."""

    cliente = ClienteChoiceField(
        queryset=Cliente.objects.filter(activo=True),
        label="Cliente",
        empty_label="Elegí un cliente",
    )
    origen = forms.ModelChoiceField(
        queryset=Origen.objects.none(),
        required=False,
        label="Origen",
        empty_label="Elegí un origen",
    )
    origen_nuevo = forms.CharField(
        label="Origen nuevo",
        max_length=150,
        required=False,
        strip=True,
    )
    fecha_muestreo = forms.DateField(
        label="Fecha de muestreo",
        widget=SelectorFecha(),
        initial=timezone.localdate,
    )
    fecha_ingreso = forms.DateField(
        label="Fecha de ingreso",
        widget=SelectorFecha(),
        initial=timezone.localdate,
    )
    sitio_extraccion = forms.CharField(label="Sitio de extracción", max_length=200, strip=True)
    tipo_vertido = forms.ChoiceField(
        label="Tipo de vertido",
        choices=TipoVertido.choices,
        initial=TipoVertido.AGUA,
    )
    nombre = forms.CharField(
        label="Nombre de la muestra",
        max_length=100,
        required=False,
        strip=True,
        help_text="Si lo dejás vacío se numera según las muestras del cliente (ej. «Muestra 6»).",
    )
    responsable_muestreo = forms.CharField(
        label="Responsable del muestreo",
        max_length=150,
        required=False,
        strip=True,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._cliente_elegido = None
        pk_cliente = self._pk_cliente()
        if pk_cliente is not None:
            self._cliente_elegido = Cliente.objects.filter(pk=pk_cliente, activo=True).first()
            self.fields["origen"].queryset = Origen.objects.filter(cliente_id=pk_cliente)
        for campo in self.fields.values():
            if isinstance(campo.widget, forms.Select):
                campo.widget.attrs["class"] = "form-select"
            else:
                campo.widget.attrs["class"] = "form-control"

    def _pk_cliente(self):
        valor = self.data.get("cliente") if self.is_bound else self.initial.get("cliente")
        try:
            return int(valor)
        except (TypeError, ValueError):
            return None

    @property
    def cliente_elegido(self):
        """Cliente activo elegido en los datos enviados o en el borrador, o `None`."""
        return self._cliente_elegido

    def full_clean(self):
        super().full_clean()
        for nombre in self.errors:
            if nombre in self.fields:
                self.fields[nombre].widget.attrs["class"] += " is-invalid"

    @staticmethod
    def validar_no_futura(fecha):
        if fecha and fecha > timezone.localdate():
            raise forms.ValidationError("La fecha no puede ser posterior a hoy.")
        return fecha

    def clean_fecha_muestreo(self):
        return self.validar_no_futura(self.cleaned_data.get("fecha_muestreo"))

    def clean_fecha_ingreso(self):
        return self.validar_no_futura(self.cleaned_data.get("fecha_ingreso"))

    def clean(self):
        cleaned_data = super().clean()
        fecha_muestreo = cleaned_data.get("fecha_muestreo")
        fecha_ingreso = cleaned_data.get("fecha_ingreso")
        if fecha_muestreo and fecha_ingreso and fecha_muestreo > fecha_ingreso:
            self.add_error(
                "fecha_muestreo",
                "La fecha de muestreo no puede ser posterior a la fecha de ingreso.",
            )
        origen = cleaned_data.get("origen")
        origen_nuevo = cleaned_data.get("origen_nuevo")
        if "origen" not in self.errors:
            if not origen and not origen_nuevo:
                self.add_error("origen", "Elegí un origen del cliente o ingresá uno nuevo.")
            elif origen and origen_nuevo:
                self.add_error(
                    "origen_nuevo", "Elegí un origen existente o ingresá uno nuevo, no ambos."
                )
        return cleaned_data

    def datos_para_sesion(self):
        """Datos normalizados listos para guardarse en la sesión durante la revisión."""
        datos = self.cleaned_data
        return {
            "cliente": datos["cliente"].pk,
            "origen": datos["origen"].pk if datos["origen"] else None,
            "origen_nuevo": datos["origen_nuevo"],
            "fecha_muestreo": datos["fecha_muestreo"].isoformat(),
            "fecha_ingreso": datos["fecha_ingreso"].isoformat(),
            "sitio_extraccion": datos["sitio_extraccion"],
            "tipo_vertido": datos["tipo_vertido"],
            "nombre": datos["nombre"],
            "responsable_muestreo": datos["responsable_muestreo"],
        }


def datos_clientes():
    """Clientes activos con sus orígenes, para actualizar la ficha y los orígenes en vivo."""
    clientes = Cliente.objects.filter(activo=True).prefetch_related("origenes")
    return [
        {
            "id": cliente.pk,
            "nombre_completo": cliente.nombre_completo,
            "razon_social_o_nombre": cliente.razon_social or cliente.nombre,
            "tipo_documento": cliente.tipo_documento,
            "numero_documento": cliente.numero_documento,
            "email": cliente.email,
            "origenes": [
                {"id": origen.pk, "nombre": origen.nombre} for origen in cliente.origenes.all()
            ],
        }
        for cliente in clientes
    ]
