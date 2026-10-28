from django import forms
from django.contrib.auth.forms import (
    AdminUserCreationForm,
    AuthenticationForm,
    BaseUserCreationForm,
    UserChangeForm,
)
from django.contrib.auth.hashers import check_password, make_password
from django.core.exceptions import NON_FIELD_ERRORS
from django.db import DatabaseError
from django.views.decorators.debug import sensitive_variables

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


class FormularioInicioSesion(AuthenticationForm):
    username = forms.CharField(
        label="Correo electrónico",
        max_length=254,
        widget=forms.TextInput(attrs={"autocomplete": "username", "autofocus": True}),
    )
    error_messages = {
        **AuthenticationForm.error_messages,
        "invalid_login": "Usuario o contraseña incorrectos",
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password"].label = "Contraseña"
        for campo in self.fields.values():
            campo.widget.attrs["class"] = "form-control"

    @property
    def cuenta_pendiente(self):
        """El template muestra este error como advertencia, no como error de credenciales."""
        return self.has_error(NON_FIELD_ERRORS, "pendiente_aprobacion")

    def clean_username(self):
        return UsuarioManager.normalizar_email(self.cleaned_data["username"])

    @sensitive_variables()
    def clean(self):
        try:
            return super().clean()
        except DatabaseError:
            self.user_cache = None
            raise forms.ValidationError(
                "No se pudo iniciar sesión. Intentá nuevamente.", code="operacion_fallida"
            ) from None

    @sensitive_variables()
    def get_invalid_login_error(self):
        # Diagnóstico, nunca una segunda vía de autenticación. Todas las ramas
        # fallidas hacen una consulta y una comprobación real o ficticia Django.
        try:
            cuenta = Usuario._default_manager.get_by_natural_key(self.cleaned_data["username"])
        except Usuario.DoesNotExist:
            cuenta = None
        encoded = cuenta.password if cuenta is not None else make_password(None)
        coincide = check_password(self.cleaned_data["password"], encoded)
        if coincide and cuenta is not None and not cuenta.is_active:
            return forms.ValidationError(
                "Tu cuenta está pendiente de aprobación", code="pendiente_aprobacion"
            )
        return super().get_invalid_login_error()
