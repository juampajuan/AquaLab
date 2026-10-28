# Feature Specification: Agregar y quitar pruebas de un estudio

**Feature Branch**: `009-gestionar-pruebas-estudio`

**Created**: 2026-10-27

**Status**: Draft

**Input**: User description: "US 5.3 y 5.4 – Agregar y quitar pruebas de un estudio. US 5.3: Como empleado del laboratorio quiero agregar una prueba adicional a un estudio existente para personalizar el análisis según los requerimientos específicos del cliente. Criterios de aceptación: sobre un estudio que permita modificaciones, se debe poder abrir el catálogo de pruebas; se debe poder seleccionar y añadir una prueba adicional; no se debe permitir añadir una prueba que ya forme parte del estudio; la prueba añadida debe sumarse a la lista de pruebas pendientes a realizar. US 5.4: Como empleado del laboratorio quiero quitar una prueba de un estudio para no realizar ensayos innecesarios si no fueron solicitados. Criterios de aceptación: se debe poder seleccionar una prueba del estudio para quitarla; solo se pueden eliminar pruebas que no tengan mediciones cargadas ni resultados guardados; el sistema debe pedir confirmación antes de efectuar la eliminación; la prueba eliminada no debe incluirse en la carga de mediciones ni en el informe final. Alcance excluido: administración del catálogo y definición de pruebas (US 5.5 y precarga científica); búsqueda y consulta general del avance y listado desde la ficha de muestra (US 5.2); mediciones, resultados, informes y cambios posteriores de estado."

## Clarifications

### Session 2026-10-27

- Q: ¿La vista mínima del estudio forma parte de esta spec o se espera a US 5.2? → A: Forma parte de esta spec (cabecera + pruebas + acciones), con acceso desde el mensaje de éxito de US 5.1; US 5.2 la amplía.
- Q: ¿Una prueba quitada se borra o se conserva marcada como quitada? → A: Se borra la asignación; sin mediciones ni resultados no tiene historial.
- Q: ¿Un estudio puede quedar sin pruebas? → A: No; la última prueba no se puede quitar.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Agregar una prueba adicional a un estudio (Priority: P1)

Como empleado con sesión activa, quiero abrir un estudio que todavía admite cambios, elegir del catálogo una prueba que no tenga y agregarla, para que el análisis cubra lo que pidió el cliente además de las pruebas del tipo.

**Why this priority**: Es el objetivo de US 5.3 y el caso más frecuente de personalización: el cliente pide un ensayo que el tipo de estudio no trae por defecto.

**Independent Test**: Con un estudio en "Pendiente de análisis" creado por US 5.1 y una prueba del catálogo que no forma parte de él, agregarla y verificar que aparece una sola vez en el estudio como pendiente, sin alterar las demás pruebas ni los datos del estudio.

**Acceptance Scenarios**:

1. **Dado** un empleado con sesión activa y un estudio que admite modificaciones, **cuando** abre el estudio, **entonces** ve su identificador, la muestra (N° PI), el tipo y la lista de pruebas asignadas, y tiene disponible la acción de agregar una prueba.
2. **Dado** un estudio que admite modificaciones, **cuando** el empleado elige agregar una prueba, **entonces** se le ofrece el catálogo de pruebas identificadas por código y nombre, sin incluir las que ya forman parte del estudio.
3. **Dada** una prueba elegida del catálogo, **cuando** el empleado solicita agregarla, **entonces** se le muestra qué prueba se va a sumar a qué estudio y se le pide confirmación explícita antes de guardar; si cancela, el estudio queda sin cambios.
4. **Dada** la confirmación, **cuando** se completa el agregado, **entonces** la prueba queda asignada al estudio una sola vez, se suma a la lista de pruebas pendientes de realizar y se informa el éxito indicando la prueba y el estudio.
5. **Dado** un estudio con una prueba agregada, **cuando** se consulta el estudio, **entonces** su muestra, tipo, estado, autor, fecha de creación y nombre y descripción históricos del tipo siguen siendo los mismos; la composición del tipo en el catálogo no cambia.

---

### User Story 2 - Quitar una prueba que no se va a realizar (Priority: P1)

Como empleado con sesión activa, quiero seleccionar una prueba de un estudio y quitarla, después de confirmar, para no realizar ensayos que el cliente no solicitó.

**Why this priority**: Es el objetivo de US 5.4. Tiene la misma prioridad que agregar porque ambas forman la personalización del conjunto precargado por el tipo, y un ensayo innecesario consume tiempo y reactivos del laboratorio.

**Independent Test**: Con un estudio en "Pendiente de análisis" que tenga al menos dos pruebas sin mediciones, quitar una con confirmación y verificar que deja de figurar en el estudio y que no se ofrecerá para carga de mediciones ni informe.

**Acceptance Scenarios**:

1. **Dado** un estudio que admite modificaciones, **cuando** el empleado lo abre, **entonces** cada prueba que puede quitarse ofrece la acción de quitarla.
2. **Dada** una prueba seleccionada para quitar, **cuando** el empleado inicia la acción, **entonces** el sistema muestra la prueba y el estudio afectados y pide confirmación explícita antes de efectuar la eliminación; si cancela, el estudio queda sin cambios.
3. **Dada** la confirmación, **cuando** se completa la acción, **entonces** la prueba deja de formar parte del estudio, se informa el éxito y el resto de las pruebas y datos del estudio no cambian.
4. **Dada** una prueba quitada, **cuando** más adelante se carguen mediciones o se genere el informe final del estudio (historias posteriores), **entonces** esa prueba no se incluye.
5. **Dada** una prueba quitada de un estudio, **cuando** el empleado vuelve a abrir el catálogo para ese estudio, **entonces** la prueba vuelve a estar disponible para agregarse.

---

### User Story 3 - Impedir modificaciones no permitidas (Priority: P2)

Como empleado, quiero que el sistema rechace agregados duplicados y quitas no permitidas, para que el conjunto de pruebas de cada estudio siga siendo confiable.

**Why this priority**: Protege la integridad de los datos del laboratorio, pero solo tiene sentido una vez que existen las acciones de agregar y quitar.

**Independent Test**: Intentar agregar una prueba ya asignada, quitar una prueba con mediciones o resultados, modificar un estudio que no admite cambios y repetir una misma confirmación; verificar los mensajes y que el estudio no cambia indebidamente.

**Acceptance Scenarios**:

1. **Dada** una prueba que ya forma parte del estudio, **cuando** se intenta agregarla (por ejemplo, porque otro empleado la agregó mientras se revisaba la confirmación), **entonces** el sistema informa que la prueba ya está en el estudio y no la duplica.
2. **Dada** una prueba del estudio con mediciones cargadas o resultados guardados, **cuando** se intenta quitarla, **entonces** el sistema no ofrece la acción o la rechaza informando el motivo, y la prueba y sus datos se conservan.
3. **Dado** un estudio que no admite modificaciones, **cuando** se intenta agregar o quitar una prueba, **entonces** el sistema rechaza la operación informando el motivo y el estudio queda sin cambios.
4. **Dada** una misma confirmación de agregado o de quita, **cuando** se reenvía, incluso simultáneamente, **entonces** el resultado es el mismo que con un único envío: la prueba se agrega una sola vez o se quita una sola vez, sin operaciones adicionales; el reenvío se informa como una operación ya aplicada.
5. **Dado** un estudio con una sola prueba asignada, **cuando** se intenta quitarla, **entonces** el sistema no ofrece la acción o la rechaza informando que el estudio debe conservar al menos una prueba; para reemplazarla, primero se agrega la nueva y después se quita la anterior.
6. **Dado** un usuario sin sesión activa, **cuando** intenta abrir el estudio, agregar o quitar una prueba, **entonces** debe iniciar sesión y no se modifica ningún estudio.
7. **Dados** una prueba o un estudio inexistentes, **cuando** se intenta operar sobre ellos, **entonces** no se modifica ningún registro: un estudio inexistente muestra la página de «no encontrado» y una prueba inexistente se rechaza indicando que no está disponible.

### Edge Cases

- El estudio deja de admitir modificaciones entre que se abre la confirmación y se confirma: se rechaza la operación sin cambios.
- Otro empleado agrega la misma prueba al mismo estudio al mismo tiempo: queda asignada una sola vez y el segundo recibe el aviso de que ya forma parte del estudio.
- Otro empleado quita la misma prueba al mismo tiempo: la prueba se quita una sola vez y el segundo recibe el aviso de que ya no forma parte del estudio.
- Se cargan mediciones de una prueba mientras se confirma su quita (cuando existan las historias de mediciones): la quita se rechaza y las mediciones se conservan; nunca se pierden mediciones o resultados por esta acción.
- Todas las pruebas del catálogo ya forman parte del estudio: se informa que no hay pruebas disponibles para agregar en lugar de ofrecer un catálogo vacío.
- El catálogo de pruebas está vacío: no puede ocurrir con un estudio existente, porque conserva al menos una prueba del catálogo (FR-014); el caso queda cubierto por el anterior y no se inventan pruebas.
- Una prueba que el tipo no trae por defecto se agrega a un estudio: no modifica la composición del tipo ni los estudios futuros de ese tipo.
- Una prueba precargada por el tipo se quita de un estudio: no la quita del tipo ni de otros estudios del mismo tipo o de la misma muestra.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema MUST permitir agregar y quitar pruebas de un estudio únicamente a empleados con sesión activa.
- **FR-002**: El sistema MUST ofrecer una vista del estudio que muestre su identificador, la muestra (N° PI), el tipo, el estado y la lista de pruebas asignadas, y que sirva de punto de entrada para agregar y quitar pruebas. Esta vista mínima forma parte de esta historia; se accede a ella desde el mensaje de éxito de la creación del estudio (US 5.1). La búsqueda de estudios y la consulta general del avance siguen siendo de US 5.2, que deberá ampliar esta vista en lugar de crear otra.
- **FR-003**: El sistema MUST permitir agregar o quitar pruebas solo en estudios que admiten modificaciones. En esta historia admite modificaciones un estudio en estado "Pendiente de análisis"; cualquier otro estado futuro lo bloquea salvo que su historia indique lo contrario.
- **FR-004**: El sistema MUST ofrecer para agregar todas las pruebas del catálogo compartido que no formen parte del estudio, identificadas por código y nombre, sin crear un catálogo paralelo ni pruebas nuevas.
- **FR-005**: El sistema MUST impedir que una misma prueba figure más de una vez en un estudio, incluso ante agregados simultáneos.
- **FR-006**: El sistema MUST incorporar la prueba agregada al estudio como pendiente de realizar, igual que las pruebas precargadas por el tipo.
- **FR-007**: El sistema MUST permitir quitar una prueba del estudio solo si no tiene mediciones cargadas ni resultados guardados. Hasta que existan las historias de mediciones y resultados ninguna prueba los tiene, pero la regla MUST quedar establecida para que esas historias la respeten.
- **FR-008**: El sistema MUST pedir confirmación explícita, mostrando la prueba y el estudio afectados, antes de agregar o quitar una prueba, y permitir cancelar sin cambios.
- **FR-009**: El sistema MUST validar nuevamente al confirmar que el estudio admite modificaciones y que la operación sigue siendo válida (prueba aún no asignada al agregar; prueba aún asignada y sin mediciones ni resultados al quitar), y rechazarla informando el motivo en caso contrario.
- **FR-010**: Una prueba quitada MUST dejar de formar parte del conjunto de pruebas del estudio, de modo que no se incluya en la carga de mediciones ni en el informe final. La asignación se elimina: al no tener mediciones ni resultados, no tiene historial que conservar (constitution, principio IV).
- **FR-011**: Agregar o quitar pruebas MUST NOT modificar la muestra, el tipo, el estado, el autor, la fecha de creación ni el nombre y la descripción históricos del tipo guardados en el estudio, ni la composición del tipo en el catálogo, ni otros estudios.
- **FR-012**: El sistema MUST informar el resultado de cada operación (éxito o motivo del rechazo). Los mensajes de éxito identifican la prueba (código y nombre) y el estudio; los de rechazo indican el motivo y se muestran en el detalle del estudio afectado, junto a su lista de pruebas.
- **FR-013**: Reenviar una misma confirmación, incluso simultáneamente, MUST producir el mismo resultado que un único envío.
- **FR-014**: El sistema MUST impedir quitar la última prueba de un estudio: todo estudio conserva al menos una prueba asignada, igual que al crearse en US 5.1.

### Key Entities *(include if feature involves data)*

- **Estudio**: Creado en US 5.1 sobre una muestra con un tipo. Se le agregan o quitan pruebas mientras admite modificaciones; sus datos de cabecera no cambian por estas acciones.
- **Prueba**: Ensayo del catálogo compartido, identificado por código y nombre. Su definición no se crea ni modifica en esta historia.
- **Prueba asignada al estudio**: Pertenencia de una prueba al conjunto de un estudio, ya sea precargada por el tipo o agregada después. Es la unidad que se agrega o quita y, en historias posteriores, la que recibe mediciones y resultados.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: En el 100% de los agregados confirmados, la prueba queda en el estudio exactamente una vez, como pendiente, y ninguna otra prueba ni dato del estudio cambia.
- **SC-002**: En el 100% de los intentos de agregar una prueba ya asignada, secuenciales o simultáneos, el estudio conserva una sola asignación de esa prueba.
- **SC-003**: En el 100% de las quitas confirmadas, la prueba deja de figurar entre las pruebas del estudio que se ofrecerán para mediciones e informe.
- **SC-004**: Ninguna prueba con mediciones o resultados se quita, y ningún estudio que no admite modificaciones cambia su conjunto de pruebas, en todos los casos de validación.
- **SC-005**: El 100% de las cancelaciones y operaciones rechazadas termina sin cambios en el estudio, con un mensaje que indica el motivo.
- **SC-006**: Un empleado puede agregar o quitar una prueba desde el estudio en menos de 1 minuto, con una sola confirmación.

## Assumptions

- **Trazabilidad**: US 5.3 – Agregar prueba al estudio y US 5.4 – Eliminar prueba del estudio. Responsable del cronograma: Manuel. Se agrupan en una sola spec porque son chicas, comparten pantalla y reglas, y las implementa la misma persona (constitution, principio I). Claves de Jira: pendientes de completar cuando el usuario las facilite.
- **Dependencia US 5.1 integrada**: PR #12 mergeado en `main` (07b89bc). Estudio, Prueba, Tipo de estudio y Prueba asignada al estudio ya existen; esta historia los consume y no duplica el catálogo.
- **Estado modificable**: Hoy el único estado de un estudio es "Pendiente de análisis", y es el que admite cambios. Las historias que introduzcan "En proceso", "Finalizado" e "Informe generado" deberán respetar el bloqueo de FR-003.
- **Mediciones y resultados**: Todavía no existen (US 6.1 y siguientes). La regla de FR-007 queda establecida ahora; esas historias deberán hacerla cumplir cuando una prueba asignada tenga mediciones o resultados.
- **Prueba re-agregada**: Una prueba quitada puede volver a agregarse al mismo estudio; se trata como un agregado nuevo.
- **Mismo resultado al reenviar (FR-013)**: Como la asignación no admite duplicados y la quita borra la asignación, reenviar una confirmación ya aplicada se informa como "la prueba ya está en el estudio" o "la prueba ya no forma parte del estudio", sin efectos adicionales.
- **Catálogo**: Se ofrecen todas las pruebas del catálogo compartido. Si en el futuro (US 5.5) las pruebas pueden desactivarse, las desactivadas no deberán ofrecerse para agregar.
- **Datos académicos**: AquaLab es un proyecto FIUBA; las pruebas de desarrollo y demostración son ficticias (DEMO) y no tienen validez científica.
- **Alcance excluido**: Administración del catálogo y definición de pruebas (US 5.5 y precarga científica); búsqueda de estudios, consulta general del avance y listado desde la ficha de muestra (US 5.2); mediciones, resultados, informes y cambios de estado del estudio o de sus pruebas.
