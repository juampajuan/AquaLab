# Feature Specification: Generar informe

**Feature Branch**: `021-generar-informe`

**Created**: 2026-11-01

**Status**: Aprobada (2026-11-01 18:40)

**Input**: User description: "US 7.2 (Jira: clave a confirmar) – Generar informe. Como empleado del laboratorio quiero generar el informe final y previsualizarlo para revisar la presentación y los datos consolidados antes de entregarlo. Criterios: (1) Desde el control de la US 7.1, con el 100% de las pruebas Completadas, «Generar informe» muestra una vista previa (borrador) con el formato institucional; nada cambia hasta confirmar. (2) El informe consolida automáticamente datos del laboratorio, del cliente (nombre o razón social, CUIT/DNI, domicilio, correo), de la muestra (N° PI, origen, nombre, fechas de muestreo e ingreso, sitio, responsable, tipo de vertido) y del estudio (número, tipo), y por cada prueba: nombre, resultado, unidad, límite, norma y si cumple, con lo fuera de norma resaltado. Un resultado por debajo del límite de detección se informa como «< LD» (ej. «< 0,1»). (3) Al confirmar «Emitir informe», solo los usuarios con el permiso «Puede emitir informes» (una migración lo asigna al grupo «Bioquímicos») emiten; el informe recibe un número correlativo propio (INF-000001, máximo + 1 sin huecos, como el N° PI), guarda quién y cuándo lo emitió y una copia de todos los datos mostrados, y el estudio pasa a «Informe generado». (4) Un informe por estudio; un estudio con informe no puede emitir otro. (5) La emisión revalida la regla de la US 7.1 con el estudio bloqueado (comprobar_generacion). (6) Los datos institucionales (nombre del laboratorio, dirección, matrícula, responsable técnico, logo) son de ejemplo y se configuran en un solo lugar hasta que el laboratorio los envíe. Fuera de alcance: PDF, impresión, firma y consulta posterior de informes (US 7.3); conclusión asistida (US 7.4); envío por correo (SCRUM-39)."

## Clarifications

### Session 2026-11-01

- Q: ¿Se previsualiza antes o después de generar? → A: Antes. «Generar informe» muestra una vista previa (borrador) y recién al confirmar «Emitir informe» se crea el informe y el estudio pasa a Informe generado; hasta ahí no cambia nada y se puede volver a corregir.
- Q: ¿El informe guarda una copia de los datos? → A: Sí. Al emitir se guarda una copia de los datos del laboratorio, del cliente, de la muestra, del estudio y de cada prueba (resultado, unidad, límite, norma, evaluación), para que editar el cliente o el catálogo después no cambie el informe.
- Q: ¿El informe tiene número propio? → A: Sí, correlativo desde 1, mostrado como «INF-000001», asignado como el N° PI (máximo + 1, sin huecos ante una falla).
- Q: ¿Hay datos institucionales del laboratorio? → A: Todavía no. Se usan datos de ejemplo configurables en un solo lugar y se reemplazan cuando el laboratorio los envíe.
- Q: ¿Quién puede emitir? → A: Solo quien tenga el permiso nuevo «Puede emitir informes», que una migración asigna al grupo «Bioquímicos» (son quienes firman). Separado del permiso de validar para poder distinguirlos más adelante.
- Q: ¿Cómo se informa un resultado por debajo del límite de detección? → A: Como «< LD» con el valor del límite (ej. «< 0,1»), como el software actual del laboratorio.
- Q: ¿Qué columnas lleva cada prueba? → A: Prueba, resultado, unidad, límite, norma y si cumple, con lo fuera de norma resaltado.
- Q: ¿Se genera PDF en esta historia? → A: No. Esta historia es la vista previa y la emisión en pantalla; PDF, impresión y firma son de la US 7.3.
- Q: ¿Un informe por estudio o por muestra? → A: Uno por estudio: cada estudio se informa cuando se completa.
- Q: ¿Quién puede ver la vista previa? → A: Cualquier empleado con sesión (como el control de la US 7.1); solo los usuarios con «Puede emitir informes» ven y usan «Emitir informe».
- Q: Con límite «Ausente», ¿un resultado por debajo del límite de detección cumple? → A: Sí. Por debajo del límite de detección el valor no se distingue de cero («no detectado»), así que cuenta como ausente. Se ajusta la regla de evaluación de la US 6.4 en esta historia; si el laboratorio opina distinto, se revierte en un solo lugar.
- Q: ¿Desde dónde se vuelve a ver un informe emitido? → A: Además de la pantalla que aparece al emitir, con un enlace «Ver informe» en el detalle del estudio y en el control de la US 7.1 cuando el estudio tiene informe. La búsqueda y el listado de informes siguen siendo de la US 7.3.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Previsualizar el informe (Priority: P1)

Como empleado del laboratorio, desde el control de un estudio listo para informar (US 7.1) toco «Generar informe» y veo el informe completo en pantalla, con el formato institucional y todos los datos consolidados, marcado como borrador. Si encuentro algo mal, vuelvo y lo corrijo; no cambió nada.

**Why this priority**: Es lo que pide la historia: revisar la presentación y los datos antes de entregarlos. Sin la vista previa, la emisión sería a ciegas.

**Independent Test**: Con un estudio de agua con pH 7,4 y Cloruro 400 mg/l validados, abrir la vista previa y verificar que muestra el laboratorio, el cliente, la muestra, el estudio y las dos pruebas con resultado, unidad, límite, norma y evaluación (Cloruro resaltado como fuera de norma), sin que el estudio cambie de estado.

**Acceptance Scenarios**:

1. **Dado** un estudio listo para informar, **cuando** se toca «Generar informe» en el control, **entonces** se muestra la vista previa del informe identificada como borrador y el estudio sigue en su estado.
2. **Dada** la vista previa, **cuando** se muestra, **entonces** incluye el encabezado institucional (nombre del laboratorio, dirección, matrícula, responsable técnico, logo), los datos del cliente (nombre o razón social, CUIT/DNI, domicilio, correo), de la muestra (N° PI, nombre, origen, fechas de muestreo e ingreso, sitio de extracción, responsable del muestreo, tipo de vertido) y del estudio (número, tipo de estudio).
3. **Dada** la vista previa, **cuando** se muestra, **entonces** lista cada prueba del estudio con nombre, resultado, unidad, límite, norma y si cumple, con las que no cumplen resaltadas.
4. **Dado** un resultado menor que el límite de detección de su prueba, **cuando** se muestra, **entonces** se informa como «< LD» con el valor del límite (ej. «< 0,1») en lugar del número.
5. **Dada** una prueba Ausente/Presente (ej. E. coli), **cuando** se muestra, **entonces** el resultado dice «Ausente» o «Presente».
6. **Dado** un estudio que no está listo (alguna prueba sin completar) o que ya tiene informe, **cuando** se intenta abrir la vista previa, **entonces** el sistema lo rechaza con el motivo de la US 7.1 y no muestra el borrador.

---

### User Story 2 - Emitir el informe (Priority: P1)

Como bioquímico, desde la vista previa confirmo «Emitir informe». El informe queda emitido con su número, la fecha y quién lo emitió, guarda una copia de todo lo que se mostró y el estudio pasa a Informe generado.

**Why this priority**: Cierra el ciclo del estudio y es la condición para la US 7.3 (consultar, exportar e inalterabilidad).

**Independent Test**: Desde la vista previa del estudio anterior, emitir y verificar que el informe tiene número INF-000001, quién lo emitió y cuándo, que el estudio está en Informe generado y que el informe emitido muestra los mismos datos que la vista previa.

**Acceptance Scenarios**:

1. **Dada** la vista previa de un estudio listo, **cuando** un usuario con el permiso «Puede emitir informes» confirma «Emitir informe», **entonces** se crea el informe con el siguiente número correlativo, quién lo emitió y la fecha y hora, y el estudio pasa a Informe generado.
2. **Dado** el informe emitido, **cuando** se completa la emisión, **entonces** se muestra el informe emitido (ya no como borrador) con su número y los mismos datos de la vista previa.
3. **Dado** un informe emitido, **cuando** después se edita el cliente, el catálogo de pruebas o los límites, **entonces** el informe sigue mostrando los datos guardados al emitir.
4. **Dado** el primer informe del sistema, **cuando** se emite, **entonces** recibe INF-000001; el siguiente, INF-000002.
5. **Dada** una emisión que falla, **cuando** se reintenta, **entonces** no quedan números salteados ni informes a medias.
6. **Dado** un estudio que, entre la vista previa y la confirmación, dejó de estar listo (se corrigió una medición, US 6.3) o ya fue informado por otra persona, **cuando** se confirma, **entonces** no se emite y se informa el motivo.

---

### User Story 3 - Solo emiten los bioquímicos (Priority: P2)

Como laboratorio, quiero que solo los integrantes del grupo «Bioquímicos» puedan emitir informes, porque son quienes los firman.

**Why this priority**: Es la regla de seguridad de la emisión; reutiliza el patrón de permisos y grupos de las US 5.5 y 6.4.

**Independent Test**: Con un empleado fuera del grupo, verificar que puede ver la vista previa pero no ve «Emitir informe» y que el intento de emitir se rechaza; agregado al grupo, emite.

**Acceptance Scenarios**:

1. **Dado** el sistema recién instalado, **cuando** se preparan los datos iniciales, **entonces** el grupo «Bioquímicos» tiene el permiso «Puede emitir informes».
2. **Dado** un empleado sin el permiso, **cuando** abre la vista previa, **entonces** la ve pero sin la acción «Emitir informe»; **cuando** intenta emitir por otra vía, **entonces** se rechaza sin cambios.

---

### Edge Cases

- Doble envío de «Emitir informe» o dos bioquímicos emitiendo a la vez: se emite un solo informe; el segundo intento informa que el estudio ya tiene informe.
- Un resultado por debajo del límite de detección en una prueba con límite «Ausente» (ej. Sólidos sedimentables 0,05 con LD 0,1): se informa «< 0,1» y cumple (FR-016).
- Resultados validados antes de este ajuste con la regla anterior conservan la evaluación guardada; los datos son de desarrollo (DEMO) y se revalidan si hace falta.
- Límite de detección no numérico (ej. «Ausente» en E. coli): no se aplica «< LD».
- Prueba sin límite comparable (US 6.4): se muestra el límite tal como figura y la evaluación «Sin límite comparable».
- Datos opcionales vacíos (domicilio, responsable del muestreo, nombre de la muestra): se muestran como «—», no se omite la fila.
- El informe muestra la evaluación y los límites guardados en la validación vigente de cada prueba (US 6.4), no los del catálogo actual.
- Un estudio con informe emitido: el control de la US 7.1 ya no ofrece generar sino «Ver informe»; la vista previa y la emisión se rechazan con el motivo.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Desde el control de la US 7.1, «Generar informe» MUST mostrar a cualquier empleado con sesión una vista previa del informe solo si el estudio está listo para informar (regla única de la US 7.1); si no, MUST rechazarlo con el motivo.
- **FR-002**: La vista previa MUST identificarse claramente como borrador y MUST NOT modificar el estudio ni crear ningún informe.
- **FR-003**: El informe MUST consolidar automáticamente: datos institucionales del laboratorio; cliente (nombre o razón social, tipo y número de documento, domicilio, correo); muestra (N° PI, nombre, origen, fecha de muestreo, fecha de ingreso, sitio de extracción, responsable del muestreo, tipo de vertido); estudio (número, tipo de estudio tal como se guardó al crearlo).
- **FR-004**: Por cada prueba del estudio, el informe MUST mostrar nombre, resultado, unidad, límite, norma y si cumple, usando la evaluación y los límites guardados en su validación vigente (US 6.4), y MUST resaltar las que no cumplen.
- **FR-005**: Un resultado numérico menor que el límite de detección numérico de su prueba MUST mostrarse como «< » seguido del valor del límite (ej. «< 0,1»). Las pruebas A/P MUST mostrar «Ausente» o «Presente».
- **FR-006**: Los datos institucionales (nombre del laboratorio, dirección, matrícula, responsable técnico y logo) MUST configurarse en un único lugar y tener valores de ejemplo hasta que el laboratorio los provea.
- **FR-007**: La vista previa MUST ofrecer «Emitir informe» solo a usuarios con el permiso «Puede emitir informes», además de volver al control sin cambios.
- **FR-008**: Al confirmar, el sistema MUST revalidar con el estudio bloqueado que sigue listo para informar (US 7.1) y que el usuario tiene el permiso; si no, MUST rechazar e informar el motivo sin cambiar nada.
- **FR-009**: Al emitir, el sistema MUST crear el informe con un número correlativo propio (siguiente al máximo, desde 1, sin huecos ante fallas), mostrado como «INF-» y seis dígitos, con quién lo emitió y la fecha y hora.
- **FR-010**: Al emitir, el informe MUST guardar una copia de todos los datos mostrados (institucionales, cliente, muestra, estudio y cada prueba con resultado, unidad, límite, norma y evaluación); el informe emitido MUST mostrarse siempre a partir de esa copia.
- **FR-011**: Al emitir, el estudio MUST pasar a «Informe generado» en la misma operación; si algo falla, MUST NOT quedar informe ni cambio de estado.
- **FR-012**: Un estudio MUST tener como máximo un informe; un segundo intento MUST rechazarse informando que ya tiene informe.
- **FR-013**: Tras emitir, el sistema MUST mostrar el informe emitido con su número, sin la marca de borrador, e informar el éxito.
- **FR-014**: El sistema MUST crear, como parte de sus datos iniciales, el permiso «Puede emitir informes» y asignarlo al grupo «Bioquímicos».
- **FR-015**: Emitir MUST NOT modificar pruebas, mediciones, resultados, validaciones, la muestra, el cliente, el catálogo ni otros estudios.
- **FR-016**: La evaluación de la US 6.4 MUST considerar que, con límite «Ausente» o «Ausencia», un resultado menor que el límite de detección numérico de la prueba cumple, igual que el 0. Aplica a la validación y a la evaluación que muestra el detalle del estudio.
- **FR-017**: Cuando el estudio tiene informe emitido, el detalle del estudio y el control de la US 7.1 MUST ofrecer «Ver informe», que muestra el informe emitido a partir de su copia, a cualquier empleado con sesión.

### Key Entities *(include if feature involves data)*

- **Informe**: Documento emitido de un estudio. Atributos: número correlativo, estudio (uno por estudio), quién lo emitió, fecha y hora de emisión, y la copia de los datos mostrados (laboratorio, cliente, muestra, estudio y pruebas). Una vez emitido no cambia (la inalterabilidad completa y la exportación son de la US 7.3).
- **Datos institucionales del laboratorio**: Nombre, dirección, matrícula, responsable técnico y logo; configurables en un solo lugar.
- **Estudio** (US 5.x): Pasa a «Informe generado» al emitir; desde ahí no admite correcciones (US 6.3).
- **Validación** (US 6.4): Fuente de la evaluación y los límites de cada prueba en el informe.
- **Grupo «Bioquímicos»** (US 6.4): Recibe el permiso «Puede emitir informes».

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Un bioquímico pasa del control del estudio al informe emitido en menos de 1 minuto, con una sola confirmación.
- **SC-002**: El 100% de los informes emitidos muestran exactamente los mismos datos que su vista previa.
- **SC-003**: Ningún informe emitido cambia después de editar el cliente, el catálogo o los límites.
- **SC-004**: Los números de informe son correlativos y sin huecos aun con emisiones simultáneas o fallidas.
- **SC-005**: El 100% de los intentos de emitir sin el permiso, con el estudio incompleto o ya informado terminan sin cambios.
- **SC-006**: El 100% de los resultados por debajo del límite de detección se informan como «< LD».

## Assumptions

- **Trazabilidad**: US 7.2 – Generar informe. Jira: clave a confirmar. Responsable: Delfina.
- **Dependencias**: Se apoya en la US 7.1 (regla única para informar y `comprobar_generacion`, PR #34, ya en `main`), en la US 6.4 (validación con evaluación y límites guardados, grupo «Bioquímicos») y en el ajuste Ausente/Presente.
- **Evaluación**: El informe no recalcula si cumple: usa la evaluación de la validación vigente de cada prueba (US 6.4), ya con el ajuste de FR-016.
- **Logo de ejemplo**: Se usa el logo de AquaLab como marcador hasta tener el del laboratorio.
- **Interfaz**: Pantallas con el diseño de SCRUM-67 y los componentes de `templates/ui/`; el informe usa un diseño de documento en pantalla, preparado para la US 7.3.
- **Datos académicos**: AquaLab es un proyecto FIUBA; los datos de desarrollo y demostración son ficticios (DEMO).
- **Alcance excluido**: PDF, impresión, firma y búsqueda o listado de informes emitidos (US 7.3); conclusión asistida (US 7.4); envío por correo (SCRUM-39); anular o reemitir un informe.
