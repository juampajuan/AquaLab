from django import forms

from .firmas import leer_firma
from .models import FirmaProfesional

FORMATOS_FECHA = ["%Y-%m-%d", "%d/%m/%Y"]


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
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
    )
    hasta = forms.DateField(
        label="Emitido hasta",
        required=False,
        input_formats=FORMATOS_FECHA,
        widget=forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
    )

    def clean(self):
        datos = super().clean()
        desde, hasta = datos.get("desde"), datos.get("hasta")
        if desde and hasta and desde > hasta:
            self.add_error("desde", "La fecha desde no puede ser posterior a la fecha hasta.")
        return datos


class FirmaForm(forms.Form):
    """Firma dibujada y matrícula de quien emite informes (US 7.3)."""

    firma = forms.CharField(required=False, widget=forms.HiddenInput)
    matricula = forms.CharField(
        label="Matrícula",
        max_length=40,
        strip=True,
        widget=forms.TextInput(attrs={"placeholder": "MP 1234", "class": "form-control"}),
    )

    def __init__(self, *args, usuario, **kwargs):
        self.usuario = usuario
        self.actual = FirmaProfesional.objects.filter(usuario=usuario).first()
        kwargs.setdefault("initial", {"matricula": self.actual.matricula if self.actual else ""})
        super().__init__(*args, **kwargs)

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
        """Crea o reemplaza la firma del usuario; sin dibujo nuevo conserva la imagen."""
        valores = {"matricula": self.cleaned_data["matricula"]}
        if self.cleaned_data["firma"] is not None:
            valores["imagen"] = self.cleaned_data["firma"]
        firma, _ = FirmaProfesional.objects.update_or_create(usuario=self.usuario, defaults=valores)
        return firma
