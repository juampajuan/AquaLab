# Notas para Claude Code — AquaLab

## Pendientes entre features

Cuando una feature resuelva un pendiente, borrar su línea.

- **US 1.2:** el login y el logout usan hoy los del admin (temporal). Reemplazar `LOGIN_URL` en
  `config/settings.py` y el botón "Cerrar sesión" de `templates/base.html` (marcado con un
  comentario).
- **US 1.2:** una cuenta pendiente de aprobación es `is_active=False`. Para mostrar "Tu cuenta está
  pendiente de aprobación" solo con contraseña correcta, ver la decisión R3 en
  `specs/001-registrar-usuario/research.md`.
- **US 1.2:** agregar un link "Iniciar sesión" en `usuarios/templates/usuarios/registro_recibido.html`
  y, desde la pantalla de login, un link a `usuarios:registro` ("Crear cuenta").
- **US 3.1 / US 3.2:** el modelo `clientes.Cliente` (con `activo=True`, `cliente.nombre_completo` y
  búsqueda por `tipo_documento` + `numero_documento` normalizado) y la vista `clientes:detalle` ya
  están disponibles. Antes de la US 3.2, definir si el dato "persona de contacto" se agrega como
  campo opcional en `Cliente` o se registra por muestra (Assumptions de `specs/003-registrar-cliente/spec.md`).
- **US 4.1:** el envío de informes por correo usa `Cliente.email`.
- **Navegación general:** cuando se cierre `002-inicio-cierre-sesion`, mover o duplicar el enlace
  `clientes:registrar` ("Registrar cliente") desde `templates/inicio.html` al navbar de
  `templates/base.html`.
