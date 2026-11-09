# Research: Comparación histórica por origen (SCRUM-60, US 8.1)

## R1. Dónde vive el cálculo

- **Decision**: módulo nuevo `estudios/comparacion.py`, puro (sin `request` ni templates), con
  `comparar(origen, *, estudio=None, codigos=None)` → lista de `HistorialPrueba` y
  `variacion(ultimo, anteriores, *, presencia)` → `Variacion`. Es la única definición del
  historial y de la variación (FR-019); la US 8.2 la llama con un estudio de referencia.
- **Rationale**: `Resultado` y `Validacion` son de `estudios`; `informes` depende de `estudios` y
  no al revés, así el Dashboard puede usarlo sin ciclos. Mismo patrón que `informes/tablero.py`
  (cálculo puro, vista delgada).
- **Alternatives**: en `informes/tablero.py` (rechazado: 8.1 se abre desde el estudio y la 8.2 no
  es del tablero); en `muestras` (rechazado: tendría que importar `estudios`, que ya importa
  `muestras`); métodos en `Origen` (rechazado: modelo de `muestras` dependiendo de `estudios`,
  como evita la US 3.3 con `clientes/historial.py`).

## R2. Qué es un resultado «validado» y cómo se consulta

- **Decision**: historial = `Resultado` cuya asignación está `Completada`, de muestras con
  `origen = X`, de las pruebas pedidas, excluido el estudio de referencia, con
  `select_related("asignacion__estudio__muestra", "asignacion__prueba")` y el `Prefetch` de la
  validación vigente (`views.validaciones_vigentes()`, movido a un lugar común si hace falta).
  Una sola consulta para todas las pruebas del origen más la del estudio de referencia; se agrupa
  por código en Python.
- **Rationale**: por el invariante de la US 6.4, «Completada» ⇔ hay `Validacion` vigente; filtrar
  por estado evita un `EXISTS` y las validaciones anuladas quedan fuera solas (Edge Case). La
  cantidad de consultas es fija (SC-005).
- **Alternatives**: `validaciones__anulada=False` en el filtro (equivalente, con JOIN y riesgo de
  duplicados); una consulta por prueba (N+1).

## R3. Orden, «anteriores» y el «último»

- **Decision**: orden por `(muestra.fecha_muestreo, muestra.numero_pi, estudio.pk)`. El «último»
  es el resultado del estudio de referencia (validado o no) o, sin referencia, el validado más
  reciente según ese orden. «Anteriores» = puntos del historial cuya muestra es anterior a la del
  último: `(fecha_muestreo, numero_pi) < (fecha_ref, numero_pi_ref)`. Los de la misma muestra
  (otros estudios) y los posteriores se dibujan pero no entran a la variación.
- **Rationale**: Edge Cases de la spec; el N° PI es correlativo y desempata la misma fecha.
- **Alternatives**: comparar por fecha de ingreso o de validación (rechazado: el criterio 2 pide
  fecha de muestreo).

## R4. Aritmética de la variación

- **Decision**: todo con `Decimal` sobre `Resultado.valor` completo (FR-011).
  `promedio = sum(anteriores) / len(anteriores)` en un `localcontext(prec=28)`;
  `dif = ultimo - referencia`; `pct = dif / referencia * 100` cuantizado a `0.1`
  `ROUND_HALF_UP`; con `referencia == 0` → `pct = None` («sin porcentaje (valor previo 0)»).
  Para mostrar, diferencias y promedio con la regla de `Resultado.valor_mostrado` (hasta 4
  decimales, sin ceros finales), coma decimal y signo explícito; flecha ▲/▼/= según el signo.
  Sin tono favorable/desfavorable: el color solo marca «fuera de la franja» (FR-016).
- **Rationale**: principio IV y la regla de presentación existente. `informes.tablero.variacion`
  trabaja con enteros, decide un tono «favorable» y está en `informes`; no aplica.
- **Alternatives**: reutilizar `tablero.variacion` (rechazado por lo anterior); `float` en el
  servidor (prohibido).

## R5. Pruebas Ausente/Presente

- **Decision**: se reconocen con `es_presencia(unidad)` (`estudios/mediciones.py`).
  `Variacion` de presencia: `cambio` (`None` si igual) con los textos «Sin cambios (Ausente)» /
  «Cambió: Ausente → Presente», y `presentes`/`total` entre los anteriores («Presente en 1 de 6»).
  En el gráfico el eje Y tiene dos marcas, 0 = «Ausente» y 1 = «Presente», y la franja permitida
  es la banda alrededor de 0 cuando el límite es «Ausente»/«Ausencia».
- **Rationale**: FR-010 y la nota de CLAUDE.md (nunca mostrar 0/1).

## R6. Límites y franja

- **Decision**: la franja usa `limites_aplicables(prueba, muestra_ref.tipo_vertido)` de
  `pruebas/limites.py` y `leer_limite` para cada borde. Muestra de referencia: la del estudio o, sin
  estudio, la del último validado. El servidor manda al JS `{"min": "…"|null, "max": "…"|null,
  "presencia": bool, "texto": "…", "origen": "general"|vertido}`; `NO_COMPARABLE` en un borde →
  sin franja y «Sin límite comparable» (la regla de `evaluar`). La evaluación de cada punto en
  la tabla es la de su validación vigente; la del punto de referencia sin validar, `evaluar` con los
  límites del catálogo (como `evaluar_asignaciones`).
- **Rationale**: `pruebas/limites.py` es la única interpretación de límites (CLAUDE.md, US 6.4).
- **Alternatives**: franja por punto según su vertido (rechazado: ilegible; el vertido de un mismo
  origen casi nunca cambia, y la tabla muestra la evaluación real de cada punto).

## R7. Dibujo con Chart.js 4.4.7 sin plugins

- **Decision**: `estudios/static/estudios/comparacion.js`, mismo patrón que
  `informes/static/informes/dashboard.js`: lee `json_script` `datos-comparacion`, un
  `<canvas data-prueba="CODIGO">` por prueba, colores de los tokens CSS. Gráfico `line` con eje X de
  categorías (etiqueta «dd/mm/aaaa · PI 200123», en orden) y datasets:
  1. «Validados» (línea, `spanGaps: true`, `null` en la posición del de referencia);
  2. «Este estudio» (solo su índice; `pointStyle: "rectRot"`, radio mayor, color `cian`,
     etiqueta «Sin validar»/«Validado» en la leyenda y el tooltip);
  3. franja: dos datasets constantes sin puntos (`min` y `max`) con `fill: "-1"`; con solo máximo,
     `fill: "start"`; con solo mínimo, `fill: "end"`; en presencia, ±0,25 alrededor de 0.
  Tooltip: fecha, N° PI, valor con unidad (texto ya armado en el servidor: «< LD»,
  «Ausente»), validado o no. La lógica de armar datasets queda en funciones puras expuestas para
  `node --test` (`estudios/tests/js/comparacion.test.cjs`), sin DOM real.
- **Rationale**: criterio y nota técnica (reutilizar Chart.js de `static/vendor` y el patrón de la
  8.3); la escala de tiempo exige un adaptador de fechas que no está vendorizado, y el plugin de
  anotaciones sería otra dependencia. Las categorías ordenadas alcanzan: el criterio pide orden por
  fecha, no espaciado proporcional.
- **Alternatives**: `chartjs-plugin-annotation` + adaptador de fechas (dos dependencias nuevas, la
  constitution pide mínimas).

## R8. Pantalla, URL y parámetros

- **Decision**: una vista `estudios:comparacion` en `GET /estudios/comparacion/`:
  - `?estudio=<pk>`: el origen es el de la muestra del estudio (404 si no existe).
  - `?cliente=<pk>&origen=<pk>`: desde el Dashboard (sin referencia). Lo valida
    `ElegirOrigenForm` (cliente activo, origen del cliente); inválido o incompleto → la misma
    pantalla muestra solo el selector con los errores (paso 2 sin JS: elegido el cliente, el select
    de orígenes trae solo los suyos).
  - `pruebas=<código>` repetible + `elegir=1` (marca que el usuario aplicó la selección; sin él, por
    defecto todas). Lo valida `ElegirPruebasForm` (`MultipleChoiceField` con
    `CheckboxSelectMultiple`, opciones = FR-013); códigos desconocidos se ignoran.
  - `@permission_required("informes.ver_dashboard", raise_exception=True)` + `@require_GET`.
- **Rationale**: GET hace que el enlace conserve la selección (US 3, escenario 4) y que sea de solo
  lectura (FR-016). Una sola vista para los dos accesos evita duplicar.
- **Alternatives**: `/estudios/origenes/<pk>/comparacion/` (un form GET no arma el path sin JS);
  un permiso nuevo (la spec decide el del Dashboard).

## R9. Selector del Dashboard

- **Decision**: `informes/dashboard.html` suma una tarjeta «Comparación histórica» con
  `ElegirOrigenForm` (`action` = `estudios:comparacion`, GET) por `ui/campo.html`, con
  `help_text`. Los orígenes de cada cliente activo van en un `json_script` (patrón de
  `muestras/static/muestras/registro_muestra.js`) y `estudios/static/estudios/elegir_origen.js`
  deja en el `<select>` de orígenes solo los del cliente elegido. Sin JS el `<select>` trae todos
  los orígenes agrupados por cliente (`<optgroup>`) y `clean()` rechaza uno de otro cliente; si se
  envía solo el cliente, la pantalla de comparación ofrece el segundo paso con sus orígenes.
- **Rationale**: FR-015, sin endpoints JSON nuevos; consistente con la US 4.1.

## R10. Acceso desde el detalle del estudio

- **Decision**: botón secundario «Comparación histórica» en `estudios/detalle.html`, visible con
  `perms.informes.ver_dashboard`, enlazando `estudios:comparacion?estudio=<pk>`. No se agrega nada a
  `informes/documento.html`, `impreso.html` ni a `informes/correos/` (FR-017; un test lo verifica).

## R11. Datos de demo (pedido del usuario: caso Ausente/Presente)

- **Decision**: **no hace falta tocar el guion**. La demo ya tiene un origen con una prueba
  Ausente/Presente que cambia de estado: «Tanque domiciliario» (María González), E. Coli Ausente
  en los meses 5 y 4, **Presente en el mes 3** (`ESPECIALES[("tanque-domiciliario", 3, "ECOLI")]`) y
  Ausente en los meses 2 y 1, todos con informe emitido (validados); el mes 0 está Pendiente.
  - Abriendo la comparación desde el estudio del mes 3: «Cambió: Ausente → Presente», «Presente en
    0 de 2».
  - Desde el Dashboard (último = mes 1): «Sin cambios (Ausente)», «Presente en 1 de 4», y el punto
    Presente se ve en el gráfico.
  Se agrega un test en `estudios/tests/test_comparacion_demo.py` que fija ese caso, así un cambio
  futuro del guion que lo rompa falla (y entonces se agregaría al guion, como pide CLAUDE.md).
- **Rationale**: la condición del pedido («si la demo no tiene…») no se cumple; cambiar el guion
  movería números que verifican las US 8.3 y 7.x (`test_demo.py`).
- **Alternatives**: agregar un caso Ausente→Presente sin validar en el mes 0 (posible a futuro si la
  US 8.2 lo necesita para desvíos de presencia).

## R12. Caso integral de Cloruro (Pozo 2)

Mediciones 11,8 / 12,1 / 12,4 / 12,0 (meses 5–2) → resultados 118, 121, 124, 120 mg/l; mes 1:
415 validado; mes 0: 430 sin validar (Cloruro = `x*10`, máximo 350 mg/l). Desde el estudio del
mes 0: contra el anterior +15 mg/l (+3,6 %); promedio de los 5 anteriores 179,6 → +250,4 mg/l
(+139,4 %); 415 y 430 por encima de la franja. Desde el Dashboard (último = 415): contra el
anterior +295 mg/l (+245,8 %), promedio 120,75 → +294,25 mg/l (+243,7 %).
