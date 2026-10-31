# Implementation Plan: Precargar el catálogo de pruebas de agua

**Branch**: `014-precargar-catalogo-pruebas` | **Date**: 2026-10-31 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/014-precargar-catalogo-pruebas/spec.md` (SCRUM-64)

## Summary

Se carga el catálogo real de 90 pruebas de agua y sus 18 límites por tipo de vertido, todo dentro de
la app `pruebas`. El modelo `Prueba` existente suma los datos que necesita la épica 6 (unidades, tipo de
cálculo, fórmula, norma, límites como texto, activa y observación), con valores por defecto para que
las pruebas DEMO y los tests actuales sigan siendo válidos. Un modelo nuevo, `LimiteVertido`, guarda
los límites cloacal y canal. El comando `importar_catalogo_pruebas` lee los dos CSV de `pruebas/datos/`
con el módulo `csv`: primero valida todo y después escribe en una sola transacción. Actualiza por
código, nunca borra ni desactiva, y conserva el nombre de las pruebas en uso avisando la diferencia. El
admin de Django permite ver, buscar, filtrar y agregar pruebas; el código y el nombre de una prueba en
uso quedan de solo lectura.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: Django 5.2 LTS (ORM, migraciones, admin, management commands) y el módulo
`csv` de la biblioteca estándar. Sin dependencias nuevas.

**Storage**: PostgreSQL 16 en Docker. La migración `pruebas/0002` agrega campos a `pruebas_prueba` y
crea `pruebas_limitevertido`. No hay migración de datos: los datos entran con el comando.

**Testing**: pytest 9.1.1 + pytest-django 4.14.0 (`call_command`, `tmp_path` para CSV con errores,
`admin_client`) y ruff 0.17.1.

**Target Platform**: Contenedor Linux (`web`) con Docker Compose; el admin se usa en un navegador de
escritorio.

**Project Type**: Aplicación web Django monolítica con templates en el servidor (sin SPA).

**Performance Goals**: La importación de 90 + 18 filas termina en segundos. En el admin, encontrar una
prueba toma menos de 30 s (SC-005).

**Constraints**: Todo o nada (FR-009); idempotente (FR-007); no borra ni desactiva (FR-008); los
límites se guardan como texto tal cual (FR-002); las mismas validaciones en el admin y en la
importación (FR-014); compatibilidad con las pruebas existentes (FR-015).

**Scale/Scope**: 2 modelos (uno ampliado y uno nuevo), 1 migración, 1 módulo de importación, 1
comando, 1 admin con inline, filtro y formulario, tests en `pruebas/tests/` y una nota en `CLAUDE.md`.

Decisiones en [research.md](./research.md) (R1–R8). No hay `NEEDS CLARIFICATION` pendientes.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Cumplimiento | Estado |
|---|---|---|
| **I. Spec primero (SDD)** | Spec de SCRUM-64 en `specs/014-precargar-catalogo-pruebas/spec.md`, con las clarificaciones resueltas. Una US, una spec y una rama. PR: «SCRUM-64 – Precargar las pruebas definidas por el científico». | ✅ |
| **II. Simplicidad y Django idiomático** | Admin, management command, `csv` estándar y `TextChoices`. Sin dependencias, vistas ni templates propios. No se evalúan fórmulas ni se comparan límites (YAGNI: épica 6). | ✅ |
| **III. Tests obligatorios** | Cada escenario de aceptación, FR y caso límite tiene test (ver [Mapa de tests](#mapa-de-tests)). No hay cálculos de resultados en esta historia; las fórmulas se prueban como texto, incluida la corrección del Magnesio. | ✅ |
| **IV. Integridad de datos** | Los límites son datos de referencia en texto, no mediciones ni resultados (R2); `Decimal` se aplica en la épica 6. Las reglas de coherencia están en el modelo (`CheckConstraint` + `clean`). Las pruebas usadas no se borran (`PROTECT`, `has_delete_permission`) y no cambian su código ni su nombre (admin e importación). | ✅ |
| **V. Seguridad** | El admin exige `is_staff` y los permisos del modelo; la guardia de sesión del admin (US 1.2) no cambia. El comando corre solo desde la terminal del contenedor. Los CSV no tienen datos personales. | ✅ |
| **VI. Idioma y consistencia** | Términos del glosario: `Prueba`, `LimiteVertido`, `TipoCalculo`, `TipoVertido`, `esta_en_uso`, `importar_catalogo_pruebas`. Etiquetas y mensajes en español. ruff. | ✅ |
| **Interfaz (UI)** | No hay pantallas propias: solo el admin de Django, que queda fuera del sistema visual de Stitch, como los admins existentes. | ✅ |

**Post-diseño (Phase 1)**: cumple todos los principios sin excepciones; no hace falta *Complexity
Tracking*.

## Diseño

### Modelo (`pruebas/models.py`)

Campos, restricciones y validaciones en [data-model.md](./data-model.md). En resumen:

```text
TipoCalculo(TextChoices)   DIRECTO | FORMULA
TipoVertido(TextChoices)   cloacal | canal
referencias_formula(formula) -> set[str]       # códigos entre llaves
Prueba (+ 11 campos, 2 CheckConstraint nuevos, clean ampliado, esta_en_uso())
LimiteVertido(prueba FK CASCADE related_name="limites_vertido", tipo_vertido, limite_min,
              limite_max, norma)  UniqueConstraint(prueba, tipo_vertido)
```

### Importación (`pruebas/importacion.py`)

```text
ErrorImportacion(Exception)    .errores: list[str]   # "archivo, línea N: motivo"
Resumen(dataclass)             pruebas_creadas/actualizadas, limites_creados/actualizados, avisos

importar(ruta_catalogo, ruta_limites) -> Resumen
  1. leer y validar ambos archivos sin escribir (columnas, si/no, choices, duplicados,
     full_clean(validate_unique=False), referencias y códigos contra el catálogo resultante)
     → si hay errores: raise ErrorImportacion(todos)
  2. transaction.atomic(): guardar pruebas por código (conservar el nombre si está en uso → aviso),
     después los límites por (prueba, tipo_vertido)
```

El comando (`pruebas/management/commands/importar_catalogo_pruebas.py`) resuelve las rutas por
defecto, llama a `importar`, imprime el resumen y los avisos, y convierte `ErrorImportacion` en
`CommandError`. Contrato completo en
[contracts/importar-catalogo-pruebas.md](./contracts/importar-catalogo-pruebas.md).

### Admin (`pruebas/admin.py`)

`PruebaAdmin` + `LimiteVertidoInline` + `ConObservacionFilter` + `PruebaAdminForm`. Contrato en
[contracts/admin-pruebas.md](./contracts/admin-pruebas.md).

### Mapa de tests

| Escenario / requisito | Test | Archivo |
|---|---|---|
| FR-015, R1: pruebas mínimas siguen siendo válidas con los defaults | `test_prueba_minima` (existente), `test_defaults_prueba_nueva` | `test_modelo.py` |
| FR-002: límites no numéricos y decimales se guardan tal cual | `test_limites_se_guardan_como_texto` (parametrizado: "Ausente", "NE", "Ph-0,2", "3.0") | `test_modelo.py` |
| FR-003, R3, edge: fórmula según tipo, `es_calculada` coherente, sin autorreferencia | `test_formula_segun_tipo_calculo`, `test_es_calculada_coherente_con_referencias`, `test_formula_no_se_referencia_a_si_misma`, `test_constraints_formula_en_base` | `test_modelo.py` |
| R3: `referencias_formula` | `test_referencias_formula` (parametrizado con fórmulas reales: RAS, NTK, MG, `x*20`) | `test_modelo.py` |
| FR-004: un límite por prueba y vertido | `test_limite_vertido_unico_por_tipo` | `test_modelo.py` |
| R6: `esta_en_uso` | `test_esta_en_uso_por_tipo_o_estudio` | `test_modelo.py` |
| US1 Esc. 1–7, SC-001: importación real de los dos archivos | `test_importa_catalogo_real` (90/18, valores de varias filas, TURBIDEZ DIRECTO + observación, MG corregida, CL2-LIB cloacal "NE", límite vacío queda vacío) | `test_importacion.py` |
| US1 Esc. 4, SC-006: 17 DIRECTO asumidas | `test_pruebas_sin_tipo_quedan_directo_con_observacion` | `test_importacion.py` |
| US2 Esc. 1, FR-007, SC-002: idempotencia | `test_reimportar_no_duplica` (3 corridas) | `test_importacion.py` |
| US2 Esc. 2, FR-006: actualiza por código | `test_reimportar_actualiza_por_codigo` (prueba y límite) | `test_importacion.py` |
| US2 Esc. 3–4, FR-008/008a, SC-003: prueba en uso conserva el nombre y las asignaciones | `test_prueba_en_uso_conserva_nombre_y_asignaciones` (tipo de estudio y estudio) | `test_importacion.py` |
| US2 Esc. 5: pruebas fuera del archivo no se tocan | `test_pruebas_fuera_del_archivo_no_se_tocan` (DEMO usada y no usada; límite fuera del archivo) | `test_importacion.py` |
| US2 Esc. 6, FR-009/010, SC-004: errores → nada cambia, línea y motivo | `test_archivo_invalido_no_cambia_nada` (parametrizado: columna faltante, código repetido, tipo de cálculo, tipo de vertido, si/no, referencia inexistente, límite de código inexistente, FORMULA sin fórmula, texto largo) y `test_reporta_todos_los_errores` | `test_importacion.py` |
| Edge: espacios laterales, BOM, referencia a una prueba más abajo en el archivo o ya existente en la base | `test_normaliza_espacios_y_acepta_bom`, `test_referencia_valida_en_archivo_o_base` | `test_importacion.py` |
| US2 Esc. 7, FR-011: resumen y avisos | `test_comando_informa_resumen_y_avisos`, `test_comando_error_sale_con_command_error` | `test_importacion.py` |
| FR-009: falla de base a mitad de camino revierte | `test_error_de_base_revierte_todo` (parche de `LimiteVertido.save`) | `test_importacion.py` |
| US3 Esc. 1–3, FR-012: listado, búsqueda, filtros | `test_admin_listado_busqueda_y_filtros` | `test_admin.py` |
| US3 Esc. 4: detalle con límites por vertido | `test_admin_detalle_muestra_limites` | `test_admin.py` |
| US3 Esc. 5, FR-014: alta válida y rechazos (código repetido o vacío, referencia inexistente) | `test_admin_alta_prueba`, `test_admin_alta_rechaza_invalidas` | `test_admin.py` |
| US3 Esc. 6–7, FR-013: código y nombre de solo lectura solo si está en uso | `test_admin_prueba_en_uso_codigo_nombre_solo_lectura`, `test_admin_prueba_libre_editable` | `test_admin.py` |
| US3 Esc. 8: no se elimina una prueba en uso | `test_admin_no_elimina_prueba_en_uso` (detalle y acción masiva) | `test_admin.py` |
| US3 Esc. 9: sin acceso al admin | `test_admin_requiere_staff_y_permiso` | `test_admin.py` |

## Project Structure

### Documentation (this feature)

```text
specs/014-precargar-catalogo-pruebas/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── importar-catalogo-pruebas.md
│   └── admin-pruebas.md
├── checklists/
│   └── requirements.md
└── tasks.md             # /speckit-tasks
```

### Source Code (repository root)

```text
pruebas/
├── models.py                        # Prueba ampliada, LimiteVertido, TipoCalculo, TipoVertido, referencias_formula
├── admin.py                         # nuevo
├── importacion.py                   # nuevo
├── management/
│   ├── __init__.py
│   └── commands/
│       ├── __init__.py
│       └── importar_catalogo_pruebas.py
├── migrations/
│   └── 0002_catalogo_pruebas.py
├── datos/
│   ├── catalogo_pruebas_agua.csv    # se versiona (hoy sin trackear)
│   └── limites_vertido.csv
└── tests/
    ├── test_modelo.py               # ampliado
    ├── test_importacion.py          # nuevo
    └── test_admin.py                # nuevo
CLAUDE.md                            # nota "Catálogo de pruebas (SCRUM-64)"
```

**Structure Decision**: todo vive en la app `pruebas` (Principio II: una app por módulo). `estudios` no
cambia: sigue referenciando `Prueba` con `PROTECT`, y `esta_en_uso()` usa los accesos inversos
existentes (`tipoestudioprueba_set`, `pruebaestudio_set`).

## Complexity Tracking

Sin violaciones de la constitution.
