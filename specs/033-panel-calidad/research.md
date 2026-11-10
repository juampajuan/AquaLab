# Research: Panel de calidad del agua

Decisiones técnicas de la US 8.4. Formato: decisión, motivo y alternativas descartadas.

## R1 – Dónde vive el cálculo

- **Decisión**: módulo nuevo `informes/calidad.py`, única fuente de los cálculos de la sección
  «Calidad». Reutiliza de `informes/tablero.py` el `Periodo` (no lo recalcula), `fecha_local`,
  `variacion` y `con_coma`. La vista `informes:dashboard` agrega `contexto["calidad"] =
  calidad.armar(contexto["periodo"])`; `tablero.armar` no cambia.
- **Motivo**: `tablero.py` ya tiene ~400 líneas y cubre otra pregunta (volumen y tiempos); la 8.2
  sumó sus desvíos al dashboard del mismo modo (módulo propio + una línea en la vista). Al recibir el
  `Periodo` ya armado, la sección usa exactamente el período del selector (FR-001) y no hay forma de
  que se desincronicen.
- **Alternativas**: agregar las funciones a `tablero.py` (archivo muy largo, mezcla dos historias);
  módulo en la app `comparacion` (la constitution la prevé, pero hoy la comparación vive en
  `estudios` y el dashboard en `informes`).

## R2 – Qué resultados entran y en qué período

- **Decisión**: base = `Validacion.objects.filter(anulada=False)` anotada con
  `dia = fecha_local("fecha_validacion")` (zona del laboratorio, como la 8.3). Evaluados =
  `evaluacion in (cumple, fuera_de_norma)`; `sin_limite` solo se cuenta aparte. Nunca se llama a
  `pruebas/limites.py`.
- **Motivo**: FR-002/003 y criterio 6. La invariante de la 6.4 (una vigente ⇔ Completada) garantiza
  una sola fila por prueba del estudio; las anuladas quedan afuera solas. Las de estudios con informe
  emitido cuentan (son resultados validados).
- **Alternativas**: filtrar por `PruebaEstudio.estado = completada` y unir a la validación (más
  joins, mismo resultado); fecha de muestreo (descartada en la spec).

## R3 – Consultas

- **Decisión**: una cantidad fija de consultas agregadas, sin N+1:
  1. Indicador general: un `aggregate` con `Count(filter=...)` para fuera de norma y evaluados del
     período y del anterior, más sin límite del período (1 consulta).
  2. Por prueba: `values("asignacion__prueba")` + `Count` fuera/evaluados, `.filter(evaluados__gte=
     MINIMO_EVALUADOS_RANKING, fuera__gte=1)`, con código y nombre en el mismo `values` (1 consulta).
  3. Por tipo de vertido: `values("asignacion__estudio__muestra__tipo_vertido")` (1 consulta); los
     tres tipos se completan en Python con `TipoVertido.choices` (los que faltan, con 0).
  4. Por cliente y por origen: `values("asignacion__estudio__muestra__cliente")` y `...__origen`
     con `fuera__gte=1`; después un `in_bulk` de los 10 primeros con `select_related("cliente")` en
     los orígenes (2 + 2 consultas).
  Total ≈ 7 consultas extra en el dashboard.
- **Motivo**: SC-004; el catálogo tiene decenas de pruebas y los clientes con incumplimientos son
  pocos, así que traer todas las filas agrupadas y ordenar en Python es barato y permite ordenar por
  porcentaje en `Decimal` (FR-015) y contar «cuántas más hay».
- **Alternativas**: ordenar por porcentaje en SQL (división en la base con tipos numéricos y
  redondeo distinto del de Python; habría que repetir la regla de orden); una consulta por cliente
  (N+1).

## R4 – Porcentajes, orden y mínimo del ranking

- **Decisión**: `porcentaje(parte, total)` → `Decimal(parte * 100) / Decimal(total)` con
  `quantize(Decimal("0.1"), ROUND_HALF_UP)`; `None` si `total == 0`. Textos con coma: «20,0 %
  (2 de 10)». Orden:
  - pruebas: `(-porcentaje_completo, -fuera, codigo)`, con el porcentaje sin redondear (fracción
    exacta) para que dos pruebas que redondean igual no empaten artificialmente;
  - clientes y orígenes: `(-fuera, -porcentaje_completo, nombre.casefold(), pk)`.
  Constantes únicas en `calidad.py`: `MINIMO_EVALUADOS_RANKING = 5` y `TOPE_LISTA = 10`. El template
  lee el mínimo del contexto («al menos 5 resultados evaluados»); un test verifica que el número no
  esté escrito en el template ni en otro módulo.
- **Motivo**: FR-006a/007/009/015 y el ajuste del usuario (mínimo 5, «30,0 % (30 de 100)»).
- **Alternativas**: mínimo en `settings` como `AQUALAB_DESVIOS` (no es un parámetro que el
  laboratorio vaya a ajustar por entorno; una constante del módulo alcanza, como
  `DIAS_SIN_AVANZAR`).

## R5 – Variación del porcentaje

- **Decisión**: se reutiliza `tablero.variacion(actual, anterior, favorable_si_sube=False)` sobre
  los porcentajes redondeados (`Decimal`) para obtener diferencia, flecha y tono (subir = peligro).
  El texto se arma en `calidad` como «▲ +5,0 p. p.» (sin el porcentaje relativo, que no tiene
  sentido sobre un porcentaje). Sin evaluados en el anterior → «sin datos previos»; sin evaluados en
  el actual → no se muestra variación.
- **Motivo**: FR-005 con la misma regla de tono de la 8.3; el partial `informes/variacion.html`
  muestra `variacion.texto`, así que `calidad` expone un objeto con `tono` y `texto` y se reutiliza
  el partial sin cambios.
- **Alternativas**: variación relativa («+100 %» al pasar de 5 % a 10 %), confusa.

## R6 – Enlaces

- **Decisión**: cliente activo → `clientes:historial` (pk); origen de cliente activo →
  `estudios:comparacion?cliente=<pk>&origen=<pk>` (sin `pruebas`: la 8.1 muestra todas). Cliente
  inactivo (y sus orígenes): `ui/estado.html` «Inactivo», sin enlace. Nombres actuales
  (`Cliente.nombre_completo`, `Origen.nombre`).
- **Motivo**: FR-010; el historial rechaza clientes inactivos y `ElegirOrigenForm` solo acepta
  orígenes de clientes activos, así que el enlace daría un error.

## R7 – Gráficos

- **Decisión**: dos gráficos más en `informes/static/informes/dashboard.js`, con los datos en el
  mismo `json_script` `datos-dashboard` (claves `calidad_pruebas` y `calidad_vertidos`):
  - ranking de pruebas: barras horizontales (`indexAxis: "y"`) del porcentaje de incumplimiento,
    color `--color-peligro`; eje de 0 al máximo del ranking redondeado a la decena (entre 10 y 100);
  - por tipo de vertido: barras apiladas «Cumple» (`--color-exito`) y «Fuera de norma»
    (`--color-peligro`) por tipo, en cantidades.
  Porcentajes como texto (`"20.0"`) para no pasar por `float` en Python. Cada gráfico con su tabla
  «Ver datos». Sin datos, no se dibuja el canvas y se muestra `ui/estado_vacio.html`.
- **Motivo**: FR-011/013 y la nota técnica (patrón y Chart.js de la 8.3). El color nunca es la única
  señal: la tabla y las etiquetas llevan el número.
- **Alternativas**: torta por vertido (tres tortas, difíciles de comparar); módulo JS aparte (dos
  gráficos más no lo justifican).

## R8 – Ubicación en la pantalla

- **Decisión**: sección «Calidad» (`informes/calidad.html`, incluida desde `dashboard.html`) entre
  los gráficos de la 8.3 y «Comparación histórica»: indicador + variación arriba; ranking de pruebas
  y vertidos lado a lado (`xl:grid-cols-2`); clientes y orígenes lado a lado debajo. Encabezado con
  ayuda (`ui/ayuda.html`) que explica que se cuentan las validaciones vigentes del período y que
  «sin límite comparable» queda afuera.
- **Motivo**: lo que depende del período queda junto, antes de lo que no depende (comparación,
  desvíos, alertas).

## R9 – Datos de demo

- **Decisión**: el guion de la demo (`estudios/demo.py`) **no cambia**. Comprobado con datos
  (2026-11-09): con «Este mes» casi ninguna prueba llega a 5 evaluados (solo pH), así que el ranking
  se verifica con «Últimos 6 meses». `test_calidad_con_la_demo` (en `informes/tests/test_calidad.py`,
  con `ahora` fijo) fija que con `ultimos_6` el ranking tiene al menos 3 pruebas y alguna con
  resultados fuera de norma, y que «Pozo 2» y «Tanque domiciliario» (Cloruro 415 y E. coli
  Presente, validados fuera de norma) aparecen en orígenes. El quickstart usa ese mismo período.
- **Motivo**: la demo tiene ~45 estudios en 6 meses; en un solo mes no alcanza el mínimo, y forzarla
  cambiaría los casos que ya usan la 8.1, 8.2 y 8.3.
- **Alternativas**: agregar estudios al guion (descartado por el usuario).
