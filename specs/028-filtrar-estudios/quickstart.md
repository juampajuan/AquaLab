# Quickstart: Filtrar estudios por estado y fecha

**Feature**: `028-filtrar-estudios` | **Plan**: [plan.md](./plan.md)

## Requisitos

- `docker compose up -d` con la base migrada.
- Datos de demo (SCRUM-78) para tener estudios en los cuatro estados y en distintas fechas:
  `docker compose exec web python manage.py cargar_demo` (no borra nada).

## Tests

```bash
docker compose exec web pytest estudios/tests/test_filtros.py estudios/tests/test_consulta.py \
  clientes/tests/test_historial.py clientes/tests/test_historial_consulta.py
docker compose exec web pytest
docker compose exec web ruff check . && docker compose exec web ruff format --check .
```

## Prueba manual (Estudios → Buscar estudio)

1. **Estado**: elegir «En proceso» → Buscar. Solo aparecen estudios «En proceso»; el contador cambia.
2. **Fechas**: Desde = hace 7 días, Hasta = hoy → solo estudios creados en la última semana, incluidos
   los de hoy. Probar solo Desde y solo Hasta.
3. **Combinar**: escribir un cliente demo (por ejemplo, «Lácteos») + estado + rango → se cumplen los
   tres.
4. **Paginar**: con un filtro que deje más de 20 estudios, pasar a la página 2 → los campos siguen
   completos y el listado sigue filtrado.
5. **Errores**: Desde posterior a Hasta → error junto a «Desde» y listado completo; editar la URL con
   `?estado=otro` o `?desde=31/02/2026` → error junto al campo, sin página de error.
6. **Sin coincidencias**: un rango sin estudios → «Ningún estudio coincide con la búsqueda y los
   filtros.» con «Limpiar filtros».
7. **Limpiar**: «Limpiar filtros» → listado completo, campos vacíos, sin el botón.
8. **Historial del cliente** (regresión): Clientes → ficha → Historial; sus filtros funcionan igual
   que antes.

Rutas, parámetros y mensajes: [contracts/buscar-estudio-ui.md](./contracts/buscar-estudio-ui.md).
