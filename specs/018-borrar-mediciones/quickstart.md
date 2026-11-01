# Quickstart: Borrar mediciones

**Feature**: `018-borrar-mediciones` | **Plan**: [plan.md](./plan.md)

## Requisitos previos

- Rama `018-borrar-mediciones` (sale de `017-modificar-mediciones`) y Docker Compose levantado.
- Sin migraciones nuevas (la `0006` de US 6.3 ya aplicada).

## Validación automática

```bash
docker compose exec web pytest estudios
docker compose exec web pytest
docker compose exec web ruff check .
docker compose exec web ruff format --check .
docker compose exec web python manage.py makemigrations --check --dry-run
```

## Recorrido manual

Mensajes exactos en [contracts/borrar-mediciones-ui.md](./contracts/borrar-mediciones-ui.md).

1. **Preparar**: un estudio con CL-, CA, DUREZA-T y MG; cargar CL- = 2,35, CA = 80 y DUREZA-T = 15.
2. **Borrar (US 1)**: «Corregir mediciones» → marcar «Borrar» en CL- → «Revisar cambios» → resumen
   CL- con 2,35 → «—» → «Guardar correcciones». CL- queda Pendiente, sin medición ni resultado, y
   aparece otra vez en «Cargar mediciones».
3. **Prevalece el borrado**: marcar «Borrar» en CA y vaciar su campo → no hay error y se borra.
4. **Dependientes (US 2)**: MG pierde su resultado, vuelve a Pendiente y avisa «Faltan resultados
   de: CA · Calcio (Ca).»; DUREZA-T no cambia.
5. **Vuelta a Pendiente de análisis**: borrar también DUREZA-T. El estudio vuelve a «Pendiente de
   análisis» y el detalle ofrece «Agregar prueba» y «Quitar».
6. **Concurrencia (US 3)**: con una medición cargada, abrir la corrección en dos pestañas, borrarla
   en una y en la otra confirmar el borrado: «COD: ya no tenía medición.».
