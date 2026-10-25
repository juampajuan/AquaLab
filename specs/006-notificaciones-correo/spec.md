# Feature Specification: Notificaciones por correo del alta de usuarios

**Feature Branch**: `006-notificaciones-correo`

**Created**: 2026-10-24

**Status**: Draft

**Input**: User description: "US 1.3 (Jira SCRUM-66) – Notificaciones por correo del alta de usuarios. Como administrador y como solicitante quiero recibir avisos por correo durante el alta de una cuenta para enterarme a tiempo de las solicitudes pendientes y de su resultado. Criterios de aceptación: (1) Al confirmarse un registro, todos los administradores (superusuarios activos) reciben un correo con nombre, apellido y correo del solicitante y un enlace al panel de administración para revisar la solicitud. (2) Al confirmarse un registro, el solicitante recibe un correo que confirma que su solicitud fue recibida y está pendiente de aprobación. (3) Cuando un administrador aprueba una cuenta (acción masiva o ficha del usuario), el solicitante recibe un correo que avisa que ya puede iniciar sesión, con enlace al inicio de sesión. (4) El administrador puede rechazar una solicitud pendiente desde el panel de administración; el sistema pide confirmación antes de rechazar. (5) Al rechazar, el solicitante recibe un correo que informa que su solicitud no fue aprobada; la cuenta no puede iniciar sesión y el correo queda disponible para una nueva solicitud. (6) Cada correo se envía una sola vez por evento: volver a aprobar una cuenta ya aprobada no reenvía el aviso. (7) Si falla el envío, el registro/aprobación/rechazo se completa igual y la falla queda en los logs. (8) Correos en español, identifican a AquaLab, sin contraseña ni datos sensibles. Nota técnica: en desarrollo y tests los correos se muestran en consola; con datos SMTP en .env se envían de verdad."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Aviso a los administradores de una solicitud nueva (Priority: P1)

Como administrador, quiero recibir un correo cada vez que alguien solicita una cuenta, para revisar y aprobar la solicitud a tiempo sin tener que entrar periódicamente al panel de administración a ver si hay pendientes.

**Why this priority**: Sin este aviso, las solicitudes quedan esperando hasta que un administrador entre por casualidad al panel. Es la notificación que destraba todo el circuito de alta: ninguna cuenta se aprueba si nadie se entera de que existe.

**Independent Test**: Con al menos un administrador activo, se registra y confirma una cuenta nueva y se verifica que cada administrador activo recibió un único correo con los datos del solicitante y el enlace para revisar la solicitud.

**Acceptance Scenarios**:

1. **Given** dos administradores activos, **When** una persona completa y confirma su solicitud de registro, **Then** cada administrador activo recibe un correo que informa que hay una solicitud de alta pendiente, con el nombre, el apellido y el correo del solicitante, y un enlace al panel de administración para revisarla.
2. **Given** un administrador inactivo y uno activo, **When** se confirma una solicitud de registro, **Then** solo el administrador activo recibe el aviso.
3. **Given** una persona en la pantalla de revisión del registro, **When** cancela la solicitud o abandona el proceso antes de confirmarla, **Then** ningún administrador recibe aviso.
4. **Given** una solicitud que no puede crearse porque el correo ya está registrado, **When** el solicitante confirma, **Then** no se envía ningún aviso a los administradores.

---

### User Story 2 - Confirmación de solicitud recibida al solicitante (Priority: P1)

Como solicitante, quiero recibir un correo apenas confirmo mi registro, para tener constancia de que mi solicitud llegó y saber que tengo que esperar la aprobación de un administrador antes de poder ingresar.

**Why this priority**: Es la primera respuesta del sistema al solicitante y evita que intente registrarse de nuevo o piense que el registro falló. Se dispara en el mismo momento que el aviso a los administradores.

**Independent Test**: Se registra y confirma una cuenta nueva y se verifica que el correo del solicitante recibió un único mensaje indicando que la solicitud fue recibida y está pendiente de aprobación.

**Acceptance Scenarios**:

1. **Given** una persona que completó el formulario de registro, **When** confirma la solicitud, **Then** recibe en el correo con el que se registró un mensaje que confirma que su solicitud fue recibida, que está pendiente de aprobación y que le avisarán por correo cuando se resuelva.
2. **Given** una solicitud ya confirmada, **When** el solicitante repite la confirmación (por ejemplo, recarga o reenvía el formulario), **Then** no recibe un segundo correo de solicitud recibida.
3. **Given** una persona que cancela la solicitud antes de confirmarla, **When** termina el proceso, **Then** no recibe ningún correo.

---

### User Story 3 - Aviso de aprobación al solicitante (Priority: P1)

Como solicitante, quiero recibir un correo cuando un administrador aprueba mi cuenta, para saber que ya puedo ingresar al sistema sin tener que probar iniciar sesión cada tanto.

**Why this priority**: Cierra el circuito de alta del lado del solicitante. Sin este aviso, el solicitante no sabe cuándo puede empezar a usar AquaLab.

**Independent Test**: Con una cuenta pendiente, un administrador la aprueba desde el panel de administración (de forma masiva o desde la ficha del usuario) y se verifica que el solicitante recibió un único correo de aprobación con el enlace al inicio de sesión.

**Acceptance Scenarios**:

1. **Given** una cuenta pendiente de aprobación, **When** un administrador la aprueba con la acción de aprobación masiva del panel, **Then** el solicitante recibe un correo que le informa que su cuenta fue aprobada y que ya puede iniciar sesión, con un enlace a la pantalla de inicio de sesión de AquaLab.
2. **Given** una cuenta pendiente de aprobación, **When** un administrador la aprueba marcándola como aprobada desde la ficha del usuario y guarda, **Then** el solicitante recibe el mismo correo de aprobación.
3. **Given** varias cuentas pendientes seleccionadas a la vez, **When** un administrador las aprueba con la acción masiva, **Then** cada solicitante recibe su propio correo de aprobación, dirigido solo a él.
4. **Given** una selección que mezcla cuentas pendientes y cuentas ya aprobadas, **When** un administrador aplica la acción de aprobación, **Then** solo los solicitantes de las cuentas que estaban pendientes reciben el correo; las cuentas ya aprobadas no reciben un nuevo aviso.
5. **Given** una cuenta ya aprobada, **When** un administrador edita y guarda otros datos de su ficha sin cambiar su estado de aprobación, **Then** no se envía ningún correo de aprobación.

---

### User Story 4 - Rechazo de una solicitud con aviso al solicitante (Priority: P2)

Como administrador, quiero rechazar desde el panel de administración una solicitud de cuenta que no corresponde, para que no quede pendiente indefinidamente y el solicitante sepa que su solicitud no fue aprobada.

**Why this priority**: Hoy una solicitud que no corresponde solo puede quedar pendiente para siempre o borrarse a mano, sin que el solicitante se entere. Es menos frecuente que la aprobación, por eso va después de los tres avisos principales.

**Independent Test**: Con una cuenta pendiente, un administrador elige rechazarla, confirma el rechazo y se verifica que el solicitante recibió el correo de rechazo, que la cuenta no puede iniciar sesión y que el mismo correo puede usarse para una nueva solicitud.

**Acceptance Scenarios**:

1. **Given** una o más cuentas pendientes seleccionadas en el panel de administración, **When** el administrador elige rechazarlas, **Then** el sistema muestra una pantalla de confirmación que lista las solicitudes a rechazar y no ejecuta ningún cambio hasta que el administrador confirme.
2. **Given** la pantalla de confirmación del rechazo, **When** el administrador cancela, **Then** las solicitudes siguen pendientes y no se envía ningún correo.
3. **Given** la pantalla de confirmación del rechazo, **When** el administrador confirma, **Then** cada solicitante recibe un correo que le informa que su solicitud de cuenta no fue aprobada, y el panel informa cuántas solicitudes se rechazaron.
4. **Given** una solicitud rechazada, **When** el solicitante intenta iniciar sesión con esas credenciales, **Then** no puede ingresar y el sistema responde igual que ante credenciales incorrectas.
5. **Given** una solicitud rechazada, **When** la misma persona vuelve a registrarse con el mismo correo, **Then** el sistema acepta la nueva solicitud como pendiente y se envían los avisos de una solicitud nueva.
6. **Given** una selección que incluye cuentas ya aprobadas, **When** el administrador aplica el rechazo, **Then** el sistema rechaza solo las cuentas pendientes y deja intactas las aprobadas, sin enviarles ningún correo.

---

### Edge Cases

- **Falla en el envío**: si el servicio de correo no está disponible o rechaza un mensaje, el registro, la aprobación o el rechazo se completan igual, el usuario ve el mismo resultado que si el correo hubiera salido y la falla queda registrada en los logs del sistema con el tipo de aviso y el destinatario, sin datos sensibles.
- **Sin administradores activos**: si al confirmarse un registro no hay ningún administrador activo, el registro se completa igual y el sistema deja constancia en los logs de que el aviso no tuvo destinatarios.
- **Administrador que también se registra**: la cuenta de un administrador no es una solicitud; crear administradores por otras vías no dispara ningún aviso de esta feature.
- **Varios administradores aprobando a la vez**: si dos administradores aprueban la misma cuenta casi al mismo tiempo, el solicitante recibe un solo correo de aprobación.
- **Volver a desactivar una cuenta**: desmarcar como aprobada una cuenta ya aprobada no envía ningún correo de esta feature (no es un rechazo de solicitud).
- **Rechazo de una cuenta ya aprobada**: el rechazo aplica solo a solicitudes pendientes; una cuenta aprobada no puede rechazarse por esta vía.
- **Contenido de los correos**: ningún correo incluye la contraseña (ni ingresada ni cifrada), identificadores de sesión ni datos de otras personas; cada correo al solicitante va dirigido solo a él.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Al confirmarse una solicitud de registro, el sistema MUST enviar un aviso a cada administrador activo con el nombre, el apellido y el correo del solicitante, y un enlace al panel de administración para revisar la solicitud.
- **FR-002**: Al confirmarse una solicitud de registro, el sistema MUST enviar al solicitante un correo que confirme que la solicitud fue recibida y está pendiente de aprobación.
- **FR-003**: El sistema MUST NOT enviar avisos de solicitud cuando el registro se cancela, se abandona antes de confirmarse o no puede crearse (por ejemplo, por correo ya registrado).
- **FR-004**: Cuando una cuenta pendiente pasa a estar aprobada, ya sea con la acción de aprobación masiva o desde la ficha del usuario, el sistema MUST enviar al solicitante un correo que le informe que puede iniciar sesión, con un enlace a la pantalla de inicio de sesión de AquaLab.
- **FR-005**: El sistema MUST permitir a los administradores rechazar una o más solicitudes pendientes desde el panel de administración.
- **FR-006**: El sistema MUST pedir confirmación explícita antes de rechazar solicitudes, mostrando cuáles se van a rechazar, y MUST permitir cancelar sin aplicar cambios.
- **FR-007**: Al confirmarse el rechazo, el sistema MUST enviar a cada solicitante rechazado un correo que le informe que su solicitud no fue aprobada.
- **FR-008**: Una solicitud rechazada MUST NOT poder iniciar sesión, y su correo MUST quedar disponible para registrar una nueva solicitud.
- **FR-009**: El rechazo MUST aplicarse solo a cuentas pendientes de aprobación; las cuentas ya aprobadas MUST quedar intactas.
- **FR-010**: Cada aviso MUST enviarse una sola vez por evento: repetir una confirmación de registro, volver a aprobar una cuenta ya aprobada o guardar la ficha de una cuenta sin cambiar su estado de aprobación MUST NOT generar correos nuevos.
- **FR-011**: Una falla en el envío de cualquier correo MUST NOT impedir ni revertir el registro, la aprobación o el rechazo, y MUST quedar registrada en los logs del sistema indicando el tipo de aviso y el destinatario.
- **FR-012**: Todos los correos MUST estar redactados en español, identificar a AquaLab como remitente y MUST NOT incluir contraseñas, identificadores de sesión ni datos personales de terceros.
- **FR-013**: Cada correo dirigido a un solicitante MUST enviarse solo a ese solicitante, sin exponer las direcciones de otros solicitantes ni de los administradores.
- **FR-014**: El sistema MUST permitir que, sin configuración de un servicio de correo real, los avisos se muestren en el registro de actividad del entorno de desarrollo en lugar de enviarse, y que se envíen de verdad cuando se configuren los datos del servicio de correo.
- **FR-015**: Esta feature MUST limitarse a los cuatro avisos del alta de cuentas (solicitud nueva a administradores, solicitud recibida, aprobación y rechazo) y a la acción de rechazo; el envío de informes a clientes, la recuperación de contraseña y la preferencia de no recibir avisos quedan fuera de alcance.

### Key Entities *(include if feature involves data)*

- **Usuario (solicitante)**: Persona que pidió una cuenta en la US 1.1. Mientras no se aprueba, su cuenta está pendiente y no puede iniciar sesión. Aporta nombre, apellido y correo para los avisos.
- **Administrador**: Usuario activo con permisos de administración total, encargado de aprobar o rechazar solicitudes. Es el destinatario del aviso de solicitud nueva.
- **Aviso por correo**: Mensaje que el sistema envía ante un evento del alta (solicitud nueva, solicitud recibida, aprobación o rechazo). Tiene un destinatario, un asunto y un texto en español. No se guarda como dato del sistema; solo las fallas de envío quedan en los logs.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: El 100% de las solicitudes confirmadas genera exactamente un aviso por cada administrador activo y exactamente una confirmación para el solicitante.
- **SC-002**: El 100% de las aprobaciones de cuentas pendientes, por cualquiera de las dos vías del panel, genera exactamente un correo de aprobación para el solicitante, y ninguna acción sobre cuentas ya aprobadas genera correos repetidos.
- **SC-003**: Un administrador puede rechazar una solicitud pendiente, con confirmación incluida, en menos de 30 segundos desde el listado de usuarios.
- **SC-004**: El 100% de los registros, aprobaciones y rechazos se completa correctamente aunque el servicio de correo falle, y cada falla queda registrada.
- **SC-005**: Ninguno de los correos enviados contiene la contraseña del solicitante ni datos de otras personas.

## Assumptions

- Decisión del equipo: el correo de "solicitud recibida" se envía en el momento en que el solicitante confirma el registro, no cuando un administrador la abre.
- Decisión del equipo: el aviso de solicitud nueva va a todos los administradores activos (superusuarios), sin una casilla de correo fija configurada aparte.
- Decisión del equipo: se agrega la acción de rechazo con su aviso, que hoy no existe en el panel de administración.
- Una solicitud rechazada no tiene historial asociado (nunca pudo operar en el sistema), por lo que dejar libre su correo es compatible con el principio de la constitution de no borrar registros con historial.
- Los avisos se disparan desde las dos formas de aprobar que ya existen en el panel de administración (US 1.1): la acción masiva y la marca de aprobada en la ficha del usuario.
- Los enlaces de los correos apuntan a la dirección pública del sistema; en desarrollo, a la dirección local.
- No se envía un aviso a los demás administradores cuando uno de ellos aprueba o rechaza una solicitud.
- Desactivar una cuenta ya aprobada es una operación administrativa distinta del rechazo y no genera correos en esta historia.
