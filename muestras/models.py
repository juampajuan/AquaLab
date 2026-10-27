from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q
from django.db.models.functions import Lower

NUMERO_PI_INICIAL = 200001


class TipoVertido(models.TextChoices):
    AGUA = "agua", "Agua"
    CLOACAL = "cloacal", "Cloacal"
    CANAL = "canal", "Canal"


class EstadoMuestra(models.TextChoices):
    INGRESADA = "ingresada", "Ingresada"


class Origen(models.Model):
    """Fuente de agua de un cliente (ej. "Pozo N°2"), reutilizable en sus próximas muestras."""

    cliente = models.ForeignKey(
        "clientes.Cliente",
        on_delete=models.PROTECT,
        related_name="origenes",
        verbose_name="cliente",
    )
    nombre = models.CharField("nombre", max_length=150)
    fecha_alta = models.DateTimeField("fecha de alta", auto_now_add=True)

    class Meta:
        verbose_name = "origen"
        verbose_name_plural = "orígenes"
        ordering = ("nombre",)
        constraints = [
            models.UniqueConstraint(
                Lower("nombre"),
                F("cliente"),
                name="origen_nombre_unico_por_cliente",
                violation_error_message="El cliente ya tiene un origen con ese nombre.",
            ),
        ]

    def __str__(self):
        return self.nombre

    def clean(self):
        super().clean()
        self.nombre = (self.nombre or "").strip()


class Muestra(models.Model):
    numero_pi = models.PositiveIntegerField("N° PI", unique=True, editable=False)
    nombre = models.CharField("nombre", max_length=100)
    cliente = models.ForeignKey(
        "clientes.Cliente",
        on_delete=models.PROTECT,
        related_name="muestras",
        verbose_name="cliente",
    )
    origen = models.ForeignKey(
        Origen,
        on_delete=models.PROTECT,
        related_name="muestras",
        verbose_name="origen",
    )
    fecha_muestreo = models.DateField("fecha de muestreo")
    fecha_ingreso = models.DateField("fecha de ingreso")
    sitio_extraccion = models.CharField("sitio de extracción", max_length=200)
    tipo_vertido = models.CharField(
        "tipo de vertido",
        max_length=10,
        choices=TipoVertido.choices,
        default=TipoVertido.AGUA,
    )
    responsable_muestreo = models.CharField("responsable del muestreo", max_length=150, blank=True)
    estado = models.CharField(
        "estado",
        max_length=20,
        choices=EstadoMuestra.choices,
        default=EstadoMuestra.INGRESADA,
        editable=False,
    )
    registrada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        editable=False,
        related_name="muestras_registradas",
        verbose_name="registrada por",
    )
    fecha_registro = models.DateTimeField("fecha de registro", auto_now_add=True)
    # Identifica el borrador confirmado: dos confirmaciones simultáneas del mismo borrador
    # registran una sola muestra.
    clave_borrador = models.UUIDField(
        "clave del borrador", unique=True, null=True, blank=True, editable=False
    )

    class Meta:
        verbose_name = "muestra"
        verbose_name_plural = "muestras"
        ordering = ("-numero_pi",)
        constraints = [
            models.CheckConstraint(
                condition=Q(numero_pi__gte=NUMERO_PI_INICIAL),
                name="muestra_numero_pi_desde_200001",
            ),
            models.CheckConstraint(
                condition=Q(fecha_muestreo__lte=F("fecha_ingreso")),
                name="muestra_muestreo_no_posterior_a_ingreso",
            ),
        ]

    def __str__(self):
        return f"N° PI {self.numero_pi} – {self.nombre}"

    def clean(self):
        super().clean()
        errores = {}
        if self.origen_id and self.cliente_id and self.origen.cliente_id != self.cliente_id:
            errores["origen"] = "El origen no pertenece al cliente seleccionado."
        if self.fecha_muestreo and self.fecha_ingreso and self.fecha_muestreo > self.fecha_ingreso:
            errores["fecha_muestreo"] = (
                "La fecha de muestreo no puede ser posterior a la fecha de ingreso."
            )
        if errores:
            raise ValidationError(errores)
