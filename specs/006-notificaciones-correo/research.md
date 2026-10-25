# Research: Notificaciones por correo del alta de usuarios

**Feature**: `006-notificaciones-correo` | **Plan**: [plan.md](./plan.md)

## R1 — Configuración del envío de correo

- **Decision**: usar el framework de correo integrado de Django (`django.core.mail`), configurado
  por variables de entorno en `config/settings.py`:
  - `EMAIL_BACKEND` (por defecto `django.core.mail.backends.console.EmailBackend`).
  - `EMAIL_HOST`, `EMAIL_PORT` (587), `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS`
    (`True`) y `EMAIL_TIMEOUT` (10 s), usados solo si se elige el backend SMTP.
  - `DEFAULT_FROM_EMAIL` (por defecto `AquaLab <no-responder@aqualab.local>`).
  - Se documentan en `.env.example`, con un ejemplo comentado para Gmail con contraseña de
    aplicación. Ninguna credencial se sube al repo (Principio V).
- **Rationale**: cumple FR-014 sin dependencias nuevas (Principio II). En desarrollo, `docker compose
  logs -f web` muestra los correos completos. pytest-django reemplaza el backend por `locmem`
  automáticamente en todos los tests, así que se verifican con `mailoutbox` sin tocar la red. En el
  CI no hace falta configurar nada.
- **Alternatives**: un servicio externo con API (SendGrid, Mailgun, Resend) — agrega una dependencia
  y una cuenta, y no aporta nada para el volumen del laboratorio; `django-anymail` — misma razón;
  elegir el backend según si `EMAIL_HOST` está definido — es más implícito que una variable
  explícita y dificulta probar el SMTP contra un servidor local.

## R2 — Dónde se disparan los avisos: llamadas explícitas, no señales

- **Decision**: los avisos se disparan con llamadas explícitas desde los tres puntos donde ocurre
  cada evento, todos dentro de la app `usuarios`:
  1. `views.registro_confirmar`, después de `crear_usuario_pendiente(datos)` → solicitud nueva
     (administradores) y solicitud recibida (solicitante).
  2. `UsuarioAdmin.aprobar_cuentas` (acción masiva) y `UsuarioAdmin.save_model` (ficha del usuario)
     → aprobación.
  3. `UsuarioAdmin.rechazar_solicitudes` (acción nueva, R4) → rechazo.
- **Rationale**: la acción masiva actual usa `queryset.update(is_active=True)`, que **no** dispara
  señales `post_save`, así que una señal no cubriría FR-004. Además, una señal sobre `Usuario`
  saltaría con cualquier `save()` (por ejemplo, `last_login` al iniciar sesión) y obligaría a
  rastrear el valor previo de `is_active` en el modelo. Las llamadas explícitas dejan cada evento en
  un solo lugar, legible y fácil de testear.
- **Alternatives**: `post_save` con un campo "valor anterior" cacheado en `__init__` — más magia y no
  cubre `update()`; reemplazar `update()` por un `save()` por usuario — sigue necesitando detectar la
  transición en el modelo.

## R3 — Una sola vez por evento y envío después del commit

- **Decision**:
  - **Transición bajo bloqueo**: la aprobación y el rechazo leen las cuentas pendientes con
    `select_for_update()` dentro de `transaction.atomic()` y solo actúan sobre las que todavía tienen
    `is_active=False`. En la ficha del usuario, `save_model` lee el estado guardado con
    `select_for_update()` antes de guardar (la vista de cambio del admin ya corre en una
    transacción) y avisa solo si pasa de `False` a `True`.
  - **Envío al confirmarse la transacción**: los avisos se agendan con
    `transaction.on_commit(...)`, así no sale ningún correo si la operación termina con error y se
    revierte.
  - El registro ya es idempotente: una confirmación repetida no vuelve a llamar a
    `crear_usuario_pendiente` (rama `datos is None` de `registro_confirmar`), así que tampoco
    vuelve a avisar.
- **Rationale**: cubre FR-010 y el caso de dos administradores aprobando a la vez: el segundo queda
  esperando el bloqueo, después lee la cuenta ya aprobada y no avisa. PostgreSQL soporta
  `SELECT ... FOR UPDATE` sin configuración extra.
- **Alternatives**: guardar una marca `aviso_aprobacion_enviado` en el modelo — agrega una migración y
  un estado que hay que mantener, cuando `is_active` ya expresa la transición; enviar dentro de la
  transacción — un correo podría salir para una operación que después se revierte.
- **Nota para los tests**: con `@pytest.mark.django_db` cada test corre dentro de una transacción que
  nunca se confirma, así que los callbacks de `on_commit` no se ejecutan solos. Los tests usan el
  fixture `django_capture_on_commit_callbacks(execute=True)` de pytest-django.

## R4 — Acción de rechazo en el admin

- **Decision**: nueva acción `rechazar_solicitudes` en `UsuarioAdmin`, con una página intermedia de
  confirmación, siguiendo el mismo patrón que la acción "Eliminar seleccionados" de Django:
  - Primer POST (`action=rechazar_solicitudes`): renderiza
    `admin/usuarios/usuario/rechazar_confirmacion.html` con las solicitudes **pendientes** de la
    selección, los `_selected_action` ocultos y los botones "Sí, rechazar" y "No, volver".
  - Segundo POST (con `confirmar=si`): en una transacción, vuelve a filtrar pendientes con
    `select_for_update()`, guarda nombre y correo de cada una, registra la baja en el historial del
    admin (`log_deletions`), **elimina** las cuentas, agenda los avisos de rechazo con `on_commit` e
    informa "Se rechazaron N solicitud(es)."
  - Si la selección no tiene ninguna pendiente, no muestra la confirmación y avisa con un mensaje de
    advertencia.
- **Rationale**: eliminar la cuenta pendiente cumple FR-008 de la forma más simple: el login falla
  igual que con credenciales incorrectas y el correo queda libre para registrarse de nuevo sin tocar
  `RegistroForm.clean_email`. Es compatible con el Principio IV, porque una cuenta nunca aprobada no
  tiene historial (no hay ninguna `ForeignKey` hacia `Usuario` en el proyecto). La página intermedia
  cumple la regla de UI de la constitution (confirmación antes de eliminar) y FR-006.
- **Alternatives**: un estado `rechazada` en el modelo — obliga a cambiar `clean_email`, la
  restricción de correo único y el login, y conserva datos que nadie usa; usar la acción "Eliminar
  seleccionados" de Django — no manda el aviso y permite borrar cuentas aprobadas (FR-009); un
  diálogo de confirmación en JavaScript — no funciona sin JS y no lista qué se rechaza.

## R5 — Destinatarios, contenido y formato de los correos

- **Decision**:
  - **Administradores**: `Usuario.objects.filter(is_superuser=True, is_active=True)`, con **un
    mensaje por administrador** (cada uno ve solo su dirección, FR-013). Si no hay ninguno, se
    registra un `warning` en el log y el registro sigue normalmente.
  - **Contenido**: texto plano en español, armado con templates en
    `usuarios/templates/usuarios/correos/` (un `_asunto.txt` y un `_cuerpo.txt` por aviso, todos con
    "AquaLab" en el asunto). Solo nombre, apellido y correo del solicitante; nunca la contraseña ni
    su hash (FR-012).
  - **Enlaces**: se arman con `request.build_absolute_uri(...)`, porque los tres puntos de disparo
    tienen el `request` a mano: la ficha del solicitante en el admin
    (`admin:usuarios_usuario_change`) y el login (`usuarios:login`). En el aviso de rechazo no va
    ningún enlace a la cuenta, que ya no existe.
  - **Módulo**: `usuarios/notificaciones.py` con una función por aviso
    (`avisar_solicitud_nueva`, `avisar_solicitud_recibida`, `avisar_aprobacion`, `avisar_rechazo`)
    y un helper `_enviar` común.
- **Rationale**: texto plano alcanza para avisos cortos y evita mantener HTML de correo (YAGNI). Los
  templates separan la redacción del código, así el equipo puede revisar los textos en el PR.
  `build_absolute_uri` evita agregar una variable `SITE_URL` que habría que mantener por entorno.
- **Alternatives**: un correo al grupo de administradores con todos en `To` — expone las direcciones
  entre sí; correos HTML con `EmailMultiAlternatives` — más trabajo sin una necesidad en la spec;
  `django.contrib.sites` para el dominio — una app y una migración más para un solo valor.

## R6 — Fallas de envío

- **Decision**: `_enviar` envía cada mensaje con `fail_silently=False` dentro de un
  `try/except Exception`, y ante una falla hace
  `logger.exception("No se pudo enviar el aviso %s a %s", tipo, destinatario)` con el logger
  `usuarios.notificaciones`. La falla de un destinatario no corta el envío a los demás. Se agrega
  una configuración mínima de `LOGGING` que manda ese logger a la consola del contenedor.
- **Rationale**: FR-011 pide que la operación se complete igual y que la falla quede registrada.
  Como el envío corre en `on_commit`, la operación ya está confirmada y el usuario ve el resultado
  normal. El mensaje de log incluye el tipo de aviso y el destinatario, pero no el cuerpo del correo
  (FR-012).
- **Alternatives**: `fail_silently=True` — pierde el registro de la falla; una cola con reintentos
  (Celery, Django-Q) — dependencia e infraestructura nuevas, fuera de escala para el proyecto.
