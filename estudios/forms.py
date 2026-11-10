from django import forms

from clientes.models import Cliente
from muestras.forms import SelectorFecha
from muestras.models import Muestra, Origen
from pruebas.limites import Evaluacion
from pruebas.models import Prueba

from .mediciones import OPCIONES_PRESENCIA, es_presencia, leer_valor, texto_presencia
from .models import EstadoEstudio, TipoEstudio

MAX_LONGITUD_BUSQUEDA = 100
MAX_ENTERO_BUSQUEDA = 9_223_372_036_854_775_807
FORMATOS_FECHA = ["%Y-%m-%d", "%d/%m/%Y"]
MENSAJE_FECHA_INVALIDA = "Ingresá una fecha válida (dd/mm/aaaa)."
CAMPOS_FILTRO = ("desde", "hasta", "estado")


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
        help_text=(
            "Define las pruebas con las que nace el estudio. Mientras no tenga mediciones se "
            "pueden agregar o quitar."
        ),
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
            queryset=Prueba.objects.filter(activa=True).exclude(
                pk__in=estudio.pruebas_asignadas.values("prueba")
            ),
            label="Prueba",
            empty_label="Elegí una prueba",
            help_text=(
                "Solo se listan las pruebas activas del catálogo que el estudio todavía no tiene."
            ),
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


# Id de la ayuda del encabezado «Medición» (cargar y corregir mediciones, US 9.1).
AYUDA_MEDICION = "ayuda-medicion"


def campo_medicion(asignacion, **kwargs):
    """Campo de texto para el valor; en las pruebas A/P, un selector Ausente/Presente."""
    if es_presencia(asignacion.prueba.unidad_medicion):
        campo = forms.CharField(
            required=False,
            max_length=40,
            label=str(asignacion.prueba),
            widget=forms.Select(choices=OPCIONES_PRESENCIA),
            **kwargs,
        )
        campo.widget.attrs.update({"class": "form-select", "aria-describedby": AYUDA_MEDICION})
        return campo
    campo = forms.CharField(required=False, max_length=40, label=str(asignacion.prueba), **kwargs)
    campo.widget.attrs.update(
        {
            "inputmode": "decimal",
            "autocomplete": "off",
            "class": "form-control",
            "aria-describedby": AYUDA_MEDICION,
        }
    )
    return campo


def leer_medicion(asignacion, texto):
    return leer_valor(texto, presencia=es_presencia(asignacion.prueba.unidad_medicion))


class CargarMedicionesForm(forms.Form):
    """Un campo opcional `medicion_<asignacion_pk>` por prueba del estudio."""

    def __init__(self, *args, asignaciones, **kwargs):
        super().__init__(*args, **kwargs)
        self.asignaciones = list(asignaciones)
        self._valores = {}
        for asignacion in self.asignaciones:
            self.fields[self.nombre(asignacion)] = campo_medicion(asignacion)

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
                valor = leer_medicion(asignacion, datos[nombre])
            except forms.ValidationError as exc:
                self.add_error(nombre, exc)
                attrs = self.fields[nombre].widget.attrs
                attrs["class"] += " is-invalid"
                attrs["aria-describedby"] = f"{AYUDA_MEDICION} {self[nombre].auto_id}_error"
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
            if vigente and es_presencia(asignacion.prueba.unidad_medicion):
                visible = texto_presencia(asignacion.medicion.valor)
            else:
                visible = vigente.replace(".", ",")
            self.fields[self.nombre(asignacion)] = campo_medicion(asignacion, initial=visible)
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
                valor = leer_medicion(asignacion, datos[nombre])
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
                attrs["aria-describedby"] = f"{AYUDA_MEDICION} {self[nombre].auto_id}_error"

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


class FiltrosEstudioForm(forms.Form):
    """Filtros de estudios por GET (SCRUM-74): rango de fechas y estado, todos opcionales.

    Es la única definición de estos filtros: la heredan el historial del cliente (US 3.3,
    `HistorialClienteForm`) y «Buscar estudio» (`FiltrarEstudiosForm`). Qué fecha se filtra lo
    decide cada vista. Mostrar «Limpiar filtros» tampoco se decide acá: las vistas lo hacen con los
    parámetros recibidos, válidos o no.
    """

    desde = forms.DateField(
        label="Desde",
        required=False,
        input_formats=FORMATOS_FECHA,
        widget=SelectorFecha(),
        error_messages={"invalid": MENSAJE_FECHA_INVALIDA},
    )
    hasta = forms.DateField(
        label="Hasta",
        required=False,
        input_formats=FORMATOS_FECHA,
        widget=SelectorFecha(),
        error_messages={"invalid": MENSAJE_FECHA_INVALIDA},
    )
    estado = forms.ChoiceField(
        label="Estado",
        required=False,
        choices=[("", "Todos"), *EstadoEstudio.choices],
        error_messages={"invalid_choice": "Elegí un estado de la lista."},
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for nombre in CAMPOS_FILTRO:
            campo = self.fields[nombre]
            clase = "form-select" if isinstance(campo.widget, forms.Select) else "form-control"
            campo.widget.attrs["class"] = clase

    def full_clean(self):
        super().full_clean()
        for nombre in self.errors:
            if nombre in CAMPOS_FILTRO:
                self.fields[nombre].widget.attrs["class"] += " is-invalid"

    def clean(self):
        datos = super().clean()
        desde, hasta = datos.get("desde"), datos.get("hasta")
        if desde and hasta and desde > hasta:
            self.add_error("desde", "La fecha desde no puede ser posterior a la fecha hasta.")
        return datos


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


class FiltrarEstudiosForm(BuscarEstudioForm, FiltrosEstudioForm):
    """Búsqueda de estudios con filtros (SCRUM-74): texto (US 5.2), estado y fecha de creación.

    `BuscarEstudioForm` queda solo con el texto: lo usa también `informes:listar`.
    """

    pendiente = forms.ChoiceField(
        label="Trabajo pendiente",
        required=False,
        choices=[
            ("", "Todos"),
            ("mediciones", "Mediciones por cargar"),
            ("validaciones", "Resultados por validar"),
        ],
        help_text=(
            "Seleccioná estudios con mediciones por cargar o resultados calculados por validar."
        ),
        widget=forms.Select(attrs={"class": "form-select"}),
        error_messages={"invalid_choice": "Elegí una categoría de pendientes de la lista."},
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        ayuda = "Fecha en que se creó el estudio. El día indicado se incluye."
        self.fields["desde"].help_text = ayuda
        self.fields["hasta"].help_text = ayuda

    def full_clean(self):
        super().full_clean()
        if "pendiente" in self.errors:
            self.fields["pendiente"].widget.attrs["class"] += " is-invalid"


class ValidarResultadosForm(forms.Form):
    """Por cada prueba con resultado, `validar_<pk>` (marcada al abrir solo si cumple) y
    `resultado_<pk>` (el valor que se vio, para no validar uno que cambió mientras tanto). Las
    filas con desvío sin revisar (`asignacion.deteccion`, US 8.2) suman `observacion_<pk>`: queda
    en la validación como revisión del desvío."""

    def __init__(self, *args, filas, marcar_todas=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.asignaciones = list(filas)
        for asignacion in self.asignaciones:
            resultado = getattr(asignacion, "resultado", None)
            self.fields[self.validar(asignacion)] = forms.BooleanField(
                required=False,
                label=f"Validar {asignacion.prueba.codigo}",
                initial=marcar_todas or asignacion.evaluacion == Evaluacion.CUMPLE,
            )
            self.fields[self.resultado(asignacion)] = forms.CharField(
                required=False,
                widget=forms.HiddenInput,
                initial=str(resultado.valor) if resultado else "",
            )
            if self.tiene_desvio(asignacion):
                self.fields[self.observacion(asignacion)] = forms.CharField(
                    required=False,
                    max_length=500,
                    label=f"Observación {asignacion.prueba.codigo}",
                    help_text=(
                        "Queda guardada en la validación de esta prueba como revisión del desvío. "
                        "Solo la ve el laboratorio."
                    ),
                    widget=forms.Textarea(attrs={"rows": 2}),
                )

    @staticmethod
    def validar(asignacion):
        return f"validar_{asignacion.pk}"

    @staticmethod
    def resultado(asignacion):
        return f"resultado_{asignacion.pk}"

    @staticmethod
    def observacion(asignacion):
        return f"observacion_{asignacion.pk}"

    @staticmethod
    def tiene_desvio(asignacion):
        """Desvío sin revisar: los ya revisados traen la constancia en `validacion_desvio`."""
        return bool(getattr(asignacion, "deteccion", None)) and not getattr(
            asignacion, "validacion_desvio", None
        )

    def clean(self):
        datos = super().clean()
        if not self.errors and not self.resumen():
            raise forms.ValidationError("Elegí al menos un resultado para validar.")
        return datos

    def filas(self):
        return [
            (
                a,
                self[self.validar(a)],
                self[self.resultado(a)],
                self[self.observacion(a)] if self.tiene_desvio(a) else None,
            )
            for a in self.asignaciones
        ]

    def con_desvio(self):
        return [a for a in self.asignaciones if self.tiene_desvio(a)]

    def elegidas_con_desvio(self):
        """Las marcadas que tienen desvío, con la observación escrita en `observacion_escrita`."""
        elegidas = [a for a in self.resumen() if self.tiene_desvio(a)]
        for asignacion in elegidas:
            asignacion.observacion_escrita = self.cleaned_data.get(self.observacion(asignacion))
        return elegidas

    def observaciones(self):
        """`{asignacion_pk: texto}` de las marcadas con desvío, para el servicio."""
        return {
            a.pk: self.cleaned_data.get(self.observacion(a), "")
            for a in self.resumen()
            if self.tiene_desvio(a)
        }

    def resumen(self):
        """Las asignaciones marcadas para validar."""
        return [a for a in self.asignaciones if self.cleaned_data.get(self.validar(a))]

    def elegidas(self):
        """`{asignacion_pk: valor_visto}` de las marcadas, para el servicio."""
        return {a.pk: self.cleaned_data[self.resultado(a)] for a in self.resumen()}

    def fuera_de_norma(self):
        return [a for a in self.asignaciones if a.evaluacion == Evaluacion.FUERA_DE_NORMA]


class ElegirPruebasForm(forms.Form):
    """Pruebas que se muestran en la comparación histórica (US 8.1). Va por GET, así el enlace
    conserva la selección. Sin `elegir` (primera visita) se muestran todas."""

    pruebas = forms.MultipleChoiceField(
        label="Pruebas a mostrar",
        required=False,
        widget=forms.CheckboxSelectMultiple,
        help_text=(
            "Las pruebas cuya evolución se dibuja. El enlace de la página guarda la selección."
        ),
    )
    elegir = forms.CharField(required=False, widget=forms.HiddenInput)

    def __init__(self, datos=None, *, disponibles):
        self.codigos = [p.codigo for p in disponibles]
        if datos is not None and datos.get("elegir"):
            # Un código que no está entre las opciones (enlace viejo o armado a mano) se ignora.
            datos = datos.copy()
            datos.setlist("pruebas", [c for c in datos.getlist("pruebas") if c in self.codigos])
            super().__init__(datos)
        else:
            super().__init__(initial={"pruebas": self.codigos, "elegir": "1"})
        self.fields["pruebas"].choices = [
            (p.codigo, f"{p.nombre} ({p.codigo})") for p in disponibles
        ]

    def clean(self):
        datos = super().clean()
        if not datos.get("pruebas"):
            self.add_error("pruebas", "Elegí al menos una prueba para ver su evolución.")
        return datos

    def elegidas(self):
        """Los códigos a mostrar: todos sin selección; ninguno si la selección es inválida."""
        if not self.is_bound:
            return list(self.codigos)
        return self.cleaned_data["pruebas"] if self.is_valid() else []


class ClienteChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return obj.nombre_completo


class ElegirOrigenForm(forms.Form):
    """Cliente y origen para la comparación histórica desde el dashboard (US 8.1).

    Sin JavaScript, los orígenes van agrupados por cliente; con solo el cliente elegido (paso 2),
    se ofrecen solo los suyos. `elegir_origen.js` filtra la lista al cambiar el cliente.
    """

    cliente = ClienteChoiceField(
        queryset=Cliente.objects.filter(activo=True),
        label="Cliente",
        empty_label="Elegí un cliente",
        help_text="El cliente dueño del punto de muestreo. Solo se listan los clientes activos.",
    )
    origen = forms.ModelChoiceField(
        queryset=Origen.objects.filter(cliente__activo=True).select_related("cliente"),
        label="Origen",
        empty_label="Elegí un origen",
        help_text="El punto de muestreo cuya evolución se quiere ver.",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        clientes = sorted(
            self.fields["cliente"].queryset, key=lambda c: (c.nombre_completo.casefold(), c.pk)
        )
        self.fields["cliente"].choices = [("", "Elegí un cliente")] + [
            (c.pk, c.nombre_completo) for c in clientes
        ]
        self.por_cliente = {
            c.pk: sorted(
                (o for o in self.fields["origen"].queryset if o.cliente_id == c.pk),
                key=lambda o: o.nombre.casefold(),
            )
            for c in clientes
        }
        elegido = self.data.get("cliente") if self.is_bound else None
        elegido = int(elegido) if elegido and str(elegido).isdigit() else None
        if elegido in self.por_cliente:
            opciones = [(o.pk, o.nombre) for o in self.por_cliente[elegido]]
        else:
            opciones = [
                (c.nombre_completo, [(o.pk, o.nombre) for o in self.por_cliente[c.pk]])
                for c in clientes
                if self.por_cliente[c.pk]
            ]
        self.fields["origen"].choices = [("", "Elegí un origen"), *opciones]

    def clean(self):
        datos = super().clean()
        cliente, origen = datos.get("cliente"), datos.get("origen")
        if cliente and origen and origen.cliente_id != cliente.pk:
            self.add_error("origen", "El origen no pertenece al cliente elegido.")
        return datos

    def origenes_por_cliente(self):
        """Para `json_script`: `{cliente_pk: [[origen_pk, nombre], …]}`."""
        return {
            str(pk): [[o.pk, o.nombre] for o in origenes]
            for pk, origenes in self.por_cliente.items()
        }
