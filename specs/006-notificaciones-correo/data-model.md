# Data Model: Notificaciones por correo del alta de usuarios

**Feature**: `006-notificaciones-correo` | **Plan**: [plan.md](./plan.md)

Esta feature **no agrega modelos, campos ni migraciones**. Usa el modelo `Usuario` de la US 1.1
(`usuarios/models.py`) y su campo `is_active` ("aprobada") como estado de la solicitud.

## Usuario (existente)

| Campo | Uso en esta feature |
|---|---|
| `email` | Destinatario de los avisos al solicitante; dato informado a los administradores. |
| `first_name`, `last_name` | Saludo en los avisos y datos del solicitante en el aviso a administradores. |
| `is_active` | `False` = solicitud pendiente; `True` = cuenta aprobada. La transición `False → True` dispara el aviso de aprobación. |
| `is_superuser` | Junto con `is_active=True`, define quiénes reciben el aviso de solicitud nueva. |
| `password` | **Nunca** se incluye en un correo (FR-012). |

## Estados de una solicitud

```text
                 confirmar registro
   (sin cuenta) ───────────────────────► PENDIENTE (is_active=False)
                 avisos: solicitud nueva   │            │
                 + solicitud recibida      │            │
                                           │ aprobar    │ rechazar (con confirmación)
                                           ▼            ▼
                        APROBADA (is_active=True)   (cuenta eliminada; el correo queda libre)
                        aviso: aprobación           aviso: rechazo
```

| Transición | Origen | Disparador | Aviso |
|---|---|---|---|
| Alta de solicitud | — | `registro_confirmar` con `accion=confirmar` y datos en sesión | Solicitud nueva (a cada administrador activo) y solicitud recibida (al solicitante) |
| Aprobación | Pendiente | Acción `aprobar_cuentas` o ficha del usuario con "aprobada" tildado | Aprobación (al solicitante) |
| Rechazo | Pendiente | Acción `rechazar_solicitudes` confirmada | Rechazo (al solicitante) |

**Reglas**

- Solo una cuenta **pendiente** puede pasar a aprobada o ser rechazada; sobre una cuenta ya aprobada
  ninguna de las dos acciones tiene efecto ni manda correos (FR-009, FR-010).
- Desmarcar "aprobada" en una cuenta aprobada no es un rechazo: vuelve a pendiente sin aviso. Si
  después se la aprueba otra vez, se manda el aviso de aprobación, porque es una transición nueva.
- Una cuenta rechazada se elimina; un nuevo registro con el mismo correo es una solicitud nueva
  (FR-008).
- Las cuentas creadas con `createsuperuser` o desde "Agregar usuario" del admin nacen aprobadas y
  no disparan avisos.

## Aviso por correo (no persistido)

Mensaje de texto plano que arma `usuarios/notificaciones.py`. No se guarda en la base; solo las
fallas de envío quedan en el log (`usuarios.notificaciones`).

| Aviso | Destinatario | Asunto | Contenido |
|---|---|---|---|
| Solicitud nueva | Cada administrador activo, un mensaje por persona | `AquaLab: nueva solicitud de cuenta` | Nombre, apellido y correo del solicitante; enlace a su ficha en el admin |
| Solicitud recibida | Solicitante | `AquaLab: recibimos tu solicitud de cuenta` | Que la solicitud está pendiente de aprobación y que le avisarán por correo |
| Aprobación | Solicitante | `AquaLab: tu cuenta fue aprobada` | Que ya puede iniciar sesión; enlace al login |
| Rechazo | Solicitante | `AquaLab: tu solicitud de cuenta no fue aprobada` | Que la solicitud no fue aprobada |

Remitente de todos: `DEFAULT_FROM_EMAIL`.
