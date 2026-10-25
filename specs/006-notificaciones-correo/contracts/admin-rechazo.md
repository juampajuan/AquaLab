# Contrato: Aprobación y rechazo de solicitudes en el admin

**Feature**: `006-notificaciones-correo` | **Plan**: [../plan.md](../plan.md)

Extiende el contrato de [001-registrar-usuario/contracts/admin-aprobacion.md](../../001-registrar-usuario/contracts/admin-aprobacion.md).
Todo pasa en el listado `Usuarios` del admin (`/admin/usuarios/usuario/`).

## Acción "Aprobar cuentas seleccionadas" (cambio)

- Sin cambios visibles: aprueba las cuentas **pendientes** de la selección y muestra
  "Se aprobaron N cuenta(s)."
- **Nuevo**: después de confirmarse la aprobación, manda el aviso de aprobación a cada cuenta que
  pasó de pendiente a aprobada. Las cuentas que ya estaban aprobadas no reciben nada.

## Ficha del usuario (cambio)

- **Nuevo**: al guardar la ficha de una cuenta que estaba pendiente con "Aprobada" tildado, se manda
  el aviso de aprobación.
- Guardar una cuenta ya aprobada, destildar "Aprobada" o crear un usuario desde "Agregar usuario"
  no manda avisos.

## Acción nueva "Rechazar solicitudes seleccionadas"

Solo disponible para quien tenga el permiso `usuarios.delete_usuario` (los superusuarios lo tienen).

### Paso 1 — Pedido de confirmación

```text
POST /admin/usuarios/usuario/
     action=rechazar_solicitudes
     _selected_action=<pk> (uno o más)
```

| Caso | Respuesta |
|---|---|
| La selección tiene al menos una cuenta pendiente | `200` con la página **"Rechazar solicitudes"** |
| La selección no tiene ninguna pendiente | `302` al listado con la advertencia "No hay solicitudes pendientes en la selección." |

La página **"Rechazar solicitudes"** (`admin/usuarios/usuario/rechazar_confirmacion.html`, extiende
el layout del admin):

- Título: "Rechazar solicitudes".
- Texto: "¿Seguro que querés rechazar estas solicitudes? Cada solicitante recibirá un correo
  avisando que su solicitud no fue aprobada. Esta acción no se puede deshacer."
- Lista de las solicitudes **pendientes** a rechazar: nombre, apellido y correo.
- Si la selección incluía cuentas aprobadas: "Las cuentas ya aprobadas de la selección no se van a
  modificar."
- Formulario POST con `csrf_token`, `action=rechazar_solicitudes`, un `_selected_action` oculto por
  cuenta pendiente y `confirmar=si`.
- Botones: **"Sí, rechazar"** (envía el formulario) y **"No, volver"** (enlace al listado, sin
  cambios).

### Paso 2 — Confirmación

```text
POST /admin/usuarios/usuario/
     action=rechazar_solicitudes
     _selected_action=<pk> (uno o más)
     confirmar=si
```

- Vuelve a filtrar la selección a las cuentas que **siguen pendientes** (bloqueándolas) y elimina
  solo esas. Registra la baja en el historial del admin.
- Después de confirmarse, manda el aviso de rechazo a cada solicitante eliminado.
- `302` al listado con el mensaje de éxito "Se rechazaron N solicitud(es)."
- Si entre el paso 1 y el 2 todas se aprobaron o rechazaron por otro administrador: "Se rechazaron
  0 solicitud(es)." y no se manda ningún correo.

## Seguridad

- Ambas acciones requieren sesión de administrador (admin de Django) y protección CSRF.
- Ninguna pantalla ni correo muestra contraseñas ni hashes.
