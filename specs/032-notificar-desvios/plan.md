# Implementation Plan: Notificar desvíos relevantes

**Branch**: `032-notificar-desvios` | **Date**: 2026-11-09 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/032-notificar-desvios/spec.md` (SCRUM-61, US 8.2)

## Summary

Cada vez que `calculo.recalcular` produce, cambia o descarta un resultado (carga, corrección,
borrado y `calcular_resultados`), un módulo nuevo `estudios/desvios.py` reevalúa solo las pruebas
cuyo valor cambió: obtiene el historial con `comparacion.comparar` (US 8.1, con un campo nuevo
`HistorialPrueba.anteriores`), promedia los últimos N validados con `comparacion.variacion` y decide
con una comparación `Decimal` exacta contra el umbral de `settings.AQUALAB_DESVIOS` (30 %, N = 3).
El resultado se guarda en un modelo nuevo `estudios.Desvio` (foto de la detección, vigente/cerrado
con motivo, revisión enlazada a la `Validacion` + observación; nunca se borra), en la misma
transacción y bajo el bloqueo del estudio. Se muestra en el detalle del estudio, en una sección
«Desvíos sin revisar» del Dashboard y en una lista completa `estudios:desvios`. **Validar es
revisar** (ajuste del usuario): la pantalla de validación destaca las pruebas con desvío (valor,
promedio, enlace a la 8.1 y un campo «Observación»), la confirmación cuenta cuántas elegidas tienen
desvío y `servicios.validar_resultados` marca el desvío como revisado en la misma transacción de la
validación. No hay pantalla aparte para revisar. No bloquea nada ni aparece en el informe. Un
comando `evaluar_desvios` cubre los datos previos y la demo valida con observación el desvío de
Pozo 2 del mes anterior.

## Technical Context

**Language/Version**: Python 3.12.

**Primary Dependencies**: Django 5.2 LTS (ORM, `select_for_update`, `UniqueConstraint`
condicional, `JSONField`, `Paginator`, formularios, mensajes), Tailwind CSS 4 y `templates/ui/`.
Sin dependencias nuevas ni JavaScript nuevo.

**Storage**: PostgreSQL 16. Migración `estudios.0009_desvio` (tabla nueva; no toca datos).

**Testing**: pytest + pytest-django con las fixtures de `estudios/tests/conftest.py` (`catalogo`,
`empleado`, `bioquimico`, `cliente_bioquimico`, fábrica `estudio_en_origen` de la 8.1), helpers
`estudios.tests.utiles.cargar`/`validar` (servicios reales), `settings` para la regla,
`django_assert_max_num_queries`, tests de concurrencia con `transaction=True` como los de
validación, la demo de SCRUM-78; ruff.

**Target Platform**: Contenedor `web` (Docker Compose) y Render; navegador de escritorio.

**Project Type**: Aplicación web Django monolítica con templates en el servidor.

**Performance Goals**: SC-007 — la reevaluación agrega una cantidad fija de consultas por
operación (una llamada a `comparar` + lectura de vigentes + escrituras por desvío); el dashboard y
la lista, cantidad fija con `select_related`. Tests con `django_assert_max_num_queries`.

**Constraints**: `Decimal` exacto, sin `float` (FR-002); transacción y bloqueo del llamador
(FR-001); nunca se borran desvíos (SC-004); no bloquea validar ni emitir (FR-013); nada en
informe/PDF/correo (FR-015); color nunca como única señal; CSS compilado al día (CI).

**Scale/Scope**: `estudios/desvios.py`, modelo + migración, cambios chicos en `comparacion.py`,
`calculo.py`, `servicios.validar_resultados` (observaciones + revisión) y `ValidarResultadosForm`
(campo `observacion_<pk>`), 1 vista + 1 URL (`estudios:desvios`), parciales y cambios en
`detalle.html`, `validar_resultados*.html` e `informes/dashboard.html`; comando
`evaluar_desvios`; demo; tests; CLAUDE.md.

Decisiones en [research.md](./research.md) (R1–R13). No hay `NEEDS CLARIFICATION` pendientes.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Cumplimiento | Estado |
|---|---|---|
| **I. Spec primero (SDD)** | Spec de US 8.2 (SCRUM-61) en Draft; el código espera su aprobación. | ✅ |
| **II. Simplicidad y Django idiomático** | Un modelo, un módulo de reglas, vistas de función y formularios Django; reutiliza `comparar`/`variacion` (sin segunda definición del historial), los parciales de UI, la paginación y el patrón de confirmación; configuración en `settings` como `AQUALAB_LABORATORIO`; sin señales (R1) ni dependencias. | ✅ |
| **III. Tests obligatorios** | Cada escenario y FR mapeado a tests ([Mapa de tests](#mapa-de-tests)); la regla con casos de borde explícitos (30 % exacto, 30,0x %, promedio 0, A/P, últimos 3 de 5). | ✅ |
| **IV. Integridad de datos** | Detección en la transacción del cálculo y revisión en la de la validación, ambas bajo el bloqueo del estudio; un vigente por prueba (único parcial); cierre con motivo y revisión inalterables (enlazada a la `Validacion`, que nunca se borra); no altera resultados ni estados más allá de la validación pedida; foto de la regla y de los previos usados. | ✅ |
| **V. Seguridad** | `LoginRequiredMiddleware`; revisar solo ocurre dentro de `validar_resultados`, que ya revalida `estudios.validar_resultados` en vista y servicio; `informes.ver_dashboard` para la lista; `require_GET` en la lista; CSRF en la validación; sin URLs de redirección libres. | ✅ |
| **VI. Idioma y consistencia** | `desvios.py`, `Desvio`, `MotivoCierre`, `reevaluar`, `revisar_al_validar`, `pendientes`; interfaz en español; ruff. | ✅ |
| **Interfaz (UI)** | Parciales reutilizables (`estudios/desvio.html`, `estudios/desvios_tabla.html`) con `ui/estado.html`, `ui/ayuda.html`, `ui/campo.html` (`help_text` en la observación), `ui/paginacion`; la revisión se guarda con la confirmación existente de la validación, que la anuncia; mensajes de Django; ícono + texto. | ✅ |

**Post-diseño (Phase 1)**: cumple todos los principios, sin excepciones.

## Diseño

```text
cargar_mediciones ─┐
corregir/borrar ───┼─► calculo.recalcular(estudio bloqueado, asignaciones)
calcular_resultados┘      antes = valores previos
                          … calcula / descarta en orden de dependencia …
                          cambiadas = nuevos o distintos; sin_resultado = descartados que tenían
                          └─► desvios.reevaluar(estudio, cambiadas, sin_resultado)        (R1, R2)
                                 comparar(origen, estudio=estudio, codigos=cambiadas)      (R3)
                                 por prueba: detectar(historial, regla())                  (R4, R5)
                                   anteriores[-N:] → variacion() → promedio, textos
                                   es_desvio(valor, promedio, umbral)  (Decimal exacto)
                                 aplicar tabla de transiciones                              (R7)

Desvio (vigente, sin revisar) ──► detalle (marca + historial)                             (R10)
                              ──► desvios.pendientes() ─► dashboard (N + 10) / estudios:desvios
                              ──► validación: fila destacada + observacion_<pk>             (R10)
                                    confirmación: «N de los M elegidos tienen desvío»
                                    servicios.validar_resultados(…, observaciones)
                                      Validacion → desvios.revisar_al_validar()             (R9)
```

### `estudios/desvios.py` (interfaz)

Ver [contracts/desvios-ui.md](./contracts/desvios-ui.md#interfaz-interna-estudiosdesviospy):
`regla`, `es_desvio`, `detectar`, `historial_suficiente`, `reevaluar`, `pendientes`, `del_estudio`,
`enlace_comparacion`, `revisar_al_validar`. Las funciones de regla son puras (se prueban sin
base); `reevaluar` es la única que crea y cierra desvíos y `revisar_al_validar` la única que los
revisa.

### Archivos

```text
config/settings.py                    # + AQUALAB_DESVIOS (R8)
estudios/
├── desvios.py                        # NUEVO: regla, detección, reevaluación, consultas
├── models.py                         # + Desvio, MotivoCierre
├── migrations/0009_desvio.py         # NUEVO
├── comparacion.py                    # HistorialPrueba.anteriores (R3)
├── calculo.py                        # recalcular → desvios.reevaluar (R1, R2)
├── servicios.py                      # validar_resultados: + observaciones, revisa desvíos (R9)
├── forms.py                          # ValidarResultadosForm: + observacion_<pk>, observaciones()
├── views.py                          # detalle y validar_resultados: desvíos; + desvios (lista)
├── urls.py                           # + desvios/
├── demo.py                           # observación al validar Pozo 2 mes 1 (R12)
├── management/commands/evaluar_desvios.py   # NUEVO (R12)
├── templates/estudios/
│   ├── desvio.html                   # NUEVO: marca + acciones (parcial)
│   ├── desvios_tabla.html            # NUEVO: tabla de pendientes (dashboard y lista)
│   ├── desvios_estudio.html          # NUEVO: sección «Desvíos» del detalle (historial)
│   ├── desvios.html                  # NUEVO: lista completa paginada
│   ├── detalle.html                  # + marca y sección
│   ├── validar_resultados.html       # + resumen, filas destacadas, observación, «Historial insuficiente»
│   └── validar_resultados_confirmar.html  # + «N de los M elegidos tienen desvío» + observaciones
└── tests/
    ├── test_desvios.py               # NUEVO: regla pura, detección, transiciones, comando
    ├── test_desvios_vista.py         # NUEVO: pantallas, validación con desvíos, permisos, dashboard
    ├── test_desvios_concurrencia.py  # NUEVO: validaciones simultáneas / corrección vs validación
    └── test_demo.py                  # + desvíos de la demo
informes/
├── views.py                          # dashboard: pendientes
└── templates/informes/dashboard.html
static/css/aqualab.css                # recompilado si hay clases nuevas
CLAUDE.md                             # sección «Desvíos (US 8.2)»
```

**Structure Decision**: aplicación Django existente; `Desvio` vive en `estudios` (dueño de
`PruebaEstudio`, `Resultado`, `Validacion` y de la comparación histórica). `informes` solo consume
`desvios.pendientes()` para el dashboard, respetando la dirección de dependencias
`informes → estudios`.

## Mapa de tests

| Requisito / escenario | Test |
|---|---|
| FR-002, US1 1–2, SC-001 | `test_desvios.py::test_es_desvio_bordes` (110 → 143 / 77 no; 143,5 / 76,9 sí; arriba y abajo) |
| FR-002, US1 4 | `::test_promedio_de_los_ultimos_n` (50, 60, 100, 110, 120 → 110) |
| FR-004, US1 3 | `::test_historial_insuficiente` (2 previos → sin desvío; `historial_suficiente`) |
| FR-017 | `::test_promedio_cero` (0,0,0 y 5 → desvío sin porcentaje; 0 → no) |
| FR-016, R5 | `::test_presencia` (3 Ausente + Presente sí; mixto no; textos sin 0/1) |
| Edge «historial» (8.1) | `::test_usa_historial_de_la_comparacion` (anulada, otra unidad, misma muestra y muestra posterior fuera) |
| FR-001, US1 1, 5 | `::test_detecta_al_cargar` (servicio real), `::test_detecta_en_dependiente` (Cloruro calculada) |
| FR-005, FR-019 | `::test_foto_de_la_deteccion` (previos, umbral, cantidad, porcentaje) |
| FR-006, US2 1–5, SC-003 | `::test_correccion_resuelve`, `::test_correccion_reemplaza_y_pierde_revision`, `::test_correccion_crea`, `::test_dependiente_sin_cambio_conserva`, `::test_borrado_sin_resultado` |
| FR-001, US2 6 | `::test_operacion_rechazada_no_toca_desvios` (informe emitido; error en recálculo → rollback) |
| Edge «historial que cambia» | `::test_validar_otro_no_reevalua` |
| FR-014, US5 1–2 | `::test_validar_con_desvio_sin_observacion` (valida, mismo valor, revisado con observación vacía, estados intactos) |
| FR-018 | `::test_comando_evaluar_desvios_idempotente` |
| FR-003, US6 | `::test_regla_configurable` (`settings`), `::test_regla_invalida` |
| R6 | `::test_un_vigente_por_asignacion` (IntegrityError), `::test_restricciones_cierre_y_revision` |
| FR-007, US1 6 | `test_desvios_vista.py::test_marca_en_detalle` (texto + ícono, comparación solo con permiso) |
| FR-008, US4 7 | `::test_historial_de_desvios_en_detalle` (motivos de cierre, revisión con quién/cuándo/observación) |
| FR-009, US3 | `::test_dashboard_contador_y_diez`, `::test_dashboard_sin_desvios`, `::test_dashboard_no_depende_del_periodo`, `::test_lista_completa_paginada`, `::test_enlaces_estudio_muestra_comparacion_y_validar` |
| FR-010, US4 1, US1 3 | `::test_validacion_destaca_desvios` (resumen, campo solo en filas con desvío), `::test_historial_insuficiente_en_validacion` |
| FR-011, US4 2, 6 | `::test_confirmacion_cuenta_desvios_elegidos`, `::test_observacion_larga_no_avanza`, `::test_editar_conserva_observacion` |
| FR-012, US4 3–5 | `test_desvios.py::test_validar_revisa_con_observacion` (validación y revisión con el mismo usuario y fecha), `::test_no_elegida_sigue_sin_revisar`, `::test_omitida_no_revisa` (cambió / ya validada), `::test_validacion_fallida_no_revisa` (rollback), `::test_recalculo_mismo_valor_conserva_revision` |
| FR-012, Edge «concurrencia» | `test_desvios_concurrencia.py::test_dos_validaciones_simultaneas` (una revisión, la segunda observación no se guarda), `::test_correccion_y_validacion_simultaneas` |
| FR-013, US4 8 | `test_desvios_vista.py::test_permisos` (lista sin `ver_dashboard` 403; «Validar» oculto sin permiso; sin URL de revisión) |
| US4 7 | `::test_sin_admin_ni_edicion` |
| FR-015, US5 3 | `::test_no_aparece_en_informe_pdf_ni_correo` |
| SC-007 | `test_desvios_vista.py::test_consultas_fijas_dashboard_y_lista`, `test_desvios.py::test_consultas_fijas_reevaluar` |
| FR-020, SC-002 | `test_demo.py::test_desvios_de_la_demo` (Pozo 2 mes 0 pendiente con 430 / 219,67 / +95,8 %; mes 1 revisado al validar con observación; cantidad de pendientes) |

## Complexity Tracking

Sin violaciones de la constitution.
