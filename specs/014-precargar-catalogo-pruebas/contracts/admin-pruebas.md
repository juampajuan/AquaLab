# Contrato: admin de pruebas

Archivo: `pruebas/admin.py`. Ruta: `/admin/pruebas/prueba/`. Requiere un usuario `is_staff` con los
permisos estándar del modelo (`pruebas.view_prueba`, `add_prueba`, `change_prueba`, `delete_prueba`).
Los superusuarios los tienen todos.

## Listado

| Elemento | Valor |
|---|---|
| Columnas | Código, Nombre, Unidad, Tipo de cálculo, Activa |
| Búsqueda | `codigo`, `nombre` (contiene, sin distinguir mayúsculas) |
| Filtros | Tipo de cálculo · Activa · Calculada a partir de otras pruebas · Observación (con / sin) |
| Orden | `codigo` (el `Meta.ordering` existente) |

## Detalle y alta

- Fieldsets: **Identificación** (código, nombre, activa) · **Cálculo** (tipo de cálculo, fórmula, es
  calculada, unidad de medición, unidad) · **Límites** (norma, mínimo, máximo, detección) ·
  **Observación**.
- Inline tabular **Límites por tipo de vertido**: tipo de vertido, mínimo, máximo y norma. Hasta 2
  filas (`max_num = len(TipoVertido)`), sin filas vacías extra (`extra = 0`).
- Validaciones: las del modelo (restricciones y `clean`, ver [data-model.md](../data-model.md)) y, en
  el formulario, que cada `{CODIGO}` de la fórmula exista en la base.

## Prueba en uso (`esta_en_uso()`)

| Acción | Resultado |
|---|---|
| Abrir | `codigo` y `nombre` se muestran como solo lectura; el resto se puede editar |
| Guardar con `codigo`/`nombre` en el POST | Se ignoran (son campos de solo lectura) |
| Eliminar desde el detalle | No aparece el botón (`has_delete_permission` devuelve `False`) |
| Eliminar con la acción masiva | El admin lista los objetos protegidos (`PROTECT`) y no borra |

## Prueba no usada

Todos los campos se pueden editar y la prueba se puede eliminar, junto con sus límites (`CASCADE`).
