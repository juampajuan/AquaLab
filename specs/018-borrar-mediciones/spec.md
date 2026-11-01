# Feature Specification: Borrar mediciones

**Feature Branch**: `018-borrar-mediciones`

**Created**: 2026-11-01

**Status**: Aprobada (2026-11-01)

**Input**: User description: "US 6.5 (Jira SCRUM-72) – Borrar mediciones. Como empleado del laboratorio quiero borrar una medición cargada por error (por ejemplo, en la prueba equivocada) para que la prueba vuelva a quedar pendiente y se cargue de nuevo cuando corresponda. Criterios de aceptación: (1) Desde la corrección de mediciones (6.3) se puede marcar una medición para borrar; el resumen la muestra como «valor anterior → se borra» y se pide confirmación antes de borrar. (2) Al confirmar, se borran la medición y su resultado, y la prueba vuelve a Pendiente para cargarse otra vez (6.1). (3) Las pruebas calculadas que dependen de la medición borrada pierden su resultado y vuelven a Pendiente; si estaban validadas, pierden la validación. (4) Si al estudio no le queda ninguna prueba cargada o completada, vuelve a «Pendiente de análisis» y vuelve a admitir agregar y quitar pruebas. (5) Con el informe emitido no se pueden borrar mediciones. Decisiones ya tomadas por el usuario al especificar la 6.3: casilla «Borrar» en cada fila del formulario de corrección (vaciar el campo sigue siendo un error); si una fila tiene la casilla marcada y además un valor editado, prevalece el borrado."

## Clarifications

### Session 2026-11-01

- Q: ¿Cómo se muestra el valor nuevo de una medición marcada para borrar en el resumen? → A: Con «—», como una prueba sin medición en el detalle, en lugar del texto «se borra» (que queda solo para lectores de pantalla). Pedido del usuario después del recorrido manual.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Borrar una medición cargada por error (Priority: P1)

Como empleado con sesión activa, en la corrección de mediciones (US 6.3) marco «Borrar» en una medición que no debía cargarse, reviso el resumen («valor anterior → se borra») y confirmo. La medición y su resultado desaparecen y la prueba vuelve a Pendiente, lista para cargarse de nuevo.

**Why this priority**: Es el objetivo de US 6.5: una medición cargada en la prueba equivocada hoy solo se puede cambiar de valor, no quitar.

**Independent Test**: Con CL- y PH cargados, marcar «Borrar» en CL- y confirmar: CL- queda Pendiente, sin medición ni resultado, y vuelve a ofrecerse en «Cargar mediciones»; PH no cambia.

**Acceptance Scenarios**:

1. **Dado** el formulario de corrección, **cuando** se abre, **entonces** cada fila ofrece una casilla «Borrar».
2. **Dada** una medición marcada para borrar, **cuando** el empleado revisa, **entonces** el resumen la muestra con su valor anterior y «—» como valor nuevo (igual que una prueba sin medición), junto con las correcciones del mismo envío, y pide confirmación; si cancela o vuelve, no cambia nada.
3. **Dada** la confirmación, **cuando** se completa, **entonces** la medición y su resultado se borran, la prueba vuelve a Pendiente y se informa el borrado.
4. **Dada** una prueba cuya medición se borró, **cuando** el empleado abre «Cargar mediciones» (US 6.1), **entonces** la prueba se ofrece otra vez.
5. **Dada** una fila con «Borrar» marcado y además un valor editado (o vaciado), **cuando** se envía, **entonces** prevalece el borrado y el valor escrito se ignora, sin errores en ese campo.
6. **Dado** un envío que solo marca borrados, **cuando** se revisa, **entonces** cuenta como cambio (no se informa «No hay cambios para guardar»).

---

### User Story 2 - Que el borrado arrastre a lo que depende de la medición (Priority: P2)

Como empleado, quiero que al borrar una medición las pruebas calculadas que dependían de ella pierdan su resultado y el estudio vuelva al estado que corresponde, para que nada quede calculado con un dato que ya no existe.

**Why this priority**: Completa la integridad del borrado; sin esto quedarían resultados huérfanos.

**Independent Test**: Con CA, DUREZA-T y MG calculados, borrar CA: MG pierde su resultado, vuelve a Pendiente y avisa que falta CA; DUREZA-T no cambia. Borrar luego todas las mediciones: el estudio vuelve a «Pendiente de análisis» y ofrece «Agregar prueba».

**Acceptance Scenarios**:

1. **Dadas** pruebas calculadas que dependen (directa o indirectamente) de la medición borrada, **cuando** se completa, **entonces** pierden su resultado, vuelven a Pendiente y el detalle indica qué les falta (US 6.2).
2. **Dadas** pruebas validadas (Completada) entre la borrada y sus dependientes, **cuando** se revisa, **entonces** el resumen avisa que perderán la validación; al confirmar, quedan Pendiente.
3. **Dado** un estudio en el que se borran todas las mediciones, **cuando** se completa, **entonces** el estudio vuelve a «Pendiente de análisis» y vuelve a admitir agregar y quitar pruebas (US 5.3/5.4).
4. **Dado** un estudio Finalizado al que se le borra una medición y le quedan otras, **cuando** se completa, **entonces** vuelve a En proceso.

---

### User Story 3 - Proteger lo emitido y los borrados simultáneos (Priority: P3)

Como empleado, quiero que no se pueda borrar nada de un estudio con informe emitido y que un borrado no pise lo que otro empleado cambió mientras tanto.

**Why this priority**: Mismas protecciones que la corrección (US 6.3), aplicadas al borrado.

**Independent Test**: Con informe emitido, verificar que no se ofrece borrar y que se rechaza; abrir la corrección en dos pestañas, corregir en una y borrar en la otra, y verificar que el borrado se omite.

**Acceptance Scenarios**:

1. **Dado** un estudio con informe emitido, **cuando** se intenta borrar una medición, **entonces** se rechaza informando el motivo y nada cambia.
2. **Dada** una medición que otro empleado corrigió después de abrir el formulario, **cuando** se confirma su borrado, **entonces** el borrado se omite con «cambió mientras se editaba»; el resto del envío se aplica.
3. **Dada** una medición que ya se borró (reenvío o borrado simultáneo), **cuando** se confirma su borrado, **entonces** se informa que ya no tenía medición y nada más cambia.

### Edge Cases

- Borrar la medición de una prueba de la que nada depende: solo esa prueba vuelve a Pendiente.
- Borrar y corregir en el mismo envío mediciones de las que depende la misma calculada: se aplican las dos y la calculada queda sin resultado si le falta la borrada.
- Después de volver a «Pendiente de análisis», una prueba Pendiente se puede quitar del estudio (US 5.4); antes, no.
- Una medición borrada no deja rastro (no hay historial de mediciones, US 6.3); la prueba queda igual que antes de cargarla.
- Si el informe se emite mientras se edita, la confirmación se rechaza sin cambios.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema MUST permitir borrar mediciones a cualquier empleado con sesión activa, igual que corregirlas (US 6.3).
- **FR-002**: El formulario de corrección (US 6.3) MUST ofrecer en cada fila una casilla «Borrar».
- **FR-003**: Una fila con «Borrar» marcado MUST tratarse como borrado aunque traiga un valor editado o vacío, sin validar ese valor; un envío con al menos un borrado MUST contar como cambio.
- **FR-004**: El resumen de revisión MUST mostrar cada borrado con su valor anterior y «—» como valor nuevo (con el texto «se borra» para lectores de pantalla), junto con las correcciones, y las pruebas que perderán la validación; MUST pedir confirmación antes de borrar.
- **FR-005**: Al confirmar, el sistema MUST borrar la medición y su resultado, y la prueba MUST volver a Pendiente (también si estaba Completada) y ofrecerse otra vez en la carga (US 6.1).
- **FR-006**: En la misma operación, las pruebas que dependen de la medición borrada MUST recalcularse (US 6.2): las calculadas que ya no se pueden calcular pierden su resultado y vuelven a Pendiente; si estaban validadas, pierden la validación.
- **FR-007**: Si después del envío el estudio no tiene ninguna prueba Cargada ni Completada, MUST volver a «Pendiente de análisis» (y volver a admitir agregar y quitar pruebas). Si estaba Finalizado y le quedan pruebas sin validar, MUST volver a En proceso (US 6.3).
- **FR-008**: Con informe emitido, el sistema MUST NOT permitir borrar mediciones y MUST informar el motivo.
- **FR-009**: Al confirmar, si la medición cambió desde que se abrió el formulario, el borrado MUST omitirse con «cambió mientras se editaba»; si ya no existe, MUST informarse «ya no tenía medición». El resto del envío se aplica. Reenviar una confirmación ya aplicada MUST NOT cambiar nada más.
- **FR-010**: El sistema MUST informar el resultado: qué mediciones se corrigieron, cuáles se borraron, cuáles se omitieron y por qué, y qué resultados no se pudieron calcular.
- **FR-011**: Todo el envío (correcciones, borrados y recálculos) MUST aplicarse en una sola operación: si algo falla, no queda nada a medias.
- **FR-012**: Borrar mediciones MUST NOT modificar otras mediciones, la muestra, los datos históricos del estudio, el catálogo ni otros estudios.

### Key Entities *(include if feature involves data)*

- **Medición** (US 6.1/6.3): se puede borrar antes del informe; no deja historial.
- **Resultado** (US 6.2): se borra con su medición; los de pruebas dependientes se recalculan o se borran.
- **Prueba asignada al estudio**: vuelve a Pendiente al borrarse su medición o, siendo calculada, al quedar sin resultado.
- **Estudio**: vuelve a «Pendiente de análisis» sin pruebas Cargadas ni Completadas, o de Finalizado a En proceso; con informe emitido no admite borrados.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Un empleado borra una medición desde el detalle del estudio en menos de 1 minuto, con una sola confirmación.
- **SC-002**: En el 100% de los borrados confirmados, la prueba queda Pendiente sin medición ni resultado y se puede volver a cargar.
- **SC-003**: Ninguna prueba conserva un resultado calculado con una medición borrada.
- **SC-004**: Ningún estudio con informe emitido pierde mediciones, y ningún borrado pisa una corrección hecha por otro empleado mientras se editaba.

## Assumptions

- **Trazabilidad**: US 6.5 – Borrar mediciones. Jira: SCRUM-72 (creada el 2026-11-01 al separar el borrado de la US 6.3). Responsable: Juan José.
- **Dependencias**: Se apoya en la corrección de mediciones (US 6.3: pantalla, servicio, concurrencia con el valor original, aviso de validación perdida) y en el cálculo (US 6.2: recálculo de dependientes y pérdida de resultados). La rama sale de `017-modificar-mediciones` (PR #30 en revisión) y se rebasa sobre `main` cuando se mergee.
- **Casilla «Borrar»**: decisión del usuario al especificar la US 6.3; vaciar un campo sigue siendo un error de la US 6.3.
- **Integridad (principio IV)**: una medición no tiene historial asociado; sin medición, la prueba vuelve al estado previo a la carga, igual que antes de cargarla. No se borran registros con historial.
- **Pendiente de análisis**: es la definición de «En proceso» de US 5.2 al revés: un estudio sin pruebas Cargadas ni Completadas no está en proceso.
- **Interfaz**: Los cambios van en las pantallas de la US 6.3 con los componentes de `templates/ui/`.
- **Alcance excluido**: borrar pruebas del estudio (US 5.4); validar resultados (US 6.4); informes (Epic 7).
