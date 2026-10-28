# Quickstart: Consultar estado del estudio

**Feature**: `009-consultar-estado-estudio` | Contrato: [contracts/consulta-estudio-ui.md](./contracts/consulta-estudio-ui.md) | Datos: [data-model.md](./data-model.md)

## Prerrequisitos

```bash
cp .env.example .env            # si aún no existe
docker compose up -d --build
docker compose exec web python manage.py migrate
docker compose exec web python manage.py cargar_demo_us51 --aplicar
```

Contar con un empleado activo (`createsuperuser` o aprobado en admin), al menos un cliente registrado (`/clientes/registrar/`), una muestra registrada (`/muestras/registrar/`) y uno o más estudios creados sobre la muestra (`/estudios/crear/`).

## Validación manual

1. Iniciar sesión y abrir `/estudios/buscar/` → formulario vacío, sin resultados.
2. Buscar por el identificador numérico del estudio (ej. `1`) → aparece el estudio correspondiente (US1-1).
3. Buscar por el N° PI de la muestra (ej. `200001`) o por parte del nombre de la muestra → se listan todos los estudios asociados a esa muestra (US1-2).
4. Buscar por nombre, razón social (con o sin tildes/mayúsculas) o DNI/CUIT del cliente (con o sin puntos/guiones) → se listan los estudios de sus muestras (US1-3, US1-6).
5. Verificar en la tabla de resultados las columnas: identificador del estudio, N° PI y nombre de la muestra, cliente y documento, tipo de estudio, fecha de creación y estado general (US1-4).
6. Hacer clic en **Ver estudio** → `/estudios/<id>/` muestra la cabecera completa del estudio, su estado general, el resumen de avance y la tabla de pruebas asignadas con código, nombre y estado individual de cada prueba (US1-5).
7. Desde el detalle del estudio, hacer clic en la muestra asociada → abre `/muestras/<id>/` (ficha de la muestra) con todos los datos vigentes de la muestra y la tabla de estudios asignados mostrando el estado general y el conteo de pruebas completadas de cada uno (US2-1, US2-2, US2-4).
8. Consultar la ficha de una muestra recién creada sin estudios → indica que aún no tiene estudios asignados y ofrece el acceso a crear uno (US2-3).
9. Buscar un texto sin coincidencias (`zzzz`) → informa `"No se encontraron estudios para «zzzz»."` (US1-7).
10. Buscar vacío o una sola letra (`a`) → muestra error junto al campo y no lista estudios (edge cases).
11. Cerrar sesión e intentar abrir `/estudios/buscar/`, `/estudios/1/` o `/muestras/1/` → redirige al login.

## Tests automatizados

```bash
docker compose exec web pytest estudios/tests/test_consulta.py muestras/tests/test_detalle.py
docker compose exec web pytest && docker compose exec web ruff check . && docker compose exec web ruff format --check .
```

Cobertura esperada:
- `estudios/tests/test_consulta.py`: estados generales de `Estudio` (`Pendiente de análisis`, `En proceso`, `Finalizado`, `Informe generado`) y estados individuales de `PruebaEstudio` (`Pendiente`, `Cargada`, `Completada`), búsqueda por identificador, por N° PI y nombre de muestra, por nombre/razón social/documento del cliente (con/sin formato y sin distinguir mayúsculas ni tildes), conservación de snapshots tras cambios en el tipo de estudio, validación de búsqueda vacía o de 1 carácter no numérico, paginación y orden, vista de detalle del estudio (cabecera, estado general, lista ordenada de pruebas y resumen de avance), 404 para ID inexistente y protección de sesión.
- `muestras/tests/test_detalle.py`: ficha de la muestra con todos sus datos vigentes, listado de estudios asignados ordenados del más reciente al más antiguo con estado general y conteo de pruebas completadas/totales, muestra sin estudios asignados, 404 para muestra inexistente y protección de sesión.
