# Research: Consultar y exportar informe

**Feature**: `022-consultar-exportar-informe` | **Plan**: [plan.md](./plan.md)

## R1 — Generación del PDF: WeasyPrint 70.0

- **Decision**: `weasyprint==70.0` (última, 2026-09-08) fijada en `requirements.txt`. Es la única
  dependencia nueva; la constitution ya la prevé para los informes en PDF. Trae como dependencias
  transitivas pydyf, tinycss2, cssselect2, tinyhtml5, Pyphen, Pillow y fonttools; no se usan
  directamente.
- **Librerías del sistema**: `libpango-1.0-0`, `libpangoft2-1.0-0`, `libharfbuzz-subset0` (WeasyPrint
  ≥ 61 las carga por cffi) y `fonts-dejavu-core` como fuente de respaldo para fontconfig. En el
  `Dockerfile` (`python:3.12-slim`, Debian) con `apt-get install --no-install-recommends` y limpieza
  de `/var/lib/apt/lists`; en el job de CI (`ubuntu-latest`) con `sudo apt-get install -y` antes de
  `pip install`. Los mismos paquetes en los dos lugares, con un comentario que lo recuerda.
- **Verificación en CI**: un paso `python -c "import weasyprint; weasyprint.HTML(string='<p>ok</p>').write_pdf()"`
  antes de pytest, para que una librería faltante falle con un mensaje claro; después, los tests de
  `informes/tests/test_pdf.py` generan PDF reales.
- **Rationale**: genera el PDF en el servidor desde HTML y CSS (los mismos templates de Django), con
  soporte de `@page`, márgenes A4, contadores de página y `break-inside`, que es lo que pide la
  historia. Sin navegador headless.
- **Alternatives considered**: ReportLab (dibujar el documento a mano, duplica el template);
  xhtml2pdf (CSS muy limitado, sin `@page` con cajas de margen); Chrome headless/Playwright (proceso
  y binario enormes en la imagen y en Render).

## R2 — Una hoja de estilos propia para PDF e impresión

- **Decision**: `static/css/informe.css`, escrita a mano (no pasa por Tailwind ni por el paso «CSS
  compilado al día» del CI). La usan el PDF (WeasyPrint) y la página de impresión del navegador.
  Contenido:
  - `@page { size: A4; margin: 18mm 15mm 20mm; }` y caja de margen
    `@bottom-center { content: string(numero) " · Página " counter(page) " de " counter(pages); }`;
    `string-set: numero content()` en el número del informe del membrete, así cada hoja lleva
    «INF-000001 · Página 1 de 2».
  - Membrete al inicio del documento (logo, nombre, dirección, matrícula; número y fecha a la
    derecha) y pie con la firma.
  - Tabla de resultados con `thead { display: table-header-group }` (se repite el encabezado en cada
    hoja), `tr { break-inside: avoid }`, y la firma con `break-inside: avoid`.
  - Solo CSS 2.1 + Paged Media: tabla y bloques (sin grid, sin variables CSS ni `oklch` que usa el
    tema de Tailwind), colores en hex con los mismos valores de la paleta de SCRUM-67.
  - Fuente Inter desde `static/fuentes/InterVariable.woff2` con `@font-face` relativo
    (`url("../fuentes/InterVariable.woff2")`), que resuelven igual el navegador y WeasyPrint.
  - `@media screen`: la página de impresión se ve como una hoja centrada con la barra «Imprimir ·
    Volver»; `@media print` oculta esa barra.
- **Rationale**: WeasyPrint no soporta todo el CSS de Tailwind 4 (capas, variables anidadas,
  `oklch`, grid complejo); una hoja chica y explícita es predecible en los dos motores. Chrome ≥ 131
  y WeasyPrint soportan las cajas de margen de `@page`; en navegadores sin soporte (Firefox) la
  impresión sale sin el pie repetido pero con todo el contenido.
- **Alternatives considered**: generar el PDF desde la pantalla con Tailwind (falla de estilos en
  WeasyPrint); `position: running()` para repetir el membrete completo en cada hoja (solo lo soporta
  WeasyPrint; la impresión del navegador no coincidiría).

## R3 — Un template impreso compartido por PDF e impresión

- **Decision**: nuevo `informes/templates/informes/impreso.html`: documento HTML completo que
  incluye el parcial nuevo `informes/documento_impreso.html` (clases semánticas `inf-*` de
  `informe.css`). El mismo render sirve:
  - **PDF**: `render_to_string("informes/impreso.html", {..., "pdf": True})` →
    `weasyprint.HTML(string=..., base_url=...)` con `stylesheets=[CSS(filename=finders.find("css/informe.css"))]`;
    con `pdf=True` el template no pone el `<link>` ni la barra de acciones.
  - **Imprimir**: `informes:imprimir` devuelve ese HTML con `<link>` a `{% static 'css/informe.css' %}`
    y `informes/imprimir.js`, que llama a `window.print()` al cargar; se abre en otra pestaña desde
    «Imprimir».
- **Reutilización**: el contenido sale siempre de `Informe.contenido` (la copia de la US 7.2,
  `armar_contenido`, con «< LD», Ausente/Presente, límites y evaluación ya resueltos como texto).
  La pantalla sigue usando `informes/documento.html` (Tailwind); los dos parciales leen las mismas
  claves y comparten el parcial nuevo de la firma, `informes/firma.html`.
- **Fidelidad (SC-002)**: un test recorre todas las hojas de `contenido` (laboratorio, cliente,
  muestra, estudio, cada prueba y la firma) y verifica que cada valor aparece en el render de
  pantalla y en el impreso; otro verifica que el PDF sale de `impreso.html` con el mismo contexto.
- **Alternatives considered**: un único parcial con clases Tailwind y `informe.css` a la vez
  (acopla las dos hojas, y cada cambio de Tailwind arriesga el PDF); imprimir la pantalla con
  `@media print` sobre `base.html` (no coincidiría con el PDF).

## R4 — La firma en la base como PNG chico

- **Decision**: modelo `FirmaProfesional` (app `informes`): uno a uno con el usuario, `imagen`
  `BinaryField` con los bytes del PNG, `matricula` (texto, 40), `actualizada`. No se usa
  `ImageField`/`MEDIA_ROOT`: Render borra el disco en cada deploy.
- **Validación en el servidor** (`informes/firmas.py:leer_firma`, la única lectura): recibe el data
  URL `data:image/png;base64,...` del formulario; rechaza otro prefijo, base64 inválido, más de
  **64 KB** decodificados, firma PNG (`\x89PNG\r\n\x1a\n`) ausente y dimensiones del bloque IHDR
  fuera de 1–1200 × 1–400 px. Todo con la biblioteca estándar (`base64`, `struct`); no se decodifican
  los píxeles.
- **Tamaño**: el canvas exporta 600 × 200 px, trazo negro sobre fondo transparente; una firma típica
  ocupa 5–20 KB. El límite deja margen y frena envíos manipulados. `DATA_UPLOAD_MAX_MEMORY_SIZE`
  (2,5 MB) no se toca.
- **Firma vacía**: el JS no completa el campo oculto si no hubo trazos; el servidor exige el campo
  cuando el usuario todavía no tiene firma. Si ya la tiene, puede cambiar solo la matrícula (el campo
  vacío conserva la imagen). Un PNG en blanco enviado a mano pasa la validación (edge case de la spec).
- **Alternatives considered**: archivo en `MEDIA_ROOT` (se pierde en Render); almacenamiento externo
  (S3: dependencia y credenciales nuevas); validar con Pillow (llega como dependencia transitiva de
  WeasyPrint, pero usarla directamente sería una dependencia más; los controles de la biblioteca
  estándar alcanzan para un PNG que solo se muestra como imagen).

## R5 — Canvas de firma con JavaScript propio

- **Decision**: `informes/static/informes/firma.js`, sin librerías. Pointer Events (`pointerdown`,
  `pointermove`, `pointerup`/`pointercancel`) con `setPointerCapture`: un solo código para mouse,
  dedo y lápiz. `touch-action: none` en el canvas para que el dedo no desplace la página. Coordenadas
  escaladas de CSS a los 600 × 200 px internos (el canvas es responsive en ancho). Trazo con
  `lineCap`/`lineJoin` redondos. Botón **Borrar** limpia el canvas y el estado. En `submit`, si hubo
  trazos, `canvas.toDataURL("image/png")` va al `<input type="hidden" name="firma">`.
- **Rationale**: Pointer Events está soportado en todos los navegadores actuales y evita mantener
  dos juegos de eventos (mouse y touch).
- **Alternatives considered**: signature_pad (dependencia nueva, la historia pide sin librerías);
  eventos `mouse*` + `touch*` separados (más código, mismo resultado).

## R6 — La firma se copia al emitir

- **Decision**: `armar_contenido(estudio, firmante=None)` agrega la clave `"firma"` cuando recibe un
  usuario con firma: `{"nombre", "matricula", "imagen"}` (la imagen como data URL base64, texto). La
  vista previa la arma con `request.user` (FR-016) y `emitir_informe` con el usuario que emite.
- `emitir_informe` exige la firma después del permiso: sin `FirmaProfesional` →
  `EmitirInformeError("Cargá tu firma y matrícula en «Mi firma» antes de emitir.")`. Se relee dentro
  de la transacción, junto con el resto del contenido.
- **Nombre**: `usuario.get_full_name()` o, si está vacío, `usuario.email` (el modelo no tiene
  `username`).
- **Informes anteriores**: su `contenido` no tiene `"firma"`; los dos parciales muestran «Sin firma
  registrada» y el pie «Emitido por» cae al usuario guardado en `emitido_por`, como hasta ahora.
- **Rationale**: la copia de la 7.2 ya es la fuente única del informe emitido; meter la firma ahí
  hace que cambiarla después no toque nada emitido (FR-015) sin tablas ni versiones de firmas.
- **Alternatives considered**: FK del informe a la firma (la firma cambia → el informe cambia);
  historial de firmas (más modelo para el mismo resultado).

## R7 — Búsqueda sobre la copia guardada

- **Decision**: `informes/busqueda.py:informes_emitidos(q, desde, hasta)` sobre `Informe` con
  anotaciones `KT()` (Django 4.2+) de `contenido`: `cliente_nombre`
  (`contenido__cliente__nombre_completo`, que ya combina razón social y nombre), `cliente_documento`
  y `numero_pi`. Filtro de `q`:
  - `INF-` opcional (sin distinguir mayúsculas) seguido de dígitos → `numero=int(...)` (los ceros a
    la izquierda no importan);
  - solo dígitos → además `numero_pi` igual al texto (sin ceros a la izquierda) y, con ≥ 4 dígitos,
    documento que contiene el texto normalizado (`normalizar_numero_documento`, como
    `estudios/busqueda.py`);
  - cualquier texto → `cliente_nombre__unaccent__icontains`.
  - `desde`/`hasta` → `fecha_emision__date__gte/lte` en la zona horaria del proyecto
    (America/Argentina/Buenos_Aires).
- Orden `-numero` (el `Meta.ordering`), `select_related("estudio", "emitido_por")`, paginado con
  `RESULTADOS_POR_PAGINA`.
- **Rationale**: buscar por cómo salió el informe (spec, Assumptions) y no depender de joins a
  cliente y muestra actuales. El volumen (cientos de informes por año) no requiere índices sobre
  `jsonb`.
- **A verificar en la implementación**: que `__unaccent` se encadene sobre la anotación `KT`
  (salida `TextField`); si no, envolver con `Unaccent(KT(...))` del módulo de PostgreSQL.
- **Alternatives considered**: reutilizar `estudios/busqueda.py:filtro_busqueda` sobre
  `estudio__muestra__cliente` (busca por datos actuales, no por los del informe); columnas
  desnormalizadas en `Informe` (migración de datos para los ya emitidos, sin ganancia real).

## R8 — Inalterabilidad

- **Decision**: `Informe` sigue sin registrarse en el admin (un test lo asegura). Se agregan
  `Informe.save()` que lanza `ValueError` si el objeto ya existe (`not self._state.adding`) y
  `Informe.delete()` que lanza siempre; `estudio` ya es `OneToOne` con `PROTECT` y `Estudio → Muestra`
  y `Muestra → Cliente` son `PROTECT`. Las vistas de consulta y exportación son solo GET y no
  escriben nada.
- **Rationale**: principio IV («un informe emitido NO se puede modificar») y criterio 4 de Jira, con
  el mínimo de código. `QuerySet.update()`/`delete()` y SQL directo quedan fuera: ningún código del
  proyecto los usa sobre `Informe`.
- **Alternatives considered**: trigger en PostgreSQL que impida `UPDATE`/`DELETE` (más fuerte, pero
  complica los tests con `transaction=True` que vacían la base); admin de solo lectura para
  auditoría (la pantalla «Informes emitidos» ya cumple esa función).

## R9 — Descarga y nombre del PDF

- **Decision**: `informes:pdf` responde `application/pdf` con
  `Content-Disposition: attachment; filename="INF-000001.pdf"` (`FileResponse`/`HttpResponse` con
  los bytes de `write_pdf()`). Sin caché en disco: se genera en cada pedido (≈ 1 s por informe), lo
  que garantiza que sale de la copia guardada.
- **Alternatives considered**: guardar el PDF al emitir (el disco de Render no persiste; un
  `BinaryField` con el PDF duplica la copia y fija el diseño de la hoja para siempre).
