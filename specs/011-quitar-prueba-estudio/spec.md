# Feature Specification: Quitar prueba del estudio

**Feature Branch**: `011-quitar-prueba-v2` (la rama original `011-quitar-prueba-estudio` quedó desactualizada respecto de `main`; ver Clarifications 2026-10-28)

**Created**: 2026-10-27

**Status**: Draft

**Input**: User description: "US 5.4 – Eliminar prueba del estudio. Como empleado del laboratorio quiero quitar una prueba de un estudio para no realizar ensayos innecesarios si no fueron solicitados. Criterios de aceptación: se debe poder seleccionar una prueba del estudio para quitarla; solo se pueden eliminar pruebas que no tengan mediciones cargadas ni resultados guardados; el sistema debe pedir confirmación antes de efectuar la eliminación; la prueba eliminada no debe incluirse en la carga de mediciones ni en el informe final. Responsable del cronograma: Manuel."

## Clarifications

### Session 2026-10-27

- Q: ¿Una prueba quitada se borra o se conserva marcada como quitada? → A: Se borra la asignación; sin mediciones ni resultados no tiene historial.
- Q: ¿Un estudio puede quedar sin pruebas? → A: No; la última prueba no se puede quitar.
- Q: ¿US 5.3 y US 5.4 van en una sola spec? → A: No. Por decisión del equipo, cada US tiene su propia spec y su propia rama; esta spec cubre solo US 5.4 y se apoya en [US 5.3](../010-agregar-prueba-estudio/spec.md).

### Session 2026-10-28

- Q: La spec se escribió antes de US 5.2 y del rediseño de la interfaz (SCRUM-67). ¿Se actualiza o se rehace? → A: Se implementa a partir de esta spec actualizada en la rama `011-quitar-prueba-v2`, que sale de `010-agregar-prueba-v2` (US 5.3 ya implementada sobre US 5.2 y SCRUM-67). Responsable: Juan Pablo.
- Q: US 5.2 ya guarda el estado de cada prueba asignada (`Pendiente`, `Cargada`, `Completada`). ¿Cómo se sabe si una prueba tiene mediciones o resultados? → A: Por ese estado: `Cargada` es una medición registrada y `Completada` un resultado validado. Solo se puede quitar una prueba en estado `Pendiente`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Quitar una prueba que no se va a realizar (Priority: P1)

Como empleado con sesión activa, quiero seleccionar una prueba de un estudio y quitarla, después de confirmar, para no realizar ensayos que el cliente no solicitó.

**Why this priority**: Es el objetivo de US 5.4: un ensayo innecesario consume tiempo y reactivos del laboratorio.

**Independent Test**: Con un estudio en "Pendiente de análisis" que tenga al menos dos pruebas sin mediciones, quitar una con confirmación y verificar que deja de figurar en el estudio y que no se ofrecerá para carga de mediciones ni informe.

**Acceptance Scenarios**:

1. **Dado** un estudio que admite modificaciones, **cuando** el empleado abre su detalle, **entonces** cada prueba que puede quitarse ofrece la acción de quitarla.
2. **Dada** una prueba seleccionada para quitar, **cuando** el empleado inicia la acción, **entonces** el sistema muestra la prueba y el estudio afectados y pide confirmación explícita antes de efectuar la eliminación; si cancela, el estudio queda sin cambios.
3. **Dada** la confirmación, **cuando** se completa la acción, **entonces** la prueba deja de formar parte del estudio, se informa el éxito y el resto de las pruebas y datos del estudio no cambian.
4. **Dada** una prueba quitada, **cuando** más adelante se carguen mediciones o se genere el informe final del estudio (historias posteriores), **entonces** esa prueba no se incluye.
5. **Dada** una prueba quitada de un estudio, **cuando** el empleado vuelve a abrir el catálogo para agregar pruebas (US 5.3), **entonces** la prueba vuelve a estar disponible para agregarse.

---

### User Story 2 - Impedir quitas no permitidas (Priority: P2)

Como empleado, quiero que el sistema rechace quitas de pruebas con mediciones, de la última prueba o en estudios que ya no admiten cambios, para que el conjunto de pruebas de cada estudio siga siendo confiable y no se pierdan datos.

**Why this priority**: Protege la integridad de los datos del laboratorio, pero solo tiene sentido una vez que existe la acción de quitar.

**Independent Test**: Intentar quitar una prueba con mediciones o resultados, quitar la última prueba, quitar en un estudio que no admite cambios y repetir una misma confirmación; verificar los mensajes y que el estudio no cambia indebidamente.

**Acceptance Scenarios**:

1. **Dada** una prueba del estudio con mediciones cargadas o resultados guardados, **cuando** se intenta quitarla, **entonces** el sistema no ofrece la acción o la rechaza informando el motivo, y la prueba y sus datos se conservan.
2. **Dado** un estudio que no admite modificaciones, **cuando** se intenta quitar una prueba, **entonces** el sistema rechaza la operación informando el motivo y el estudio queda sin cambios.
3. **Dada** una misma confirmación de quita, **cuando** se reenvía, incluso simultáneamente, **entonces** la prueba se quita una sola vez, sin operaciones adicionales; el reenvío se informa como una operación ya aplicada.
4. **Dado** un estudio con una sola prueba asignada, **cuando** se intenta quitarla, **entonces** el sistema no ofrece la acción o la rechaza informando que el estudio debe conservar al menos una prueba; para reemplazarla, primero se agrega la nueva (US 5.3) y después se quita la anterior.
5. **Dado** un usuario sin sesión activa, **cuando** intenta quitar una prueba, **entonces** debe iniciar sesión y no se modifica ningún estudio.
6. **Dados** un estudio inexistente o una prueba que no pertenece al estudio, **cuando** se intenta quitarla, **entonces** no se modifica ningún registro: un estudio inexistente muestra la página de «no encontrado» y una prueba ajena o ya quitada se informa como que no forma parte del estudio.

### Edge Cases

- El estudio deja de admitir modificaciones entre que se abre la confirmación y se confirma: se rechaza la operación sin cambios.
- Otro empleado quita la misma prueba al mismo tiempo: la prueba se quita una sola vez y el segundo recibe el aviso de que ya no forma parte del estudio.
- Dos empleados quitan al mismo tiempo las dos únicas pruebas de un estudio: se quita una sola y la otra se rechaza porque el estudio debe conservar al menos una prueba.
- Se cargan mediciones de una prueba mientras se confirma su quita (cuando existan las historias de mediciones): la quita se rechaza y las mediciones se conservan; nunca se pierden mediciones o resultados por esta acción.
- Una prueba precargada por el tipo se quita de un estudio: no la quita del tipo ni de otros estudios del mismo tipo o de la misma muestra.
- Una prueba se quita y luego se vuelve a agregar: la nueva asignación es independiente; reenviar la confirmación de la quita anterior no la afecta.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema MUST permitir quitar pruebas de un estudio únicamente a empleados con sesión activa.
- **FR-002**: El sistema MUST ofrecer la acción de quitar en cada prueba del detalle del estudio que pueda quitarse. El detalle es la ficha del estudio de US 5.2, con la columna Acción que dejó US 5.3; esta historia no crea otra vista.
- **FR-003**: El sistema MUST permitir quitar pruebas solo en estudios que admiten modificaciones, con la misma regla que US 5.3 (estado "Pendiente de análisis").
- **FR-004**: El sistema MUST permitir quitar una prueba del estudio solo si no tiene mediciones cargadas ni resultados guardados, es decir, solo si su estado individual (US 5.2) es `Pendiente`. Una prueba `Cargada` (con medición) o `Completada` (con resultado) no se puede quitar. Las historias de mediciones y resultados (Epic 6) cambian ese estado y MUST respetar esta regla.
- **FR-005**: El sistema MUST pedir confirmación explícita, mostrando la prueba y el estudio afectados, antes de quitar una prueba, y permitir cancelar sin cambios.
- **FR-006**: El sistema MUST validar nuevamente al confirmar que el estudio admite modificaciones, que la prueba sigue asignada, que no tiene mediciones ni resultados y que no es la última, y rechazar la operación informando el motivo en caso contrario.
- **FR-007**: Una prueba quitada MUST dejar de formar parte del conjunto de pruebas del estudio, de modo que no se incluya en la carga de mediciones ni en el informe final. La asignación se elimina: al no tener mediciones ni resultados, no tiene historial que conservar (constitution, principio IV).
- **FR-008**: Quitar pruebas MUST NOT modificar la muestra, el tipo, el estado, el autor, la fecha de creación ni el nombre y la descripción históricos del tipo guardados en el estudio, ni la composición del tipo en el catálogo, ni otros estudios.
- **FR-009**: El sistema MUST informar el resultado de cada operación (éxito o motivo del rechazo). Los mensajes de éxito identifican la prueba (código y nombre) y el estudio; los de rechazo indican el motivo y se muestran en el detalle del estudio afectado.
- **FR-010**: Reenviar una misma confirmación, incluso simultáneamente, MUST producir el mismo resultado que un único envío.
- **FR-011**: El sistema MUST impedir quitar la última prueba de un estudio: todo estudio conserva al menos una prueba asignada, igual que al crearse en US 5.1.

### Key Entities *(include if feature involves data)*

- **Estudio**: Creado en US 5.1. Se le quitan pruebas mientras admite modificaciones; sus datos de cabecera no cambian por esta acción.
- **Prueba asignada al estudio**: Pertenencia de una prueba al conjunto de un estudio, precargada por el tipo o agregada en US 5.3, con su estado individual (`Pendiente`, `Cargada` o `Completada`, US 5.2). Es la unidad que se quita y, en historias posteriores, la que recibe mediciones y resultados.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: En el 100% de las quitas confirmadas, la prueba deja de figurar entre las pruebas del estudio que se ofrecerán para mediciones e informe, y ninguna otra prueba ni dato del estudio cambia.
- **SC-002**: Ninguna prueba con mediciones o resultados se quita, y ningún estudio que no admite modificaciones cambia su conjunto de pruebas, en todos los casos de validación.
- **SC-003**: En el 100% de los casos de validación, incluidas quitas simultáneas, ningún estudio queda sin pruebas.
- **SC-004**: El 100% de las cancelaciones y operaciones rechazadas termina sin cambios en el estudio, con un mensaje que indica el motivo.
- **SC-005**: Un empleado puede quitar una prueba desde el estudio en menos de 1 minuto, con una sola confirmación.

## Assumptions

- **Trazabilidad**: US 5.4 – Eliminar prueba del estudio. Jira: SCRUM-51. Responsable original del cronograma: Manuel; reimplementación: Juan Pablo (ver Clarifications 2026-10-28).
- **Dependencia US 5.2 y US 5.3**: Esta historia usa la ficha del estudio y el estado de cada prueba de US 5.2, y la regla de estudio modificable (`Estudio.admite_modificaciones`), las excepciones (`GestionPruebasError`) y la columna Acción de [US 5.3](../010-agregar-prueba-estudio/spec.md). Su rama sale de `010-agregar-prueba-v2` y su PR se mergea después del de US 5.3.
- **Spec separada de US 5.3**: El equipo no aprobó la spec conjunta de US 5.3 y US 5.4 (rama `009-gestionar-pruebas-estudio`) y pidió una spec y una rama por US.
- **Mediciones y resultados**: Las pantallas de carga todavía no existen (US 6.1 y siguientes), pero el estado individual de US 5.2 ya las representa. FR-004 se apoya en ese estado; las historias del Epic 6 deberán pasar la prueba a `Cargada` o `Completada` al registrar mediciones o resultados.
- **Interfaz**: las pantallas nuevas siguen el diseño de SCRUM-67 (constitution v1.1.0) y se arman con los componentes de `templates/ui/`.
- **Mismo resultado al reenviar (FR-010)**: Como la quita borra la asignación, reenviar una confirmación ya aplicada se informa como "la prueba ya no forma parte del estudio", sin efectos adicionales.
- **Datos académicos**: AquaLab es un proyecto FIUBA; las pruebas de desarrollo y demostración son ficticias (DEMO) y no tienen validez científica.
- **Alcance excluido**: Agregar pruebas (US 5.3); el detalle del estudio (US 5.2); administración del catálogo (US 5.5); búsqueda de estudios y consulta general del avance (US 5.2); mediciones, resultados, informes y cambios de estado del estudio o de sus pruebas.
