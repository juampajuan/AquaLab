# Quickstart: Quitar prueba del estudio

**Feature**: `011-quitar-prueba-estudio` | **Plan**: [plan.md](./plan.md)

## Requisitos previos

- Rama `011-quitar-prueba-estudio`, con US 5.3 implementada (la rama sale de
  `010-agregar-prueba-estudio`), y Docker Compose levantado.
- Un empleado aprobado, catálogo DEMO de US 5.1 cargado y al menos una muestra registrada (ver
  [quickstart de US 5.3](../010-agregar-prueba-estudio/quickstart.md)).

## Validación automática

```bash
docker compose exec web pytest estudios
docker compose exec web pytest
docker compose exec web ruff check .
docker compose exec web ruff format --check .
docker compose exec web python manage.py makemigrations --check --dry-run
```

Resultado esperado: todos los tests en verde, `ruff` sin errores y **sin migraciones pendientes**.

## Recorrido manual

Rutas y mensajes exactos en [contracts/quitar-prueba-ui.md](./contracts/quitar-prueba-ui.md).

1. **Llegar al estudio**: crear un estudio con un tipo de dos o más pruebas y abrir el enlace
   «Estudio N» del mensaje de éxito. Cada prueba ofrece «Quitar».
2. **Quitar (US 1)**: «Quitar» en una prueba → confirmación con la prueba y el estudio → «Quitar
   prueba». La prueba desaparece del detalle y vuelve a ofrecerse en «Agregar prueba».
3. **Cancelar**: «Quitar» en otra prueba y elegir «Cancelar». El estudio no cambia.
4. **Reenvío**: después de quitar, volver atrás en el navegador y confirmar de nuevo. Se informa que
   la prueba ya no forma parte del estudio.
5. **Última prueba (FR-011)**: quitar pruebas hasta dejar una. Su fila ya no ofrece «Quitar» e
   indica que el estudio debe conservar al menos una prueba.
6. **Sin sesión (FR-001)**: cerrar sesión y abrir la URL de quitar. Redirige al login.
