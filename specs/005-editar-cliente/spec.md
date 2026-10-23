# Feature Specification: Editar cliente

**Feature Branch**: `005-editar-cliente`

**Created**: 2026-10-23

**Status**: Draft

**Input**: User description: "SCRUM-45 / US 3.2 - Como empleado del laboratorio quiero modificar los datos de un cliente seleccionado y guardar los cambios para mantener su información de contacto actualizada. Criterios de aceptación: Se debe poder acceder a la edición desde la ficha del cliente seleccionado. Se deben poder modificar teléfono, correo electrónico, domicilio o persona de contacto. El sistema debe validar que los datos modificados cumplan con los formatos esperados. Se debe permitir guardar los cambios o cancelar la operación. Los cambios guardados deben reflejarse inmediatamente en el sistema."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Editar datos de un cliente registrado (Priority: P1)

Como empleado del laboratorio, quiero modificar los datos de un cliente seleccionado desde su ficha y guardar los cambios para mantener su información personal, fiscal y de contacto actualizada y corregir eventuales errores de carga.

**Why this priority**: Mantener actualizados y sin errores los datos del cliente (especialmente correo electrónico, teléfono, domicilio, nombre/razón social y documento) es indispensable para identificarlo correctamente, asociarle muestras y enviarle los informes analíticos.

**Independent Test**: Con un cliente activo registrado, se puede probar abriendo su ficha, accediendo a la edición, modificando sus datos con valores válidos e inválidos, confirmando o cancelando la operación, y verificando que solo los cambios válidos y confirmados reemplazan inmediatamente los datos vigentes en su ficha.

**Acceptance Scenarios**:

1. **Given** un empleado con sesión activa que visualiza la ficha de un cliente registrado, **When** elige editar el cliente, **Then** el sistema muestra el formulario de edición precargado con todos los datos vigentes del cliente (nombre, razón social, tipo de documento, número de documento, correo electrónico, teléfono y domicilio).
2. **Given** el formulario de edición de un cliente, **When** el empleado modifica uno o más datos (correo electrónico, teléfono, domicilio, nombre, razón social o documento) con valores válidos, revisa los cambios y confirma la operación, **Then** el sistema actualiza el cliente, informa que la modificación fue exitosa y muestra la ficha del cliente con los nuevos datos reflejados inmediatamente.
3. **Given** el formulario de edición de un cliente, **When** el empleado deja vacíos tanto el nombre como la razón social, o quita el tipo de documento, el número de documento o el correo electrónico, **Then** el sistema indica los datos obligatorios faltantes y no modifica los datos vigentes del cliente.
4. **Given** el formulario de edición de un cliente, **When** el empleado ingresa un correo electrónico o un teléfono con formato inválido, o un número de documento inválido para su tipo (DNI que no tiene 7 u 8 dígitos, o CUIT de 11 dígitos sin dígito verificador válido), **Then** el sistema solicita corregir el dato erróneo antes de permitir la confirmación y conserva los valores ingresados en el formulario.
5. **Given** dos clientes registrados, **When** el empleado intenta cambiar el tipo y número de documento de uno por el documento que ya pertenece al otro cliente (incluso con espacios, puntos o guiones distintos), **Then** el sistema informa que ya existe otro cliente con ese documento y rechaza el cambio.
6. **Given** el formulario de edición de un cliente, **When** el empleado modifica otros datos pero mantiene el mismo tipo y número de documento del propio cliente, **Then** el sistema permite continuar y confirmar sin considerarlo un duplicado.
7. **Given** una edición en curso en el formulario o en la instancia de revisión previa a confirmar, **When** el empleado elige volver a editar o cancelar la operación, **Then** el sistema no guarda ningún cambio, mantiene intactos los datos previos del cliente y regresa a su ficha.
8. **Given** los cambios válidos mostrados para revisión, **When** el empleado confirma la edición repetidamente, **Then** el sistema aplica la actualización de forma segura sin producir errores ni inconsistencias.

### Edge Cases

- Conservar el propio tipo y número de documento del cliente editado (con o sin puntos, guiones o espacios) es válido y no dispara error de cliente duplicado.
- Un cliente puede pasar de tener solo nombre a tener razón social (o ambos), siempre que al menos uno de los dos quede completo.
- Los espacios laterales accidentales en campos de texto y los separadores en el número de documento (puntos, guiones, espacios) se normalizan antes de validar y guardar.
- El teléfono y el domicilio son opcionales: el empleado puede agregarlos, modificarlos o vaciarlos (borrar un teléfono o domicilio anterior) y el sistema guarda el cambio válido.
- Si el cliente está inactivo o no existe cuando se intenta acceder a su edición o confirmar los cambios, el sistema informa que el cliente no está disponible y no realiza modificaciones.
- Si ocurre una falla al intentar guardar los cambios confirmados, el sistema informa que no pudo completarse la actualización y conserva los datos anteriores sin presentarlos como actualizados.
- Un empleado sin sesión activa no puede acceder a la edición ni enviar modificaciones de un cliente.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema MUST permitir editar clientes únicamente a empleados con una sesión activa.
- **FR-002**: El sistema MUST ofrecer el acceso a la edición desde la ficha del cliente seleccionado.
- **FR-003**: El sistema MUST mostrar en la edición los datos vigentes del cliente como punto de partida.
- **FR-004**: El sistema MUST permitir modificar todos los datos editables del cliente: nombre, razón social, tipo de documento (DNI o CUIT), número de documento, correo electrónico, teléfono y domicilio.
- **FR-005**: El sistema MUST exigir que al menos uno entre nombre y razón social esté completo, además del tipo de documento, número de documento y correo electrónico como datos obligatorios, permitiendo dejar vacíos teléfono y domicilio.
- **FR-006**: El sistema MUST validar el formato del correo electrónico, del teléfono (cuando se informe) y del número de documento según su tipo (DNI de 7 u 8 dígitos; CUIT de 11 dígitos con dígito verificador válido).
- **FR-007**: El sistema MUST impedir que se asigne a un cliente una combinación de tipo y número de documento (normalizado sin espacios, puntos ni guiones) que ya pertenezca a otro cliente registrado, permitiendo conservar el documento propio del cliente editado.
- **FR-008**: El sistema MUST mostrar los errores de validación antes de aplicar los cambios, indicando qué dato debe corregirse y conservando los valores ingresados por el empleado.
- **FR-009**: El sistema MUST presentar una instancia de revisión y solicitar confirmación explícita antes de guardar los cambios del cliente.
- **FR-010**: El sistema MUST permitir volver desde la instancia de revisión para seguir editando los datos antes de confirmar.
- **FR-011**: El sistema MUST permitir cancelar la edición en cualquier momento previo a la confirmación, regresando a la ficha del cliente sin modificar sus datos vigentes.
- **FR-012**: Al confirmarse la edición, el sistema MUST persistir los cambios e informar claramente que la actualización fue exitosa, reflejando los nuevos datos de inmediato en la ficha del cliente y en las búsquedas posteriores.
- **FR-013**: El sistema MUST impedir la edición de clientes inactivos o inexistentes, informando que el cliente no está disponible.
- **FR-014**: Esta feature MUST limitarse a la modificación de los datos del cliente seleccionado; el alta, la baja o desactivación, la fusión de clientes y el historial de auditoría de cambios quedan fuera de alcance.

### Key Entities *(include if feature involves data)*

- **Cliente**: Persona o empresa registrada en el laboratorio (creada en la US 2.1 y consultada en la US 3.1), cuyos datos de identificación (nombre, razón social, tipo y número de documento) y de contacto (correo electrónico, teléfono y domicilio) se actualizan manteniendo su mismo identificador interno y sus asociaciones en el sistema.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Un empleado puede modificar los datos de un cliente desde su ficha y confirmar los cambios en menos de 1 minuto.
- **SC-002**: El 100% de las ediciones confirmadas se refleja de forma inmediata al consultar la ficha del cliente o buscarlo por sus nuevos datos.
- **SC-003**: El 100% de los intentos de guardar datos con campos obligatorios vacíos, formatos inválidos (documento, correo o teléfono) o documento perteneciente a otro cliente es rechazado sin alterar los datos vigentes del cliente.
- **SC-004**: El 100% de las ediciones canceladas antes de la confirmación finaliza manteniendo intactos los datos previos del cliente.

## Assumptions

- Decisión del equipo: no se agrega un campo "persona de contacto" al cliente; para la comunicación y el envío de informes basta con el correo electrónico obligatorio y los datos existentes de la ficha (nombre, razón social, teléfono y domicilio).
- Decisión del equipo: además de los datos de contacto (correo electrónico, teléfono y domicilio), se permite editar también nombre, razón social, tipo de documento y número de documento para poder subsanar errores cometidos durante el alta del cliente (US 2.1).
- Se aplican las mismas reglas de validación y normalización definidas en el alta de cliente (US 2.1): DNI de 7 u 8 dígitos, CUIT de 11 dígitos con dígito verificador válido, teléfono opcional de 7 a 15 dígitos y correo electrónico obligatorio.
- Conforme al principio de Interfaz (UI) de la constitution de AquaLab, toda acción que guarda cambios sobre datos existentes solicita confirmación explícita antes de ejecutarse.
- Los cambios actualizan directamente los datos vigentes del cliente; no se requiere conservar un historial de versiones de los datos de contacto o identificación.
- Solo se editan clientes activos; la baja o reactivación de clientes no forma parte de esta historia.
