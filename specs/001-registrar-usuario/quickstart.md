# Quickstart: validar "Registrar usuario"

**Feature**: `001-registrar-usuario` | **Plan**: [plan.md](./plan.md)

Guía para comprobar de punta a punta que la feature funciona. Detalle de pantallas y mensajes en
[contracts/registro-ui.md](./contracts/registro-ui.md); del admin en
[contracts/admin-aprobacion.md](./contracts/admin-aprobacion.md); del modelo en
[data-model.md](./data-model.md).

## Prerrequisitos

- Tarea de setup terminada (ver "Requisitos para el setup" en `plan.md`): proyecto Django, Docker
  Compose con `web` + `db`, app `usuarios` con el modelo `Usuario` y `.env` creado a partir de
  `.env.example`.
- Docker y Docker Compose instalados.

## Levantar el entorno

```bash
docker compose up -d --build
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser   # pide correo, nombre, apellido y contraseña
```

## Tests automatizados

```bash
docker compose exec web pytest usuarios
docker compose exec web ruff check .
docker compose exec web ruff format --check .
```

**Esperado**: todos los tests en verde (al menos uno por cada escenario de aceptación 1–8) y ruff
sin errores.

## Validación manual

App en `http://localhost:8000`.

| # | Pasos | Resultado esperado | Escenario |
|---|---|---|---|
| 1 | Ir a `/usuarios/registro/` sin sesión | Se ve el formulario (no redirige al login) | FR-001 |
| 2 | Enviar el formulario vacío | Error "Este campo es obligatorio." en cada campo; no avanza | 2 |
| 3 | Completar con correo `ana@` | Error de formato en el correo; nombre y apellido siguen cargados | 4, FR-007 |
| 4 | Completar `  Ana `, `Pérez`, `  Ana@Lab.com `, contraseña válida repetida → Continuar | Pantalla de revisión con "Ana", "Pérez", "ana@lab.com"; **no** aparece la contraseña (ver también el código fuente de la página) | FR-008, FR-014 |
| 5 | En la revisión, "Volver y editar" | Formulario con nombre, apellido y correo precargados; contraseña vacía | 5 |
| 6 | Continuar de nuevo y elegir "Cancelar" | Mensaje "Registro cancelado."; en el admin no existe `ana@lab.com` | 5, SC-003 |
| 7 | Repetir el paso 4 y "Confirmar" | Página "Registro recibido…"; en el admin aparece `ana@lab.com` con Aprobada = ✘ | 1 |
| 8 | Volver atrás en el navegador y reenviar la confirmación | No se crea una segunda cuenta (el admin muestra una sola) | 6 |
| 9 | Registrar `ANA@lab.com ` | Error "Este correo no está disponible." | 3 |
| 10 | (Cuando exista la US 1.2) Intentar iniciar sesión con `ana@lab.com` | No ingresa | 7 |
| 11 | Entrar a `/admin/` con el superusuario → Usuarios → filtro "Aprobada: No" → seleccionar `ana@lab.com` → acción "Aprobar cuentas seleccionadas" | Mensaje "Se aprobaron 1 cuenta(s)."; Aprobada = ✔ | 8, FR-013 |
| 12 | (Cuando exista la US 1.2) Iniciar sesión con `ana@lab.com` | Ingresa | 8 |

Mientras la US 1.2 no esté implementada, los escenarios 7 y 8 se verifican con los tests
automatizados (`authenticate()` / `Client.login()` con la cuenta pendiente y con la aprobada).

## Limpieza

```bash
docker compose down        # agrega -v para borrar también la base
```
