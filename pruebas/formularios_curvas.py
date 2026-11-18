"""Formularios de la carga de curvas de calibración (US 6.6).

Las reglas de la recta están en `curvas` (`ajustar`, `leer_fecha`); acá solo se leen los campos y
se muestran los errores junto a cada uno. La tabla de puntos es un formset sin JavaScript: los
botones «Agregar fila» y «Quitar» reenvían el formulario (research R7).
"""

from django import forms
from django.core import signing
from django.core.exceptions import ValidationError
from django.forms import BaseFormSet, formset_factory

from estudios.mediciones import leer_valor
from muestras.forms import FORMATOS_FECHA, SelectorFecha

from . import curvas

FILAS_INICIALES = 3
PREFIJO = "puntos"
SALT_ARCHIVO = "pruebas.curva.archivo.v1"


def firmar_archivo(nombre):
    """El nombre del archivo importado viaja firmado en el formulario: no se puede inventar."""
    return signing.dumps(nombre, salt=SALT_ARCHIVO) if nombre else ""


def leer_archivo_firmado(valor):
    try:
        nombre = signing.loads(valor, salt=SALT_ARCHIVO) if valor else ""
    except signing.BadSignature:
        return ""
    return nombre if isinstance(nombre, str) else ""


class CurvaForm(forms.Form):
    fecha_preparacion = forms.DateField(
        label="Fecha de preparación",
        help_text="Día en que se prepararon los estándares.",
        input_formats=FORMATOS_FECHA,
        widget=SelectorFecha(),
    )
    observacion = forms.CharField(
        label="Observación",
        required=False,
        max_length=2000,
        widget=forms.Textarea(attrs={"rows": 2}),
    )
    archivo_origen = forms.CharField(required=False, max_length=255, widget=forms.HiddenInput)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["fecha_preparacion"].widget.attrs["class"] = "form-control"
        self.fields["observacion"].widget.attrs["class"] = "form-control"

    def clean_archivo_origen(self):
        return leer_archivo_firmado(self.cleaned_data.get("archivo_origen", ""))[:255]

    def clean_fecha_preparacion(self):
        fecha = self.cleaned_data["fecha_preparacion"]
        try:
            curvas.leer_fecha(fecha.isoformat())
        except curvas.CurvaInvalida as exc:
            raise ValidationError(exc.errores["fecha_preparacion"]) from exc
        return fecha

    def full_clean(self):
        super().full_clean()
        for nombre in self.errors:
            if nombre in self.fields:
                self.fields[nombre].widget.attrs["class"] += " is-invalid"


class ImportarForm(forms.Form):
    archivo = forms.FileField(
        label="Archivo (.csv o .xlsx)",
        required=False,
        help_text="CSV o Excel (.xlsx) con una columna de concentración y otra de absorbancia.",
        widget=forms.ClearableFileInput(
            attrs={"accept": ".csv,.xlsx", "class": "form-control", "data-importar-al-elegir": ""}
        ),
    )


class ElegirColumnasForm(forms.Form):
    """Qué columna es cada una, cuando el archivo no lo dice en sus encabezados."""

    columna_concentracion = forms.TypedChoiceField(label="Concentración", coerce=int)
    columna_absorbancia = forms.TypedChoiceField(label="Absorbancia", coerce=int)

    def __init__(self, *args, columnas=(), **kwargs):
        super().__init__(*args, **kwargs)
        for campo in self.fields.values():
            campo.choices = list(columnas)
            campo.widget.attrs["class"] = "form-select"

    def clean(self):
        datos = super().clean()
        elegidas = (datos.get("columna_concentracion"), datos.get("columna_absorbancia"))
        if None not in elegidas and elegidas[0] == elegidas[1]:
            raise ValidationError("Elegí dos columnas distintas.")
        return datos

    def columnas(self):
        return self.cleaned_data["columna_concentracion"], self.cleaned_data["columna_absorbancia"]


class PuntoForm(forms.Form):
    concentracion = forms.CharField(label="Concentración", required=False, max_length=30)
    absorbancia = forms.CharField(label="Absorbancia", required=False, max_length=30)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in self.fields.values():
            campo.widget.attrs.update({"class": "form-control numeros", "inputmode": "decimal"})

    def clean(self):
        datos = super().clean()
        textos = {c: (datos.get(c) or "").strip() for c in ("concentracion", "absorbancia")}
        self.vacio = not any(textos.values())
        if self.vacio:
            return datos
        faltan = {
            "concentracion": curvas.MENSAJE_FALTA_CONCENTRACION,
            "absorbancia": curvas.MENSAJE_FALTA_ABSORBANCIA,
        }
        self.punto = []
        for campo, texto in textos.items():
            if not texto:
                self.add_error(campo, faltan[campo])
                continue
            try:
                valor = leer_valor(texto)
            except ValidationError as exc:
                self.add_error(campo, exc)
                continue
            if valor < 0:
                self.add_error(campo, curvas.MENSAJE_NEGATIVO)
                continue
            self.punto.append(valor)
        return datos

    def full_clean(self):
        super().full_clean()
        for nombre in self.errors:
            if nombre in self.fields:
                self.fields[nombre].widget.attrs["class"] += " is-invalid"


class BasePuntoFormSet(BaseFormSet):
    def clean(self):
        """Arma los puntos (sin las filas vacías) y calcula la recta (`curvas.ajustar`)."""
        self.puntos, self.ajuste = [], None
        if any(form.errors for form in self.forms):
            return
        # Django no valida las filas extra sin cambios: quedan sin `vacio` y cuentan como vacías.
        self.puntos = [tuple(form.punto) for form in self.forms if not getattr(form, "vacio", True)]
        try:
            self.ajuste = curvas.ajustar(self.puntos)
        except curvas.CurvaInvalida as exc:
            raise ValidationError(list(exc.errores.values())) from exc

    def textos(self):
        """Los puntos como textos, para el borrador de la confirmación."""
        return [[str(c), str(a)] for c, a in self.puntos]


PuntoFormSet = formset_factory(
    PuntoForm,
    formset=BasePuntoFormSet,
    extra=0,
    max_num=curvas.MAXIMO_PUNTOS,
    validate_max=True,
    absolute_max=curvas.MAXIMO_PUNTOS,
)


def filas_enviadas(datos):
    """Las filas del formset tal como se escribieron [(concentración, absorbancia)], sin validar."""
    try:
        total = min(int(datos.get(f"{PREFIJO}-TOTAL_FORMS", 0)), curvas.MAXIMO_PUNTOS)
    except (TypeError, ValueError):
        total = 0
    return [
        (
            datos.get(f"{PREFIJO}-{n}-concentracion", ""),
            datos.get(f"{PREFIJO}-{n}-absorbancia", ""),
        )
        for n in range(max(total, 0))
    ]


def formset_con(filas):
    """Formset sin enviar con estas filas (al menos FILAS_INICIALES)."""
    filas = list(filas) + [("", "")] * max(FILAS_INICIALES - len(filas), 0)
    return PuntoFormSet(
        prefix=PREFIJO,
        initial=[{"concentracion": c, "absorbancia": a} for c, a in filas],
    )
