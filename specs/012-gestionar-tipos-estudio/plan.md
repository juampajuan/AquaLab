# Implementation Plan: US 5.5 — Gestionar tipos de estudio

**Branch**: 012-Gestionar-Catalogo-Estudios | **Date**: 2026-10-28 | **Spec**: [spec.md](spec.md)

**Input**: specs/012-gestionar-tipos-estudio/spec.md. Base a95efb46 (main con US 5.1/5.2). Al generar el plan, el usuario había autorizado el diseño, pero no tasks ni implementación. Posteriormente autorizó $speckit-tasks, ya ejecutado con 50 tareas verificadas y pendientes. La implementación sigue sin autorización; la aprobación formal del equipo continúa pendiente (T001). Spec funcional confirmada, checklist documental 16/16, aprobación formal global del equipo no acreditada.

**Note**: Generado usando setup-plan.sh --json y el plan-template originales instalados, sin actualizar Spec Kit. Se conserva su estructura; investigación y fase 1 documentales completadas. No hay extensions.yml ni hooks antes/después de plan.

## Summary

Agregar la gestión de tipos sobre el catálogo ya persistido: alta, edición, desactivación, reactivación y eliminación solo de nunca usados. Permiso específico, confirmación firmada y escritor transaccional único con control de versión. Conservar snapshots/asignaciones y consumidor US 5.1; no nuevas tablas, migraciones, CRUD de pruebas, mediciones ni datos científicos. Decisiones en [research.md](research.md); modelo existente en [data-model.md](data-model.md); contratos [UI](contracts/gestion-tipos-ui.md) y [servicio](contracts/gestion-tipos-servicio.md).

## Technical Context

**Language/Version**: Python 3.12, Django 5.2 LTS (5.2.18 en base).
**Primary Dependencies**: ORM, forms, signing, sessions, auth/permission_required, messages, paginator, Bootstrap y psycopg ya disponibles; ninguna dependencia nueva.
**Storage**: PostgreSQL 16; esquema actual, atomic y lock de fila TipoEstudio. Sin nuevas migraciones previstas.
**Testing**: pytest-django/PostgreSQL, unitarios/servicio/UI/contratos y concurrencia real; Ruff/check/migrations y regresiones JS existentes.
**Target Platform**: Docker Compose Linux; navegador de escritorio Chrome para demo FIUBA.
**Project Type**: Monolito Django, templates server-side y módulos dentro de estudios.
**Performance Goals**: Sin SLA ni volumen de laboratorio inventados. Listado paginado a 20, consulta de pruebas seleccionadas y conteos de utilización, sin N+1. No locks en listado; transacciones cortas al preparar configuración coherente y confirmar. Benchmark solo si aparece necesidad medida.
**Constraints**: Único catálogo; no cambios en US 5.1/5.2; permiso en GET/POST/servicio; conjunto publicable no vacío; versión stale rechazada; historial inalterado; datos DEMO explícitos.
**Scale/Scope**: Proyecto académico FIUBA; cinco operaciones de un tipo por transacción, listado y resumen. No búsqueda avanzada, API REST ni edición científica. Límite de 20 borradores por sesión y TTL una hora, siguiendo el patrón de infraestructura existente.

## Constitution Check

*GATE: evaluación antes de fase 0 y revalidación tras fase 1.*

| Principio | Antes de investigación | Después del diseño |
|---|---|---|
| I. Spec primero | Spec/checklist revisadas y plan expresamente autorizado; no aprobación de implementar | Solo documentos; aprobación formal por equipo debe registrarse antes de código. Sin excepción ni aprobación inventada. |
| II. Simplicidad | Stack y entidades existentes | Módulos de estudios; sin nuevos modelos, frameworks o dependencias. |
| III. Tests | Al menos un test automatizado por escenario | Mapa explícito abajo; tests previstos, no ejecutados ni declarados verdes. |
| IV. Integridad | Historial y referencias existentes | Locks/versiones, atomicidad, UNIQUE/PROTECT y no reescritura de estudios. No mediciones. |
| V. Seguridad | Sesión, CSRF y permiso específico | Defensa GET/POST/servicio; tokens de fase; no roles nuevos ni secretos en documentos. |
| VI. UI/idioma | Confirmación obligatoria y español | Formularios, mensajes y Bootstrap existentes; no mutaciones de catálogo mediante GET. |

Gates del diseño pasan: la Constitution prohíbe código de producto sin spec aprobada por el equipo, no esta planificación expresamente autorizada. Aprobación formal sigue siendo puerta de implementación. Checklist no reemplaza revisión del equipo. Las referencias históricas de la spec a modelos inexistentes ya fueron corregidas en el diagnóstico aceptado.

## Project Structure

### Documentation (this feature)

spec.md; checklists/requirements.md; diagnostico-previo-plan.md; plan.md; research.md; data-model.md; contracts/gestion-tipos-ui.md; contracts/gestion-tipos-servicio.md; quickstart.md. tasks.md no se generó en el workflow de plan; se generó posteriormente mediante $speckit-tasks autorizado por el usuario, con 50 tareas verificadas.

### Source Code (repository root)

Ubicaciones PROPUESTAS, no implementadas:

- estudios/gestion_tipos.py: servicio público gestionar_tipo_estudio y lector administrativo coherente; errores/resultados de dominio.
- estudios/forms_tipos.py: formulario único de nombre/descripción/composición, sin campo activo, basado en modelos existentes.
- estudios/confirmaciones_tipos.py: contexto de formulario y borradores/tokens de confirmación propios, sin modificar confirmaciones.py.
- estudios/views_tipos.py: listado, preparar operaciones y confirmar/cancelar, permiso en cada acceso.
- estudios/urls.py: incluir rutas estáticas tipos/ antes de rutas genéricas; conservar las actuales.
- estudios/templates/estudios/tipos/{lista,formulario,confirmar,conflicto}.html: base.html y mensajes por campo.
- templates/base.html e inicio.html: enlace condicionado al permiso, sin alterar navegación funcional de US 5.1/5.2.
- estudios/tests/test_gestion_tipos_servicio.py, test_gestion_tipos_ui.py, test_gestion_tipos_confirmaciones.py, test_gestion_tipos_concurrencia.py; ampliar conftest.py solo con fixtures de permiso/gestión preservando las consumidoras.
- pruebas/models.py, estudios/models.py, migrations/, catalogo.py, servicios.py y flujos de creación/consulta: se reutilizan, NO se recrean ni modifican para esta historia en el diseño propuesto.

**Structure Decision**: separar gestión de consumo dentro de la app estudios evita mezclar reglas administrativas con crear_estudio y permite probar el contrato común sin duplicar entidades.

## Estrategia transaccional y versiones

Ver contrato del servicio para entradas, validaciones y errores. Escritor único: permiso → normalización → atomic → lock del tipo existente → versión esperada → validación de operación → comparar estado canónico → escribir datos/M2M/versión o no-op → salir de atomic → éxito.

Crear publica tipo activo/composición con version=1; editar conserva disponibilidad; desactivar/reactivar solo cambian activo; cada cambio efectivo invalida la versión una vez. No-op válido y vigente no escribe ni incrementa; stale nunca se transforma en no-op exitoso. Borrado comprueba versión y uso bajo lock; no existe versión posterior a eliminar. Validar conjunto en alta/edición/reactivación, no exigir reparar un tipo inválido antes de desactivarlo/eliminarlo nunca usado.

La UNIQUE Lower(nombre) resuelve carreras entre tipos distintos; capturar errores fuera de atomic. No ampliar garantías a escrituras directas que eludan este protocolo. Versión en save/M2M no es automática y no debe inferirse de los tests helpers.

## Coordinación con estudios y eliminación

El consumidor toma advisory 5_100_001 y luego la fila del tipo. El escritor toma solo esa fila; no adquiere luego el advisory. Un tipo por operación. Crear primero implica que eliminar ve el estudio y rechaza; eliminar primero implica que crear ve inexistente. Igual orden para edición/desactivación: creación anterior íntegra o conflicto/no disponibilidad, nunca mezcla. No tocar Estudio, PruebaEstudio, snapshots, creador/hora ni pruebas científicas. PROTECT/FK son defensa adicional. No es necesario bloquear estudios para luego adquirir el tipo.

## Confirmaciones, permisos y contratos

Listado y lector administrativo incluyen inactivos (el consumidor leer_configuracion no los admite). Permiso específico antes de leer datos en todas las rutas, servicio con validación propia y CSRF en POST. Tipo desactivado puede editarse sin reactivación implícita. Contexto firmado desde GET evita que una edición abierta con versión vieja se actualice silenciosamente al preparar su resumen. Resumen, payload y versión quedan ligados al token; conflicto exige acción de revisión nueva y confirmación explícita. No se implementa idempotencia persistente administrativa nueva: se documentan los resultados de reenvíos reales.

## Plan de pruebas y trazabilidad

Cada escenario tendrá al menos un test pytest-django. Agrupación US1/US2/US3 corresponde a recorridos de esta spec, no a historias del backlog distintas.

| Escenarios / requisitos | Archivo propuesto y verificaciones |
|---|---|
| US1 1–7; FR-002/003/004/009/011/015; SC-001/002/005/006/008 | test_gestion_tipos_servicio/ui: alta exacta y activa, pruebas existentes/no repetidas, vacíos, límites 150, nombre duplicado al crear/editar, recorte/caso/tildes/espacios internos, descripción vacía, resumen/volver/cancelar, catálogo vacío y referencias eliminadas antes de confirmar. |
| US2 1–4/7; FR-005/006/010/016; SC-003/005 | servicio/ui: conservar identidad y activo, textos/asignaciones históricas incluso descripción vacía, futuros estudios con versión/textos nuevos, rollback tras cabecera y tras M2M. |
| US2 5/6; US3 3; FR-008/012; SC-007 | concurrencia/ui: integración real con crear_estudio, cambio/rechazo de revisión y confirmación nueva, ambas ordenaciones del lock, versiones sucesivas, tipo inactivo. |
| US2 8–11; FR-013/017; SC-009 | servicio/concurrencia: dos editores, stale desde GET y al confirmar, no-op vigente sin DML, stale con valores coincidentes rechazado, solo mayúsculas sí incrementa, orden/duplicación de IDs no incrementa, cambios combinados una vez, fallas sin versión parcial. |
| US3 1/2/4; FR-007/008 | servicio/ui: uso histórico bloquea eliminación, desactivación y cancelación sin pérdida de referencias; lector administrativo muestra inactivos y consumidor no los ofrece. |
| US3 5–7; FR-001/014; SC-008 | ui/confirmaciones/servicio: anónimo, usuario activo sin permiso, is_staff sin permiso, con permiso, revocación entre resumen y POST; todas las rutas y POST directos. |
| Reactivación/eliminación 1–8; FR-018/019; SC-010/011 | servicio/ui/concurrencia: éxito, prueba ausente, legado vacío, no reactivación accidental, tipo usado incluso finalizado/inactivo, ambas ordenaciones de eliminar/crear, cancelación, fallo y versión antigua. |
| FR-009/010/013/014/017, seguridad transversal | confirmaciones: token de fase incorrecta, firma/usuario/sesión/tipo/acción/payload alterados, vencimiento, purga de expirados antes del límite de sesión, múltiples pestañas, cancelado luego reenviado, reenvíos sin dobles altas y sin garantías de resultado persistente inventadas; GET sin escrituras de dominio; CSRF. |

Concurrencia sobre PostgreSQL real, django_db(transaction=True), conexiones independientes, eventos/barreras, lock_timeout/statement_timeout locales a las conexiones de test y futures/join acotados. No SQLite, sleeps como única coordinación ni mocks de locks. Testear cambios de composición versus creación y conflictos de unicidad entre tipos distintos. Referencias de Prueba que desaparezcan concurrentemente deben causar rechazo/rollback por validación o FK, no registros parciales.

## Riesgos y dependencias

Aprobación formal del equipo (T001) y autorización de implementación pendientes; la revisión del diseño y la autorización posterior de tasks ya se realizaron. Jira administrativo pendiente. US 5.5 no existe todavía: tests propuestos no ejecutados. Captura de versión y confirmación firmada, permisos y tratamiento de rollback necesitan revisión especial en implementación. Usuarios que escriban por SQL/admin genérico fuera del contrato pueden romper el invariante de composición/versionado; no es un camino soportado. Sin SLA o benchmark inventados. Borrado de estudios con historial no se ofrece en estas historias: cualquier futura política de purga requeriría revisar el significado de nunca usado.

## Complexity Tracking

No hay violaciones de Constitution ni excepciones que justificar. No se usa aprobación inexistente para implementar; solo se entrega diseño bajo autorización expresa. No nuevas tablas ni dependencias. Fases 0/1 documentadas; al cerrar el plan aún no se habían generado tasks. Posteriormente se generaron y verificaron 50 tareas. No se modificó código ni se ejecutaron migraciones, cargas o tests de producto en este trabajo documental.
