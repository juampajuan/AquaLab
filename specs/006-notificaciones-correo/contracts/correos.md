# Contrato: Avisos por correo del alta de usuarios

**Feature**: `006-notificaciones-correo` | **Plan**: [../plan.md](../plan.md)

Interfaz interna en `usuarios/notificaciones.py` y textos que recibe cada destinatario. Los textos
viven en `usuarios/templates/usuarios/correos/` y se pueden ajustar en la revisión del PR sin tocar
el código.

## Funciones

| Función | Se llama desde | Destinatarios |
|---|---|---|
| `avisar_solicitud_nueva(request, usuario)` | `views.registro_confirmar` | Cada `Usuario` con `is_superuser=True` e `is_active=True`, un mensaje por persona |
| `avisar_solicitud_recibida(request, usuario)` | `views.registro_confirmar` | `usuario.email` |
| `avisar_aprobacion(request, usuario)` | `UsuarioAdmin.aprobar_cuentas`, `UsuarioAdmin.save_model` | `usuario.email` |
| `avisar_rechazo(nombre, email)` | `UsuarioAdmin.rechazar_solicitudes` | `email` (la cuenta ya no existe) |

Reglas comunes:

- Los llamadores las agendan con `transaction.on_commit(...)`; las funciones envían en el momento.
- Nunca lanzan excepciones por fallas de envío: las registran en el logger
  `usuarios.notificaciones` (nivel `ERROR`, con tipo de aviso y destinatario) y siguen con el
  siguiente destinatario.
- Sin administradores activos, `avisar_solicitud_nueva` registra un `WARNING`
  ("Solicitud de alta sin administradores activos para avisar") y no envía nada.
- Remitente: `settings.DEFAULT_FROM_EMAIL`. Formato: texto plano en UTF-8.

## Textos

Los textos son una propuesta para revisar en el PR. `{nombre}` es `first_name` del solicitante.

### Solicitud nueva (a cada administrador)

- **Asunto**: `AquaLab: nueva solicitud de cuenta`
- **Cuerpo**:

  ```text
  Hola, {nombre del administrador}:

  {first_name} {last_name} ({email}) solicitó una cuenta en AquaLab.

  Podés revisar la solicitud y aprobarla o rechazarla desde el panel de administración:
  {enlace absoluto a /admin/usuarios/usuario/<pk>/change/}

  —
  AquaLab
  ```

### Solicitud recibida (al solicitante)

- **Asunto**: `AquaLab: recibimos tu solicitud de cuenta`
- **Cuerpo**:

  ```text
  Hola, {nombre}:

  Recibimos tu solicitud de cuenta en AquaLab. Está pendiente de aprobación por un
  administrador del laboratorio.

  Te vamos a avisar por este medio cuando se resuelva.

  —
  AquaLab
  ```

### Aprobación (al solicitante)

- **Asunto**: `AquaLab: tu cuenta fue aprobada`
- **Cuerpo**:

  ```text
  Hola, {nombre}:

  Un administrador aprobó tu cuenta en AquaLab. Ya podés iniciar sesión con tu correo y tu
  contraseña:
  {enlace absoluto a /usuarios/login/}

  —
  AquaLab
  ```

### Rechazo (al solicitante)

- **Asunto**: `AquaLab: tu solicitud de cuenta no fue aprobada`
- **Cuerpo**:

  ```text
  Hola, {nombre}:

  Tu solicitud de cuenta en AquaLab no fue aprobada. Si creés que se trata de un error,
  comunicate con el laboratorio.

  —
  AquaLab
  ```

## Configuración (variables de entorno)

| Variable | Valor por defecto | Uso |
|---|---|---|
| `EMAIL_BACKEND` | `django.core.mail.backends.console.EmailBackend` | Consola en desarrollo; `django.core.mail.backends.smtp.EmailBackend` para enviar de verdad |
| `EMAIL_HOST` | `localhost` | Servidor SMTP |
| `EMAIL_PORT` | `587` | Puerto SMTP |
| `EMAIL_HOST_USER` | vacío | Usuario SMTP |
| `EMAIL_HOST_PASSWORD` | vacío | Contraseña SMTP (por ejemplo, una contraseña de aplicación de Gmail) |
| `EMAIL_USE_TLS` | `True` | STARTTLS |
| `EMAIL_TIMEOUT` | `10` | Segundos de espera máxima por conexión |
| `DEFAULT_FROM_EMAIL` | `AquaLab <no-responder@aqualab.local>` | Remitente |

En los tests, pytest-django usa siempre el backend en memoria (`locmem`), sin importar estas
variables.
