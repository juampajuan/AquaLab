# Implementation Plan: Notificar desvíos relevantes

**Branch**: `032-notificar-desvios` | **Date**: 2026-11-09 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/032-notificar-desvios/spec.md` (SCRUM-61, US 8.2)

## Summary

El desvío **no se guarda**: un módulo nuevo `estudios/desvios.py` lo calcula al vuelo para los
resultados Cargados y sin validar, con el historial de `comparacion.comparar` (US 8.1, con un campo
nuevo `HistorialPrueba.anteriores`), el promedio de los últimos N validados de
`comparacion.variacion` y una comparación `Decimal` exacta contra el umbral de
`settings.AQUALAB_DESVIOS` (30 %, N = 3). Se muestra en el detalle del estudio, en la pantalla de
validación y en una sección «Desvíos sin revisar» del Dashboard con lista completa
`estudios:desvios`. Una corrección se refleja sola porque se evalúa el resultado vigente; no se
toca `calculo.py` ni los servicios de carga y corrección. **Validar es revisar**: la validación
destaca las pruebas con desvío con un campo «Observación», la confirmación cuenta las elegidas con
desvío y `servicios.validar_resultados` vuelve a evaluar bajo el bloqueo y guarda en la
`Validacion` la observación y, como constancia, el promedio y el umbral (migración
`estudios.0009_validacion_desvio`). No bloquea nada ni aparece en el informe. La demo valida con
observación el desvío de Pozo 2 del mes anterior.

## Technical Context

**Language/Version**: Python 3.12.

**Primary Dependencies**: Django 5.2 LTS (ORM, `Paginator`, formularios, mensajes), Tailwind CSS 4
y `templates/ui/`. Sin dependencias nuevas ni JavaScript nuevo.

**Storage**: PostgreSQL 16. Migración `estudios.0009_validacion_desvio`: tres columnas nuevas en
`Validacion` (`observacion`, `desvio_promedio`, `desvio_umbral`) y un `CheckConstraint`. Sin tabla
de desvíos.

**Testing**: pytest + pytest-django con las fixtures de `estudios/tests/conftest.py` (`catalogo`,
`empleado`, `bioquimico`, `cliente_bioquimico`, `cliente_http`, `pruebas_division`, fábrica
`estudio_en_origen` de la 8.1), helpers `estudios.tests.utiles.cargar`/`validar`/`asignacion_de`,
`corregir_mediciones`, `settings` para la regla, `django_assert_max_num_queries`, concurrencia con
`transaction=True` como `test_concurrencia_validacion.py`, la demo de SCRUM-78; ruff.

**Target Platform**: Contenedor `web` (Docker Compose) y Render; navegador de escritorio.

**Project Type**: Aplicación web Django monolítica con templates en el servidor.

**Performance Goals**: SC-007 — detalle y validación: una llamada a `comparar` por estudio
(cantidad fija de consultas). Dashboard y lista: una consulta de asignaciones pendientes + una
llamada a `comparar` por estudio con resultados sin validar (decenas como mucho; research R8).
Tests con `django_assert_max_num_queries`.

**Constraints**: `Decimal` exacto, sin `float` (FR-002); calcular desvíos no escribe nada
(FR-011); la constancia se escribe solo al crear la validación, en su transacción (FR-009); no
bloquea validar ni emitir; nada en informe/PDF/correo (FR-012); color nunca como única señal; CSS
compilado al día (CI).

**Scale/Scope**: `estudios/desvios.py`, 3 campos + migración en `Validacion`, campo `anteriores`
en `comparacion.py`, cambios en `servicios.validar_resultados` y `ValidarResultadosForm`, 1 vista +
1 URL (`estudios:desvios`), parciales y cambios en `detalle.html`, `validar_resultados*.html` e
`informes/dashboard.html`; demo; tests; CLAUDE.md.

Decisiones en [research.md](./research.md) (R1–R11). No hay `NEEDS CLARIFICATION` pendientes.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Cumplimiento | Estado |
|---|---|---|
| **I. Spec primero (SDD)** | Spec de US 8.2 (SCRUM-61) en Draft con los ajustes del usuario; el código espera su aprobación. | ✅ |
| **II. Simplicidad y Django idiomático** | Sin modelo nuevo: el desvío es derivado; tres campos en `Validacion`; un módulo de reglas de solo lectura; reutiliza `comparar`/`variacion` (sin segunda definición del historial), parciales de UI, paginación y la confirmación existente de la validación; configuración en `settings`; sin señales ni comandos ni dependencias. | ✅ |
| **III. Tests obligatorios** | Cada escenario y FR mapeado a tests ([Mapa de tests](#mapa-de-tests)); la regla con casos de borde explícitos (30 % exacto, 30,0x %, promedio 0, A/P, últimos 3 de 5). | ✅ |
| **IV. Integridad de datos** | Calcular no escribe; la constancia nace con la validación, en su transacción y bajo el bloqueo del estudio, con la evaluación de ese momento; nunca se modifica (la validación se anula, no se edita); no altera resultados ni estados. | ✅ |
| **V. Seguridad** | `LoginRequiredMiddleware`; revisar solo ocurre dentro de `validar_resultados`, que ya revalida `estudios.validar_resultados` en vista y servicio; la constancia la calcula el servidor (no viene del formulario); `informes.ver_dashboard` y `require_GET` en la lista. | ✅ |
| **VI. Idioma y consistencia** | `desvios.py`, `Regla`, `Deteccion`, `Pendiente`, `evaluar_estudio`, `pendientes`, `observacion`, `desvio_promedio`, `desvio_umbral`; interfaz en español; ruff. | ✅ |
| **Interfaz (UI)** | Parciales reutilizables (`estudios/desvio.html`, `estudios/desvios_tabla.html`) con `ui/estado.html`, `ui/icono.html`, `ui/ayuda.html`, `ui/campo.html` (`help_text` en la observación), `ui/paginacion.html`; la revisión se guarda con la confirmación existente de la validación, que la anuncia; mensajes de Django; ícono + texto. | ✅ |

**Post-diseño (Phase 1)**: cumple todos los principios, sin excepciones.

## Diseño

```text
carga / corrección ──► Resultado (Cargada)        (sin cambios: calculo.py intacto)

detalle / validación ──► desvios.evaluar_estudio(estudio, asignaciones)               (R1)
dashboard / lista    ──► desvios.pendientes() ─ por estudio ─► evaluar_estudio
                              comparar(origen, estudio=estudio, codigos=…)              (R2)
                              por prueba: detectar(historial, regla())                  (R3, R4)
                                anteriores[-N:] → variacion() → promedio, textos
                                es_desvio(valor, promedio, umbral)  (Decimal exacto)

validación: fila destacada + observacion_<pk> → confirmación «N de los M elegidos…»
  servicios.validar_resultados(…, observaciones)  [estudio y pruebas bloqueados]       (R5)
     evaluar_estudio → Validacion(observacion, desvio_promedio, desvio_umbral)          (R6)
```

### `estudios/desvios.py` (interfaz)

Ver [contracts/desvios-ui.md](./contracts/desvios-ui.md#interfaz-interna-estudiosdesviospy):
`regla`, `es_desvio`, `detectar`, `historial_suficiente`, `evaluar_estudio`, `pendientes`,
`enlace_comparacion`, `texto_regla` y textos. Todo de solo lectura; las funciones de regla son
puras (se prueban sin base).

### Archivos

```text
config/settings.py                    # + AQUALAB_DESVIOS (R7)
estudios/
├── desvios.py                        # NUEVO: regla, detección al vuelo, pendientes, textos
├── models.py                         # Validacion: + observacion, desvio_promedio, desvio_umbral (R6)
├── migrations/0009_validacion_desvio.py   # NUEVO
├── comparacion.py                    # HistorialPrueba.anteriores (R2)
├── servicios.py                      # validar_resultados: + observaciones, constancia (R5)
├── forms.py                          # ValidarResultadosForm: + observacion_<pk>, observaciones()
├── views.py                          # detalle y validar_resultados: desvíos; + desvios_pendientes
├── urls.py                           # + desvios/
├── demo.py                           # observación al validar Pozo 2 mes 1 (R10)
├── templates/estudios/
│   ├── desvio.html                   # NUEVO: marca pendiente / revisado (parcial)
│   ├── desvios_tabla.html            # NUEVO: tabla de pendientes (dashboard y lista)
│   ├── desvios.html                  # NUEVO: lista completa paginada
│   ├── detalle.html                  # + marca
│   ├── validar_resultados.html       # + resumen, filas destacadas, observación, «Historial insuficiente»
│   └── validar_resultados_confirmar.html  # + «N de los M elegidos tienen desvío» + observaciones
└── tests/
    ├── test_desvios.py               # NUEVO: regla pura, detección al vuelo, pendientes, regla configurable
    ├── test_desvios_validacion.py    # NUEVO: constancia al validar (servicio)
    ├── test_desvios_vista.py         # NUEVO: detalle, validación, dashboard, lista, permisos, informe
    ├── test_desvios_concurrencia.py  # NUEVO: validaciones simultáneas / corrección vs validación
    ├── test_comparacion.py           # + anteriores
    └── test_demo.py                  # + desvíos de la demo
informes/
├── views.py                          # dashboard: pendientes
├── templates/informes/dashboard.html # + sección «Desvíos sin revisar»
└── tests/test_dashboard.py           # + sección
static/css/aqualab.css                # recompilado si hay clases nuevas
CLAUDE.md                             # sección «Desvíos (US 8.2)»
```

**Structure Decision**: aplicación Django existente; la lógica vive en `estudios` (dueño de
`Resultado`, `Validacion` y de la comparación histórica). `informes` solo consume
`desvios.pendientes()` para el dashboard, respetando la dirección `informes → estudios`.

## Mapa de tests

| Requisito / escenario | Test |
|---|---|
| FR-002, US1 1–2, SC-001 | `test_desvios.py::test_es_desvio_bordes` (110 → 143 / 77 no; 143,5 / 76,9 sí) |
| FR-002, US1 4 | `::test_promedio_de_los_ultimos_n` (50, 60, 100, 110, 120 → 110) |
| FR-004, US1 3 | `::test_historial_insuficiente` |
| FR-014 | `::test_promedio_cero` |
| FR-013 | `::test_presencia` (3 Ausente + Presente sí, promedio 0; mixto no; textos sin 0/1) |
| Edge «historial» | `::test_usa_historial_de_la_comparacion` (cargado, anulado, otro origen, muestra posterior, misma muestra fuera), `::test_estudio_de_muestra_antigua` |
| FR-001, US1 1, 5 | `::test_evaluar_estudio` (CL- 160 → `Deteccion`; 143 → `None`; 2 previos → insuficiente; sin resultado → ausente), `::test_dependiente` (DIV) |
| FR-001, US1 6, SC-003 | `::test_correccion_se_refleja` (160 → 115 sin desvío → 200 con desvío; borrar → sin entrada) |
| FR-011 | `::test_calcular_no_escribe` (`django_assert_num_queries` sin INSERT/UPDATE; conteos iguales) |
| FR-006, US2 7 | `::test_pendientes` (solo Cargadas con desvío, orden por `fecha_calculo`; validar o corregir dentro del umbral lo saca) |
| FR-003, US5 | `::test_regla_configurable`, `::test_regla_invalida`, `::test_regla_en_un_solo_lugar` |
| FR-009, US3 3–4, 6–7, SC-004 | `test_desvios_validacion.py::test_constancia_al_validar`, `::test_sin_desvio_sin_constancia`, `::test_no_elegida_no_guarda`, `::test_omitida_no_guarda`, `::test_validacion_fallida_no_guarda`, `::test_constancia_inalterable`, `::test_correccion_posterior` |
| Edge «aparece mientras se valida» | `::test_evalua_al_confirmar` |
| FR-011, US4 1–2 | `::test_validar_con_desvio_sin_observacion` |
| R6 | `::test_restriccion_desvio_completo` |
| FR-009, Edge «concurrencia» | `test_desvios_concurrencia.py::test_dos_validaciones_simultaneas`, `::test_correccion_y_validacion_simultaneas` |
| FR-005, US1 7–8 | `test_desvios_vista.py::test_marca_en_detalle`, `::test_revisado_en_detalle` |
| FR-006, US2 1–6 | `::test_dashboard_contador_y_diez`, `::test_dashboard_sin_desvios`, `::test_dashboard_no_depende_del_periodo`, `::test_lista_completa_paginada`, `::test_enlaces`; `informes/tests/test_dashboard.py::test_seccion_desvios_sin_revisar` |
| FR-007, US3 1 | `::test_validacion_destaca_desvios`, `::test_historial_insuficiente_en_validacion` |
| FR-008, US3 2, 5 | `::test_confirmacion_cuenta_desvios_elegidos`, `::test_observacion_larga_no_avanza`, `::test_editar_conserva_observacion`, `::test_confirmar_avisa_revisados` |
| FR-010, US3 8 | `::test_permisos` (lista sin `ver_dashboard` 403; «Validar» oculto sin permiso; no existe URL de revisión) |
| FR-012, US4 3 | `::test_no_aparece_en_informe_pdf_ni_correo` |
| SC-007 | `::test_consultas_dashboard_y_lista` (por estudio, no por prueba), `test_desvios.py::test_consultas_evaluar_estudio` |
| FR-015, SC-002 | `test_demo.py::test_desvios_de_la_demo` |

## Complexity Tracking

Sin violaciones de la constitution.
