# Quickstart: Agregar y quitar pruebas de un estudio

**Feature**: `009-gestionar-pruebas-estudio` | **Plan**: [plan.md](./plan.md)

## Requisitos previos

- Rama `009-gestionar-pruebas-estudio` y Docker Compose levantado.
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

Rutas y mensajes exactos en [contracts/pruebas-estudio-ui.md](./contracts/pruebas-estudio-ui.md).

1. **Llegar al estudio**: crear un estudio en `/estudios/crear/` y abrir el enlace «Estudio N» del
   mensaje de éxito. Se ven la cabecera y las pruebas del tipo, todas como «Pendiente».
2. **Agregar (US 1)**: «Agregar prueba» → la lista no incluye las pruebas ya asignadas → elegir una
   → «Revisar» → «Confirmar». La prueba aparece una vez en el detalle como pendiente y el tipo de
   estudio no cambia (nueva creación del mismo tipo sigue trayendo solo sus pruebas).
3. **Cancelar**: repetir el paso 2 y elegir «Cancelar» en la confirmación. El estudio no cambia.
4. **Reenvío**: después de confirmar un agregado, volver atrás en el navegador y confirmar de nuevo.
   Se informa que la prueba ya forma parte del estudio y no se duplica.
5. **Quitar (US 2)**: «Quitar» en una prueba → confirmación con la prueba y el estudio → «Quitar
   prueba». La prueba desaparece del detalle y vuelve a ofrecerse en «Agregar prueba».
6. **Última prueba (FR-014)**: quitar pruebas hasta dejar una. Su fila ya no ofrece «Quitar» e
   indica que el estudio debe conservar al menos una prueba.
7. **Sin sesión (FR-001)**: cerrar sesión y abrir `/estudios/<pk>/`. Redirige al login.
8. **Estudio inexistente**: abrir `/estudios/999999/`. Responde 404.
