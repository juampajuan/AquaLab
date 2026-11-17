# Feature Specification: Iniciar un estudio desde el asistente

**Feature Branch**: `040-iniciar-estudio-asistente`

**Created**: 2026-11-17

**Status**: Borrador

**Input**: User description: "US 10.3 (SCRUM-85) – Iniciar un estudio desde el asistente. Como empleado quiero pedirle al asistente que registre una muestra o un estudio y que me pregunte lo que falta, para cargarlo más rápido. Criterios de aceptación: Se le puede pedir, por ejemplo: «Registrá una muestra de Lácteos del Sur, pozo 2, para un físico-químico básico». El asistente pregunta los datos que faltan: cliente, origen, tipo de estudio y fechas. Con los datos completos, lleva al formulario de registro de siempre, ya completo, para revisar y confirmar. El asistente nunca crea nada solo: la muestra o el estudio se crean únicamente al confirmar en esa pantalla, con las mismas validaciones y permisos de siempre. Si un dato no coincide con nada del sistema (cliente u origen inexistente, tipo inactivo), lo informa y ofrece las opciones que sí existen. Si se abandona la conversación, no queda nada creado. Fuera de alcance: cargar mediciones o validar desde el asistente; dar de alta clientes nuevos. Depende de: US 10.1 (asistente de consultas), US 4.1 (Registrar muestra) y US 5.1 (Crear estudio)."

**Trazabilidad**: US 10.3, Jira SCRUM-85.

## Clarifications

### Session 2026-11-17

- Q: ¿La muestra y el estudio se confirman por separado o en una sola confirmación nueva? → A: Por separado, en las dos pantallas de siempre: tras registrar la muestra, el mensaje de éxito ofrece «Crear el estudio <tipo>» con muestra y tipo ya elegidos.
- Q: ¿El asistente pregunta las dos fechas o supone el ingreso como hoy? → A: Pregunta siempre las dos fechas que falten (muestreo e ingreso); no supone ninguna.
- Q: ¿Un origen que el cliente no tiene puede ofrecerse como origen nuevo? → A: Sí: el asistente avisa, ofrece los orígenes del cliente y «Registrarlo como origen nuevo»; elegido, el formulario llega con «Origen nuevo» completo y se crea solo al confirmar la muestra.
- Q: Si se pide una muestra sin tipo de estudio, ¿el asistente lo pregunta? → A: Sí, con los tipos activos como opciones más «Solo registrar la muestra», que va primera entre las opciones (siempre visible y a un toque, aunque haya muchos tipos); elegida, el enlace lleva al registro sin ofrecer después crear un estudio.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Registrar una muestra con su estudio desde el asistente (Priority: P1)

Como empleado le pido al asistente «Registrá una muestra de Lácteos del Sur, pozo 2, para un
físico-químico básico». El asistente reconoce el cliente, el origen y el tipo de estudio, me
pregunta lo que falta (las fechas) y, con todo completo, me ofrece un enlace al formulario de
registro de muestra de siempre, ya completo con esos datos. Reviso, completo lo que el asistente
no pide (por ejemplo el sitio de extracción) y confirmo como siempre. Al registrarse la muestra,
la pantalla me ofrece crear el estudio del tipo pedido para esa muestra, también ya elegido, que
confirmo en la pantalla de creación de estudio de siempre.

**Why this priority**: Es el ejemplo de la historia y el caso de todos los días: llega una
muestra y hay que registrarla con su estudio. Sola ya entrega el valor de la historia.

**Independent Test**: Con la demo cargada, pedir el registro del ejemplo, responder las fechas,
seguir el enlace y verificar que el formulario muestra cliente, origen y fechas elegidos; que
antes de confirmar no existe ninguna muestra nueva; que al confirmar se crea con el N° PI
siguiente; y que el paso siguiente ofrece crear el estudio con el tipo pedido, que tampoco existe
hasta confirmarlo.

**Acceptance Scenarios**:

1. **Dado** un empleado con el asistente abierto, **cuando** pide «Registrá una muestra de Lácteos
   del Sur, pozo 2, para un físico-químico básico», **entonces** el asistente identifica el cliente,
   el origen y el tipo de estudio en los datos del sistema y pregunta solo lo que falta (las fechas
   de muestreo y de ingreso).
2. **Dado** un pedido de muestra sin tipo de estudio («Registrá una muestra de Lácteos del Sur, pozo
   2»), **cuando** se envía, **entonces** el asistente pregunta el tipo ofreciendo como opciones
   primero «Solo registrar la muestra» y después los tipos activos; con «Solo registrar la muestra»
   el registro sigue igual pero sin ofrecer después crear un estudio.
3. **Dado** que el asistente preguntó las fechas, **cuando** se responde («la tomaron ayer, llegó
   hoy»), **entonces** el asistente resume los datos reunidos (cliente, origen, tipo de estudio,
   fechas) y ofrece un enlace «Revisar y registrar la muestra».
4. **Dado** el enlace, **cuando** se lo sigue, **entonces** se abre el formulario de registro de
   muestra de siempre con el cliente, el origen y las fechas ya completos (y el sitio de extracción,
   el tipo de vertido, el nombre o el responsable si se dijeron en la conversación), y los campos que
   faltan quedan para completar como siempre.
5. **Dado** el formulario precargado, **cuando** se lo envía y se confirma, **entonces** la muestra
   se registra con las mismas validaciones, mensajes y numeración (N° PI) que un registro hecho a mano.
6. **Dada** una muestra recién registrada desde un pedido que incluía tipo de estudio, **cuando** se
   ve el mensaje de éxito, **entonces** ofrece «Crear el estudio <tipo>» para esa muestra, que lleva a
   la pantalla de crear estudio de siempre con la muestra y el tipo ya elegidos; el estudio se crea
   solo al confirmar ahí.
7. **Dado** cualquier momento antes de confirmar en la pantalla de registro, **cuando** se mira el
   sistema, **entonces** no hay ninguna muestra, estudio ni origen nuevo creado por la conversación.

---

### User Story 2 - Crear un estudio para una muestra existente (Priority: P1)

Como empleado le pido al asistente «Creá un estudio bacteriológico para el PI 200417». El
asistente encuentra la muestra y el tipo, y me ofrece el enlace a la pantalla de crear estudio de
siempre con la muestra y el tipo ya elegidos, para revisar y confirmar.

**Why this priority**: Es la otra mitad del pedido («registre una muestra o un estudio») y la
forma de agregar un segundo estudio a una muestra ya registrada.

**Independent Test**: Pedir un estudio para un N° PI existente, seguir el enlace y verificar que
la pantalla de crear estudio muestra esa muestra y ese tipo elegidos, que el estudio no existe
hasta confirmar y que al confirmar nace con las pruebas del tipo como siempre.

**Acceptance Scenarios**:

1. **Dada** una muestra existente, **cuando** se pide un estudio de un tipo activo para su N° PI,
   **entonces** el asistente ofrece un enlace «Revisar y crear el estudio» a la pantalla de crear
   estudio con la muestra y el tipo ya elegidos.
2. **Dado** un pedido de estudio sin muestra o sin tipo, **cuando** se envía, **entonces** el
   asistente pregunta el dato que falta (el N° PI de la muestra o el tipo de estudio).
3. **Dado** el enlace, **cuando** se confirma en la pantalla de crear estudio, **entonces** el
   estudio se crea con las mismas validaciones, confirmación y mensajes de siempre; si la muestra o
   el tipo ya no están disponibles al confirmar, la pantalla lo informa como siempre.

---

### User Story 3 - Datos que no coinciden con el sistema (Priority: P2)

Como empleado, si nombro un cliente, un origen o un tipo de estudio que no existe o no está
disponible, el asistente me lo dice y me ofrece las opciones que sí existen para elegir.

**Why this priority**: Sin esto el pedido termina en un formulario mal completado o en datos
inventados; es lo que hace confiable al asistente, pero el flujo principal funciona sin ello si
los nombres son exactos.

**Independent Test**: Pedir una muestra para un cliente inexistente, para un origen que el
cliente no tiene y para un tipo inactivo, y verificar en cada caso el aviso y las opciones
ofrecidas, sin que se genere ningún enlace de registro con el dato inválido.

**Acceptance Scenarios**:

1. **Dado** un cliente que no existe o está inactivo, **cuando** se lo nombra, **entonces** el
   asistente informa que no lo encontró, ofrece como opciones los clientes activos parecidos (si hay)
   y aclara que dar de alta un cliente se hace en «Registrar cliente», no desde el asistente.
2. **Dado** un nombre que coincide con varios clientes activos, **cuando** se lo nombra, **entonces**
   el asistente ofrece esos clientes como opciones para elegir, como en la US 10.1.
3. **Dado** un origen que el cliente no tiene, **cuando** se lo nombra, **entonces** el asistente lo
   informa, ofrece como opciones los orígenes del cliente y la opción de registrarlo como origen
   nuevo (que el formulario de siempre permite y crea solo al confirmar la muestra).
4. **Dado** un tipo de estudio inactivo o inexistente, **cuando** se lo nombra, **entonces** el
   asistente informa que no está disponible y ofrece los tipos activos parecidos o, si no hay
   parecidos, la lista de tipos activos.
5. **Dado** un N° PI que no existe, **cuando** se pide un estudio para él, **entonces** el asistente
   responde que no hay ninguna muestra con ese N° PI y no ofrece enlace.

---

### User Story 4 - Abandonar sin dejar nada creado (Priority: P2)

Como empleado puedo cerrar el asistente, cambiar de tema o no seguir el enlace, y no queda nada
creado ni reservado.

**Why this priority**: Es una garantía de la historia («el asistente nunca crea nada solo»); se
cumple casi por construcción, pero tiene que verificarse.

**Independent Test**: Llevar una conversación hasta el enlace final, cerrar el panel sin seguirlo
(o seguirlo y salir del formulario sin confirmar) y verificar que no cambió la cantidad de
muestras, estudios ni orígenes, y que el próximo registro hecho a mano toma el N° PI siguiente al
último existente.

**Acceptance Scenarios**:

1. **Dada** una conversación de registro en cualquier punto, **cuando** se cierra el panel, se cambia
   de tema o se cierra la sesión, **entonces** no queda ninguna muestra, estudio ni origen creado ni
   ningún N° PI consumido.
2. **Dado** un formulario precargado desde el asistente, **cuando** se sale sin confirmar,
   **entonces** no queda nada creado, igual que con un formulario completado a mano.

---

### Edge Cases

- **Permisos**: quien pide el registro sin poder registrar muestras o crear estudios recibe el mismo
  rechazo que en esas pantallas; el asistente no ofrece un enlace a una pantalla que la persona no
  puede usar.
- **Datos que cambian entre la conversación y la confirmación** (cliente desactivado, tipo
  desactivado, origen borrado): la pantalla de siempre los valida al enviar y muestra sus mensajes de
  siempre; el asistente no garantiza nada que la pantalla no revalide.
- **Fechas**: «hoy», «ayer» o «el 12/11» se entienden con la fecha del laboratorio; una fecha futura o
  una de ingreso anterior a la de muestreo la rechaza el formulario con sus mensajes de siempre. Si no
  se entiende la fecha, el asistente la vuelve a preguntar.
- **Enlace manipulado o viejo**: los datos del enlace son solo valores iniciales del formulario; un
  valor que no existe o no está disponible se ignora (el campo queda para elegir) y nunca se crea nada
  sin la confirmación de siempre.
- **Pedido mixto o fuera de alcance**: «registrá la muestra y cargá el pH en 7,2» o «validá el
  estudio» → el asistente ayuda solo con el registro y aclara que cargar mediciones o validar se hace
  en las pantallas correspondientes.
- **Dar de alta un cliente**: «registrá el cliente Juan Pérez» → el asistente responde que no puede y
  ofrece el enlace a «Registrar cliente».
- **Servicio de IA no disponible**: los mismos avisos de la US 10.1; el registro a mano funciona
  igual.
- **Borrador de registro en curso**: si ya había un registro de muestra a medio confirmar en la
  sesión, abrir el enlace del asistente lo reemplaza, igual que empezar un registro nuevo a mano.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El asistente MUST reconocer pedidos de registrar una muestra (con o sin tipo de
  estudio) y de crear un estudio para una muestra existente, además de las consultas de la US 10.1.
- **FR-002**: Para registrar una muestra, el asistente MUST reunir cliente, origen, fecha de
  muestreo y fecha de ingreso, y el tipo de estudio si el pedido lo incluye, preguntando solo los que
  falten (si falta el tipo, lo pregunta con «Solo registrar la muestra» como primera opción).
  Ninguna fecha se supone: si no se dijo, se pregunta (se acepta «hoy» como respuesta). Para crear un estudio MUST reunir la muestra (N° PI) y el tipo de estudio.
- **FR-003**: Cliente, origen, tipo de estudio y muestra MUST resolverse contra los datos del sistema
  con las mismas reglas que las pantallas (solo clientes activos, orígenes del cliente elegido, solo
  tipos activos); el asistente nunca usa un valor que no salió de esa búsqueda.
- **FR-004**: Si un dato no coincide o no está disponible, el asistente MUST informarlo y ofrecer
  como opciones elegibles las que sí existen (clientes activos parecidos, orígenes del cliente más
  «origen nuevo», tipos activos), con el mismo mecanismo de opciones de la US 10.1.
- **FR-005**: Con los datos completos, el asistente MUST ofrecer un único enlace al formulario de
  siempre (registro de muestra o crear estudio) con esos datos como valores iniciales, junto con un
  resumen de lo reunido. El enlace lo arma AquaLab, nunca el modelo.
- **FR-006**: El asistente y sus herramientas MUST NOT crear, modificar ni borrar datos (muestras,
  estudios, orígenes, borradores de sesión, N° PI). Se mantiene la garantía de solo lectura de la
  US 10.1.
- **FR-007**: El formulario precargado MUST comportarse igual que el de siempre: mismos campos,
  validaciones, permisos, confirmación, mensajes y numeración; los datos del enlace son solo valores
  iniciales y un valor inválido o no disponible se descarta en silencio.
- **FR-008**: Si el registro de muestra se inició con un tipo de estudio, al registrarse la muestra la
  pantalla MUST ofrecer crear ese estudio para la muestra recién creada, llevando a crear estudio con
  muestra y tipo elegidos. El estudio se crea solo al confirmar ahí.
- **FR-009**: El asistente MUST NOT ofrecer enlaces a pantallas que la persona no puede usar y MUST
  NOT dar de alta clientes, cargar mediciones ni validar; ante esos pedidos responde qué puede hacer y
  dónde se hace lo otro.
- **FR-010**: Las fechas dichas en lenguaje natural MUST interpretarse con la fecha del laboratorio;
  si no son claras, el asistente MUST volver a preguntar en vez de suponer.
- **FR-011**: Al servicio externo MUST NOT enviarse datos de contacto del cliente ni datos de usuarios,
  como en la US 10.1.

### Key Entities *(include if feature involves data)*

- **Pedido de registro (en la conversación)**: los datos reunidos hasta el momento (cliente, origen u
  origen nuevo, fechas, tipo de estudio, muestra, y opcionalmente sitio, vertido, nombre y
  responsable). No se guarda en la base: vive en la conversación y termina en el enlace.
- **Enlace de registro precargado**: dirección del formulario de siempre con los datos como valores
  iniciales. No reserva nada ni concede permisos.
- Se usan sin cambios **Cliente**, **Origen**, **Muestra**, **Tipo de estudio** y **Estudio**.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: El ejemplo de la historia llega al formulario de registro completo en no más de 3
  mensajes del empleado (pedido, fechas y, si hace falta, una elección).
- **SC-002**: En el 100 % de las conversaciones de prueba, la cantidad de muestras, estudios y
  orígenes y el próximo N° PI no cambian hasta confirmar en la pantalla de siempre.
- **SC-003**: El 100 % de los datos precargados coincide con lo resuelto en la conversación, y
  ningún dato inexistente o no disponible llega precargado.
- **SC-004**: Ante cada dato que no coincide (cliente, origen, tipo, N° PI) el asistente informa el
  problema y ofrece al menos una opción válida cuando existe.
- **SC-005**: Registrar una muestra con su estudio a partir del asistente toma menos tiempo que
  hacerlo a mano recorriendo las pantallas (medido en la prueba manual con la demo).

## Assumptions

- Puede usarlo cualquier empleado con sesión iniciada, como el asistente de la US 10.1 y las pantallas
  de registro de muestra y crear estudio (que hoy solo exigen sesión).
- La muestra y el estudio siguen siendo dos pasos con dos confirmaciones (las pantallas de la US 4.1
  y la US 5.1); no hay una confirmación combinada (decidido en Clarifications).
- El asistente pregunta solo cliente, origen, fechas y tipo de estudio (los del criterio de
  aceptación). Sitio de extracción, tipo de vertido, nombre y responsable se precargan si se dijeron;
  si no, se completan en el formulario (el vertido arranca en «Agua» como siempre).
- Un origen que el cliente no tiene puede usarse como «origen nuevo» solo si se lo elige entre las
  opciones (nunca sin preguntar), como permite el formulario de la US 4.1; se crea solo al confirmar
  la muestra (decidido en Clarifications).
- Sin cambios en el modelo de datos ni en la conversación sin guardar de la US 10.1 (panel,
  `sessionStorage`, límites de vueltas y tiempo, servicio de IA y avisos).
