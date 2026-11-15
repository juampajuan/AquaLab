# Contrato: herramientas ofrecidas al modelo

Definidas en `asistente/herramientas.py` con el formato `tools` de OpenAI
(`{"type": "function", "function": {"name", "description", "parameters"}}`). Todas son de solo
lectura, se ejecutan con el usuario que pregunta (research R5) dentro de una transacción
`READ ONLY` (R6) y devuelven un objeto JSON con:

- `encontrado`: `true`/`false`.
- `mensaje`: si `encontrado` es `false`, el texto a decir («No hay ninguna muestra con el N° PI
  200999.»).
- `datos`: lo pedido, solo con los campos de la lista blanca (data-model.md).
- `total` / `mostrados` cuando se recorta una lista.

Las referencias para los enlaces se guardan del lado de AquaLab y no se envían al modelo.
Argumentos inválidos (tipo incorrecto, faltantes) → `{"encontrado": false, "mensaje": "Pedido
inválido."}`; una herramienta desconocida → igual. Una excepción inesperada se registra y se
devuelve `{"encontrado": false, "mensaje": "No se pudo consultar."}`.

## `buscar_muestra`

- **Parámetros**: `numero_pi` (entero, opcional), `texto` (string, opcional; al menos uno).
- **Sin ninguno de los dos**: `encontrado: false`, «Indicá el N° PI o un texto para buscar la
  muestra.».
- **Con `numero_pi`**: la muestra exacta o «No hay ninguna muestra con el N° PI N.» (también
  para números ≤ 0 o fuera de rango).
  - **Datos**: `numero_pi`, nombre, cliente (nombre), origen, estado, fechas de muestreo e
    ingreso, tipo de vertido, sitio de extracción, `total_estudios` y `estudios`: `[{numero,
    tipo, estado, pruebas_completadas, total_pruebas, con_informe}]` de
    `muestras.views.estudios_de_la_ficha` (orden `-pk`, como la ficha), solo los 5 más recientes
    (`ESTUDIOS_POR_MUESTRA`). Con `total_estudios > 5`, `mensaje`: «La muestra tiene T estudios;
    se detallan los 5 más recientes.» y AquaLab agrega el aviso y el enlace a la ficha a la
    respuesta final (FR-009a).
  - **Referencias**: muestra, cada estudio listado, el cliente (si activo).
- **Con `texto`**: un **resumen** de las muestras cuyo nombre, origen o cliente (nombre o razón
  social) coinciden, sin acentos ni mayúsculas, más recientes primero (`-fecha_ingreso`,
  `-numero_pi`), hasta 10, con `total` y `mostrados`. Sin coincidencias: «No hay muestras que
  coincidan con «texto».».
  - **Datos**: `muestras: [{numero_pi, nombre, cliente, origen, fecha_ingreso,
    total_estudios}]`, sin los estudios de cada una (cantidad fija de consultas); para verlos, el
    modelo vuelve a llamar con el `numero_pi` elegido.
  - **Referencias**: cada muestra listada.

## `buscar_cliente`

- **Parámetros**: `texto` (string, obligatorio).
- **Datos**: `[{nombre, activo}]` hasta 10, de `buscar_clientes(texto)` (activos) más los
  inactivos que coinciden, marcados `activo: false` sin más datos.
- **Referencias**: ficha e historial de cada cliente activo.

## `estudios_de_cliente`

- **Parámetros**: `cliente` (string: nombre) o `cliente_id` (entero devuelto antes; opcional).
- **Varias coincidencias**: `encontrado: true`, `datos.coincidencias: [{nombre}]` y
  `mensaje: "Hay varios clientes con ese nombre; pedí cuál."`.
- **Cliente inactivo**: `encontrado: false`, «El cliente X está inactivo.».
- **Datos**: los 10 estudios más recientes según `muestras_del_historial` (`numero_pi`, origen,
  tipo, fecha de ingreso, estado, `con_informe`), con `total`.
- **Referencias**: cliente, historial, cada muestra y estudio, informes emitidos.

## `detalle_estudio`

- **Parámetros**: `numero` (entero: N° de estudio), o `numero_pi` (entero), o `texto` (string:
  muestra, origen, cliente o tipo, con `filtro_busqueda` + origen). Opcional `solo_fuera_de_norma`
  (booleano).
- **Varias coincidencias** (por PI con varios estudios o por texto): `datos.coincidencias:
  [{numero, numero_pi, origen, tipo, fecha, estado}]` hasta 10, más recientes primero, y
  `mensaje` pidiendo elegir.
- **Datos**: estudio (`numero`, `numero_pi`, cliente, origen, tipo, estado, `con_informe`) y
  `pruebas`: `[{codigo, nombre, estado, resultado, unidad, sin_resultado, fuera_de_rango_curva,
  evaluacion, limite, norma, origen_limites, validada, fecha_validacion}]` de
  `pruebas_del_detalle`. `resultado` con `texto_resultado` («< 0,5», «Ausente», «7,2»).
  Con `solo_fuera_de_norma`, solo las `fuera_de_norma`, más `resumen: {sin_resultado,
  sin_limite_comparable, total}`.
- **Referencias**: estudio, muestra, cliente (si activo), informe (si emitido).
