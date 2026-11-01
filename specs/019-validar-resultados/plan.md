# Implementation Plan: Validar resultados

**Branch**: `019-validar-resultados` | **Date**: 2026-11-01 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/019-validar-resultados/spec.md` (US 6.4, Jira a confirmar)

## Summary

Desde el detalle del estudio, quien tiene el permiso **Puede validar resultados** (grupo
«Bioquímicos», creado por migración) abre **Validar resultados**: una pantalla con las pruebas
Cargadas con resultado, su límite aplicable y su evaluación, con marcadas solo las que cumplen.
Se reutiliza el flujo de carga y corrección (revisar / editar / confirmar, más «Marcar todas»). El
servicio `validar_resultados` bloquea el estudio, rechaza con informe emitido, omite las ya
validadas, las que ya no tienen resultado y las que cambiaron desde la revisión, y por cada una
crea una `Validacion` (quién, cuándo, límites usados y evaluación) y la pasa a Completada; si no
queda ninguna sin validar, el estudio pasa a Finalizado. La evaluación (cumple / fuera de norma /
sin límite comparable) es un módulo puro `pruebas/limites.py` que el detalle también usa para
mostrarla antes de validar. Un recálculo o borrado posterior anula la `Validacion` (sin borrarla) desde un
único punto (`calculo.cambiar_estado`).

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: Django 5.2 LTS (ORM, auth: permisos y grupos, forms, messages), Tailwind
CSS 4 y componentes de `templates/ui/`. Sin dependencias nuevas ni JavaScript.

**Storage**: PostgreSQL 16 en Docker. Tabla nueva `estudios_validacion`; migraciones
`estudios/migrations/0007_validacion.py` (modelo y permiso) y `0008_grupo_bioquimicos.py` (datos).

**Testing**: pytest 9.1.1 + pytest-django 4.14.0; fixtures `estudio_de`, `catalogo` y helper
`cargar` (US 6.2/6.3); concurrencia con `transaction=True` e hilos; ruff 0.17.1.

**Target Platform**: Contenedor Linux (`web`) con Docker Compose; navegador de escritorio.

**Project Type**: Aplicación web Django monolítica con templates en el servidor (sin SPA).

**Performance Goals**: Validar un estudio completo en menos de 1 minuto con una sola confirmación
(SC-001); evaluación en memoria para ≤ 90 pruebas por estudio, con una consulta para los límites.

**Constraints**: Solo con el permiso (FR-001); nada cambia con informe emitido (FR-013);
concurrencia optimista por el valor visto (FR-014, SC-006); evaluación guardada inmutable mientras
la prueba esté Completada (FR-012); sin CSS nuevo (el CSS compilado lo controla el CI).

**Scale/Scope**: 1 modelo + 2 migraciones, 1 módulo de evaluación, 1 cambio en `calculo.py`, 1
formulario, 1 servicio + 1 excepción + 1 resultado, 1 vista, 2 templates, 1 URL, cambios en
`detalle` (vista y template), sección en `CLAUDE.md` y tests. El admin de estudios (solo lectura)
es otra tarea del sprint: no se toca `estudios/admin.py` para no chocar.

Decisiones en [research.md](./research.md) (R1–R8). No hay `NEEDS CLARIFICATION` pendientes.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Cumplimiento | Estado |
|---|---|---|
| **I. Spec primero (SDD)** | Spec de US 6.4 con 11 aclaraciones (2026-11-01). PR: «US 6.4 – Validar resultados». El código espera la aprobación de la spec. Clave de Jira a confirmar. | ✅ |
| **II. Simplicidad y Django idiomático** | Permisos y grupos de `django.contrib.auth`, mismo flujo y componentes que carga/corrección, sin JavaScript ni dependencias. La evaluación es un módulo de funciones puras (R3). | ✅ |
| **III. Tests obligatorios** | Cada escenario y FR con test (ver [Mapa de tests](#mapa-de-tests)); la evaluación se prueba con los límites reales del catálogo y valores en el borde. | ✅ |
| **IV. Integridad de datos** | Validar no toca resultado ni medición; la evaluación y los límites usados se guardan; con informe emitido nada cambia. Perder la validación al recalcular es la excepción ya justificada en US 6.2 (*Complexity Tracking*). | ⚠️ Excepción heredada de US 6.2 |
| **V. Seguridad** | `LoginRequiredMiddleware` + `@permission_required(raise_exception=True)` + revalidación en el servicio; cambios solo por POST con CSRF; asignaciones buscadas dentro del estudio de la URL. | ✅ |
| **VI. Idioma y consistencia** | `Validacion`, `validar_resultados`, `validada_por`, `Evaluacion`, grupo «Bioquímicos». Interfaz en español. ruff. | ✅ |
| **Interfaz (UI)** | Resumen y confirmación antes de guardar, `messages`, componentes existentes (`etiqueta-danger` ya existe). | ✅ |

**Post-diseño (Phase 1)**: cumple todos los principios; la única excepción es la de US 6.2.

## Diseño

### Flujo

```text
GET  /estudios/<pk>/                           → detalle: evaluación por resultado, «Validada por …»,
                                                 botón «Validar resultados» (con permiso)
GET  /estudios/<pk>/resultados/validar/        → 403 sin permiso | 302 con informe | formulario
POST                          accion=marcar_todas → formulario con todas marcadas
POST                          accion=revisar      → error «Elegí al menos…» | resumen
POST                          accion=editar       → formulario con la selección
POST                          accion=confirmar    → validar_resultados() → 302 detalle + mensajes
validar_resultados (estudio bloqueado)
  └─ permiso? informe? → filas bloqueadas → ya validada / sin resultado / cambió → omitir
     → evaluar(limites_aplicables) → Validacion + Completada → ¿todas Completadas? → Finalizado
recalcular / descartar (US 6.2, 6.3, 6.5) → cambiar_estado: sale de Completada → anula Validacion
```

Rutas y mensajes en [contracts/validar-resultados-ui.md](./contracts/validar-resultados-ui.md);
modelo, reglas y transiciones en [data-model.md](./data-model.md).

### Mapa de tests

| Escenario / requisito | Test | Archivo |
|---|---|---|
| FR-007 — reglas de evaluación con límites reales (dentro, bordes, fuera; Ausente con 0 y ≠ 0; SOE, NE, Ph±0,2, sin límites; coma y punto) | `test_leer_limite`, `test_evaluar` (parametrizados) | `pruebas/tests/test_limites.py` |
| FR-006, US2 Esc. 3–4 — límites por vertido reemplazan a los generales; Agua usa generales; vertido con solo máximo | `test_limites_aplicables` (parametrizado: Agua, Cloacal, Canal, sin fila de vertido) | `pruebas/tests/test_limites.py` |
| US3 Esc. 1, FR-002 — grupo «Bioquímicos» con el permiso tras migrar | `test_grupo_bioquimicos_tiene_el_permiso` | `estudios/tests/test_validacion_permisos.py` |
| US3 Esc. 2–3, FR-001/003 — sin permiso: sin botón y 403; con el grupo: botón y acceso; quien cargó puede validar | `test_sin_permiso_no_ve_ni_valida`, `test_bioquimico_ve_y_valida`, `test_quien_cargo_puede_validar` | `test_validacion_permisos.py` |
| US1 Esc. 1–2, FR-004 — lista Cargadas con resultado; marcadas solo las que cumplen | `test_formulario_lista_y_marca_las_que_cumplen` | `estudios/tests/test_validar_resultados.py` |
| FR-004 — «Marcar todas» y al menos una | `test_marcar_todas`, `test_revisar_sin_elegir_rechaza` | `test_validar_resultados.py` |
| US1 Esc. 3, FR-005 — resumen destaca fuera de norma; editar y cancelar sin cambios | `test_revisar_muestra_resumen`, `test_editar_conserva_seleccion` | `test_validar_resultados.py` |
| US1 Esc. 4/7, FR-009/010 — confirmar: Completada, quién, cuándo, límites y evaluación; fuera de norma se valida igual | `test_confirmar_valida`, `test_validar_guarda_evaluacion_y_limites`, `test_fuera_de_norma_se_valida` | `test_validar_resultados.py`, `estudios/tests/test_servicio_validacion.py` |
| US1 Esc. 5–6, FR-011 — Finalizado solo con todas Completadas | `test_ultima_validacion_finaliza`, `test_con_pendientes_sigue_en_proceso` | `test_servicio_validacion.py` |
| US2 Esc. 1–8, FR-008/012 — evaluación visible antes de validar; validada muestra lo guardado aunque cambie el catálogo | `test_detalle_muestra_evaluacion`, `test_detalle_validada_usa_lo_guardado` | `estudios/tests/test_consulta.py` |
| FR-013 — informe emitido rechaza (vista y servicio) | `test_informe_emitido_rechaza`, `test_vista_informe_emitido_rechaza` | `test_servicio_validacion.py`, `test_validar_resultados.py` |
| FR-014 — omite ya validada, sin resultado y cambiada; reenvío no cambia nada | `test_omite_ya_validada`, `test_omite_sin_resultado`, `test_omite_si_cambio`, `test_reenvio_no_cambia` | `test_servicio_validacion.py` |
| R2, FR-017 — corregir o borrar una medición validada anula la `Validacion` (se conserva) y revalidar crea otra vigente | `test_correccion_anula_validacion`, `test_borrado_anula_validacion`, `test_revalidar_conserva_anulada` | `test_servicio_validacion.py` |
| FR-015 — informa validadas, omitidas con su motivo y si el estudio quedó Finalizado | `test_confirmar_valida_y_redirige`, `test_confirmar_informa_omitidas` | `test_validar_resultados.py` |
| FR-016 — no modifica resultado, medición, muestra, catálogo ni otros estudios | `test_validacion_no_modifica_otros_datos` | `test_servicio_validacion.py` |
| Concurrencia — dos validaciones simultáneas del mismo estudio | `test_validaciones_concurrentes` (`transaction=True`, hilos) | `estudios/tests/test_concurrencia_validacion.py` |
| Falla de base no valida nada | `test_error_de_base_al_validar` | `test_validar_resultados.py` |

## Project Structure

### Documentation (this feature)

```text
specs/019-validar-resultados/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── validar-resultados-ui.md
├── checklists/
│   └── requirements.md
└── tasks.md              # /speckit-tasks
```

### Source Code (repository root)

```text
CLAUDE.md                                      # + sección «Validación de resultados (US 6.4)»; se quita la nota «Epic 6 (validación, US 6.4)» y la de SCRUM-64
pruebas/
├── limites.py                                 # nuevo: leer_limite, limites_aplicables, evaluar, Evaluacion
└── tests/test_limites.py                      # nuevo
estudios/
├── models.py                                  # + OrigenLimites, Validacion (permiso validar_resultados)
├── migrations/0007_validacion.py              # nueva
├── migrations/0008_grupo_bioquimicos.py       # nueva (datos)
├── calculo.py                                 # cambiar_estado: al salir de Completada anula la Validacion
├── forms.py                                   # + ValidarResultadosForm
├── servicios.py                               # + ValidarResultadosError, ResultadoValidacion, validar_resultados
├── views.py                                   # + validar_resultados; detalle con evaluación y botón
├── urls.py                                    # + <int:pk>/resultados/validar/
├── templates/estudios/
│   ├── detalle.html                           # + evaluación, límite, «Validada por …», botón
│   ├── validar_resultados.html                # nuevo
│   └── validar_resultados_confirmar.html      # nuevo
└── tests/
    ├── test_servicio_validacion.py            # nuevo
    ├── test_validar_resultados.py             # nuevo
    ├── test_validacion_permisos.py            # nuevo
    ├── test_concurrencia_validacion.py        # nuevo
    └── test_consulta.py                       # + evaluación en el detalle
```

**Structure Decision**: la validación vive en la app `estudios`, junto a la carga, el cálculo y
la corrección; la interpretación de los límites, en `pruebas`, junto a `formulas.py`, porque es
lógica del catálogo.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Principio IV: un resultado validado pierde la validación al recalcularse o descartarse. | Es la excepción ya justificada y aprobada en `specs/016-calcular-resultado/plan.md`; esta historia agrega que, al perderse, la `Validacion` queda anulada (R2, FR-017): no se borra, y la vigente nunca describe un resultado distinto. | Ver el plan de US 6.2. Mantenerla vigente mostraría una evaluación y un «Validada por» que ya no corresponden; borrarla perdería el historial (principio IV). |
