# Feature Specification: Registrar cliente

**Feature Branch**: `003-registrar-cliente`

**Created**: 2026-10-18

**Status**: Draft

**Input**: User description: "SCRUM-43 / US 2.1 - Como empleado del laboratorio quiero registrar un nuevo cliente con sus datos personales y de contacto para poder asociarle muestras y estudios analíticos."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Registrar cliente (Priority: P1)

Como empleado del laboratorio, quiero registrar un nuevo cliente con sus datos personales y de contacto para poder asociarle muestras y estudios analíticos.

**Why this priority**: Sin un cliente registrado no es posible identificar a quién pertenecen las muestras y los estudios analíticos posteriores.

**Independent Test**: Se puede probar con altas válidas, incompletas y duplicadas; confirmando o cancelando el registro; y verificando que solamente un cliente válido y confirmado queda disponible para asociarlo a nuevas muestras.

**Acceptance Scenarios**:

1. **Given** un empleado con sesión activa y un identificador que no pertenece a otro cliente, **When** ingresa nombre o razón social, tipo y número de documento, agrega los datos de contacto disponibles y confirma, **Then** el sistema crea un único cliente e informa que el alta fue exitosa.
2. **Given** un cliente creado correctamente, **When** el empleado inicia el registro de una nueva muestra, **Then** el cliente aparece disponible para ser asociado sin pasos adicionales.
3. **Given** un alta sin nombre o razón social, tipo de documento o número de documento, **When** el empleado intenta continuar, **Then** el sistema indica los campos faltantes y no crea el cliente.
4. **Given** un cliente existente con el mismo tipo y número de documento, **When** el empleado intenta registrarlo nuevamente usando espacios o separadores diferentes, **Then** el sistema informa que el cliente ya existe y rechaza el alta.
5. **Given** datos de contacto opcionales ingresados, **When** el teléfono o correo no tiene un formato válido, **Then** el sistema solicita corregirlo antes de permitir la confirmación.
6. **Given** un alta válida todavía no confirmada, **When** el empleado vuelve a editar o cancela, **Then** el sistema no guarda el cliente.
7. **Given** los datos válidos mostrados para revisión, **When** el empleado confirma, **Then** el sistema guarda un solo cliente aunque la confirmación se accione repetidamente.

### Edge Cases

- Una empresa puede tener razón social sin nombre personal y una persona puede tener nombre sin razón social; al menos uno de los dos valores es obligatorio.
- Un documento que solo difiere por espacios, puntos o guiones se considera el mismo identificador.
- Los espacios laterales en datos de texto no forman parte de los valores registrados.
- Si se informa correo electrónico o teléfono, su formato debe ser válido; dejarlos vacíos no impide el alta.
- Una confirmación repetida o un reintento por una respuesta demorada no crea clientes duplicados.
- Si el alta no puede completarse, el cliente no aparece disponible para asociar a muestras.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema MUST permitir registrar clientes únicamente a empleados con una sesión activa.
- **FR-002**: El sistema MUST admitir clientes identificados mediante nombre personal o razón social.
- **FR-003**: El sistema MUST solicitar al menos uno entre nombre personal y razón social.
- **FR-004**: El sistema MUST solicitar tipo de documento, limitado a DNI o CUIT, y número de documento.
- **FR-005**: El sistema MUST permitir ingresar teléfono, correo electrónico y domicilio como datos de contacto opcionales.
- **FR-006**: El sistema MUST validar el formato de los datos de contacto cuando sean informados.
- **FR-007**: El sistema MUST impedir dos clientes con el mismo tipo y número de documento, ignorando espacios y separadores de presentación.
- **FR-008**: El sistema MUST mostrar los errores antes de crear el cliente e indicar qué dato debe corregirse.
- **FR-009**: El sistema MUST conservar los datos válidos ingresados cuando el empleado deba corregir otro campo.
- **FR-010**: El sistema MUST presentar una instancia de revisión y solicitar confirmación explícita antes de guardar el cliente.
- **FR-011**: El sistema MUST permitir volver desde la confirmación para editar o cancelar sin crear el cliente.
- **FR-012**: El sistema MUST crear como máximo un cliente por confirmación válida, incluso ante acciones repetidas.
- **FR-013**: El sistema MUST informar claramente si el alta fue exitosa o no pudo completarse.
- **FR-014**: El cliente creado correctamente MUST quedar disponible de inmediato para ser asociado a nuevas muestras.
- **FR-015**: Esta feature MUST limitarse al alta del cliente y su disponibilidad; edición, baja, búsqueda avanzada y asociación efectiva de muestras quedan fuera de alcance.

### Key Entities *(include if feature involves data)*

- **Cliente**: Persona o empresa que solicita servicios al laboratorio. Se identifica mediante nombre o razón social y un documento único, y puede incluir datos de contacto.
- **Identificación fiscal o personal**: Combinación de tipo de documento y número que distingue de forma única a un cliente.
- **Datos de contacto**: Teléfono, correo electrónico y domicilio opcionales que permiten comunicarse con el cliente.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Un empleado puede completar y confirmar un alta válida en menos de 2 minutos.
- **SC-002**: El 100% de los intentos sin identificación obligatoria o con formatos inválidos son rechazados sin crear un cliente.
- **SC-003**: El 100% de los intentos de duplicar un tipo y número de documento existente son rechazados.
- **SC-004**: El 100% de los clientes creados correctamente queda disponible de inmediato para seleccionarlo al registrar una nueva muestra.
- **SC-005**: Al menos el 90% de empleados representativos puede registrar un cliente correctamente en el primer intento, sin asistencia externa.

## Assumptions

- Los datos obligatorios del Sprint 1 son nombre o razón social, tipo de documento y número de documento.
- Teléfono, correo electrónico y domicilio son opcionales porque Jira indica que se deben poder ingresar, pero no los declara obligatorios.
- DNI y CUIT son los únicos tipos de documento contemplados en esta iteración.
- La unicidad se evalúa sobre la combinación normalizada de tipo y número de documento.
- La US 1.2 provee la sesión activa requerida para acceder al registro.
- La asociación concreta con muestras pertenece a una historia posterior; esta feature solo garantiza que el cliente quede disponible para esa operación.
- Edición, eliminación, historial y combinación de clientes duplicados quedan fuera del alcance del Sprint 1.
