# Feature Specification: Panel de administración

**Feature Branch**: `025-Panel-Administracion`

**Created**: 2026-11-03

**Status**: Implementación funcional completada; cierre de validación local documentado en quickstart.md. Requisitos aprobados sin cambios.

**Input**: Como administrador del laboratorio quiero una sección de administración dentro de la app, con el mismo diseño que el resto, para hacer las tareas habituales sin entrar al panel de Django, que tiene demasiadas opciones y es fácil perderse.

**Trazabilidad**: Historia de Jira «Panel de administración», proporcionada en esta conversación. Clave Jira y número de US del backlog no informados; pendientes de vincular cuando el equipo los proporcione. El número 025 identifica la spec, no una clave Jira ni un número de US.

**Alcance**: Acceso administrativo, solicitudes de cuenta, usuarios y roles, consulta del catálogo de pruebas y reubicación de «Gestionar tipos de estudio». Quedan fuera la edición del catálogo de pruebas dentro de AquaLab y la creación de usuarios desde este panel. No incluye gestionar membresías de Administradores ni permisos individuales desde las nuevas pantallas.

## Clarifications

### Session 2026-11-03

- Q: ¿Qué autorización requiere el panel y cómo afecta a la gestión de tipos? → A: El panel exige pertenencia a Administradores y permiso administrativo propio, sin excepción para superusuarios ajenos al grupo. La gestión de tipos conserva exclusivamente su permiso específico y el acceso directo para quienes lo posean; su enlace en Administración requiere además poder ver esa sección.
- Q: ¿Cómo se distinguen aprobación, desactivación y reactivación de una cuenta? → A: Pendiente significa registrada sin aprobar; Activa, aprobada y habilitada; Desactivada, previamente aprobada y suspendida. Las pendientes se gestionan solo desde Solicitudes; reactivar una aprobada no repite el aviso inicial. Se conserva el historial sin conceder accesos inesperados ni presumir aprobación previa cuando no hay evidencia.
- Q: ¿Qué relación tiene la condición administrativa con el rol profesional y qué modifica un cambio de rol? → A: Son independientes y pueden coexistir. Usuario común y Bioquímico son los roles profesionales; cambiarlos solo incorpora o retira la pertenencia a Bioquímicos y conserva los demás grupos y permisos. Se permite cambiar el propio rol con confirmación, pero nunca desactivar la propia cuenta; no se añaden restricciones a combinaciones de roles.
- Q: ¿Puede rechazarse eliminando una cuenta histórica inactiva clasificada conservadoramente como Pendiente cuando tiene historial protegido, referencias que impiden eliminarla o firma profesional? → A: No. Se impide el rechazo, se informa el motivo y se conservan íntegramente la cuenta, su correo, sus referencias, su firma y su historial, sin aviso de rechazo ni resolución efectiva. Puede revisarse y, si corresponde, aprobarse mediante el flujo normal, sin activación automática ni presunción de aprobación previa. No se debilitan protecciones ni se eliminan referencias o firmas para rechazarla. Las pendientes elegibles sin esos impedimentos mantienen el rechazo habitual con eliminación, liberación del correo y aviso.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Acceder a Administración con autorización (Priority: P1)

Como administrador quiero encontrar las tareas administrativas en una sección propia del menú, con el diseño habitual de AquaLab y acceso restringido.

**Why this priority**: Protege las cuentas y concentra el acceso a todas las funciones de la historia.

**Independent Test**: Comparar navegación y acceso directo con grupo y permiso, grupo sin permiso, permiso sin grupo y superusuario fuera del grupo; comprobar por separado el permiso específico de tipos.

**Acceptance Scenarios**:

1. **Given** una cuenta activa del grupo Administradores con el permiso de administración, **When** inicia sesión, **Then** ve «Administración» y sus accesos a solicitudes, usuarios y roles y catálogo de pruebas, con el diseño común de la app.
2. **Given** una cuenta autenticada que carece del grupo Administradores, del permiso administrativo o de ambos, **When** navega o intenta acceder directamente a solicitudes, usuarios y roles o catálogo, **Then** no ve la sección y recibe HTTP 403 en cada pantalla o acción protegida, sin consultar ni modificar datos administrativos.
3. **Given** una sesión sin autenticar, **When** intenta entrar a una pantalla administrativa, **Then** se solicita iniciar sesión mediante el comportamiento existente.
4. **Given** un usuario cuyo permiso administrativo o pertenencia a Administradores fue revocado después de abrir una pantalla, **When** confirma una operación administrativa, **Then** recibe HTTP 403 y la operación no se realiza.
5. **Given** un superusuario que no pertenece a Administradores, **When** intenta acceder al nuevo panel o a sus acciones, **Then** no ve la sección y recibe HTTP 403, sin acceso excepcional por ser superusuario.
6. **Given** la configuración inicial del sistema, **When** se consulta el grupo Administradores, **Then** el grupo existe y tiene asignado el permiso administrativo propio dentro del esquema de permisos existente.

### User Story 2 - Resolver solicitudes de cuenta (Priority: P1)

Como administrador quiero ver las solicitudes pendientes y aprobarlas o rechazarlas sin usar el admin de Django.

**Why this priority**: Permite incorporar usuarios mediante un flujo cotidiano que ya existe en el sistema.

**Independent Test**: Registrar una solicitud, resolverla desde AquaLab y comprobar acceso y avisos; intentar rechazar una pendiente histórica con historial protegido o firma y comprobar su conservación, el motivo informado, la ausencia de aviso y la disponibilidad del flujo normal de aprobación posterior.

**Acceptance Scenarios**:

1. **Given** solicitudes pendientes de aprobación, **When** se abre su listado, **Then** cada solicitud muestra nombre, apellido y correo, y los botones «Aprobar» y «Rechazar».
2. **Given** una solicitud pendiente, **When** el administrador aprueba y confirma la acción, **Then** la cuenta puede iniciar sesión, desaparece de pendientes y recibe el mismo aviso de aprobación que recibe actualmente, con el enlace al inicio de sesión.
3. **Given** una solicitud pendiente elegible para eliminación, **When** el administrador pulsa «Rechazar», **Then** ve la identidad de la cuenta y las consecuencias de la acción y puede confirmar o cancelar; hasta confirmar no cambia la solicitud.
4. **Given** la confirmación de rechazo, **When** el administrador cancela, **Then** la cuenta continúa pendiente y no se envía un aviso de rechazo.
5. **Given** una solicitud pendiente sin historial protegido, relaciones que impidan eliminarla ni firma profesional, **When** se confirma su rechazo efectivo, **Then** la cuenta se elimina, deja de figurar como pendiente, no puede iniciar sesión, su correo queda disponible para solicitar otra cuenta y recibe el aviso de rechazo existente.
6. **Given** una solicitud que otro administrador ya resolvió o un envío repetido, **When** se intenta resolver de nuevo, **Then** no se repite la transición ni se duplica el aviso, y se informa que ya no está pendiente.
7. **Given** una aprobación o rechazo efectivo confirmado y una falla en el envío del correo, **When** termina la operación, **Then** la decisión se conserva y la falla se trata como en el flujo de avisos existente.
8. **Given** cuentas pendientes y previamente aprobadas que están desactivadas, **When** se consulta Solicitudes de cuenta, **Then** solo aparecen las pendientes; las desactivadas no pueden aprobarse ni rechazarse como solicitudes.
9. **Given** una cuenta histórica inactiva clasificada conservadoramente como Pendiente por falta de evidencia de aprobación previa y con historial protegido, referencias que impidan eliminarla o firma profesional, **When** el administrador intenta confirmar su rechazo, **Then** el rechazo se impide y se explica el motivo; se conservan íntegramente cuenta, correo, referencias, firma e historial y su estado Pendiente sin acceso, no se envía aviso de rechazo y permanece disponible la revisión del caso y su aprobación mediante el flujo normal, sin activación automática ni presunción de aprobación previa.

### User Story 3 - Gestionar roles y estado de usuarios (Priority: P1)

Como administrador quiero consultar el rol y estado de las cuentas y cambiarlos con confirmación, sin desactivarme accidentalmente.

**Why this priority**: Permite mantener el acceso al laboratorio y los privilegios profesionales.

**Independent Test**: Cambiar el rol profesional propio y de otra cuenta aprobada, verificar que solo cambia su pertenencia a Bioquímicos, cambiar el estado de otra cuenta, cancelar cambios y comprobar la prohibición de desactivar la cuenta propia.

**Acceptance Scenarios**:

1. **Given** usuarios registrados, **When** se abre «Usuarios y roles», **Then** se muestran nombre, apellido, correo, rol «Usuario común» o «Bioquímico» y estado «Pendiente», «Activa» o «Desactivada» de cada cuenta; las pendientes se gestionan exclusivamente desde Solicitudes de cuenta.
2. **Given** una cuenta previamente aprobada, propia o de otra persona, **When** se elige un nuevo rol profesional, **Then** se muestra una confirmación que identifica la cuenta, el rol actual y el propuesto; cancelar conserva el rol anterior y confirmar incorpora o retira únicamente su pertenencia a Bioquímicos, sin modificar otros grupos ni permisos.
3. **Given** otra cuenta activa, **When** se confirma su desactivación, **Then** pasa a «Desactivada», pierde el acceso a las funciones autenticadas y conserva su identidad, grupos, permisos e historial.
4. **Given** otra cuenta desactivada y previamente aprobada, **When** se confirma su reactivación, **Then** pasa a «Activa», recupera el acceso según sus permisos conservados y no recibe nuevamente el aviso de aprobación inicial.
5. **Given** un cambio de estado propuesto, **When** se cancela la confirmación, **Then** se conserva el estado anterior.
6. **Given** un administrador operando sobre su propia cuenta, **When** intenta desactivarla, incluso mediante acceso directo a la acción, **Then** la operación se impide, se explica el motivo y la cuenta permanece activa.
7. **Given** un cambio de rol o estado confirmado por otro administrador mientras la pantalla estaba abierta, **When** se confirma una propuesta sobre información desactualizada, **Then** se informa el cambio y se solicita revisar el estado vigente antes de modificarlo.
8. **Given** una cuenta pendiente, **When** se intenta activarla o gestionarla desde Usuarios y roles, incluso mediante acceso directo a la acción, **Then** no se aplica el cambio y se indica que debe resolverse desde Solicitudes de cuenta.
9. **Given** una cuenta histórica inactiva sin evidencia de aprobación previa, **When** se incorpora la distinción de estados, **Then** conserva su identidad, permisos e historial, permanece sin acceso y no se considera previamente aprobada ni elegible para reactivación como tal; requiere el flujo de aprobación.
10. **Given** una cuenta aprobada que pertenece a Administradores, **When** se confirma su rol Bioquímico, **Then** pertenece simultáneamente a ambos grupos y conserva sus otros grupos y permisos.
11. **Given** un administrador bioquímico operando sobre su propia cuenta, **When** confirma el cambio a Usuario común, **Then** se retira únicamente su pertenencia a Bioquímicos y conserva Administradores y los demás grupos y permisos; la prohibición de desactivarse continúa vigente.

### User Story 4 - Consultar el catálogo de pruebas (Priority: P2)

Como administrador quiero encontrar pruebas por código o nombre y consultar sus datos principales; si necesito editarlas, quiero abrir su ficha en el admin de Django.

**Why this priority**: Evita navegar por opciones ajenas a la consulta cotidiana del catálogo.

**Independent Test**: Buscar por parte del código y del nombre, consultar pruebas activas e inactivas y seguir el enlace de una ficha.

**Acceptance Scenarios**:

1. **Given** pruebas activas e inactivas, **When** se abre el catálogo sin búsqueda, **Then** se listan ambas con código, nombre, tipo de cálculo, unidad del resultado, estado activo/inactivo y enlace para editar en el admin de Django.
2. **Given** un texto que coincide parcialmente con un código o nombre, **When** se busca, **Then** se muestran las coincidencias sin distinguir mayúsculas y minúsculas.
3. **Given** una búsqueda sin coincidencias o un catálogo vacío, **When** se consulta el listado, **Then** se informa que no hay resultados y se permite limpiar la búsqueda.
4. **Given** una prueba del listado, **When** se sigue su enlace de edición, **Then** se abre su ficha existente en el admin de Django, que conserva sus propias restricciones de acceso y edición.
5. **Given** una prueba sin unidad informada, **When** se muestra en el listado, **Then** se presenta «Sin unidad», siguiendo la convención existente.

### User Story 5 - Encontrar la gestión de tipos en Administración (Priority: P2)

Como usuario autorizado quiero encontrar «Gestionar tipos de estudio» en Administración y mantener las capacidades y el permiso que ya tiene esa función.

**Why this priority**: Agrupa tareas de configuración y evita duplicar la gestión ya implementada.

**Independent Test**: Verificar la nueva ubicación y repetir los flujos existentes con y sin autorización administrativa y con y sin `estudios.gestionar_catalogo`; este último sigue siendo el único permiso obligatorio de la gestión de tipos.

**Acceptance Scenarios**:

1. **Given** una cuenta autorizada para Administración y con el permiso vigente de gestión de tipos, **When** abre el menú, **Then** encuentra «Gestionar tipos de estudio» en Administración y ya no en Estudios.
2. **Given** una cuenta autorizada para Administración sin el permiso específico de tipos, **When** navega o intenta gestionar tipos por acceso directo, **Then** no ve esa opción y recibe HTTP 403 al intentar acceder a su gestión.
3. **Given** acceso autorizado a tipos de estudio, **When** se usa el acceso reubicado, **Then** se conserva la funcionalidad existente, incluidas confirmaciones, desactivación y protección de tipos usados, sin modificar estudios previos.
4. **Given** una cuenta activa con `estudios.gestionar_catalogo` que no tiene autorización para Administración, **When** navega e ingresa directamente a gestión de tipos, **Then** no ve Administración y conserva el acceso directo a esa funcionalidad, sin exigir el permiso administrativo.

### Edge Cases

- Sin solicitudes o usuarios que mostrar, los listados presentan un estado vacío comprensible.
- Una solicitud resuelta o una cuenta eliminada mientras se revisa no permite confirmar cambios sobre una identidad inexistente ni sobre otra cuenta.
- Una cuenta desactivada no aparece como solicitud pendiente; una pendiente no puede activarse ni gestionarse desde Usuarios y roles.
- Reactivar una cuenta previamente aprobada conserva sus grupos, permisos e historial y no reenvía el aviso de aprobación inicial.
- Al incorporar la distinción de estados, una cuenta histórica inactiva sin evidencia de aprobación previa permanece sin acceso, conserva sus registros y no se presume aprobada. Distinguir pendiente de desactivada requiere reconocer la aprobación previa, además de la habilitación actual de acceso.
- Una pendiente histórica con historial protegido, referencias que impidan eliminarla o firma profesional no puede eliminarse por rechazo: se informa el impedimento y se conservan cuenta, correo e historial, sin aviso de rechazo. Puede revisarse y aprobarse por el flujo normal si corresponde; no se activa automáticamente ni se debilitan protecciones o eliminan referencias o firmas para completar el rechazo.
- Reenviar una aprobación o rechazo no genera nuevos avisos para la misma resolución.
- La desactivación de un usuario con actividad histórica conserva las referencias a sus operaciones.
- Cancelar una confirmación no cambia datos ni envía avisos asociados a una operación no realizada.
- El enlace a Django admin no concede por sí mismo autorización para editar pruebas.
- Pertenecer a Administradores sin permiso o tener el permiso sin pertenecer al grupo no autoriza el nuevo panel; ser superusuario fuera del grupo tampoco. La gestión de tipos conserva su acceso directo con su autorización existente.
- Cambiar el propio rol profesional requiere confirmación y no permite desactivar la cuenta propia; Administrador y Bioquímico pueden coexistir sin restricciones adicionales.
- Retirar la pertenencia a Bioquímicos no elimina permisos individuales ni permisos obtenidos por otros grupos, aunque otorguen facultades equivalentes. El cambio no altera la condición administrativa ni el estado de la cuenta.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema DEBE incorporar «Administración» en el menú común, visible solo a usuarios activos del grupo «Administradores» que dispongan del permiso administrativo propio, para concentrar solicitudes de cuenta, usuarios y roles, consulta del catálogo de pruebas y gestión de tipos autorizada.
- **FR-002**: El grupo «Administradores» DEBE estar disponible como parte de los datos iniciales del sistema y contar con un permiso propio de administración, dentro del esquema de grupos y permisos existente.
- **FR-003**: Las nuevas pantallas y acciones administrativas DEBEN comprobar la autorización en cada acceso; los usuarios autenticados sin la pertenencia al grupo y el permiso exigidos DEBEN recibir HTTP 403, sin exposición ni modificación de datos protegidos. Esta regla no incorpora una segunda autorización a la gestión de tipos existente.
- **FR-004**: El nuevo panel DEBE exigir conjuntamente pertenecer a «Administradores» y disponer del permiso administrativo propio. El permiso sin el grupo o el grupo sin el permiso NO DEBEN autorizar el acceso. Un superusuario fuera del grupo NO DEBE tener acceso excepcional. La gestión de tipos DEBE conservar su autorización existente, `estudios.gestionar_catalogo`, sin requerir además autorización administrativa.
- **FR-005**: Las pantallas DEBEN conservar el diseño, navegación, mensajes en español y patrones de confirmación del resto de AquaLab. Cada cambio DEBE identificar la cuenta afectada y permitir confirmar o cancelar antes de guardarse.
- **FR-006**: El listado de solicitudes DEBE identificar cada cuenta pendiente mediante nombre, apellido y correo y ofrecer «Aprobar» y «Rechazar»; no DEBE admitir resolver cuentas que ya no están pendientes.
- **FR-007**: Aprobar una solicitud DEBE habilitar el acceso de la cuenta y emitir el mismo aviso de aprobación existente una sola vez por resolución, con enlace al inicio de sesión.
- **FR-008**: Rechazar una solicitud pendiente elegible DEBE pedir confirmación y, cuando el rechazo sea efectivo, eliminar la cuenta, retirar la solicitud, impedir el acceso, liberar el correo para otra solicitud y enviar el aviso existente. Una pendiente sin historial protegido, relaciones que impidan eliminarla ni firma profesional es elegible para el rechazo habitual. Si una cuenta histórica inactiva clasificada conservadoramente como Pendiente tiene esos impedimentos, el rechazo DEBE impedirse e informar el motivo, conservando íntegramente cuenta, correo, referencias, firma e historial; NO DEBE enviarse aviso de rechazo porque no hubo resolución efectiva. NO DEBEN debilitarse las protecciones de integridad ni eliminarse referencias o firmas para completar el rechazo. Cancelar DEBE conservar la solicitud sin aviso.
- **FR-009**: «Usuarios y roles» DEBE listar la identidad, el rol común/bioquímico y el estado de las cuentas, y permitir cambios confirmados de rol y activación/desactivación de cuentas previamente aprobadas, sin ofrecer creación de usuarios ni edición de permisos individuales o membresías administrativas. Las cuentas pendientes DEBEN gestionarse exclusivamente desde Solicitudes de cuenta.
- **FR-010**: El sistema DEBE distinguir «Pendiente» (registrada, todavía no aprobada), «Activa» (aprobada y habilitada para iniciar sesión) y «Desactivada» (previamente aprobada, con acceso suspendido). La aprobación previa y la habilitación actual DEBEN distinguirse: la ausencia de acceso por sí sola NO DEBE identificar ambos estados. Las pendientes solo DEBEN aprobarse o rechazarse desde Solicitudes de cuenta, sujetas a la elegibilidad de FR-008, y NO DEBEN activarse desde Usuarios y roles. Las desactivadas NO DEBEN aparecer como solicitudes pendientes. Reactivar una cuenta previamente aprobada DEBE restaurar su acceso sin reenviar el aviso de aprobación inicial. Los registros históricos DEBEN conservarse sin conceder accesos inesperados; ante una cuenta inactiva cuya aprobación previa no pueda determinarse, NO DEBE asumirse que fue aprobada ni permitirse reactivarla como previamente aprobada. Si se impide su rechazo por FR-008, DEBE permanecer Pendiente y sin acceso; el administrador PUEDE revisar el caso y, si corresponde, aprobarla mediante el flujo normal, sin activación automática ni presunción de aprobación previa.
- **FR-011**: La pertenencia a Administradores DEBE ser independiente del rol profesional; una persona PUEDE ser Administrador y Bioquímico simultáneamente. Los roles profesionales visibles DEBEN ser «Usuario común» y «Bioquímico», según la ausencia o presencia de pertenencia al grupo Bioquímicos. Cambiar el rol DEBE únicamente incorporar o retirar esa pertenencia, sin modificar otros grupos, permisos ni el estado de la cuenta. Un administrador PUEDE cambiar su propio rol profesional con confirmación y NO PUEDE desactivar su propia cuenta. NO DEBEN añadirse restricciones sobre combinaciones de roles no solicitadas en esta historia.
- **FR-012**: Un administrador NO DEBE poder desactivar su propia cuenta. Desactivar otra cuenta aprobada DEBE impedir su acceso autenticado y conservar su identidad, grupos, permisos e historial asociado.
- **FR-013**: El catálogo de consulta DEBE incluir pruebas activas e inactivas, con código, nombre, tipo de cálculo, unidad del resultado y estado; DEBE permitir buscar coincidencias parciales por código o nombre sin distinguir mayúsculas y minúsculas y limpiar la búsqueda.
- **FR-014**: Cada prueba DEBE ofrecer un enlace a su edición existente en Django admin, conservando sus autorizaciones y restricciones actuales. La aplicación NO DEBE permitir editar pruebas dentro del nuevo catálogo de consulta.
- **FR-015**: «Gestionar tipos de estudio» DEBE pasar de Estudios a Administración en el menú. Su enlace DEBE aparecer únicamente para quienes puedan ver Administración y posean `estudios.gestionar_catalogo`. Quienes solo posean ese permiso DEBEN conservar el acceso directo a la funcionalidad, con su comportamiento existente y sin un segundo permiso obligatorio.
- **FR-016**: Las operaciones DEBEN reutilizar los permisos, cuentas, grupos y avisos existentes, sin un sistema paralelo. Una falla de correo NO DEBE revertir una resolución confirmada; resolver nuevamente la misma solicitud NO DEBE duplicar avisos.
- **FR-017**: Confirmar sobre información modificada desde su revisión DEBE informar el conflicto y exigir revisar la información vigente, sin sobrescribir silenciosamente decisiones de otro administrador.

### Key Entities *(include if feature involves data)*

- **Usuario**: Cuenta existente identificada por correo único, nombre y apellido; tiene grupos, permisos y estado Pendiente, Activa o Desactivada. Su aprobación previa se distingue de la habilitación actual de acceso; una cuenta histórica inactiva sin aprobación comprobable no se presume aprobada.
- **Solicitud de cuenta**: Petición de registro pendiente de resolución; se aprueba o, si es elegible, se rechaza usando el flujo existente. Una cuenta desactivada no se asume una solicitud nueva; una pendiente histórica con impedimentos de eliminación se conserva sin resolución de rechazo.
- **Grupo Administradores**: Agrupación administrativa con permiso propio; ambas condiciones son necesarias para acceder al nuevo panel, sin excepción para superusuarios fuera del grupo.
- **Rol común/bioquímico**: Clasificación profesional visible: Bioquímico si pertenece al grupo Bioquímicos, Usuario común si no pertenece. Es independiente de Administradores; cambiarla solo modifica la pertenencia a Bioquímicos, conservando los demás grupos y permisos.
- **Prueba**: Entrada del catálogo existente con código, nombre, tipo de cálculo, unidad y estado; esta historia solo la consulta.
- **Tipo de estudio**: Configuración de pruebas existente; conserva sus reglas y permiso específico, cambiando su ubicación en el menú.
- **Aviso de resolución**: Comunicación existente de aprobación o rechazo, asociada a una resolución efectiva y sin duplicación por reenvío.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: El 100 % de los accesos y operaciones de las nuevas pantallas intentados por cuentas autenticadas sin pertenencia a Administradores o sin permiso administrativo se rechazan con HTTP 403 y sin cambios de datos, incluidos superusuarios fuera del grupo.
- **SC-002**: El 100 % de las aprobaciones confirmadas y de los rechazos efectivos confirmados de cuentas elegibles para rechazo deja la solicitud en el resultado esperado; en condiciones normales de entrega, se recibe exactamente un aviso existente por resolución y ninguno por cancelación o reenvío. En el 100 % de los intentos de rechazo impedidos por historial protegido, referencias o firma profesional, se conserva íntegramente la cuenta con su correo e historial y su estado Pendiente sin acceso, se informa el motivo y no se envía aviso de rechazo.
- **SC-003**: El 100 % de los cambios de rol y estado requiere confirmación; ninguna cancelación produce cambios y todos los intentos de desactivación propia se impiden. El 100 % de los cambios de rol profesional, incluidos los propios, modifica solo la pertenencia a Bioquímicos y conserva los demás grupos, permisos y el estado de la cuenta.
- **SC-004**: En un conjunto conocido de pruebas activas e inactivas, todas las coincidencias por fragmento de código o nombre son recuperables y cada fila muestra los cinco datos requeridos y el enlace a la ficha correspondiente.
- **SC-005**: Un administrador autorizado puede resolver una solicitud y cambiar el rol o estado de otra cuenta sin entrar al panel externo, en un máximo de tres acciones desde el listado correspondiente, incluida la confirmación.
- **SC-006**: La opción de gestión de tipos aparece una única vez en el menú, bajo Administración y solo con ambas autorizaciones de navegación; el 100 % de sus escenarios vigentes sigue cumpliéndose para quienes posean su permiso específico, incluido el acceso directo sin autorización administrativa.
- **SC-007**: En un conjunto conocido de cuentas pendientes, activas y desactivadas, el 100 % se muestra con el estado correspondiente; ninguna desactivada aparece como solicitud, ninguna pendiente se activa desde Usuarios y roles y ninguna reactivación reenvía el aviso inicial. Las cuentas históricas inactivas sin aprobación comprobable conservan sus registros y ninguna obtiene acceso por la incorporación de los estados.

## Assumptions

- Se reutilizan las cuentas, autenticación, grupos y permisos existentes. El acceso sin sesión conserva el inicio de sesión actual; HTTP 403 se aplica a cuentas autenticadas sin autorización.
- La aprobación y los rechazos efectivos de cuentas elegibles mantienen los avisos y el comportamiento vigentes; los rechazos impedidos por FR-008 no resuelven la solicitud ni envían aviso. No se cambia en esta historia quién recibe el aviso de una solicitud nueva: actualmente lo reciben los superusuarios activos.
- El rol profesional se apoya en la pertenencia al grupo Bioquímicos, sin crear otra clasificación de permisos y sin alterar otros grupos ni permisos individuales. Las facultades concedidas por otras vías se conservan.
- La búsqueda parcial sin distinguir mayúsculas y la unidad del resultado son valores por defecto para la consulta. Se utiliza «Sin unidad» cuando corresponda.
- El permiso de administración no implica conceder acceso adicional al admin de Django. El enlace de edición queda sujeto a sus permisos existentes.
- El acceso rápido de gestión de tipos en Inicio conserva la función existente; esta historia solicita reubicar su entrada en el menú, sin rediseñar Inicio.
- Las decisiones FR-004, FR-010 y FR-011, y la elegibilidad de rechazo de FR-008 para cuentas históricas, fueron aprobadas por el responsable e incorporadas mediante `$speckit-clarify`. La representación técnica de estados y la creación del grupo con su permiso mediante migración se detallan en el plan; esta especificación no impone campos. Las correcciones se revisan con `$speckit-analyze` antes de implementar.

### Funcionalidades existentes que se reutilizan

- Registro de cuentas y acceso sujeto a aprobación (specs 001 y 002).
- Aprobación y rechazo con liberación del correo, confirmación de rechazo, avisos de resolución y tratamiento de fallas de envío (spec 006).
- Catálogo de pruebas, sus datos, búsqueda y edición protegida en Django admin (spec 014); solo la consulta dentro de AquaLab es nueva.
- Grupo Bioquímicos y sus permisos actuales de validación de resultados y emisión de informes (specs 019 y 021).
- Gestión de tipos con permiso propio, confirmaciones y protección del historial (spec 012).
- Diseño común, navegación y componentes existentes (spec 013).
