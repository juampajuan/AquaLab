from django.conf import settings
from django.db import models
from django.db.models import Q
from django.db.models.functions import Lower


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


class PruebaEstudio(models.Model):
    estudio = models.ForeignKey(Estudio, on_delete=models.PROTECT, related_name="pruebas_asignadas")
    prueba = models.ForeignKey("pruebas.Prueba", on_delete=models.PROTECT)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=("estudio", "prueba"), name="estudio_prueba_unica"),
        ]

    def __str__(self):
        return f"{self.estudio} · {self.prueba}"
