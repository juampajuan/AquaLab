# Inventario de futuro commit — US 5.5 (012)

Fecha: 28/10/2026. Rama codex/012-gestionar-tipos-estudio, base a95efb46. Inventario propuesto, sin staging ni commit. Incluye este inventario y cierre-tecnico.md. Cualquier cambio posterior requiere contrastar nuevamente esta lista.

**Total exacto: 30 archivos.**

| # | Archivo relativo al repositorio | Clasificación |
|---|---|---|
| 1 | `.dockerignore` | Exclusión de respaldos |
| 2 | `.gitignore` | Exclusión de respaldos |
| 3 | `estudios/confirmaciones_tipos.py` | Servicio/formularios/confirmaciones/rutas |
| 4 | `estudios/forms_tipos.py` | Servicio/formularios/confirmaciones/rutas |
| 5 | `estudios/gestion_tipos.py` | Servicio/formularios/confirmaciones/rutas |
| 6 | `estudios/templates/estudios/tipos/confirmar.html` | UI/navegación |
| 7 | `estudios/templates/estudios/tipos/conflicto.html` | UI/navegación |
| 8 | `estudios/templates/estudios/tipos/formulario.html` | UI/navegación |
| 9 | `estudios/templates/estudios/tipos/lista.html` | UI/navegación |
| 10 | `estudios/tests/conftest.py` | Tests/fixtures |
| 11 | `estudios/tests/test_gestion_tipos_concurrencia.py` | Tests/fixtures |
| 12 | `estudios/tests/test_gestion_tipos_confirmaciones.py` | Tests/fixtures |
| 13 | `estudios/tests/test_gestion_tipos_servicio.py` | Tests/fixtures |
| 14 | `estudios/tests/test_gestion_tipos_ui.py` | Tests/fixtures |
| 15 | `estudios/urls.py` | Servicio/formularios/confirmaciones/rutas |
| 16 | `estudios/views_tipos.py` | Servicio/formularios/confirmaciones/rutas |
| 17 | `specs/012-gestionar-tipos-estudio/checklists/requirements.md` | Documentación US 5.5 |
| 18 | `specs/012-gestionar-tipos-estudio/cierre-tecnico.md` | Documentación US 5.5 |
| 19 | `specs/012-gestionar-tipos-estudio/contracts/gestion-tipos-servicio.md` | Documentación US 5.5 |
| 20 | `specs/012-gestionar-tipos-estudio/contracts/gestion-tipos-ui.md` | Documentación US 5.5 |
| 21 | `specs/012-gestionar-tipos-estudio/data-model.md` | Documentación US 5.5 |
| 22 | `specs/012-gestionar-tipos-estudio/diagnostico-previo-plan.md` | Documentación US 5.5 |
| 23 | `specs/012-gestionar-tipos-estudio/inventario-commit.md` | Documentación US 5.5 |
| 24 | `specs/012-gestionar-tipos-estudio/plan.md` | Documentación US 5.5 |
| 25 | `specs/012-gestionar-tipos-estudio/quickstart.md` | Documentación US 5.5 |
| 26 | `specs/012-gestionar-tipos-estudio/research.md` | Documentación US 5.5 |
| 27 | `specs/012-gestionar-tipos-estudio/spec.md` | Documentación US 5.5 |
| 28 | `specs/012-gestionar-tipos-estudio/tasks.md` | Documentación US 5.5 |
| 29 | `templates/base.html` | UI/navegación |
| 30 | `templates/inicio.html` | UI/navegación |

## Excluidos y revisión

.local-backups/ (todos los respaldos, preservados); .env (configuración/credenciales QA); .pytest_cache/; .ruff_cache/; .specify/feature.json (contexto local ignorado). También excluir cualquier __pycache__, logs, temporales o dumps de base que aparezcan. Volúmenes PostgreSQL, sesiones y datos DEMO QA no son archivos del repositorio y no se exportaron. Ninguna contraseña QA se incluye; passwords sintéticos de fixtures son exclusivamente de test.

Los únicos seis archivos versionados modificados son .gitignore, .dockerignore, estudios/tests/conftest.py, estudios/urls.py, templates/base.html y templates/inicio.html. Son cambios deliberados de US 5.5. Los otros archivos de esta lista son nuevos/sin seguimiento. No hay modificaciones ajenas que deban descartarse ni archivos existentes que eliminar.

Verificados modelos/migraciones, muestras, servicios/catalogo/views existentes, specs de otras historias, Constitution e instalación Spec Kit sin diff. No se modifican otros worktrees. Staging vacío. Antes de un futuro commit usar solo esta lista y volver a revisar diff/secretos; este documento no ejecuta git add.
