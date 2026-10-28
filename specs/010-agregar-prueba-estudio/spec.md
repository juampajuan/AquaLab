# Feature Specification: Agregar prueba al estudio

**Feature Branch**: `010-agregar-prueba-estudio`

**Created**: 2026-10-27

**Status**: Draft

**Input**: User description: "US 5.3 – Agregar prueba al estudio. Como empleado del laboratorio quiero agregar una prueba adicional a un estudio existente para personalizar el análisis según los requerimientos específicos del cliente. Criterios de aceptación: sobre un estudio que permita modificaciones, se debe poder abrir el catálogo de pruebas; se debe poder seleccionar y añadir una prueba adicional; no se debe permitir añadir una prueba que ya forme parte del estudio; la prueba añadida debe sumarse a la lista de pruebas pendientes a realizar. Responsable del cronograma: Manuel."

## Clarifications

### Session 2026-10-27

- Q: ¿La vista mínima del estudio forma parte de esta spec o se espera a US 5.2? → A: Forma parte de esta spec (cabecera + pruebas + acción de agregar), con acceso desde el mensaje de éxito de US 5.1. US 5.4 le suma la acción de quitar y US 5.2 la amplía en lugar de crear otra.
- Q: ¿US 5.3 y US 5.4 van en una sola spec? → A: No. Por decisión del equipo, cada US tiene su propia spec y su propia rama; esta spec cubre solo US 5.3. La quita de pruebas es [US 5.4](../011-quitar-prueba-estudio/spec.md).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Agregar una prueba adicional a un estudio (Priority: P1)

Como empleado con sesión activa, quiero abrir un estudio que todavía admite cambios, elegir del catálogo una prueba que no tenga y agregarla, para que el análisis cubra lo que pidió el cliente además de las pruebas del tipo.

**Why this priority**: Es el objetivo de US 5.3: el cliente pide un ensayo que el tipo de estudio no trae por defecto.

**Independent Test**: Con un estudio en "Pendiente de análisis" creado por US 5.1 y una prueba del catálogo que no forma parte de él, agregarla y verificar que aparece una sola vez en el estudio como pendiente, sin alterar las demás pruebas ni los datos del estudio.

**Acceptance Scenarios**:

1. **Dado** un empleado con sesión activa y un estudio que admite modificaciones, **cuando** abre el estudio, **entonces** ve su identificador, la muestra (N° PI), el tipo, el estado y la lista de pruebas asignadas, y tiene disponible la acción de agregar una prueba.
2. **Dado** un estudio que admite modificaciones, **cuando** el empleado elige agregar una prueba, **entonces** se le ofrece el catálogo de pruebas identificadas por código y nombre, sin incluir las que ya forman parte del estudio.
3. **Dada** una prueba elegida del catálogo, **cuando** el empleado solicita agregarla, **entonces** se le muestra qué prueba se va a sumar a qué estudio y se le pide confirmación explícita antes de guardar; si cancela, el estudio queda sin cambios.
4. **Dada** la confirmación, **cuando** se completa el agregado, **entonces** la prueba queda asignada al estudio una sola vez, se suma a la lista de pruebas pendientes de realizar y se informa el éxito indicando la prueba y el estudio.
5. **Dado** un estudio con una prueba agregada, **cuando** se consulta el estudio, **entonces** su muestra, tipo, estado, autor, fecha de creación y nombre y descripción históricos del tipo siguen siendo los mismos; la composición del tipo en el catálogo no cambia.

---

### User Story 2 - Impedir agregados no permitidos (Priority: P2)

Como empleado, quiero que el sistema rechace agregados duplicados o sobre estudios que ya no admiten cambios, para que el conjunto de pruebas de cada estudio siga siendo confiable.

**Why this priority**: Protege la integridad de los datos del laboratorio, pero solo tiene sentido una vez que existe la acción de agregar.

**Independent Test**: Intentar agregar una prueba ya asignada, agregar en un estudio que no admite cambios y repetir una misma confirmación; verificar los mensajes y que el estudio no cambia indebidamente.

**Acceptance Scenarios**:

1. **Dada** una prueba que ya forma parte del estudio, **cuando** se intenta agregarla (por ejemplo, porque otro empleado la agregó mientras se revisaba la confirmación), **entonces** el sistema informa que la prueba ya está en el estudio y no la duplica.
2. **Dado** un estudio que no admite modificaciones, **cuando** se intenta agregar una prueba, **entonces** el sistema rechaza la operación informando el motivo y el estudio queda sin cambios.
3. **Dada** una misma confirmación de agregado, **cuando** se reenvía, incluso simultáneamente, **entonces** la prueba se agrega una sola vez, sin operaciones adicionales; el reenvío se informa como una operación ya aplicada.
4. **Dado** un usuario sin sesión activa, **cuando** intenta abrir el estudio o agregar una prueba, **entonces** debe iniciar sesión y no se modifica ningún estudio.
5. **Dados** una prueba o un estudio inexistentes, **cuando** se intenta operar sobre ellos, **entonces** no se modifica ningún registro: un estudio inexistente muestra la página de «no encontrado» y una prueba inexistente se rechaza indicando que no está disponible.

### Edge Cases

- El estudio deja de admitir modificaciones entre que se abre la confirmación y se confirma: se rechaza la operación sin cambios.
- Otro empleado agrega la misma prueba al mismo estudio al mismo tiempo: queda asignada una sola vez y el segundo recibe el aviso de que ya forma parte del estudio.
- Todas las pruebas del catálogo ya forman parte del estudio: se informa que no hay pruebas disponibles para agregar en lugar de ofrecer un catálogo vacío.
- El catálogo de pruebas está vacío: no puede ocurrir con un estudio existente, porque se creó con al menos una prueba del catálogo (US 5.1); el caso queda cubierto por el anterior y no se inventan pruebas.
- Una prueba que el tipo no trae por defecto se agrega a un estudio: no modifica la composición del tipo ni los estudios futuros de ese tipo, ni otros estudios de la misma muestra.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema MUST permitir abrir el estudio y agregarle pruebas únicamente a empleados con sesión activa.
- **FR-002**: El sistema MUST ofrecer una vista del estudio que muestre su identificador, la muestra (N° PI), el tipo, el estado y la lista de pruebas asignadas, y que sirva de punto de entrada para agregar pruebas. Se accede a ella desde el mensaje de éxito de la creación del estudio (US 5.1). La búsqueda de estudios y la consulta general del avance siguen siendo de US 5.2, que deberá ampliar esta vista en lugar de crear otra.
- **FR-003**: El sistema MUST permitir agregar pruebas solo en estudios que admiten modificaciones. En esta historia admite modificaciones un estudio en estado "Pendiente de análisis"; cualquier otro estado futuro lo bloquea salvo que su historia indique lo contrario. La misma regla vale para quitar pruebas (US 5.4).
- **FR-004**: El sistema MUST ofrecer para agregar todas las pruebas del catálogo compartido que no formen parte del estudio, identificadas por código y nombre, sin crear un catálogo paralelo ni pruebas nuevas.
- **FR-005**: El sistema MUST impedir que una misma prueba figure más de una vez en un estudio, incluso ante agregados simultáneos.
- **FR-006**: El sistema MUST incorporar la prueba agregada al estudio como pendiente de realizar, igual que las pruebas precargadas por el tipo.
- **FR-007**: El sistema MUST pedir confirmación explícita, mostrando la prueba y el estudio afectados, antes de agregar una prueba, y permitir cancelar sin cambios.
- **FR-008**: El sistema MUST validar nuevamente al confirmar que el estudio admite modificaciones y que la prueba sigue sin estar asignada, y rechazar la operación informando el motivo en caso contrario.
- **FR-009**: Agregar pruebas MUST NOT modificar la muestra, el tipo, el estado, el autor, la fecha de creación ni el nombre y la descripción históricos del tipo guardados en el estudio, ni la composición del tipo en el catálogo, ni otros estudios.
- **FR-010**: El sistema MUST informar el resultado de cada operación (éxito o motivo del rechazo). Los mensajes de éxito identifican la prueba (código y nombre) y el estudio; los de rechazo indican el motivo y se muestran en el detalle del estudio afectado.
- **FR-011**: Reenviar una misma confirmación, incluso simultáneamente, MUST producir el mismo resultado que un único envío.

### Key Entities *(include if feature involves data)*

- **Estudio**: Creado en US 5.1 sobre una muestra con un tipo. Se le agregan pruebas mientras admite modificaciones; sus datos de cabecera no cambian por esta acción.
- **Prueba**: Ensayo del catálogo compartido, identificado por código y nombre. Su definición no se crea ni modifica en esta historia.
- **Prueba asignada al estudio**: Pertenencia de una prueba al conjunto de un estudio, ya sea precargada por el tipo o agregada después. Es la unidad que se agrega y, en historias posteriores, la que recibe mediciones y resultados.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: En el 100% de los agregados confirmados, la prueba queda en el estudio exactamente una vez, como pendiente, y ninguna otra prueba ni dato del estudio cambia.
- **SC-002**: En el 100% de los intentos de agregar una prueba ya asignada, secuenciales o simultáneos, el estudio conserva una sola asignación de esa prueba.
- **SC-003**: Ningún estudio que no admite modificaciones cambia su conjunto de pruebas en los casos de validación.
- **SC-004**: El 100% de las cancelaciones y operaciones rechazadas termina sin cambios en el estudio, con un mensaje que indica el motivo.
- **SC-005**: Un empleado puede agregar una prueba desde el estudio en menos de 1 minuto, con una sola confirmación.

## Assumptions

- **Trazabilidad**: US 5.3 – Agregar prueba al estudio. Responsable del cronograma: Manuel. Clave de Jira: pendiente de completar cuando el usuario la facilite.
- **Spec separada de US 5.4**: El equipo no aprobó la spec conjunta de US 5.3 y US 5.4 (rama `009-gestionar-pruebas-estudio`) y pidió una spec y una rama por US. US 5.4 está en `specs/011-quitar-prueba-estudio/` y depende de esta historia (usa el detalle del estudio y la regla de estudio modificable).
- **Dependencia US 5.1 integrada**: PR #12 mergeado en `main` (07b89bc). Estudio, Prueba, Tipo de estudio y Prueba asignada al estudio ya existen; esta historia los consume y no duplica el catálogo.
- **Estado modificable**: Hoy el único estado de un estudio es "Pendiente de análisis", y es el que admite cambios. Las historias que introduzcan "En proceso", "Finalizado" e "Informe generado" deberán respetar el bloqueo de FR-003.
- **Mismo resultado al reenviar (FR-011)**: Como la asignación no admite duplicados, reenviar una confirmación ya aplicada se informa como "la prueba ya está en el estudio", sin efectos adicionales.
- **Catálogo**: Se ofrecen todas las pruebas del catálogo compartido. Si en el futuro (US 5.5) las pruebas pueden desactivarse, las desactivadas no deberán ofrecerse para agregar.
- **Datos académicos**: AquaLab es un proyecto FIUBA; las pruebas de desarrollo y demostración son ficticias (DEMO) y no tienen validez científica.
- **Alcance excluido**: Quitar pruebas (US 5.4); administración del catálogo y definición de pruebas (US 5.5 y precarga científica); búsqueda de estudios, consulta general del avance y listado desde la ficha de muestra (US 5.2); mediciones, resultados, informes y cambios de estado del estudio o de sus pruebas.
