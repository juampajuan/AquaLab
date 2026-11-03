from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.db.models import Q
from django.db.models.functions import Lower
from django.utils import timezone


class UsuarioManager(BaseUserManager):
    use_in_migrations = True

    @staticmethod
    def normalizar_email(email):
        return email.strip().lower()

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("El correo electrónico es obligatorio.")
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("aprobada", extra_fields.get("is_active", True))
        if extra_fields.get("is_active", True) and not extra_fields["aprobada"]:
            raise ValueError("Una cuenta activa debe estar aprobada.")
        usuario = self.model(email=self.normalizar_email(email), **extra_fields)
        usuario.set_password(password)
        usuario.save(using=self._db)
        return usuario

    def create_superuser(self, email, password, **extra_fields):
        extra_fields["is_staff"] = True
        extra_fields["is_superuser"] = True
        extra_fields["is_active"] = True
        extra_fields["aprobada"] = True
        return self.create_user(email, password, **extra_fields)


class EstadoCuenta(models.TextChoices):
    PENDIENTE = "pendiente", "Pendiente"
    ACTIVA = "activa", "Activa"
    DESACTIVADA = "desactivada", "Desactivada"


class Usuario(AbstractUser):
    username = None
    email = models.EmailField("correo electrónico", unique=True)
    first_name = models.CharField("nombre", max_length=150)
    last_name = models.CharField("apellido", max_length=150)
    is_active = models.BooleanField(
        "activa",
        default=True,
        help_text=(
            "Indica si la cuenta está habilitada para iniciar sesión. "
            "Desactivarla conserva su aprobación previa y su historial."
        ),
    )
    aprobada = models.BooleanField("aprobada previamente", default=True, editable=False)
    version_administrativa = models.PositiveBigIntegerField(
        "versión administrativa", default=1, editable=False
    )
    date_joined = models.DateTimeField("fecha de registro", default=timezone.now)

    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = UsuarioManager()

    class Meta:
        verbose_name = "usuario"
        verbose_name_plural = "usuarios"
        permissions = [("administrar_panel", "Puede administrar el panel de AquaLab")]
        constraints = [
            models.UniqueConstraint(
                Lower("email"),
                name="usuario_email_unico_ci",
                violation_error_message="Este correo no está disponible.",
            ),
            models.CheckConstraint(
                condition=Q(is_active=False) | Q(aprobada=True),
                name="usuario_activo_implica_aprobada",
                violation_error_message="Una cuenta activa debe estar aprobada.",
            ),
            models.CheckConstraint(
                condition=Q(version_administrativa__gte=1),
                name="usuario_version_administrativa_positiva",
            ),
        ]

    @property
    def estado_cuenta(self):
        if not self.aprobada:
            return EstadoCuenta.PENDIENTE
        return EstadoCuenta.ACTIVA if self.is_active else EstadoCuenta.DESACTIVADA

    def __str__(self):
        return self.email

    def clean(self):
        super().clean()
        if self.email:
            self.email = UsuarioManager.normalizar_email(self.email)
