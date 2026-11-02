# Feature Specification: Consultar historial del cliente

**Feature Branch**: `023-historial-cliente`

**Created**: 2026-11-02

**Status**: Borrador

**Input**: User description: "US 3.3 – Consultar historial del cliente. Como empleado del laboratorio quiero consultar el historial de muestras, estudios e informes de un cliente para conocer sus análisis anteriores y responder sus consultas. Criterios de aceptación: (1) Se debe poder acceder al historial desde la ficha del cliente seleccionado. (2) Se deben listar las muestras del cliente con su código (N° PI), fecha de ingreso, estudios asociados y estado de cada estudio. (3) El listado debe ordenarse del más reciente al más antiguo. (4) Se debe poder filtrar por rango de fechas y por estado del estudio. (5) Se debe poder acceder al detalle de cada estudio y, si tiene informe generado, consultarlo. (6) Si el cliente no tiene muestras registradas, el sistema debe indicarlo."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ver el historial del cliente (Priority: P1)

Como empleado del laboratorio, desde la ficha de un cliente abro «Historial» y veo todas sus muestras, de la más reciente a la más antigua, cada una con su N° PI, fecha de ingreso, origen y los estudios que tiene, con el estado de cada uno. Así puedo responderle al cliente qué se le analizó y en qué quedó.

**Why this priority**: Es el núcleo de la historia: sin el listado no hay historial. Por sí solo ya permite responder la consulta típica de un cliente.

**Independent Test**: Con un cliente con tres muestras ingresadas en fechas distintas (una con dos estudios, una con uno y una sin estudios) y otro cliente con una muestra, abrir el historial del primero desde su ficha y verificar que aparecen solo sus tres muestras, ordenadas de la más reciente a la más antigua, con sus estudios y estados.

**Acceptance Scenarios**:

1. **Dada** la ficha de un cliente, **cuando** el empleado la abre, **entonces** ve la acción «Historial» que lleva al historial de ese cliente.
2. **Dado** un cliente con muestras, **cuando** se abre su historial, **entonces** se listan todas sus muestras (y solo las suyas) con N° PI, fecha de ingreso y origen, y debajo de cada una sus estudios con número, tipo de estudio y estado.
3. **Dado** un cliente con muestras de distintas fechas de ingreso, **cuando** se abre su historial, **entonces** las muestras aparecen de la fecha de ingreso más reciente a la más antigua; a igual fecha, primero la de N° PI mayor.
4. **Dada** una muestra sin estudios, **cuando** se muestra en el historial, **entonces** aparece igual, indicando «Sin estudios».
5. **Dado** un cliente sin muestras registradas, **cuando** se abre su historial, **entonces** el sistema indica que el cliente no tiene muestras registradas.
6. **Dado** el historial, **cuando** se muestra, **entonces** el encabezado identifica al cliente (nombre o razón social y documento) y ofrece volver a su ficha.

---

### User Story 2 - Filtrar el historial por fechas y estado (Priority: P2)

Como empleado del laboratorio, en el historial de un cliente con muchas muestras acoto por un rango de fechas de ingreso y por estado del estudio (por ejemplo, «Informe generado» del último trimestre) para encontrar rápido lo que el cliente pregunta.

**Why this priority**: Es un criterio de aceptación explícito y gana valor con clientes de muchos análisis, pero el historial completo de la US 1 ya es útil sin él.

**Independent Test**: Con un cliente con muestras ingresadas en septiembre y octubre, y estudios en distintos estados, filtrar por octubre y verificar que solo quedan las de octubre; filtrar por «Informe generado» y verificar que solo quedan las muestras con algún estudio en ese estado, mostrando solo esos estudios; combinar los dos filtros.

**Acceptance Scenarios**:

1. **Dado** el historial, **cuando** se indica una fecha «desde» y/o «hasta», **entonces** se listan solo las muestras con fecha de ingreso dentro del rango, con los dos extremos incluidos.
2. **Dado** el historial, **cuando** se elige un estado de estudio, **entonces** se listan solo las muestras con al menos un estudio en ese estado y, de cada una, solo los estudios en ese estado.
3. **Dados** los dos filtros, **cuando** se aplican juntos, **entonces** se cumplen ambos.
4. **Dado** un rango con «desde» posterior a «hasta», una fecha inválida o un estado inexistente, **cuando** se aplica, **entonces** el sistema lo indica junto al campo y no filtra.
5. **Dados** filtros que no dejan ninguna muestra, **cuando** se aplican, **entonces** el sistema indica que ninguna muestra coincide con los filtros (distinto del aviso de cliente sin muestras) y ofrece limpiarlos.
6. **Dados** filtros aplicados, **cuando** se pasa de página, **entonces** los filtros se conservan.

---

### User Story 3 - Ir al detalle del estudio, de la muestra o al informe (Priority: P2)

Como empleado del laboratorio, desde el historial abro el detalle de un estudio para ver sus pruebas y resultados, o el de la muestra, y si el estudio tiene informe generado abro el informe emitido.

**Why this priority**: Completa la consulta: el historial dice qué hay y desde acá se llega al dato puntual. Reutiliza pantallas que ya existen (US 5.2, US 7.2).

**Independent Test**: Con un cliente con un estudio en proceso y otro con informe emitido, verificar desde el historial que cada estudio lleva a su detalle, que el N° PI lleva a la ficha de la muestra y que solo el estudio con informe ofrece «Ver informe», que abre el informe emitido.

**Acceptance Scenarios**:

1. **Dado** un estudio en el historial, **cuando** se elige, **entonces** se abre el detalle del estudio (US 5.2).
2. **Dada** una muestra en el historial, **cuando** se elige su N° PI, **entonces** se abre la ficha de la muestra (US 5.2).
3. **Dado** un estudio con informe generado, **cuando** se muestra en el historial, **entonces** ofrece «Ver informe» con el número del informe, que abre el informe emitido (US 7.2).
4. **Dado** un estudio sin informe, **cuando** se muestra, **entonces** no ofrece «Ver informe».

---

### Edge Cases

- Cliente inactivo: su ficha no está disponible (US 3.2), así que tampoco su historial; se aplica el mismo aviso y se vuelve a la búsqueda.
- Cliente inexistente (identificador inválido): página no encontrada.
- Cliente con muchas muestras: el historial se pagina (20 muestras por página, como el resto de los listados) sin cortar los estudios de una muestra entre páginas.
- El estado mostrado es siempre el actual del estudio; el tipo de estudio se muestra como se guardó al crearlo (US 5.2), aunque el catálogo haya cambiado.
- Una muestra con estudios en distintos estados aparece una sola vez; el filtro por estado solo oculta los estudios que no coinciden.
- Filtro por estado sin fechas, o solo «desde» o solo «hasta»: válidos.
- El historial es solo de consulta: no ofrece acciones que modifiquen muestras, estudios ni informes.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: La ficha de un cliente activo MUST ofrecer la acción «Historial», que abre el historial de ese cliente.
- **FR-002**: El historial MUST estar disponible para cualquier empleado con sesión y MUST rechazar clientes inactivos con el mismo aviso que la ficha (US 3.2).
- **FR-003**: El historial MUST listar todas las muestras del cliente, y solo las suyas, con N° PI, fecha de ingreso y origen.
- **FR-004**: Por cada muestra, el historial MUST listar sus estudios con número, tipo de estudio (el guardado al crearlo) y estado actual; una muestra sin estudios MUST indicar «Sin estudios».
- **FR-005**: Las muestras MUST ordenarse por fecha de ingreso de la más reciente a la más antigua y, a igual fecha, por N° PI descendente; los estudios de cada muestra, del más reciente al más antiguo.
- **FR-006**: El historial MUST permitir filtrar por rango de fecha de ingreso (desde, hasta, ambos opcionales e inclusivos) y MUST rechazar un rango con «desde» posterior a «hasta», una fecha inválida o un estado inexistente, indicándolo junto al campo sin filtrar.
- **FR-007**: El historial MUST permitir filtrar por estado del estudio (Pendiente de análisis, En proceso, Finalizado, Informe generado): quedan las muestras con al menos un estudio en ese estado y, de cada una, solo esos estudios.
- **FR-008**: Los filtros MUST poder combinarse y limpiarse, y MUST conservarse al paginar.
- **FR-009**: Si el cliente no tiene muestras, el historial MUST indicar que no tiene muestras registradas; si tiene pero ninguna coincide con los filtros, MUST indicar que ninguna coincide.
- **FR-010**: Cada estudio del historial MUST enlazar a su detalle (US 5.2) y cada N° PI a la ficha de la muestra.
- **FR-011**: Un estudio con informe emitido MUST ofrecer «Ver informe» con el número del informe, que abre el informe emitido (US 7.2); un estudio sin informe MUST NOT ofrecerlo.
- **FR-012**: El historial MUST paginarse de a 20 muestras, con todos los estudios de cada muestra en la misma página.
- **FR-013**: El historial MUST ser solo de consulta y MUST NOT modificar ningún dato.

### Key Entities *(include if feature involves data)*

- **Cliente** (US 2.1): Dueño del historial; se identifica con nombre o razón social y documento.
- **Muestra** (US 4.1): Unidad del historial; N° PI, fecha de ingreso, origen.
- **Estudio** (US 5.1/5.2): Asociado a una muestra; número, tipo de estudio guardado y estado.
- **Informe** (US 7.2): Uno por estudio como máximo; número «INF-000001» y acceso al informe emitido.

No se agregan entidades ni datos nuevos: la historia solo consulta información existente.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Un empleado llega desde la ficha del cliente al informe de un análisis anterior en no más de 3 acciones.
- **SC-002**: Con filtros de fecha y estado, un empleado encuentra un estudio puntual de un cliente con 100 muestras en menos de 30 segundos.
- **SC-003**: El 100% de las muestras del historial pertenecen al cliente consultado y ninguna muestra suya queda afuera sin filtros.
- **SC-004**: El historial de un cliente con 100 muestras se muestra en menos de 2 segundos.

## Assumptions

- **Trazabilidad**: US 3.3 – Consultar historial del cliente. Jira: clave a confirmar (probablemente SCRUM-46: las claves conocidas siguen el orden de `docs/extra/jira-import.csv`, ID 13 + 33). Responsable: Manuelklly.
- **Dependencias**: Se apoya en la ficha del cliente (US 3.1/3.2), las muestras y orígenes (US 4.1), el detalle del estudio y de la muestra (US 5.2) y el informe emitido (US 7.2, ya en `main`). La búsqueda y exportación de informes es de la US 7.3 (rama `022-consultar-exportar-informe`); acá solo se enlaza al informe emitido.
- **Rango de fechas**: Se filtra por fecha de ingreso de la muestra, que es la fecha que muestra el listado.
- **Permisos**: Como la ficha del cliente, cualquier empleado con sesión puede ver el historial.
- **Interfaz**: Pantalla con el diseño de SCRUM-67 y los componentes de `templates/ui/`.
- **Datos académicos**: AquaLab es un proyecto FIUBA; los datos de desarrollo y demostración son ficticios (DEMO).
- **Alcance excluido**: Exportar o imprimir el historial; búsqueda de informes (US 7.3); comparación histórica por origen (US 8.1); filtrar por origen o tipo de estudio; editar desde el historial.
