# Contrato: Aprobación de cuentas en el admin de Django

**Feature**: `001-registrar-usuario` | **Plan**: [../plan.md](../plan.md)

La aprobación se hace con el admin de Django (`/admin/`), sin pantallas propias (spec, Assumptions).

## Acceso

- Requiere un usuario con `is_staff=True`, `is_active=True` y permiso `usuarios.change_usuario`.
  El primero es el superusuario creado en el setup con `python manage.py createsuperuser`
  (pide correo, nombre, apellido y contraseña).
- El login del admin usa el correo como identificador.

## Listado `Usuarios` (`/admin/usuarios/usuario/`)

| Elemento | Valor |
|---|---|
| Columnas | Correo electrónico, Nombre, Apellido, Aprobada (✔/✘), Fecha de registro |
| Filtro lateral | "Aprobada" (Sí / No) → "No" lista las cuentas pendientes; "Es staff" |
| Búsqueda | correo, nombre, apellido |
| Orden | más recientes primero (`-date_joined`) |
| Acción masiva | **"Aprobar cuentas seleccionadas"** |

### Acción "Aprobar cuentas seleccionadas"

- Pone `is_active=True` en las cuentas seleccionadas.
- Mensaje de éxito: "Se aprobaron N cuenta(s)."
- Es idempotente: aprobar una cuenta ya aprobada no cambia nada.
- Solo disponible para quien tenga `usuarios.change_usuario`.

## Ficha del usuario

- Secciones: datos personales (correo, nombre, apellido), contraseña (link estándar de Django para
  cambiarla, nunca se muestra), estado (**Aprobada**), permisos (`is_staff`, `is_superuser`,
  grupos), fechas.
- Tildar "Aprobada" y guardar también aprueba la cuenta.
- El email editado se normaliza (minúsculas, sin espacios) y respeta la unicidad.

## Alta desde el admin

Se mantiene el alta estándar (`add_form` adaptado a correo + nombre + apellido + contraseña). No es
parte del flujo de la spec, pero el admin lo necesita para funcionar con el modelo propio.
