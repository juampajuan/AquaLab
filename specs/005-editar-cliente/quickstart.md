# Quickstart: validar "Editar cliente"

**Feature**: `005-editar-cliente` | **Plan**: [plan.md](./plan.md)

Guía para comprobar de punta a punta que la US 3.2 (SCRUM-45) funciona. Detalle de pantallas y
mensajes en [contracts/edicion-cliente-ui.md](./contracts/edicion-cliente-ui.md); de campos y
validaciones en [data-model.md](./data-model.md).

## Prerrequisitos

- Docker y Docker Compose corriendo (`web` + `db`).
- Archivo `.env` creado a partir de `.env.example`.
- Un usuario activo y al menos dos clientes activos registrados.

## Levantar el entorno

```bash
docker compose up -d --build
docker compose exec web python manage.py migrate
```

## Tests automatizados y formato

```bash
docker compose exec web pytest clientes/tests/test_edicion.py
docker compose exec web pytest
docker compose exec web ruff check .
docker compose exec web ruff format --check .
```

**Esperado**: todos los tests en verde (al menos uno por cada escenario de aceptación 1–8) y `ruff`
sin errores.

## Validación manual

App en `http://localhost:8000`.

| # | Pasos | Resultado esperado | Escenario / Requisito |
|---|---|---|---|
| 1 | Sin iniciar sesión, abrir `/clientes/1/editar/` | Redirige a la pantalla de inicio de sesión | FR-001 |
| 2 | Iniciar sesión, abrir la ficha de un cliente (`/clientes/<id>/`) y hacer clic en **"Editar cliente"** | Abre `/clientes/<id>/editar/` con todos los datos vigentes precargados | Esc. 1, FR-002, FR-003 |
| 3 | Vaciar tanto `Nombre` como `Razón social` (o vaciar `Correo electrónico`) y enviar **Continuar** | Muestra errores obligatorios sin modificar al cliente | Esc. 3, FR-005, FR-008 |
| 4 | Ingresar correo inválido (`mal@`), teléfono inválido (`123`) o DNI/CUIT inválido y enviar **Continuar** | Muestra error junto al campo y conserva los valores ingresados | Esc. 4, FR-006, FR-008 |
| 5 | Cambiar el tipo y número de documento por el de **otro** cliente registrado y enviar **Continuar** | Error `"Ya existe un cliente registrado con este tipo y número de documento."`; no avanza | Esc. 5, FR-007 |
| 6 | Mantener el mismo documento del propio cliente, cambiar correo, teléfono y domicilio por valores válidos y enviar **Continuar** | Avanza a `/clientes/<id>/editar/confirmar/` mostrando el resumen de los nuevos datos | Esc. 6, FR-007, FR-009 |
| 7 | En la confirmación, hacer clic en **"Volver y editar"** | Vuelve al formulario con los datos modificados precargados; la base no cambió | Esc. 7, FR-010 |
| 8 | Avanzar con **Continuar** y hacer clic en **"Cancelar"** | Redirige a la ficha con `"Edición de cliente cancelada."` y los datos previos intactos | Esc. 7, FR-011, SC-004 |
| 9 | Editar datos con valores válidos, hacer clic en **Continuar** y luego en **"Confirmar"** | Redirige a `/clientes/<id>/` con `"Datos del cliente actualizados correctamente."` y los nuevos datos visibles de inmediato | Esc. 2, FR-012, SC-001, SC-002 |
| 10 | Volver atrás a la pantalla de confirmación y reenviar **"Confirmar"** | No produce error ni inconsistencias; redirige a la ficha del cliente | Esc. 8 |
