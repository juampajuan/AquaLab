# Implementation Plan: Registrar muestra

**Branch**: `007-registrar-muestra` | **Date**: 2026-10-27 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/007-registrar-muestra/spec.md` (US 4.1 / SCRUM-47)

## Summary

Alta de muestras físicas para empleados con sesión iniciada, en una app nueva `muestras` con los
modelos `Origen` (fuente de agua de un cliente) y `Muestra`. El formulario (`/muestras/registrar/`)
elige el cliente en una lista de clientes activos filtrable al escribir (script propio, sin
dependencias) y muestra su ficha; el origen se elige entre los del cliente o se ingresa uno nuevo.
Sigue el flujo de dos pasos ya usado en `clientes`: formulario → resumen con borrador en sesión
(`session["muestra_pendiente"]`) → confirmación. Al confirmar, `registrar_muestra()` crea en una
sola transacción el origen nuevo (si hace falta) y la muestra, con el N° PI = máximo + 1 (desde
200001) calculado bajo un advisory lock de PostgreSQL, estado "Ingresada", usuario y fecha de
registro; luego vuelve al formulario vacío mostrando el N° PI.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: Django 5.2 LTS (auth, sessions, messages, forms, ORM, admin,
`django.contrib.postgres`), Bootstrap 5.3 (CDN, en `base.html`). JavaScript propio sin librerías
para el filtro de clientes. Sin dependencias nuevas.

**Storage**: PostgreSQL 16 en Docker (`DATABASE_URL`). Tablas nuevas `muestras_origen` y
`muestras_muestra`. Borrador de revisión en la sesión de Django.

**Testing**: pytest-django con el test client de Django; `node --test` para la lógica de filtrado
del script (mismo esquema que `usuarios/tests/js/`); ruff (lint + format).

**Target Platform**: Contenedor Linux (`web`) con Docker Compose; navegador de escritorio.

**Project Type**: Aplicación web Django monolítica con templates en el servidor (sin SPA).

**Performance Goals**: Registrar una muestra con origen conocido en menos de 1 minuto (SC-001). La
lista de clientes se filtra en el navegador al instante (cientos de clientes).

**Constraints**: N° PI único y consecutivo aun con registros simultáneos (FR-012, FR-013); origen y
muestra se guardan juntos o no se guarda nada (FR-018); confirmación con resumen antes de guardar
(FR-017, sección Interfaz); fechas según la zona del laboratorio (`America/Argentina/Buenos_Aires`);
sesión obligatoria (FR-001); textos y nombres del dominio en español (Principio VI).

**Scale/Scope**: App nueva `muestras` (2 modelos, 1 migración, formulario, servicio
`registrar_muestra`, 2 vistas, 2 templates, 1 script, admin de solo lectura) + enlaces en
`base.html` e `inicio.html` + tests en `muestras/tests/`.

Decisiones documentadas en [research.md](./research.md) (R1–R8). No hay `NEEDS CLARIFICATION`
pendientes.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Cumplimiento | Estado |
|---|---|---|
| **I. Spec primero (SDD)** | Spec con US 4.1 / SCRUM-47 en `specs/007-registrar-muestra/spec.md`, clarificada y commiteada. El PR se titulará `"US 4.1 – Registrar muestra"`. | ✅ |
| **II. Simplicidad y Django idiomático** | App `muestras` (prevista en la constitution). `Form`, sesiones, `messages`, admin y ORM de Django. El filtro de clientes es un script chico propio, con el formulario funcionando sin él; sin librerías nuevas. El advisory lock usa PostgreSQL, ya requerido por el proyecto. | ✅ |
| **III. Tests obligatorios** | Cada escenario de aceptación (US1 1–7, US2 1–5, US3 1–5), FR y caso límite tiene test (ver [Mapa de tests](#mapa-de-tests)). | ✅ |
| **IV. Integridad de datos** | N° PI único (`unique` + `CheckConstraint`) y asociado a cliente y origen. Origen único por cliente (constraint funcional con `Lower`). `CheckConstraint` de fechas. FK con `PROTECT` (nada con historial se borra). Validaciones en formulario y `Muestra.clean()`, no solo en el template ni en el script. Sin mediciones numéricas en esta historia (no aplica `Decimal`). | ✅ |
| **V. Seguridad** | Vistas protegidas por `LoginRequiredMiddleware`; CSRF en todos los POST. El `json_script` solo expone datos de clientes a empleados logueados (los mismos que ya ven en "Buscar cliente") y escapa el contenido. | ✅ |
| **VI. Idioma y consistencia** | Términos del glosario: `Muestra`, `Origen`, `Cliente`. Campos `numero_pi`, `fecha_muestreo`, `tipo_vertido`, etc. Interfaz y mensajes en español. ruff. | ✅ |
| **Interfaz (UI)** | Extiende `base.html`, Bootstrap 5.3, errores por campo, resumen y confirmación antes de guardar, mensajes con `messages`, enlace en la barra. | ✅ |

**Post-diseño (Phase 1)**: cumple todos los principios sin excepciones en *Complexity Tracking*.

## Diseño

### Flujo de registro de muestra

```text
GET  /muestras/registrar/              → descarta borrador; formulario con hoy/hoy/Agua
GET  /muestras/registrar/?volver=1     → precarga session["muestra_pendiente"]
POST /muestras/registrar/              → inválido: 200 con errores y valores conservados
                                       → válido: session["muestra_pendiente"] = datos normalizados
                                         → 302 a /muestras/registrar/confirmar/
GET  /muestras/registrar/confirmar/    → resumen [Confirmar] [Volver y editar] [Cancelar]
POST accion=cancelar                   → borra borrador → 302 a /muestras/registrar/ + info
POST accion=confirmar                  → atomic: advisory lock → revalidar → origen (get/crear)
                                         → numero_pi = max + 1 (o 200001) → crear Muestra
                                         → borra borrador, session["ultima_muestra_pi"] = n
                                         → 302 a /muestras/registrar/ + "Muestra registrada con N° PI n."
```

Detalles en [contracts/registro-muestra-ui.md](./contracts/registro-muestra-ui.md) y
[data-model.md](./data-model.md).

### Formulario `RegistroMuestraForm` (`forms.Form`)

- `cliente`: `ModelChoiceField(Cliente.objects.filter(activo=True))`, etiqueta
  `nombre_completo · TIPO número`.
- `origen`: `ModelChoiceField(required=False)`; en `__init__` su queryset se limita a
  `Origen.objects.filter(cliente_id=<cliente enviado o del borrador>)` (vacío si no hay cliente).
- `origen_nuevo`, `sitio_extraccion`, `nombre`, `responsable_muestreo`: `CharField` con `strip=True`.
- `fecha_muestreo`, `fecha_ingreso`: `DateField` con `DateInput(type="date")`,
  `initial=timezone.localdate`.
- `tipo_vertido`: `ChoiceField(TipoVertido.choices, initial="agua")`.
- `clean()`: regla "origen o origen nuevo, exactamente uno"; fechas ≤ hoy; muestreo ≤ ingreso;
  `nombre` vacío → `"Muestra 1"`.
- `datos_para_sesion()`: dict serializable (pks e ISO) como en `RegistroClienteForm`.
- Clases Bootstrap e `is-invalid` como en `clientes/forms.py`.

### Mapa de tests

| Escenario / requisito | Test | Archivo |
|---|---|---|
| FR-001 — vistas requieren sesión | `test_vistas_registro_muestra_requieren_sesion` | `test_registro.py` |
| US1 Esc. 1 — valores iniciales (hoy, hoy, Agua, vacíos) | `test_formulario_inicial_propone_hoy_y_agua` | `test_registro.py` |
| US1 Esc. 2, FR-002, FR-003 — solo clientes activos; datos del cliente para la ficha | `test_formulario_lista_solo_clientes_activos_con_sus_datos` | `test_registro.py` |
| US1 Esc. 2, Q2 — filtro por nombre, razón social o documento (tildes y separadores) | `filtra clientes por texto normalizado` | `js/registro_muestra.test.cjs` |
| US1 Esc. 3, FR-004 — orígenes del cliente elegido | `test_formulario_ofrece_solo_origenes_del_cliente` | `test_registro.py` |
| US1 Esc. 4, FR-017 — resumen con todos los datos | `test_post_valido_guarda_borrador_y_muestra_resumen` | `test_registro.py` |
| US1 Esc. 5, FR-012/014/015/019 — registra con PI = máx + 1, Ingresada, usuario, fecha; vuelve vacío con el PI | `test_confirmar_registra_muestra_con_pi_siguiente_y_datos_automaticos` | `test_registro.py` |
| US1 Esc. 6 — primera muestra → 200001 | `test_primera_muestra_recibe_pi_200001` | `test_servicio.py` |
| US1 Esc. 7 — volver conserva datos; cancelar no crea nada ni consume PI | `test_volver_y_editar_conserva_borrador`, `test_cancelar_no_registra_ni_consume_pi` | `test_registro.py` |
| US2 Esc. 1, FR-005 — origen nuevo se crea y se asocia | `test_confirmar_con_origen_nuevo_crea_origen_del_cliente` | `test_registro.py` |
| US2 Esc. 2–3 — origen nuevo disponible solo para su cliente | `test_origen_nuevo_disponible_solo_para_su_cliente` | `test_registro.py` |
| US2 Esc. 4, FR-006 — nombre repetido (mayúsculas/espacios) reutiliza el origen | `test_origen_nuevo_repetido_reutiliza_existente`, `test_constraint_origen_unico_por_cliente` | `test_servicio.py`, `test_modelos.py` |
| US2 Esc. 5 — cancelar con origen nuevo no lo crea | `test_cancelar_no_registra_ni_consume_pi` (con origen nuevo) | `test_registro.py` |
| US3 Esc. 1, FR-007/016 — faltantes indican el campo y conservan datos | `test_campos_obligatorios_faltantes_indican_cada_campo` (parametrizado) | `test_registro.py` |
| US3 Esc. 1, R4 — ni origen ni nuevo / ambos | `test_origen_o_origen_nuevo_exactamente_uno` | `test_registro.py` |
| US3 Esc. 2, Q1 — nombre vacío → "Muestra 1" | `test_nombre_vacio_se_registra_como_muestra_1` | `test_registro.py` |
| US3 Esc. 3, Q4 — responsable vacío o texto libre | `test_responsable_opcional_texto_libre` | `test_registro.py` |
| US3 Esc. 4, FR-009 — fechas futuras o muestreo > ingreso | `test_fechas_invalidas_rechazadas`, `test_constraint_fechas_muestra` | `test_registro.py`, `test_modelos.py` |
| US3 Esc. 5 — origen de otro cliente / cliente inactivo o inexistente | `test_origen_de_otro_cliente_rechazado`, `test_cliente_inactivo_o_inexistente_rechazado` | `test_registro.py` |
| FR-010 — tipo de vertido solo Agua/Cloacal/Canal | `test_tipo_vertido_fuera_de_opciones_rechazado` | `test_registro.py` |
| FR-013 — registros concurrentes no repiten PI | `test_registros_concurrentes_no_repiten_pi` (`transaction=True`, hilos) | `test_servicio.py` |
| FR-018 — falla al guardar no deja origen nuevo ni consume PI | `test_error_al_guardar_revierte_origen_y_pi` | `test_servicio.py` |
| Edge — doble confirmación registra una sola muestra | `test_confirmacion_repetida_registra_una_sola_muestra` | `test_registro.py` |
| Edge — cliente desactivado entre formulario y confirmación | `test_cliente_desactivado_antes_de_confirmar_no_registra` | `test_registro.py` |
| Edge — texto solo con espacios cuenta como vacío | `test_textos_solo_espacios_son_vacios` | `test_registro.py` |
| R8 — enlace "Registrar muestra" en la barra | `test_navbar_tiene_enlace_registrar_muestra` | `test_registro.py` |

## Project Structure

### Documentation (this feature)

```text
specs/007-registrar-muestra/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── registro-muestra-ui.md
├── checklists/
│   └── requirements.md
└── tasks.md             # lo genera /speckit-tasks
```

### Source Code (repository root)

```text
config/
├── settings.py                         # + "muestras" en INSTALLED_APPS
└── urls.py                             # + path("muestras/", include("muestras.urls"))
templates/
├── base.html                           # + enlace "Registrar muestra"
└── inicio.html                         # + botón "Registrar muestra"
muestras/                               # app nueva
├── __init__.py
├── apps.py
├── admin.py                            # Origen y Muestra, solo lectura de numero_pi/registro
├── models.py                           # Origen, Muestra, TipoVertido, EstadoMuestra
├── forms.py                            # RegistroMuestraForm
├── servicios.py                        # registrar_muestra, siguiente_numero_pi, MuestraNoDisponible
├── views.py                            # registrar, registrar_confirmar
├── urls.py                             # registrar/, registrar/confirmar/
├── migrations/
│   ├── __init__.py
│   └── 0001_initial.py
├── static/muestras/
│   └── registro_muestra.js             # filtro de clientes, ficha y orígenes
├── templates/muestras/
│   ├── registro_form.html
│   └── registro_confirmar.html
└── tests/
    ├── __init__.py
    ├── conftest.py                     # empleado, clientes, orígenes, datos válidos
    ├── test_modelos.py
    ├── test_servicio.py
    ├── test_registro.py
    └── js/
        └── registro_muestra.test.cjs
```

**Structure Decision**: app nueva `muestras`, como fija la constitution (una app por módulo).
`clientes` y `usuarios` no cambian; `muestras` depende de ellos por FK. La lógica de alta va en
`muestras/servicios.py` (transacción, lock y N° PI) para testearla aparte de las vistas, siguiendo la
idea de `crear_cliente` en `clientes/views.py` pero en su propio módulo porque es más extensa.

## Complexity Tracking

Sin violaciones de la constitution.
