# Implementation Plan: Cálculo automático del resultado

**Branch**: `016-calcular-resultado` | **Date**: 2026-10-31 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/016-calcular-resultado/spec.md` (US 6.2, SCRUM-54)

## Summary

Las fórmulas del catálogo (SCRUM-64) dejan de ser texto sin evaluar. Un evaluador propio
(`pruebas/formulas.py`) calcula con `Decimal` la gramática del catálogo (`x`, `{CODIGO}`, `+ - * /`,
paréntesis y `sqrt`) y rechaza cualquier otra cosa, también al guardar pruebas en el admin o al
importar. Un modelo nuevo `Resultado` (uno a uno con `PruebaEstudio`) guarda el valor completo con
la unidad y la fórmula usadas. El motor `estudios/calculo.py` recalcula, con el estudio bloqueado,
solo las pruebas afectadas por un cambio y en orden de dependencia: lo llama `cargar_mediciones`
(US 6.1) al guardar, y lo expone el servicio `recalcular_resultados` para US 6.3, que rechaza
cambios con informe emitido. El detalle del estudio muestra el resultado con hasta 4 decimales o
el motivo por el que falta.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: Django 5.2 LTS; módulo `decimal` de la biblioteca estándar. Sin
dependencias nuevas ni JavaScript.

**Storage**: PostgreSQL 16 en Docker. Tabla nueva `estudios_resultado` (migración
`estudios/migrations/0005_resultado.py`).

**Testing**: pytest 9.1.1 + pytest-django 4.14.0; casos conocidos con valores esperados
explícitos (principio III); concurrencia con `transaction=True` e hilos; ruff 0.17.1.

**Target Platform**: Contenedor Linux (`web`) con Docker Compose; navegador de escritorio.

**Project Type**: Aplicación web Django monolítica con templates en el servidor (sin SPA).

**Performance Goals**: El resultado aparece en el detalle apenas se guarda la medición (SC-002):
el cálculo corre en la misma transacción, sobre ≤ 90 pruebas por estudio.

**Constraints**: Cálculo exacto con `Decimal`, nunca `float` (principio IV); solo se recalculan
las pruebas afectadas (FR-008); sin cambios con informe emitido (FR-009); un error de cálculo no
impide guardar la medición (FR-007); resultados validados que se recalculan pierden la validación
(excepción justificada, ver *Complexity Tracking*).

**Scale/Scope**: 1 módulo de fórmulas, 1 modelo + migración, 1 propiedad de `Estudio`, 1 módulo de
cálculo, 1 servicio + 1 excepción, cambios en `cargar_mediciones` (servicio y vista), en `detalle`
(vista y template) y en `Prueba.clean()`, 1 comando de gestión, nota en `CLAUDE.md` y tests en
`pruebas/tests/` y `estudios/tests/`.

Decisiones en [research.md](./research.md) (R1–R8). No hay `NEEDS CLARIFICATION` pendientes.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Cumplimiento | Estado |
|---|---|---|
| **I. Spec primero (SDD)** | Spec de US 6.2 (SCRUM-54) en `specs/016-calcular-resultado/spec.md`, clarificada el 2026-10-31; una US por spec y por rama. PR: «US 6.2 – Cálculo automático del resultado». El código espera la aprobación de la spec. | ✅ |
| **II. Simplicidad y Django idiomático** | Sin dependencias nuevas: el evaluador es un analizador chico con la biblioteca estándar (R1), porque `eval`/`ast` usan `float` y una librería requiere acuerdo del equipo. Llamadas explícitas, sin señales (R3). Sin pantallas nuevas. | ✅ |
| **III. Tests obligatorios** | Cada escenario y FR con test (ver [Mapa de tests](#mapa-de-tests)); al menos un caso conocido por fórmula distinta del catálogo, con valor esperado explícito (SC-001), más los casos de error. | ✅ |
| **IV. Integridad de datos** | `Decimal` en evaluación y almacenamiento; resultado guardado con su unidad y la fórmula usada; `PROTECT`; el informe emitido bloquea todo cambio. **Excepción**: un resultado validado se recalcula y pierde la validación si se corrige una medición antes del informe (Clarifications). Justificada en *Complexity Tracking*. | ⚠️ Excepción justificada |
| **V. Seguridad** | Sin rutas nuevas. Las fórmulas nunca se ejecutan como código: solo la gramática del catálogo (R1). | ✅ |
| **VI. Idioma y consistencia** | Términos del glosario: `Resultado`, `recalcular`, `evaluar_formula`, `admite_correcciones`. Mensajes en español. ruff. | ✅ |
| **Interfaz (UI)** | Solo una columna nueva en el detalle con los componentes existentes; avisos con `messages`. | ✅ |

**Post-diseño (Phase 1)**: cumple todos los principios; la única excepción está justificada abajo.

## Diseño

### Flujo

```text
cargar_mediciones (US 6.1, estudio bloqueado)
  └─ crea Medicion(es) → calculo.recalcular(estudio, guardadas) → ResultadoCarga.sin_calcular
                                                                    └─ vista: advertencias (FR-013)
recalcular_resultados(estudio_pk, asignacion_pks, usuario)   # para US 6.3
  └─ bloquea estudio → admite_correcciones? → calculo.recalcular(...)
detalle → resultado.valor_mostrado | calculo.motivo_sin_resultado(...)
```

Mensajes, motivos y casos conocidos en
[contracts/calculo-resultado.md](./contracts/calculo-resultado.md); modelo y transiciones en
[data-model.md](./data-model.md).

### Fórmulas (`pruebas/formulas.py`)

```text
FormulaInvalida(ValidationError)
CalculoImposible(Exception)            # .motivo
validar_formula(texto)
evaluar_formula(texto, x, resultados) -> Decimal
```

### Cálculo (`estudios/calculo.py`)

```text
recalcular(estudio, asignaciones) -> list[(Prueba, motivo)]   # estudio ya bloqueado
motivo_sin_resultado(asignacion, por_codigo) -> str | None
```

### Mapa de tests

| Escenario / requisito | Test | Archivo |
|---|---|---|
| FR-002, SC-001 — casos conocidos por fórmula, operadores, signo, paréntesis y `sqrt` | `test_evaluar_formula_casos_conocidos` (parametrizado con la tabla del contrato y una fórmula por caso del catálogo) | `pruebas/tests/test_formulas.py` |
| FR-002 — errores de evaluación | `test_evaluar_formula_division_por_cero`, `test_evaluar_formula_raiz_negativa`, `test_evaluar_formula_sin_x` | `pruebas/tests/test_formulas.py` |
| FR-002 — se rechaza lo que no es la gramática | `test_validar_formula_rechaza` (parametrizado: `__import__`, `x**2`, `1e3`, `abs(x)`, `{}`, paréntesis sin cerrar…) | `pruebas/tests/test_formulas.py` |
| R1 — las 25 fórmulas del catálogo son válidas; el admin y la importación rechazan una inválida | `test_formulas_del_catalogo_validas`, `test_prueba_clean_rechaza_formula_invalida` | `pruebas/tests/test_formulas.py` |
| US1 Esc. 1–2, FR-001/004 — Directo y Fórmula al guardar la medición, con unidad y fórmula | `test_carga_calcula_resultado_directo_y_formula` | `estudios/tests/test_calculo.py` |
| US1 Esc. 3, FR-005 — detalle con resultado, unidad y 4 decimales | `test_detalle_muestra_resultado`, `test_valor_mostrado` (parametrizado: 23.5, 0.0041, 1234.5, 0, -0.00001) | `estudios/tests/test_cargar_mediciones.py`, `estudios/tests/test_modelos.py` |
| US2 Esc. 1, FR-003 — calculada con referencias pasa a Cargada | `test_calculada_se_calcula_al_completar_referencias` | `estudios/tests/test_calculo.py` |
| US2 Esc. 2–4, FR-006 — motivos sin resultado | `test_motivo_sin_resultado` (parametrizado: falta medición, faltan referencias, referencia fuera del estudio, división por cero) | `estudios/tests/test_calculo.py` |
| US2 Esc. 3 — cadena en orden | `test_cadena_de_calculadas` (NA → NA-MEQ → CATIONES con K-MEQ, CA-MEQ y MG-MEQ) | `estudios/tests/test_calculo.py` |
| US2 Esc. 5, FR-007, FR-013 — fórmula que falla: medición guardada, advertencia en el mensaje | `test_falla_de_calculo_no_impide_guardar`, `test_mensaje_carga_advierte_falla_de_calculo` | `estudios/tests/test_calculo.py`, `estudios/tests/test_cargar_mediciones.py` |
| US3 Esc. 1–2, FR-008 — recálculo de la prueba y sus dependientes; las demás no cambian | `test_recalcular_actualiza_dependientes_y_no_otras` | `estudios/tests/test_calculo.py` |
| US3 Esc. 3, FR-009 — validada pierde la validación | `test_recalculo_quita_validacion` | `estudios/tests/test_calculo.py` |
| US3 Esc. 4, FR-009 — informe emitido rechaza | `test_recalcular_con_informe_emitido_rechaza` | `estudios/tests/test_calculo.py` |
| FR-010 — cambio de catálogo no recalcula; resultado conserva fórmula y unidad | `test_resultado_conserva_formula_y_unidad` | `estudios/tests/test_calculo.py` |
| FR-011 — comando para mediciones previas, idempotente | `test_comando_calcular_resultados` | `estudios/tests/test_calculo.py` |
| FR-012 — no cambia mediciones, muestra, snapshots, catálogo ni otros estudios | `test_calculo_no_modifica_otros_datos` | `estudios/tests/test_calculo.py` |
| Edge — resultado de calculada que deja de poder calcularse vuelve a Pendiente | `test_calculada_sin_referencias_vuelve_a_pendiente` | `estudios/tests/test_calculo.py` |
| Edge — referencias circulares | `test_referencias_circulares` | `estudios/tests/test_calculo.py` |
| R2 — un resultado por asignación; `PROTECT` | `test_un_resultado_por_asignacion`, `test_asignacion_con_resultado_protegida` | `estudios/tests/test_modelos.py` |
| Concurrencia — dos cargas simultáneas de las referencias de una calculada | `test_cargas_concurrentes_calculan_una_vez` (`transaction=True`, hilos) | `estudios/tests/test_concurrencia_mediciones.py` |

## Project Structure

### Documentation (this feature)

```text
specs/016-calcular-resultado/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── calculo-resultado.md
├── checklists/
│   └── requirements.md
└── tasks.md              # /speckit-tasks
```

### Source Code (repository root)

```text
CLAUDE.md                                   # + sección «Cálculo de resultados (US 6.2)»; notas Epic 6 actualizadas
pruebas/
├── formulas.py                             # nuevo: validar_formula, evaluar_formula
├── models.py                               # Prueba.clean() valida la fórmula
└── tests/test_formulas.py                  # nuevo
estudios/
├── models.py                               # + Resultado, Estudio.admite_correcciones
├── migrations/0005_resultado.py            # nueva
├── calculo.py                              # nuevo: recalcular, motivo_sin_resultado
├── servicios.py                            # cargar_mediciones llama a recalcular; + RecalculoError, recalcular_resultados
├── views.py                                # cargar_mediciones (advertencias), detalle (resultado y motivo)
├── templates/estudios/detalle.html         # + columna Resultado
├── management/commands/calcular_resultados.py   # nuevo
└── tests/
    ├── conftest.py                         # + fixtures con pruebas reales del catálogo (PH, CL-, CA, DUREZA-T, MG, NA…)
    ├── test_calculo.py                     # nuevo
    ├── test_modelos.py                     # + Resultado
    ├── test_cargar_mediciones.py           # + resultado en el detalle y advertencias
    └── test_concurrencia_mediciones.py     # + cálculo concurrente
```

**Structure Decision**: el evaluador va en `pruebas` (es la semántica de las fórmulas del
catálogo, junto a `referencias_formula`); el resultado y el motor en `estudios`, junto a
`Medicion` y `cargar_mediciones`. Sin app nueva.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Principio IV: «un resultado validado no se puede modificar». Un recálculo por una medición corregida antes del informe reemplaza un resultado validado y le quita la validación (vuelve a `Cargada`). | Pedido por el usuario (Clarifications 2026-10-31) y por SCRUM-55 («los nuevos valores deben reemplazar a los anteriores y revalidarse»). Corregir un error de carga es parte del flujo del laboratorio antes de emitir el informe. | **Rechazar la corrección**: deja un error de carga sin poder corregirse aunque el cliente todavía no recibió nada. **Conservar el resultado validado viejo**: muestra un resultado que no corresponde a sus mediciones (contradice SC-003). La excepción no permite editar resultados a mano, nunca conserva una validación sobre datos que cambiaron y termina al emitir el informe, que es lo que el principio protege. |
