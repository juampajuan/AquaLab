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
