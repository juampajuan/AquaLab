from django import forms
from django.contrib.auth.forms import AdminUserCreationForm, BaseUserCreationForm, UserChangeForm
from django.contrib.auth.hashers import make_password

from .models import Usuario, UsuarioManager


class UsuarioChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = Usuario
        fields = "__all__"


class UsuarioCreationForm(AdminUserCreationForm):
    class Meta(AdminUserCreationForm.Meta):
        model = Usuario
        fields = ("email", "first_name", "last_name")


class RegistroForm(BaseUserCreationForm):
    """Paso 1 del registro: valida los datos, pero no crea la cuenta."""

    class Meta:
        model = Usuario
        fields = ("first_name", "last_name", "email")
        labels = {
            "first_name": "Nombre",
            "last_name": "Apellido",
            "email": "Correo electrónico",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password1"].label = "Contraseña"
        self.fields["password2"].label = "Repetir contraseña"
        for campo in self.fields.values():
            campo.required = True
            campo.widget.attrs["class"] = "form-control"

    def full_clean(self):
        super().full_clean()
        for nombre in self.errors:
            if nombre in self.fields:
                self.fields[nombre].widget.attrs["class"] += " is-invalid"

    def clean_email(self):
        email = UsuarioManager.normalizar_email(self.cleaned_data["email"])
        if Usuario.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Este correo no está disponible.")
        return email

    def datos_para_sesion(self):
        """Datos que esperan la confirmación en la sesión, con la contraseña ya hasheada."""
        return {
            "first_name": self.cleaned_data["first_name"],
            "last_name": self.cleaned_data["last_name"],
            "email": self.cleaned_data["email"],
            "password": make_password(self.cleaned_data["password1"]),
        }
