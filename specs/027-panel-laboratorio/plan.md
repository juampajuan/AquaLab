# Implementation Plan: Panel del laboratorio

**Branch**: `027-panel-laboratorio` | **Date**: 2026-11-08 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/027-panel-laboratorio/spec.md` (SCRUM-75, US 8.3)

## Summary

Nueva pantalla `informes:dashboard` (`/informes/dashboard/`), con enlace propio debajo de «Inicio»
solo para quien tiene el permiso nuevo `informes.ver_dashboard` (una migración lo da a
«Bioquímicos» y «Administradores»). Un módulo de cálculo puro, `informes/tablero.py`, define los
períodos (este mes, mes anterior, 3 y 6 meses, con su período anterior), cuenta muestras, estudios
e informes, calcula el tiempo de respuesta (días corridos ingreso → emisión), las series fijas
(6 meses y 12 semanas) y las alertas (estudios sin actividad hace más de 7 días; Finalizados sin
informe). Todo con consultas agregadas en la zona horaria del laboratorio. Los gráficos se dibujan
con Chart.js 4.4.7 guardado en `static/vendor/`, leyendo los datos de `json_script`; cada gráfico
tiene su tabla equivalente. Las variaciones llevan flecha, signo y color según si el cambio es
favorable.

## Technical Context

**Language/Version**: Python 3.12; JavaScript sin dependencias propias (solo Chart.js).

**Primary Dependencies**: Django 5.2 LTS (ORM con `TruncDate`/`TruncMonth` con `tzinfo`,
`Subquery`, `Greatest`, `Max`; auth: permisos y grupos), Tailwind CSS 4 y `templates/ui/`.
**Nueva**: Chart.js 4.4.7 (MIT), archivo `chart.umd.min.js` versionado en `static/vendor/` (la
constitution la prevé «cuando lo pida una spec»; el criterio 7 lo pide).

**Storage**: PostgreSQL 16. Sin tablas nuevas; migración `informes/0004_permiso_dashboard.py`
(permiso en `Informe.Meta.permissions` + asignación a los dos grupos).

**Testing**: pytest + pytest-django; fixtures de `estudios/tests/conftest.py` (`estudio_de`,
`cargar`, `validar`, `bioquimico`, `cliente_bioquimico`) y la demo de SCRUM-78
(`estudios.demo.cargar_demo` con `ahora` fijo) para escenarios integrales; ruff.

**Target Platform**: Contenedor `web` (Docker Compose) y Render; navegador de escritorio.

**Project Type**: Aplicación web Django monolítica con templates en el servidor.

**Performance Goals**: Panel completo < 2 s con la demo y < 5 s con 10.000 estudios (SC-004): una
cantidad fija de consultas agregadas (~12), sin N+1.

**Constraints**: Solo lectura (FR-018); zona horaria del laboratorio (FR-016); sin CDN (FR-017);
gráficos con tabla equivalente (FR-012); color nunca como única señal (FR-006a); CSS compilado al
día (CI).

**Scale/Scope**: `informes/tablero.py`, vista `dashboard`, URL, template `informes/dashboard.html`,
`informes/static/informes/dashboard.js`, `static/vendor/chart.umd.min.js`, ícono
`templates/ui/iconos/chart-column.svg`, enlace en `templates/ui/menu.html`, migración, CLAUDE.md y
tests.

Decisiones en [research.md](./research.md) (R1–R9). No hay `NEEDS CLARIFICATION` pendientes.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Cumplimiento | Estado |
|---|---|---|
| **I. Spec primero (SDD)** | Spec de US 8.3 con 3 aclaraciones (2026-11-08). El código espera la aprobación de la spec. | ✅ |
| **II. Simplicidad y Django idiomático** | Vive en la app `informes` (sin app nueva: la lista de módulos de la constitution no la prevé); cálculo con ORM y agregaciones; un solo módulo de cálculo; Chart.js es la dependencia prevista por la constitution y el criterio 7; JS mínimo. | ✅ |
| **III. Tests obligatorios** | Cada FR y escenario con test (ver [Mapa de tests](#mapa-de-tests)), con fechas fijas y la demo para los casos integrales. | ✅ |
| **IV. Integridad de datos** | Solo lectura; no modifica ningún registro. | ✅ |
| **V. Seguridad** | `LoginRequiredMiddleware` + `@permission_required("informes.ver_dashboard", raise_exception=True)`; el enlace solo con `perms.informes.ver_dashboard`. | ✅ |
| **VI. Idioma y consistencia** | `tablero.py`, `periodo`, `tiempo_respuesta`, `alertas`; interfaz en español; ruff. | ✅ |
| **Interfaz (UI)** | Componentes de `templates/ui/` (`ui/indicador.html`, `.tarjeta`, `.tabla`, `ui/estado.html`, `ui/estado_vacio.html`); tokens de color del tema (`exito`, `peligro`, `tinta-suave`). | ✅ |

**Post-diseño (Phase 1)**: cumple todos los principios, sin excepciones.

## Diseño

```text
GET /informes/dashboard/?periodo=este_mes|mes_anterior|ultimos_3|ultimos_6
  ├─ sin sesión → login; sin permiso → 403
  └─ tablero.armar(hoy, clave_periodo) →
       periodo + anterior          (R2)
       indicadores ×3 + variación  (R3, R4)
       tiempo de respuesta + var.  (R5)
       estudios por estado         (hoy)
       serie mensual (6)           (R5)  ─┐
       serie semanal (12)          (R6)  ─┴→ json_script → dashboard.js → Chart.js
       alertas: sin avanzar / finalizados sin informe (R7)
```

Detalle en [data-model.md](./data-model.md); pantalla en
[contracts/dashboard-ui.md](./contracts/dashboard-ui.md).

### Mapa de tests

| Escenario / requisito | Test | Archivo |
|---|---|---|
| FR-004/006, US1 Esc. 2–4 — períodos y período anterior (día 1, día 8, 31 de marzo, 3 y 6 meses) | `test_periodos` (parametrizado) | `informes/tests/test_tablero.py` |
| FR-005, US1 Esc. 2, edge «muestra con varios estudios» | `test_indicadores_cuentan_por_fecha` | idem |
| FR-006/006a, US1 Esc. 5–6 — variación, «sin datos previos», tono según favorable | `test_variacion` (parametrizado) | idem |
| FR-007, US2 Esc. 1–2 — tiempo de respuesta, sin informes | `test_tiempo_de_respuesta` | idem |
| FR-008/010/011, US2 Esc. 3–5 — series de 6 meses y 12 semanas, independientes del período | `test_series_fijas` | idem |
| FR-009, US1 Esc. 7 — estudios por estado | `test_estudios_por_estado` | idem |
| FR-013, US3 Esc. 1–2 — última actividad (creación, carga, corrección, validación) | `test_sin_avanzar` | idem |
| FR-014, US3 Esc. 3 — Finalizados sin informe con días desde la última validación | `test_finalizados_sin_informe` | idem |
| FR-016 — zona horaria (registro a las 23:30 de un día) | `test_zona_horaria` | idem |
| SC-006 — la demo muestra Pozo domiciliario y Escuela N° 12 | `test_alertas_con_la_demo` | idem |
| FR-001/003, US4 Esc. 2–3 — menú, 403, login | `test_acceso` (parametrizado) | `informes/tests/test_dashboard.py` |
| FR-002, US4 Esc. 1 — permiso en los dos grupos | `test_permiso_en_grupos` | idem |
| FR-004 — selector, período inválido → este mes | `test_selector_de_periodo` | idem |
| FR-012/015/017 — tablas de los gráficos, alertas con enlaces, Chart.js local | `test_pantalla_completa` | idem |
| Edge «base vacía» | `test_base_vacia` | idem |
| FR-018 — no modifica nada | `test_solo_lectura` | idem |
| SC-004 — consultas acotadas | `test_cantidad_de_consultas` (`django_assert_max_num_queries`) | idem |

## Project Structure

### Documentation (this feature)

```text
specs/027-panel-laboratorio/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── dashboard-ui.md
├── checklists/
│   └── requirements.md
└── tasks.md              # /speckit-tasks
```

### Source Code (repository root)

```text
CLAUDE.md                                         # + sección «Panel del laboratorio (US 8.3)»
static/vendor/chart.umd.min.js                    # nuevo: Chart.js 4.4.7 (MIT, con su cabecera)
static/css/aqualab.css                            # recompilado si cambian clases
templates/ui/iconos/chart-column.svg              # nuevo (Lucide, ISC)
templates/ui/menu.html                            # + enlace «Dashboard» debajo de «Inicio»
informes/
├── models.py                                     # Informe.Meta.permissions + ver_dashboard
├── migrations/0004_permiso_dashboard.py          # nueva: permiso + grupos
├── tablero.py                                    # nuevo: períodos, indicadores, series, alertas
├── views.py                                      # + dashboard
├── urls.py                                       # + dashboard/
├── templates/informes/dashboard.html             # nuevo
├── static/informes/dashboard.js                  # nuevo: dibuja los 2 gráficos
└── tests/test_tablero.py, test_dashboard.py      # nuevos
estudios/tests/conftest.py                        # bioquimico: + ver_dashboard
```

**Structure Decision**: el panel vive en `informes` (reportes del laboratorio), porque la
constitution fija la lista de apps y no prevé una app de dashboard; `comparacion` queda para la
8.1/8.2.

## Complexity Tracking

Sin violaciones a la constitution: no aplica.
