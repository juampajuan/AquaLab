# Implementation Plan: Seleccionar estudio y controlar pruebas pendientes

**Branch**: `020-controlar-pruebas-pendientes` | **Date**: 2026-11-01 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/020-controlar-pruebas-pendientes/spec.md` (US 7.1)

## Summary

Se crea la app `informes` con tres vistas: el listado de estudios a informar (búsqueda de
`estudios:buscar`, avance «N de M pruebas completadas» y filtro «Solo listos para informar»), el
control de pruebas de un estudio (todas sus pruebas con su estado, marcando «Incompleta» o «Sin
validar») y la acción «Generar informe» (POST). Una única regla,
`informes.servicios.motivo_para_no_informar`, decide si el estudio se puede informar (100% de sus
pruebas Completadas y sin informe emitido); el control la usa para habilitar el botón y
`comprobar_generacion` la revalida con el estudio bloqueado. Hasta US 7.2, una generación permitida
solo avisa que todavía no está disponible. Sin modelos ni migraciones.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: Django 5.2 LTS; componentes de `templates/ui/` (Tailwind ya compilado).
Sin dependencias nuevas ni JavaScript.

**Storage**: PostgreSQL 16 en Docker. **Sin migraciones**: solo lectura más un bloqueo de fila.

**Testing**: pytest 9.1.1 + pytest-django 4.14.0; fixtures de `estudios/tests/conftest.py`
(`catalogo`, `estudio_de`, `empleado`, `muestra`, `cliente_http`), importadas desde `informes/tests/conftest.py`, y `asignacion_de` de `estudios/tests/utiles.py`;
ruff 0.17.1.

**Target Platform**: Contenedor Linux (`web`) con Docker Compose; navegador de escritorio.

**Project Type**: Aplicación web Django monolítica con templates en el servidor (sin SPA).

**Performance Goals**: Encontrar un estudio y saber si está listo en menos de 30 s (SC-001); el
listado hace una consulta anotada por página.

**Constraints**: La regla de habilitación es única y se revalida al generar (FR-009); consultar no
modifica nada (FR-011); US 6.4 (rama `019-validar-resultados`) todavía no está en `main`.

**Scale/Scope**: app nueva `informes` (servicios, vistas, urls, 2 templates, tests); extracción de
`estudios/busqueda.py`; enlaces en menú, inicio y detalle del estudio; nota en `CLAUDE.md`.

Decisiones en [research.md](./research.md) (R1–R7). No hay `NEEDS CLARIFICATION` pendientes.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Cumplimiento | Estado |
|---|---|---|
| **I. Spec primero (SDD)** | Spec de US 7.1 (clave de Jira a confirmar). PR: «US 7.1 – Seleccionar estudio y controlar pruebas pendientes». El código espera la aprobación de la spec. | ✅ |
| **II. Simplicidad y Django idiomático** | Vistas de función, `Paginator`, anotaciones `Count`, `messages`; app `informes` prevista en la constitution; reutiliza `BuscarEstudioForm` y el filtro de búsqueda; sin modelos ni dependencias nuevas. | ✅ |
| **III. Tests obligatorios** | Cada escenario y FR con test (ver [Mapa de tests](#mapa-de-tests)). | ✅ |
| **IV. Integridad de datos** | Solo lectura; la generación se bloquea si hay pruebas sin validar, y se revalida con el estudio bloqueado. Nada cambia con informe emitido. | ✅ |
| **V. Seguridad** | Sesión obligatoria (`LoginRequiredMiddleware`); generar solo por POST con CSRF; 404 para estudios inexistentes. | ✅ |
| **VI. Idioma y consistencia** | Interfaz, mensajes y nombres en español (`motivo_para_no_informar`, `comprobar_generacion`, `InformeNoDisponible`). ruff. | ✅ |
| **Interfaz (UI)** | Componentes de `templates/ui/`; mismos badges de estado que el detalle. «Generar informe» no guarda datos en esta historia; su confirmación es de US 7.2. | ✅ |

**Post-diseño (Phase 1)**: cumple todos los principios, sin excepciones.

## Diseño

### Flujo

```text
informes:listar  ── Seleccionar ──▶  informes:control  ── POST Generar ──▶  informes:generar
 (q, listos, page)                  motivo_para_no_informar               comprobar_generacion
 estudios_para_informar               ├─ None → botón habilitado            (select_for_update)
   filtro_busqueda(q)                 └─ motivo → botón deshabilitado       ├─ InformeNoDisponible → error
   + Count(total, completadas)                                              └─ ok → aviso «próximamente» (US 7.2)
```

Pantallas y mensajes en [contracts/control-informe-ui.md](./contracts/control-informe-ui.md);
regla y etiquetas en [data-model.md](./data-model.md).

### Mapa de tests

| Escenario / requisito | Test | Archivo |
|---|---|---|
| US1 Esc. 1, FR-001/002 — listado con estado y avance, orden, acceso desde menú e inicio | `test_listado_muestra_estado_y_avance`, `test_listado_ordenado_y_paginado`, `test_menu_e_inicio_enlazan_informes` | `informes/tests/test_listar.py` |
| US1 Esc. 2, FR-003 — búsqueda con los criterios de estudios; sin resultados | `test_busqueda_por_numero_pi_cliente_y_tipo` (parametrizado), `test_busqueda_sin_resultados` | `informes/tests/test_listar.py` |
| US1 Esc. 3, FR-003 — filtro «Solo listos» | `test_filtro_solo_listos`, `test_filtro_listos_coincide_con_la_regla` | `informes/tests/test_listar.py` |
| US1 Esc. 4–5, FR-004 — seleccionar abre el control; enlace desde el detalle | `test_seleccionar_abre_control`, `test_detalle_enlaza_control` | `informes/tests/test_listar.py`, `informes/tests/test_control.py` |
| US2 Esc. 1, FR-005 — ficha y todas las pruebas con estado | `test_control_muestra_ficha_y_pruebas` | `informes/tests/test_control.py` |
| US2 Esc. 2–3, FR-006 — «Incompleta» y «Sin validar», conteo | `test_control_marca_incompletas_y_sin_validar` | `informes/tests/test_control.py` |
| US2 Esc. 4, FR-008 — botón deshabilitado con motivo | `test_boton_deshabilitado_con_pruebas_sin_completar` | `informes/tests/test_control.py` |
| US2 Esc. 5, FR-007/008 — 100% Completadas habilita | `test_boton_habilitado_con_todas_completadas` | `informes/tests/test_control.py` |
| US2 Esc. 6, FR-009 — rechazo por otra vía; pérdida de validación entre GET y POST | `test_generar_rechaza_si_hay_pruebas_sin_completar`, `test_generar_revalida_con_datos_vigentes`, `test_generar_solo_post` | `informes/tests/test_generar.py` |
| US2 Esc. 7, FR-010 — informe emitido | `test_control_con_informe_emitido`, `test_generar_con_informe_emitido_rechaza` | `informes/tests/test_control.py`, `informes/tests/test_generar.py` |
| FR-007 — regla: emitido, sin pruebas, 99 de 100, todas | `test_motivo_para_no_informar` (parametrizado) | `informes/tests/test_servicios.py` |
| FR-009 — `comprobar_generacion` bloquea el estudio | `test_comprobar_generacion_bloquea_estudio` | `informes/tests/test_servicios.py` |
| FR-011 — consultar no modifica nada | `test_consultar_no_modifica` | `informes/tests/test_control.py` |
| SC-004 — mismos estados que el detalle | `test_control_y_detalle_muestran_el_mismo_estado` | `informes/tests/test_control.py` |
| Edge — estudio inexistente | `test_control_estudio_inexistente_404` | `informes/tests/test_control.py` |
| R4 — refactor de la búsqueda de estudios | tests existentes de `estudios/tests/test_consulta.py` | — |

## Project Structure

### Documentation (this feature)

```text
specs/020-controlar-pruebas-pendientes/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── control-informe-ui.md
├── checklists/
│   └── requirements.md
└── tasks.md              # /speckit-tasks
```

### Source Code (repository root)

```text
CLAUDE.md                                   # sección «Control previo al informe (US 7.1)»
config/
├── settings.py                             # + "informes" en INSTALLED_APPS
└── urls.py                                 # + path("informes/", include("informes.urls"))
estudios/
├── busqueda.py                             # nuevo: filtro_busqueda(q) extraído de views.buscar
├── views.py                                # buscar usa filtro_busqueda
└── templates/estudios/detalle.html         # + enlace «Controlar para informe»
informes/                                   # app nueva (sin modelos)
├── __init__.py
├── apps.py
├── servicios.py                            # motivo_para_no_informar, comprobar_generacion,
│                                           # estudios_para_informar, InformeNoDisponible
├── views.py                                # listar, control, generar
├── urls.py
├── templates/informes/
│   ├── listar.html
│   └── control.html
└── tests/
    ├── __init__.py
    ├── conftest.py                         # importa las fixtures de estudios/tests/conftest.py (sin pytest_plugins)
    ├── test_servicios.py
    ├── test_listar.py
    ├── test_control.py
    └── test_generar.py
templates/
├── inicio.html                             # + acceso rápido «Informes»
└── ui/menu.html                            # + sección «Informes»
```

**Structure Decision**: app `informes` nueva según la constitution (R1); la única pieza que se
toca en `estudios` es la extracción del filtro de búsqueda y el enlace del detalle.

## Complexity Tracking

Sin violaciones de la constitution.
