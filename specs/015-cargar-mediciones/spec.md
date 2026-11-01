# Feature Specification: Cargar mediciones

**Feature Branch**: `015-cargar-mediciones`

**Created**: 2026-10-31

**Status**: Aprobada (2026-10-31)

**Input**: User description: "US 6.1 (Jira SCRUM-53) – Cargar mediciones. Como empleado del laboratorio quiero ingresar los valores de las mediciones obtenidas a partir de la muestra para registrar los datos primarios de cada prueba. Criterios de aceptación: (1) Desde un estudio se muestran sus pruebas que esperan carga de datos (estado Pendiente), con su nombre y la unidad de medición. (2) Se puede ingresar la medición cruda de cada prueba (un valor por prueba: lo que leyó el analista, ej. pH, mL gastados, absorbancia). (3) Se pueden cargar algunas pruebas y dejar otras para después; no hace falta completar todo el estudio de una vez. (4) El sistema valida que cada valor tenga formato numérico válido (acepta coma o punto decimal) y muestra el error junto al campo. (5) La medición queda asociada a la prueba del estudio, con el usuario que la cargó y la fecha y hora. (6) Al guardar una medición, la prueba pasa de Pendiente a Cargada. (7) Las pruebas calculadas a partir de otras (es_calculada) no piden medición. Fuera de alcance: calcular el resultado y aplicar fórmulas o límites (US 6.2), modificar mediciones ya cargadas (US 6.3), validar resultados (US 6.4)."

## Clarifications

### Session 2026-10-31

- Q: ¿Cuándo pasa el estudio a "En proceso"? → A: Con su primera medición; desde ahí no se agregan ni quitan pruebas (US 5.3/5.4 sin cambios).
- Q: ¿Cuántos decimales se aceptan y se conservan los ceros finales? → A: Hasta 6 decimales; el valor se conserva tal como se escribió, con sus ceros finales (7,20 sigue siendo 7,20).

### Session 2026-11-01 (ajuste posterior: pruebas A/P)

- Q: ¿Cómo se cargan las pruebas de presencia/ausencia (unidad «A/P» en el catálogo, ej. E. coli y Pseudomonas)? → A: Con un selector Ausente/Presente en lugar del campo numérico. Se guarda 0 (Ausente) o 1 (Presente) sin cambiar el modelo de medición, y las pantallas muestran siempre el texto, sin repetir la unidad.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Cargar las mediciones de las pruebas pendientes de un estudio (Priority: P1)

Como empleado con sesión activa, desde el detalle de un estudio abro la carga de mediciones, veo las pruebas que esperan datos con su nombre y unidad de medición, ingreso el valor que leí para algunas o todas, confirmo, y esas pruebas quedan con su medición registrada y en estado Cargada.

**Why this priority**: Es el objetivo de US 6.1: sin las mediciones crudas no hay cálculo de resultados (US 6.2), ni validación (US 6.4), ni informe.

**Independent Test**: Con un estudio en "Pendiente de análisis" con tres pruebas directas pendientes, cargar el valor de dos, confirmar y verificar que esas dos quedan Cargadas con el valor, el usuario y la fecha y hora, y que la tercera sigue Pendiente y vuelve a ofrecerse en la próxima carga.

**Acceptance Scenarios**:

1. **Dado** un estudio que admite carga de mediciones, **cuando** el empleado abre su detalle, **entonces** encuentra la acción para cargar mediciones.
2. **Dado** un estudio con pruebas en estado Pendiente, **cuando** el empleado abre la carga de mediciones, **entonces** el sistema muestra cada prueba pendiente que requiere medición con su código, nombre y unidad de medición, y un campo para ingresar un único valor por prueba.
3. **Dado** el formulario de carga, **cuando** el empleado completa el valor de algunas pruebas, deja otras vacías y continúa, **entonces** el sistema muestra un resumen con las pruebas y los valores a guardar (con su unidad) y pide confirmación; si cancela o vuelve, no se guarda nada y puede corregir los valores.
4. **Dada** la confirmación, **cuando** se completa la acción, **entonces** cada valor queda registrado como medición de la prueba del estudio, junto con el usuario que la cargó y la fecha y hora; esas pruebas pasan de Pendiente a Cargada, se informa el éxito y las pruebas que quedaron vacías siguen Pendientes.
5. **Dado** un estudio al que ya se le cargaron algunas pruebas, **cuando** el empleado vuelve a abrir la carga, **entonces** solo se ofrecen las pruebas que siguen Pendientes; las Cargadas se pueden consultar en el detalle del estudio con su valor, unidad, usuario y fecha y hora, pero no se modifican desde esta pantalla.
6. **Dado** un estudio en "Pendiente de análisis", **cuando** se guarda su primera medición, **entonces** el estudio pasa a "En proceso".

---

### User Story 2 - Validar los valores ingresados (Priority: P2)

Como empleado, quiero que el sistema rechace valores que no son números y me indique el error junto al campo, para no registrar datos primarios inválidos que arruinen el cálculo posterior.

**Why this priority**: Protege la integridad de los datos del laboratorio, pero solo tiene sentido una vez que existe la carga.

**Independent Test**: Enviar el formulario con valores "7,25", "0.418", "abc", "1.234,5" y todos los campos vacíos; verificar cuáles se aceptan, los mensajes junto a cada campo y que no se guarda nada mientras haya errores.

**Acceptance Scenarios**:

1. **Dado** un valor con coma o punto como separador decimal (ej. "7,25" o "7.25"), **cuando** se envía, **entonces** se acepta y se guarda exactamente el mismo número, sin redondeos ni conversiones.
2. **Dado** un valor que no es un número válido (texto, más de un separador decimal, separadores de miles, notación científica o símbolos), **cuando** se envía, **entonces** el sistema muestra el error junto a ese campo, conserva los demás valores ingresados y no guarda ninguna medición del envío.
3. **Dado** un formulario sin ningún valor ingresado, **cuando** se envía, **entonces** el sistema informa que hay que ingresar al menos una medición y no guarda nada.
4. **Dado** un valor con espacios al principio o al final, **cuando** se envía, **entonces** se ignoran los espacios; un campo con solo espacios cuenta como vacío.

---

### User Story 3 - Impedir cargas no permitidas (Priority: P3)

Como empleado, quiero que el sistema no pida mediciones para pruebas calculadas y rechace cargas sobre pruebas ya cargadas o estudios cerrados, para que cada prueba tenga una única medición confiable.

**Why this priority**: Cubre reglas y casos de concurrencia que no forman parte del flujo principal.

**Independent Test**: Con un estudio que tenga una prueba calculada, abrir la carga y verificar que no pide valor; intentar cargar en un estudio Finalizado; confirmar dos veces la misma carga y verificar que la medición se guarda una sola vez.

**Acceptance Scenarios**:

1. **Dada** una prueba del estudio calculada a partir de otras pruebas, **cuando** se abre la carga de mediciones, **entonces** no se ofrece un campo para ella; se muestra indicando que su resultado se calcula a partir de otras pruebas, y sigue Pendiente.
2. **Dado** un estudio sin pruebas pendientes que requieran medición, **cuando** se abre la carga, **entonces** el sistema informa que no hay mediciones para cargar y no ofrece guardar.
3. **Dado** un estudio "Finalizado" o con "Informe generado", **cuando** se intenta cargar mediciones, **entonces** el sistema no ofrece la acción o la rechaza informando el motivo, sin cambios.
4. **Dada** una prueba que pasó a Cargada después de abrir el formulario (otro empleado la cargó o se reenvió la confirmación), **cuando** se confirma, **entonces** su medición no se reemplaza ni se duplica: se informa que esa prueba ya tenía medición cargada y el resto de las pruebas del envío se guarda normalmente.
5. **Dada** una prueba que se quitó del estudio (US 5.4) después de abrir el formulario, **cuando** se confirma, **entonces** no se registra medición para ella y se informa que ya no forma parte del estudio.
6. **Dado** un usuario sin sesión activa, **cuando** intenta cargar mediciones, **entonces** debe iniciar sesión y no se registra ninguna medición; un estudio inexistente muestra la página de «no encontrado».

### Edge Cases

- Dos empleados cargan al mismo tiempo la misma prueba: se guarda una sola medición (la primera confirmada) y el segundo recibe el aviso de que la prueba ya tenía medición.
- Se intenta quitar una prueba (US 5.4) mientras se confirma su medición: o se quita sin medición o se carga y deja de poder quitarse; nunca queda una medición de una prueba quitada.
- Valores negativos o cero (ej. absorbancia de un blanco): se aceptan; esta historia no valida rangos ni límites (US 6.2).
- Valores con más de 6 decimales o fuera del tamaño admitido: se rechazan con un error junto al campo, en lugar de redondearse.
- Valores con ceros finales (ej. "7,20" o "0,4180"): se guardan y se muestran con los mismos decimales con que se escribieron.
- Una prueba sin unidad de medición definida en el catálogo (ej. pH): se muestra sin unidad, con una indicación visible de que no tiene.
- La unidad de medición o el nombre de la prueba cambian en el catálogo después de cargar: la medición conserva la unidad con la que se cargó.
- Al guardar la primera medición, el estudio pasa a "En proceso" y deja de admitir que se agreguen o quiten pruebas (US 5.3 y US 5.4); las pruebas Pendientes restantes se siguen pudiendo cargar.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema MUST permitir cargar mediciones únicamente a empleados con sesión activa.
- **FR-002**: El sistema MUST ofrecer la acción de cargar mediciones desde el detalle del estudio (US 5.2) cuando el estudio admite carga y tiene al menos una prueba Pendiente que requiere medición.
- **FR-003**: El sistema MUST permitir cargar mediciones solo en estudios "Pendiente de análisis" o "En proceso"; en "Finalizado" o "Informe generado" MUST rechazarlo informando el motivo.
- **FR-004**: La pantalla de carga MUST listar las pruebas del estudio en estado Pendiente que requieren medición, con código, nombre y unidad de medición, y un campo para un único valor por prueba. Las pruebas calculadas a partir de otras MUST mostrarse sin campo, indicando que su resultado se calcula, y no recibir medición.
- **FR-005**: El sistema MUST permitir guardar solo algunas de las pruebas listadas; las que quedan vacías siguen Pendientes y se ofrecen en cargas posteriores. MUST exigir al menos un valor por envío.
- **FR-006**: El sistema MUST aceptar como valor un número decimal con coma o punto como separador decimal, con signo opcional, y rechazar cualquier otro formato (texto, separadores de miles, más de un separador, notación científica, más de 6 decimales o cifras fuera del tamaño admitido), mostrando el error junto al campo correspondiente y conservando los valores ingresados. Excepción: en las pruebas con unidad de medición «A/P» el valor MUST elegirse entre Ausente y Presente (se guarda 0 o 1) y cualquier otro valor MUST rechazarse.
- **FR-007**: Si algún valor del envío es inválido, el sistema MUST NOT guardar ninguna medición de ese envío.
- **FR-008**: El sistema MUST mostrar un resumen de las mediciones a guardar (prueba, valor y unidad) y pedir confirmación antes de guardarlas, permitiendo volver a corregir o cancelar sin cambios.
- **FR-009**: Cada medición MUST guardarse asociada a la prueba del estudio, con el valor exacto ingresado (sin redondeo y con la misma cantidad de decimales, incluidos los ceros finales), la unidad de medición vigente al momento de cargarla, el usuario que la cargó y la fecha y hora de la carga.
- **FR-010**: Al guardar la medición de una prueba, su estado MUST pasar de Pendiente a Cargada en la misma operación. Una prueba Cargada no se puede quitar del estudio (regla de US 5.4).
- **FR-011**: Al guardar la primera medición de un estudio "Pendiente de análisis", el estudio MUST pasar a "En proceso" en la misma operación. Desde ese momento el estudio no admite agregar ni quitar pruebas (regla de US 5.3 y US 5.4, que no cambia).
- **FR-012**: Cada prueba del estudio MUST tener como máximo una medición. Al confirmar, el sistema MUST revalidar cada prueba: si ya está Cargada o ya no forma parte del estudio, la omite sin cambiar sus datos y lo informa; el resto del envío se guarda. Reenviar una misma confirmación, incluso simultáneamente, MUST producir el mismo resultado que un único envío.
- **FR-013**: El sistema MUST informar el resultado de cada carga: cuántas mediciones y de qué pruebas se guardaron, y cuáles se omitieron y por qué.
- **FR-014**: El detalle del estudio MUST mostrar, para cada prueba Cargada, su valor medido con unidad, el usuario que la cargó y la fecha y hora.
- **FR-015**: Las mediciones guardadas MUST NOT modificarse ni borrarse desde esta historia (US 6.3), y cargar mediciones MUST NOT modificar la muestra, el tipo, los datos históricos del estudio, el catálogo de pruebas ni otros estudios.

### Key Entities *(include if feature involves data)*

- **Medición**: Valor crudo leído por el analista para una prueba de un estudio (ej. pH, mL gastados, absorbancia). Atributos: prueba del estudio a la que pertenece (una sola medición por prueba del estudio), valor numérico exacto, unidad de medición al momento de cargarla, usuario que la cargó y fecha y hora de carga. No se borra mientras exista; impide quitar la prueba del estudio.
- **Prueba asignada al estudio**: Pertenencia de una prueba a un estudio (US 5.1/5.3), con su estado individual. Esta historia la pasa de Pendiente a Cargada al recibir su medición.
- **Estudio**: Pasa de "Pendiente de análisis" a "En proceso" con su primera medición.
- **Prueba (catálogo)**: Aporta código, nombre, unidad de medición y si es calculada a partir de otras pruebas (SCRUM-64).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Un empleado puede cargar las mediciones de un estudio de 10 pruebas en menos de 3 minutos, con una sola confirmación.
- **SC-002**: En el 100% de las cargas confirmadas, cada valor guardado coincide exactamente con el ingresado (coma o punto) y queda con su unidad, usuario y fecha y hora.
- **SC-003**: El 100% de los envíos con algún valor inválido termina sin mediciones guardadas y con el error indicado junto a cada campo inválido.
- **SC-004**: En todos los casos de validación, incluidos reenvíos y cargas simultáneas, ninguna prueba del estudio tiene más de una medición y ninguna medición existente se reemplaza.
- **SC-005**: Ninguna prueba calculada recibe una medición, y ningún estudio "Finalizado" o con "Informe generado" recibe mediciones.

## Assumptions

- **Trazabilidad**: US 6.1 – Cargar mediciones. Jira: SCRUM-53. Primera historia del Epic 6.
- **Dependencias**: Se apoya en el detalle del estudio y el estado individual de las pruebas (US 5.2), la regla de quita por estado Pendiente (US 5.4) y el catálogo de pruebas con unidad de medición y marca de calculada (SCRUM-64).
- **Estado "En proceso"**: Se toma la definición de US 5.2: un estudio está "En proceso" cuando al menos una prueba fue cargada o completada (confirmado en Clarifications). Pasar a "Finalizado" no es parte de esta historia (US 6.4).
- **Pruebas calculadas**: Son las marcadas como calculadas a partir de otras pruebas en el catálogo; quedan Pendientes hasta que se calcule su resultado (US 6.2). Las pruebas de tipo Fórmula que no son calculadas usan la medición propia (`x`) y sí piden valor.
- **Unidad**: Se usa la unidad de medición de la prueba (lo que lee el analista), no la unidad del resultado. Se guarda junto con la medición (constitution, principio IV).
- **Precisión**: Hasta 6 decimales, conservando los escritos (Clarifications). La cantidad máxima de cifras enteras se define en el plan, con margen suficiente para las lecturas habituales del laboratorio; los valores se guardan como decimales exactos, nunca como coma flotante.
- **Confirmación**: Guardar mediciones sigue el patrón común de confirmación antes de guardar (constitution, Interfaz).
- **Interfaz**: Las pantallas nuevas siguen el diseño de SCRUM-67 y se arman con los componentes de `templates/ui/`.
- **Datos académicos**: AquaLab es un proyecto FIUBA; los datos de desarrollo y demostración son ficticios (DEMO).
- **Alcance excluido**: Calcular el resultado y aplicar fórmulas o límites (US 6.2); modificar o borrar mediciones ya cargadas (US 6.3); validar resultados y pasar pruebas a Completada o el estudio a Finalizado (US 6.4); informes.
