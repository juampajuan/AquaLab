# Feature Specification: Precargar el catálogo de pruebas de agua

**Feature Branch**: `014-precargar-catalogo-pruebas`

**Created**: 2026-10-31

**Status**: Draft

**Input**: User description: "SCRUM-64 – Precargar las pruebas definidas por el científico. Como laboratorio queremos tener cargado en AquaLab el catálogo real de pruebas de agua, con los datos que necesitan las US de mediciones y resultados (épica 6), para dejar de depender de datos demo. Datos: pruebas/datos/catalogo_pruebas_agua.csv (90 pruebas) y pruebas/datos/limites_vertido.csv (18 límites por tipo de vertido), filtrados y sin datos personales. Alcance: atributos completos de cada prueba (límites como texto), límites por tipo de vertido en una entidad aparte, comando de importación repetible que actualiza por código y no borra pruebas usadas, y pruebas visibles en el admin (ver, buscar, agregar; código y nombre no editables si la prueba ya se usó). Fuera de alcance: curvas de calibración, mediciones, cálculo de resultados, evaluación de fórmulas y validación contra límites."

## Clarifications

### Session 2026-10-31

- Q: Si el archivo trae otro nombre para una prueba ya usada, ¿qué hace la importación? → A: Conserva el nombre guardado, actualiza el resto e informa la diferencia.
- Q: ¿Qué hace la importación con las pruebas de la base que no figuran en el archivo? → A: No las toca; solo crea y actualiza. Las pruebas demo se quitan aparte.

**Trazabilidad**: SCRUM-64 – Precargar las pruebas definidas por el científico. Prepara los datos que consumirá la épica 6 (mediciones y resultados).

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Importar el catálogo real de pruebas (Priority: P1)

Como laboratorio, quiero cargar en AquaLab el catálogo de pruebas de agua que hoy usa el software del
laboratorio, con todos los datos que necesita el cálculo de resultados, para que los tipos de estudio y
los estudios usen pruebas reales y no datos demo.

**Why this priority**: Sin el catálogo real no hay base para la épica 6 ni para armar tipos de estudio
reales. Es el núcleo de la historia.

**Independent Test**: Sobre una base sin pruebas, correr la importación con los dos archivos y verificar
que quedan exactamente 90 pruebas y 18 límites por tipo de vertido, con los valores de los archivos.

**Acceptance Scenarios**:

1. **Dado** un catálogo sin pruebas, **cuando** se importan los dos archivos, **entonces** quedan 90
   pruebas, cada una con código, nombre, unidad del resultado, unidad de medición, tipo de cálculo,
   fórmula, indicación de si se calcula a partir de otras pruebas, norma, límite mínimo, límite máximo,
   límite de detección y estado activo, con los valores tal como figuran en el archivo.
2. **Dada** una prueba cuyo límite no es numérico (por ejemplo "Ausente", "SOE", "NE" o "Ph-0,2"),
   **cuando** se importa, **entonces** el límite se guarda con exactamente ese texto.
3. **Dado** un límite vacío en el archivo, **cuando** se importa, **entonces** la prueba queda sin ese
   límite (vacío), sin inventar un valor.
4. **Dadas** las 17 pruebas sin tipo de cálculo en el sistema original, **cuando** se importan,
   **entonces** quedan con tipo de cálculo DIRECTO y conservan la observación que indica que debe
   confirmarse con el laboratorio.
5. **Dada** la prueba de Magnesio, **cuando** se importa, **entonces** su fórmula es
   `({DUREZA-T}-{CA}*2.5)*0.243`, es decir, la versión corregida.
6. **Dado** el archivo de límites por tipo de vertido, **cuando** se importa, **entonces** cada límite
   (cloacal o canal) queda asociado a su prueba con su límite mínimo, límite máximo y norma, y una
   prueba tiene como máximo un límite por cada tipo de vertido.
7. **Dada** una fórmula, **cuando** se importa, **entonces** se guarda como texto, sin evaluarla; en ella
   `x` representa el valor medido y `{CODIGO}` el resultado de otra prueba del catálogo.

---

### User Story 2 - Volver a importar sin duplicar ni romper el historial (Priority: P2)

Como laboratorio, quiero poder volver a correr la importación cuando el científico corrija el catálogo,
para mantenerlo actualizado sin duplicar pruebas ni afectar los tipos de estudio y estudios que ya las
usan.

**Why this priority**: El catálogo se va a ajustar (por ejemplo, al confirmar las 17 pruebas DIRECTO);
sin una reimportación segura cada corrección sería una carga manual con riesgo de errores.

**Independent Test**: Importar dos veces seguidas y verificar que la cantidad de pruebas y límites no
cambia; modificar un valor en el archivo, reimportar y verificar que se actualizó la prueba existente.

**Acceptance Scenarios**:

1. **Dado** un catálogo ya importado, **cuando** se vuelve a importar el mismo archivo, **entonces** no se
   crean pruebas ni límites duplicados y los datos quedan iguales.
2. **Dada** una prueba existente cuyo código figura en el archivo con otros datos, **cuando** se
   reimporta, **entonces** se actualiza esa misma prueba (se identifica por código) con los datos del
   archivo.
3. **Dada** una prueba ya usada en un tipo de estudio o en un estudio, **cuando** se reimporta,
   **entonces** la prueba no se borra y sus asignaciones en tipos de estudio y estudios se conservan.
4. **Dada** una prueba usada cuyo nombre en el archivo difiere del guardado, **cuando** se reimporta,
   **entonces** se conserva el nombre guardado, se actualizan los demás datos y la importación informa
   la diferencia (código, nombre guardado y nombre del archivo).
5. **Dada** una prueba de la base que no figura en el archivo, **cuando** se reimporta, **entonces**
   la importación no la modifica, ni la borra ni la desactiva: solo crea y actualiza las pruebas del
   archivo. Las pruebas demo se quitan por fuera de la importación.
6. **Dado** un archivo con un error (columna faltante, código repetido, tipo de cálculo distinto de
   DIRECTO o FORMULA, tipo de vertido distinto de cloacal o canal, o un límite por vertido de un código
   que no existe en el catálogo), **cuando** se importa, **entonces** la importación se rechaza
   completa, se informa qué fila y qué problema hay, y el catálogo queda como estaba.
7. **Dada** una importación exitosa, **cuando** termina, **entonces** informa cuántas pruebas y límites
   se crearon y cuántos se actualizaron.

---

### User Story 3 - Consultar y mantener las pruebas en el admin (Priority: P3)

Como administrador del laboratorio, quiero ver, buscar y agregar pruebas desde el panel de
administración, para revisar el catálogo y hacer altas puntuales sin depender de un desarrollador.

**Why this priority**: Facilita la revisión del catálogo importado, pero la carga principal la resuelve
la importación.

**Independent Test**: Con el catálogo importado, ingresar al admin con un usuario administrador, buscar
una prueba por código o nombre, abrirla, agregar una prueba nueva y verificar que una prueba usada no
permite cambiar código ni nombre.

**Acceptance Scenarios**:

1. **Dado** un administrador con sesión iniciada, **cuando** abre el listado de pruebas, **entonces** ve
   las pruebas con su código, nombre, unidad, tipo de cálculo y estado activo.
2. **Dado** el listado, **cuando** busca por parte del código o del nombre, **entonces** ve solo las
   pruebas que coinciden.
3. **Dado** el listado, **cuando** filtra por tipo de cálculo o por estado activo, **entonces** ve solo
   las pruebas que cumplen el filtro.
4. **Dada** una prueba, **cuando** el administrador la abre, **entonces** ve todos sus datos y sus límites
   por tipo de vertido.
5. **Dado** el formulario de alta, **cuando** completa código y nombre únicos y válidos, **entonces** se
   crea la prueba; si el código ya existe o falta el código o el nombre, se rechaza indicando el error.
6. **Dada** una prueba usada en un tipo de estudio o en un estudio, **cuando** el administrador la abre,
   **entonces** el código y el nombre se muestran pero no se pueden modificar; el resto de los datos sí.
7. **Dada** una prueba no usada, **cuando** el administrador la edita, **entonces** puede modificar
   también el código y el nombre.
8. **Dada** una prueba usada, **cuando** se intenta eliminarla desde el admin, **entonces** se impide la
   eliminación.
9. **Dado** un usuario sin acceso al admin, **cuando** intenta ingresar al listado de pruebas,
   **entonces** no puede verlo ni modificar nada.

### Edge Cases

- Una prueba con tipo FORMULA cuya fórmula está vacía, o una DIRECTO con fórmula: se rechaza en la
  importación y en el admin.
- Una fórmula que referencia un `{CODIGO}` que no existe en el catálogo: se rechaza la importación de
  ese archivo completo. En el archivo actual todas las referencias existen.
- Límites decimales: se conservan tal como vienen (por ejemplo "3.0" no se transforma en "3").
- Espacios al inicio o al final de un código, nombre o valor: se descartan al importar.
- Valores de las columnas "sí/no" distintos de `si` y `no`: se rechaza la importación indicando la fila.
- La columna `observacion` acompaña a la prueba como nota interna; no es parte del cálculo.
- Una prueba demo previa con un código distinto a los del catálogo: la importación no la toca.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Cada prueba DEBE guardar código (único y obligatorio), nombre (obligatorio), unidad del
  resultado, unidad de medición, tipo de cálculo (DIRECTO o FORMULA), fórmula, si se calcula a partir de
  otras pruebas, norma, límite mínimo, límite máximo, límite de detección, si está activa y una
  observación interna.
- **FR-002**: Los límites (mínimo, máximo y de detección, y los de vertido) DEBEN guardarse como texto
  tal como vienen, incluidos valores no numéricos ("Ausente", "Ausencia", "SOE", "NE", "Ph-0,2",
  "Ph+0,2"). Un límite vacío queda vacío.
- **FR-003**: La fórmula DEBE guardarse como texto sin evaluarla. Una prueba FORMULA DEBE tener fórmula
  y una DIRECTO NO DEBE tenerla.
- **FR-004**: El sistema DEBE guardar los límites por tipo de vertido (cloacal y canal) en una entidad
  separada asociada a la prueba, con límite mínimo, límite máximo y norma, y como máximo un límite por
  prueba y tipo de vertido.
- **FR-005**: El sistema DEBE ofrecer un comando que importe el catálogo de pruebas y los límites por
  tipo de vertido desde los dos archivos del repositorio, y que permita indicar otros archivos con el
  mismo formato.
- **FR-006**: La importación DEBE identificar las pruebas por código: crea las que no existen y
  actualiza las existentes. Lo mismo para los límites, identificados por prueba y tipo de vertido.
- **FR-007**: Correr la importación varias veces con los mismos archivos DEBE dejar el mismo resultado,
  sin duplicados.
- **FR-008**: La importación NO DEBE borrar ni desactivar pruebas (usadas o no, figuren o no en el
  archivo) ni alterar las asignaciones de tipos de estudio y estudios.
- **FR-008a**: Si el archivo trae otro nombre para una prueba usada en un tipo de estudio o en un
  estudio, la importación DEBE conservar el nombre guardado, actualizar los demás datos e informar la
  diferencia al terminar.
- **FR-009**: La importación DEBE validar todo el contenido antes de guardar y aplicarse completa o no
  aplicarse: ante cualquier error se informan fila y motivo y el catálogo queda sin cambios.
- **FR-010**: La importación DEBE validar que las referencias `{CODIGO}` de las fórmulas y los códigos
  del archivo de límites existan en el catálogo resultante.
- **FR-011**: Al terminar, la importación DEBE informar cantidades de pruebas y límites creados y
  actualizados.
- **FR-012**: Las pruebas DEBEN estar disponibles en el panel de administración para usuarios con
  acceso: listado con código, nombre, unidad, tipo de cálculo y estado activo; búsqueda por código y
  nombre; filtros por tipo de cálculo y estado activo; detalle con sus límites por tipo de vertido; y
  alta.
- **FR-013**: En el admin, el código y el nombre de una prueba usada en un tipo de estudio o en un
  estudio NO DEBEN poder editarse; los demás datos sí. Una prueba usada NO DEBE poder eliminarse.
- **FR-014**: Las validaciones de FR-001 a FR-004 DEBEN aplicarse igual en la importación y en el
  admin.
- **FR-015**: Las pruebas existentes antes de esta historia (incluidas las demo) DEBEN seguir siendo
  válidas: los nuevos datos son opcionales salvo código, nombre, tipo de cálculo (DIRECTO por defecto) y
  estado activo (activa por defecto).

### Key Entities

- **Prueba**: análisis que el laboratorio realiza sobre una muestra de agua. Atributos: código, nombre,
  unidad del resultado, unidad de medición, tipo de cálculo, fórmula, si se calcula a partir de otras
  pruebas, norma, límites mínimo, máximo y de detección (texto), si está activa y observación. Se usa en
  tipos de estudio y estudios.
- **Límite por tipo de vertido**: límite aplicable a una prueba según el destino del vertido (cloacal o
  canal). Atributos: prueba, tipo de vertido, límite mínimo, límite máximo (texto) y norma.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Tras una importación sobre una base vacía, el catálogo tiene exactamente 90 pruebas y 18
  límites por tipo de vertido, y el 100 % de los valores coincide con los archivos.
- **SC-002**: Tres importaciones consecutivas de los mismos archivos dejan la misma cantidad de pruebas
  y límites que una sola.
- **SC-003**: Después de reimportar, el 100 % de las asignaciones de pruebas en tipos de estudio y
  estudios existentes se conserva.
- **SC-004**: Un archivo con un error deja el catálogo sin ningún cambio y el mensaje permite ubicar la
  fila con problema.
- **SC-005**: Un administrador encuentra cualquier prueba del catálogo por código o nombre en menos de
  30 segundos.
- **SC-006**: Las 17 pruebas asumidas como DIRECTO pueden identificarse en el admin por su observación
  para confirmarlas con el laboratorio.

## Assumptions

- Solo se importan pruebas de agua que se calculan sin curva de calibración; las curvas y sus pruebas
  quedan para el próximo sprint.
- Cargar mediciones, calcular resultados, evaluar fórmulas y comparar contra límites son de la épica 6
  y quedan fuera de alcance.
- El estado activo se guarda y se muestra en el admin; que los formularios de tipos de estudio y de
  estudios dejen de ofrecer pruebas inactivas queda fuera de alcance (en el archivo actual todas están
  activas).
- El acceso al admin y los permisos para ver, agregar o modificar pruebas son los estándar del panel de
  administración; no se crea un rol nuevo.
- Los archivos están en UTF-8 con encabezado y separados por coma, tal como están en
  `pruebas/datos/`. No contienen datos personales.
- Los límites por tipo de vertido de una prueba que ya no figuran en el archivo se conservan; la
  importación solo crea y actualiza.
- Una prueba "usada" es una prueba asignada a al menos un tipo de estudio o a al menos un estudio.
- Correr la importación es una tarea de quien administra la instalación, no de los usuarios del
  laboratorio desde la interfaz.
