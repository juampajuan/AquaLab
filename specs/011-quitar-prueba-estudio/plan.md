# Implementation Plan: Quitar prueba del estudio

**Branch**: `011-quitar-prueba-v2` | **Date**: 2026-10-27 (actualizado 2026-10-28) | **Spec**: [spec.md](./spec.md)

> **Actualización 2026-10-28**: se implementa sobre `010-agregar-prueba-v2` (US 5.3 ya implementada
> sobre US 5.2 y el rediseño de SCRUM-67). La ficha del estudio (`estudios:detalle`) es la de US 5.2
> y ya tiene la columna Acción vacía de US 5.3. Ya existen `Estudio.admite_modificaciones`,
> `GestionPruebasError`, `PruebaYaAsignada` y `agregar_prueba`. Las pantallas usan Tailwind y los
> componentes de `templates/ui/`. «Tiene mediciones o resultados» se lee del estado individual de
> la prueba (US 5.2): solo una prueba `Pendiente` se puede quitar.

**Input**: Feature specification from `specs/011-quitar-prueba-estudio/spec.md` (US 5.4)

## Summary

Quita de pruebas de un estudio, dentro de la app `estudios`, sin cambios de esquema y sobre lo que
entregan US 5.2 (la ficha `/estudios/<pk>/` y el estado de cada prueba) y
[US 5.3](../010-agregar-prueba-estudio/plan.md) (`Estudio.admite_modificaciones`,
`GestionPruebasError` y la columna Acción). El detalle suma un botón **Quitar** por
prueba, que lleva a una confirmación y luego borra la asignación. El servicio `quitar_prueba`
bloquea la fila del estudio y la de la asignación, y revalida que el estudio admita cambios, que la
asignación siga en el estudio, que no sea la última y que `PruebaEstudio.puede_quitarse()` lo
permita (estado `Pendiente`: sin mediciones ni resultados).

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: Django 5.2 LTS (ORM, messages), Tailwind CSS 4 y componentes de
`templates/ui/` (SCRUM-67). Sin JavaScript ni dependencias nuevas.

**Storage**: PostgreSQL 16 en Docker. Tabla existente `estudios_pruebaestudio`; sin migraciones.

**Testing**: pytest 9.1.1 + pytest-django 4.14.0 con el test client de Django; tests de
concurrencia con `transaction=True` e hilos en `estudios/tests/test_concurrencia_pruebas.py`
(creado en US 5.3); ruff 0.17.1.

**Target Platform**: Contenedor Linux (`web`) con Docker Compose; navegador de escritorio.

**Project Type**: Aplicación web Django monolítica con templates en el servidor (sin SPA).

**Performance Goals**: Quitar una prueba en menos de 1 minuto con una sola confirmación (SC-005).

**Constraints**: Confirmación antes de eliminar (FR-005, sección Interfaz); revalidación bajo
bloqueo de la fila del estudio (FR-006, FR-011); reenvío idempotente (FR-010); la cabecera, los
snapshots y el catálogo no cambian (FR-008); sesión obligatoria (FR-001); textos en español
(Principio VI). **Depende de US 5.3**: la rama sale de `010-agregar-prueba-v2` y el PR se
mergea después del de US 5.3.

**Scale/Scope**: 1 servicio + 2 excepciones, 1 método de modelo, 1 vista, 1 template nuevo, 1 URL,
columna Acción de `detalle.html`, componente `.btn-chico` en `static/src/aqualab.css` (CSS
recompilado), nota en `CLAUDE.md` y tests en `estudios/tests/`.

Decisiones documentadas en [research.md](./research.md) (R1–R5). No hay `NEEDS CLARIFICATION`
pendientes.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Cumplimiento | Estado |
|---|---|---|
| **I. Spec primero (SDD)** | Spec de US 5.4 en `specs/011-quitar-prueba-estudio/spec.md`, una US por spec y por rama, como pidió el equipo. El código espera la aprobación de la spec (T001); US 5.3 ya está implementada en `010-agregar-prueba-v2`. PR: «US 5.4 – Quitar prueba del estudio» (SCRUM-51). | ✅ |
| **II. Simplicidad y Django idiomático** | Vista de función con confirmación GET/POST, como un borrado estándar de Django. Sin JavaScript, dependencias ni modelos nuevos; `puede_quitarse()` se apoya en el estado existente de US 5.2, sin crear modelos de mediciones (YAGNI). | ✅ |
| **III. Tests obligatorios** | Cada escenario de aceptación (US1 1–5, US2 1–6), FR y caso límite tiene test (ver [Mapa de tests](#mapa-de-tests)). | ✅ |
| **IV. Integridad de datos** | Solo se borra una asignación en estado `Pendiente` (sin mediciones ni resultados), que no tiene historial (Clarifications); el estado se lee con la fila de la asignación bloqueada y las futuras mediciones apuntarán con `PROTECT`. Regla de la última prueba bajo bloqueo de la fila del estudio. Reglas en el modelo y el servicio, no solo en el template. | ✅ |
| **V. Seguridad** | Vistas protegidas por `LoginRequiredMiddleware`; el borrado solo por POST con CSRF; la asignación se busca dentro del estudio de la URL (no se puede operar sobre otro estudio cambiando el id). | ✅ |
| **VI. Idioma y consistencia** | Términos del dominio: `quitar_prueba`, `puede_quitarse`, `PruebaYaQuitada`, `UltimaPrueba`. Interfaz y mensajes en español. ruff. | ✅ |
| **Interfaz (UI)** | Extiende `base.html` con los componentes de `templates/ui/` (constitution v1.1.0): `ui/encabezado.html`, resumen y acciones de confirmación; confirmación antes de eliminar, mensajes con `messages`. El botón chico de la tabla es un componente nuevo (`.btn-chico`) en el CSS del tema, no clases sueltas. | ✅ |

**Post-diseño (Phase 1)**: cumple todos los principios sin excepciones en *Complexity Tracking*.

## Diseño

### Flujo

```text
GET  /estudios/<pk>/pruebas/<asignacion_pk>/quitar/   → confirmación (o 302 detalle si no se puede)
POST                                                  → quitar_prueba() → 302 detalle + mensaje
```

Rutas, condiciones y mensajes exactos en
[contracts/quitar-prueba-ui.md](./contracts/quitar-prueba-ui.md); reglas en
[data-model.md](./data-model.md).

### Servicio (`estudios/servicios.py`)

```text
GestionPruebasError(Exception)          # de US 5.3
├── PruebaYaAsignada                    # de US 5.3
├── PruebaYaQuitada                     # nuevo: reenvío o quita simultánea (se informa como aviso)
└── UltimaPrueba                        # nuevo: FR-011

quitar_prueba(estudio_pk, asignacion_pk, usuario) -> Prueba   # la prueba quitada, para el mensaje
```

Sesión activa → `transaction.atomic()` → `select_for_update()` del estudio →
`admite_modificaciones` → asignación del estudio (`select_for_update`) → no es la última →
`puede_quitarse()` → `delete()` (R3).

### Mapa de tests

| Escenario / requisito | Test | Archivo |
|---|---|---|
| FR-001, US2 Esc. 5 — vistas requieren sesión | `test_vistas_quitar_prueba_requieren_sesion` (GET y POST) | `test_quitar_prueba.py` |
| US1 Esc. 1, FR-002 — acción quitar en cada prueba quitable | `test_detalle_ofrece_quitar_en_pruebas_quitables` | `test_quitar_prueba.py` |
| US1 Esc. 2, FR-005, SC-004 — GET quitar muestra confirmación con Cancelar y no borra | `test_quitar_get_muestra_confirmacion_sin_borrar` | `test_quitar_prueba.py` |
| US1 Esc. 3–4, FR-007/009 — confirmar quita la asignación | `test_confirmar_quita_prueba`, `test_quitar_prueba_borra_asignacion` | `test_quitar_prueba.py`, `test_servicio_pruebas.py` |
| US1 Esc. 3, FR-008, edge cases — cabecera, snapshots, tipo y otros estudios no cambian | `test_quitar_no_modifica_cabecera_tipo_ni_otros_estudios` | `test_servicio_pruebas.py` |
| US1 Esc. 5, edge case — prueba quitada puede re-agregarse; reenvío viejo no afecta la nueva | `test_prueba_quitada_puede_agregarse_de_nuevo` | `test_servicio_pruebas.py` |
| US2 Esc. 1, FR-004 — prueba `Cargada` o `Completada` no se quita ni se ofrece | `test_quitar_rechaza_prueba_con_mediciones` (parametrizado por estado), `test_detalle_no_ofrece_quitar_prueba_con_mediciones` | `test_servicio_pruebas.py`, `test_quitar_prueba.py` |
| US2 Esc. 2, FR-003 — estudio no modificable rechaza quitar | `test_estudio_no_modificable_rechaza_quitar` (parametrizado por estado), `test_vistas_estudio_no_modificable_no_ofrecen_quitar` (estados guardados en la base) | `test_servicio_pruebas.py`, `test_quitar_prueba.py` |
| US2 Esc. 3, FR-010 — reenvío se informa como ya aplicado | `test_reenvio_confirmar_quitar_informa_ya_quitada` | `test_quitar_prueba.py` |
| US2 Esc. 4, FR-011 — última prueba no se quita ni se ofrece | `test_ultima_prueba_no_se_puede_quitar`, `test_detalle_no_ofrece_quitar_ultima_prueba` | `test_servicio_pruebas.py`, `test_quitar_prueba.py` |
| US2 Esc. 6 — estudio inexistente 404; asignación de otro estudio | `test_quitar_estudio_inexistente_responde_404`, `test_quitar_asignacion_de_otro_estudio_rechazada` | `test_quitar_prueba.py` |
| Edge — quitas simultáneas de las dos únicas pruebas dejan una | `test_quitas_concurrentes_conservan_una_prueba` (`transaction=True`, hilos) | `test_concurrencia_pruebas.py` |
| Edge — quitas simultáneas de la misma asignación quitan una vez | `test_quitas_concurrentes_misma_asignacion` (`transaction=True`, hilos) | `test_concurrencia_pruebas.py` |
| R4 — regla del modelo | `test_puede_quitarse_solo_pendiente` | `test_modelos.py` |
| Falla de base no informa éxito ni cambia nada | `test_error_de_base_al_quitar_no_cambia_estudio` | `test_quitar_prueba.py` |

## Project Structure

### Documentation (this feature)

```text
specs/011-quitar-prueba-estudio/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── quitar-prueba-ui.md
├── checklists/
│   └── requirements.md
└── tasks.md
```

### Source Code (repository root)

```text
CLAUDE.md                                   # + nota para Epic 6 (estado, bloqueo, PROTECT)
static/
├── src/aqualab.css                         # + .btn-chico
└── css/aqualab.css                         # recompilado
estudios/
├── models.py                               # + PruebaEstudio.puede_quitarse()
├── servicios.py                            # + PruebaYaQuitada, UltimaPrueba, quitar_prueba
├── views.py                                # + quitar_prueba (detalle no cambia: usa total_pruebas)
├── urls.py                                 # + <int:pk>/pruebas/<int:asignacion_pk>/quitar/
├── templates/estudios/
│   ├── detalle.html                        # existente (US 5.2/5.3): columna Acción con «Quitar»
│   └── quitar_prueba_confirmar.html        # nuevo
└── tests/
    ├── conftest.py                         # + asignacion
    ├── test_modelos.py                     # + regla del modelo
    ├── test_servicio_pruebas.py            # + tests de quitar (de US 5.3)
    ├── test_quitar_prueba.py               # nuevo
    └── test_concurrencia_pruebas.py        # + quitas concurrentes (de US 5.3)
```

**Structure Decision**: todo dentro de la app `estudios`, extendiendo los archivos de US 5.3. Los
tests de vistas van en un archivo propio (`test_quitar_prueba.py`) para que cada US tenga los suyos.

## Complexity Tracking

Sin violaciones de la constitution.
