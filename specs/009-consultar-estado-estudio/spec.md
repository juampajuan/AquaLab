# Feature Specification: Consultar estado del estudio

**Feature Branch**: `009-consultar-estado-estudio`

**Created**: 2026-10-27

**Status**: Draft

**Input**: User description: "US 5.2 – Consultar estado del estudio. Como empleado del laboratorio quiero consultar un estudio y conocer su estado de avance para verificar qué pruebas se encuentran pendientes y cuáles realizadas. Criterios de aceptación: Se debe poder buscar el estudio por identificador, muestra o cliente. Se debe visualizar el estado general del estudio (ej. Pendiente, En Proceso, Finalizado). Se debe mostrar la lista de pruebas asignadas con su estado individual (Pendiente / Completada). Se debe poder consultar la lista de estudios asignados desde la ficha de la muestra (viene de la 4.2, eliminada)."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Buscar estudios y consultar su estado y pruebas asignadas (Priority: P1)

Como empleado del laboratorio, quiero buscar un estudio por su identificador, por la muestra a la que pertenece o por el cliente remitente, y abrir su detalle para ver el estado general del estudio junto con el listado de sus pruebas asignadas y el estado individual de cada una, para verificar qué pruebas se encuentran pendientes y cuáles ya fueron realizadas.

**Why this priority**: Es el flujo principal de la historia: permite localizar cualquier estudio del laboratorio y conocer de inmediato tanto su avance general como el estado de cada una de las pruebas que lo componen.

**Independent Test**: Con muestras, clientes y estudios de prueba registrados en distintos estados de avance, se busca por identificador de estudio, por N° PI o nombre de muestra y por nombre, razón social o documento del cliente; se verifica que la lista muestra las coincidencias con su estado general y que, al abrir un estudio, se visualizan sus datos de cabecera, su estado general y todas sus pruebas asignadas con el estado individual de cada una.

**Acceptance Scenarios**:

1. **Given** un empleado con sesión activa y estudios registrados, **When** busca por el identificador numérico de un estudio, **Then** el sistema lista el estudio cuyo identificador coincide.
2. **Given** un empleado con sesión activa y estudios registrados, **When** busca por el N° PI o por parte del nombre de una muestra, **Then** el sistema lista todos los estudios asociados a las muestras que coinciden.
3. **Given** un empleado con sesión activa y estudios registrados, **When** busca por parte del nombre, de la razón social o del número de documento (DNI o CUIT, con o sin puntos, guiones o espacios) de un cliente, **Then** el sistema lista todos los estudios cuyas muestras pertenecen a los clientes que coinciden.
4. **Given** una búsqueda con coincidencias, **When** se muestra la lista de resultados, **Then** cada fila indica al menos el identificador del estudio, el N° PI y nombre de la muestra, el cliente (razón social o nombre y tipo/número de documento), el tipo de estudio, la fecha de creación y el estado general del estudio (`Pendiente de análisis`, `En proceso`, `Finalizado` o `Informe generado`).
5. **Given** una lista de resultados de búsqueda, **When** el empleado selecciona un estudio, **Then** el sistema muestra la vista de detalle del estudio con su cabecera completa (identificador, muestra con su N° PI, nombre y origen, cliente con su documento, tipo de estudio con su descripción, fecha y hora de creación, usuario creador y estado general del estudio) y la lista de todas las pruebas asignadas indicando el código, el nombre y el estado individual de cada prueba (`Pendiente`, `Cargada` o `Completada`).
6. **Given** un texto de búsqueda en mayúsculas, minúsculas o con tildes distintas a las registradas, **When** el empleado busca por muestra o por cliente, **Then** el sistema encuentra igualmente los estudios correspondientes.
7. **Given** un criterio de búsqueda sin coincidencias, **When** el empleado realiza la búsqueda, **Then** el sistema informa claramente que no se encontraron estudios y permite buscar de nuevo.

---

### User Story 2 - Consultar la lista de estudios asignados desde la ficha de la muestra (Priority: P2)

Como empleado del laboratorio, quiero abrir la ficha de una muestra registrada y ver la lista de todos los estudios que tiene asignados junto con su estado general y acceso al detalle de cada uno, para conocer todos los análisis solicitados sobre esa muestra y navegar entre la muestra y sus estudios.

**Why this priority**: Cubre el cuarto criterio de aceptación (incorporado desde la antigua US 4.2) y conecta la gestión de muestras con el seguimiento de estudios, permitiendo recorrer los análisis tanto desde el buscador de estudios como desde la propia muestra.

**Independent Test**: Con una muestra registrada que tiene varios estudios asignados (y otra sin estudios), se abre la ficha de cada muestra y se comprueba que muestra todos los datos vigentes de la muestra junto con el listado de sus estudios (o el aviso de que aún no tiene estudios) y que al elegir un estudio se accede a su detalle completo.

**Acceptance Scenarios**:

1. **Given** un empleado con sesión activa y una muestra registrada, **When** accede a la ficha de la muestra, **Then** el sistema muestra los datos vigentes de la muestra (N° PI, nombre, cliente, origen, fecha de muestreo, fecha de ingreso, sitio de extracción, tipo de vertido, responsable del muestreo, estado de la muestra, usuario que la registró y fecha y hora de registro) y la sección de estudios asignados.
2. **Given** una muestra que tiene uno o más estudios asignados, **When** el empleado consulta la ficha de la muestra, **Then** el sistema lista todos sus estudios ordenados del más reciente al más antiguo, mostrando para cada uno su identificador, el tipo de estudio, la fecha de creación, el estado general y el resumen de pruebas realizadas sobre el total de pruebas asignadas, con acceso directo al detalle de cada estudio.
3. **Given** una muestra recién registrada que aún no tiene estudios asignados, **When** el empleado consulta la ficha de la muestra, **Then** el sistema informa que la muestra no tiene estudios asignados y ofrece la opción de crear un estudio.
4. **Given** el detalle de un estudio, **When** el empleado selecciona la muestra asociada, **Then** el sistema abre la ficha de esa muestra.

### Edge Cases

- Búsqueda vacía o solo con espacios: el sistema no lista todos los estudios sin filtro; solicita ingresar un criterio de búsqueda.
- Búsqueda por texto no numérico de un solo carácter: el sistema indica que se deben ingresar al menos 2 caracteres para acotar la búsqueda; en cambio, si el valor ingresado es un número entero (ej. `1`), sí se permite buscar porque puede corresponder al identificador de un estudio.
- Una muestra tiene varios estudios (de igual o distinto tipo): todos se listan al buscar por la muestra y en la ficha de la muestra, distinguibles por su identificador, tipo y fecha de creación.
- El tipo de estudio fue renombrado, editado en su descripción o desactivado después de crearse el estudio: tanto en los resultados de búsqueda como en el detalle del estudio y en la ficha de la muestra se muestran el nombre y la descripción históricos que tenía el tipo al momento de crearse el estudio.
- El cliente de la muestra se encuentra inactivo: sus muestras y estudios históricos siguen pudiendo buscarse y consultarse normalmente.
- Muchas coincidencias en la búsqueda: la lista de estudios se presenta ordenada del más reciente al más antiguo y paginada para mantener la lectura clara.
- Consulta de un estudio o de una muestra cuyo identificador no existe: el sistema responde indicando que el registro solicitado no existe.
- Un usuario sin sesión activa intenta buscar estudios, abrir el detalle de un estudio o ver la ficha de una muestra: el sistema no muestra información sensible y redirige al inicio de sesión.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema MUST permitir buscar estudios, consultar el detalle de un estudio y ver la ficha de una muestra únicamente a empleados con sesión activa.
- **FR-002**: El sistema MUST permitir buscar estudios desde un único campo de búsqueda por identificador del estudio, por muestra (N° PI o nombre de la muestra) o por cliente (nombre, razón social o número de documento DNI/CUIT).
- **FR-003**: El sistema MUST ignorar mayúsculas/minúsculas y tildes al comparar el texto de búsqueda con el nombre de la muestra y con el nombre o razón social del cliente.
- **FR-004**: El sistema MUST ignorar espacios, puntos y guiones al comparar el texto de búsqueda con el número de documento (DNI o CUIT) del cliente.
- **FR-005**: El sistema MUST permitir buscar por coincidencia exacta del identificador numérico del estudio (incluso si tiene un solo dígito) y rechazar búsquedas vacías o textos no numéricos de menos de 2 caracteres, indicando al empleado qué debe ingresar.
- **FR-006**: El sistema MUST listar todos los estudios que coincidan con el criterio buscado, ordenados del más reciente al más antiguo y de forma paginada cuando haya muchas coincidencias.
- **FR-007**: En cada resultado de la búsqueda de estudios, el sistema MUST mostrar el identificador del estudio, el N° PI y nombre de la muestra, el cliente (razón social o nombre y tipo/número de documento), el nombre histórico del tipo de estudio, la fecha de creación y el estado general del estudio.
- **FR-008**: El sistema MUST informar claramente cuando una búsqueda de estudios no arroje coincidencias.
- **FR-009**: Al seleccionar un estudio (desde la búsqueda o desde la ficha de una muestra), el sistema MUST mostrar su vista de detalle con los datos de cabecera: identificador del estudio, muestra asociada (N° PI, nombre y origen), cliente (razón social o nombre y documento), tipo de estudio (nombre y descripción históricos), estado general del estudio (`Pendiente de análisis`, `En proceso`, `Finalizado` o `Informe generado`), usuario creador y fecha y hora de creación.
- **FR-010**: En la vista de detalle del estudio, el sistema MUST mostrar la lista de todas las pruebas asignadas al estudio, ordenadas por código de prueba, indicando para cada una su código, su nombre y su estado individual (`Pendiente`, `Cargada` o `Completada`), además de un resumen de cuántas pruebas están completadas y cuántas pendientes o en carga sobre el total.
- **FR-011**: Toda prueba asignada a un estudio MUST iniciar en estado individual `Pendiente` al crearse el estudio, pudiendo encontrarse en `Pendiente`, `Cargada` o `Completada` al momento de la consulta.
- **FR-012**: El sistema MUST proveer una vista de ficha de la muestra donde se visualicen todos los datos vigentes de la muestra (N° PI, nombre, cliente, origen, fecha de muestreo, fecha de ingreso, sitio de extracción, tipo de vertido, responsable del muestreo, estado de la muestra, usuario registrante y fecha y hora de registro) y la lista de todos los estudios asignados a esa muestra.
- **FR-013**: En la ficha de la muestra, cada estudio asignado MUST mostrar su identificador, el nombre histórico del tipo de estudio, la fecha de creación, el estado general del estudio, el conteo de avance de sus pruebas y un enlace directo al detalle del estudio; si la muestra no tiene estudios asignados, el sistema MUST indicarlo claramente.
- **FR-014**: El sistema MUST permitir navegar desde el detalle de un estudio hacia la ficha de su muestra asociada y hacia la ficha de su cliente, así como acceder a la ficha de la muestra recién creada o asociada al estudio.
- **FR-015**: Esta feature MUST limitarse a la búsqueda y consulta del estado de avance de los estudios, sus pruebas asignadas y la ficha de la muestra con sus estudios; la adición o eliminación manual de pruebas del estudio (US 5.3 y US 5.4), la carga de mediciones (US 6.1), el cálculo y validación de resultados (US 6.2 y US 6.4) y la generación de informes (US 7.2) quedan fuera de alcance.

### Key Entities *(include if feature involves data)*

- **Estudio**: Análisis de un tipo determinado aplicado sobre una muestra concreta (ver US 5.1). Atributos consultados: identificador único, muestra asociada, tipo de estudio (nombre y descripción históricos al momento de crearse), estado general (`Pendiente de análisis`, `En proceso`, `Finalizado`, `Informe generado`), usuario creador, fecha y hora de creación y conjunto de pruebas asignadas.
- **Prueba asignada al estudio**: Cada una de las pruebas del catálogo que forman parte de un estudio concreto. Atributos consultados: prueba del catálogo (código y nombre) y estado individual de avance (`Pendiente`, `Cargada`, `Completada`).
- **Muestra**: Muestra física de agua ingresada al laboratorio (ver US 4.1), identificada por su N° PI único y vinculada a un cliente y un origen. Puede tener cero, uno o varios estudios asignados.
- **Cliente**: Persona o empresa remitente de la muestra (ver US 2.1 y US 3.1).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Un empleado con sesión activa puede encontrar un estudio buscando por su identificador, por el N° PI de su muestra o por los datos del cliente y visualizar su estado general y el de sus pruebas en menos de 30 segundos.
- **SC-002**: El 100% de los estudios registrados puede localizarse buscando tanto por su identificador único como por el N° PI o nombre de su muestra y por el nombre, razón social o documento de su cliente.
- **SC-003**: En el 100% de los estudios consultados, el estado general del estudio y el listado de pruebas asignadas con su estado individual coinciden exactamente con los datos vigentes registrados en el sistema.
- **SC-004**: Desde la ficha de cualquier muestra registrada se visualiza el 100% de los estudios asociados a esa muestra y se puede acceder al detalle de cada uno en un solo clic.
- **SC-005**: Los resultados de búsqueda de estudios y las vistas de detalle de estudio y ficha de muestra se presentan al empleado en menos de 2 segundos para el volumen esperado de operaciones del laboratorio.

## Assumptions

- Los empleados autenticados con sesión activa (US 1.2) son los únicos usuarios habilitados para buscar y consultar estudios y muestras; no se distinguen permisos adicionales por rol en esta historia.
- Los estados generales posibles de un estudio, de acuerdo con las definiciones del dominio del laboratorio, son: `Pendiente de análisis`, `En proceso`, `Finalizado` e `Informe generado`. Todo estudio recién creado inicia en `Pendiente de análisis` (US 5.1).
- Los estados individuales posibles de cada prueba asignada a un estudio, de acuerdo con las definiciones del dominio del laboratorio, son: `Pendiente` (sin medición cargada), `Cargada` (con medición registrada pendiente de validación) y `Completada` (resultado validado). Toda prueba asignada inicia en `Pendiente` al crearse el estudio; las transiciones a `Cargada` y `Completada` ocurren en las historias del Epic 6.
- El buscador de estudios utiliza un único campo de texto que evalúa simultáneamente el identificador numérico del estudio, el N° PI y el nombre de la muestra, y el nombre, la razón social y el documento (DNI/CUIT) del cliente, siguiendo el mismo patrón de usabilidad del buscador de clientes (US 3.1).
- Como en la US 4.1 quedó fuera de alcance la vista de consulta/ficha de la muestra y el cuarto criterio de aceptación de esta historia provino de la US 4.2 eliminada (*"Se debe poder consultar la lista de estudios asignados desde la ficha de la muestra"*), esta historia incorpora la vista de ficha de la muestra con sus datos vigentes y el listado de sus estudios asignados.
- Por tratarse únicamente de operaciones de lectura y consulta (sin alta, modificación ni borrado de datos), no se requieren pantallas de confirmación en esta historia.
