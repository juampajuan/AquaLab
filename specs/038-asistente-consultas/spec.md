# Feature Specification: Asistente de consultas en lenguaje natural

**Feature Branch**: `038-asistente-consultas`

**Created**: 2026-11-15

**Status**: Borrador

**Input**: User description: "US 10.1 (SCRUM-83) – Asistente de consultas en lenguaje natural. Como bioquímico quiero preguntar en lenguaje natural por una muestra, un estudio o un cliente, para ver estados, resultados y qué no cumple sin recorrer pantallas. Criterios de aceptación: (1) Desde AquaLab se abre el asistente y se puede preguntar, por ejemplo: «¿Cómo está el PI 200417?», «¿Qué estudios tiene Lácteos del Sur?», «¿Qué no cumple en el estudio de la escuela N° 12?». (2) La respuesta usa solo datos del sistema: estado de la muestra y de sus estudios, pruebas con su estado, resultados y evaluación (cumple / fuera de norma / sin límite comparable) y la norma usada. (3) Si no encuentra lo que se pregunta (un N° PI inexistente, un cliente que no está), lo dice. No inventa datos. (4) Cada muestra, estudio o cliente mencionado tiene un enlace a su pantalla. (5) Respeta los permisos de quien pregunta: solo muestra lo que esa persona puede ver en las pantallas. (6) El asistente solo consulta: no crea, modifica ni borra nada. (7) Si el servicio de IA no responde o se agotó la cuota, muestra un aviso claro y el resto de AquaLab funciona igual. (8) Al servicio externo no se mandan datos de contacto del cliente (correo, teléfono, dirección). Fuera de alcance: guardar el historial de conversaciones; preguntas sobre el catálogo de pruebas o los usuarios; crear o modificar datos (US 10.3). Depende de: las consultas existentes de muestras, estudios, clientes y validación (US 5.2, 3.3, 6.4). Servicio de IA con plan gratuito (Groq), configurable por variable de entorno."

**Trazabilidad**: US 10.1, Jira SCRUM-83.

## Clarifications

### Session 2026-11-16 (validación con Groq y prueba visual)

- Q: ¿Qué muestra «¿Cómo está el PI…?»? → A: Por estudio, su estado y cuántas pruebas cumplen, están fuera de norma o sin límite comparable (los cuenta AquaLab), y solo las que no cumplen; el detalle completo queda en el enlace al estudio. El estado de la muestra no se muestra (SCRUM-82).
- Q: ¿Qué pasa con los enlaces cuando el asistente pide elegir entre varias coincidencias? → A: Son opciones que mandan la pregunta de seguimiento sin salir del panel, con un ↗ para abrir la pantalla. Las marca AquaLab desde la herramienta.
- Q: ¿Se pierde la conversación al seguir un enlace? → A: No: se guarda en el almacenamiento de la pestaña mientras el panel está abierto y se reabre en la pantalla nueva. Cerrar el panel, la pestaña o la sesión la borra. Nada va a la base (reemplaza «solo en la página abierta»).
- Q: ¿Se busca por fecha («el del mes 3»)? → A: No, queda fuera de alcance.

### Session 2026-11-15

- Q: ¿Quién puede usar el asistente? → A: Cualquier empleado con sesión iniciada (técnicos incluidos), sin permiso propio; las respuestas respetan los permisos de cada uno como las pantallas.
- Q: ¿Cómo se configura el servicio de IA? → A: Groq (plan gratuito, para la demo). Clave, dirección del servicio y modelo por variables de entorno en `.env`, con Groq por defecto; sin la clave AquaLab arranca igual y el asistente aparece deshabilitado. Los tests simulan el servicio y nunca llaman a Groq.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Preguntar por una muestra (Priority: P1)

Como bioquímico abro el asistente desde cualquier pantalla de AquaLab (no el admin) y pregunto por una muestra por su N° PI («¿Cómo está el PI 200417?»). El asistente responde con sus estudios y, para cada uno, su estado y un resumen de sus pruebas (cuántas cumplen, están fuera de norma o sin límite comparable), detallando las que no cumplen, con enlaces a la ficha de la muestra y de cada estudio, donde está el detalle completo.

**Why this priority**: Es la consulta más frecuente del laboratorio y la que más pantallas ahorra (muestra → estudio → pruebas). Sola ya entrega el valor de la historia.

**Independent Test**: Con la demo cargada, preguntar por el N° PI de una muestra con un estudio Finalizado y verificar que cada estado, resultado, evaluación y norma de la respuesta coincide con la ficha de la muestra y el detalle del estudio, y que los enlaces llevan a esas pantallas.

**Acceptance Scenarios**:

1. **Dado** un empleado con sesión iniciada en cualquier pantalla de AquaLab (no el admin), **cuando** toca «Asistente», **entonces** se abre un panel con un campo para escribir la pregunta y ejemplos de preguntas posibles.
2. **Dada** una muestra existente, **cuando** se pregunta «¿Cómo está el PI 200417?», **entonces** la respuesta indica el N° PI, el cliente, el origen, la fecha de ingreso y, por cada estudio, su tipo, su estado y cuántas pruebas cumplen, están fuera de norma o sin límite comparable (contadas por AquaLab), con las que no cumplen detalladas (nombre, resultado con su unidad); el detalle de todas las pruebas (estado, resultado, evaluación, límite y norma) está en el estudio enlazado y se obtiene preguntando por el estudio. El estado de la muestra no se muestra (SCRUM-82 lo sacó de la ficha).
3. **Dada** la respuesta, **cuando** se mira, **entonces** la muestra y cada estudio mencionados tienen un enlace a su pantalla (ficha de la muestra, detalle del estudio).
4. **Dado** un N° PI que no existe, **cuando** se pregunta por él, **entonces** el asistente responde que no hay ninguna muestra con ese N° PI, sin mostrar datos de otra muestra.
5. **Dada** una prueba sin resultado (Pendiente, o sin curva o fórmula calculable), **cuando** aparece en la respuesta, **entonces** se indica que no tiene resultado (y el motivo que muestra el sistema), nunca un valor estimado.
6. **Dada** una prueba con resultado todavía no validado, **cuando** aparece en la respuesta, **entonces** se indica que no está validada y su evaluación se presenta igual que en el detalle del estudio.
7. **Dada** una muestra con más estudios de los que el asistente puede detallar en una respuesta (más de 5), **cuando** se pregunta por ella, **entonces** se detallan los 5 más recientes, la respuesta avisa cuántos estudios tiene en total y que el resto está en la ficha de la muestra, y siempre incluye el enlace a esa ficha.

---

### User Story 2 - Preguntar qué no cumple (Priority: P1)

Como bioquímico pregunto qué no cumple en un estudio o en una muestra («¿Qué no cumple en el estudio de la escuela N° 12?») y el asistente me lista solo las pruebas fuera de norma, con su resultado, el límite y la norma usada.

**Why this priority**: Es la pregunta que motiva la historia: encontrar los incumplimientos sin abrir cada estudio.

**Independent Test**: Con un estudio que tiene una prueba fuera de norma, una que cumple y una sin límite comparable, preguntar qué no cumple y verificar que la respuesta nombra solo la fuera de norma, con valor, límite y norma iguales a los del detalle del estudio.

**Acceptance Scenarios**:

1. **Dado** un estudio con pruebas fuera de norma, **cuando** se pregunta qué no cumple, **entonces** se listan solo esas pruebas con su resultado y unidad, el límite aplicado y la norma, con enlace al estudio.
2. **Dado** un estudio sin pruebas fuera de norma, **cuando** se pregunta qué no cumple, **entonces** el asistente responde que no hay pruebas fuera de norma y aclara cuántas pruebas no tienen resultado o no tienen límite comparable, si las hay.
3. **Dada** una pregunta que coincide con más de un estudio o muestra (por ejemplo, la escuela tiene varios estudios), **cuando** se responde, **entonces** el asistente muestra las coincidencias (con N° PI, fecha y estado, cada una con su enlace) y pide elegir, o responde por el más reciente diciéndolo explícitamente.
4. **Dada** una pregunta por un origen o cliente que no se encuentra, **cuando** se responde, **entonces** el asistente dice que no lo encontró, sin inventar uno parecido como si fuera el pedido.

---

### User Story 3 - Preguntar por un cliente (Priority: P2)

Como bioquímico pregunto por un cliente («¿Qué estudios tiene Lácteos del Sur?») y el asistente me muestra sus muestras y estudios recientes con su estado, con enlaces a la ficha del cliente, a su historial y a cada estudio.

**Why this priority**: Aporta una vista rápida del cliente, pero el historial del cliente (US 3.3) ya cubre esa necesidad en pantalla.

**Independent Test**: Preguntar por un cliente con varias muestras y verificar que la respuesta coincide con su historial (orden, estados, tipos de estudio) y enlaza a la ficha y al historial.

**Acceptance Scenarios**:

1. **Dado** un cliente activo con muestras, **cuando** se pregunta qué estudios tiene, **entonces** se listan sus estudios más recientes (N° PI, origen, tipo de estudio, fecha y estado), en el mismo orden que su historial, con enlace a cada uno y a la ficha y el historial del cliente.
2. **Dado** un cliente con más estudios de los que entran en una respuesta, **cuando** se responde, **entonces** se muestran los más recientes, se indica cuántos hay en total y se ofrece el enlace al historial completo.
3. **Dado** un nombre de cliente que no existe, **cuando** se pregunta, **entonces** el asistente dice que no encontró ese cliente.
4. **Dado** un nombre que coincide con varios clientes, **cuando** se pregunta, **entonces** el asistente lista los clientes encontrados (cada uno con su enlace) y pide elegir.
5. **Dado** un cliente inactivo, **cuando** se pregunta por él, **entonces** el asistente indica que el cliente está inactivo y no muestra más datos que los que muestran las pantallas para un cliente inactivo.
6. **Dada** cualquier respuesta sobre un cliente, **cuando** se mira, **entonces** no incluye su correo, teléfono ni domicilio.

---

### User Story 4 - Seguir trabajando cuando el asistente no está disponible (Priority: P2)

Si el servicio de IA no responde, rechaza la consulta o se agotó la cuota, el asistente muestra un aviso claro y el resto de AquaLab funciona igual.

**Why this priority**: El servicio externo es gratuito y con cuota; su caída no puede afectar el trabajo del laboratorio.

**Independent Test**: Simular el servicio caído, lento y sin cuota; verificar el aviso en cada caso y que las demás pantallas siguen funcionando con normalidad.

**Acceptance Scenarios**:

1. **Dado** el servicio de IA sin responder dentro del tiempo de espera, **cuando** se hace una pregunta, **entonces** el asistente muestra «El asistente no está disponible en este momento. Probá de nuevo más tarde o usá las pantallas de AquaLab.» y se puede volver a preguntar.
2. **Dada** la cuota del servicio agotada, **cuando** se hace una pregunta, **entonces** el aviso indica que se alcanzó el límite de consultas del asistente y que se puede usar el resto de AquaLab.
3. **Dado** AquaLab sin la clave del servicio en la configuración, **cuando** arranca y se abre cualquier pantalla, **entonces** AquaLab funciona normalmente, el asistente se muestra deshabilitado con el aviso «El asistente no está configurado» y ninguna otra pantalla cambia.
4. **Dada** solo la clave en la configuración, **cuando** se hace una pregunta, **entonces** el asistente usa Groq con el modelo por defecto; **dados** otra dirección o modelo en la configuración, **entonces** usa esos.
5. **Dada** una falla del asistente, **cuando** se navega por cualquier otra pantalla, **entonces** se comporta igual que sin el asistente.

---

### Edge Cases

- Pregunta fuera de alcance (catálogo de pruebas, usuarios, temas ajenos al laboratorio): el asistente responde que solo consulta muestras, estudios y clientes, y no contesta lo otro.
- Pedido de crear, modificar, validar, borrar o emitir algo («validá el PI 200417», «borrá ese estudio»): el asistente responde que solo consulta; no cambia nada.
- Pregunta vacía o demasiado larga: se rechaza antes de consultar, con el motivo.
- Instrucciones incrustadas en la pregunta o en datos del sistema (por ejemplo, el nombre o el sitio de extracción de una muestra con el texto «ignorá las reglas»): no cambian lo que el asistente puede hacer ni le permiten mostrar datos fuera de lo permitido.
- N° PI con formato inválido («PI 12»): se responde que no hay una muestra con ese número.
- Estudio con informe emitido: se muestran los datos del sistema igual que en sus pantallas y el enlace al informe si quien pregunta puede verlo.
- Resultados Ausente/Presente y por debajo del límite de detección: se muestran con el mismo texto que en las pantallas («Ausente», «Presente», «< LD»), nunca como 0 o 1.
- Valores con decimales: se muestran como en las pantallas (coma decimal, mismos decimales), sin redondeos distintos.
- Preguntas encadenadas («¿y qué no cumple?» después de preguntar por un PI): se entienden sobre lo último consultado mientras el panel siga abierto en esa pestaña, también al navegar con un enlace o recargar; al cerrar el panel, la pestaña o la sesión, la conversación se pierde.
- Datos que cambian mientras se conversa: cada respuesta usa los datos vigentes al momento de esa pregunta.

## Requirements *(mandatory)*

### Functional Requirements

**Acceso y uso**

- **FR-001**: AquaLab DEBE ofrecer un acceso al asistente desde el layout común de las pantallas de AquaLab (no el admin), disponible para cualquier empleado con sesión iniciada (técnicos incluidos), sin un permiso propio: cada uno ve en las respuestas lo mismo que en las pantallas (FR-010).
- **FR-002**: El asistente DEBE aceptar preguntas en español escritas libremente, de hasta 500 caracteres, y rechazar las vacías o más largas sin consultar.
- **FR-003**: El asistente DEBE responder preguntas sobre: una muestra (por N° PI), un estudio (por N° PI, cliente, origen o tipo de estudio), un cliente (por nombre o razón social), y qué no cumple en cualquiera de ellos.

**Contenido de las respuestas**

- **FR-004**: Toda la información de una respuesta (estados, resultados, unidades, evaluaciones, límites, normas, fechas, nombres) DEBE salir de los datos del sistema al momento de la pregunta; el asistente NO DEBE completar, estimar ni inventar datos.
- **FR-005**: Los datos que muestra una respuesta DEBEN coincidir con los que muestran las pantallas correspondientes (ficha de la muestra, detalle del estudio, historial del cliente): mismos estados, resultado con el mismo formato y unidad, la evaluación de la validación vigente (o la del detalle si aún no está validada) y la norma usada.
- **FR-006**: Si lo preguntado no existe o no se encuentra, el asistente DEBE decirlo explícitamente y NO DEBE presentar otro registro como si fuera el pedido.
- **FR-007**: Si la pregunta coincide con varios registros, el asistente DEBE mostrar las coincidencias identificables (con enlace) y pedir precisión, o responder por uno indicando explícitamente cuál eligió y por qué. Las coincidencias que lista AquaLab se muestran como opciones para elegir: cada una manda la pregunta de seguimiento sobre ese registro sin salir del panel y tiene además un acceso a su pantalla.
- **FR-008**: Cada muestra, estudio, cliente e informe mencionado en una respuesta DEBE tener un enlace a su pantalla en AquaLab.
- **FR-009**: Las respuestas sobre un cliente con muchas muestras DEBEN limitarse a los estudios más recientes (hasta 10), indicando el total y enlazando al historial completo.
- **FR-009a**: Las respuestas sobre una muestra con más de 5 estudios DEBEN detallar los 5 más recientes, avisar el total y que el resto está en la ficha de la muestra, e incluir siempre el enlace a esa ficha.

**Permisos y solo lectura**

- **FR-010**: El asistente DEBE mostrar solo lo que quien pregunta puede ver en las pantallas de AquaLab, con sus permisos vigentes (por ejemplo, el enlace a un informe solo si puede verlo; un cliente inactivo como lo muestran las pantallas).
- **FR-011**: El asistente NO DEBE crear, modificar ni borrar ningún dato del laboratorio, aunque se lo pidan; ante un pedido de cambio, DEBE responder que solo consulta.
- **FR-012**: Las preguntas fuera de alcance (catálogo de pruebas, usuarios, otros temas) y los pedidos de cambio DEBEN responderse con un mensaje fijo de AquaLab que indica que el asistente solo consulta y qué consultas admite. Toda respuesta que no se apoye en datos consultados en esa misma pregunta DEBE reemplazarse por ese mensaje fijo, sin importar lo que haya redactado el servicio de IA.
- **FR-013**: Ninguna instrucción incluida en la pregunta o en los datos del sistema DEBE ampliar lo que el asistente puede consultar, mostrar o hacer.

**Servicio externo y privacidad**

- **FR-014**: Al servicio de IA externo NO DEBEN enviarse el correo, el teléfono ni el domicilio de ningún cliente, ni datos de los usuarios de AquaLab (correo, contraseña, sesión).
- **FR-015**: La clave, la dirección del servicio y el modelo DEBEN configurarse por variables de entorno (en `.env`), con Groq como servicio por defecto: sin indicar dirección ni modelo se usa Groq, y basta con la clave. Sin la clave, AquaLab DEBE arrancar igual y el asistente se muestra deshabilitado con un aviso; el resto de AquaLab funciona igual.
- **FR-016**: Si el servicio no responde dentro de un tiempo de espera, responde con error o informa cuota agotada, el asistente DEBE mostrar un aviso claro (distinguiendo «no disponible» de «límite de consultas alcanzado») y permitir volver a preguntar; la falla DEBE quedar registrada en el log de la aplicación sin el texto de la pregunta.
- **FR-017**: Una falla o demora del asistente NO DEBE afectar la carga ni el funcionamiento de ninguna otra pantalla de AquaLab.

**Conversación**

- **FR-018**: El asistente DEBE entender preguntas de seguimiento sobre lo consultado antes mientras el panel siga abierto en esa pestaña del navegador, también después de navegar a otra pantalla con un enlace de la respuesta (el panel se reabre con la conversación).
- **FR-019**: Las conversaciones NO DEBEN guardarse en AquaLab (ni en la base ni en el servidor). Solo el navegador las guarda, en el almacenamiento de esa pestaña y mientras el panel esté abierto, para seguirlas al navegar; se borran al cerrar el panel, al cerrar la pestaña o la sesión, y en cualquier pantalla sin panel (inicio de sesión).

### Key Entities *(include if feature involves data)*

- **Pregunta**: texto libre de quien pregunta; no se guarda.
- **Respuesta del asistente**: texto en español con los datos encontrados y enlaces a las pantallas de los registros mencionados; no se guarda.
- **Datos consultados** (existentes, solo lectura): Muestra (N° PI, cliente, origen, fechas, estado), Estudio (tipo según su copia, estado, informe), Prueba del estudio (estado, medición, resultado con unidad, validación vigente con evaluación y límites usados), Cliente (nombre, estado activo/inactivo; sin datos de contacto hacia el servicio externo).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: En un conjunto de al menos 20 preguntas de prueba sobre la demo (muestras, estudios, clientes, «qué no cumple», registros inexistentes), el 100 % de los datos mostrados coincide con las pantallas de AquaLab y ninguna respuesta incluye un dato que no esté en el sistema.
- **SC-002**: El 100 % de las preguntas por un N° PI, cliente u origen inexistente responde que no lo encontró.
- **SC-003**: Un bioquímico obtiene qué no cumple en un estudio con una sola pregunta, sin abrir pantallas, en menos de 15 segundos desde que envía la pregunta (con el servicio disponible).
- **SC-004**: El 100 % de los registros mencionados en las respuestas tiene un enlace que lleva a su pantalla.
- **SC-005**: Ninguna consulta al asistente cambia datos del laboratorio (verificable: la base queda igual antes y después de cualquier pregunta, incluidas las que piden cambios).
- **SC-006**: Ningún envío al servicio externo contiene correo, teléfono o domicilio de un cliente.
- **SC-007**: Con el servicio caído, sin cuota o sin configurar, el 100 % de las demás pantallas funciona igual y el asistente muestra el aviso correspondiente en menos de 20 segundos.

## Assumptions

- El servicio de IA es Groq con su plan gratuito, pensado para la demo; el modelo por defecto se elige en el plan y se puede cambiar por variable de entorno sin tocar el código. El texto de la respuesta lo redacta el servicio, pero los datos que contiene los obtiene AquaLab con sus consultas existentes (US 5.2, 3.3, 6.4) y los permisos de quien pregunta.
- Los nombres de cliente, origen, tipos de estudio y pruebas, y los resultados, sí se envían al servicio externo: son necesarios para responder y no son datos de contacto.
- La búsqueda por nombre de cliente u origen no distingue mayúsculas ni acentos y admite coincidencias parciales, como las búsquedas existentes.
- «Más reciente» sigue el orden del historial del cliente (fecha de ingreso y N° PI descendentes).
- El tiempo de espera del servicio es de unos 15 segundos; el número exacto se fija en el plan.
- No se pide un límite de preguntas por usuario: la cuota es la del servicio gratuito.
- Los tests automatizados simulan el servicio de IA (respuestas, demoras, errores y cuota agotada) y nunca llaman a Groq: corren sin clave y sin conexión, también en el CI.
- Interfaz orientada a escritorio, como el resto de AquaLab.
- Fuera de alcance: guardar conversaciones en AquaLab, búsquedas por fecha o período («el estudio de agosto», «el del mes 3»: el asistente solo puede elegir entre las coincidencias listadas, que traen su fecha), preguntas sobre el catálogo de pruebas o los usuarios, la comparación histórica y los desvíos (US 8.1 y 8.2), el dashboard, y crear o modificar datos (US 10.3).
