# Feature Specification: Panel del laboratorio

**Feature Branch**: `027-panel-laboratorio`

**Created**: 2026-11-08

**Status**: Aprobada (2026-11-08)

**Input**: User description: "SCRUM-75 – 8.3 Panel del laboratorio. Como responsable del laboratorio quiero ver indicadores del trabajo del laboratorio para seguir el volumen de trabajo y los tiempos de respuesta sin revisar estudio por estudio. Criterios de aceptación: (1) Nueva pantalla «Dashboard» en el menú, visible para Bioquímicos y Administradores. (2) Indicadores del período elegido (este mes, por defecto): muestras ingresadas, estudios creados e informes emitidos, con su variación contra el período anterior. (3) Tiempo de respuesta: días promedio desde el ingreso de la muestra hasta la emisión del informe, con un gráfico de su evolución por mes. (4) Estudios por estado: cuántos hay en cada uno (pendiente, en proceso, finalizado, informe generado). (5) Gráfico de actividad: muestras ingresadas e informes emitidos por semana. (6) Alertas: estudios sin avanzar hace más de 7 días, y estudios finalizados sin informe emitido, con enlace a cada uno. (7) Gráficos con Chart.js guardado en static/, sin CDN."

## Clarifications

### Session 2026-11-08

- Q: ¿Dónde va «Dashboard» en el menú lateral? → A: Enlace propio justo debajo de «Inicio» (Inicio → Dashboard → Clientes → Muestras → Estudios → Informes → Administración), con ícono, visible solo con el permiso y resaltado cuando se está en el panel.
- Q: Si hay muchos estudios en una alerta, ¿se muestran todos o solo algunos? → A: Todos, en una lista con desplazamiento dentro de la tarjeta de la alerta.
- Q: ¿De qué color se muestran las variaciones contra el período anterior? → A: El color indica si el cambio es bueno o malo: más muestras, estudios o informes en verde y menos en rojo; en el tiempo de respuesta, al revés (más días en rojo, menos en verde). Siempre con flecha y signo además del color.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ver el volumen de trabajo del período (Priority: P1)

Como responsable del laboratorio, abro «Dashboard» desde el menú y veo, para el mes en curso, cuántas muestras ingresaron, cuántos estudios se crearon y cuántos informes se emitieron, cada uno con su variación contra el mismo tramo del período anterior, y cuántos estudios hay hoy en cada estado. Puedo cambiar el período a mes anterior, últimos 3 meses o últimos 6 meses.

**Why this priority**: Es el núcleo de la historia: seguir el volumen de trabajo sin revisar estudio por estudio.

**Independent Test**: Con la demo de SCRUM-78 cargada, entrar como bioquímico, abrir el Dashboard y verificar que los tres indicadores del mes en curso coinciden con los datos (contados a mano) y que la variación compara contra los mismos días del mes anterior; cambiar a «Últimos 6 meses» y verificar los nuevos valores.

**Acceptance Scenarios**:

1. **Dado** un usuario con acceso al dashboard, **cuando** abre el menú, **entonces** ve «Dashboard» justo debajo de «Inicio» y al tocarlo se muestra el panel con el período «Este mes» elegido.
2. **Dado** el período «Este mes» al día 8, **cuando** se muestra el panel, **entonces** indica las muestras ingresadas (por fecha de ingreso), los estudios creados y los informes emitidos entre el día 1 y el 8, y la variación de cada uno contra el 1 al 8 del mes anterior, en cantidad y porcentaje.
3. **Dado** el período «Mes anterior», **cuando** se elige, **entonces** los indicadores cubren ese mes completo y se comparan contra el mes previo completo.
4. **Dados** los períodos «Últimos 3 meses» y «Últimos 6 meses», **cuando** se eligen, **entonces** cubren los últimos 3 o 6 meses calendario (incluido el actual hasta hoy) y se comparan contra el mismo tramo corrido 3 o 6 meses hacia atrás (FR-006).
5. **Dado** un aumento de muestras ingresadas y un aumento del tiempo de respuesta, **cuando** se muestran las variaciones, **entonces** la de muestras se ve en verde con «▲» y la del tiempo de respuesta en rojo con «▲».
6. **Dado** un indicador cuyo período anterior fue 0, **cuando** se muestra la variación, **entonces** muestra la diferencia en cantidad y, en lugar del porcentaje, «sin datos previos».
7. **Dado** el panel, **cuando** se muestra, **entonces** incluye cuántos estudios hay hoy en cada estado (Pendiente de análisis, En proceso, Finalizado, Informe generado), sin depender del período elegido.

---

### User Story 2 - Seguir el tiempo de respuesta y la actividad (Priority: P1)

Como responsable, veo cuántos días tarda en promedio el laboratorio desde que ingresa una muestra hasta que se emite su informe, con un gráfico de los últimos 6 meses, y un gráfico de las últimas 12 semanas con las muestras ingresadas y los informes emitidos por semana.

**Why this priority**: El tiempo de respuesta es la otra mitad del objetivo de la historia; el gráfico semanal muestra la carga de trabajo en el tiempo.

**Independent Test**: Con la demo cargada, verificar que el promedio del período coincide con el calculado a mano (días corridos entre ingreso y emisión de los informes emitidos en el período), que el gráfico mensual tiene 6 puntos y el semanal 12 semanas, y que no cambian al elegir otro período.

**Acceptance Scenarios**:

1. **Dado** un período con informes emitidos, **cuando** se muestra el panel, **entonces** el tiempo de respuesta es el promedio de días corridos entre la fecha de ingreso de la muestra y la fecha de emisión de cada informe emitido en el período, con un decimal, y su variación contra el período anterior.
2. **Dado** un período sin informes emitidos, **cuando** se muestra, **entonces** el tiempo de respuesta indica «Sin informes en el período».
3. **Dado** el panel, **cuando** se muestra, **entonces** el gráfico de tiempo de respuesta tiene un punto por cada uno de los últimos 6 meses (incluido el actual) con el promedio de los informes emitidos ese mes; un mes sin informes queda sin punto.
4. **Dado** el panel, **cuando** se muestra, **entonces** el gráfico de actividad muestra, para cada una de las últimas 12 semanas (lunes a domingo, incluida la actual), las muestras ingresadas y los informes emitidos.
5. **Dado** el panel, **cuando** se cambia el período, **entonces** los dos gráficos no cambian.
6. **Dado** un navegador sin JavaScript o si los gráficos no cargan, **cuando** se muestra el panel, **entonces** los datos de cada gráfico se pueden leer igual en una tabla.

---

### User Story 3 - Alertas de estudios demorados (Priority: P1)

Como responsable, veo una lista de estudios que no avanzan hace más de 7 días y otra de estudios finalizados que todavía no tienen informe, cada uno con un enlace a su detalle, para destrabarlos.

**Why this priority**: Es lo accionable del panel: lleva directamente a lo que hay que resolver.

**Independent Test**: Con la demo cargada, verificar que «Pozo domiciliario» del mes anterior aparece como estudio sin avanzar, que «Escuela N° 12» del mes anterior aparece como finalizado sin informe, y que sus enlaces llevan al detalle de cada estudio.

**Acceptance Scenarios**:

1. **Dado** un estudio Pendiente de análisis o En proceso cuya última actividad (creación, carga, corrección o validación de alguna de sus pruebas) fue hace más de 7 días, **cuando** se muestra el panel, **entonces** aparece en «Estudios sin avanzar» con N° de estudio, N° PI, cliente, estado y días sin actividad, y un enlace a su detalle.
2. **Dado** un estudio con actividad en los últimos 7 días, **cuando** se muestra el panel, **entonces** no aparece en «Estudios sin avanzar».
3. **Dado** un estudio Finalizado sin informe emitido, **cuando** se muestra el panel, **entonces** aparece en «Finalizados sin informe» con sus datos, los días desde que quedó Finalizado y un enlace a su detalle, sin importar cuántos días pasaron.
4. **Dadas** las dos alertas, **cuando** se muestran, **entonces** listan todos sus estudios del más antiguo al más reciente, en una lista con desplazamiento dentro de la tarjeta, e indican cuántos hay en cada una.
5. **Dado** que no hay estudios en una alerta, **cuando** se muestra, **entonces** indica «No hay estudios en esta situación».

---

### User Story 4 - Solo para Bioquímicos y Administradores (Priority: P2)

Como laboratorio, quiero que el dashboard lo vean solo los Bioquímicos y los Administradores, porque es una herramienta de gestión.

**Why this priority**: Es la regla de acceso; reutiliza el patrón de permisos de las US 6.4 y 7.2.

**Independent Test**: Con el técnico de la demo, verificar que no ve «Dashboard» en el menú y que la dirección directa se rechaza; con el bioquímico y con un usuario solo Administrador, que sí lo ven.

**Acceptance Scenarios**:

1. **Dado** el sistema recién instalado, **cuando** se preparan los datos iniciales, **entonces** existe el permiso «Puede ver el dashboard» y lo tienen los grupos «Bioquímicos» y «Administradores».
2. **Dado** un usuario sin el permiso, **cuando** abre el menú, **entonces** no ve «Dashboard»; **cuando** entra por la dirección directa, **entonces** se rechaza sin mostrar datos.
3. **Dado** un usuario sin sesión, **cuando** entra por la dirección directa, **entonces** se lo lleva al inicio de sesión.

---

### Edge Cases

- Base sin datos (laboratorio recién instalado): todos los indicadores en 0, gráficos vacíos con «Sin datos», alertas sin estudios; nada falla.
- Día 1 del mes con «Este mes»: el período es solo el día 1 y se compara con el día 1 del mes anterior.
- Mes anterior más corto (ej. 31 de marzo contra febrero): el tramo anterior termina el último día de ese mes.
- Muestra con varios estudios: cuenta una vez en «muestras ingresadas»; cada estudio cuenta en «estudios creados».
- Informe emitido en el período de una muestra ingresada antes: cuenta en el tiempo de respuesta del período de emisión.
- Estudios de clientes inactivos: se cuentan igual (es trabajo del laboratorio).
- Fechas: se usa la zona horaria del laboratorio (Argentina) para decidir a qué día, semana y mes pertenece cada registro.
- Período elegido inválido en la dirección: se usa «Este mes».
- Alerta con muchos estudios (ej. 200): se listan todos dentro de su tarjeta con desplazamiento; el resto del panel no se corre.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema MUST ofrecer una pantalla «Dashboard» accesible desde un enlace propio del menú lateral, ubicado justo debajo de «Inicio» y antes de «Clientes», con ícono, resaltado cuando se está en el panel y visible solo para usuarios con el permiso «Puede ver el dashboard».
- **FR-002**: El sistema MUST crear, como parte de sus datos iniciales, el permiso «Puede ver el dashboard» y asignarlo a los grupos «Bioquímicos» y «Administradores».
- **FR-003**: Un usuario sin el permiso MUST NOT ver el enlace y MUST ser rechazado al entrar por la dirección directa, sin ver datos.
- **FR-004**: El panel MUST permitir elegir el período entre «Este mes» (por defecto), «Mes anterior», «Últimos 3 meses» y «Últimos 6 meses».
- **FR-005**: Para el período elegido, el panel MUST mostrar: muestras ingresadas (por fecha de ingreso), estudios creados (por fecha de creación) e informes emitidos (por fecha de emisión).
- **FR-006**: Cada indicador MUST mostrar su variación contra el período anterior, en cantidad y porcentaje. El período anterior de «Este mes» MUST ser el mismo tramo de días del mes anterior (del 1 al día de hoy, o hasta el último día si ese mes es más corto); el de «Mes anterior», el mes completo previo; el de «Últimos N meses», los N meses calendario inmediatamente anteriores, hasta el mismo día relativo. Si el valor anterior es 0, MUST mostrarse la diferencia y «sin datos previos» en lugar del porcentaje.
- **FR-006a**: Cada variación MUST mostrarse con flecha y signo (ej. «▲ +12 %») y con un color que indique si el cambio es favorable: un aumento de muestras, estudios o informes es favorable (verde) y una baja, desfavorable (rojo); en el tiempo de respuesta es al revés (más días, rojo; menos días, verde). Sin cambio, gris. El color nunca es la única señal.
- **FR-007**: El panel MUST mostrar el tiempo de respuesta del período: promedio, con un decimal, de días corridos entre la fecha de ingreso de la muestra y la fecha de emisión de cada informe emitido en el período, con su variación contra el período anterior; sin informes, «Sin informes en el período».
- **FR-008**: El panel MUST mostrar un gráfico con el tiempo de respuesta promedio de cada uno de los últimos 6 meses (incluido el actual), calculado como en FR-007 con los informes emitidos en cada mes.
- **FR-009**: El panel MUST mostrar cuántos estudios hay hoy en cada estado (Pendiente de análisis, En proceso, Finalizado, Informe generado), independientemente del período.
- **FR-010**: El panel MUST mostrar un gráfico con las muestras ingresadas y los informes emitidos en cada una de las últimas 12 semanas (lunes a domingo, incluida la actual).
- **FR-011**: Los gráficos de FR-008 y FR-010 MUST NOT depender del período elegido.
- **FR-012**: Los datos de cada gráfico MUST poder leerse también como tabla, para quien no puede ver el gráfico.
- **FR-013**: El panel MUST mostrar la alerta «Estudios sin avanzar»: estudios Pendientes de análisis o En proceso cuya última actividad fue hace más de 7 días. La última actividad MUST ser la fecha más reciente entre la creación del estudio y la carga, corrección o validación de cualquiera de sus pruebas.
- **FR-014**: El panel MUST mostrar la alerta «Finalizados sin informe»: todos los estudios Finalizados sin informe emitido, con los días desde que quedaron Finalizados (fecha de la última validación).
- **FR-015**: Cada estudio de una alerta MUST mostrar N° de estudio, N° PI, cliente, estado y días, con un enlace a su detalle; cada alerta MUST indicar cuántos estudios tiene, mostrarlos todos (en una lista con desplazamiento dentro de su tarjeta, para que el panel no se alargue), ordenarlos del más antiguo al más reciente y, si está vacía, decir «No hay estudios en esta situación».
- **FR-016**: Las fechas MUST asignarse a días, semanas y meses según la zona horaria del laboratorio.
- **FR-017**: Los gráficos MUST funcionar sin conexión a servicios externos (la biblioteca de gráficos se sirve desde la propia aplicación).
- **FR-018**: El panel es de solo lectura: MUST NOT modificar ningún dato.

### Key Entities *(include if feature involves data)*

- **Indicador del período**: Cantidad de muestras ingresadas, estudios creados o informes emitidos en un período, con su valor en el período anterior y la variación.
- **Tiempo de respuesta**: Promedio de días corridos entre ingreso de la muestra y emisión del informe, por período y por mes.
- **Alerta**: Estudio que requiere atención (sin avanzar más de 7 días, o Finalizado sin informe), con su antigüedad.
- **Permiso «Puede ver el dashboard»**: Nuevo; lo tienen Bioquímicos y Administradores.
- Se apoya en **Muestra** (fecha de ingreso), **Estudio** (creación y estado), **Medición** (carga y corrección), **Validación** (fecha) e **Informe** (emisión); no crea entidades de datos nuevas.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Un responsable conoce el volumen de trabajo y el tiempo de respuesta del mes en menos de 10 segundos desde que abre el Dashboard, sin abrir ningún estudio.
- **SC-002**: El 100 % de los indicadores coincide con el conteo manual de los mismos datos para cada período.
- **SC-003**: El 100 % de los estudios que cumplen la regla de cada alerta aparece en ella, y ninguno que no la cumple.
- **SC-004**: El panel se muestra completo en menos de 2 segundos con el volumen de la demo (unos 45 estudios) y en menos de 5 segundos con 10.000 estudios.
- **SC-005**: El 100 % de los intentos de ver el panel sin el permiso se rechazan sin mostrar datos.
- **SC-006**: Con la demo de SCRUM-78, el panel muestra el estudio estancado de «Pozo domiciliario» y el finalizado sin informe de «Escuela N° 12».

## Assumptions

- **Trazabilidad**: SCRUM-75 – 8.3 Panel del laboratorio. Responsable: Delfina. Depende de SCRUM-78 (datos de demo) para probarse; habilita SCRUM-77 (tarjeta «Ver dashboard» en el inicio) y la lista de desvíos de SCRUM-61 (8.2), que se agregará en esa historia.
- **Decisiones tomadas con la responsable antes de especificar (2026-11-08)**: permiso propio asignado a los dos grupos (el técnico no lo ve); períodos este mes, mes anterior, 3 y 6 meses; «Este mes» se compara con los mismos días del mes anterior; gráficos fijos de 6 meses y 12 semanas que no cambian con el período; última actividad = creación o carga, corrección o validación de alguna prueba; tiempo de respuesta en días corridos por fecha de emisión.
- **Superusuario**: como en el resto de Django, el superusuario tiene todos los permisos y ve el dashboard aunque no esté en ningún grupo (a diferencia del panel de administración de la 025, que lo excluye a propósito). Es de solo lectura y no da facultades nuevas.
- **Borrar una medición (US 6.5)**: no deja fecha guardada, así que no cuenta como actividad para «Estudios sin avanzar». Limitación conocida; agregar un campo de última actividad no se justifica por ahora.
- **Fecha en que un estudio quedó Finalizado**: no se guarda; se toma la de su última validación vigente (es la que lo pasa a Finalizado, US 6.4).
- **Interfaz**: diseño de SCRUM-67 con los componentes de `templates/ui/`; la biblioteca de gráficos (Chart.js) se guarda en los archivos estáticos del proyecto, sin CDN, como pide el criterio 7.
- **Datos académicos**: proyecto FIUBA; se prueba con la demo ficticia.
- **Alcance excluido**: lista de desvíos sin revisar (SCRUM-61, 8.2); comparación histórica por origen (SCRUM-60, 8.1); panel de calidad de agua (SCRUM-76, 8.4); tarjeta en el inicio (SCRUM-77, 8.5); exportar los indicadores; rango de fechas libre.
