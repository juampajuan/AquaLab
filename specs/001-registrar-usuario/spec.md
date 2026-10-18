# Feature Specification: Registrar usuario

**Feature Branch**: `001-registrar-usuario`

**Created**: 2026-10-18

**Status**: Draft

**Input**: User description: "SCRUM-41 / US 1.1 - Como usuario del sistema quiero registrarme ingresando mi información personal y credenciales para tener una cuenta autorizada y acceder a las funciones del laboratorio."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Registrar usuario (Priority: P1)

Como usuario del sistema, quiero registrarme ingresando mi información personal y credenciales para tener una cuenta autorizada y acceder a las funciones del laboratorio.

**Why this priority**: La cuenta es la condición de entrada para que una persona pueda autenticarse y utilizar las funciones protegidas del sistema.

**Independent Test**: Se puede probar completando registros válidos, incompletos y duplicados; confirmando o cancelando el alta; y verificando que solamente una cuenta válida y confirmada queda disponible para iniciar sesión.

**Acceptance Scenarios**:

1. **Given** una persona sin una cuenta registrada, **When** ingresa nombre, apellido, un identificador de acceso nuevo y una contraseña, revisa los datos y confirma la operación, **Then** el sistema crea una única cuenta activa y comunica que el registro fue exitoso.
2. **Given** un formulario de registro incompleto, **When** la persona intenta continuar, **Then** el sistema identifica los campos obligatorios faltantes y no crea ninguna cuenta.
3. **Given** que ya existe una cuenta con el mismo identificador de acceso, **When** otra persona intenta registrarlo usando diferencias de mayúsculas, minúsculas o espacios laterales, **Then** el sistema informa que el identificador no está disponible y no crea una cuenta duplicada.
4. **Given** que la persona eligió un correo electrónico como identificador, **When** el correo no tiene un formato válido, **Then** el sistema solicita corregirlo antes de permitir la confirmación.
5. **Given** un formulario válido todavía no confirmado, **When** la persona elige volver o cancelar, **Then** el sistema no crea la cuenta y permite continuar editando los datos.
6. **Given** un formulario válido mostrado para revisión, **When** la persona confirma el registro, **Then** el sistema guarda la cuenta una sola vez aunque la confirmación se accione repetidamente.
7. **Given** una cuenta creada correctamente, **When** la persona intenta iniciar sesión con el identificador y la contraseña registrados, **Then** la cuenta se encuentra habilitada para autenticarse.

### Edge Cases

- Un identificador que solo difiere de otro por mayúsculas, minúsculas o espacios laterales se considera duplicado.
- Si el identificador tiene formato de correo electrónico, su estructura debe ser válida.
- Los espacios laterales accidentales en nombre, apellido e identificador no forman parte del valor registrado.
- Una confirmación repetida o un reintento por una respuesta demorada no genera más de una cuenta.
- Si el alta no puede completarse, el sistema informa el resultado y no presenta la cuenta como creada.
- La contraseña no aparece en el resumen de confirmación ni en los mensajes de validación.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema MUST permitir que una persona no autenticada acceda al registro de usuario.
- **FR-002**: El sistema MUST solicitar nombre, apellido, identificador de acceso y contraseña como datos obligatorios.
- **FR-003**: El sistema MUST aceptar como identificador de acceso un nombre de usuario o un correo electrónico.
- **FR-004**: El sistema MUST validar el formato cuando el identificador ingresado sea un correo electrónico.
- **FR-005**: El sistema MUST impedir dos cuentas con el mismo identificador de acceso, sin considerar diferencias de mayúsculas, minúsculas o espacios laterales.
- **FR-006**: El sistema MUST mostrar los errores antes de crear la cuenta e indicar qué dato debe corregirse.
- **FR-007**: El sistema MUST conservar los datos válidos ingresados cuando la persona deba corregir otro campo.
- **FR-008**: El sistema MUST presentar una instancia de revisión y solicitar confirmación explícita antes de guardar la cuenta.
- **FR-009**: El sistema MUST permitir volver desde la confirmación para editar o cancelar sin crear la cuenta.
- **FR-010**: El sistema MUST crear como máximo una cuenta por confirmación válida, incluso ante acciones repetidas.
- **FR-011**: El sistema MUST informar claramente si el alta fue exitosa o no pudo completarse.
- **FR-012**: La cuenta creada correctamente MUST quedar activa y disponible de inmediato para iniciar sesión.
- **FR-013**: El sistema MUST evitar exponer la contraseña en la revisión, los mensajes de validación y la confirmación final.
- **FR-014**: Esta feature MUST limitarse al alta de la cuenta; recuperación de contraseña, verificación de correo, asignación de roles y edición posterior quedan fuera de alcance.

### Key Entities *(include if feature involves data)*

- **Usuario**: Persona habilitada para acceder a AquaLab. Posee nombre, apellido, un identificador de acceso único y un estado que indica si puede autenticarse.
- **Credencial**: Información secreta asociada a un usuario que permite comprobar su identidad sin exponerla en pantallas ni mensajes.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Una persona puede completar un registro válido y recibir la confirmación del alta en menos de 2 minutos.
- **SC-002**: El 100% de los intentos con campos obligatorios faltantes, correo inválido o identificador duplicado son rechazados sin crear una cuenta.
- **SC-003**: El 100% de los registros cancelados antes de la confirmación finalizan sin persistir una cuenta.
- **SC-004**: El 100% de las cuentas creadas correctamente quedan disponibles de inmediato para iniciar sesión con las credenciales registradas.
- **SC-005**: Al menos el 90% de usuarios representativos puede completar el alta correctamente en el primer intento, sin asistencia externa.

## Assumptions

- El registro es autogestionado y no requiere aprobación posterior, porque la historia indica que la cuenta queda habilitada para iniciar sesión.
- La persona elige un único identificador de acceso: nombre de usuario o correo electrónico. Ese mismo identificador se utiliza para iniciar sesión.
- Los campos obligatorios del Sprint 1 son nombre, apellido, identificador de acceso y contraseña.
- No se asignan ni muestran roles en esta historia; la definición de roles y permisos queda fuera del Sprint 1.
- No se incluyen verificación de correo, recuperación o cambio de contraseña, autenticación multifactor ni edición de perfil.
- La US 1.2 depende de que existan cuentas activas creadas por esta feature.
