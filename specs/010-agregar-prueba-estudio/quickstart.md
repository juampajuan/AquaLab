# Quickstart: Agregar prueba al estudio

**Feature**: `010-agregar-prueba-estudio` | **Plan**: [plan.md](./plan.md)

## Requisitos previos

- Rama `010-agregar-prueba-estudio` y Docker Compose levantado.
- Un empleado aprobado (cuenta activa).
- Catálogo DEMO de US 5.1 cargado y al menos una muestra registrada (US 4.1):

```bash
docker compose up -d --build
docker compose exec web python manage.py migrate
docker compose exec web python manage.py cargar_demo_us51            # simulación
docker compose exec web python manage.py cargar_demo_us51 --aplicar  # carga real
```

## Validación automática

```bash
docker compose exec web pytest estudios
docker compose exec web pytest
docker compose exec web ruff check .
docker compose exec web ruff format --check .
docker compose exec web python manage.py makemigrations --check --dry-run
```

Resultado esperado: todos los tests en verde, `ruff` sin errores y **sin migraciones pendientes**
(esta historia no cambia el esquema).

## Recorrido manual

Rutas y mensajes exactos en [contracts/agregar-prueba-ui.md](./contracts/agregar-prueba-ui.md).

1. **Llegar al estudio**: crear un estudio en `/estudios/crear/` y abrir el enlace «Estudio N» del
   mensaje de éxito. Se ven la cabecera y las pruebas del tipo, todas como «Pendiente».
2. **Agregar (US 1)**: «Agregar prueba» → la lista no incluye las pruebas ya asignadas → elegir una
   → «Revisar» → «Confirmar». La prueba aparece una vez en el detalle como pendiente y el tipo de
   estudio no cambia (una nueva creación del mismo tipo sigue trayendo solo sus pruebas).
3. **Cancelar**: repetir el paso 2 y elegir «Cancelar» en la confirmación. El estudio no cambia.
4. **Reenvío**: después de confirmar un agregado, volver atrás en el navegador y confirmar de nuevo.
   Se informa que la prueba ya forma parte del estudio y no se duplica.
5. **Sin pruebas disponibles**: agregar todas las pruebas del catálogo. «Agregar prueba» informa que
   no hay pruebas disponibles.
6. **Sin sesión (FR-001)**: cerrar sesión y abrir `/estudios/<pk>/`. Redirige al login.
7. **Estudio inexistente**: abrir `/estudios/999999/`. Responde 404.
