# Feature Specification: Registrar usuario

**Feature Branch**: `001-registrar-usuario`

**Created**: 2026-10-18

**Status**: Draft

**Input**: User description: "SCRUM-41 / US 1.1 - Como usuario del sistema quiero registrarme ingresando mi información personal y credenciales para tener una cuenta autorizada y acceder a las funciones del laboratorio."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Registrar usuario (Priority: P1)

Como usuario del sistema, quiero registrarme ingresando mi información personal y credenciales para tener una cuenta autorizada y acceder a las funciones del laboratorio.

**Why this priority**: La cuenta es la condición de entrada para que una persona pueda autenticarse y utilizar las funciones protegidas del sistema.

**Independent Test**: Se puede probar completando registros válidos, incompletos y duplicados; confirmando o cancelando el alta; y verificando que una cuenta confirmada queda pendiente de aprobación y solo puede iniciar sesión después de que un administrador la apruebe.

**Acceptance Scenarios**:

1. **Given** una persona sin una cuenta registrada, **When** ingresa nombre, apellido, un correo electrónico nuevo y una contraseña, revisa los datos y confirma la operación, **Then** el sistema crea una única cuenta en estado "pendiente de aprobación" e informa que el registro fue recibido y que podrá ingresar cuando un administrador apruebe la cuenta.
2. **Given** un formulario de registro incompleto, **When** la persona intenta continuar, **Then** el sistema identifica los campos obligatorios faltantes y no crea ninguna cuenta.
3. **Given** que ya existe una cuenta con el mismo correo electrónico, **When** otra persona intenta registrarlo usando diferencias de mayúsculas, minúsculas o espacios laterales, **Then** el sistema informa que el correo no está disponible y no crea una cuenta duplicada.
4. **Given** un formulario de registro, **When** el correo electrónico no tiene un formato válido, **Then** el sistema solicita corregirlo antes de permitir la confirmación.
5. **Given** un formulario válido todavía no confirmado, **When** la persona elige volver o cancelar, **Then** el sistema no crea la cuenta y permite continuar editando los datos.
6. **Given** un formulario válido mostrado para revisión, **When** la persona confirma el registro, **Then** el sistema guarda la cuenta una sola vez aunque la confirmación se accione repetidamente.
7. **Given** una cuenta en estado "pendiente de aprobación", **When** la persona intenta iniciar sesión con su correo y contraseña, **Then** el sistema no le permite ingresar.
8. **Given** una cuenta en estado "pendiente de aprobación", **When** un administrador la aprueba, **Then** la persona puede iniciar sesión con el correo y la contraseña registrados.

### Edge Cases

- Un correo que solo difiere de otro por mayúsculas, minúsculas o espacios laterales se considera duplicado, aunque la cuenta existente esté pendiente de aprobación.
- Los espacios laterales accidentales en nombre, apellido y correo no forman parte del valor registrado.
- Una confirmación repetida o un reintento por una respuesta demorada no genera más de una cuenta.
- Si el alta no puede completarse, el sistema informa el resultado y no presenta la cuenta como creada.
- La contraseña no aparece en el resumen de confirmación ni en los mensajes de validación.
- Una cuenta que nunca es aprobada permanece pendiente y no puede iniciar sesión.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema MUST permitir que una persona no autenticada acceda al registro de usuario.
- **FR-002**: El sistema MUST solicitar nombre, apellido, correo electrónico y contraseña como datos obligatorios.
- **FR-003**: El sistema MUST usar el correo electrónico como único identificador de acceso.
- **FR-004**: El sistema MUST validar el formato del correo electrónico.
- **FR-005**: El sistema MUST impedir dos cuentas con el mismo correo electrónico, sin considerar diferencias de mayúsculas, minúsculas o espacios laterales.
- **FR-006**: El sistema MUST mostrar los errores antes de crear la cuenta e indicar qué dato debe corregirse.
- **FR-007**: El sistema MUST conservar los datos válidos ingresados cuando la persona deba corregir otro campo.
- **FR-008**: El sistema MUST presentar una instancia de revisión y solicitar confirmación explícita antes de guardar la cuenta.
- **FR-009**: El sistema MUST permitir volver desde la confirmación para editar o cancelar sin crear la cuenta.
- **FR-010**: El sistema MUST crear como máximo una cuenta por confirmación válida, incluso ante acciones repetidas.
- **FR-011**: El sistema MUST informar claramente si el alta fue exitosa o no pudo completarse.
- **FR-012**: La cuenta creada MUST quedar en estado "pendiente de aprobación" y MUST NOT permitir iniciar sesión hasta ser aprobada.
- **FR-013**: Un administrador del sistema MUST poder aprobar una cuenta pendiente; una vez aprobada, la cuenta queda habilitada para iniciar sesión.
- **FR-014**: El sistema MUST evitar exponer la contraseña en la revisión, los mensajes de validación y la confirmación final.
- **FR-015**: Esta feature MUST limitarse al alta de la cuenta y su aprobación; recuperación de contraseña, verificación de correo, asignación de roles, rechazo o eliminación de solicitudes, notificaciones de aprobación y edición posterior quedan fuera de alcance.
- **FR-016**: El sistema MUST pedir la contraseña dos veces y rechazar el registro si no coinciden. La contraseña MUST tener al menos 8 caracteres, no ser una contraseña de uso común, no estar compuesta solo por números y no parecerse a los datos personales ingresados.

### Key Entities *(include if feature involves data)*

- **Usuario**: Persona que solicita acceso a AquaLab. Posee nombre, apellido, un correo electrónico único y un estado ("pendiente de aprobación" o "aprobada") que indica si puede autenticarse.
- **Credencial**: Información secreta asociada a un usuario que permite comprobar su identidad sin exponerla en pantallas ni mensajes.
- **Administrador**: Usuario con permiso para aprobar cuentas pendientes.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Una persona puede completar un registro válido y recibir la confirmación del alta en menos de 2 minutos.
- **SC-002**: El 100% de los intentos con campos obligatorios faltantes, correo inválido o correo duplicado son rechazados sin crear una cuenta.
- **SC-003**: El 100% de los registros cancelados antes de la confirmación finalizan sin persistir una cuenta.
- **SC-004**: El 100% de las cuentas recién registradas no pueden iniciar sesión hasta ser aprobadas.
- **SC-005**: El 100% de las cuentas aprobadas pueden iniciar sesión con las credenciales registradas.

## Assumptions

- Decisión del equipo: el registro es autogestionado, pero la cuenta queda **pendiente de aprobación** para evitar que cualquier persona acceda a los datos del laboratorio (principio V de la constitution). Esto modifica el criterio original de la US 1.1 ("el usuario registrado debe quedar habilitado para iniciar sesión"); la US se actualiza en Jira y en la planilla.
- Decisión del equipo: el correo electrónico es el único identificador de acceso, y es el mismo que se usa para iniciar sesión (US 1.2).
- La aprobación la realiza un administrador mediante la herramienta de administración del sistema; una pantalla de aprobación propia queda fuera del alcance del Sprint 1.
- El primer administrador se crea durante el setup del proyecto, fuera del flujo de registro.
- Los campos obligatorios del Sprint 1 son nombre, apellido, correo electrónico y contraseña.
- No se asignan ni muestran roles en esta historia; ser administrador es un permiso del sistema, no un rol del dominio. La definición de roles y permisos queda fuera del Sprint 1.
- No se notifica a la persona cuando su cuenta es aprobada; simplemente puede volver a intentar el ingreso.
- No se incluyen verificación de correo, recuperación o cambio de contraseña, autenticación multifactor ni edición de perfil.
- La US 1.2 depende de que existan cuentas aprobadas creadas por esta feature.
