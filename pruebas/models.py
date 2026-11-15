import re
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from .formulas import FormulaInvalida, validar_formula

REFERENCIA = re.compile(r"\{([^{}]+)\}")
MENSAJE_UNIDAD_CURVA = "Indicá la unidad del resultado (la de la concentración)."
UNIDAD_ABSORBANCIA = "Abs"


def referencias_formula(formula):
    """Códigos de las pruebas que usa una fórmula: x es el valor medido y {CODIGO} otra prueba."""
    return {codigo.strip() for codigo in REFERENCIA.findall(formula or "")}


class TipoCalculo(models.TextChoices):
    DIRECTO = "DIRECTO", "Directo"
    FORMULA = "FORMULA", "Fórmula"
    CURVA = "CURVA", "Curva de calibración"  # US 6.6


class TipoVertido(models.TextChoices):
    CLOACAL = "cloacal", "Cloacal"
    CANAL = "canal", "Canal"


class Prueba(models.Model):
    codigo = models.CharField("código", max_length=50, unique=True)
    nombre = models.CharField("nombre", max_length=150)
    unidad = models.CharField("unidad del resultado", max_length=50, blank=True, default="")
    unidad_medicion = models.CharField("unidad de medición", max_length=50, blank=True, default="")
    tipo_calculo = models.CharField(
        "tipo de cálculo",
        max_length=10,
        choices=TipoCalculo.choices,
        default=TipoCalculo.DIRECTO,
    )
    formula = models.CharField(
        "fórmula",
        max_length=255,
        blank=True,
        default="",
        help_text="x es el valor medido; {CODIGO} es el resultado de otra prueba.",
    )
    es_calculada = models.BooleanField("calculada a partir de otras pruebas", default=False)
    norma = models.CharField("norma", max_length=150, blank=True, default="")
    limite_min = models.CharField("límite mínimo", max_length=50, blank=True, default="")
    limite_max = models.CharField("límite máximo", max_length=50, blank=True, default="")
    limite_deteccion = models.CharField(
        "límite de detección", max_length=50, blank=True, default=""
    )
    activa = models.BooleanField("activa", default=True)
    observacion = models.TextField("observación", blank=True, default="")
    # Gestión desde la app (SCRUM-73): concurrencia, reemplazo en cascada y última modificación.
    version = models.PositiveBigIntegerField("versión", default=1, editable=False)
    reemplazada_por = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        editable=False,
        related_name="reemplaza_a",
        verbose_name="reemplazada por",
    )
    creada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        editable=False,
        related_name="+",
        verbose_name="creada por",
    )
    fecha_creacion = models.DateTimeField(
        "fecha de creación", null=True, blank=True, editable=False
    )
    modificada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        editable=False,
        related_name="+",
        verbose_name="modificada por",
    )
    fecha_modificacion = models.DateTimeField(
        "fecha de modificación", null=True, blank=True, editable=False
    )

    TEXTOS = (
        "codigo",
        "nombre",
        "unidad",
        "unidad_medicion",
        "formula",
        "norma",
        "limite_min",
        "limite_max",
        "limite_deteccion",
        "observacion",
    )

    class Meta:
        ordering = ("codigo",)
        constraints = [
            models.CheckConstraint(condition=~Q(codigo=""), name="prueba_codigo_no_vacio"),
            models.CheckConstraint(condition=~Q(nombre=""), name="prueba_nombre_no_vacio"),
            models.CheckConstraint(
                condition=Q(tipo_calculo__in=(TipoCalculo.DIRECTO, TipoCalculo.CURVA), formula="")
                | (Q(tipo_calculo=TipoCalculo.FORMULA) & ~Q(formula="")),
                name="prueba_formula_segun_tipo",
            ),
            models.CheckConstraint(
                condition=Q(es_calculada=False) | Q(tipo_calculo=TipoCalculo.FORMULA),
                name="prueba_calculada_es_formula",
            ),
            models.CheckConstraint(condition=Q(version__gte=1), name="prueba_version_positiva"),
        ]

    def __str__(self):
        return f"{self.codigo} · {self.nombre}"

    def save(self, *args, **kwargs):
        self._normalizar()
        return super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        self._normalizar()
        if self.tipo_calculo == TipoCalculo.DIRECTO and self.formula:
            raise ValidationError({"formula": "Una prueba de tipo Directo no lleva fórmula."})
        if self.tipo_calculo == TipoCalculo.FORMULA and not self.formula:
            raise ValidationError({"formula": "Una prueba de tipo Fórmula necesita una fórmula."})
        if self.tipo_calculo == TipoCalculo.CURVA:
            if self.formula:
                raise ValidationError(
                    {"formula": "Una prueba por curva de calibración no lleva fórmula."}
                )
            if not self.unidad:
                raise ValidationError({"unidad": MENSAJE_UNIDAD_CURVA})
        if self.formula:
            try:
                validar_formula(self.formula)
            except FormulaInvalida as exc:
                raise ValidationError({"formula": exc.messages}) from exc
        referencias = referencias_formula(self.formula)
        if self.codigo in referencias:
            raise ValidationError({"formula": "La prueba no puede referenciarse a sí misma."})
        if self.es_calculada != bool(referencias):
            raise ValidationError(
                {
                    "es_calculada": (
                        "Marcala solo si la fórmula referencia otras pruebas ({CODIGO})."
                    )
                }
            )

    def _normalizar(self):
        for campo in self.TEXTOS:
            setattr(self, campo, getattr(self, campo).strip())

    @property
    def curva_vigente(self):
        """La curva de calibración vigente (US 6.6), o None."""
        return self.curvas.filter(vigente=True).first()

    def esta_en_uso(self):
        """Asignada a algún tipo de estudio o estudio: no se borra ni cambia código o nombre."""
        return self.pk is not None and (
            self.tipoestudioprueba_set.exists() or self.pruebaestudio_set.exists()
        )


class LimiteVertido(models.Model):
    prueba = models.ForeignKey(
        Prueba, on_delete=models.CASCADE, related_name="limites_vertido", verbose_name="prueba"
    )
    tipo_vertido = models.CharField("tipo de vertido", max_length=10, choices=TipoVertido.choices)
    limite_min = models.CharField("límite mínimo", max_length=50, blank=True, default="")
    limite_max = models.CharField("límite máximo", max_length=50, blank=True, default="")
    norma = models.CharField("norma", max_length=150, blank=True, default="")

    TEXTOS = ("limite_min", "limite_max", "norma")

    class Meta:
        verbose_name = "límite por tipo de vertido"
        verbose_name_plural = "límites por tipo de vertido"
        ordering = ("prueba__codigo", "tipo_vertido")
        constraints = [
            models.UniqueConstraint(fields=("prueba", "tipo_vertido"), name="limite_vertido_unico"),
        ]

    def __str__(self):
        return f"{self.prueba.codigo} · {self.get_tipo_vertido_display()}"

    def save(self, *args, **kwargs):
        self._normalizar()
        return super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        self._normalizar()

    def _normalizar(self):
        for campo in self.TEXTOS:
            setattr(self, campo, getattr(self, campo).strip())


class CurvaCalibracion(models.Model):
    """Curva de calibración de una prueba por absorbancia (US 6.6).

    La recta es absorbancia = pendiente × concentración + ordenada. Nunca se edita; a lo sumo una
    vigente por prueba. Una curva usada en algún resultado (`usada`) no se borra.
    """

    prueba = models.ForeignKey(
        Prueba, on_delete=models.CASCADE, related_name="curvas", verbose_name="prueba"
    )
    fecha_preparacion = models.DateField("fecha de preparación")
    observacion = models.TextField("observación", blank=True, default="")
    archivo_origen = models.CharField("archivo de origen", max_length=255, blank=True, default="")
    pendiente = models.DecimalField("pendiente", max_digits=24, decimal_places=12)
    ordenada = models.DecimalField("ordenada al origen", max_digits=24, decimal_places=12)
    r2 = models.DecimalField("R²", max_digits=11, decimal_places=10)
    concentracion_min = models.DecimalField("concentración mínima", max_digits=18, decimal_places=6)
    concentracion_max = models.DecimalField("concentración máxima", max_digits=18, decimal_places=6)
    absorbancia_min = models.DecimalField("absorbancia mínima", max_digits=18, decimal_places=6)
    absorbancia_max = models.DecimalField("absorbancia máxima", max_digits=18, decimal_places=6)
    vigente = models.BooleanField("vigente", default=False)
    usada = models.BooleanField("usada en resultados", default=False)
    cargada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="+",
        verbose_name="cargada por",
    )
    fecha_carga = models.DateTimeField("fecha de carga")
    clave = models.UUIDField("clave de confirmación", unique=True)

    class Meta:
        verbose_name = "curva de calibración"
        verbose_name_plural = "curvas de calibración"
        ordering = ("-fecha_carga", "-pk")
        constraints = [
            models.UniqueConstraint(
                fields=("prueba",), condition=Q(vigente=True), name="curva_vigente_unica"
            ),
            models.CheckConstraint(condition=~Q(pendiente=0), name="curva_pendiente_no_cero"),
            models.CheckConstraint(
                condition=Q(r2__gte=0) & Q(r2__lte=1), name="curva_r2_entre_0_y_1"
            ),
        ]

    def __str__(self):
        return f"{self.prueba.codigo} · curva del {self.fecha_preparacion:%d/%m/%Y}"

    @property
    def r2_bajo(self):
        from .curvas import R2_MINIMO

        return self.r2 < R2_MINIMO

    @property
    def r2_texto(self):
        """R² con 4 decimales y coma (0,9996)."""
        from .curvas import texto_numero

        return texto_numero(self.r2, Decimal("0.0001"))

    @property
    def rango_texto(self):
        """Rango de concentraciones de los estándares con la unidad: «0–0,4 mg/l»."""
        from .curvas import texto_numero

        desde, hasta = texto_numero(self.concentracion_min), texto_numero(self.concentracion_max)
        return f"{desde}–{hasta} {self.prueba.unidad}".rstrip()

    def concentracion(self, absorbancia):
        """Concentración que corresponde a una absorbancia: (absorbancia − ordenada) / pendiente."""
        return (absorbancia - self.ordenada) / self.pendiente


class PuntoCurva(models.Model):
    """Estándar de una curva: concentración conocida y absorbancia leída."""

    curva = models.ForeignKey(
        CurvaCalibracion, on_delete=models.CASCADE, related_name="puntos", verbose_name="curva"
    )
    orden = models.PositiveSmallIntegerField("orden")
    concentracion = models.DecimalField("concentración", max_digits=18, decimal_places=6)
    absorbancia = models.DecimalField("absorbancia", max_digits=18, decimal_places=6)

    class Meta:
        verbose_name = "punto de la curva"
        verbose_name_plural = "puntos de la curva"
        ordering = ("orden",)
        constraints = [
            models.UniqueConstraint(fields=("curva", "orden"), name="punto_curva_orden_unico"),
            models.CheckConstraint(condition=Q(orden__gte=1), name="punto_curva_orden_positivo"),
            models.CheckConstraint(
                condition=Q(concentracion__gte=0) & Q(absorbancia__gte=0),
                name="punto_curva_no_negativo",
            ),
        ]

    def __str__(self):
        return f"{self.curva} · punto {self.orden}"
