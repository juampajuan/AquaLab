# Feature Specification: Diseño de la interfaz

**Feature Branch**: `013-diseno-ui`

**Created**: 2026-10-28

**Status**: Draft

**Input**: User description: "SCRUM-67 – Diseño de la interfaz con Stitch. Como empleado del laboratorio quiero una interfaz profesional, moderna y consistente en todas las pantallas para trabajar de forma más clara y cómoda y que AquaLab se vea como un producto terminado. Alcance: todas las pantallas existentes hasta la US 5.1. Fuera de alcance: funcionalidades o pantallas nuevas, el admin de Django, los correos de la US 1.3 y las pantallas de las US 5.2 a 5.5."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Navegar el sistema con una estructura clara (Priority: P1)

Como empleado del laboratorio, quiero un diseño común en todas las pantallas, con un menú agrupado por
módulo, la identidad de AquaLab y mis datos de sesión siempre visibles, para ubicarme rápido y moverme
entre clientes, muestras y estudios sin perderme.

**Why this priority**: El layout común está en todas las pantallas; sin él no hay diseño consistente
y el resto de las historias no se puede apreciar.

**Independent Test**: Se puede probar iniciando sesión y recorriendo todas las secciones desde el menú,
verificando que cada pantalla comparte la misma estructura, que el menú indica la sección actual y que
cerrar sesión funciona desde cualquier pantalla.

**Acceptance Scenarios**:

1. **Given** un empleado con sesión iniciada, **When** abre cualquier pantalla interna, **Then** ve la identidad de AquaLab, un menú con los módulos Inicio, Clientes (Buscar cliente, Registrar cliente), Muestras (Registrar muestra) y Estudios (Crear estudio), su nombre y la opción de cerrar sesión.
2. **Given** un empleado en una pantalla de un módulo, **When** mira el menú, **Then** la opción correspondiente a esa pantalla aparece destacada.
3. **Given** un empleado con sesión iniciada, **When** elige cerrar sesión desde el menú, **Then** la sesión se cierra igual que antes del rediseño.
4. **Given** una persona sin sesión, **When** abre el inicio de sesión o el registro de usuario, **Then** ve un diseño de acceso con la identidad de AquaLab y sin el menú interno.

---

### User Story 2 - Completar y confirmar operaciones con formularios consistentes (Priority: P1)

Como empleado del laboratorio, quiero que todos los formularios y sus pantallas de confirmación se vean y
se comporten de la misma manera, para cargar datos sin errores y saber siempre qué estoy por guardar.

**Why this priority**: Las altas (usuario, cliente, muestra, estudio) y la edición de cliente son el
trabajo diario del laboratorio y todas siguen el mismo flujo "completar → revisar → confirmar".

**Independent Test**: Se puede probar recorriendo cada flujo de alta y edición con datos válidos e
inválidos, verificando que los errores aparecen junto a cada campo, que el resumen muestra los datos
cargados y que confirmar, volver y cancelar se comportan igual que antes.

**Acceptance Scenarios**:

1. **Given** cualquier formulario del sistema, **When** el empleado lo abre, **Then** ve los campos agrupados con etiquetas claras, los obligatorios identificados y la acción principal destacada.
2. **Given** un formulario con datos inválidos o incompletos, **When** el empleado intenta continuar, **Then** cada error aparece junto al campo correspondiente, con el mismo texto que antes del rediseño, y los datos válidos se conservan.
3. **Given** un formulario válido, **When** el empleado continúa, **Then** ve una pantalla de resumen con el mismo diseño en todos los flujos y las acciones Confirmar, Volver y editar y Cancelar claramente diferenciadas.
4. **Given** el formulario de registro de muestra, **When** el empleado elige un cliente, **Then** ve la mini-ficha del cliente y los orígenes de ese cliente igual que antes, integrados al nuevo diseño.
5. **Given** cualquier operación, **When** se guarda o falla, **Then** el sistema muestra el mensaje de éxito, error o información con un estilo distinto para cada tipo.

---

### User Story 3 - Consultar información de un vistazo (Priority: P2)

Como empleado del laboratorio, quiero que los resultados de búsqueda, las fichas y los estados se lean de un
vistazo, para encontrar un cliente y entender su situación sin leer cada dato.

**Why this priority**: La búsqueda y la ficha de cliente son el punto de partida de varios flujos, pero
el sistema ya es usable sin este cambio visual.

**Independent Test**: Se puede probar buscando clientes con y sin resultados, recorriendo la paginación
y abriendo fichas de clientes activos e inactivos.

**Acceptance Scenarios**:

1. **Given** una búsqueda con resultados, **When** el empleado la ejecuta, **Then** ve una tabla con encabezados claros, la cantidad de resultados, la acción "Ver ficha" en cada fila y la paginación cuando corresponde.
2. **Given** una búsqueda sin resultados, **When** el empleado la ejecuta, **Then** ve un estado vacío que explica que no se encontraron clientes para lo buscado.
3. **Given** la ficha de un cliente, **When** el empleado la abre, **Then** ve un encabezado con el nombre o razón social, los datos agrupados y las acciones disponibles.
4. **Given** un estado del dominio (cliente Activo/Inactivo, muestra Ingresada, estudio Pendiente de análisis), **When** aparece en pantalla, **Then** se muestra como una etiqueta de color reconocible y siempre igual en todo el sistema.

---

### User Story 4 - Empezar el trabajo desde un panel de inicio (Priority: P3)

Como empleado del laboratorio, quiero que el inicio me muestre accesos rápidos a las tareas principales y un
resumen de la actividad del laboratorio, para arrancar el trabajo diario en un clic y saber de un vistazo
cuánto trabajo hay.

**Why this priority**: Mejora la primera impresión y la demo, pero las mismas acciones ya están en el menú.

**Independent Test**: Se puede probar con datos cargados (muestras con y sin estudios, con distintas
fechas de ingreso, y estudios), verificando que los indicadores y la tabla coinciden con esos
datos, y con una base sin muestras, verificando el estado vacío.

**Acceptance Scenarios**:

1. **Given** un empleado que inicia sesión, **When** llega al inicio, **Then** ve un saludo y accesos rápidos a Buscar cliente, Registrar cliente, Registrar muestra y Crear estudio, cada uno con un ícono y una breve descripción.
2. **Given** el panel de inicio, **When** el empleado elige un acceso rápido, **Then** llega a la pantalla correspondiente.
3. **Given** muestras con al menos un estudio y muestras sin ningún estudio, **When** el empleado abre el inicio, **Then** el indicador "Muestras sin estudio" muestra solo la cantidad de muestras que todavía no tienen ningún estudio creado.
4. **Given** muestras con fecha de ingreso hoy y en otros días, **When** el empleado abre el inicio, **Then** el indicador "Muestras ingresadas hoy" muestra solo las que tienen fecha de ingreso igual a la fecha actual.
5. **Given** estudios registrados, **When** el empleado abre el inicio, **Then** el indicador "Estudios pendientes de análisis" muestra la cantidad de estudios en ese estado.
6. **Given** más de 5 muestras registradas, **When** el empleado abre el inicio, **Then** la tabla "Últimas muestras registradas" muestra las 5 más recientes, de la más nueva a la más vieja, con N° PI, cliente, origen, fecha de ingreso y estado.
7. **Given** que todavía no hay muestras registradas, **When** el empleado abre el inicio, **Then** los indicadores muestran 0 y la tabla muestra un estado vacío con un acceso a "Registrar muestra".

---

### Edge Cases

- Nombres, razones sociales, orígenes o correos muy largos no rompen tablas, fichas ni resúmenes.
- Un formulario con errores en varios campos a la vez muestra todos los errores sin desordenar el diseño.
- Errores generales que no pertenecen a un campo (por ejemplo, "No se pudo completar el registro") se muestran arriba del formulario.
- Varios mensajes al mismo tiempo se muestran apilados y legibles.
- La pantalla de confirmación de estudio vencida ("Recuperar solicitud") mantiene el diseño del resto de las confirmaciones.
- Crear estudio sin tipos de estudio disponibles muestra el error actual dentro del nuevo diseño.
- El inicio de sesión de una cuenta pendiente de aprobación muestra el mismo mensaje de error que antes.
- "Registro recibido" sin un registro en curso muestra el mismo contenido alternativo que antes.
- En una ventana angosta el menú y los contenidos siguen siendo usables, sin desplazamiento horizontal de la página.
- La protección de sesión existente (pantallas que se ocultan al cerrar sesión en otra pestaña) sigue funcionando con el nuevo diseño.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Todas las pantallas internas MUST compartir un layout común con identidad de AquaLab, menú agrupado por módulo (Inicio, Clientes, Muestras, Estudios), nombre del usuario logueado y opción de cerrar sesión.
- **FR-002**: El menú MUST destacar la sección en la que se encuentra el usuario.
- **FR-003**: Las pantallas de acceso (inicio de sesión, registro de usuario, confirmación y registro recibido) MUST usar un layout de acceso propio, con identidad de AquaLab y sin el menú interno.
- **FR-004**: El rediseño MUST cubrir las 15 pantallas existentes: inicio de sesión, registro de usuario, confirmar registro, registro recibido, inicio, registrar cliente, confirmar cliente, buscar cliente, ficha de cliente, editar cliente, confirmar edición, registrar muestra, confirmar muestra, crear estudio y confirmar estudio.
- **FR-005**: Los formularios MUST mostrar etiquetas en todos los campos, identificar los obligatorios, mostrar cada error junto a su campo y los errores generales arriba del formulario.
- **FR-006**: Todas las pantallas de resumen y confirmación MUST compartir el mismo diseño, con la acción de confirmar destacada y las de volver y cancelar diferenciadas.
- **FR-007**: Las tablas de resultados MUST mostrar encabezados, cantidad de resultados, acciones por fila, estado vacío y paginación con el mismo diseño.
- **FR-008**: Las fichas de detalle MUST mostrar un encabezado con la identificación del registro, los datos agrupados y las acciones disponibles.
- **FR-009**: Los estados del dominio (cliente Activo/Inactivo, muestra Ingresada, estudio Pendiente de análisis) MUST mostrarse como etiquetas con un color fijo por estado en todo el sistema.
- **FR-010**: Los mensajes de éxito, error e información MUST distinguirse visualmente entre sí y poder cerrarse.
- **FR-011**: El inicio MUST ser un panel con saludo y accesos rápidos a Buscar cliente, Registrar cliente, Registrar muestra y Crear estudio.
- **FR-019**: El inicio MUST mostrar tres indicadores calculados con los datos actuales al abrir la pantalla: "Muestras sin estudio" (muestras que todavía no tienen ningún estudio creado), "Muestras ingresadas hoy" (muestras cuya fecha de ingreso es la fecha actual) y "Estudios pendientes de análisis" (estudios en ese estado).
- **FR-020**: El inicio MUST mostrar la tabla "Últimas muestras registradas" con las 5 muestras registradas más recientemente, ordenadas de la más nueva a la más vieja, con N° PI, cliente, origen, fecha de ingreso y estado; sin muestras, MUST mostrar un estado vacío con acceso a "Registrar muestra".
- **FR-021**: El panel de inicio MUST ser solo de consulta: no permite modificar datos ni filtrar, y no agrega pantallas nuevas.
- **FR-012**: Salvo el panel de inicio (FR-019 a FR-021), el rediseño MUST NOT cambiar el comportamiento del sistema: mismos campos, validaciones, textos de mensajes, flujos de confirmación, permisos y direcciones de las pantallas.
- **FR-013**: Los elementos visuales repetidos (campos, botones, tablas, fichas, resúmenes, etiquetas de estado y mensajes) MUST definirse una sola vez y reutilizarse, para que las pantallas futuras (US 5.2 a 5.5) puedan adoptarlos sin rediseño.
- **FR-014**: Los colores, tipografías y espaciados MUST seguir un único sistema visual, definido con Stitch y aprobado por el equipo.
- **FR-015**: Todos los textos de la interfaz MUST estar en español.
- **FR-016**: La interfaz MUST estar orientada a escritorio y seguir siendo usable en ventanas angostas, sin desplazamiento horizontal de la página.
- **FR-017**: La interfaz MUST cumplir accesibilidad básica: contraste legible entre texto y fondo, etiquetas asociadas a cada campo y foco visible al navegar con teclado.
- **FR-018**: La interfaz MUST funcionar sin depender de recursos externos en tiempo de ejecución para sus estilos.

### Key Entities

No se agregan ni modifican datos. El panel de inicio solo lee Muestra (N° PI, cliente, origen, fecha de
ingreso, estado, orden de registro y si tiene estudios) y Estudio (estado). Los estados visibles
(cliente Activo/Inactivo, muestra Ingresada, estudio Pendiente de análisis) son los ya existentes.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: El 100% de las 15 pantallas del alcance usan el nuevo diseño, sin pantallas con el estilo anterior.
- **SC-002**: El 100% de las pruebas automáticas existentes siguen pasando después del rediseño, sin cambios en el comportamiento que verifican.
- **SC-003**: Un empleado puede llegar desde el inicio a cualquiera de las acciones principales en un solo clic.
- **SC-004**: En una revisión con el equipo, cada estado del dominio se identifica por su color sin leer el texto en el 100% de las pantallas donde aparece.
- **SC-005**: Ninguna pantalla del alcance presenta desplazamiento horizontal de la página en ventanas de 375 px de ancho o más.
- **SC-006**: El texto principal de todas las pantallas cumple una relación de contraste de al menos 4.5:1 con su fondo.
- **SC-007**: El equipo aprueba el resultado como "listo para mostrar en la demo" en la revisión del sprint.
- **SC-008**: El 100% de los valores del panel de inicio (tres indicadores y tabla) coinciden con los datos cargados en las pruebas.

## Assumptions

- Alcance: las pantallas existentes hasta la US 5.1 en `main`. Las pantallas de las US 5.2 a 5.5 se desarrollan en paralelo con el diseño anterior y se adaptan a los componentes de esta feature cuando se integren.
- El diseño visual se genera con Google Stitch y el equipo lo aprueba antes de implementarlo. La forma de implementar los estilos la define la constitution vigente (v1.1.0).
- Decisión del equipo: el panel de inicio incluye tres indicadores y la tabla de últimas muestras, porque se calculan con datos que ya existen y mejoran la demo. Un dashboard completo (gráficos, alertas, filtros, métricas históricas) queda para una US propia.
- "Hoy" es la fecha actual del laboratorio (zona horaria de Argentina).
- La tabla muestra la fecha de ingreso (solo día), no la hora de registro.
- No se agregan pantallas nuevas (por ejemplo, listado de muestras o aprobación de cuentas fuera del admin); quedan como posibles US futuras.
- El admin de Django mantiene su diseño propio y sigue usándose para aprobar o rechazar cuentas.
- Los correos de la US 1.3 siguen en texto plano.
- No se incluye modo oscuro ni internacionalización.
- El logo de AquaLab se define junto con el sistema visual en Stitch; si no hay logo, se usa el nombre con una tipografía distintiva.
