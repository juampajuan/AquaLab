# Feature Specification: Notificar desvíos relevantes

**Feature Branch**: `032-notificar-desvios`

**Created**: 2026-11-09

**Status**: Draft

**Input**: User description: "US 8.2 (SCRUM-61) – Notificar desvíos relevantes. Como bioquímico quiero recibir un aviso cuando un resultado se aleje del historial de su origen para revisar la medición antes de validar. Criterios: (1) El desvío se detecta cuando se calcula el resultado (al cargar o corregir mediciones); queda marcado en el detalle del estudio y en la pantalla de validación, y aparece en la lista «Desvíos sin revisar» del dashboard, que muestra cuántos hay pendientes. (2) Regla inicial: hay desvío si el resultado difiere más de un 30 % del promedio de los últimos 3 resultados validados de ese origen, para arriba o para abajo; hacen falta al menos 3 resultados previos; el umbral se confirma con el laboratorio y queda configurable en un solo lugar. (3) Cada desvío muestra la muestra, el origen, la prueba, el valor observado y el promedio histórico, con enlaces al estudio y a la comparación histórica de la 8.1. (4) Un desvío se puede marcar como revisado; queda guardado quién y cuándo lo revisó. (5) La advertencia no impide validar ni cambia el resultado. Notas técnicas: reutilizar estudios/comparacion.py de la 8.1 (comparar y variacion) para el historial; si una corrección recalcula el resultado, el desvío se vuelve a evaluar. Diferencial pedido por la profesora: no recortar."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Enterarse del desvío en el momento de cargar o corregir (Priority: P1)

Como bioquímico, cuando se carga o se corrige una medición y el resultado calculado se aleja más
de lo tolerado del promedio de los últimos resultados validados de ese origen, el sistema registra
un desvío y lo veo marcado en el detalle del estudio y en la pantalla de validación, con el valor
observado, el promedio histórico y la diferencia, para revisar la medición antes de validarla.

**Why this priority**: Es el núcleo de la historia: sin la detección y la marca no hay aviso.

**Independent Test**: Con un origen con Cloruro validado 100, 110 y 120 mg/l en tres muestras
anteriores, cargar en un estudio nuevo de ese origen una medición que dé 160 mg/l (promedio 110,
+45,5 %) y verificar que el detalle del estudio y la pantalla de validación marcan Cloruro como
desvío con «Observado 160 mg/l · Promedio de los últimos 3: 110 mg/l · +50 mg/l (+45,5 %)».

**Acceptance Scenarios**:

1. **Dado** un origen con al menos 3 resultados validados anteriores de una prueba, **cuando** se
   carga una medición y el resultado calculado difiere del promedio de los últimos 3 en más del
   umbral (30 %), para arriba o para abajo, **entonces** se registra un desvío para esa prueba del
   estudio y el estudio muestra la marca «Desvío» en la fila de la prueba.
2. **Dado** el mismo historial (promedio 110), **cuando** el resultado es 143 (+30,0 %) o 77
   (−30,0 %), **entonces** no hay desvío (el umbral es «más de»); con 143,5 o 76,9 sí lo hay.
3. **Dado** un origen con solo 2 resultados validados anteriores de la prueba, **cuando** se
   calcula un resultado muy distinto, **entonces** no se registra desvío y el estudio no muestra
   marca (la prueba indica «Historial insuficiente para detectar desvíos» en la pantalla de
   validación).
4. **Dado** un origen con 5 resultados validados anteriores (50, 60, 100, 110, 120), **cuando** se
   evalúa un resultado, **entonces** el promedio usado es el de los 3 más recientes por fecha de
   muestreo (110), no el de todos.
5. **Dada** una prueba calculada que depende de la medida cargada (p. ej. Cloruro a partir de su
   medición, u otra prueba con fórmula que la referencia), **cuando** el cálculo produce su
   resultado, **entonces** también se evalúa como desvío.
6. **Dado** un estudio con desvíos, **cuando** se abre la pantalla de validación, **entonces** cada
   prueba con desvío muestra la advertencia con el valor observado, el promedio histórico, la
   diferencia y un enlace a la comparación histórica, y un resumen arriba indica cuántos desvíos
   tiene el estudio («2 pruebas con desvío»).
7. **Dado** un desvío, **cuando** se muestra en cualquier pantalla, **entonces** se identifica
   con texto e ícono (no solo con color).

---

### User Story 2 - Volver a evaluar al corregir o borrar (Priority: P1)

Como bioquímico, si una medición se corrige o se borra, el desvío se vuelve a evaluar con el nuevo
resultado: desaparece si el valor corregido ya no se aleja, se actualiza si sigue alejándose, y
queda registro de lo que pasó.

**Why this priority**: Un desvío suele deberse a un error de carga; la corrección es su resolución
natural y no puede dejar avisos falsos ni perder avisos verdaderos.

**Independent Test**: Con el desvío de 160 del US 1, corregir la medición para que dé 115 y
verificar que el estudio deja de mostrar el desvío y que la lista del dashboard ya no lo cuenta;
volver a corregir a 200 y verificar que aparece un desvío nuevo, sin revisar.

**Acceptance Scenarios**:

1. **Dado** un desvío sin revisar, **cuando** se corrige la medición y el nuevo resultado queda
   dentro del umbral, **entonces** el desvío deja de estar vigente («Resuelto por corrección»), no
   se muestra en el estudio ni en la lista de pendientes y queda en el historial de desvíos del
   estudio.
2. **Dado** un desvío (revisado o no), **cuando** se corrige la medición y el nuevo resultado
   sigue fuera del umbral, **entonces** el desvío anterior deja de estar vigente y se registra uno
   nuevo, sin revisar, con el nuevo valor: la revisión anterior se refería a otro valor.
3. **Dada** una prueba sin desvío, **cuando** una corrección la deja fuera del umbral, **entonces**
   se registra un desvío nuevo.
4. **Dada** una corrección que recalcula pruebas dependientes, **cuando** cambian sus resultados,
   **entonces** cada prueba recalculada se vuelve a evaluar; las que no cambiaron conservan su
   desvío tal como estaba.
5. **Dada** una medición con desvío, **cuando** se borra la medición (o queda sin resultado una
   prueba dependiente), **entonces** el desvío deja de estar vigente («Sin resultado»).
6. **Dada** una corrección rechazada (p. ej. el estudio ya tiene informe emitido o la medición
   cambió mientras se editaba), **cuando** no se aplica, **entonces** los desvíos quedan como
   estaban.

---

### User Story 3 - Ver los desvíos pendientes en el dashboard (Priority: P1)

Como bioquímico, en el Dashboard veo la lista «Desvíos sin revisar» con cuántos hay pendientes y,
para cada uno, la muestra, el origen, la prueba, el valor observado y el promedio histórico, con
enlaces al estudio y a la comparación histórica, para no depender de abrir estudio por estudio.

**Why this priority**: Es la «notificación» propiamente dicha: el lugar donde el laboratorio se
entera de todos los desvíos abiertos.

**Independent Test**: Con la demo cargada, abrir el Dashboard y verificar que «Desvíos sin
revisar» indica la cantidad pendiente e incluye Cloruro de «Pozo 2» (430 mg/l) con sus enlaces;
seguir el enlace a la comparación y verificar que abre la de ese estudio.

**Acceptance Scenarios**:

1. **Dado** el Dashboard, **cuando** se muestra, **entonces** tiene la sección «Desvíos sin
   revisar» con la cantidad total pendiente bien visible (p. ej. «3 pendientes»).
2. **Dados** desvíos sin revisar, **cuando** se lista la sección, **entonces** cada fila muestra
   el N° PI de la muestra (enlace a la muestra), el cliente y el origen, la prueba, el valor
   observado con unidad, el promedio histórico con unidad, la diferencia en porcentaje con flecha
   y signo, la fecha de detección y si el resultado ya fue validado, con enlaces «Ver estudio» y
   «Comparación histórica» (la de la US 8.1 con ese estudio como referencia y esa prueba elegida).
3. **Dados** más desvíos pendientes que los que entran en el panel, **cuando** se muestra,
   **entonces** el panel lista los 10 más recientes y ofrece «Ver todos», que abre la lista
   completa paginada con los mismos datos.
4. **Dado** que no hay desvíos pendientes, **cuando** se muestra el Dashboard, **entonces** la
   sección indica «No hay desvíos sin revisar».
5. **Dado** el filtro de período del Dashboard, **cuando** se cambia, **entonces** la lista de
   desvíos no cambia: muestra todos los pendientes, sin importar cuándo se detectaron.
6. **Dado** el Dashboard o la lista completa, **cuando** se ordenan los desvíos, **entonces** van
   del detectado más recientemente al más antiguo.

---

### User Story 4 - Marcar un desvío como revisado (Priority: P2)

Como bioquímico, después de revisar la medición marco el desvío como revisado (con una observación
opcional, p. ej. «Se repitió la medición, el valor es correcto»); el sistema guarda quién y cuándo
lo revisó, y el desvío sale de la lista de pendientes.

**Why this priority**: Cierra el circuito del aviso (criterio 4) y evita que la lista crezca sin
control.

**Independent Test**: Marcar como revisado el desvío de Cloruro de «Pozo 2» con una observación,
confirmar, y verificar que el contador del dashboard baja en 1 y que el estudio muestra «Revisado
por Bioquímica Demo el 09/11/2026 14:30 – Se repitió la medición».

**Acceptance Scenarios**:

1. **Dado** un desvío sin revisar, **cuando** un usuario con permiso elige «Marcar como revisado»
   (desde el detalle del estudio, la pantalla de validación o la lista de desvíos), **entonces** se
   le pide confirmación mostrando la prueba, el valor observado y el promedio, con un campo de
   observación opcional.
2. **Dada** la confirmación, **cuando** se acepta, **entonces** el desvío queda revisado con el
   usuario, la fecha y hora y la observación; sale de «Desvíos sin revisar» y se muestra un mensaje
   de éxito.
3. **Dado** un desvío revisado, **cuando** se muestra en el estudio o en la validación, **entonces**
   sigue visible como «Desvío revisado» con quién, cuándo y la observación (sin la advertencia
   destacada).
4. **Dado** un desvío que ya fue revisado por otra persona o que dejó de estar vigente por una
   corrección mientras se confirmaba, **cuando** se confirma, **entonces** no se modifica y se
   informa «El desvío ya estaba revisado» o «El desvío ya no está vigente (el resultado cambió)».
5. **Dada** una observación de más de 500 caracteres, **cuando** se confirma, **entonces** se
   muestra el error junto al campo.
6. **Dado** un usuario sin permiso para revisar, **cuando** ve un desvío, **entonces** no ve la
   acción «Marcar como revisado» y si envía el pedido igual recibe «sin permiso».
7. **Dado** un desvío revisado, **cuando** se lo intenta modificar o borrar, **entonces** no es
   posible: la revisión es inalterable (solo una corrección del resultado genera un desvío nuevo).

---

### User Story 5 - La advertencia no bloquea (Priority: P2)

Como bioquímico, puedo validar un resultado con desvío (revisado o no) sin que el sistema me lo
impida ni cambie el valor: el aviso es informativo.

**Why this priority**: Criterio 5; la decisión profesional queda en el bioquímico.

**Independent Test**: Validar Cloruro de «Pozo 2» con el desvío sin revisar y verificar que se
valida igual, con el mismo valor, y que el desvío sigue en la lista como pendiente.

**Acceptance Scenarios**:

1. **Dado** un resultado con desvío sin revisar, **cuando** se valida, **entonces** la validación
   se registra igual que sin desvío y el resultado no cambia.
2. **Dado** un resultado con desvío sin revisar, **cuando** se valida, **entonces** el desvío
   sigue sin revisar (validar no equivale a revisar) y en la lista figura como «Validado».
3. **Dado** cualquier desvío, **cuando** se registra, revisa o deja de estar vigente, **entonces**
   no cambia el estado de la prueba, del estudio ni de su validación.
4. **Dado** un estudio con desvíos, **cuando** se emite el informe, **entonces** el informe, su
   PDF, la impresión y el correo al cliente no mencionan desvíos.
5. **Dado** un estudio con desvíos sin revisar, **cuando** se abre el control previo al informe,
   **entonces** se indica «Tiene N desvíos sin revisar» como aviso, sin impedir emitir.

---

### User Story 6 - Ajustar la regla con el laboratorio (Priority: P3)

Como responsable del sistema, puedo cambiar el umbral (30 %) y la cantidad de resultados previos
(3) en un único lugar de la configuración, para ajustarlos cuando el laboratorio los confirme, sin
tocar el resto del sistema; cada desvío recuerda con qué regla se detectó.

**Why this priority**: El umbral es provisorio (criterio 2), pero el valor inicial ya es usable.

**Independent Test**: Cambiar el umbral a 50 % y verificar que un resultado +45,5 % ya no genera
desvío, mientras que los desvíos registrados antes siguen mostrando «detectado con umbral 30 %».

**Acceptance Scenarios**:

1. **Dada** la configuración con umbral U y cantidad N, **cuando** se evalúa un resultado,
   **entonces** se usan U y N, y no hay otro lugar del sistema donde estén escritos.
2. **Dado** un desvío registrado, **cuando** se muestra, **entonces** indica el umbral y la
   cantidad de resultados con que se detectó, y los resultados del historial usados (N° PI y
   valor), aunque la configuración haya cambiado después.
3. **Dado** un cambio de configuración, **cuando** se aplica, **entonces** los desvíos ya
   registrados no se recalculan; la regla nueva se usa en las próximas evaluaciones.
4. **Dado** el texto de ayuda de las pantallas, **cuando** se muestra la regla, **entonces** se lee
   con los valores vigentes («más de un 30 % respecto del promedio de los últimos 3 resultados
   validados del origen»).

---

### Edge Cases

- **Historial**: «resultados validados anteriores» son los del historial de la comparación
  histórica (US 8.1): resultados con validación vigente de la misma prueba, de muestras del mismo
  origen anteriores a la del estudio (por fecha de muestreo y, a igual fecha, N° PI), con la misma
  unidad; excluye otros estudios de la misma muestra. Los «últimos 3» son los 3 más recientes de
  ese orden.
- **Validación anulada**: un resultado previo cuya validación se anuló no cuenta hasta volver a
  validarse.
- **Estudio de una muestra antigua**: si se carga un estudio de una muestra anterior a otras ya
  validadas del origen, se compara solo contra las muestras anteriores a la suya.
- **Muestra sin origen**: no se evalúa desvío.
- **Promedio 0**: si el promedio de los previos es 0 y el resultado es distinto de 0, hay desvío y
  se muestra «sin porcentaje (promedio previo 0)»; si el resultado también es 0, no hay desvío.
- **Pruebas Ausente/Presente**: no se usan porcentajes. Hay desvío si el resultado es distinto del
  de los últimos 3 validados cuando estos coinciden entre sí (los 3 Ausente y el actual Presente, o
  al revés); si los 3 no coinciden no hay desvío. Se muestra «Presente (los últimos 3: Ausente)»,
  nunca 0 y 1.
- **Resultado por debajo del límite de detección**: se compara con su valor completo, como en la
  US 8.1, y se muestra «< LD».
- **Varias pruebas con desvío en el mismo estudio**: cada una es un desvío propio en la lista.
- **Varios estudios de la misma muestra**: cada estudio se evalúa por separado.
- **Estudio con informe emitido**: sus resultados no se recalculan, por lo tanto no se generan ni
  cambian desvíos; los pendientes se pueden marcar como revisados igual.
- **Historial que cambia después**: si más tarde se validan o anulan otros resultados del origen,
  los desvíos ya registrados no se recalculan; solo se reevalúa cuando cambia el resultado de esa
  prueba en ese estudio.
- **Resultados anteriores a esta historia**: los resultados sin validar existentes se pueden
  evaluar una vez con una tarea de mantenimiento, que no duplica desvíos al repetirse.
- **Concurrencia**: dos usuarios que marcan el mismo desvío a la vez dejan una sola revisión; el
  segundo recibe «El desvío ya estaba revisado».
- **Cliente u origen inactivo**: los desvíos se siguen mostrando y se pueden revisar (es historia).
- **Usuario sin acceso al dashboard**: no ve la sección ni la lista completa («sin permiso» si
  entra por el enlace); en el estudio igual ve la marca de desvío.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema MUST evaluar si hay desvío cada vez que se calcula o recalcula el
  resultado de una prueba de un estudio (carga de mediciones, corrección, recálculo de
  dependientes y la tarea de completar resultados), dentro de la misma operación: si la operación
  se rechaza o falla, tampoco quedan cambios de desvíos.
- **FR-002**: Hay desvío si, con al menos N resultados validados anteriores de la prueba en el
  origen (Edge Cases, «Historial»), el resultado difiere del promedio de los últimos N en más de U
  por ciento del promedio, en cualquier sentido. Valores iniciales: U = 30 %, N = 3. La comparación
  usa valores completos y aritmética decimal exacta; un porcentaje exactamente igual a U no es
  desvío.
- **FR-003**: U y N MUST definirse en un único lugar de la configuración del sistema; el historial
  y el promedio MUST obtenerse con la misma definición de historial y variación de la comparación
  histórica (US 8.1), sin una segunda implementación.
- **FR-004**: Con menos de N resultados previos, sin origen o sin resultado, no se registra desvío;
  la pantalla de validación indica «Historial insuficiente para detectar desvíos» cuando falta
  historial.
- **FR-005**: Cada desvío MUST guardar el estudio y la prueba, el valor observado y su unidad, el
  promedio, la diferencia y el porcentaje, los resultados previos usados (N° PI y valor), el umbral
  y la cantidad aplicados y la fecha y hora de detección.
- **FR-006**: Para una misma prueba de un estudio MUST haber como máximo un desvío vigente. Cuando
  el resultado se recalcula: si el valor no cambió, el desvío queda igual; si cambió y sigue fuera
  del umbral, el anterior deja de estar vigente y se registra uno nuevo sin revisar; si quedó
  dentro del umbral o sin resultado, el anterior deja de estar vigente («Resuelto por corrección» /
  «Sin resultado»). Los desvíos que dejan de estar vigentes no se borran.
- **FR-007**: El detalle del estudio y la pantalla de validación MUST marcar cada prueba con desvío
  vigente (texto + ícono), con el valor observado, el promedio de los últimos N, la diferencia
  (cantidad y porcentaje con flecha y signo), su estado (sin revisar / revisado con quién, cuándo y
  observación) y un enlace a la comparación histórica; la pantalla de validación además resume
  cuántos desvíos tiene el estudio.
- **FR-008**: El detalle del estudio MUST ofrecer el historial de desvíos de la prueba (incluidos
  los no vigentes, con el motivo), para trazabilidad.
- **FR-009**: El Dashboard MUST mostrar la sección «Desvíos sin revisar» con la cantidad total de
  desvíos vigentes sin revisar y los 10 detectados más recientemente, y un enlace «Ver todos» a una
  lista completa paginada. Ambas MUST mostrar por desvío: N° PI (enlace a la muestra), cliente,
  origen, prueba, valor observado y promedio con unidad, porcentaje, fecha de detección, si el
  resultado está validado, y los enlaces «Ver estudio» y «Comparación histórica» (estudio de
  referencia y prueba elegida). La lista no depende del período elegido en el Dashboard.
- **FR-010**: Un usuario con permiso MUST poder marcar como revisado un desvío vigente sin revisar,
  con confirmación previa y una observación opcional de hasta 500 caracteres; el sistema MUST
  guardar el usuario y la fecha y hora. La revisión MUST ser inalterable y no se puede deshacer ni
  borrar.
- **FR-011**: Marcar como revisado MUST revalidar al confirmar: si el desvío ya estaba revisado o
  dejó de estar vigente, no se modifica y se informa el motivo; dos confirmaciones simultáneas dejan
  una sola revisión.
- **FR-012**: El permiso para marcar como revisado MUST ser el mismo que el de validar resultados
  (grupo Bioquímicos); la sección y la lista completa del Dashboard MUST requerir el permiso del
  Dashboard. Sin permiso no se muestran las acciones y el pedido responde «sin permiso».
- **FR-013**: Los desvíos MUST ser solo informativos: no impiden validar ni emitir el informe, no
  cambian resultados, estados ni validaciones, y validar no los marca como revisados.
- **FR-014**: El control previo al informe MUST avisar cuántos desvíos sin revisar tiene el
  estudio, sin impedir la emisión.
- **FR-015**: Los desvíos MUST ser solo para el laboratorio: no aparecen en el informe, su PDF, la
  impresión ni el correo al cliente.
- **FR-016**: Las pruebas Ausente/Presente MUST evaluarse por cambio de estado (Edge Cases) y
  mostrarse como «Ausente»/«Presente».
- **FR-017**: Con promedio previo 0 MUST aplicarse la regla de Edge Cases («Promedio 0»).
- **FR-018**: El sistema MUST ofrecer una tarea de mantenimiento que evalúe una vez los resultados
  existentes sin validar de estudios sin informe; repetirla MUST NOT duplicar desvíos.
- **FR-019**: Cada desvío MUST mostrar el umbral y la cantidad con que se detectó; un cambio de
  configuración no recalcula los desvíos existentes.
- **FR-020**: La demo del laboratorio MUST incluir el desvío de Cloruro de «Pozo 2» como pendiente
  y al menos un desvío revisado, para mostrar la historia.

### Key Entities *(include if feature involves data)*

- **Desvío**: aviso de que el resultado de una prueba de un estudio se aleja del historial del
  origen. Guarda la prueba del estudio, el valor observado y su unidad, el promedio, la diferencia
  y el porcentaje (o el cambio de estado en Ausente/Presente), los resultados previos usados, el
  umbral y la cantidad de la regla, la fecha de detección, si está vigente y, si no, cuándo y por
  qué dejó de estarlo.
- **Revisión del desvío**: quién, cuándo y con qué observación se revisó un desvío; inalterable,
  como máximo una por desvío.
- **Regla de desvío** (configuración): umbral porcentual y cantidad de resultados previos.
- Reutiliza **Resultado**, **Validación**, **Muestra** y **Origen**, y el historial y la variación
  de la comparación histórica (US 8.1).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: El 100 % de los resultados calculados con al menos N previos que superan el umbral
  quedan marcados como desvío en la misma operación de carga o corrección, y ninguno dentro del
  umbral (verificado con casos conocidos en los bordes: exactamente 30 %, apenas más, promedio 0,
  Ausente/Presente).
- **SC-002**: Desde el Dashboard, un bioquímico llega a la comparación histórica de un desvío
  pendiente en 1 clic y lo marca como revisado en 2 (acción y confirmación).
- **SC-003**: Tras una corrección, la lista de desvíos pendientes refleja el nuevo resultado de
  inmediato: 0 desvíos vigentes con un valor distinto del resultado actual.
- **SC-004**: El 100 % de los desvíos revisados conserva quién y cuándo los revisó, y ningún desvío
  se borra.
- **SC-005**: Validar y emitir informes funciona igual con o sin desvíos (0 operaciones bloqueadas
  por un desvío) y ningún informe, PDF ni correo menciona desvíos.
- **SC-006**: Cambiar el umbral requiere modificar un solo valor de configuración.
- **SC-007**: La carga o corrección de un estudio de 20 pruebas con 6 meses de historia no tarda
  perceptiblemente más (menos de 1 segundo adicional) y el Dashboard con la sección se muestra en
  menos de 2 segundos.

## Assumptions

- «Notificar» significa avisar dentro del sistema (marca en el estudio, en la validación y lista
  del Dashboard); no se envían correos ni notificaciones fuera de AquaLab.
- Los «últimos 3 resultados validados» se toman del mismo historial que la comparación histórica
  (US 8.1), que ya excluye otros estudios de la misma muestra y resultados de otra unidad; el
  promedio de la 8.2 usa solo los últimos N, mientras que la 8.1 sigue mostrando el de todos.
- El porcentaje se calcula sobre el promedio (|resultado − promedio| / promedio) y se muestra con
  un decimal, como en la US 8.1; la decisión de desvío usa el valor exacto, no el redondeado.
- Revisar es una tarea del bioquímico (mismo permiso que validar); los Administradores con permiso
  de Dashboard ven la lista pero no revisan salvo que también sean Bioquímicos.
- El umbral y la cantidad se cambian en la configuración del sistema (no desde una pantalla); el
  laboratorio confirma el 30 % antes de la entrega final.
- Validar un resultado no implica revisar su desvío; un desvío sin revisar de un resultado ya
  validado sigue en la lista hasta que alguien lo marque como revisado.
- La demo de SCRUM-78 se amplía con el caso de desvío revisado (y queda el de «Pozo 2» sin revisar);
  si el guion genera desvíos en meses anteriores, se marcan como revisados en el guion.
- Se reutilizan los componentes de pantalla existentes (tablas, badges, confirmación, mensajes,
  ayuda) y el Dashboard de la US 8.3; no se agregan dependencias.
