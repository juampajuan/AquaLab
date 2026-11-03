# Contrato de interfaz: Consultar y exportar informe

**Feature**: `022-consultar-exportar-informe` | **Plan**: [plan.md](../plan.md)

Todas las rutas requieren sesión (`LoginRequiredMiddleware`; sin sesión → 302 al login) y los POST
llevan CSRF. Prefijo `informes/`. Estudio sin informe o inexistente → **404**.

## Menú

- `ui/menu.html`, sección **Informes**: se agrega **Informes emitidos** (`informes:emitidos`),
  activo también en `informes:ver`. «Seleccionar estudio» (US 7.1) queda igual.
- Barra superior (`base.html`), junto al nombre del usuario: enlace **Mi firma** (ícono
  `pen-line`) solo con `perms.informes.emitir_informes`.

## `GET /informes/emitidos/` — `informes:emitidos`

- Cualquier empleado con sesión. Parámetros: `q`, `desde`, `hasta`, `page`.
- Formulario: búsqueda («N° de informe, cliente, documento o N° PI»), fecha desde, fecha hasta,
  **Buscar** y **Limpiar**.
- Tabla, del más reciente al más antiguo: **Informe** (`INF-000001`), **Emisión** (`d/m/Y H:i`),
  **Cliente** (`contenido.cliente.nombre_completo` y documento), **N° PI**, **Estudio** (número y
  tipo), **Emitido por** (`contenido.firma.nombre` o el usuario), acción **Ver** → `informes:ver`.
- Paginación con `ui/paginacion.html`, conservando `q`, `desde` y `hasta`.
- Vacío sin filtros: «Todavía no hay informes emitidos.»; con filtros: «No hay informes que
  coincidan con la búsqueda.» (`ui/estado_vacio.html`).
- Formulario inválido (fecha mal escrita o rango invertido): 200 con el error en el campo y sin
  tabla.

## `GET /informes/estudios/<pk>/informe/` — `informes:ver` (cambio de la US 7.2)

- El documento de pantalla (`informes/documento.html`) desde `informe.contenido`, ahora con el
  bloque de firma (`informes/firma.html`): imagen, nombre y «Mat. <matrícula>», o «Sin firma
  registrada».
- Acciones: **Descargar PDF** (`btn btn-primario`, ícono `download`) → `informes:pdf`;
  **Imprimir** (`btn btn-secundario`, ícono `printer`, `target="_blank"`) → `informes:imprimir`;
  **Volver a informes emitidos**; **Ver detalle del estudio**. Se mantiene «Volver al control».

## `GET /informes/estudios/<pk>/informe/pdf/` — `informes:pdf`

- 200 `application/pdf`, `Content-Disposition: attachment; filename="INF-000001.pdf"`.
- Hoja A4 desde `informes/impreso.html` + `static/css/informe.css`, siempre con `informe.contenido`.
- Error de WeasyPrint → 302 a `informes:ver` + «No se pudo generar el PDF. Intentá nuevamente.» y
  el error queda en el log `informes`.

## `GET /informes/estudios/<pk>/informe/imprimir/` — `informes:imprimir`

- 200 `informes/impreso.html` (documento HTML independiente, sin `base.html`): barra de pantalla
  **Imprimir** / **Volver al informe** (oculta al imprimir) y el documento A4. `informes/imprimir.js`
  abre el diálogo de impresión al cargar.

## Documento impreso — `informes/documento_impreso.html` (parcial)

Mismos datos y orden que `informes/documento.html` (contrato de la US 7.2), con clases `inf-*`:

1. **Membrete**: logo («aqualab» → marca AquaLab en SVG), nombre, dirección, matrícula del
   laboratorio; a la derecha «Informe N° INF-000001» (`string-set` para el pie) y la fecha.
2. **Cliente**, **Muestra**, **Estudio**: pares rótulo/valor en tablas de dos columnas; vacíos «—».
3. **Resultados**: Prueba (nombre y código), Resultado, Unidad, Límite (y origen si no es general),
   Norma, Cumple; fuera de norma con fondo resaltado y texto «Fuera de norma» (no depende solo del
   color). Encabezado repetido en cada hoja; ninguna fila partida.
4. **Pie del documento**: «Responsable técnico: …», bloque de firma (`informes/firma.html`) y
   «Emitido el d/m/Y H:i».
5. **Pie de cada hoja** (`@page`): «INF-000001 · Página N de M».

## `GET|POST /informes/mi-firma/` — `informes:mi_firma`

- Sin `informes.emitir_informes` → **403** (`@permission_required(raise_exception=True)`).
- GET: encabezado «Mi firma»; si tiene firma, la actual y la matrícula; canvas 600 × 200 con borde
  punteado y el texto de ayuda «Firmá con el mouse o con el dedo»; botón **Borrar**; campo
  **Matrícula** (ej. «MP 1234»); **Guardar firma** (`btn btn-primario`).
- POST válido → 302 a `informes:mi_firma` + «Se guardó tu firma.».
- POST inválido → 200 con los errores (`ui/errores_form.html`); la firma guardada no cambia.

## `GET /informes/estudios/<pk>/vista-previa/` — cambio de la US 7.2

- El documento muestra el bloque de firma con la firma de `request.user` (si la tiene).
- Con permiso y **sin** firma: en lugar de **Emitir informe**, aviso de advertencia «Para emitir
  necesitás cargar tu firma y matrícula.» con enlace **Cargar mi firma** → `informes:mi_firma`.

## `POST /informes/estudios/<pk>/generar/` — cambio de la US 7.2

- Sin firma: `EmitirInformeError` → 302 a `informes:control` + «Cargá tu firma y matrícula en «Mi
  firma» antes de emitir.»; no se emite nada.
