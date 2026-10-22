# Feature Specification: Buscar cliente registrado

**Feature Branch**: `004-buscar-cliente`

**Created**: 2026-10-22

**Status**: Draft

**Input**: User description: "US 3.1 – Buscar cliente registrado (SCRUM-44). Como empleado del laboratorio quiero buscar un cliente registrado por tipo/número de documento o nombre/razón social para consultar sus datos o seleccionarlo para otros flujos. Criterios de aceptación: Se debe poder buscar por Razón Social, Nombre o CUIT/DNI. El sistema debe listar las coincidencias encontradas. Al seleccionar un cliente, se deben visualizar todos sus datos personales y de contacto vigentes."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Buscar clientes y ver sus datos (Priority: P1)

Como empleado del laboratorio, quiero buscar un cliente registrado por nombre, razón social o número de documento (DNI/CUIT), para ver la lista de coincidencias y consultar los datos personales y de contacto vigentes del cliente que necesito.

**Why this priority**: Es el núcleo de la historia: sin poder encontrar un cliente ya registrado, no se puede consultar su información ni asociarlo a muestras y estudios.

**Independent Test**: Con clientes de prueba registrados, se puede probar buscando por cada criterio (nombre, razón social, documento), verificando la lista de coincidencias y abriendo un resultado para comprobar que muestra todos sus datos vigentes.

**Acceptance Scenarios**:

1. **Given** un empleado con sesión activa y clientes registrados, **When** ingresa parte del nombre de un cliente y busca, **Then** el sistema lista todos los clientes cuyo nombre contiene ese texto.
2. **Given** un empleado con sesión activa y clientes registrados, **When** ingresa parte de una razón social y busca, **Then** el sistema lista todos los clientes cuya razón social contiene ese texto.
3. **Given** un cliente registrado con un DNI o CUIT, **When** el empleado busca por ese número (con o sin puntos, guiones o espacios), **Then** el sistema lista al cliente correspondiente.
4. **Given** una búsqueda con coincidencias, **When** se muestra la lista, **Then** cada resultado muestra al menos el nombre o razón social, el tipo y número de documento y el correo electrónico, para distinguir un cliente de otro.
5. **Given** una lista de coincidencias, **When** el empleado selecciona un cliente, **Then** el sistema muestra todos sus datos personales y de contacto vigentes: nombre, razón social, tipo y número de documento, correo electrónico, teléfono y domicilio.
6. **Given** un texto de búsqueda sin coincidencias, **When** el empleado busca, **Then** el sistema informa que no se encontraron clientes y permite buscar de nuevo.
7. **Given** un texto en mayúsculas, minúsculas o con tildes distintas a las registradas, **When** el empleado busca, **Then** el sistema encuentra igualmente al cliente.

---

### User Story 2 - Seleccionar un cliente para otros flujos (Priority: P2)

Como empleado del laboratorio, quiero poder elegir un cliente de los resultados de la búsqueda para usarlo en otros flujos (por ejemplo, registrar una muestra), sin tener que volver a escribir sus datos.

**Why this priority**: Aporta valor a las historias posteriores, pero hoy no existen esos flujos; esta historia solo debe dejar disponible la selección.

**Independent Test**: Se puede probar verificando que, desde la lista de resultados y desde la vista de datos del cliente, existe una forma de identificar de manera inequívoca al cliente elegido.

**Acceptance Scenarios**:

1. **Given** una lista de coincidencias, **When** el empleado elige un cliente, **Then** el sistema identifica de forma inequívoca a ese cliente (y no a otro con datos parecidos) para continuar el flujo.
2. **Given** dos clientes con el mismo nombre y distinto documento, **When** aparecen en los resultados, **Then** el empleado puede distinguirlos por su tipo y número de documento.

### Edge Cases

- Búsqueda vacía o solo con espacios: el sistema no lista a todos los clientes por error; indica que se debe ingresar un texto de búsqueda.
- Texto de búsqueda muy corto (por ejemplo, un solo carácter): se indica que se ingrese un mínimo de caracteres para acotar los resultados.
- Búsqueda por número parcial de documento: se listan los clientes cuyo documento contiene esos dígitos.
- Muchas coincidencias: la lista se presenta de forma paginada u ordenada para que sea manejable, con un orden consistente.
- Clientes con solo nombre o solo razón social: se encuentran por el dato que tengan registrado.
- El cliente deja de existir o se desactiva entre la búsqueda y la selección: el sistema informa que el cliente no está disponible en vez de mostrar datos obsoletos.
- Un empleado sin sesión activa no puede buscar ni ver datos de clientes.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema MUST permitir buscar clientes únicamente a empleados con sesión activa.
- **FR-002**: El sistema MUST permitir buscar por nombre, por razón social y por número de documento (DNI o CUIT) desde un único campo de búsqueda.
- **FR-003**: El sistema MUST ignorar mayúsculas/minúsculas y tildes al comparar el texto de búsqueda con nombre y razón social.
- **FR-004**: El sistema MUST ignorar espacios, puntos y guiones del texto de búsqueda al compararlo con el número de documento.
- **FR-005**: El sistema MUST listar todos los clientes que coinciden parcialmente con el texto ingresado.
- **FR-006**: El sistema MUST mostrar en cada resultado el nombre o razón social, el tipo y número de documento y el correo electrónico.
- **FR-007**: El sistema MUST rechazar búsquedas vacías o con menos de 2 caracteres, indicando al empleado qué debe ingresar.
- **FR-008**: El sistema MUST informar claramente cuando no hay coincidencias.
- **FR-009**: El sistema MUST permitir seleccionar un cliente de la lista y mostrar todos sus datos personales y de contacto vigentes (nombre, razón social, tipo y número de documento, correo electrónico, teléfono y domicilio).
- **FR-010**: El sistema MUST mostrar siempre los datos actuales del cliente al momento de la consulta, no una copia previa.
- **FR-011**: El sistema MUST identificar de manera inequívoca al cliente seleccionado para que otros flujos puedan reutilizar la selección.
- **FR-012**: El sistema MUST presentar los resultados en un orden consistente y de forma manejable cuando haya muchas coincidencias.
- **FR-013**: Esta feature MUST limitarse a buscar, listar y consultar; el alta, la edición, la baja y la asociación efectiva de muestras quedan fuera de alcance.

### Key Entities *(include if feature involves data)*

- **Cliente**: Persona o empresa registrada en el laboratorio (ver US 2.1). Atributos consultados: nombre, razón social, tipo y número de documento, correo electrónico, teléfono, domicilio y estado.
- **Búsqueda de cliente**: Texto ingresado por el empleado y conjunto de clientes que lo contienen en nombre, razón social o documento. No se guarda; es una consulta.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Un empleado encuentra un cliente registrado y llega a ver sus datos completos en menos de 30 segundos.
- **SC-002**: El 100% de los clientes registrados puede encontrarse buscando por su nombre, su razón social o su número de documento.
- **SC-003**: El 100% de los resultados de una búsqueda contiene el texto buscado en nombre, razón social o documento, y ningún cliente que lo contenga queda fuera de la lista.
- **SC-004**: Los datos mostrados al seleccionar un cliente coinciden en un 100% con los datos registrados vigentes.
- **SC-005**: Dos clientes con nombres iguales o similares siempre pueden distinguirse en la lista por su documento.
- **SC-006**: Los resultados de una búsqueda se muestran de forma inmediata para el empleado (en menos de 2 segundos) con el volumen de clientes esperado del laboratorio.

## Assumptions

- Los empleados autenticados (US 1.2) son los únicos usuarios; no se distinguen roles dentro de esta historia.
- El criterio de la US permite buscar por razón social, nombre o CUIT/DNI; se resuelve con un único campo de búsqueda que revisa los tres datos, sin pedir al empleado que elija el tipo de búsqueda. El tipo de documento no se exige para buscar por número.
- La coincidencia es parcial ("contiene") para facilitar la búsqueda con datos incompletos.
- "Datos vigentes" se entiende como los datos actuales del registro del cliente; esta historia no maneja historial de cambios.
- Los clientes con estado inactivo (por baja lógica, según la constitution) no se ofrecen para seleccionarlos en otros flujos; si se listan en la búsqueda, se identifican como inactivos. Hoy no existe la baja de clientes, por lo que todos los registrados están activos.
- La vista de datos de un cliente ya existe desde la US 2.1 y se reutiliza para mostrar la información al seleccionar un resultado.
- El dato "persona de contacto" no forma parte de esta historia (pendiente de decisión del equipo antes de la US 3.2).
- La integración efectiva con otros flujos (por ejemplo, registrar una muestra, US 4.1) queda fuera de alcance; esta historia solo deja disponible la selección.
- La edición de datos del cliente es parte de la US 3.2 y no se incluye aquí.
