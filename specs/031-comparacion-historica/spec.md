# Feature Specification: Comparación histórica por origen

**Feature Branch**: `031-comparacion-historica`

**Created**: 2026-11-09

**Status**: Draft

**Input**: User description: "SCRUM-60 – 8.1 Comparación histórica por origen. Como bioquímico quiero ver la evolución de los resultados de un mismo origen a lo largo del tiempo para detectar variaciones que requieran revisión. La asociación de la muestra a un origen ya está resuelta (US 4.1). Criterios: (1) Desde el detalle de un estudio, y desde el dashboard eligiendo cliente y origen, se accede a la comparación histórica del origen. (2) Por cada prueba se muestra un gráfico de evolución con los resultados de ese origen, ordenados por fecha de muestreo, con la franja del límite permitido dibujada. (3) Se pueden ver varias pruebas a la vez y elegir cuáles mostrar. (4) Por cada prueba se indica la variación del último resultado contra el anterior y contra el promedio de los anteriores. (5) El historial usa solo resultados validados de la misma prueba; el resultado del estudio actual aparece destacado en el gráfico aunque todavía no esté validado, para poder revisarlo antes de validar; las pruebas sin historial muestran el valor actual sin gráfico. (6) Se indica la variación pero no se valida ni se rechaza ningún resultado automáticamente; es solo para el laboratorio, el cliente no lo ve. Notas técnicas: reutilizar Chart.js de static/vendor y el patrón de dashboard.js de la US 8.3; el cálculo del historial y de la variación debe quedar en una función reutilizable, porque la 8.2 (SCRUM-61, desvíos) lo va a usar. Diferencial pedido por la profesora: no recortar."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Revisar un resultado contra la historia del origen antes de validarlo (Priority: P1)

Como bioquímico, desde el detalle de un estudio entro a «Comparación histórica» y veo, para cada
prueba del estudio, un gráfico con los resultados validados anteriores del mismo origen ordenados
por fecha de muestreo, con el resultado de este estudio destacado (aunque todavía no esté validado)
y la franja del límite permitido. Así detecto si el valor actual se aparta de lo habitual antes de
validarlo.

**Why this priority**: Es el objetivo central de la historia: revisar variaciones en el momento en
que se decide validar.

**Independent Test**: Con la demo de SCRUM-78 cargada, abrir el estudio de «Pozo 2» con Cloruro
430 sin validar y verificar que el gráfico de Cloruro muestra los resultados validados anteriores
(~120 … 415) en orden de fecha de muestreo, el 430 destacado como «sin validar» y la franja del
límite de Cloruro.

**Acceptance Scenarios**:

1. **Dado** el detalle de un estudio cuya muestra tiene origen, **cuando** un usuario con acceso
   lo abre, **entonces** ve la acción «Comparación histórica», que lleva a la comparación del
   origen de esa muestra con el estudio como referencia.
2. **Dado** un origen con resultados validados de Cloruro en muestras anteriores, **cuando** se
   abre la comparación desde un estudio con Cloruro calculado y sin validar, **entonces** el
   gráfico de Cloruro muestra un punto por cada resultado validado, ordenado por fecha de muestreo,
   y el resultado del estudio actual como punto destacado (con otro color y forma) e identificado
   como «Sin validar».
3. **Dado** el resultado actual ya validado, **cuando** se muestra el gráfico, **entonces** sigue
   destacado como resultado del estudio actual e identificado como «Validado».
4. **Dado** un estudio cuya prueba todavía no tiene resultado, **cuando** se muestra la
   comparación, **entonces** el gráfico muestra el historial sin punto destacado y la prueba
   indica «Sin resultado en este estudio».
5. **Dada** una prueba del estudio sin resultados validados anteriores en ese origen, **cuando**
   se muestra la comparación, **entonces** se ve el valor actual (o «Sin resultado en este
   estudio») con la leyenda «Sin historial para comparar», sin gráfico ni variación.
6. **Dado** cualquier punto del gráfico, **cuando** se pasa el puntero o el foco sobre él,
   **entonces** se ve la fecha de muestreo, el N° PI, el valor con su unidad y si está validado.

---

### User Story 2 - Ver la variación del último resultado (Priority: P1)

Como bioquímico, por cada prueba veo cuánto cambió el último resultado contra el anterior y contra
el promedio de todos los anteriores, en cantidad y porcentaje, para dimensionar el cambio sin hacer
cuentas.

**Why this priority**: El criterio 4 es la medida concreta del desvío y la base que reutiliza la
US 8.2.

**Independent Test**: Con historial conocido (p. ej. 100, 120, 140 validados y 210 actual),
verificar que la variación contra el anterior es +70 (+50 %) y contra el promedio (120) es +90
(+75 %).

**Acceptance Scenarios**:

1. **Dado** un estudio de referencia con resultado, **cuando** se calcula la variación,
   **entonces** el «último» es el resultado de ese estudio, el «anterior» es el último resultado
   validado de una muestra anterior del mismo origen y el «promedio» es el de todos los resultados
   validados de muestras anteriores (FR-008).
2. **Dada** la comparación abierta desde el dashboard (sin estudio de referencia), **cuando** se
   calcula la variación, **entonces** el «último» es el resultado validado más reciente y se
   compara contra los validados anteriores a él.
3. **Dados** resultados 100, 120, 140 validados y 210 actual, **cuando** se muestra la variación,
   **entonces** indica «+70 mg/l (+50,0 %)» contra el anterior y «+90 mg/l (+75,0 %)» contra el
   promedio (120), con flecha y signo.
4. **Dado** un único resultado anterior, **cuando** se muestra la variación, **entonces** la
   variación contra el anterior y contra el promedio coinciden y se muestran las dos.
5. **Dado** un anterior o un promedio igual a 0, **cuando** se muestra la variación,
   **entonces** muestra la diferencia en cantidad y, en lugar del porcentaje, «sin porcentaje
   (valor previo 0)».
6. **Dada** una prueba Ausente/Presente, **cuando** se muestra la variación, **entonces** no se
   muestran cantidades ni porcentajes: se indica «Sin cambios (Ausente)» o «Cambió: Ausente →
   Presente», y contra los anteriores cuántos fueron Presente (p. ej. «Presente en 1 de 6»).
7. **Dada** cualquier variación, **cuando** se muestra, **entonces** no hay ningún aviso de
   «rechazado» ni «validado» automático ni cambia el estado de ninguna prueba ni estudio: el color
   indica solo si el último resultado está fuera de la franja del límite.

---

### User Story 3 - Elegir qué pruebas ver (Priority: P2)

Como bioquímico, elijo qué pruebas se muestran (varias a la vez) para concentrarme en las que me
interesan, por ejemplo Cloruro y Conductividad juntas.

**Why this priority**: Con estudios de muchas pruebas, ver todos los gráficos a la vez dificulta
la revisión.

**Independent Test**: Abrir la comparación de un estudio con 10 pruebas, dejar elegidas solo 2 y
verificar que se muestran solo esos 2 gráficos, y que al volver a abrir el enlace copiado se ven
las mismas 2.

**Acceptance Scenarios**:

1. **Dada** la comparación desde un estudio, **cuando** se abre, **entonces** están elegidas
   todas las pruebas del estudio, en el orden del estudio.
2. **Dada** la comparación desde el dashboard, **cuando** se abre, **entonces** las opciones son
   todas las pruebas con al menos un resultado validado en ese origen (por nombre) y están todas
   elegidas.
3. **Dada** la lista de pruebas, **cuando** se marcan o desmarcan pruebas y se aplica, **entonces**
   se muestran solo las elegidas; hay atajos «Todas» y «Ninguna».
4. **Dada** una selección, **cuando** se copia el enlace de la página, **entonces** al abrirlo se
   ve la misma selección.
5. **Dada** una selección sin ninguna prueba, **cuando** se aplica, **entonces** se indica
   «Elegí al menos una prueba para ver su evolución».
6. **Dado** el selector, **cuando** se usa solo con teclado, **entonces** se pueden marcar las
   pruebas y aplicar sin mouse.

---

### User Story 4 - Consultar un origen desde el dashboard (Priority: P2)

Como bioquímico, desde el Dashboard elijo un cliente y uno de sus orígenes y veo la evolución de
ese origen, sin tener que buscar un estudio.

**Why this priority**: Permite el seguimiento del origen fuera del momento de validar (criterio 1).

**Independent Test**: En el Dashboard, elegir el cliente de «Pozo 2» y el origen «Pozo 2», abrir
la comparación y verificar que muestra los resultados validados de ese origen sin punto destacado.

**Acceptance Scenarios**:

1. **Dado** el Dashboard, **cuando** se muestra, **entonces** tiene una sección «Comparación
   histórica» donde se elige un cliente y luego uno de sus orígenes.
2. **Dado** un cliente elegido, **cuando** se despliegan los orígenes, **entonces** se listan solo
   los de ese cliente, por nombre.
3. **Dados** cliente y origen elegidos, **cuando** se confirma, **entonces** se abre la comparación
   de ese origen, sin estudio de referencia ni punto destacado.
4. **Dado** un origen que no es del cliente elegido (enlace armado a mano), **cuando** se confirma,
   **entonces** se muestra el error junto al campo y no se abre la comparación.
5. **Dado** un origen sin ningún resultado validado, **cuando** se abre la comparación,
   **entonces** indica «Este origen todavía no tiene resultados validados» y ofrece volver.
6. **Dado** un navegador sin JavaScript, **cuando** se elige el cliente, **entonces** igualmente
   se puede elegir el origen (el formulario funciona en dos pasos).

---

### User Story 5 - Leer los datos sin gráfico y en contexto (Priority: P3)

Como bioquímico, puedo leer los datos de cada gráfico en una tabla y entrar a la muestra o estudio
de cada punto, para revisar el detalle de un valor que llama la atención.

**Why this priority**: Accesibilidad (igual que el panel de la US 8.3) y trazabilidad del dato.

**Independent Test**: Abrir «Ver datos» de un gráfico y verificar que la tabla lista fecha de
muestreo, N° PI, valor con unidad, estado de validación y enlace al estudio de cada punto.

**Acceptance Scenarios**:

1. **Dado** cualquier gráfico, **cuando** se abre «Ver datos», **entonces** se ve una tabla con
   fecha de muestreo, N° PI (enlace a la muestra), valor con unidad, evaluación contra el límite y
   si está validado, en el mismo orden del gráfico.
2. **Dado** un navegador sin JavaScript o si los gráficos no cargan, **cuando** se muestra la
   comparación, **entonces** las tablas, la franja del límite y las variaciones se leen igual.
3. **Dado** un resultado por debajo del límite de detección, **cuando** se muestra en la tabla o
   en el gráfico, **entonces** se lee «< LD» como en el informe, y en el gráfico se dibuja en su
   valor.

---

### Edge Cases

- **Fechas iguales**: dos muestras del mismo origen con la misma fecha de muestreo se ordenan por
  N° PI; para la variación, una muestra con la misma fecha y N° PI menor cuenta como anterior.
- **Estudio de referencia antiguo**: si el estudio de referencia no es el más reciente del origen,
  el gráfico muestra también los validados posteriores, pero la variación compara solo contra los
  anteriores a la muestra de referencia.
- **Varios estudios de una misma muestra con la misma prueba**: cada resultado validado es un
  punto propio (mismo N° PI, distinto estudio); en la variación cuentan todos.
- **Otros estudios de la misma muestra**: los validados de la misma muestra que el estudio de
  referencia aparecen en el gráfico pero no cuentan como «anteriores» (no son otro muestreo).
- **Validación anulada**: un resultado cuya validación se anuló (por corrección) no forma parte
  del historial hasta que se vuelva a validar; si es el estudio de referencia, se muestra
  destacado como «Sin validar».
- **Unidad distinta**: si un resultado validado tiene otra unidad que la de referencia (cambio del
  catálogo), aparece en la tabla con el aviso «Otra unidad (…), no se compara» y no entra al
  gráfico ni a la variación.
- **Límites por vertido**: la franja usa los límites aplicables a la muestra de referencia (la del
  estudio o, desde el dashboard, la del resultado más reciente), con su tipo de vertido; se indica
  qué límites se dibujan («Límite general» o el vertido).
- **Límite incompleto o no comparable**: con solo máximo la franja va desde el borde inferior del
  gráfico hasta el máximo; con solo mínimo, desde el mínimo hasta el borde superior; sin límite
  comparable no se dibuja franja y se lee «Sin límite comparable».
- **Pruebas Ausente/Presente**: el gráfico muestra los puntos en dos niveles «Ausente» y
  «Presente» (nunca 0 y 1) y la franja marca «Ausente» como permitido.
- **Pruebas calculadas**: se comparan sus resultados como cualquier otra (p. ej. Cloruro).
- **Prueba quitada del catálogo de un tipo de estudio**: el historial es por prueba, no por tipo
  de estudio; los resultados validados se siguen comparando.
- **Cliente u origen inactivo**: desde un estudio la comparación se abre igual (es historia); en el
  selector del dashboard se ofrecen solo clientes activos.
- **Historial largo**: se muestran todos los resultados validados del origen, sin recortar por
  fecha ni cantidad.
- **Usuario sin acceso**: no ve la acción en el detalle del estudio ni la sección del dashboard, y
  si entra por el enlace recibe «sin permiso».
- **Estudio o origen inexistente**: página «no encontrado».

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema MUST ofrecer una pantalla «Comparación histórica» de un origen, a la que
  se accede desde el detalle de un estudio (con ese estudio como referencia) y desde el Dashboard
  eligiendo cliente y origen (sin estudio de referencia).
- **FR-002**: La comparación MUST mostrar el cliente, el origen y, si hay estudio de referencia,
  su N° PI, tipo de estudio y estado, con un enlace para volver a él.
- **FR-003**: El historial de una prueba MUST incluir solo resultados de esa misma prueba con
  validación vigente, de muestras del mismo origen, excluido el estudio de referencia; sin
  recortar por fecha ni cantidad.
- **FR-004**: El historial MUST ordenarse por fecha de muestreo de la muestra y, a igual fecha, por
  N° PI.
- **FR-005**: Por cada prueba elegida con historial, el sistema MUST mostrar un gráfico de
  evolución con los puntos del historial y, si existe, el resultado del estudio de referencia
  destacado (distinto color y forma) e identificado como «Validado» o «Sin validar».
- **FR-006**: Cada gráfico MUST dibujar la franja del límite permitido según los límites aplicables
  a la muestra de referencia (los del vertido reemplazan a los generales), con la regla de límites
  incompletos y no comparables de los Edge Cases, e indicar los límites usados.
- **FR-007**: Una prueba elegida sin historial MUST mostrar el valor actual (o «Sin resultado en
  este estudio») con «Sin historial para comparar», sin gráfico ni variación.
- **FR-008**: Por cada prueba con un último resultado y al menos un resultado anterior, el sistema
  MUST indicar la variación del último contra el anterior y contra el promedio de todos los
  anteriores, como diferencia en la unidad de la prueba y como porcentaje con un decimal, con
  flecha y signo. «Último» es el resultado del estudio de referencia o, sin él, el validado más
  reciente; «anteriores» son los del historial de muestras previas a la del último (FR-004 y Edge
  Cases).
- **FR-009**: Si el valor contra el que se compara es 0, la variación MUST mostrar la diferencia y
  «sin porcentaje (valor previo 0)» en lugar del porcentaje.
- **FR-010**: Las pruebas Ausente/Presente MUST mostrarse como «Ausente»/«Presente» (nunca 0 y 1)
  y su variación MUST expresarse como cambio de estado y cantidad de Presente entre los anteriores,
  sin porcentajes.
- **FR-011**: Los cálculos de valores, promedios y variaciones MUST hacerse con el valor completo
  del resultado (no el redondeado) y en aritmética decimal exacta; se muestran con hasta 4
  decimales como el resto de los resultados.
- **FR-012**: El usuario MUST poder elegir qué pruebas se muestran (varias a la vez, con atajos
  «Todas» y «Ninguna»); la selección MUST quedar en el enlace de la página. Por defecto se eligen
  todas las pruebas disponibles (FR-013).
- **FR-013**: Las pruebas disponibles MUST ser las del estudio de referencia (en su orden) o, sin
  él, las que tienen al menos un resultado validado en el origen (por nombre).
- **FR-014**: Cada gráfico MUST tener su tabla «Ver datos» con fecha de muestreo, N° PI (enlace a
  la muestra), valor con unidad (con «< LD» cuando corresponda), evaluación contra el límite y
  estado de validación, legible sin JavaScript.
- **FR-015**: El Dashboard MUST incluir un selector de cliente (solo activos) y origen (solo del
  cliente elegido) que funcione también sin JavaScript, y MUST rechazar un origen que no sea del
  cliente con un error junto al campo.
- **FR-016**: La comparación MUST ser de solo lectura: no valida, rechaza ni modifica resultados,
  pruebas, estudios ni informes, y no muestra ningún veredicto automático; solo marca si un valor
  está fuera de la franja del límite.
- **FR-017**: La comparación MUST ser solo para el laboratorio: no aparece en el informe, en su
  PDF, en la impresión ni en el correo al cliente.
- **FR-018**: El acceso MUST requerir el mismo permiso que el Dashboard («ver dashboard»: grupos
  Bioquímicos y Administradores); sin él no se muestran los accesos y la pantalla responde «sin
  permiso».
- **FR-019**: El cálculo del historial y de la variación de una prueba en un origen MUST ser una
  única definición reutilizable, que use la US 8.2 (desvíos), independiente de la pantalla.
- **FR-020**: Un resultado validado con otra unidad que la de referencia MUST listarse en la tabla
  con el aviso «Otra unidad (…), no se compara» y quedar fuera del gráfico y de la variación.

### Key Entities *(include if feature involves data)*

- **Origen**: punto de muestreo de un cliente (US 4.1); agrupa las muestras que se comparan.
- **Muestra**: aporta la fecha de muestreo, el N° PI y el tipo de vertido (para los límites).
- **Resultado / Validación**: el valor calculado de una prueba en un estudio y su validación
  vigente; solo los validados forman el historial.
- **Punto del historial** (derivado, no se guarda): fecha de muestreo, N° PI, estudio, valor,
  unidad, evaluación contra el límite, validado o no, y si es el de referencia.
- **Variación** (derivada, no se guarda): último valor, anterior, promedio de los anteriores,
  diferencias y porcentajes (o cambio de estado para Ausente/Presente).

No se agregan datos nuevos al sistema: todo se deriva de muestras, resultados y validaciones.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Desde el detalle de un estudio, un bioquímico llega a la evolución de sus pruebas en
  1 clic, y desde el Dashboard en 3 interacciones (cliente, origen, confirmar).
- **SC-002**: Con el caso «Pozo 2» de la demo, el desvío de Cloruro (430 contra un historial de
  ~120 y 415) se identifica a simple vista en el gráfico y en la variación, sin abrir otros
  estudios.
- **SC-003**: El 100 % de los valores, promedios y variaciones mostrados coinciden con el cálculo
  manual a partir de los resultados validados (verificado con casos de prueba conocidos).
- **SC-004**: Ningún resultado sin validar distinto del estudio de referencia aparece en ningún
  gráfico, tabla ni variación.
- **SC-005**: La comparación de un origen con 6 meses de historia y 20 pruebas se muestra en menos
  de 2 segundos.
- **SC-006**: Toda la información de los gráficos se puede leer con teclado y lector de pantalla
  mediante las tablas «Ver datos».
- **SC-007**: Abrir la comparación no cambia ningún dato del sistema (verificado comparando el
  estado de resultados, validaciones y estudios antes y después).

## Assumptions

- Los clientes no tienen acceso al sistema; «el cliente no lo ve» significa que no figura en el
  informe, su PDF, la impresión ni el correo (FR-017).
- El público es el mismo del Dashboard (permiso «ver dashboard»); los empleados sin ese permiso
  siguen viendo el detalle del estudio sin la acción nueva.
- «Misma prueba» es la misma prueba del catálogo (mismo código), sin importar el tipo de estudio.
- «Promedio de los anteriores» es el promedio simple de todos los resultados validados anteriores
  a la muestra del último, sin ventana de tiempo.
- La franja se dibuja con los límites de la muestra de referencia aunque muestras anteriores hayan
  tenido otro tipo de vertido; la evaluación de cada punto en la tabla usa la de su validación
  vigente (los límites con que se validó).
- Se reutilizan la librería de gráficos ya incluida para el Dashboard (US 8.3), sus colores y su
  patrón de tabla «Ver datos»; no se agregan dependencias externas.
- El caso «Pozo 2» de la demo (SCRUM-78) alcanza para probar la historia; si hace falta otro caso
  (p. ej. Ausente/Presente), se agrega al guion de la demo.
