# Implementation Plan: Registrar usuario

**Branch**: `001-registrar-usuario` | **Date**: 2026-10-18 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/001-registrar-usuario/spec.md` (US 1.1 / SCRUM-41)

## Summary

Registro autogestionado de usuarios con aprobación posterior de un administrador. Se usa un modelo
de usuario propio (`usuarios.Usuario`, hereda de `AbstractUser`, sin `username`) con el **correo
como identificador de login**, único sin distinguir mayúsculas ni espacios. El registro es un flujo
de dos pasos renderizado en el servidor: formulario → **revisión y confirmación** (los datos
validados esperan en la sesión, con la contraseña ya hasheada) → alta. La cuenta se crea **inactiva**
(`is_active=False` = "pendiente de aprobación"), por lo que el backend de Django ya le impide
iniciar sesión; un administrador la aprueba desde el **admin de Django** con una acción
"Aprobar cuentas seleccionadas". El proyecto Django todavía no existe: la sección
[Requisitos para el setup](#requisitos-para-el-setup) lista lo que la tarea de setup tiene que dejar
listo para esta feature.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: Django 5.2 LTS (auth, admin, sessions, messages, forms), Bootstrap 5.3
(CDN, en `base.html`). Sin dependencias nuevas para esta feature.

**Storage**: PostgreSQL 16 en Docker (`DATABASE_URL`). Una tabla nueva (`usuarios_usuario` + M2M de
grupos/permisos). Datos transitorios del registro en la sesión de Django (backend de base de datos,
el por defecto).

**Testing**: pytest-django con el test client de Django; ruff (lint + format).

**Target Platform**: Contenedor Linux (`web`) servido localmente con Docker Compose; navegador de
escritorio.

**Project Type**: Aplicación web Django monolítica con templates del servidor (sin SPA).

**Performance Goals**: Sin metas específicas más allá de SC-001 (registro completo en < 2 min, que
depende de la persona, no del sistema). Volumen esperado: decenas de usuarios.

**Constraints**: Contraseña nunca en texto plano ni reenviada al navegador (FR-014, principio V);
CSRF en todos los formularios; textos en español; como máximo una cuenta por confirmación (FR-010).

**Scale/Scope**: 3 pantallas públicas (formulario, revisión, registro recibido) + configuración del
admin. Un laboratorio, decenas de usuarios.

Todas las incógnitas quedaron resueltas en [research.md](./research.md) (R1–R10). No hay
NEEDS CLARIFICATION pendientes.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Cumplimiento | Estado |
|---|---|---|
| **I. Spec primero** | Spec aprobada con US 1.1 / SCRUM-41. El PR deberá titularse "US 1.1 – Registrar usuario" y referenciar `specs/001-registrar-usuario/`. | ✅ |
| **II. Simplicidad y Django idiomático** | Se usa `AbstractUser`, `BaseUserCreationForm`, `is_active`, admin, sesiones y mensajes de Django. Sin dependencias nuevas (se descartó `django-formtools`, R5). Todo en la app `usuarios`. Nada fuera de la spec (sin roles, sin estado "rechazada", sin emails). | ✅ |
| **III. Tests obligatorios** | Un test por escenario de aceptación 1–8 + tests de modelo y admin (ver [Mapa de tests](#mapa-de-tests)). CI con pytest + ruff. No hay cálculos de resultados en esta feature. | ✅ |
| **IV. Integridad de datos** | Unicidad del correo validada en el formulario **y** garantizada por constraint en la base (R2). Sin datos numéricos ni registros con historial en esta feature. No se borran cuentas (rechazo/eliminación fuera de alcance). | ✅ |
| **V. Seguridad** | `LoginRequiredMiddleware` global; solo las vistas de registro son públicas (`@login_not_required`). Contraseña hasheada antes de guardarla en sesión y en la base; nunca se muestra. CSRF activo. Secretos por `.env`. | ✅ |
| **VI. Idioma y consistencia** | UI y mensajes en español; `verbose_name` en español; modelo `Usuario` y vistas/formularios en español. Los campos heredados de Django (`first_name`, `last_name`, `is_active`, `email`) quedan con su nombre ("lo propio de Django queda como es"). | ✅ |
| **UI** | Extiende `base.html`, Bootstrap 5.3, errores junto a cada campo, mensajes con el framework de mensajes, **confirmación antes de guardar** (es justamente el paso de revisión). | ✅ |

**Resultado**: sin violaciones. **Re-chequeo post-diseño (Phase 1)**: sin cambios; el diseño de
[data-model.md](./data-model.md) y [contracts/](./contracts/) mantiene todos los puntos.

## Requisitos para el setup

La tarea de infraestructura (antes de las US del Sprint 1) crea el proyecto. Para esta feature
necesita dejar lo siguiente. **Lo marcado con ⚠️ es bloqueante y tiene que estar antes del primer
`migrate`**: cambiar el modelo de usuario después obliga a borrar la base y rehacer las migraciones
de todo el equipo.

### Proyecto y configuración

- Proyecto Django 5.2 con settings en `config/` (`config/settings.py`, `config/urls.py`).
- `INSTALLED_APPS` incluye `django.contrib.admin`, `auth`, `contenttypes`, `sessions`, `messages`,
  `staticfiles` y la app `usuarios`.
- ⚠️ `AUTH_USER_MODEL = "usuarios.Usuario"`.
- ⚠️ App `usuarios` con el modelo `Usuario` y `UsuarioManager` tal como están en
  [data-model.md](./data-model.md) (email como `USERNAME_FIELD`, sin `username`, nombre y apellido
  obligatorios, constraint `usuario_email_unico_ci`) y su migración `0001_initial`, generada
  **antes** de correr cualquier `migrate`.
- `MIDDLEWARE` con el orden estándar de `startproject` + `django.contrib.auth.middleware.LoginRequiredMiddleware`
  (después de `AuthenticationMiddleware`).
- `LOGIN_URL`: mientras no exista la US 1.2 puede quedar en `"admin:login"`; la US 1.2 lo cambia a
  su vista de login.
- `AUTH_PASSWORD_VALIDATORS`: los cuatro por defecto de `startproject`.
- `LANGUAGE_CODE = "es-ar"`, `TIME_ZONE = "America/Argentina/Buenos_Aires"`, `USE_I18N = True`,
  `USE_TZ = True` (los mensajes estándar de Django y del admin salen en español).
- `DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"`.
- Base de datos desde `DATABASE_URL`; `SECRET_KEY` y `DEBUG` desde variables de entorno. La librería
  para leer `DATABASE_URL` (p. ej. `dj-database-url`) es decisión y justificación del setup.
- `config/urls.py` con `path("admin/", admin.site.urls)` y
  `path("usuarios/", include("usuarios.urls"))` (esta feature crea `usuarios/urls.py`; el setup
  puede dejarlo vacío con `app_name = "usuarios"`).

### Templates y UI

- `templates/base.html` (en `TEMPLATES["DIRS"]`) con Bootstrap 5.3 por CDN, barra de navegación,
  `{% block title %}`, `{% block content %}` y el bloque que renderiza `messages` como alertas de
  Bootstrap. La barra debe funcionar **sin usuario logueado** (las pantallas de registro son
  públicas): mostrar el nombre y "Cerrar sesión" solo si `user.is_authenticated`.

### Docker, tests y CI

- `docker compose` con `web` (Python 3.12) y `db` (PostgreSQL 16); `.env.example` con
  `DATABASE_URL`, `SECRET_KEY`, `DEBUG`.
- pytest-django configurado (`DJANGO_SETTINGS_MODULE = "config.settings"` en `pyproject.toml`).
  El usuario de la base debe poder crear la base de test (`CREATEDB`); con el usuario por defecto
  de la imagen de PostgreSQL ya puede.
- ruff configurado en `pyproject.toml`; GitHub Actions corriendo pytest (con servicio PostgreSQL) y
  ruff en cada PR.

### Primer administrador

- Documentar en el README: `docker compose exec web python manage.py createsuperuser` (pide correo,
  nombre, apellido y contraseña). Es el administrador que aprueba cuentas (spec, Assumptions).

### Reparto setup ↔ feature

| Lo hace el setup | Lo hace esta feature |
|---|---|
| Modelo `Usuario`, `UsuarioManager`, migración `0001`, `AUTH_USER_MODEL` | Tests del modelo (normalización, unicidad, superusuario) |
| `base.html` con mensajes | Templates de registro, revisión y registro recibido |
| `LoginRequiredMiddleware` | Vistas de registro con `@login_not_required` |
| `usuarios/admin.py` mínimo (registrar el modelo con un `UserAdmin` adaptado, para que el admin funcione) | Configuración completa de `UsuarioAdmin` + acción "Aprobar cuentas seleccionadas" |
| `usuarios/urls.py` vacío con `app_name` | Rutas de registro |

> Si el setup no llega a incluir el modelo, esta feature lo crea **siempre que nadie haya corrido
> `migrate` todavía** en ninguna rama. En cuanto exista otra migración que dependa de `auth`, ya no
> se puede.

## Diseño

### Flujo de registro

```text
GET  /usuarios/registro/            → formulario (precargado si hay datos en sesión, sin contraseña)
POST /usuarios/registro/            → inválido: mismo formulario con errores
                                    → válido: session["registro_pendiente"] = {nombre, apellido,
                                       email normalizado, make_password(...)} → 302 a confirmar
GET  /usuarios/registro/confirmar/  → resumen sin contraseña [Confirmar] [Volver y editar] [Cancelar]
POST accion=cancelar                → borra la sesión de registro → 302 a registro
POST accion=confirmar               → atomic: crear Usuario(is_active=False) → borrar sesión
                                       → 302 a /usuarios/registro/recibido/ + mensaje
```

Detalles (rutas, mensajes, casos borde) en [contracts/registro-ui.md](./contracts/registro-ui.md).
Idempotencia y concurrencia en [research.md R7](./research.md).

### Componentes

| Archivo | Contenido |
|---|---|
| `usuarios/models.py` | `Usuario`, `UsuarioManager` (setup) |
| `usuarios/forms.py` | `RegistroForm(BaseUserCreationForm)`: `first_name`, `last_name`, `email`, `password1`, `password2`; `clean_email` normaliza y valida disponibilidad. Formularios del admin (`UsuarioCreationForm`, `UsuarioChangeForm`) |
| `usuarios/views.py` | `registro`, `registro_confirmar`, `registro_recibido` (vistas de función, `@login_not_required`). Helper `crear_usuario_pendiente(datos)` que encapsula el alta + manejo de `IntegrityError` |
| `usuarios/urls.py` | Las tres rutas, `app_name = "usuarios"` |
| `usuarios/admin.py` | `UsuarioAdmin(UserAdmin)` + acción `aprobar_cuentas` ([contracts/admin-aprobacion.md](./contracts/admin-aprobacion.md)) |
| `usuarios/templates/usuarios/registro_form.html` | Formulario con errores por campo (Bootstrap `is-invalid` / `invalid-feedback`) |
| `usuarios/templates/usuarios/registro_confirmar.html` | Resumen + botones; deshabilita "Confirmar" al enviar |
| `usuarios/templates/usuarios/registro_recibido.html` | Resultado |

### Mapa de tests

| Escenario / requisito | Test (en `usuarios/tests/`) |
|---|---|
| Esc. 1 — registro válido crea una cuenta pendiente e informa | `test_registro.py::test_confirmar_crea_cuenta_pendiente` |
| Esc. 2 — campos obligatorios faltantes | `test_registro.py::test_formulario_incompleto_no_avanza` (parametrizado por campo) |
| Esc. 3 — correo duplicado (mayúsculas/espacios, cuenta pendiente) | `test_registro.py::test_correo_duplicado_rechazado` (parametrizado) |
| Esc. 4 — correo inválido | `test_registro.py::test_correo_invalido_rechazado` |
| Esc. 5 — volver / cancelar no crea la cuenta | `test_registro.py::test_volver_precarga_datos_sin_password`, `::test_cancelar_no_crea_cuenta` |
| Esc. 6 — confirmación repetida / concurrente | `test_registro.py::test_confirmacion_repetida_crea_una_cuenta`, `::test_integrity_error_no_crea_segunda_cuenta` |
| Esc. 7 — pendiente no puede iniciar sesión | `test_autenticacion.py::test_cuenta_pendiente_no_autentica` (`authenticate()` → `None`) |
| Esc. 8 — aprobada puede iniciar sesión | `test_admin.py::test_accion_aprobar_activa_cuentas` + `test_autenticacion.py::test_cuenta_aprobada_autentica` |
| FR-001 — registro público con `LoginRequiredMiddleware` | `test_registro.py::test_registro_accesible_sin_sesion` |
| FR-007 — conserva datos válidos | `test_registro.py::test_errores_conservan_datos_validos` |
| FR-014 — contraseña nunca expuesta | `test_registro.py::test_password_no_aparece_en_respuestas` (formulario con error, revisión, recibido) y `::test_sesion_guarda_hash` |
| Edge — espacios laterales | `test_modelo.py::test_normaliza_email_y_nombres` |
| R2 — constraint en la base | `test_modelo.py::test_constraint_email_case_insensitive` (`IntegrityError` saltando el formulario) |
| Superusuario | `test_modelo.py::test_create_superuser_activo_y_staff` |

## Project Structure

### Documentation (this feature)

```text
specs/001-registrar-usuario/
├── spec.md
├── plan.md              # Este archivo
├── research.md          # Phase 0
├── data-model.md        # Phase 1
├── quickstart.md        # Phase 1
├── contracts/
│   ├── registro-ui.md
│   └── admin-aprobacion.md
├── checklists/
│   └── requirements.md
└── tasks.md             # Phase 2 (/speckit-tasks, no lo crea este comando)
```

### Source Code (repository root)

```text
config/                          # setup
├── settings.py
└── urls.py
templates/
└── base.html                    # setup
usuarios/
├── models.py                    # setup: Usuario, UsuarioManager
├── migrations/0001_initial.py   # setup
├── admin.py                     # setup (mínimo) → esta feature (UsuarioAdmin + acción)
├── urls.py                      # setup (vacío) → esta feature (rutas)
├── forms.py                     # esta feature
├── views.py                     # esta feature
├── templates/usuarios/
│   ├── registro_form.html
│   ├── registro_confirmar.html
│   └── registro_recibido.html
└── tests/
    ├── conftest.py
    ├── test_modelo.py
    ├── test_registro.py
    ├── test_autenticacion.py
    └── test_admin.py
manage.py, Dockerfile, docker-compose.yml, pyproject.toml, requirements.txt, .env.example,
.github/workflows/ci.yml          # setup
```

**Structure Decision**: proyecto Django único en la raíz del repo, settings en `config/`, una app
por módulo (principio II); esta feature vive entera en `usuarios/`. Los tests van dentro de cada app
(`usuarios/tests/`) para que cada integrante trabaje en su app sin tocar carpetas compartidas.

## Decisiones confirmadas con el equipo

1. **"Repetir contraseña"** (R6): ✅ el formulario pide la contraseña dos veces. No es un dato nuevo,
   pero no figura en FR-002.
2. **Reingresar la contraseña al volver a editar** (R6): ✅ nombre, apellido y correo se conservan;
   la contraseña no, para no reenviarla al navegador (FR-014 sobre FR-007 solo para el secreto).
3. **Validadores de contraseña de Django** (mínimo 8 caracteres, no común, no solo números, no
   parecida a los datos personales): ✅ se usan los de por defecto.
4. **Contrato con la US 1.2**: pendiente ⇔ `is_active=False`. La 002 necesita
   `AllowAllUsersModelBackend` (o equivalente) para mostrar "Tu cuenta está pendiente de
   aprobación" solo con contraseña correcta (research R3). Comunicado a quien implemente la 002.
5. **Confirmación concurrente** (R7): ✅ se simplificó. Si la base rechaza un correo repetido al
   confirmar, se muestra "Este correo no está disponible."; no se compara el hash de la contraseña.

## Complexity Tracking

Sin violaciones de la constitution: no aplica.
