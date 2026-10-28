# Implementation Plan: Consultar estado del estudio

**Branch**: `009-consultar-estado-estudio` | **Date**: 2026-10-27 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/009-consultar-estado-estudio/spec.md` (US 5.2 / SCRUM-49)

## Summary

Consulta de avance de estudios y de los estudios asignados a una muestra para empleados con sesión activa:
1. Se completan las opciones de `EstadoEstudio` (`Pendiente de análisis`, `En proceso`, `Finalizado`, `Informe generado`) y se agrega `EstadoPruebaEstudio` (`Pendiente`, `Cargada`, `Completada`) junto con el campo `estado` en `PruebaEstudio` (por defecto `Pendiente`).
2. Se incorpora el buscador unificado `GET /estudios/buscar/` (`estudios:buscar`) con `BuscarEstudioForm`: filtra estudios por identificador numérico exacto (`pk`), por muestra (`numero_pi` exacto o `nombre` con `unaccent__icontains`) o por cliente (`nombre` y `razon_social` con `unaccent__icontains`, o `numero_documento` normalizado), paginando de a 20 resultados ordenados del más reciente al más antiguo (`-pk`).
3. Se incorpora la vista de detalle del estudio `GET /estudios/<int:pk>/` (`estudios:detalle`), que muestra la cabecera completa del estudio (incluidos los snapshots históricos del tipo de estudio), su estado general, el resumen de avance y la tabla de pruebas asignadas con el estado individual de cada una.
4. Se incorpora la ficha de la muestra `GET /muestras/<int:pk>/` (`muestras:detalle`), que muestra todos los datos vigentes de la muestra y la lista de sus estudios asignados con su estado general, el conteo de pruebas completadas sobre el total y el enlace al detalle de cada estudio.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: Django 5.2 LTS (ORM, forms, `Paginator`, `django.contrib.postgres` para el lookup `unaccent`), Bootstrap 5.3 (CDN en `base.html`). Sin dependencias nuevas de pip.

**Storage**: PostgreSQL 16 en Docker (`DATABASE_URL`). Una migración `estudios/migrations/0003_estados_estudio_y_prueba.py` que amplía los choices de `Estudio.estado` y agrega `PruebaEstudio.estado` con valor por defecto `"pendiente"`.

**Testing**: pytest-django con el test client de Django; ruff (lint + format).

**Target Platform**: Contenedor Linux (`web`) con Docker Compose; navegador de escritorio.

**Project Type**: Aplicación web Django monolítica con templates renderizados en el servidor.

**Performance Goals**: Resultados de búsqueda y vistas de detalle en menos de 2 s (SC-005) mediante `select_related` y `annotate` sin consultas N+1.

**Constraints**: Sesión activa obligatoria (FR-001, Principio V; cubierta por `LoginRequiredMiddleware` y el guardia de sesión en `base.html`); validación del texto de búsqueda en el formulario (Principio IV); preservación de los snapshots históricos `tipo_nombre_snapshot` y `tipo_descripcion_snapshot` (US 5.1); textos e identificadores de dominio en español (Principio VI); alcance acotado a lectura y consulta (FR-015).

**Scale/Scope**: 1 migración en `estudios`, 1 formulario (`BuscarEstudioForm`), 2 vistas en `estudios` (`buscar`, `detalle`), 1 vista en `muestras` (`detalle`), 3 templates nuevos (`estudios/buscar.html`, `estudios/detalle.html`, `muestras/detalle.html`), enlaces en navegación y suite de tests en `estudios/tests/test_consulta.py` y `muestras/tests/test_detalle.py`.

Decisiones documentadas en [research.md](./research.md). No hay `NEEDS CLARIFICATION` pendientes.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Cumplimiento | Estado |
|---|---|---|
| **I. Spec primero (SDD)** | Spec de US 5.2 en `specs/009-consultar-estado-estudio/spec.md`. El PR se titulará `"US 5.2 – Consultar estado del estudio"` y referenciará la spec. | ✅ |
| **II. Simplicidad y Django idiomático** | ORM (`select_related`, `annotate`, `unaccent`) + `Form` + `Paginator` + templates de servidor en las apps existentes `estudios` y `muestras`. Sin dependencias ni capas extra. | ✅ |
| **III. Tests obligatorios** | Cada escenario de aceptación de US1 (1–7), US2 (1–4) y cada caso límite tendrá tests automatizados en `estudios/tests/test_consulta.py` y `muestras/tests/test_detalle.py` (ver [quickstart.md](./quickstart.md)). | ✅ |
| **IV. Integridad de datos** | Flujo de solo lectura; no modifica ni elimina muestras, estudios ni pruebas. Validación de la consulta en `BuscarEstudioForm` y constraints de modelo preservadas. | ✅ |
| **V. Seguridad** | Vistas protegidas por `LoginRequiredMiddleware` y guardia de sesión. Consultas por GET idempotentes y parametrizadas en el ORM; salida escapada en templates. | ✅ |
| **VI. Idioma y consistencia** | Interfaz, mensajes y código de dominio en español: `EstadoEstudio`, `EstadoPruebaEstudio`, `BuscarEstudioForm`, `buscar`, `detalle`. | ✅ |

**Post-diseño (Phase 1)**: sin cambios; sigue cumpliendo todos los principios de la constitución.

## Project Structure

### Documentation (this feature)

```text
specs/009-consultar-estado-estudio/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── consulta-estudio-ui.md
└── tasks.md             # lo genera /speckit-tasks
```

### Source Code (repository root)

```text
estudios/
├── models.py                        # + estados completos en EstadoEstudio, + EstadoPruebaEstudio y campo estado en PruebaEstudio
├── forms.py                         # + BuscarEstudioForm
├── views.py                         # + buscar(), + detalle()
├── urls.py                          # + path("buscar/", ...), + path("<int:pk>/", ...)
├── migrations/
│   └── 0003_estados_estudio_y_prueba.py
├── templates/estudios/
│   ├── buscar.html                  # nuevo: formulario GET + tabla de resultados + paginación
│   └── detalle.html                 # nuevo: cabecera del estudio + avance + tabla de pruebas asignadas
└── tests/
    ├── test_modelos.py              # actualiza aserción de choices de EstadoEstudio y cubre EstadoPruebaEstudio
    └── test_consulta.py             # nuevo: tests de búsqueda y detalle de estudio

muestras/
├── views.py                         # + detalle() (ficha de la muestra con estudios asignados)
├── urls.py                          # + path("<int:pk>/", views.detalle, name="detalle")
├── templates/muestras/
│   └── detalle.html                 # nuevo: datos vigentes de la muestra + tabla de estudios asignados
└── tests/
    └── test_detalle.py              # nuevo: tests de la ficha de la muestra y sus estudios

templates/base.html                  # + enlace "Buscar estudio" en la navbar
templates/inicio.html                # + botón "Buscar estudio"
```

**Structure Decision**: Se extienden las apps existentes `estudios` (búsqueda y detalle de estudio, estados de estudio y de prueba asignada) y `muestras` (ficha de la muestra con su listado de estudios asignados), respetando la separación de dominios por app (Principio II).

## Complexity Tracking

Sin violaciones de la constitution.
