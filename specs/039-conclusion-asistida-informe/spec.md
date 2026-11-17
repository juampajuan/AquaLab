# Feature Specification: US 10.2 — Conclusión asistida del informe

**Feature Branch**: `39-Conclucion-Asistida`

**Created**: 2026-11-16

**Status**: Aclaraciones Q1–Q3 aprobadas por el responsable e incorporadas mediante `$speckit-clarify`; especificación funcionalmente cerrada y lista para revisión antes de `$speckit-plan`. No se ejecutan planificación, tareas ni implementación en esta fase.

**Input**: Como bioquímico quiero que el sistema me proponga una conclusión con las pruebas fuera de norma y la norma de cada una, para revisarla y sumarla al informe y al correo.

**Trazabilidad**: US 10.2. Clave Jira propia no informada; no se deduce de SCRUM-79, que identifica una dependencia. La numeración secuencial 039 de la carpeta es independiente del nombre de rama solicitado.

**Criterios proporcionados por el responsable**:

1. En la vista previa del informe hay un botón «Proponer conclusión», que arma un borrador con las pruebas fuera de norma, el valor obtenido, el límite y la norma de cada una.
2. Los datos del borrador salen del sistema, de la validación vigente de cada prueba. La IA solo redacta el texto: no agrega pruebas, valores ni normas.
3. Si todas las pruebas cumplen, el borrador lo dice.
4. El borrador es editable: el bioquímico lo corrige o lo reescribe.
5. Sin la aprobación del bioquímico, la conclusión no entra al informe. Se puede emitir sin conclusión.
6. Al emitir, la conclusión aprobada se guarda en la copia del informe y queda inalterable como el resto.
7. El PDF, la impresión y el correo del informe muestran la misma conclusión.
8. Si el servicio de IA no responde, se ofrece un borrador armado con una plantilla fija con los mismos datos, para no bloquear la emisión.
9. Los informes emitidos antes de esta historia no cambian.

## Clarifications

### Session 2026-11-16

- Q: ¿Quién puede proponer y aprobar una conclusión? → A: Se requieren conjuntamente pertenencia a Bioquímicos y permiso efectivo de emisión. Ambas condiciones se verifican también en el acceso directo a las dos acciones. No se alteran permisos existentes de consulta, validación, emisión o envío ni se conceden permisos automáticamente.
- Q: ¿Cuándo pierde vigencia una aprobación, quién puede emitir y qué ocurre al abandonar o recargar la vista? → A: La aprobación corresponde a una versión exacta del texto y a sus hechos de origen. Editar el texto, generar otra propuesta o cambiar esos hechos la invalida; debe seguir vigente al emitir. Puede emitir otro bioquímico autorizado mientras la aprobación siga vigente. Los borradores se conservan al abandonar o recargar, sin aprobación automática. No se agrega expiración temporal.
- Q: ¿Qué conclusión se ofrece cuando hay pruebas con información insuficiente? → A: Se permite un borrador parcial con los hechos verificables y la identificación expresa de las pruebas no evaluables y sus motivos: falta de validación vigente, límite comparable o norma. No se inventan datos ni se reemplaza una validación faltante con el catálogo actual. Puede editarse y aprobarse conservando las advertencias. Solo se indica cumplimiento integral si todas las pruebas son evaluables, tienen evaluación vigente y cumplen; con pruebas no evaluables nunca se afirma cumplimiento íntegro. Emitir sin conclusión sigue disponible bajo las reglas actuales.

## User Scenarios & Testing *(mandatory)*

Estos recorridos pertenecen a la misma US 10.2; no son nuevas historias del backlog. Cada escenario deberá contar con una prueba automatizada según Constitution. Aquí se definen resultados esperados, sin generar ni ejecutar tests.

En esta especificación, **bioquímico autorizado** es una persona con sesión activa que pertenece al grupo Bioquímicos y tiene el permiso efectivo de emisión existente. La política conjunta se aplica a proponer y aprobar conclusiones; no amplía ni restringe la consulta, validación, emisión sin conclusión o envío actuales.

### User Story 1 - Obtener un borrador con hechos verificados (Priority: P1)

Como bioquímico autorizado solicito desde la vista previa una conclusión que describa las pruebas fuera de norma con sus datos reales, sin delegar a la IA la determinación del cumplimiento.

**Why this priority**: Ahorra redacción manteniendo la autoridad de las validaciones del laboratorio.

**Independent Test**: Preparar estudios con vista previa disponible y validaciones conocidas; solicitar la propuesta y contrastar cada dato con los resultados y validaciones vigentes. Incluir pruebas sin validación vigente, sin límite comparable o sin norma y comprobar el borrador parcial sin cambiar las condiciones de emisión existentes. Obtener un borrador es verificable sin emitir un informe.

**Acceptance Scenarios**:

1. **Given** dos pruebas fuera de norma con validación vigente, **When** el bioquímico autorizado pulsa «Proponer conclusión» en la vista previa, **Then** aparece un borrador que identifica ambas una sola vez, con valor, unidad, límite aplicado y norma registrados, sin agregar incumplimientos.
2. **Given** un estudio con todas sus pruebas evaluables, con validación vigente y evaluadas como «Cumple», **When** se propone la conclusión, **Then** el borrador indica que todas cumplen y no inventa incumplimientos ni recomendaciones de tratamiento.
3. **Given** una prueba con validaciones anuladas históricas y una vigente, **When** se arma el borrador, **Then** solo la vigente determina evaluación, límite y norma, sin duplicar la prueba ni citar incumplimientos anteriores.
4. **Given** un catálogo cuyos límites o normas cambiaron después de validar, **When** se solicita la propuesta sin cambiar la validación vigente, **Then** se citan el límite y la norma guardados al validar, no los actuales del catálogo.
5. **Given** resultados presentados como Ausente/Presente, con unidades o por debajo del límite de detección, **When** se redacta el borrador, **Then** se respeta la presentación del informe y la evaluación vigente, sin que la IA recalcule, redondee o interprete nuevamente el cumplimiento.
6. **Given** un estudio listo para informar, **When** se solicita una propuesta, **Then** no se emite un informe ni se modifican mediciones, resultados o validaciones, y la propuesta no queda aprobada automáticamente.
7. **Given** una vista previa disponible con una prueba fuera de norma validada y otra sin validación vigente, **When** se propone la conclusión, **Then** se obtiene un borrador parcial con los hechos verificables de la primera y la identificación de la segunda como no evaluable por falta de validación vigente, sin sustituirla por una evaluación del catálogo ni afirmar cumplimiento integral.
8. **Given** pruebas evaluables que cumplen y otra con validación vigente «Sin límite comparable», **When** se propone la conclusión, **Then** el borrador identifica esta última y el motivo, conserva los hechos verificables de las demás y no afirma que todo el estudio cumple.
9. **Given** una prueba cuya validación vigente no tiene norma registrada, **When** se propone la conclusión, **Then** el borrador parcial identifica la prueba y la ausencia de norma, conserva sus valores, límites y evaluación conocidos sin inventar una norma y no presenta el estudio como íntegramente conforme.
10. **Given** una vista previa disponible en la que ninguna prueba es evaluable por los motivos previstos, **When** se propone la conclusión, **Then** se ofrece un borrador parcial que identifica las pruebas y sus motivos de información insuficiente, sin inventar resultados ni evaluaciones o afirmar cumplimiento integral; la emisión sin conclusión conserva sus reglas actuales.

---

### User Story 2 - Editar y aprobar expresamente la incorporación (Priority: P1)

Como bioquímico autorizado puedo corregir o reescribir el borrador y decidir si incorporo el texto revisado al emitir. La conclusión es opcional.

**Why this priority**: La revisión profesional es condición de incorporación, sin obligar a utilizar una conclusión automática.

**Independent Test**: Comparar borradores sin aprobación, aprobados e invalidados por edición, regeneración o cambio de hechos; emitir con y sin conclusión, abandonar y recargar la vista. Contrastar cuentas con ambas condiciones de autorización, solo grupo, solo permiso y ninguna condición, tanto en la interfaz como por acceso directo.

**Acceptance Scenarios**:

1. **Given** un borrador propuesto, **When** el bioquímico autorizado lo corrige o reescribe, aprueba ese texto y emite sin cambios intermedios, **Then** el informe incorpora el texto revisado y aprobado, no la primera propuesta automática.
2. **Given** una propuesta o un texto editado sin aprobación vigente, **When** se emite sin conclusión cumpliendo los requisitos actuales, **Then** el informe se emite sin incorporar el borrador, aunque contenga texto o haya tenido una aprobación que se invalidó.
3. **Given** una propuesta generada correctamente, **When** termina la redacción sin una acción profesional de aprobación, **Then** sigue siendo borrador y no figura como conclusión aprobada.
4. **Given** una cuenta activa sin pertenencia a Bioquímicos ni permiso de emisión, **When** intenta proponer o aprobar, incluso accediendo directamente a cualquiera de las acciones, **Then** ambas acciones se deniegan y no se genera una propuesta ni una aprobación por esa vía; no cambian sus permisos de consulta existentes.
5. **Given** una persona sin sesión activa o cuya cuenta fue desactivada, **When** intenta proponer o aprobar, **Then** no obtiene acceso autenticado a esas acciones ni puede aprobar texto.
6. **Given** una cuenta activa de Bioquímicos sin permiso efectivo de emisión, **When** intenta proponer o aprobar, también por acceso directo, **Then** se deniegan ambas acciones sin concederle permisos.
7. **Given** una cuenta activa con permiso efectivo de emisión pero fuera de Bioquímicos, **When** intenta proponer o aprobar, también por acceso directo, **Then** se deniegan ambas acciones; se conserva su permiso existente para emitir sin conclusión.
8. **Given** una cuenta activa perteneciente a Bioquímicos y con permiso efectivo de emisión, **When** solicita una propuesta o aprueba un borrador del estudio, **Then** puede realizar esas acciones bajo las condiciones de esta historia, sin adquirir facultades adicionales de consulta, validación o envío.
9. **Given** una conclusión aprobada, **When** se modifica su texto antes de emitir, **Then** la aprobación queda invalidada, el texto editado queda como borrador y no puede incorporarse amparado por la aprobación anterior.
10. **Given** una conclusión aprobada, **When** se genera una nueva propuesta antes de emitir, **Then** la aprobación anterior queda invalidada incluso si el nuevo texto coincide con el anterior; la propuesta nueva requiere aprobación expresa.
11. **Given** una conclusión aprobada, **When** cambian sus resultados, validaciones u otros hechos de origen antes de emitir, **Then** su aprobación queda invalidada y al emitir no se incorpora como vigente; se conserva la opción de emitir sin conclusión si se cumplen las reglas actuales del estudio.
12. **Given** un borrador editado y no aprobado, **When** el bioquímico abandona la pantalla y regresa al mismo borrador o recarga la vista, **Then** en ambos recorridos se conserva el texto editado y su falta de aprobación, sin aprobación automática.
13. **Given** una conclusión aprobada cuyo texto y hechos no cambiaron, **When** se recarga la vista, **Then** se conserva el borrador con la misma versión y su estado de aprobación vigente; la recarga no crea una aprobación nueva ni vuelve vigente una invalidada.
14. **Given** una aprobación invalidada, **When** el bioquímico autorizado revisa el texto y los hechos actuales y los aprueba expresamente de nuevo, **Then** solo esa nueva versión aprobada puede incorporarse, siempre que continúe vigente al emitir.
15. **Given** un borrador parcial que identifica pruebas no evaluables y sus motivos, **When** el bioquímico autorizado lo edita y aprueba, **Then** se permite la revisión y aprobación manteniendo las advertencias correspondientes; ni la edición ni la aprobación convierten esas pruebas en conformes o permiten afirmar cumplimiento integral.

---

### User Story 3 - Conservar el texto aprobado en todos los medios (Priority: P1)

Como bioquímico quiero que la conclusión aprobada quede conservada al emitir y llegue sin cambios al informe consultado, PDF, impresión y correo.

**Why this priority**: Una conclusión diferente entre medios o cambiante después de emitir rompe la integridad de la revisión profesional.

**Independent Test**: Emitir con un texto aprobado conocido; comparar todas las salidas, modificar después datos de origen y repetir la consulta. Comparar también un informe anterior a US 10.2.

**Acceptance Scenarios**:

1. **Given** un texto aprobado y sus hechos de origen identificados, **When** se emite el informe, **Then** la copia conserva el texto y la trazabilidad hacia el estudio, las pruebas y las validaciones que fundamentaron la propuesta, sin depender de futuras respuestas de IA.
2. **Given** un informe emitido con conclusión, **When** cambia después el catálogo, la firma profesional u otros datos editables de origen, **Then** no cambia la conclusión ni el resto de su copia.
3. **Given** un informe con conclusión aprobada, **When** se consulta, descarga en PDF, imprime o envía, **Then** la consulta, PDF, impresión, ambos cuerpos del correo y PDF adjunto muestran el mismo contenido textual aprobado; solo varía la maquetación.
4. **Given** un informe emitido con conclusión y la IA no disponible, **When** se descarga, imprime, envía o reenvía por los flujos existentes, **Then** se utiliza el texto conservado sin solicitarlo nuevamente a la IA ni bloquear la operación por su indisponibilidad.
5. **Given** un informe anterior a esta historia, **When** se consulta, descarga, imprime o envía después de incorporar US 10.2, **Then** conserva su copia y presentación sin conclusión añadida ni generación retrospectiva de texto.
6. **Given** un informe ya emitido, **When** se intenta agregar, sustituir o aprobar una nueva conclusión para él, **Then** no se modifica su copia y se conserva la inmutabilidad existente.
7. **Given** una conclusión aprobada por un bioquímico y otro bioquímico autorizado para emitir, **When** la segunda persona emite mientras la aprobación sigue vigente y se cumplen las condiciones actuales de emisión, **Then** el informe incorpora el mismo texto aprobado y conserva la identidad de quien aprobó sin atribuirle esa aprobación a quien emite.

---

### User Story 4 - Continuar ante fallos o ausencia de IA (Priority: P1)

Como bioquímico quiero un borrador de plantilla fija con los mismos hechos cuando la IA no pueda redactar, manteniendo edición, aprobación y emisión sin conclusión.

**Why this priority**: Un servicio auxiliar no debe detener la emisión del laboratorio.

**Independent Test**: Simular fallos y ausencia de configuración; contrastar los hechos de la plantilla con los disponibles para redactar y completar una emisión con o sin conclusión aprobada. No requiere contactar al proveedor real.

**Acceptance Scenarios**:

1. **Given** datos vigentes disponibles y una solicitud sin respuesta al finalizar el tiempo de espera del servicio, **When** se informa la indisponibilidad, **Then** se ofrece el borrador de plantilla fija con esos mismos hechos, sin espera indefinida ni aprobación automática.
2. **Given** un fallo de conexión, cuota agotada, rechazo de credenciales o error del proveedor, **When** se solicita una propuesta, **Then** se avisa del uso de respaldo y se ofrece la plantilla, manteniendo la posibilidad de emitir sin conclusión.
3. **Given** el servicio de IA sin configurar, **When** se solicita una conclusión, **Then** se obtiene la plantilla fija sin exigir configurar IA para poder emitir.
4. **Given** una respuesta vacía, inutilizable o que agrega o altera pruebas, valores, límites o normas, **When** se recibe la respuesta, **Then** no se ofrece como propuesta fiel a los datos y se ofrece el respaldo con los hechos del sistema.
5. **Given** la plantilla fija para un estudio con todas sus pruebas evaluables, con evaluación vigente y conformes, **When** se presenta, **Then** expresa ese cumplimiento y admite edición y aprobación como cualquier borrador, sin incorporarse automáticamente al informe.
6. **Given** información parcial por falta de validación vigente, límite comparable o norma y un servicio de IA indisponible o sin configurar, **When** se solicita una propuesta, **Then** la plantilla fija conserva los mismos hechos verificables e identifica las mismas pruebas no evaluables con sus motivos; puede editarse y aprobarse conservando las advertencias o emitirse sin conclusión con las reglas actuales.

### Edge Cases

- Las validaciones anuladas no cuentan como vigentes ni duplican pruebas.
- Los límites específicos del tipo de vertido registrados al validar no se sustituyen por límites generales actuales.
- «Sin límite comparable» no equivale a «Cumple»; una norma vacía no se completa de memoria ni con fuentes ajenas al sistema. Se identifica cada prueba afectada como no evaluable y se explicita su motivo en el borrador parcial, conservando los hechos verificables disponibles.
- Una prueba sin validación vigente se identifica como no evaluable por ese motivo; no se sustituye con una evaluación del catálogo actual. No se agregan condiciones a la emisión sin conclusión.
- Si algunas o todas las pruebas son no evaluables, se permite el borrador parcial, pero nunca se afirma cumplimiento integral. Editar o aprobar conserva las advertencias correspondientes; no equivale a validar las pruebas faltantes.
- Una edición del texto aprobado, nueva propuesta o cambio de sus hechos de origen invalida la aprobación; se verifica su vigencia al emitir. Que una propuesta nueva repita el texto anterior no conserva la aprobación anterior.
- Abandonar o recargar la vista conserva el borrador y su estado real de aprobación; nunca aprueba un texto nuevo ni recupera una aprobación invalidada. No se define caducidad temporal de aprobaciones.
- Una persona distinta de quien aprobó puede emitir la conclusión si es un bioquímico autorizado y la aprobación sigue vigente; se distinguen ambas responsabilidades.
- El texto en un borrador no implica aprobación. Un fallo de IA tampoco crea una aprobación ni un informe.
- Los nombres, normas u otros datos del laboratorio no son instrucciones para la IA; no habilitan acciones ni hechos ajenos al estudio.
- Reenviar conserva la conclusión de la copia, sin cambiar destinatario, permisos ni confirmaciones del envío existente.
- Un estudio que dejó de estar listo o ya fue informado sigue sujeto a las restricciones de emisión actuales.
- Quedan fuera de alcance las recomendaciones de tratamiento del agua y las conclusiones de informes ya emitidos.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: AquaLab DEBE ofrecer «Proponer conclusión» en la vista previa para el recorrido del bioquímico autorizado, sin emitir al solicitarla.
- **FR-002**: El borrador DEBE identificar cada prueba fuera de norma una sola vez, con valor obtenido, unidad, límite aplicado y norma registrados, provenientes del estudio y sus validaciones vigentes. Si falta alguno de los hechos necesarios, DEBE conservar los hechos verificables disponibles e identificar la ausencia y la prueba afectada según FR-018, sin completar datos inexistentes.
- **FR-003**: AquaLab DEBE determinar los incumplimientos y sus hechos. Las validaciones anuladas y los cambios posteriores del catálogo NO DEBEN sustituir la validación vigente utilizada.
- **FR-004**: La IA DEBE limitarse a redactar; NO DEBE decidir cumplimiento, agregar pruebas, inventar valores o normas ni reinterpretar resultados. Si su texto no respeta los hechos proporcionados, NO DEBE presentarse como fiel y DEBE ofrecerse la plantilla fija.
- **FR-005**: Si todas las pruebas son evaluables y cuentan con evaluación vigente «Cumple», propuesta y plantilla DEBEN indicarlo. Si hay pruebas no evaluables por los motivos de FR-018, NO DEBE afirmarse que el estudio cumple íntegramente ni confundirse ausencia de incumplimientos con cumplimiento de todas las pruebas.
- **FR-006**: El bioquímico autorizado DEBE poder editar o reescribir el borrador antes de aprobar el texto que desea incorporar, incluidos los borradores parciales, conservando las advertencias correspondientes. Los borradores DEBEN conservarse al abandonar la pantalla o recargarla, sin que conservarlos implique aprobarlos automáticamente.
- **FR-007**: AquaLab DEBE distinguir borrador, texto editado y conclusión aprobada. Generar o editar NO DEBE equivaler a aprobar; solo el texto expresamente aprobado puede incorporarse.
- **FR-008**: AquaLab DEBE permitir emitir sin conclusión cumpliendo las reglas actuales. Un borrador no aprobado, una aprobación invalidada, la ausencia de propuesta o un fallo de IA NO DEBEN exigir incorporar texto ni alterar las condiciones existentes de emisión sin conclusión.
- **FR-009**: Para proponer y para aprobar una conclusión, AquaLab DEBE exigir conjuntamente sesión activa, pertenencia al grupo Bioquímicos y permiso efectivo de emisión existente. DEBE verificar estas condiciones también en el acceso directo a ambas acciones, no solo en los botones. No se conceden permisos automáticamente ni se alteran las autorizaciones existentes de consulta, validación, emisión o envío; el chat de US 10.1 no obtiene facultades nuevas.
- **FR-010**: La aprobación DEBE corresponder a una versión exacta del texto y a los hechos de origen utilizados para fundamentarlo. Modificar ese texto, generar otra propuesta o cambiar esos hechos DEBE invalidarla. AquaLab DEBE comprobar que siga vigente al emitir; una aprobación invalidada no autoriza incorporar la conclusión y se requiere una nueva revisión y aprobación expresa para incorporarla. Puede emitir una persona distinta de quien aprobó si es un bioquímico autorizado y la aprobación continúa vigente. No se establece expiración temporal de aprobaciones.
- **FR-011**: Al emitir, AquaLab DEBE conservar el texto aprobado, sus advertencias de información insuficiente cuando corresponda y la relación con su estudio, pruebas y validaciones de origen utilizadas en la copia del informe, identificando quién aprobó esa versión y distinguiéndolo de quien emite cuando sean personas distintas. La trazabilidad DEBE identificar las ausencias, sin atribuir a una prueba una validación inexistente. Ese contenido DEBE permanecer inmutable como el resto.
- **FR-012**: Consulta, PDF, impresión, cuerpos del correo y PDF adjunto DEBEN mostrar la misma conclusión conservada, independientemente de diferencias de presentación.
- **FR-013**: Ante timeout, fallo de conexión, cuota, credenciales rechazadas o respuesta inutilizable, AquaLab DEBE ofrecer una plantilla fija con los mismos hechos y avisar del respaldo, sin bloquear la emisión por el fallo externo.
- **FR-014**: Sin configuración de IA, AquaLab DEBE ofrecer el respaldo sin exigir habilitar el servicio para emitir. La plantilla DEBE ser editable y requerir aprobación para incorporarse.
- **FR-015**: Consultar, descargar, imprimir, enviar o reenviar un informe emitido NO DEBE regenerar la conclusión ni depender de IA.
- **FR-016**: Los informes anteriores DEBEN conservar sus copias y salidas sin conclusión añadida. Tampoco se permitirá agregar o sustituir conclusiones de informes ya emitidos.
- **FR-017**: Se DEBEN conservar las reglas actuales de estudio listo, firma y matrícula, permisos y confirmaciones de emisión y correo. No se incorporan recomendaciones de tratamiento ni cambios de resultados, límites, normas o validaciones.
- **FR-018**: AquaLab DEBE permitir un borrador parcial cuando haya pruebas sin validación vigente, límite comparable o norma registrada. DEBE incluir los hechos verificables de las pruebas con evaluación vigente e identificar expresamente las pruebas no evaluables y los motivos correspondientes. NO DEBE inventar límites, normas, resultados o incumplimientos ni utilizar valores actuales del catálogo para reemplazar una validación faltante. DEBE permitir editar y aprobar el borrador conservando las advertencias; mientras existan pruebas no evaluables, NO DEBE afirmarse cumplimiento íntegro del estudio. Se mantiene la opción de emitir sin conclusión bajo las reglas actuales.
- **FR-019**: La redacción DEBE reutilizar el servicio de US 10.1 y sus restricciones de privacidad: no enviar datos de contacto ni documento del cliente, credenciales o datos personales del usuario como hechos para redactar. La función nueva NO DEBE convertir el chat de consultas en una vía de aprobación, validación o emisión automática.

### Key Entities *(include if feature involves data)*

- **Estudio por informar**: reúne las pruebas revisadas y sigue sujeto a las condiciones existentes de emisión.
- **Resultado y validación vigente**: el resultado aporta valor y unidad; la validación no anulada aporta evaluación, límites y norma disponibles. Son los hechos de origen; el historial anulado y el catálogo actual no reemplazan una validación faltante. Una ausencia de norma o límite comparable se identifica como información insuficiente, no como cumplimiento.
- **Borrador de conclusión**: texto revisable, asistido o de plantilla fija, relacionado con sus hechos de origen. Puede ser parcial, identificando las pruebas no evaluables, sus motivos y los hechos verificables disponibles; sus advertencias se conservan al editar y aprobar. Se conserva al abandonar o recargar la vista con su estado real de aprobación; conservarlo no crea una aprobación.
- **Conclusión editada**: texto corregido o reescrito por el profesional, sujeto a aprobación expresa antes de incorporarse.
- **Aprobación profesional**: identifica qué persona autorizada aprobó una versión exacta del texto y sus hechos de origen. La invalidan una edición del texto, otra propuesta o un cambio de esos hechos; debe seguir vigente al emitir. Quien emite puede ser otro bioquímico autorizado y queda diferenciado de quien aprobó. No tiene expiración temporal definida en esta historia.
- **Informe emitido**: copia inmutable con la conclusión aprobada cuando la haya y su trazabilidad. Sus salidas posteriores parten de esa copia.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: En todos los casos de aceptación, el 100% de las pruebas fuera de norma con hechos verificables aparece una sola vez con datos concordantes con su validación vigente; las ausencias se identifican según FR-018 y se agregan cero hechos ajenos o validaciones inexistentes.
- **SC-002**: En todos los casos con pruebas íntegramente evaluables y con evaluación vigente «Cumple», propuesta y respaldo expresan ese cumplimiento. Si existe al menos una prueba no evaluable, se realizan cero afirmaciones de cumplimiento íntegro del estudio.
- **SC-003**: Cero informes de aceptación incorporan texto sin aprobación profesional expresa y vigente para esa versión exacta y sus hechos al emitir; el 100% de los casos de emisión sin conclusión mantiene esa opción con sus requisitos existentes, incluidas las aprobaciones invalidadas.
- **SC-004**: En todos los informes de aceptación con conclusión, consulta, PDF, impresión, ambos cuerpos del correo y adjunto conservan el 100% del contenido textual aprobado, salvo maquetación.
- **SC-005**: Todos los fallos y casos sin configuración definidos permiten obtener el respaldo o emitir sin conclusión; el vencimiento del tiempo de espera no deja la solicitud esperando indefinidamente.
- **SC-006**: El 100% de los informes históricos de la muestra de regresión conserva contenido y salidas sin conclusión añadida; ningún informe emitido permite cambiarla después.
- **SC-007**: El 100% de las conclusiones incorporadas permite identificar quién aprobó la versión emitida y las validaciones que fundamentaron sus datos, distinguiendo a la persona emisora si es otra; ninguna validación anulada se identifica como vigente.
- **SC-008**: Cero intentos de proponer o aprobar obtienen acceso si falta pertenencia a Bioquímicos, permiso efectivo de emisión o sesión activa, incluidos los accesos directos. Cero datos de contacto, documentos de clientes, credenciales o datos personales de usuarios se envían como hechos para redactar.
- **SC-009**: En el 100% de los casos de edición de texto aprobado, nueva propuesta o cambio de hechos, se invalida la aprobación anterior. En el 100% de los casos de abandono o recarga se conserva el borrador sin crear aprobaciones ni revalidar las que fueron invalidadas.
- **SC-010**: En el 100% de los casos de información insuficiente se ofrece un borrador parcial, asistido o de plantilla fija, que identifica las pruebas no evaluables y sus motivos y conserva los hechos verificables. Sus advertencias se mantienen al editar, aprobar y emitir con conclusión; cero datos se completan desde el catálogo actual para reemplazar validaciones faltantes.

## Assumptions

- El responsable proporcionó Q1–Q3 ya aprobadas; se incorporaron sin preguntas redundantes ni decisiones por inferencia. La sesión de aclaraciones y los requisitos registran las tres decisiones; no quedan aclaraciones funcionales pendientes.
- Se conserva el español, el vocabulario del laboratorio, la autenticación y la presentación común de AquaLab. «Fuera de norma» es la evaluación normativa, no el aviso de desvío histórico entre resultados.
- La IA ayuda a redactar; no valida ni aprueba. No se prometen recomendaciones de tratamiento, conclusiones sobre emitidos ni funciones nuevas del chat.
- «El correo muestra la conclusión» comprende el cuerpo en sus presentaciones disponibles y el adjunto, conforme al pedido de sumarla al informe y al correo; no implica envío automático al emitir ni cambio de destinatario.
- No se fija un nuevo tiempo numérico de espera ni una longitud máxima en esta fase. Se reutiliza el servicio con espera limitada; los límites técnicos se evaluarán al planificar y no constituyen nuevas reglas del laboratorio.

### Dependencias y comportamiento existente verificado

- **US 10.1 — Asistente**: [spec existente](../038-asistente-consultas/spec.md). Hay servicio configurable, manejo de fallos, restricciones de privacidad y pruebas simuladas. Su conversación es de consulta: no genera una conclusión aprobable ni registra aprobaciones. Reutilizar el servicio no autoriza al chat a escribir o emitir.
- **US 7.2 — Generar informe**: [spec existente](../021-generar-informe/spec.md). Vista previa y emisión construyen el documento con los datos del estudio; al emitir se conserva una copia. Hoy no hay conclusión ni aprobación de conclusión. El armado actual tiene un respaldo contra catálogo si falta validación: eso no acredita una validación vigente para esta historia y no debe adoptarse inadvertidamente como tal.
- **US 7.3 — PDF e impresión**: [spec existente](../022-consultar-exportar-informe/spec.md). Ambos parten de la copia emitida y comparten documento de impresión. La conclusión nueva deberá mantener esa identidad y compatibilidad con copias anteriores sin conclusión.
- **SCRUM-79 — Correo**: [spec existente](../029-enviar-informe/spec.md). El mensaje toma datos de la copia y adjunta su PDF; actualmente el cuerpo no contiene una conclusión. El destinatario es el correo actual del cliente y el envío requiere confirmación. Se agrega la conclusión aprobada conservando ese comportamiento.
- **Validación de resultados**: [spec existente](../019-validar-resultados/spec.md). Hay una validación vigente por prueba e historial anulado. La norma, límites y evaluación guardados al validar son la autoridad de la propuesta; el valor y unidad pertenecen al resultado asociado.
- **Autorización actual**: la vista previa admite empleados autenticados. Emitir y enviar requieren permiso efectivo de emisión, que Bioquímicos recibe habitualmente; validar resultados tiene su propia autorización. No existe actualmente una aprobación de conclusión. La política nueva de proponer y aprobar exige ambas condiciones de FR-009, sin cambiar los permisos de esas operaciones existentes.

El estado de calidad actualizado se refleja en los marcadores de la checklist. Sus notas iniciales se conservan sin editar conforme al workflow original; describen la revisión anterior a esta sesión, no aclaraciones todavía abiertas.

`$speckit-clarify` finaliza con las tres decisiones incorporadas y la especificación lista para revisión del responsable. No se ejecutaron `$speckit-plan`, `$speckit-tasks` ni `$speckit-implement`, ni se generaron código o tests de producto. La siguiente fase propuesta es `$speckit-plan`, sujeta a aprobación del responsable.
