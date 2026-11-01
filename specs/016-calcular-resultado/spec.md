# Feature Specification: Cálculo automático del resultado

**Feature Branch**: `016-calcular-resultado`

**Created**: 2026-10-31

**Status**: Draft

**Input**: User description: "US 6.2 (Jira SCRUM-54) – Cálculo automático del resultado. Como empleado del laboratorio quiero que el sistema calcule automáticamente el resultado de la prueba para evitar errores de cálculo manual o transcripción. Criterios de aceptación: (1) El sistema debe aplicar la fórmula o curva de calibración correspondiente a la prueba. (2) El cálculo debe procesar los valores de las mediciones ingresadas. (3) El resultado calculado debe mostrarse con su unidad de medida correspondiente (ej. mg/L, UFC/ml). (4) El sistema debe advertir si faltan mediciones para completar el cálculo. (5) Al modificar una medición (US 6.3, SCRUM-55), el resultado de esa prueba y el de las pruebas calculadas que dependen de ella se recalculan automáticamente. Nota: riesgo identificado: errores en el cálculo; tests obligatorios. Acuerdo con US 6.3: el recálculo del resultado al modificar una medición se implementa en esta historia, que es la que tiene el modelo de resultados."

## Clarifications

### Session 2026-10-31

- Q: ¿Con cuántos decimales se muestra el resultado? → A: Se guarda con 10 decimales y se muestra redondeado a 4 decimales como máximo, sin ceros finales de más (23,5; 0,72; 0,0041).
- Q: ¿El mensaje al guardar mediciones avisa los resultados que no se pudieron calcular? → A: Sí, solo las fórmulas que no se pudieron evaluar; las pruebas que esperan otros resultados se ven solo en el detalle.
- Q: Si se corrige una medición y una prueba que depende de ella ya está validada (Completada), ¿qué pasa? → A: Mientras no se haya emitido el informe, la corrección se acepta: los dependientes validados se recalculan, pierden la validación y vuelven a Cargada para revalidarse (US 6.3: «revalidarse»). Con informe emitido, se rechaza. Es una excepción al principio IV que se justifica en `plan.md`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Obtener el resultado de cada prueba al cargar su medición (Priority: P1)

Como empleado, cuando guardo la medición de una prueba (US 6.1), el sistema calcula su resultado aplicando la fórmula de la prueba al valor medido, y en el detalle del estudio veo el resultado con su unidad, sin hacer cuentas a mano.

**Why this priority**: Es el objetivo de US 6.2: el cálculo manual o la transcripción son el riesgo identificado del proyecto, y sin resultado no hay validación (US 6.4) ni informe.

**Independent Test**: Cargar la medición de una prueba de tipo Fórmula (ej. Cloruro, `x*10`, con 2,35 mL) y una de tipo Directo (ej. pH 7,20) y verificar que el detalle muestra los resultados 23,5 mg/l y 7,2 UpH (la medición del pH se sigue viendo como 7,20).

**Acceptance Scenarios**:

1. **Dada** una prueba de tipo Fórmula cuya fórmula usa el valor medido (ej. `x*10`), **cuando** se guarda su medición (2,35), **entonces** su resultado es el de aplicar la fórmula a ese valor (23,5) y se guarda con la unidad del resultado de la prueba (mg/l).
2. **Dada** una prueba de tipo Directo, **cuando** se guarda su medición, **entonces** su resultado es el mismo valor medido, con la unidad del resultado de la prueba.
3. **Dado** un estudio con pruebas que tienen resultado, **cuando** el empleado abre su detalle, **entonces** cada prueba muestra su resultado con su unidad junto a la medición; las que no tienen resultado lo indican.
4. **Dadas** fórmulas con varias operaciones (paréntesis, multiplicaciones, divisiones y raíz cuadrada, ej. NTK-T `(25*0.05-x*0.05)*0.01408*100/50*10000`), **cuando** se calcula, **entonces** el resultado coincide con el valor esperado calculado a mano para casos conocidos del catálogo.

---

### User Story 2 - Calcular las pruebas que dependen de otras (Priority: P2)

Como empleado, quiero que las pruebas calculadas a partir de otras (ej. Sólidos disueltos a partir de Conductividad, Magnesio a partir de Dureza total y Calcio) obtengan su resultado en cuanto estén los resultados que necesitan, y que el sistema me avise cuáles faltan mientras tanto.

**Why this priority**: Completa el cálculo de las pruebas calculadas, que no tienen medición propia (US 6.1); depende de que exista el resultado de las pruebas medidas.

**Independent Test**: En un estudio con Dureza total, Calcio y Magnesio, cargar solo Calcio y verificar que Magnesio advierte que falta Dureza total; cargar Dureza total y verificar que Magnesio obtiene su resultado.

**Acceptance Scenarios**:

1. **Dada** una prueba calculada cuyas pruebas de referencia ya tienen resultado en el mismo estudio, **cuando** se guarda la última medición que faltaba, **entonces** la prueba calculada obtiene su resultado con su unidad y pasa a Cargada.
2. **Dada** una prueba calculada a la que le faltan resultados de referencia, **cuando** el empleado abre el detalle del estudio, **entonces** se advierte qué pruebas faltan (por código y nombre) y la prueba sigue Pendiente.
3. **Dada** una cadena de pruebas calculadas (ej. Sodio → Meq/l de Sodio → Total Cationes → CE/Sumatoria de cationes), **cuando** se completa la última medición de la que dependen, **entonces** se calculan todas las de la cadena en el orden correcto.
4. **Dada** una prueba calculada que referencia una prueba que no forma parte del estudio, **cuando** se abre el detalle, **entonces** se advierte que esa prueba no está en el estudio y que el resultado no se puede calcular.
5. **Dada** una fórmula que no se puede evaluar con los valores del estudio (ej. una división por cero o la raíz de un número negativo), **cuando** se guarda la medición que dispara el cálculo, **entonces** la prueba queda sin resultado, el mensaje de la carga advierte la prueba y el motivo, y el detalle lo sigue indicando; la medición y el resto de las pruebas se guardan normalmente.

---

### User Story 3 - Recalcular al cambiar una medición (Priority: P3)

Como empleado, cuando una medición cambia (al corregirla en US 6.3), quiero que el resultado de esa prueba y el de las pruebas calculadas que dependen de ella se recalculen solos, para que nunca quede un resultado que no corresponde a sus datos.

**Why this priority**: Lo pide el acuerdo con US 6.3; la pantalla para modificar mediciones llega con esa historia, así que acá se entrega el recálculo que ella va a usar.

**Independent Test**: Con Calcio, Dureza total y Magnesio ya calculados, cambiar la medición de Calcio y verificar que se recalculan Calcio y Magnesio, y que las pruebas que no dependen de Calcio no cambian.

**Acceptance Scenarios**:

1. **Dada** una prueba con resultado, **cuando** su medición cambia, **entonces** su resultado se recalcula con el valor nuevo.
2. **Dadas** pruebas calculadas que dependen (directa o indirectamente) de esa prueba, **cuando** su medición cambia, **entonces** también se recalculan; las demás pruebas del estudio no cambian.
3. **Dada** una prueba dependiente con resultado validado (Completada, US 6.4) en un estudio sin informe emitido, **cuando** cambia una medición de la que depende, **entonces** su resultado se recalcula, pierde la validación y vuelve a Cargada para validarse de nuevo.
4. **Dado** un estudio con informe emitido, **cuando** se intenta cambiar una de sus mediciones, **entonces** el cambio se rechaza informando el motivo y ningún resultado cambia.

### Edge Cases

- Una fórmula que referencia una prueba sin resultado en el estudio no se calcula y lo advierte; en cuanto ese resultado existe, se calcula sola.
- Una prueba calculada que referencia otra calculada espera a que esa tenga resultado (cadenas de cualquier largo, sin ciclos: el catálogo no permite que una prueba se referencie a sí misma).
- La fórmula o la unidad de la prueba cambian en el catálogo después de calcular: el resultado guardado conserva la fórmula y la unidad con las que se calculó; no se recalcula por cambios del catálogo.
- Pruebas que tenían medición antes de esta historia (cargadas con US 6.1): obtienen su resultado al ponerse en marcha la historia, igual que si se hubieran cargado después.
- Un resultado con más de 4 decimales (ej. 0,004123) se muestra redondeado (0,0041); uno menor que 0,00005 se muestra como 0. El valor guardado conserva sus 10 decimales.
- Resultados negativos o cero (ej. NTK orgánico = NTK total − amonio): se guardan tal cual; esta historia no compara con límites (US 6.4).
- Una prueba sin unidad en el catálogo, vacía o escrita «--» (ej. RAS, o la medición de Sodio): se muestra «Sin unidad», tanto en el resultado como en la medición.
- Un estudio Finalizado (todas sus pruebas validadas) al que se le corrige una medición antes del informe: los dependientes vuelven a Cargada, así que el estudio deja de estar completo; volver de Finalizado a En proceso lo define US 6.4, dueña de ese estado.
- Si el cálculo falla por un error inesperado, la medición se guarda igual y la prueba queda sin resultado con la advertencia; nunca se muestra un resultado incorrecto.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Al guardar la medición de una prueba, el sistema MUST calcular su resultado en la misma operación: igual al valor medido para pruebas de tipo Directo, y aplicando la fórmula de la prueba con `x` = valor medido para las de tipo Fórmula.
- **FR-002**: El sistema MUST evaluar las fórmulas del catálogo con números decimales exactos: suma, resta, multiplicación, división, paréntesis, raíz cuadrada, el valor medido (`x`) y resultados de otras pruebas del mismo estudio (`{CODIGO}`). Cualquier otra expresión MUST rechazarse sin evaluarse.
- **FR-003**: Una prueba calculada a partir de otras MUST obtener su resultado en cuanto todas sus pruebas de referencia tengan resultado en el mismo estudio, y pasar de Pendiente a Cargada. Las cadenas de pruebas calculadas MUST resolverse en orden de dependencia.
- **FR-004**: Cada resultado MUST guardarse asociado a la prueba del estudio, con su valor, la unidad del resultado de la prueba y la fórmula aplicada vigentes al calcularlo, y la fecha y hora del cálculo.
- **FR-005**: El detalle del estudio MUST mostrar, para cada prueba, su resultado con su unidad (o «Sin unidad»), redondeado a 4 decimales como máximo y sin ceros finales de más (ej. 23,5; 0,72; 0,0041; 1234,5). El valor se guarda con 10 decimales; el redondeo a 4 es solo para mostrarlo. Una unidad vacía o «--» se muestra «Sin unidad».
- **FR-006**: Para cada prueba sin resultado, el detalle MUST indicar por qué: falta su medición, faltan resultados de otras pruebas (listándolas por código y nombre), una prueba de referencia no forma parte del estudio, o la fórmula no se pudo evaluar (ej. división por cero).
- **FR-007**: Un error al calcular MUST NOT impedir guardar la medición ni afectar el resultado de las demás pruebas; la prueba afectada queda sin resultado con la advertencia.
- **FR-013**: Al guardar mediciones (US 6.1), el sistema MUST advertir en el mensaje de la carga cada prueba cuya fórmula no se pudo evaluar, con su código y el motivo. Las pruebas que solo esperan resultados de otras pruebas no se advierten en ese mensaje (se ven en el detalle, FR-006).
- **FR-008**: Cuando cambia la medición de una prueba (US 6.3), el sistema MUST recalcular en la misma operación su resultado y el de todas las pruebas calculadas que dependen de ella, directa o indirectamente; las demás no cambian.
- **FR-009**: Un resultado validado (prueba Completada, US 6.4) MUST NOT editarse a mano. Si cambia su propia medición o una de la que depende, y el estudio no tiene informe emitido, MUST recalcularse, perder la validación y volver a Cargada para revalidarse. Con informe emitido, el cambio de medición MUST rechazarse informando el motivo y ningún resultado cambia.
- **FR-010**: Los resultados MUST NOT recalcularse por cambios posteriores en la fórmula o la unidad del catálogo.
- **FR-011**: Las mediciones guardadas antes de esta historia MUST obtener su resultado (y el de las calculadas que correspondan) al ponerla en marcha.
- **FR-012**: Calcular resultados MUST NOT modificar las mediciones, la muestra, los datos históricos del estudio, el catálogo ni otros estudios.

### Key Entities *(include if feature involves data)*

- **Resultado**: Valor calculado de una prueba del estudio. Atributos: prueba del estudio (uno por prueba), valor numérico exacto, unidad del resultado, fórmula aplicada y fecha y hora del cálculo. Se reemplaza al recalcular; si estaba validado, pierde la validación. No cambia con informe emitido.
- **Medición** (US 6.1): Valor crudo de una prueba; es el `x` de su fórmula.
- **Prueba asignada al estudio**: Las pruebas calculadas pasan de Pendiente a Cargada al obtener su resultado.
- **Prueba (catálogo)**: Aporta el tipo de cálculo (Directo o Fórmula), la fórmula, la unidad del resultado y si se calcula a partir de otras pruebas (SCRUM-64).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: El 100% de las fórmulas del catálogo importado se calculan correctamente en los casos de prueba con valores esperados conocidos (al menos un caso por fórmula distinta).
- **SC-002**: El resultado de una prueba aparece en el detalle del estudio inmediatamente después de guardar su medición, sin pasos adicionales del empleado.
- **SC-003**: En el 100% de los casos de validación, ninguna prueba muestra un resultado que no corresponda a sus mediciones actuales: después de un cambio de medición, todos los resultados dependientes están recalculados.
- **SC-004**: El 100% de las pruebas sin resultado indica el motivo en el detalle del estudio.
- **SC-005**: Ningún resultado cambia en un estudio con informe emitido, y ningún resultado recalculado conserva una validación anterior.

## Assumptions

- **Trazabilidad**: US 6.2 – Cálculo automático del resultado. Jira: SCRUM-54. Responsable: Juan José (la tomó en lugar del compañero asignado originalmente; la US 6.3 se hace después, en `017-…`).
- **Dependencias**: Se apoya en la carga de mediciones (US 6.1: una medición por prueba del estudio, con su valor exacto) y en el catálogo de pruebas con tipo de cálculo, fórmula, unidad del resultado y marca de calculada (SCRUM-64).
- **Curva de calibración**: El catálogo no tiene curvas de calibración propias; las conversiones (ej. absorbancia a concentración) están expresadas como fórmulas. Esta historia aplica esas fórmulas; cargar curvas por separado queda fuera de alcance.
- **Cálculo automático**: No hay un botón «Calcular»: el resultado se obtiene al guardar la medición, y el de las calculadas en cuanto están sus referencias.
- **Excepción al principio IV**: la constitution dice que un resultado validado no se modifica. Aquí no se edita a mano: un recálculo por una medición corregida lo reemplaza y le quita la validación, y solo antes del informe (Clarifications). La excepción se justifica en `plan.md` (Governance).
- **Estado de la prueba**: Una prueba medida ya está Cargada desde US 6.1; obtener el resultado no cambia su estado. Una calculada pasa de Pendiente a Cargada con su resultado. Pasar a Completada es US 6.4.
- **Modificar mediciones**: La pantalla para corregir mediciones es US 6.3 (acuerdo en SCRUM-54/55). Esta historia entrega el recálculo que esa pantalla usará; aquí se prueba directamente sobre el cambio de la medición.
- **Precisión de cálculo**: Los cálculos se hacen con decimales exactos (constitution, principio IV); la raíz cuadrada se calcula con precisión suficiente para que el redondeo mostrado sea exacto.
- **Interfaz**: Las pantallas siguen el diseño de SCRUM-67 con los componentes de `templates/ui/`.
- **Datos académicos**: AquaLab es un proyecto FIUBA; los datos de desarrollo y demostración son ficticios (DEMO).
- **Alcance excluido**: Comparar con límites normativos o de referencia e indicar fuera de norma, y validar resultados (US 6.4); la pantalla para modificar mediciones (US 6.3); informes (Epic 7); comparación histórica y desvíos (Epic 8); editar fórmulas del catálogo.
