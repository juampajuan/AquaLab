# Feature Specification: Filtrar estudios por estado y fecha

**Feature Branch**: `028-filtrar-estudios`

**Created**: 2026-11-08

**Status**: Borrador

**Input**: User description: "SCRUM-74 – Filtrar estudios por estado y fecha. Como empleado del laboratorio quiero filtrar los estudios por estado y por fecha de creación para encontrar rápido, por ejemplo, los que están en proceso o los de la última semana. Criterios de aceptación: (1) En «Buscar estudio» se agregan los filtros Estado (todos, pendiente de análisis, en proceso, finalizado o informe generado), Desde y Hasta, ambas fechas incluidas. (2) Los filtros se combinan entre sí y con la búsqueda por texto que ya existe. (3) La paginación conserva los filtros al cambiar de página. (4) Un botón «Limpiar filtros» vuelve al listado completo. (5) Si una fecha no es válida, o «Desde» es posterior a «Hasta», se muestra un error junto al campo y no se filtra. (6) Se reutiliza el mismo patrón de filtros del historial del cliente (US 3.3)."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Filtrar por estado (Priority: P1)

Como empleado del laboratorio, en «Buscar estudio» elijo un estado (por ejemplo, «En proceso») y veo solo los estudios que están en ese estado, para saber qué trabajo tengo abierto.

**Why this priority**: Es el uso más frecuente que motiva la tarea (ver los estudios en proceso) y por sí solo ya acorta la búsqueda.

**Independent Test**: Con estudios en los cuatro estados, elegir «En proceso» y verificar que solo aparecen los estudios en proceso; elegir «Todos» y verificar que aparecen todos.

**Acceptance Scenarios**:

1. **Dado** «Buscar estudio», **cuando** se abre, **entonces** ofrece el filtro **Estado** con las opciones Todos, Pendiente de análisis, En proceso, Finalizado e Informe generado, con «Todos» elegido.
2. **Dados** estudios en distintos estados, **cuando** se elige un estado y se filtra, **entonces** se listan solo los estudios en ese estado, con el contador de resultados de ese listado.
3. **Dado** el filtro en «Todos», **cuando** se filtra, **entonces** no se restringe por estado.
4. **Dado** un estado que no está en la lista (por ejemplo, un enlace modificado a mano), **cuando** se filtra, **entonces** el sistema lo indica junto al campo y no filtra.

---

### User Story 2 - Filtrar por fecha de creación (Priority: P1)

Como empleado del laboratorio, indico una fecha «Desde» y/o «Hasta» y veo solo los estudios creados en ese rango (por ejemplo, los de la última semana).

**Why this priority**: Es el otro filtro explícito de la tarea; junto con el estado cubre los dos ejemplos del pedido.

**Independent Test**: Con estudios creados el 1, el 5 y el 10 de un mes, filtrar del 5 al 10 y verificar que aparecen los del 5 y el 10 (extremos incluidos) y no el del 1; filtrar solo «Desde» 5 o solo «Hasta» 5 y verificar cada lado.

**Acceptance Scenarios**:

1. **Dado** «Buscar estudio», **cuando** se indica «Desde» y/o «Hasta», **entonces** se listan solo los estudios con fecha de creación dentro del rango, con los dos días extremos incluidos completos.
2. **Dado** solo «Desde» o solo «Hasta», **cuando** se filtra, **entonces** el rango queda abierto del otro lado.
3. **Dada** una fecha inválida, **cuando** se filtra, **entonces** el sistema indica el error junto a ese campo y no filtra.
4. **Dado** «Desde» posterior a «Hasta», **cuando** se filtra, **entonces** el sistema indica el error junto a «Desde» y no filtra.

---

### User Story 3 - Combinar, paginar y limpiar (Priority: P2)

Como empleado del laboratorio, combino el estado, el rango de fechas y el texto de búsqueda que ya existía (por ejemplo, «En proceso» de la última semana de un cliente), recorro las páginas sin perder los filtros y, cuando termino, vuelvo al listado completo con «Limpiar filtros».

**Why this priority**: Hace útiles los filtros con muchos estudios, pero cada filtro solo ya funciona sin esto.

**Independent Test**: Con más de 20 estudios que cumplen estado + rango + texto, filtrar con los tres, pasar a la página 2 y verificar que siguen aplicados; pulsar «Limpiar filtros» y verificar que se ve el listado completo con los campos vacíos.

**Acceptance Scenarios**:

1. **Dados** el texto, el estado y el rango, **cuando** se aplican juntos, **entonces** se listan solo los estudios que cumplen todos.
2. **Dados** filtros aplicados con más de una página de resultados, **cuando** se pasa de página, **entonces** los filtros (incluido el texto) se conservan.
3. **Dado** algún filtro o texto recibido, válido o no, **cuando** se muestra la pantalla, **entonces** ofrece «Limpiar filtros», que vuelve al listado completo sin texto ni filtros; sin filtros ni texto no se ofrece.
4. **Dados** filtros (con estado o fechas) que no dejan ningún estudio, **cuando** se aplican, **entonces** el sistema indica que ningún estudio coincide con la búsqueda y los filtros (distinto del aviso de que aún no hay estudios registrados) y ofrece limpiarlos.

---

### Edge Cases

- Fecha de creación en el límite del día (por ejemplo, 23:59 del día «Hasta» o 00:00 del día «Desde»): queda incluida; el día se cuenta en la zona horaria del laboratorio, la misma con la que se muestra la fecha en el listado.
- «Desde» igual a «Hasta»: válido, lista los estudios de ese día.
- Valor inválido en cualquier campo (fecha, estado o texto demasiado largo): se indica junto al campo y el listado se muestra sin filtrar, como en el historial del cliente (US 3.3); los valores ingresados quedan en el formulario para corregirlos.
- Página inexistente con filtros (por ejemplo, tras cambiar los filtros): se muestra la última página disponible, como hoy.
- El estado filtrado es siempre el actual del estudio.
- La pantalla sigue siendo solo de consulta.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: «Buscar estudio» MUST ofrecer, junto a la búsqueda por texto existente, los filtros **Estado** (Todos, Pendiente de análisis, En proceso, Finalizado, Informe generado), **Desde** y **Hasta**, todos opcionales.
- **FR-002**: El filtro Estado MUST dejar solo los estudios cuyo estado actual es el elegido; «Todos» MUST NOT restringir.
- **FR-003**: Desde y Hasta MUST filtrar por la fecha de creación del estudio, con ambos días incluidos completos, contados en la zona horaria del laboratorio; cada uno MUST poder usarse solo.
- **FR-004**: Los filtros y el texto MUST combinarse entre sí: el listado muestra solo los estudios que cumplen todos los criterios indicados.
- **FR-005**: Una fecha inválida, un «Desde» posterior a «Hasta» o un estado fuera de la lista MUST indicarse junto al campo correspondiente, y con cualquier valor inválido el listado MUST mostrarse sin filtrar (mismo comportamiento que el historial del cliente, US 3.3).
- **FR-006**: La paginación MUST conservar el texto y todos los filtros al cambiar de página.
- **FR-007**: Cuando se recibió texto o algún filtro, válido o no, la pantalla MUST ofrecer «Limpiar filtros», que vuelve al listado completo sin texto ni filtros; reemplaza al actual «Ver todos».
- **FR-008**: Si hay algún filtro de estado o fecha aplicado y ningún estudio coincide, MUST indicarse que ningún estudio coincide con la búsqueda y los filtros, con la acción «Limpiar filtros»; con solo texto se mantiene el aviso actual («No se encontraron estudios para «…».»), y si no hay estudios registrados, el aviso actual de que aún no hay estudios.
- **FR-009**: El orden, las columnas, el tamaño de página (20) y los enlaces del listado MUST mantenerse como hoy (US 5.2).
- **FR-010**: Los filtros MUST verse y comportarse como los del historial del cliente (US 3.3): mismos campos de fecha, mismos mensajes de error y misma acción «Limpiar filtros».

### Key Entities *(include if feature involves data)*

- **Estudio** (US 5.1/5.2): se filtra por su estado actual y su fecha de creación.

No se agregan entidades ni datos nuevos: la tarea solo consulta información existente.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Un empleado obtiene los estudios en proceso de la última semana en no más de 3 acciones desde «Buscar estudio».
- **SC-002**: El 100% de los estudios listados con filtros cumplen todos los criterios indicados, y ningún estudio que los cumple queda afuera.
- **SC-003**: Con 1000 estudios registrados, el listado filtrado se muestra en menos de 2 segundos.
- **SC-004**: Ningún valor inválido en los filtros produce una página de error: siempre se ve el mensaje junto al campo.

## Assumptions

- **Trazabilidad**: SCRUM-74 – Filtrar estudios por estado y fecha (tarea de la épica SCRUM-70 «Interfaz y usabilidad», Sprint 4). Responsable: JuanJTorga.
- **Dependencias**: Se apoya en «Buscar estudio» (US 5.2), con su búsqueda por texto compartida con el control previo al informe (US 7.1), y en el patrón de filtros del historial del cliente (US 3.3, ya en `main`).
- **Fecha**: Se filtra por la fecha de creación del estudio, que es la que muestra el listado.
- **Valores inválidos**: Se sigue el historial del cliente: con un valor inválido se muestra el listado sin filtrar y el error junto al campo. Cambia el comportamiento actual de un texto demasiado largo, que hoy no muestra listado.
- **Permisos**: Como hoy, cualquier empleado con sesión puede usar «Buscar estudio».
- **Interfaz**: Diseño de SCRUM-67 y componentes de `templates/ui/`; las ayudas siguen la US 9.1.
- **Datos académicos**: AquaLab es un proyecto FIUBA; los datos de desarrollo y demostración son ficticios (DEMO).
- **Alcance excluido**: Filtros en «Informes» (control previo y emitidos), filtrar por cliente, origen o tipo de estudio como campos separados, cambiar el orden del listado y exportarlo.
