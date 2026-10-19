# Notas para Claude Code — AquaLab

## Pendientes entre features

Cuando una feature resuelva un pendiente, borrar su línea.

- **US 1.2:** el login y el logout usan hoy los del admin (temporal). Reemplazar `LOGIN_URL` en
  `config/settings.py` y el botón "Cerrar sesión" de `templates/base.html` (marcado con un
  comentario).
- **US 1.2:** una cuenta pendiente de aprobación es `is_active=False`. Para mostrar "Tu cuenta está
  pendiente de aprobación" solo con contraseña correcta, ver la decisión R3 en
  `specs/001-registrar-usuario/research.md`.
