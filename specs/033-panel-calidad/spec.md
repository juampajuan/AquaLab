# Feature Specification: Panel de calidad del agua

**Feature Branch**: `033-panel-calidad`

**Created**: 2026-11-09

**Status**: Draft

**Input**: User description: "US 8.4 (SCRUM-76) – Panel de calidad del agua. Como bioquímico quiero ver el nivel de cumplimiento de los resultados para detectar qué pruebas, clientes u orígenes presentan más incumplimientos. Criterios: (1) En el Dashboard, sección «Calidad», para el período elegido (el mismo selector de la 8.3). (2) Porcentaje de resultados fuera de norma sobre el total de resultados validados del período. (3) Pruebas que más fallan: ranking con el porcentaje de incumplimiento de cada una. (4) Cumplimiento por tipo de vertido (agua, cloacal, canal). (5) Clientes y orígenes con más incumplimientos, con enlace al historial del cliente (US 3.3) y a la comparación histórica del origen (US 8.1). (6) Se usa la evaluación guardada en la Validacion vigente («cumple» o «fuera de norma»); no se recalcula. Mismo permiso que el Dashboard. Notas técnicas: reutilizar el período y el patrón de informes/tablero.py y dashboard.js de la 8.3, y Chart.js de static/vendor."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ver el nivel de cumplimiento del período (Priority: P1)

Como bioquímico, abro el Dashboard y, en la sección «Calidad», veo qué porcentaje de los resultados
validados en el período elegido quedó fuera de norma, con cuántos resultados fuera de norma y cuántos
evaluados en total, y su variación contra el período anterior. Al cambiar el período con el selector
del Dashboard, la sección se actualiza junto con el resto del panel.

**Why this priority**: Es el indicador central de la historia: el nivel de cumplimiento general.

**Independent Test**: Con la demo de SCRUM-78 cargada, abrir el Dashboard como bioquímico, contar a
mano las validaciones vigentes del período con evaluación «cumple» y «fuera de norma» y verificar que
el porcentaje coincide; cambiar a «Últimos 6 meses» y verificar el nuevo valor.

**Acceptance Scenarios**:

1. **Dado** un período con 40 resultados validados evaluados (36 «cumple» y 4 «fuera de norma»),
   **cuando** se muestra la sección «Calidad», **entonces** indica «10,0 % fuera de norma», «4 de 40
   resultados».
2. **Dado** el selector de período del Dashboard, **cuando** se elige otro período, **entonces** la
   sección «Calidad» usa ese mismo período (no tiene un selector propio).
3. **Dado** un período anterior con 5,0 % fuera de norma y el actual con 10,0 %, **cuando** se
   muestra la variación, **entonces** se ve «▲ +5,0 p. p.» en rojo (más incumplimiento es
   desfavorable); una baja se ve en verde con «▼»; sin cambio, gris con «=».
4. **Dado** un período anterior sin resultados evaluados, **cuando** se muestra la variación,
   **entonces** indica «sin datos previos».
5. **Dado** un período con resultados validados «sin límite comparable», **cuando** se muestra la
   sección, **entonces** no cuentan en el porcentaje ni en el total, y se informan aparte («3
   resultados sin límite comparable, fuera del cálculo»).
6. **Dado** un período sin resultados evaluados, **cuando** se muestra la sección, **entonces**
   indica «Sin resultados validados en el período» y los rankings y el gráfico por vertido quedan
   vacíos con ese mismo aviso.

---

### User Story 2 - Pruebas que más fallan (Priority: P1)

Como bioquímico, veo un ranking de las pruebas con incumplimientos en el período, ordenadas por su
porcentaje de incumplimiento, para saber qué parámetros conviene vigilar.

**Why this priority**: Es el primer «qué» que pide la historia y el más útil para el laboratorio.

**Independent Test**: Con la demo cargada y «Últimos 6 meses», verificar que cada prueba del ranking
muestra sus resultados fuera de norma, sus evaluados y el porcentaje contados a mano, y que el orden
es el de FR-007.

**Acceptance Scenarios**:

1. **Dado** Cloruro con 2 de 10 resultados fuera de norma y E. coli con 1 de 4, **cuando** se
   muestra el ranking, **entonces** E. coli (25,0 %) aparece antes que Cloruro (20,0 %), cada una con
   su código, nombre, «fuera de norma / evaluados» y porcentaje.
2. **Dadas** dos pruebas con el mismo porcentaje, **cuando** se ordenan, **entonces** va primero la
   que tiene más resultados fuera de norma y, si también empatan, por código.
3. **Dada** una prueba sin resultados fuera de norma en el período, **cuando** se muestra el
   ranking, **entonces** no aparece.
4. **Dadas** más de 10 pruebas con incumplimientos, **cuando** se muestra el ranking, **entonces**
   se ven las 10 primeras y se indica cuántas más hay.
5. **Dado** el ranking, **cuando** se muestra, **entonces** tiene un gráfico de barras y su tabla
   «Ver datos» con los mismos valores.

---

### User Story 3 - Cumplimiento por tipo de vertido (Priority: P2)

Como bioquímico, veo el cumplimiento del período separado por tipo de vertido (Agua, Cloacal,
Canal), porque cada uno se rige por límites distintos.

**Why this priority**: Completa el panorama general; depende del mismo conteo de la US 1.

**Independent Test**: Con la demo cargada, contar a mano los resultados evaluados y fuera de norma de
cada tipo de vertido (según el vertido de la muestra) y compararlos con el gráfico y su tabla.

**Acceptance Scenarios**:

1. **Dado** el período, **cuando** se muestra «Cumplimiento por tipo de vertido», **entonces** para
   Agua, Cloacal y Canal (siempre los tres, en ese orden) indica evaluados, «cumple», «fuera de norma»
   y el porcentaje de cumplimiento.
2. **Dado** un tipo de vertido sin resultados evaluados en el período, **cuando** se muestra,
   **entonces** figura con 0 evaluados y «Sin resultados» en lugar del porcentaje.
3. **Dado** el gráfico, **cuando** se muestra, **entonces** tiene su tabla «Ver datos» con los mismos
   valores.

---

### User Story 4 - Clientes y orígenes con más incumplimientos (Priority: P2)

Como bioquímico, veo qué clientes y qué orígenes tuvieron más resultados fuera de norma en el
período, y desde cada uno voy al historial del cliente o a la comparación histórica del origen.

**Why this priority**: Es lo accionable de la sección: lleva a quién y a dónde hay que mirar.

**Independent Test**: Con la demo cargada y «Últimos 6 meses», verificar los conteos de cada cliente y
origen listados, que el enlace de un cliente abre su historial (US 3.3) y que el de un origen abre la
comparación histórica de ese origen (US 8.1).

**Acceptance Scenarios**:

1. **Dado** el período, **cuando** se muestra «Clientes con más incumplimientos», **entonces** lista
   los clientes con al menos un resultado fuera de norma, con «fuera de norma / evaluados» y
   porcentaje, ordenados por cantidad fuera de norma (de mayor a menor), luego por porcentaje y luego
   por nombre; hasta 10, indicando cuántos más hay.
2. **Dado** un cliente de la lista, **cuando** se toca su enlace, **entonces** se abre su historial
   (US 3.3).
3. **Dado** un cliente inactivo con incumplimientos, **cuando** se muestra la lista, **entonces**
   aparece igual, marcado como inactivo y sin enlace (el historial no admite clientes inactivos).
4. **Dado** el período, **cuando** se muestra «Orígenes con más incumplimientos», **entonces** lista
   los orígenes (con su cliente) con al menos un resultado fuera de norma, con el mismo formato y
   orden que los clientes; hasta 10, indicando cuántos más hay.
5. **Dado** un origen de la lista, **cuando** se toca su enlace, **entonces** se abre la comparación
   histórica de ese origen (US 8.1).
6. **Dado** que no hay incumplimientos en el período, **cuando** se muestran las listas,
   **entonces** indican «No hubo resultados fuera de norma en el período».

---

### Edge Cases

- Base sin datos: porcentaje sin valor («Sin resultados validados en el período»), listas y gráficos
  vacíos; nada falla.
- Validación anulada (corrección o borrado posterior, US 6.3/6.5): no cuenta; solo la vigente.
- Prueba validada, corregida y vuelta a validar: cuenta una sola vez, con la evaluación y la fecha de
  la validación vigente.
- Validación vigente cuyo resultado ya está en un informe emitido: cuenta igual (es un resultado
  validado).
- Cambio posterior de los límites del catálogo: no altera nada; se usa la evaluación guardada.
- Pruebas Ausente/Presente: cuentan igual que las numéricas según su evaluación guardada.
- Cliente o origen cuyo nombre cambió después: se muestra el nombre actual (el panel es de gestión,
  no un documento emitido).
- Muestra de un tipo de vertido sin límites propios (usó los generales): cuenta en su tipo de vertido.
- Fechas: la fecha de validación se asigna al día según la zona horaria del laboratorio, como en la
  8.3.
- Porcentajes con un decimal, redondeo a la mitad hacia arriba; nunca se divide por cero.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El Dashboard MUST incluir una sección «Calidad» que use el período elegido en el
  selector del Dashboard (US 8.3), sin selector propio.
- **FR-002**: La sección MUST considerar solo los resultados con una validación vigente (no anulada)
  cuya fecha de validación cae dentro del período, y MUST usar la evaluación guardada en esa
  validación, sin volver a evaluarla contra los límites actuales.
- **FR-003**: «Evaluados» MUST ser los resultados de FR-002 con evaluación «cumple» o «fuera de
  norma». Los «sin límite comparable» MUST quedar fuera del porcentaje y del total, y MUST informarse
  su cantidad aparte.
- **FR-004**: La sección MUST mostrar el porcentaje de resultados fuera de norma sobre los evaluados
  del período, con un decimal, junto con ambas cantidades.
- **FR-005**: El porcentaje MUST mostrar su variación contra el período anterior (el mismo de la
  8.3), en puntos porcentuales, con flecha, signo y color: una suba es desfavorable (rojo), una baja
  favorable (verde), sin cambio gris. Sin evaluados en alguno de los dos períodos, MUST mostrarse
  «sin datos previos» (anterior) o ningún porcentaje (actual).
- **FR-006**: La sección MUST mostrar el ranking de pruebas con al menos un resultado fuera de norma
  en el período, cada una con código, nombre, fuera de norma, evaluados y porcentaje de
  incumplimiento.
- **FR-007**: El ranking de pruebas MUST ordenarse por porcentaje de incumplimiento (mayor primero),
  luego por cantidad fuera de norma y luego por código, y MUST mostrar hasta 10 pruebas indicando
  cuántas más hay.
- **FR-008**: La sección MUST mostrar, para Agua, Cloacal y Canal (siempre los tres, en ese orden),
  evaluados, «cumple», «fuera de norma» y porcentaje de cumplimiento, según el tipo de vertido de la
  muestra; un tipo sin evaluados MUST indicar «Sin resultados».
- **FR-009**: La sección MUST mostrar los clientes y, por separado, los orígenes con al menos un
  resultado fuera de norma en el período, con fuera de norma, evaluados y porcentaje, ordenados por
  cantidad fuera de norma, luego por porcentaje y luego por nombre, hasta 10 de cada uno indicando
  cuántos más hay. Cada origen MUST mostrar también su cliente.
- **FR-010**: Cada cliente activo MUST enlazar a su historial (US 3.3); un cliente inactivo MUST
  aparecer marcado como tal y sin enlace. Cada origen MUST enlazar a su comparación histórica (US
  8.1).
- **FR-011**: El ranking de pruebas y el cumplimiento por tipo de vertido MUST tener gráfico y su
  tabla «Ver datos» con los mismos valores, para quien no puede ver el gráfico.
- **FR-012**: La sección MUST verse solo con el permiso del Dashboard («Puede ver el dashboard»); no
  agrega permisos nuevos.
- **FR-013**: Los gráficos MUST funcionar sin servicios externos (la misma biblioteca de gráficos
  servida por la aplicación que usa la 8.3).
- **FR-014**: La sección es de solo lectura: MUST NOT modificar ningún dato, y nada de ella va al
  informe, al PDF ni a los correos.
- **FR-015**: Los porcentajes MUST calcularse sin errores de redondeo binario, con un decimal y
  redondeo a la mitad hacia arriba, y nunca dividir por cero.

### Key Entities *(include if feature involves data)*

- **Resultado evaluado**: Prueba de un estudio con validación vigente «cumple» o «fuera de norma»,
  fechada por su validación; se agrupa por prueba, tipo de vertido, cliente y origen de la muestra.
- **Indicador de calidad**: Porcentaje fuera de norma del período, con fuera de norma, evaluados, sin
  límite comparable y variación contra el período anterior.
- **Fila de ranking**: Prueba, cliente u origen con sus fuera de norma, evaluados y porcentaje.
- Se apoya en **Validación** (fecha, evaluación, anulada), **Muestra** (tipo de vertido, cliente,
  origen), **Prueba**, **Cliente** y **Origen**; no crea entidades de datos nuevas.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Un bioquímico identifica la prueba, el cliente y el origen con más incumplimientos del
  período en menos de 15 segundos desde que abre el Dashboard, sin abrir ningún estudio.
- **SC-002**: El 100 % de los porcentajes y conteos coincide con el conteo manual de las validaciones
  vigentes de cada período.
- **SC-003**: Cambiar los límites del catálogo después de validar no cambia ningún valor de la
  sección (0 diferencias).
- **SC-004**: El Dashboard completo, con la sección «Calidad», se sigue mostrando en menos de 2
  segundos con el volumen de la demo y en menos de 5 segundos con 10.000 estudios.
- **SC-005**: El 100 % de los enlaces de clientes y orígenes lleva al historial o a la comparación
  del cliente u origen correcto.
- **SC-006**: El 100 % de los intentos de ver la sección sin el permiso se rechazan sin mostrar datos.

## Assumptions

- **Trazabilidad**: SCRUM-76 – US 8.4 Panel de calidad del agua. Depende de la 8.3 (Dashboard,
  período y permiso), la 6.4 (validación y su evaluación), la 3.3 (historial) y la 8.1 (comparación
  histórica); se prueba con la demo de SCRUM-78.
- **Fecha que ubica un resultado en el período**: la de su validación vigente. El criterio habla de
  «resultados validados del período», y así un resultado no cambia de período cuando se valida tarde.
  Consecuencia: una muestra tomada en un mes y validada en el siguiente cuenta en el siguiente.
- **«Sin límite comparable»** no es cumplimiento ni incumplimiento: queda fuera del porcentaje (el
  criterio 6 nombra solo «cumple» y «fuera de norma») y se informa aparte para que no se pierda.
- **Variación contra el período anterior**: se agrega por coherencia con los indicadores de la 8.3;
  en puntos porcentuales porque el indicador ya es un porcentaje.
- **Ranking de pruebas por porcentaje** (lo pide el criterio 3); **clientes y orígenes por
  cantidad** («con más incumplimientos», criterio 5). Solo aparecen los que tienen al menos un
  incumplimiento; tope de 10 por lista para que el panel no se alargue.
- **Superusuario**: como en la 8.3, ve la sección por tener todos los permisos.
- **Interfaz**: diseño de SCRUM-67 con los componentes de `templates/ui/`; mismo patrón de tarjetas,
  gráficos y «Ver datos» de la 8.3.
- **Datos académicos**: proyecto FIUBA; se prueba con la demo ficticia. Si la demo no tiene
  incumplimientos suficientes para probar los rankings, se agregan casos al guion de SCRUM-78.
- **Alcance excluido**: pantalla aparte con el listado completo de incumplimientos; exportar los
  indicadores; filtros por cliente, prueba o vertido; rango de fechas libre; tarjeta en el inicio
  (SCRUM-77, 8.5).
