# Implementation Plan: Registrar cliente

**Branch**: `003-registrar-cliente` | **Date**: 2026-10-19 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/003-registrar-cliente/spec.md` (US 2.1 / SCRUM-43)

## Summary

Alta de clientes del laboratorio por parte de empleados con sesión activa. Se crea la nueva app de
Django `clientes` con el modelo `Cliente`, que admite identificación por nombre personal, razón
social o ambos (al menos uno obligatorio), tipo de documento (`DNI` o `CUIT`), número de documento
normalizado (sin espacios, puntos ni guiones) y validado según su tipo (DNI de 7 u 8 dígitos; CUIT
de 11 dígitos con validación módulo 11 de su dígito verificador), correo electrónico obligatorio y
teléfono y domicilio opcionales. La unicidad se garantiza por la combinación normalizada de
`(tipo_documento, numero_documento)` tanto en el formulario como mediante un `UniqueConstraint` en
PostgreSQL. El registro sigue el mismo flujo de dos pasos en el servidor que `usuarios`: formulario
→ **revisión y confirmación** (datos validados en `request.session["cliente_pendiente"]`) → creación
transaccional e idempotente y redirección a la **ficha del cliente** (`/clientes/<id>/`), donde se
consultan de inmediato todos los datos registrados.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: Django 5.2 LTS (auth, admin, sessions, messages, forms, ORM), Bootstrap
5.3 (CDN, en `base.html`). Sin dependencias nuevas para esta feature.

**Storage**: PostgreSQL 16 en Docker (`DATABASE_URL`). Una tabla nueva (`clientes_cliente`) con
`UniqueConstraint` sobre `(tipo_documento, numero_documento)` y `CheckConstraint` para exigir al
menos uno entre `nombre` y `razon_social`. Datos transitorios de revisión en la sesión de Django
(`request.session["cliente_pendiente"]`).

**Testing**: pytest-django con el test client de Django; ruff (lint + format).

**Target Platform**: Contenedor Linux (`web`) servido localmente con Docker Compose; navegador de
escritorio.

**Project Type**: Aplicación web Django monolítica con templates renderizados en el servidor (sin
SPA).

**Performance Goals**: Completar un alta válida en menos de 2 minutos (SC-001). Volumen esperado:
cientos de clientes.

**Constraints**: Acceso exclusivo con sesión activa (FR-001, Principio V); confirmación explícita
antes de guardar (FR-010, sección Interfaz de la constitution); idempotencia ante confirmaciones
repetidas (FR-012); textos y nombres del dominio en español (Principio VI).

**Scale/Scope**: 1 modelo nuevo (`Cliente`), 3 pantallas protegidas (formulario de alta, revisión y
confirmación, ficha de detalle del cliente) + registro en el admin de Django.

Todas las decisiones de diseño quedaron documentadas en [research.md](./research.md) (R1–R9). No hay
`NEEDS CLARIFICATION` pendientes.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Cumplimiento | Estado |
|---|---|---|
| **I. Spec primero (SDD)** | Spec aprobada con US 2.1 / SCRUM-43 en `specs/003-registrar-cliente/spec.md`. El PR deberá titularse `"US 2.1 – Registrar cliente"` y referenciar `specs/003-registrar-cliente/`. | ✅ |
| **II. Simplicidad y Django idiomático** | Se usa `ModelForm` / `Form` de Django, sesiones, framework de mensajes, `UniqueConstraint`, `CheckConstraint` y el admin de Django. Sin dependencias externas nuevas (validador de CUIT en Python puro, R3). Todo en la nueva app `clientes`. Nada fuera de alcance (sin edición, baja ni búsqueda avanzada, FR-015). | ✅ |
| **III. Tests obligatorios** | Al menos un test automatizado con pytest-django por cada escenario de aceptación 1–8 + tests unitarios de modelo, normalización, dígito verificador de CUIT y constraints (ver [Mapa de tests](#mapa-de-tests)). CI con pytest + ruff. | ✅ |
| **IV. Integridad de los datos del laboratorio** | Validaciones de reglas de negocio en formulario y en `Cliente.clean()`, respaldadas por `UniqueConstraint` y `CheckConstraint` en PostgreSQL (R2, R3, R4). Incluye `activo=True` para no borrar clientes con historial futuro. | ✅ |
| **V. Seguridad** | Todas las vistas de `clientes` requieren sesión activa mediante `LoginRequiredMiddleware` (sin `@login_not_required`, R9). Protección CSRF activa en todos los formularios. | ✅ |
| **VI. Idioma y consistencia** | Interfaz, mensajes de error y éxito, `verbose_name` y nombres del modelo (`Cliente`, `nombre`, `razon_social`, `tipo_documento`, `numero_documento`, `telefono`, `domicilio`, `activo`, `fecha_alta`) en español siguiendo el Glosario. Código formateado con ruff. | ✅ |
| **Interfaz (UI)** | Extiende `templates/base.html`, usa Bootstrap 5.3, muestra errores junto a cada campo (`is-invalid` / `invalid-feedback`), pide confirmación explícita antes de guardar y usa el framework `messages` de Django. | ✅ |

**Resultado**: sin violaciones. **Re-chequeo post-diseño (Phase 1)**: el diseño de
[data-model.md](./data-model.md) y [contracts/registro-cliente-ui.md](./contracts/registro-cliente-ui.md)
cumple todos los principios sin requerir excepciones en Complexity Tracking.

## Diseño

### Flujo de registro de cliente

```text
GET  /clientes/registrar/            → formulario vacío (o precargado si hay cliente_pendiente en sesión)
POST /clientes/registrar/            → inválido: 200 mismo formulario con errores y datos válidos conservados
                                     → válido: session["cliente_pendiente"] = datos normalizados
                                       → 302 a /clientes/registrar/confirmar/
GET  /clientes/registrar/confirmar/  → resumen de datos [Confirmar] [Volver y editar] [Cancelar]
POST accion=cancelar                 → borra session["cliente_pendiente"] → 302 a /clientes/registrar/
POST accion=confirmar                → atomic: crear Cliente(activo=True) → borrar cliente_pendiente
                                       → session["ultimo_cliente_creado_id"] = cliente.pk
                                       → 302 a /clientes/<pk>/ + mensaje de éxito
GET  /clientes/<pk>/                 → ficha con todos los datos registrados del cliente
```

Detalles de rutas, campos y mensajes exactos en
[contracts/registro-cliente-ui.md](./contracts/registro-cliente-ui.md).

### Componentes

| Archivo | Contenido |
|---|---|
| `config/settings.py` | Agregar `"clientes"` a `INSTALLED_APPS` |
| `config/urls.py` | Agregar `path("clientes/", include("clientes.urls"))` |
| `templates/inicio.html` | Enlace a `{% url 'clientes:registrar' %}` ("Registrar cliente") |
| `clientes/apps.py` | `ClientesConfig` (`name = "clientes"`, `verbose_name = "Clientes"`) |
| `clientes/models.py` | `TipoDocumento`, `Cliente`, `normalizar_numero_documento`, `es_cuit_valido`, `validar_documento`, `validar_telefono` |
| `clientes/migrations/0001_initial.py` | Migración inicial del modelo `Cliente` y sus constraints |
| `clientes/forms.py` | `RegistroClienteForm`: limpieza, normalización, validación cruzada (`nombre`/`razon_social`, `tipo_documento`/`numero_documento`, unicidad) y método `datos_para_sesion()` |
| `clientes/views.py` | `registrar`, `registrar_confirmar`, `detalle` y helper `crear_cliente(datos)` dentro de `transaction.atomic()` |
| `clientes/urls.py` | `app_name = "clientes"` y rutas `registrar/`, `registrar/confirmar/`, `<int:pk>/` |
| `clientes/admin.py` | `ClienteAdmin` (`list_display`, `list_filter`, `search_fields`, `readonly_fields`) |
| `clientes/templates/clientes/registro_form.html` | Formulario Bootstrap 5.3 con errores por campo y generales |
| `clientes/templates/clientes/registro_confirmar.html` | Resumen de revisión + botones Confirmar, Volver y editar, Cancelar |
| `clientes/templates/clientes/detalle.html` | Ficha de consulta del cliente con todos los datos registrados |

### Mapa de tests

| Escenario / requisito | Test (en `clientes/tests/`) |
|---|---|
| Esc. 1 — alta válida confirmada crea un único cliente e informa éxito | `test_registro.py::test_confirmar_crea_cliente_persona_con_dni`, `::test_confirmar_crea_cliente_empresa_con_cuit` |
| Esc. 2 — consultar el cliente recién creado muestra todos los datos registrados | `test_registro.py::test_detalle_muestra_todos_los_datos_registrados` |
| Esc. 3 — alta sin nombre/razón social, tipo/número de documento o correo electrónico indica faltantes y no crea el cliente | `test_registro.py::test_formulario_incompleto_no_avanza` (parametrizado por campo obligatorio y por ambos `nombre` + `razon_social` vacíos) |
| Esc. 4 — documento duplicado con espacios, puntos o guiones distintos es rechazado | `test_registro.py::test_documento_duplicado_con_separadores_rechazado` (parametrizado para DNI y CUIT con puntos, guiones y espacios) |
| Esc. 5 — correo electrónico o teléfono con formato inválido impide avanzar a confirmación | `test_registro.py::test_correo_invalido_rechazado`, `::test_telefono_invalido_rechazado` |
| Esc. 6 — volver a editar o cancelar desde la revisión no guarda el cliente | `test_registro.py::test_volver_y_editar_precarga_datos_sin_crear_cliente`, `::test_cancelar_borra_sesion_y_no_crea_cliente` |
| Esc. 7 — confirmación repetida o concurrente guarda un solo cliente | `test_registro.py::test_confirmacion_repetida_crea_un_solo_cliente`, `::test_integrity_error_al_confirmar_no_duplica_cliente` |
| Esc. 8 — DNI que no tiene 7 u 8 dígitos o CUIT sin 11 dígitos o con dígito verificador inválido es rechazado | `test_registro.py::test_dni_formato_invalido_rechazado`, `::test_cuit_formato_o_digito_verificador_invalido_rechazado` |
| FR-001 — vistas requieren sesión activa | `test_registro.py::test_vistas_requieren_sesion_activa` (GET/POST a `registrar`, `registrar_confirmar` y `detalle` sin sesión redirigen al login) |
| FR-009 — errores conservan los datos válidos ingresados | `test_registro.py::test_errores_conservan_datos_validos` |
| FR-013 / R8 — falla de base de datos al confirmar informa el error sin crear el cliente | `test_registro.py::test_error_de_base_al_confirmar_informa_sin_crear` |
| Edge cases — normalización de espacios laterales, documento y constraints en la base | `test_modelo.py::test_normaliza_campos_y_documento`, `::test_validador_cuit_modulo_11`, `::test_constraint_documento_unico`, `::test_constraint_nombre_o_razon_social_obligatorio` |

## Project Structure

### Documentation (this feature)

```text
specs/003-registrar-cliente/
├── spec.md
├── plan.md                          # Este archivo
├── research.md                      # Phase 0
├── data-model.md                    # Phase 1
├── quickstart.md                    # Phase 1
├── contracts/
│   └── registro-cliente-ui.md       # Phase 1
├── checklists/
│   └── requirements.md
└── tasks.md                         # Phase 2 (/speckit-tasks, próximo paso)
```

### Source Code (repository root)

```text
config/
├── settings.py                      # + "clientes" en INSTALLED_APPS
└── urls.py                          # + path("clientes/", include("clientes.urls"))
templates/
├── base.html                        # setup (sin cambios en esta feature)
└── inicio.html                      # + link/botón "Registrar cliente"
clientes/
├── __init__.py
├── apps.py
├── models.py                        # TipoDocumento, Cliente, normalización y validadores
├── migrations/
│   ├── __init__.py
│   └── 0001_initial.py
├── admin.py                         # ClienteAdmin
├── forms.py                         # RegistroClienteForm
├── views.py                         # registrar, registrar_confirmar, detalle, crear_cliente
├── urls.py                          # app_name = "clientes"
├── templates/clientes/
│   ├── registro_form.html
│   ├── registro_confirmar.html
│   └── detalle.html
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_modelo.py
    └── test_registro.py
```

**Structure Decision**: proyecto Django monolítico en la raíz del repositorio; la US 2.1 crea su
propia app `clientes/` siguiendo el Principio II de la constitution, con sus templates en
`clientes/templates/clientes/` y sus tests aislados en `clientes/tests/` para no generar conflictos
de merge con las ramas `001-registrar-usuario` ni `002-inicio-cierre-sesion`.

## Complexity Tracking

Sin excepciones a la constitution.
