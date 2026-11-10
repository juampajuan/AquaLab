# Implementation Plan: Gestionar catálogo de pruebas

**Branch**: `035-gestionar-catalogo-pruebas` | **Date**: 2026-11-10 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/035-gestionar-catalogo-pruebas/spec.md` (SCRUM-73)

## Summary

Alta, edición, eliminación, desactivación y reactivación de pruebas desde «Administración → Catálogo
de pruebas», en la app `pruebas`, con el mismo esquema de confirmación y concurrencia que la gestión
de tipos de estudio (US 5.5): formulario → resumen firmado → confirmar, con `version` en `Prueba`
para no pisar cambios. Un único servicio, `pruebas/gestion.py:gestionar_prueba`, bloquea la fila,
revalida permiso, versión, «en uso», referencias en fórmulas y reglas de límites, y guarda quién y
cuándo. La regla «prueba activa» se aplica donde hoy no existe: formulario y servicio de tipos de
estudio, «agregar prueba» y la creación de estudios (solo pruebas activas del tipo). El listado
actual marca las pruebas que dependen de una inactiva y enlaza a la ficha nueva. Al desactivar se puede
elegir «Reemplazar por»: la cascada actualiza las fórmulas que la usan y los tipos que la incluyen,
y el cálculo resuelve los reemplazos en los estudios anteriores (research R11). El admin de Django
y `importar_catalogo_pruebas` siguen igual.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: Django 5.2 LTS (forms, `signing`, `select_for_update`), Tailwind CSS 4 y
`templates/ui/`. Sin dependencias nuevas ni JavaScript nuevo: el campo fórmula queda siempre visible, con la ayuda
«Solo si el tipo de cálculo es Fórmula».

**Storage**: PostgreSQL 16. Migración `pruebas/0003_gestion_catalogo.py`: en `Prueba`, `version`
(entero ≥ 1), `reemplazada_por` (FK a `Prueba`, `PROTECT`, nulo), `creada_por`/`modificada_por` (FK a usuario, `PROTECT`, nulos para las existentes),
`fecha_creacion`/`fecha_modificacion` (nulas para las existentes).

**Testing**: pytest + pytest-django; fixtures de `usuarios/tests/conftest.py` (administrador del
panel) y `estudios/tests/conftest.py` (`catalogo`, `estudio_de`, `bioquimico`); ruff.

**Target Platform**: Contenedor `web` (Docker Compose) y Render.

**Project Type**: Aplicación web Django monolítica con templates en el servidor.

**Performance Goals**: Alta completa < 3 minutos para una persona (SC-001); pantallas sin N+1.

**Constraints**: Historial intacto (FR-008, principio IV; el reemplazo reescribe fórmulas pero los
resultados guardan la suya y el cálculo resuelve los reemplazos, FR-016c); acceso del panel 025 sin excepción para
superusuarios (FR-015); concurrencia optimista (FR-016); CSV y admin sin cambios (FR-017).

**Scale/Scope**: app `pruebas` (servicio, formularios, confirmaciones, vistas, URLs, 5 templates,
migración); cambios puntuales en `estudios` (forms de tipos y de agregar prueba, `gestion_tipos`,
`catalogo.configuracion_bloqueada`, `servicios.agregar_prueba`) y en el listado de
`usuarios/views_administracion.py`; CLAUDE.md y tests.

Decisiones en [research.md](./research.md) (R1–R9). No hay `NEEDS CLARIFICATION` pendientes.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Cumplimiento | Estado |
|---|---|---|
| **I. Spec primero (SDD)** | Spec de SCRUM-73 con 3 aclaraciones (2026-11-10). El código espera la aprobación de la spec. | ✅ |
| **II. Simplicidad y Django idiomático** | Vive en `pruebas` (su módulo); reutiliza `Prueba.clean()` (fórmulas), `esta_en_uso()`, `leer_limite` y el patrón de confirmación de tipos de estudio; sin dependencias. | ✅ |
| **III. Tests obligatorios** | Cada FR y escenario con test (ver [Mapa de tests](#mapa-de-tests)). | ✅ |
| **IV. Integridad de datos** | Las pruebas en uso no cambian su método; validaciones e informes guardan su copia y no se tocan; eliminar solo sin uso ni referencias (no se borra historial); desactivar en lugar de borrar. | ✅ |
| **V. Seguridad** | `administracion_requerida` (grupo + permiso, 403) en vistas y revalidación en el servicio; POST con CSRF; tokens firmados atados a usuario y sesión. | ✅ |
| **VI. Idioma y consistencia** | `gestionar_prueba`, `PruebaForm`, `creada_por`; interfaz en español; ruff. | ✅ |
| **Interfaz (UI)** | Confirmación previa (patrón común), `messages`, componentes de `templates/ui/`, ayudas en límites y fórmula (US 9.1). | ✅ |

**Post-diseño (Phase 1)**: cumple todos los principios, sin excepciones.

## Diseño

```text
/administracion/pruebas/                     listado (existente): + «Nueva prueba», enlaces a ficha,
                                             marca «Depende de una prueba inactiva: X»
/administracion/pruebas/nueva/               formulario → POST → resumen (token firmado)
/administracion/pruebas/<pk>/                ficha: datos, uso, quién/cuándo, acciones
/administracion/pruebas/<pk>/editar/         formulario (campos bloqueados si está en uso) → resumen
/administracion/pruebas/<pk>/desactivar/     confirmación con avisos (fórmulas, tipos)
/administracion/pruebas/<pk>/reactivar/      confirmación
/administracion/pruebas/<pk>/eliminar/       confirmación (solo sin uso ni referencias)
/administracion/pruebas/confirmar/           POST único: gestionar_prueba(...) → mensaje → ficha/listado

gestionar_prueba(usuario, operacion, prueba_id, version_esperada, datos)   (una transacción)
  autorizar → select_for_update → version → reglas (en uso, referencias, límites, fórmula)
  → guardar Prueba + LimiteVertido + creada/modificada_por y fecha → version += 1
```

Pantallas y mensajes en [contracts/catalogo-ui.md](./contracts/catalogo-ui.md); campos y reglas en
[data-model.md](./data-model.md).

### Mapa de tests

| Escenario / requisito | Test | Archivo |
|---|---|---|
| FR-001/003, US1 Esc. 1–2, 5–6 — alta Directa y Fórmula, límites por vertido, cancelar | `test_alta_*` | `pruebas/tests/test_gestion.py` |
| FR-002, US1 Esc. 3–4 — fórmula inválida, inexistente, autorreferencia; código repetido (mayúsculas) | `test_alta_rechaza` (parametrizado) | idem |
| FR-002a — límites: número, «Ausente», texto inválido, mín > máx | `test_limites_validos` (parametrizado) | `pruebas/tests/test_formularios.py` |
| FR-006, US2 — editar todo y eliminar sin uso; referenciada no se elimina ni cambia código | `test_sin_uso_*` | `pruebas/tests/test_gestion.py` |
| FR-007, US3 Esc. 1–3 — en uso: solo límites/norma/LD/observación; bloqueados y envío alterado | `test_en_uso_*` | idem |
| FR-008, US3 Esc. 4 — validaciones e informes iguales tras editar límites; validación nueva usa el nuevo | `test_historial_intacto` | idem |
| FR-009, US4 Esc. 5–6 — avisos de fórmulas y de tipos al desactivar | `test_avisos_desactivar` | `pruebas/tests/test_vistas.py` |
| FR-010 — inactiva no se ofrece en tipos ni en agregar prueba; edición de tipo conserva las ya incluidas | `test_inactiva_no_se_ofrece` | `estudios/tests/test_catalogo_activas.py` |
| FR-009/011, US4 Esc. 9 — desactivar sube la versión de los tipos; confirmación vieja de crear estudio se rechaza | `test_confirmacion_vieja_se_rechaza` | idem |
| FR-011, US4 Esc. 3 — estudio nuevo solo con activas; tipo sin activas rechaza | `test_estudio_nuevo_solo_activas` | idem |
| FR-012, US4 Esc. 4 — estudio existente con prueba inactiva: carga, cálculo, validación, informe | `test_estudio_existente_sigue` | idem |
| FR-013/014 — listado: marca «Depende de…», «Nueva prueba», enlaces a ficha | `test_listado` | `pruebas/tests/test_vistas.py` |
| FR-015, US5 — 403 (común, bioquímico, superusuario fuera del grupo), login | `test_acceso` (parametrizado) | idem |
| FR-016, edges — versión cambiada, pasó a estar en uso entre abrir y confirmar | `test_concurrencia_*` | `pruebas/tests/test_gestion.py` |
| FR-016a — creada/modificada por y fecha; «Sin registro» en las existentes | `test_auditoria` | idem |
| FR-016b, US6 Esc. 1–3, 7 — reemplazo: candidatas compatibles, cascada en fórmulas y tipos, resumen | `test_reemplazo_*` | `pruebas/tests/test_reemplazo.py` |
| FR-016c, US6 Esc. 4–6 — estudio viejo recalcula igual; cadena A→B→C; historial intacto | `test_recalculo_con_reemplazo`, `test_cadena` | `estudios/tests/test_calculo_reemplazos.py` |
| FR-017 — CSV y admin siguen funcionando | tests existentes de `pruebas` sin cambios | `pruebas/tests/` |

## Project Structure

### Documentation (this feature)

```text
specs/035-gestionar-catalogo-pruebas/
├── spec.md, plan.md, research.md, data-model.md, quickstart.md
├── contracts/catalogo-ui.md
├── checklists/requirements.md
└── tasks.md              # /speckit-tasks
```

### Source Code (repository root)

```text
CLAUDE.md                                         # + sección «Gestión del catálogo (SCRUM-73)»
config/urls.py                                    # + administracion/pruebas/ → pruebas.urls
pruebas/
├── models.py                                     # + version, creada_por/fecha, modificada_por/fecha
├── migrations/0003_gestion_catalogo.py
├── gestion.py                                    # nuevo: gestionar_prueba, errores, reglas
├── formularios.py                                # nuevo: PruebaForm, LimitesVertidoForm, validar_limite
├── confirmaciones.py                             # nuevo: tokens firmados (patrón de tipos)
├── views.py, urls.py                             # nuevos (namespace «catalogo»)
├── templates/pruebas/{ficha,formulario,confirmar}.html
└── tests/test_gestion.py, test_formularios.py, test_vistas.py
estudios/
├── forms_tipos.py, forms.py                      # solo activas (+ ya incluidas al editar un tipo)
├── gestion_tipos.py                              # rechaza agregar inactivas; reactivar exige una activa
├── calculo.py                                    # resolver_referencias: reemplazos en estudios viejos
├── catalogo.py                                   # configuracion_bloqueada: solo activas
├── servicios.py                                  # agregar_prueba revalida activa
└── tests/test_catalogo_activas.py
usuarios/
├── views_administracion.py                       # listado: dependencias inactivas
└── templates/usuarios/administracion/pruebas.html # «Nueva prueba», enlaces a ficha, marcas
```

**Structure Decision**: la gestión vive en `pruebas` (la app del catálogo); el listado sigue en
`usuarios` porque es parte del panel 025 y su URL (`administracion:pruebas`) ya está en el menú.

## Complexity Tracking

Sin violaciones a la constitution: no aplica.
