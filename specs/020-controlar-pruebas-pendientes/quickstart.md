# Quickstart: Seleccionar estudio y controlar pruebas pendientes

**Feature**: `020-controlar-pruebas-pendientes` | **Plan**: [plan.md](./plan.md)

## Requisitos

```bash
docker compose up -d
docker compose exec web python manage.py migrate
docker compose exec web python manage.py importar_catalogo_pruebas
```

Un usuario aprobado, un cliente, una muestra y un estudio con al menos 3 pruebas.

## Tests

```bash
docker compose exec -T web pytest -q informes estudios/tests/test_consulta.py
docker compose exec -T web ruff check . && docker compose exec -T web ruff format --check .
```

## Recorrido manual

1. **Listado** — Menú «Informes» → «Seleccionar estudio». Se ve el estudio con su estado y
   «0 de 3 pruebas completadas». Buscar por su N° PI: aparece solo ese. Marcar «Solo listos para
   informar»: no aparece.
2. **Control con pendientes** — «Seleccionar». Las 3 pruebas figuran Pendiente con «Incompleta»;
   aviso «Hay 3 pruebas sin completar.» y «Generar informe» deshabilitado.
3. **Sin validar** — Cargar mediciones en una prueba (US 6.1) y volver: esa prueba figura Cargada
   con «Sin validar».
4. **Rechazo por otra vía** — Con el estudio incompleto, enviar el POST de generar (por ejemplo,
   desde una pestaña que quedó abierta cuando estaba listo): mensaje de error con el motivo y nada
   cambia.
5. **Listo** — Completar todas las pruebas (validándolas como bioquímico con US 6.4; para probar rápido, en el shell:
   `PruebaEstudio.objects.filter(estudio_id=N).update(estado="completada")`). El control avisa
   «El estudio está listo para informar…», «Generar informe» habilitado; al pulsarlo, aviso de que
   la generación estará disponible próximamente. El listado lo muestra con «Solo listos».
6. **Consistencia** — El detalle del estudio muestra los mismos estados y el enlace «Controlar para
   informe».
