# Notas para Claude Code — AquaLab

## Pendientes entre features

Cuando una feature resuelva un pendiente, borrar su línea.

- **US 4.1:** el envío de informes por correo usa `Cliente.email`.

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
