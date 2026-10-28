from django.db import models
from django.db.models import Q


class Prueba(models.Model):
    codigo = models.CharField("código", max_length=50, unique=True)
    nombre = models.CharField("nombre", max_length=150)

    class Meta:
        ordering = ("codigo",)
        constraints = [
            models.CheckConstraint(condition=~Q(codigo=""), name="prueba_codigo_no_vacio"),
            models.CheckConstraint(condition=~Q(nombre=""), name="prueba_nombre_no_vacio"),
        ]

    def __str__(self):
        return f"{self.codigo} · {self.nombre}"

    def save(self, *args, **kwargs):
        self.codigo = self.codigo.strip()
        self.nombre = self.nombre.strip()
        return super().save(*args, **kwargs)

    def clean(self):
        super().clean()
        self.codigo = self.codigo.strip()
        self.nombre = self.nombre.strip()
