from decimal import ROUND_HALF_UP, Decimal

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.db.models.functions import Lower

from pruebas.limites import Evaluacion


class TipoEstudio(models.Model):
    nombre = models.CharField("nombre", max_length=150)
    descripcion = models.TextField("descripción", blank=True, default="")
    activo = models.BooleanField("activo", default=True)
    version = models.PositiveBigIntegerField("versión", default=1, editable=False)
    pruebas = models.ManyToManyField("pruebas.Prueba", through="TipoEstudioPrueba")

    class Meta:
        ordering = ("nombre", "pk")
        permissions = [("gestionar_catalogo", "Puede gestionar el catálogo de tipos de estudio")]
        constraints = [
            models.UniqueConstraint(Lower("nombre"), name="tipo_estudio_nombre_unico_ci"),
            models.CheckConstraint(condition=~Q(nombre=""), name="tipo_estudio_nombre_no_vacio"),
            models.CheckConstraint(
                condition=Q(version__gte=1), name="tipo_estudio_version_positiva"
            ),
        ]

    def __str__(self):
        return self.nombre

    def save(self, *args, **kwargs):
        self.nombre = self.nombre.strip()
        return super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        self.nombre = self.nombre.strip()


class TipoEstudioPrueba(models.Model):
    tipo = models.ForeignKey(TipoEstudio, on_delete=models.CASCADE)
    prueba = models.ForeignKey("pruebas.Prueba", on_delete=models.PROTECT)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("tipo", "prueba"), name="tipo_prueba_unica"),
        ]

    def __str__(self):
        return f"{self.tipo} · {self.prueba}"


class EstadoEstudio(models.TextChoices):
    PENDIENTE_ANALISIS = "pendiente_analisis", "Pendiente de análisis"
    EN_PROCESO = "en_proceso", "En proceso"
    FINALIZADO = "finalizado", "Finalizado"
    INFORME_GENERADO = "informe_generado", "Informe generado"


class EstadoPruebaEstudio(models.TextChoices):
    PENDIENTE = "pendiente", "Pendiente"
    CARGADA = "cargada", "Cargada"
    COMPLETADA = "completada", "Completada"


class Estudio(models.Model):
    muestra = models.ForeignKey(
        "muestras.Muestra", on_delete=models.PROTECT, related_name="estudios"
    )
    tipo = models.ForeignKey(TipoEstudio, on_delete=models.PROTECT, related_name="estudios")
    estado = models.CharField(
        max_length=30,
        choices=EstadoEstudio.choices,
        default=EstadoEstudio.PENDIENTE_ANALISIS,
        editable=False,
    )
    creado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="estudios_creados",
        editable=False,
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    tipo_nombre_snapshot = models.CharField(max_length=150, editable=False)
    tipo_descripcion_snapshot = models.TextField(blank=True, default="", editable=False)
    tipo_version_snapshot = models.PositiveBigIntegerField(editable=False)
    clave_idempotencia = models.UUIDField(unique=True, editable=False)

    class Meta:
        ordering = ("-pk",)
        constraints = [
            models.CheckConstraint(
                condition=Q(tipo_version_snapshot__gte=1), name="estudio_version_positiva"
            ),
        ]

    def __str__(self):
        return f"Estudio {self.pk} · {self.tipo_nombre_snapshot}"

    @property
    def admite_modificaciones(self):
        return self.estado == EstadoEstudio.PENDIENTE_ANALISIS

    @property
    def admite_mediciones(self):
        return self.estado in (EstadoEstudio.PENDIENTE_ANALISIS, EstadoEstudio.EN_PROCESO)

    @property
    def admite_correcciones(self):
        """Mediciones y resultados se pueden cambiar (y recalcular) hasta emitir el informe."""
        return self.estado != EstadoEstudio.INFORME_GENERADO


class PruebaEstudio(models.Model):
    estudio = models.ForeignKey(Estudio, on_delete=models.PROTECT, related_name="pruebas_asignadas")
    prueba = models.ForeignKey("pruebas.Prueba", on_delete=models.PROTECT)
    estado = models.CharField(
        "estado",
        max_length=20,
        choices=EstadoPruebaEstudio.choices,
        default=EstadoPruebaEstudio.PENDIENTE,
        editable=False,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("estudio", "prueba"), name="estudio_prueba_unica"),
        ]

    def __str__(self):
        return f"{self.estudio} · {self.prueba}"

    def puede_quitarse(self):
        """Solo una prueba Pendiente: Cargada y Completada tienen mediciones o resultados.

        La carga de mediciones (US 6.1) la pasa a Cargada; los resultados del Epic 6 deben
        pasarla a Completada y referenciar a PruebaEstudio con on_delete=PROTECT.
        """
        return self.estado == EstadoPruebaEstudio.PENDIENTE


class Medicion(models.Model):
    asignacion = models.OneToOneField(
        PruebaEstudio, on_delete=models.PROTECT, related_name="medicion", editable=False
    )
    valor = models.DecimalField("valor", max_digits=18, decimal_places=6)
    decimales = models.PositiveSmallIntegerField("decimales")
    unidad = models.CharField("unidad", max_length=50, blank=True, default="")
    cargada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="mediciones_cargadas",
        editable=False,
    )
    fecha_carga = models.DateTimeField("fecha de carga", auto_now_add=True)
    corregida_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.PROTECT,
        related_name="mediciones_corregidas",
        editable=False,
    )
    fecha_correccion = models.DateTimeField("fecha de corrección", null=True, blank=True)

    class Meta:
        verbose_name = "medición"
        verbose_name_plural = "mediciones"
        constraints = [
            models.CheckConstraint(
                condition=Q(decimales__lte=6), name="medicion_decimales_validos"
            ),
            models.CheckConstraint(
                condition=Q(corregida_por__isnull=True, fecha_correccion__isnull=True)
                | Q(corregida_por__isnull=False, fecha_correccion__isnull=False),
                name="medicion_correccion_completa",
            ),
        ]

    def __str__(self):
        return f"{self.asignacion} = {self.valor_ingresado} {self.unidad}".rstrip()

    @property
    def valor_ingresado(self):
        """El valor con los decimales que escribió el analista (7,20 y no 7,200000)."""
        return self.valor.quantize(Decimal(1).scaleb(-self.decimales))


class Resultado(models.Model):
    asignacion = models.OneToOneField(
        PruebaEstudio, on_delete=models.PROTECT, related_name="resultado", editable=False
    )
    valor = models.DecimalField("valor", max_digits=28, decimal_places=10)
    unidad = models.CharField("unidad", max_length=50, blank=True, default="")
    formula = models.CharField("fórmula", max_length=255, blank=True, default="")
    fecha_calculo = models.DateTimeField("fecha de cálculo", auto_now=True)

    class Meta:
        verbose_name = "resultado"
        verbose_name_plural = "resultados"

    def __str__(self):
        return f"{self.asignacion} = {self.valor_mostrado} {self.unidad}".rstrip()

    @property
    def valor_mostrado(self):
        """Hasta 4 decimales y sin ceros finales (23,5; 0,0041); el guardado conserva 10."""
        valor = self.valor.quantize(Decimal("0.0001"), ROUND_HALF_UP).normalize()
        if not valor:
            return Decimal(0)
        # normalize() escribe 80 como 8E+1; un entero vuelve a exponente 0.
        return valor.quantize(Decimal(1)) if valor.as_tuple().exponent > 0 else valor


class OrigenLimites(models.TextChoices):
    GENERAL = "general", "Generales"
    CLOACAL = "cloacal", "Cloacal"
    CANAL = "canal", "Canal"


class Validacion(models.Model):
    """Un bioquímico confirmó el resultado de una prueba del estudio (US 6.4).

    Hay a lo sumo una vigente por prueba, y la hay si y solo si la prueba está Completada. Cuando
    deja de estarlo (recálculo o borrado de la medición) se anula y se conserva como historial.
    """

    asignacion = models.ForeignKey(
        PruebaEstudio, on_delete=models.PROTECT, related_name="validaciones", editable=False
    )
    validada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="validaciones",
        editable=False,
    )
    fecha_validacion = models.DateTimeField("fecha de validación", auto_now_add=True)
    limite_min = models.CharField("límite mínimo", max_length=50, blank=True, default="")
    limite_max = models.CharField("límite máximo", max_length=50, blank=True, default="")
    norma = models.CharField("norma", max_length=150, blank=True, default="")
    origen_limites = models.CharField(
        "origen de los límites", max_length=10, choices=OrigenLimites.choices
    )
    evaluacion = models.CharField("evaluación", max_length=20, choices=Evaluacion.choices)
    anulada = models.BooleanField("anulada", default=False)
    fecha_anulacion = models.DateTimeField("fecha de anulación", null=True, blank=True)

    class Meta:
        verbose_name = "validación"
        verbose_name_plural = "validaciones"
        permissions = [("validar_resultados", "Puede validar resultados")]
        constraints = [
            models.UniqueConstraint(
                fields=["asignacion"],
                condition=Q(anulada=False),
                name="validacion_vigente_unica",
            ),
            models.CheckConstraint(
                condition=Q(anulada=False, fecha_anulacion__isnull=True)
                | Q(anulada=True, fecha_anulacion__isnull=False),
                name="validacion_anulacion_completa",
            ),
        ]

    def __str__(self):
        estado = " (anulada)" if self.anulada else ""
        return f"{self.asignacion}: {self.get_evaluacion_display()}{estado}"
