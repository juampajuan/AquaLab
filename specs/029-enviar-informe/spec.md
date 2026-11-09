# Feature Specification: Envío del informe por correo

**Feature Branch**: `029-enviar-informe`

**Created**: 2026-11-09

**Status**: Borrador

**Input**: User description: "SCRUM-79 – Envío de informe por mail. Decisiones del autor (la tarjeta no tiene criterios): (1) El envío es manual: un botón «Enviar por correo» en el informe emitido, con confirmación, que permite volver a enviarlo. (2) Se envía siempre al correo del cliente registrado en su ficha (`Cliente.email`). (3) Se guarda el historial de envíos (quién, cuándo, a qué dirección y si salió bien) y se muestra en el informe. (4) Puede enviarlo quien puede emitir informes (Bioquímicos)."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Enviar el informe al cliente (Priority: P1)

Como bioquímico, desde un informe emitido elijo «Enviar por correo», reviso a qué dirección va a salir y confirmo; el cliente recibe un correo de AquaLab con el informe en PDF adjunto.

**Why this priority**: Es el objetivo de la tarjeta: que el cliente reciba su informe sin que el laboratorio tenga que descargarlo y mandarlo a mano.

**Independent Test**: Con un informe emitido de un cliente con correo, abrir el informe, elegir «Enviar por correo», confirmar y verificar que sale un único correo a la dirección del cliente, con el PDF del informe adjunto, y que se ve el aviso de éxito.

**Acceptance Scenarios**:

1. **Dado** un informe emitido y un usuario que puede emitir informes, **cuando** abre el informe, **entonces** ve la acción «Enviar por correo».
2. **Dada** la acción «Enviar por correo», **cuando** se elige, **entonces** el sistema muestra una confirmación con el número del informe, el cliente y la dirección a la que se enviará, y no envía nada todavía.
3. **Dada** la confirmación, **cuando** el usuario confirma, **entonces** se envía un correo a la dirección del cliente con el informe en PDF adjunto (el mismo que se descarga desde el informe) y el usuario vuelve al informe con un aviso de que se envió a esa dirección.
4. **Dada** la confirmación, **cuando** el usuario cancela, **entonces** vuelve al informe sin enviar nada ni registrar un envío.
5. **Dado** el correo enviado, **cuando** el cliente lo recibe, **entonces** está en español, identifica a AquaLab, indica el número de informe, la muestra (N° PI) y el estudio, y no incluye datos de acceso ni información de otros clientes.

---

### User Story 2 - Historial de envíos (Priority: P2)

Como empleado del laboratorio, en el informe veo cada vez que se envió: quién lo envió, cuándo, a qué dirección y si salió bien, para responder si el cliente dice que no lo recibió.

**Why this priority**: Da trazabilidad a los envíos, pero el envío de la US 1 ya resuelve la necesidad principal.

**Independent Test**: Enviar un informe dos veces (una con éxito y otra simulando una falla del servidor de correo) y verificar que el informe muestra los dos envíos, del más reciente al más antiguo, con usuario, fecha, dirección y resultado.

**Acceptance Scenarios**:

1. **Dado** un informe sin envíos, **cuando** se muestra, **entonces** indica que todavía no se envió por correo.
2. **Dado** un envío confirmado, **cuando** termina, **entonces** queda registrado con el usuario, la fecha y hora, la dirección usada y el resultado (enviado o falló).
3. **Dado** un informe con envíos, **cuando** se muestra, **entonces** lista todos sus envíos del más reciente al más antiguo.
4. **Dado** un informe ya enviado, **cuando** el usuario elige «Enviar por correo» otra vez, **entonces** la confirmación le avisa cuándo fue el último envío exitoso y, si confirma, se envía y registra de nuevo.

---

### User Story 3 - Fallas y casos que impiden el envío (Priority: P2)

Como bioquímico, si el correo no puede salir, el sistema me lo dice claramente y el informe no se altera, para que pueda reintentar o avisar al cliente por otro medio.

**Why this priority**: Un servidor de correo caído o un dato faltante no pueden romper la pantalla del informe ni dejar dudas de si el cliente lo recibió.

**Independent Test**: Simular una falla del servidor de correo y verificar que el usuario ve un mensaje de error, que el envío queda registrado como fallido y que el informe sigue igual; con un usuario sin el permiso, verificar que no ve la acción y que no puede enviar.

**Acceptance Scenarios**:

1. **Dada** una falla al enviar (servidor de correo caído o que rechaza el mensaje) o al generar el PDF, **cuando** se confirma, **entonces** el usuario vuelve al informe con un mensaje de que no se pudo enviar y que intente nuevamente, el envío queda registrado como fallido y la falla queda en el log del sistema.
2. **Dado** un usuario sin permiso para emitir informes, **cuando** abre un informe, **entonces** no ve «Enviar por correo», y si intenta enviarlo igual, el sistema lo rechaza sin enviar ni registrar nada.
3. **Dado** un estudio sin informe emitido, **cuando** se intenta enviar su informe, **entonces** el sistema responde que no existe (no hay nada para enviar).
4. **Dado** un doble clic o un reenvío del formulario de confirmación, **cuando** llegan dos pedidos seguidos, **entonces** se envía y registra un solo correo por confirmación.

---

### Edge Cases

- El correo del cliente cambió después de emitir el informe: se envía a la dirección actual de la ficha del cliente, que es la que se muestra en la confirmación y queda en el historial.
- Cliente inactivo: el informe sigue disponible y se puede enviar a su correo registrado.
- El envío no cambia el informe emitido, su contenido, su número ni el estado del estudio: sigue siendo inalterable (US 7.3).
- Informe anterior a la firma (sin firma registrada): se envía igual, con el PDF tal como se descarga.
- Un envío fallido no impide reintentar: cada intento queda registrado.
- En desarrollo y en los tests, los correos se muestran en la consola o se capturan; con los datos del servidor de correo configurados, salen de verdad (mismo criterio que la US 1.3).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: La pantalla del informe emitido MUST ofrecer «Enviar por correo» a los usuarios que pueden emitir informes, y MUST NOT ofrecerlo a los demás.
- **FR-002**: «Enviar por correo» MUST pedir confirmación mostrando el número de informe, el cliente y la dirección de destino; sin confirmar, MUST NOT enviar ni registrar nada.
- **FR-003**: Al confirmar, el sistema MUST enviar un único correo a la dirección del cliente registrada en su ficha al momento del envío, con el informe en PDF adjunto, idéntico al que se descarga desde el informe.
- **FR-004**: El correo MUST estar en español, identificar a AquaLab e indicar el número de informe, el N° PI de la muestra y el estudio; MUST NOT incluir contraseñas, enlaces que requieran sesión ni datos de otros clientes.
- **FR-005**: Cada envío confirmado MUST quedar registrado con el informe, el usuario, la fecha y hora, la dirección usada y el resultado (enviado o falló); los registros MUST NOT poder modificarse ni borrarse desde la aplicación.
- **FR-006**: La pantalla del informe MUST mostrar el historial de envíos del más reciente al más antiguo, o indicar que todavía no se envió.
- **FR-007**: Un informe ya enviado MUST poder enviarse de nuevo; la confirmación MUST avisar la fecha del último envío exitoso.
- **FR-008**: Si el envío o la generación del PDF fallan, el usuario MUST ver un mensaje de error claro, el envío MUST registrarse como fallido y la falla MUST quedar en el log; la pantalla MUST seguir funcionando.
- **FR-009**: El sistema MUST rechazar el envío de usuarios sin permiso para emitir informes, aunque lo intenten sin pasar por la pantalla, sin enviar ni registrar nada.
- **FR-010**: Cada confirmación MUST producir como máximo un envío, aunque el formulario se envíe dos veces.
- **FR-011**: Enviar MUST NOT modificar el informe emitido, su contenido ni el estado del estudio.

### Key Entities *(include if feature involves data)*

- **Informe** (US 7.2/7.3): El informe emitido que se envía; no cambia.
- **Cliente** (US 2.1): Dueño del estudio; su correo de la ficha es el destino.
- **Envío de informe** (nuevo): Cada intento confirmado de enviar un informe por correo; guarda el informe, quién lo envió, cuándo, a qué dirección y el resultado.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Un bioquímico envía un informe emitido al cliente en no más de 2 acciones desde la pantalla del informe (elegir y confirmar).
- **SC-002**: El 100% de los envíos confirmados (exitosos o fallidos) quedan en el historial del informe.
- **SC-003**: Ninguna falla del servidor de correo produce una página de error: el usuario siempre ve un mensaje y vuelve al informe.
- **SC-004**: El PDF adjunto es idéntico al que se descarga desde el informe.

## Assumptions

- **Trazabilidad**: SCRUM-79 – Envío de informe por mail (tarea del Sprint 4). Resuelve el pendiente «Envío de informes (SCRUM-39)» de `CLAUDE.md`. Responsable: JuanJTorga.
- **Alcance decidido por el autor**: envío manual con confirmación y reenvío; destino = correo del cliente en su ficha; historial visible en el informe; permiso = el de emitir informes (Bioquímicos).
- **Dependencias**: Informe emitido e inalterable (US 7.2/7.3), PDF del informe (US 7.3), correo del cliente (US 2.1/3.2) y configuración de correo y criterio de fallas de la US 1.3.
- **Remitente**: el remitente configurado del sistema (el mismo de los avisos de la US 1.3).
- **Interfaz**: diseño de SCRUM-67 con `templates/ui/` y la confirmación común del sistema.
- **Datos académicos**: AquaLab es un proyecto FIUBA; los datos de desarrollo y demostración son ficticios (DEMO).
- **Alcance excluido**: envío automático al emitir; elegir o agregar destinatarios; envío masivo de varios informes; reintentos automáticos; confirmación de lectura o de entrega por parte del cliente; plantillas de correo editables.
