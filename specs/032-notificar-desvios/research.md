# Research: Notificar desvíos relevantes (SCRUM-61, US 8.2)

Decisiones de diseño tomadas a partir del código existente y de los ajustes del usuario (validar
es revisar; el desvío se calcula al vuelo, sin modelo propio). No quedan `NEEDS CLARIFICATION`.

## R1. El desvío se calcula al vuelo, no se guarda

- **Decision**: no hay modelo `Desvio`. `estudios/desvios.py` evalúa el desvío de los resultados
  Cargados y sin validar cada vez que se muestran: detalle del estudio, pantalla de validación y
  lista «Desvíos sin revisar». Los servicios de carga y corrección no cambian; `calculo.recalcular`
  solo suma el aviso por correo de R12 (tanda 3), que no guarda nada.
- **Rationale**: pedido del usuario. El resultado vigente es la única fuente: una carga o una
  corrección se refleja sola (FR-001, SC-003), no hay estado que pueda quedar desincronizado ni
  transiciones que mantener, y no hace falta un comando para datos previos.
- **Alternatives considered**: modelo `Desvio` persistido con reevaluación en `recalcular` y
  comando `evaluar_desvios` (diseño anterior: más código, migración, invariantes y casos de
  concurrencia para la misma información visible).

## R2. Historial: `comparacion.comparar` + un campo nuevo `anteriores`

- **Decision**: la evaluación de un estudio hace una sola llamada a
  `comparacion.comparar(origen, estudio=estudio, codigos=…)`. A `HistorialPrueba` se le agrega
  `anteriores: tuple[Punto, ...]`, la misma lista que hoy se calcula en `historial_de_prueba` y se
  pasa a `variacion` (validados de muestras previas, misma unidad, en orden). La 8.2 toma
  `anteriores[-N:]`, calcula su mediana (R3) y usa `comparacion.cambio` para la diferencia y el
  porcentaje.
- **Rationale**: FR-003 pide una sola definición del historial. `comparar` ya resuelve validación
  vigente, orden por `(fecha_muestreo, numero_pi)`, exclusión de otros estudios de la misma muestra
  y de otra unidad, con cantidad fija de consultas. Exponer `anteriores` es el cambio mínimo y no
  altera la pantalla de la 8.1.
- **Alternatives considered**: una consulta propia de «últimos 3 validados» (segunda definición,
  prohibida por FR-003); un parámetro `ultimos=N` en `comparar` (mezcla la regla de la 8.2 en la
  8.1).

## R3. Referencia: mediana de los últimos N; regla exacta, sin redondeo ni división

- **Decision (referencia)**: `desvios.mediana(valores)` de los últimos N `anteriores` (con N par,
  el promedio de los dos centrales, en `Decimal`). No se usa `comparacion.variacion`, que promedia.
- **Rationale (referencia)**: ajuste del usuario. Un pico aislado contamina el promedio: en la
  demo, Detergentes de «Colectora» da 4,2 contra 14 / 4,1 / 4,3, que es −43,8 % contra el promedio
  (7,4667, desvío falso) y −2,3 % contra la mediana (4,3, sin desvío). La mediana sigue detectando
  el pico cuando es el resultado actual.
- **Alternatives considered (referencia)**: promedio (diseño anterior, sensible a picos); promedio
  recortado (con N = 3 equivale a la mediana y es más difícil de explicar).
- **Decision (regla)**: `desvios.es_desvio(valor, referencia, umbral)`:
  `abs(valor − referencia) * 100 > umbral * abs(referencia)` si `referencia != 0`; con `referencia == 0`,
  desvío si `valor != 0` (FR-014). Todo `Decimal`. El porcentaje que se muestra es el de
  `comparacion.cambio` (0,1 `ROUND_HALF_UP`), solo para mostrar.
- **Rationale**: FR-002 (exactamente 30 % no es desvío; decide el valor completo). Multiplicar en
  vez de dividir evita depender de la precisión del contexto.
- **Alternatives considered**: comparar el porcentaje redondeado (30,04 % → 30,0 % no sería
  desvío, contra lo pedido).

## R4. Pruebas Ausente/Presente

- **Decision**: con `es_presencia(unidad)`: desvío si los N anteriores tienen todos el mismo valor
  (0 o 1) y el actual es el otro. La referencia es ese valor común (0 o 1, la mediana de valores
  iguales); no hay porcentaje. El texto es «Presente (los últimos 3: Ausente)».
- **Rationale**: Edge Case de la spec; la 8.1 ya trata A/P como cambio de estado. Usar el valor
  común como referencia deja la constancia de la validación (R6) siempre completa.
- **Alternatives considered**: tratar 0/1 como números (con historial mixto daría desvíos sin
  sentido); excluir A/P (contra «no recortar»).

## R5. Revisar al validar

- **Decision**: no hay servicio, vista ni pantalla propios para revisar.
  `servicios.validar_resultados(estudio_pk, elegidas, usuario, observaciones=None)`: con el estudio
  y las pruebas ya bloqueados, hace una llamada a `desvios.evaluar_estudio(estudio, asignaciones)`
  y, por cada prueba que efectivamente valida, crea la `Validacion` con `observacion` y, si
  `detectar` dio desvío, `desvio_referencia` y `desvio_umbral`. Las omitidas («ya estaba validada»,
  «ya no tenía resultado», «cambió mientras se revisaba») no guardan nada.
- **Rationale**: FR-009 — la constancia nace en la misma fila y transacción que la validación, así
  que una validación rechazada o fallida no deja nada, y dos validaciones simultáneas dejan una
  sola. Se reevalúa bajo el bloqueo porque lo que vale es la evaluación al confirmar (Edge Case
  «desvío que aparece o desaparece mientras se valida»); el valor visto ya lo controla
  `resultado_<pk>`.
- **Alternatives considered**: guardar lo que se vio en la pantalla (campos ocultos manipulables y
  posiblemente viejos); acción separada «Marcar como revisado» (descartada por el usuario).

## R6. Constancia en `Validacion`

- **Decision**: migración `estudios.0009_validacion_desvio` que agrega a `Validacion`:
  `observacion = CharField(max_length=500, blank=True, default="")`,
  `desvio_referencia = DecimalField(max_digits=28, decimal_places=10, null=True, blank=True)` y
  `desvio_umbral = DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)`, con
  `CheckConstraint` `validacion_desvio_completo` (ambos nulos o ambos no nulos). «Validada con
  desvío» ⇔ `desvio_umbral IS NOT NULL`. Quién y cuándo: `validada_por`, `fecha_validacion`.
- **Rationale**: pedido del usuario; `Validacion` ya es inalterable en la práctica (nunca se borra,
  se anula), así que la constancia sobrevive a una corrección posterior (US 3, escenario 7). Las
  validaciones existentes quedan con valores nulos/vacíos: sin desvío registrado.
- **Alternatives considered**: guardar también la cantidad N o los previos (no se pidió; la
  cantidad vigente está en la configuración y los previos se ven en la comparación histórica).

## R7. Configuración en un solo lugar

- **Decision**: `settings.AQUALAB_DESVIOS = {"umbral": "30", "cantidad": 3}` con un comentario
  como el de `AQUALAB_LABORATORIO`. `desvios.regla()` es la única lectura: devuelve
  `Regla(umbral: Decimal, cantidad: int)` y valida (umbral > 0, cantidad ≥ 1;
  `ImproperlyConfigured` si no). Los textos de ayuda se arman con `texto_regla(regla())`.
- **Rationale**: FR-003, US 5; los tests cambian la regla con el fixture `settings`.
- **Alternatives considered**: modelo de configuración editable en el admin (no se pidió pantalla);
  constante en el módulo (cambiarla es tocar código).

## R8. Lista de pendientes

- **Decision**: `desvios.pendientes()` consulta las asignaciones `CARGADA` con resultado (con
  `select_related` de prueba, resultado y estudio → muestra → cliente/origen), las agrupa por
  estudio y llama una vez a `evaluar_estudio` por estudio; devuelve una lista de `Pendiente`
  (asignación, estudio, muestra, prueba, `Deteccion`, `fecha_calculo` del resultado) ordenada por
  `fecha_calculo` descendente y pk. El dashboard usa `len()` y `[:10]`; la lista completa,
  `Paginator` sobre la lista (25 por página). El enlace a la comparación es
  `estudios:comparacion?estudio=<pk>&pruebas=<código>&elegir=1`.
- **Rationale**: FR-006. Las consultas crecen con la cantidad de estudios con resultados sin
  validar (cada `comparar` es de cantidad fija), no con las pruebas; en un laboratorio son decenas
  como mucho (la demo tiene 4), dentro de SC-007. Un test fija las consultas por estudio.
- **Alternatives considered**: calcular en `informes/tablero.py` (los desvíos son de `estudios`);
  una consulta SQL agregada (sería una segunda definición del historial, prohibida por FR-003).

## R9. Pantallas y permisos

- **Decision**:
  - Detalle (cualquier empleado): marca `estudios/desvio.html` en las filas Cargadas con desvío y
    «Desvío revisado» en las Completadas cuya validación vigente tiene constancia.
  - Validación (`estudios.validar_resultados`): filas con desvío destacadas, campo
    `observacion_<pk>` de `ValidarResultadosForm` (`CharField(max_length=500, required=False)`,
    `help_text`) solo para ellas; resumen «N pruebas con desvío»; «Historial insuficiente para
    detectar desvíos» en las demás que no alcanzan N. El campo viaja oculto a la confirmación
    (como `resultado_<pk>`) y `form.observaciones()` arma el dict para el servicio, solo de las
    elegidas.
  - Confirmación: «N de los M resultados elegidos tienen desvío: quedarán revisados al validar»,
    con prueba y observación (FR-008). No impide confirmar.
  - Dashboard y `estudios:desvios`: `informes.ver_dashboard`; «Validar» solo con
    `perms.estudios.validar_resultados`.
  - Informe, PDF, impresión, correo y control previo: sin cambios.
- **Rationale**: FR-005 a FR-010.
- **Alternatives considered**: observación general para toda la validación (no dice a qué prueba
  se refiere); permiso nuevo `revisar_desvios` (mismo público que valida).

## R10. Demo

- **Decision**: con el guion actual, Pozo 2 Cloruro da desvío en el mes 1 (415 contra 121, 124,
  120 → mediana 121, +243,0 %) y en el mes 0 (430 contra 124, 120, 415 → mediana 124, +246,8 %). Como la demo valida con el
  servicio real, la validación del mes 1 guarda la constancia sola; `cargar_estudio` pasa
  `observaciones` para ese Cloruro («Se repitió la medición: el valor es correcto.»). El del mes 0
  (estudio CARGADO) queda pendiente. `test_demo.py` fija los dos casos y la cantidad de pendientes.
- **Rationale**: FR-015; la demo usa los servicios reales (SCRUM-78).
- **Alternatives considered**: cambiar el guion (no hace falta).

## R11. Notas

- Calcular un desvío no escribe nada (FR-011): `evaluar_estudio` y `pendientes` son de solo
  lectura; solo `validar_resultados` escribe la constancia.
- Corrección de un resultado validado: el recálculo anula la validación (US 6.3); la prueba vuelve
  a Cargada y se evalúa de nuevo con el valor nuevo. La validación anulada conserva su constancia.
- No se agrega admin; la constancia se ve en el detalle del estudio.

## R12. Aviso por correo al calcular (tanda 3)

- **Decision**: módulo `estudios/notificaciones.py` (como `usuarios/notificaciones.py`).
  `calculo.recalcular` guarda los valores previos y, al terminar, llama a
  `notificaciones.avisar_desvios(estudio, codigos)` con los códigos cuyo resultado es nuevo o
  cambió de valor. Esa función relee esas asignaciones Cargadas, las evalúa con
  `desvios.evaluar_estudio` (dentro de la transacción y con el estudio bloqueado por el llamador),
  arma los datos de cada `Deteccion` como textos y agenda `transaction.on_commit(enviar)`. `enviar`
  busca los usuarios activos del grupo «Bioquímicos» y manda un `EmailMessage` por desvío
  (destinatarios en `to`), con asunto y cuerpo de `estudios/correos/desvio_asunto.txt` y
  `desvio_cuerpo.txt` (patrón de `informes/envios.py`). Cada falla queda en el logger
  `estudios.notificaciones` y no se propaga; sin bioquímicos activos, una advertencia.
- **Enlace absoluto**: `settings.AQUALAB_URL_BASE` (variable de entorno, por defecto
  `http://localhost:8000`) + `reverse("estudios:detalle")`; en Render se configura con la URL
  pública. El cálculo no tiene `request`, así que no se usa `build_absolute_uri`.
- **Rationale**: pedido del usuario (ajuste 4). Enganchar en `recalcular` cubre carga, corrección
  y dependientes en un solo lugar; comparar con los valores previos evita reenviar un recálculo con
  el mismo valor (FR-016); `on_commit` garantiza que una operación deshecha no avise (FR-018) y que
  el envío no frene ni rompa la carga (FR-019). `desvios.py` sigue siendo de solo lectura.
- **Alternatives considered**: enviar desde cada servicio (tres lugares); señales de `Resultado`
  (no ven el valor previo y el proyecto evita señales, US 1.3); enviar sincrónico dentro de la
  transacción (una falla o un servidor lento afectaría la carga).
- **Nota**: la demo usa los servicios reales, así que también genera los correos de sus desvíos
  (en desarrollo salen por la consola). La validación no recalcula: no envía correos.
