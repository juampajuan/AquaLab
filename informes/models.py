import base64

from django.conf import settings
from django.db import models
from django.db.models import Q


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
