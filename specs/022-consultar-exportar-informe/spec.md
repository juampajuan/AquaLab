# Feature Specification: Consultar y exportar informe

**Feature Branch**: `022-consultar-exportar-informe`

**Created**: 2026-11-02

**Status**: Aprobada (2026-11-02)

**Input**: User description: "SCRUM-59 – US 7.3 Consultar y exportar informe. Como empleado del laboratorio quiero consultar los informes emitidos y exportarlos en el formato que necesite para entregar los resultados al cliente de forma física o digital. Criterios (Jira): (1) Se debe poder buscar y acceder a los informes de estudios finalizados. (2) Se debe poder seleccionar el formato de exportación (PDF o imprimir en hoja A4). (3) El documento exportado debe mantener fidelidad de datos, membrete y firma profesional. (4) El informe emitido debe quedar registrado inalterable para auditorías y consultas posteriores. Alcance: listado de informes emitidos con búsqueda por número, cliente (nombre, razón social o documento) y N° PI y filtro por fechas de emisión, desde el menú, para cualquier empleado con sesión; PDF A4 generado en el servidor (descarga) e impresión A4 desde el navegador, siempre a partir de la copia congelada; membrete con los datos institucionales de la US 7.2; firma profesional dibujada una sola vez por cada usuario con «Puede emitir informes» en la pantalla «Mi firma», junto con su matrícula, guardada como imagen chica; sin firma no puede emitir; al emitir se copian firma, nombre y matrícula en el informe; los informes anteriores sin firma se exportan con «Sin firma registrada»; el informe emitido no se edita ni se borra. Fuera de alcance: envío por correo (SCRUM-39), anular o reemitir informes, firma digital con validez legal, conclusión asistida (US 7.4)."

## Clarifications

### Session 2026-11-02

Decisiones tomadas por el usuario en la descripción de la historia:

- Q: ¿Qué formatos de exportación hay? → A: PDF A4 generado por el sistema y descargado, e impresión en A4 desde el navegador. Los dos salen de la copia guardada al emitir.
- Q: ¿Qué es la «firma profesional»? → A: Una imagen de la firma manuscrita que cada emisor dibuja una vez en pantalla («Mi firma»), con su matrícula. No es una firma digital con certificado (fuera de alcance).
- Q: ¿Se puede emitir sin firma? → A: No. Quien tiene «Puede emitir informes» y no cargó su firma no puede emitir hasta cargarla.
- Q: ¿Cambiar la firma cambia los informes ya emitidos? → A: No. Al emitir se copian en el informe la firma, el nombre y la matrícula de quien emite.
- Q: ¿Qué pasa con los informes emitidos antes de esta historia? → A: Se consultan y exportan igual, con la leyenda «Sin firma registrada» en el lugar de la firma.
- Q: ¿Quién ve el listado y exporta? → A: Cualquier empleado con sesión.
- Q: ¿Por qué se busca? → A: Número de informe, cliente (nombre, razón social o documento) y N° PI, con filtro por rango de fechas de emisión.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Buscar y abrir un informe emitido (Priority: P1)

Como empleado del laboratorio, desde el menú abro «Informes emitidos», busco por número de informe, cliente o N° PI (y si hace falta acoto por fechas de emisión) y abro el informe que necesito.

**Why this priority**: Es el primer criterio de la historia y la puerta de entrada para exportar: sin encontrar el informe no se puede entregar.

**Independent Test**: Con tres informes emitidos de dos clientes distintos, buscar por el número de uno, por el documento del cliente y por un N° PI, y por un rango de fechas que deje afuera a uno; verificar que cada búsqueda muestra solo los que corresponden y que al abrir uno se ve el informe emitido.

**Acceptance Scenarios**:

1. **Dado** un empleado con sesión, **cuando** abre «Informes emitidos» desde el menú, **entonces** ve los informes emitidos, del más reciente al más antiguo, con número, fecha de emisión, cliente, N° PI, estudio y quién lo emitió.
2. **Dado** el listado, **cuando** busca por número de informe (ej. «INF-000002» o «2»), **entonces** ve solo ese informe.
3. **Dado** el listado, **cuando** busca por nombre, razón social o número de documento del cliente, **entonces** ve solo los informes de los clientes que coinciden.
4. **Dado** el listado, **cuando** busca por N° PI, **entonces** ve solo los informes de esa muestra.
5. **Dado** el listado, **cuando** indica una fecha desde y/o hasta, **entonces** ve solo los informes emitidos en ese rango, con ambos extremos incluidos; el filtro se combina con la búsqueda.
6. **Dada** una búsqueda sin coincidencias, **cuando** se muestra, **entonces** el listado indica que no hay informes que coincidan.
7. **Dado** un informe del listado, **cuando** lo abre, **entonces** ve el informe emitido tal como se guardó al emitir, con las acciones de exportar.
8. **Dada** una búsqueda con fecha «desde» posterior a la fecha «hasta» o con una fecha inválida, **cuando** se envía, **entonces** se informa el error y no se filtra a ciegas.

---

### User Story 2 - Exportar el informe a PDF o imprimirlo en A4 (Priority: P1)

Como empleado del laboratorio, desde un informe emitido elijo «Descargar PDF» para enviarlo en forma digital o «Imprimir» para entregarlo en papel. En los dos casos el documento sale en hoja A4, con el membrete del laboratorio, todos los datos del informe y la firma de quien lo emitió.

**Why this priority**: Es el objetivo de la historia: entregar los resultados al cliente en el formato que necesite.

**Independent Test**: Con un informe emitido por un bioquímico con firma cargada, descargar el PDF y verificar que es A4, que se llama con el número del informe y que contiene el membrete, los datos del cliente, de la muestra, del estudio, cada prueba con su resultado y evaluación, y la firma con nombre y matrícula; abrir la vista de impresión y verificar que solo se imprime el documento.

**Acceptance Scenarios**:

1. **Dado** un informe emitido, **cuando** el empleado elige «Descargar PDF», **entonces** recibe un archivo PDF en hoja A4 cuyo nombre incluye el número del informe (ej. «INF-000001.pdf»).
2. **Dado** el PDF, **cuando** se abre, **entonces** contiene exactamente los mismos datos que el informe emitido en pantalla: membrete (nombre del laboratorio, dirección, matrícula, logo), cliente, muestra, estudio y cada prueba con resultado, unidad, límite, norma y evaluación, con lo fuera de norma resaltado, «< LD» y «Ausente»/«Presente» como en pantalla.
3. **Dado** un informe emitido con firma, **cuando** se exporta, **entonces** muestra la firma, el nombre y la matrícula de quien lo emitió, la fecha de emisión y el número del informe.
4. **Dado** un informe emitido antes de esta historia (sin firma guardada), **cuando** se exporta, **entonces** en el lugar de la firma dice «Sin firma registrada» y el resto del documento sale completo.
5. **Dado** un informe emitido, **cuando** el empleado elige «Imprimir», **entonces** se abre la impresión del navegador con el documento en A4, sin menú, botones ni otros elementos de la pantalla.
6. **Dado** un informe con muchas pruebas que ocupa más de una hoja, **cuando** se exporta o imprime, **entonces** las hojas llevan número de página y el número del informe, y ninguna fila de prueba queda partida entre dos hojas.
7. **Dado** un informe emitido, **cuando** después se editan el cliente, el catálogo, los datos institucionales o la firma del emisor, **entonces** el PDF y la impresión siguen mostrando los datos guardados al emitir.

---

### User Story 3 - Cargar mi firma y matrícula (Priority: P1)

Como bioquímico, entro a «Mi firma», dibujo mi firma con el mouse o el dedo y cargo mi matrícula. Desde ahí puedo emitir informes, que saldrán con mi firma.

**Why this priority**: La firma profesional es un criterio de aceptación, y sin ella ningún bioquímico podría emitir después de esta historia.

**Independent Test**: Con un bioquímico sin firma, verificar que no puede emitir y que se le indica cargarla; cargar firma y matrícula en «Mi firma», emitir un informe y verificar que el informe muestra esa firma, el nombre y la matrícula.

**Acceptance Scenarios**:

1. **Dado** un usuario con el permiso «Puede emitir informes», **cuando** abre «Mi firma» desde el menú de usuario, **entonces** ve un recuadro para dibujar la firma con el mouse o el dedo, un campo para la matrícula y, si ya la cargó, su firma y matrícula actuales.
2. **Dado** «Mi firma», **cuando** dibuja la firma, completa la matrícula y guarda, **entonces** queda guardada y se informa el éxito.
3. **Dado** «Mi firma», **cuando** intenta guardar con el recuadro vacío o sin matrícula, **entonces** se rechaza indicando qué falta y no cambia lo guardado.
4. **Dado** el recuadro de firma, **cuando** se equivoca, **entonces** puede borrar el trazo y volver a dibujar antes de guardar.
5. **Dado** un usuario con firma cargada, **cuando** la vuelve a dibujar o cambia la matrícula y guarda, **entonces** se usan las nuevas en los informes que emita desde entonces; los ya emitidos no cambian.
6. **Dado** un usuario sin el permiso «Puede emitir informes», **cuando** intenta abrir «Mi firma», **entonces** no ve la opción en el menú y el acceso se rechaza.
7. **Dado** un usuario con el permiso y sin firma cargada, **cuando** abre la vista previa de la US 7.2, **entonces** en lugar de «Emitir informe» ve un aviso con el enlace a «Mi firma»; **cuando** intenta emitir por otra vía, **entonces** se rechaza con ese motivo y no se emite nada.
8. **Dado** un usuario con firma cargada, **cuando** emite un informe (US 7.2), **entonces** el informe guarda una copia de su firma, su nombre y su matrícula, y la vista previa muestra cómo saldrá firmado.

---

### User Story 4 - Informe inalterable para auditorías (Priority: P2)

Como laboratorio, quiero que el informe emitido quede registrado tal como se entregó y no se pueda editar ni borrar, para poder auditarlo y volver a consultarlo en cualquier momento.

**Why this priority**: Es un criterio de aceptación y un principio del proyecto; la emisión de la US 7.2 ya guarda la copia, esta historia asegura que ninguna vía la cambie.

**Independent Test**: Con un informe emitido, verificar que ninguna pantalla (incluida la administración) permite modificarlo ni borrarlo, y que exportarlo dos veces en momentos distintos, con cambios intermedios en el cliente y el catálogo, da el mismo contenido.

**Acceptance Scenarios**:

1. **Dado** un informe emitido, **cuando** cualquier usuario, incluso un administrador, busca editarlo o borrarlo, **entonces** no existe la acción y un intento directo se rechaza sin cambios.
2. **Dado** un informe emitido, **cuando** se borra o desactiva el cliente, la muestra o el estudio asociados, **entonces** el sistema no lo permite mientras exista el informe.
3. **Dado** un informe emitido, **cuando** se exporta varias veces a lo largo del tiempo, **entonces** el contenido de datos es siempre el mismo.

---

### Edge Cases

- Informe de un estudio cuyo cliente cambió de nombre después de emitir: el listado y el documento muestran los datos guardados en el informe; la búsqueda por cliente lo encuentra por los datos guardados.
- Búsqueda por número con o sin el prefijo «INF-» y con o sin ceros a la izquierda: encuentra el mismo informe.
- Firma dibujada con un solo punto o un trazo mínimo: se acepta si el recuadro no está vacío; la responsabilidad de que sea legible es del usuario.
- Firma demasiado grande o en un formato no válido (envío manipulado): se rechaza sin cambiar la firma guardada.
- Usuario que pierde el permiso «Puede emitir informes»: su firma queda guardada y los informes que emitió siguen mostrándola; no puede emitir ni abrir «Mi firma».
- Datos opcionales vacíos en el informe: se muestran como «—», como en la US 7.2.
- Informe con logo de ejemplo de AquaLab (US 7.2): el PDF lo incluye igual.
- Informe que no existe o número inexistente en la dirección: se muestra «no encontrado», sin errores.
- Sin informes emitidos todavía: el listado indica que aún no hay informes.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema MUST ofrecer, desde el menú principal, el listado «Informes emitidos» a cualquier empleado con sesión.
- **FR-002**: El listado MUST mostrar, por informe, número, fecha de emisión, cliente, N° PI, número y tipo de estudio y quién lo emitió, ordenado del más reciente al más antiguo y paginado.
- **FR-003**: El listado MUST permitir buscar por número de informe (con o sin «INF-» y ceros a la izquierda), por nombre, razón social o número de documento del cliente y por N° PI, usando los datos guardados en el informe.
- **FR-004**: El listado MUST permitir filtrar por fecha de emisión desde y/o hasta, ambos extremos inclusive, combinable con la búsqueda; una fecha inválida o un rango invertido MUST informarse como error.
- **FR-005**: Desde el listado MUST poder abrirse cada informe emitido, que se muestra a partir de la copia guardada (US 7.2), con las acciones «Descargar PDF» e «Imprimir».
- **FR-006**: «Descargar PDF» MUST entregar un archivo PDF en hoja A4, generado por el sistema a partir de la copia guardada del informe, con el número del informe en el nombre del archivo.
- **FR-007**: «Imprimir» MUST abrir la impresión del navegador con el documento preparado para hoja A4, mostrando solo el informe (sin menú, botones ni avisos de la pantalla).
- **FR-008**: El PDF y la impresión MUST reproducir los mismos datos que el informe en pantalla, incluyendo el membrete institucional (nombre, dirección, matrícula, logo), la firma, el nombre y la matrícula del emisor, la fecha y el número del informe.
- **FR-009**: En informes de más de una hoja, cada hoja MUST llevar el número del informe y el número de página, y las filas de pruebas MUST NOT partirse entre hojas.
- **FR-010**: Un informe sin firma guardada (emitido antes de esta historia) MUST exportarse e imprimirse con la leyenda «Sin firma registrada» en el lugar de la firma.
- **FR-011**: El sistema MUST ofrecer la pantalla «Mi firma» solo a usuarios con el permiso «Puede emitir informes», donde dibujan su firma con el mouse o el dedo y cargan su matrícula; MUST permitir borrar el trazo antes de guardar y reemplazar la firma más adelante.
- **FR-012**: «Mi firma» MUST rechazar el guardado con la firma vacía, sin matrícula o con una imagen inválida o mayor que el tamaño máximo, sin cambiar lo guardado.
- **FR-013**: La firma MUST guardarse en el sistema como una imagen de tamaño reducido, asociada al usuario, una por usuario.
- **FR-014**: La emisión de la US 7.2 MUST exigir, además del permiso, que el usuario tenga firma y matrícula cargadas; si no, la vista previa MUST mostrar el aviso con el enlace a «Mi firma» en lugar de «Emitir informe» y la emisión MUST rechazarse con ese motivo sin cambios.
- **FR-015**: Al emitir, el informe MUST guardar en su copia la firma, el nombre completo y la matrícula de quien emite; cambios posteriores de la firma, la matrícula o el nombre MUST NOT modificar informes ya emitidos.
- **FR-016**: La vista previa de la US 7.2 MUST mostrar la firma con la que saldrá el informe.
- **FR-017**: Un informe emitido MUST NOT poder editarse ni borrarse por ninguna vía, incluida la administración; el estudio, la muestra y el cliente asociados MUST NOT poder borrarse mientras exista el informe.
- **FR-018**: Consultar, exportar o imprimir un informe MUST NOT modificar el informe, el estudio ni ningún otro dato.

### Key Entities *(include if feature involves data)*

- **Informe** (US 7.2): Se consulta, busca y exporta siempre desde su copia guardada. Esta historia agrega a esa copia la firma, el nombre y la matrícula de quien lo emite. No se edita ni se borra.
- **Firma profesional**: Imagen reducida de la firma manuscrita de un usuario con permiso de emitir, junto con su matrícula profesional. Una por usuario; se puede reemplazar sin afectar informes emitidos.
- **Datos institucionales del laboratorio** (US 7.2): Forman el membrete del documento exportado.
- **Usuario con «Puede emitir informes»** (US 7.2, grupo «Bioquímicos»): Carga su firma y es el único que puede emitir.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Un empleado encuentra un informe emitido por número, cliente o N° PI y lo descarga en PDF en menos de 30 segundos.
- **SC-002**: El 100% de los PDF e impresiones muestran exactamente los mismos datos que el informe emitido en pantalla.
- **SC-003**: El 100% de los informes emitidos después de esta historia llevan firma, nombre y matrícula de quien los emitió.
- **SC-004**: Ningún informe emitido cambia su contenido después de editar el cliente, el catálogo, los datos institucionales o la firma del emisor.
- **SC-005**: El 100% de los intentos de editar o borrar un informe emitido, o de emitir sin firma cargada, terminan sin cambios.
- **SC-006**: Un bioquímico carga su firma y matrícula en menos de 1 minuto.

## Assumptions

- **Trazabilidad**: US 7.3 – Consultar y exportar informe. Jira: SCRUM-59.
- **Dependencias**: Se apoya en la US 7.2 (informe con número, copia guardada, datos institucionales, permiso «Puede emitir informes» del grupo «Bioquímicos», PR #35, ya en `main`).
- **Generación de PDF**: La constitución ya prevé WeasyPrint para los informes en PDF; su incorporación (dependencia y librerías del sistema) se justifica en el plan.
- **Firma sin librerías**: El dibujo de la firma se resuelve en la página sin componentes de terceros.
- **Matrícula**: Texto libre corto (ej. «MP 1234»); no se valida contra un registro externo.
- **Nombre del emisor**: Se usa el nombre y apellido del usuario; si no los tiene cargados, el nombre de usuario.
- **Búsqueda por cliente**: Usa los datos del cliente guardados en el informe, para encontrar un informe por cómo salió aunque el cliente se haya editado después.
- **Ver informe**: La pantalla del informe emitido de la US 7.2 es la que se abre desde el listado; se le agregan las acciones de exportar.
- **Interfaz**: Pantallas con el diseño de SCRUM-67 y los componentes de `templates/ui/`; el documento reutiliza el diseño del informe de la US 7.2.
- **Datos académicos**: AquaLab es un proyecto FIUBA; los datos de desarrollo y demostración son ficticios (DEMO).
- **Alcance excluido**: Envío por correo (SCRUM-39); anular o reemitir un informe; firma digital con certificado o validez legal; conclusión asistida (US 7.4); firma de más de un profesional por informe.
