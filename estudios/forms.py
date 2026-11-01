from django import forms

from muestras.models import Muestra
from pruebas.models import Prueba

from .mediciones import leer_valor
from .models import TipoEstudio

MAX_LONGITUD_BUSQUEDA = 100
MAX_ENTERO_BUSQUEDA = 9_223_372_036_854_775_807


class MuestraChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return f"PI {obj.numero_pi} · {obj.cliente.nombre_completo} · {obj.origen.nombre}"


class CrearEstudioForm(forms.Form):
    muestra = MuestraChoiceField(
        queryset=Muestra.objects.select_related("cliente", "origen"),
        label="Muestra",
        empty_label="Elegí una muestra",
    )
    tipo = forms.ModelChoiceField(
        queryset=TipoEstudio.objects.filter(activo=True),
        label="Tipo de estudio",
        empty_label="Elegí un tipo",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for campo in self.fields.values():
            campo.widget.attrs["class"] = "form-select"


class AgregarPruebaForm(forms.Form):
    def __init__(self, *args, estudio, **kwargs):
        super().__init__(*args, **kwargs)
        self.estudio = estudio
        self.fields["prueba"] = forms.ModelChoiceField(
            queryset=Prueba.objects.exclude(pk__in=estudio.pruebas_asignadas.values("prueba")),
            label="Prueba",
            empty_label="Elegí una prueba",
        )
        self.fields["prueba"].widget.attrs["class"] = "form-select"

    def full_clean(self):
        super().full_clean()
        if "prueba" in self.errors:
            self.fields["prueba"].widget.attrs["class"] += " is-invalid"

    def prueba_ya_asignada(self):
        """Prueba enviada que ya forma parte del estudio (reenvío), o `None`."""
        asignadas = Prueba.objects.filter(pk__in=self.estudio.pruebas_asignadas.values("prueba"))
        try:
            return forms.ModelChoiceField(queryset=asignadas).clean(self.data.get("prueba"))
        except forms.ValidationError:
            return None


class CargarMedicionesForm(forms.Form):
    """Un campo opcional `medicion_<asignacion_pk>` por prueba del estudio."""

    def __init__(self, *args, asignaciones, **kwargs):
        super().__init__(*args, **kwargs)
        self.asignaciones = list(asignaciones)
        self._valores = {}
        for asignacion in self.asignaciones:
            campo = forms.CharField(required=False, max_length=40, label=str(asignacion.prueba))
            campo.widget.attrs.update(
                {"inputmode": "decimal", "autocomplete": "off", "class": "form-control"}
            )
            self.fields[self.nombre(asignacion)] = campo

    @staticmethod
    def nombre(asignacion):
        return f"medicion_{asignacion.pk}"

    def clean(self):
        datos = super().clean()
        self._valores = {}
        for asignacion in self.asignaciones:
            nombre = self.nombre(asignacion)
            if nombre not in datos:
                continue
            try:
                valor = leer_valor(datos[nombre])
            except forms.ValidationError as exc:
                self.add_error(nombre, exc)
                attrs = self.fields[nombre].widget.attrs
                attrs["class"] += " is-invalid"
                attrs["aria-describedby"] = f"{self[nombre].auto_id}_error"
                continue
            if valor is not None:
                self._valores[asignacion.pk] = valor
        if not self._valores and not self.errors:
            raise forms.ValidationError("Ingresá al menos una medición.")
        return datos

    def pruebas_quitadas(self):
        """Valores enviados para asignaciones que ya no son del estudio (pruebas quitadas)."""
        propios = set(self.fields)
        return sum(
            1
            for nombre, texto in self.data.items()
            if nombre.startswith("medicion_") and nombre not in propios and texto.strip()
        )

    def filas(self):
        return [(a, self[self.nombre(a)]) for a in self.asignaciones]

    def valores(self):
        return dict(self._valores)

    def resumen(self):
        """`(asignacion, nombre, texto)` de las pruebas con valor, para revisar y reenviar."""
        return [
            (a, self.nombre(a), self.cleaned_data[self.nombre(a)].strip())
            for a in self.asignaciones
            if a.pk in self._valores
        ]


class CorregirMedicionesForm(forms.Form):
    """Por cada prueba con medición, `medicion_<pk>` (el valor corregido, precargado),
    `original_<pk>` (el valor que se vio al abrir, para detectar cambios ajenos) y `borrar_<pk>`."""

    def __init__(self, *args, asignaciones, **kwargs):
        super().__init__(*args, **kwargs)
        self.asignaciones = list(asignaciones)
        self._nuevos, self._originales, self._borrar = {}, {}, set()
        for asignacion in self.asignaciones:
            # Al confirmar puede venir una asignación cuya medición ya se borró (reenvío).
            if hasattr(asignacion, "medicion"):
                vigente = str(asignacion.medicion.valor_ingresado)
            else:
                vigente = ""
            campo = forms.CharField(
                required=False,
                max_length=40,
                label=str(asignacion.prueba),
                initial=vigente.replace(".", ","),
            )
            campo.widget.attrs.update(
                {"inputmode": "decimal", "autocomplete": "off", "class": "form-control"}
            )
            self.fields[self.nombre(asignacion)] = campo
            self.fields[self.original(asignacion)] = forms.CharField(
                widget=forms.HiddenInput, initial=vigente
            )
            self.fields[self.borrar(asignacion)] = forms.BooleanField(
                required=False, label=f"Borrar la medición de {asignacion.prueba.codigo}"
            )

    @staticmethod
    def nombre(asignacion):
        return f"medicion_{asignacion.pk}"

    @staticmethod
    def original(asignacion):
        return f"original_{asignacion.pk}"

    @staticmethod
    def borrar(asignacion):
        return f"borrar_{asignacion.pk}"

    def clean(self):
        datos = super().clean()
        self._nuevos, self._originales, self._borrar = {}, {}, set()
        for asignacion in self.asignaciones:
            nombre = self.nombre(asignacion)
            try:
                self._originales[asignacion.pk] = leer_valor(datos.get(self.original(asignacion)))
            except forms.ValidationError:
                self._originales[asignacion.pk] = None
            if self._originales[asignacion.pk] is None:
                raise forms.ValidationError(
                    "La solicitud no es válida. Volvé a abrir la corrección."
                )
            if datos.get(self.borrar(asignacion)):
                # Prevalece el borrado: el valor escrito no se valida.
                self._errors.pop(nombre, None)
                self._borrar.add(asignacion.pk)
                continue
            if nombre not in datos:
                continue
            try:
                valor = leer_valor(datos[nombre])
            except forms.ValidationError as exc:
                self.add_error(nombre, exc)
                continue
            if valor is None:
                self.add_error(nombre, "La medición no puede quedar vacía.")
            else:
                self._nuevos[asignacion.pk] = valor
        if not self.errors and not self.cambios():
            raise forms.ValidationError("No hay cambios para guardar.")
        return datos

    def full_clean(self):
        super().full_clean()
        for asignacion in self.asignaciones:
            nombre = self.nombre(asignacion)
            if nombre in self.errors:
                attrs = self.fields[nombre].widget.attrs
                attrs["class"] += " is-invalid"
                attrs["aria-describedby"] = f"{self[nombre].auto_id}_error"

    def filas(self):
        return [
            (a, self[self.nombre(a)], self[self.original(a)], self[self.borrar(a)])
            for a in self.asignaciones
        ]

    def originales(self):
        return dict(self._originales)

    def cambios(self):
        """`(asignacion, anterior, nuevo)` de las filas cuyo valor escrito difiere del que se vio
        al abrir (con sus decimales: 7,2 ≠ 7,20), con `nuevo = None` para las marcadas para borrar.
        Nunca se compara con la base: si otro empleado la cambió mientras tanto, el servicio lo
        detecta e informa."""
        cambios = []
        for a in self.asignaciones:
            if a.pk in self._borrar:
                cambios.append((a, self._originales[a.pk], None))
            elif a.pk in self._nuevos and str(self._nuevos[a.pk]) != str(self._originales[a.pk]):
                cambios.append((a, self._originales[a.pk], self._nuevos[a.pk]))
        return cambios


class BuscarEstudioForm(forms.Form):
    """Texto de búsqueda de estudios (por GET): identificador, muestra, cliente o tipo."""

    q = forms.CharField(
        label="Identificador, muestra, cliente o tipo de estudio",
        required=False,
        max_length=MAX_LONGITUD_BUSQUEDA,
        strip=True,
        error_messages={
            "max_length": "Ingresá como máximo 100 caracteres para buscar.",
        },
    )

    def clean_q(self):
        valor = (self.cleaned_data.get("q") or "").strip()
        if not valor:
            return ""
        if valor.isdigit():
            try:
                if not valor.isascii():
                    raise ValueError
                numero = int(valor)
            except ValueError as exc:
                raise forms.ValidationError("Ingresá un número válido para buscar.") from exc
            if numero < 1 or numero > MAX_ENTERO_BUSQUEDA:
                raise forms.ValidationError("Ingresá un número válido para buscar.")
            return valor
        if len(valor) < 2:
            raise forms.ValidationError("Ingresá al menos 2 caracteres para buscar.")
        return valor
