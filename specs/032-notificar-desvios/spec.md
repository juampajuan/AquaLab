# Feature Specification: Notificar desvíos relevantes

**Feature Branch**: `032-notificar-desvios`

**Created**: 2026-11-09

**Status**: Draft

**Input**: User description: "US 8.2 (SCRUM-61) – Notificar desvíos relevantes. Como bioquímico quiero recibir un aviso cuando un resultado se aleje del historial de su origen para revisar la medición antes de validar. Criterios: (1) El desvío se detecta cuando se calcula el resultado (al cargar o corregir mediciones); queda marcado en el detalle del estudio y en la pantalla de validación, y aparece en la lista «Desvíos sin revisar» del dashboard, que muestra cuántos hay pendientes. (2) Regla inicial: hay desvío si el resultado difiere más de un 30 % del promedio de los últimos 3 resultados validados de ese origen, para arriba o para abajo; hacen falta al menos 3 resultados previos; el umbral se confirma con el laboratorio y queda configurable en un solo lugar. (3) Cada desvío muestra la muestra, el origen, la prueba, el valor observado y el promedio histórico, con enlaces al estudio y a la comparación histórica de la 8.1. (4) Un desvío se puede marcar como revisado; queda guardado quién y cuándo lo revisó. (5) La advertencia no impide validar ni cambia el resultado. Notas técnicas: reutilizar estudios/comparacion.py de la 8.1 (comparar y variacion) para el historial; si una corrección recalcula el resultado, el desvío se vuelve a evaluar. Diferencial pedido por la profesora: no recortar."

**Ajustes posteriores (2026-11-09, pedidos del usuario)**:

1. Validar una prueba con desvío cuenta como revisarlo; no hay una acción separada de «Marcar como
   revisado». En la pantalla de validación las pruebas con desvío se destacan con el valor, el
   mediana histórica, un enlace a la comparación de la 8.1 y un campo «Observación» opcional. La
   confirmación indica cuántos de los resultados elegidos tienen desvío.
2. El desvío no se guarda: se calcula en el momento, con el historial de la comparación histórica
   (8.1), sobre los resultados calculados y todavía sin validar, cada vez que se muestra el
   detalle del estudio, la pantalla de validación o la lista del dashboard. Al corregir una
   medición, el cálculo usa el valor nuevo sin ningún paso adicional. La revisión queda guardada
   en la validación: quién y cuándo validó, la observación y, como constancia, la mediana y el
   umbral contra los que se comparó si había desvío.
3. La referencia es la **mediana** de los últimos N resultados validados, no el promedio: un pico
   aislado en el historial contamina el promedio (caso de la demo: Detergentes de «Colectora», 4,2
   contra 14 / 4,1 / 4,3 da −43,8 % contra el promedio y −2,3 % contra la mediana). En
   Ausente/Presente no cambia nada.
4. Además del aviso en pantalla, cuando un resultado recién calculado (carga, corrección o
   recálculo de dependientes) queda en desvío, se envía un correo por cada desvío a cada uno de
   los usuarios activos del grupo Bioquímicos (uno por destinatario: nadie ve las direcciones de
   los otros), con la muestra, el cliente, el origen, la prueba, el
   valor observado, la mediana, el porcentaje y un enlace al estudio. No se reenvía si el valor no
   cambió; una falla de envío no afecta la carga.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ver el desvío en el estudio (Priority: P1)

Como bioquímico, cuando un resultado calculado (al cargar o corregir una medición) se aleja más de
lo tolerado del mediana de los últimos resultados validados de ese origen, lo veo marcado como
desvío en el detalle del estudio, con el valor observado, el mediana histórica y la diferencia,
para revisar la medición antes de validarla.

**Why this priority**: Es el núcleo de la historia: sin la detección y la marca no hay aviso.

**Independent Test**: Con un origen con Cloruro validado 100, 110 y 120 mg/l en tres muestras
anteriores, cargar en un estudio nuevo de ese origen una medición que dé 160 mg/l y verificar que el
detalle del estudio marca Cloruro como desvío con «Observado 160 mg/l · Mediana de los últimos 3:
110 mg/l · ▲ +50 mg/l (+45,5 %)»; corregir la medición para que dé 115 y verificar que la marca
desaparece.

**Acceptance Scenarios**:

1. **Dado** un origen con al menos 3 resultados validados anteriores de una prueba, **cuando** un
   estudio de ese origen tiene un resultado calculado sin validar que difiere del mediana de los
   últimos 3 en más del umbral (30 %), para arriba o para abajo, **entonces** el detalle del
   estudio muestra la marca «Desvío» en la fila de la prueba.
2. **Dado** el mismo historial (mediana 110), **cuando** el resultado es 143 (+30,0 %) o 77
   (−30,0 %), **entonces** no hay desvío (el umbral es «más de»); con 143,5 o 76,9 sí lo hay.
3. **Dado** un origen con solo 2 resultados validados anteriores de la prueba, **cuando** el
   resultado es muy distinto, **entonces** no hay desvío ni marca.
4. **Dado** un origen con 5 resultados validados anteriores (50, 60, 100, 110, 120), **cuando** se
   evalúa un resultado, **entonces** la mediana usada es la de los 3 más recientes por fecha de
   muestreo (110), no el de todos.
5. **Dada** una prueba calculada que depende de otras (p. ej. un cociente de dos mediciones),
   **cuando** tiene resultado, **entonces** también se evalúa como desvío.
6. **Dado** un resultado con desvío, **cuando** se corrige la medición y el nuevo resultado queda
   dentro del umbral, **entonces** la marca desaparece; si una corrección deja fuera del umbral un
   resultado que no lo estaba, aparece la marca. Si se borra la medición, no hay resultado ni
   marca.
7. **Dado** un resultado validado que tenía desvío al validarse, **cuando** se muestra el detalle,
   **entonces** la fila indica «Desvío revisado» con quién y cuándo lo validó, la observación y la
   mediana y el umbral con que se comparó.
8. **Dado** un desvío, **cuando** se muestra en cualquier pantalla, **entonces** se identifica
   con texto e ícono (no solo con color) y ofrece el enlace «Comparación histórica» a quien tiene
   acceso a ella.

---

### User Story 2 - Ver los desvíos pendientes en el dashboard (Priority: P1)

Como bioquímico, en el Dashboard veo la lista «Desvíos sin revisar» con cuántos hay pendientes y,
para cada uno, la muestra, el origen, la prueba, el valor observado y el mediana histórica, con
enlaces al estudio, a la comparación histórica y a la validación, para no depender de abrir
estudio por estudio.

**Why this priority**: Es la «notificación» propiamente dicha: el lugar donde el laboratorio se
entera de todos los desvíos abiertos.

**Independent Test**: Con la demo cargada, abrir el Dashboard y verificar que «Desvíos sin
revisar» indica la cantidad pendiente e incluye Cloruro de «Pozo 2» (430 mg/l) con sus enlaces;
seguir el enlace a la comparación y verificar que abre la de ese estudio.

**Acceptance Scenarios**:

1. **Dado** el Dashboard, **cuando** se muestra, **entonces** tiene la sección «Desvíos sin
   revisar» con la cantidad total pendiente bien visible (p. ej. «3 pendientes»): todos los
   resultados calculados y sin validar que tienen desvío en ese momento.
2. **Dados** desvíos sin revisar, **cuando** se lista la sección, **entonces** cada fila muestra
   el N° PI de la muestra (enlace a la muestra), el cliente y el origen, la prueba, el valor
   observado con unidad, el mediana histórica con unidad, la diferencia en porcentaje con flecha
   y signo y la fecha del cálculo del resultado, con enlaces «Ver estudio», «Comparación
   histórica» (la de la US 8.1 con ese estudio como referencia y esa prueba elegida) y, para quien
   puede validar, «Validar» (la pantalla de validación del estudio).
3. **Dados** más desvíos pendientes que los que entran en el panel, **cuando** se muestra,
   **entonces** el panel lista los 10 más recientes y ofrece «Ver todos», que abre la lista
   completa paginada con los mismos datos.
4. **Dado** que no hay desvíos pendientes, **cuando** se muestra el Dashboard, **entonces** la
   sección indica «No hay desvíos sin revisar».
5. **Dado** el filtro de período del Dashboard, **cuando** se cambia, **entonces** la lista de
   desvíos no cambia: muestra todos los pendientes.
6. **Dado** el Dashboard o la lista completa, **cuando** se ordenan los desvíos, **entonces** van
   del resultado calculado más recientemente al más antiguo.
7. **Dado** un desvío pendiente, **cuando** se corrige la medición y queda dentro del umbral o se
   valida el resultado, **entonces** deja de figurar en la lista.

---

### User Story 3 - Revisar el desvío al validar (Priority: P1)

Como bioquímico, en la pantalla de validación veo destacadas las pruebas con desvío, con el valor
observado, el mediana histórica y un enlace a la comparación histórica, y puedo escribir una
observación (p. ej. «Se repitió la medición, el valor es correcto»). Al validar una de esas
pruebas, queda constancia en la validación de quién y cuándo la revisó, la observación y la
mediana y el umbral con que se comparó, y sale de la lista de pendientes.

**Why this priority**: Cierra el circuito del aviso (criterio 4) en el momento natural en que el
bioquímico decide sobre el resultado, sin un paso aparte.

**Independent Test**: Abrir la validación del estudio de «Pozo 2», ver Cloruro destacado con 430
mg/l y la mediana, escribir una observación, validarlo y confirmar; verificar que el contador del
dashboard baja en 1 y que el estudio muestra «Desvío revisado · Validado por Bioquímica Demo el
09/11/2026 14:30 – Se repitió la medición · mediana 124 mg/l, umbral 30 %».

**Acceptance Scenarios**:

1. **Dado** un estudio con resultados sin validar con desvío, **cuando** se abre la pantalla de
   validación, **entonces** esas pruebas se destacan (texto + ícono) con el valor observado, el
   mediana de los últimos N, la diferencia (cantidad y porcentaje con flecha y signo), un enlace
   «Comparación histórica» y un campo «Observación» opcional; un resumen arriba indica cuántas
   tienen desvío («2 pruebas con desvío»). Las demás no tienen el campo; las que no tienen
   historial suficiente indican «Historial insuficiente para detectar desvíos».
2. **Dados** resultados elegidos para validar, **cuando** se pasa a la confirmación, **entonces**
   la confirmación indica cuántos de los elegidos tienen desvío («2 de los 5 resultados elegidos
   tienen desvío: quedarán revisados al validar»), con la prueba y la observación escrita de cada
   uno.
3. **Dada** la confirmación, **cuando** se valida, **entonces** cada validación de una prueba con
   desvío guarda la observación y la mediana y el umbral con que se comparó en ese momento; quién
   y cuándo son los de la validación. Si la validación no se aplica (se omite, se rechaza o
   falla), no queda nada guardado.
4. **Dada** una prueba con desvío que no se elige para validar, **cuando** se validan las demás,
   **entonces** sigue pendiente y su observación no se guarda.
5. **Dada** una observación de más de 500 caracteres, **cuando** se pasa a la confirmación,
   **entonces** se muestra el error junto al campo y no se avanza.
6. **Dada** una validación con desvío, **cuando** se la consulta después, **entonces** la
   constancia no cambia aunque el historial del origen o la configuración cambien.
7. **Dado** un resultado validado con desvío que se corrige, **cuando** pierde su validación,
   **entonces** vuelve a evaluarse con el valor nuevo y, si sigue con desvío, vuelve a figurar
   como pendiente; la validación anulada conserva su constancia.
8. **Dado** un usuario sin permiso para validar, **cuando** ve un desvío, **entonces** no ve la
   acción «Validar» en el dashboard y no puede revisarlo.

---

### User Story 4 - La advertencia no bloquea (Priority: P2)

Como bioquímico, puedo validar un resultado con desvío sin que el sistema me lo impida ni cambie el
valor: el aviso es informativo y la observación es opcional.

**Why this priority**: Criterio 5; la decisión profesional queda en el bioquímico.

**Independent Test**: Validar Cloruro de «Pozo 2» sin escribir observación y verificar que se
valida igual, con el mismo valor, y que la validación guarda la constancia del desvío con la
observación vacía.

**Acceptance Scenarios**:

1. **Dado** un resultado con desvío, **cuando** se valida sin observación, **entonces** la
   validación se registra igual que sin desvío, el resultado no cambia y queda la constancia.
2. **Dado** cualquier desvío, **cuando** se calcula o se muestra, **entonces** no cambia ningún
   dato: ni el resultado, ni el estado de la prueba o del estudio, ni las validaciones.
3. **Dado** un estudio con desvíos, **cuando** se emite el informe, **entonces** el informe, su
   PDF, la impresión y el correo al cliente no mencionan desvíos ni observaciones de revisión.

---

### User Story 5 - Ajustar la regla con el laboratorio (Priority: P3)

Como responsable del sistema, puedo cambiar el umbral (30 %) y la cantidad de resultados previos
(3) en un único lugar de la configuración, para ajustarlos cuando el laboratorio los confirme, sin
tocar el resto del sistema.

**Why this priority**: El umbral es provisorio (criterio 2), pero el valor inicial ya es usable.

**Independent Test**: Cambiar el umbral a 50 % y verificar que un resultado sin validar de +45,5 %
deja de figurar como desvío, mientras que una validación hecha antes con desvío sigue mostrando
«umbral 30 %».

**Acceptance Scenarios**:

1. **Dada** la configuración con umbral U y cantidad N, **cuando** se evalúa un resultado,
   **entonces** se usan U y N, y no hay otro lugar del sistema donde estén escritos.
2. **Dado** un cambio de configuración, **cuando** se muestran los pendientes, **entonces** se
   evalúan con la regla nueva; las validaciones ya hechas conservan el umbral con que se
   compararon.
3. **Dado** el texto de ayuda de las pantallas, **cuando** se muestra la regla, **entonces** se lee
   con los valores vigentes («más de un 30 % respecto del mediana de los últimos 3 resultados
   validados del origen»).

---

### User Story 6 - Recibir el aviso por correo (Priority: P2)

Como bioquímico, cuando se calcula un resultado que queda en desvío recibo un correo con los datos
del desvío y un enlace al estudio, para enterarme aunque no esté mirando el dashboard.

**Why this priority**: Es la «notificación» fuera de la pantalla; el aviso en el sistema (US 1 a
US 3) ya cubre la revisión.

**Independent Test**: Con Cloruro validado 100, 110 y 120 mg/l en el origen, cargar 16 (→ 160) en
un estudio nuevo y verificar que cada bioquímico activo recibe un correo con N° PI, cliente,
origen, «Cloruro (CL-)», «Observado: 160 mg/l», «Mediana de los últimos 3: 110 mg/l», «+45,5 %» y
el enlace absoluto al estudio; corregir a 11,5 (sin desvío) y verificar que no llega otro.

**Acceptance Scenarios**:

1. **Dado** un resultado recién calculado (carga, corrección o recálculo de una prueba que
   depende de otra) que queda en desvío, **cuando** la operación se guarda, **entonces** se envía
   un correo por ese desvío a cada usuario activo del grupo Bioquímicos, con él como único
   destinatario.
2. **Dada** una carga que deja dos pruebas en desvío, **cuando** se guarda, **entonces** salen dos
   correos por bioquímico activo, uno por desvío.
3. **Dado** el correo, **cuando** se lee, **entonces** incluye N° PI de la muestra, cliente,
   origen, prueba (nombre y código), valor observado, mediana de los últimos N (o el estado de los
   últimos N en Ausente/Presente), porcentaje con signo y un enlace absoluto al detalle del
   estudio, y no incluye la observación ni datos de otros estudios.
4. **Dado** un resultado sin desvío, con historial insuficiente o cuyo valor no cambió en el
   recálculo, **cuando** se guarda, **entonces** no se envía correo.
5. **Dada** una corrección que cambia el valor y sigue en desvío, **cuando** se guarda,
   **entonces** se envía un correo nuevo con el valor nuevo.
6. **Dada** una operación que se rechaza o falla después de calcular, **cuando** se deshace,
   **entonces** no se envía ningún correo.
7. **Dado** un error del servidor de correo, **cuando** se intenta enviar, **entonces** la falla
   queda registrada en el log y la carga o corrección queda guardada igual, sin mensaje de error.
8. **Dados** bioquímicos inactivos o usuarios de otros grupos, **cuando** se envía el aviso,
   **entonces** no lo reciben; sin ningún bioquímico activo, no se envía y queda una advertencia
   en el log.

---

### Edge Cases

- **Historial**: «resultados validados anteriores» son los del historial de la comparación
  histórica (US 8.1): resultados con validación vigente de la misma prueba, de muestras del mismo
  origen anteriores a la del estudio (por fecha de muestreo y, a igual fecha, N° PI), con la misma
  unidad; excluye otros estudios de la misma muestra. Los «últimos 3» son los 3 más recientes de
  ese orden.
- **El historial cambia**: como el desvío se calcula en el momento, si se validan o se anulan
  otros resultados del origen, la evaluación de los pendientes puede cambiar; lo guardado en una
  validación no cambia.
- **Validación anulada**: un resultado previo cuya validación se anuló no cuenta hasta volver a
  validarse.
- **Estudio de una muestra antigua**: si un estudio es de una muestra anterior a otras ya
  validadas del origen, se compara solo contra las muestras anteriores a la suya.
- **Pico aislado en el historial**: un valor anómalo entre los últimos N no mueve la referencia
  (p. ej. 14 / 4,1 / 4,3 → mediana 4,3: un 4,2 no es desvío).
- **N par**: si la cantidad configurada es par, la mediana es el promedio de los dos valores
  centrales.
- **Mediana 0**: si la mediana de los previos es 0 y el resultado es distinto de 0, hay desvío y
  se muestra «sin porcentaje (mediana previa 0)»; si el resultado también es 0, no hay desvío.
- **Pruebas Ausente/Presente**: no se usan porcentajes. Hay desvío si el resultado es distinto del
  de los últimos 3 validados cuando estos coinciden entre sí (los 3 Ausente y el actual Presente, o
  al revés); si los 3 no coinciden no hay desvío. Se muestra «Presente (los últimos 3: Ausente)»,
  nunca 0 y 1.
- **Resultado por debajo del límite de detección**: se compara con su valor completo, como en la
  US 8.1, y se muestra «< LD».
- **Varias pruebas con desvío en el mismo estudio**: cada una es una fila propia en la lista y
  tiene su propia observación en la validación.
- **Resultados sin calcular**: una prueba sin resultado (pendiente o con fórmula que no se pudo
  calcular) no se evalúa.
- **Desvío que aparece o desaparece mientras se valida**: lo que queda guardado es la evaluación
  hecha al confirmar la validación, con el historial de ese momento.
- **Concurrencia**: dos bioquímicos que validan la misma prueba a la vez dejan una sola validación;
  el segundo recibe «ya estaba validada» y su observación no se guarda.
- **Estudio con informe emitido**: todas sus pruebas están validadas; no tiene pendientes.
- **Cliente u origen inactivo**: los desvíos se siguen mostrando y se revisan al validar igual.
- **Correo y validación**: validar no recalcula el resultado, así que no envía correos; el aviso es
  solo para resultados recién calculados.
- **Demo**: la carga de la demo usa los servicios reales, así que también genera los correos de
  sus desvíos (en desarrollo salen por la consola).
- **Usuario sin acceso al dashboard**: no ve la sección ni la lista completa («sin permiso» si
  entra por el enlace); en el estudio igual ve la marca de desvío.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema MUST evaluar el desvío en el momento de mostrar cada resultado calculado y
  sin validar (detalle del estudio, pantalla de validación y lista de pendientes), con su valor
  actual; no guarda desvíos. Una carga o corrección se refleja sin pasos adicionales.
- **FR-002**: Hay desvío si, con al menos N resultados validados anteriores de la prueba en el
  origen (Edge Cases, «Historial»), el resultado difiere de la mediana de los últimos N en más de U
  por ciento de la mediana, en cualquier sentido. Valores iniciales: U = 30 %, N = 3. La comparación
  usa valores completos y aritmética decimal exacta; un porcentaje exactamente igual a U no es
  desvío.
- **FR-003**: U y N MUST definirse en un único lugar de la configuración del sistema; el historial
  MUST obtenerse con la misma definición de historial de la comparación histórica (US 8.1), sin
  una segunda implementación; la mediana se calcula sobre los últimos N de ese historial.
- **FR-004**: Con menos de N resultados previos o sin resultado no hay desvío; la pantalla de
  validación indica «Historial insuficiente para detectar desvíos» cuando falta historial.
- **FR-005**: El detalle del estudio MUST marcar cada prueba sin validar con desvío (texto +
  ícono), con el valor observado, el mediana de los últimos N, la diferencia (cantidad y
  porcentaje con flecha y signo) y un enlace a la comparación histórica; y cada prueba validada con
  desvío como «Desvío revisado», con quién, cuándo, la observación, la mediana y el umbral
  guardados.
- **FR-006**: El Dashboard MUST mostrar la sección «Desvíos sin revisar» con la cantidad total de
  resultados sin validar con desvío y los 10 calculados más recientemente, y un enlace «Ver todos»
  a una lista completa paginada. Ambas MUST mostrar por desvío: N° PI (enlace a la muestra),
  cliente, origen, prueba, valor observado y mediana con unidad, porcentaje, fecha del cálculo y
  los enlaces «Ver estudio», «Comparación histórica» (estudio de referencia y prueba elegida) y,
  con permiso de validar, «Validar». La lista no depende del período elegido en el Dashboard.
- **FR-007**: La pantalla de validación MUST destacar cada prueba con desvío con el valor
  observado, el mediana histórica, la diferencia, un enlace a la comparación histórica y un campo
  «Observación» opcional de hasta 500 caracteres, y MUST resumir cuántas pruebas mostradas tienen
  desvío. No hay otra acción para revisar un desvío.
- **FR-008**: La confirmación de la validación MUST indicar cuántos de los resultados elegidos
  tienen desvío, con la prueba y la observación de cada uno, sin impedir confirmar.
- **FR-009**: Al validar una prueba, el sistema MUST volver a evaluar el desvío en la misma
  operación y, si lo hay, guardar en la validación la observación, la mediana y el umbral usados;
  quién y cuándo revisó son los de la validación. Si la validación de esa prueba se omite, se
  rechaza o falla, no se guarda nada. Lo guardado es inalterable.
- **FR-010**: Revisar MUST requerir el mismo permiso que validar resultados (grupo Bioquímicos); la
  sección y la lista completa del Dashboard MUST requerir el permiso del Dashboard. Sin permiso no
  se muestran las acciones y el pedido responde «sin permiso».
- **FR-011**: Los desvíos MUST ser solo informativos: no impiden validar ni emitir el informe, la
  observación es opcional y calcularlos no cambia ningún dato.
- **FR-012**: Los desvíos y las observaciones MUST ser solo para el laboratorio: no aparecen en el
  informe, su PDF, la impresión ni el correo al cliente.
- **FR-013**: Las pruebas Ausente/Presente MUST evaluarse por cambio de estado (Edge Cases) y
  mostrarse como «Ausente»/«Presente».
- **FR-014**: Con mediana previa 0 MUST aplicarse la regla de Edge Cases («Mediana 0»).
- **FR-015**: La demo del laboratorio MUST incluir el desvío de Cloruro de «Pozo 2» como pendiente
  y al menos una validación con desvío y observación, para mostrar la historia.
- **FR-016**: Cuando una carga, corrección o recálculo de dependientes deja un resultado nuevo o
  con un valor distinto en desvío, el sistema MUST enviar un correo por cada desvío y por cada
  usuario activo del grupo Bioquímicos, con ese usuario como único destinatario (sin copias ni
  otras direcciones visibles); si el valor no cambió, MUST NOT reenviarlo. Una falla con un
  destinatario MUST NOT impedir el envío a los demás.
- **FR-017**: El correo MUST incluir N° PI, cliente, origen, prueba, valor observado, mediana de
  los últimos N, porcentaje y un enlace absoluto al detalle del estudio, armado con una dirección
  base configurable del sistema.
- **FR-018**: El correo MUST enviarse solo después de que la operación quede guardada; si la
  operación se deshace, MUST NOT enviarse.
- **FR-019**: Una falla de envío MUST quedar registrada en el log y MUST NOT afectar la operación
  ni mostrar un error al usuario.
- **FR-020**: Los correos de desvíos MUST ir solo a usuarios del laboratorio (grupo Bioquímicos),
  nunca al cliente.

### Key Entities *(include if feature involves data)*

- **Desvío** (derivado, no se guarda): resultado sin validar, valor observado, mediana de los
  últimos N validados, diferencia y porcentaje (o cambio de estado en Ausente/Presente), y los
  resultados previos usados.
- **Validación** (existente, se amplía): además de quién, cuándo y la evaluación contra límites,
  guarda la observación opcional y, si había desvío al validar, la mediana y el umbral contra los
  que se comparó.
- **Regla de desvío** (configuración): umbral porcentual y cantidad de resultados previos.
- Reutiliza **Resultado**, **Muestra** y **Origen**, y el historial y la variación de la
  comparación histórica (US 8.1).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: El 100 % de los resultados sin validar con al menos N previos que superan el umbral
  se muestran como desvío, y ninguno dentro del umbral (verificado con casos conocidos en los
  bordes: exactamente 30 %, apenas más, mediana 0, Ausente/Presente).
- **SC-002**: Desde el Dashboard, un bioquímico llega a la comparación histórica de un desvío
  pendiente en 1 clic y a la validación que lo revisa en 1 clic.
- **SC-003**: Tras una corrección, el detalle, la validación y la lista reflejan el nuevo resultado
  en la siguiente vista, sin pasos adicionales.
- **SC-004**: El 100 % de las validaciones de resultados con desvío guardan la observación, la
  mediana y el umbral, y esa constancia no cambia después.
- **SC-005**: Validar y emitir informes funciona igual con o sin desvíos (0 operaciones bloqueadas
  por un desvío) y ningún informe, PDF ni correo menciona desvíos.
- **SC-006**: Cambiar el umbral requiere modificar un solo valor de configuración.
- **SC-007**: El detalle y la validación de un estudio de 20 pruebas con 6 meses de historia, y el
  Dashboard con la sección de desvíos, se muestran en menos de 2 segundos.
- **SC-008**: El 100 % de los resultados recién calculados en desvío generan exactamente un correo
  por desvío a cada bioquímico activo, y ninguna operación deshecha ni recálculo con el mismo valor
  genera correos.

## Assumptions

- «Notificar» es avisar dentro del sistema (marca en el estudio, en la validación y lista del
  Dashboard) y, desde el ajuste 4, por correo a los bioquímicos activos al calcularse un resultado
  en desvío. El correo no reemplaza la revisión: el desvío se revisa al validar.
- La dirección base de los enlaces del correo se configura en el sistema (en desarrollo,
  `http://localhost:8000`), porque el cálculo no ocurre dentro de un pedido web.
- «El desvío se detecta cuando se calcula el resultado» se cumple porque la evaluación usa siempre
  el resultado vigente: aparece en cuanto el resultado existe y se actualiza con cada corrección.
- Los «últimos 3 resultados validados» se toman del mismo historial que la comparación histórica
  (US 8.1); la mediana de la 8.2 usa solo los últimos N, mientras que la 8.1 sigue mostrando el de
  todos.
- El porcentaje se calcula sobre la mediana (|resultado − mediana| / mediana) y se muestra con
  un decimal, como en la US 8.1; la decisión de desvío usa el valor exacto, no el redondeado.
- «Marcar como revisado» (criterio 4) se cumple al validar: quien valida una prueba con desvío lo
  revisó en esa pantalla, donde vio el valor, la mediana y el enlace a la comparación. Por eso la
  revisión usa el permiso de validar; los Administradores con permiso de Dashboard ven la lista
  pero no revisan salvo que también sean Bioquímicos.
- La «fecha» de un desvío pendiente es la del último cálculo de su resultado.
- El umbral y la cantidad se cambian en la configuración del sistema (no desde una pantalla); el
  laboratorio confirma el 30 % antes de la entrega final.
- La demo de SCRUM-78 valida con observación el Cloruro de «Pozo 2» del mes anterior (validación
  con desvío) y deja sin validar el del mes actual (desvío pendiente).
- Se reutilizan los componentes de pantalla existentes (tablas, badges, mensajes, ayuda) y el
  Dashboard de la US 8.3; no se agregan dependencias.
