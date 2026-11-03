# Feature Specification: Ayuda en formularios

**Feature Branch**: `024-ayuda-formularios`

**Created**: 2026-11-03

**Status**: Borrador

**Input**: User description: "US 9.1 (SCRUM-68) – Ayuda en formularios (tooltips). Como empleado del laboratorio quiero ver una ayuda breve junto a los campos de los formularios para entender qué cargar sin tener que preguntar. Criterios: (1) Los campos que lo necesitan muestran un ícono de ayuda junto a la etiqueta; al pasar el mouse, enfocarlo con teclado o tocarlo, aparece un texto breve. (2) Funciona con mouse, teclado (Tab/Escape) y pantallas táctiles, y los lectores de pantalla leen la ayuda. (3) Se implementa una sola vez en el partial de campos (templates/ui/campo.html) a partir del help_text de Django, sin librerías externas. (4) Se cargan textos de ayuda en los formularios existentes donde el campo no es obvio (clientes, muestras, estudios, tipos de estudio, mediciones, mi firma). Fuera de alcance: ayuda en el admin de Django y tutoriales guiados."

## Clarifications

### Session 2026-11-03

- Q: ¿Todo texto de ayuda pasa a tooltip, o las instrucciones para completar bien el campo siguen
  visibles? → A: El tooltip explica qué significa el campo; las instrucciones necesarias para
  completarlo bien siguen como texto visible debajo del campo. Los requisitos de contraseña del
  registro y la indicación de Ctrl/Cmd en tipos de estudio quedan visibles como hoy; solo el texto
  del nombre de la muestra pasa a tooltip.
- Q: ¿Cómo se explica en la tabla de carga y corrección de mediciones la forma de escribir el
  valor? → A: Las dos cosas: el aviso de información visible arriba de la tabla suma el formato
  (coma o punto decimal, sin miles; «Ausente»/«Presente» en las pruebas A/P) y la columna
  «Medición» lleva un tooltip que explica qué es la medición (el valor leído, antes del cálculo).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ver la ayuda de un campo (Priority: P1)

Como empleado del laboratorio, al completar un formulario veo un ícono de ayuda junto a la
etiqueta de los campos que pueden generar dudas. Al pasar el mouse sobre el ícono, o al llegar a
él con Tab, aparece un texto breve que explica qué cargar; al irme del ícono o apretar Escape, el
texto se oculta. En una pantalla táctil, tocar el ícono muestra la ayuda y tocar afuera la cierra.

**Why this priority**: Es el comportamiento central de la historia: sin el componente de ayuda
no hay dónde mostrar los textos. Se puede probar con un solo campo que tenga ayuda.

**Independent Test**: En un formulario con un campo con ayuda y otro sin ayuda, verificar que
solo el primero muestra el ícono, que la ayuda aparece con mouse, con teclado y con un toque, que
se cierra con Escape, al salir y al tocar afuera, y que un lector de pantalla la anuncia al
llegar al campo.

**Acceptance Scenarios**:

1. **Dado** un campo con texto de ayuda, **cuando** se muestra el formulario, **entonces** junto
   a su etiqueta aparece un ícono de ayuda y el texto queda oculto.
2. **Dado** un campo sin texto de ayuda, **cuando** se muestra el formulario, **entonces** no
   aparece ningún ícono de ayuda.
3. **Dado** el ícono de ayuda, **cuando** el empleado pasa el mouse sobre él, **entonces**
   aparece el texto de ayuda; **cuando** retira el mouse, **entonces** se oculta.
4. **Dado** el formulario, **cuando** el empleado llega al ícono con Tab, **entonces** aparece el
   texto de ayuda; **cuando** sigue con Tab o aprieta Escape, **entonces** se oculta y el foco no
   se pierde.
5. **Dada** una pantalla táctil, **cuando** el empleado toca el ícono, **entonces** aparece el
   texto; **cuando** lo vuelve a tocar o toca fuera de la ayuda, **entonces** se oculta.
6. **Dado** un lector de pantalla, **cuando** el foco llega al control del campo, **entonces** el
   lector anuncia la etiqueta y también el texto de ayuda, aunque la ayuda esté oculta a la vista.
7. **Dada** una ayuda abierta, **cuando** se abre la de otro campo, **entonces** la primera se
   cierra: nunca hay dos ayudas visibles a la vez.
8. **Dado** un campo con error y con ayuda, **cuando** se muestra el formulario, **entonces** el
   mensaje de error sigue visible junto al campo como hasta ahora y la ayuda sigue disponible en
   el ícono.

---

### User Story 2 - Textos de ayuda en los formularios existentes (Priority: P1)

Como empleado del laboratorio, en los formularios que uso todos los días (registrar y editar
cliente, registrar muestra, crear estudio, agregar prueba, tipos de estudio, cargar y corregir
mediciones, mi firma) encuentro ayuda en los campos que no se explican solos: qué formato lleva
el documento, qué es el origen y cuándo crear uno nuevo, qué fecha va en muestreo y cuál en
ingreso, qué cambia el tipo de vertido, cómo se escriben los decimales, qué es la matrícula.

**Why this priority**: Es el valor concreto para el usuario: el componente sin textos no ayuda a
nadie. Comparte prioridad con la US 1 porque ninguna de las dos sirve sola.

**Independent Test**: Recorrer cada formulario de la lista y verificar que los campos indicados
en la tabla de textos de ayuda (FR-010) muestran el ícono con su texto y que los campos obvios no
lo tienen.

**Acceptance Scenarios**:

1. **Dado** cada formulario de la lista, **cuando** se abre, **entonces** los campos indicados en
   FR-010 muestran el ícono de ayuda con un texto breve en español.
2. **Dados** campos de significado evidente (por ejemplo, nombre, correo o teléfono), **cuando**
   se muestra el formulario, **entonces** no llevan ícono de ayuda.
3. **Dado** el registro de muestra, **cuando** se muestra el campo «Nombre de la muestra»,
   **entonces** su ayuda actual (cómo se numera si se deja vacío) pasa a verse con el ícono, igual
   que el resto.
4. **Dado** el formulario de tipos de estudio, **cuando** se muestra el campo de pruebas,
   **entonces** el tooltip explica qué son las pruebas por defecto y la indicación actual de cómo
   elegir varias pruebas (Ctrl o Cmd) sigue visible debajo del campo, como hoy.
5. **Dado** el registro de usuario, **cuando** se muestra el campo de contraseña, **entonces** los
   requisitos de contraseña siguen visibles debajo del campo, como hoy, y no pasan a tooltip.
6. **Dada** la carga o corrección de mediciones, **cuando** se muestra la tabla, **entonces** el
   aviso de información visible arriba de la tabla indica cómo escribir el valor (coma o punto
   decimal, sin separador de miles; «Ausente» o «Presente» en las pruebas A/P), y la columna
   «Medición» tiene un ícono de ayuda que explica qué es la medición: el valor leído en el
   análisis, a partir del cual se calcula el resultado.

---

### Edge Cases

- **Ayuda cerca del borde de la pantalla**: el texto se ve completo, sin cortarse ni generar
  desplazamiento horizontal de la página.
- **Ayuda abierta y envío del formulario o cambio de campo**: abrir o cerrar la ayuda no modifica
  el valor del campo, no envía el formulario y no mueve el foco fuera del ícono.
- **Sin JavaScript**: la ayuda sigue siendo accesible (al menos con mouse y teclado sobre el
  ícono, y siempre para el lector de pantalla); el formulario funciona igual.
- **Texto de ayuda largo**: se muestra completo dentro de la ayuda, con saltos de línea si hace
  falta, sin desbordar la pantalla.
- **Campo con significado e instrucción**: muestra las dos cosas a la vez, el ícono con el
  significado junto a la etiqueta y la instrucción visible debajo del campo, sin repetir el mismo
  texto en los dos lugares.
- **Campos de opciones** (botones segmentados, como el tipo de documento): el ícono va junto al
  título del grupo y la ayuda se asocia al grupo.
- **Campos sin etiqueta visible**: no muestran ícono; su ayuda, si la tuvieran, igual se asocia
  al control para el lector de pantalla.
- **Clic en la etiqueta**: tocar o hacer clic en la etiqueta sigue llevando el foco al control,
  como hoy; el ícono es un elemento aparte.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Todo campo de formulario de las pantallas de AquaLab que tenga texto de ayuda DEBE
  mostrar un ícono de ayuda junto a su etiqueta; los campos sin texto de ayuda NO DEBEN mostrarlo.
- **FR-002**: El texto de ayuda DEBE estar oculto por defecto y aparecer al pasar el mouse sobre
  el ícono, al enfocarlo con el teclado o al tocarlo en una pantalla táctil.
- **FR-003**: La ayuda DEBE ocultarse al retirar el mouse, al quitar el foco, al apretar Escape,
  al volver a tocar el ícono o al tocar fuera de la ayuda.
- **FR-004**: El ícono DEBE poder alcanzarse con Tab, tener un nombre accesible (por ejemplo,
  «Ayuda: <etiqueta del campo>») y no ser un control que envíe el formulario.
- **FR-005**: El texto de ayuda DEBE estar asociado al control del campo de forma que un lector de
  pantalla lo anuncie al llegar al control, esté o no visible, junto con los mensajes de error que
  el campo ya anuncia.
- **FR-006**: Solo puede haber una ayuda visible a la vez en la pantalla.
- **FR-007**: El comportamiento de la ayuda DEBE definirse una única vez como componente
  reutilizable del sistema visual, incorporado al parcial de campos de formulario, de modo que
  toda pantalla que use ese parcial lo obtenga sin código propio. Los lugares que no usan el
  parcial (los encabezados de la tabla de mediciones) DEBEN reutilizar el mismo componente.
  El tooltip explica qué significa el campo; las instrucciones necesarias para completarlo bien
  (como los requisitos de contraseña del registro o cómo elegir varias pruebas con Ctrl/Cmd) NO
  pasan al tooltip: siguen como texto visible debajo del campo, con el mismo estilo de hoy, y
  también se asocian al control para el lector de pantalla.
- **FR-008**: El componente NO DEBE depender de librerías externas.
- **FR-009**: La ayuda DEBE seguir el sistema visual de AquaLab (colores, tipografía, ícono) y
  verse completa en el ancho de pantalla de escritorio y en pantallas táctiles, sin desplazamiento
  horizontal.
- **FR-010**: Se DEBEN cargar textos de ayuda breves (una o dos oraciones, en español) al menos en
  estos campos:

  | Formulario | Campo | Qué explica la ayuda |
  |---|---|---|
  | Registrar y editar cliente | Razón social | Cuándo usarla en lugar del nombre (empresas u organismos). |
  | Registrar y editar cliente | Tipo de documento | Diferencia entre DNI y CUIT y cuándo corresponde cada uno. |
  | Registrar y editar cliente | Número de documento | Que se puede escribir con o sin puntos y guiones (se guardan solo los números). |
  | Registrar y editar cliente | Correo electrónico | Que se usa para enviar los informes al cliente. |
  | Registrar muestra | Origen | Qué es el origen (la fuente de agua) y que permite comparar resultados históricos. |
  | Registrar muestra | Origen nuevo | Cuándo crear uno y que no se duplica si ya existe con otro uso de mayúsculas. |
  | Registrar muestra | Fecha de muestreo | Que es la fecha en que se tomó la muestra. |
  | Registrar muestra | Fecha de ingreso | Que es la fecha en que llegó al laboratorio. |
  | Registrar muestra | Sitio de extracción | Qué punto concreto se indica (canilla, pozo, cámara). |
  | Registrar muestra | Tipo de vertido | Que define qué límites se usan para evaluar los resultados. |
  | Registrar muestra | Nombre de la muestra | La ayuda actual: cómo se numera si se deja vacío. |
  | Registrar muestra | Responsable del muestreo | Quién tomó la muestra. |
  | Crear estudio | Tipo de estudio | Que define las pruebas con que nace el estudio y que después se pueden agregar o quitar. |
  | Agregar prueba | Prueba | Que solo se listan las pruebas que el estudio todavía no tiene. |
  | Tipos de estudio | Pruebas | Que son las pruebas por defecto de los estudios nuevos (la indicación de Ctrl/Cmd sigue visible). |
  | Cargar y corregir mediciones | Medición (columna) | Que es el valor leído en el análisis, a partir del cual se calcula el resultado. El formato (coma o punto, sin miles; Ausente/Presente) va visible en el aviso de arriba de la tabla. |
  | Mi firma | Matrícula | Qué matrícula profesional va y que se imprime en los informes. |
  | Mi firma | Firma | Cómo dibujarla y que se copia en cada informe que se emita. |

- **FR-011**: Los textos de ayuda NO DEBEN repetir la etiqueta ni explicar lo obvio; DEBEN usar
  los términos del Glosario del proyecto.
- **FR-012**: Los mensajes de error de los campos DEBEN seguir mostrándose visibles junto al campo
  como hasta ahora; la ayuda no los reemplaza ni los oculta.
- **FR-013**: Las pantallas del administrador de Django NO cambian.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: El 100 % de los campos listados en FR-010 muestran ayuda, y ningún campo sin texto
  de ayuda muestra el ícono.
- **SC-002**: La ayuda de cualquier campo se puede abrir y cerrar usando solo el teclado, solo el
  mouse y solo el tacto, en todos los formularios incluidos.
- **SC-003**: Con un lector de pantalla, la ayuda de cada campo de FR-010 se anuncia al llegar al
  campo, sin tener que abrirla.
- **SC-004**: Un empleado que no conoce el formulario de registro de muestra lo completa sin
  consultar a otra persona por el significado de los campos.
- **SC-005**: Ninguna pantalla con formularios necesita código propio para mostrar la ayuda: se
  obtiene solo con cargar el texto del campo.

## Assumptions

- De las ayudas que hoy se ven como texto debajo del campo, solo la del nombre de la muestra pasa
  a tooltip (explica qué significa dejarlo vacío). Los requisitos de contraseña del registro de
  usuario y la indicación de Ctrl/Cmd en tipos de estudio son instrucciones para completar bien el
  campo y quedan visibles como hoy.
- Los formularios de búsqueda y filtros (buscar cliente, buscar estudio, informes emitidos,
  historial) y el inicio de sesión no necesitan textos nuevos, pero obtienen el componente si en
  el futuro se les carga una ayuda.
- Los textos de FR-010 son una primera versión del equipo; el laboratorio puede pedir ajustes de
  redacción sin que cambie el alcance.
- La interfaz sigue orientada a escritorio; el soporte táctil cubre tablets o pantallas táctiles
  del laboratorio, sin un diseño móvil propio.
- Depende del parcial de campos y del sistema visual de la spec 013 y de los formularios de las
  US ya implementadas (3.1, 3.2, 4.1, 5.1, 5.3, 5.5, 6.1, 6.3, 7.3).
- Fuera de alcance: ayuda en el administrador de Django y tutoriales o recorridos guiados.
