# Implementation Plan: Borrar mediciones

**Branch**: `018-borrar-mediciones` | **Date**: 2026-11-01 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/018-borrar-mediciones/spec.md` (US 6.5, SCRUM-72)

## Summary

El borrado se suma a la corrección de mediciones de US 6.3: una casilla «Borrar» por fila, el
resumen con «valor → se borra» y la misma confirmación. En el servicio `corregir_mediciones`, un
valor nuevo `None` significa borrar: con la misma regla del valor original (y «ya no tenía
medición» si ya no existe) se borra la `Medicion` y se llama a `recalcular_resultados` con las
corregidas y las borradas, que por la regla de US 6.2 deja sin resultado y en Pendiente a la
borrada y a sus calculadas dependientes. Al final, un estudio sin pruebas Cargadas ni Completadas
vuelve a «Pendiente de análisis». Sin cambios de esquema.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: Django 5.2 LTS; componentes de `templates/ui/`. Sin dependencias nuevas
ni JavaScript.

**Storage**: PostgreSQL 16 en Docker. **Sin migraciones**: se borran filas de `Medicion` y
`Resultado` y cambian estados.

**Testing**: pytest 9.1.1 + pytest-django 4.14.0; fixtures y helpers de US 6.2/6.3
(`estudio_de`, `catalogo`, `cargar`, `asignacion_de`, `envio` de `test_corregir_mediciones.py`);
concurrencia con `transaction=True` e hilos; ruff 0.17.1.

**Target Platform**: Contenedor Linux (`web`) con Docker Compose; navegador de escritorio.

**Project Type**: Aplicación web Django monolítica con templates en el servidor (sin SPA).

**Performance Goals**: Borrar una medición en menos de 1 minuto con una sola confirmación (SC-001).

**Constraints**: Todo el envío en una transacción (FR-011); sin borrados con informe emitido
(FR-008); concurrencia optimista con el valor original (FR-009); confirmación antes de borrar
(Interfaz); depende de la rama `017-modificar-mediciones` (PR #30).

**Scale/Scope**: cambios en `CorregirMedicionesForm`, `corregir_mediciones` y
`ResultadoCorreccion`, la vista `corregir_mediciones` y sus dos templates; nota en `CLAUDE.md`;
tests en `estudios/tests/`.

Decisiones en [research.md](./research.md) (R1–R5). No hay `NEEDS CLARIFICATION` pendientes.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Cumplimiento | Estado |
|---|---|---|
| **I. Spec primero (SDD)** | Spec de US 6.5 (SCRUM-72), historia propia separada de US 6.3 para respetar «1 US = 1 spec». PR: «US 6.5 – Borrar mediciones». El código espera la aprobación de la spec. | ✅ |
| **II. Simplicidad y Django idiomático** | Reutiliza pantalla, servicio, regla de concurrencia y recálculo de US 6.2/6.3; sin modelos, migraciones, JavaScript ni dependencias nuevas. | ✅ |
| **III. Tests obligatorios** | Cada escenario y FR con test (ver [Mapa de tests](#mapa-de-tests)). | ✅ |
| **IV. Integridad de datos** | Solo se borra la medición (sin historial asociado) y los resultados que dependen de ella; nada con informe emitido; todo el envío es atómico. «No se borran registros con historial» no aplica: la medición no tiene historial (US 6.3). La pérdida de validación es la excepción ya justificada en US 6.2. | ⚠️ Excepción heredada de US 6.2 |
| **V. Seguridad** | Solo por POST con CSRF; las asignaciones se buscan dentro del estudio de la URL; sesión obligatoria. | ✅ |
| **VI. Idioma y consistencia** | Interfaz y mensajes en español; `borrar_<pk>`, `borradas`. ruff. | ✅ |
| **Interfaz (UI)** | La acción que elimina datos pide confirmación (resumen «se borra»); avisos con `messages`; componentes existentes. | ✅ |

**Post-diseño (Phase 1)**: cumple todos los principios; la única excepción es la de US 6.2.

## Diseño

### Flujo

```text
corregir_mediciones (estudio bloqueado)
  └─ informe? → por fila: sin medición → «ya no tenía medición»
                          vigente ≠ original → «cambió mientras se editaba»
                          nuevo None → borrar Medicion
                          vigente == nuevo → «ya tenía ese valor»
                          si no → corregir
     → recalcular_resultados(corregidas + borradas)   # US 6.2: descartar → Pendiente
     → sin Cargadas ni Completadas → Pendiente de análisis
       | Finalizado con alguna sin validar → En proceso
```

Mensajes en [contracts/borrar-mediciones-ui.md](./contracts/borrar-mediciones-ui.md); transiciones
en [data-model.md](./data-model.md).

### Mapa de tests

| Escenario / requisito | Test | Archivo |
|---|---|---|
| US1 Esc. 1, FR-001/002 — casilla «Borrar» en cada fila; cualquier empleado puede borrar | `test_formulario_ofrece_borrar`, `test_otro_empleado_puede_borrar` | `test_corregir_mediciones.py` |
| US1 Esc. 2, FR-004 — resumen «se borra» con confirmación; cancelar sin cambios | `test_revisar_muestra_borrado` | `test_corregir_mediciones.py` |
| US1 Esc. 3–4, FR-005 — borrar: medición y resultado fuera, prueba Pendiente y ofrecida en la carga | `test_borrar_medicion`, `test_confirmar_borra_y_vuelve_a_ofrecerse` | `test_servicio_correccion.py`, `test_corregir_mediciones.py` |
| US1 Esc. 5, FR-003 — prevalece el borrado (vacío o inválido) | `test_borrado_prevalece_sobre_el_valor` (parametrizado: vacío, `abc`, `9`) | `test_corregir_mediciones.py` |
| US1 Esc. 6 — solo borrados cuenta como cambio | `test_solo_borrados_no_es_sin_cambios` | `test_corregir_mediciones.py` |
| US2 Esc. 1, FR-006 — dependientes sin resultado y Pendiente; borrar y corregir referencias de la misma calculada | `test_borrar_deja_dependientes_pendientes`, `test_borrar_y_corregir_referencias_de_la_misma_calculada` | `test_servicio_correccion.py` |
| US2 Esc. 2 — validadas: aviso y vuelven a Pendiente | `test_borrar_validada`, `test_revisar_avisa_validacion_por_borrado` | `test_servicio_correccion.py`, `test_corregir_mediciones.py` |
| US2 Esc. 3, FR-007 — sin mediciones → Pendiente de análisis; vuelve a ofrecer agregar y quitar | `test_borrar_todo_vuelve_a_pendiente_de_analisis`, `test_detalle_tras_borrar_todo` | `test_servicio_correccion.py`, `test_corregir_mediciones.py` |
| US2 Esc. 4 — Finalizado con mediciones restantes → En proceso | `test_borrar_en_finalizado_reabre` | `test_servicio_correccion.py` |
| US3 Esc. 1, FR-008 — informe emitido rechaza | `test_borrar_con_informe_emitido_rechaza` | `test_servicio_correccion.py` |
| US3 Esc. 2–3, FR-009 — cambio ajeno y ya borrada; reenvío | `test_borrar_omite_si_cambio`, `test_borrar_omite_si_ya_no_existe`, `test_reenvio_de_borrado` | `test_servicio_correccion.py`, `test_corregir_mediciones.py` |
| FR-010 — mensajes de borradas y corregidas juntas | `test_mensajes_borrado_y_correccion` | `test_corregir_mediciones.py` |
| FR-011 — una falla no deja nada a medias | `test_falla_en_recalculo_no_borra` | `test_servicio_correccion.py` |
| FR-012 — no cambia otras mediciones ni otros estudios | `test_borrado_no_modifica_otros_datos` | `test_servicio_correccion.py` |
| Concurrencia — corregir y borrar la misma medición a la vez | `test_borrado_y_correccion_concurrentes` | `test_concurrencia_mediciones.py` |

## Project Structure

### Documentation (this feature)

```text
specs/018-borrar-mediciones/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── borrar-mediciones-ui.md
├── checklists/
│   └── requirements.md
└── tasks.md              # /speckit-tasks
```

### Source Code (repository root)

```text
CLAUDE.md                                        # sección de US 6.3: borrado y vuelta a Pendiente de análisis
estudios/
├── forms.py                                     # CorregirMedicionesForm: borrar_<pk>, validación condicional
├── servicios.py                                 # corregir_mediciones: nuevo None = borrar; borradas; Pendiente de análisis
├── views.py                                     # corregir_mediciones: asignaciones al confirmar; mensajes
├── templates/estudios/
│   ├── corregir_mediciones.html                 # + columna Borrar
│   └── corregir_mediciones_confirmar.html       # «se borra», aviso de cambios, oculto borrar_<pk>
└── tests/
    ├── test_servicio_correccion.py              # + borrado
    ├── test_corregir_mediciones.py              # + borrado
    └── test_concurrencia_mediciones.py          # + borrado concurrente
```

**Structure Decision**: extiende los archivos de US 6.3; sin archivos de producción nuevos.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Principio IV: un resultado validado se pierde si se borra la medición de la que depende. | Es la excepción justificada en `specs/016-calcular-resultado/plan.md`; borrar es el caso extremo de corregir. | Ver el plan de US 6.2; además el resumen avisa qué pruebas perderán la validación antes de confirmar. |
