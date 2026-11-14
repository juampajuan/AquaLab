# Implementation Plan: Curva de calibración para pruebas por absorbancia

**Branch**: `037-curva-calibracion` | **Date**: 2026-11-14 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/037-curva-calibracion/spec.md` (US 6.6, SCRUM-38)

## Summary

Tercer tipo de cálculo del catálogo, «Curva de calibración». Cada prueba por curva tiene curvas
(`CurvaCalibracion` + `PuntoCurva`, app `pruebas`), a lo sumo una vigente. El administrador la carga
desde la ficha de gestión (SCRUM-73): puntos a mano en un formset o importados de `.csv`/`.xlsx`
(`pruebas/importacion_curvas.py`), recta por mínimos cuadrados en `Decimal` (`pruebas/curvas.py:ajustar`),
gráfico con el Chart.js ya vendorizado y confirmación con borrador firmado. `guardar_curva` pasa la
vigente a histórica y, si se marca, calcula las mediciones que esperaban curva. El cálculo de
resultados (`estudios/calculo.py`) suma la rama `CURVA`: concentración = (absorbancia − ordenada) /
pendiente, con la curva del resultado existente o la vigente (`curvas.curva_para`), guardada en
`Resultado.curva`. Sin curva → «Falta curva de calibración.» (no se valida). El aviso «fuera del
rango» se calcula al vuelo. Consulta de solo lectura para todos los empleados (`curvas:`). Única
dependencia nueva: `openpyxl` para `.xlsx` (R9).

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: Django 5.2 LTS (formsets, `signing`, `select_for_update`), Tailwind CSS 4 y
`templates/ui/`, Chart.js 4.4.7 (ya en `static/vendor/`). **Nueva**: `openpyxl==3.1.5` (+
`et-xmlfile==2.0.0`), solo para leer `.xlsx`; justificada en [research.md](./research.md) R9.

**Storage**: PostgreSQL 16. Migraciones `pruebas/0004_curvas_calibracion.py` (tipo `CURVA`,
constraint, `CurvaCalibracion`, `PuntoCurva`) y `estudios/0012_resultado_curva.py` (`Resultado.curva`).
Advisory lock `pg_advisory_xact_lock(6_600_001, prueba_id)` (exclusivo/compartido, R5).

**Testing**: pytest + pytest-django; fixtures de `pruebas/tests/conftest.py` (`administrador_catalogo`,
`cliente_catalogo`, `datos_prueba`) y `estudios/tests/conftest.py` (`estudio_de`, `bioquimico`,
`django_capture_on_commit_callbacks`); `node --test` para `curva.js`; ruff.

**Target Platform**: Contenedor `web` (Docker Compose) y Render.

**Project Type**: Aplicación web Django monolítica con templates en el servidor.

**Performance Goals**: Carga de una curva de 6 puntos < 3 minutos (SC-001); detalle del estudio sin
N+1 (`resultado__curva` en `select_related`).

**Constraints**: `Decimal` en todo el cálculo (principio IV; el `float` de openpyxl se convierte al
leer, R8); recálculo con la misma curva (FR-020); resultados, validaciones e informes anteriores no
cambian (FR-022); sin `IntegrityError` ni deadlocks entre carga de mediciones, confirmación y
borrado de curvas (R5); archivos ≤ 1 MB, ≤ 1000 filas, ≤ 50 puntos.

**Scale/Scope**: app `pruebas` (modelos, migración, `curvas.py`, `importacion_curvas.py`,
formularios, vistas, URLs, 5 templates, `curva.js`); cambios puntuales en `estudios`
(`Resultado.curva`, `calculo.calcular/recalcular`, detalle y validación) y en `pruebas/gestion.py`
(R12); `requirements.txt`, CI (`node --test`), CLAUDE.md y tests.

Decisiones en [research.md](./research.md) (R1–R13). No hay `NEEDS CLARIFICATION` pendientes.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Cumplimiento | Estado |
|---|---|---|
| **I. Spec primero (SDD)** | Spec de US 6.6 / SCRUM-38 con 3 aclaraciones (2026-11-14); el edge case de R12 se agregó primero en la spec. El código espera la aprobación de la spec. | ✅ |
| **II. Simplicidad y Django idiomático** | Vive en `pruebas`; reutiliza `gestion.autorizar`, el patrón de `confirmaciones.py`, `calculo.recalcular`, `leer_valor` y Chart.js. Formset sin JS para la tabla. **Una dependencia nueva** (`openpyxl`), justificada en R9 y a acordar en el PR. | ✅ (con justificación) |
| **III. Tests obligatorios** | Cada escenario y FR con test ([Mapa de tests](#mapa-de-tests)); recta y conversión con el caso de referencia de R2 y valores explícitos. | ✅ |
| **IV. Integridad de datos** | `Decimal` (pendiente/ordenada 12 decimales, R² 10, resultado 10); la curva se guarda con el resultado y no se edita; la usada no se borra (`usada` + `PROTECT`); una curva nueva no recalcula nada anterior; resultados validados e informes intactos. | ✅ |
| **V. Seguridad** | Carga/borrado con `administracion_requerida` + revalidación en el servicio; consulta solo con sesión; CSRF; borrador firmado atado a usuario y sesión; archivo limitado en tamaño y filas, no se guarda. | ✅ |
| **VI. Idioma y consistencia** | `CurvaCalibracion`, `PuntoCurva`, `guardar_curva`, `curva_para`; interfaz en español; ruff. | ✅ |
| **Interfaz (UI)** | Confirmación previa (guardar y borrar), `messages`, componentes de `templates/ui/`, ayudas en fecha, puntos y archivo (US 9.1), gráfico con tabla de datos. | ✅ |

**Post-diseño (Phase 1)**: cumple todos los principios; la única salvedad es la dependencia nueva,
justificada en R9 (Complexity Tracking).

## Diseño

```text
/administracion/pruebas/<pk>/                 ficha (existente) + sección «Curvas de calibración»
/administracion/pruebas/<pk>/curvas/nueva/    formset + archivo; accion: agregar_fila | quitar_<n> |
                                              importar | elegir_columnas | calcular | guardar
/administracion/pruebas/<pk>/curvas/confirmar/ resumen (+ «Calcularlas con esta curva») → guardar_curva
/administracion/pruebas/curvas/plantilla.csv  plantilla
/administracion/pruebas/curvas/<c>/borrar/    confirmación → borrar_curva
/pruebas/<pk>/curvas/  ·  /pruebas/curvas/<c>/  consulta de solo lectura (cualquier empleado)

guardar_curva(usuario, prueba_id, datos, clave, calcular_pendientes)      (una transacción)
  autorizar → [estudios candidatos FOR UPDATE, por pk] → advisory exclusivo(prueba)
  → Prueba FOR UPDATE (tipo CURVA) → ¿clave existe? devolverla → ajustar(puntos)
  → vigente anterior = histórica → crear curva + puntos → recalcular pendientes por estudio

borrar_curva(usuario, curva_id)
  autorizar → advisory exclusivo(prueba) → curva FOR UPDATE → usada? rechazar
  → borrar → si era vigente: anterior más reciente = vigente

calculo.recalcular(...)  rama CURVA:
  curva = curvas.curva_para(asignacion, bloquear=True)   # resultado.curva o vigente (advisory compartido)
  valor = (x − ordenada) / pendiente  → Resultado(curva=curva, formula="") → curva.usada = True
```

Pantallas y mensajes en [contracts/curvas-ui.md](./contracts/curvas-ui.md); modelos y reglas en
[data-model.md](./data-model.md); concurrencia en research R5.

### Mapa de tests

| Escenario / requisito | Test | Archivo |
|---|---|---|
| FR-001/002, US1 Esc. 1–3 — tipo «Curva», unidad obligatoria, sin fórmula, «Abs», «Sin curva vigente» | `test_prueba_por_curva_*` | `pruebas/tests/test_curvas_catalogo.py` |
| US1 Esc. 4 — prueba en uso no pasa a Curva | `test_en_uso_no_pasa_a_curva` | idem |
| R12 — con curvas no cambia de tipo; eliminar sin uso borra sus curvas | `test_cambio_tipo_con_curvas`, `test_eliminar_borra_curvas` | idem |
| FR-011, R2 — recta, ordenada y R² del caso de referencia; réplicas; blanco | `test_ajustar_caso_referencia`, `test_ajustar_replicas` | `pruebas/tests/test_curvas_calculo.py` |
| FR-004, US2 Esc. 3–5 — < 3 puntos, vacíos, negativos, concentraciones o absorbancias iguales, pendiente 0 | `test_ajustar_rechaza` (parametrizado) | idem |
| FR-015a, US2 Esc. 9 — aviso R² < 0,995 (y 0,995 exacto sin aviso) | `test_r2_bajo` | idem |
| FR-003/005/012, US2 Esc. 1–2, 6–8 — formset, agregar/quitar filas, calcular, resumen, cancelar, fecha futura | `test_carga_manual_*` | `pruebas/tests/test_curvas_vistas.py` |
| FR-013/014, US2 Esc. 7 — guarda todo, vigente nueva, anterior histórica | `test_guardar_curva_*` | `pruebas/tests/test_curvas_servicio.py` |
| FR-014, edge — dos confirmaciones simultáneas: una sola vigente; reenvío de la misma clave no duplica | `test_concurrencia_guardar`, `test_clave_repetida` (`transaction=True`) | `pruebas/tests/test_curvas_concurrencia.py` |
| FR-006/007, US3 Esc. 2–5 — CSV `;` y `,`, BOM, Latin-1, XLSX, títulos/vacías/texto ignorados, coma o punto, detección de columnas | `test_leer_*` (parametrizado) | `pruebas/tests/test_curvas_importacion.py` |
| FR-007, US3 Esc. 5 — columnas dudosas: elegir; dos iguales rechazadas | `test_elegir_columnas` | idem + `test_curvas_vistas.py` |
| FR-008, US3 Esc. 6–8 — formato, tamaño, ilegible, vacío, «La fila 4 no tiene absorbancia», < 3 puntos: tabla sin cambios | `test_archivo_invalido` (parametrizado) | idem |
| FR-009/010, US3 Esc. 1, 9 — plantilla descargable e importable; nombre de archivo guardado tras editar puntos | `test_plantilla`, `test_archivo_origen` | `pruebas/tests/test_curvas_vistas.py` |
| FR-016/017, US4 Esc. 1–2 — resultado = (abs − ordenada)/pendiente (0,126 → 0,2501002004), curva guardada y mostrada | `test_calculo_con_curva`, `test_detalle_muestra_curva` | `estudios/tests/test_calculo_curva.py` |
| FR-018, US4 Esc. 3–4 — sin curva: medición guardada, sin resultado, «Falta curva…», no se valida | `test_sin_curva` | idem |
| FR-019, US4 Esc. 5 — fuera de rango (debajo, encima, bordes) en detalle y validación; se valida igual | `test_fuera_de_rango` (parametrizado) | idem |
| FR-021, US4 Esc. 6 — fórmula que usa una prueba por curva toma la concentración | `test_formula_usa_concentracion` | idem |
| FR-022, US4 Esc. 7, SC-006 — curva nueva no cambia resultados, validaciones ni informes | `test_curva_nueva_no_recalcula` | idem |
| FR-025, US4 Esc. 8–10 — pendientes: cuenta en el resumen, calcular con la casilla, sin casilla esperan, estudios con informe excluidos | `test_pendientes_*` | `pruebas/tests/test_curvas_servicio.py` |
| FR-020, US5 Esc. 1–4 — corrección con la misma curva; sin resultado previo usa vigente; borrada y recargada usa vigente; pierde validación | `test_correccion_*` | `estudios/tests/test_calculo_curva.py` |
| FR-015, US6 Esc. 4–5 — borrar sin usar (vuelve la anterior / queda sin curva); usada no se borra por ninguna vía | `test_borrar_curva_*` | `pruebas/tests/test_curvas_servicio.py` |
| R5, edges — borrar mientras se calcula con ella; carga durante confirmación; sin deadlock | `test_concurrencia_borrar`, `test_concurrencia_carga` (`transaction=True`) | `pruebas/tests/test_curvas_concurrencia.py` |
| FR-024, US6 Esc. 1–3 — consulta: vigente, históricas, detalle, enlace desde el estudio a la histórica | `test_consulta_*` | `pruebas/tests/test_curvas_vistas.py` |
| FR-023, US7 — 403 en carga, importar, confirmar, plantilla y borrar (técnico, bioquímico fuera del grupo, superusuario fuera del grupo); consulta OK; login | `test_acceso` (parametrizado) | idem |
| R11 — funciones puras de `curva.js` (datasets, extremos) | `curva.test.js` | `pruebas/tests/js/` |

## Project Structure

### Documentation (this feature)

```text
specs/037-curva-calibracion/
├── spec.md, plan.md, research.md, data-model.md, quickstart.md
├── contracts/curvas-ui.md
├── checklists/requirements.md
└── tasks.md              # /speckit-tasks
```

### Source Code (repository root)

```text
CLAUDE.md                                         # + sección «Curvas de calibración (US 6.6)»
requirements.txt                                  # + openpyxl==3.1.5, et-xmlfile==2.0.0
.github/workflows/ci.yml                          # node --test … pruebas/tests/js
config/urls.py                                    # + pruebas/ → pruebas.urls_curvas (namespace curvas)
pruebas/
├── models.py                                     # TipoCalculo.CURVA, constraint, clean, CurvaCalibracion, PuntoCurva
├── migrations/0004_curvas_calibracion.py
├── curvas.py                                     # nuevo: ajustar, curva_para, fuera_de_rango,
│                                                 #   pendientes_de_curva, guardar_curva, borrar_curva
├── importacion_curvas.py                         # nuevo: leer_archivo, extraer_puntos, plantilla
├── formularios_curvas.py                         # nuevo: CurvaForm, PuntoFormSet, ElegirColumnasForm
├── confirmaciones.py                             # + operación «curva» (borrador con clave)
├── gestion.py                                    # R12: cambio de tipo con curvas
├── formularios.py                                # «Abs» por defecto con tipo Curva
├── views_curvas.py, urls.py, urls_curvas.py      # carga/borrado (catalogo:) y consulta (curvas:)
├── templates/pruebas/ficha.html                  # + sección de curvas
├── templates/pruebas/curvas/{formulario,confirmar,listar,detalle,borrar}.html
├── static/pruebas/curva.js
└── tests/test_curvas_*.py, tests/js/curva.test.js
estudios/
├── models.py                                     # Resultado.curva
├── migrations/0012_resultado_curva.py
├── calculo.py                                    # rama CURVA en calcular/recalcular
├── views.py                                      # select_related de la curva; fuera de rango
├── templates/estudios/{detalle,validar_resultados}.html  # curva usada y aviso
└── tests/test_calculo_curva.py
```

**Structure Decision**: las curvas son parte del catálogo → app `pruebas` (carga en el panel
`catalogo:`, consulta en `curvas:`). `estudios` solo suma la FK y la rama de cálculo, porque
`calculo.py` es el único lugar donde se calculan resultados.

## Complexity Tracking

| Desvío | Por qué hace falta | Alternativa más simple descartada porque |
|---|---|---|
| Dependencia nueva `openpyxl` (constitution II) | El criterio 3 pide importar `.xlsx`; la biblioteca estándar no lo lee | Solo CSV incumple el criterio; leer el XML a mano es frágil; pandas es mucho más pesada y usa `float` |
