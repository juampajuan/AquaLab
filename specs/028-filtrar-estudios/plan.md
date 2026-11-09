# Implementation Plan: Filtrar estudios por estado y fecha

**Branch**: `028-filtrar-estudios` | **Date**: 2026-11-08 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/028-filtrar-estudios/spec.md` (SCRUM-74)

## Summary

«Buscar estudio» (`estudios:buscar`, US 5.2) suma los filtros **Estado**, **Desde** y **Hasta**
(fecha de creación, días completos en la zona del laboratorio), combinables con la búsqueda por
texto. Para reutilizar el patrón del historial del cliente (US 3.3), sus campos y su validación se
mueven a una base `estudios.forms.FiltrosEstudioForm`, que heredan `HistorialClienteForm` (sin
cambios visibles) y el nuevo `FiltrarEstudiosForm` (= `BuscarEstudioForm` + la base). La consulta
suma `estudios/busqueda.py:filtro_estado_fechas`. Como en el historial: un valor inválido muestra el
error junto al campo y el listado completo, la paginación lleva la query string completa y
«Limpiar filtros» reemplaza a «Ver todos». Sin modelos, migraciones, dependencias ni JavaScript.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: Django 5.2 LTS (forms, ORM `Q`, `Paginator`, `django.utils.timezone`),
Tailwind CSS 4 y componentes de `templates/ui/` (`campo`, `ayuda`, `estado_vacio`, `paginacion`,
`icono`). Sin dependencias nuevas.

**Storage**: PostgreSQL 16 en Docker. Sin tablas ni migraciones: lee `estudios_estudio`
(`estado`, `fecha_creacion`) y lo que ya muestra el listado.

**Testing**: pytest + pytest-django (fixtures de `estudios/tests/conftest.py`: `cliente_http`,
`escenario_consulta`, …); ruff. `fecha_creacion` es `auto_now_add`: los tests fijan fechas con
`Estudio.objects.filter(pk=…).update(fecha_creacion=…)` (dato de prueba, no de producción).

**Target Platform**: Contenedor Linux (`web`) con Docker Compose; navegador de escritorio.

**Project Type**: Aplicación web Django monolítica con templates en el servidor (sin SPA).

**Performance Goals**: SC-003 — 1000 estudios filtrados en menos de 2 s: un `WHERE` simple más la
paginación de 20 que ya existe; la cantidad de consultas no cambia con los filtros.

**Constraints**: `informes:listar` (que usa `BuscarEstudioForm` y `filtro_busqueda`) no cambia;
el historial del cliente conserva etiquetas, mensajes y tests; CSS compilado al día (CI).

**Scale/Scope**: 1 función de consulta, 2 formularios (base + búsqueda), 1 vista modificada, 1
template modificado, `HistorialClienteForm` refactorizado, ajuste de 3 tests de US 5.2, tests nuevos,
CSS recompilado si hay clases nuevas y nota en `CLAUDE.md`.

Decisiones en [research.md](./research.md) (R1–R7). No hay `NEEDS CLARIFICATION` pendientes.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Cumplimiento | Estado |
|---|---|---|
| **I. Spec primero (SDD)** | Spec de SCRUM-74 (commit `75050ae`); la aprobación del equipo es requisito antes de `/speckit-implement`. PR: «SCRUM-74 – Filtrar estudios por estado y fecha». | ⚠️ aprobación pendiente |
| **II. Simplicidad y Django idiomático** | `forms.Form` con herencia, `Q` y `Paginator`; reutiliza el formulario del historial en vez de copiarlo; sin JS, modelos ni dependencias. | ✅ |
| **III. Tests obligatorios** | Cada escenario y FR con test (ver [Mapa de tests](#mapa-de-tests)); el refactor del historial queda cubierto por sus tests actuales. Sin cálculos nuevos. | ✅ |
| **IV. Integridad de datos** | Solo lectura (GET). | ✅ |
| **V. Seguridad** | `LoginRequiredMiddleware`; GET sin efectos; parámetros validados por el formulario. | ✅ |
| **VI. Idioma y consistencia** | `FiltrosEstudioForm`, `FiltrarEstudiosForm`, `filtro_estado_fechas`, `hay_filtros`; interfaz en español; ruff. | ✅ |
| **Interfaz (UI)** | `ui/campo.html` con errores junto al campo y ayuda (`help_text`) en Desde/Hasta (US 9.1); estado vacío con acción; sin acciones que guarden. | ✅ |

**Post-diseño (Phase 1)**: cumple todos los principios, sin excepciones. El cambio de comportamiento
ante un texto inválido (R3) sale del criterio 6 de la tarea y queda en la spec.

## Diseño

### Flujo

```text
GET /estudios/buscar/?q=&estado=&desde=&hasta=&page=
buscar(request)
  ├─ FiltrarEstudiosForm(GET)
  │    válido   → qs.filter(filtro_busqueda(q)) si q
  │               qs.filter(filtro_estado_fechas(desde, hasta, estado))
  │    inválido → errores junto al campo, qs sin filtrar (R3)
  ├─ Paginator(qs, 20).get_page(page)
  ├─ parametros = GET sin "page" (urlencode)          → ui/paginacion.html
  ├─ hay_filtros = q/estado/desde/hasta recibidos     → «Limpiar filtros»
  └─ filtrado    = formulario válido con algún filtro → mensajes de vacío (R5)
```

```python
# estudios/busqueda.py (firma)
def filtro_estado_fechas(desde=None, hasta=None, estado="") -> Q:
    """Estado actual y días completos de fecha_creacion en la zona del laboratorio."""
```

Parámetros, mensajes y pantalla en [contracts/buscar-estudio-ui.md](./contracts/buscar-estudio-ui.md);
campos que se leen en [data-model.md](./data-model.md).

### Mapa de tests

| Escenario / requisito | Test | Archivo |
|---|---|---|
| US1 Esc. 1, FR-001 — la pantalla ofrece Estado (Todos + 4), Desde y Hasta, «Todos» por defecto | `test_muestra_los_filtros` | `estudios/tests/test_filtros.py` |
| US1 Esc. 2–3, FR-002 — filtra por estado; «Todos» no restringe | `test_filtra_por_estado` (parametrizado por estado), `test_estado_todos_no_restringe` | `estudios/tests/test_filtros.py` |
| US1 Esc. 4, FR-005 — estado fuera de la lista → error, sin filtrar | `test_filtros_invalidos` (parametrizado) | `estudios/tests/test_filtros.py` |
| US2 Esc. 1–2, FR-003 — rango inclusivo con días completos en la zona del laboratorio (00:00 y 23:59 locales); solo desde / solo hasta; desde = hasta | `test_filtro_fechas` (parametrizado), `test_bordes_del_dia_en_zona_del_laboratorio` | `estudios/tests/test_filtros.py` |
| US2 Esc. 3–4, FR-005 — fecha inválida, desde > hasta → error junto al campo, listado completo | `test_filtros_invalidos` (parametrizado) | `estudios/tests/test_filtros.py` |
| US3 Esc. 1, FR-004 — texto + estado + rango combinados | `test_filtros_combinados_con_texto` | `estudios/tests/test_filtros.py` |
| US3 Esc. 2, FR-006 — la paginación conserva texto y filtros | `test_paginacion_conserva_filtros` | `estudios/tests/test_filtros.py` |
| US3 Esc. 3, FR-007 — «Limpiar filtros» con parámetros recibidos (válidos o no), sin parámetros no aparece; ya no hay «Ver todos» | `test_limpiar_filtros` (parametrizado) | `estudios/tests/test_filtros.py` |
| US3 Esc. 4, FR-008 — sin coincidencias con filtros: mensaje propio + acción; sin estudios: aviso actual | `test_sin_coincidencias_con_filtros` | `estudios/tests/test_filtros.py` |
| FR-009 — orden y columnas sin cambios | tests actuales de `test_consulta.py` | `estudios/tests/test_consulta.py` |
| FR-005 / R3 — texto inválido: mensaje + listado completo | 3 tests ajustados (`page_obj` ya no es `None`) | `estudios/tests/test_consulta.py` |
| FR-010 — mismos mensajes y comportamiento que el historial; el historial no cambia | `test_formulario_comparte_reglas_con_historial` + tests actuales del historial | `estudios/tests/test_filtros.py`, `clientes/tests/test_historial*.py` |
| Consulta — `filtro_estado_fechas` sin criterios no restringe | `test_filtro_estado_fechas_vacio` | `estudios/tests/test_filtros.py` |
| SC-003 — consultas constantes con filtros | `test_consultas_no_dependen_de_los_filtros` | `estudios/tests/test_filtros.py` |
| US 9.1 — ayuda en Desde/Hasta (`aria-describedby` → `_helptext`) | `test_ayuda_en_fechas` | `estudios/tests/test_filtros.py` |
| `informes:listar` sin cambios | tests actuales de `informes` | `informes/tests/` |

## Project Structure

### Documentation (this feature)

```text
specs/028-filtrar-estudios/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── buscar-estudio-ui.md
├── checklists/
│   └── requirements.md
└── tasks.md              # /speckit-tasks
```

### Source Code (repository root)

```text
CLAUDE.md                                  # + sección «Filtrar estudios (SCRUM-74)»
estudios/
├── busqueda.py                            # + filtro_estado_fechas
├── forms.py                               # + FiltrosEstudioForm (base), FiltrarEstudiosForm
├── views.py                               # buscar: filtros, parametros, hay_filtros, filtrado
├── templates/estudios/buscar.html         # fila de filtros, «Limpiar filtros», estados vacíos
└── tests/
    ├── test_filtros.py                    # nuevo
    └── test_consulta.py                   # ajuste de 3 tests de texto inválido (R3)
clientes/forms.py                          # HistorialClienteForm hereda FiltrosEstudioForm
static/css/aqualab.css                     # recompilado si el template usa clases nuevas
```

**Structure Decision**: la base de filtros vive en `estudios/forms.py` porque filtra estudios y
`clientes` ya depende de `estudios` (nunca al revés). `FORMATOS_FECHA` y `MENSAJE_FECHA_INVALIDA`
pasan a `estudios/forms.py` y `clientes/forms.py` los importa, para que los mensajes no se separen.
`informes/forms.py` tiene su propia copia de `FORMATOS_FECHA` y queda fuera de alcance.

## Complexity Tracking

Sin violaciones a la constitution: no aplica.
