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
Las **opciones** (research R12) son referencias con una `pregunta` de seguimiento: las devuelven
las herramientas cuando listan coincidencias para elegir (`detalle_estudio` con varios estudios:
«¿Qué no cumple en el estudio N?» con `solo_fuera_de_norma`, si no «¿Cómo está el estudio N?»;
`buscar_muestra` por texto: «¿Cómo está el PI N?»; `buscar_cliente` y `estudios_de_cliente` con
varios: «¿Qué estudios tiene X?», solo clientes activos). Solo cuentan las de la última
herramienta y van primero en los enlaces.
Argumentos inválidos (tipo incorrecto, faltantes) → `{"encontrado": false, "mensaje": "Pedido
inválido."}`; una herramienta desconocida → igual. Una excepción inesperada se registra y se
devuelve `{"encontrado": false, "mensaje": "No se pudo consultar."}`.

## `buscar_muestra`

- **Parámetros**: `numero_pi` (entero, opcional), `texto` (string, opcional; al menos uno).
- **Sin ninguno de los dos**: `encontrado: false`, «Indicá el N° PI o un texto para buscar la
  muestra.».
- **Con `numero_pi`**: la muestra exacta o «No hay ninguna muestra con el N° PI N.» (también
  para números ≤ 0 o fuera de rango).
  - **Datos**: `numero_pi`, nombre, cliente (nombre), origen, fechas de muestreo e ingreso, tipo
    de vertido, sitio de extracción (sin el estado de la muestra, SCRUM-82), `total_estudios` y
    `estudios`: `[{numero, tipo, estado, pruebas_completadas, total_pruebas, con_informe,
    resumen, pruebas}]` de `muestras.views.estudios_de_la_ficha` (orden `-pk`, como la ficha),
    solo los 5 más recientes (`ESTUDIOS_POR_MUESTRA`). `pruebas`: `[{codigo, nombre, estado,
    resultado, unidad, evaluacion}]` (los valores de `detalle_estudio`, sin límite ni norma);
    `resumen`: `{cumple, fuera_de_norma, sin_limite_comparable, sin_resultado}`, contado por
    AquaLab. Con `total_estudios > 5`, `mensaje`: «La muestra tiene T estudios;
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
  - **Referencias**: cada muestra listada. **Opciones**: cada muestra, con «¿Cómo está el PI N?».

## `buscar_cliente`

- **Parámetros**: `texto` (string, obligatorio).
- **Datos**: `clientes: [{id, nombre, activo}]` hasta 10: primero los activos de
  `buscar_clientes(texto)` y después los inactivos que coinciden con el mismo
  `clientes.views.filtro_clientes` (nombre, razón social o documento), marcados `activo: false`
  sin más datos. El `id` es el que acepta `estudios_de_cliente`. Sin coincidencias: «No hay
  clientes que coincidan con «texto».».
- **Referencias**: ficha e historial de cada cliente activo.

## `estudios_de_cliente`

- **Parámetros**: `cliente` (string: nombre o razón social) o `cliente_id` (entero devuelto por
  `buscar_cliente`).
- **No encontrado**: «No hay ningún cliente que coincida con «texto».» o «No hay ningún cliente
  con ese identificador.».
- **Varias coincidencias**: `encontrado: true`, `datos.coincidencias: [{id, nombre, activo}]`
  (hasta 10) y `mensaje: "Hay varios clientes con ese nombre; pedí cuál."`, sin estudios.
- **Cliente inactivo**: `encontrado: false`, «El cliente X está inactivo.», sin referencias.
- **Datos**: `cliente` (nombre) y `estudios`: los 10 más recientes según
  `muestras_del_historial` (`numero`, `numero_pi`, origen, tipo, fecha de ingreso, estado,
  `con_informe`), con `total` y `mostrados`. Con `total > 10`, AquaLab agrega «X tiene T
  estudios; se muestran los 10 más recientes. El resto está en su historial.» y pone primero el
  enlace al historial (FR-009).
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
