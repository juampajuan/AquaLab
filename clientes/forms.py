from django import forms

from .models import (
    Cliente,
    normalizar_numero_documento,
    validar_documento,
    validar_telefono,
)

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
    """Paso 1 del registro de cliente: valida y normaliza los datos, pero no guarda en la base."""

    numero_documento = forms.CharField(
        label="Número de documento",
        max_length=30,
        strip=True,
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for nombre, campo in self.fields.items():
            if nombre == "tipo_documento":
                campo.widget.attrs["class"] = "form-select"
            else:
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
                    if Cliente.objects.filter(
                        tipo_documento=tipo, numero_documento=numero
                    ).exists():
                        self.add_error(
                            "numero_documento",
                            "Ya existe un cliente registrado con este tipo y número de documento.",
                        )

        return cleaned_data

    def _post_clean(self):
        # La validación de modelo y unicidad ya se ejecutó en `clean()` con datos normalizados.
        pass

    def datos_para_sesion(self):
        """Datos normalizados listos para guardarse en `session['cliente_pendiente']`."""
        return {campo: self.cleaned_data[campo] for campo in CAMPOS_CLIENTE}
