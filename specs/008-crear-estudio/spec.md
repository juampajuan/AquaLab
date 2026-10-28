# Feature Specification: Crear estudio sobre una muestra

> Estado vigente de cierre: implementación y 40/40 tareas completadas; recorrido Chrome y carga demo confirmados por el usuario, sin observación directa del asistente. Detalle y límites en [cierre-tecnico.md](cierre-tecnico.md). Las notas de evolución anteriores se conservan como historial. Sin commit ni PR.

**Feature Branch**: `codex/008-crear-estudio`

**Created**: 2026-10-27

**Status**: Aprobada por el equipo según confirmación expresa del usuario en este chat el 27/10/2026; implementación autorizada, sin evidencia externa adicional aportada.

**Input**: User description: "US 5.1 — Como empleado del laboratorio quiero crear un estudio sobre una muestra y asignarle un tipo de estudio para precargar automáticamente el conjunto de pruebas que le corresponden. Criterios de aceptación: seleccionar una muestra registrada; elegir un tipo de estudio del catálogo; precargar automáticamente las pruebas definidas para ese tipo; iniciar el estudio en estado Pendiente de análisis. Responsable del cronograma: Juan Pablo. Dependencias: US 4.1 — Registrar muestra y US 5.5 — Catálogo de tipos de estudio y pruebas predefinidas. Referencias a Jira de US 5.1 y US 5.5: pendientes de completar por indicación del usuario; no se asignan códigos SCRUM supuestos."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Crear un estudio con las pruebas de su tipo (Priority: P1)

Como empleado con sesión activa, quiero seleccionar una muestra registrada y un tipo de estudio disponible, revisar las pruebas que le corresponden y confirmar la creación para dejar preparado su análisis.

**Why this priority**: Es el resultado central de US 5.1 y permite continuar con las historias de realización de pruebas sin cargar manualmente el conjunto estándar.

**Independent Test**: Con una muestra elegible y un tipo disponible que tenga un conjunto conocido de pruebas ficticias identificadas como DEMO o fixtures sintéticas aisladas, crear el estudio y comprobar su muestra, tipo, estado inicial y conjunto exacto de pruebas. No se requieren mediciones ni resultados.

**Acceptance Scenarios**:

1. **Dado** un empleado con sesión activa y muestras elegibles registradas, **cuando** inicia la creación de un estudio, **entonces** puede seleccionar una muestra identificada por su N° PI y reconocer el cliente y origen asociados para distinguirla de otras muestras.
2. **Dada** una muestra seleccionada y tipos disponibles en el catálogo, **cuando** el empleado elige un tipo, **entonces** se muestran las pruebas predefinidas de ese tipo sin exigir su selección individual.
3. **Dados** una muestra y un tipo válidos, **cuando** el empleado solicita crear el estudio, **entonces** se presenta un resumen de muestra, tipo y pruebas y se pide confirmación explícita antes de guardar.
4. **Dado** un resumen válido, **cuando** el empleado confirma, **entonces** se crea un estudio asociado a la muestra y al tipo seleccionados, con exactamente las pruebas de la configuración confirmada, cada una una sola vez, y estado general "Pendiente de análisis"; se informa el éxito identificando el estudio y la muestra.
5. **Dado** un resumen abierto, **cuando** el empleado vuelve a editar, **entonces** conserva la selección para corregirla sin crear un estudio; si cancela, no se crea el estudio ni se asignan pruebas.
6. **Dado** un estudio ya creado, **cuando** se renombra el tipo, se edita su descripción (incluido vaciarla), se cambia su composición o se desactiva, **entonces** el estudio conserva nombre y descripción históricos y sus pruebas asignadas; nuevos estudios reciben los textos y composición vigentes que confirmen. La administración corresponde a US 5.5.
7. **Dado** un empleado que confirma la creación, **cuando** el estudio queda registrado, **entonces** se le asigna automáticamente un identificador numérico único y se registran el usuario creador autenticado y la fecha y hora de creación, sin que el empleado pueda elegirlos ni sustituirlos por valores enviados manualmente.
8. **Dada** una muestra con un estudio creado, **cuando** el empleado confirma una nueva solicitud de otro tipo disponible, **entonces** se crea otro estudio sobre la misma muestra, con su propio identificador, estado inicial, trazabilidad y pruebas, sin modificar el estudio anterior.

---

### User Story 2 - Evitar estudios incompletos o creaciones accidentales (Priority: P2)

Como empleado, quiero que se rechacen selecciones inválidas y que una confirmación repetida no duplique mi operación para mantener confiables los estudios de la muestra.

**Why this priority**: La preparación de un estudio solo es útil si sus pruebas son completas y corresponden al tipo confirmado.

**Independent Test**: Intentar crear un estudio con selecciones inválidas, cancelar y repetir una misma confirmación; verificar los mensajes y la ausencia de estudios parciales o duplicados por reenvío.

**Acceptance Scenarios**:

1. **Dada** la creación de un estudio, **cuando** falta la muestra o el tipo, **entonces** el sistema indica qué selección debe completarse, conserva los valores válidos y no crea registros.
2. **Dada** una muestra inexistente o un tipo inexistente, desactivado o sin pruebas definidas, **cuando** se intenta confirmar, **entonces** el sistema informa que la selección no está disponible y no crea el estudio.
3. **Dado** que no hay muestras elegibles o tipos disponibles, **cuando** el empleado intenta iniciar la creación, **entonces** se informa qué dato previo falta y no se ofrece una creación vacía ni se inventan tipos o pruebas.
4. **Dada** una confirmación válida, **cuando** ocurre una falla durante la creación o asignación de pruebas, **entonces** no quedan un estudio parcial ni asignaciones parciales y no se informa éxito.
5. **Dada** una misma operación de creación, **cuando** su confirmación se reenvía, incluso simultáneamente, **entonces** se crea un único estudio para esa operación. Una nueva solicitud deliberada puede crear otro estudio del mismo tipo según la decisión definitiva FR-013.
6. **Dado** un usuario sin sesión activa, **cuando** intenta acceder o confirmar la creación, **entonces** debe iniciar sesión y no se crea ningún estudio.
7. **Decisión definitiva del proyecto (FR-013): Dada** una muestra que ya tiene un estudio de un tipo determinado, **cuando** el empleado inicia y confirma una nueva solicitud deliberada del mismo tipo para esa muestra, **entonces** se crea un estudio distinto, en "Pendiente de análisis", con su propio conjunto de pruebas asignadas y sin modificar el estudio anterior. Esta regla fue aprobada por el usuario como decisión del equipo/proyecto.
8. **Decisión definitiva del proyecto (FR-014): Dada** una muestra ya registrada cuyo cliente está inactivo, **cuando** un empleado con sesión activa selecciona la muestra y confirma un tipo disponible, **entonces** se permite crear el estudio con sus pruebas y trazabilidad, sin reactivar ni modificar al cliente. Se aplica el mismo resultado si el cliente se desactiva entre la selección y la confirmación; su inactividad por sí sola no impide continuar con la muestra ingresada.
9. **Dado** un resumen con un conjunto de pruebas que cambió antes de confirmar, **cuando** se envía esa confirmación, **entonces** no se crea el estudio, se informa el cambio, se muestra el conjunto actualizado completo y se exige una nueva confirmación explícita. Reenviar la confirmación anterior no acepta el nuevo conjunto.
10. **Dado** el resumen actualizado, **cuando** el empleado vuelve a confirmar y el conjunto sigue vigente al crearse el estudio, **entonces** se crea un único estudio con exactamente ese conjunto. Si vuelve a cambiar, se repite la revisión sin crear registros parciales.
11. **Dadas** una modificación concurrente del conjunto del tipo y una confirmación, **cuando** ambas coinciden durante la creación, **entonces** solo son válidos dos resultados: el estudio se crea íntegramente con el conjunto explícitamente confirmado antes de que tenga efecto la modificación, o no se crea y se exige revisar y confirmar el conjunto actualizado. Nunca se crea con un conjunto diferente del confirmado ni con una mezcla de configuraciones. Las confirmaciones concurrentes de una misma solicitud siguen creando como máximo un estudio.

### Edge Cases

- La muestra seleccionada deja de existir antes de la confirmación: se rechaza sin crear registros.
- El tipo se desactiva o queda sin pruebas antes de confirmar: se rechaza la creación y se permite corregir la selección.
- El conjunto de pruebas del tipo cambia mientras el empleado revisa el resumen: no se crea el estudio con esa confirmación; se muestra el conjunto actualizado y se requiere una nueva confirmación explícita (FR-015).
- Una misma muestra ya tiene un estudio del tipo elegido: se permite crear otro mediante una nueva solicitud deliberada; cada estudio conserva su identidad y sus pruebas asignadas (decisión del proyecto FR-013).
- El cliente de la muestra está inactivo o se desactiva mientras se revisa: se permite continuar sobre la muestra ya registrada sin reactivar al cliente (decisión del proyecto FR-014).
- El catálogo cambia nuevamente después de mostrar el resumen actualizado, incluso mientras se procesa su nueva confirmación: se mantiene la regla de consistencia de FR-015; no se acepta un conjunto no confirmado ni mezclado.
- El empleado cambia el tipo durante la edición: las pruebas mostradas deben corresponder únicamente al último tipo elegido.
- Dos confirmaciones de una misma operación llegan simultáneamente: se mantiene una sola creación, sin confundir este caso con dos solicitudes deliberadas distintas.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema MUST permitir crear estudios únicamente a empleados con sesión activa.
- **FR-002**: El sistema MUST permitir seleccionar una muestra registrada y elegible, identificándola por N° PI y mostrando su cliente y origen; no debe crear ni modificar muestras u orígenes como parte de este flujo.
- **FR-003**: El sistema MUST permitir elegir un tipo existente y disponible del catálogo de US 5.5; los tipos desactivados no se ofrecen para nuevas creaciones.
- **FR-004**: El sistema MUST mostrar y asignar automáticamente el conjunto de pruebas predefinidas del tipo elegido, sin omisiones, duplicados ni pruebas ajenas a esa configuración. No se permite añadir o quitar pruebas manualmente en esta historia.
- **FR-005**: El sistema MUST asociar el estudio a una sola muestra y a un solo tipo de estudio y comenzar su estado general como "Pendiente de análisis".
- **FR-006**: El sistema MUST presentar muestra, tipo y pruebas para confirmación explícita antes de guardar, permitir volver a editar conservando la selección y permitir cancelar sin guardar.
- **FR-007**: El sistema MUST validar las selecciones también al confirmar, rechazar referencias inexistentes y tipos no disponibles o sin pruebas, e indicar el problema conservando las selecciones que sigan siendo válidas.
- **FR-008**: El sistema MUST crear el estudio y asignar todas sus pruebas como una única operación: se completa todo o no queda creado ningún registro de esa operación; una falla nunca se presenta como éxito.
- **FR-009**: El sistema MUST impedir que el reenvío de la confirmación de una misma operación, incluso concurrente, cree estudios adicionales.
- **FR-010**: Conservar las pruebas asignadas y snapshots históricos de nombre y descripción del tipo al crear el estudio, incluida descripción vacía, aunque el tipo se renombre, edite o desactive posteriormente. Mantener referencia estable al tipo. El versionado de fórmulas, unidades y límites no pertenece a esta historia.
- **FR-011**: El sistema MUST informar la creación exitosa de manera que el empleado pueda identificar el estudio creado y la muestra a la que pertenece.
- **FR-012**: Consumir las pruebas y tipos del catálogo compartido, sin crear un catálogo paralelo ni atribuir validez científica a los datos académicos ficticios. No definir fórmulas, unidades, límites o normas arbitrarias. Los datos DEMO deben estar claramente identificados y cargarse solo por una acción explícita autorizada.
- **FR-013 — decisión funcional definitiva del proyecto**: Permitir múltiples estudios del mismo tipo sobre una muestra mediante solicitudes deliberadas distintas; cada uno tiene identificador, estado, pruebas y trazabilidad propios. No imponer unicidad muestra/tipo. Doble clic, reenvíos o confirmaciones concurrentes de una misma solicitud crean un único estudio. Confirmado por el usuario como decisión del equipo/proyecto, no como validación directa del laboratorio.
- **FR-014 — decisión funcional definitiva del proyecto**: Permitir estudios sobre muestras previamente registradas válidas aunque su cliente esté actualmente inactivo; no reactivar al cliente ni modificar datos históricos de la muestra. No cambia las validaciones de US 4.1 para muestras nuevas. Confirmado por el usuario como decisión del proyecto, no como validación directa del laboratorio.
- **FR-015 — decisión de especificación aprobada por el usuario**: Si el conjunto de pruebas del tipo cambia entre revisión y confirmación, el sistema MUST abstenerse de crear el estudio con esa confirmación, informar el cambio, mostrar el conjunto actualizado y exigir una nueva confirmación explícita. La confirmación del resumen anterior no sirve para aceptar el nuevo conjunto. Si vuelve a cambiar, se aplica nuevamente la misma regla. Ante modificaciones concurrentes, la creación MUST ser consistente con la configuración vigente en el momento de crear el estudio: o la creación íntegra con el conjunto confirmado precede al cambio, o se rechaza esa confirmación y se exige revisar la configuración actualizada. Nunca se permite un conjunto distinto del confirmado ni una mezcla de configuraciones; se mantiene FR-008 y la idempotencia de FR-009. Esta decisión no se atribuye a una confirmación del laboratorio; el contrato funcional está aceptado para diseño y su integración se verificará después.
- **FR-016**: El sistema MUST registrar automáticamente en cada estudio el usuario autenticado que lo creó y la fecha y hora efectiva de creación. Estos datos no son elegibles ni modificables por el empleado durante el alta y no pueden reemplazarse por valores proporcionados manualmente. El reenvío de una misma confirmación conserva la trazabilidad del único estudio creado.
- **FR-017**: El sistema MUST asignar automáticamente a cada estudio un identificador numérico único. Las notas no exigen que sea consecutivo, sin huecos ni que siga la numeración PI de la muestra; no se trasladan esas reglas del alta de muestras.

- **FR-018**: Guardar snapshots de nombre y descripción revisados, asignaciones y cabecera en una sola operación. Cambios posteriores no reescriben ese historial. Si cambian los textos durante revisión también se exige revisar y confirmar antes de guardar snapshots diferentes.
- **FR-019**: Mantener una sola base compartida con códigos únicos de pruebas, nombres únicos de tipos ignorando mayúsculas y espacios laterales (tildes/espacios internos distinguen), descripción opcional y composición no vacía sin duplicados; no implementar la administración US 5.5 dentro del alta de estudios.
- **FR-020**: Permitir fixtures sintéticas aisladas en tests y un manifiesto ficticio DEMO aprobado para desarrollo/QA, mediante un mecanismo explícito, reproducible e idempotente separado de migraciones y arranque. No hay fuente científica externa pendiente. Si falta catálogo cargado, informar la ausencia sin inventar datos automáticamente ni ofrecer una creación vacía.

### Key Entities *(include if feature involves data)*

- **Muestra**: Muestra física previamente registrada, identificada por N° PI y asociada a un cliente y un origen. Es el objeto analizado; su alta pertenece a US 4.1.
- **Estudio**: Identificador numérico único, muestra y tipo, estado inicial Pendiente de análisis, creador y fecha/hora automáticos, snapshots del nombre y descripción del tipo, clave de idempotencia por solicitud y conjunto propio de pruebas asignadas.
- **Tipo de estudio**: Definición del catálogo que determina qué pruebas se incluyen por defecto y si puede elegirse para nuevas creaciones. Su administración pertenece a US 5.5.
- **Prueba**: Ensayo definido por el científico y disponible en el catálogo. Su definición científica no se crea en US 5.1.
- **Prueba asignada al estudio**: Pertenencia de una prueba concreta al conjunto de un estudio; permanece independiente de cambios posteriores en la composición del tipo. No implica cargar mediciones ni resultados en esta historia.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: En todos los casos válidos de aceptación, el estudio creado queda asociado exactamente a la muestra y tipo confirmados, y comienza en "Pendiente de análisis".
- **SC-002**: Para cada tipo del catálogo académico disponible utilizado en la validación, el 100% de las pruebas predefinidas se asigna una sola vez y no aparece ninguna prueba adicional.
- **SC-003**: El 100% de los casos de cancelación, selección inválida o falla de creación termina sin estudios ni asignaciones parciales de esa operación.
- **SC-004**: En todos los casos de reenvío secuencial y simultáneo de una misma confirmación, se registra exactamente un estudio por operación.
- **SC-005**: El 100% de los estudios validados conserva sus pruebas y snapshots de nombre y descripción, incluida descripción vacía, después de renombrar, editar o desactivar el tipo.
- **SC-006**: El 100% de los estudios creados en los casos de aceptación tiene un identificador numérico único y registra automáticamente al empleado que confirmó y la fecha/hora de creación; los intentos de sustituir manualmente esos datos no alteran la trazabilidad.
- **SC-007**: En todos los casos de cambio del conjunto de pruebas, incluidos cambios sucesivos y concurrentes con la confirmación, no se crea ningún estudio con pruebas distintas de las explícitamente confirmadas ni con configuraciones mezcladas. Cuando el cambio precede a la creación, se exige una nueva confirmación del conjunto actualizado y no se crea el estudio al reenviar la confirmación anterior.

## Assumptions

- **Trazabilidad**: US 5.1 — Crear estudio sobre una muestra. Responsable del cronograma: Juan Pablo. Clave y enlace de Jira de US 5.1 y US 5.5: pendientes de completar cuando el usuario los facilite; no bloquean la redacción de este borrador.
- **Dependencia US 4.1 integrada**: PR #11 mergeado en main 6b29f434f31898c6b90290a8efd03fac475721a6. Checkout de US 5.1 actualizado por fast-forward después de respaldo verificado. Muestra conserva PK, PI único, cliente/origen, estado Ingresada y trazabilidad. Las correcciones no alteran su contrato consumidor. La clave de borrador de muestras no se reutiliza para estudios.
- **Contrato compartido aceptado para diseño**: El usuario es responsable de ambas historias y autoriza US 5.1 primero con la base persistente mínima compartida. US 5.5 administrará las mismas entidades de catálogo posteriormente. No se modifica su rama ni se duplica el catálogo. El orden anterior en su borrador es histórico y queda superado por esta instrucción.
- **Datos académicos**: AquaLab es un proyecto FIUBA; todos los datos de desarrollo y demostración son ficticios. El manifiesto DEMO fue aprobado y el usuario informa que se cargó correctamente mediante cargar_demo_us51 --aplicar. Las asociaciones demuestran software, no validez científica. No hay laboratorio real ni fuente externa pendiente.
- **Recorrido aprobado**: Selección por N° PI con cliente/origen visibles y mensaje de éxito con identificador del estudio; sin consulta general, que pertenece a otra historia.
- **Estados**: Esta historia fija solo el estado inicial del estudio. Los estados individuales y la evolución de las pruebas deberán coordinarse con US 5.2 y las historias de realización de pruebas.
- **Alcance excluido**: Administración del catálogo y definición de pruebas (US 5.5 y precarga científica); búsqueda y consulta general del avance y listado desde la ficha de muestra (US 5.2); agregar o quitar pruebas manualmente (US 5.3 y US 5.4); mediciones, resultados, informes y cambios posteriores de estado.
- **Revisión y evidencia**: Spec aprobada por el equipo según declaración del usuario; implementación autorizada. FR-013/014 son decisiones definitivas del proyecto. La validación manual en Chrome fue informada por el usuario; no se atribuyen capturas, registros ni observación directa al asistente. Ver cierre-tecnico.md.

### Estado de decisiones y dependencias

| Punto | Estado | Pendiente y responsable de validación |
|---|---|---|
| Referencia a muestra y tipo, varias instancias de estudio por muestra, pruebas predefinidas, estado inicial y trazabilidad | Respaldados por backlog, notas y las indicaciones del usuario | Spec aprobada según el usuario; US 4.1 integrada y base compartida implementada. |
| FR-013: repetir tipo | Decisión definitiva del proyecto | Implementada; tests y validación manual informada por el usuario. |
| FR-014: cliente inactivo | Decisión definitiva del proyecto | Implementada; tests y validación manual informada por el usuario. |
| FR-015: nueva confirmación y concurrencia | Implementada y probada en PostgreSQL | El futuro escritor US 5.5 debe respetar lock y versión; no se declara su implementación. |
| US 4.1: muestras | Integrada en main 6b29f43 | Sin cambios necesarios al contrato Muestra. |
| US 5.5 y catálogo académico | Base mínima y cargador DEMO entregados por US 5.1 | Administración US 5.5 posterior sobre las mismas entidades; sin fuente externa pendiente. |
| Claves y enlaces Jira de US 5.1 y US 5.5 | Referencias administrativas pendientes | El usuario las facilitará; se conserva la identificación funcional. |

### Datos mínimos requeridos del catálogo y alternativa de precarga

US 5.1 necesita, independientemente de cómo se administren esos datos:

- Tipos de estudio identificables, con nombre y disponibilidad para nuevas creaciones.
- Pruebas ficticias del catálogo identificables, con código y nombre para reconocerlas y mantener la referencia al catálogo.
- La relación explícita entre cada tipo y su conjunto de pruebas por defecto, sin duplicados y con al menos una prueba por tipo, según US 5.5.
- Un acuerdo para preservar las asignaciones de estudios existentes ante cambios posteriores del catálogo y para coordinar las modificaciones del conjunto con las confirmaciones de US 5.1, conforme a FR-015. La política funcional está definida; su contrato compartido está adoptado por el usuario para diseño. Una precarga no elimina esta necesidad si se permiten cambios durante el uso.

La carga DEMO aprobada aporta tipos, pruebas y asociaciones ficticias en desarrollo/QA mediante una ejecución explícita de cargar_demo_us51. No crea un catálogo paralelo ni estudios automáticamente; reutiliza la base mínima que extenderá US 5.5. El usuario informa la carga correcta para la validación manual.

La precarga no resuelve la administración del catálogo: crear, editar o desactivar tipos, mantener sus pruebas por defecto y proteger tipos utilizados sigue correspondiendo a US 5.5. Tampoco sustituye el acuerdo compartido sobre esas entidades. El mecanismo implementado y su manifiesto están documentados en propuesta-datos-demo.md y quickstart.md.

Las unidades, fórmulas, curvas, límites y normas son datos del catálogo que consumirán las historias de mediciones, cálculos y validación. US 5.1 conserva la referencia a la prueba y su pertenencia al estudio; no calcula resultados ni decide versiones de esos atributos científicos.

### Fuentes y precedencia de decisiones

| Fuente | Aporte a esta especificación | Límite de interpretación |
|---|---|---|
| [Constitution](../../.specify/memory/constitution.md) | Trazabilidad, sesión obligatoria, confirmación antes de guardar, integridad y separación entre spec e implementación | No se modifica en este workflow. |
| [Backlog, US 5.1 y US 5.5](../../docs/extra/jira-import.csv) | Cuatro criterios originales; catálogo separado; cambios de composición solo para futuros estudios; precarga científica como tarea separada | Los IDs de importación no acreditan claves Jira. |
| [Notas de reunión y definiciones clave, 26/10/2026](sources/notas-reunion-2026-10-26.txt), secciones «Respuestas a las dudas», «Cabecera del estudio» y «Cada prueba dentro del estudio» | Varios estudios por muestra; referencia a muestra y tipo; pruebas predefinidas; identificador, usuario y fecha/hora automáticos; estado inicial y separación de US 5.3/5.4 | Documento aportado por el usuario que sintetiza reunión, análisis del software actual y backlog. No se atribuye todo su contenido a una confirmación directa del laboratorio; sus ejemplos no son un catálogo completo ni datos normativos aprobados. |
| Decisión definitiva del usuario sobre FR-013 | Permitir repetir tipo mediante nuevas solicitudes deliberadas | Decisión del equipo/proyecto, no validación directa de un laboratorio. |
| Decisiones definitivas del usuario sobre FR-014/015 y contexto FIUBA | Admitir clientes inactivos; exigir nueva confirmación y consistencia concurrente; datos académicos DEMO | No implica implementación ni aprobación del código futuro de US 5.5. |

Las notas también describen otros estados de muestra, pruebas y estudio, y decisiones de muestras que pueden diferir del PR #11. Se usan aquí solo los requisitos pertinentes a US 5.1. No se cambian el alta de muestras, sus estados ni la ubicación de la persona de contacto desde esta historia. El tipo de estudio «Vuelco a canal» no se equipara automáticamente al tipo de vertido «Canal» de una muestra.

## Historial de decisiones — sustituido por el estado vigente anterior

Las sesiones conservadas a continuación documentan la evolución; sus restricciones superadas no son requisitos actuales. El cierre vigente está en cierre-tecnico.md.

## Clarifications

### Session 2026-10-27

- Q1: ¿Una muestra puede tener varios estudios del mismo tipo mediante solicitudes deliberadas distintas? → A inicial del usuario: sí. Precisión posterior al aportar las notas: es una decisión provisional nuestra, pendiente de validación con el laboratorio; el documento solo confirma varios estudios, potencialmente de tipos distintos. El reenvío de una misma confirmación sigue creando un único estudio por operación.
- Fuente incorporada: notas de reunión del 26/10/2026. Se añaden trazabilidad automática (FR-016), identificador del estudio (FR-017) y escenario de varios estudios de tipos distintos, y se documenta el contrato funcional mínimo y la alternativa de datos precargados para US 5.5. Las notas no resuelven FR-014 ni FR-015.
- Q2 / FR-014: El equipo propone permitir crear estudios de muestras ya ingresadas aunque el cliente esté inactivo, incluso si se desactiva durante la revisión. El usuario pide documentarlo como propuesta pendiente de validación del laboratorio, no como requisito confirmado.
- Q3 / FR-015: El usuario establece mostrar el conjunto actualizado y exigir una nueva confirmación explícita si cambia entre revisión y confirmación, garantizando consistencia también con modificaciones concurrentes. Queda definida la política funcional; sigue abierto el acuerdo con US 5.5 para sostenerla. No se afirma que haya sido implementada o probada.
- FR-013 se mantiene provisionalmente como indicó el usuario; no se cierra su validación externa. La especificación continúa en Draft y no se avanza a plan.

### Actualización aceptada para diseño — 27/10/2026

Esta actualización prevalece sobre las menciones históricas de orden y dudas de sesiones anteriores. FR-013/014 se diseñan y prueban con sus escenarios US2 7/8 como supuestos aceptados, sin declarar validación del laboratorio. El usuario autoriza US 5.1 antes de la gestión US 5.5.

Contrato aceptado: Prueba con identidad estable, código único y nombre; TipoEstudio con nombre, descripción opcional, activo, versión y composición no vacía; Estudio con muestra, tipo, estado inicial, identidad, creador, fecha/hora, snapshots y clave de idempotencia; PruebaEstudio con asignaciones propias. US 5.1 puede incorporar solo la base persistente necesaria. US 5.5 administrará exactamente esas entidades. No se exige permiso de administración del catálogo a un empleado que crea estudios.


Escenarios complementarios: descripción histórica vacía se conserva tras editarla; textos cambiados entre revisión y confirmación exigen un nuevo resumen y confirmación; fixtures genéricas aisladas permiten comprobar selección, snapshots e idempotencia sin acreditar composiciones científicas oficiales. Las fixtures se destruyen/revierten con la base de test.

Fuente de contrato revisada: spec local de US 5.5 en E:/Codex/worktrees/us55-tipos-estudio/AquaLab/specs/009-gestionar-tipos-estudio/spec.md. No está integrada en esta rama ni se modifica. La responsabilidad lógica de US 5.5 sobre el catálogo se mantiene aunque el esquema mínimo se entregue como prerrequisito acotado de US 5.1.

### Autorización documental posterior — revisión y tareas

El usuario solicita revisar el diseño y generar tasks con el Spec Kit original, sin implementar. Esto supera únicamente las referencias históricas a no ejecutar tasks todavía; no aprueba formalmente la spec en nombre del equipo ni valida externamente FR-013/014. Los supuestos aceptados y el contrato funcional se conservan.


## Confirmación vigente de implementación — 27/10/2026

El usuario confirma expresamente en este chat que la especificación fue aprobada por el equipo y autoriza implementar el plan/tareas revisados. Esta declaración es la evidencia disponible para T001; no se aportan ni inventan acta, enlace Jira o nombres de revisores. T001 no exige un comprobante externo específico. FR-013/014 quedan como decisiones funcionales definitivas del proyecto, sin atribuir validación al laboratorio; esta actualización sustituye sus etiquetas históricas de supuesto/validación pendiente. La precarga científica oficial y sus responsables siguen pendientes para uso real. Se autoriza desarrollo incremental sin commits/push/PR/merge ni cambios en US 5.5.


## Aclaración académica vigente — decisión del usuario

AquaLab es un proyecto académico FIUBA. Los datos de desarrollo y demostración son ficticios y deben identificarse como DEMO, sin atribuirles validez científica. No hay laboratorio real ni catálogo científico oficial externo pendiente; las referencias anteriores a esa dependencia quedan sustituidas por esta decisión. Se mantienen las reglas funcionales, separación Prueba/TipoEstudio, snapshots y contrato con US 5.5. La carga demo será explícita, reproducible e idempotente, separada de migraciones y arranque; el mecanismo y manifiesto están propuestos en [propuesta-datos-demo.md](propuesta-datos-demo.md), pendientes de revisión antes de implementar o modificar datos. No se cargaron datos ni se completó T037 con esta actualización documental.


Actualización de ejecución demo: el usuario aprobó el manifiesto y el mecanismo; cargar_demo_us51 está implementado con simulación por defecto, guardas de desarrollo/QA y escritura únicamente mediante --aplicar. No se ejecutó --aplicar sobre la base local. La validación manual sigue pendiente; ver quickstart.md para comandos y pruebas. Esta nota sustituye el estado anterior de propuesta pendiente de revisión.
