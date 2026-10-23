# Implementation Plan: Editar cliente

**Branch**: `005-editar-cliente` | **Date**: 2026-10-23 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/005-editar-cliente/spec.md` (US 3.2 / SCRUM-45)

## Summary

Edición de los datos de un cliente activo desde su ficha (`clientes:detalle`) para empleados con
sesión iniciada. Permite modificar todos los datos del cliente (`nombre`, `razon_social`,
`tipo_documento`, `numero_documento`, `email`, `telefono` y `domicilio`) reutilizando la validación
y normalización de `RegistroClienteForm` (`EditarClienteForm`) y excluyendo al propio cliente al
comprobar unicidad de `(tipo_documento, numero_documento)`. Sigue el flujo de dos pasos en el
servidor: formulario precargado (`/clientes/<pk>/editar/`) → revisión y confirmación con borrador en
sesión (`request.session[f"cliente_edicion_{pk}"]` en `/clientes/<pk>/editar/confirmar/`) →
actualización transaccional e idempotente del `Cliente` y redirección a su ficha (`/clientes/<pk>/`).

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: Django 5.2 LTS (auth, sessions, messages, forms, ORM), Bootstrap 5.3
(CDN, en `base.html`). Sin dependencias nuevas.

**Storage**: PostgreSQL 16 en Docker (`DATABASE_URL`), tabla `clientes_cliente`. Borrador de revisión
en la sesión de Django (`request.session[f"cliente_edicion_{pk}"]`).

**Testing**: pytest-django con el test client de Django; ruff (lint + format).

**Target Platform**: Contenedor Linux (`web`) con Docker Compose; navegador de escritorio.

**Project Type**: Aplicación web Django monolítica con templates en el servidor (sin SPA).

**Performance Goals**: Completar la edición y confirmación en menos de 1 minuto (SC-001) y reflejar
los cambios de inmediato en la ficha y búsquedas (SC-002).

**Constraints**: Sesión activa obligatoria (FR-001, Principio V); solo clientes con `activo=True`
(FR-013, Principio IV); confirmación explícita antes de guardar cambios (FR-009, sección Interfaz de
la constitution); idempotencia ante confirmaciones repetidas (Escenario 8); textos y nombres del
dominio en español (Principio VI).

**Scale/Scope**: Extensión del formulario en `clientes/forms.py`, 2 vistas nuevas (`editar`,
`editar_confirmar`) y helper `actualizar_cliente`, 2 templates (`editar_form.html`,
`editar_confirmar.html`), botón `"Editar cliente"` en `detalle.html` y tests en
`clientes/tests/test_edicion.py`.

Decisiones documentadas en [research.md](./research.md) (R1–R4). No hay `NEEDS CLARIFICATION`
pendientes.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Cumplimiento | Estado |
|---|---|---|
| **I. Spec primero (SDD)** | Spec con US 3.2 / SCRUM-45 en `specs/005-editar-cliente/spec.md`. El PR se titulará `"US 3.2 – Editar cliente"` y referenciará la spec. | ✅ |
| **II. Simplicidad y Django idiomático** | Reutiliza `ModelForm`, sesiones, framework `messages` y el modelo `Cliente` en la app `clientes`. Sin dependencias ni capas extra. | ✅ |
| **III. Tests obligatorios** | Cada escenario de aceptación (1–8) y caso límite tendrá test en `clientes/tests/test_edicion.py` (ver [Mapa de tests](#mapa-de-tests)). | ✅ |
| **IV. Integridad de datos** | Validaciones en el formulario y en `Cliente.clean()`, respaldadas por `UniqueConstraint` y `CheckConstraint` en PostgreSQL. Respeta `activo=True`. | ✅ |
| **V. Seguridad** | Vistas protegidas por `LoginRequiredMiddleware`. Protección CSRF activa en todos los formularios POST. | ✅ |
| **VI. Idioma y consistencia** | Interfaz, mensajes y nombres de dominio (`Cliente`, `EditarClienteForm`, `editar`, `editar_confirmar`) en español. Formato con ruff. | ✅ |
| **Interfaz (UI)** | Extiende `templates/base.html`, usa Bootstrap 5.3, muestra errores por campo (`is-invalid` / `invalid-feedback`), pide confirmación antes de guardar y usa `messages`. | ✅ |

**Post-diseño (Phase 1)**: cumple todos los principios sin requerir excepciones en *Complexity
Tracking*.

## Diseño

### Flujo de edición de cliente

```text
GET  /clientes/<pk>/                        → ficha del cliente con botón [Editar cliente]
GET  /clientes/<pk>/editar/                 → limpia borrador previo y precarga formulario con datos vigentes
GET  /clientes/<pk>/editar/?volver=1        → precarga formulario con session[f"cliente_edicion_{pk}"]
POST /clientes/<pk>/editar/                 → inválido: 200 con errores y valores ingresados conservados
                                            → válido: session[f"cliente_edicion_{pk}"] = datos normalizados
                                              → 302 a /clientes/<pk>/editar/confirmar/
GET  /clientes/<pk>/editar/confirmar/       → resumen de cambios [Confirmar] [Volver y editar] [Cancelar]
POST accion=cancelar                        → borra session[f"cliente_edicion_{pk}"] → 302 a /clientes/<pk>/ + mensaje info
POST accion=confirmar                       → atomic: actualizar Cliente → borrar session[f"cliente_edicion_{pk}"]
                                              → session["ultimo_cliente_editado_id"] = cliente.pk
                                              → 302 a /clientes/<pk>/ + mensaje de éxito
```

Detalles en [contracts/edicion-cliente-ui.md](./contracts/edicion-cliente-ui.md).

### Mapa de tests

| Escenario / requisito | Test (en `clientes/tests/test_edicion.py`) |
|---|---|
| Esc. 1 — acceder a la edición desde la ficha precarga todos los datos vigentes del cliente | `test_get_editar_precarga_datos_vigentes_y_ficha_tiene_link` |
| Esc. 2 — modificar datos válidos y confirmar actualiza al cliente, informa éxito y refleja los cambios inmediatamente en su ficha | `test_confirmar_edicion_actualiza_cliente_y_refleja_en_detalle` |
| Esc. 3 — dejar vacíos nombre y razón social o quitar tipo/número de documento o correo indica faltantes y no modifica al cliente | `test_edicion_campos_obligatorios_faltantes_no_modifica` |
| Esc. 4 — formato inválido de correo, teléfono, DNI o CUIT solicita corrección y conserva valores ingresados | `test_edicion_formatos_invalidos_rechazados_y_conserva_datos` |
| Esc. 5 — cambiar documento por el de otro cliente existente (con o sin separadores) es rechazado | `test_edicion_documento_de_otro_cliente_rechazado` |
| Esc. 6 — mantener el mismo documento del propio cliente permite continuar y confirmar sin falso duplicado | `test_edicion_mismo_documento_propio_con_o_sin_separadores_permitido` |
| Esc. 7 — volver a editar o cancelar desde el formulario o la revisión no guarda cambios y mantiene los datos previos | `test_volver_y_editar_conserva_borrador_sin_modificar_bd`, `test_cancelar_en_confirmacion_borra_sesion_y_no_modifica_cliente` |
| Esc. 8 — confirmación repetida o colisión concurrente se maneja sin errores ni inconsistencias | `test_confirmacion_repetida_es_idempotente`, `test_integrity_error_al_confirmar_edicion_informa_duplicado` |
| FR-001 — vistas de edición requieren sesión activa | `test_vistas_edicion_requieren_sesion_activa` |
| FR-013 — cliente inactivo o inexistente no puede editarse | `test_editar_cliente_inactivo_redirige_con_advertencia`, `test_editar_cliente_inexistente_devuelve_404` |
| Edge cases — vaciar campos opcionales (`telefono`, `domicilio`) y error de base de datos al confirmar | `test_edicion_permite_vaciar_telefono_y_domicilio`, `test_error_de_base_al_confirmar_edicion_informa_sin_modificar` |

## Project Structure

### Documentation (this feature)

```text
specs/005-editar-cliente/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── edicion-cliente-ui.md
├── checklists/
│   └── requirements.md
└── tasks.md             # lo genera /speckit-tasks
```

### Source Code (repository root)

```text
clientes/
├── forms.py                         # + EditarClienteForm y exclusión de self.instance.pk en unicidad
├── views.py                         # + editar, editar_confirmar, actualizar_cliente, clave_sesion_edicion
├── urls.py                          # + <int:pk>/editar/ y <int:pk>/editar/confirmar/
├── templates/clientes/
│   ├── detalle.html                 # + botón "Editar cliente"
│   ├── editar_form.html             # nuevo
│   └── editar_confirmar.html        # nuevo
└── tests/
    └── test_edicion.py              # nuevo
```

**Structure Decision**: Se extiende la app `clientes` existente (Principio II: una app por módulo),
reutilizando el modelo `Cliente`, sus validadores y el patrón de formulario + confirmación en sesión.

## Complexity Tracking

Sin violaciones de la constitution.
