# Research: Precargar el catálogo de pruebas de agua

Decisiones de diseño de SCRUM-64. No quedan `NEEDS CLARIFICATION`: las dos preguntas de la spec se
resolvieron el 2026-10-31 (nombre de prueba usada se conserva; la importación no borra ni desactiva).

## R1 — Campos nuevos con valores por defecto en el modelo existente

- **Decision**: ampliar `pruebas.Prueba` con una migración `0002` de `AddField`. Todos los textos nuevos
  son `CharField`/`TextField` con `blank=True, default=""`; `tipo_calculo` usa `default=DIRECTO`,
  `es_calculada=False` y `activa=True`.
- **Rationale**: las pruebas DEMO (`cargar_demo_us51`) y los 14 tests que hacen
  `Prueba.objects.create(codigo=..., nombre=...)` siguen siendo válidos sin tocarlos (FR-015).
  `TipoEstudioPrueba` y `PruebaEstudio` siguen apuntando al mismo modelo con `PROTECT`.
- **Alternatives considered**: un modelo nuevo `DefinicionPrueba` 1:1. Se descartó porque duplica la
  identidad de la prueba y obliga a cambiar los consumidores.

## R2 — Límites y fórmula como texto

- **Decision**: `limite_min`, `limite_max`, `limite_deteccion` (y los de vertido) son
  `CharField(max_length=50, blank=True)`. El valor se guarda tal como viene, con `strip()` como única
  normalización: "3.0" sigue siendo "3.0" y "Ph-0,2" sigue siendo "Ph-0,2". `formula` es
  `CharField(max_length=255, blank=True)` y no se evalúa.
- **Rationale**: lo pide la spec (FR-002, FR-003). Hay valores no numéricos ("Ausente", "SOE", "NE",
  "Ph±0,2"). El Principio IV (guardar con `Decimal`) se aplica a mediciones y resultados, que son de la
  épica 6; un límite de referencia no es un resultado. La conversión numérica, si hace falta, la decide
  la épica 6.
- **Alternatives considered**: `DecimalField` más un campo de texto para los casos no numéricos. Se
  descartó porque mezcla dos representaciones y la validación contra límites está fuera de alcance.
- **Largos**: el máximo del archivo es 8 en límites, 37 en fórmula, 26 en norma y 16 en unidades; los
  máximos del modelo (50/255/150/50) dejan margen.

## R3 — Reglas de coherencia en el modelo

- **Decision**:
  - `CheckConstraint`: con `DIRECTO` la fórmula está vacía; con `FORMULA` la fórmula no está vacía.
  - `CheckConstraint`: `es_calculada` solo con `FORMULA`.
  - `Prueba.clean()`: `es_calculada` es verdadero si y solo si la fórmula contiene alguna referencia
    `{CODIGO}`, y una prueba no puede referenciarse a sí misma.
  - Una función `referencias_formula(formula) -> set[str]` en `pruebas/models.py` extrae los códigos
    con la expresión `\{([^{}]+)\}`. La usan `clean()`, el formulario del admin y la importación.
- **Rationale**: las reglas de negocio van en el modelo (Principio IV) y valen igual para el admin y la
  importación (FR-014). Los 90 registros del archivo ya cumplen estas reglas: los 15 calculados tienen
  referencias y los 75 restantes no.
- **Alternatives considered**: validar solo en la importación. Se descartó porque el admin permite dar
  de alta pruebas.

## R4 — Existencia de las pruebas referenciadas

- **Decision**: la importación valida que cada `{CODIGO}` exista en el catálogo resultante, es decir,
  en los códigos del archivo más los que ya están en la base (FR-010). En el admin, `PruebaAdminForm`
  valida contra la base. `Prueba.clean()` no lo valida.
- **Rationale**: dentro de la importación una prueba puede referenciar a otra que aparece más abajo en
  el archivo (por ejemplo `CATIONES` → `NA-MEQ`). Si `clean()` consultara la base, el orden de las filas
  haría fallar la importación.

## R5 — Importación en dos fases y todo o nada

- **Decision**: la lógica vive en `pruebas/importacion.py`; el comando es una capa delgada.
  1. **Validar sin escribir**: se leen los dos CSV con `csv.DictReader` (`encoding="utf-8-sig"`, que
     acepta UTF-8 con o sin BOM) y se verifican las columnas obligatorias. Por cada fila se valida
     `si`/`no`, el tipo de cálculo, el tipo de vertido, los códigos duplicados y las referencias, y se
     corre `full_clean(validate_unique=False)` sobre la instancia (nueva, o la existente con los datos
     del archivo). Los errores se juntan con archivo, número de línea (el encabezado es la línea 1) y
     motivo.
  2. **Escribir**: si no hubo errores, se guarda todo dentro de `transaction.atomic()`: primero las
     pruebas (crear o actualizar por código) y después los límites (crear o actualizar por
     `(prueba, tipo_vertido)`).
- **Rationale**: FR-009 pide que la importación se aplique completa o no se aplique y que informe fila y
  motivo. Juntar todos los errores evita corregir de a uno. Un error inesperado de base dentro de
  `atomic` revierte todo.
- **Alternatives considered**: `loaddata` con un fixture. Se descartó porque no actualiza por código, no
  protege el nombre de pruebas usadas y obliga a convertir los CSV. `update_or_create` fila por fila sin
  validar antes deja errores a mitad de camino.

## R6 — Pruebas usadas durante la importación

- **Decision**: se consideran usadas las pruebas que tienen al menos un `TipoEstudioPrueba` o un
  `PruebaEstudio` (método `Prueba.esta_en_uso()`, más un conjunto de ids precalculado en la
  importación). Si el archivo trae otro nombre para una prueba usada, se conserva el nombre guardado, se
  actualiza el resto y se agrega un aviso al resumen. Nunca se borra ni se desactiva una prueba, y
  tampoco un límite que ya no figure en el archivo.
- **Rationale**: Clarifications P1 y P2 (2026-10-31), FR-008 y FR-008a. Es la misma regla que el admin
  (FR-013).

## R7 — Admin de Django

- **Decision**: en `pruebas/admin.py`:
  - `PruebaAdmin` con `list_display`, `search_fields = ("codigo", "nombre")` y `list_filter` por tipo de
    cálculo, activa, `es_calculada` y un filtro propio "Observación" (con o sin), que cubre SC-006.
  - `LimiteVertidoInline` tabular para ver y editar los límites dentro de la prueba.
  - `get_readonly_fields` agrega `codigo` y `nombre` cuando `obj.esta_en_uso()`.
  - `has_delete_permission` devuelve `False` para una prueba usada. El borrado masivo ya queda frenado
    por `PROTECT`: el admin muestra los objetos protegidos y no borra.
  - `PruebaAdminForm` valida que existan las referencias de la fórmula (R4).
- **Rationale**: es lo que Django ya trae (Principio II). Los permisos son los estándar del admin
  (`view`/`add`/`change`/`delete`); no se agrega un permiso nuevo.
- **Alternatives considered**: buscar también en `observacion`. Se descartó porque la búsqueda "CA"
  traería al Magnesio por el texto de su observación, contra el escenario 2 de la User Story 3.

## R8 — Concurrencia

- **Decision**: no se agrega un bloqueo. La importación es una tarea manual de quien administra la
  instalación. Si dos corridas se cruzan, la restricción `unique` de `codigo` y la de
  `(prueba, tipo_vertido)` impiden duplicados; la corrida que falla se revierte entera y puede
  repetirse.
- **Rationale**: YAGNI (Principio II). El advisory lock de `registrar_muestra` resuelve otro problema
  (numeración sin huecos).
