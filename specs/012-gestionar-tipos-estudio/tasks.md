---
description: "Tareas de implementación US 5.5 — Gestionar tipos de estudio (012)"
---

# Tasks: US 5.5 — Gestionar tipos de estudio

**Input**: specs/012-gestionar-tipos-estudio/{spec.md,plan.md,research.md,data-model.md,contracts/,quickstart.md} aceptados por el usuario como base de tareas el 28/10/2026.
**Prerequisites**: Diseño disponible y checklist documental 16/16. La aprobación formal del equipo y la autorización de implementar fueron comunicadas por el usuario el 28/10/2026 y registradas en Notes (T001 completada).
**Tests**: Obligatorios por petición expresa y Constitution: al menos un test por escenario, escritos antes de la implementación correspondiente y con fallo pertinente documentado. Esta generación no ejecutó tests ni acredita resultados.
**Organization**: US1/US2/US3 son los recorridos P1/P2/P3 de esta spec, no otras historias del backlog. Reactivación/eliminación se incluyen en US3 como extensión confirmada del retiro/disponibilidad de tipos. Las historias se verifican con fixtures propias, pero se implementan secuencialmente porque comparten escritor, rutas y confirmaciones.

## Format: [ID] [P?] [Story] Description

Al generarse este documento, todas las tareas estaban pendientes; sus marcadores actuales reflejan únicamente avances verificados. [P] solo habilita trabajo simultáneo sobre archivos diferentes una vez satisfechas sus dependencias; no autoriza agentes, commits ni iniciar implementación en esta entrega. Rutas relativas al worktree E:/Codex/worktrees/us55-tipos-estudio/AquaLab. Usar los scripts/skills originales sin actualizarlos.

## Path Conventions

App existente estudios; Prueba existente en pruebas. Sin nuevos modelos, migraciones, dependencias o admin editable de tipos. El esquema, servicio crear_estudio, consulta US 5.2 y contratos consumidores se reutilizan intactos. QA en proyecto Compose aqualab-us55, con su base/volumen propio y puerto 8012, según quickstart.md; no tocar contenedores de otro worktree.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Aprobar antes de código y comprobar la base real, sin recrear infraestructura.

- [X] T001 Registrar en Notes de specs/012-gestionar-tipos-estudio/tasks.md evidencia real de aprobación formal de la spec por el equipo y autorización de implementar; si no existe, detener T002 en adelante. La aceptación de diseño/tareas actual no la sustituye. No inventar actas, revisores o Jira ni exigir un comprobante externo no requerido por Constitution. Consultar spec/checklist como entradas; no modificar sus archivos o marcadores desde implement salvo autorización expresa del usuario para registrar aprobación allí. La checklist sigue siendo revisión documental, no avance de código.
- [X] T002 Verificar y registrar en specs/012-gestionar-tipos-estudio/quickstart.md rama/base, respaldos excluidos y QA aislado; comprobar sin modificar pruebas/models.py, estudios/models.py y migrations que se reutilizan: id «BigAutoField, identidad estable»; Prueba.codigo «CharField(50), obligatorio, unique exacto, espacios laterales recortados; Check no vacío» y Prueba.nombre «CharField(150), obligatorio, recortado; Check no vacío»; permiso estudios.gestionar_catalogo ya declarado. No crear modelos/migraciones ni asignar permisos automáticamente. Confirmar configuración de base del proyecto aqualab-us55 y pruebas futuras según quickstart, sin usar la base de otro checkout (depende T001).

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Fixtures aisladas, autorización y contratos comunes antes de escrituras de historia. Todo código nuevo requiere T001 satisfecha.

- [X] T003 Añadir fixtures de gestores con permiso, usuario sin permiso, staff sin permiso y tipos activos/inactivos en estudios/tests/conftest.py; reutilizar empleado, Muestra, Prueba/TipoEstudio existentes sin cambiar sus fixtures consumidoras. Respetar TipoEstudio.activo «BooleanField(default=True)» y version «PositiveBigIntegerField(default=1, editable=False), Check >=1. No incremento automático en save/M2M». Datos solo sintéticos de pytest; permiso explícito por fixture y usuarios recargados al probar revocación, sin seeds/autoload de desarrollo (depende T002).
- [X] T004 [P] Escribir tests fundacionales en estudios/tests/test_gestion_tipos_servicio.py de guardia usuario/permiso antes de consultar tipos y lector administrativo coherente que incluye inactivos/vacíos; contrastar con leer_configuracion consumidor que los rechaza. Preservar «ManyToManyField a pruebas.Prueba mediante TipoEstudioPrueba», «tipo FK CASCADE, prueba FK PROTECT; UniqueConstraint(tipo, prueba)» y Estudio.tipo «FK TipoEstudio PROTECT, related_name estudios; cualquier estado de estudio protege uso histórico». Registrar fallo por funcionalidad administrativa ausente, no un éxito supuesto (FR-001/007/012/014; depende T003).
- [X] T005 [P] Escribir tests de infraestructura de tokens en estudios/tests/test_gestion_tipos_confirmaciones.py: fases distintas, usuario/HMAC de sesión/acción/tipo/versión/digest, TTL 3600s, JSON canónico con IDs ordenados/deduplicados, UUID por borrador, purga de expirados antes del máximo 20 pendientes vigentes y aislamiento de pestañas. No escribir catálogo al preparar ni aceptar contexto de edición como confirmación; registrar fallo inicial pertinente (FR-009/014/017; depende T003).
- [X] T006 Crear fundamentos de estudios/gestion_tipos.py: errores/resultados del contrato, validación de usuario activo autenticado y has_perm, normalización/canonización y lectura administrativa con atomic/lock del tipo cuando se prepare copia coherente o conflicto. No modificar catalogo.py ni crear un catálogo paralelo; no publicar escrituras parciales de operaciones aún no implementadas. Ejecutar T004 y registrar resultado real (FR-001/012/014; depende T004/T005).
- [X] T007 Implementar infraestructura separada en estudios/confirmaciones_tipos.py: salts tipos.edicion.v1 y tipos.confirmacion.v1; contexto desde GET ligado a versión de apertura; borradores tipos_pendientes con creado_en, copia revisada y digest del payload; purga/TTL/límite; firma/identidad/fase y descarte. No reutilizar ni modificar confirmaciones.py de US 5.1; la sesión no es idempotencia persistente. Ejecutar T005 antes de abrir UI (FR-009/014/017; depende T005/T006).

**Checkpoint**: Base común verificable; modelos intactos. No se presenta el permiso declarado como autorización ya aplicada a endpoints ni los helpers de tests como CRUD existente.

## Phase 3: User Story 1 — Crear tipo con pruebas existentes (Priority: P1, MVP)

**Goal**: Alta autorizada con resumen/confirmación y composición exacta, sin crear Prueba.
**Independent Test**: Con fixtures aisladas y gestor, alta válida produce tipo activo v1 y conjunto exacto; errores/cancelación no dejan filas parciales. No requiere muestras o estudios para alta.

### Tests for User Story 1 — primero

- [X] T008 [P] [US1] Escribir en estudios/tests/test_gestion_tipos_servicio.py tests US1 1–4/6/7: alta v1 activa, datos exactos, nombre obligatorio/duplicado, pruebas existentes/no vacías/deduplicadas, descripción vacía y preservada, caso/tildes/espacios internos; fallo tras cabecera o M2M revierte todo; alta repetida no duplica nombre. Sin Prueba nueva ni propiedades científicas. Mostrar fallos antes de T011 (FR-002/003/004/010/011/013/015; depende T007).
- [X] T009 [P] [US1] Escribir en estudios/tests/test_gestion_tipos_ui.py tests US1 1–7: formulario/selector existente, errores por campo y conservación, catálogo Prueba vacío, resumen exacto sin crear, volver/cancelar, éxito y navegación. Incluir todas las rutas de esta fase: anónimo/login, sin permiso/403, staff sin permiso/403, con permiso; POST directo y CSRF (FR-001/002/003/004/009/014/015; depende T007).
- [X] T010 [P] [US1] Extender estudios/tests/test_gestion_tipos_confirmaciones.py para alta: token manipulado/otra sesión/usuario/acción/tipo/fase/digest, expirado o cancelado reenviado, campos extra no cambian nombre/descripcion/pruebas confirmados, y múltiples solicitudes no se cruzan. Preparar/cancelar no crea tipo; registro de fallo antes de T013/T014 (FR-009/010/014; depende T007).

### Implementation for User Story 1

- [X] T011 [P] [US1] Incorporar crear a gestionar_tipo_estudio en estudios/gestion_tipos.py: guardia, normalizar/validar, atomic, tipo activo version=1 y asociaciones completas; existencia de pruebas también al confirmar; captura de IntegrityError/DatabaseError fuera de atomic. Constraint tipo_estudio_nombre_unico_ci como defensa final; no UUID persistente administrativo ni reintento silencioso que invente otro nombre. Resultado después de commit (FR-002/003/004/010/011/013/015; depende T008/T009/T010).
- [X] T012 [P] [US1] Crear TipoEstudioForm en estudios/forms_tipos.py: nombre «CharField(150), obligatorio, recortado; UniqueConstraint Lower(nombre), Check no vacío. Mayúsculas no distinguen para unicidad; tildes y espacios internos sí»; descripcion «TextField(blank=True, default=""), no NULL; opcional», Textarea strip=False; pruebas ModelMultipleChoiceField requerido, sin Prueba.activo inexistente. Sin campos de activo/version/usuario/snapshots editables ni ModelForm.save como escritor (FR-002/003/004/015; depende T008/T009/T010).
- [X] T013 [P] [US1] Extender estudios/confirmaciones_tipos.py con preparación y verificación de propuesta de alta, copia canónica completa de nombre/descripcion/IDs y token de confirmación. Invalida borrador anterior solo al preparar propuesta nueva válida; volver conserva valores; no aceptar campos libres del POST de confirmación ni convertir firma vencida en permiso de guardar (FR-009/014; depende T008/T009/T010).
- [X] T014 [US1] Crear estudios/views_tipos.py para listado paginado 20 (nombre/pk, estado todos/activos/inactivos), GET/POST crear y GET/POST confirmar/cancelar. Permiso específico antes de leer datos en cada ruta, métodos limitados, servicio con defensa propia; POST preparar solo sesión, confirmar solo escritor. GET no muta tablas de dominio; resultado tras commit y errores seguros. Aún no publicar acciones futuras sin rutas disponibles (FR-001/009/010/014; depende T011/T012/T013).
- [X] T015 [P] [US1] Crear estudios/templates/estudios/tipos/formulario.html con Bootstrap/base, errores por campo, CSRF, selección de pruebas, token contextual aplicable y conservación de propuesta; sin checkbox activo ni altas científicas (FR-002/003/004/009/011; depende T014).
- [X] T016 [P] [US1] Crear estudios/templates/estudios/tipos/confirmar.html con operación, nombre/descripcion y pruebas revisadas, token oculto, Confirmar/Volver/Cancelar; muestra copia asociada al token, nunca configuración nueva con token viejo (FR-009/010; depende T014).
- [X] T017 [P] [US1] Crear estudios/templates/estudios/tipos/lista.html con estado, pruebas/uso informativos, filtro simple y paginación, catálogo vacío y enlace de alta; no enlaces a operaciones aún no integradas ni uso del lector consumidor para ocultar inactivos (FR-009/012/014; depende T014).
- [X] T018 [US1] Integrar las rutas tipos_listar/tipos_crear/tipos_confirmar en estudios/urls.py antes de la ruta genérica existente y enlace condicionado a perms.estudios.gestionar_catalogo en templates/base.html e inicio.html. Mantener rutas y permisos de US 5.1/5.2 intactos; ocultar enlace no sustituye guardias GET/POST/servicio (FR-001/014; depende T015/T016/T017).
- [X] T019 [US1] Ejecutar los tests de alta/UI/tokens y lector de esta fase con PostgreSQL QA aislado y registrar comandos/resultados en specs/012-gestionar-tipos-estudio/quickstart.md. Verificar US1 1–7, permisos, ausencia de parciales y de datos de producción; corregir únicamente implementación autorizada si fallan antes de marcar completado (FR-001 a FR-004/009 a FR-015; depende T018).

**Checkpoint**: MVP de alta completo, incluidas seguridad/atomicidad. No equivale a US 5.5 terminada ni a permiso de deploy/commit automático.

## Phase 4: User Story 2 — Editar sin alterar estudios existentes (Priority: P2)

**Goal**: Edición completa, versión desde apertura, no-op y conflicto sin pérdida histórica.
**Independent Test**: Crear tipos/estudios con fixtures, no mediante la UI de alta; editar por el nuevo flujo conserva identidad/disponibilidad/historial y rechaza stale. La implementación depende de la fase US1 por módulos comunes.

### Tests for User Story 2 — primero

- [X] T020 [P] [US2] Extender estudios/tests/test_gestion_tipos_servicio.py con US2 1–4/7/11: editar datos/composición, mantener PK y activo, nombre propio no duplica, última prueba no se quita sin reemplazo; snapshots/asignaciones/autor/hora de estudios intactos, incluida descripción histórica vacía. No-op válido sin DML, versión vigente requerida, cambios combinados incrementan una vez, caso del nombre sí cambia y orden/IDs repetidos no; rollback de datos/M2M/versión (FR-005/006/010/013/016/017; depende T019).
- [X] T021 [P] [US2] Extender estudios/tests/test_gestion_tipos_ui.py con US2 1–5/7/8/10: editar activo e inactivo sin reactivación implícita, validaciones, permiso GET/POST, versión capturada al abrir GET, conflicto ya al preparar resumen, propuesta/vigente separadas y revisión nueva explícita. Estudio nuevo consume lo confirmado; el previo mantiene textos/pruebas (FR-005/006/009/012/014/016/017; depende T019).
- [X] T022 [P] [US2] Extender estudios/tests/test_gestion_tipos_confirmaciones.py con contexto de edición viejo, token de fase falsa, versión/tipo/payload alterados, reenvío anterior después de conflicto y permiso revocado entre resumen/confirmación; ningún caso refresca versión o consentimiento silenciosamente (FR-009/014/017; depende T019).
- [X] T023 [P] [US2] Escribir en estudios/tests/test_gestion_tipos_concurrencia.py pruebas US2 5/6/8–11: dos editores sobre misma versión, conflictos sucesivos, edición y crear_estudio en ambas ordenaciones, y altas/ediciones distintas por nombre equivalente. PostgreSQL real, django_db(transaction=True), conexiones por hilo, eventos/barrera, lock_timeout/statement_timeout y futures/join acotados; no mocks de locks ni SQLite (FR-010/012/013/017; depende T019).

### Implementation for User Story 2

- [X] T024 [P] [US2] Extender gestionar_tipo_estudio en estudios/gestion_tipos.py para editar: atomic → select_for_update TipoEstudio → comparar versión → validar → canonizar/comparar → guardar datos/M2M/version o sin_cambios. Mantener «PositiveBigIntegerField(default=1, editable=False), Check >=1» y aumentar solo una vez por cambio efectivo; stale se rechaza antes de no-op. No escribir «tipo_nombre_snapshot CharField(150), tipo_descripcion_snapshot TextField opcional, tipo_version_snapshot PositiveBigInteger >=1» ni ninguna asignación PruebaEstudio «unique(estudio, prueba), FK Prueba y Estudio PROTECT». Manejar errores fuera de atomic y releer tras rollback (FR-005/006/010/013/016/017; depende T020/T021/T022/T023).
- [X] T025 [P] [US2] Extender estudios/forms_tipos.py para edición validando nombre con excepción de PK propia, mismos límites/normalización de T012 y selección final no vacía. Conservar activo de la entidad; no exponer ni aceptar cambios en version/snapshots. No implementar escrituras desde formulario (FR-004/005/015; depende T020/T021/T022/T023).
- [X] T026 [P] [US2] Extender estudios/confirmaciones_tipos.py con contexto firmado desde GET de edición (usuario/HMAC/acción/tipo/version de apertura) y versión esperada preservada hasta preparar y confirmar. Token de resumen distinto con digest; conflicto no reetiqueta el payload viejo con versión actual. No-op sigue requiriendo confirmación vigente, cancelación no guarda (FR-009/014/017; depende T020/T021/T022/T023).
- [X] T027 [US2] Extender estudios/views_tipos.py con tipos_editar, preparación coherente y manejo de conflicto al preparar/confirmar: propuesta antigua y configuración vigente separadas, nuevo GET explícito de revisión antes de preparar/confirmar otra vez. Lector administrativo incluye inactivos/vacíos; jamás usar leer_configuracion para excluirlos. Permiso antes de lookup y CSRF (FR-005/009/012/014/017; depende T024/T025/T026).
- [X] T028 [P] [US2] Crear estudios/templates/estudios/tipos/conflicto.html con propuesta anterior y datos vigentes claramente diferenciados, mensaje sin guardado y enlace a revisar nueva base; no botón que acepte automáticamente la versión nueva ni datos de otra solicitud (FR-009/017; depende T027).
- [X] T029 [P] [US2] Extender estudios/templates/estudios/tipos/formulario.html, confirmar.html y lista.html para edición: contexto de versión de apertura, volver conservando propuesta, disponibilidad informativa/no editable y mensajes de actualización/sin cambios. No sobrescribir borradores de otras pestañas (FR-005/009/017; depende T027).
- [X] T030 [US2] Incorporar tipos_editar en estudios/urls.py conservando las rutas actuales y verificar los enlaces de listado/formulario/conflicto en estudios/tests/test_gestion_tipos_ui.py, sin crear consultas o permisos nuevos de estudios (FR-005/014; depende T028/T029).
- [X] T031 [US2] Ejecutar servicio/UI/confirmaciones de edición, concurrencia de T023 y regresiones consumidoras estudios/tests/test_servicio.py y test_registro.py con PostgreSQL; registrar comandos/resultados en specs/012-gestionar-tipos-estudio/quickstart.md. Acreditar US2 1–11 y no inferir historial correcto solo del helper mutante de tests (FR-005/006/010/012/013/016/017; depende T030).

**Checkpoint**: Escritor administrativo real coordinado con crear_estudio; ninguna mutación pública fuera de su atomic. Stale nunca acepta por coincidir valores; no-op no publica versión.

## Phase 5: User Story 3 — Disponibilidad, reactivación y eliminación protegida (Priority: P3)

**Goal**: Desactivar/reactivar y borrar solo tipos nunca usados con autorización/confirmación/versiones e integridad concurrente.
**Independent Test**: Fixtures con tipos utilizados/nunca usados e inactivos, sin requerir alta previa por UI. Verificar resultados e historial tanto en servicio como en endpoints; ejecución secuencial por el escritor común.

### Tests for User Story 3 — primero

- [X] T032 [P] [US3] Extender estudios/tests/test_gestion_tipos_servicio.py con US3 1–4 y reactivación/eliminación 1/2/4/5/7/8: desactivar/reactivar con version vigente e incremento único/no-op, reactivar exige pruebas válidas, desactivar/eliminar puede retirar legado inválido nunca usado, tipo utilizado incluso finalizado/inactivo protegido, eliminar solo tipo/through y conservar Prueba, rollback y versión vieja siempre rechazada. No inventar versión posterior al borrar (FR-007/008/010/017/018/019; depende T031).
- [X] T033 [P] [US3] Extender estudios/tests/test_gestion_tipos_ui.py con US3 1–7 y reactivación/eliminación 1–5/7/8: listados activos/inactivos, resumen/volver/cancelar, éxito y rechazo de usados con alternativa de desactivación; GET/POST directo en cada acción sin permiso, staff sin permiso, con permiso y cuenta inactiva. Crear estudio rechaza desactivación previa; reactivado vuelve a ofrecerse (FR-001/007/008/009/014/018/019; depende T031).
- [X] T034 [P] [US3] Extender estudios/tests/test_gestion_tipos_confirmaciones.py para falsificar acción/tipo/version/digest, intentar convertir desactivar en eliminar, firma vencida, pendiente cancelado, permiso revocado y reenvíos tras éxito. Alta repetida puede dar duplicado, edición/disponibilidad repetida stale y eliminación repetida inexistente; no prometer resultado idempotente persistente administrativo (FR-009/010/014/017/018/019; depende T031).
- [X] T035 [P] [US3] Extender estudios/tests/test_gestion_tipos_concurrencia.py con desactivar/reactivar frente a revisión/creación de estudio, eliminar frente a primera creación en ambos órdenes (reactivación/eliminación escenario 6) y dos modificaciones de disponibilidad/eliminación sobre versión compartida. Asegurar conexiones/hilos terminados y errores capturados; ningún escritor toma advisory 5_100_001 después del lock TipoEstudio (FR-007/008/010/012/013/017/018/019; depende T031).

### Implementation for User Story 3

- [X] T036 [P] [US3] Añadir desactivar/reactivar al único servicio en estudios/gestion_tipos.py: autorización, atomic, lock tipo, versión antes de validación/no-op, destino activo fijo por operación; mantener textos/composición/historial. Reactivar exige conjunto válido no vacío; desactivar no fuerza reparar legado vacío. Cambiar activo publica v+1 una vez; vigente ya en destino devuelve sin_cambios sin DML (FR-007/008/010/017/018; depende T032/T033/T034/T035).
- [X] T037 [US3] Añadir eliminar a estudios/gestion_tipos.py: lock tipo → versión → estudios.exists sin filtro estado/fecha/activo → delete solo nunca usado; PROTECT/FK adicionales. Error TipoUtilizado con alternativa de desactivación; datos y composición se revierten ante fallo; Prueba y todo historial intactos. No adquirir lock de creación de estudios después del tipo, no bloquear estudios para luego bloquear tipo ni recrear entidad ausente (FR-007/010/012/019; depende T036).
- [X] T038 [P] [US3] Extender estudios/confirmaciones_tipos.py para versiones y estados destino de desactivar/reactivar/eliminar, metadatos de uso solo informativos y copia revisada; la acción de negocio viene de token/borrador y el servicio vuelve a comprobar uso. Cancelado no se revive; purga y tope de pendientes mantienen aislamiento (FR-009/014/017/018/019; depende T032/T033/T034/T035).
- [X] T039 [US3] Extender estudios/views_tipos.py con GET de resumen de desactivar/reactivar/eliminar y confirmación única, todos con permiso antes de consulta y métodos limitados. Mostrar uso bloqueante al preparar borrado sin confiar en ese conteo al confirmar; entidad inexistente/error controlado; no DML en GET ni acciones alternativas automáticas (FR-001/007/008/009/014/018/019; depende T037/T038).
- [X] T040 [P] [US3] Extender estudios/templates/estudios/tipos/lista.html y confirmar.html para disponibilidad e irreversibilidad de eliminación, operación/version correctas, uso histórico y enlace explícito a preparar desactivación. No mostrar botones como si permiso o conteo UI bastaran ni alterar las pantallas US 5.1/5.2 (FR-007/008/009/014/018/019; depende T039).
- [X] T041 [P] [US3] Integrar tipos_desactivar/tipos_reactivar/tipos_eliminar en estudios/urls.py conservando rutas anteriores y namespace; no enlaces GET que ejecuten mutaciones ni endpoints genéricos sin guardia. Verificar métodos y nombre de rutas contra contracts/gestion-tipos-ui.md (FR-001/009/014/018/019; depende T039).
- [X] T042 [US3] Ejecutar matriz completa de autorización/CSRF/tokens/rutas de esta fase en estudios/tests/test_gestion_tipos_ui.py y test_gestion_tipos_confirmaciones.py, incluyendo revocación entre peticiones, GET sin DML de dominio y llamadas directas al servicio sin permiso. Registrar resultados reales en specs/012-gestionar-tipos-estudio/quickstart.md sin equiparar marcador documental a test aprobado (FR-001/009/014/017/018/019; depende T040/T041).
- [X] T043 [US3] Ejecutar todos los tests administrativos de servicio/concurrencia de US3 y regresiones de creación/consulta (estudios/tests/test_servicio.py, test_consulta.py y muestras/tests/test_detalle.py) con PostgreSQL, registrando comandos y resultados en specs/012-gestionar-tipos-estudio/quickstart.md. Acreditar US3 1–7 y escenarios adicionales 1–8 sin corrupción histórica o referencias huérfanas (FR-006/007/008/010/012/013/016/018/019; depende T042).

**Checkpoint**: Cinco operaciones cubiertas por un solo escritor; snapshots y pruebas de estudios previos permanecen. No se implementa gestión científica, agregar/quitar pruebas de estudio ni aprobación automática de usuarios.

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Evidencia completa, regresiones, validación manual y cierre revisable, sin commits automáticos.

- [X] T044 Revisar en specs/012-gestionar-tipos-estudio/tasks.md la matriz FR-001 a FR-019, SC-001 a SC-011 y los 33 escenarios de spec frente a estudios/tests/test_gestion_tipos_*.py; documentar huecos reales y resolverlos con tests primero antes de declarar cobertura. Verificar que los contratos aceptados se respetan y detenerse para revisión si aparece un cambio de alcance, sin editar requisitos para acomodar código (depende T043).
- [X] T045 Ejecutar en QA aislado todos los controles de specs/012-gestionar-tipos-estudio/quickstart.md: suite general pytest, Ruff check y format --check, Django check, makemigrations --check --dry-run, migrate --check sobre las migraciones existentes y node --test usuarios/tests/js/sesion.test.cjs. Registrar resultados reales; ninguna migración nueva esperada, ningún éxito supuesto ni alteración de base ajena (depende T044).
- [X] T046 Revisar y preparar specs/012-gestionar-tipos-estudio/quickstart.md con nombres/rutas realmente implementados y cuentas QA autorizadas; usar cargar_demo_us51 solo explícitamente y sobre el proyecto aqualab-us55, dry-run antes de aplicar cuando sea necesario. Probar con tipos nuevos [DEMO FIUBA US55] sobre Prueba DEMO-US51, sin modificar el manifiesto base, limpiar historial automáticamente ni cargar datos durante migrate/startup (depende T045).
- [X] T047 Realizar o solicitar al usuario el recorrido Chrome de specs/012-gestionar-tipos-estudio/quickstart.md, registrar ejecutor/fecha/entorno/casos/resultados y pendientes de forma real. Incluir alta/edición/volver/cancelar, permisos, no-op, dos editores, historial, desactivar/reactivar y eliminar nunca usado/rechazar usado. Distinguir reporte del usuario de observación directa y de concurrencia automatizada; no completar lo no validado (depende T046).
- [X] T048 Registrar en Notes de specs/012-gestionar-tipos-estudio/tasks.md y en quickstart.md la evidencia de aprobación T001, resultados automáticos/manuales, limitaciones y dependencias reales; mantener checklists/requirements.md en lectura y no alterar sus archivos/marcadores para simular implementación, Jira, CI remoto o aprobación de código. Si falta algún resultado, mantener ese cierre pendiente (depende T047).
- [X] T049 Inspeccionar diff y generar inventario selectivo de archivos en specs/012-gestionar-tipos-estudio/inventario-commit.md, verificando modelos/migraciones/US 5.1/5.2, Constitution y Spec Kit sin cambios accidentales y ningún dato local/secretos/backups/cachés. Preservar .local-backups fuera de futuros commits; no staging ni commit automático (depende T048).
- [X] T050 Presentar cierre contra specs/012-gestionar-tipos-estudio/plan.md y tasks.md, comprobar qué tareas tienen evidencia suficiente antes de marcarlas y listar pendientes; no autorizar por inferencia push/PR/merge o implementación extra. Acreditar ausencia de cambios ajenos y preparar revisión final de la historia (depende T049).

## Dependencies & Execution Order

- **Puerta de producto**: T001 → T002. La autorización original de tasks solo generaba este documento y no completaba T001; la confirmación posterior del 28/10/2026 sí quedó registrada en Notes. La evidencia formal debe existir antes de escribir incluso fixtures/tests o módulos durante implement. No se infiere de haber aceptado plan/tasks.
- **Base**: T002 → T003 → T004/T005 (archivos distintos) → T006 → T007. T006 espera ambos tests fundacionales; no publicar endpoints incompletos.
- **US1**: T007 → T008/T009/T010 → T011/T012/T013 → T014 → T015/T016/T017 → T018 → T019.
- **US2**: T019 → T020/T021/T022/T023 → T024/T025/T026 → T027 → T028/T029 → T030 → T031.
- **US3**: T031 → T032/T033/T034/T035. Luego T036 → T037; T038 puede correr en paralelo con T036/T037 en archivo diferente, después de los mismos tests. T037/T038 → T039 → T040/T041 → T042 → T043.
- **Cierre**: T043 → T044 → T045 → T046 → T047 → T048 → T049 → T050. No cerrar documentación dependiente de manual mientras falte ese reporte.
- Historias independientes para validar con fixtures, NO para editar simultáneamente escritor/confirmaciones/rutas compartidos. Un cambio de nombre, descripción, activo o composición efectivo invalida todas las revisiones de esa versión; respetar versiones también entre diferentes operaciones.
- En cada fase: tests primero y fallo pertinente comprobado; después implementación; finalmente ejecución verde. Si un test pasa ya por infraestructura existente, registrar esa realidad y no fingir un rojo. No se crean modelos o migraciones como pasos de relleno.

## Parallel Examples

- **Fundación**: T004 (servicio) y T005 (confirmaciones), tras T003. Luego ejecución secuencial T006/T007.
- **US1**: T008/T009/T010 en archivos de tests separados. Tras ellos, T011 (gestión), T012 (forms) y T013 (confirmaciones) son independientes sobre módulos distintos; T014 los integra. T015/T016/T017 son tres templates distintos.
- **US2**: T020/T021/T022/T023 son tests distintos; T024/T025/T026 módulos distintos tras tests. T028 (conflicto.html) puede coexistir con T029 (otros tres templates), una vez finalizado T027.
- **US3**: T032/T033/T034/T035 en tests distintos. T036 y T038 son archivos diferentes; T037 debe esperar T036 por compartir gestion_tipos.py. T040 (templates) y T041 (urls) son independientes tras T039.
- [P] no habilita correr suites que compartan simultáneamente la misma base test_ de PostgreSQL. Usar una ejecución de pytest o bases de test separadas; no introducir pytest-xdist/dependencias nuevas para esto ni compartir conexiones entre hilos.

## Implementation Strategy

1. Revisar tasks, obtener evidencia real de T001 y permiso de implementar; no ejecutar producto por la mera presencia de esta lista.
2. Base compartida ya existe: solo guardia/lectura administrativa, fixtures y confirmaciones nuevas.
3. MVP = US1 terminada con permisos, atomicidad y confirmación; validar independientemente antes de editar/disponibilidad. MVP no se presenta como US 5.5 completa.
4. Añadir US2 con historial/versiones/conflictos y ambas ordenaciones con crear_estudio.
5. Añadir US3 con desactivación/reactivación/eliminación y protección concurrente; luego controles completos y Chrome antes del cierre.
6. Fuera de alcance: nuevo catálogo/entidades, fórmulas, límites, modelos de idempotencia administrativa, migraciones, CRUD de pruebas y escritura de estudios desde catálogo. No commit/push/PR/merge implícitos en tasks.

## Coverage Summary

| Requisito | Tareas principales |
|---|---|
| FR-001 | T004,T006,T009,T014,T018,T033,T039,T042 |
| FR-002 | T008,T009,T011,T012,T015 |
| FR-003 | T008,T009,T011,T012 |
| FR-004 | T008,T011,T012,T020,T024,T025,T032,T036 |
| FR-005 | T020,T021,T024,T025,T027,T029,T030 |
| FR-006 | T020,T021,T024,T031,T043 |
| FR-007 | T004,T032,T033,T035,T036,T037,T039,T043 |
| FR-008 | T032,T033,T035,T036,T039,T043 |
| FR-009 | T005,T007,T009,T010,T013,T014,T015,T016,T021,T022,T026,T027,T028,T029,T033,T034,T038,T039,T040,T042 |
| FR-010 | T008,T010,T011,T020,T023,T024,T032,T034,T035,T036,T037,T043 |
| FR-011 | T008,T011,T015,T019,T046 |
| FR-012 | T004,T006,T017,T021,T023,T027,T031,T035,T037,T043 |
| FR-013 | T008,T011,T020,T023,T024,T035,T043 |
| FR-014 | T004,T005,T006,T007,T009,T010,T013,T014,T018,T021,T022,T026,T027,T030,T033,T034,T038,T039,T040,T041,T042 |
| FR-015 | T008,T009,T011,T012,T020,T025 |
| FR-016 | T020,T021,T024,T031,T043 |
| FR-017 | T005,T007,T020,T021,T022,T023,T024,T026,T027,T028,T029,T032,T034,T035,T036,T038,T042 |
| FR-018 | T032,T033,T034,T035,T036,T038,T039,T040,T041,T042,T043 |
| FR-019 | T032,T033,T034,T035,T037,T038,T039,T040,T041,T042,T043 |
| SC-001/002/005/006 | T008,T009,T010,T011,T019,T020,T032,T043,T045 |
| SC-003/007/009 | T020,T021,T022,T023,T024,T031,T035,T043 |
| SC-004/010/011 | T032,T033,T034,T035,T036,T037,T043 |
| SC-008 | T004,T009,T020,T033,T042 |

| Escenarios de spec | Tests y verificación |
|---|---|
| US1 1–7 (7) | T008/T009/T010 → T019 |
| US2 1–11 (11) | T020/T021/T022/T023 → T031 |
| US3 1–7 (7) | T032/T033/T034/T035 → T042/T043 |
| Reactivación/eliminación 1–8 (8) | T032/T033/T034/T035 → T042/T043 |

## Notes y estado de generación

### Aprobación y autorización — 28/10/2026

El usuario comunica expresamente que el equipo aprobó la especificación completa de US 5.5 (012), incluidos FR-018 (reactivación) y FR-019 (eliminación de tipos nunca utilizados), y autoriza comenzar la implementación mediante el Spec Kit original. Esta comunicación satisface T001; no se aportan ni se inventan nombres de aprobadores, actas o enlaces. Los párrafos de generación siguientes conservan el estado histórico anterior a esta autorización. La validación manual en Chrome sigue pendiente hasta su ejecución efectiva por el usuario.


Generado con setup-tasks.sh --json y TASKS_TEMPLATE_CONTENT del template original, sin hooks: no existe .specify/extensions.yml antes/después. Todas las tareas pendientes; ningún código, tests, datos o migraciones ejecutados en esta entrega. La aceptación del diseño para generar tasks está documentada por el usuario; aprobación formal global del equipo y autorización de implementación siguen pendientes. Jira administrativo pendiente, sin fuente científica externa necesaria: FIUBA y datos DEMO. No se modifica spec/plan/contratos/checklist para declarar avances ni se ejecuta speckit-implement. Este archivo será validado por formato, IDs, rutas, dependencias, paralelismo y cobertura de 19 FR/11 SC antes de entregarlo.


## Validación documental de esta generación

50 tareas pendientes (0 ejecutadas). Distribución: Setup 2, Foundational 5, US1 12, US2 12, US3 12 y cierre 7. IDs T001–T050 consecutivos, formato de checklist y etiquetas por fase correctos, rutas presentes y dependencias sin ciclos/referencias futuras. Revisadas 28 tareas [P] en 10 grupos con archivos distintos y sin dependencias internas. Matriz de 19/19 FR y 11/11 SC; 33 escenarios asignados a tests por historia. La cobertura es del plan de trabajo: no acredita tests ejecutados ni código implementado. No hay hooks before_tasks/after_tasks porque no existe extensions.yml.

### Revisión de cobertura T044 — 28/10/2026

Se contrastaron los 19 FR, 11 SC y 33 escenarios con los tests existentes, sin cambiar requisitos para adaptarlos al código. Se añadieron casos faltantes de cancelación desde formulario, primera utilización durante revisión de eliminación, disponibilidad, cuentas inactivas, paginación y nombres equivalentes entre gestores distintos. Dos defectos UI se reprodujeron primero y corrigieron: enlace a desactivar cuando aparece el primer estudio, y cancelación del borrador al volver al formulario. Un fallo adicional fue de preparación de test (empleado y gestor comparten fixture); se separó la cuenta sin permiso.

Evidencia: 98 tests administrativos aprobados (278.04s); ampliación UI/tokens tras cancelación: 48 aprobados (26.44s). Los cuatro casos HTTP consumidor/escritor real — nombre, descripción, composición y desactivación — aprobaron (13.25s). PostgreSQL real y tiempos de espera acotados; las carreras verifican pg_blocking_pids, no mocks de locks. La suite general posterior valida el conjunto final.

Archivos de referencia: S = estudios/tests/test_gestion_tipos_servicio.py; U = test_gestion_tipos_ui.py; C = test_gestion_tipos_concurrencia.py; F = test_gestion_tipos_confirmaciones.py, todos dentro de estudios/tests/.

| Escenario | Tests automatizados reales (prefijo test_) |
|---|---|
| US1 1 | S alta_exacta_y_reenvio; U alta_resumen_volver_cancelar_y_exito |
| US1 2 | S alta_invalida_no_guarda; U formulario_vacio_errores_catalogo_y_csrf |
| US1 3 | S alta_invalida_no_guarda; U prueba_desaparece_antes_confirmacion |
| US1 4 | U formulario_vacio_errores_catalogo_y_csrf |
| US1 5 | U alta_resumen_volver_cancelar_y_exito; cancelar_desde_formulario_al_volver_invalida_resumen |
| US1 6 | S unicidad_tildes_espacios_y_descripcion_vacia; editar_inactivo_y_no_quitar_ultima |
| US1 7 | S unicidad_tildes_espacios_y_descripcion_vacia |
| US2 1 | S historial_y_estudio_futuro |
| US2 2 | S editar_inactivo_y_no_quitar_ultima |
| US2 3 | S edicion_unicidad_y_referencias_invalidas |
| US2 4 | S historial_y_estudio_futuro |
| US2 5 | U consumidor_ui_exige_reconfirmar_escritor_real |
| US2 6 | C edicion_con_creacion |
| US2 7 | U edicion_cancelacion_noop_y_catalogo_preservado; S edicion_rollback |
| US2 8 | U conflicto_desde_apertura_y_confirmacion |
| US2 9 | C dos_editores; S noop_sin_dml_y_stale_no_se_acepta |
| US2 10 | U conflicto_desde_apertura_y_confirmacion |
| US2 11 | S edicion_rollback |
| US3 1 | S proteccion_cualquier_historia; U usado_no_elimina_y_ofrece_desactivacion |
| US3 2 | S proteccion_cualquier_historia; disponibilidad_version_y_noop |
| US3 3 | U consumidor_ui_exige_reconfirmar_escritor_real (desactivar) |
| US3 4 | U operaciones_resumen_cancelacion_y_exito (desactivar) |
| US3 5 | U acceso_sin_permiso; todas_acciones_protegidas (anónimo) |
| US3 6 | U acceso_sin_permiso; todas_acciones_protegidas |
| US3 7 | U alta_resumen_volver_cancelar_y_exito; operaciones_resumen_cancelacion_y_exito |
| Reactivación/eliminación 1 | S reactivado_disponible_y_revision_anterior_rechazada |
| Reactivación/eliminación 2 | S legado_vacio_no_reactiva_pero_se_retira |
| Reactivación/eliminación 3 | U todas_acciones_protegidas; S servicio_sin_permiso_rechaza |
| Reactivación/eliminación 4 | U operaciones_resumen_cancelacion_y_exito; S legado_vacio_no_reactiva_pero_se_retira |
| Reactivación/eliminación 5 | S proteccion_cualquier_historia (todos los estados); U confirmar_eliminar_si_aparece_primer_estudio |
| Reactivación/eliminación 6 | C disponibilidad_eliminacion_con_creacion (ambos órdenes) |
| Reactivación/eliminación 7 | U operaciones_resumen_cancelacion_y_exito; S eliminar_rollback; disponibilidad_rollback_y_sin_historia_alterada |
| Reactivación/eliminación 8 | S disponibilidad_version_y_noop; C dos_operaciones_misma_version; U conflicto_desde_apertura_y_confirmacion |

| Requisitos | Evidencia automatizada complementaria |
|---|---|
| FR-001/014; SC-008 | Guardias de servicio/GET/POST; staff sin permiso; cuenta inactiva; permiso revocado; enlace oculto; CSRF y F fases/sesión. |
| FR-002/003/004/015; SC-001/002 | Alta y edición inválidas, referencias existentes, selección no vacía, deduplicación, nombre propio/existente, tildes/espacios y descripción exacta/vacía. |
| FR-005/006/016; SC-003 | Edición conserva PK/activo; historial_y_estudio_futuro acredita textos, creador/hora y asignaciones, incluso descripción histórica vacía; consumidor HTTP usa el escritor real. |
| FR-007/008; SC-004 | Protección en todos los estados, tipo inactivo, rechazo de revisión previa, catálogo consumidor y carreras de disponibilidad/eliminación. |
| FR-009; SC-005 | Resumen/volver/cancelación en ambas pantallas y cada operación; tokens, TTL, múltiples pestañas y reenvíos; rollback en cabecera/composición/disponibilidad/delete. |
| FR-010/013/017; SC-007/009 | No-op sin DML; stale antes de no-op; incremento único; rollback; ambas ordenaciones con creación; dos editores; altas/ediciones por nombre equivalente. |
| FR-011; SC-006 | Prueba conserva cantidad/identidad al crear y eliminar; ningún escritor de definiciones científicas ni seeds automáticos. |
| FR-012 | Mismos modelos y consumidor; lector administrativo incluye legado vacío/inactivo; servicio crear_estudio y modelos sin cambios; tests de integración reales. |
| FR-018; SC-010 | Reactivación válida, sin pruebas rechazada, permiso/versiones, consumidor disponible e historial preservado. |
| FR-019; SC-011 | Borrado solo nunca usado, Prueba conservada, PROTECT, rollback y ambas ordenaciones frente al primer estudio. |

No queda un escenario sin cobertura automatizada identificada. Esto no sustituye la validación manual pendiente ni acredita CI remoto/revisión de código por otro integrante.


### Verificación general T045 — 28/10/2026

- `docker exec aqualab-us55-qa pytest -q --tb=short`: **526 passed in 301.97s**. Suite completa, incluidos los tests transaccionales de concurrencia e idempotencia integrados y los nuevos administrativos.
- PostgreSQL real **16.15**; base QA `aqualab_us55`, tests en `test_aqualab_us55`; conexiones independientes y comprobación efectiva de bloqueo mediante pg_blocking_pids. Ningún SQLite ni mock de locks.
- `docker exec aqualab-us55-qa ruff check .`: All checks passed.
- `docker exec aqualab-us55-qa ruff format --check .`: 121 files already formatted.
- `docker exec aqualab-us55-qa python manage.py check`: sin problemas.
- `docker exec aqualab-us55-qa python manage.py makemigrations --check --dry-run`: No changes detected.
- `docker exec aqualab-us55-qa python manage.py migrate --check`: exit 0; migraciones existentes aplicadas en QA, ninguna nueva generada.
- `node --test usuarios/tests/js/sesion.test.cjs`: 14 aprobados, 0 fallos.

Estado: T001–T045 completadas con evidencia. T046 parcialmente preparada: faltan cuentas QA activas y carga explícita DEMO para completar el recorrido. La base propia nueva tiene 0 usuarios; no se crean ni copian cuentas automáticamente. T047 (Chrome) no realizada; T048–T050 siguen pendientes por sus dependencias de manual/evidencia/inventario/cierre. No hay aprobación remota de código o CI inventada. Ningún commit, push, PR ni merge.

### Estado de cierre parcial — 28/10/2026

Servidor QA `aqualab-us55-web-qa` preparado en puerto 8012. Smoke HTTP: GET /estudios/tipos/ sin sesión redirige 302 al login. No es evidencia Chrome. T046 sigue pendiente de cuentas y carga DEMO explícitas en la base propia nueva; instrucciones reproducibles en quickstart.md. T047–T050 no completadas por dependencia de la validación manual. Se verificó git diff --check sin errores, staging vacío y ausencia de cambios en modelos/migraciones, consumidor de US 5.1/5.2, muestras, Constitution e instalación de Spec Kit. Solo se añadieron rutas/navegación de gestión y fixtures propias a archivos compartidos. No existe extensions.yml: no hay hooks before_implement/after_implement que ejecutar. Sin commit, push, PR ni merge.

### T046 completada — 28/10/2026

Por autorización expresa del usuario, se prepararon únicamente en aqualab-us55 las cuentas activas gestor.us55@aqualab.test (permiso específico gestionar_catalogo) y comun.us55@aqualab.test (sin permiso), ambas sin staff/superusuario. Contraseñas aleatorias solo en memoria, no publicadas ni grabadas en archivos; quickstart documenta changepassword interactivo para que el usuario establezca las propias.

Se verificaron base aqualab_us55, red aqualab-us55_default y volumen aqualab-us55_postgres_data, distintos del otro proyecto. Cargar_demo_us51: dry-run correcto → aplicar autorizado → simulación posterior reutiliza todo. Conteos comprobados: 2 clientes, 2 orígenes, 2 muestras (PI 200001/200002), 3 pruebas y 4 tipos base US51; 0 estudios y 0 tipos adicionales US55. Detalle y comandos exactos en quickstart.md.

Login HTTP real de ambas cuentas verificado con cookies/CSRF: gestor GET gestión 200; común GET/POST 403; sin sesión 302 al login en puerto 8012. No es recorrido Chrome. T047 sigue pendiente; también T048–T050 por sus dependencias. Estado actual: 46/50 completas. Sin cambios de código ni migraciones, sin modificaciones de otros worktrees, sin commit/push/PR/merge.


### T047/T048 — 28/10/2026

El usuario informó validación satisfactoria de nueve casos Chrome en QA US 5.5: alta, edición/versionado, duplicados/vacíos, desactivación, reactivación, historial, borrado usado rechazado, borrado nunca usado sin borrar pruebas y acceso sin permiso rechazado. Detalle y limitaciones en quickstart.md. Evidencia informada por el usuario, sin observación directa de Codex, capturas ni HTTP inventados. No se equipara el reporte de nueve casos con los doce pasos originales. La evidencia de concurrencia/rollback corresponde a tests PostgreSQL, no al navegador.

Aprobación T001 comunicada por el usuario el 28/10/2026 (spec completa y FR-018/019). Evidencia automatizada anterior: 526 pytest en PostgreSQL 16.15 y 14 JavaScript; controles Ruff/Django/migraciones aprobados. Reejecución de cierre en curso, se registrará resultado antes de cerrar T050. Jira pendiente administrativo; CI remoto y revisión de código de otro integrante aún no realizados, sin sustituirlos por la aprobación de spec.


### T049 — inventario verificado (28/10/2026)

inventario-commit.md enumera exactamente 30 archivos (6 modificados versionados y 24 nuevos), incluidos inventario y cierre. Coincide con git diff --name-only + git ls-files --others --exclude-standard. Se revisaron los seis diffs compartidos y los módulos de gestión, permisos, versionado, tokens y eliminación; no se detectaron cambios ajenos. Escaneo de claves privadas y URLs de base con credenciales sin hallazgos en los archivos candidatos. Passwords literales de fixtures son sintéticos, no secretos QA. Respaldos/.env/cachés/contexto local ignorado excluidos; datos QA permanecen en el volumen Docker, sin exportar. Staging vacío, git diff --check correcto. No se eliminaron respaldos.


### T050 — cierre técnico verificado (28/10/2026)

Suite final: 526 passed in 346.77s, PostgreSQL real aislado; 14 JavaScript aprobados. Ruff check/format, Django check, makemigrations --check --dry-run y migrate --check correctos. Revisión final de spec/plan/contratos y cobertura de 19 FR, 11 SC y 33 escenarios sin bloqueos técnicos identificados. Nueve casos Chrome informados por el usuario, sin observación directa de Codex. Ver cierre-tecnico.md e inventario-commit.md (30 archivos). T001–T050 completas; checklist 16/16 sin tocar. Staging vacío; rama/HEAD intactos, sin commit/push/PR/merge/rebase ni cambios ajenos. Pendientes administrativos: Jira, CI remoto y revisión de código del futuro PR. Esta conclusión no afirma que esos controles remotos ya existan.
