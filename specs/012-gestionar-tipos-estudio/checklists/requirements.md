# Specification Quality Checklist: Gestionar tipos de estudio

**Purpose**: Revisar el borrador de US 5.5 sin anticipar diseño ni implementación.
**Created**: 2026-10-27
**Feature**: [spec.md](../spec.md)

## Content Quality

- [x] No contiene detalles de implementación.
- [x] Se centra en el valor del responsable técnico y consumidores del catálogo.
- [x] Está escrita para participantes no técnicos, en español.
- [x] Están completas las secciones obligatorias del template original.

## Requirement Completeness

- [x] No quedan marcas de aclaración pendientes.
- [x] Todos los requisitos son inequívocos y verificables sin decisiones pendientes.
- [x] Los criterios de éxito son medibles.
- [x] Los criterios de éxito son independientes de tecnologías.
- [x] Todos los escenarios de aceptación están cerrados.
- [x] Se identificaron casos límite y concurrencia.
- [x] El alcance y exclusiones están expresados.
- [x] Se identificaron dependencias y supuestos.

## Feature Readiness

- [x] Todos los requisitos tienen criterios de aceptación definitivos.
- [x] Los escenarios cubren alta, edición, protección histórica y desactivación.
- [x] Los criterios de éxito permiten evaluar el resultado funcional.
- [x] Se distingue infraestructura compartida existente de funcionalidades US 5.5 todavía no implementadas.

## Revalidación vigente — 28/10/2026

**16/16 controles documentales satisfechos.** Se evalúa calidad y definición de requisitos, no implementación ni aprobación formal global del equipo. La spec continúa Draft para que el usuario revise este diagnóstico; no se ejecutó plan.

| Control antes pendiente | Evidencia suficiente para cerrarlo | Lo que no acredita |
|---|---|---|
| Requisitos inequívocos/verificables | El usuario confirma permisos, unicidad y descripción opcional, conjunto no vacío, historial, versiones, reactivación y eliminación de nunca usados. FR-014 a FR-019 expresan las condiciones; no hay política funcional por elegir. | No es una aprobación formal global del equipo ni un permiso para implementar. |
| Escenarios de aceptación cerrados | US1/US2/US3 y los ocho escenarios de reactivación/eliminación conservan resultados verificables de éxito, rechazo, permiso, cancelación, fallas y concurrencia; FR-018/019 ahora están confirmados por el usuario. | No son resultados de tests del CRUD de US 5.5. |
| Criterios definitivos por requisito | FR-001 a FR-019 están cubiertos por esos escenarios y SC-001 a SC-011; contrato cotejado con infraestructura real integrada de US 5.1. | No reemplaza la revisión del equipo ni garantiza la implementación futura. |

### Bloqueos históricos descartados y pendientes reales

- US 5.1 ya se integró por PR #12; existen Prueba, TipoEstudio, composición, Estudio/PruebaEstudio y snapshots. La rama 012 avanzó a origin/main a95efb46 preservando los borradores y el contexto. No se duplican modelos.
- La dependencia de un proveedor científico oficial está superada por la aclaración académica FIUBA. Fixtures y datos DEMO identificados están autorizados; ya existe cargar_demo_us51. No se ejecutó ninguna carga aquí.
- FR-013/014 de US 5.1 son decisiones definitivas del proyecto, no validaciones externas pendientes. Sus artefactos se leen en la base integrada, sin modificarlos.
- El permiso específico ya está declarado; su enforcement en gestión, el escritor atómico/versionado y las operaciones de US 5.5 faltan implementar. El conjunto no vacío no está garantizado por una constraint M2M: debe validarse en el nuevo escritor.
- Pendiente inmediato: revisión de este diagnóstico y autorización de ejecutar plan. La guía SDD pide revisar la spec; la aprobación formal del equipo deberá acreditarse antes de código de producto según Constitution. No se inventa esa evidencia.
- Jira sigue pendiente administrativo. No bloquea el diseño ni se deduce su código.
- No se generaron plan.md, research.md, data-model.md, contracts/, quickstart.md de US 5.5, tareas de implementación, modelos ni migraciones. No se hizo commit, push ni merge.

## Historial de la checklist — no describe el estado vigente

El registro siguiente se preserva como evidencia de la revisión anterior (13/16). Sus dependencias y propuestas pendientes fueron reevaluadas arriba; no se borra el historial ni se lo interpreta como aprobación actual.

## Notes

- Revalidación tras adopción funcional de FR-018/019: 13/16 controles satisfechos. Se cierra exclusivamente la ausencia de marcas de aclaración: las preguntas funcionales se contestaron con las reglas expresas del usuario y se sustituyeron por estados de aprobación formal pendiente. Los otros tres controles siguen abiertos porque no hay evidencia de aprobación definitiva del alcance por el equipo; escenarios y criterios propuestos están definidos, pero aún no son acuerdos definitivos. Draft; no aprobada globalmente ni autorizada para plan.
- FR-014 resuelto por el usuario: permiso específico de gestión del catálogo. US3, escenarios 6 y 7, y SC-008 cubren rechazo sin autorización y gestión autorizada; no se equipara con permisos administrativos ni se crea un rol de dominio.
- FR-015 resuelto por el usuario: recortar espacios laterales y comparar nombres sin distinguir mayúsculas, conservando diferencias de tildes y espacios internos; descripción opcional. US1, escenarios 2, 6 y 7, y SC-008 cubren unicidad y descripción vacía; aplica también a edición.
- FR-016 resuelto por el usuario: estudios anteriores conservan nombre y descripción históricos además de sus pruebas; US2, escenario 4, y SC-003 actualizados. El mecanismo compartido con US 5.1 sigue pendiente; no se acredita integración implementada.
- FR-012 adoptado por el usuario: US 5.5 posee TipoEstudio y composición; US 5.1 posee Estudio, asignaciones y snapshots históricos. Se añadieron datos e interfaces funcionales mínimas con entradas, resultados y garantías, sin endpoints, modelos científicos ni código de US 5.1.
- FR-017 adoptado por el usuario: versión desactualizada rechazada, conflicto visible y revisión de configuración actual, con guardado atómico de datos y pruebas. US2, escenarios 8 a 11, y SC-009 cubren ediciones simultáneas, reintentos y fallas; son criterios documentados, no tests ejecutados.
- FR-018 y FR-019: propuestas funcionales adoptadas por el usuario y pendientes de aprobación formal del equipo, no decisiones del laboratorio. Reactivación requiere permiso, confirmación, versión vigente y pruebas válidas; vuelve a habilitar nuevas creaciones sin alterar estudios existentes. Eliminación definitiva solo para nunca usados; cualquier estudio histórico impide borrar y permite desactivar como alternativa. Escenarios de propuestas 1 a 8 y SC-010/011 cubren éxito, validaciones, permiso, cancelación, falla, versiones y concurrencia. Son evidencia de definición documental, no de aprobación o pruebas ejecutadas.
- Evidencia de los siete criterios oficiales: alta/nombre/descripción → FR-002 y US1; selección de pruebas existentes → FR-003; conjunto no vacío → FR-004; edición → FR-005 y US2; estudios futuros → FR-006; protección/desactivación → FR-007/008 y US3; exclusión científica → FR-011 y SC-006.
- Constitution aporta sesión, confirmación e historial. La descripción oficial más reciente del usuario incluye editar descripción; no se limita a la redacción anterior del CSV.
- La precarga científica está en el backlog como Task, ID de importación 31; no acredita clave Jira ni que existan datos o modelos.
- Se revisó US 5.1 sin modificarla. Sus FR-013 y FR-014 siguen abiertos; FR-015 orienta el contrato de consistencia propuesto sin declarar aprobadas ambas specs.
- Al retomar US 5.1 deberá incorporarse y revisar la conservación de textos históricos y el reparto adoptado aquí; su spec no se ha actualizado ni se declara totalmente alineada. El contrato funcional está adoptado, pero sincronizar el documento consumidor y verificar integración siguen pendientes.
- Dependencias externas abiertas: responsable y representación existente de Prueba, fuente aprobada y tarea de precarga científica; claves Jira pendientes. No se consideran resueltas por adoptar el contrato ni se crean datos ficticios para cubrirlas. Deben acordarse antes del diseño que las requiera; no se exige tener ejecución funcional durante specify.
- Protección histórica y concurrencia entre catálogo y estudios se verificarán conjuntamente cuando exista US 5.1; no hay evidencia de ejecución funcional ni datos oficiales cargados.
- No se generaron plan, tareas de implementación, modelos, migraciones, datos científicos, commits, push o merge.
- Para aprobar formalmente: registrar aprobación del equipo de la spec completa, especialmente FR-018/019; acordar responsable, fuente oficial e identidades compartidas de la dependencia Prueba/precarga; revalidar los controles pendientes con esa evidencia. Para iniciar plan se requiere además indicación de continuar tras la revisión. No es necesario tener modelos o datos cargados ni tests de integración ejecutados en specify; Jira sigue pendiente administrativo, no bloqueo funcional por sí solo.
