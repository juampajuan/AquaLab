# Research: Notificar desvíos relevantes (SCRUM-61, US 8.2)

Decisiones de diseño tomadas a partir del código existente. No quedan `NEEDS CLARIFICATION`.

## R1. Dónde se detecta: dentro de `calculo.recalcular`

- **Decision**: la detección se engancha al final de `calculo.recalcular(estudio, asignaciones)`,
  que llama a `desvios.reevaluar(estudio, cambiadas, sin_resultado)`.
- **Rationale**: todos los caminos que producen o cambian un resultado pasan por `recalcular`:
  `cargar_mediciones`, `corregir_mediciones` (vía `recalcular_resultados`), el borrado de la US 6.5
  (vía `descartar`) y el comando `calcular_resultados`. El estudio ya está bloqueado
  (`select_for_update`) y todo corre en la transacción del llamador, así que si la operación se
  rechaza o falla tampoco quedan desvíos (FR-001). No hay que tocar cada servicio.
- **Alternatives considered**: señales `post_save` de `Resultado` (no ven el «antes», se disparan
  por fila y no por operación, y el proyecto evita señales: ver US 1.3); llamar desde cada servicio
  (cuatro lugares que mantener en sincronía).

## R2. Qué se reevalúa: solo los resultados que cambiaron

- **Decision**: `recalcular` guarda los valores previos (`valores` antes del bucle). Al terminar:
  `cambiadas` = códigos con resultado nuevo o con valor distinto del previo; `sin_resultado` =
  códigos que tenían resultado y lo perdieron (`descartar`). Las calculadas cuyo valor no cambió no
  se tocan (US 2, escenario 4).
- **Rationale**: FR-006 («si el valor no cambió, el desvío queda igual») y el Edge Case «historial
  que cambia después» (solo se reevalúa cuando cambia el resultado de esa prueba en ese estudio).
- **Alternatives considered**: reevaluar todo el estudio en cada carga (cambiaría desvíos de
  pruebas que nadie tocó si el historial del origen cambió entretanto, y generaría avisos nuevos
  sin un cambio que los explique).

## R3. Historial: `comparacion.comparar` + un campo nuevo `anteriores`

- **Decision**: `reevaluar` llama una sola vez a
  `comparacion.comparar(origen, estudio=estudio, codigos=cambiadas)`. A `HistorialPrueba` se le
  agrega `anteriores: tuple[Punto, ...]`, la misma lista que hoy se calcula en
  `historial_de_prueba` y se pasa a `variacion` (validados de muestras previas, misma unidad, en
  orden). La 8.2 toma `anteriores[-N:]` y llama a `comparacion.variacion(ref, ultimos, ...)` para
  el promedio y los textos.
- **Rationale**: FR-003 pide una sola definición del historial. `comparar` ya resuelve validación
  vigente, orden por `(fecha_muestreo, numero_pi)`, exclusión de otros estudios de la misma muestra
  y de otra unidad, y lo hace con cantidad fija de consultas. Exponer `anteriores` es el cambio
  mínimo y no altera la pantalla de la 8.1 (que sigue promediando todos).
- **Alternatives considered**: una consulta propia de «últimos 3 validados» (segunda definición
  del historial, prohibida por FR-003); agregar un parámetro `ultimos=N` a `comparar` (mezcla la
  regla de la 8.2 en la 8.1).

## R4. Regla exacta, sin redondeo ni división

- **Decision**: `desvios.es_desvio(valor, promedio, umbral)`:
  `abs(valor − promedio) * 100 > umbral * promedio` si `promedio > 0`; con `promedio == 0`, desvío
  si `valor != 0` (FR-017). Todo `Decimal`. El porcentaje que se guarda y muestra es el de
  `comparacion.cambio` (0,1 `ROUND_HALF_UP`), solo para mostrar.
- **Rationale**: FR-002 (exactamente 30 % no es desvío; el valor completo decide). Multiplicar en
  vez de dividir evita depender de la precisión del contexto. Los resultados son ≥ 0 en el
  catálogo; un promedio negativo (no ocurre) se trata con `abs(promedio)` por robustez.
- **Alternatives considered**: comparar el porcentaje redondeado (30,04 % → 30,0 % no sería
  desvío, contra lo pedido).

## R5. Pruebas Ausente/Presente

- **Decision**: con `es_presencia(unidad)`: desvío si los N anteriores tienen todos el mismo valor
  (0 o 1) y el actual es el otro. No hay promedio ni porcentaje (`promedio = None`,
  `porcentaje = None`); el texto es «Presente (los últimos 3: Ausente)».
- **Rationale**: Edge Case de la spec; un promedio de 0/1 no tiene sentido para el laboratorio y la
  8.1 ya trata A/P como cambio de estado.
- **Alternatives considered**: tratar 0/1 como números (con promedio 0 todo Presente sería desvío
  aun con historial mixto); excluir A/P (contra «no recortar»).

## R6. Modelo: `Desvio` con la revisión enlazada a la `Validacion`

- **Decision**: un modelo `estudios.Desvio` (ver [data-model.md](./data-model.md)) con la foto de
  la detección (valor, unidad, promedio, porcentaje, previos en JSON, umbral, cantidad, fecha), el
  cierre (`vigente`, `fecha_cierre`, `motivo_cierre`) y la revisión: `validacion` (FK a la
  `Validacion` con la que se revisó, `PROTECT`, null) y `observacion`. Quién y cuándo salen de
  `validacion.validada_por` y `validacion.fecha_validacion`. Restricciones: uno vigente por
  asignación (único parcial, como `Validacion`), cierre completo y observación solo si está
  revisado (`CheckConstraint`).
- **Rationale**: validar cuenta como revisar (ajuste del usuario): enlazar la validación garantiza
  que quién/cuándo coinciden con ella sin duplicar datos, y una `Validacion` nunca se borra (se
  anula), así que la revisión sobrevive aunque la validación se anule después. El patrón «vigente
  + cierre, nunca se borra» es el de `Validacion` (principio IV, FR-006, SC-004).
- **Alternatives considered**: `revisado_por` + `fecha_revision` propios (duplican la validación y
  podrían divergir); tabla `RevisionDesvio` aparte (uno a uno sin beneficio); borrar el desvío al
  corregir (pierde trazabilidad, FR-008).

## R7. Transiciones al reevaluar

- **Decision** (por prueba cambiada, con la regla vigente):
  | Vigente antes | Nuevo resultado | Acción |
  |---|---|---|
  | — | desvío | crear |
  | — | sin desvío / historial insuficiente | nada |
  | sí | desvío (valor distinto) | cerrar el anterior `REEMPLAZADO` + crear uno nuevo sin revisar |
  | sí | sin desvío / historial insuficiente | cerrar `CORREGIDO` («Resuelto por corrección») |
  | sí | sin resultado | cerrar `SIN_RESULTADO` |
  Se cierra con `filter(vigente=True).update(...)` antes de crear el nuevo (respeta el único
  parcial).
- **Rationale**: FR-006 y US 2. La revisión anterior se refería a otro valor; por eso el nuevo
  nace sin revisar.
- **Alternatives considered**: actualizar en el lugar el desvío vigente (perdería el valor y la
  revisión originales).

## R8. Configuración en un solo lugar

- **Decision**: `settings.AQUALAB_DESVIOS = {"umbral": "30", "cantidad": 3}` con un comentario
  como el de `AQUALAB_LABORATORIO`. `desvios.regla()` es la única lectura: devuelve
  `Regla(umbral: Decimal, cantidad: int)` y valida (umbral > 0, cantidad ≥ 1;
  `ImproperlyConfigured` si no). Cada desvío guarda `umbral` y `cantidad`. Los textos de ayuda se
  arman con `regla()`.
- **Rationale**: FR-003, FR-019, US 6; los tests cambian la regla con el fixture `settings`.
- **Alternatives considered**: modelo de configuración editable en el admin (no se pidió pantalla;
  agrega migración y permisos); constante en el módulo (cambiarla es tocar código).

## R9. Revisar al validar: dentro de `servicios.validar_resultados`

- **Decision**: no hay servicio, vista ni pantalla propios para revisar. `validar_resultados(
  estudio_pk, elegidas, usuario, observaciones=None)` recibe además `{asignacion_pk: texto}`.
  Después de crear la `Validacion` de cada prueba que efectivamente se valida, llama a
  `desvios.revisar_al_validar(asignacion, validacion, observacion)`, que hace
  `Desvio.objects.filter(asignacion=…, vigente=True, validacion__isnull=True).update(
  validacion=…, observacion=…)`. Las omitidas («ya estaba validada», «ya no tenía resultado»,
  «cambió mientras se revisaba») no llegan a ese paso.
- **Rationale**: FR-012 — misma transacción y mismo bloqueo (estudio y luego pruebas) que la
  validación, así que una validación rechazada o fallida no deja revisión, y dos validaciones
  simultáneas dejan una sola (la segunda se omite por «ya estaba validada»). Un desvío solo cambia
  cuando cambia el valor (R2), y el valor visto ya se controla con `resultado_<pk>`: lo que se
  revisa es exactamente lo que se mostró.
- **Edge «recálculo con el mismo valor»**: la prueba vuelve a Cargada pero el desvío sigue
  revisado (`validacion` apunta a la anulada); el `update` filtra `validacion__isnull=True`, así
  que revalidar no pisa la revisión ni la observación.
- **Alternatives considered**: acción separada «Marcar como revisado» (descartada por el usuario:
  un paso más y la posibilidad de validar sin mirar el desvío o revisarlo sin validar).

## R10. Pantallas y permisos

- **Decision**:
  - Detalle del estudio (cualquier empleado): marca en la fila (`estudios/desvio.html`) y sección
    «Desvíos» con todos los del estudio (vigentes y cerrados con motivo, revisión con quién,
    cuándo y observación; FR-007, FR-008).
  - Validación (`estudios.validar_resultados`): las filas con desvío vigente sin revisar se
    destacan con la marca, el enlace a la comparación y un campo `observacion_<pk>` en
    `ValidarResultadosForm` (`CharField(max_length=500, required=False)`, `help_text`), creado
    solo para esas filas; resumen «N pruebas con desvío»; «Historial insuficiente para detectar
    desvíos» por fila (cuenta de `anteriores` < N con un `comparar` sobre las filas mostradas).
    La vista adjunta `asignacion.desvio` con `desvios.del_estudio`. El campo viaja oculto a la
    confirmación (como `resultado_<pk>`) y `form.observaciones()` arma el dict para el servicio,
    solo de las elegidas.
  - Confirmación de la validación: «N de los M resultados elegidos tienen desvío: quedarán
    revisados al validar», con prueba y observación (FR-011). No impide confirmar.
  - Dashboard y `estudios:desvios` (lista completa paginada): `informes.ver_dashboard`; acción
    «Validar» → `estudios:validar_resultados` solo con `perms.estudios.validar_resultados`.
  - Control previo al informe: sin cambios (un desvío sin revisar implica una prueba sin validar,
    que ya impide informar).
- **Rationale**: FR-007 a FR-013 con el ajuste del usuario: la revisión ocurre donde se decide el
  resultado. El campo solo existe para las filas con desvío, así una observación nunca se guarda en
  una prueba sin desvío.
- **Alternatives considered**: una observación general para toda la validación (no dice a qué
  desvío se refiere); permiso nuevo `revisar_desvios` (mismo público que valida).

## R11. Consulta de pendientes y comparación enlazada

- **Decision**: `desvios.pendientes()` (vigentes con `validacion IS NULL`, `-fecha_deteccion`,
  `-pk`, con `select_related` de asignación → prueba y estudio → muestra → cliente/origen) es la
  única consulta; la usan el dashboard (`count()` + `[:10]`) y la lista (`Paginator`, 25 por
  página). El enlace a la comparación es
  `estudios:comparacion?estudio=<pk>&pruebas=<código>&elegir=1`. No hay columna «Validado»: un
  pendiente siempre es de un resultado sin validar.
- **Rationale**: FR-009 y SC-007 (cantidad fija de consultas). La comparación ya acepta esos
  parámetros (US 8.1).
- **Alternatives considered**: calcular pendientes en `informes/tablero.py` (los desvíos son de
  `estudios`; el tablero no debe redefinirlos).

## R12. Datos previos y demo

- **Decision**:
  - Comando `python manage.py evaluar_desvios`: para estudios sin informe, evalúa las asignaciones
    Cargadas con resultado y **sin ningún desvío registrado**, por estudio en una transacción con
    el estudio bloqueado. Idempotente (FR-018).
  - Demo: con el guion actual, Pozo 2 Cloruro da desvío en el mes 1 (415 contra 121, 124, 120 →
    +241 %) y en el mes 0 (430 contra 124, 120, 415 → +95,8 %). Como la demo valida con el
    servicio real, los desvíos de los estudios que el guion valida quedan revisados solos; se pasa
    `observaciones` para el Cloruro de Pozo 2 del mes 1 («Se repitió la medición: el valor es
    correcto.»). El del mes 0 (estudio CARGADO) queda pendiente. `test_demo.py` fija: Pozo 2 mes 0
    Cloruro pendiente (430 / 219,67 / +95,8 %), mes 1 revisado con observación, y la cantidad de
    pendientes (los estudios PARCIAL/CARGADO del guion) para detectar cambios (FR-020).
- **Rationale**: los datos cargados antes de la 8.2 no tienen desvíos; la demo usa los servicios
  reales (CLAUDE.md, SCRUM-78), así que los desvíos nacen y se revisan solos.
- **Alternatives considered**: migración de datos que evalúe (lenta, acoplada al historial
  vigente al migrar y difícil de repetir).

## R13. Notas

- Estudio con informe emitido: los servicios no llegan a `recalcular` (`admite_correcciones`), así
  que no se crean ni cierran desvíos; todas sus pruebas están validadas, así que sus desvíos ya
  están revisados.
- Validar no pasa por `recalcular`: solo revisa (R9), no crea ni cierra desvíos.
- Invariante: una prueba Completada no tiene desvío vigente sin revisar (validar revisa; un cambio
  de valor que crea uno nuevo devuelve la prueba a Cargada).
- No hay admin de `Desvio` (como `Informe` y `Validacion`): solo se crea y cierra por `reevaluar`
  y se revisa por `validar_resultados`.
