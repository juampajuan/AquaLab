import re

from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q

PESOS_CUIT = (5, 4, 3, 2, 7, 6, 5, 4, 3, 2)
PATRON_TELEFONO = re.compile(r"^[+\d\s\-()]+$")
MENSAJE_DOCUMENTO_CON_MUESTRAS = (
    "No se puede modificar el documento de un cliente que ya tiene muestras registradas."
)


class TipoDocumento(models.TextChoices):
    DNI = "DNI", "DNI"
    CUIT = "CUIT", "CUIT"


def normalizar_numero_documento(valor):
    return re.sub(r"[\s.\-]", "", valor or "")


def es_cuit_valido(cuit):
    if not cuit or len(cuit) != 11 or not cuit.isdigit():
        return False
    suma = sum(int(digito) * peso for digito, peso in zip(cuit[:10], PESOS_CUIT, strict=True))
    resto = suma % 11
    if resto == 0:
        verificador = 0
    elif resto == 1:
        verificador = 9
    else:
        verificador = 11 - resto
    return int(cuit[10]) == verificador


def validar_documento(tipo, numero):
    if tipo == TipoDocumento.DNI:
        if not numero.isdigit() or len(numero) not in (7, 8):
            raise ValidationError(
                {"numero_documento": "El DNI debe tener 7 u 8 dígitos numéricos."}
            )
    elif tipo == TipoDocumento.CUIT and not es_cuit_valido(numero):
        raise ValidationError(
            {"numero_documento": "El CUIT debe tener 11 dígitos y un dígito verificador válido."}
        )


def validar_telefono(valor):
    if not valor:
        return
    cantidad_digitos = sum(caracter.isdigit() for caracter in valor)
    if not PATRON_TELEFONO.fullmatch(valor) or not (7 <= cantidad_digitos <= 15):
        raise ValidationError("Ingresá un número de teléfono válido (entre 7 y 15 dígitos).")


class Cliente(models.Model):
    nombre = models.CharField("nombre", max_length=200, blank=True)
    razon_social = models.CharField("razón social", max_length=200, blank=True)
    tipo_documento = models.CharField(
        "tipo de documento",
        max_length=4,
        choices=TipoDocumento.choices,
    )
    numero_documento = models.CharField("número de documento", max_length=11)
    email = models.EmailField("correo electrónico", max_length=254)
    telefono = models.CharField("teléfono", max_length=30, blank=True)
    domicilio = models.CharField("domicilio", max_length=255, blank=True)
    activo = models.BooleanField("activo", default=True)
    fecha_alta = models.DateTimeField("fecha de alta", auto_now_add=True)

    class Meta:
        verbose_name = "cliente"
        verbose_name_plural = "clientes"
        ordering = ("razon_social", "nombre", "id")
        constraints = [
            models.UniqueConstraint(
                fields=["tipo_documento", "numero_documento"],
                name="cliente_documento_unico",
                violation_error_message=(
                    "Ya existe un cliente registrado con este tipo y número de documento."
                ),
            ),
            models.CheckConstraint(
                condition=~Q(nombre="", razon_social=""),
                name="cliente_nombre_o_razon_social_obligatorio",
            ),
        ]

    def __str__(self):
        return f"{self.nombre_completo} ({self.tipo_documento} {self.numero_documento})"

    @property
    def nombre_completo(self):
        if self.razon_social and self.nombre:
            return f"{self.razon_social} ({self.nombre})"
        return self.razon_social or self.nombre

    def clean(self):
        super().clean()
        self.nombre = (self.nombre or "").strip()
        self.razon_social = (self.razon_social or "").strip()
        self.numero_documento = normalizar_numero_documento(self.numero_documento)
        self.email = (self.email or "").strip().lower()
        self.telefono = (self.telefono or "").strip()
        self.domicilio = (self.domicilio or "").strip()

        errores = {}

        if not self.nombre and not self.razon_social:
            errores["__all__"] = [
                "Debés ingresar al menos el nombre o la razón social del cliente."
            ]

        if self.tipo_documento and self.numero_documento:
            try:
                validar_documento(self.tipo_documento, self.numero_documento)
            except ValidationError as exc:
                errores.update(exc.message_dict)
            else:
                if self.pk and self.muestras.exists():
                    actual = (
                        Cliente.objects.filter(pk=self.pk)
                        .values_list("tipo_documento", "numero_documento")
                        .first()
                    )
                    if actual and (self.tipo_documento, self.numero_documento) != actual:
                        errores["numero_documento"] = [MENSAJE_DOCUMENTO_CON_MUESTRAS]

        if self.telefono:
            try:
                validar_telefono(self.telefono)
            except ValidationError as exc:
                errores["telefono"] = exc.messages

        if errores:
            raise ValidationError(errores)
