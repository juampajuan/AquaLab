# Feature Specification: Registrar muestra

**Feature Branch**: `007-registrar-muestra`

**Created**: 2026-10-27

**Status**: Draft

**Input**: User description: "US 4.1 (Jira SCRUM-47) – Registrar muestra. Como empleado del laboratorio quiero registrar el ingreso de una muestra física asociándola a un cliente y asignándole un código para identificarla y asegurar su trazabilidad dentro del laboratorio. Criterios de aceptación: (1) Se selecciona el cliente de los clientes registrados; al elegirlo se muestran su razón social, CUIT/DNI y email. (2) El origen (fuente de agua, ej. "Pozo N°2") se elige entre los usados anteriormente por ese cliente, o se da de alta uno nuevo desde el mismo formulario; el origen nuevo queda asociado al cliente y disponible para sus próximas muestras. (3) Son obligatorios: cliente, origen, fecha de muestreo, fecha de ingreso, sitio de extracción y tipo de vertido. (4) La fecha de muestreo y la de ingreso proponen la fecha de hoy y se pueden corregir. (5) El tipo de vertido se elige entre Agua, Cloacal y Canal, con Agua por defecto. (6) Son opcionales el nombre de la muestra (si queda vacío se usa "Muestra 1") y el responsable del muestreo. (7) El sistema asigna automáticamente un N° PI entero y único, sumando 1 al último registrado y empezando en 200001. (8) El sistema guarda automáticamente el usuario que registró la muestra y la fecha y hora del registro. (9) La muestra queda en estado "Ingresada". (10) No se permite guardar si falta algún dato obligatorio, y se indica cuál falta. (11) Antes de guardar se pide confirmación mostrando un resumen de los datos. Fuera de alcance: la persona de contacto va en el Cliente, no en la muestra; una muestra con historial no se borra, se desactiva (no es parte de esta historia)."

## Clarifications

### Session 2026-10-27

- Q: Si el nombre de la muestra queda vacío, ¿se usa siempre "Muestra 1" o se numera ("Muestra 1", "Muestra 2", …)? → A: Siempre "Muestra 1" (valor fijo por defecto).
- Q: ¿Cómo se elige el cliente en el formulario: lista desplegable o búsqueda? → A: Lista desplegable que se filtra al escribir por nombre, razón social o número de documento.
- Q: ¿Origen y sitio de extracción son datos distintos? → A: Sí: el origen es la fuente de agua reutilizable del cliente; el sitio de extracción es texto libre propio de cada muestra.
- Q: ¿El responsable del muestreo es texto libre o un usuario del sistema? → A: Texto libre (puede ser personal externo al laboratorio).
- Q: Tras confirmar el registro, ¿a qué pantalla se dirige al empleado? → A: Al formulario de registro vacío, con un mensaje de éxito que muestra el N° PI asignado.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Registrar el ingreso de una muestra con un origen ya conocido (Priority: P1)

Como empleado del laboratorio, quiero registrar el ingreso de una muestra física eligiendo el cliente que la trae y uno de sus orígenes ya usados, para que el sistema le asigne un N° PI único y la muestra quede identificada y trazable desde su llegada al laboratorio.

**Why this priority**: Es el flujo central de la historia y el punto de partida de todo el circuito del laboratorio (estudios, resultados, informes y comparación histórica): sin muestras registradas con su N° PI, cliente y origen no hay nada que analizar ni comparar.

**Independent Test**: Con un cliente activo que ya tiene al menos un origen asociado, se completa el formulario de registro, se revisa el resumen, se confirma y se verifica que la muestra queda guardada con el N° PI siguiente al último, estado "Ingresada", el cliente y el origen elegidos, el usuario que la registró y la fecha y hora del registro.

**Acceptance Scenarios**:

1. **Given** un empleado con sesión activa, **When** abre el registro de muestra, **Then** el sistema muestra el formulario con la fecha de muestreo y la fecha de ingreso precargadas con la fecha de hoy, el tipo de vertido en "Agua" y los campos de nombre de la muestra y responsable del muestreo vacíos.
2. **Given** el formulario de registro de muestra, **When** el empleado escribe parte del nombre, la razón social o el número de documento y selecciona un cliente de la lista filtrada, **Then** el sistema muestra la razón social (o el nombre, si el cliente no tiene razón social), el tipo y número de documento (CUIT/DNI) y el correo electrónico de ese cliente.
3. **Given** un cliente seleccionado que tiene orígenes usados anteriormente, **When** el empleado despliega la elección del origen, **Then** el sistema ofrece únicamente los orígenes asociados a ese cliente.
4. **Given** el formulario con todos los datos obligatorios completos y válidos, **When** el empleado solicita guardar, **Then** el sistema muestra un resumen con todos los datos ingresados (cliente, origen, fechas, sitio de extracción, tipo de vertido, nombre de la muestra y responsable del muestreo) y pide confirmación antes de guardar.
5. **Given** el resumen de una muestra válida, **When** el empleado confirma, **Then** el sistema registra la muestra con un N° PI igual al último N° PI registrado más 1, en estado "Ingresada", guarda automáticamente el usuario que la registró y la fecha y hora del registro, e informa el éxito mostrando el N° PI asignado, dejando al empleado en un formulario de registro vacío listo para la siguiente muestra.
6. **Given** que no existe ninguna muestra registrada, **When** el empleado confirma el registro de la primera muestra, **Then** el sistema le asigna el N° PI 200001.
7. **Given** el formulario o el resumen previo a confirmar, **When** el empleado vuelve a editar o cancela la operación, **Then** el sistema no registra ninguna muestra ni consume un N° PI, y en el caso de volver a editar conserva los datos ingresados.

---

### User Story 2 - Dar de alta un origen nuevo desde el registro de muestra (Priority: P2)

Como empleado del laboratorio, quiero dar de alta un origen nuevo del cliente desde el mismo formulario de registro de muestra cuando la fuente de agua todavía no fue usada, para no interrumpir la carga y que ese origen quede disponible para las próximas muestras del cliente.

**Why this priority**: Cada cliente nuevo y cada fuente de agua nueva requieren crear su origen; sin esto, la primera muestra de un cliente no podría registrarse. Se separa de P1 porque el flujo con orígenes existentes es comprobable por sí solo.

**Independent Test**: Con un cliente activo sin orígenes (o con orígenes que no corresponden a la fuente de la muestra), se ingresa un origen nuevo en el formulario, se confirma el registro y se verifica que la muestra queda asociada al origen nuevo y que ese origen aparece ofrecido al registrar una nueva muestra del mismo cliente, pero no al registrar una de otro cliente.

**Acceptance Scenarios**:

1. **Given** un cliente seleccionado, **When** el empleado elige dar de alta un origen nuevo e ingresa su nombre (ej. "Pozo N°2") y confirma el registro de la muestra, **Then** el sistema crea el origen asociado a ese cliente y registra la muestra asociada a ese origen.
2. **Given** un origen creado al registrar una muestra de un cliente, **When** el empleado registra una nueva muestra de ese mismo cliente, **Then** el origen aparece entre los orígenes disponibles para elegir.
3. **Given** un origen creado para un cliente, **When** el empleado registra una muestra de otro cliente, **Then** ese origen no aparece entre los orígenes disponibles.
4. **Given** un cliente que ya tiene el origen "Pozo N°2", **When** el empleado intenta dar de alta un origen nuevo con el mismo nombre (sin distinguir mayúsculas/minúsculas ni espacios laterales), **Then** el sistema no crea un origen duplicado y asocia la muestra al origen existente.
5. **Given** que el empleado ingresó un origen nuevo, **When** cancela el registro de la muestra antes de confirmar, **Then** el sistema no crea el origen.

---

### User Story 3 - Impedir el registro de muestras incompletas o inconsistentes (Priority: P3)

Como empleado del laboratorio, quiero que el sistema no me permita guardar una muestra con datos obligatorios faltantes o inválidos y me indique cuál corregir, para que todas las muestras registradas sean trazables y confiables.

**Why this priority**: Protege la integridad de los datos del laboratorio, pero depende de que exista el flujo de registro (P1).

**Independent Test**: Se intenta guardar el formulario dejando vacío cada dato obligatorio por separado y con valores inválidos, y se verifica que en cada caso el sistema indica el dato a corregir, conserva lo ingresado y no registra ninguna muestra.

**Acceptance Scenarios**:

1. **Given** el formulario de registro de muestra, **When** el empleado intenta guardar sin alguno de los datos obligatorios (cliente, origen, fecha de muestreo, fecha de ingreso, sitio de extracción o tipo de vertido), **Then** el sistema no avanza al resumen, indica junto a cada dato faltante que es obligatorio y conserva los datos ya ingresados.
2. **Given** el formulario de registro de muestra, **When** el empleado deja vacío el nombre de la muestra y confirma el registro, **Then** el sistema registra la muestra con el nombre "Muestra 1".
3. **Given** el formulario de registro de muestra, **When** el empleado deja vacío el responsable del muestreo y confirma el registro, **Then** el sistema registra la muestra sin responsable del muestreo.
4. **Given** el formulario de registro de muestra, **When** el empleado ingresa una fecha de muestreo posterior a la fecha de ingreso, o alguna de las fechas posterior a hoy, **Then** el sistema indica el error en la fecha correspondiente y no avanza al resumen.
5. **Given** el formulario de registro de muestra, **When** el empleado intenta usar un origen que pertenece a otro cliente o un cliente inactivo o inexistente, **Then** el sistema rechaza el dato y no registra la muestra.

### Edge Cases

- Dos empleados confirman el registro de una muestra al mismo tiempo: cada muestra recibe un N° PI distinto y consecutivo; nunca se repite un N° PI.
- El empleado confirma dos veces el mismo resumen (doble clic o reenvío): se registra una sola muestra.
- El empleado cambia el cliente seleccionado después de haber elegido un origen: el origen elegido deja de ser válido y debe elegirse o darse de alta uno del nuevo cliente.
- Si el texto escrito no coincide con ningún cliente activo, la lista no ofrece opciones y no se puede avanzar sin elegir un cliente.
- El cliente seleccionado no tiene orígenes previos: la única opción es dar de alta un origen nuevo.
- Los espacios laterales en los campos de texto (origen nuevo, sitio de extracción, nombre de la muestra, responsable) se eliminan; un campo obligatorio que solo contiene espacios se considera vacío.
- El cliente seleccionado se desactiva entre que se abre el formulario y se confirma: el sistema informa que el cliente no está disponible y no registra la muestra.
- Si ocurre una falla al guardar la muestra confirmada, el sistema informa que no se pudo registrar, no deja creado un origen nuevo huérfano ni presenta la muestra como registrada.
- Un usuario sin sesión activa no puede acceder al registro de muestras ni enviar datos.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema MUST permitir registrar muestras únicamente a empleados con una sesión activa.
- **FR-002**: El sistema MUST permitir seleccionar el cliente de la muestra solo entre los clientes registrados y activos, mediante una lista desplegable que se filtra a medida que el empleado escribe parte del nombre, la razón social o el número de documento.
- **FR-003**: Al seleccionar un cliente, el sistema MUST mostrar su razón social (o su nombre, si no tiene razón social), su tipo y número de documento (CUIT/DNI) y su correo electrónico.
- **FR-004**: El sistema MUST ofrecer como orígenes elegibles únicamente los orígenes asociados al cliente seleccionado.
- **FR-005**: El sistema MUST permitir dar de alta un origen nuevo desde el mismo formulario de registro de muestra; el origen nuevo MUST quedar asociado al cliente de la muestra y disponible para sus próximas muestras.
- **FR-006**: El sistema MUST impedir orígenes duplicados para un mismo cliente (mismo nombre, sin distinguir mayúsculas/minúsculas ni espacios laterales), reutilizando el origen existente en lugar de crear uno nuevo.
- **FR-007**: El sistema MUST exigir como datos obligatorios: cliente, origen, fecha de muestreo, fecha de ingreso, sitio de extracción y tipo de vertido.
- **FR-007a**: El sitio de extracción MUST ser un texto libre propio de cada muestra (ej. "Canilla de salida del tanque"), distinto del origen; no se reutiliza ni se ofrece como lista.
- **FR-008**: El sistema MUST proponer la fecha de hoy como fecha de muestreo y como fecha de ingreso, permitiendo corregirlas.
- **FR-009**: El sistema MUST validar que la fecha de muestreo no sea posterior a la fecha de ingreso y que ninguna de las dos sea posterior a la fecha actual.
- **FR-010**: El sistema MUST permitir elegir el tipo de vertido solo entre "Agua", "Cloacal" y "Canal", proponiendo "Agua" por defecto.
- **FR-011**: El sistema MUST tratar como opcionales el nombre de la muestra y el responsable del muestreo; si el nombre de la muestra queda vacío, MUST registrarse siempre con el valor fijo "Muestra 1" (sin numeración automática). El responsable del muestreo es un texto libre (nombre de quien tomó la muestra, sea o no empleado del laboratorio) y no se vincula con un usuario del sistema.
- **FR-012**: El sistema MUST asignar automáticamente a cada muestra un N° PI entero y único, igual al mayor N° PI registrado más 1, comenzando en 200001 cuando no hay muestras; el N° PI no es editable por el empleado.
- **FR-013**: El sistema MUST garantizar que el N° PI no se repita aun cuando varias muestras se registren simultáneamente.
- **FR-014**: El sistema MUST registrar automáticamente el usuario que registró la muestra y la fecha y hora del registro, sin que el empleado pueda modificarlos.
- **FR-015**: El sistema MUST dejar toda muestra recién registrada en estado "Ingresada".
- **FR-016**: El sistema MUST impedir guardar una muestra con datos obligatorios faltantes o inválidos, indicando junto a cada dato cuál falta o debe corregirse y conservando los valores ingresados.
- **FR-017**: Antes de guardar, el sistema MUST mostrar un resumen de los datos de la muestra (incluido si el origen es nuevo) y solicitar confirmación explícita; MUST permitir volver a editar o cancelar sin registrar nada.
- **FR-018**: El registro de la muestra y el alta del origen nuevo (si lo hay) MUST ocurrir juntos: o se guardan ambos o ninguno.
- **FR-019**: Al confirmarse el registro, el sistema MUST informar el éxito mostrando el N° PI asignado y volver al formulario de registro vacío (con los valores por defecto) para permitir cargar la siguiente muestra.
- **FR-020**: Esta feature MUST limitarse al alta de la muestra (y de su origen nuevo); la edición, desactivación y consulta/listado de muestras, los cambios de estado posteriores, la asignación de estudios y la persona de contacto (que pertenece al cliente) quedan fuera de alcance.

### Key Entities *(include if feature involves data)*

- **Muestra**: Muestra física de agua ingresada al laboratorio. Atributos: N° PI (código único asignado por el sistema), nombre, cliente, origen, fecha de muestreo, fecha de ingreso, sitio de extracción (texto libre), tipo de vertido (Agua, Cloacal o Canal), responsable del muestreo (opcional, texto libre), estado (inicialmente "Ingresada"), usuario que la registró y fecha y hora del registro.
- **Origen**: Fuente de agua de un cliente (ej. "Pozo N°2") de la que provienen sus muestras. Pertenece a un único cliente y su nombre no se repite dentro de ese cliente. Es la base de la comparación histórica de resultados.
- **Cliente**: Persona o empresa registrada en el laboratorio (US 2.1). Tiene muchos orígenes y muchas muestras.
- **Usuario**: Empleado del laboratorio con sesión activa que registra la muestra (US 1.1/1.2).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Un empleado puede registrar una muestra de un cliente con origen ya conocido, desde que abre el formulario hasta ver el N° PI asignado, en menos de 1 minuto.
- **SC-002**: El 100% de las muestras registradas tiene un N° PI único, consecutivo al anterior, y queda asociada a un cliente, un origen, un usuario registrante y una fecha y hora de registro.
- **SC-003**: El 100% de los intentos de guardar con algún dato obligatorio faltante o inválido es rechazado, indicando el dato a corregir y sin registrar la muestra.
- **SC-004**: El 100% de los orígenes dados de alta al registrar una muestra aparece disponible en el siguiente registro de muestra del mismo cliente y en ningún otro cliente.
- **SC-005**: El 100% de los registros cancelados antes de la confirmación finaliza sin crear muestras ni orígenes y sin consumir un N° PI.

## Assumptions

- Lo que se muestra al elegir el cliente sale de los datos ya registrados del Cliente (US 2.1); si el cliente es una persona sin razón social, se muestra su nombre. El correo mostrado es el correo del cliente, que es también el que se usará para el envío de informes.
- Solo se pueden elegir clientes activos; los inactivos no aparecen en la selección.
- El nombre "Muestra 1" por defecto es un valor fijo indicado por el criterio de aceptación; no se numera automáticamente por cliente ni por origen. La identificación unívoca de la muestra la da el N° PI.
- (Confirmado en Clarifications) "Origen" y "sitio de extracción" son datos distintos: el origen es la fuente de agua reutilizable del cliente (ej. "Pozo N°2"); el sitio de extracción es un texto libre propio de cada muestra que describe dónde se tomó (ej. "Canilla de salida del tanque").
- Las fechas de muestreo e ingreso son solo fechas (sin hora); la hora queda registrada únicamente en la fecha y hora del registro.
- No se admiten fechas futuras ni una fecha de muestreo posterior a la de ingreso: una muestra no puede ingresar antes de tomarse ni registrarse antes de existir. Se permiten fechas pasadas sin límite para cargar ingresos atrasados.
- Como el N° PI se calcula sobre el mayor registrado y las muestras con historial no se borran (se desactivan, según la constitution), un N° PI nunca se reutiliza.
- Cualquier empleado con sesión activa (cuenta aprobada) puede registrar muestras; no se definen permisos adicionales en esta historia.
- Conforme a la constitution, la acción de guardar pide confirmación antes de ejecutarse y los mensajes de éxito y error se muestran con el mecanismo de mensajes habitual de la aplicación.
- La edición o desactivación de orígenes y de muestras, y los demás estados de la muestra, se abordarán en otras historias.
