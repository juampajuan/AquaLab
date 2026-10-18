# Feature Specification: Registrar cliente

**Feature Branch**: `003-registrar-cliente`

**Created**: 2026-10-18

**Status**: Draft

**Input**: User description: "SCRUM-43 / US 2.1 - Como empleado del laboratorio quiero registrar un nuevo cliente con sus datos personales y de contacto para poder asociarle muestras y estudios analíticos."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Registrar cliente (Priority: P1)

Como empleado del laboratorio, quiero registrar un nuevo cliente con sus datos personales y de contacto para poder asociarle muestras y estudios analíticos.

**Why this priority**: Sin un cliente registrado no es posible identificar a quién pertenecen las muestras y los estudios analíticos posteriores.

**Independent Test**: Se puede probar con altas válidas, incompletas, duplicadas y con documentos inválidos; confirmando o cancelando el registro; y verificando que solamente un cliente válido y confirmado queda guardado y puede consultarse.

**Acceptance Scenarios**:

1. **Given** un empleado con sesión activa y un documento que no pertenece a otro cliente, **When** ingresa nombre o razón social, tipo y número de documento, correo electrónico y, opcionalmente, teléfono y domicilio, y confirma, **Then** el sistema crea un único cliente e informa que el alta fue exitosa.
2. **Given** un cliente creado correctamente, **When** el empleado consulta el cliente recién creado (por ejemplo, desde la confirmación del alta), **Then** ve todos los datos registrados.
3. **Given** un alta sin nombre o razón social, tipo de documento, número de documento o correo electrónico, **When** el empleado intenta continuar, **Then** el sistema indica los campos faltantes y no crea el cliente.
4. **Given** un cliente existente con el mismo tipo y número de documento, **When** el empleado intenta registrarlo nuevamente usando espacios o separadores diferentes, **Then** el sistema informa que el cliente ya existe y rechaza el alta.
5. **Given** un alta en curso, **When** el correo electrónico o el teléfono informado no tiene un formato válido, **Then** el sistema solicita corregirlo antes de permitir la confirmación.
6. **Given** un alta válida todavía no confirmada, **When** el empleado vuelve a editar o cancela, **Then** el sistema no guarda el cliente.
7. **Given** los datos válidos mostrados para revisión, **When** el empleado confirma, **Then** el sistema guarda un solo cliente aunque la confirmación se accione repetidamente.
8. **Given** un alta en curso, **When** el número de documento no tiene un formato válido para su tipo (DNI que no tiene 7 u 8 dígitos, o CUIT que no tiene 11 dígitos o cuyo dígito verificador no es correcto), **Then** el sistema solicita corregirlo y no permite la confirmación.

### Edge Cases

- Una empresa puede tener razón social sin nombre personal y una persona puede tener nombre sin razón social; al menos uno de los dos valores es obligatorio.
- Un documento que solo difiere por espacios, puntos o guiones se considera el mismo identificador; el formato se valida sobre el número sin esos separadores.
- Los espacios laterales en datos de texto no forman parte de los valores registrados.
- El correo electrónico es obligatorio y su formato debe ser válido. Si se informa teléfono, su formato debe ser válido; dejar vacíos el teléfono o el domicilio no impide el alta.
- Una confirmación repetida o un reintento por una respuesta demorada no crea clientes duplicados.
- Si el alta no puede completarse, el cliente no aparece disponible para asociar a muestras.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema MUST permitir registrar clientes únicamente a empleados con una sesión activa.
- **FR-002**: El sistema MUST admitir clientes identificados mediante nombre personal o razón social.
- **FR-003**: El sistema MUST solicitar al menos uno entre nombre personal y razón social.
- **FR-004**: El sistema MUST solicitar tipo de documento, limitado a DNI o CUIT, y número de documento.
- **FR-005**: El sistema MUST solicitar el correo electrónico como dato de contacto obligatorio y permitir ingresar teléfono y domicilio como datos opcionales.
- **FR-006**: El sistema MUST validar el formato del correo electrónico y, cuando sea informado, el del teléfono.
- **FR-007**: El sistema MUST impedir dos clientes con el mismo tipo y número de documento, ignorando espacios y separadores de presentación.
- **FR-008**: El sistema MUST mostrar los errores antes de crear el cliente e indicar qué dato debe corregirse.
- **FR-009**: El sistema MUST conservar los datos válidos ingresados cuando el empleado deba corregir otro campo.
- **FR-010**: El sistema MUST presentar una instancia de revisión y solicitar confirmación explícita antes de guardar el cliente.
- **FR-011**: El sistema MUST permitir volver desde la confirmación para editar o cancelar sin crear el cliente.
- **FR-012**: El sistema MUST crear como máximo un cliente por confirmación válida, incluso ante acciones repetidas.
- **FR-013**: El sistema MUST informar claramente si el alta fue exitosa o no pudo completarse.
- **FR-014**: El cliente creado correctamente MUST quedar disponible de inmediato para ser asociado a nuevas muestras.
- **FR-015**: Esta feature MUST limitarse al alta del cliente y su disponibilidad; edición, baja, búsqueda avanzada y asociación efectiva de muestras quedan fuera de alcance.
- **FR-016**: El sistema MUST validar el número de documento según su tipo: DNI de 7 u 8 dígitos; CUIT de 11 dígitos con dígito verificador válido.

### Key Entities *(include if feature involves data)*

- **Cliente**: Persona o empresa que solicita servicios al laboratorio. Se identifica mediante nombre o razón social y un documento único, y tiene al menos un correo electrónico de contacto.
- **Identificación fiscal o personal**: Combinación de tipo de documento y número que distingue de forma única a un cliente.
- **Datos de contacto**: Correo electrónico (obligatorio), teléfono y domicilio (opcionales) que permiten comunicarse con el cliente.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Un empleado puede completar y confirmar un alta válida en menos de 2 minutos.
- **SC-002**: El 100% de los intentos sin identificación obligatoria o con formatos inválidos son rechazados sin crear un cliente.
- **SC-003**: El 100% de los intentos de duplicar un tipo y número de documento existente son rechazados.
- **SC-004**: El 100% de los clientes creados correctamente queda guardado y puede consultarse de inmediato.
- **SC-005**: El 100% de los números de documento con formato inválido para su tipo son rechazados sin crear un cliente.

## Assumptions

- Decisión del equipo: los datos obligatorios del Sprint 1 son nombre o razón social, tipo de documento, número de documento y correo electrónico.
- Teléfono y domicilio son opcionales.
- DNI y CUIT son los únicos tipos de documento contemplados en esta iteración. Para el CUIT se valida también el dígito verificador.
- La "persona de contacto" que la US 3.2 permite editar no se registra en esta historia; queda pendiente de decisión del equipo antes de la spec de la US 3.2.
- La disponibilidad del cliente para asociarlo a muestras se verificará con la US 4.1, cuando exista el registro de muestras.
- La unicidad se evalúa sobre la combinación normalizada de tipo y número de documento.
- La US 1.2 provee la sesión activa requerida para acceder al registro.
- La asociación concreta con muestras pertenece a una historia posterior; esta feature solo garantiza que el cliente quede disponible para esa operación.
- Edición, eliminación, historial y combinación de clientes duplicados quedan fuera del alcance del Sprint 1.
