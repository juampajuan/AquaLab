# Feature Specification: Inicio personalizado por rol

**Feature Branch**: `033-inicio-personalizado-rol`

**Created**: 2026-11-09

**Status**: Implementación completa; 52/52 tareas verificadas y 27/27 escenarios cubiertos. El usuario realizó y aprobó la revisión funcional y la revisión técnica local está aprobada. Siguen pendientes la clave Jira/US real, el CI remoto y la revisión y aprobación del futuro PR por el equipo.

**Numeración**: Se mantiene 033 por decisión del responsable. También existe la rama remota `033-panel-calidad`, correspondiente a otra historia; esta entrega no modifica esa rama.

**Input**: Como empleado del laboratorio quiero ver en el inicio lo que tengo pendiente según mi rol, para saber qué hacer apenas entro.

**Trazabilidad**: Historia aprobada en Jira «Inicio personalizado por rol», con descripción y cuatro criterios proporcionados por el responsable. Clave Jira y número de US del backlog no informados; pendientes de vincular cuando estén disponibles. 033 identifica la especificación, no una clave Jira ni un número de US.

**Criterios de Jira**:

1. Los indicadores del inicio dependen del rol: el técnico ve los estudios con mediciones por cargar; el bioquímico, además, los resultados por validar y los estudios listos para emitir.
2. Cada indicador enlaza a la lista correspondiente.
3. Los accesos rápidos se reagrupan por módulo, en orden de trabajo: Clientes → Muestras → Estudios → Informes.
4. Para quien tiene acceso al dashboard, aparece una tarjeta «Ver dashboard».

**Alcance**: Personalizar los pendientes del inicio, enlazarlos con sus listas, reagrupar los accesos existentes y ofrecer acceso al dashboard del laboratorio según la autorización vigente. Incluye la selección de pendientes necesaria en los listados existentes cuando todavía no está disponible. No cambia las reglas de carga, cálculo, validación, emisión, firma profesional ni autorización; no crea roles ni un dashboard nuevo. No incorpora asignación personal de trabajo, avisos, emisión desde el inicio ni rediseño de otras pantallas.

## Clarifications

### Session 2026-11-09

- Q: ¿Cómo se distinguen Técnico y Bioquímico y cómo afectan Administración y los permisos a los indicadores? → A: Técnico corresponde a Usuario común; Bioquímico corresponde a pertenecer a Bioquímicos. Administradores es independiente: un administrador común ve los indicadores del técnico y uno bioquímico los del bioquímico. La presentación por rol conserva los permisos efectivos de consulta y operación, sin conceder ni retirar autorizaciones.
- Q: ¿El pendiente de validación cuenta resultados individuales o estudios y qué debe permitir identificar su destino? → A: Cuenta resultados individuales calculados y pendientes de validación. Un estudio con cinco aporta cinco; uno con uno aporta uno; uno sin pendientes aporta cero. El listado de destino debe permitir identificar cada resultado que contribuye, sin confundir cantidad de resultados con cantidad de estudios.
- Q: ¿Se conservan los indicadores generales actuales junto con los pendientes por rol? → A: Se reemplazan por los indicadores específicos del rol, sin un segundo bloque de contadores generales ni duplicaciones. Se conservan las demás funcionalidades del inicio fuera de los cambios solicitados.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Reconocer el trabajo pendiente según el rol (Priority: P1)

Como empleado quiero reconocer desde el inicio qué trabajo del laboratorio puedo continuar según mi rol y mis autorizaciones.

**Why this priority**: Es el objetivo principal de la historia: identificar el siguiente trabajo al ingresar.

**Independent Test**: Preparar estudios con carga sin iniciar, carga parcial, resultados calculados sin validar, resultados validados e informes emitidos; comparar Técnico y Bioquímico, con y sin pertenencia a Administradores. Verificar también permisos individuales, superusuarios y ausencia de permisos de operación conforme a FR-002 y FR-011.

**Acceptance Scenarios**:

1. **Given** un técnico con acceso habitual y un estudio sin mediciones y otro parcialmente cargado, ambos con pruebas que admiten carga pendiente, **When** abre el inicio, **Then** ve «Estudios con mediciones por cargar» con valor 2, aunque los estudios tengan estados generales diferentes.
2. **Given** el mismo técnico sin autorización para validar ni emitir, **When** abre el inicio, **Then** ve su pendiente de mediciones y no recibe acciones de validación o emisión restringidas.
3. **Given** un bioquímico con las autorizaciones habituales, **When** abre el inicio, **Then** ve «Estudios con mediciones por cargar», «Resultados por validar» y «Estudios listos para emitir»; los primero y tercero cuentan estudios distintos y el segundo cuenta resultados individuales.
4. **Given** un estudio con varias pruebas que requieren medición y otro que solo tiene una prueba calculada pendiente, **When** se muestran los pendientes de carga, **Then** el primero cuenta una sola vez y el segundo no cuenta por esa prueba calculada.
5. **Given** resultados existentes sin validar, pruebas sin resultado y resultados con validación vigente, **When** se consulta el pendiente de validación, **Then** solo los primeros aportan al indicador, incluyendo los que volvieron a requerir validación tras una corrección.
6. **Given** un estudio sin pruebas, otro con alguna prueba sin completar, uno con todas completas y sin informe y otro con informe generado, **When** se consulta «Estudios listos para emitir», **Then** solo cuenta el tercero.
7. **Given** ausencia de pendientes de una categoría visible, **When** se abre el inicio, **Then** su indicador muestra 0 y conserva el enlace a un listado vacío comprensible.
8. **Given** un bioquímico autorizado para emitir que aún no cargó su firma profesional, **When** consulta los estudios listos, **Then** la falta de su firma no cambia el conteo de estudios y el flujo de emisión conserva el requisito de firma y matrícula.
9. **Given** un administrador que no pertenece a Bioquímicos, **When** abre el inicio, **Then** ve el indicador del técnico y la pertenencia administrativa no agrega los indicadores profesionales del bioquímico.
10. **Given** un administrador que pertenece a Bioquímicos y tiene las autorizaciones habituales, **When** abre el inicio, **Then** ve los tres indicadores del bioquímico.
11. **Given** una cuenta fuera de Bioquímicos con permisos individuales de validación o emisión, incluida una cuenta de superusuario, **When** abre el inicio, **Then** conserva la presentación del técnico y sus permisos efectivos siguen habilitando los accesos y operaciones existentes por sus vías autorizadas.
12. **Given** un bioquímico sin permiso efectivo para validar o emitir, **When** consulta sus indicadores y sigue sus enlaces de consulta permitidos, **Then** no obtiene acciones restringidas ni acceso a operaciones para las que carece de permiso; los accesos directos conservan la denegación actual.
13. **Given** un estudio con cinco resultados pendientes de validación, otro con uno y otro sin resultados pendientes, **When** un bioquímico consulta el inicio, **Then** «Resultados por validar» muestra 6, sin contar estudios ni pruebas cuyo resultado todavía no existe.
14. **Given** el inicio personalizado de un técnico o un bioquímico, **When** se revisan sus bloques, **Then** no aparecen los contadores generales anteriores de muestras sin estudio, muestras ingresadas hoy ni estudios pendientes de análisis, tampoco en un segundo bloque; se conservan la bienvenida y las últimas muestras y se aplican la agrupación de accesos y tarjeta de dashboard solicitadas.

---

### User Story 2 - Abrir la lista del pendiente (Priority: P1)

Como empleado quiero abrir desde cada indicador la lista de trabajo que representa, para continuar sin reconstruir una búsqueda.

**Why this priority**: Un número sin acceso al trabajo correspondiente no satisface el segundo criterio de Jira.

**Independent Test**: Seguir cada indicador con datos conocidos, recorrer todas las páginas y comparar sus integrantes con la definición del pendiente, sin cambios concurrentes.

**Acceptance Scenarios**:

1. **Given** estudios con y sin mediciones por cargar, **When** se sigue ese indicador, **Then** se abre el listado de estudios mostrando únicamente los estudios que cumplen la definición de carga pendiente, incluidas las cargas parciales.
2. **Given** seis resultados por validar distribuidos en dos estudios y una cuenta a la que corresponde ese indicador, **When** lo sigue, **Then** llega a la selección de pendientes donde puede identificar los seis resultados por su estudio y prueba, sin incluir resultados ya validados o todavía no calculados; mostrar dos estudios no debe presentarse como un total de dos resultados. La continuación hacia validación conserva su autorización actual.
3. **Given** estudios listos y no listos para informar, **When** se sigue «Estudios listos para emitir», **Then** se abre la selección de estudios de Informes con «Solo listos» activo, sin incluir estudios ya informados.
4. **Given** un pendiente resuelto por otra persona después de abrir el inicio, **When** se sigue el indicador, **Then** la lista refleja el estado vigente; al consultar nuevamente el inicio se actualiza el conteo. El inicio no reserva trabajo ni permite eludir las comprobaciones de cada operación.
5. **Given** una lista con más elementos que una página, **When** se cambia de página, **Then** se conserva la selección de pendientes y el indicador representa el total, no solo la primera página.
6. **Given** resultados pendientes distribuidos entre varios estudios y páginas, **When** se recorren los resultados identificables en toda la selección sin cambios concurrentes, **Then** cada resultado aparece una sola vez y su cantidad total coincide con el contador de resultados del inicio, aunque un mismo estudio reúna varios.

---

### User Story 3 - Encontrar los accesos por módulo (Priority: P2)

Como empleado quiero encontrar los accesos rápidos agrupados en el orden habitual del trabajo del laboratorio.

**Why this priority**: Facilita pasar de la gestión del cliente a la emisión sin buscar accesos dispersos.

**Independent Test**: Revisar los grupos y seguir los accesos con una cuenta común y otra autorizada para gestionar tipos de estudio.

**Acceptance Scenarios**:

1. **Given** una cuenta autenticada, **When** abre el inicio, **Then** encuentra los grupos Clientes, Muestras, Estudios e Informes en ese orden.
2. **Given** los accesos rápidos actuales, **When** se presenta la agrupación, **Then** Clientes reúne Buscar cliente y Registrar cliente; Muestras reúne Registrar muestra; Estudios reúne Crear estudio y Buscar estudio; Informes reúne la selección de estudios para informar.
3. **Given** una cuenta con autorización para gestionar tipos, **When** abre el inicio, **Then** conserva ese acceso dentro de Estudios; una cuenta sin esa autorización no lo ve. Esta agrupación no cambia su ubicación actual en el menú de Administración ni sus permisos de acceso directo.
4. **Given** cualquiera de estos accesos, **When** se utiliza, **Then** se abre su funcionalidad existente con sus autorizaciones actuales, sin duplicaciones ni cambios de datos por la navegación.

---

### User Story 4 - Entrar al dashboard autorizado (Priority: P2)

Como empleado autorizado quiero abrir el dashboard del laboratorio desde una tarjeta del inicio.

**Why this priority**: Acerca la supervisión existente a quienes ya pueden usarla.

**Independent Test**: Comparar cuentas con y sin autorización vigente para ver el dashboard, independientemente de su rol profesional o administrativo.

**Acceptance Scenarios**:

1. **Given** una cuenta con autorización para ver el dashboard, **When** abre el inicio, **Then** aparece una tarjeta «Ver dashboard» y al seguirla abre el dashboard del laboratorio existente.
2. **Given** una cuenta sin esa autorización, **When** abre el inicio, **Then** no aparece la tarjeta; intentar ingresar directamente conserva la denegación existente.
3. **Given** una cuenta común con autorización individual para el dashboard o una cuenta de Bioquímicos sin autorización efectiva para él, **When** abre el inicio, **Then** la tarjeta depende de la autorización vigente y no del nombre del rol.

### Edge Cases

- Un estudio puede tener simultáneamente mediciones por cargar y resultados por validar: aporta una unidad al conteo de estudios con carga pendiente y tantas unidades al conteo de validación como resultados individuales pendientes tenga.
- Un resultado calculado de una prueba calculada también cuenta si está Cargada y pendiente de validación; no requiere una medición manual propia para aportar al contador. Una prueba todavía sin resultado no cuenta.
- Las pruebas calculadas no se cargan manualmente; la ausencia de su resultado no equivale por sí sola a una medición pendiente.
- Una validación anulada por corrección no sustituye una vigente; el resultado recalculado vuelve al pendiente de validación cuando las reglas actuales lo habilitan.
- Una prueba validada fuera de norma también está completada; el inicio no agrega un bloqueo de emisión por ese motivo.
- Un estudio con informe generado no aporta a ninguno de los tres pendientes y mantiene la inalterabilidad vigente.
- Las cuentas sin sesión o sin acceso habilitado conservan las restricciones actuales de autenticación.
- Ser Administrador no equivale a ser Bioquímico; pueden coexistir. Administradores, otros grupos, permisos individuales y condición de superusuario no sustituyen la pertenencia a Bioquímicos para determinar el rol de presentación. Las autorizaciones efectivas siguen controlando cada consulta y operación; pertenecer a Bioquímicos no permite eludirlas.
- Los indicadores y enlaces deben poder identificarse y utilizarse con teclado, sin depender exclusivamente del color, siguiendo la interfaz común en español.
- Eliminar los contadores generales del inicio no elimina sus datos ni altera el dashboard u otras consultas existentes; no se presenta un segundo bloque con los contadores retirados.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El inicio DEBE mostrar al técnico «Estudios con mediciones por cargar» y al bioquímico, además, «Resultados por validar» y «Estudios listos para emitir», sujeto a la distinción de FR-002 y conservando los permisos reales de cada operación.
- **FR-002**: Técnico DEBE corresponder funcionalmente a Usuario común, sin pertenencia a Bioquímicos; Bioquímico DEBE corresponder a quien pertenece a Bioquímicos. Administradores DEBE ser independiente del rol profesional: un administrador común recibe la presentación del técnico y uno bioquímico la del bioquímico. Los permisos individuales, otros grupos o la condición de superusuario NO DEBEN sustituir esa pertenencia para agregar indicadores profesionales. El sistema NO DEBE crear un rol Técnico ni modificar grupos, permisos o autorizaciones existentes. La presentación por rol NO DEBE habilitar consultas ni operaciones que sus permisos efectivos no permitan.
- **FR-003**: «Estudios con mediciones por cargar» DEBE contar una vez cada estudio que admita carga de mediciones, en Pendiente de análisis o En proceso, con al menos una prueba no calculada en estado Pendiente según las reglas actuales de carga. No DEBE usar únicamente el estado general del estudio ni incluir como carga manual las pruebas calculadas pendientes.
- **FR-004**: «Resultados por validar» DEBE contar una vez cada resultado individual existente de una prueba en estado Cargada, todavía sin validación vigente y perteneciente a un estudio sin informe generado, según las reglas actuales de validación. DEBE incluir resultados de pruebas calculadas y resultados recalculados que vuelven a requerir validación; DEBE excluir pruebas todavía sin resultado y resultados con validación vigente. Un estudio con cinco pendientes aporta cinco, otro con uno aporta uno y uno sin pendientes aporta cero. No DEBE contar estudios ni crear estados nuevos.
- **FR-005**: «Estudios listos para emitir» DEBE contar una vez cada estudio con al menos una prueba, todas sus pruebas en estado Completada y sin informe generado, con la misma regla de la selección «Solo listos» de Informes. La autorización y la firma con matrícula de quien emite siguen siendo requisitos de emisión, sin modificar la preparación del estudio.
- **FR-006**: Cada indicador DEBE abrir su lista con la selección pertinente activa: mediciones hacia los estudios con carga pendiente; validación hacia los resultados pendientes identificables por estudio y prueba; emisión hacia la selección «Solo listos» de Informes. Se DEBEN reutilizar los listados y reglas existentes, incorporando la selección de carga y validación que falta y la identificación de cada resultado que aporta al contador. Un listado que solo identifique estudios sin permitir reconocer esos resultados NO DEBE considerarse suficiente. Esta selección e identificación es parte de esta historia y todavía no existe; no se exige una nueva pantalla independiente ni se prescribe su organización visual.
- **FR-007**: El conteo y el listado DEBEN representar exactamente los mismos pendientes para los mismos datos vigentes. Carga y emisión DEBEN contar estudios distintos; validación DEBE contar resultados individuales distintos. Si se agrupan resultados por estudio, el usuario DEBE poder identificar cada resultado pendiente por estudio y prueba y distinguir el total de resultados del total de estudios; la suma de esos resultados en todas las páginas DEBE coincidir con el indicador. No se DEBEN añadir restricciones por fecha, creador o empleado asignado que excluyan pendientes del laboratorio.
- **FR-008**: Cada categoría visible DEBE mostrar 0 cuando no tenga pendientes; su enlace DEBE abrir una lista vacía con un mensaje comprensible. La selección DEBE conservarse al paginar y la navegación no DEBE ejecutar operaciones de carga, validación o emisión.
- **FR-009**: Los accesos rápidos DEBEN agruparse de forma visible como Clientes → Muestras → Estudios → Informes, conservando las funciones y restricciones descritas en User Story 3. No DEBEN ofrecer módulos ni operaciones nuevos fuera de este alcance.
- **FR-010**: El inicio DEBE ofrecer una tarjeta titulada «Ver dashboard» únicamente a quien tenga la autorización vigente `informes.ver_dashboard` para ver el dashboard del laboratorio. El enlace DEBE abrir ese dashboard existente y conservar su comprobación de acceso. No DEBE sustituir ese permiso por el rol profesional o la autorización del panel de Administración ni conceder permisos nuevos.
- **FR-011**: Mostrar un indicador o acceso NO DEBE conceder permisos. Los enlaces de los indicadores DEBEN conducir únicamente a consultas permitidas al usuario; consultar pendientes NO DEBE habilitar validación ni emisión. Cada acción de validar o emitir DEBE seguir exigiendo su permiso efectivo actual, incluso para Bioquímicos. Carecer de esos permisos NO DEBE sortearse desde el inicio ni mediante acceso directo. Las cuentas con permisos por otras vías DEBEN conservar sus accesos existentes aunque su rol no agregue los indicadores profesionales. Los cambios de rol o permiso DEBEN reflejarse en la siguiente consulta del inicio.
- **FR-012**: La nueva presentación DEBE respetar la interfaz común, su navegación y mensajes en español. Los conteos DEBEN reflejar los datos vigentes al consultar la página; no se requiere actualización continua ni reserva de tareas.
- **FR-013**: Los indicadores actuales «Muestras sin estudio», «Muestras ingresadas hoy» y «Estudios pendientes de análisis» DEBEN reemplazarse por los pendientes específicos del rol de FR-001 a FR-005. NO DEBEN conservarse en un segundo bloque ni duplicarse con otros rótulos. El inicio DEBE conservar sus demás funcionalidades fuera de los cambios solicitados, incluidas la bienvenida y las últimas muestras. No se DEBEN agregar listados para los contadores retirados.

### Key Entities *(include if feature involves data)*

- **Empleado**: Cuenta habilitada existente; Técnico equivale funcionalmente a Usuario común y Bioquímico a pertenecer a Bioquímicos. Administradores es independiente. Los permisos efectivos gobiernan consultas y operaciones; esta historia no altera identidad, grupos ni facultades.
- **Estudio**: Análisis de una muestra con pruebas asignadas y estados Pendiente de análisis, En proceso, Finalizado e Informe generado. Su estado general no describe por sí solo todos los pendientes de sus pruebas.
- **Prueba de un estudio**: Asignación Pendiente, Cargada o Completada; puede requerir medición manual o calcularse a partir de otras pruebas.
- **Medición y Resultado**: Datos y resultado del análisis existentes; un resultado puede estar calculado sin validar, tanto para una prueba medida como para una calculada. Cada resultado pendiente se identifica por su estudio y prueba y aporta una unidad al indicador de validación, independientemente de otros resultados del mismo estudio.
- **Validación**: Revisión profesional vigente o anulada; completar una prueba requiere la validación según las reglas actuales.
- **Informe**: Documento emitido de un estudio; su emisión lo retira de los pendientes y conserva los requisitos profesionales vigentes.
- **Indicador de pendiente**: Nombre, cantidad, unidad y enlace a la selección correspondiente. Las unidades son estudios con carga pendiente, resultados individuales por validar y estudios listos para emitir; un mismo estudio puede aportar varios resultados, pero solo una unidad a cada conteo de estudios.
- **Dashboard del laboratorio**: Vista existente de indicadores, gráficos y alertas de actividad del laboratorio, distinta del panel de Administración.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: En un conjunto conocido que incluya carga parcial, pruebas calculadas, resultados sin validar, correcciones, estudios listos e informados, el 100 % de los conteos coincide con FR-003 a FR-005: estudios distintos para carga y emisión, resultados individuales para validación. El caso de cinco resultados más uno más cero DEBE mostrar 6 resultados por validar.
- **SC-002**: El 100 % de los indicadores visibles permite abrir en una sola acción su lista con la selección activa; recorrer todas sus páginas recupera todos y solo los pendientes esperados para la misma información vigente. Cada resultado contado DEBE poder identificarse por estudio y prueba, una sola vez, y el total identificable DEBE coincidir con el indicador de validación.
- **SC-003**: El 100 % de las cuentas de la matriz de aceptación —Técnico y Bioquímico, con y sin Administradores, permisos individuales y superusuarios— recibe la presentación de su rol conforme a FR-002 y conserva sus permisos efectivos conforme a FR-011. Ninguna cuenta sin permiso para el dashboard ve su tarjeta ni logra ingresar por ese acceso; ningún indicador permite validar o emitir sin el permiso requerido.
- **SC-004**: Los cuatro grupos de accesos aparecen una sola vez y en el orden solicitado, y el 100 % de los accesos conservados abre su funcionalidad existente con sus restricciones.
- **SC-005**: En una revisión de aceptación, un técnico y un bioquímico con accesos habituales pueden identificar el pendiente pertinente a su trabajo y abrir su lista en un máximo de 30 segundos desde el inicio, sin asistencia ni búsquedas manuales.
- **SC-006**: En el 100 % de los casos de aceptación del inicio personalizado, los tres contadores generales anteriores están ausentes y los indicadores por rol no se duplican; la bienvenida y las últimas muestras conservan su comportamiento existente.

## Assumptions

- Los pendientes son del laboratorio completo, como las consultas actuales; «lo que tengo pendiente» significa trabajo pertinente al rol, no trabajo asignado personalmente. No se introduce asignación individual de tareas.
- Se conserva la bienvenida y la sección de últimas muestras; no se solicita su rediseño. Los tres indicadores generales se reemplazan por decisión aprobada, sin un segundo bloque.
- Se reutilizan las reglas actuales de estudios, mediciones, resultados, validaciones y preparación de informes. Una corrección puede invalidar validaciones previas antes de emitir, conforme al comportamiento vigente; esta historia no lo redefine.
- Se reutilizan los listados y accesos existentes; se añade la selección de pendientes y la identificación de los resultados que falte. El listado de estudios actual no identifica por sí solo todos los resultados que aporta cada estudio al contador: esa correspondencia debe incorporarse para cumplir FR-006 y FR-007. Filtrar por En proceso no equivale a filtrar mediciones pendientes o resultados por validar.
- La trazabilidad por clave Jira y número de US requiere información posterior del equipo y no impide revisar este borrador; no se deduce un identificador a partir de 033.
- El objetivo de 30 segundos de SC-005 es un supuesto de aceptación propuesto para evaluar la facilidad de orientación, no una medición ya realizada.

### Funcionalidades existentes que se reutilizan

- Inicio con bienvenida, accesos rápidos y últimas cinco muestras (spec 013). Se reutiliza su presentación común; los tres indicadores generales actuales, que no son enlaces, se reemplazan conforme a FR-013.
- Carga de pruebas no calculadas pendientes, cálculo automático y corrección o borrado con recálculo (specs 015 a 018).
- Validación profesional de resultados y registro de validaciones vigentes o anuladas (spec 019).
- Búsqueda paginada de estudios por texto, estado y fechas (specs 009 y 028). No cuenta hoy con selección específica de mediciones por cargar ni resultados por validar, ni identifica cada resultado pendiente en esa selección; las capacidades faltantes quedan delimitadas por FR-006 y FR-007.
- Selección de estudios para informar con «Solo listos», control de completitud, emisión protegida y firma profesional (specs 020 a 022).
- Roles comunes/bioquímicos y condición administrativa independiente del rol profesional (spec 025).
- Dashboard del laboratorio y autorización propia, habitual para Bioquímicos y Administradores, sin depender exclusivamente de esas pertenencias (spec 027).
- Componentes comunes de accesos, indicadores, estados vacíos y navegación; accesos existentes de Clientes, Muestras, Estudios e Informes (spec 013).

### Decisiones pendientes para aclaración

- No quedan decisiones funcionales pendientes de aclaración. Las tres respuestas aprobadas se registran en Clarifications y se integran en escenarios, requisitos, casos límite, entidades, supuestos y criterios de éxito.
- Sigue pendiente completar la clave Jira y el número de US cuando el equipo los informe; no se inventan identificadores. Esa información de trazabilidad no es una ambigüedad del comportamiento y deberá revisarse en el chequeo de Constitution al planificar.

Registro histórico: la fase de `$speckit-clarify` se detuvo para revisión. Posteriormente se aprobaron planificación y tareas y se completó el análisis; el responsable autorizó la implementación el 2026-11-10. Las decisiones funcionales de esta especificación permanecen intactas.
