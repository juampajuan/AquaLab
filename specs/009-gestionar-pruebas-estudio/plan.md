# Implementation Plan: Agregar y quitar pruebas de un estudio

**Branch**: `009-gestionar-pruebas-estudio` | **Date**: 2026-10-27 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/009-gestionar-pruebas-estudio/spec.md` (US 5.3 y US 5.4)

## Summary

Personalización del conjunto de pruebas de un estudio creado en US 5.1, dentro de la app
`estudios` y sin cambios de esquema. Un detalle mínimo del estudio (`/estudios/<pk>/`), enlazado
desde el mensaje de éxito de la creación, muestra la cabecera y las pruebas asignadas y ofrece
**agregar** una prueba del catálogo que el estudio no tenga (formulario → confirmación → guardar) y
**quitar** una asignación (confirmación → borrar). Los servicios `agregar_prueba` y `quitar_prueba`
bloquean la fila del estudio, revalidan las reglas (estudio en «Pendiente de análisis», prueba no
duplicada, al menos una prueba, sin mediciones ni resultados) y solo crean o borran filas de
`PruebaEstudio`. Las reglas viven en el modelo: `Estudio.admite_modificaciones` y
`PruebaEstudio.puede_quitarse()`; este último es el punto de extensión para US 6.1.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: Django 5.2 LTS (ORM, forms, messages, `format_html`), Bootstrap 5.3 (CDN,
en `base.html`). Sin JavaScript ni dependencias nuevas.

**Storage**: PostgreSQL 16 en Docker. Tablas existentes `estudios_estudio` y
`estudios_pruebaestudio`; sin migraciones.

**Testing**: pytest 9.1.1 + pytest-django 4.14.0 con el test client de Django; tests de
concurrencia con `transaction=True` e hilos, como en `estudios/tests/test_concurrencia.py`; ruff
0.17.1.

**Target Platform**: Contenedor Linux (`web`) con Docker Compose; navegador de escritorio.

**Project Type**: Aplicación web Django monolítica con templates en el servidor (sin SPA).

**Performance Goals**: Agregar o quitar una prueba en menos de 1 minuto con una sola confirmación
(SC-006). Volumen chico: decenas de pruebas por catálogo y por estudio.

**Constraints**: Confirmación antes de guardar o eliminar (FR-008, sección Interfaz); revalidación
bajo bloqueo de la fila del estudio (FR-009, FR-005, FR-014); reenvío idempotente (FR-013); la
cabecera, los snapshots y el catálogo no cambian (FR-011); sesión obligatoria (FR-001); textos en
español (Principio VI).

**Scale/Scope**: 2 servicios + 4 excepciones, 1 propiedad y 1 método de modelo, 1 formulario,
3 vistas, 4 templates, 3 URLs, cambio de texto en `exito` de US 5.1, nota en `CLAUDE.md` y tests en
`estudios/tests/`.

Decisiones documentadas en [research.md](./research.md) (R1–R8). No hay `NEEDS CLARIFICATION`
pendientes.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Cumplimiento | Estado |
|---|---|---|
| **I. Spec primero (SDD)** | Spec de US 5.3 y US 5.4 en `specs/009-gestionar-pruebas-estudio/spec.md`, clarificada. Se agrupan dos US porque son chicas, comparten pantalla y reglas y las implementa la misma persona (Manuel), como permite el principio. El código espera la aprobación de la spec por el equipo. PR: «US 5.3 / 5.4 – Agregar y quitar pruebas de un estudio». | ✅ (aprobación pendiente antes de implementar) |
| **II. Simplicidad y Django idiomático** | Vistas de función, `forms.Form`, `messages` y ORM, como en US 5.1. Confirmación con campo oculto revalidado en vez de borrador en sesión (R2). Sin JavaScript, dependencias ni modelos nuevos; `puede_quitarse()` deja el punto de extensión sin crear modelos de mediciones (YAGNI). | ✅ |
| **III. Tests obligatorios** | Cada escenario de aceptación (US1 1–5, US2 1–5, US3 1–7), FR y caso límite tiene test (ver [Mapa de tests](#mapa-de-tests)). Sin cálculos de resultados en esta historia. | ✅ |
| **IV. Integridad de datos** | `UniqueConstraint(estudio, prueba)` ya existente; bloqueo de fila para la regla de la última prueba; solo se borra una asignación sin mediciones ni resultados, que no tiene historial (Clarifications Q2); las futuras mediciones apuntarán con `PROTECT`. Reglas en el modelo y el servicio, no solo en el template. Snapshots y catálogo intactos. | ✅ |
| **V. Seguridad** | Vistas protegidas por `LoginRequiredMiddleware`; CSRF en todos los POST; la asignación se busca dentro del estudio de la URL (no se puede operar sobre otro estudio cambiando el id). El enlace del mensaje se arma con `format_html`, que escapa los datos. | ✅ |
| **VI. Idioma y consistencia** | Términos del dominio: `Estudio`, `Prueba`, `PruebaEstudio`, `agregar_prueba`, `quitar_prueba`, `admite_modificaciones`. Interfaz y mensajes en español. ruff. | ✅ |
| **Interfaz (UI)** | Extiende `base.html`, Bootstrap 5.3, error junto al campo, confirmación antes de agregar y antes de quitar, mensajes con `messages`. | ✅ |

**Post-diseño (Phase 1)**: cumple todos los principios sin excepciones en *Complexity Tracking*.

## Diseño

### Flujos

```text
GET  /estudios/<pk>/                                  → detalle (404 si no existe)

GET  /estudios/<pk>/pruebas/agregar/                  → formulario con catálogo sin las asignadas
POST accion=revisar                                   → inválido: 200 con error en el campo
                                                      → válido: 200 confirmación (prueba oculta)
POST accion=confirmar                                 → agregar_prueba() → 302 detalle + mensaje

GET  /estudios/<pk>/pruebas/<asignacion_pk>/quitar/   → confirmación (o 302 detalle si no se puede)
POST                                                  → quitar_prueba() → 302 detalle + mensaje
```

Rutas, condiciones y mensajes exactos en
[contracts/pruebas-estudio-ui.md](./contracts/pruebas-estudio-ui.md); reglas en
[data-model.md](./data-model.md).

### Servicios (`estudios/servicios.py`)

```text
GestionPruebasError(Exception)          # mensaje = texto para el empleado
├── PruebaYaAsignada                    # reenvío o agregado simultáneo (se informa como aviso)
├── PruebaYaQuitada                     # reenvío o quita simultánea (se informa como aviso)
└── UltimaPrueba                        # FR-014

agregar_prueba(estudio_pk, prueba_pk, usuario) -> PruebaEstudio
quitar_prueba(estudio_pk, asignacion_pk, usuario) -> Prueba   # la prueba quitada, para el mensaje
```

Ambos: sesión activa → `transaction.atomic()` → `select_for_update()` del estudio →
`admite_modificaciones` → reglas propias (R4) → crear o borrar la `PruebaEstudio`.

### Formulario `AgregarPruebaForm(forms.Form)`

- `__init__(self, *args, estudio, **kwargs)`: `prueba = ModelChoiceField(Prueba.objects.exclude(
  pk__in=estudio.pruebas_asignadas.values("prueba")), empty_label="Elegí una prueba")`, clase
  `form-select` e `is-invalid` como en `CrearEstudioForm`.
- La vista pasa al template si el queryset está vacío, para mostrar la alerta en lugar del
  formulario (R6).

### Mapa de tests

| Escenario / requisito | Test | Archivo |
|---|---|---|
| FR-001, US3 Esc. 6 — vistas requieren sesión | `test_vistas_gestion_pruebas_requieren_sesion` (parametrizado por ruta y método) | `test_gestion_pruebas.py` |
| US1 Esc. 1, FR-002 — detalle muestra cabecera, pruebas y acción agregar | `test_detalle_muestra_cabecera_pruebas_y_acciones` | `test_gestion_pruebas.py` |
| R1 — mensaje de éxito de US 5.1 enlaza al detalle | `test_exito_creacion_enlaza_al_detalle` | `test_gestion_pruebas.py` |
| US1 Esc. 2, FR-004 — catálogo sin las ya asignadas | `test_agregar_ofrece_solo_pruebas_no_asignadas` | `test_gestion_pruebas.py` |
| US1 Esc. 3, FR-008, SC-005 — revisar muestra confirmación con Cancelar y no guarda | `test_revisar_muestra_confirmacion_sin_guardar` | `test_gestion_pruebas.py` |
| US1 Esc. 4, FR-006/012 — confirmar agrega una vez como pendiente | `test_confirmar_agrega_prueba_una_vez`, `test_agregar_prueba_crea_asignacion` | `test_gestion_pruebas.py`, `test_servicio_pruebas.py` |
| US1 Esc. 5, FR-011, edge cases — cabecera, snapshots, tipo y otros estudios no cambian | `test_agregar_no_modifica_cabecera_tipo_ni_otros_estudios`, `test_quitar_no_modifica_cabecera_tipo_ni_otros_estudios` | `test_servicio_pruebas.py` |
| US2 Esc. 1 — acción quitar en cada prueba quitable | `test_detalle_ofrece_quitar_en_pruebas_quitables` | `test_gestion_pruebas.py` |
| US2 Esc. 2, FR-008, SC-005 — GET quitar muestra confirmación con Cancelar y no borra | `test_quitar_get_muestra_confirmacion_sin_borrar` | `test_gestion_pruebas.py` |
| US2 Esc. 3–4, FR-010 — confirmar quita la asignación | `test_confirmar_quita_prueba`, `test_quitar_prueba_borra_asignacion` | `test_gestion_pruebas.py`, `test_servicio_pruebas.py` |
| US2 Esc. 5 — prueba quitada vuelve a ofrecerse y puede re-agregarse | `test_prueba_quitada_puede_agregarse_de_nuevo` | `test_servicio_pruebas.py` |
| US3 Esc. 1, FR-005/009 — prueba ya asignada se rechaza (formulario y servicio) | `test_revisar_prueba_ya_asignada_da_error_en_campo`, `test_agregar_prueba_ya_asignada_rechazada` | `test_gestion_pruebas.py`, `test_servicio_pruebas.py` |
| US3 Esc. 2, FR-007 — no se quita si `puede_quitarse()` es falso | `test_quitar_rechaza_prueba_con_mediciones` (monkeypatch del método) | `test_servicio_pruebas.py` |
| US3 Esc. 3, FR-003 — estudio no modificable rechaza agregar y quitar | `test_estudio_no_modificable_rechaza_cambios`, `test_vistas_estudio_no_modificable_redirigen` (monkeypatch de `admite_modificaciones`) | `test_servicio_pruebas.py`, `test_gestion_pruebas.py` |
| US3 Esc. 4, FR-013 — reenvío de agregar y de quitar se informa como ya aplicado | `test_reenvio_confirmar_agregar_no_duplica`, `test_reenvio_confirmar_quitar_informa_ya_quitada` | `test_gestion_pruebas.py` |
| US3 Esc. 5, FR-014 — última prueba no se quita ni se ofrece | `test_ultima_prueba_no_se_puede_quitar`, `test_detalle_no_ofrece_quitar_ultima_prueba` | `test_servicio_pruebas.py`, `test_gestion_pruebas.py` |
| US3 Esc. 7 — estudio inexistente 404; prueba inexistente; asignación de otro estudio o inexistente | `test_estudio_inexistente_responde_404`, `test_agregar_prueba_inexistente_rechazada`, `test_quitar_asignacion_de_otro_estudio_rechazada` | `test_gestion_pruebas.py` |
| Edge — agregados simultáneos de la misma prueba dejan una sola asignación | `test_agregados_concurrentes_no_duplican` (`transaction=True`, hilos) | `test_concurrencia_pruebas.py` |
| Edge — quitas simultáneas no dejan el estudio vacío ni quitan dos veces la misma prueba | `test_quitas_concurrentes_conservan_una_prueba`, `test_quitas_concurrentes_misma_asignacion` (`transaction=True`, hilos) | `test_concurrencia_pruebas.py` |
| Edge — todas las pruebas del catálogo ya asignadas | `test_agregar_sin_pruebas_disponibles_informa` | `test_gestion_pruebas.py` |
| R5 — reglas del modelo | `test_admite_modificaciones_solo_pendiente_analisis`, `test_puede_quitarse_sin_mediciones` | `test_modelos.py` |
| R8 — falla de base no informa éxito ni cambia nada | `test_error_de_base_al_agregar_no_cambia_estudio` | `test_gestion_pruebas.py` |

## Project Structure

### Documentation (this feature)

```text
specs/009-gestionar-pruebas-estudio/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── pruebas-estudio-ui.md
├── checklists/
│   └── requirements.md
└── tasks.md             # lo genera /speckit-tasks
```

### Source Code (repository root)

```text
CLAUDE.md                                   # + nota para US 6.1 (puede_quitarse, PROTECT) y US 5.2 (ampliar detalle)
estudios/
├── models.py                               # + Estudio.admite_modificaciones, PruebaEstudio.puede_quitarse()
├── servicios.py                            # + GestionPruebasError y subclases, agregar_prueba, quitar_prueba
├── forms.py                                # + AgregarPruebaForm
├── views.py                                # + detalle, agregar_prueba, quitar_prueba; exito con enlace
├── urls.py                                 # + <int:pk>/, <int:pk>/pruebas/agregar/, <int:pk>/pruebas/<int:asignacion_pk>/quitar/
├── templates/estudios/
│   ├── detalle.html                        # nuevo
│   ├── agregar_prueba.html                 # nuevo
│   ├── agregar_prueba_confirmar.html       # nuevo
│   └── quitar_prueba_confirmar.html        # nuevo
└── tests/
    ├── conftest.py                         # + estudio con pruebas asignadas, pruebas extra del catálogo
    ├── test_modelos.py                     # + reglas del modelo
    ├── test_servicio_pruebas.py            # nuevo
    ├── test_gestion_pruebas.py             # nuevo
    └── test_concurrencia_pruebas.py        # nuevo
```

**Structure Decision**: todo dentro de la app `estudios`, dueña de `Estudio` y `PruebaEstudio`
(una app por módulo, Principio II). `pruebas` y `muestras` no cambian. Los servicios se suman a
`estudios/servicios.py` junto a `crear_estudio`, con excepciones propias para no mezclarlas con
`CrearEstudioError`.

## Complexity Tracking

Sin violaciones de la constitution.
