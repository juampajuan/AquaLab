# Quickstart: Notificaciones por correo del alta de usuarios

**Feature**: `006-notificaciones-correo` | **Plan**: [plan.md](./plan.md)

Guía para comprobar la feature de punta a punta. Textos y destinatarios esperados en
[contracts/correos.md](./contracts/correos.md); pantallas del admin en
[contracts/admin-rechazo.md](./contracts/admin-rechazo.md).

## Requisitos

- Proyecto levantado según el [README](../../README.md) (`docker compose up -d --build`,
  `migrate`) y al menos un superusuario creado con `createsuperuser`.
- Sin cambios en `.env`: por defecto los correos se muestran en la consola.

En otra terminal, dejar abierto el log para ver los correos:

```bash
docker compose logs -f web
```

## 1. Solicitud nueva y solicitud recibida (US 1 y US 2)

1. Sin sesión, ir a <http://localhost:8000/usuarios/registro/>, completar el formulario y confirmar.
2. **Esperado** en el log: un correo `AquaLab: nueva solicitud de cuenta` por cada superusuario
   activo, con los datos del solicitante y un enlace a su ficha en el admin, y un correo
   `AquaLab: recibimos tu solicitud de cuenta` al correo registrado.
3. Recargar la página de confirmación o volver atrás y reenviar: **no** aparecen correos nuevos.
4. Repetir el registro con otro correo pero cancelar en la revisión: **no** aparece ningún correo.

## 2. Aprobación (US 3)

1. Entrar a <http://localhost:8000/admin/usuarios/usuario/?is_active__exact=0> como superusuario.
2. Seleccionar la solicitud del paso 1 y aplicar **"Aprobar cuentas seleccionadas"**.
3. **Esperado**: "Se aprobaron 1 cuenta(s)." y en el log un correo `AquaLab: tu cuenta fue
   aprobada` con el enlace al login.
4. Aplicar la acción otra vez sobre la misma cuenta: "Se aprobaron 0 cuenta(s)." y **ningún** correo.
5. Registrar otra solicitud, abrir su ficha, tildar **"Aprobada"** y guardar: aparece el mismo correo
   de aprobación.

## 3. Rechazo (US 4)

1. Registrar otra solicitud con un correo nuevo, por ejemplo `rechazo@lab.com`.
2. En el listado del admin, seleccionarla y aplicar **"Rechazar solicitudes seleccionadas"**.
3. **Esperado**: la página "Rechazar solicitudes" con nombre, apellido y correo. Elegir
   **"No, volver"**: la solicitud sigue pendiente y no hay correo.
4. Repetir y elegir **"Sí, rechazar"**: "Se rechazaron 1 solicitud(es).", la cuenta desaparece del
   listado y en el log aparece `AquaLab: tu solicitud de cuenta no fue aprobada`.
5. Intentar iniciar sesión con esa cuenta: "Usuario o contraseña incorrectos".
6. Registrarse de nuevo con `rechazo@lab.com`: se acepta y llegan otra vez los dos avisos de
   solicitud nueva.

## 4. Falla de envío (opcional)

1. En `.env`, poner `EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend` y
   `EMAIL_HOST=servidor-inexistente`, y reiniciar con `docker compose up -d`.
2. Registrar una solicitud.
3. **Esperado**: el registro termina normalmente ("Registro recibido...") y en el log aparece
   `No se pudo enviar el aviso ...` con el tipo de aviso y el destinatario.
4. Volver a dejar `.env` como estaba.

## 5. Envío real con SMTP (opcional)

Con una cuenta de Gmail y una
[contraseña de aplicación](https://support.google.com/accounts/answer/185833), completar en `.env`:

```bash
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=tu-cuenta@gmail.com
EMAIL_HOST_PASSWORD=la-contraseña-de-aplicación
DEFAULT_FROM_EMAIL=AquaLab <tu-cuenta@gmail.com>
```

Reiniciar con `docker compose up -d` y repetir el paso 1 con un correo propio.

## 6. Tests y formato

```bash
docker compose exec web pytest usuarios
docker compose exec web ruff check .
docker compose exec web ruff format --check .
```

**Esperado**: todo en verde, incluidos los tests nuevos de `usuarios/tests/test_notificaciones.py`
y los ya existentes de registro y admin.
