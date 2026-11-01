# Quickstart: Cargar mediciones

**Feature**: `015-cargar-mediciones` | **Plan**: [plan.md](./plan.md)

## Requisitos previos

- Rama `015-cargar-mediciones` y Docker Compose levantado.
- Migraciones aplicadas (`docker compose exec web python manage.py migrate`): incluye
  `estudios.0004_medicion`.
- Catálogo cargado con `docker compose exec web python manage.py importar_catalogo_pruebas`
  (SCRUM-64), un empleado aprobado y una muestra registrada.

## Validación automática

```bash
docker compose exec web pytest estudios
docker compose exec web pytest
docker compose exec web ruff check .
docker compose exec web ruff format --check .
docker compose exec web python manage.py makemigrations --check --dry-run
```

Resultado esperado: todos los tests en verde, `ruff` sin errores y sin migraciones pendientes.

## Recorrido manual

Rutas y mensajes exactos en [contracts/cargar-mediciones-ui.md](./contracts/cargar-mediciones-ui.md).

1. **Preparar**: crear un tipo de estudio con al menos tres pruebas directas (por ejemplo, PH,
   TEMPERATURA y una con unidad vacía) y una calculada, y crear un estudio de ese tipo.
2. **Abrir la carga (US 1)**: en el detalle, «Cargar mediciones». Se listan las pruebas directas con
   su unidad; la calculada aparece aparte, sin campo.
3. **Validar (US 2)**: escribir `abc` en una y `0,1234567` en otra → «Revisar mediciones». Cada
   error aparece junto a su campo y los valores se conservan. Enviar todo vacío → «Ingresá al menos
   una medición.»
4. **Cargar algunas**: escribir `7,20` en PH y `18.5` en TEMPERATURA, dejar el resto vacío →
   «Revisar mediciones» → resumen con dos mediciones → «Guardar mediciones». El detalle muestra
   ambas Cargadas con `7,20 UpH` y `18,5 °C`, usuario y fecha y hora; el estudio pasa a "En
   proceso" y ya no ofrece «Agregar prueba» ni «Quitar».
5. **Volver a cargar**: «Cargar mediciones» ofrece solo las pruebas que siguen Pendientes.
6. **Reenvío (US 3)**: en el paso 4, volver atrás en el navegador hasta el resumen y confirmar de
   nuevo. Se informa que esas pruebas ya tenían medición; los valores no cambian.
7. **Sin sesión**: cerrar sesión y abrir `/estudios/<pk>/mediciones/cargar/`. Redirige al login.

Los estudios "Finalizado" o con "Informe generado" todavía no se pueden generar desde la interfaz
(US 6.4 y US 7.x): esa regla la cubren los tests automáticos.
