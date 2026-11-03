from django import forms


class OperacionForm(forms.Form):
    accion = forms.ChoiceField(choices=[("confirmar", "Confirmar"), ("cancelar", "Cancelar")])
    token = forms.CharField(widget=forms.HiddenInput)

    def clean(self):
        datos = super().clean()
        if set(self.data) - {"csrfmiddlewaretoken", *self.fields}:
            raise forms.ValidationError("El envío contiene campos no permitidos.")
        if any(len(self.data.getlist(k)) != 1 for k in self.data):
            raise forms.ValidationError("El envío contiene campos repetidos.")
        return datos


class RolForm(OperacionForm):
    token = None
    accion = forms.ChoiceField(choices=[("revisar", "Revisar")])
    contexto = forms.CharField(widget=forms.HiddenInput)
    rol = forms.ChoiceField(
        label="Nuevo rol profesional",
        choices=[("comun", "Usuario común"), ("bioquimico", "Bioquímico")],
        widget=forms.Select(attrs={"class": "form-select"}),
    )

    def __init__(self, *args, rol_actual, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["rol"].choices = [
            (valor, etiqueta)
            for valor, etiqueta in self.fields["rol"].choices
            if valor != rol_actual
        ]
