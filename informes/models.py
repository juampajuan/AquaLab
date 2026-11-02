import base64

from django.conf import settings
from django.db import models
from django.db.models import Q


class Informe(models.Model):
    """Informe emitido de un estudio (US 7.2), con la copia de todo lo que se mostró.

    `contenido` se arma con `informes.contenido.armar_contenido` y no cambia: el informe emitido
    se muestra siempre desde esa copia, aunque después se editen el cliente o el catálogo.
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
        permissions = [("emitir_informes", "Puede emitir informes")]
        constraints = [
            models.CheckConstraint(condition=Q(numero__gte=1), name="informe_numero_positivo"),
        ]

    def __str__(self):
        return f"{self.numero_mostrado} · {self.estudio}"

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
