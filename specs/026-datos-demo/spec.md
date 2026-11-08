# Feature Specification: Datos de demo

**Feature Branch**: `026-datos-demo`

**Created**: 2026-11-08

**Status**: Aprobada (2026-11-08)

**Input**: User description: "SCRUM-78 – Datos de demo (tarea técnica). Como equipo queremos un comando que cargue datos de ejemplo realistas para poder mostrar y probar el dashboard. Criterios de aceptación: (1) El comando cargar_demo carga clientes ficticios con varios orígenes y muestras de los últimos 6 meses por origen, con estudios en todos los estados e informes emitidos. (2) Incluye resultados fuera de norma y al menos un desvío claro en el historial de algún origen (un valor que se dispara). (3) Crea un técnico y un bioquímico con firma, y usa el catálogo real de pruebas. (4) Solo corre en desarrollo. Reemplaza al viejo cargar_demo_us51. Orden sugerido: datos de demo → 8.3 → 8.1 → 8.2 → 8.4 → 8.5. Los datos van primero porque sin ellos no hay nada que mostrar."

## Clarifications

### Session 2026-11-08

- Q: ¿Cómo se ven los nombres de los clientes y orígenes demo en las pantallas? → A: Nombres realistas y ficticios (ej. «Lácteos del Sur S.A.», «Pozo 2»), sin prefijo visible; lo demo se reconoce por el correo `@demo.aqualab` y por documentos de un rango inventado.
- Q: ¿Los valores de la demo tienen que salir iguales cada vez que se carga en una base nueva? → A: Sí. Mismas mediciones, mismos fuera de norma y mismo desvío en cada carga; las fechas son relativas al día de ejecución.
- Q: ¿Qué tipos de estudio usa la demo? → A: La demo crea 3 tipos realistas con pruebas del catálogo real («Físico-químico básico», «Bacteriológico», «Vuelco a colectora»); si ya existe uno con ese nombre, lo reutiliza sin modificarlo.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Cargar una demo completa con un comando (Priority: P1)

Como integrante del equipo, en mi entorno de desarrollo con la base vacía ejecuto `cargar_demo` y obtengo un laboratorio con seis meses de actividad: clientes ficticios con varios orígenes, una muestra por mes y por origen, estudios en todos los estados, informes emitidos, resultados fuera de norma y un desvío claro en el historial de un origen. Así puedo mostrar y probar el dashboard y las pantallas existentes sin cargar nada a mano.

**Why this priority**: Es la historia: sin datos no hay nada que mostrar en el dashboard (SCRUM-75, 76, 60, 61, 77), y cargarlos a mano lleva horas.

**Independent Test**: En una base de desarrollo recién migrada, ejecutar el comando y verificar que existen los clientes, orígenes y muestras de los últimos 6 meses, que hay estudios en cada uno de los cuatro estados, informes emitidos con firma, al menos un resultado fuera de norma y una serie de resultados validados de un origen donde el último valor se dispara.

**Acceptance Scenarios**:

1. **Dada** una base de desarrollo migrada y sin datos de demo, **cuando** se ejecuta `cargar_demo`, **entonces** se crean al menos 3 clientes ficticios, cada uno con 2 o 3 orígenes, y por cada origen una muestra por mes de los últimos 6 meses (incluido el actual), con fechas de muestreo e ingreso dentro de ese mes.
2. **Dada** la demo cargada, **cuando** se consultan los estudios, **entonces** hay estudios en Pendiente de análisis, En proceso, Finalizado e Informe generado, y la mayoría de los meses anteriores al actual tienen sus estudios con informe emitido.
3. **Dada** la demo cargada, **cuando** se abre un informe emitido, **entonces** muestra los datos del estudio, quién lo emitió con su firma y matrícula, y se puede exportar como los demás.
4. **Dada** la demo cargada, **cuando** se revisan los resultados, **entonces** hay resultados fuera de norma en varios orígenes y meses.
5. **Dada** la demo cargada, **cuando** se mira el historial de resultados validados de una prueba en un origen elegido para el desvío, **entonces** los meses anteriores son estables y el último resultado validado es al menos el triple del promedio de los tres anteriores.
6. **Dada** la demo cargada, **cuando** se mira el estudio del mes actual de ese mismo origen, **entonces** tiene un resultado calculado y sin validar que también se aleja claramente del historial, para mostrar el aviso antes de validar.
7. **Dada** la demo cargada, **cuando** termina el comando, **entonces** informa un resumen de lo creado (clientes, orígenes, muestras, estudios por estado, informes) y los usuarios demo con su contraseña.

---

### User Story 2 - Usuarios demo para cada rol (Priority: P1)

Como integrante del equipo, quiero un técnico y un bioquímico de demo para entrar con cada rol y ver lo que cada uno tiene pendiente, sin crear cuentas a mano.

**Why this priority**: El inicio con pendientes (SCRUM-77) y los permisos del dashboard (SCRUM-75) dependen del rol; sin usuarios de cada rol no se pueden mostrar.

**Independent Test**: Después de cargar la demo, iniciar sesión con cada usuario demo y verificar que el técnico no puede validar ni emitir, que el bioquímico sí, que el bioquímico tiene firma registrada y que existen estudios pendientes para cada uno.

**Acceptance Scenarios**:

1. **Dada** la demo cargada, **cuando** se inicia sesión con el técnico demo, **entonces** entra como usuario común (sin el grupo Bioquímicos ni Administradores) y hay estudios con mediciones por cargar.
2. **Dada** la demo cargada, **cuando** se inicia sesión con el bioquímico demo, **entonces** pertenece a Bioquímicos y a Administradores, tiene firma y matrícula registradas, y hay resultados por validar y estudios listos para emitir informe.
3. **Dados** los informes emitidos de la demo, **cuando** se consultan, **entonces** los emitió el bioquímico demo y las mediciones las cargó el técnico demo.

---

### User Story 3 - Solo en desarrollo y sin duplicar (Priority: P2)

Como equipo, quiero que el comando nunca toque una base que no sea de desarrollo y que no duplique la demo si se ejecuta dos veces.

**Why this priority**: Protege los datos reales y evita demos inconsistentes; no aporta datos nuevos, por eso P2.

**Independent Test**: Ejecutar el comando fuera del entorno de desarrollo y verificar que se rechaza sin cambios; ejecutarlo dos veces en desarrollo y verificar que la segunda no crea nada y lo informa.

**Acceptance Scenarios**:

1. **Dado** un entorno que no está marcado como desarrollo (o sin modo de depuración), **cuando** se ejecuta el comando, **entonces** se rechaza con un mensaje que lo explica y no cambia nada.
2. **Dada** una base que ya tiene la demo, **cuando** se vuelve a ejecutar, **entonces** no crea nada e informa que la demo ya está cargada y cómo empezar de cero.
3. **Dada** una base sin el catálogo de pruebas, **cuando** se ejecuta el comando, **entonces** importa primero el catálogo real y luego carga la demo.
4. **Dada** una falla en medio de la carga, **cuando** termina el comando, **entonces** no queda ningún dato de demo a medias.
5. **Dado** el repositorio, **cuando** se busca el comando anterior `cargar_demo_us51`, **entonces** ya no existe y la documentación indica `cargar_demo`.

---

### Edge Cases

- Base con datos propios cargados a mano (no de demo): la demo se suma sin modificarlos; los números de muestra e informe continúan desde los existentes.
- Mes actual recién empezado: las fechas de la demo nunca quedan en el futuro.
- Ejecutado justo después de otra ejecución que falló: como no quedó nada a medias, se carga completa.
- Un correo de usuario demo ya existe sin ser de la demo: se rechaza sin cambios e indica el conflicto (no se toma ni se modifica una cuenta ajena).
- Tipo de estudio con el mismo nombre que uno demo pero con otras pruebas: se rechaza sin cambios e indica el conflicto (no se modifica el tipo existente ni se crea un duplicado).
- Catálogo modificado a mano: si ya hay catálogo cargado no se reimporta, para no pisar cambios.
- Pruebas Ausente/Presente (ej. E. coli): reciben valores de Ausente o Presente, no números arbitrarios.
- Resultados por debajo del límite de detección: al menos uno, para que se vea «< LD» en informes.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema MUST ofrecer un comando `cargar_demo` que cargue, en una sola operación, todos los datos de demo descritos en esta especificación.
- **FR-001a**: Los valores cargados (clientes, orígenes, mediciones, fuera de norma y desvío) MUST ser los mismos en cada carga sobre una base nueva; solo las fechas cambian, calculadas a partir del día de ejecución.
- **FR-002**: El comando MUST ejecutarse solo en un entorno marcado explícitamente como desarrollo y con modo de depuración; en cualquier otro caso MUST rechazarse sin cambios.
- **FR-003**: El comando MUST crear al menos 3 clientes ficticios de distinto tipo (empresa, organismo público y particular), cada uno con 2 o 3 orígenes. Los nombres de clientes y orígenes MUST ser realistas y sin prefijo visible; los clientes demo MUST reconocerse por su correo en el dominio `demo.aqualab` y por documentos de un rango ficticio.
- **FR-004**: Por cada origen MUST crearse una muestra por mes de los últimos 6 meses, incluido el actual, con fechas de muestreo e ingreso dentro del mes y nunca futuras.
- **FR-005**: Cada muestra MUST tener al menos un estudio de uno de 3 tipos de estudio demo armados con pruebas del catálogo real: «Físico-químico básico», «Bacteriológico» y «Vuelco a colectora». Si ya existe un tipo con ese nombre y las mismas pruebas, MUST reutilizarse sin modificarlo; si existe con otras pruebas, el comando MUST rechazar la carga sin cambios e indicar el conflicto.
- **FR-006**: La demo MUST incluir estudios en los cuatro estados (Pendiente de análisis, En proceso, Finalizado, Informe generado). Los meses anteriores al actual MUST quedar mayormente con informe emitido; los del mes actual, repartidos entre los demás estados.
- **FR-007**: Los estudios MUST seguir las mismas reglas que si los hubiera cargado una persona: numeración de muestras e informes sin huecos, resultados calculados, validaciones guardadas e informes con la copia de sus datos.
- **FR-008**: Las fechas de cada paso (ingreso, creación del estudio, carga de mediciones, validación y emisión) MUST quedar repartidas en el pasado de forma coherente (cada paso posterior al anterior), con tiempos de respuesta variables de pocos días a pocas semanas, para que los indicadores por período y por semana tengan valores distintos.
- **FR-009**: La demo MUST incluir al menos un estudio estancado (sin avanzar hace más de 7 días) y al menos un estudio Finalizado sin informe emitido.
- **FR-010**: La demo MUST incluir resultados fuera de norma en varios orígenes y meses, al menos un resultado por debajo del límite de detección y pruebas Ausente/Presente con ambos valores.
- **FR-011**: En al menos un origen y una prueba, los resultados validados de los meses anteriores MUST ser estables, y el último resultado validado MUST ser al menos el triple del promedio de los tres anteriores. El estudio del mes actual de ese origen MUST tener un resultado de esa prueba calculado, sin validar y también alejado del historial.
- **FR-012**: El comando MUST crear un técnico demo (usuario común) y un bioquímico demo (grupos Bioquímicos y Administradores, con firma y matrícula de ejemplo), activos y con una contraseña conocida de desarrollo. Las mediciones MUST figurar cargadas por el técnico y las validaciones y emisiones, por el bioquímico.
- **FR-013**: Si el catálogo de pruebas está vacío, el comando MUST importar el catálogo real antes de cargar; si ya hay catálogo, MUST NOT reimportarlo.
- **FR-014**: Si la base ya contiene la demo, el comando MUST NOT crear nada e MUST informar que ya está cargada y cómo empezar de cero.
- **FR-015**: Si un correo de usuario demo ya existe y no pertenece a la demo, el comando MUST rechazar la carga sin cambios.
- **FR-016**: La carga MUST ser atómica: ante cualquier falla no MUST quedar ningún dato de demo.
- **FR-017**: Al terminar, el comando MUST imprimir un resumen con las cantidades creadas y los usuarios demo con su contraseña.
- **FR-018**: El comando anterior `cargar_demo_us51` y sus pruebas MUST eliminarse, y la documentación del proyecto MUST indicar cómo usar `cargar_demo`.
- **FR-019**: La demo MUST NOT modificar datos existentes que no sean de la demo.

### Key Entities *(include if feature involves data)*

- **Cliente demo**: Cliente ficticio con nombre realista; se reconoce por su correo `@demo.aqualab` y su documento de rango ficticio. Tiene 2 o 3 orígenes.
- **Origen**: Punto de extracción del cliente (pozo, tanque, salida a canal…); agrupa la serie mensual de muestras sobre la que se ve el historial y el desvío.
- **Muestra / Estudio / Medición / Resultado / Validación / Informe** (US 4.1 a 7.3): Se crean con las mismas reglas de la aplicación, con fechas repartidas en los últimos 6 meses.
- **Tipo de estudio demo**: «Físico-químico básico», «Bacteriológico» y «Vuelco a colectora», con pruebas del catálogo real; se reutilizan si ya existen iguales.
- **Usuario demo**: Técnico (usuario común) y bioquímico (Bioquímicos y Administradores, con firma profesional).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Desde una base de desarrollo vacía y migrada, una persona del equipo tiene la demo completa con un solo comando en menos de 1 minuto.
- **SC-002**: Cada uno de los últimos 6 meses tiene muestras ingresadas en todos los orígenes demo, y al menos 5 de esos meses tienen informes emitidos.
- **SC-003**: Los cuatro estados de estudio tienen al menos 2 estudios cada uno.
- **SC-004**: Hay al menos un desvío de 3 veces o más sobre el promedio de los tres resultados validados anteriores de una prueba en un origen.
- **SC-005**: El 100 % de las ejecuciones fuera de desarrollo, con la demo ya cargada o con un conflicto de usuario o de tipo de estudio terminan sin cambios en la base.
- **SC-006**: Con cada usuario demo, quien presenta encuentra trabajo pendiente acorde a su rol apenas inicia sesión.
- **SC-007**: Dos cargas en bases nuevas el mismo día producen los mismos clientes, orígenes, valores medidos y evaluaciones.

## Assumptions

- **Trazabilidad**: SCRUM-78 – Datos de demo (tarea técnica). Responsable: Delfina. Va antes de SCRUM-75 (8.3), SCRUM-60 (8.1), SCRUM-61 (8.2), SCRUM-76 (8.4) y SCRUM-77 (8.5).
- **Volumen**: 3 clientes con 2 o 3 orígenes cada uno y una muestra mensual por origen (unas 45 muestras); suficiente para los gráficos sin hacer lenta la carga.
- **Volver a empezar**: Los informes emitidos no se pueden borrar (US 7.3), así que no hay opción para recargar la demo; para empezar de cero se recrea la base de desarrollo.
- **Contraseña de desarrollo**: Los usuarios demo tienen una contraseña conocida y documentada; es aceptable porque el comando solo corre en desarrollo.
- **Entorno**: Se reutiliza la marca de entorno de desarrollo que ya usaba `cargar_demo_us51`; `qa` deja de estar permitido porque el criterio pide «solo en desarrollo».
- **Regla de desvío**: El desvío se diseña para superar con amplitud la regla inicial de SCRUM-61 (más del 30 % contra el promedio de los últimos 3 validados), así sigue siendo claro si el laboratorio ajusta el umbral.
- **Datos ficticios**: AquaLab es un proyecto FIUBA; nombres, documentos y valores son inventados. No llevan prefijo visible para que la presentación se vea natural.
- **Alcance excluido**: El dashboard y sus indicadores (SCRUM-75, 76, 60, 61, 77); recargar o borrar la demo; datos para producción.
