# Implementation Plan: Panel de calidad del agua

**Branch**: `033-panel-calidad` | **Date**: 2026-11-09 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/033-panel-calidad/spec.md` (SCRUM-76, US 8.4)

## Summary

Nueva sección «Calidad» dentro de `informes:dashboard`, para el mismo período del selector de la
8.3. Un módulo de cálculo puro, `informes/calidad.py`, recibe el `Periodo` de `tablero.periodo` y,
sobre las validaciones vigentes (`anulada=False`) fechadas en el período (zona del laboratorio),
cuenta con la evaluación guardada: porcentaje fuera de norma con su variación en puntos
porcentuales, ranking de pruebas (mínimo `MINIMO_EVALUADOS_RANKING = 5` evaluados, filas
«20,0 % (2 de 10)»), cumplimiento por tipo de vertido y clientes y orígenes con más
incumplimientos, con enlaces al historial (3.3) y a la comparación histórica (8.1). Unas 7
consultas agregadas, porcentajes en `Decimal`. Dos gráficos más en `dashboard.js` con el Chart.js
local, cada uno con su tabla «Ver datos». Sin modelos, migraciones ni permisos nuevos; el guion de la demo no cambia (R9).

## Technical Context

**Language/Version**: Python 3.12; JavaScript sin dependencias propias (solo Chart.js).

**Primary Dependencies**: Django 5.2 LTS (ORM: `values` + `Count(filter=...)`, `TruncDate` con
`tzinfo`), Tailwind CSS 4 y `templates/ui/`, Chart.js 4.4.7 ya en `static/vendor/` (8.3). Sin
dependencias nuevas.

**Storage**: PostgreSQL 16. Sin tablas ni migraciones.

**Testing**: pytest + pytest-django; fixtures de `estudios/tests/conftest.py` (`estudio_en_origen`,
`cargar`, `validar`, `bioquimico`, `cliente_bioquimico`) e `informes/tests/conftest.py`; la demo de
SCRUM-78 con `ahora` fijo para el caso integral; ruff.

**Target Platform**: Contenedor `web` (Docker Compose) y Render; navegador de escritorio.

**Project Type**: Aplicación web Django monolítica con templates en el servidor.

**Performance Goals**: el Dashboard completo sigue < 2 s con la demo y < 5 s con 10.000 estudios
(SC-004): ~7 consultas agregadas más, sin N+1 (R3).

**Constraints**: solo lectura (FR-014); evaluación guardada, nunca recalculada (FR-002); zona
horaria del laboratorio; sin CDN (FR-013); gráficos con tabla equivalente (FR-011); `Decimal` sin
`float` (FR-015); el mínimo del ranking en un solo lugar (FR-006a); CSS compilado al día (CI).

**Scale/Scope**: `informes/calidad.py`, una línea en la vista `dashboard`, parcial
`informes/calidad.html`, inclusión en `dashboard.html`, dos gráficos en `dashboard.js`, CLAUDE.md
y tests.

Decisiones en [research.md](./research.md) (R1–R9). No hay `NEEDS CLARIFICATION` pendientes.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Cumplimiento | Estado |
|---|---|---|
| **I. Spec primero (SDD)** | Spec de US 8.4 con el ajuste del usuario (2026-11-09) registrado en Clarifications. El código espera la aprobación de la spec. | ✅ |
| **II. Simplicidad y Django idiomático** | Vive en `informes` junto al dashboard (sin app nueva); ORM y agregaciones; reutiliza `Periodo`, `variacion` y el partial de variación de la 8.3; sin dependencias nuevas; JS mínimo en el archivo existente. | ✅ |
| **III. Tests obligatorios** | Cada escenario y FR con test (ver [Mapa de tests](#mapa-de-tests)); porcentajes con valores esperados explícitos. | ✅ |
| **IV. Integridad de datos** | Solo lectura; usa la evaluación guardada en la validación (no reevalúa con límites actuales); `Decimal`. | ✅ |
| **V. Seguridad** | La sección está dentro de la vista con `@permission_required("informes.ver_dashboard", raise_exception=True)`; no hay rutas nuevas. | ✅ |
| **VI. Idioma y consistencia** | `calidad.py`, `Conteo`, `FilaPrueba`, `MINIMO_EVALUADOS_RANKING`; interfaz en español; ruff. | ✅ |
| **Interfaz (UI)** | `.tarjeta`, `.tabla`, `ui/ayuda.html`, `ui/estado.html`, `ui/estado_vacio.html`, `informes/variacion.html`; tokens `exito`/`peligro`. | ✅ |

**Post-diseño (Phase 1)**: cumple todos los principios, sin excepciones.

## Diseño

```text
GET /informes/dashboard/?periodo=...
  └─ views.dashboard
       contexto = tablero.armar(clave)                       (8.3, sin cambios)
       contexto["calidad"] = calidad.armar(contexto["periodo"])
       contexto["datos_graficos"] |= contexto["calidad"]["graficos"]
            │
            └─ calidad.armar(p)
                 base = Validacion vigentes + dia local       (R2)
                 indicador (actual, anterior, sin_limite)     1 consulta   (R3, R5)
                 por prueba  → mínimo 5, orden, tope 10       1 consulta   (R4)
                 por vertido → Agua, Cloacal, Canal           1 consulta
                 por cliente / por origen → in_bulk top 10    4 consultas  (R6)
                 graficos → json_script → dashboard.js        (R7)
```

Detalle en [data-model.md](./data-model.md); pantalla en
[contracts/calidad-ui.md](./contracts/calidad-ui.md).

### Mapa de tests

| Escenario / requisito | Test | Archivo |
|---|---|---|
| FR-002, edges anulada / revalidada / con informe / cambio de límites — solo vigentes, evaluación guardada | `test_cuenta_solo_validaciones_vigentes`, `test_no_reevalua_con_limites_actuales` | `informes/tests/test_calidad.py` |
| FR-003/004, US1 Esc. 1 y 5 — 4 de 40 → 10,0 %, sin límite aparte | `test_indicador_general` | idem |
| FR-005, US1 Esc. 3–4 — variación en p. p., tono, «sin datos previos» | `test_variacion_del_porcentaje` (parametrizado) | idem |
| FR-001, US1 Esc. 2 — mismo período que el selector, por fecha de validación (zona horaria) | `test_usa_el_periodo_del_dashboard`, `test_zona_horaria` | idem |
| FR-006/007, US2 Esc. 1–4 y 6 — mínimo 5, formato, orden, desempates, tope 10 + restantes | `test_ranking_de_pruebas` (parametrizado) | idem |
| FR-006a — el mínimo solo en `calidad.MINIMO_EVALUADOS_RANKING` | `test_minimo_definido_en_un_solo_lugar` | idem |
| FR-008, US3 Esc. 1–2 — tres vertidos siempre, «Sin resultados» | `test_cumplimiento_por_vertido` | idem |
| FR-009, US4 Esc. 1 y 4 — clientes y orígenes, orden, tope | `test_clientes_y_origenes` | idem |
| FR-010, US4 Esc. 2–3 y 5 — enlaces e inactivos sin enlace | `test_enlaces_de_clientes_y_origenes` | idem |
| FR-015, edges — redondeo a la mitad, sin división por cero | `test_porcentaje` (parametrizado) | idem |
| US1 Esc. 6, US2 Esc. 5, US4 Esc. 6, edge base vacía | `test_seccion_sin_datos` | `informes/tests/test_dashboard.py` |
| FR-011/013, US2 Esc. 7, US3 Esc. 3 — canvas, tablas «Ver datos», datos en `json_script` | `test_seccion_calidad_en_pantalla` | idem |
| FR-012, SC-006 — sin permiso no ve la sección | `test_acceso` (existente, + aserción) | idem |
| FR-014 — no modifica nada | `test_solo_lectura` (existente, + sección) | idem |
| SC-004 — consultas acotadas | `test_cantidad_de_consultas` (existente, nuevo máximo) | idem |
| Demo (`ultimos_6`) — ranking con ≥ 3 pruebas y alguna fuera de norma; Pozo 2 y Tanque domiciliario en orígenes | `test_calidad_con_la_demo` | `informes/tests/test_calidad.py` |

## Project Structure

### Documentation (this feature)

```text
specs/033-panel-calidad/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── calidad-ui.md
├── checklists/
│   └── requirements.md
└── tasks.md              # /speckit-tasks
```

### Source Code (repository root)

```text
CLAUDE.md                                         # + sección «Panel de calidad (US 8.4)»
static/css/aqualab.css                            # recompilado si cambian clases
informes/
├── calidad.py                                    # nuevo: indicador, rankings, vertidos
├── views.py                                      # dashboard: + calidad.armar
├── templates/informes/calidad.html               # nuevo: sección «Calidad»
├── templates/informes/dashboard.html             # + include de calidad.html
├── static/informes/dashboard.js                  # + 2 gráficos
└── tests/test_calidad.py                         # nuevo; test_dashboard.py ampliado
```

**Structure Decision**: la sección es parte del dashboard, así que vive en `informes` con un
módulo propio (como `estudios/desvios.py` para la 8.2), sin tocar `tablero.py`.

## Complexity Tracking

Sin violaciones a la constitution: no aplica.
