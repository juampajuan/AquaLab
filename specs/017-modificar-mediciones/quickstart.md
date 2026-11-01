# Quickstart: Modificar las mediciones

**Feature**: `017-modificar-mediciones` | **Plan**: [plan.md](./plan.md)

## Requisitos previos

- Rama `017-modificar-mediciones` (sale de `016-calcular-resultado`) y Docker Compose levantado.
- Migraciones aplicadas: `docker compose exec web python manage.py migrate` (incluye
  `estudios.0006_medicion_correccion`).
- Catálogo cargado (`importar_catalogo_pruebas`) y resultados al día (`calcular_resultados`).

## Validación automática

```bash
docker compose exec web pytest estudios
docker compose exec web pytest
docker compose exec web ruff check .
docker compose exec web ruff format --check .
docker compose exec web python manage.py makemigrations --check --dry-run
```

Resultado esperado: todo en verde, `ruff` sin errores y sin migraciones pendientes.

## Recorrido manual

Rutas y mensajes exactos en [contracts/corregir-mediciones-ui.md](./contracts/corregir-mediciones-ui.md).

1. **Preparar**: un estudio con CL-, CA, DUREZA-T y MG; cargar CL- = 2,35, CA = 80 y DUREZA-T = 15
   (MG = 24,3).
2. **Corregir (US 1)**: en el detalle, «Corregir mediciones». Cada medición aparece con su valor
   (2,35; 80; 15) y quién la cargó. Cambiar CL- a 2,53 → «Revisar cambios» → resumen
   «2,35 → 2,53 ml» → «Guardar correcciones». El detalle muestra 2,53, el resultado 25,3 mg/l y
   «Corregida por …».
3. **Dependientes**: corregir CA a 40. MG pasa a 48,6 mg/l; DUREZA-T no cambia.
4. **Validar (US 2)**: vaciar un campo, escribir `abc` en otro y enviar sin cambios; ver los
   errores junto a cada campo y «No hay cambios para guardar.».
5. **Concurrencia (US 3)**: abrir la corrección en dos pestañas, corregir CL- a 2,60 en una y
   después a 2,70 en la otra. La segunda informa «CL-: cambió mientras se editaba.» y CL- queda en
   2,60. Reenviar la primera confirmación informa «CL-: ya tenía ese valor.».
6. **Validados e informe (US 3)**: los estados Completada, Finalizado e Informe generado todavía
   no se pueden generar desde la interfaz (US 6.4 y Epic 7); los cubren los tests automáticos.
