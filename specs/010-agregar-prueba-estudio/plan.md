# Implementation Plan: Agregar prueba al estudio

**Branch**: `010-agregar-prueba-estudio` | **Date**: 2026-10-27 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/010-agregar-prueba-estudio/spec.md` (US 5.3)

## Summary

Agregado de pruebas a un estudio creado en US 5.1, dentro de la app `estudios` y sin cambios de
esquema. Un detalle mínimo del estudio (`/estudios/<pk>/`), enlazado desde el mensaje de éxito de la
creación, muestra la cabecera y las pruebas asignadas y ofrece **agregar** una prueba del catálogo
que el estudio no tenga (formulario → confirmación → guardar). El servicio `agregar_prueba` bloquea
la fila del estudio, revalida que esté en «Pendiente de análisis» y que la prueba no esté asignada, y
solo crea una fila de `PruebaEstudio`. La regla de estudio modificable vive en el modelo
(`Estudio.admite_modificaciones`). US 5.4 se construye sobre este detalle, esta regla y la excepción
`GestionPruebasError`.

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

**Performance Goals**: Agregar una prueba en menos de 1 minuto con una sola confirmación (SC-005).
Volumen chico: decenas de pruebas por catálogo y por estudio.

**Constraints**: Confirmación antes de guardar (FR-007, sección Interfaz); revalidación bajo
bloqueo de la fila del estudio (FR-005, FR-008); reenvío idempotente (FR-011); la cabecera, los
snapshots y el catálogo no cambian (FR-009); sesión obligatoria (FR-001); textos en español
(Principio VI).

**Scale/Scope**: 1 servicio + 2 excepciones, 1 propiedad de modelo, 1 formulario, 2 vistas,
3 templates, 2 URLs, cambio de texto en `exito` de US 5.1, nota en `CLAUDE.md` y tests en
`estudios/tests/`.

Decisiones documentadas en [research.md](./research.md) (R1–R6). No hay `NEEDS CLARIFICATION`
pendientes.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Cumplimiento | Estado |
|---|---|---|
| **I. Spec primero (SDD)** | Spec de US 5.3 en `specs/010-agregar-prueba-estudio/spec.md`, una US por spec y por rama, como pidió el equipo. El código espera la aprobación de la spec (T001). PR: «US 5.3 – Agregar prueba al estudio». | ✅ (aprobación pendiente antes de implementar) |
| **II. Simplicidad y Django idiomático** | Vistas de función, `forms.Form`, `messages` y ORM, como en US 5.1. Confirmación con campo oculto revalidado en vez de borrador en sesión (R2). Sin JavaScript, dependencias ni modelos nuevos. | ✅ |
| **III. Tests obligatorios** | Cada escenario de aceptación (US1 1–5, US2 1–5), FR y caso límite tiene test (ver [Mapa de tests](#mapa-de-tests)). Sin cálculos de resultados en esta historia. | ✅ |
| **IV. Integridad de datos** | `UniqueConstraint(estudio, prueba)` ya existente más comprobación bajo bloqueo de fila. Regla de estudio modificable en el modelo y el servicio, no solo en el template. Snapshots y catálogo intactos. No se borra nada. | ✅ |
| **V. Seguridad** | Vistas protegidas por `LoginRequiredMiddleware`; CSRF en todos los POST. El enlace del mensaje se arma con `format_html`, que escapa los datos. | ✅ |
| **VI. Idioma y consistencia** | Términos del dominio: `Estudio`, `Prueba`, `PruebaEstudio`, `agregar_prueba`, `admite_modificaciones`. Interfaz y mensajes en español. ruff. | ✅ |
| **Interfaz (UI)** | Extiende `base.html`, Bootstrap 5.3, error junto al campo, confirmación antes de agregar, mensajes con `messages`. | ✅ |

**Post-diseño (Phase 1)**: cumple todos los principios sin excepciones en *Complexity Tracking*.

## Diseño

### Flujo

```text
GET  /estudios/<pk>/                       → detalle (404 si no existe)

GET  /estudios/<pk>/pruebas/agregar/       → formulario con catálogo sin las asignadas
POST accion=revisar                        → inválido: 200 con error en el campo
                                           → válido: 200 confirmación (prueba oculta)
POST accion=confirmar                      → agregar_prueba() → 302 detalle + mensaje
```

Rutas, condiciones y mensajes exactos en
[contracts/agregar-prueba-ui.md](./contracts/agregar-prueba-ui.md); reglas en
[data-model.md](./data-model.md).

### Servicio (`estudios/servicios.py`)

```text
GestionPruebasError(Exception)          # mensaje = texto para el empleado; US 5.4 suma subclases
└── PruebaYaAsignada                    # reenvío o agregado simultáneo (se informa como aviso)

agregar_prueba(estudio_pk, prueba_pk, usuario) -> PruebaEstudio
```

Sesión activa → `transaction.atomic()` → `select_for_update()` del estudio →
`admite_modificaciones` → prueba existente y no asignada → crear la `PruebaEstudio` (R3).

### Formulario `AgregarPruebaForm(forms.Form)`

- `__init__(self, *args, estudio, **kwargs)`: `prueba = ModelChoiceField(Prueba.objects.exclude(
  pk__in=estudio.pruebas_asignadas.values("prueba")), empty_label="Elegí una prueba")`, clase
  `form-select` e `is-invalid` como en `CrearEstudioForm`.
- La vista pasa al template si el queryset está vacío, para mostrar la alerta en lugar del
  formulario (R5).

### Mapa de tests

| Escenario / requisito | Test | Archivo |
|---|---|---|
| FR-001, US2 Esc. 4 — vistas requieren sesión | `test_vistas_agregar_prueba_requieren_sesion` (parametrizado por ruta y método) | `test_agregar_prueba.py` |
| US1 Esc. 1, FR-002 — detalle muestra cabecera, pruebas y acción agregar | `test_detalle_muestra_cabecera_pruebas_y_accion_agregar` | `test_agregar_prueba.py` |
| R1 — mensaje de éxito de US 5.1 enlaza al detalle | `test_exito_creacion_enlaza_al_detalle` | `test_agregar_prueba.py` |
| US1 Esc. 2, FR-004 — catálogo sin las ya asignadas | `test_agregar_ofrece_solo_pruebas_no_asignadas` | `test_agregar_prueba.py` |
| US1 Esc. 3, FR-007, SC-004 — revisar muestra confirmación con Cancelar y no guarda | `test_revisar_muestra_confirmacion_sin_guardar` | `test_agregar_prueba.py` |
| US1 Esc. 4, FR-006/010 — confirmar agrega una vez como pendiente | `test_confirmar_agrega_prueba_una_vez`, `test_agregar_prueba_crea_asignacion` | `test_agregar_prueba.py`, `test_servicio_pruebas.py` |
| US1 Esc. 5, FR-009, edge cases — cabecera, snapshots, tipo y otros estudios no cambian | `test_agregar_no_modifica_cabecera_tipo_ni_otros_estudios` | `test_servicio_pruebas.py` |
| US2 Esc. 1, FR-005/008 — prueba ya asignada se rechaza (formulario y servicio) | `test_revisar_prueba_ya_asignada_da_error_en_campo`, `test_agregar_prueba_ya_asignada_rechazada` | `test_agregar_prueba.py`, `test_servicio_pruebas.py` |
| US2 Esc. 2, FR-003 — estudio no modificable rechaza agregar | `test_estudio_no_modificable_rechaza_agregar`, `test_vistas_estudio_no_modificable_no_ofrecen_agregar` (monkeypatch de `admite_modificaciones`) | `test_servicio_pruebas.py`, `test_agregar_prueba.py` |
| US2 Esc. 3, FR-011 — reenvío se informa como ya aplicado | `test_reenvio_confirmar_agregar_no_duplica` | `test_agregar_prueba.py` |
| US2 Esc. 5 — estudio inexistente 404; prueba inexistente | `test_estudio_inexistente_responde_404`, `test_agregar_prueba_inexistente_rechazada` | `test_agregar_prueba.py` |
| Edge — agregados simultáneos de la misma prueba dejan una sola asignación | `test_agregados_concurrentes_no_duplican` (`transaction=True`, hilos) | `test_concurrencia_pruebas.py` |
| Edge — todas las pruebas del catálogo ya asignadas | `test_agregar_sin_pruebas_disponibles_informa` | `test_agregar_prueba.py` |
| R4 — regla del modelo | `test_admite_modificaciones_solo_pendiente_analisis` | `test_modelos.py` |
| R6 — falla de base no informa éxito ni cambia nada | `test_error_de_base_al_agregar_no_cambia_estudio` | `test_agregar_prueba.py` |

## Project Structure

### Documentation (this feature)

```text
specs/010-agregar-prueba-estudio/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── agregar-prueba-ui.md
├── checklists/
│   └── requirements.md
└── tasks.md
```

### Source Code (repository root)

```text
CLAUDE.md                                   # + nota: detalle compartido con US 5.4 y US 5.2
estudios/
├── models.py                               # + Estudio.admite_modificaciones
├── servicios.py                            # + GestionPruebasError, PruebaYaAsignada, agregar_prueba
├── forms.py                                # + AgregarPruebaForm
├── views.py                                # + detalle, agregar_prueba; exito con enlace
├── urls.py                                 # + <int:pk>/, <int:pk>/pruebas/agregar/
├── templates/estudios/
│   ├── detalle.html                        # nuevo
│   ├── agregar_prueba.html                 # nuevo
│   └── agregar_prueba_confirmar.html       # nuevo
└── tests/
    ├── conftest.py                         # + estudio, prueba_extra
    ├── test_modelos.py                     # + regla del modelo
    ├── test_servicio_pruebas.py            # nuevo
    ├── test_agregar_prueba.py              # nuevo
    └── test_concurrencia_pruebas.py        # nuevo
```

**Structure Decision**: todo dentro de la app `estudios`, dueña de `Estudio` y `PruebaEstudio`
(una app por módulo, Principio II). `pruebas` y `muestras` no cambian. El servicio se suma a
`estudios/servicios.py` junto a `crear_estudio`, con excepciones propias para no mezclarlas con
`CrearEstudioError`. Los archivos `test_servicio_pruebas.py` y `test_concurrencia_pruebas.py` los
amplía US 5.4.

## Complexity Tracking

Sin violaciones de la constitution.
