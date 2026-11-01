import re

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

from .formulas import FormulaInvalida, validar_formula

REFERENCIA = re.compile(r"\{([^{}]+)\}")


def referencias_formula(formula):
    """Códigos de las pruebas que usa una fórmula: x es el valor medido y {CODIGO} otra prueba."""
    return {codigo.strip() for codigo in REFERENCIA.findall(formula or "")}


class TipoCalculo(models.TextChoices):
    DIRECTO = "DIRECTO", "Directo"
    FORMULA = "FORMULA", "Fórmula"


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
                condition=Q(tipo_calculo=TipoCalculo.DIRECTO, formula="")
                | (Q(tipo_calculo=TipoCalculo.FORMULA) & ~Q(formula="")),
                name="prueba_formula_segun_tipo",
            ),
            models.CheckConstraint(
                condition=Q(es_calculada=False) | Q(tipo_calculo=TipoCalculo.FORMULA),
                name="prueba_calculada_es_formula",
            ),
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
