# Quickstart: validar "Registrar muestra"

**Feature**: `007-registrar-muestra` | **Plan**: [plan.md](./plan.md)

Guía para comprobar de punta a punta que la US 4.1 (SCRUM-47) funciona. Detalle de pantallas y
mensajes en [contracts/registro-muestra-ui.md](./contracts/registro-muestra-ui.md); de campos y
validaciones en [data-model.md](./data-model.md).

## Prerrequisitos

- Docker y Docker Compose corriendo (`web` + `db`).
- Archivo `.env` creado a partir de `.env.example`.
- Un usuario activo, dos clientes activos (A y B) y uno inactivo (C).

## Levantar el entorno

```bash
docker compose up -d --build
docker compose exec web python manage.py migrate
```

## Tests automatizados y formato

```bash
docker compose exec web pytest muestras
docker compose exec web pytest
docker compose exec web ruff check .
docker compose exec web ruff format --check .
docker compose exec web python manage.py makemigrations --check --dry-run
```

**Esperado**: todo en verde (al menos un test por escenario de aceptación de las tres historias),
`ruff` sin errores y sin migraciones pendientes.

## Validación manual

App en `http://localhost:8000`.

| # | Pasos | Resultado esperado | Escenario / Requisito |
|---|---|---|---|
| 1 | Sin iniciar sesión, abrir `/muestras/registrar/` | Redirige al login | FR-001 |
| 2 | Iniciar sesión y pulsar "Registrar muestra" en la barra | Formulario con fechas de hoy, tipo de vertido "Agua", nombre y responsable vacíos | US1 Esc. 1 |
| 3 | Abrir la lista de clientes | Aparecen A y B; C (inactivo) no | US1 Esc. 2, FR-002 |
| 4 | Elegir A | Se ven su razón social (o nombre), documento y correo; A no tiene orígenes, así que se abre "origen nuevo" | US1 Esc. 2, edge case |
| 5 | Pulsar "Continuar" sin completar nada más | No avanza; error junto a origen y sitio de extracción, el resto conservado | US3 Esc. 1 |
| 6 | Origen nuevo "Pozo N°2", sitio "Canilla del tanque", nombre vacío → Continuar | Resumen con todos los datos, origen marcado "(nuevo)" y nombre "Muestra 1 (el número se confirma al guardar)" | US1 Esc. 4, US2 Esc. 1 |
| 7 | Pulsar "Volver y editar" | Formulario con los datos ingresados | US1 Esc. 7 |
| 8 | Volver al resumen y Confirmar | Formulario vacío con "Muestra registrada con N° PI 200001." (si es la primera). Cronometrado desde el paso 2 con un origen existente: menos de 1 minuto (SC-001) | US1 Esc. 5–6, FR-019 |
| 9 | Registrar otra muestra de A con nombre "Muestra de rutina", y una tercera con el nombre vacío | "Pozo N°2" aparece entre sus orígenes; los N° PI son 200002 y 200003; la tercera se llama "Muestra 3" | US2 Esc. 2, FR-012, FR-011 |
| 10 | Elegir B | "Pozo N°2" no aparece entre los orígenes de B | US2 Esc. 3 |
| 11 | En A, origen nuevo " pozo n°2 " → confirmar | Se reutiliza el origen existente; no se crea un duplicado (verificar en el admin) | US2 Esc. 4 |
| 12 | Fecha de muestreo mañana, o posterior a la de ingreso | Error en la fecha correspondiente | US3 Esc. 4 |
| 13 | Llegar al resumen y Cancelar | "Registro de muestra cancelado."; no se creó muestra ni origen; el siguiente N° PI no cambió | US1 Esc. 7, US2 Esc. 5, SC-005 |
| 14 | En el resumen, doble clic en Confirmar | Una sola muestra registrada | Edge case |
| 15 | En el admin (`/admin/`), abrir la muestra | Estado "Ingresada", usuario que la registró y fecha y hora del registro | FR-014, FR-015 |
| 16 | En el admin, abrir el origen "Pozo N°2" de A (tiene muestras) | El cliente se muestra como solo lectura y no se puede reasignar | Consistencia origen–cliente |
