# Feature Specification: Modificar las mediciones

**Feature Branch**: `017-modificar-mediciones`

**Created**: 2026-11-01

**Status**: Aprobada (2026-11-01)

**Input**: User description: "US 6.3 (Jira SCRUM-55) – Modificar las mediciones. Como empleado del laboratorio quiero visualizar y modificar los datos de las mediciones para corregir errores de carga antes de la finalización del estudio. Criterios de aceptación: (1) Se deben mostrar los valores cargados previamente para su revisión. (2) Se deben poder editar las mediciones mientras el estudio no esté finalizado. (3) Al modificar un valor, el sistema debe recalcular el resultado automáticamente. (4) Los nuevos valores deben reemplazar a los anteriores y revalidarse. Aclaración del usuario: «estudio finalizado» en esta historia significa que se emitió el informe (estado Informe generado); hasta entonces las mediciones se pueden corregir, también en un estudio en estado Finalizado. Acuerdo con US 6.2 (SCRUM-54, PR #29): el recálculo lo provee la 6.2; esta historia agrega la pantalla y la actualización de la medición, y un resultado validado que se recalcula pierde la validación y vuelve a Cargada para revalidarse."

## Clarifications

### Session 2026-11-01

- Q: ¿Se conserva el historial de valores anteriores de una medición corregida? → A: No: se guarda solo el valor vigente, con quién la cargó y quién la corrigió por última vez (y cuándo). El valor anterior se reemplaza, como pide la tarjeta.
- Q: ¿Se puede borrar una medición? → A: Sí, pero en su propia historia: US 6.5 – Borrar mediciones (SCRUM-72), con spec propia. Esta spec solo cubre corregir valores.
- Q: ¿Quién puede corregir una medición? → A: Cualquier empleado con sesión activa, igual que la carga (US 6.1), no solo quien la cargó; queda registrado quién corrigió.
- Q: ¿Cómo se corrige una prueba A/P? → A: (ajuste posterior) Con el mismo selector Ausente/Presente que la carga (FR-006 de la US 6.1), precargado con el valor vigente; el resumen muestra «Ausente → Presente».

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Corregir mediciones cargadas (Priority: P1)

Como empleado con sesión activa, desde el detalle de un estudio abro la corrección de mediciones, veo las mediciones ya cargadas con su valor, unidad, quién y cuándo las cargó, cambio las que tienen errores, reviso el cambio (valor anterior → valor nuevo) y confirmo. El valor nuevo reemplaza al anterior y los resultados se recalculan solos.

**Why this priority**: Es el objetivo de US 6.3: un error de tipeo en una medición hoy no tiene arreglo y arrastra resultados equivocados al informe.

**Independent Test**: Con un estudio que tiene Cloruro cargado en 2,35 (resultado 23,5 mg/l), corregir la medición a 2,53, confirmar y verificar que la medición es 2,53 y el resultado 25,3 mg/l.

**Acceptance Scenarios**:

1. **Dado** un estudio sin informe emitido que tiene mediciones cargadas, **cuando** el empleado abre su detalle, **entonces** encuentra la acción para corregir mediciones.
2. **Dado** el formulario de corrección, **cuando** se abre, **entonces** muestra cada prueba con medición (código, nombre y unidad de medición) con su valor actual tal como se cargó, quién la cargó y cuándo, en un campo editable.
3. **Dado** el formulario, **cuando** el empleado cambia algunos valores y continúa, **entonces** el sistema muestra un resumen solo con las mediciones que cambian (valor anterior → valor nuevo, con unidad) y pide confirmación; si cancela o vuelve, no cambia nada.
4. **Dada** la confirmación, **cuando** se completa, **entonces** cada valor nuevo reemplaza al anterior, la medición registra quién la corrigió y cuándo, se recalculan el resultado de esas pruebas y el de las que dependen de ellas, y se informa el éxito.
5. **Dado** un estudio en estado Finalizado (todas sus pruebas validadas) sin informe emitido, **cuando** se corrige una medición, **entonces** la corrección se acepta igual que en un estudio En proceso.

---

### User Story 2 - Validar los valores corregidos (Priority: P2)

Como empleado, quiero que el valor corregido se valide igual que al cargarlo, para no reemplazar un dato bueno por uno inválido.

**Why this priority**: Mismo riesgo que en US 6.1: un dato primario inválido arruina los cálculos.

**Independent Test**: Corregir con «abc», con más de 6 decimales y dejando un campo vacío; verificar los mensajes junto a cada campo y que no cambia ninguna medición.

**Acceptance Scenarios**:

1. **Dado** un valor corregido con coma o punto decimal, **cuando** se envía, **entonces** se acepta con las mismas reglas que en la carga (US 6.1): hasta 12 cifras enteras y 6 decimales, conservando los decimales escritos.
2. **Dado** un valor con formato inválido, **cuando** se envía, **entonces** el error se muestra junto al campo, se conservan los valores escritos y no se guarda ninguna corrección del envío.
3. **Dado** un campo vaciado, **cuando** se envía, **entonces** se informa junto al campo que la medición no puede quedar vacía; borrar mediciones es US 6.5 (SCRUM-72).
4. **Dado** un envío en el que ningún valor cambió, **cuando** se continúa, **entonces** se informa que no hay cambios para guardar.

---

### User Story 3 - Revalidar lo que cambió y proteger lo emitido (Priority: P3)

Como empleado, quiero que, si una corrección cambia resultados ya validados, esos resultados vuelvan a quedar pendientes de validar, y que no se pueda corregir nada de un estudio con informe emitido.

**Why this priority**: Protege la integridad de lo que valida el laboratorio y de lo que recibe el cliente; ocurre solo cuando ya hubo validaciones (US 6.4).

**Independent Test**: Con Calcio y Magnesio validados, corregir Calcio y verificar que la confirmación avisa que ambos pierden la validación y que después quedan en Cargada; con el informe emitido, verificar que no se ofrece corregir y que se rechaza.

**Acceptance Scenarios**:

1. **Dada** una corrección que recalcula resultados validados (de la prueba corregida o de las que dependen de ella), **cuando** se revisa, **entonces** el resumen advierte qué pruebas perderán la validación.
2. **Dada** esa corrección confirmada, **cuando** se completa, **entonces** esas pruebas quedan en Cargada con su resultado nuevo, para validarse otra vez.
3. **Dado** un estudio Finalizado al que una corrección le devuelve pruebas a Cargada, **cuando** se completa, **entonces** el estudio vuelve a En proceso.
4. **Dado** un estudio con informe emitido, **cuando** se intenta corregir una medición, **entonces** el sistema no ofrece la acción o la rechaza informando el motivo, y nada cambia.
5. **Dada** una medición que otro empleado corrigió después de abrir el formulario, **cuando** se confirma, **entonces** esa corrección se omite y se informa que la medición cambió mientras se editaba; el resto del envío se guarda.
6. **Dado** un usuario sin sesión activa, **cuando** intenta corregir, **entonces** debe iniciar sesión y nada cambia; un estudio inexistente muestra la página de «no encontrado».

### Edge Cases

- Un valor que solo cambia en la forma de escribirse (7,2 por 7,20) cuenta como cambio: cambia la cantidad de decimales con que se informa.
- Una corrección que hace imposible un cálculo (ej. un divisor que pasa a 0): la medición se corrige igual, la prueba calculada pierde su resultado y vuelve a Pendiente, y se advierte el motivo (US 6.2).
- Las pruebas calculadas no tienen medición y no aparecen en el formulario; se recalculan solas si dependen de una medición corregida.
- Una prueba que se quitó del estudio no tiene medición y no aparece (solo se quitan pruebas Pendientes).
- Las pruebas Pendientes sin medición no aparecen: se cargan con US 6.1.
- Si el informe se emite mientras se edita, la confirmación se rechaza sin cambios.
- Una medición corregida dos veces conserva solo el último valor y la última corrección (quién y cuándo); el valor intermedio no queda registrado (Clarifications).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema MUST permitir corregir mediciones a cualquier empleado con sesión activa, haya cargado o no la medición, y solo a ellos.
- **FR-002**: El detalle del estudio MUST ofrecer la acción de corregir mediciones cuando el estudio no tiene informe emitido y tiene al menos una medición.
- **FR-003**: El formulario de corrección MUST mostrar cada prueba con medición (código, nombre y unidad de medición), con su valor actual tal como se cargó, quién la cargó y cuándo, en un campo editable precargado.
- **FR-004**: Los valores corregidos MUST validarse con las mismas reglas que la carga (US 6.1). Un campo vacío MUST rechazarse junto al campo. Si algún valor es inválido, MUST NOT guardarse ninguna corrección del envío.
- **FR-005**: El sistema MUST mostrar un resumen con las mediciones que cambian (valor anterior → valor nuevo, con unidad) y las pruebas que perderán la validación, y pedir confirmación; un envío sin cambios MUST informarse sin pedir confirmación.
- **FR-006**: Al confirmar, cada valor nuevo MUST reemplazar al anterior conservando la cantidad de decimales escrita, y la medición MUST registrar quién la corrigió y la fecha y hora de la corrección, conservando quién la cargó originalmente y cuándo.
- **FR-007**: En la misma operación, el sistema MUST recalcular el resultado de las pruebas corregidas y el de todas las que dependen de ellas (US 6.2). Si la operación falla, no queda ninguna corrección a medias.
- **FR-008**: Las pruebas cuyo resultado validado se recalcula MUST volver a Cargada para validarse otra vez; si el estudio estaba Finalizado y alguna prueba vuelve a Cargada o Pendiente, el estudio MUST volver a En proceso.
- **FR-009**: Con informe emitido, el sistema MUST NOT permitir corregir mediciones: no ofrece la acción y rechaza el intento informando el motivo.
- **FR-010**: Al confirmar, si una medición cambió desde que se abrió el formulario, el sistema MUST omitir esa corrección e informarlo; el resto del envío se guarda. Reenviar una confirmación ya aplicada MUST NOT volver a cambiar nada.
- **FR-011**: El sistema MUST informar el resultado de la corrección: qué mediciones se corrigieron, cuáles se omitieron y por qué, y qué resultados no se pudieron calcular (US 6.2).
- **FR-012**: El sistema MUST guardar solo el valor vigente de cada medición, con quién la cargó y cuándo, y quién la corrigió por última vez y cuándo; el valor anterior se reemplaza y no se conserva un historial de correcciones. El detalle del estudio MUST mostrar, para una medición corregida, quién la corrigió y cuándo.
- **FR-013**: Corregir mediciones MUST NOT modificar otras mediciones, la muestra, los datos históricos del estudio, el catálogo ni otros estudios.

### Key Entities *(include if feature involves data)*

- **Medición** (US 6.1): Valor crudo de una prueba del estudio. Suma quién la corrigió por última vez y cuándo; conserva quién la cargó y cuándo.
- **Resultado** (US 6.2): Se recalcula al corregir la medición de la que depende; si estaba validado, pierde la validación.
- **Prueba asignada al estudio**: Vuelve de Completada a Cargada si su resultado se recalcula; vuelve a Pendiente si, siendo calculada, la corrección hace que ya no se pueda calcular (US 6.2).
- **Estudio**: Vuelve de Finalizado a En proceso si alguna prueba vuelve a Cargada o Pendiente; con informe emitido no admite correcciones.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Un empleado corrige una medición desde el detalle del estudio en menos de 1 minuto, con una sola confirmación.
- **SC-002**: En el 100% de las correcciones confirmadas, el resultado de la prueba y el de sus dependientes corresponden al valor nuevo inmediatamente después de confirmar.
- **SC-003**: El 100% de los envíos con algún valor inválido termina sin cambios y con el error junto al campo.
- **SC-004**: Ningún resultado validado conserva su validación después de recalcularse, y ningún estudio con informe emitido cambia sus mediciones.
- **SC-005**: Ninguna corrección pisa una corrección hecha por otro empleado mientras se editaba.

## Assumptions

- **Trazabilidad**: US 6.3 – Modificar las mediciones. Jira: SCRUM-55. Responsable: Juan José.
- **Dependencias**: Se apoya en la carga de mediciones (US 6.1: una medición por prueba, reglas de formato) y en el cálculo de resultados (US 6.2: recálculo de la prueba y sus dependientes, rechazo con informe emitido, pérdida de la validación). La rama sale de `016-calcular-resultado` (PR #29 en revisión) y se rebasa sobre `main` cuando se mergee.
- **«Estudio finalizado»**: En esta historia significa informe emitido (aclaración del usuario). El estado Finalizado del sistema (todas las pruebas validadas, antes del informe) todavía admite correcciones.
- **Revalidarse**: Comprende las dos cosas: el valor nuevo pasa por las mismas validaciones de formato que la carga, y los resultados validados que cambian vuelven a quedar pendientes de validar (acuerdo con US 6.2).
- **Estudio Finalizado → En proceso**: La US 6.2 dejó este cambio de estado del estudio a la historia que lo provoca; como la corrección es lo que devuelve pruebas a Cargada o Pendiente, lo hace esta historia.
- **Una pantalla para todas**: Se corrige desde una sola pantalla con todas las mediciones del estudio, igual que la carga (US 6.1); solo se guardan los valores que cambiaron.
- **Interfaz**: Las pantallas siguen el diseño de SCRUM-67 con los componentes de `templates/ui/`.
- **Datos académicos**: AquaLab es un proyecto FIUBA; los datos de desarrollo y demostración son ficticios (DEMO).
- **Alcance excluido**: Borrar mediciones (US 6.5, SCRUM-72); cargar mediciones nuevas (US 6.1); validar resultados (US 6.4); emitir informes (Epic 7).
