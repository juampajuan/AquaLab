# Research: Curva de calibración para pruebas por absorbancia

Decisiones técnicas de la US 6.6 (SCRUM-38). Formato: decisión, motivo y alternativas descartadas.

## R1 – Tipo de cálculo y dónde viven las curvas
- **Decisión**: `TipoCalculo.CURVA = "CURVA", "Curva de calibración"` en `pruebas/models.py`. La
  constraint `prueba_formula_segun_tipo` pasa a «(Directo o Curva) sin fórmula, o Fórmula con
  fórmula»; `Prueba.clean()` rechaza fórmula en una prueba por curva y exige la unidad del resultado.
  Los modelos `CurvaCalibracion` y `PuntoCurva` van en la app `pruebas` (son parte del catálogo);
  `Resultado` (app `estudios`) suma `curva` (FK `PROTECT`, nula).
- **Motivo**: una app por módulo (constitution II): la curva es un dato del catálogo de la prueba,
  como sus límites. `estudios` ya depende de `pruebas`, no al revés.
- **Alternativas**: app nueva `curvas` (agrega una app para dos modelos); guardar la recta en la
  `Prueba` (pierde las históricas y la trazabilidad, FR-013/017).

## R2 – Recta por mínimos cuadrados con `Decimal`
- **Decisión**: `pruebas/curvas.py:ajustar(puntos)` calcula, con `decimal.localcontext(prec=40)`:
  `pendiente = (nΣxy − ΣxΣy) / (nΣx² − (Σx)²)`, `ordenada = (Σy − pendiente·Σx) / n` y
  `R² = (nΣxy − ΣxΣy)² / ((nΣx² − (Σx)²)(nΣy² − (Σy)²))`, con x = concentración e y = absorbancia.
  Guarda pendiente y ordenada redondeadas a 12 decimales y R² a 10 (`ROUND_HALF_UP`); **el resultado
  se calcula con los valores guardados**, así un recálculo da siempre lo mismo. Rechaza (`CurvaInvalida`)
  menos de 3 puntos, todas las concentraciones iguales (denominador 0), todas las absorbancias
  iguales o una pendiente que redondeada da 0. Constante `R2_MINIMO = Decimal("0.995")` solo en
  `curvas.py` (aviso FR-015a; no bloquea).
- **Motivo**: principio IV (nunca `float`) y principio III (casos con valores esperados). La forma
  cerrada de la recta no necesita librerías.
- **Caso de referencia** (spec US2): puntos (0; 0,000), (0,1; 0,052), (0,2; 0,101), (0,3; 0,153),
  (0,4; 0,199) → pendiente 0,499000000000, ordenada 0,001200000000, R² 0,9996025692. Absorbancia
  0,126 → 0,2501002004; 0,250 → 0,4985971944 (calculados aparte con `Decimal`, prec 40).
- **Alternativas**: `statistics.linear_regression` (usa `float`); numpy (dependencia y `float`).

## R3 – Cálculo del resultado y curva usada
- **Decisión**: en `estudios/calculo.py`, `calcular(asignacion, todas, valores, curva=None)` suma la
  rama `CURVA`: `valor = (x − curva.ordenada) / curva.pendiente`. La curva la decide
  `pruebas/curvas.py:curva_para(asignacion, *, bloquear=False)`: la del resultado existente
  (`asignacion.resultado.curva`, FR-020) o, si no tiene, la vigente de la prueba. Sin curva →
  `FaltanDatos("Falta curva de calibración.")`, que `motivo_sin_resultado` ya muestra (FR-018) y que
  `recalcular` no informa como falla. `recalcular` llama a `curva_para(..., bloquear=True)`, pasa la
  curva a `calcular`, la guarda en `Resultado.curva` (`formula` queda vacía) y marca la curva como
  usada (`CurvaCalibracion.usada`, R6).
- **Motivo**: un único punto de cálculo (CLAUDE.md, US 6.2); corrección y recálculo por
  dependencias reutilizan el resultado existente con `update_or_create`, así mantienen la curva sin
  código extra. Borrar la medición (US 6.5) borra el resultado (`descartar`) y la próxima carga toma
  la vigente (US5 Esc. 3). Las fórmulas que nombran una prueba por curva ya usan su resultado (FR-021).
- **Alternativas**: guardar la curva en la `Medicion` (la corrección de US 6.3 la pisaría y no es un
  dato medido).

## R4 – Fuera del rango de la curva
- **Decisión**: no se guarda. `curvas.fuera_de_rango(resultado)` compara la absorbancia medida con
  `absorbancia_min`/`absorbancia_max` de la curva usada (bordes inclusivos = dentro). El detalle del
  estudio y la validación muestran «Fuera del rango de la curva (<conc. mín>–<conc. máx> <unidad>)»
  con el componente de aviso; validar no lo revisa (FR-019).
- **Motivo**: se deduce de datos inalterables (medición + curva usada), como el desvío (US 8.2).

## R5 – Concurrencia y orden de bloqueos
- **Decisión**: un advisory lock por prueba, `pg_advisory_xact_lock(6_600_001, prueba_id)`:
  - `guardar_curva` (exclusivo): si se pidió «Calcularlas con esta curva», primero bloquea con
    `select_for_update` los estudios candidatos (mediciones de la prueba sin resultado en estudios
    que admiten mediciones), **ordenados por pk**; después toma el lock exclusivo y bloquea la
    `Prueba` (revalida tipo `CURVA` y permiso); busca la `clave` (R7); pasa la vigente a histórica,
    crea la curva y sus puntos y, por cada estudio bloqueado, vuelve a consultar sus pendientes de
    esa prueba y llama a `calculo.recalcular(estudio, pendientes)`.
  - `borrar_curva` (exclusivo): bloquea la curva, revalida `usada`, la borra y, si era vigente,
    marca vigente la anterior más reciente (`-fecha_carga`, `-pk`).
  - `curva_para(bloquear=True)` (compartido, `pg_advisory_xact_lock_shared`) antes de leer la
    vigente: lo toman la carga, la corrección y los recálculos, que ya tienen el estudio bloqueado.
- **Orden**: siempre estudio(s) → lock de la prueba. Borrar no toma estudios; las cargas solo toman
  el compartido. No hay ciclos; dos cargas no se bloquean entre sí.
- **Efecto**: una curva no se puede borrar mientras alguien calcula con ella (sin `IntegrityError`
  por la FK); una carga que empezó antes de confirmar una curva nueva calcula con la vigente de ese
  momento y queda registrada. Una medición que llega sin curva entre la lista de candidatos y el lock
  no se calcula en esa operación: sigue esperando (edge case de la spec). `UniqueConstraint`
  (`prueba`, `vigente=True`) es la red de seguridad de FR-014.
- **Alternativas**: `select_for_update` sobre la curva vigente en la carga (deadlock con
  `guardar_curva`, que bloquea la vieja y después los estudios); bloquear la fila de la `Prueba` en
  cada carga (serializa todas las cargas de esa prueba y choca con la gestión del catálogo).

## R6 – Curva usada y borrado
- **Decisión**: `CurvaCalibracion.usada` (booleano, nunca vuelve a `False`) se pone en `True` en
  `recalcular` al guardar un resultado con esa curva (`filter(pk=…, usada=False).update(usada=True)`).
  Una curva usada no se borra aunque su resultado se haya descartado después; `Resultado.curva` es
  `PROTECT` como respaldo. Ninguna curva tiene edición (no hay vista ni operación).
- **Motivo**: «ya se usó en algún resultado» (criterio 6) es un hecho histórico; contar los
  resultados actuales permitiría borrar la curva de una medición borrada.

## R7 – Flujo de pantalla, borrador y doble envío
- **Decisión**: una pantalla (`catalogo:nueva_curva`) con fecha, observación, archivo y un formset
  de puntos (`PuntoFormSet`, mín. 3 filas visibles). Los botones envían `accion`: `agregar_fila`,
  `quitar_<n>`, `importar`, `elegir_columnas`, `calcular` y `guardar` (sin JavaScript para la tabla,
  como la carga de mediciones). `calcular` muestra pendiente, ordenada, R², aviso de R² y el gráfico;
  `guardar` revalida, calcula y guarda un borrador firmado (mismo esquema que
  `pruebas/confirmaciones.py`, operación `curva`) con una `clave` UUID; la confirmación hace POST a
  `catalogo:confirmar_curva`. `CurvaCalibracion.clave` es `unique`: bajo el lock, si ya existe una
  curva con esa clave se devuelve esa (reenvío o doble clic), como el N° PI de muestras. Cancelar
  vuelve a la pantalla con los puntos del borrador.
- **Motivo**: patrón de confirmación del proyecto (constitution UI) y protección contra doble envío
  ya probada (US 4.1).
- **Alternativas**: tabla editable en JS (más código y tests de JS para algo que el formset resuelve).

## R8 – Lectura de archivos (.csv y .xlsx)
- **Decisión**: `pruebas/importacion_curvas.py:leer_archivo(archivo)` devuelve una tabla (lista de
  filas de textos) o `ArchivoInvalido(motivo)`; `extraer_puntos(tabla, columnas=None)` devuelve los
  puntos o `ArchivoInvalido`. Reglas:
  - Extensión `.csv` o `.xlsx` (otra → «Solo se aceptan archivos .csv o .xlsx.»); tamaño ≤ 1 MB;
    hasta 1000 filas leídas y 50 puntos.
  - CSV: UTF-8 (con o sin BOM) y, si falla, Latin-1; separador detectado con `csv.Sniffer` entre
    `;`, `,` y tabulador (por defecto `;`).
  - XLSX: `openpyxl.load_workbook(read_only=True, data_only=True)`, primera hoja; un número de celda
    (`int`/`float`) pasa a `Decimal(repr(valor))` redondeado a 6 decimales (`ROUND_HALF_UP`) y se
    escribe como texto. Es el único `float` de la historia: lo entrega la librería y se convierte
    antes de cualquier cálculo (principio IV).
  - Columnas: la primera fila con una celda que, sin tildes ni mayúsculas, empieza por «conc» y
    otra por «abs» define la columna de concentración y la de absorbancia. Si no hay una fila así,
    o hay más de una columna candidata para alguna, se pide elegir (`ElegirColumnasForm`, con una
    vista previa de las primeras 5 filas); la tabla leída queda en el borrador de la sesión.
  - Filas: cada valor se lee con `estudios.mediciones.leer_valor`; una fila sin ningún número en
    las dos columnas se ignora (títulos, vacías, textos); con un solo número es error «La fila N no
    tiene absorbancia» / «… no tiene concentración» (N = número de fila del archivo). Un valor
    negativo o inválido también es error de esa fila. Cualquier error → no se carga ningún punto.
  - Menos de 3 puntos válidos → «El archivo trae N puntos válidos: hacen falta al menos 3.»
  - El nombre del archivo (sin ruta, máx. 255) viaja en el borrador y se guarda en
    `archivo_origen`; los puntos editados después en la tabla mantienen ese nombre (US3 Esc. 9).
  - El archivo no se guarda en disco ni en la base (solo su nombre).
- **Plantilla**: `catalogo:plantilla_curva` devuelve un CSV UTF-8 con BOM, separador `;` y coma
  decimal (abre bien en Excel en español): encabezado `Concentración;Absorbancia` y los 5 puntos del
  caso de referencia.
- **Motivo**: FR-006 a FR-010; `leer_valor` es la única lectura de números escritos (CLAUDE.md).

## R9 – Dependencia nueva: `openpyxl==3.1.5`
- **Decisión**: agregar `openpyxl==3.1.5` (y su única dependencia, `et-xmlfile==2.0.0`, fijada) a
  `requirements.txt`, solo para leer `.xlsx`.
- **Justificación (constitution II)**: el criterio 3 exige Excel y la biblioteca estándar no lee
  `.xlsx`. `openpyxl` es Python puro (sin librerías de sistema: no toca el `Dockerfile` ni el CI),
  es la librería de referencia para `.xlsx`, tiene licencia MIT y se usa en modo solo lectura.
  Riesgos y mitigación: archivos maliciosos o enormes → límite de 1 MB antes de abrirlo,
  `read_only=True`, se leen como máximo 1000 filas, y cualquier excepción al abrir se informa como
  «No se pudo leer el archivo.».
- **Alternativas**: pandas (pesada, `float` y numpy); leer el XML del `.xlsx` a mano con `zipfile`
  (frágil: estilos, celdas compartidas, fechas); aceptar solo CSV (incumple el criterio 3).
  Requiere acuerdo del equipo: se avisa en el PR.

## R10 – Mediciones que esperan curva (aclaración 1)
- **Decisión**: `curvas.pendientes_de_curva(prueba)` devuelve las asignaciones de la prueba con
  medición y sin resultado en estudios que admiten mediciones (`Estudio.admite_mediciones`: los que
  tienen informe o están Finalizados no pueden tener una prueba sin resultado). La confirmación
  muestra «N mediciones en M estudios esperan curva» y la casilla «Calcularlas con esta curva»
  (desmarcada). Con la casilla, `guardar_curva` las calcula en la misma transacción con
  `calculo.recalcular` (que pasa el estudio a «En proceso» si hace falta, como cualquier cálculo,
  y avisa desvíos US 8.2). El mensaje dice cuántas se calcularon.
- **Motivo**: un solo lugar de cálculo; misma transacción para que «calculadas» sea exacto.

## R11 – Acceso y pantallas
- **Decisión**: carga, importación, plantilla, confirmación y borrado bajo `catalogo:`
  (`/administracion/pruebas/<pk>/curvas/...`) con `administracion_requerida`; los servicios
  revalidan con `pruebas.gestion.autorizar` (FR-023). Consulta de solo lectura para cualquier
  empleado con sesión en el namespace nuevo `curvas:` (`/pruebas/<pk>/curvas/` y
  `/pruebas/curvas/<pk>/`, `require_GET`), que enlaza el detalle del estudio (FR-024). La ficha de
  gestión suma la sección «Curvas de calibración» (vigente, «Nueva curva», enlace a la consulta).
- **Gráfico**: Chart.js 4.4.7 ya vendorizado (`static/vendor/chart.umd.min.js`), cargado solo en la
  pantalla de carga y en el detalle de la curva. `pruebas/static/pruebas/curva.js` lee un
  `json_script` con los puntos y los extremos de la recta (calculados en el servidor, como textos) y
  dibuja puntos + recta. La tabla de puntos sirve de «Ver datos». Sus funciones puras se prueban con
  `node --test pruebas/tests/js` (se suma al comando del CI).

## R12 – Cambios de tipo de cálculo con curvas cargadas
- **Decisión**: una prueba sin uso que ya tiene curvas no puede pasar de «Curva de calibración» a
  otro tipo: `gestionar_prueba` lo rechaza con «Tiene curvas de calibración cargadas: borralas antes
  de cambiar el tipo de cálculo.». Eliminar una prueba sin uso borra sus curvas
  (`CurvaCalibracion.prueba` es `CASCADE`): sin uso no hay resultados, así que ninguna está usada.
- **Motivo**: evita curvas huérfanas sin borrar datos en silencio. Edge case agregado a la spec.

## R13 – Lo que no cambia
- El informe emitido, el PDF y el correo no muestran la curva (fuera de alcance); `armar_contenido`
  no se toca. Las validaciones no guardan la curva (ya está en el resultado).
- `importar_catalogo_pruebas` acepta `CURVA` como tipo (lo valida `Prueba.clean()`); no carga curvas.
- La demo (`cargar_demo`) no suma pruebas por curva: el quickstart crea las suyas.
