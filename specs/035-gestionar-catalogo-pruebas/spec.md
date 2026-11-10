# Feature Specification: Gestionar catálogo de pruebas

**Feature Branch**: `035-gestionar-catalogo-pruebas`

**Created**: 2026-11-10

**Status**: Borrador

**Input**: User description: "SCRUM-73 – Gestionar catálogo de pruebas. Como administrador del laboratorio quiero dar de alta, editar y desactivar pruebas del catálogo desde la app, con reglas que protejan los estudios ya hechos, para mantener el catálogo al día sin entrar al admin de Django. Criterios de aceptación: (1) Desde «Administración» → Catálogo de pruebas (SCRUM-71) se puede crear una prueba: código, nombre, tipo de cálculo, fórmula (solo si el tipo es fórmula), unidades, límites por tipo de vertido, norma y límite de detección. La fórmula se valida al guardar. (2) Si la prueba no está en uso (no está en ningún tipo ni estudio), se puede editar todo y también eliminarla, con confirmación. (3) Si la prueba está en uso: se pueden editar los límites, la norma, el límite de detección y la observación, y el cambio solo afecta las validaciones futuras; el código, el nombre, el tipo de cálculo, la fórmula y las unidades quedan bloqueados, con un mensaje que explica que, para cambiar el método, hay que crear una prueba nueva y desactivar la anterior; no se puede eliminar, solo desactivar. (4) Desactivar o reactivar, con confirmación. Una prueba inactiva no se ofrece al armar tipos de estudio ni al agregar pruebas a un estudio. Donde ya estaba asignada sigue funcionando: se le cargan mediciones, se calcula, se valida y se informa. (5) Los informes emitidos y las validaciones hechas no cambian al editar una prueba. (6) Solo el grupo «Administradores» puede gestionar el catálogo. El resto recibe un error 403. Fuera de alcance: las curvas de calibración (próximo sprint) y la importación masiva desde CSV (sigue el comando importar_catalogo_pruebas). Depende de: SCRUM-71, porque usa la sección y el grupo «Administradores»."

## Clarifications

### Session 2026-11-10

- Q: Al cargar los límites de una prueba, ¿el sistema tiene que controlar lo que se escribe o acepta cualquier texto, como hoy? → A: Solo se aceptan números (coma o punto) y «Ausente»/«Ausencia»; cualquier otro texto se rechaza, y si mínimo y máximo son números, el mínimo no puede superar al máximo. «Ausente» significa «no detectado» (0 o por debajo del límite de detección) y es el límite de las pruebas de presencia (A/P) y de mediciones con límite de detección como Sólidos sedimentables; para conteos enteros que no deben aparecer (ej. Coliformes fecales, ajuste de la US 8.4) se usa máx. 0. El formulario lo explica en la ayuda del campo.
- Q: ¿La ficha de cada prueba tiene que mostrar quién la modificó por última vez y cuándo? → A: Sí. Se guarda quién la creó y quién la modificó por última vez, con fecha, y se muestra en la ficha; el historial completo de cambios queda fuera de alcance.
- Q: Al desactivar una prueba que está en tipos de estudio, ¿la confirmación tiene que avisar qué tipos la incluyen? → A: Sí. Lista los tipos de estudio activos que la incluyen («Los estudios nuevos de estos tipos no la van a incluir») y marca los que se quedarían sin ninguna prueba activa («Este tipo no se va a poder usar»); se puede confirmar igual.
- Q: Si reemplazo una prueba por una nueva (ej. Calcio por Calcio nuevo), ¿hay que crear también una versión nueva de cada prueba que la usa en su fórmula (ej. Magnesio)? → A: No. Al desactivar se puede elegir «Reemplazar por» otra prueba y el sistema actualiza en cascada las fórmulas de todas las pruebas que la usan y los tipos de estudio que la incluyen; los estudios ya hechos siguen calculándose con la prueba vieja. Vale para cualquier prueba, no solo Calcio. Cambia el criterio 3 de Jira (ya no hace falta recrear las pruebas que dependen de la reemplazada).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Dar de alta una prueba (Priority: P1)

Como administrador, desde «Administración → Catálogo de pruebas» toco «Nueva prueba», completo sus datos (código, nombre, tipo de cálculo, fórmula si corresponde, unidades, límites generales y por tipo de vertido, norma, límite de detección y observación), reviso un resumen y confirmo. La prueba queda activa en el catálogo, lista para usarse en tipos de estudio.

**Why this priority**: Sin alta no hay gestión: es lo que hoy obliga a entrar al admin de Django o a reimportar el CSV.

**Independent Test**: Crear una prueba Directa y otra de tipo Fórmula que referencie a la primera; verificar que aparecen activas en el listado y que se ofrecen al armar un tipo de estudio. Intentar crear una con fórmula inválida o código repetido y verificar el error junto al campo.

**Acceptance Scenarios**:

1. **Dado** el listado del catálogo, **cuando** el administrador toca «Nueva prueba», completa los datos y confirma en el resumen, **entonces** la prueba se crea activa y se vuelve al listado con un mensaje de éxito.
2. **Dado** el tipo de cálculo «Directo», **cuando** se completa el formulario, **entonces** la fórmula no se pide ni se guarda; **dado** «Fórmula», **entonces** la fórmula es obligatoria.
3. **Dada** una fórmula con errores de escritura, que referencia una prueba inexistente o que se referencia a sí misma, **cuando** se intenta guardar, **entonces** se rechaza con el motivo junto al campo fórmula y no se crea nada.
4. **Dado** un código que ya existe (sin distinguir mayúsculas), **cuando** se intenta guardar, **entonces** se rechaza indicándolo.
5. **Dados** límites para Cloacal o Canal, **cuando** se guarda, **entonces** quedan como límites propios de ese tipo de vertido; si se dejan vacíos, ese vertido usa los límites generales.
6. **Dado** el resumen previo, **cuando** se cancela, **entonces** se vuelve al formulario con los datos cargados y no se crea nada.

---

### User Story 2 - Editar o eliminar una prueba sin uso (Priority: P1)

Como administrador, abro una prueba que todavía no está en ningún tipo de estudio ni estudio, corrijo cualquier dato y confirmo; o la elimino con confirmación si fue un error.

**Why this priority**: Corregir errores de carga es la tarea más frecuente del catálogo.

**Independent Test**: Con una prueba recién creada y sin uso, cambiar código, nombre, tipo, fórmula y unidades; después eliminarla y verificar que ya no existe.

**Acceptance Scenarios**:

1. **Dada** una prueba sin uso, **cuando** se abre su ficha, **entonces** todos los campos son editables y se ofrecen «Guardar», «Desactivar» y «Eliminar».
2. **Dada** una prueba sin uso, **cuando** se confirma «Eliminar», **entonces** se borra junto con sus límites por vertido y se vuelve al listado con un mensaje.
3. **Dada** una prueba sin uso pero referenciada en la fórmula de otra prueba, **cuando** se intenta eliminar, **entonces** se rechaza indicando qué pruebas la usan.
4. **Dada** una prueba a la que otras pruebas referencian, **cuando** se intenta cambiar su código, **entonces** se rechaza indicando qué fórmulas la usan (cambiarlo rompería esas fórmulas).

---

### User Story 3 - Editar una prueba en uso sin alterar el historial (Priority: P1)

Como administrador, abro una prueba que ya está en tipos de estudio o estudios y actualizo sus límites, norma, límite de detección u observación. Los datos que definen el método (código, nombre, tipo de cálculo, fórmula y unidades) se ven bloqueados con una explicación.

**Why this priority**: Es la regla que protege los estudios ya hechos; los límites cambian con las normas y hay que poder actualizarlos.

**Independent Test**: Con una prueba usada en un estudio validado e informado, cambiar su límite máximo; verificar que el informe emitido y la validación existente no cambian y que una validación nueva usa el límite nuevo.

**Acceptance Scenarios**:

1. **Dada** una prueba en uso, **cuando** se abre su ficha, **entonces** código, nombre, tipo de cálculo, fórmula y unidades se muestran bloqueados con el mensaje «Esta prueba ya se usa en tipos de estudio o estudios: su método no se puede cambiar. Para cambiarlo, creá una prueba nueva y desactivá esta.», y no se ofrece «Eliminar».
2. **Dada** una prueba en uso, **cuando** se cambian límites, norma, límite de detección u observación y se confirma, **entonces** se guardan.
3. **Dado** un intento de cambiar un dato bloqueado por otra vía (por ejemplo, un envío modificado), **cuando** se procesa, **entonces** se rechaza sin cambios.
4. **Dada** una prueba en uso con validaciones e informes, **cuando** se cambian sus límites, **entonces** las validaciones ya hechas y los informes emitidos muestran los límites y la evaluación de antes; las validaciones siguientes usan los nuevos.

---

### User Story 4 - Desactivar y reactivar (Priority: P2)

Como administrador, desactivo una prueba que el laboratorio dejó de usar o que se reemplazó, y la reactivo si vuelve a hacer falta, siempre con confirmación.

**Why this priority**: Es la única forma de retirar pruebas con historial; depende de que el alta y la edición existan.

**Independent Test**: Desactivar una prueba asignada a un tipo de estudio y a un estudio en curso; verificar que no se ofrece al armar tipos ni al agregar pruebas, que los estudios nuevos de ese tipo no la incluyen y que el estudio en curso sigue cargando, calculando, validando e informando. Reactivarla y verificar que vuelve a ofrecerse.

**Acceptance Scenarios**:

1. **Dada** una prueba activa, **cuando** se confirma «Desactivar», **entonces** queda inactiva y el listado lo indica.
2. **Dada** una prueba inactiva, **cuando** se arma o edita un tipo de estudio, o se agregan pruebas a un estudio, **entonces** no se ofrece.
3. **Dado** un tipo de estudio que incluye una prueba inactiva, **cuando** se crea un estudio nuevo de ese tipo, **entonces** el estudio se crea solo con las pruebas activas del tipo; si el tipo no tiene ninguna activa, la creación se rechaza con un mensaje que lo explica.
4. **Dado** un estudio que ya tenía la prueba asignada, **cuando** la prueba se desactiva, **entonces** se le siguen cargando mediciones, se calcula, se valida y se informa como antes.
5. **Dada** una prueba incluida en tipos de estudio activos, **cuando** se va a desactivar, **entonces** la confirmación lista esos tipos, avisa que los estudios nuevos no la van a incluir y marca los que se quedarían sin pruebas activas; se puede confirmar igual.
6. **Dada** una prueba que la fórmula de alguna prueba **activa** referencia, **cuando** se va a desactivar, **entonces** la confirmación avisa qué pruebas la usan y que en los estudios nuevos no se van a poder calcular hasta que la reemplacen; se puede confirmar igual.
7. **Dada** una prueba activa cuya fórmula referencia una prueba inactiva, **cuando** se muestra el listado del catálogo, **entonces** queda marcada con «Depende de una prueba inactiva: <códigos>», para que se reemplace.
8. **Dada** una prueba inactiva, **cuando** se confirma «Reactivar», **entonces** vuelve a estar activa y a ofrecerse; si su fórmula usa alguna prueba inactiva, la confirmación lo avisa («Usa en su fórmula una prueba inactiva: <códigos>») y se puede confirmar igual.
9. **Dada** la confirmación de crear un estudio abierta con un tipo, **cuando** otra persona desactiva o reactiva una prueba de ese tipo antes de confirmar, **entonces** la creación se rechaza con el aviso de que el tipo cambió y no se crea un estudio distinto del confirmado.

---

### User Story 6 - Reemplazar una prueba en cascada (Priority: P2)

Como administrador, cuando el laboratorio cambia el método de una prueba que otras usan en su fórmula (ej. Calcio, que usa Magnesio), creo la prueba nueva y, al desactivar la vieja, elijo «Reemplazar por» la nueva. El sistema actualiza solo las fórmulas que la usaban y los tipos de estudio que la incluían, sin que tenga que recrear las pruebas que dependen de ella.

**Why this priority**: Evita recrear en cadena todas las pruebas que dependen de la reemplazada; aplica a cualquier prueba con dependientes.

**Independent Test**: Con `MG` (fórmula con `{CA}`) en uso, crear `CA2`, desactivar `CA` eligiendo «Reemplazar por CA2»; verificar que la fórmula de `MG` usa `{CA2}`, que los tipos tienen `CA2` en lugar de `CA`, que un estudio nuevo calcula `MG` con `CA2` y que en un estudio viejo corregir la medición de `CA` recalcula `MG` igual que antes.

**Acceptance Scenarios**:

1. **Dada** una prueba activa con dependientes o en tipos de estudio, **cuando** se va a desactivar, **entonces** se ofrece «Reemplazar por» con las pruebas activas compatibles (misma unidad del resultado, que no sean ella misma ni dependan de ella); elegir una es opcional.
2. **Dado** un reemplazo elegido, **cuando** se confirma, **entonces** en una sola operación: la prueba queda inactiva y registrada como reemplazada por la nueva; en la fórmula de cada prueba que la referenciaba, `{CODIGO_VIEJO}` pasa a `{CODIGO_NUEVO}`; y en cada tipo de estudio que la incluía, la vieja se cambia por la nueva (si el tipo ya tenía la nueva, solo se quita la vieja).
3. **Dado** el resumen previo, **cuando** se muestra, **entonces** lista exactamente qué fórmulas y qué tipos se van a modificar.
4. **Dado** un estudio creado antes del reemplazo, **cuando** se corrige una medición y se recalcula, **entonces** las fórmulas que ahora nombran la prueba nueva usan el valor de la vieja en ese estudio y el resultado es el mismo que antes del reemplazo.
5. **Dados** reemplazos encadenados (A por B y después B por C), **cuando** se recalcula un estudio que tiene A, **entonces** las fórmulas que nombran C usan el valor de A.
6. **Dados** los resultados, validaciones e informes ya hechos, **cuando** se hace un reemplazo, **entonces** no cambian.
7. **Dada** una prueba con unidad del resultado distinta, **cuando** se intenta elegirla como reemplazo, **entonces** no se ofrece (y si se envía igual, se rechaza): cambiaría el significado de las fórmulas que la usan.
8. **Dada** una prueba activa que se va a desactivar, **cuando** se elige «Crear una prueba nueva para reemplazarla», **entonces** se abre el alta con los datos de la vieja (código vacío, misma unidad del resultado fija) y, al confirmar, en una sola operación se crea la nueva y se hace el reemplazo del escenario 2; si algo falla (código repetido, fórmula que usa la vieja o una que depende de ella), no se crea nada y la vieja sigue activa.

---

### User Story 5 - Solo Administradores (Priority: P2)

Como laboratorio, quiero que solo el grupo «Administradores» gestione el catálogo.

**Why this priority**: Regla de seguridad; reutiliza el acceso del panel de administración (SCRUM-71).

**Independent Test**: Con un bioquímico, un técnico y un superusuario fuera del grupo, verificar 403 en todas las pantallas y acciones del catálogo; con un administrador, acceso completo.

**Acceptance Scenarios**:

1. **Dado** un usuario sin la pertenencia a «Administradores» y el permiso del panel, **cuando** entra a crear, editar, eliminar, desactivar o reactivar por cualquier dirección, **entonces** recibe 403 y no cambia nada (también un superusuario fuera del grupo, como en el resto del panel).
2. **Dado** un usuario sin sesión, **cuando** entra a cualquier pantalla del catálogo, **entonces** se lo lleva al inicio de sesión.

---

### Edge Cases

- Dos administradores editan la misma prueba a la vez: el segundo en confirmar recibe un aviso de que la prueba cambió mientras la editaba y no pisa los cambios del primero.
- La prueba pasa a estar en uso entre abrir la ficha y confirmar (alguien la agregó a un tipo): al confirmar se revalida y, si se tocó un dato bloqueado, se rechaza con el motivo.
- Una prueba de tipo Fórmula cuya fórmula referencia otras pruebas queda marcada como «calculada a partir de otras pruebas» automáticamente; no es un dato que cargue el administrador.
- Pasar de «Fórmula» a «Directo» en una prueba sin uso borra la fórmula.
- Pruebas que hoy tienen límites de texto no comparable (ej. «NE» en Cloro libre cloacal, «SOE» en Olor, «Ph-0,2» en pH de saturación): al editarlas desde la app hay que reemplazar ese límite por un número, «Ausente» o vacío para poder guardar. La importación por CSV no aplica esta regla y sigue aceptando lo que traiga el archivo.
- Una prueba inactiva sigue apareciendo en la consulta del catálogo, en los estudios e informes donde ya estaba y en la importación por CSV (que no la reactiva ni la borra).
- La importación por CSV puede seguir actualizando límites y normas de pruebas existentes; no cambia el nombre de una prueba en uso (regla actual).
- El admin de Django queda como respaldo y no aplica todas estas reglas (por ejemplo, no bloquea las unidades de una prueba en uso): no es el camino habitual.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Desde «Administración → Catálogo de pruebas», el sistema MUST permitir crear una prueba con código, nombre, tipo de cálculo, fórmula (obligatoria solo con tipo Fórmula), unidad de medición, unidad del resultado, límites mínimo y máximo generales, límites por tipo de vertido (Cloacal y Canal, opcionales), norma, límite de detección y observación. La prueba nueva queda activa.
- **FR-002**: Al guardar, el sistema MUST validar la fórmula con la misma regla que hoy usa el catálogo (gramática, referencias a pruebas existentes, sin autorreferencia) y MUST rechazar códigos repetidos sin distinguir mayúsculas.
- **FR-002a**: Los límites mínimo y máximo (generales y por vertido) MUST aceptar solo vacío, un número (coma o punto) o «Ausente»/«Ausencia»; cualquier otro texto MUST rechazarse junto al campo. Si mínimo y máximo son números, el mínimo MUST NOT superar al máximo. La ayuda del campo MUST explicar que «Ausente» es «no detectado» (pruebas A/P y mediciones con límite de detección) y que para conteos que no deben aparecer se usa máx. 0.
- **FR-003**: El sistema MUST determinar «calculada a partir de otras pruebas» según la fórmula (si referencia otras pruebas), sin pedirlo al usuario.
- **FR-004**: Toda alta, edición, eliminación, desactivación y reactivación MUST pedir confirmación con un resumen antes de guardarse, y permitir cancelar sin cambios.
- **FR-005**: Una prueba MUST considerarse «en uso» si está asignada a algún tipo de estudio o a algún estudio (regla actual del catálogo).
- **FR-006**: Si la prueba no está en uso, MUST poder editarse completa y eliminarse, salvo que la fórmula de otra prueba la referencie: en ese caso MUST rechazarse la eliminación y el cambio de código, indicando qué pruebas la usan.
- **FR-007**: Si la prueba está en uso, MUST poder editarse solo límites (generales y por vertido), norma, límite de detección y observación; código, nombre, tipo de cálculo, fórmula y unidades MUST mostrarse bloqueados con el mensaje de US3 Esc. 1, MUST NOT poder eliminarse y MUST revalidarse estas reglas al confirmar.
- **FR-008**: Editar una prueba MUST NOT modificar validaciones ya hechas, resultados ya calculados ni informes emitidos; los límites nuevos se usan solo en validaciones posteriores.
- **FR-009**: El sistema MUST permitir desactivar y reactivar una prueba, con confirmación. Si alguna prueba activa la referencia en su fórmula, la confirmación de desactivar MUST listar esas pruebas y advertir que no se podrán calcular en estudios nuevos. Si está en tipos de estudio activos, la confirmación MUST listarlos («Los estudios nuevos de estos tipos no la van a incluir») y marcar los que se quedarían sin ninguna prueba activa («Este tipo no se va a poder usar»). En ambos casos se puede confirmar igual. Desactivar o reactivar una prueba MUST contar como un cambio de los tipos de estudio que la incluyen, para que una confirmación de crear estudio abierta antes se rechace con el aviso de que el tipo cambió.
- **FR-010**: Una prueba inactiva MUST NOT ofrecerse al crear o editar tipos de estudio ni al agregar pruebas a un estudio.
- **FR-011**: Al crear un estudio, MUST asignarse solo las pruebas activas de su tipo; si el tipo no tiene ninguna activa, la creación MUST rechazarse con un mensaje que lo explique. Si las pruebas activas del tipo cambiaron entre la confirmación y la creación, la creación MUST rechazarse (el estudio nunca se crea distinto de lo confirmado).
- **FR-012**: En los estudios donde una prueba inactiva ya estaba asignada, MUST seguir funcionando la carga, el cálculo, la corrección, la validación y el informe.
- **FR-013**: El listado del catálogo MUST marcar las pruebas activas cuya fórmula referencia alguna prueba inactiva, con los códigos de esas pruebas.
- **FR-014**: Cada prueba del listado MUST enlazar a su ficha de gestión en la app (en lugar de al admin de Django), y el listado MUST ofrecer «Nueva prueba».
- **FR-015**: Solo los usuarios con la pertenencia a «Administradores» y el permiso del panel de administración MUST poder ver las pantallas y ejecutar las acciones del catálogo; el resto MUST recibir 403 sin cambios (también un superusuario fuera del grupo).
- **FR-016**: Si la prueba cambió desde que se abrió la ficha, la confirmación MUST rechazarse con un aviso, sin pisar los cambios de otra persona.
- **FR-016a**: Al crear una prueba desde la app MUST guardarse quién la creó y cuándo; al editarla, desactivarla o reactivarla, quién lo hizo y cuándo (solo la última modificación). La ficha MUST mostrar ambos datos («Sin registro» para las pruebas anteriores a esta historia o cargadas por importación).
- **FR-016b**: Al desactivar una prueba, MUST poder elegirse opcionalmente «Reemplazar por» otra prueba activa con la misma unidad del resultado, que no sea ella misma ni la referencie (directa o indirectamente). Con reemplazo, en la misma operación MUST: registrar el reemplazo; reemplazar `{CODIGO_VIEJO}` por `{CODIGO_NUEVO}` en la fórmula de toda prueba que la referenciaba (aunque esté en uso: es la única forma en que cambia la fórmula de una prueba en uso, y no altera su método); cambiar la prueba vieja por la nueva en todo tipo de estudio que la incluía, subiendo su versión; y mostrar antes, en el resumen, las fórmulas y tipos afectados.
- **FR-016c**: Desde la confirmación de desactivar MUST poder crearse la prueba de reemplazo: un alta precargada con los datos de la vieja (código vacío, unidad del resultado fija) cuya confirmación crea la nueva y aplica FR-016b en la misma transacción. Su fórmula MUST NOT usar la vieja ni las que dependen de ella.
- **FR-016c**: Al calcular o recalcular un estudio, si una fórmula nombra una prueba que el estudio no tiene, MUST usarse la prueba del estudio que fue reemplazada (directa o en cadena) por la nombrada. Así los estudios anteriores al reemplazo siguen calculando igual.
- **FR-017**: La importación por CSV (`importar_catalogo_pruebas`) MUST seguir funcionando como hoy, y el admin de Django MUST seguir disponible como respaldo.

### Key Entities *(include if feature involves data)*

- **Prueba**: Entrada del catálogo (código, nombre, tipo de cálculo, fórmula, unidades, límites generales, norma, límite de detección, observación, activa, creada por y fecha, modificada por última vez por y fecha). «En uso» si está en algún tipo de estudio o estudio.
- **Reemplazo**: Vínculo «reemplazada por» entre una prueba desactivada y la nueva; lo usan la cascada de fórmulas y tipos y el cálculo de los estudios anteriores.
- **Límite por tipo de vertido**: Límites y norma propios de Cloacal o Canal para una prueba; reemplazan a los generales para ese vertido.
- **Tipo de estudio** (US 5.5): Paquete de pruebas; los estudios nuevos toman solo sus pruebas activas.
- **Validación / Informe** (US 6.4, 7.2): Guardan los límites y la evaluación del momento; no cambian al editar la prueba.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Un administrador da de alta una prueba completa en menos de 3 minutos, sin entrar al admin de Django.
- **SC-002**: El 100 % de las ediciones de pruebas en uso dejan iguales las validaciones y los informes emitidos anteriores.
- **SC-003**: El 100 % de los intentos de cambiar un dato bloqueado, eliminar una prueba en uso o referenciada, o gestionar el catálogo sin permiso terminan sin cambios.
- **SC-004**: Ninguna prueba inactiva se ofrece al armar tipos ni al agregar pruebas, y ningún estudio nuevo la incluye.
- **SC-005**: El 100 % de los estudios que ya tenían una prueba desactivada pueden completar su ciclo (carga, cálculo, validación e informe).
- **SC-006**: Toda prueba activa que depende de una inactiva aparece marcada en el listado del catálogo.
- **SC-007**: Reemplazar una prueba con dependientes se hace en una sola confirmación, sin recrear ninguna prueba dependiente, y el 100 % de los recálculos de estudios anteriores dan el mismo resultado que antes del reemplazo.

## Assumptions

- **Trazabilidad**: SCRUM-73 – Gestionar catálogo de pruebas. Responsable: Delfina. Depende de SCRUM-71 (panel de administración, grupo «Administradores»).
- **Decisiones tomadas con la responsable antes de especificar (2026-11-10)**: los estudios nuevos toman solo las pruebas activas del tipo; desactivar una prueba usada en fórmulas se permite con aviso, y el listado marca las pruebas que dependen de una inactiva para que se reemplace; eliminar una prueba referenciada en una fórmula no se permite; el admin de Django queda como respaldo; el acceso es el del panel 025 (grupo + permiso, sin excepción para superusuarios).
- **Hoy `activa` no se usa**: ni el armado de tipos ni «agregar prueba» filtran inactivas; esta historia agrega esos filtros.
- **Nombre en uso**: el criterio bloquea el nombre de una prueba en uso, igual que hoy el admin y la importación.
- **Interfaz**: diseño de SCRUM-67 y componentes de `templates/ui/`, con confirmación previa como el resto del panel de administración; ayudas en los campos que no son evidentes (US 9.1).
- **Alcance excluido**: curvas de calibración (próximo sprint); importación masiva (sigue el comando); historial completo de cambios de cada prueba (solo se guarda la última modificación); reemplazar sin desactivar (el reemplazo siempre retira la prueba vieja); deshacer un reemplazo.
