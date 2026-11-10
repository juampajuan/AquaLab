# Quickstart: Gestionar catálogo de pruebas

Pantallas en [contracts/catalogo-ui.md](./contracts/catalogo-ui.md); reglas en [data-model.md](./data-model.md).

## Preparación
1. Rama `035-gestionar-catalogo-pruebas`; `docker compose up -d`; `migrate` (aplica `pruebas.0003`).
2. Catálogo y demo: `importar_catalogo_pruebas` y `cargar_demo` (con `AQUALAB_ENTORNO=desarrollo`).
3. Entrar como `bioquimico@demo.aqualab` / `Demo-1234` (es Administrador).

## Recorrido
1. Administración → Catálogo de pruebas → «Nueva prueba»: crear `TEST-DIR` (Directo) y `TEST-FOR`
   (Fórmula `{TEST-DIR}*2`); probar una fórmula inválida, un código repetido y un límite «NE» → error.
2. Editar `TEST-DIR` (sin uso) cambiando código → rechazado porque `TEST-FOR` la usa; eliminar
   `TEST-FOR` y después `TEST-DIR` → eliminadas.
3. Abrir `CL-` (en uso): método bloqueado con el mensaje; cambiar el límite máximo → guardado.
   Ver un informe emitido con Cloruro: muestra el límite anterior.
4. Desactivar `CA`: aviso «La usan en su fórmula: MG…» y tipos afectados; confirmar. En el listado,
   `MG` marcada «Depende de una prueba inactiva: CA». Reactivar `CA`.
5. Desactivar `TURBIDEZ`: crear un estudio «Físico-químico básico» → no la incluye; un estudio en
   curso que ya la tenía sigue cargando y validando. Reactivarla.
6. Entrar como `tecnico@demo.aqualab` → `/administracion/pruebas/nueva/` da 403.

## Tests
```bash
docker compose exec web pytest pruebas estudios/tests/test_catalogo_activas.py
docker compose exec web pytest
```
