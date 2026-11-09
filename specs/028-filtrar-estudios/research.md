# Research: Filtrar estudios por estado y fecha

**Feature**: `028-filtrar-estudios` | **Plan**: [plan.md](./plan.md)

No había `NEEDS CLARIFICATION` en el contexto técnico; estas son las decisiones de diseño.

## R1. Un formulario de filtros compartido con el historial

- **Decision**: Los campos `desde`, `hasta` y `estado`, la validación de rango y la marca
  `is-invalid` se mueven de `clientes.forms.HistorialClienteForm` a una base nueva
  `estudios.forms.FiltrosEstudioForm`. `HistorialClienteForm` pasa a heredarla y solo cambia las
  etiquetas («Ingreso desde», «Ingreso hasta», «Estado del estudio»). «Buscar estudio» usa
  `FiltrarEstudiosForm(BuscarEstudioForm, FiltrosEstudioForm)`, con las etiquetas «Desde», «Hasta» y
  «Estado».
- **Rationale**: El criterio 6 pide reutilizar el patrón del historial y FR-010, mismos mensajes. Una
  sola definición evita que los dos formularios se separen. La base va en `estudios` porque filtra
  estudios (estado `EstadoEstudio`) y porque `clientes` ya depende de `estudios` (al revés crearía un
  ciclo de imports: `clientes/models.py` no puede importar `estudios`, pero `clientes/forms.py` sí).
- **Alternatives considered**: Copiar los campos en `estudios/forms.py` (duplica mensajes y la regla
  desde ≤ hasta); agregar los campos a `BuscarEstudioForm` (lo usa también `informes:listar`, que
  quedaría validando filtros que no muestra).

## R2. Rango de fechas sobre un `DateTimeField`

- **Decision**: `fecha_creacion` es `DateTimeField` (con `USE_TZ`). El filtro convierte los días a
  límites conscientes de zona en `TIME_ZONE` (America/Argentina/Buenos_Aires):
  `fecha_creacion >= inicio(desde)` y `fecha_creacion < inicio(hasta + 1 día)`. Lo arma
  `estudios/busqueda.py:filtro_estado_fechas(desde, hasta, estado)`, que devuelve un `Q`.
- **Rationale**: Ambos días quedan completos (incluye 23:59:59.999 de «Hasta», FR-003) y en la misma
  zona con la que el listado muestra la fecha (`|date` usa la zona actual). Comparar con límites
  permite usar índices; `__date` convierte cada fila.
- **Alternatives considered**: `fecha_creacion__date__range` (mismo resultado, pero castea cada fila;
  menos explícito sobre la zona); `__lte=hasta` sobre el datetime (perdería todo el día «Hasta»).

## R3. Valores inválidos: listado completo, sin filtrar

- **Decision**: Si el formulario no valida (texto, fecha, rango o estado), la vista lista todos los
  estudios sin aplicar ningún criterio y el formulario muestra los errores junto a cada campo con los
  valores recibidos. Es lo que hace `clientes:historial`.
- **Rationale**: Criterios 5 y 6 de la tarea y supuesto de la spec. Una pantalla con un solo
  comportamiento ante errores es más predecible.
- **Impacto**: Cambia lo que hoy hace un texto inválido (menos de 2 caracteres, número inválido o
  más de 100 caracteres): hoy `page_obj` es `None` y no se muestra listado. Se ajustan los tres tests
  de `estudios/tests/test_consulta.py` que lo verifican (`test_busqueda_un_caracter_no_numerico_rechazada`,
  `test_busqueda_numero_invalido_o_fuera_de_rango_muestra_error`,
  `test_busqueda_supera_longitud_maxima_muestra_error`): siguen comprobando el mensaje y pasan a
  esperar el listado completo. `informes:listar` no cambia.
- **Alternatives considered**: Mantener «sin listado» ante errores (contradice el criterio 6);
  aplicar los criterios válidos e ignorar el inválido (el usuario vería un resultado que no pidió).

## R4. «Limpiar filtros» y parámetros de la paginación

- **Decision**: `hay_filtros` es verdadero si llegó `q`, `desde`, `hasta` o `estado` no vacíos,
  válidos o no (como `hay_filtros` del historial). «Limpiar filtros» enlaza a `estudios:buscar` sin
  parámetros y reemplaza a «Ver todos». La paginación recibe `parametros` = la query string actual
  sin `page` (`request.GET.copy()` + `pop("page")` + `urlencode()`), igual que el historial.
- **Rationale**: FR-006/FR-007; un filtro inválido también debe poder limpiarse. Copiar la query
  string completa conserva todos los criterios sin enumerarlos en el template.
- **Alternatives considered**: Armar la query en el template campo por campo (lo que se hace hoy con
  `q`): hay que acordarse de cada filtro nuevo.

## R5. Estados vacíos

- **Decision**: Tres casos: sin estudios registrados («Aún no hay estudios registrados.», como hoy);
  solo texto sin coincidencias («No se encontraron estudios para «…».», como hoy); con algún filtro
  aplicado y sin coincidencias, «Ningún estudio coincide con la búsqueda y los filtros.» con la acción
  «Limpiar filtros» (`ui/estado_vacio.html`, como el historial). El encabezado de la tabla dice
  «N estudios encontrados» si hay texto o filtros aplicados.
- **Rationale**: FR-008 sin cambiar los mensajes ya probados de la US 5.2.

## R6. Ayudas (US 9.1)

- **Decision**: `desde` y `hasta` llevan `help_text` en `FiltrarEstudiosForm` («Fecha en que se creó
  el estudio. El día indicado se incluye.»), dibujado por `ui/campo.html`. Estado no lleva ayuda: sus
  opciones se explican solas. Los textos van en el formulario, no en el modelo (CLAUDE.md, US 9.1).
- **Rationale**: Constitution 1.2.0 (sección Interfaz): «Desde» no dice por sí solo que es la fecha
  de creación (el listado también tiene muestras con fecha de ingreso).

## R7. Sin JavaScript, índices ni migraciones

- **Decision**: Formulario GET común, sin JS. No se agrega índice sobre `fecha_creacion`.
- **Rationale**: SC-003 (1000 estudios en menos de 2 s) se cumple con un filtro simple y la
  paginación existente; un índice sería una migración sin necesidad medida (YAGNI).
