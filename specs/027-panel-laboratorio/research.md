# Research: Panel del laboratorio

Decisiones técnicas de la US 8.3. Formato: decisión, motivo y alternativas descartadas.

## R1 – App, URL y permiso

- **Decisión**: el panel vive en la app `informes`: URL `informes:dashboard` (`/informes/dashboard/`),
  permiso `ver_dashboard` («Puede ver el dashboard») en `Informe.Meta.permissions`, y la migración
  `informes.0004_permiso_dashboard` lo asigna a «Bioquímicos» y «Administradores» con el patrón de
  `informes.0002` (`create_permissions` + `models_module`). Depende de `estudios.0008` y
  `usuarios.0004`.
- **Motivo**: la constitution fija una app por módulo (`usuarios`, `clientes`, `muestras`,
  `estudios`, `pruebas`, `informes`, `comparacion`); el dashboard resume el trabajo hasta el informe
  y `comparacion` queda para 8.1/8.2. Un permiso propio (aclarado antes de la spec) permite darlo a
  otros sin meterlos en un grupo.
- **Alternativas**: app nueva `tablero` (requiere enmendar la constitution); revisar pertenencia a
  grupos en la vista (duplica la lógica del panel 025 y no se puede asignar a una persona).

## R2 – Períodos

- **Decisión**: `tablero.periodo(clave, hoy)` devuelve `(inicio, fin, inicio_anterior,
  fin_anterior)` como fechas locales inclusivas:
  - `este_mes`: del 1 a hoy; anterior: del 1 del mes previo al mismo día (o su último día).
  - `mes_anterior`: el mes previo completo; anterior: el mes anterior a ese, completo.
  - `ultimos_3` / `ultimos_6`: del 1 del mes de hace 2 (o 5) meses a hoy; anterior: el mismo tramo
    corrido 3 (o 6) meses hacia atrás, con el día recortado al último del mes.
  Clave inválida → `este_mes`.
- **Motivo**: FR-004/006 y la aclaración «mismos días del mes anterior». Funciones puras, fáciles
  de probar con fechas fijas.
- **Alternativas**: ventanas móviles de 30/90 días (no coinciden con «mes» del laboratorio).

## R3 – Conteos del período

- **Decisión**: muestras por `fecha_ingreso` (fecha), estudios por `fecha_creacion` e informes por
  `fecha_emision` convertidas a fecha local con `TruncDate(..., tzinfo=zona del laboratorio)`; un
  `aggregate(Count(filter=...))` por modelo para período y anterior a la vez (3 consultas).
- **Motivo**: FR-005/016; una consulta por modelo mantiene el panel rápido (SC-004).

## R4 – Variación

- **Decisión**: `variacion(actual, anterior, favorable_si_sube=True)` → `diferencia`, `porcentaje`
  (redondeado a entero; `None` si anterior es 0 → «sin datos previos»), `sentido`
  (`sube`/`baja`/`igual`, con «▲», «▼», «=») y `tono` (`exito`, `peligro`, `neutro`). El tiempo de
  respuesta usa `favorable_si_sube=False`.
- **Motivo**: FR-006/006a; el tono sale de una sola regla y el template solo lo pinta, siempre con
  flecha y signo.

## R5 – Tiempo de respuesta y serie mensual

- **Decisión**: días corridos = fecha local de emisión − `muestra.fecha_ingreso`. Se calcula en la
  base (`TruncDate` − fecha, en PostgreSQL da días enteros) y se promedia con `Avg`, redondeado a un
  decimal con `Decimal` (sin `float`). La serie de 6 meses agrupa por `TruncMonth(fecha_emision,
  tzinfo)` en una consulta; los meses sin informes quedan `None`.
- **Motivo**: FR-007/008 y aclaración «por fecha de emisión, días corridos». Mismo cálculo para el
  período y para cada mes.

## R6 – Serie semanal

- **Decisión**: 12 semanas de lunes a domingo, desde el lunes de hace 11 semanas hasta el domingo
  de la semana actual; dos consultas agrupadas por `TruncWeek` (muestras por `fecha_ingreso`,
  informes por fecha local de emisión). Etiqueta de cada semana: «dd/mm» del lunes.
- **Motivo**: FR-010/011; `TruncWeek` de PostgreSQL empieza el lunes (ISO).

## R7 – Alertas

- **Decisión**:
  - **Última actividad** = `Greatest(fecha_creacion, Subquery(Max(fecha_carga)),
    Subquery(Max(fecha_correccion)), Subquery(Max(fecha_validacion)))` sobre las pruebas del
    estudio (PostgreSQL ignora los `NULL` en `GREATEST`). «Sin avanzar»: estado Pendiente de
    análisis o En proceso y última actividad anterior a `ahora − 7 días`. Días = días locales
    completos desde la última actividad.
  - **Finalizados sin informe**: estado Finalizado y sin `Informe`; días desde la última
    `Validacion` vigente.
  - Ambas con `select_related("muestra__cliente")`, ordenadas de la más antigua a la más reciente,
    todas (aclaración 2), en una lista con desplazamiento.
- **Motivo**: FR-013/014/015 y la aclaración previa «última actividad = creación o carga,
  corrección o validación». Dos consultas, sin N+1.
- **Alternativas**: un campo «última actividad» en `Estudio` (migración y mantenerlo en cada
  servicio; YAGNI mientras la consulta alcance).

## R8 – Gráficos

- **Decisión**: Chart.js 4.4.7 UMD (`chart.umd.min.js`, MIT, con su cabecera de licencia) en
  `static/vendor/`, cargado solo en el dashboard. Los datos van en `{{ datos|json_script:"datos-dashboard" }}`
  y `informes/static/informes/dashboard.js` dibuja una línea (tiempo de respuesta, 6 meses) y barras
  agrupadas (muestras e informes, 12 semanas) con los colores del tema. Cada gráfico tiene una tabla
  equivalente debajo (`<details>` «Ver datos»), y el `<canvas>` lleva `role="img"` y `aria-label`.
- **Motivo**: criterio 7 y FR-012/017; sin CDN y legible sin JavaScript.
- **Alternativas**: SVG generado en el servidor (más código propio); CDN (lo prohíbe el criterio).

## R9 – Menú e ícono

- **Decisión**: enlace propio en `templates/ui/menu.html` debajo de «Inicio» dentro de
  `{% if perms.informes.ver_dashboard %}`, resaltado con `vista == 'informes:dashboard'`, con el
  ícono `chart-column` de Lucide (se agrega a `templates/ui/iconos/`, misma licencia ISC).
- **Motivo**: aclaración 1; mismo patrón que los demás enlaces del menú.
