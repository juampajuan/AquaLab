# Feature Specification: Gestionar tipos de estudio

**Feature Branch**: `012-Gestionar-Catalogo-Estudios`

**Created**: 2026-10-27

**Status**: Draft para revisión del diagnóstico previo a plan — reglas funcionales confirmadas por el usuario el 28/10/2026; base compartida integrada. No se declara aprobación formal global del equipo ni autorización de implementar.

**Input**: User description: "US 5.5 — Como responsable técnico quiero crear y editar tipos de estudio y definir sus pruebas por defecto para mantener el catálogo actualizado sin depender de un desarrollador. Criterios oficiales: crear un tipo con nombre obligatorio y único y descripción; seleccionar pruebas predeterminadas del catálogo existente; no permitir tipos sin pruebas; editar nombre, descripción y conjunto de pruebas; aplicar cambios únicamente a estudios creados posteriormente; impedir eliminar tipos utilizados y permitir desactivarlos; no crear pruebas científicas nuevas. El usuario desarrollará US 5.5 antes de US 5.1. Solo especificación, sin plan ni implementación. Clave y enlace Jira pendientes, sin códigos supuestos."


**Vigencia del contexto**: La descripción Input conserva el pedido inicial. El orden actual es US 5.1 implementada e integrada antes de US 5.5; el contexto es académico FIUBA y todos los datos de desarrollo/demo son ficticios identificados. No hay proveedor científico externo pendiente. Las decisiones y dependencias vigentes están debajo; las aclaraciones del 27/10 se conservan como historial.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Crear un tipo con pruebas existentes (Priority: P1)

Como responsable técnico autorizado, quiero crear un tipo con nombre, descripción y pruebas predeterminadas para que pueda utilizarse al crear estudios.

**Why this priority**: Provee el catálogo necesario para US 5.1 sin cargar manualmente cada prueba en el estudio.

**Independent Test**: Con pruebas ficticias precargadas e identificadas para desarrollo o fixtures aisladas y un usuario autorizado según FR-014, crear y confirmar un tipo y verificar sus datos y conjunto exacto de pruebas. No requiere muestras ni estudios para comprobar el alta.

**Acceptance Scenarios**:

1. **Dado** un usuario autorizado con sesión activa y pruebas existentes, **cuando** completa nombre válido, descripción y una o más pruebas distintas, **entonces** puede revisar el resumen y confirmar la creación de un tipo que conserva exactamente esos datos y pruebas, sin modificar las definiciones científicas.
2. **Dado** un nombre vacío o solo con espacios, un nombre igual a otro al ignorar mayúsculas y espacios laterales o una selección vacía de pruebas, **cuando** se intenta guardar, **entonces** se rechaza el alta, se indican los errores y se conservan los valores válidos. La misma comparación se aplica a la edición, sin considerar duplicado el propio tipo.
3. **Dada** una selección con pruebas inexistentes, **cuando** se confirma, **entonces** se rechaza el alta sin guardar un tipo ni asociaciones parciales.
4. **Dado** un catálogo de pruebas vacío, **cuando** se intenta crear un tipo, **entonces** se informa la falta de pruebas precargadas y no se permite guardar un tipo vacío ni crear pruebas científicas en este flujo.
5. **Dado** un resumen de alta, **cuando** se cancela, **entonces** no se guarda nada; volver a editar conserva los datos para corregirlos.
6. **Dado** un nombre válido y al menos una prueba existente, **cuando** se confirma el tipo dejando la descripción vacía, **entonces** se permite guardarlo; la descripción también puede vaciarse al editar.
7. **Dados** dos nombres que difieren en tildes o espacios internos, **cuando** se comparan para validar unicidad, **entonces** esas diferencias se conservan: solo se ignoran mayúsculas y espacios laterales. El nombre se guarda sin espacios laterales.

---

### User Story 2 - Editar sin alterar estudios existentes (Priority: P2)

Como responsable técnico autorizado, quiero editar nombre, descripción y composición para que los nuevos estudios usen la configuración actual sin alterar los anteriores.

**Why this priority**: Permite mantener el catálogo y preservar el historial de estudios.

**Independent Test**: La edición puede probarse con pruebas precargadas. US 5.1 ya existe en la base integrada: sus estudios, asignaciones e historial se reutilizan para verificar la integración real, sin recrear esa historia dentro del catálogo. El escritor de US 5.5 aún debe implementarse y probarse.

**Acceptance Scenarios**:

1. **Dado** un tipo existente, **cuando** se editan nombre, descripción y conjunto de pruebas y se confirma el resumen, **entonces** se guarda íntegramente la configuración elegida, conservando identidad del tipo, nombre único y al menos una prueba.
2. **Dado** un tipo con una prueba, **cuando** se intenta quitarla sin seleccionar otra, **entonces** se rechaza el guardado y permanece la configuración anterior.
3. **Dada** una edición con nombre utilizado o prueba inexistente, **cuando** se confirma, **entonces** se informa el error sin cambios parciales.
4. **Dado** un tipo usado en estudios, **cuando** cambia su composición, nombre o descripción, **entonces** los estudios existentes conservan exactamente sus asignaciones y el nombre y descripción históricos del tipo que recibieron al crearse; los nuevos reciben los textos y composición vigentes que confirmen, manteniendo en ambos casos la referencia estable al tipo.
5. **Dado** un estudio en revisión en US 5.1, **cuando** cambia la composición antes de crearse, **entonces** no se crea silenciosamente con otra configuración: se informa el cambio, se muestra el conjunto actualizado y se exige nueva confirmación explícita; la confirmación anterior no sirve para aceptar el nuevo conjunto.
6. **Dadas** una edición de composición y una creación de estudio concurrentes, **cuando** coinciden, **entonces** el estudio se crea íntegramente con el conjunto confirmado antes de que tenga efecto el cambio, o no se crea y se exige revisar y confirmar el actualizado. Nunca se mezclan configuraciones. Si vuelve a cambiar, se repite la revisión. La política está confirmada. US 5.1 implementa el lado consumidor; la verificación conjunta con las operaciones administrativas reales de US 5.5 queda para su implementación.
7. **Dada** una edición pendiente, **cuando** se cancela o falla el guardado, **entonces** permanece la configuración anterior y no cambia ningún estudio existente.
8. **Dados** dos usuarios autorizados que abren la misma versión de un tipo, **cuando** el primero confirma una edición y el segundo intenta guardar usando la versión anterior, **entonces** se rechaza el segundo guardado, se informa el conflicto y se permite revisar la configuración vigente, sin sobrescribir el primer cambio ni modificar parcialmente datos o pruebas.
9. **Dados** dos guardados simultáneos basados en la misma versión, **cuando** ambos intentan modificar el tipo, **entonces** como máximo uno se acepta y el otro recibe un conflicto; la configuración resultante coincide íntegramente con el guardado aceptado, sin mezclar nombre, descripción o pruebas de ambos intentos.
10. **Dado** un conflicto, **cuando** el usuario revisa la configuración vigente y vuelve a preparar y confirmar sus cambios sobre esa versión, **entonces** el guardado puede aceptarse si sigue vigente; si hubo otra modificación, se rechaza de nuevo. Un reenvío del guardado desactualizado no fuerza la actualización.
11. **Dada** una actualización válida, **cuando** falla el guardado de datos o del conjunto de pruebas, **entonces** se conserva íntegramente la configuración y versión previas, sin publicar una versión parcialmente actualizada.

---

### User Story 3 - Desactivar y conservar historial (Priority: P3)

Como responsable técnico autorizado, quiero retirar un tipo de nuevas creaciones sin perder las referencias de estudios que ya lo utilizaron.

**Why this priority**: Evita usar tipos retirados y conserva trazabilidad.

**Independent Test**: Desactivar un tipo y verificar su disponibilidad; la protección de tipos utilizados y sus referencias se validarán con los modelos ya integrados de US 5.1, sin crear otros modelos de estudios.

**Acceptance Scenarios**:

1. **Dado** un tipo usado en estudios, **cuando** se intenta eliminar, **entonces** se impide la eliminación y se permite desactivarlo.
2. **Dado** un tipo, **cuando** se confirma su desactivación tras revisar el resumen, **entonces** deja de estar disponible para nuevos estudios y los anteriores conservan referencias y pruebas.
3. **Dado** un estudio en revisión cuyo tipo se desactiva antes de crearse, **cuando** se intenta confirmar, **entonces** se rechaza e informa que debe elegirse otro tipo disponible.
4. **Dada** una desactivación pendiente, **cuando** se cancela, **entonces** se conserva la disponibilidad anterior.
5. **Dado** un usuario sin sesión, **cuando** intenta administrar tipos, **entonces** debe iniciar sesión y no se guardan cambios.
6. **Dado** un usuario autenticado sin el permiso específico de gestión del catálogo, **cuando** intenta acceder a la gestión o enviar directamente una creación, edición o desactivación, **entonces** se rechaza la operación sin cambios; la sesión activa por sí sola no concede autorización.
7. **Dado** un usuario con sesión activa y el permiso específico de gestión del catálogo, **cuando** administra tipos válidos, **entonces** puede crear, editar y desactivar con las validaciones y confirmaciones previstas. La denominación responsable técnico se representa mediante esa autorización, sin exigir un nuevo rol de dominio.

### Edge Cases

- Dos altas o ediciones concurrentes intentan usar el mismo nombre: no pueden quedar nombres duplicados según la equivalencia acordada en FR-015.
- Dos ediciones modifican el mismo tipo: se detecta la versión desactualizada y se rechaza el guardado con conflicto; se permite revisar la configuración vigente sin sobrescribir cambios ajenos (FR-017).
- La misma prueba se envía varias veces: se conserva una sola pertenencia, porque la composición es un conjunto.
- Una prueba deja de existir antes del guardado: se rechaza sin referencias inválidas ni cambios parciales.
- Desactivación y creación de estudio concurrentes: o el estudio se crea válidamente antes de la desactivación o se rechaza; no se crea después con un tipo no disponible.
- Durante la edición puede vaciarse temporalmente la selección, pero no confirmarse sin una prueba.
- Cambiar nombre o descripción de un tipo usado no modifica los textos históricos conservados por estudios existentes, incluso si la descripción histórica estaba vacía (FR-016).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema MUST exigir sesión activa y permiso específico de gestión del catálogo para gestionar tipos, según FR-014.
- **FR-002**: El sistema MUST permitir crear tipos con nombre obligatorio y único y descripción opcional; se rechaza el nombre vacío o solo con espacios. Se aplican las reglas de comparación de FR-015 al crear y editar.
- **FR-003**: El sistema MUST permitir seleccionar solo pruebas existentes y asociar cada una una sola vez al tipo.
- **FR-004**: El sistema MUST impedir guardar tipos sin al menos una prueba, al crear y al editar.
- **FR-005**: El sistema MUST permitir editar nombre, descripción y composición conservando la identidad del tipo y las validaciones del alta.
- **FR-006**: El sistema MUST aplicar cambios de composición solo a estudios futuros; los existentes conservan sus pruebas asignadas independientemente de la composición actual, además del nombre y descripción históricos del tipo conforme a FR-016.
- **FR-007**: El sistema MUST impedir eliminar tipos usados en estudios y permitir desactivarlos conservando referencias y asignaciones históricas.
- **FR-008**: El sistema MUST excluir tipos desactivados de nuevas creaciones de estudios y rechazar confirmaciones anteriores a la creación si la desactivación ya tuvo efecto.
- **FR-009**: El sistema MUST mostrar resumen y exigir confirmación antes de crear, editar o desactivar; cancelar no guarda cambios. Los errores identifican qué corregir y conservan valores válidos.
- **FR-010**: El sistema MUST guardar datos y composición como una operación completa o no guardar ningún cambio de esa operación.
- **FR-011**: El sistema MUST consumir pruebas científicas existentes sin crear, modificar o deducir fórmulas, unidades, límites, curvas u otras definiciones científicas. Sin pruebas precargadas, informa la dependencia y no permite guardar tipos vacíos.
- **FR-012 — contrato funcional adoptado por el usuario**: US 5.5 es responsable de TipoEstudio y su relación con las pruebas existentes; ofrece configuración y disponibilidad coherentes. US 5.1 es responsable de Estudio, sus pruebas asignadas y los snapshots históricos de nombre y descripción del tipo. Si cambia la composición antes de crear el estudio, US 5.1 muestra la actualizada y exige nueva confirmación explícita; ante concurrencia, o la creación íntegra precede al cambio o se rechaza la confirmación anterior. No se mezclan configuraciones ni se acepta otro conjunto silenciosamente. La base persistente única se entregó en US 5.1; US 5.5 agrega su gestión, sin duplicar entidades ni ampliar definiciones científicas. No se atribuye aprobación global del equipo a esta distribución.
- **FR-013**: El sistema MUST mantener nombre único y conjunto no vacío ante operaciones concurrentes sin modificar retrospectivamente asignaciones de estudios existentes.
- **FR-014 — decisión aprobada por el usuario**: El sistema MUST autorizar la gestión de tipos a usuarios con permiso específico de gestión del catálogo. Una sesión activa sin esa autorización no basta; el control cubre acceso y operaciones enviadas directamente. No se crea por esta decisión un rol de dominio Responsable técnico ni se equipara automáticamente con ser administrador. La autorización específica ya está declarada en la base compartida; su aplicación en gestión y asignación administrativa se revisarán en el diseño, sin ampliar la historia a una nueva gestión de roles.
- **FR-015 — decisión aprobada por el usuario**: El sistema MUST recortar espacios laterales del nombre y comprobar su unicidad ignorando mayúsculas y minúsculas. Las tildes y espacios internos sí distinguen nombres. El nombre sigue siendo obligatorio y no puede quedar vacío tras recortarlo. La descripción es opcional y puede quedar vacía, tanto al crear como al editar. La edición conserva su propia identidad y no se considera duplicado de sí misma.
- **FR-016 — decisión aprobada por el usuario**: Los estudios existentes MUST conservar el nombre y descripción históricos del tipo recibidos al crearse, además de sus pruebas asignadas y referencia al tipo. Renombrar, editar la descripción o desactivar el tipo no reescribe esos textos, incluida una descripción histórica vacía. Los estudios posteriores reciben los textos vigentes que correspondan a su creación. El contrato compartido asigna esos snapshots a US 5.1; su preservación y consumo ya están implementados por US 5.1. US 5.5 debe respetarlos al administrar las mismas entidades; no recrea ni reescribe estudios.
- **FR-017 — decisión adoptada por el usuario**: El sistema MUST detectar y rechazar todo guardado de edición basado en una versión desactualizada del tipo. Se informa el conflicto y se permite revisar la configuración vigente antes de preparar y confirmar una nueva edición; no se sobrescribe automáticamente. La comprobación y actualización de nombre, descripción, disponibilidad cuando corresponda y conjunto de pruebas MUST constituir una única operación atómica, incluso con guardados simultáneos. Toda modificación efectiva de esos datos invalida la versión anterior para ediciones; las fallas no publican cambios de datos o versión. Una desactivación también invalida una edición abierta previamente.
- **FR-018 — decisión funcional confirmada por el usuario el 28/10/2026**: Permitir reactivar tipos desactivados con el permiso específico de gestión del catálogo, resumen y confirmación explícita y una versión vigente, validando que tengan al menos una prueba válida del catálogo existente. Si alguna referencia seleccionada no es válida, se rechaza sin reactivación parcial. Al reactivarse vuelven a estar disponibles para estudios nuevos; no se modifica ningún estudio existente, sus asignaciones ni sus snapshots. Se aplica el control de versión y atomicidad de FR-017. Es una decisión del proyecto académico confirmada por el usuario; no se atribuye a un laboratorio real ni acredita por sí sola aprobación formal global de la spec por el equipo.
- **FR-019 — decisión funcional confirmada por el usuario el 28/10/2026**: Permitir eliminar definitivamente solo tipos que nunca hayan sido utilizados en estudios, con permiso específico de gestión del catálogo, resumen, confirmación explícita y comprobaciones vigentes de versión y utilización. Cualquier estudio asociado, incluso histórico y aunque el tipo esté desactivado, impide eliminarlo; se ofrece desactivación como alternativa. La comprobación y eliminación deben preservar integridad ante operaciones concurrentes: nunca se permite borrar un tipo que ha quedado asociado a un estudio ni crear referencias a un tipo eliminado. No se borran las pruebas científicas del catálogo. Es una decisión del proyecto confirmada por el usuario; complementa el criterio original de impedir eliminar tipos usados, sin atribuirla a un laboratorio real ni acreditar aprobación formal global del equipo.

### Key Entities *(include if feature involves data)*

Entidades funcionales del contrato ya sustentadas por la infraestructura integrada de US 5.1. Se reutilizan sus identidades; no se propone un nuevo modelo científico ni otra base de catálogo:

- **Prueba**: Elemento existente del catálogo compartido con identidad estable, código y nombre. Puede ser ficticio y estar identificado como DEMO; su alta/carga no pertenece a la gestión de tipos. US 5.1 aporta un cargador demo explícito, reproducible e idempotente, separado de migraciones. No se redefine en US 5.5.
- **Tipo de estudio**: Agrupación reutilizable con identidad estable, nombre único, descripción, disponibilidad y conjunto no vacío de pruebas predeterminadas.
- **Composición del tipo**: Pertenencia de pruebas al tipo; un tipo contiene una o más pruebas y una prueba puede reutilizarse en varios tipos. Editarla no modifica las asignaciones ya hechas a estudios.
- **Estudio, consumidor de US 5.1**: Referencia una muestra y un tipo y conserva su propio conjunto de pruebas asignadas y el nombre y descripción históricos del tipo al crearse. No se crea o administra desde US 5.5.
- **Prueba asignada al estudio, responsabilidad de US 5.1**: Referencia a una prueba del catálogo asignada a un estudio concreto. Su pertenencia no se reconstruye permanentemente desde la composición actual del tipo.
- **Versión de configuración del tipo**: Identificación de un estado coherente de sus datos y composición para detectar ediciones desactualizadas. Es parte del contrato compartido ya implementado por US 5.1; la gestión administrativa debe respetar esa identidad de configuración y su invalidación, sin crear otro versionado incompatible.

### Escenarios de reactivación y eliminación confirmados por el usuario

El usuario confirmó estas reglas como decisiones funcionales del proyecto. Sus escenarios definen el alcance para planificar; no se atribuyen a un laboratorio real ni acreditan por sí solos aprobación formal global del equipo.

1. **Dado** un tipo desactivado con al menos una prueba y todas sus referencias válidas, **cuando** un usuario con permiso específico revisa y confirma reactivarlo sobre su versión vigente, **entonces** vuelve a estar disponible para estudios nuevos sin cambiar ningún estudio existente, sus pruebas ni sus snapshots.
2. **Dado** un tipo desactivado sin pruebas o con una referencia seleccionada inválida, **cuando** se intenta confirmar la reactivación, **entonces** se informa el error y permanece desactivado sin cambios parciales.
3. **Dado** un usuario sin permiso específico, **cuando** intenta reactivar o eliminar un tipo, incluso enviando directamente la operación, **entonces** se rechaza sin cambios.
4. **Dado** un tipo nunca utilizado en estudios, **cuando** un usuario autorizado revisa y confirma su eliminación sobre datos vigentes y sigue sin haber sido utilizado, **entonces** se elimina definitivamente el tipo y sus asociaciones de composición, sin borrar las pruebas científicas del catálogo.
5. **Dado** un tipo con cualquier estudio asociado, incluso histórico, **cuando** se intenta eliminar definitivamente, **entonces** se impide la eliminación y se ofrece desactivación como alternativa; estar desactivado no habilita su eliminación.
6. **Dado** un intento de eliminación y una primera creación de estudio concurrentes, **cuando** se resuelven, **entonces** o el tipo se elimina antes y no se crea el estudio, o el estudio se crea primero y se impide eliminar el tipo. Nunca queda un estudio referenciando un tipo eliminado.
7. **Dada** una reactivación o eliminación en revisión, **cuando** se cancela, **entonces** se conserva el estado previo. Si falla el guardado o la eliminación, tampoco quedan cambios parciales.
8. **Dado** un intento de reactivación o eliminación basado en una versión desactualizada, **cuando** se confirma, **entonces** se informa el conflicto, no se aplica la operación y se permite revisar la configuración vigente. Reenviar la confirmación anterior no fuerza la operación.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Todos los tipos creados en casos válidos conservan nombre, descripción y exactamente las pruebas confirmadas, con al menos una y sin repeticiones.
- **SC-002**: El 100% de intentos con nombre ausente, duplicado o sin pruebas se rechaza sin cambios parciales.
- **SC-003**: El 100% de estudios usados en validación de integración conserva sus pruebas y el nombre y descripción históricos del tipo tras editarlo o desactivarlo; los posteriores reciben los textos y composición vigentes de configuraciones disponibles y confirmadas.
- **SC-004**: Todos los intentos de eliminar tipos usados se rechazan conservando referencias; los desactivados no se ofrecen para nuevos estudios.
- **SC-005**: Todas las cancelaciones y fallas de guardado de los casos de aceptación conservan el estado anterior del catálogo.
- **SC-006**: Ningún caso de aceptación de US 5.5 crea o modifica definiciones científicas.
- **SC-007 — contrato adoptado, verificación futura**: En todos los casos de edición o desactivación concurrente con creación de estudio, no quedan estudios con pruebas mezcladas, no confirmadas o asignadas después de retirarse el tipo. US 5.1 ya implementa el consumo coherente; falta implementar y verificar el escritor US 5.5 con esa base real. No está pendiente decidir de nuevo esta política.
- **SC-008**: Todos los accesos y operaciones de gestión sin permiso específico se rechazan sin cambios; los usuarios autorizados pueden completar los casos válidos. Todos los casos de nombres equivalentes según FR-015 se rechazan como duplicados, y la descripción vacía se admite.
- **SC-009**: El 100% de las ediciones basadas en versiones desactualizadas se rechaza con conflicto sin cambios parciales. En guardados simultáneos de una misma versión se acepta como máximo uno; los datos y pruebas publicados coinciden íntegramente con esa operación. Todos los casos de falla conservan la configuración y versión previas.
- **SC-010 — decisión funcional confirmada por el usuario**: En todos los casos válidos de reactivación, el tipo vuelve a estar disponible para estudios nuevos sin alterar los existentes; todos los casos sin permiso, sin pruebas válidas o con versión desactualizada se rechazan sin cambios.
- **SC-011 — decisión funcional confirmada por el usuario**: Todas las eliminaciones aceptadas corresponden a tipos nunca utilizados; todo intento sobre tipos con cualquier estudio asociado se rechaza. Los casos concurrentes con creación de estudio no producen referencias inválidas ni borran pruebas científicas.

## Assumptions

### Fuentes y estado de decisiones

- **Alcance confirmado**: criterios originales de US 5.5 y la lista de decisiones expresamente confirmadas por el usuario el 28/10/2026: permiso específico, unicidad/nombre, descripción opcional, al menos una prueba, historial, versiones, reactivación y eliminación solo de nunca usados.
- **Constitution y guía**: [Constitution](../../.specify/memory/constitution.md) exige spec aprobada por el equipo antes de código de producto. La [guía SDD](../../docs/guias/guia-sdd-paso-a-paso.md) pide revisar la spec antes de plan y aclara que la checklist no reemplaza la revisión del equipo. No se modifica ninguna.
- **Base integrada**: US 5.1 se integró por PR #12 (07b89bc); origin/main y esta rama apuntan a a95efb46db9b94a8913d44f8dbff8fd4c8482d81, que además integra US 5.2 por PR #16. Los modelos, snapshots y consumidor compartido existen; la gestión US 5.5 no existe todavía.
- **Datos FIUBA**: el backlog contiene una tarea histórica de precarga; no se interpreta como una dependencia de un científico o laboratorio real. Se permiten datos ficticios identificados y fixtures aisladas, sin atribuir validez científica. No se deducen fórmulas, límites ni normas. El cargador demo de US 5.1 se reutiliza si corresponde, siempre explícitamente; no se ejecutó en este diagnóstico.
- **Planificación**: el orden definitivo fue US 5.1 primero y US 5.5 después. Las dos specs ya están disponibles en esta base; no se modifica US 5.1. Jira continúa pendiente administrativo, sin inventar claves.
- **Revisión pendiente**: el usuario desea revisar este diagnóstico antes de autorizar plan. No hay aclaraciones funcionales abiertas en las reglas confirmadas. No se inventa aprobación formal global del equipo; deberá acreditarse antes de implementar según Constitution.
- **Alcance excluido**: crear/editar definiciones de Prueba, mediciones, resultados, fórmulas, límites, validación científica, informes, creación de estudios y agregar/quitar pruebas de un estudio. Reactivación y eliminación de nunca usados están confirmadas para US 5.5 con las condiciones de FR-018/019.

### Contrato mínimo funcional adoptado para US 5.1

| Elemento | Contrato vigente | Infraestructura disponible / trabajo US 5.5 |
|---|---|---|
| Prueba identificable | Una definición compartida con identidad estable, código único y nombre; datos académicos, sin atributos científicos nuevos | Existe en la base US 5.1; no duplicar ni convertir US 5.5 en gestión de pruebas. |
| Tipo identificable | Identidad estable, nombre único conforme a FR-015, descripción opcional, disponibilidad y versión | Persistencia existente; faltan las operaciones administrativas autorizadas. |
| Composición | Pruebas existentes, sin duplicados, conjunto final no vacío | Relación compartida existente; la validación de conjunto final y su escritura atómica son responsabilidad del nuevo flujo US 5.5. |
| Historial | Cada estudio conserva sus pruebas y textos históricos; referencia estable al tipo | US 5.1 ya copia snapshots y asignaciones; US 5.5 no los reescribe. |
| Cambios durante revisión | Versión de configuración y lectura coherente; el consumidor exige nueva confirmación si cambió | El consumidor US 5.1 está implementado; US 5.5 debe publicar cambios coherentes e invalidar versiones antiguas. |
| Protección de uso | Un tipo con cualquier estudio asociado, incluso histórico, no se elimina | Relación protectora existente; falta comprobar uso/versión y aplicar la eliminación autorizada sin carreras. |

La propiedad funcional de TipoEstudio y composición sigue siendo US 5.5, aunque su base persistente mínima la entregó US 5.1. Esta historia administra esas mismas entidades. Ver [diagnóstico de infraestructura existente](diagnostico-previo-plan.md) y [contrato integrado del consumidor](../008-crear-estudio/contracts/catalogo-compartido.md). El primero registra hechos del código actual, no es un plan técnico nuevo.

#### Interfaces funcionales mínimas

Describen entradas, salidas y garantías funcionales. La lectura para crear estudios ya existe; el diseño futuro definirá las interfaces administrativas faltantes sin reemplazar el consumidor.

| Operación y responsable | Entrada mínima | Salida o resultado funcional |
|---|---|---|
| Ofrecer tipos disponibles — US 5.5 | Solicitud del consumidor | Identidad, nombre, descripción opcional y disponibilidad de los tipos seleccionables. |
| Consultar configuración — US 5.5 | Identidad del tipo | Identidad, nombre, descripción, disponibilidad, versión de configuración y conjunto de referencias estables a pruebas con código y nombre, leídos como una configuración coherente; o tipo inexistente. |
| Guardar edición — US 5.5 | Identidad, versión revisada, nombre, descripción y conjunto propuestos; usuario autorizado | Configuración íntegra y su versión vigente, o conflicto con acceso a la configuración actual, error de validación o falta de autorización. Nunca guardado parcial. |
| Desactivar — US 5.5 | Identidad, versión revisada y confirmación de usuario autorizado | Tipo no disponible y versión actualizada, o conflicto, rechazo o cancelación sin cambios. |
| Crear estudio con configuración confirmada — US 5.1, coordinada con catálogo | Identidad del tipo, configuración/versión revisada y datos de la solicitud propios de US 5.1 | US 5.1 guarda estudio, pruebas asignadas y snapshots coherentes con la creación, o rechaza por cambio/no disponibilidad y exige revisión; US 5.5 no crea estudios. El consumidor integrado y su contrato de coordinación se reutilizan; falta el escritor administrativo de US 5.5. |
| Consultar utilización para protección — coordinación US 5.5 / US 5.1 | Identidad estable del tipo | Condición de uso confiable para impedir eliminar un tipo utilizado, incluso concurrentemente. US 5.1 es dueña de los estudios; no se replica su modelo en US 5.5. La eliminación de nunca usados está confirmada en FR-019. |
| Reactivar — decisión confirmada por el usuario | Identidad, versión revisada y confirmación de usuario con permiso específico | Tipo disponible con al menos una prueba válida, o rechazo/conflicto sin cambios ni modificación de estudios existentes. |
| Eliminar definitivamente — decisión confirmada por el usuario | Identidad, versión revisada, condición de nunca utilizado y confirmación de usuario con permiso específico | Eliminación íntegra solo si nunca fue usado; en caso de uso se rechaza y ofrece desactivación. Se preservan referencias concurrentes y pruebas científicas. |

Para preservar el historial, cada estudio conserva sus propias referencias de pruebas y los textos históricos del tipo al crearse. Editar composición, nombre o descripción del tipo no reemplaza esos datos; los cambios afectan a futuras creaciones. La conservación ya está incorporada al consumidor de US 5.1 y se respetará al desarrollar su escritor US 5.5. No se fija aquí versionado de fórmulas, unidades o límites.

### Dependencias y validación futura

1. Reutilizar el catálogo mínimo y el consumidor integrados de US 5.1. No hay bloqueo por ausencia de modelos, asignaciones, snapshots o fuente científica externa.
2. Revisar el diagnóstico y esta actualización antes de autorizar plan. La aprobación formal del equipo no se da por aportada; Constitution la requiere antes de código de producto. La checklist refleja calidad documental y no sustituye esa aprobación.
3. Planificar las operaciones de gestión y sus tests: permisos, validaciones, confirmaciones/cancelación, conflictos entre editores, atomicidad, historial, reactivación y eliminación concurrente con creación de estudios. Los helpers existentes de tests no prueban un CRUD US 5.5 todavía inexistente.
4. Datos de test/demo claramente ficticios, cargas explícitas, sin redefinir pruebas ni cargar automáticamente al iniciar o migrar.
5. US 4.1 y US 5.2 están integradas en la base; no se copian ni modifican. FR-013/014 de US 5.1 son decisiones definitivas del proyecto, no supuestos externos abiertos. US 5.3/5.4 se mantienen fuera del alcance de gestión del catálogo.

### Separación de ramas y artefactos

- US 5.5: 012-Gestionar-Catalogo-Estudios, specs/012-gestionar-tipos-estudio/, worktree E:/Codex/worktrees/us55-tipos-estudio/AquaLab.
- La rama avanzó de 2541b857 a a95efb46 de manera segura tras verificar respaldo y relación de descendencia; no se hizo merge, rebase ni commit nuevo y se preservaron los borradores locales.
- Los otros worktrees no se modifican. La actualización incorpora los archivos ya versionados en main a este checkout; las únicas ediciones propias de esta tarea son documentación US 5.5.

## Historial de aclaraciones — se conserva, no redefine el estado vigente

Las condiciones de laboratorio, orden de implementación y propuestas pendientes de las sesiones anteriores quedan sustituidas por las confirmaciones y comprobaciones anteriores. No se borra ni altera ese registro histórico.

## Clarifications

### Session 2026-10-27

- Q1 / FR-014: ¿Quién gestiona tipos como responsable técnico? → Respuesta del usuario: usuarios con permiso específico de gestión del catálogo. Se añade cobertura para accesos y operaciones sin autorización; no se presupone un rol de dominio nuevo.
- Q2 / FR-015: ¿Aprobar comparación sin distinguir mayúsculas ni espacios laterales, conservar diferencias de tildes y espacios internos y permitir descripción vacía? → Respuesta del usuario: aprobado. Se aplica a alta y edición.
- Q3 / FR-016: ¿Qué textos muestran los estudios anteriores si cambia el tipo? → Respuesta del usuario: conservar nombre y descripción históricos. Se incorpora la obligación funcional al historial y al contrato propuesto con US 5.1, sin implementar ni modificar su spec.
- Las primeras tres respuestas cerraron FR-014 a FR-016. Posteriormente el usuario adopta el reparto de responsabilidades FR-012 y la detección y rechazo de guardados desactualizados FR-017, con actualización atómica del tipo y su conjunto. Ya no se registran esos dos puntos como políticas por decidir; no se acredita implementación ni integración.
- Reactivación FR-018 y eliminación definitiva de tipos nunca utilizados FR-019: el usuario adopta las propuestas y sus reglas funcionales, sujetas a aprobación formal del equipo. Se precisan autorización, validaciones, efecto sobre disponibilidad, protección de cualquier estudio histórico, alternativa de desactivación y garantías concurrentes. Se sustituyen las preguntas de elección funcional por un estado explícito de aprobación pendiente; no se registra aprobación inexistente.
- Se mantiene Draft, sin pasar a plan, sin modificar US 5.1 y sin implementar entidades o interfaces. La aprobación global del equipo y el acuerdo sobre dependencias científicas no se presuponen.

### Condiciones pendientes para aprobación y paso a diseño

1. Obtener y registrar la aprobación formal del equipo de la spec completa, incluidas las propuestas FR-018 y FR-019 y sus condiciones. No basta la adopción individual del usuario para afirmar que esa aprobación ya existe.
2. Acordar y documentar el límite de la dependencia científica: quién proporciona y mantiene la entidad Prueba y sus identidades, quién entrega/valida la fuente oficial y quién ejecuta la tarea separada de precarga. No es necesario haber cargado todos los datos ni ejecutar integración antes de aprobar la spec, pero no debe diseñarse suponiendo modelos o fuentes no acordados.
3. Tras esa evidencia, revalidar los controles documentales pendientes y revisar la coherencia del contrato al retomar US 5.1. La sincronización posterior de su borrador no se da por realizada; sus validaciones de laboratorio FR-013/FR-014 no se cierran por aprobar US 5.5.
4. Solo después de la revisión de la spec, y con autorización para continuar, ejecutar plan mediante el Spec Kit instalado. Las decisiones de módulo, versión, persistencia, permisos concretos y coordinación transaccional pertenecen a ese diseño técnico; no son requisitos de implementación que deban existir ya para aprobar la especificación.

Las claves/enlaces Jira permanecen pendientes administrativos por instrucción del usuario y no bloquean por sí solos la aprobación funcional. Tampoco se exige CI ni tests de implementación en esta fase exclusivamente documental.



### Session 2026-10-28 — preparación previa a plan

El usuario confirma expresamente las reglas FR-014 a FR-019 y la reactivación/eliminación con sus condiciones. Aclara el contexto académico FIUBA. Se verifica US 5.1 integrada en origin/main y se reutiliza la base real; se eliminan del estado vigente los bloqueos documentales por modelos inexistentes, validación de laboratorio o fuente científica oficial. Las reglas funcionales quedan cerradas por el usuario; no se registra una aprobación formal global del equipo inexistente. El usuario pide revisar este diagnóstico antes de ejecutar plan: no se ejecutó setup-plan.sh ni se generaron sus artefactos.
