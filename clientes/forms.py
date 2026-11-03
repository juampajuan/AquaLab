from django import forms

from estudios.models import EstadoEstudio
from muestras.forms import SelectorFecha

from .models import (
    MENSAJE_DOCUMENTO_CON_MUESTRAS,
    Cliente,
    TipoDocumento,
    normalizar_numero_documento,
    validar_documento,
    validar_telefono,
)

MAX_LONGITUD_BUSQUEDA = 100
FORMATOS_FECHA = ["%Y-%m-%d", "%d/%m/%Y"]
MENSAJE_FECHA_INVALIDA = "Ingresá una fecha válida (dd/mm/aaaa)."
MENSAJE_DOCUMENTO_DUPLICADO = "Ya existe un cliente registrado con este tipo y número de documento."

CAMPOS_CLIENTE = (
    "nombre",
    "razon_social",
    "tipo_documento",
    "numero_documento",
    "email",
    "telefono",
    "domicilio",
)


class RegistroClienteForm(forms.ModelForm):
    """Paso 1 del alta o edición: valida y normaliza los datos sin guardar en la base."""

    numero_documento = forms.CharField(
        label="Número de documento",
        max_length=30,
        strip=True,
        # Campo declarado: Meta.help_texts no se le aplica.
        help_text="Podés escribirlo con o sin puntos y guiones: se guardan solo los números.",
    )

    class Meta:
        model = Cliente
        fields = CAMPOS_CLIENTE
        labels = {
            "nombre": "Nombre",
            "razon_social": "Razón social",
            "tipo_documento": "Tipo de documento",
            "numero_documento": "Número de documento",
            "email": "Correo electrónico",
            "telefono": "Teléfono",
            "domicilio": "Domicilio",
        }
        # Ayuda de los campos que no se explican solos (US 9.1). Va en el formulario y no en el
        # modelo: allí generaría una migración y se vería en el admin.
        help_texts = {
            "razon_social": (
                "Nombre legal de la empresa u organismo. Si el cliente es una persona, "
                "completá el nombre."
            ),
            "tipo_documento": (
                "DNI para personas; CUIT para empresas, organismos o personas que facturan."
            ),
            "email": "A este correo se envían los informes del cliente.",
        }
        # Se dibuja como botones segmentados DNI / CUIT (templates/ui/campo.html).
        widgets = {"tipo_documento": forms.RadioSelect}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Sin la opción vacía "---------": con radios no tiene sentido.
        self.fields["tipo_documento"].choices = TipoDocumento.choices
        for campo in self.fields.values():
            campo.widget.attrs["class"] = "form-control"

    def full_clean(self):
        super().full_clean()
        for nombre in self.errors:
            if nombre in self.fields:
                self.fields[nombre].widget.attrs["class"] += " is-invalid"

    def clean_nombre(self):
        return (self.cleaned_data.get("nombre") or "").strip()

    def clean_razon_social(self):
        return (self.cleaned_data.get("razon_social") or "").strip()

    def clean_email(self):
        return (self.cleaned_data.get("email") or "").strip().lower()

    def clean_telefono(self):
        telefono = (self.cleaned_data.get("telefono") or "").strip()
        if telefono:
            validar_telefono(telefono)
        return telefono

    def clean_domicilio(self):
        return (self.cleaned_data.get("domicilio") or "").strip()

    def clean(self):
        cleaned_data = super().clean()
        nombre = cleaned_data.get("nombre") or ""
        razon_social = cleaned_data.get("razon_social") or ""
        if not nombre and not razon_social:
            raise forms.ValidationError(
                "Debés ingresar al menos el nombre o la razón social del cliente."
            )

        tipo = cleaned_data.get("tipo_documento")
        numero_raw = cleaned_data.get("numero_documento")
        if numero_raw is not None:
            numero = normalizar_numero_documento(numero_raw)
            cleaned_data["numero_documento"] = numero
            if tipo:
                try:
                    validar_documento(tipo, numero)
                except forms.ValidationError as exc:
                    self.add_error(None, exc)
                else:
                    if (
                        self.instance
                        and self.instance.pk
                        and (
                            tipo != self.instance.tipo_documento
                            or numero != self.instance.numero_documento
                        )
                        and self.instance.muestras.exists()
                    ):
                        self.add_error("numero_documento", MENSAJE_DOCUMENTO_CON_MUESTRAS)
                    else:
                        qs = Cliente.objects.filter(tipo_documento=tipo, numero_documento=numero)
                        if self.instance and self.instance.pk:
                            qs = qs.exclude(pk=self.instance.pk)
                        if qs.exists():
                            self.add_error("numero_documento", MENSAJE_DOCUMENTO_DUPLICADO)

        return cleaned_data

    def _post_clean(self):
        # La validación de modelo y unicidad ya se ejecutó en `clean()` con datos normalizados.
        pass

    def datos_para_sesion(self):
        """Datos normalizados listos para guardarse en la sesión durante la revisión."""
        return {campo: self.cleaned_data[campo] for campo in CAMPOS_CLIENTE}


EditarClienteForm = RegistroClienteForm


class BuscarClienteForm(forms.Form):
    """Texto de búsqueda de clientes (por GET): nombre, razón social o número de documento."""

    q = forms.CharField(
        label="Nombre, razón social o documento",
        required=False,
        min_length=2,
        max_length=MAX_LONGITUD_BUSQUEDA,
        strip=True,
        error_messages={
            "min_length": "Ingresá al menos 2 caracteres para buscar.",
            "max_length": "Ingresá como máximo 100 caracteres para buscar.",
        },
    )


class HistorialClienteForm(forms.Form):
    """Filtros del historial del cliente (US 3.3), por GET: rango de fecha de ingreso y estado.

    Mostrar «Limpiar filtros» no se decide acá: la vista lo hace con los parámetros recibidos,
    válidos o no.
    """

    desde = forms.DateField(
        label="Ingreso desde",
        required=False,
        input_formats=FORMATOS_FECHA,
        widget=SelectorFecha(),
        error_messages={"invalid": MENSAJE_FECHA_INVALIDA},
    )
    hasta = forms.DateField(
        label="Ingreso hasta",
        required=False,
        input_formats=FORMATOS_FECHA,
        widget=SelectorFecha(),
        error_messages={"invalid": MENSAJE_FECHA_INVALIDA},
    )
    estado = forms.ChoiceField(
        label="Estado del estudio",
        required=False,
        choices=[("", "Todos"), *EstadoEstudio.choices],
        error_messages={"invalid_choice": "Elegí un estado de la lista."},
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in self.fields.values():
            clase = "form-select" if isinstance(campo.widget, forms.Select) else "form-control"
            campo.widget.attrs["class"] = clase

    def full_clean(self):
        super().full_clean()
        for nombre in self.errors:
            if nombre in self.fields:
                self.fields[nombre].widget.attrs["class"] += " is-invalid"

    def clean(self):
        datos = super().clean()
        desde, hasta = datos.get("desde"), datos.get("hasta")
        if desde and hasta and desde > hasta:
            self.add_error("desde", "La fecha desde no puede ser posterior a la fecha hasta.")
        return datos
