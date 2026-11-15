# Feature Specification: Curva de calibración para pruebas por absorbancia

**Feature Branch**: `037-curva-calibracion`

**Created**: 2026-11-14

**Status**: Borrador

**Input**: User description: "US 6.6 (Jira SCRUM-38) – Curva de calibración para pruebas por absorbancia. Como administrador del laboratorio quiero cargar las curvas de calibración de las pruebas que se miden por absorbancia, a mano o importándolas desde un archivo, para que AquaLab convierta la absorbancia en concentración con la curva vigente y quede registrado con qué curva se calculó cada resultado, asegurando la trazabilidad. Criterios de aceptación: (1) En el catálogo de pruebas se puede elegir el tipo de cálculo «Curva de calibración» (además de Directo y Fórmula), con la unidad del resultado. (2) Desde la ficha de una prueba con curva se da de alta una curva nueva con: fecha de preparación, los puntos de los estándares (concentración conocida y absorbancia leída, mínimo 3 puntos) y una observación opcional. (3) Los puntos se pueden cargar a mano (fila por fila) o importar desde un archivo: CSV o Excel (.csv, .xlsx); el sistema detecta las columnas de concentración y absorbancia e ignora títulos, filas vacías y celdas con texto; acepta coma o punto decimal; si no puede identificarlas, pide elegir cuál es cada una; los puntos leídos se muestran en la misma tabla de la carga manual, donde se pueden corregir, agregar o quitar antes de seguir; si el archivo no se puede leer o no trae al menos 3 puntos válidos, se indica el motivo (ej. «la fila 4 no tiene absorbancia») y no se carga nada; se puede descargar una plantilla con el formato sugerido. (4) Con los puntos, el sistema calcula la recta por mínimos cuadrados (pendiente, ordenada y R²) y la muestra junto con un gráfico de los puntos antes de guardar. (5) Antes de guardar se pide confirmación con un resumen de la curva (si se importó, incluye el nombre del archivo, que queda registrado con la curva). (6) Cada prueba tiene una sola curva vigente: al guardar una nueva, la anterior queda como histórica. Una curva que ya se usó en algún resultado no se edita ni se borra. (7) Al cargar la absorbancia en un estudio, el resultado se calcula con la curva vigente: concentración = (absorbancia − ordenada) / pendiente. (8) Cada resultado guarda con qué curva se calculó; la ficha del estudio la muestra junto al resultado (fecha de la curva y R²). (9) Si la prueba no tiene curva vigente, no se calcula el resultado y se indica «Falta curva de calibración». No se puede validar (igual que una prueba sin medición). (10) Si la absorbancia queda fuera del rango de los estándares de la curva, se muestra un aviso junto al resultado. No bloquea: el bioquímico decide al validar. (11) Al corregir una medición, el resultado se recalcula con la misma curva con la que se había calculado (no con una más nueva). (12) Solo quien tiene permiso de gestionar el catálogo puede cargar curvas. Cualquier empleado puede ver la curva vigente y las históricas de una prueba. Fuera de alcance: importar en un solo archivo las curvas de varias pruebas a la vez; archivos en otros formatos (PDF, imágenes, .xls viejo, .ods); pasar a curva las pruebas que hoy usan fórmula; curvas no lineales; vencimiento automático de curvas por fecha."

## Clarifications

### Session 2026-11-14

- Q: Si una prueba por curva tiene absorbancias cargadas sin resultado («Falta curva de calibración»), ¿qué pasa al cargar una curva? → A: Se ofrece al guardar: la confirmación muestra cuántas mediciones esperan curva y la opción «Calcularlas con esta curva»; si no se marca, quedan esperando (se calculan al corregirlas). Los estudios con informe emitido no se tocan.
- Q: ¿Se exige un R² mínimo para guardar una curva? → A: No se bloquea. Con R² menor que 0,995 se muestra un aviso en el cálculo y en el resumen de confirmación, y se puede guardar igual.
- Q: ¿Se puede borrar una curva cargada por error? → A: Sí, con confirmación, solo si no se usó en ningún resultado. Si era la vigente, vuelve a quedar vigente la anterior (o la prueba queda sin curva). Una curva usada nunca se borra.

### Session 2026-11-15

- Q: Si se confirma una curva sin marcar «Calcularlas con esta curva», ¿cómo se calculan después esas mediciones? (Corregir con el mismo valor no hace nada.) → A: En el detalle del estudio, esas pruebas muestran «Se cargó antes de la curva vigente» y la acción «Calcular con la curva vigente», con confirmación, para cualquier empleado que pueda cargar mediciones. Reemplaza el «quedan esperando hasta que se corrijan» de la primera aclaración.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Definir una prueba por curva de calibración (Priority: P1)

Como administrador, al dar de alta (o editar, si no está en uso) una prueba del catálogo, elijo el tipo de cálculo «Curva de calibración» e indico la unidad del resultado (la de la concentración). La prueba queda lista para recibir curvas.

**Why this priority**: Es la puerta de entrada: sin este tipo de cálculo no hay dónde cargar una curva ni forma de que una prueba la use.

**Independent Test**: Crear la prueba «Nitritos (curva)» con tipo «Curva de calibración» y unidad del resultado mg/l; verificar que la ficha la muestra con ese tipo, sin fórmula, y con el aviso de que todavía no tiene curva vigente.

**Acceptance Scenarios**:

1. **Dado** el alta de una prueba del catálogo, **cuando** se elige el tipo de cálculo, **entonces** se ofrecen «Directo», «Fórmula» y «Curva de calibración».
2. **Dado** el tipo «Curva de calibración», **cuando** se completa el formulario, **entonces** la unidad del resultado es obligatoria, la fórmula no se pide ni se guarda y la unidad de medición se propone como «Abs».
3. **Dada** una prueba por curva recién creada, **cuando** se abre su ficha, **entonces** indica «Sin curva vigente» y ofrece cargar una curva.
4. **Dada** una prueba en uso, **cuando** se intenta cambiar su tipo de cálculo a «Curva de calibración», **entonces** se rechaza con el mensaje de método bloqueado de SCRUM-73 (hay que crear una prueba nueva y reemplazar la anterior).

---

### User Story 2 - Cargar una curva a mano (Priority: P1)

Como administrador, desde la ficha de una prueba por curva cargo una curva nueva: la fecha de preparación, los puntos de los estándares (concentración conocida y absorbancia leída) fila por fila y, si quiero, una observación. El sistema calcula la recta, me la muestra con un gráfico y, al confirmar, pasa a ser la curva vigente de la prueba.

**Why this priority**: Es el camino mínimo para tener una curva vigente; la importación (US3) solo es otra forma de llenar la misma tabla.

**Independent Test**: Cargar los puntos (0; 0,000), (0,1; 0,052), (0,2; 0,101), (0,3; 0,153), (0,4; 0,199) y verificar pendiente, ordenada y R² contra valores calculados aparte; confirmar y verificar que queda vigente y la curva anterior, si la había, pasa a histórica.

**Acceptance Scenarios**:

1. **Dada** la ficha de una prueba por curva, **cuando** el administrador toca «Nueva curva», **entonces** ve un formulario con fecha de preparación, observación opcional y una tabla de puntos (concentración y absorbancia) donde puede agregar y quitar filas.
2. **Dados** al menos 3 puntos válidos, **cuando** se toca «Calcular recta», **entonces** el sistema muestra la pendiente, la ordenada al origen y el R² de la recta por mínimos cuadrados, y un gráfico con los puntos y la recta.
3. **Dados** menos de 3 puntos válidos, **cuando** se intenta calcular, **entonces** se indica que hacen falta al menos 3 puntos y no se avanza.
4. **Dado** un punto con concentración o absorbancia vacía, no numérica o negativa, **cuando** se intenta calcular, **entonces** se marca el error junto a ese punto indicando qué falta o qué está mal.
5. **Dados** puntos con todas las concentraciones iguales o con todas las absorbancias iguales, **cuando** se intenta calcular, **entonces** se rechaza explicando que la recta no permite convertir absorbancia en concentración.
6. **Dada** la recta calculada, **cuando** se toca «Guardar», **entonces** se pide confirmación con un resumen (prueba, fecha de preparación, cantidad de puntos, rango de concentraciones, pendiente, ordenada, R² y observación).
7. **Dado** el resumen, **cuando** se confirma, **entonces** la curva queda vigente, la que estaba vigente pasa a histórica y se vuelve a la ficha con un mensaje de éxito; **cuando** se cancela, **entonces** se vuelve a la tabla con los puntos cargados y no se guarda nada.
8. **Dada** una fecha de preparación posterior a hoy, **cuando** se intenta guardar, **entonces** se rechaza junto al campo.
9. **Dada** una recta con R² menor que 0,995, **cuando** se calcula y en el resumen de confirmación, **entonces** se muestra el aviso «R² menor que 0,995: revisá los puntos antes de guardar» y se puede guardar igual.

---

### User Story 3 - Importar los puntos desde un archivo (Priority: P2)

Como administrador, en lugar de tipear los puntos subo el archivo que exporta el espectrofotómetro o la planilla del laboratorio (CSV o Excel). El sistema detecta las columnas de concentración y absorbancia, ignora títulos, filas vacías y textos, y me muestra los puntos en la misma tabla de la carga manual para que los revise antes de seguir.

**Why this priority**: Ahorra tipeo y errores de transcripción, pero la carga manual ya cubre el objetivo de la historia.

**Independent Test**: Importar la plantilla descargada con 5 puntos y una fila de título; verificar que aparecen los 5 puntos en la tabla, editables, y que al guardar el nombre del archivo queda registrado con la curva.

**Acceptance Scenarios**:

1. **Dada** la carga de una curva, **cuando** se toca «Descargar plantilla», **entonces** se descarga un archivo con el formato sugerido (columnas «Concentración» y «Absorbancia» y un ejemplo).
2. **Dado** un archivo .csv o .xlsx con encabezados reconocibles de concentración y absorbancia, **cuando** se importa, **entonces** los puntos leídos aparecen en la tabla de puntos, donde se pueden corregir, agregar o quitar antes de calcular.
3. **Dado** un archivo con filas de título, filas vacías y celdas con texto fuera de los puntos, **cuando** se importa, **entonces** esas filas se ignoran y solo se toman las filas con concentración y absorbancia numéricas.
4. **Dado** un archivo con números escritos con coma o con punto decimal, **cuando** se importa, **entonces** se leen igual.
5. **Dado** un archivo en el que el sistema no puede identificar qué columna es cada una, **cuando** se importa, **entonces** se pide elegir cuál es la columna de concentración y cuál la de absorbancia, mostrando una vista previa de las columnas, y después se cargan los puntos.
6. **Dado** un archivo que no se puede leer (formato no admitido, dañado o vacío), **cuando** se importa, **entonces** se indica el motivo y la tabla de puntos queda como estaba.
7. **Dado** un archivo con una fila con concentración pero sin absorbancia (o al revés), **cuando** se importa, **entonces** se indica el motivo con el número de fila (ej. «La fila 4 no tiene absorbancia») y no se carga ningún punto.
8. **Dado** un archivo con menos de 3 puntos válidos, **cuando** se importa, **entonces** se indica que hacen falta al menos 3 puntos y no se carga ningún punto.
9. **Dada** una curva cuyos puntos se importaron, **cuando** se confirma, **entonces** el resumen y la curva guardada incluyen el nombre del archivo; si después se editaron puntos en la tabla, se guardan los puntos editados con el mismo nombre de archivo de origen.

---

### User Story 4 - Calcular el resultado con la curva vigente (Priority: P1)

Como empleado del laboratorio, cargo la absorbancia leída de una prueba por curva en un estudio y el sistema calcula la concentración con la curva vigente de esa prueba, guardando con qué curva lo hizo. En la ficha del estudio veo el resultado junto a la fecha de la curva y su R².

**Why this priority**: Es el objetivo de la historia: convertir absorbancia en concentración sin cálculo manual y con trazabilidad.

**Independent Test**: Con la curva de pendiente 0,5 y ordenada 0,001 vigente, cargar una absorbancia de 0,126 y verificar un resultado de 0,25 mg/l con la fecha y el R² de esa curva en la ficha del estudio.

**Acceptance Scenarios**:

1. **Dada** una prueba por curva con curva vigente, **cuando** se carga su absorbancia en un estudio, **entonces** el resultado es (absorbancia − ordenada) / pendiente, con la unidad del resultado de la prueba.
2. **Dado** un resultado calculado con curva, **cuando** se abre la ficha del estudio, **entonces** junto al resultado se muestra la curva usada (fecha de preparación y R²), con un enlace para verla.
3. **Dada** una prueba por curva sin curva vigente, **cuando** se carga su absorbancia, **entonces** la medición se guarda, no se calcula el resultado y se indica «Falta curva de calibración».
4. **Dada** una prueba sin resultado por falta de curva, **cuando** se intenta validar, **entonces** no se ofrece para validar, igual que una prueba sin medición.
5. **Dada** una absorbancia menor que la del estándar más bajo o mayor que la del más alto de la curva, **cuando** se calcula el resultado, **entonces** se muestra el resultado con el aviso «Fuera del rango de la curva (<mín>–<máx> <unidad>)» en la ficha del estudio y en la validación, y se puede validar igual.
6. **Dada** una prueba de fórmula que usa una prueba por curva (ej. `{NO2}*1,5`), **cuando** la prueba por curva tiene resultado, **entonces** la fórmula usa la concentración calculada, no la absorbancia.
7. **Dado** un resultado calculado con una curva, **cuando** después se carga una curva nueva para esa prueba, **entonces** el resultado no cambia y sigue mostrando la curva con la que se calculó.
8. **Dadas** mediciones de la prueba sin resultado por falta de curva, **cuando** se va a confirmar una curva nueva, **entonces** el resumen indica cuántas mediciones esperan curva (y en cuántos estudios) y ofrece «Calcularlas con esta curva».
9. **Dada** la opción «Calcularlas con esta curva» marcada, **cuando** se confirma, **entonces** en la misma operación esas mediciones se calculan con la curva nueva, que queda registrada en cada resultado, y el mensaje de éxito dice cuántas se calcularon; **sin marcarla**, quedan sin resultado.
10. **Dado** un estudio con informe emitido o Finalizado, **cuando** se calculan las mediciones que esperaban curva, **entonces** ese estudio no se toca ni se cuenta (solo cuentan los estudios Pendientes de análisis o En proceso).
11. **Dada** una medición sin resultado cargada antes de que la prueba tuviera curva, **cuando** ya hay curva vigente y se abre el detalle del estudio, **entonces** la prueba muestra «Se cargó antes de la curva vigente» (no «Falta curva de calibración») y el estudio ofrece «Calcular con la curva vigente».
12. **Dada** la acción «Calcular con la curva vigente», **cuando** se confirma, **entonces** se calculan con la curva vigente de cada prueba todas las mediciones del estudio en esa situación, con sus dependientes, y el mensaje dice cuántas; si al confirmar ya no queda ninguna (otra persona las calculó), se informa sin cambios.

---

### User Story 5 - Corregir una medición manteniendo la curva (Priority: P2)

Como empleado del laboratorio, corrijo la absorbancia de una prueba por curva (US 6.3) y el resultado se recalcula con la misma curva con la que se había calculado, aunque desde entonces se haya cargado una curva más nueva.

**Why this priority**: Garantiza que una corrección no mezcle curvas dentro de un mismo estudio; depende de US4.

**Independent Test**: Calcular un resultado con la curva A, cargar la curva B, corregir la absorbancia y verificar que el resultado nuevo sale con la curva A y sigue mostrando la curva A.

**Acceptance Scenarios**:

1. **Dado** un resultado calculado con la curva A y una curva B vigente, **cuando** se corrige la absorbancia, **entonces** el resultado se recalcula con la curva A.
2. **Dada** una prueba que no tenía resultado por falta de curva, **cuando** se corrige su absorbancia a otro valor y hay una curva vigente, **entonces** el resultado se calcula con la curva vigente (para calcularla sin cambiar el valor está «Calcular con la curva vigente», US4 Esc. 12).
3. **Dada** una medición borrada (US 6.5) de una prueba por curva, **cuando** se vuelve a cargar, **entonces** se calcula con la curva vigente en ese momento.
4. **Dado** un resultado validado de una prueba por curva, **cuando** se corrige la absorbancia, **entonces** pierde la validación como cualquier otra corrección (US 6.3/6.4).

---

### User Story 6 - Consultar curvas de una prueba (Priority: P2)

Como empleado del laboratorio, consulto la curva vigente y las históricas de una prueba: fecha de preparación, puntos, pendiente, ordenada, R², gráfico, quién la cargó y cuándo, observación, archivo de origen y si ya se usó en algún resultado.

**Why this priority**: Da la trazabilidad pedida (con qué curva se calculó cada resultado), pero no es necesaria para calcular.

**Independent Test**: Con una prueba que tuvo dos curvas, entrar como técnico (sin permiso de catálogo) y verificar que ve la vigente marcada, la histórica y el detalle de cada una, sin opciones para cargar curvas.

**Acceptance Scenarios**:

1. **Dada** una prueba por curva, **cuando** cualquier empleado consulta sus curvas, **entonces** ve la vigente destacada y las históricas de la más nueva a la más vieja, cada una con fecha de preparación, R², quién la cargó y cuándo.
2. **Dada** una curva, **cuando** se abre su detalle, **entonces** muestra los puntos, la pendiente, la ordenada, el R², el gráfico, la observación, el archivo de origen (si se importó) y si ya se usó en algún resultado.
3. **Dado** el enlace de la curva en la ficha del estudio, **cuando** se sigue, **entonces** se abre el detalle de la curva con la que se calculó ese resultado (aunque ya sea histórica).
4. **Dada** una curva que no se usó en ningún resultado, **cuando** un administrador confirma «Borrar curva», **entonces** se borra; si era la vigente, vuelve a quedar vigente la anterior más reciente, o la prueba queda «Sin curva vigente» si no había otra.
5. **Dada** una curva usada en algún resultado, **cuando** se abre su detalle o se intenta borrarla por cualquier vía, **entonces** no se ofrece «Borrar curva» y el intento se rechaza sin cambios, indicando que ya se usó.

---

### User Story 7 - Solo quien gestiona el catálogo carga curvas (Priority: P2)

Como laboratorio, quiero que solo quien tiene permiso para gestionar el catálogo de pruebas pueda cargar curvas.

**Why this priority**: Regla de seguridad; reutiliza el permiso de gestión del catálogo (SCRUM-73).

**Independent Test**: Con un bioquímico y un técnico, verificar 403 al cargar o importar curvas por cualquier dirección y acceso a la consulta; con un administrador, acceso completo.

**Acceptance Scenarios**:

1. **Dado** un usuario sin permiso de gestionar el catálogo, **cuando** entra a cargar, importar, confirmar o borrar una curva por cualquier dirección, **entonces** recibe 403 y no se guarda nada.
2. **Dado** un usuario sin permiso de gestionar el catálogo, **cuando** consulta las curvas de una prueba, **entonces** las ve sin las opciones de carga.
3. **Dado** un usuario sin sesión, **cuando** entra a cualquier pantalla de curvas, **entonces** se lo lleva al inicio de sesión.

---

### Edge Cases

- Una curva se borra mientras alguien carga una absorbancia con ella como vigente: si la medición se guardó antes, la curva ya está usada y el borrado se rechaza; si no, la medición se calcula con la que haya quedado vigente.
- Se confirma una curva con «Calcularlas con esta curva» mientras alguien corrige una de esas mediciones: cada medición se calcula una sola vez y con una sola curva; la que ya tenga resultado al procesarse no se recalcula.
- Dos administradores guardan una curva nueva para la misma prueba a la vez: queda vigente la última confirmada y la otra queda histórica; nunca quedan dos vigentes.
- Una curva se guarda mientras se está cargando una absorbancia en un estudio: el resultado se calcula con la curva vigente en el momento de guardar la medición, y queda registrado cuál fue.
- Puntos repetidos (réplicas del mismo estándar): se aceptan y entran todos en el cálculo de la recta.
- El blanco (concentración 0) es un punto más; no se fuerza la recta a pasar por el origen.
- Una absorbancia que da concentración negativa (menor que la ordenada): queda fuera del rango de la curva y se muestra con el aviso; se aplica la regla habitual de límite de detección («< LD») si corresponde.
- Un archivo .xlsx con varias hojas: se leen los puntos de la primera hoja.
- Un archivo con más de dos columnas numéricas (ej. réplicas o promedio): el sistema no adivina; pide elegir cuál es la de concentración y cuál la de absorbancia.
- Una prueba por curva sin uso que ya tiene curvas cargadas no puede cambiar a otro tipo de cálculo: se indica que primero hay que borrar sus curvas. Si se elimina la prueba (sin uso), se eliminan también sus curvas, que nunca se usaron.
- La prueba por curva se desactiva (SCRUM-73): sus curvas siguen consultables y los estudios donde ya estaba siguen calculando con la curva vigente o la ya usada.
- Un informe ya emitido o un resultado validado no cambian por cargar una curva nueva (principio IV).
- La importación del catálogo por CSV (`importar_catalogo_pruebas`) no carga curvas; si trae el tipo «Curva de calibración», la prueba queda sin curva vigente hasta que se cargue desde la app.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El catálogo de pruebas MUST ofrecer el tipo de cálculo «Curva de calibración», además de «Directo» y «Fórmula», en el alta y en la edición de una prueba sin uso (las reglas de método bloqueado de SCRUM-73 se mantienen).
- **FR-002**: Una prueba por curva MUST tener unidad del resultado, MUST NOT tener fórmula y MUST proponer «Abs» como unidad de medición.
- **FR-003**: Desde la ficha de gestión de una prueba por curva, el sistema MUST permitir dar de alta una curva con fecha de preparación (obligatoria, no posterior a hoy), puntos de estándares (concentración conocida y absorbancia leída) y observación opcional.
- **FR-004**: Cada punto MUST tener concentración y absorbancia numéricas no negativas (coma o punto decimal, con la misma regla de lectura que las mediciones); una curva MUST tener al menos 3 puntos y al menos dos concentraciones y dos absorbancias distintas.
- **FR-005**: Los puntos MUST poder cargarse fila por fila en una tabla donde se agregan, corrigen y quitan antes de calcular.
- **FR-006**: El sistema MUST permitir importar los puntos desde un archivo .csv o .xlsx (primera hoja); otros formatos MUST rechazarse indicando cuáles se aceptan.
- **FR-007**: Al importar, el sistema MUST detectar las columnas de concentración y absorbancia por sus encabezados, ignorar títulos, filas vacías y celdas con texto, y aceptar coma o punto decimal. Si no puede identificarlas, MUST pedir al usuario que elija cuál es cada columna con una vista previa.
- **FR-008**: Si el archivo no se puede leer, tiene una fila con solo uno de los dos valores o no trae al menos 3 puntos válidos, el sistema MUST indicar el motivo (con el número de fila cuando aplique) y MUST NOT cargar ningún punto en la tabla.
- **FR-009**: Los puntos importados MUST mostrarse en la misma tabla de la carga manual, editables antes de calcular.
- **FR-010**: El sistema MUST ofrecer una plantilla descargable con el formato sugerido (columnas «Concentración» y «Absorbancia» y un ejemplo).
- **FR-011**: Con los puntos, el sistema MUST calcular la recta absorbancia = pendiente × concentración + ordenada por mínimos cuadrados, con su R², con aritmética decimal exacta, y mostrarla con un gráfico de los puntos y la recta antes de guardar.
- **FR-012**: Antes de guardar, el sistema MUST pedir confirmación con un resumen (prueba, fecha de preparación, cantidad de puntos, rango de concentraciones, pendiente, ordenada, R², observación y, si se importó, nombre del archivo) y permitir cancelar sin cambios.
- **FR-013**: Cada curva MUST guardar quién la cargó y cuándo, sus puntos, pendiente, ordenada, R², rango de concentraciones, observación y, si se importó, el nombre del archivo de origen.
- **FR-014**: Cada prueba MUST tener a lo sumo una curva vigente; al confirmar una nueva, la vigente anterior MUST pasar a histórica en la misma operación, también con confirmaciones simultáneas.
- **FR-015**: Una curva MUST NOT poder editarse: para cambiar puntos se carga una curva nueva. Una curva no usada en ningún resultado MUST poder borrarse con confirmación por quien gestiona el catálogo; si era la vigente, la anterior más reciente MUST volver a quedar vigente (o la prueba queda sin curva vigente). Una curva usada MUST NOT poder borrarse, revalidándolo al confirmar.
- **FR-015a**: Si el R² es menor que 0,995, el sistema MUST mostrar un aviso al calcular y en el resumen de confirmación, y MUST permitir guardar igual.
- **FR-016**: Al calcular el resultado de una prueba por curva sin curva asignada, el sistema MUST usar la curva vigente: concentración = (absorbancia − ordenada) / pendiente, con la unidad del resultado de la prueba y la misma precisión que el resto de los resultados (US 6.2).
- **FR-017**: Cada resultado de una prueba por curva MUST guardar la curva con la que se calculó; la ficha del estudio MUST mostrarla junto al resultado (fecha de preparación y R²) con enlace a su detalle.
- **FR-018**: Si la prueba por curva no tiene curva vigente, el sistema MUST guardar la medición, MUST NOT calcular el resultado y MUST indicar «Falta curva de calibración»; esa prueba MUST NOT poder validarse.
- **FR-019**: Si la absorbancia está fuera del rango de absorbancias de los estándares de la curva, el sistema MUST mostrar un aviso junto al resultado en la ficha del estudio y en la validación, sin impedir validar.
- **FR-020**: Al recalcular un resultado que ya tenía curva (corrección de la medición o recálculo por dependencias), el sistema MUST usar esa misma curva, aunque haya otra vigente.
- **FR-021**: Las fórmulas que referencian una prueba por curva MUST usar su resultado (la concentración).
- **FR-022**: Cargar una curva nueva MUST NOT modificar resultados ya calculados, validaciones ni informes emitidos.
- **FR-023**: Solo los usuarios con permiso de gestionar el catálogo de pruebas (SCRUM-73) MUST poder cargar, importar, confirmar y borrar curvas; el resto MUST recibir 403 sin cambios.
- **FR-024**: Cualquier empleado con sesión MUST poder consultar la curva vigente y las históricas de una prueba, con su detalle.
- **FR-025**: Si hay mediciones de la prueba sin resultado por falta de curva en estudios Pendientes de análisis o En proceso, el resumen de confirmación de una curva nueva MUST indicar cuántas son (y en cuántos estudios) y ofrecer «Calcularlas con esta curva». Marcada, MUST calcularlas con esa curva en la misma operación (con sus dependientes y el estado del estudio como cualquier cálculo de US 6.2), sin tocar mediciones que ya tengan resultado; sin marcar, MUST dejarlas sin resultado.
- **FR-026**: Una prueba por curva con medición y sin resultado, cuya prueba ya tiene curva vigente, MUST mostrar «Se cargó antes de la curva vigente» en el detalle del estudio, y el estudio MUST ofrecer «Calcular con la curva vigente», con confirmación, a quien puede cargar mediciones, mientras el estudio admita mediciones. Al confirmar, MUST calcular en una operación todas las de ese estudio en esa situación, con la vigente de cada prueba y sus dependientes, sin tocar las que ya tengan resultado e informando cuántas se calcularon.

### Key Entities *(include if feature involves data)*

- **Prueba** (catálogo): suma el tipo de cálculo «Curva de calibración». Tiene a lo sumo una curva vigente.
- **Curva de calibración**: pertenece a una prueba; fecha de preparación, observación, archivo de origen (opcional), pendiente, ordenada, R², rango de concentraciones y de absorbancias, vigente o histórica, quién la cargó y cuándo, y si se usó en algún resultado.
- **Punto de la curva**: estándar de una curva: concentración conocida y absorbancia leída.
- **Medición** (US 6.1): para una prueba por curva, la absorbancia leída.
- **Resultado** (US 6.2): para una prueba por curva, la concentración, con la curva usada.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Un administrador carga una curva de 6 puntos (a mano o importando la plantilla) y la deja vigente en menos de 3 minutos.
- **SC-002**: La pendiente, la ordenada, el R² y los resultados coinciden con los valores de referencia de los casos de prueba en todos sus decimales mostrados.
- **SC-003**: El 100 % de los resultados de pruebas por curva muestran con qué curva se calcularon, y el 100 % de los recálculos usan esa misma curva.
- **SC-004**: El 100 % de los archivos con errores (ilegibles, con filas incompletas o con menos de 3 puntos) terminan con un motivo y sin puntos cargados.
- **SC-005**: Ninguna prueba por curva sin curva vigente tiene resultado ni se puede validar.
- **SC-006**: Cargar una curva nueva no cambia ningún resultado anterior, validación ni informe emitido.

## Assumptions

- **Trazabilidad**: US 6.6 – Curva de calibración para pruebas por absorbancia. Jira: SCRUM-38. Responsable: a confirmar.
- **Dependencias**: se apoya en el catálogo gestionado desde la app (SCRUM-73: ficha de la prueba, permiso de gestión y método bloqueado en uso), en la carga, el cálculo, la corrección, el borrado y la validación de mediciones (US 6.1 a 6.5) y en la regla de lectura de valores de las mediciones.
- **Permiso**: «permiso de gestionar el catálogo» es el mismo de SCRUM-73 (grupo «Administradores» con el permiso del panel de administración).
- **Consulta**: la consulta de curvas es una pantalla de solo lectura para todos los empleados, enlazada desde la ficha del estudio; la carga está en la ficha de gestión de la prueba (panel de administración).
- **Unidades**: la concentración de los estándares está en la unidad del resultado de la prueba; no se aplican factores de dilución (fuera de alcance).
- **Vigencia**: la vigente es la última curva confirmada, no la de fecha de preparación más reciente.
- **Pruebas en uso**: una prueba en uso no cambia de tipo de cálculo (SCRUM-73); pasarla a curva es crear una prueba nueva por curva y reemplazar la anterior con el reemplazo de SCRUM-73, a mano, cuando el laboratorio cargue sus curvas.
- **Informe**: el informe emitido y su PDF no muestran la curva; la trazabilidad queda en el sistema (fuera de alcance mostrarla en el informe).
- **Interfaz**: diseño de SCRUM-67 y componentes de `templates/ui/`, con confirmación previa como el resto del panel y ayudas en los campos no evidentes (US 9.1). El gráfico usa la misma librería de gráficos ya incorporada (US 8.1/8.3).
- **Alcance excluido**: importar curvas de varias pruebas en un solo archivo; formatos distintos de .csv y .xlsx (PDF, imágenes, .xls, .ods); migrar las pruebas que hoy usan fórmula; curvas no lineales; vencimiento automático por fecha; mostrar la curva en el informe.
