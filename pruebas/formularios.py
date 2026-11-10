"""Formulario de alta y edición de pruebas (SCRUM-73).

Las reglas son las de `gestion.validar_datos` (la misma que usa el servicio): acá solo se muestran
los errores junto a cada campo. Con `bloquear_metodo=True` (prueba en uso) los campos del método
quedan deshabilitados y Django ignora lo que se envíe para ellos; con `fijar_unidad=True` (prueba
nueva que reemplaza a otra), solo la unidad del resultado.
"""

from django import forms

from . import gestion
from .models import TipoCalculo

AYUDA_LIMITE = (
    "Un número (con coma o punto) o «Ausente». «Ausente» significa «no detectado»: cero o por "
    "debajo del límite de detección (pruebas Ausente/Presente y mediciones como Sólidos "
    "sedimentables). Para conteos que no deben aparecer, como Coliformes fecales, usá máx. 0."
)
AYUDA_FORMULA = (
    "Solo si el tipo de cálculo es Fórmula. x es el valor medido y {CODIGO} el resultado de otra "
    "prueba. Ejemplo: {DUREZA-T}-{CA}*2.5"
)
AYUDA_LD = "Por debajo de este valor el resultado se informa como «< LD»."
AYUDA_VERTIDO = (
    "Si se completa, reemplaza a los límites generales para las muestras de este vertido."
)


def texto(etiqueta, maximo, *, requerido=False, ayuda="", area=False):
    return forms.CharField(
        label=etiqueta,
        max_length=maximo,
        required=requerido,
        help_text=ayuda,
        widget=forms.Textarea(attrs={"rows": 3}) if area else None,
    )


class PruebaForm(forms.Form):
    codigo = texto("Código", 50, requerido=True)
    nombre = texto("Nombre", 150, requerido=True)
    tipo_calculo = forms.ChoiceField(
        label="Tipo de cálculo", choices=TipoCalculo.choices, initial=TipoCalculo.DIRECTO
    )
    formula = texto("Fórmula", 255, ayuda=AYUDA_FORMULA)
    unidad_medicion = texto("Unidad de medición", 50, ayuda="La unidad de lo que se mide.")
    unidad = texto("Unidad del resultado", 50, ayuda="La unidad del resultado que se informa.")
    limite_min = texto("Límite mínimo", 50, ayuda=AYUDA_LIMITE)
    limite_max = texto("Límite máximo", 50, ayuda=AYUDA_LIMITE)
    norma = texto("Norma", 150)
    limite_deteccion = texto("Límite de detección", 50, ayuda=AYUDA_LD)
    cloacal_limite_min = texto("Mínimo cloacal", 50, ayuda=AYUDA_VERTIDO)
    cloacal_limite_max = texto("Máximo cloacal", 50, ayuda=AYUDA_VERTIDO)
    cloacal_norma = texto("Norma cloacal", 150)
    canal_limite_min = texto("Mínimo canal", 50, ayuda=AYUDA_VERTIDO)
    canal_limite_max = texto("Máximo canal", 50, ayuda=AYUDA_VERTIDO)
    canal_norma = texto("Norma canal", 150)
    observacion = texto("Observación", 2000, area=True)

    def __init__(self, *args, prueba=None, bloquear_metodo=False, fijar_unidad=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.prueba = prueba
        for nombre, campo in self.fields.items():
            campo.widget.attrs["class"] = (
                "form-select" if isinstance(campo, forms.ChoiceField) else "form-control"
            )
            if bloquear_metodo and nombre in gestion.CAMPOS_METODO:
                campo.disabled = True
        if fijar_unidad:  # reemplazo: la nueva lleva la unidad de la que reemplaza
            self.fields["unidad"].disabled = True

    def clean(self):
        datos = super().clean()
        if self.errors:
            return datos
        try:
            self.datos_servicio_ = gestion.validar_datos(datos, self.prueba)
        except gestion.DatosInvalidos as exc:
            for campo, mensaje in exc.errores.items():
                self.add_error(campo if campo in self.fields else None, mensaje)
        return datos

    def full_clean(self):
        super().full_clean()
        for nombre in self.errors:
            if nombre in self.fields:
                self.fields[nombre].widget.attrs["class"] += " is-invalid"

    def datos_servicio(self):
        return self.datos_servicio_

    def secciones(self):
        """Campos agrupados para el template."""
        grupos = (
            ("Identificación", "id-card", ("codigo", "nombre")),
            ("Cálculo", "flask-conical", ("tipo_calculo", "formula", "unidad_medicion", "unidad")),
            (
                "Límites generales",
                "clipboard-list",
                ("limite_min", "limite_max", "norma", "limite_deteccion"),
            ),
            (
                "Límites para vertido cloacal",
                "droplet",
                ("cloacal_limite_min", "cloacal_limite_max", "cloacal_norma"),
            ),
            (
                "Límites para vertido a canal",
                "droplet",
                ("canal_limite_min", "canal_limite_max", "canal_norma"),
            ),
            ("Observación", "pencil", ("observacion",)),
        )
        return [(titulo, icono, [self[c] for c in campos]) for titulo, icono, campos in grupos]
