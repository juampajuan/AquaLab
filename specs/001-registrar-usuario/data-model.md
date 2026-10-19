# Data Model: Registrar usuario

**Feature**: `001-registrar-usuario` | **Fecha**: 2026-10-18 | **Plan**: [plan.md](./plan.md)

## Entidad: `Usuario` (app `usuarios`)

Modelo de usuario del proyecto (`AUTH_USER_MODEL = "usuarios.Usuario"`). Hereda de
`django.contrib.auth.models.AbstractUser`. Cubre las entidades **Usuario** y **Credencial** de la
spec; **Administrador** no es una entidad aparte (ver más abajo).

> ⚠️ Este modelo y su migración inicial los crea la **tarea de setup** (ver "Requisitos para el
> setup" en `plan.md`), porque tiene que existir antes de la primera migración del proyecto.

### Campos

| Campo | Tipo Django | Origen | Reglas |
|---|---|---|---|
| `id` | `BigAutoField` | `DEFAULT_AUTO_FIELD` | PK |
| `email` | `EmailField(unique=True)` | redefinido | Obligatorio. Identificador de login (`USERNAME_FIELD`). Se guarda normalizado: `strip()` + `lower()`. Único sin distinguir mayúsculas (constraint abajo). `verbose_name="correo electrónico"` |
| `first_name` | `CharField(max_length=150)` | redefinido (sin `blank=True`) | Obligatorio. Sin espacios laterales. `verbose_name="nombre"` |
| `last_name` | `CharField(max_length=150)` | redefinido (sin `blank=True`) | Obligatorio. Sin espacios laterales. `verbose_name="apellido"` |
| `password` | `CharField(128)` | `AbstractBaseUser` | Siempre hasheada por Django (PBKDF2). Nunca se muestra |
| `is_active` | `BooleanField` | `AbstractUser` | `False` = pendiente de aprobación; `True` = aprobada. `verbose_name="aprobada"` en el admin |
| `is_staff` | `BooleanField` | `AbstractUser` | Acceso al admin. `False` para cuentas registradas |
| `is_superuser` | `BooleanField` | `PermissionsMixin` | `False` para cuentas registradas |
| `date_joined` | `DateTimeField` | `AbstractUser` | Fecha de registro (se muestra en el admin) |
| `last_login` | `DateTimeField(null)` | `AbstractBaseUser` | Lo usa la US 1.2 |
| `groups`, `user_permissions` | M2M | `PermissionsMixin` | Sin uso en esta feature |
| `username` | — | **eliminado** (`username = None`) | — |

### Configuración del modelo

- `USERNAME_FIELD = "email"`
- `EMAIL_FIELD = "email"`
- `REQUIRED_FIELDS = ["first_name", "last_name"]` (los pide `createsuperuser`)
- `objects = UsuarioManager()`
- `Meta.constraints = [UniqueConstraint(Lower("email"), name="usuario_email_unico_ci", violation_error_message="Este correo no está disponible.")]`
- `Meta.verbose_name = "usuario"`, `verbose_name_plural = "usuarios"`
- `__str__` → el email.
- `clean()` normaliza el email (`strip().lower()`), para que también se normalice al editar desde
  el admin.

### `UsuarioManager` (hereda de `BaseUserManager`)

| Método | Comportamiento |
|---|---|
| `normalizar_email(email)` | `email.strip().lower()`. Lo usan el manager, el modelo y el formulario |
| `create_user(email, password=None, **extra)` | Normaliza email, hashea la contraseña. `is_active` por defecto `True` (comportamiento estándar de Django; el **registro** pasa `is_active=False` explícitamente) |
| `create_superuser(email, password, **extra)` | `is_staff=True`, `is_superuser=True`, `is_active=True` |

### Validaciones

| Regla | Dónde | Requisito |
|---|---|---|
| Nombre, apellido, email y contraseña obligatorios | Modelo (`blank=False`) + formulario | FR-002 |
| Formato de email válido | `EmailField` (validador de Django) | FR-004 |
| Email único sin mayúsculas/espacios | Formulario (`email__iexact`) + `unique=True` + `UniqueConstraint(Lower("email"))` | FR-005 |
| Espacios laterales eliminados | `forms.CharField/EmailField(strip=True)` + normalización del manager/modelo | Edge case |
| Contraseña válida | `AUTH_PASSWORD_VALIDATORS` (por defecto de Django) + coincidencia con "Repetir contraseña" | FR-002, R6 |
| Contraseña nunca en texto plano | `make_password()` antes de guardarla en sesión; `password` hasheado en la base | FR-014, principio V |

## Estados de la cuenta

```text
                  confirmar registro
   (no existe) ──────────────────────▶ PENDIENTE DE APROBACIÓN
                                       is_active = False
                                       └─ no puede iniciar sesión
                                              │
                                              │ administrador: acción "Aprobar cuentas
                                              │ seleccionadas" o tilda "Aprobada" en el admin
                                              ▼
                                         APROBADA
                                       is_active = True
                                       └─ puede iniciar sesión (US 1.2)
```

- No hay transición de vuelta ni estado "rechazada" en esta feature (FR-015). Un administrador
  técnicamente puede destildar `is_active` en el admin, pero no es un flujo definido por la spec.
- Una cuenta que nunca se aprueba queda pendiente indefinidamente (edge case).

## Datos transitorios: registro en revisión (sesión)

No es una tabla: vive en `request.session["registro_pendiente"]` entre el paso de formulario y la
confirmación (ver research R5).

| Clave | Contenido |
|---|---|
| `first_name` | Nombre sin espacios laterales |
| `last_name` | Apellido sin espacios laterales |
| `email` | Email normalizado |
| `password` | Hash de `make_password()` — **nunca** la contraseña original |

- Se crea al enviar un formulario válido; se reemplaza si la persona vuelve a enviar el formulario.
- Se elimina al confirmar (éxito) o al cancelar.

## Administrador

No es una entidad propia: es un `Usuario` con `is_staff=True` y permiso para modificar usuarios
(en la práctica, el superusuario del setup). No es un rol del dominio (spec, Assumptions).

## Contrato hacia otras features

- **US 1.2 (`002-inicio-cierre-sesion`)**: autentica con `email` + contraseña;
  pendiente ⇔ `is_active=False`; el nombre a mostrar es `first_name` (o `get_full_name()`).
- Cualquier feature futura que referencie al usuario usa `settings.AUTH_USER_MODEL`, nunca el
  `User` de Django.
