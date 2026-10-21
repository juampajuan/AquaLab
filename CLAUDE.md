# Notas para Claude Code — AquaLab

## Pendientes entre features

Cuando una feature resuelva un pendiente, borrar su línea.

- **US 3.1 / US 3.2:** el modelo `clientes.Cliente` (con `activo=True`, `cliente.nombre_completo` y
  búsqueda por `tipo_documento` + `numero_documento` normalizado) y la vista `clientes:detalle` ya
  están disponibles. Antes de la US 3.2, definir si el dato "persona de contacto" se agrega como
  campo opcional en `Cliente` o se registra por muestra (Assumptions de `specs/003-registrar-cliente/spec.md`).
- **US 4.1:** el envío de informes por correo usa `Cliente.email`.

## Autenticación integrada (US 1.2)

- Login/logout propios en usuarios; LOGIN_URL y ambos cierres llevan al login AquaLab.
- Se mantiene ModelBackend y aprobación mediante is_active. Diagnóstico de pendiente solo con
  contraseña correcta; decisiones en specs/002-inicio-cierre-sesion/research.md.
- Login y registro recibido ya incluyen los enlaces recíprocos; Registrar cliente está en navbar.
- La guardia de sesión comparte lógica entre layouts de AquaLab y admin; los permisos administrativos
  permanecen intactos. No exponer sessionid ni usar la huella HMAC como autorización.
- T027/navegador acreditada por reporte del usuario; T001/aprobación formal y T032 siguen pendientes. Consultar tasks.md antes de
  declarar cerrada la historia; implementación local autorizada por excepción documentada en plan.md.
