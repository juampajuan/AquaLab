---

description: "Lista de tareas de la US 7.3 – Consultar y exportar informe"
---

# Tasks: Consultar y exportar informe

**Input**: `specs/022-consultar-exportar-informe/` (`plan.md`, `spec.md`, `research.md`,
`data-model.md`, `contracts/consultar-exportar-informe-ui.md`, `quickstart.md`)

**Prerequisites**: `plan.md`, `spec.md` (aprobada el 2026-11-02) y `main` con la US 7.2 (PR #35):
`Informe` (`numero`, `estudio`, `emitido_por`, `fecha_emision`, `contenido`, `numero_mostrado`,
permiso `emitir_informes`), `informes/contenido.py:armar_contenido`, `servicios.emitir_informe` y
`EmitirInformeError`, las vistas `vista_previa`, `generar` y `ver`, los templates
`documento.html`, `vista_previa.html` y `ver.html`, `settings.AQUALAB_LABORATORIO`; fixtures
`empleado`, `cliente_http`, `estudio_de`, `catalogo`, `bioquimico`, `cliente_bioquimico`, helpers
`cargar`, `validar` (los tests de `informes` importan `estudios/tests/conftest.py`) y, en
`informes/tests/conftest.py`, `completar`, `otra_muestra` y `estudio_para`.

**Tests**: SÍ. La constitution (principio III) exige un test por escenario de aceptación. Los tests
siguen el «Mapa de tests» de `plan.md` y se escriben **antes** de la implementación de cada historia
(deben fallar primero). Los PDF de los tests son **reales** (WeasyPrint instalado en Docker y en CI).

**Organization**: cuatro user stories — US1 (P1, buscar y abrir), US2 (P1, exportar PDF e
imprimir), US3 (P1, mi firma y emisión con firma) y US4 (P2, inalterable).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: se puede ejecutar en paralelo (archivos distintos, sin dependencias pendientes)
- **[Story]**: user story a la que pertenece la tarea (`[US1]` … `[US4]`)
- Rutas relativas a la raíz del repo

## Convenciones para todas las tareas

- Textos y mensajes en **español**, copiados **literalmente** de
  `contracts/consultar-exportar-informe-ui.md`.
- Pantallas con el diseño de SCRUM-67 y `templates/ui/` (`ui/encabezado.html`, `.tarjeta`,
  `.tabla`, `ui/paginacion.html`, `ui/estado_vacio.html`, `ui/errores_form.html`, `aviso`). Si se
  agrega una clase de Tailwind, recompilar el CSS (T040).
- El documento A4 (`impreso.html`, `documento_impreso.html`) usa **solo** clases `inf-*` de
  `static/css/informe.css`, nunca Tailwind (research R2).
- PDF e impresión salen **siempre** de `informe.contenido`; nunca se vuelve a llamar a
  `armar_contenido` para un informe emitido.
- Las vistas llaman a `pdf.generar_pdf` y `servicios.emitir_informe` por el módulo; los tests
  parchean `informes.pdf.generar_pdf` e `informes.servicios.emitir_informe`.
- Permiso: `informes.emitir_informes` (`@permission_required(..., raise_exception=True)` en
  `mi_firma` y `generar`, revalidado en el servicio, `{% if perms.informes.emitir_informes %}` en
  templates).
- Comandos dentro de Docker: `docker compose exec web pytest informes estudios`,
  `docker compose exec web ruff check .`, `docker compose exec web ruff format --check .`.

---

## Phase 1: Setup (Shared Infrastructure)

- [X] T001 Confirmar que la rama `022-consultar-exportar-informe` sale de `main` con la US 7.2 (PR #35) y ejecutar `docker compose exec web pytest` y `docker compose exec web python manage.py makemigrations --check --dry-run`: suite en verde y sin cambios pendientes antes de empezar.
- [X] T002 Agregar WeasyPrint según research R1: «`weasyprint==70.0`» en `requirements.txt` (orden alfabético, como el resto); en `Dockerfile`, antes de `COPY requirements.txt`, un `RUN apt-get update && apt-get install -y --no-install-recommends libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz-subset0 fonts-dejavu-core && rm -rf /var/lib/apt/lists/*` con el comentario «Librerías de sistema de WeasyPrint (US 7.3). Las mismas en el CI (.github/workflows/ci.yml).». Reconstruir (`docker compose up -d --build`) y comprobar `docker compose exec web python -c "import weasyprint; weasyprint.HTML(string='<p>ok</p>').write_pdf()"`.
- [X] T003 [P] En `.github/workflows/ci.yml`: antes de «Instalar dependencias», paso «Librerías de sistema de WeasyPrint» con `sudo apt-get update && sudo apt-get install -y libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz-subset0 fonts-dejavu-core` y el comentario «Mismas librerías que el Dockerfile.»; después de «Instalar dependencias», paso «WeasyPrint instalado» con `python -c "import weasyprint; weasyprint.HTML(string='<p>ok</p>').write_pdf()"`. La verificación en GitHub Actions (job verde con `pytest`) se hace en el PR (T043).
- [X] T004 [P] Agregar los íconos Lucide (licencia ISC, ya en `templates/ui/iconos/LICENSE.txt`) `download.svg`, `printer.svg` y `pen-line.svg` en `templates/ui/iconos/`, con el mismo formato que los existentes (`viewBox="0 0 24 24"`, `stroke="currentColor"`, sin `width`/`height`).

---

## Phase 2: Foundational (Blocking Prerequisites)

**⚠️ CRITICAL**: ninguna historia empieza antes de terminar esta fase.

- [X] T005 [P] Crear `informes/tests/test_firmas.py` con `test_leer_firma` parametrizado (research R4): PNG válido de 600 × 200 generado en el test con `zlib` + `struct` (sin Pillow) → devuelve los bytes; prefijo distinto de `data:image/png;base64,` (ej. `data:image/jpeg;base64,`) → error «La firma no es una imagen válida.»; base64 inválido → mismo error; bytes sin la firma PNG `\x89PNG\r\n\x1a\n` → mismo error; IHDR con 0 de ancho, 1201 de ancho o 401 de alto → mismo error; más de 64 KB decodificados (`64 * 1024 + 1`) → «La firma es demasiado grande.». Agregar en `informes/tests/utiles.py` (nuevo) el helper `png(ancho=600, alto=200)` y `data_url(bytes)`, que usan también los demás tests.
- [X] T006 Crear `informes/firmas.py` con `leer_firma(texto) -> bytes` hasta que pase T005: solo biblioteca estándar (`base64.b64decode(..., validate=True)`, `struct.unpack(">II", ...)` sobre los bytes 16–24 del IHDR); constantes `TAMANO_MAXIMO = 64 * 1024`, `ANCHO_MAXIMO = 1200`, `ALTO_MAXIMO = 400`; lanza `ValidationError` con los mensajes de T005. Docstring: es la única lectura de la firma (FR-012).
- [X] T007 Agregar `FirmaProfesional` en `informes/models.py` según `data-model.md`: «`usuario = OneToOneField(AUTH_USER_MODEL, on_delete=CASCADE, related_name="firma_profesional")`», «`imagen = BinaryField("imagen")`», «`matricula = CharField("matrícula", max_length=40)`», «`actualizada = DateTimeField(auto_now=True)`», `Meta.verbose_name = "firma profesional"`, `verbose_name_plural = "firmas profesionales"`, propiedad `data_url` → `"data:image/png;base64," + base64.b64encode(bytes(imagen)).decode()` y `__str__`. Generar `informes/migrations/0003_firmaprofesional.py` con `makemigrations`. En `informes/tests/test_modelos.py`: `test_firma_data_url` (devuelve el prefijo y vuelve a decodificar a los mismos bytes) y `test_una_firma_por_usuario` (`IntegrityError`).
- [X] T008 Fixtures de firma en `estudios/tests/conftest.py`: `firma_de(usuario, matricula="MP 1234")` (fixture que devuelve una función que crea la `FirmaProfesional` con el PNG de `informes/tests/utiles.py:png()`), y el fixture `bioquimico` **le crea la firma** («MP 1234») para que los tests de la 7.2 que emiten (`test_emitir.py`, `test_servicio_emision.py`, `test_concurrencia_emision.py`, `test_ver.py`, `test_vista_previa.py`, `test_generar.py`, `test_permisos.py`) sigan pasando cuando la emisión exija firma (T031). Agregar `bioquimico_sin_firma` (en el grupo, sin `FirmaProfesional`) para los tests de US3. Ejecutar `docker compose exec web pytest informes estudios`: todo en verde.
- [X] T009 [P] En `informes/tests/test_contenido.py`: `test_armar_contenido_con_firmante` (con `bioquimico`: `contenido["firma"] == {"nombre": "<nombre completo>", "matricula": "MP 1234", "imagen": firma.data_url}`), `test_nombre_sin_full_name_usa_email` (usuario con nombre y apellido vacíos → `nombre` = correo), `test_armar_contenido_firmante_sin_firma` y `test_armar_contenido_sin_firmante` (sin clave `"firma"`), y que `json.dumps(contenido)` funcione (todo texto).
- [X] T010 Cambiar `armar_contenido(estudio, firmante=None)` en `informes/contenido.py` hasta que pase T009 (research R6): si `firmante` tiene `firma_profesional`, agrega `"firma": {"nombre": firmante.get_full_name() or firmante.email, "matricula": firma.matricula, "imagen": firma.data_url}`; si no, no agrega la clave. Actualizar el docstring del módulo (la firma se copia al emitir; los informes anteriores no la tienen).
- [X] T011 Crear `informes/templates/informes/firma.html` (parcial compartido por pantalla e impreso; research R3): recibe `firma` (`contenido.firma` o nada) y usa solo las clases semánticas `firma`, `firma-imagen`, `firma-nombre` y `firma-matricula`, definidas dos veces: en `static/src/aqualab.css` (`@layer components` con `@apply`, para la pantalla; recompilar en T040) y en `static/css/informe.css` (T022). Con firma: `<img src="{{ firma.imagen }}" alt="Firma de {{ firma.nombre }}">`, nombre y «Mat. {{ firma.matricula }}»; sin firma: «Sin firma registrada». En `informes/tests/test_ver.py`: `test_parcial_firma` (con y sin firma, render con `render_to_string`).

**Checkpoint**: WeasyPrint instalado en Docker y declarado en CI, `FirmaProfesional` con su lectura validada, firma en el contenido y la suite de la 7.2 en verde con la fixture nueva.

---

## Phase 3: User Story 1 - Buscar y abrir un informe emitido (Priority: P1) 🎯 MVP

**Goal**: desde el menú, listar los informes emitidos, buscarlos por número, cliente, documento o N° PI, filtrarlos por fechas y abrirlos.

**Independent Test**: con tres informes de dos clientes, cada búsqueda y el rango de fechas muestran solo los que corresponden y «Ver» abre el informe emitido.

### Tests for User Story 1 ⚠️ (escribir primero, deben fallar)

- [X] T012 [P] [US1] Crear `informes/tests/test_busqueda.py` sobre `informes/busqueda.py:informes_emitidos` (fixture local que emite tres informes con `servicios.emitir_informe` y `bioquimico`, en muestras de `otra_muestra` con dos clientes: «Aguas del Sur SA» razón social con CUIT, y «José Núñez» DNI): `test_busca_por_numero` parametrizado (`"INF-000002"`, `"inf-2"`, `"2"`, `"0002"` → solo el 2), `test_busca_por_cliente` («nunez» sin tilde y «aguas del» → los de ese cliente), `test_busca_por_documento` (≥ 4 dígitos del documento), `test_busca_por_numero_pi`, `test_busca_por_datos_guardados` (renombrar el cliente después de emitir: encuentra por el nombre viejo y no por el nuevo), `test_filtra_por_fechas` (cambiar `fecha_emision` con `Informe.objects.filter(pk=...).update(...)` a tres días distintos; `desde`, `hasta` y ambos inclusivos, en hora de Buenos Aires: un informe a las 23:30 del día D entra con `hasta=D`), `test_fechas_y_busqueda_combinadas` y `test_orden_mas_reciente_primero`.
- [X] T013 [P] [US1] Crear `informes/tests/test_emitidos.py` sobre `informes:emitidos`: `test_menu_informes_emitidos` (el menú tiene «Informes emitidos» y queda activo en `informes:emitidos` y en `informes:ver`), `test_listado_columnas_y_orden` (informe, emisión `d/m/Y H:i`, cliente con documento, N° PI, estudio con tipo, emitido por `contenido.firma.nombre`; para un informe sin `"firma"` en el contenido, el nombre del usuario `emitido_por`; enlace «Ver» a `informes:ver`), `test_paginacion_conserva_filtros` (21 informes con `RESULTADOS_POR_PAGINA = 20`: la página 2 lleva `q`, `desde` y `hasta`), `test_listado_vacio` parametrizado («Todavía no hay informes emitidos.» sin filtros; «No hay informes que coincidan con la búsqueda.» con filtros), `test_fechas_invalidas` parametrizado (`desde=31/02/2026` → error en el campo; `desde` > `hasta` → «La fecha desde no puede ser posterior a la fecha hasta.»; 200 sin tabla) y `test_cualquier_empleado_ve_el_listado` (con `cliente_http`).
- [X] T014 [P] [US1] En `informes/tests/test_ver.py`: `test_ver_vuelve_a_emitidos` (enlace «Volver a informes emitidos» a `informes:emitidos`) y `test_ver_pk_inexistente_404` (además del `test_ver_sin_informe_404` de la 7.2).

### Implementation for User Story 1

- [X] T015 [US1] Crear `informes/forms.py` con `BuscarInformeForm` según `data-model.md`: «`q = CharField(required=False, max_length=100)`» (con `strip`), «`desde = DateField(required=False)`» y «`hasta = DateField(required=False)`» (`input_formats` `%d/%m/%Y` y `%Y-%m-%d`, widget `DateInput(attrs={"type": "date"})`); `clean()`: si están las dos y `desde > hasta`, error «La fecha desde no puede ser posterior a la fecha hasta.» en `desde`.
- [X] T016 [US1] Crear `informes/busqueda.py` con `informes_emitidos(q, desde, hasta)` según research R7 hasta que pase T012: `Informe.objects.select_related("estudio", "emitido_por").annotate(cliente_nombre=KT("contenido__cliente__nombre_completo"), cliente_documento=KT("contenido__cliente__numero_documento"), numero_pi=KT("contenido__muestra__numero_pi"))`; `q` con `INF-` opcional (`re.fullmatch(r"(?i)(?:inf-?)?(\d+)", q)`) → `numero=int(...)`; solo dígitos → también `numero_pi=str(int(q))` y, con ≥ 4 dígitos, `cliente_documento__contains=normalizar_numero_documento(q)`; siempre `cliente_nombre__unaccent__icontains=q` (si `__unaccent` no se encadena sobre `KT`, usar `Unaccent(KT(...))` de `django.contrib.postgres.lookups`, como prevé R7); `fecha_emision__date__gte=desde` / `__lte=hasta`. Docstring: es la única búsqueda de informes emitidos y busca en la copia guardada.
- [X] T017 [US1] Agregar la vista `emitidos` en `informes/views.py` y la ruta `path("emitidos/", views.emitidos, name="emitidos")` en `informes/urls.py`: `BuscarInformeForm(request.GET or None)`; si es válido (o no está ligado) → `informes_emitidos(...)` paginado con `RESULTADOS_POR_PAGINA` de `estudios/views.py`; `parametros` con `urlencode` de `q`, `desde` y `hasta` (en `aaaa-mm-dd`) para la paginación; contexto `form`, `page_obj`, `parametros`, `hay_filtros`.
- [X] T018 [US1] Crear `informes/templates/informes/emitidos.html` según el contrato (encabezado «Informes emitidos», sección «Informes»; formulario con búsqueda, desde, hasta, **Buscar** y **Limpiar**; tabla `.tabla` con las columnas del contrato; «Emitido por» = `informe.contenido.firma.nombre|default:informe.emitido_por.get_full_name|default:informe.emitido_por.email`; vacío con `ui/estado_vacio.html`; `ui/paginacion.html` con `parametros`). Siguiendo el estilo de `informes/templates/informes/listar.html`.
- [X] T019 [US1] Agregar «Informes emitidos» a la sección Informes de `templates/ui/menu.html` (activo con `informes:emitidos` o `informes:ver`; «Seleccionar estudio» deja de marcarse en `informes:ver`). En `informes/templates/informes/ver.html`: acción **Volver a informes emitidos** → `informes:emitidos`; se mantienen «Volver al control» y «Ver detalle del estudio». (Los botones de exportar se agregan en T026.)

**Checkpoint**: listado, búsqueda, filtro de fechas y apertura del informe funcionando; T012–T014 en verde.

---

## Phase 4: User Story 2 - Exportar el informe a PDF o imprimirlo en A4 (Priority: P1)

**Goal**: desde el informe emitido, descargar un PDF A4 generado en el servidor o imprimirlo en A4 desde el navegador, con membrete, datos, firma y pie por hoja, siempre desde la copia guardada.

**Independent Test**: el PDF de un informe firmado es A4, se llama `INF-00000N.pdf` y contiene membrete, datos, pruebas y firma; la página de impresión es independiente y sin menú.

### Tests for User Story 2 ⚠️ (escribir primero, deben fallar)

- [X] T020 [P] [US2] Crear `informes/tests/test_impreso.py` (fixture que emite un informe de pH 7,4, Cloruro 40 → 400, E. coli Ausente y SS10 0,05 → «< 0,1» con `bioquimico`): helper `valores(contenido)` que recorre laboratorio (salvo `logo`), cliente, muestra, estudio, cada prueba (`nombre`, `codigo`, `resultado_texto`, `limite_texto`, `norma`, `evaluacion_texto`) y firma (`nombre`, `matricula`); `test_impreso_contiene_todo_el_contenido` (render de `informes/impreso.html` con `pdf=True`: cada valor aparece, escapado con `django.utils.html.escape`; `INF-` + número y fecha de emisión; la fila de Cloruro con la clase `inf-fuera`), `test_pantalla_contiene_todo_el_contenido` (lo mismo sobre la respuesta de `informes:ver`, SC-002), `test_impreso_con_firma` (`<img` con `src` = `contenido["firma"]["imagen"]`, nombre y «Mat. MP 1234»), `test_sin_firma_registrada` (quitar `"firma"` del contenido con `Informe.objects.filter(pk=...).update(contenido=...)`: pantalla e impreso dicen «Sin firma registrada»), `test_imprimir_pagina_independiente` (`informes:imprimir`: 200, `<!DOCTYPE html>`, `<link` a `css/informe.css`, `informes/imprimir.js`, la barra `inf-barra` con «Imprimir» y «Volver al informe», sin `data-menu-navegacion`) y `test_exportacion_no_cambia_al_editar` (después de emitir: editar el domicilio del cliente, el límite máximo del Cloruro, `settings.AQUALAB_LABORATORIO["nombre"]` con `settings` fixture y redibujar la firma del bioquímico → el impreso sigue con los valores del contenido y no con los nuevos).
- [X] T021 [P] [US2] Crear `informes/tests/test_pdf.py` con PDF **reales**: `test_ver_ofrece_pdf_e_imprimir` (en `informes:ver`, enlaces a `informes:pdf` y a `informes:imprimir` con `target="_blank"`), `test_exportar_sin_informe_404` parametrizado sobre `informes:pdf` e `informes:imprimir` (estudio sin informe y `pk` inexistente → 404), `test_pdf_descarga_a4` (`informes:pdf` → 200, `Content-Type: application/pdf`, `Content-Disposition` = `attachment; filename="INF-000001.pdf"`, cuerpo empieza con `%PDF-`; y `pdf.documento(informe)` (el `weasyprint.Document` renderizado) tiene páginas de 595 × 842 pt ± 1, A4), `test_pdf_sale_de_impreso` (parchear `informes.pdf.render_to_string` con `wraps` y comprobar que se llamó con `informes/impreso.html`, `pdf=True` y `contenido=informe.contenido`), `test_sin_firma_registrada_en_pdf` (informe sin `"firma"` → el PDF se genera sin error), `test_pdf_varias_hojas` (estudio con todas las pruebas no calculadas del catálogo de vertido, o un contenido con 80 pruebas armado en el test → `len(documento.pages) > 1`), `test_hoja_de_estilos_paged_media` (`static/css/informe.css` contiene `size: A4`, `counter(page)`, `counter(pages)`, `string(numero)`, `break-inside: avoid` y `table-header-group`), `test_exportar_no_modifica` (`informe.contenido`, `estudio.estado` y `fecha_emision` iguales antes y después de `informes:pdf` e `informes:imprimir`) y `test_pdf_error_redirige` (parchear `informes.pdf.generar_pdf` para que lance `Exception` → 302 a `informes:ver` con «No se pudo generar el PDF. Intentá nuevamente.» y un registro en el log `informes`, con `caplog`).

### Implementation for User Story 2

- [X] T022 [US2] Crear `static/css/informe.css` según research R2 y el «Diseño → Hoja A4» de `plan.md`: `@font-face` Inter con `url("../fuentes/InterVariable.woff2")`; `@page { size: A4; margin: 18mm 15mm 20mm; @bottom-center { content: string(numero) " · Página " counter(page) " de " counter(pages); font-size: 8pt; color: #5b6b7f; } }`; `.inf-numero { string-set: numero content(); }`; membrete (`.inf-membrete`, logo, nombre en marino), secciones con tablas rótulo/valor (`.inf-datos`), `.inf-tabla` con `thead { display: table-header-group; }` y `tr { break-inside: avoid; }`, `.inf-fuera` con fondo de peligro suave, `.inf-pie` y `.firma` con `break-inside: avoid` (imagen de máximo 60 mm × 20 mm); `@media screen` (hoja de 210 mm centrada con sombra y la barra `.inf-barra`) y `@media print` (`.inf-barra { display: none; }`). Solo CSS 2.1 + Paged Media: sin grid, variables CSS ni `oklch`; colores hex de la paleta de SCRUM-67 (tomarlos de `static/src/aqualab.css`).
- [X] T023 [US2] Crear `informes/templates/informes/documento_impreso.html` (parcial, clases `inf-*`) con los mismos datos y orden que `documento.html` y el contrato: membrete (logo «aqualab» con el SVG de `ui/icono.html` `droplet`, nombre, dirección, matrícula; a la derecha «Informe N° <span class="inf-numero">INF-…</span>» y la fecha), Cliente, Muestra, Estudio (vacíos «—»), tabla de Resultados (Prueba con código, Resultado, Unidad con `|unidad` y vacía en A/P, Límite con origen si no es general, Norma, Cumple con el texto de la evaluación; fila fuera de norma con `inf-fuera`), pie con «Responsable técnico: …», `{% include "informes/firma.html" with firma=contenido.firma %}` y «Emitido el d/m/Y H:i». Crear `informes/templates/informes/impreso.html`: documento completo (`<!DOCTYPE html>`, `lang="es"`, título «Informe INF-…»); si no es `pdf`, `<link rel="stylesheet" href="{% static 'css/informe.css' %}">`, la barra `inf-barra` (**Imprimir** con `data-imprimir`, **Volver al informe** → `informes:ver`) y `<script src="{% static 'informes/imprimir.js' %}" defer>`; incluye `documento_impreso.html`.
- [X] T024 [P] [US2] Crear `informes/static/informes/imprimir.js`: al cargar llama a `window.print()`, y el botón `[data-imprimir]` también. Sin dependencias.
- [X] T025 [US2] Crear `informes/pdf.py`: `documento(informe)` → `weasyprint.HTML(string=render_to_string("informes/impreso.html", {"informe": informe, "contenido": informe.contenido, "pdf": True}), base_url=str(settings.BASE_DIR)).render(stylesheets=[weasyprint.CSS(filename=finders.find("css/informe.css"))])` y `generar_pdf(informe) -> bytes` (`documento(informe).write_pdf()`). Docstring: siempre desde la copia guardada (FR-006). Vista `pdf` en `informes/views.py` (ruta `estudios/<int:pk>/informe/pdf/`, nombre `pdf`): `get_object_or_404(Informe, estudio__pk=pk)` → `pdf.generar_pdf(informe)` → `HttpResponse(content_type="application/pdf")` con `Content-Disposition: attachment; filename="{numero_mostrado}.pdf"`; ante `Exception`, `logger.exception` en el log `informes` y 302 a `informes:ver` con el mensaje del contrato.
- [X] T026 [US2] Vista `imprimir` en `informes/views.py` (ruta `estudios/<int:pk>/informe/imprimir/`, nombre `imprimir`): `get_object_or_404(Informe, estudio__pk=pk)` → `render(request, "informes/impreso.html", {"informe": informe, "contenido": informe.contenido, "pdf": False})`. En `informes/templates/informes/ver.html`, acciones **Descargar PDF** (`btn btn-primario`, ícono `download`) → `informes:pdf` e **Imprimir** (`btn btn-secundario`, ícono `printer`, `target="_blank" rel="noopener"`) → `informes:imprimir`. Agregar el bloque de firma al documento de pantalla `informes/templates/informes/documento.html` (`{% include "informes/firma.html" with firma=contenido.firma %}` en el pie) y que «Emitido por» use `contenido.firma.nombre` cuando exista (si no, el usuario `emitido_por`, como en la 7.2). Pasar T020 y T021.

**Checkpoint**: PDF real A4 descargable e impresión desde el navegador, ambos desde la copia; T020–T021 en verde.

---

## Phase 5: User Story 3 - Cargar mi firma y matrícula (Priority: P1)

**Goal**: cada usuario con «Puede emitir informes» dibuja su firma y carga su matrícula; sin firma no puede emitir; al emitir, la firma queda copiada en el informe.

**Independent Test**: un bioquímico sin firma no puede emitir y ve el enlace a «Mi firma»; tras cargarla, el informe emitido muestra su firma, nombre y matrícula.

### Tests for User Story 3 ⚠️ (escribir primero, deben fallar)

- [X] T027 [P] [US3] Crear `informes/tests/test_mi_firma.py` sobre `informes:mi_firma`: `test_mi_firma_muestra_actual` (sin firma: canvas `data-firma`, botón «Borrar», campo «Matrícula», «Guardar firma»; con firma: la imagen actual y la matrícula), `test_guarda_firma_y_matricula` (POST con `firma=data_url(png())` y `matricula=" MP 9 "` → 302 a `informes:mi_firma`, «Se guardó tu firma.», `FirmaProfesional` del usuario con esos bytes y «MP 9»), `test_rechaza_firma_invalida` parametrizado (sin firma y sin firma previa → «Dibujá tu firma antes de guardar.»; sin matrícula; data URL JPEG; PNG de 1201 px; más de 64 KB → 200 con el error y la firma guardada sin cambios), `test_reemplaza_firma` (nueva imagen → se reemplaza, sigue habiendo una sola), `test_solo_matricula_conserva_imagen` (firma vacía con firma previa y matrícula nueva → conserva la imagen), `test_firma_es_del_usuario` (el POST solo crea o cambia la del `request.user`), `test_mi_firma_sin_permiso_403` (GET y POST con `cliente_http`) y `test_enlace_mi_firma_solo_con_permiso` (la barra superior muestra «Mi firma» con `cliente_bioquimico` y no con `cliente_http`).
- [X] T028 [P] [US3] En `informes/tests/test_vista_previa.py`: `test_vista_previa_muestra_firma` (con `cliente_bioquimico`: la imagen, el nombre y la matrícula del bioquímico) y `test_vista_previa_sin_firma_ofrece_cargarla` (con `bioquimico_sin_firma`: no está «Emitir informe»; está «Para emitir necesitás cargar tu firma y matrícula.» con el enlace «Cargar mi firma» a `informes:mi_firma`). Revisar que `test_vista_previa_emitir_solo_con_permiso` siga valiendo con la fixture de T008.
- [X] T029 [P] [US3] En `informes/tests/test_servicio_emision.py`: `test_emitir_sin_firma_rechaza` (`bioquimico_sin_firma` → `EmitirInformeError` «Cargá tu firma y matrícula en «Mi firma» antes de emitir.», sin `Informe` y el estudio sin cambio de estado), `test_emitir_copia_firma` (el `contenido["firma"]` del informe = nombre, «MP 1234» y el data URL de la firma) y `test_cambiar_firma_no_cambia_emitidos` (después de emitir, cambiar imagen y matrícula de la `FirmaProfesional` → el informe guardado conserva las anteriores, FR-015). En `informes/tests/test_emitir.py`: `test_generar_sin_firma` (POST con `bioquimico_sin_firma` → 302 a `informes:control` con el mensaje y sin informe).

### Implementation for User Story 3

- [X] T030 [US3] Agregar `FirmaForm` en `informes/forms.py` según `data-model.md`: recibe `usuario` en el constructor; «`firma = CharField(required=False, widget=HiddenInput)`» — obligatorio si el usuario no tiene firma («Dibujá tu firma antes de guardar.»), si viene se convierte con `informes.firmas.leer_firma` (sus errores al campo); «`matricula = CharField(max_length=40)`» obligatoria y con `strip`; inicial con la matrícula guardada. Método `guardar()` que hace `update_or_create` de la `FirmaProfesional` de ese usuario (si `firma` vino vacía, conserva la imagen).
- [X] T031 [US3] En `informes/servicios.py:emitir_informe`, después del control de permiso: si el usuario no tiene `firma_profesional` → `EmitirInformeError("Cargá tu firma y matrícula en «Mi firma» antes de emitir.")`; pasar `firmante=usuario` a `armar_contenido` (research R6). Actualizar el docstring. En `informes/views.py:vista_previa`: `armar_contenido(estudio, request.user)` y en el contexto `puede_emitir` (permiso) y `falta_firma` (permiso sin `firma_profesional`).
- [X] T032 [US3] Vista `mi_firma` en `informes/views.py` (ruta `mi-firma/`, nombre `mi_firma`) con `@permission_required("informes.emitir_informes", raise_exception=True)`: GET con `FirmaForm(usuario=request.user)`; POST válido → `guardar()`, `messages.success(request, "Se guardó tu firma.")`, 302 a `informes:mi_firma`; inválido → 200 con errores. Template `informes/templates/informes/mi_firma.html` según el contrato (encabezado «Mi firma»; firma actual con `firma.data_url` y matrícula si existe; `<canvas data-firma width="600" height="200">` con borde punteado, «Firmá con el mouse o con el dedo», botón **Borrar** `data-firma-borrar`, `<input type="hidden" name="firma">`, campo **Matrícula** con placeholder «MP 1234», **Guardar firma** `btn btn-primario`, `ui/errores_form.html`) y `<script src="{% static 'informes/firma.js' %}" defer>`.
- [X] T033 [P] [US3] Crear `informes/static/informes/firma.js` según research R5: Pointer Events (`pointerdown` con `setPointerCapture`, `pointermove`, `pointerup`/`pointercancel`) sobre `[data-firma]`; `canvas.style.touchAction = "none"`; coordenadas escaladas de CSS a 600 × 200 (`getBoundingClientRect`); trazo negro, `lineWidth` 2.5, `lineCap`/`lineJoin` `round`, fondo transparente; `[data-firma-borrar]` limpia el canvas y la marca de trazos; en `submit` del formulario, si hubo trazos, `input[name=firma].value = canvas.toDataURL("image/png")`, si no, lo deja vacío. Sin dependencias.
- [X] T034 [US3] En `informes/templates/informes/vista_previa.html`: el documento muestra la firma de `contenido.firma` (ya incluida por T026 en `documento.html`); con `falta_firma`, en lugar del formulario «Emitir informe», un `aviso aviso-advertencia` «Para emitir necesitás cargar tu firma y matrícula.» con el enlace **Cargar mi firma** → `informes:mi_firma`. En `templates/base.html`, junto al nombre del usuario y antes de «Cerrar sesión», el enlace **Mi firma** (ícono `pen-line`) solo con `perms.informes.emitir_informes`. Pasar T027–T029 y toda la suite de `informes`.

**Checkpoint**: «Mi firma» con canvas propio, emisión que exige y copia la firma, vista previa firmada; T027–T029 y los tests de la 7.2 en verde.

---

## Phase 6: User Story 4 - Informe inalterable para auditorías (Priority: P2)

**Goal**: ninguna vía modifica ni borra un informe emitido.

**Independent Test**: sin admin de informes; `save()` sobre uno existente y `delete()` fallan; estudio, muestra y cliente quedan protegidos.

### Tests for User Story 4 ⚠️ (escribir primero, deben fallar)

- [X] T035 [P] [US4] En `informes/tests/test_modelos.py`: `test_informe_no_registrado_en_admin` (`Informe not in admin.site._registry`, y `/admin/informes/informe/` → 404 para un superusuario), `test_informe_no_se_modifica` (cambiar `contenido` y `save()` → `ValueError` «Un informe emitido no se puede modificar.»; el de la base sigue igual), `test_informe_no_se_borra` (`informe.delete()` → `ValueError`; el informe sigue) y `test_no_se_borran_estudio_muestra_ni_cliente` (`ProtectedError` al borrar el estudio, la muestra y el cliente de un informe emitido). Revisar que `test_estudio_con_informe_protegido` (7.2) siga igual.

### Implementation for User Story 4

- [X] T036 [US4] En `informes/models.py:Informe` según research R8 y `data-model.md`: `save()` que lanza `ValueError("Un informe emitido no se puede modificar.")` si `not self._state.adding`, y `delete()` que lanza `ValueError("Un informe emitido no se puede borrar.")`. Docstring con FR-017. Confirmar que `informes/admin.py` no existe ni registra `Informe` y que ningún código del proyecto hace `save()` sobre un informe existente (`emitir_informe` usa `create`). Pasar T035.

**Checkpoint**: informe emitido inalterable; T035 en verde.

---

## Phase 7: Polish & Cross-Cutting Concerns

- [X] T037 [P] Actualizar `CLAUDE.md`: nueva sección «Consultar y exportar informe (US 7.3)» (`informes/busqueda.py:informes_emitidos` es la única búsqueda de informes y busca en la copia; PDF con `informes/pdf.py` y la impresión desde `informes/impreso.html` + `static/css/informe.css`, sin Tailwind, siempre desde `informe.contenido`; WeasyPrint 70.0 con las mismas librerías de sistema en `Dockerfile` y CI; `FirmaProfesional` en la base como PNG validado por `informes/firmas.py:leer_firma`, ≤ 64 KB; sin firma no se emite y la firma se copia en `contenido["firma"]`; los informes anteriores dicen «Sin firma registrada»; `Informe.save/delete` bloqueados; en los tests, `bioquimico` ya tiene firma y `bioquimico_sin_firma` no). En la sección de la US 7.2, quitar «El informe no se edita ni se borra» como regla solo de la 7.2 y remitir a la nueva sección.
- [X] T038 [P] Actualizar `README.md` si lista el stack o los requisitos del sistema: WeasyPrint y las librerías de Pango (solo si ya hay una sección de stack o instalación; no crear secciones nuevas).
- [X] T039 Ejecutar `docker compose exec web ruff check .`, `docker compose exec web ruff format --check .` y `docker compose exec web python manage.py makemigrations --check --dry-run`.
- [X] T040 [P] Recompilar Tailwind (`docker compose exec -u "$(id -u):$(id -g)" web tailwindcss -i static/src/aqualab.css -o static/css/aqualab.css --minify`); si `static/css/aqualab.css` cambia, incluirlo en el commit. `static/css/informe.css` no se compila.
- [X] T041 Ejecutar la suite completa `docker compose exec web pytest`: todo en verde, incluidos los PDF reales.
- [X] T042 Recorrer `specs/022-consultar-exportar-informe/quickstart.md` (pasos 1 a 12) en el navegador, incluida la firma con el dedo (celular o modo táctil de las herramientas del navegador) y la impresión en Chrome, y marcar el resultado en esta lista.
- [ ] T043 Abrir el PR «US 7.3 – Consultar y exportar informe» (referencia a `specs/022-consultar-exportar-informe/` y SCRUM-59) y comprobar en GitHub Actions que pasan los pasos «Librerías de sistema de WeasyPrint», «WeasyPrint instalado» y `pytest`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: `T001` → `T002`; `T003` y `T004` en paralelo con `T002`.
- **Foundational (Phase 2)**: depende de `T002`. `T005` → `T006`; `T007` → `T008` (la fixture usa el helper `png()` de `T005`); `T009` → `T010` (necesita `T007`/`T008`); `T011` después de `T010`.
- **US1 (Phase 3)**: depende de la fase 2. MVP de consulta.
- **US2 (Phase 4)**: depende de la fase 2 (`T011`); conviene después de US1 porque ambas tocan `ver.html`.
- **US3 (Phase 5)**: depende de la fase 2 y de `T026` (firma en `documento.html`); sus tests (`T027`–`T029`) se pueden escribir en paralelo a US2.
- **US4 (Phase 6)**: depende solo de la fase 2; se puede hacer en paralelo a US1–US3.
- **Polish (Phase 7)**: depende de las cuatro historias.

### Grafo

```text
T001 → T002 ─┬→ T005 → T006 ─┐
T003, T004   └→ T007 → T008 ─┴→ T009 → T010 → T011
                                              │
            ┌─────────────────────────────────┤
            ▼                                 ▼
US1: T012, T013, T014 → T015 → T016 → T017 → T018 → T019
US2: T020, T021 → T022 → T023, T024 → T025 → T026
US3: T027, T028, T029 → T030 → T031 → T032, T033 → T034
US4: T035 → T036
Polish: T037, T038 → T039, T040 → T041 → T042 → T043
```

---

## Parallel Example: User Story 1

```bash
Task T012: "Tests de la búsqueda en informes/tests/test_busqueda.py"
Task T013: "Tests del listado en informes/tests/test_emitidos.py"
Task T014: "Tests de ver/exportar en informes/tests/test_ver.py"
```

## Parallel Example: User Story 3

```bash
Task T027: "Tests de Mi firma en informes/tests/test_mi_firma.py"
Task T028: "Tests de la vista previa con firma en informes/tests/test_vista_previa.py"
Task T029: "Tests de emisión con firma en informes/tests/test_servicio_emision.py y test_emitir.py"
```

---

## Implementation Strategy

### En dos tandas (según `docs/guias/guia-sdd-paso-a-paso.md`)

1. **Tanda 1 (Fases 1 y 2 — `T001` a `T011`)**: WeasyPrint en `requirements.txt`, Dockerfile y CI;
   íconos; `leer_firma` y `FirmaProfesional` con su migración; la firma en `armar_contenido`; la
   fixture `bioquimico` con firma para que los tests de la 7.2 sigan pasando; el parcial de firma.
   Suite en verde y un PDF de prueba generado dentro de Docker.
2. **Tanda 2 (Fases 3 a 7 — `T012` a `T043`)**: US1 (listado y búsqueda), US2 (PDF real e
   impresión), US3 (Mi firma y emisión con firma) y US4 (inalterable), cada una con sus tests
   escritos primero y mostrados en rojo; cerrar con `CLAUDE.md`, `ruff`, CSS, suite completa,
   recorrido manual y CI en el PR.

**MVP**: tanda 1 + US1 permite encontrar y abrir cualquier informe emitido; US2 agrega la entrega
física o digital, que es el objetivo de la historia.
