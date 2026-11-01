# Implementation Plan: Modificar las mediciones

**Branch**: `017-modificar-mediciones` | **Date**: 2026-11-01 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/017-modificar-mediciones/spec.md` (US 6.3, SCRUM-55)

## Summary

Desde el detalle del estudio, **Corregir mediciones** abre una pantalla con todas las mediciones
cargadas, precargadas con su valor. Se reutiliza el flujo de la carga (US 6.1): revisar (valor
anterior → nuevo y aviso de las pruebas que perderán la validación), editar y confirmar. El
servicio `corregir_mediciones` bloquea el estudio, rechaza si el informe se emitió, omite las
mediciones que otro cambió mientras se editaba (comparando con el valor original), actualiza la
misma fila de `Medicion` con quién y cuándo la corrigió, y llama en la misma transacción a
`recalcular_resultados` (US 6.2). Si el estudio estaba Finalizado y alguna prueba deja de estar
Completada, vuelve a En proceso.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: Django 5.2 LTS (ORM, forms, messages), Tailwind CSS 4 y componentes de
`templates/ui/`. Sin dependencias nuevas ni JavaScript.

**Storage**: PostgreSQL 16 en Docker. Dos columnas nuevas en `estudios_medicion` (migración
`estudios/migrations/0006_medicion_correccion.py`).

**Testing**: pytest 9.1.1 + pytest-django 4.14.0; concurrencia con `transaction=True` e hilos;
fixtures `estudio_de`, `catalogo`, `pruebas_division` y helper `cargar` de US 6.2; ruff 0.17.1.

**Target Platform**: Contenedor Linux (`web`) con Docker Compose; navegador de escritorio.

**Project Type**: Aplicación web Django monolítica con templates en el servidor (sin SPA).

**Performance Goals**: Corregir una medición en menos de 1 minuto con una sola confirmación
(SC-001); el recálculo corre en la misma transacción (≤ 90 pruebas por estudio).

**Constraints**: Mismas reglas de formato que la carga (`leer_valor`); todo o nada (FR-007);
concurrencia optimista por valor original (FR-010); sin cambios con informe emitido (FR-009);
confirmación antes de guardar (Interfaz); depende de la rama `016-calcular-resultado` (PR #29).

**Scale/Scope**: 2 campos + migración, 1 función extraída en `calculo.py`, 1 formulario, 1
servicio + 1 excepción + 1 resultado, 1 vista, 2 templates, 1 URL, cambios en `detalle` (vista y
template), nota en `CLAUDE.md` y tests en `estudios/tests/`.

Decisiones en [research.md](./research.md) (R1–R6). No hay `NEEDS CLARIFICATION` pendientes.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Cumplimiento | Estado |
|---|---|---|
| **I. Spec primero (SDD)** | Spec de US 6.3 (SCRUM-55) clarificada el 2026-11-01; el borrado se separó en US 6.5 (SCRUM-72) para respetar «1 US = 1 spec». PR: «US 6.3 – Modificar las mediciones». El código espera la aprobación de la spec. | ✅ |
| **II. Simplicidad y Django idiomático** | Mismo flujo, formularios y componentes que la carga (US 6.1); sin JavaScript ni dependencias; la concurrencia se resuelve con el valor original, sin campos de versión (R3). | ✅ |
| **III. Tests obligatorios** | Cada escenario y FR con test (ver [Mapa de tests](#mapa-de-tests)); el recálculo ya tiene sus casos conocidos en US 6.2 y aquí se prueba el valor nuevo de punta a punta. | ✅ |
| **IV. Integridad de datos** | `Decimal` y decimales escritos (`leer_valor`); unidad sin cambios; quién y cuándo corrigió; nada cambia con informe emitido. La pérdida de validación de un resultado recalculado es la excepción ya justificada en el plan de US 6.2 (*Complexity Tracking*). | ⚠️ Excepción heredada de US 6.2 |
| **V. Seguridad** | `LoginRequiredMiddleware`; cambios solo por POST con CSRF; las asignaciones se buscan dentro del estudio de la URL; el usuario sale de la sesión. | ✅ |
| **VI. Idioma y consistencia** | `corregir_mediciones`, `CorregirMedicionesForm`, `corregida_por`, `fecha_correccion`. Interfaz en español. ruff. | ✅ |
| **Interfaz (UI)** | Confirmación antes de guardar, errores junto a cada campo, `messages`; componentes existentes, sin CSS nuevo. | ✅ |

**Post-diseño (Phase 1)**: cumple todos los principios; la única excepción es la de US 6.2.

## Diseño

### Flujo

```text
GET  /estudios/<pk>/                         → detalle: «Corregir mediciones» y «Corregida por …»
GET  /estudios/<pk>/mediciones/corregir/     → formulario precargado (302 si hay informe emitido)
POST                       accion=revisar    → formulario con errores | resumen anterior → nuevo
POST                       accion=editar     → formulario con los valores
POST                       accion=confirmar  → corregir_mediciones() → 302 detalle + mensajes
corregir_mediciones (estudio bloqueado)
  └─ informe? → filas bloqueadas → original == vigente? → actualizar → recalcular_resultados()
     → Finalizado con alguna prueba no Completada → En proceso
```

Rutas y mensajes en [contracts/corregir-mediciones-ui.md](./contracts/corregir-mediciones-ui.md);
modelo y transiciones en [data-model.md](./data-model.md).

### Mapa de tests

| Escenario / requisito | Test | Archivo |
|---|---|---|
| FR-001, US3 Esc. 6 — sesión obligatoria; 404; cualquier empleado puede corregir | `test_corregir_requiere_sesion`, `test_corregir_estudio_inexistente_404`, `test_otro_empleado_puede_corregir` | `test_corregir_mediciones.py` |
| US1 Esc. 1, FR-002 — botón en el detalle solo si corresponde | `test_detalle_ofrece_corregir`, `test_detalle_no_ofrece_corregir` (parametrizado: sin mediciones, informe emitido) | `test_corregir_mediciones.py` |
| US1 Esc. 2, FR-003 — formulario precargado con valor tal como se escribió, unidad y quién cargó | `test_formulario_precargado` | `test_corregir_mediciones.py` |
| US1 Esc. 3, FR-005 — resumen solo con cambios; editar y cancelar sin cambios | `test_revisar_muestra_solo_cambios`, `test_editar_conserva_valores` | `test_corregir_mediciones.py` |
| US1 Esc. 4, FR-006/007/011 — confirmar corrige, registra quién y recalcula | `test_confirmar_corrige_y_recalcula`, `test_corregir_mediciones_actualiza_la_misma_fila` | `test_corregir_mediciones.py`, `test_servicio_correccion.py` |
| US1 Esc. 5 — se corrige en un estudio Finalizado | `test_corregir_en_estudio_finalizado` | `test_servicio_correccion.py` |
| US2 Esc. 1–2, FR-004 — formato y nada guardado si hay un inválido | `test_revisar_con_valor_invalido_no_guarda`, `test_confirmar_con_valor_invalido_no_guarda` | `test_corregir_mediciones.py` |
| US2 Esc. 3–4 — campo vacío; sin cambios | `test_campo_vacio_rechazado`, `test_sin_cambios` | `test_corregir_mediciones.py` |
| Edge — `7,2` → `7,20` cuenta como cambio | `test_cambio_de_decimales_es_cambio` | `test_corregir_mediciones.py` |
| US3 Esc. 1 — el resumen avisa quién pierde la validación | `test_revisar_avisa_perdida_de_validacion` | `test_corregir_mediciones.py` |
| US3 Esc. 2–3, FR-008 — validadas vuelven a Cargada; Finalizado → En proceso | `test_correccion_quita_validacion_y_reabre_estudio` | `test_servicio_correccion.py` |
| US3 Esc. 4, FR-009 — informe emitido rechaza (vista y servicio) | `test_informe_emitido_rechaza` (servicio), `test_vista_informe_emitido_rechaza` | `test_servicio_correccion.py`, `test_corregir_mediciones.py` |
| US3 Esc. 5, FR-010 — cambio ajeno omitido; reenvío no cambia nada | `test_omite_si_cambio_mientras_se_editaba`, `test_reenvio_informa_ya_tenia_ese_valor` | `test_servicio_correccion.py`, `test_corregir_mediciones.py` |
| Edge — corrección que hace imposible un cálculo | `test_correccion_a_division_por_cero_advierte` | `test_corregir_mediciones.py` |
| FR-013 — no cambia otras mediciones, la muestra, el catálogo ni otros estudios | `test_correccion_no_modifica_otros_datos` | `test_servicio_correccion.py` |
| Constraint — quién y cuándo corrigió van juntos | `test_medicion_correccion_completa` | `test_modelos.py` |
| Concurrencia — dos correcciones simultáneas de la misma medición | `test_correcciones_concurrentes` (`transaction=True`, hilos) | `test_concurrencia_mediciones.py` |
| Falla de base no corrige nada | `test_error_de_base_al_corregir` | `test_corregir_mediciones.py` |

## Project Structure

### Documentation (this feature)

```text
specs/017-modificar-mediciones/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── corregir-mediciones-ui.md
├── checklists/
│   └── requirements.md
└── tasks.md              # /speckit-tasks
```

### Source Code (repository root)

```text
CLAUDE.md                                   # + sección «Corrección de mediciones (US 6.3)»; nota US 6.3 de la sección de US 6.2
estudios/
├── models.py                               # Medicion: + corregida_por, fecha_correccion, constraint
├── migrations/0006_medicion_correccion.py  # nueva
├── calculo.py                              # + afectadas() (extraída de recalcular)
├── forms.py                                # + CorregirMedicionesForm
├── servicios.py                            # + CorregirMedicionesError, ResultadoCorreccion, corregir_mediciones
├── views.py                                # + corregir_mediciones; detalle con el botón
├── urls.py                                 # + <int:pk>/mediciones/corregir/
├── templates/estudios/
│   ├── detalle.html                        # + botón y «Corregida por …»
│   ├── corregir_mediciones.html            # nuevo
│   └── corregir_mediciones_confirmar.html  # nuevo
└── tests/
    ├── test_modelos.py                     # + constraint
    ├── test_servicio_correccion.py         # nuevo
    ├── test_corregir_mediciones.py         # nuevo
    └── test_concurrencia_mediciones.py     # + correcciones concurrentes
```

**Structure Decision**: todo en la app `estudios`, junto a la carga (US 6.1) y el cálculo (US 6.2).

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Principio IV: un resultado validado pierde la validación al recalcularse por una corrección. | Es la excepción ya justificada y aprobada en `specs/016-calcular-resultado/plan.md`; esta historia es la que la ejerce (la pantalla de corrección). | Ver el plan de US 6.2. Aquí además se avisa en el resumen qué pruebas perderán la validación antes de confirmar (FR-005). |
