from django import forms
from django.core.validators import RegexValidator

from muestras.forms import FORMATOS_FECHA, SelectorFecha

from .firmas import leer_firma
from .models import FirmaProfesional


class RevisionConclusionForm(forms.Form):
    revision_esperada = forms.IntegerField(min_value=0)
    huella_hechos_vista = forms.CharField(
        min_length=64, max_length=64, validators=[RegexValidator(r"\A[0-9a-f]{64}\Z")]
    )

    def clean_revision_esperada(self):
        if isinstance(self.data.get("revision_esperada"), bool):
            raise forms.ValidationError("La revisión debe ser un número entero.")
        return self.cleaned_data["revision_esperada"]


class GuardarConclusionForm(RevisionConclusionForm):
    texto = forms.CharField(
        label="Borrador de conclusión",
        required=False,
        strip=False,
        widget=forms.Textarea,
        help_text="Se conserva como borrador. Editarlo invalida la aprobación anterior.",
    )

    def clean_texto(self):
        return self.cleaned_data["texto"].replace("\r\n", "\n")


class AprobarConclusionForm(RevisionConclusionForm):
    huella_texto_visto = forms.CharField(
        min_length=64, max_length=64, validators=[RegexValidator(r"\A[0-9a-f]{64}\Z")]
    )
    confirmacion = forms.BooleanField(
        label="Apruebo el texto final y sus advertencias",
        help_text="La aprobación corresponde exactamente al texto y a los hechos revisados.",
        error_messages={"required": "Confirmá expresamente la aprobación del texto revisado."},
    )


class EmitirConclusionForm(forms.Form):
    incluir_conclusion = forms.CharField(required=False)
    revision_conclusion = forms.IntegerField(required=False, min_value=1)

    def clean_incluir_conclusion(self):
        valor = self.data.get("incluir_conclusion", "")
        if type(valor) is bool:
            return valor
        if valor not in ("", "0", "1"):
            raise forms.ValidationError("La opción de conclusión no es válida.")
        return valor == "1"

    def clean_revision_conclusion(self):
        valor = self.data.get("revision_conclusion")
        if valor not in (None, "") and (
            type(valor) is not int and (not isinstance(valor, str) or not valor.isdecimal())
        ):
            raise forms.ValidationError("La revisión debe ser un número entero.")
        return self.cleaned_data["revision_conclusion"]

    def clean(self):
        datos = super().clean()
        if datos.get("incluir_conclusion") and datos.get("revision_conclusion") is None:
            self.add_error("revision_conclusion", "Indicá la revisión aprobada para emitir.")
        return datos


class BuscarInformeForm(forms.Form):
    """Búsqueda de informes emitidos (US 7.3)."""

    q = forms.CharField(
        label="Buscar",
        required=False,
        max_length=100,
        strip=True,
        widget=forms.TextInput(attrs={"placeholder": "N° de informe, cliente, documento o N° PI"}),
    )
    desde = forms.DateField(
        label="Emitido desde",
        required=False,
        input_formats=FORMATOS_FECHA,
        widget=SelectorFecha(attrs={"class": "form-control"}),
    )
    hasta = forms.DateField(
        label="Emitido hasta",
        required=False,
        input_formats=FORMATOS_FECHA,
        widget=SelectorFecha(attrs={"class": "form-control"}),
    )

    envio = forms.ChoiceField(
        label="Envío por correo",
        required=False,
        choices=[("", "Todos"), ("sin_enviar", "Sin enviar"), ("enviados", "Enviados")],
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    def full_clean(self):
        super().full_clean()
        for nombre in ("desde", "hasta"):
            if nombre in self.errors:
                self.fields[nombre].widget.attrs["class"] = "form-control is-invalid"

    def clean(self):
        datos = super().clean()
        desde, hasta = datos.get("desde"), datos.get("hasta")
        if desde and hasta and desde > hasta:
            self.add_error("desde", "La fecha desde no puede ser posterior a la fecha hasta.")
        return datos


class FirmaForm(forms.Form):
    """Firma dibujada y matrícula de quien emite informes (US 7.3).

    La matrícula se escribe solo con la primera firma (SCRUM-81): después el campo queda
    deshabilitado (Django ignora lo enviado y usa la guardada) y solo un administrador la corrige
    desde el admin. La firma dibujada se puede reemplazar siempre.
    """

    firma = forms.CharField(required=False, widget=forms.HiddenInput)
    matricula = forms.CharField(
        label="Matrícula",
        max_length=40,
        strip=True,
        help_text=(
            "Tu matrícula profesional, por ejemplo «MP 1234». "
            "Sale junto a tu firma en los informes."
        ),
        widget=forms.TextInput(attrs={"placeholder": "MP 1234", "class": "form-control"}),
    )

    def __init__(self, *args, usuario, **kwargs):
        self.usuario = usuario
        self.actual = FirmaProfesional.objects.filter(usuario=usuario).first()
        kwargs.setdefault("initial", {"matricula": self.actual.matricula if self.actual else ""})
        super().__init__(*args, **kwargs)
        if self.actual is not None:
            self.fields["matricula"].disabled = True

    def full_clean(self):
        super().full_clean()
        if "matricula" in self.errors:
            self.fields["matricula"].widget.attrs["class"] += " is-invalid"

    def clean_firma(self):
        texto = self.cleaned_data["firma"]
        if not texto:
            if self.actual is None:
                raise forms.ValidationError("Dibujá tu firma antes de guardar.")
            return None
        return leer_firma(texto)

    def guardar(self):
        """Crea la firma del usuario o reemplaza su imagen; la matrícula guardada no cambia."""
        if self.actual is None:
            return FirmaProfesional.objects.create(
                usuario=self.usuario,
                imagen=self.cleaned_data["firma"],
                matricula=self.cleaned_data["matricula"],
            )
        if self.cleaned_data["firma"] is not None:
            self.actual.imagen = self.cleaned_data["firma"]
            self.actual.save(update_fields=["imagen", "actualizada"])
        return self.actual
