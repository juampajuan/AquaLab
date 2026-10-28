# Notas para Claude Code — AquaLab

## Pendientes entre features

Cuando una feature resuelva un pendiente, borrar su línea.

- **Envío de informes (SCRUM-39):** el envío de informes por correo usa `Cliente.email`.

## Mensajes de commit

Conventional Commits en español, con la US en el mensaje: `tipo(ámbito): descripción`.

- Spec Kit: `docs(specs): spec de la US 3.2 – Editar cliente` (igual para `plan` y `tasks`).
- Código: `feat(<app>): US 3.2 – Editar cliente`; correcciones `fix(<app>): ...`.
- Infraestructura y configuración: `chore: ...`.

## Avisos por correo (US 1.3)

- Los avisos de `usuarios/notificaciones.py` se llaman explícitamente desde `registro_confirmar`,
  `UsuarioAdmin.aprobar_cuentas`, `UsuarioAdmin.save_model` y `UsuarioAdmin.rechazar_solicitudes`.
  No se usan señales: `queryset.update()` no las dispara.
- Siempre se agendan con `transaction.on_commit`; una falla de envío solo queda en el log
  `usuarios.notificaciones`. Rechazar elimina la cuenta pendiente para liberar el correo.
- En los tests: `django_capture_on_commit_callbacks(execute=True)` y `mailoutbox`.

## Autenticación integrada (US 1.2)

- Login/logout propios en usuarios; LOGIN_URL y ambos cierres llevan al login AquaLab.
- Se mantiene ModelBackend y aprobación mediante is_active. Diagnóstico de pendiente solo con
  contraseña correcta; decisiones en specs/002-inicio-cierre-sesion/research.md.
- Login y registro recibido ya incluyen los enlaces recíprocos; Registrar cliente está en navbar.
- La guardia de sesión comparte lógica entre layouts de AquaLab y admin; los permisos administrativos
  permanecen intactos. No exponer sessionid ni usar la huella HMAC como autorización.
- T027/navegador acreditada por reporte del usuario; T001/aprobación formal y T032 siguen pendientes. Consultar tasks.md antes de
  declarar cerrada la historia; implementación local autorizada por excepción documentada en plan.md.

## Registro de muestras (US 4.1)

- El N° PI lo asigna `muestras/servicios.py:registrar_muestra` (máximo + 1, desde 200001) bajo
  `pg_advisory_xact_lock`. No usar secuencias ni `AutoField`: dejan huecos ante un rollback.
- El origen nuevo se crea (o se reutiliza, sin distinguir mayúsculas) en la misma transacción que la
  muestra, después del lock; cancelar o fallar no deja orígenes huérfanos ni consume N° PI.
- Cada borrador lleva una `clave_borrador` (UUID, `unique` en `Muestra`); bajo el lock, si ya hay una
  muestra con esa clave se devuelve en vez de crear otra. Borrar el borrador de la sesión no alcanza:
  las sesiones de Django no se bloquean y dos confirmaciones simultáneas leen el mismo borrador.
- La ficha del cliente y sus orígenes se actualizan en vivo con
  `muestras/static/muestras/registro_muestra.js`; con un cliente ya elegido (errores o `?volver=1`)
  los renderiza el servidor. No hay buscador de clientes: se quitó tras la prueba manual.

## Pruebas de un estudio (US 5.3)

- `estudios/servicios.py:agregar_prueba` bloquea la fila del estudio (`select_for_update`) y revalida
  todo bajo ese bloqueo; US 5.4 (`quitar_prueba`) usa el mismo esquema para la regla de al menos una
  prueba. `Estudio.admite_modificaciones` es la única regla de estudio modificable.
- La vista `agregar_prueba` y el servicio se llaman igual: la vista usa `servicios.agregar_prueba`, y
  los tests que lo parchean apuntan a `estudios.servicios.agregar_prueba`.
- `estudios:detalle` es la única vista del estudio: US 5.4 completa su columna Acción y US 5.2 debe
  ampliarla en vez de crear otra. La columna Estado de cada prueba es el texto fijo «Pendiente» hasta
  que US 5.2 / 6.4 agreguen el estado por prueba.
