# Implementation Plan: Buscar cliente registrado

**Branch**: `004-buscar-cliente` | **Date**: 2026-10-22 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/004-buscar-cliente/spec.md` (US 3.1 / SCRUM-44)

## Summary

Pantalla de búsqueda de clientes para empleados con sesión activa: un único campo `q` enviado por
**GET** a `/clientes/buscar/`. La consulta filtra `Cliente` con `activo=True` y combina (OR) una
coincidencia parcial `icontains` **sin distinguir mayúsculas ni tildes** sobre `nombre` y
`razon_social`, y una coincidencia parcial sobre `numero_documento` usando el texto normalizado
(sin espacios, puntos ni guiones) cuando este es solo dígitos. La validación del texto (mínimo 2
caracteres, no vacío) vive en un `Form` de Django. Los resultados se ordenan con el `ordering` ya
definido en el modelo y se paginan de a 20. Cada resultado enlaza a la ficha existente
`clientes:detalle` (`/clientes/<id>/`), cuyo `pk` identifica al cliente de forma inequívoca para
otros flujos. No hay modelo ni tabla nuevos: solo una migración que habilita la extensión
`unaccent` de PostgreSQL.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: Django 5.2 LTS (ORM, forms, `Paginator`, messages), Bootstrap 5.3 (CDN,
en `base.html`). `django.contrib.postgres` (ya incluido en Django) para el lookup `unaccent`.
Sin dependencias nuevas de pip.

**Storage**: PostgreSQL 16 en Docker (`DATABASE_URL`). Sin tablas ni columnas nuevas. Una migración
`clientes/migrations/0002_unaccent.py` con `UnaccentExtension()`. La búsqueda no se persiste.

**Testing**: pytest-django con el test client; ruff (lint + format).

**Target Platform**: Contenedor Linux (`web`) con Docker Compose; navegador de escritorio.

**Project Type**: Aplicación web Django monolítica con templates en el servidor (sin SPA).

**Performance Goals**: Resultados en menos de 2 s (SC-006) con cientos de clientes.

**Constraints**: Sesión activa obligatoria (FR-001, Principio V; la cubre `LoginRequiredMiddleware`);
solo clientes `activo=True`; validación en el formulario, no solo en el template (Principio IV);
textos en español (Principio VI); alcance limitado a buscar/listar/consultar (FR-013).

**Scale/Scope**: 0 modelos nuevos, 1 vista nueva (`buscar`), 1 formulario, 1 template, 1 migración
de extensión, ajuste menor de `detalle` y enlaces de navegación.

Decisiones documentadas en [research.md](./research.md). No hay `NEEDS CLARIFICATION` pendientes.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Cumplimiento | Estado |
|---|---|---|
| **I. Spec primero (SDD)** | Spec con US 3.1 / SCRUM-44 en `specs/004-buscar-cliente/spec.md`. El PR se titulará `"US 3.1 – Buscar cliente registrado"` y referenciará la spec. | ✅ |
| **II. Simplicidad y Django idiomático** | ORM + `Form` + `Paginator` + templates de servidor, en la app `clientes`. `unaccent` viene con `django.contrib.postgres` (parte de Django), sin dependencia nueva. Sin servicios ni capas extra. | ✅ |
| **III. Tests obligatorios** | Cada escenario de aceptación (US1 1–7, US2 1–2) y cada caso límite tendrá test en `clientes/tests/test_busqueda.py` (ver [quickstart.md](./quickstart.md)). | ✅ |
| **IV. Integridad de datos** | Solo lectura; no modifica ni borra clientes. Respeta la baja lógica filtrando `activo=True`. Validación del texto en el `Form`. | ✅ |
| **V. Seguridad** | Vista protegida por `LoginRequiredMiddleware`. Búsqueda por GET sin efectos secundarios (no requiere CSRF). El texto se pasa al ORM parametrizado y se escapa en el template. | ✅ |
| **VI. Idioma y consistencia** | Interfaz y mensajes en español; nombres de dominio: `Cliente`, `buscar`, `BuscarClienteForm`. | ✅ |

**Post-diseño (Phase 1)**: sin cambios; sigue cumpliendo todos los principios. Sin violaciones, por
lo que no se completa *Complexity Tracking*.

## Project Structure

### Documentation (this feature)

```text
specs/004-buscar-cliente/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── busqueda-cliente-ui.md
└── tasks.md             # lo genera /speckit-tasks
```

### Source Code (repository root)

```text
clientes/
├── forms.py                         # + BuscarClienteForm
├── views.py                         # + buscar(); detalle() maneja cliente inactivo
├── urls.py                          # + path("buscar/", views.buscar, name="buscar")
├── migrations/
│   └── 0002_unaccent.py             # UnaccentExtension()
├── templates/clientes/
│   ├── buscar.html                  # nuevo: formulario GET + resultados + paginación
│   └── detalle.html                 # + enlace "Volver a la búsqueda"
└── tests/
    └── test_busqueda.py             # nuevo

config/settings.py                   # + "django.contrib.postgres" en INSTALLED_APPS
templates/base.html                  # + enlace "Buscar cliente" en la navbar
templates/inicio.html                # + botón "Buscar cliente"
```

**Structure Decision**: Se extiende la app `clientes` existente (Principio II: una app por módulo).
La lógica de filtrado queda en la vista/formulario; no se crea capa de servicios (YAGNI).

## Complexity Tracking

Sin violaciones de la constitution.
