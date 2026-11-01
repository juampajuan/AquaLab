# Feature Specification: Seleccionar estudio y controlar pruebas pendientes

**Feature Branch**: `020-controlar-pruebas-pendientes`

**Created**: 2026-11-01

**Status**: Draft

**Input**: User description: "US 7.1 – Seleccionar estudio y controlar pruebas pendientes. Como empleado del laboratorio quiero seleccionar un estudio y verificar las pruebas pendientes para asegurarme de que todos los ensayos estén terminados antes de emitir el informe. Criterios de aceptación: * Se debe poder seleccionar el estudio a informar. * El sistema debe mostrar el listado de pruebas y su estado. * El sistema debe bloquear la generación del informe si existen pruebas incompletas o sin validar. * Solo se habilita la generación cuando el 100% de las pruebas estén finalizadas. Contexto: ya existen EstadoEstudio (pendiente_analisis, en_proceso, finalizado, informe_generado) y EstadoPruebaEstudio (pendiente, cargada, completada); "finalizada/validada" = Completada (la valida US 6.4). La generación del informe en sí es la US 7.2; esta US solo controla la habilitación."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Seleccionar el estudio a informar (Priority: P1)

Como empleado con sesión activa, entro a la sección «Informes», busco el estudio que quiero informar (por N° PI, cliente, muestra o tipo de estudio) y lo selecciono. En el listado veo, para cada estudio, su estado y cuántas de sus pruebas están completadas, para saber de antemano cuáles están listos.

**Why this priority**: Es la puerta de entrada al Epic de informes: sin elegir el estudio no hay nada que controlar ni generar.

**Independent Test**: Con tres estudios (uno Finalizado, uno En proceso y uno con informe emitido), abrir «Informes», buscar por el N° PI de cada muestra y verificar que cada uno aparece con su estado y su avance («3 de 3 pruebas completadas», «1 de 4…») y que al seleccionarlo se abre su control de pruebas.

**Acceptance Scenarios**:

1. **Dado** un empleado con sesión activa, **cuando** abre «Informes» desde la navegación o la pantalla de inicio, **entonces** ve el listado de estudios con su N° PI, cliente, tipo de estudio, estado y avance de pruebas completadas, del más reciente al más antiguo.
2. **Dado** el listado, **cuando** busca por N° PI, número de estudio, nombre o documento del cliente, nombre de la muestra o tipo de estudio, **entonces** se muestran solo los estudios que coinciden; si no hay ninguno, se informa «No se encontraron estudios».
3. **Dado** el listado, **cuando** filtra por «Listos para informar», **entonces** se muestran solo los estudios con todas sus pruebas completadas y sin informe emitido.
4. **Dado** un estudio del listado, **cuando** lo selecciona, **entonces** se abre el control de pruebas de ese estudio (User Story 2).
5. **Dado** el detalle de un estudio (US 5.2), **cuando** el empleado lo consulta, **entonces** encuentra un acceso al control de pruebas para informar ese mismo estudio.

---

### User Story 2 - Controlar las pruebas pendientes y habilitar la generación (Priority: P1)

Como empleado, en el control de pruebas del estudio elegido veo los datos de la muestra y el cliente y el listado de todas las pruebas del estudio con su estado (Pendiente, Cargada o Completada). Si queda alguna prueba sin completar, el sistema me lo indica, me dice cuáles y cuántas faltan, y no me deja generar el informe; cuando el 100% de las pruebas está Completada, la acción «Generar informe» queda habilitada.

**Why this priority**: Es el control que pide la US: evita emitir un informe con ensayos sin terminar o sin validar.

**Independent Test**: Con un estudio de 3 pruebas (2 Completadas y 1 Cargada), abrir su control y verificar que se listan las 3 con su estado, que se indica «Falta completar 1 de 3 pruebas» señalando la Cargada como «sin validar» y que «Generar informe» está deshabilitada; validar la que falta (US 6.4) y verificar que la acción se habilita.

**Acceptance Scenarios**:

1. **Dado** un estudio seleccionado, **cuando** se abre su control, **entonces** se muestran el N° PI, la muestra, el cliente, el tipo de estudio, el estado del estudio y el listado de todas sus pruebas (código, nombre y estado).
2. **Dado** un estudio con pruebas Pendientes (sin medición), **cuando** se abre su control, **entonces** esas pruebas se destacan como «incompletas» y se indica cuántas faltan del total.
3. **Dado** un estudio con pruebas Cargadas (con medición o resultado pero sin validar), **cuando** se abre su control, **entonces** esas pruebas se destacan como «sin validar» y se indica cuántas faltan del total.
4. **Dado** un estudio con al menos una prueba que no está Completada, **cuando** se abre su control, **entonces** la acción «Generar informe» se muestra deshabilitada con el motivo («Hay N pruebas sin completar»).
5. **Dado** un estudio con el 100% de sus pruebas Completadas y sin informe emitido, **cuando** se abre su control, **entonces** se informa que el estudio está listo para informar y la acción «Generar informe» está habilitada.
6. **Dado** un estudio con pruebas sin completar, **cuando** se intenta generar el informe por otra vía (por ejemplo, con la dirección directa o un formulario viejo), **entonces** el sistema lo rechaza, informa el motivo y no cambia nada.
7. **Dado** un estudio con informe ya emitido, **cuando** se abre su control, **entonces** se informa que el informe ya fue generado y no se ofrece generarlo otra vez.

---

### Edge Cases

- Una prueba que estaba Completada pierde la validación (se corrige o borra su medición, US 6.3/6.5) mientras el control está abierto: al intentar generar, el sistema vuelve a verificar y rechaza; al recargar, la acción aparece deshabilitada.
- Un estudio recién creado, con todas sus pruebas Pendientes: el control muestra «Falta completar N de N pruebas» y la generación bloqueada.
- Un estudio con una prueba calculada sin resultado (le falta un dato, US 6.2): figura como incompleta y se muestra el motivo que ya da el detalle del estudio.
- Un estudio inexistente (dirección inválida): se informa que no existe, sin error del sistema.
- Las pruebas se muestran con los mismos estados y textos que el detalle del estudio, para que las dos pantallas nunca digan cosas distintas.
- El conteo de completadas es exacto: un estudio con 99 de 100 pruebas Completadas sigue bloqueado.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema MUST permitir a cualquier empleado con sesión activa consultar los estudios a informar y su control de pruebas.
- **FR-002**: El sistema MUST ofrecer una sección «Informes», accesible desde la navegación y la pantalla de inicio, con el listado de estudios (N° PI, cliente, tipo de estudio, estado y avance «N de M pruebas completadas»), ordenado del más reciente al más antiguo y paginado.
- **FR-003**: El listado MUST permitir buscar por N° PI, número de estudio, nombre o documento del cliente, nombre de la muestra y tipo de estudio, con los mismos criterios que la búsqueda de estudios existente (US 5.2), y MUST permitir filtrar solo los estudios listos para informar.
- **FR-004**: Seleccionar un estudio MUST abrir su control de pruebas; el detalle del estudio MUST ofrecer un acceso a ese control.
- **FR-005**: El control MUST mostrar los datos de identificación del estudio (N° PI, muestra, cliente, tipo de estudio tal como se guardó al crearlo, estado) y el listado de **todas** sus pruebas con código, nombre y estado.
- **FR-006**: El control MUST distinguir las pruebas que impiden informar: Pendiente como «incompleta» y Cargada como «sin validar», e indicar cuántas faltan del total.
- **FR-007**: Un estudio está listo para informar si y solo si tiene al menos una prueba, el 100% de sus pruebas está Completada y no tiene informe emitido.
- **FR-008**: La acción «Generar informe» MUST mostrarse habilitada solo si el estudio está listo para informar; en otro caso MUST mostrarse deshabilitada con el motivo.
- **FR-009**: El sistema MUST verificar la regla de FR-007 en el momento de generar, con los datos vigentes, y MUST rechazar e informar el motivo si no se cumple, sin cambiar nada. Esta regla MUST ser la única que use la generación del informe (US 7.2).
- **FR-010**: Con informe emitido, el control MUST indicarlo y MUST NOT ofrecer generarlo otra vez.
- **FR-011**: Consultar el listado y el control MUST NOT modificar ningún estudio, prueba, medición ni resultado.

### Key Entities *(include if feature involves data)*

- **Estudio** (US 5.1/5.2): el que se elige para informar; su estado (Pendiente de análisis, En proceso, Finalizado, Informe generado) se muestra pero no cambia en esta historia.
- **Prueba asignada al estudio**: cada una con su estado Pendiente, Cargada o Completada (validada en US 6.4); solo Completada cuenta como finalizada.
- **Informe** (US 7.2): no se crea en esta historia; esta historia define cuándo se puede generar.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Un empleado encuentra un estudio por su N° PI y sabe si está listo para informar en menos de 30 segundos.
- **SC-002**: El 100% de los intentos de generar el informe de un estudio con alguna prueba sin completar se rechaza.
- **SC-003**: En el 100% de los estudios con todas sus pruebas completadas y sin informe, la generación está habilitada.
- **SC-004**: El control y el detalle del estudio muestran siempre el mismo estado para cada prueba.

## Assumptions

- **Trazabilidad**: US 7.1 – Seleccionar estudio y controlar pruebas pendientes (Epic 6 de Jira: Informes). Clave de Jira a confirmar. Responsable según el cronograma: Delfina (semana 5).
- **«Finalizada» = Completada**: una prueba está finalizada cuando su resultado fue validado (US 6.4); Pendiente es «incompleta» y Cargada es «sin validar». Con todas las pruebas Completadas, US 6.4 pasa el estudio a Finalizado; esta historia igual cuenta las pruebas para no depender solo del estado del estudio.
- **Dependencias**: Se apoya en los estados de US 5.2 y en la validación de US 6.4 (rama `019-validar-resultados`, todavía no mergeada). Mientras US 6.4 no esté en `main`, ninguna prueba llega a Completada por la interfaz y la generación queda siempre bloqueada; los tests preparan los estados directamente.
- **Generar informe**: el contenido, la previsualización y el paso a «Informe generado» son de US 7.2. En esta historia la acción «Generar informe» existe con su habilitación y su rechazo; hasta que llegue US 7.2, habilitada lleva a un aviso de que la generación todavía no está disponible.
- **Sección «Informes»**: es el lugar de las historias 7.1 a 7.3 (consultar y exportar informes, US 7.3, se sumará ahí). La búsqueda reutiliza los criterios de la búsqueda de estudios (US 5.2) para no tener dos reglas distintas.
- **Permisos**: cualquier empleado con sesión activa puede consultar y generar, como el resto de las pantallas de estudios; no se agrega un permiso nuevo.
- **Interfaz**: con los componentes de `templates/ui/` (tablas, badges de estado, mensajes), siguiendo el diseño de la spec 013.
- **Alcance excluido**: generar, previsualizar o exportar el informe (US 7.2/7.3); validar resultados (US 6.4); enviar informes por correo (SCRUM-39).
