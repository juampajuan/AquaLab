# Feature Specification: Validar resultados

**Feature Branch**: `019-validar-resultados`

**Created**: 2026-11-01

**Status**: Draft

**Input**: User description: "US 6.4 (Jira: clave a confirmar) – Validar resultados. Como bioquímico quiero validar los resultados calculados y guardarlos para asegurar que cumplen los parámetros técnicos y normativos antes del cierre. Criterios: (1) Solo los usuarios con el permiso «Puede validar resultados» validan; una migración crea el grupo «Bioquímicos» con ese permiso y el admin asigna a las personas (mismo patrón que gestionar_catalogo de la US 5.5). (2) Desde el detalle del estudio se eligen una o varias pruebas Cargadas con resultado y se validan en un envío, con resumen y confirmación. (3) Cada resultado se compara con los límites del catálogo: los del tipo de vertido de la muestra (Cloacal/Canal) si existen; si no, los generales. Límites numéricos: cumple si está entre mínimo y máximo (los que haya). (4) Límite «Ausente»/«Ausencia»: cumple solo si el resultado es 0 (en pruebas A/P, Ausente). (5) Límites no comparables (ej. SOE, NE, Ph-0,2/Ph+0,2): se muestran el valor y el límite con «Sin límite comparable» y se validan sin marcar cumple. (6) El detalle indica fuera de norma apenas existe el resultado, antes de validar. (7) Al validar, la prueba pasa a Completada y se guardan quién validó, cuándo, los límites usados y si cumple. (8) Cuando todas las pruebas del estudio están Completadas, el estudio pasa a Finalizado. Ya resuelto en US 6.2/6.3: corregir una medición quita la validación y devuelve el estudio a En proceso. Fuera de alcance: observaciones en mediciones, comparar pH de saturación contra el pH, informes."

## Clarifications

### Session 2026-11-01

- Q: ¿Quién puede validar? → A: Solo quien tenga el permiso «Puede validar resultados». Se crea un grupo «Bioquímicos» con ese permiso y el administrador agrega a las personas al grupo (mismo patrón que el permiso de gestión del catálogo de la US 5.5). No es un rol nuevo del sistema.
- Q: ¿Se valida prueba por prueba o todo junto? → A: Se eligen una o varias pruebas y se validan en un solo envío, con resumen y confirmación, como la carga de mediciones (US 6.1).
- Q: ¿Qué límite se usa? → A: El del tipo de vertido de la muestra (Cloacal o Canal) si la prueba lo tiene; si no, el general. Agua usa siempre el general.
- Q: ¿Contra qué límites se compara? → A: Contra los límites del catálogo importado del laboratorio (SCRUM-64).
- Q: ¿Cómo se evalúan las pruebas A/P? → A: Cumplen si el resultado es Ausente (se guarda como 0).
- Q: ¿Cómo se evalúan los límites «Ausente»/«Ausencia» en pruebas numéricas (ej. Sólidos sedimentables, Coliformes fecales)? → A: Cumplen solo si el resultado es exactamente 0; no hay tolerancia por límite de detección.
- Q: ¿Qué pasa con los límites que no son números ni «Ausente» (SOE, NE, Ph-0,2 / Ph+0,2)? → A: Se muestran el resultado y el límite tal como está en el catálogo, con la leyenda «Sin límite comparable», y la prueba se valida sin marcar si cumple.
- Q: ¿Cuándo se ve si un resultado está fuera de norma? → A: Apenas existe el resultado, antes de validarlo, para que el bioquímico lo vea al revisar.
- Q: ¿Se guarda la evaluación al validar? → A: Sí: quién validó, cuándo, los límites usados y si cumple, para que un cambio posterior del catálogo no altere lo validado ni el futuro informe.
- Q: ¿Puede validar quien cargó o corrigió la medición? → A: Sí: alcanza con el permiso del grupo «Bioquímicos», sin doble control; quedan registrados quién cargó, quién corrigió y quién validó.
- Q: ¿Qué pasa con el registro de una validación que se pierde al corregir o borrar la medición? → A: (tras /speckit-analyze) Se conserva marcado como anulado, con la fecha de anulación; no se borra (principio IV). Solo se muestra la validación vigente.
- Q: ¿Las pruebas aparecen marcadas para validar al abrir la pantalla? → A: Solo las que cumplen; las fuera de norma y las sin límite comparable aparecen sin marcar, para elegirlas a conciencia. Hay una acción «Marcar todas».

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Validar los resultados de un estudio (Priority: P1)

Como bioquímico, desde el detalle de un estudio abro la validación, veo las pruebas que tienen resultado y todavía no están validadas, con su resultado, los límites que corresponden a la muestra y si cumplen, elijo las que quiero validar, reviso el resumen y confirmo. Esas pruebas quedan Completadas y, si ya no queda ninguna sin validar, el estudio pasa a Finalizado.

**Why this priority**: Es el objetivo de US 6.4: sin validación ninguna prueba llega a Completada, ningún estudio se finaliza y no se puede emitir el informe (Epic 7).

**Independent Test**: Con un estudio de agua que tiene pH cargado en 7,4 y Cloruro en 120 mg/l, validar ambas pruebas y verificar que quedan Completadas con «Cumple», con quién validó y cuándo, y que el estudio pasa a Finalizado.

**Acceptance Scenarios**:

1. **Dado** un estudio sin informe emitido con al menos una prueba Cargada con resultado, **cuando** un usuario con el permiso de validar abre su detalle, **entonces** encuentra la acción para validar resultados.
2. **Dado** el formulario de validación, **cuando** se abre, **entonces** lista cada prueba Cargada con resultado (código, nombre, resultado con unidad, límites aplicados con su norma y si cumple) para elegir cuáles validar; vienen marcadas solo las que cumplen, y las fuera de norma o sin límite comparable quedan sin marcar.
3. **Dado** el formulario, **cuando** el bioquímico elige una o varias pruebas y continúa, **entonces** el sistema muestra un resumen de las pruebas a validar, destacando las que no cumplen, y pide confirmación; si vuelve o cancela, no cambia nada.
4. **Dada** la confirmación, **cuando** se completa, **entonces** cada prueba elegida pasa a Completada y guarda quién la validó, cuándo, los límites usados y si cumple, y se informa el éxito.
5. **Dado** un estudio al que, con esta validación, ya no le queda ninguna prueba sin validar, **cuando** se confirma, **entonces** el estudio pasa a Finalizado.
6. **Dado** un estudio al que todavía le quedan pruebas Pendientes o Cargadas sin validar, **cuando** se confirma la validación de otras, **entonces** el estudio sigue En proceso.
7. **Dado** un resultado que no cumple, **cuando** se valida, **entonces** se valida igual (la validación confirma el resultado, no lo aprueba) y queda registrado que no cumple.

---

### User Story 2 - Ver si cada resultado cumple (Priority: P2)

Como empleado del laboratorio, en el detalle del estudio veo junto a cada resultado si cumple, si está fuera de norma o si no tiene un límite comparable, aunque todavía no se haya validado.

**Why this priority**: Permite detectar desvíos apenas se carga una medición, antes de llegar a la validación; también sirve de base para el informe y el dashboard.

**Independent Test**: Con una muestra de agua y Cloruro cargado en 400 mg/l (máximo del catálogo: 350), verificar que el detalle muestra el resultado como fuera de norma sin haberlo validado.

**Acceptance Scenarios**:

1. **Dado** un resultado dentro de los límites aplicables, **cuando** se ve el detalle del estudio, **entonces** se indica que cumple.
2. **Dado** un resultado por debajo del mínimo o por encima del máximo aplicable, **cuando** se ve el detalle, **entonces** se indica fuera de norma de forma visualmente destacada.
3. **Dada** una muestra con tipo de vertido Cloacal o Canal y una prueba con límite propio para ese vertido (ej. pH en Cloacal: 7,01 a 10), **cuando** se evalúa su resultado, **entonces** se usan esos límites y no los generales (pH: 6,4 a 8,5).
4. **Dada** una muestra de Agua, **cuando** se evalúa un resultado, **entonces** se usan siempre los límites generales.
5. **Dada** una prueba A/P (ej. E. coli) con límite «Ausente», **cuando** su resultado es Ausente, **entonces** cumple; **cuando** es Presente, **entonces** está fuera de norma.
6. **Dada** una prueba numérica con límite «Ausente» o «Ausencia» (ej. Sólidos sedimentables, Coliformes fecales), **cuando** su resultado es 0, **entonces** cumple; **cuando** es cualquier otro valor, **entonces** está fuera de norma.
7. **Dada** una prueba con un límite no comparable (ej. Olor «SOE», Cloro libre en Cloacal «NE») o sin ningún límite, **cuando** se ve el detalle, **entonces** se muestran el resultado y el límite tal como figura en el catálogo con la leyenda «Sin límite comparable».
8. **Dada** una prueba ya validada, **cuando** se ve el detalle, **entonces** se muestra la evaluación guardada al validar (límites usados y si cumple), quién validó y cuándo, aunque el catálogo haya cambiado después.

---

### User Story 3 - Habilitar a los bioquímicos (Priority: P3)

Como administrador, agrego a una persona al grupo «Bioquímicos» desde el panel de administración para que pueda validar resultados; quien no está en el grupo no ve la acción ni puede validar.

**Why this priority**: Es la condición de seguridad de la historia; su configuración es mínima porque reutiliza los permisos y grupos existentes del sistema.

**Independent Test**: Con dos empleados, uno en el grupo «Bioquímicos» y otro no, verificar que solo el primero ve la acción de validar y que el segundo es rechazado si intenta validar directamente.

**Acceptance Scenarios**:

1. **Dado** el sistema recién instalado, **cuando** se preparan los datos iniciales, **entonces** existe el grupo «Bioquímicos» con el permiso «Puede validar resultados».
2. **Dado** un empleado que no tiene el permiso, **cuando** abre el detalle de un estudio, **entonces** no ve la acción de validar; **cuando** intenta validar por otra vía, **entonces** el sistema lo rechaza sin cambios.
3. **Dado** un administrador, **cuando** agrega a un empleado al grupo «Bioquímicos», **entonces** ese empleado puede validar desde su próximo acceso.

---

### Edge Cases

- Un estudio con informe emitido: no ofrece la validación y rechaza el intento informando el motivo; ningún resultado cambia.
- Una prueba Cargada sin resultado (ej. una calculada que todavía no se puede calcular): no aparece para validar; el detalle sigue mostrando el motivo sin resultado (US 6.2).
- Confirmación de una prueba que ya fue validada (doble envío o validación de otro bioquímico): se omite e informa «ya estaba validada»; no cambia quién ni cuándo.
- El resultado cambió entre la revisión y la confirmación (otro empleado corrigió una medición, US 6.3): esa prueba no se valida y se informa que cambió; el resto del envío se valida.
- Confirmación sin ninguna prueba elegida: se rechaza pidiendo elegir al menos una.
- Una prueba validada cuya medición se corrige después (US 6.3) o se borra (US 6.5): pierde la validación (ya resuelto en esas historias): su registro queda anulado, se conserva y deja de mostrarse; al volver a validarla se evalúa con los límites vigentes en ese momento.
- Límite de vertido con solo un extremo (ej. Coliformes fecales en Canal: máximo 2000): reemplaza a los límites generales completos; se compara solo contra el extremo que tiene.
- Límites con decimales escritos con punto en el catálogo (ej. «8.5»): se interpretan como número.
- El resultado se compara con su valor completo, no con el redondeo que se muestra en pantalla.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema MUST permitir validar resultados únicamente a usuarios con sesión activa y el permiso «Puede validar resultados», incluso si son quienes cargaron o corrigieron la medición (sin doble control); MUST rechazar cualquier intento sin ese permiso sin cambiar nada.
- **FR-002**: El sistema MUST crear, como parte de sus datos iniciales, el grupo «Bioquímicos» con el permiso «Puede validar resultados». Agregar o quitar personas del grupo MUST hacerse desde el panel de administración existente.
- **FR-003**: El detalle del estudio MUST ofrecer la acción de validar solo a usuarios con el permiso, cuando el estudio no tiene informe emitido y tiene al menos una prueba Cargada con resultado.
- **FR-004**: El formulario de validación MUST listar las pruebas del estudio en estado Cargada que tienen resultado, con código, nombre, resultado con su unidad, límites aplicados con su norma y su evaluación, y permitir elegir una o varias. Al abrirse, MUST aparecer marcadas solo las que cumplen; las fuera de norma y las sin límite comparable MUST aparecer sin marcar. MUST ofrecer una acción para marcar todas y exigir al menos una elegida.
- **FR-005**: El sistema MUST mostrar un resumen de las pruebas elegidas, destacando las que no cumplen, y pedir confirmación antes de validar, permitiendo volver a elegir o cancelar sin cambios.
- **FR-006**: Los límites aplicables a un resultado MUST ser los del tipo de vertido de la muestra cuando la prueba tiene límites para ese vertido (Cloacal o Canal), y en caso contrario los límites generales de la prueba. Los límites del vertido MUST reemplazar a los generales completos.
- **FR-007**: La evaluación de un resultado MUST ser una de tres: «Cumple», «Fuera de norma» o «Sin límite comparable», con estas reglas:
  - Límites numéricos: cumple si el resultado es mayor o igual al mínimo (si hay) y menor o igual al máximo (si hay); si no, fuera de norma.
  - Límite «Ausente» o «Ausencia»: cumple solo si el resultado es exactamente 0 (en pruebas A/P, Ausente); si no, fuera de norma.
  - Sin ningún límite, o con límites que no son números ni «Ausente»/«Ausencia» (ej. «SOE», «NE», «Ph-0,2», «Ph+0,2»): sin límite comparable.
- **FR-008**: El detalle del estudio MUST mostrar la evaluación de cada resultado apenas existe, antes de validarlo, destacando visualmente los fuera de norma, junto con el límite aplicado tal como figura en el catálogo.
- **FR-009**: Al confirmar, cada prueba elegida MUST pasar a Completada y guardar quién la validó, la fecha y hora, los límites usados (mínimo, máximo, norma y si son generales o de qué vertido) y la evaluación. Validar MUST NOT cambiar el resultado ni la medición.
- **FR-010**: Un resultado fuera de norma MUST poder validarse igual; la validación confirma el resultado, no lo aprueba.
- **FR-011**: Cuando, tras una validación, todas las pruebas del estudio están Completadas, el estudio MUST pasar a Finalizado. Si queda alguna Pendiente o Cargada, MUST seguir En proceso.
- **FR-012**: Una prueba validada MUST mostrar la evaluación guardada al validar, no una recalculada con el catálogo vigente.
- **FR-013**: Con informe emitido, el sistema MUST NOT permitir validar: no ofrece la acción y rechaza el intento informando el motivo.
- **FR-014**: Al confirmar, el sistema MUST omitir e informar las pruebas que ya estaban validadas, las que ya no tienen resultado y aquellas cuyo resultado cambió desde la revisión; el resto del envío MUST validarse. Reenviar una confirmación ya aplicada MUST NOT cambiar nada.
- **FR-015**: El sistema MUST informar el resultado de la validación: qué pruebas se validaron, cuáles se omitieron y por qué, y si el estudio pasó a Finalizado.
- **FR-016**: Validar MUST NOT modificar otras pruebas, la muestra, los datos históricos del estudio, el catálogo ni otros estudios.
- **FR-017**: Cuando una prueba validada deja de estar Completada (US 6.2/6.3/6.5), su validación MUST quedar anulada con la fecha de anulación y MUST NOT borrarse. Solo la validación vigente (no anulada) MUST mostrarse y contar como validación de la prueba.

### Key Entities *(include if feature involves data)*

- **Validación de un resultado**: Registro de que un bioquímico confirmó el resultado de una prueba del estudio. Atributos: quién validó, fecha y hora, límites usados (mínimo, máximo, norma, origen: general o vertido) y evaluación (cumple, fuera de norma, sin límite comparable). A lo sumo una vigente por prueba del estudio; si el resultado se recalcula (US 6.2/6.3) o se descarta (US 6.5), queda anulada con su fecha de anulación y se conserva como historial.
- **Resultado** (US 6.2): Valor calculado con su unidad. No cambia al validarse.
- **Prueba asignada al estudio**: Pasa de Cargada a Completada al validarse.
- **Estudio**: Pasa a Finalizado cuando todas sus pruebas están Completadas.
- **Prueba del catálogo y límites por tipo de vertido** (SCRUM-64): Fuente de los límites generales y por vertido, guardados como texto.
- **Grupo «Bioquímicos»**: Grupo de usuarios con el permiso «Puede validar resultados».

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Un bioquímico valida todas las pruebas con resultado de un estudio desde su detalle en menos de 1 minuto, con una sola confirmación.
- **SC-002**: El 100% de los resultados del catálogo con límites numéricos o «Ausente»/«Ausencia» se evalúan correctamente frente a casos conocidos (dentro, en el borde y fuera de cada límite).
- **SC-003**: El 100% de los intentos de validar sin el permiso o con informe emitido terminan sin cambios.
- **SC-004**: Ninguna prueba validada cambia su evaluación mostrada por un cambio posterior del catálogo.
- **SC-005**: El 100% de los estudios con todas sus pruebas validadas quedan Finalizados inmediatamente después de confirmar.
- **SC-006**: Ninguna validación se aplica sobre un resultado distinto del que vio el bioquímico al revisar.

## Assumptions

- **Trazabilidad**: US 6.4 – Validar resultados. Jira: clave a confirmar (probablemente SCRUM-56, siguiendo a SCRUM-53 a 55 de las US 6.1 a 6.3). Responsable: Delfina.
- **Dependencias**: Se apoya en la carga de mediciones (US 6.1), el cálculo de resultados (US 6.2), la corrección y el borrado de mediciones (US 6.3 y 6.5), el ajuste Ausente/Presente de las pruebas A/P (PR #32, que debe mergearse antes) y el catálogo importado con sus límites (SCRUM-64).
- **Pérdida de la validación**: Ya la definen las US 6.2, 6.3 y 6.5: un resultado recalculado o descartado vuelve a Cargada o Pendiente y el estudio deja de estar Finalizado. Esta historia solo agrega que, en ese caso, el registro de la validación queda anulado (no se borra). No se registra quién la anuló: lo dice la corrección o el borrado de la medición (US 6.3/6.5).
- **Sin revertir a mano**: Esta historia no ofrece «desvalidar» una prueba; la única forma de quitar una validación es corregir o borrar su medición.
- **Bordes inclusivos**: Un resultado igual al mínimo o al máximo cumple.
- **Pruebas sin tipo confirmado**: Las 17 pruebas importadas como Directo «a confirmar con el laboratorio» se evalúan igual que el resto con sus límites; varias tienen límites no comparables (ej. Olor «SOE», pH de saturación «Ph±0,2»).
- **Pruebas calculadas**: Se validan igual que las medidas; todas las pruebas del estudio deben estar Completadas para finalizarlo.
- **Una pantalla para todas**: Se valida desde una sola pantalla con todas las pruebas validables del estudio, igual que la carga y la corrección.
- **Interfaz**: Las pantallas siguen el diseño de SCRUM-67 con los componentes de `templates/ui/`.
- **Datos académicos**: AquaLab es un proyecto FIUBA; los datos de desarrollo y demostración son ficticios (DEMO).
- **Alcance excluido**: Observaciones o comentarios en mediciones; comparar el pH de saturación contra el pH de la misma muestra; marcar a mano si cumple una prueba sin límite comparable; «desvalidar» a mano; curvas de calibración; generar o emitir informes (Epic 7); dashboard (US 8.x).
