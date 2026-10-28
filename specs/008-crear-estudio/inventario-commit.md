# Inventario exacto previsto para el commit local — US 5.1

Total: **50 archivos**; 4 existentes modificados y 46 nuevos. Rutas relativas a E:/Martino-Codex/AquaLab. Ningún archivo staged; no se ejecutó git add ni commit.

| Estado previsto | Archivo |
|---|---|
| Modificado | `config/settings.py` |
| Modificado | `config/urls.py` |
| Nuevo | `estudios/__init__.py` |
| Nuevo | `estudios/apps.py` |
| Nuevo | `estudios/catalogo.py` |
| Nuevo | `estudios/confirmaciones.py` |
| Nuevo | `estudios/forms.py` |
| Nuevo | `estudios/management/__init__.py` |
| Nuevo | `estudios/management/commands/__init__.py` |
| Nuevo | `estudios/management/commands/cargar_demo_us51.py` |
| Nuevo | `estudios/migrations/__init__.py` |
| Nuevo | `estudios/migrations/0001_initial.py` |
| Nuevo | `estudios/migrations/0002_estudio.py` |
| Nuevo | `estudios/models.py` |
| Nuevo | `estudios/servicios.py` |
| Nuevo | `estudios/templates/estudios/crear_confirmar.html` |
| Nuevo | `estudios/templates/estudios/crear_form.html` |
| Nuevo | `estudios/tests/__init__.py` |
| Nuevo | `estudios/tests/conftest.py` |
| Nuevo | `estudios/tests/test_catalogo_contrato.py` |
| Nuevo | `estudios/tests/test_concurrencia.py` |
| Nuevo | `estudios/tests/test_confirmaciones.py` |
| Nuevo | `estudios/tests/test_demo_us51.py` |
| Nuevo | `estudios/tests/test_modelos.py` |
| Nuevo | `estudios/tests/test_registro.py` |
| Nuevo | `estudios/tests/test_servicio.py` |
| Nuevo | `estudios/urls.py` |
| Nuevo | `estudios/views.py` |
| Nuevo | `pruebas/__init__.py` |
| Nuevo | `pruebas/apps.py` |
| Nuevo | `pruebas/migrations/__init__.py` |
| Nuevo | `pruebas/migrations/0001_initial.py` |
| Nuevo | `pruebas/models.py` |
| Nuevo | `pruebas/tests/__init__.py` |
| Nuevo | `pruebas/tests/test_modelo.py` |
| Nuevo | `specs/008-crear-estudio/checklists/requirements.md` |
| Nuevo | `specs/008-crear-estudio/cierre-tecnico.md` |
| Nuevo | `specs/008-crear-estudio/contracts/catalogo-compartido.md` |
| Nuevo | `specs/008-crear-estudio/contracts/crear-estudio-ui.md` |
| Nuevo | `specs/008-crear-estudio/data-model.md` |
| Nuevo | `specs/008-crear-estudio/inventario-commit.md` |
| Nuevo | `specs/008-crear-estudio/plan.md` |
| Nuevo | `specs/008-crear-estudio/propuesta-datos-demo.md` |
| Nuevo | `specs/008-crear-estudio/quickstart.md` |
| Nuevo | `specs/008-crear-estudio/research.md` |
| Nuevo | `specs/008-crear-estudio/sources/notas-reunion-2026-10-26.txt` |
| Nuevo | `specs/008-crear-estudio/spec.md` |
| Nuevo | `specs/008-crear-estudio/tasks.md` |
| Modificado | `templates/base.html` |
| Modificado | `templates/inicio.html` |

Los datos de base no forman parte del commit. Se incluyen el comando y su manifiesto documental, no un dump ni filas creadas en la demo. sources/notas-reunion-2026-10-26.txt es la fuente documental aportada por el usuario y citada por la spec.

Excluidos expresamente: .local-backups/** (respaldos preservados y no ignorados), .env, .venv/**, __pycache__/**, .pytest_cache/**, .ruff_cache/**, bytecode, logs, dumps, volúmenes Docker y todo archivo del worktree de US 5.5.

Antes del commit usar una selección explícita de este inventario, revisar git diff --cached --name-status y confirmar que coincide. No usar git add . ni añadir respaldos. Constitution y recursos originales Spec Kit no forman parte del cambio.
