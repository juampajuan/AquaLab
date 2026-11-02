# Implementation Plan: Consultar historial del cliente

**Branch**: `023-historial-cliente` | **Date**: 2026-11-02 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/023-historial-cliente/spec.md` (US 3.3, Jira a confirmar)

## Summary

La ficha del cliente (US 3.2) suma el botón **Historial**, que abre `clientes:historial`
(`/clientes/<pk>/historial/`). La pantalla lista las muestras del cliente de la fecha de ingreso
más reciente a la más antigua (a igual fecha, N° PI descendente), cada una con su origen y sus
estudios (número, tipo guardado al crearlo, estado actual y, si hay informe emitido, «Ver informe
INF-000001»). Un formulario GET (`HistorialClienteForm`) filtra por rango de fecha de ingreso y por
estado del estudio; la consulta vive en `clientes/historial.py:muestras_del_historial`, que pagina
muestras (20 por página) y trae los estudios con un `Prefetch` filtrado, así los estudios de una
muestra nunca se cortan entre páginas y la cantidad de consultas no depende del tamaño del
historial. Es una pantalla de solo lectura: no hay modelos, migraciones ni servicios que escriban.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: Django 5.2 LTS (ORM con `Prefetch`, forms, `Paginator`, messages),
Tailwind CSS 4 y componentes de `templates/ui/` (`encabezado`, `estado`, `estado_vacio`,
`paginacion`, `campo`, `errores_form`). Sin dependencias nuevas ni JavaScript.

**Storage**: PostgreSQL 16 en Docker. Sin tablas ni migraciones nuevas: lee `clientes_cliente`,
`muestras_muestra`, `muestras_origen`, `estudios_estudio` e `informes_informe`.

**Testing**: pytest 9.1.1 + pytest-django 4.14.0; fixtures de `clientes/tests/conftest.py`
(`empleado`, `cliente_autenticado`, `cliente_existente`) y helpers nuevos para crear muestras y
estudios en un estado dado; `CaptureQueriesContext` para comparar consultas con 1 y 100 muestras
(SC-004); ruff 0.17.1.

**Target Platform**: Contenedor Linux (`web`) con Docker Compose; navegador de escritorio.

**Project Type**: Aplicación web Django monolítica con templates en el servidor (sin SPA).

**Performance Goals**: Historial de un cliente con 100 muestras en menos de 2 s (SC-004): cantidad
de consultas constante por página (la misma con 1 que con 100 muestras: sin N+1 por muestra,
estudio ni informe).

**Constraints**: Solo lectura (FR-013); solo muestras del cliente (SC-003); estudios de una muestra
en la misma página (FR-012); tipo de estudio desde `tipo_nombre_snapshot` (US 5.2); cliente
inactivo con el mismo aviso que la ficha (FR-002); CSS compilado al día (CI).

**Scale/Scope**: 1 módulo de consulta, 1 formulario, 1 vista, 1 URL, 1 template nuevo + botón en
`clientes/detalle.html`, CSS recompilado si aparecen clases nuevas, sección en `CLAUDE.md` y tests.

Decisiones en [research.md](./research.md) (R1–R7). No hay `NEEDS CLARIFICATION` pendientes.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Cumplimiento | Estado |
|---|---|---|
| **I. Spec primero (SDD)** | Spec de US 3.3 (commit `6b7e212`); la aprobación del equipo es requisito antes de `/speckit-implement`. PR: «US 3.3 – Consultar historial del cliente». Clave de Jira a confirmar. | ⚠️ aprobación pendiente |
| **II. Simplicidad y Django idiomático** | Vista función + `forms.Form` + ORM (`Prefetch`, `Paginator`) en la app `clientes` (la US es del módulo Clientes); reutiliza las vistas de detalle existentes; sin JS, sin modelos ni dependencias (YAGNI). | ✅ |
| **III. Tests obligatorios** | Cada escenario y FR con test (ver [Mapa de tests](#mapa-de-tests)). Sin cálculos nuevos. | ✅ |
| **IV. Integridad de datos** | Solo lectura: no hay POST ni escritura; el informe se muestra desde su copia (`informes:ver`, US 7.2). | ✅ |
| **V. Seguridad** | `LoginRequiredMiddleware` cubre la vista; GET que no modifica nada; cliente inactivo rechazado igual que la ficha. | ✅ |
| **VI. Idioma y consistencia** | `historial`, `muestras_del_historial`, `HistorialClienteForm`, `estudios_historial`; interfaz en español; ruff. | ✅ |
| **Interfaz (UI)** | Componentes de `templates/ui/`; errores junto a cada campo; estado vacío; sin acciones que guarden (no requiere confirmación). | ✅ |

**Post-diseño (Phase 1)**: cumple todos los principios, sin excepciones nuevas.

## Diseño

### Flujo

```text
GET /clientes/<pk>/                     → ficha (US 3.2) + botón «Historial»
GET /clientes/<pk>/historial/           → 404 inexistente | 302 buscar + aviso si inactivo
    ?desde=&hasta=&estado=&page=          | 200 historial (filtros inválidos → errores, sin filtrar)
historial(request, pk)
  └─ HistorialClienteForm(GET) → muestras_del_historial(cliente, desde, hasta, estado)
     → Paginator(20) → template: muestra → muestra.estudios_historial (prefetch, con informe)
```

Rutas, parámetros y textos en [contracts/historial-cliente-ui.md](./contracts/historial-cliente-ui.md);
datos que se leen en [data-model.md](./data-model.md).

### Mapa de tests

| Escenario / requisito | Test | Archivo |
|---|---|---|
| US1 Esc. 1, FR-001 — la ficha ofrece «Historial» | `test_ficha_ofrece_historial` | `clientes/tests/test_historial.py` |
| US1 Esc. 2, FR-003/004, SC-003 — solo las muestras del cliente, con N° PI, fecha, origen y estudios (número, tipo guardado, estado) | `test_lista_muestras_del_cliente`, `test_muestra_tipo_guardado` | `clientes/tests/test_historial.py` |
| US1 Esc. 3, FR-005 — orden por fecha de ingreso y N° PI desc; estudios desc | `test_orden_del_historial` | `clientes/tests/test_historial_consulta.py` |
| US1 Esc. 4 — muestra sin estudios: «Sin estudios» | `test_muestra_sin_estudios` | `clientes/tests/test_historial.py` |
| US1 Esc. 5, FR-009 — cliente sin muestras | `test_cliente_sin_muestras` | `clientes/tests/test_historial.py` |
| US1 Esc. 6 — encabezado con cliente y documento, volver a la ficha | `test_encabezado_identifica_cliente` | `clientes/tests/test_historial.py` |
| FR-002 — inactivo → aviso y 302; inexistente → 404; sin sesión → login | `test_cliente_inactivo`, `test_cliente_inexistente_404`, `test_requiere_sesion` | `clientes/tests/test_historial.py` |
| US2 Esc. 1, FR-006 — rango de fechas inclusivo; solo desde / solo hasta | `test_filtro_fechas` (parametrizado) | `clientes/tests/test_historial_consulta.py` |
| US2 Esc. 2, FR-007 — filtro por estado: muestras con algún estudio y solo esos estudios | `test_filtro_estado` | `clientes/tests/test_historial_consulta.py` |
| US2 Esc. 3 — filtros combinados | `test_filtros_combinados` | `clientes/tests/test_historial_consulta.py` |
| US2 Esc. 4, FR-006 — desde > hasta, fecha inválida, estado inexistente → error junto al campo, sin filtrar, con «Limpiar filtros» | `test_filtros_invalidos` (parametrizado) | `clientes/tests/test_historial.py` |
| US2 Esc. 5, FR-009 — sin coincidencias: mensaje propio y «Limpiar filtros» | `test_sin_coincidencias` | `clientes/tests/test_historial.py` |
| US2 Esc. 6, FR-008/012 — paginación de 20 muestras, conserva filtros, estudios no se cortan | `test_paginacion_conserva_filtros` | `clientes/tests/test_historial.py` |
| US3 Esc. 1–2, FR-010 — enlaces al detalle del estudio y a la ficha de la muestra | `test_enlaces_a_detalles` | `clientes/tests/test_historial.py` |
| US3 Esc. 3–4, FR-011 — «Ver informe INF-…» solo si el estudio tiene `Informe` | `test_ver_informe_solo_con_informe` | `clientes/tests/test_historial.py` |
| FR-013 — solo lectura: POST no permitido (405), nada cambia | `test_historial_solo_lectura` | `clientes/tests/test_historial.py` |
| SC-004 — misma cantidad de consultas con 1 y con 100 muestras | `test_consultas_acotadas` | `clientes/tests/test_historial.py` |
| Diseño — usa los componentes de `templates/ui/` | `test_historial_usa_componentes` | `clientes/tests/test_diseno.py` |

## Project Structure

### Documentation (this feature)

```text
specs/023-historial-cliente/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── historial-cliente-ui.md
├── checklists/
│   └── requirements.md
└── tasks.md              # /speckit-tasks
```

### Source Code (repository root)

```text
CLAUDE.md                                      # + sección «Historial del cliente (US 3.3)»
clientes/
├── historial.py                               # nuevo: muestras_del_historial
├── forms.py                                   # + HistorialClienteForm
├── views.py                                   # + historial
├── urls.py                                    # + <int:pk>/historial/
├── templates/clientes/
│   ├── detalle.html                           # + botón «Historial»
│   └── historial.html                         # nuevo
└── tests/
    ├── conftest.py                            # + helpers muestra_de / estudio_en
    ├── test_historial.py                      # nuevo (vista)
    ├── test_historial_consulta.py             # nuevo (consulta y filtros)
    └── test_diseno.py                         # + componentes del historial
static/css/aqualab.css                         # recompilado si el template usa clases nuevas
```

**Structure Decision**: el historial vive en la app `clientes` porque la US 3.3 es del módulo
Clientes y se entra desde la ficha; lee muestras, estudios e informes sin modificarlos. Los
imports de modelos de otras apps quedan en `clientes/historial.py` (nunca en `clientes/models.py`,
que importan `muestras` y `estudios`), para no crear ciclos.

## Complexity Tracking

Sin violaciones a la constitution: no aplica.
