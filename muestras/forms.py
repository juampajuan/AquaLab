import datetime
import uuid

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


# Se acepta dd/mm/aaaa (lo que escribe el usuario) y aaaa-mm-dd (enlaces y sesión).
FORMATOS_FECHA = ["%d/%m/%Y", "%Y-%m-%d"]


class SelectorFecha(forms.DateInput):
    """Fecha como texto dd/mm/aaaa, igual en cualquier navegador.

    El selector nativo (`type="date"`) muestra el formato del idioma del navegador: en uno en
    inglés pide mm/dd/aaaa y «12/04» se lee como 4 de diciembre. aqualab.js agrega las barras
    mientras se escribe (`data-fecha`).
    """

    input_type = "text"

    def __init__(self, attrs=None):
        super().__init__(
            format="%d/%m/%Y",
            attrs={
                "placeholder": "dd/mm/aaaa",
                "inputmode": "numeric",
                "maxlength": "10",
                "autocomplete": "off",
                "data-fecha": "",
                **(attrs or {}),
            },
        )

    def format_value(self, value):
        # Un valor aaaa-mm-dd (de un enlace o de la sesión) se muestra como dd/mm/aaaa.
        if isinstance(value, str):
            try:
                value = datetime.date.fromisoformat(value)
            except ValueError:
                return value
        return super().format_value(value)


class TipoEstudioOpcional(forms.ModelChoiceField):
    """Tipo de estudio pedido para crear después de registrar la muestra (US 10.3). Un valor
    inválido o un tipo desactivado se descarta en silencio: es un dato oculto que no se edita
    (un `clean_tipo_estudio` no alcanza, el error salta antes)."""

    def clean(self, value):
        try:
            return super().clean(value)
        except forms.ValidationError:
            return None


def tipos_activos():
    from estudios.models import TipoEstudio

    return TipoEstudio.objects.filter(activo=True)


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
        help_text=(
            "Fuente de agua de la que se tomó la muestra (pozo, red, efluente). Permite comparar "
            "los resultados de un mismo origen a lo largo del tiempo."
        ),
    )
    origen_nuevo = forms.CharField(
        label="Origen nuevo",
        max_length=150,
        required=False,
        strip=True,
        help_text=(
            "Si la fuente no está en la lista, escribí su nombre. Si ya existe con otras "
            "mayúsculas, se usa la existente."
        ),
    )
    fecha_muestreo = forms.DateField(
        label="Fecha de muestreo",
        input_formats=FORMATOS_FECHA,
        widget=SelectorFecha(),
        initial=timezone.localdate,
        help_text="Día en que se tomó la muestra.",
    )
    fecha_ingreso = forms.DateField(
        label="Fecha de ingreso",
        input_formats=FORMATOS_FECHA,
        widget=SelectorFecha(),
        initial=timezone.localdate,
        help_text="Día en que la muestra llegó al laboratorio.",
    )
    sitio_extraccion = forms.CharField(
        label="Sitio de extracción",
        max_length=200,
        strip=True,
        help_text=(
            "Punto exacto de donde se tomó, por ejemplo la canilla de la cocina o la boca del pozo."
        ),
    )
    tipo_vertido = forms.ChoiceField(
        label="Tipo de vertido",
        choices=TipoVertido.choices,
        initial=TipoVertido.AGUA,
        help_text=(
            "Define con qué límites se evalúan los resultados: los del vertido elegido reemplazan "
            "a los generales."
        ),
        # Se dibuja como botones segmentados (templates/ui/campo.html).
        widget=forms.RadioSelect,
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
        help_text="Persona que tomó la muestra.",
    )
    tipo_estudio = TipoEstudioOpcional(
        queryset=None, required=False, widget=forms.HiddenInput, label="Tipo de estudio"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["tipo_estudio"].queryset = tipos_activos()
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
            "tipo_estudio": datos["tipo_estudio"].pk if datos.get("tipo_estudio") else None,
            "clave_borrador": str(uuid.uuid4()),
        }

    @property
    def tipo_estudio_elegido(self):
        """Tipo activo pedido para el estudio siguiente (nota del formulario), o `None`."""
        if self.is_bound:
            valor = self.data.get("tipo_estudio")
        else:
            valor = self.initial.get("tipo_estudio")
        return tipo_activo(valor)


def tipo_activo(valor):
    """El tipo de estudio activo con ese pk, o `None` (también para valores inválidos)."""
    try:
        pk = int(valor)
    except (TypeError, ValueError):
        return None
    return tipos_activos().filter(pk=pk).first()


def _texto(valor, largo):
    valor = (valor or "").strip()
    return valor if valor and len(valor) <= largo else None


def _fecha_iso(valor):
    try:
        return datetime.date.fromisoformat(valor or "").isoformat()
    except ValueError:
        return None


def valores_iniciales(parametros):
    """Valores iniciales del registro a partir de un GET (US 10.3,
    contracts/enlaces-precargados.md). Única función de saneo: lo que no existe o no está
    disponible se descarta en silencio. Nunca crea nada."""
    iniciales = {}
    try:
        pk_cliente = int(parametros.get("cliente", ""))
    except ValueError:
        pk_cliente = None
    cliente = Cliente.objects.filter(pk=pk_cliente, activo=True).first() if pk_cliente else None
    if cliente is not None:
        iniciales["cliente"] = cliente.pk
        try:
            pk_origen = int(parametros.get("origen", ""))
        except ValueError:
            pk_origen = None
        if pk_origen and Origen.objects.filter(pk=pk_origen, cliente=cliente).exists():
            iniciales["origen"] = pk_origen
    if "origen" not in iniciales and (nuevo := _texto(parametros.get("origen_nuevo"), 150)):
        iniciales["origen_nuevo"] = nuevo
    for campo in ("fecha_muestreo", "fecha_ingreso"):
        if fecha := _fecha_iso(parametros.get(campo)):
            iniciales[campo] = fecha
    for campo, largo in (("sitio_extraccion", 200), ("nombre", 100), ("responsable_muestreo", 150)):
        if valor := _texto(parametros.get(campo), largo):
            iniciales[campo] = valor
    if parametros.get("tipo_vertido") in TipoVertido.values:
        iniciales["tipo_vertido"] = parametros["tipo_vertido"]
    if tipo := tipo_activo(parametros.get("tipo_estudio")):
        iniciales["tipo_estudio"] = tipo.pk
    return iniciales


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
