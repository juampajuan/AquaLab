# Tasks: US 5.1 — Crear estudio sobre una muestra

## Estado vigente de cierre — 27/10/2026

**40/40 tareas completas.** T037 se cierra con la confirmación manual del usuario en este chat, T039 con su registro y límites reales, y T040 con revisión de consistencia, controles finales e inventario. Los recuentos anteriores 37/40 y referencias a validación pendiente se conservan como historial, no describen el estado vigente.

- Manual informado por el usuario: PI 200001, Bacteriológico con 2 pruebas, resumen/volver, confirmación pendiente de análisis, reenvío sin duplicación observada, segunda solicitud del mismo tipo, PI 200002 de cliente inactivo, cancelación y tipo desactivado no disponible. Informa además cargar_demo_us51 --aplicar correcto, sin estudios precargados. No se inventan capturas, logs ni observación directa del asistente.
- Revalidación automatizada final: **361 passed in 180.10s**; **14 tests JS aprobados**. Ruff check/format --check, Django check, makemigrations --check --dry-run, migrate --check y git diff --check pasan. Tests PostgreSQL aislados; no modificaciones de datos locales en este cierre.
- Revisión original speckit-analyze: 20 FR y 7 SC con tareas asociadas (100% documental), sin contradicciones técnicas bloqueantes. Se corrigieron referencias documentales superadas a supuestos y catálogo externo; sin cambios funcionales. Detalle en cierre-tecnico.md.
- Inventario: **50 archivos**, 4 modificados + 46 nuevos, en inventario-commit.md. Sin staging ni commit; respaldos, cachés, secretos y otros worktrees excluidos. Constitution, Spec Kit y US 5.5 intactos.
- No hay validación científica externa pendiente: proyecto académico FIUBA. Quedan para el futuro PR CI remoto y revisión de otro integrante, más el pendiente administrativo Jira. La gestión de catálogo US 5.5 reutilizará esta base posteriormente.

**Input**: Design documents from `specs/008-crear-estudio/`.
**Prerequisites**: spec.md, plan.md, research.md, data-model.md, contracts/ y quickstart.md revisados para generación documental. La aprobación de la spec está acreditada por la confirmación expresa del usuario en este chat; el plan y la implementación fueron autorizados. No hay acta ni enlace externo aportado.
**Tests**: Obligatorios por petición del usuario y Constitution: un test por escenario de aceptación, incluidos contratos y concurrencia. Al generarse esta lista no se habían ejecutado tests; el cierre y los resultados reales se registran al final.
**Organization**: Fases compartidas de catálogo y dos historias de usuario de spec.md. US1/US2 aquí no son US 5.1/5.5 del backlog: son los recorridos P1/P2 dentro de US 5.1.

## Format: `[ID] [P?] [Story] Description`

Estado de ejecución: consultar las marcas de cada tarea y el registro de cierre al final. Rutas relativas al checkout E:/Martino-Codex/AquaLab. [P] solo permite edición paralela en archivos diferentes una vez resueltas dependencias comunes; no autoriza crear agentes ni ejecutar tareas ahora. No se hacen commits automáticos ni se modifica US 5.5.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Puerta de aprobación y estructura mínima; reutilizar Django, Docker, auth, Bootstrap y CI existentes.

- [X] T001 Registrar en specs/008-crear-estudio/checklists/requirements.md la aprobación formal de spec y revisión requerida del plan por el equipo cuando exista evidencia real, confirmando autorización de implementar; si falta, detener toda tarea de código T002 en adelante. Registrar FR-013/014 como decisiones funcionales definitivas del proyecto, sin atribuir validación directa al laboratorio; mantener fuente/responsable de precarga oficial abiertos; Jira no se inventa (FR-013, FR-014).
- [X] T002 Crear únicamente estructura vacía de apps previstas en pruebas/__init__.py, pruebas/apps.py, pruebas/migrations/__init__.py, pruebas/tests/__init__.py, estudios/__init__.py, estudios/apps.py, estudios/migrations/__init__.py y estudios/tests/__init__.py; registrar apps en config/settings.py sin sustituir infraestructura existente, sin admin editable, CRUD de catálogo ni datos de producción (FR-019; depende T001).

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Base persistente compartida y lectura coherente; sin implementar la administración de US 5.5.

- [X] T003 Definir factories sintéticas aisladas en estudios/tests/conftest.py para usuario aprobado, clientes activos/inactivos, Muestra integrada, pruebas TEST-A/TEST-B y tipos genéricos; referencias científicas solo id/código/nombre, sin fórmulas/límites/unidades; helpers de mutación exclusivamente de test toman lock del tipo y aumentan versión en atomic. No fixtures autoload ni seeds fuera de la base de pytest (FR-012, FR-020; depende T002; se utilizarán tras crear modelos).
- [X] T004 Escribir tests de representación mínima y constraints en pruebas/tests/test_modelo.py: código único, vacío/espacios, longitud, nombre obligatorio y recorte; documentar fallo previo a implementación y no crear datos de producción (FR-019/020; depende T002).
- [X] T005 Implementar únicamente Prueba en pruebas/models.py con «id: BigAutoField, identidad estable», «codigo: CharField(50), obligatorio, unique, espacios laterales recortados, comparación exacta (mayúsculas distinguen); Check no vacío» y «nombre: CharField(150), obligatorio, recortado; Check no vacío»; validar límites en full_clean y sin campos científicos adicionales (FR-019; depende T004).
- [X] T006 Escribir tests de catálogo mínimo en estudios/tests/test_modelos.py para nombre único sin mayúsculas/espacios laterales, diferencias de tildes/espacios internos, descripción vacía, versión >=1, relación no duplicada y Prueba protegida si está referenciada; sin implementar mutadores de catálogo (FR-019; depende T003/T005).
- [X] T007 Implementar TipoEstudio y TipoEstudioPrueba en estudios/models.py: «id: BigAutoField», «nombre: CharField(150), obligatorio, recortado; UniqueConstraint Lower(nombre), Check no vacío. Tildes/espacios internos distinguen», «descripcion: TextField(blank=True, default=""), no NULL; opcional», «activo: BooleanField(default=True)», «version: PositiveBigIntegerField(default=1), Check >=1», «pruebas: ManyToManyField a pruebas.Prueba mediante TipoEstudioPrueba»; through con «id BigAutoField; tipo FK TipoEstudio CASCADE; prueba FK Prueba PROTECT. UniqueConstraint(tipo, prueba)». Declarar permiso gestionar_catalogo sin asignarlo automáticamente ni exigirlo al creador de estudios; no CRUD ni admin de tipos (FR-019; depende T006).
- [X] T008 Generar y revisar pruebas/migrations/0001_initial.py y estudios/migrations/0001_initial.py solo para Prueba, TipoEstudio y TipoEstudioPrueba con constraints definidos; estudios inicial depende de pruebas inicial, no de Estudio aún no creado. Aplicar solo en desarrollo/test tras revisar dependencias; sin migraciones de datos ni tocar muestras/migrations/ (FR-019/020; depende T005/T007).
- [X] T009 Implementar lectura coherente del catálogo en estudios/catalogo.py: atomic y bloqueo de TipoEstudio al preparar configuración, validar activo/conjunto no vacío/referencias existentes, devolver id/textos/versión y conjunto id/código/nombre como copia íntegra. Añadir pruebas en estudios/tests/test_catalogo_contrato.py; helpers de escritura quedan exclusivamente en tests. Verificar invariantes y migraciones de base con PostgreSQL, sin publicar un servicio de administración US 5.5 (FR-003, FR-004, FR-007, FR-019; depende T008).

**Checkpoint**: La base del catálogo es única; ningún CHECK del M2M se presenta como garantía de conjunto no vacío. El consumidor valida y el futuro escritor US 5.5 deberá cumplir el protocolo compartido.

## Phase 3: User Story 1 - Crear un estudio con las pruebas de su tipo (Priority: P1)

**Goal**: Selección, resumen, confirmación y creación íntegra con pruebas propias y snapshots.
**Independent Test**: Con muestras y catálogo sintético de pytest, crear un estudio, comprobar estado/autor/hora/snapshots/asignaciones, cancelar otro y verificar que no existe; no depende de CRUD US 5.5 ni de datos científicos oficiales.

### Tests for User Story 1

- [X] T010 [US1] Extender estudios/tests/test_modelos.py con tests de Estudio/PruebaEstudio: UUID obligatorio único, PK distinta de PI, sin unicidad muestra/tipo, FK PROTECT y asignaciones únicas; validar límites/choices/full_clean y mostrar fallo antes de modelos de estudio (FR-005, FR-009, FR-013, FR-016/019; depende T009).
- [X] T011 [US1] Añadir Estudio en estudios/models.py con «id: BigAutoField; identificador numérico único, huecos permitidos. No es el PI», «muestra: FK muestras.Muestra PROTECT, related_name="estudios"», «tipo: FK TipoEstudio PROTECT, related_name="estudios"», «estado: CharField(30), choice pendiente_analisis / Pendiente de análisis, default y editable=False», «creado_por: FK AUTH_USER_MODEL PROTECT, related_name="estudios_creados", editable=False», «fecha_creacion: DateTimeField(auto_now_add=True)», «tipo_nombre_snapshot: CharField(150), obligatorio, editable=False», «tipo_descripcion_snapshot: TextField(blank=True, default=""), editable=False», «tipo_version_snapshot: PositiveBigIntegerField, Check >=1, editable=False» y «clave_idempotencia: UUIDField(unique=True, null=False, editable=False), generado por servidor al preparar solicitud»; no duplicar cliente/origen ni agregar estados futuros (FR-005, FR-009, FR-010, FR-013, FR-016/018; depende T010).
- [X] T012 [US1] Añadir PruebaEstudio en estudios/models.py con «id BigAutoField; estudio FK Estudio PROTECT; prueba FK Prueba PROTECT; UniqueConstraint(estudio, prueba), related_name="pruebas_asignadas" en estudio»; sin mediciones/resultados/estado científico y sin unicidad muestra/tipo (FR-004, FR-010, FR-019; depende T011).
- [X] T013 [US1] Generar y revisar estudios/migrations/0002_estudio.py con Estudio/PruebaEstudio y sus constraints; depender de estudios/0001_initial, muestras/0002_clave_borrador y swappable_dependency(AUTH_USER_MODEL), sin alterar Muestra ni migraciones integradas. Comprobar migración sobre esquema existente y ejecutar tests de T010 (FR-019; depende T012).
- [X] T014 [P] [US1] Escribir en estudios/tests/test_servicio.py casos US1 4/7/8: composición exacta, estado pendiente_analisis, snapshots del servidor, creador/hora no manipulables y nueva solicitud legítima de distinto tipo; expresar guardado atómico e idempotencia básica como criterios, sin ejecutar código de catálogo futuro (FR-004/005, FR-008/011, FR-016/018; depende T013).
- [X] T015 [P] [US1] Escribir en estudios/tests/test_registro.py casos US1 1/2/3/5: etiquetas PI/cliente/origen, tipos activos, resumen exacto sin guardar, volver conserva selección, cancelar sin filas y éxito con ID/PI/formulario vacío; comprobar mismos datos del resumen y versión firmada (FR-002/003, FR-006, FR-011; depende T013).
- [X] T016 [P] [US1] Escribir en estudios/tests/test_catalogo_contrato.py US1 6 y escenarios de FR-018: renombrar, editar/vaciar descripción, cambiar composición y desactivar después de crear; asignaciones, snapshots, autor y hora anteriores intactos, incluida descripción inicialmente vacía (FR-010, FR-018; depende T013).

### Implementation for User Story 1

- [X] T017 [US1] Implementar estudios/confirmaciones.py para preparar UUID servidor y token firmado con salt estudios.creacion.v1, TTL 3600s, UUID/usuario/huella HMAC de sesión/muestra_id/tipo_id/version; mapa de pendientes por UUID con copia íntegra del resumen. No exponer sessionid ni aceptar snapshots del POST; una nueva solicitud o selección editada recibe UUID nuevo. No inferir confirmación de la sesión más reciente (FR-006, FR-009, FR-015, FR-018; depende T014/T015/T016).
- [X] T018 [US1] Implementar formulario de selección en estudios/forms.py con Muestra integrada sin filtrar cliente activo y TipoEstudio activo; errores por campo, versión/configuración preparadas desde catálogo servidor, sin campos editables de creador/hora/snapshots/idempotencia ni permiso gestionar_catalogo para empleados que crean estudios (FR-001/003, FR-007, FR-014, FR-016; depende T017).
- [X] T019 [US1] Implementar creación en estudios/servicios.py: atomic → pg_advisory_xact_lock(5_100_001) → buscar UUID persistido y validar creador/muestra/tipo antes de devolver existente → exigir pendiente para solicitud aún no creada → select_for_update del tipo → validar activo/version/conjunto → crear Estudio y PruebaEstudio con snapshots desde servidor. Capturar DatabaseError fuera de atomic; no reutilizar clave ni servicio registrar_muestra (FR-004/005, FR-008/010, FR-015/018; depende T018).
- [X] T020 [US1] Implementar flujo y rutas de selección/resumen/confirmación/volver/cancelar en estudios/views.py y estudios/urls.py según contracts/crear-estudio-ui.md; GET muestra la copia revisada asociada al token, no catálogo nuevo con token viejo; autenticación/CSRF existentes, éxito después de commit, cancelación retira UUID pendiente sin borrar estudios (FR-001/003, FR-006, FR-011, FR-016; depende T019).
- [X] T021 [P] [US1] Crear estudios/templates/estudios/crear_form.html con base.html, etiquetas de muestra PI/cliente/origen, tipos disponibles, errores Bootstrap y mensaje de catálogo vacío; sin definiciones científicas, altas de catálogo ni datos de producción (FR-002/003, FR-007, FR-012, FR-020; depende T020).
- [X] T022 [P] [US1] Crear estudios/templates/estudios/crear_confirmar.html con muestra/tipo/nombre/descripcion/pruebas de la copia revisada, token oculto, Confirmar/Volver/Cancelar y CSRF; no regenerar silenciosamente confirmación al renderizar una versión nueva (FR-004, FR-006, FR-018; depende T020).
- [X] T023 [US1] Conectar estudios/urls.py desde config/urls.py y añadir enlaces en templates/base.html y templates/inicio.html; conservar navegación/guardia de sesión existente y acceso solo autenticado, sin permisos de administración de catálogo como requisito de crear estudios (FR-001/002, FR-011; depende T021/T022).
- [X] T024 [US1] Ejecutar tests US1 con PostgreSQL y registrar resultados reales en specs/008-crear-estudio/quickstart.md, verificando T014/T015/T016 y escenarios US1 1 a 8; no declarar el MVP listo si falta idempotencia o atomicidad del servicio base. No marcar evidencia manual no realizada (FR-001/020; depende T023).

**Checkpoint**: US1 verificable sobre catálogo compartido aislado, no un despliegue científico listo para producción. Ningún admin o CRUD de tipos añadido.

## Phase 4: User Story 2 - Evitar estudios incompletos o creaciones accidentales (Priority: P2)

**Goal**: Completar rechazo de entradas inválidas, reenvíos, conflicto/recuperación y concurrencia, respetando las decisiones funcionales definitivas FR-013/014.
**Independent Test**: US2 1 a 11 sobre base aislada: un estudio por solicitud, nuevas solicitudes válidas, rollback completo y resumen actualizado con nueva confirmación; no requiere US 5.5 implementada.

### Tests for User Story 2

- [X] T025 [P] [US2] Extender estudios/tests/test_registro.py con US2 1/2/3/6/8: cada faltante, referencias inválidas, tipo vacío/inactivo, catálogo vacío, anónimo/cuenta no aprobada/CSRF y cliente ya inactivo o desactivado durante revisión; cero filas parciales y cliente sin reactivar (FR-001, FR-007, FR-012, FR-014, FR-020; depende T024).
- [X] T026 [P] [US2] Crear estudios/tests/test_confirmaciones.py para firma manipulada, ausencia, usuario/sesión ajenos, expiración, cancelar seguido de token viejo, pestañas separadas, UUID ajeno/muestra/tipo diferentes y recuperación que conserva UUID; token inválido no hace lookup de otro usuario ni crea. Cubrir que confirmar expirado no guarda y recuperar solo consulta/renueva resumen (FR-001, FR-006, FR-009, FR-015/018; depende T024).
- [X] T027 [P] [US2] Crear estudios/tests/test_concurrencia.py con django_db(transaction=True), conexiones por hilo, events/barriers y timeout/join acotados: mismo UUID simultáneo → mismo ID/un conjunto; UUID distintos misma muestra/tipo → estudios distintos; creador bloquea primero → configuración anterior íntegra; editor bloquea primero → conflicto/nueva confirmación; desactivación primero → rechazo. Asegurar hilos terminados y recoger errores (FR-008/010, FR-013, FR-015, FR-018; depende T024).
- [X] T028 [P] [US2] Extender estudios/tests/test_servicio.py con US2 4/5/7: falla de una asignación revierte estudio/UUID/asignaciones y permite reintento; clave persistida reused con mismo creador/selección devuelve historial incluso tras cambio/desactivación; misma clave con otra operación rechazada; otra solicitud legítima misma muestra/tipo crea otro estudio sin modificar el previo (FR-008/010, FR-013, FR-016; depende T024).
- [X] T029 [US2] Extender estudios/tests/test_catalogo_contrato.py con US2 9/10/11 y textos: cambios sucesivos exigen nueva aceptación; POST viejo tras resumen actualizado no crea; cambio solo nombre/descripcion también exige revisión; comprobar helper de futuro escritor con lock tipo, incremento una vez por cambio efectivo de nombre/descripcion/activo/composición y no incremento por no-op/rollback. No publicar ese helper como CRUD US 5.5 (FR-010, FR-015, FR-018/019; depende T025/T026/T027/T028).

### Implementation for User Story 2

- [X] T030 [US2] Completar recuperación y seguridad en estudios/confirmaciones.py según contrato: firma criptográfica/usuario/sesión válidos para recuperar un token vencido no autorizan crear; devolver solo resultado propio o renovar resumen del UUID aún pendiente, sin revivir cancelados; UUID no recuperable requiere nueva operación explícita, no auto-generación silenciosa (FR-001, FR-006, FR-009, FR-015; depende T029).
- [X] T031 [US2] Completar rechazos y concurrencia del servicio en estudios/servicios.py: comparar UUID por identidad creador+muestra+tipo, no catálogo actual al devolver resultado previo; validar íntegramente configuración nueva bajo lock y reconstruir conflicto solo con copia coherente. No actualizar historial existente ni capturar errores dentro de transacción rota; mantener asignación única (FR-004, FR-007/010, FR-013/018; depende T030).
- [X] T032 [US2] Completar estudios/views.py y estudios/templates/estudios/crear_confirmar.html con accion=recuperar, mensajes/rechazos y resumen/token nuevos juntos al cambiar versión, manteniendo UUID; confirmar expirado rechaza, POST anterior jamás confirma conjunto nuevo y cancelar no crea ni elimina filas. Mantener decisiones funcionales definitivas FR-013/014 y no exigir activo de Cliente al crear Estudio (FR-006/009, FR-013/015, FR-018; depende T031).
- [X] T033 [US2] Ejecutar tests US2 y de concurrencia con PostgreSQL, registrar comandos y resultados reales en specs/008-crear-estudio/quickstart.md; comprobar todas las ordenaciones y ausencia de hilos pendientes, rollback, snapshots y asignaciones únicas. Si fallan, corregir solo implementación autorizada y volver a verificar antes de continuar (FR-001/020; depende T032).

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Evidencia real, revisión de contrato y cierre condicionado; sin desarrollo de US 5.5 ni carga científica de producción.

- [X] T034 Revisar trazabilidad de los 20 FR y escenarios US1/US2 en specs/008-crear-estudio/plan.md y estudios/tests/; comprobar que cada escenario tiene al menos un test automatizado relevante y que el contrato de catálogo no se valida solo con tests que imitan su implementación (depende T033).
- [X] T035 Ejecutar check, makemigrations --check --dry-run, suite completa pytest, ruff check/format --check y node --test usuarios/tests/js/sesion.test.cjs conforme a specs/008-crear-estudio/quickstart.md; registrar resultados, no éxitos supuestos, y verificar que las migraciones no incluyen datos sintéticos (depende T034).
- [X] T036 Preparar pasos manuales detallados y resultados esperados en specs/008-crear-estudio/quickstart.md para usuario: crear/resumen/cancelar/volver, doble envío, clientes inactivos, cambios de catálogo solo mediante helper aislado de tests o entorno expresamente controlado; no pedir cargar fixtures sintéticas en producción ni implementar un admin para poder probar (depende T035).
- [X] T037 Realizar o solicitar al usuario la validación manual prevista en specs/008-crear-estudio/quickstart.md en entorno aislado autorizado y registrar quién/cuándo/casos/resultados; dejar pendiente lo no probado. Los tests concurrentes automatizados no se sustituyen por doble clic manual (depende T036).
- [X] T038 Revisar y actualizar únicamente specs/008-crear-estudio/contracts/catalogo-compartido.md con los nombres/campos/migraciones efectivamente implementados y garantías de reutilización por futura US 5.5; no modificar su worktree, desarrollar su CRUD, duplicar modelos ni atribuir aprobación pendiente del equipo sobre sus operaciones (depende T035).
- [X] T039 Registrar en specs/008-crear-estudio/checklists/requirements.md y plan.md estado real de aprobación formal, decisiones del proyecto FR-013/014, contrato y datos demo académicos (manifiesto/mecanismo/códigos ficticios), distinguiendo tests sintéticos de uso productivo. Si cambia una decisión externa, revisar spec y diseño antes de implementar la nueva regla; Jira no se inventa (depende T037/T038).
- [X] T040 Inspeccionar diff y archivos generados contra specs/008-crear-estudio/data-model.md y contratos, verificar solo alcance US 5.1/base compartida autorizada, ningún dato demo presentado como validación científica oficial ni cambio de US 5.5, y presentar evidencias para revisión final sin commit/push/merge automáticos (depende T039).

## Dependencies & Execution Order

- T001 es puerta real antes de cualquier código. La autorización expresa posterior del usuario cubre implementar y verificar, sin commits/push/PR/merge.
- T002 → T003/T004 → T005 → T006 → T007 → T008 → T009. T003 puede definirse antes, pero sus factories se ejecutan con modelos migrados; pruebas inicialmente fallan por funcionalidad ausente, no se presentan como verdes.
- Fase compartida completa antes de T010. US1: T010 → T011 → T012 → T013 → T014/T015/T016 → T017 → T018 → T019 → T020 → T021/T022 → T023 → T024.
- US2 depende expresamente de US1; sus pruebas se ejecutan sobre el flujo existente: T025/T026/T027/T028 → T029 → T030 → T031 → T032 → T033. No se promete independencia de implementación entre historias dependientes; sí validación separada de sus objetivos.
- Final: T034 → T035 → T036 → T037; T038 tras T035; T039 requiere ambos, T040 cierra inspección.
- Tests antes de las tareas de implementación correspondientes y evidencia de fallo pertinente; los tests de integración que requieren modelos pueden fallar inicialmente por ausencia de funcionalidad, sin maquillar resultados.

## Parallel Examples

- **US1**: tras T013 pueden prepararse T014 (test_servicio.py), T015 (test_registro.py) y T016 (test_catalogo_contrato.py) en paralelo; tras T020, T021 y T022 modifican templates distintos. Las tareas sobre estudios/models.py siempre en secuencia.
- **US2**: tras T024, T025/T026/T027/T028 editan cuatro archivos diferentes y no dependen entre sí. T029 se serializa después y los cambios de servicio/vistas también.
- No hay automatización de agentes ni instrucciones de commits implícitas en [P]. El usuario es responsable de ambas US del backlog.

## Implementation Strategy

1. Revisar esta lista; obtener evidencia real de T001 antes de código.
2. Base persistente mínima y tests, sin gestión del catálogo US 5.5.
3. US1 como MVP verificable, incluyendo atomicidad e idempotencia base, snapshots y confirmación segura.
4. US2 completa escenarios de errores, recuperación y carreras; no desplegar MVP incompleto en seguridad/integridad.
5. Validación completa/manual y revisión de contrato. La precarga científica oficial permanece como dependencia para uso real; no se carga contenido científico inventado para cerrar tareas.

## Coverage Summary

| Requisito | Tareas principales |
|---|---|
| FR-001 | T015,T018,T020,T023,T025,T026,T030 |
| FR-002 | T015,T018,T021,T023 |
| FR-003 | T009,T015,T018,T021 |
| FR-004 | T009,T012,T014,T019,T031 |
| FR-005 | T010,T011,T014,T019 |
| FR-006 | T015,T017,T020,T022,T026,T030,T032 |
| FR-007 | T009,T018,T025,T031 |
| FR-008 | T014,T019,T027,T028,T031 |
| FR-009 | T010,T011,T017,T019,T026,T027,T028,T030,T031 |
| FR-010 | T012,T016,T019,T027,T028,T029 |
| FR-011 | T014,T015,T020,T023 |
| FR-012 | T003,T021,T025,T035,T040 |
| FR-013 | T001,T010,T011,T027,T028,T039 |
| FR-014 | T001,T018,T025,T032,T039 |
| FR-015 | T017,T019,T025,T026,T027,T029,T030,T032 |
| FR-016 | T011,T014,T019,T028 |
| FR-017 | T010,T011,T013,T014 |
| FR-018 | T011,T014,T016,T019,T026,T027,T029 |
| FR-019 | T002,T004,T005,T006,T007,T008,T009,T038 |
| FR-020 | T003,T021,T025,T035,T039,T040 |
| SC-001/SC-002 | T014,T015,T019,T024 |
| SC-003/SC-004 | T025,T026,T027,T028,T033 |
| SC-005/SC-006 | T014,T016,T028,T029 |
| SC-007 | T026,T027,T029,T031,T032,T033 |

## Notes

La generación original fue documental. La confirmación posterior del usuario acredita la aprobación de la spec por el equipo y autoriza implementar el plan; FR-013/014 son decisiones definitivas del proyecto, no confirmaciones directas del laboratorio. El estado vigente es el de las marcas y la evidencia de cierre. La fuente y responsable de precarga científica siguen pendientes para uso real, sin impedir tests sintéticos aislados. Las tareas no autorizan modificar Constitution, versión de Spec Kit o US 5.5 ni crear nuevos datos científicos.

## Confirmación vigente de implementación — 27/10/2026

El usuario confirma expresamente en este chat que la especificación fue aprobada por el equipo y autoriza implementar el plan/tareas revisados. Esta declaración es la evidencia disponible para T001; no se aportan ni inventan acta, enlace Jira o nombres de revisores. T001 no exige un comprobante externo específico. FR-013/014 quedan como decisiones funcionales definitivas del proyecto, sin atribuir validación al laboratorio; esta actualización sustituye sus etiquetas históricas de supuesto/validación pendiente. La precarga científica oficial y sus responsables siguen pendientes para uso real. Se autoriza desarrollo incremental sin commits/push/PR/merge ni cambios en US 5.5.


## Estado real de ejecución — cierre técnico

**37/40 tareas completas**: T001–T036 y T038. **Pendientes: T037, T039 y T040**. Las marcas acreditan implementación y verificaciones automatizadas; no aprobación de PR ni resultados manuales.

- T001: confirmación del usuario en este chat de aprobación por el equipo, autorización del plan/implementación y decisiones FR-013/014 definitivas del proyecto. Sin actas, Jira o revisores inventados. Checklist documental 16/16.
- T002–T013: estructura, esquema mínimo compartido, constraints y tres migraciones implementados; tests de modelos y aplicación efectiva en PostgreSQL verificados. El UUID obligatorio se acredita en PostgreSQL; el estado inicial se fija en el servicio y no acepta valores de formulario.
- T014–T024: flujo, firma, snapshots, auditoría, resumen/confirmación/volver/cancelar, acceso y navegación implementados y probados; solicitudes de tipos diferentes y del mismo tipo mantienen independencia.
- T025–T033: seguridad, recuperación, rollback, idempotencia persistente, conflictos sucesivos, catálogo inactivo/vacío, cliente inactivo y las cinco pruebas concurrentes pasan en PostgreSQL real.
- T034: trazabilidad revisada contra el mapa del plan; escenarios US1 1–8 y US2 1–11 tienen cobertura en test_registro, test_servicio, test_confirmaciones, test_catalogo_contrato, test_modelos y test_concurrencia. No hay cálculos científicos incluidos ni CRUD US 5.5.
- T035: suite general final 343 passed (154.73s); Ruff lint/formato, Django check, makemigrations y migrate --check pasan; 14 tests JavaScript aprobados. Comandos, entorno, fallos intermedios corregidos y resultado final en quickstart.md.
- T036: pasos y resultados esperados de Chrome detallados en quickstart.md; todavía no ejecutados manualmente.
- T038: contrato documenta módulos/campos, interfaz real de lectura, migraciones entregadas, versión y protocolo obligatorio del escritor futuro de US 5.5. Sus pantallas no se implementaron ni validaron.

**T037 pendiente**: validar en Chrome y registrar ejecutor/fecha/casos/resultados. Para el recorrido completo hace falta catálogo válido o QA expresamente aislado; la base de desarrollo sigue sin contenido científico. No cargar fixtures en producción.

**T039 pendiente** por su dependencia explícita de T037: aprobación, decisiones y dependencias actuales ya se documentan, pero falta incorporar el resultado manual real para cerrar ese registro. La fuente/responsable/códigos de precarga oficial y Jira permanecen pendientes; no se requieren para acreditar tests estructurales.

**T040 pendiente** por la cadena T039: la inspección técnica del diff ya se realizó y no halló cambios fuera de alcance; falta incorporar la evidencia manual y presentar el cierre final correspondiente. No se omiten sus dependencias para inflar el recuento.

No se hicieron commits, push, PR ni merge. Los respaldos locales se preservan fuera de la futura selección del commit. Este registro no acredita CI remoto ni aprobación de código de otro integrante.


## Aclaración académica vigente — decisión del usuario

AquaLab es un proyecto académico FIUBA. Los datos de desarrollo y demostración son ficticios y deben identificarse como DEMO, sin atribuirles validez científica. No hay laboratorio real ni catálogo científico oficial externo pendiente; las referencias anteriores a esa dependencia quedan sustituidas por esta decisión. Se mantienen las reglas funcionales, separación Prueba/TipoEstudio, snapshots y contrato con US 5.5. La carga demo será explícita, reproducible e idempotente, separada de migraciones y arranque; el mecanismo y manifiesto están propuestos en [propuesta-datos-demo.md](propuesta-datos-demo.md), pendientes de revisión antes de implementar o modificar datos. No se cargaron datos ni se completó T037 con esta actualización documental.


## Infraestructura demo autorizada e implementada

El usuario aprobó propuesta-datos-demo.md. Se implementaron el comando explícito cargar_demo_us51 y 18 tests aislados, sin alterar las 40 tareas originales ni marcar cierres manuales. El entorno exige AQUALAB_ENTORNO=desarrollo|qa y DEBUG=True; el modo predeterminado simula sin escrituras y solo --aplicar permite cargar. Reutiliza registrar_muestra y conserva la separación de entidades con US 5.5. No hay datos científicos oficiales pendientes ni carga local ejecutada. Ver quickstart.md para comandos y evidencia. Permanecen 37/40 completas: T037, T039 y T040 siguen sin completar hasta la validación manual.


Resultado final de la infraestructura demo: docker compose exec -T web pytest → 361 passed in 161.17s (suite completa, incluidos los 18 tests demo). Ruff check: All checks passed; Ruff format --check: 122 files already formatted; manage.py check: 0 issues; makemigrations --check --dry-run: No changes detected. La ayuda CLI se verificó con cargar_demo_us51 --help. La consulta de solo lectura a desarrollo confirmó Prueba=0, TipoEstudio=0, Estudio=0 y muestras con prefijo DEMO=0. No se ejecutó --aplicar fuera de pytest. T037/T039/T040 permanecen abiertos (37/40 tareas originales completas). Sin commit/push/PR/merge; US 5.5 intacta.
