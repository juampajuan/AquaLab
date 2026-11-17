import base64

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import F, Q


class Informe(models.Model):
    """Informe emitido de un estudio (US 7.2), con la copia de todo lo que se mostró.

    `contenido` se arma con `informes.contenido.armar_contenido` y no cambia: el informe emitido
    se muestra siempre desde esa copia, aunque después se editen el cliente o el catálogo. Es
    inalterable (US 7.3): no está en el admin y `save()`/`delete()` rechazan cambiarlo o borrarlo.
    """

    numero = models.PositiveIntegerField("número", unique=True, editable=False)
    estudio = models.OneToOneField(
        "estudios.Estudio", on_delete=models.PROTECT, related_name="informe", editable=False
    )
    emitido_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="informes_emitidos",
        editable=False,
    )
    fecha_emision = models.DateTimeField("fecha de emisión", auto_now_add=True)
    contenido = models.JSONField("contenido", editable=False)

    class Meta:
        verbose_name = "informe"
        verbose_name_plural = "informes"
        ordering = ("-numero",)
        permissions = [
            ("emitir_informes", "Puede emitir informes"),
            ("ver_dashboard", "Puede ver el dashboard"),
        ]
        constraints = [
            models.CheckConstraint(condition=Q(numero__gte=1), name="informe_numero_positivo"),
        ]

    def __str__(self):
        return f"{self.numero_mostrado} · {self.estudio}"

    def save(self, *args, **kwargs):
        """Solo se guarda al emitir: un informe emitido no se modifica (US 7.3, FR-017)."""
        if not self._state.adding:
            raise ValueError("Un informe emitido no se puede modificar.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Un informe emitido no se borra (US 7.3, FR-017)."""
        raise ValueError("Un informe emitido no se puede borrar.")

    @property
    def numero_mostrado(self):
        return f"INF-{self.numero:06d}"


class BorradorConclusion(models.Model):
    estudio = models.OneToOneField(
        "estudios.Estudio", on_delete=models.PROTECT, related_name="borrador_conclusion"
    )
    revision = models.PositiveBigIntegerField(default=1)
    texto_editorial = models.TextField(blank=True, default="")
    texto_final = models.TextField(blank=True, default="")
    hechos = models.JSONField(default=dict, blank=True)
    huella_hechos = models.CharField(
        max_length=64, validators=[RegexValidator(r"\A[0-9a-f]{64}\Z")]
    )
    advertencias = models.JSONField(default=list, blank=True)
    requiere_revision = models.BooleanField(default=False)
    origen_propuesta = models.CharField(
        max_length=10, choices=[("ia", "IA"), ("plantilla", "Plantilla"), ("manual", "Manual")]
    )
    motivo_respaldo = models.CharField(
        max_length=24,
        blank=True,
        default="",
        choices=[
            (codigo, codigo)
            for codigo in (
                "sin_configuracion",
                "no_disponible",
                "cuota",
                "respuesta_invalida",
                "plazo",
                "capacidad",
                "tamano",
            )
        ],
    )
    solicitud_propuesta = models.UUIDField(null=True, blank=True)
    editado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="conclusiones_editadas",
    )
    fecha_edicion = models.DateTimeField()
    aprobada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="conclusiones_aprobadas",
    )
    nombre_aprobador = models.TextField(blank=True, default="")
    fecha_aprobacion = models.DateTimeField(null=True, blank=True)
    revision_aprobada = models.PositiveBigIntegerField(null=True, blank=True)
    huella_texto_aprobado = models.CharField(
        max_length=64, blank=True, default="", validators=[RegexValidator(r"\A[0-9a-f]{64}\Z")]
    )
    huella_hechos_aprobados = models.CharField(
        max_length=64, blank=True, default="", validators=[RegexValidator(r"\A[0-9a-f]{64}\Z")]
    )

    class Meta:
        default_permissions = ()
        constraints = [
            models.CheckConstraint(
                condition=Q(revision__gte=1), name="conclusion_revision_positiva"
            ),
            models.CheckConstraint(
                condition=(
                    Q(
                        aprobada_por__isnull=True,
                        nombre_aprobador="",
                        fecha_aprobacion__isnull=True,
                        revision_aprobada__isnull=True,
                        huella_texto_aprobado="",
                        huella_hechos_aprobados="",
                    )
                    | (
                        Q(
                            aprobada_por__isnull=False,
                            fecha_aprobacion__isnull=False,
                            revision_aprobada__isnull=False,
                        )
                        & ~Q(nombre_aprobador="")
                        & ~Q(huella_texto_aprobado="")
                        & ~Q(huella_hechos_aprobados="")
                    )
                ),
                name="conclusion_aprobacion_completa",
            ),
            models.CheckConstraint(
                condition=Q(revision_aprobada__isnull=True) | Q(revision_aprobada=F("revision")),
                name="conclusion_revision_aprobada",
            ),
            models.CheckConstraint(
                condition=Q(aprobada_por__isnull=True)
                | Q(huella_hechos_aprobados=F("huella_hechos"), requiere_revision=False),
                name="conclusion_aprobacion_vigente",
            ),
        ]

    def __str__(self):
        return f"Conclusión del estudio {self.estudio_id}, revisión {self.revision}"

    def clean(self):
        super().clean()
        for campo in ("hechos", "advertencias"):
            if not solo_textos(getattr(self, campo)):
                raise ValidationError({campo: "Los hechos deben contener únicamente textos."})
        for campo in ("texto_editorial", "texto_final"):
            if "\x00" in getattr(self, campo):
                raise ValidationError({campo: "El texto contiene un carácter no permitido."})


def solo_textos(valor):
    if isinstance(valor, dict):
        return all(isinstance(k, str) and solo_textos(v) for k, v in valor.items())
    if isinstance(valor, list):
        return all(solo_textos(v) for v in valor)
    return isinstance(valor, str)


class FirmaProfesional(models.Model):
    """Firma manuscrita y matrícula de quien emite informes (US 7.3).

    La imagen es un PNG chico validado por `informes.firmas.leer_firma` y se guarda en la base
    (Render no conserva los archivos subidos). Al emitir se copia dentro de `Informe.contenido`,
    así que cambiarla después no modifica los informes ya emitidos.
    """

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="firma_profesional"
    )
    imagen = models.BinaryField("imagen")
    matricula = models.CharField("matrícula", max_length=40)
    actualizada = models.DateTimeField("actualizada", auto_now=True)

    class Meta:
        verbose_name = "firma profesional"
        verbose_name_plural = "firmas profesionales"

    def __str__(self):
        return f"Firma de {self.usuario}"

    @property
    def data_url(self):
        return "data:image/png;base64," + base64.b64encode(bytes(self.imagen)).decode()


class ResultadoEnvio(models.TextChoices):
    ENVIADO = "enviado", "Enviado"
    FALLIDO = "fallido", "Falló"


class EnvioInforme(models.Model):
    """Cada envío confirmado de un informe por correo (SCRUM-79), exitoso o fallido. Inalterable.

    Lo crea solo `informes.envios.enviar_informe`, con el resultado ya conocido. `clave` es la de
    la pantalla de confirmación: un envío por confirmación aunque el formulario llegue dos veces.
    """

    informe = models.ForeignKey(
        Informe, on_delete=models.PROTECT, related_name="envios", editable=False
    )
    enviado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="envios_de_informes",
        editable=False,
    )
    fecha = models.DateTimeField("fecha", auto_now_add=True)
    destinatario = models.EmailField("enviado a", max_length=254)
    resultado = models.CharField("resultado", max_length=10, choices=ResultadoEnvio.choices)
    clave = models.UUIDField(unique=True, editable=False)

    class Meta:
        verbose_name = "envío de informe"
        verbose_name_plural = "envíos de informes"
        ordering = ("-fecha", "-pk")
        constraints = [
            models.CheckConstraint(
                condition=Q(resultado__in=ResultadoEnvio.values),
                name="envio_informe_resultado_valido",
            ),
        ]

    def __str__(self):
        return (
            f"{self.informe.numero_mostrado} → {self.destinatario} ({self.get_resultado_display()})"
        )

    def save(self, *args, **kwargs):
        """Solo se guarda al registrar el envío: el historial no se modifica (FR-005)."""
        if not self._state.adding:
            raise ValueError("Un envío de informe no se puede modificar.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """El historial de envíos no se borra (FR-005)."""
        raise ValueError("Un envío de informe no se puede borrar.")
