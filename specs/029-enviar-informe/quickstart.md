# Quickstart: Envío del informe por correo

**Feature**: `029-enviar-informe` | **Plan**: [plan.md](./plan.md)

## Requisitos

- `docker compose up -d`, `docker compose exec web python manage.py migrate` (`informes.0005`).
- Datos de demo: `docker compose exec web python manage.py cargar_demo` (requiere
  `AQUALAB_ENTORNO=desarrollo` en el `.env`). Entrar con `bioquimico@demo.aqualab` / `Demo-1234`.
- Sin datos SMTP en el `.env`, los correos se ven en la consola: `docker compose logs -f web`.

## Tests

```bash
docker compose exec web pytest informes/tests/test_envios.py informes/tests/test_ver.py
docker compose exec web pytest
docker compose exec web ruff check . && docker compose exec web ruff format --check .
docker compose exec web python manage.py makemigrations --check --dry-run
```

## Prueba manual

1. **Enviar**: Informes → Informes emitidos → abrir uno → «Enviar por correo». La confirmación
   muestra el número, el cliente, su correo y «Nunca se envió».
2. **Confirmar**: «Enviar informe» → vuelve al informe con «Se envió el informe INF-… a …». En la
   consola se ve el correo con el adjunto `INF-….pdf` (como contenido MIME).
3. **Historial**: la sección «Envíos por correo» muestra el envío (fecha, correo, usuario, Enviado).
4. **Reenviar**: «Enviar por correo» otra vez → la confirmación muestra el último envío; confirmar →
   dos filas en el historial.
5. **Cancelar**: en la confirmación, «Cancelar» → vuelve al informe sin fila nueva.
6. **Doble clic**: en la confirmación, el botón se deshabilita al enviar; volver atrás y reenviar
   el mismo formulario → «ya se había enviado con esta confirmación», sin fila nueva.
7. **Falla**: con `EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend` y `EMAIL_HOST`
   inexistente en el `.env` (recrear `web`) → «No se pudo enviar…», fila «Falló» y traza en el log.
   Volver el `.env` a como estaba.
8. **Permiso**: con `tecnico@demo.aqualab`, el informe no muestra el botón y `…/informe/enviar/` da 403.

Rutas, mensajes y correo: [contracts/enviar-informe-ui.md](./contracts/enviar-informe-ui.md).
