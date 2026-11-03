# Implementation Plan: Consultar y exportar informe

**Branch**: `022-consultar-exportar-informe` | **Date**: 2026-11-02 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/022-consultar-exportar-informe/spec.md` (US 7.3, SCRUM-59)

## Summary

Nueva pantalla **Informes emitidos** (menú Informes) que busca sobre la copia guardada de cada
informe (`Informe.contenido`, US 7.2) por número, cliente, documento y N° PI, con filtro de fechas
de emisión. Desde el informe emitido: **Descargar PDF**, generado en el servidor con **WeasyPrint
70.0** en A4, e **Imprimir**, una página independiente que abre la impresión del navegador. Los dos
usan el mismo template (`informes/impreso.html`) y la misma hoja de estilos propia
(`static/css/informe.css`, sin Tailwind): membrete, tabla sin filas partidas y pie «INF-… · Página
N de M» en cada hoja. Cada usuario con «Puede emitir informes» dibuja su firma en **Mi firma**
(canvas con JS propio, Pointer Events) y carga su matrícula; la firma se guarda en la base como PNG
chico (`FirmaProfesional.imagen`, `BinaryField`, validado en el servidor). Sin firma no se emite;
al emitir, firma, nombre y matrícula se copian en `contenido["firma"]`. Los informes anteriores
salen con «Sin firma registrada». `Informe` rechaza `save()` sobre uno existente y `delete()`.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: Django 5.2 LTS (ORM con `KT()` sobre `jsonb`, `BinaryField`, auth,
messages, staticfiles), **WeasyPrint 70.0** (nueva, prevista en la constitution) con Pango y
HarfBuzz del sistema, Tailwind CSS 4 para las pantallas, JS propio sin librerías.

**Storage**: PostgreSQL 16 en Docker. Tabla nueva `informes_firmaprofesional`; migración
`informes/migrations/0003_firmaprofesional.py`. Sin archivos subidos (Render borra el disco).

**Testing**: pytest 9.1.1 + pytest-django 4.14.0; fixtures de `estudios/tests/conftest.py` (las importa
`informes/tests/conftest.py`) más una fixture nueva `firma` / `bioquimico_con_firma`; PDF
reales con WeasyPrint en los tests; ruff 0.17.1.

**Target Platform**: Contenedor Linux (`web`, `python:3.12-slim`) con Docker Compose; CI en
`ubuntu-latest`; navegador de escritorio y móvil (firma con el dedo).

**Project Type**: Aplicación web Django monolítica con templates en el servidor (sin SPA).

**Performance Goals**: Encontrar y descargar un informe en menos de 30 s (SC-001); PDF de un
informe de ≤ 90 pruebas en ≈ 1–2 s; listado paginado con una consulta.

**Constraints**: PDF e impresión siempre desde `Informe.contenido` (FR-006/018); mismos datos que la
pantalla (SC-002); firma ≤ 64 KB en la base; ninguna otra dependencia de Python; las mismas
librerías del sistema en Dockerfile y CI; nada de `float` (principio IV, los valores ya son texto).

**Scale/Scope**: 1 modelo + 1 migración, `Informe.save/delete` bloqueados, 3 módulos nuevos
(`firmas.py`, `busqueda.py`, `pdf.py`) + `forms.py`, cambios en `contenido.py` y `servicios.py`, 4
vistas nuevas (`emitidos`, `pdf`, `imprimir`, `mi_firma`) y cambios en `ver` y `vista_previa`, 5
templates nuevos + 3 cambiados, 2 JS, 1 CSS, 3 íconos, `Dockerfile`, `ci.yml`, `requirements.txt`,
`CLAUDE.md` y tests.

Decisiones en [research.md](./research.md) (R1–R9). No hay `NEEDS CLARIFICATION` pendientes.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Cumplimiento | Estado |
|---|---|---|
| **I. Spec primero (SDD)** | Spec de US 7.3 (SCRUM-59) con decisiones del usuario en Clarifications (2026-11-02). Aprobada por el equipo el 2026-11-02. PR: «US 7.3 – Consultar y exportar informe». | ✅ |
| **II. Simplicidad y Django idiomático** | Una sola dependencia nueva, WeasyPrint, que la constitution reserva para «informes en PDF» y se justifica en R1. Templates de Django para PDF e impresión; `BinaryField` en lugar de almacenamiento externo; JS propio mínimo (canvas e impresión), sin SPA. | ✅ |
| **III. Tests obligatorios** | Cada escenario y FR con test (ver [Mapa de tests](#mapa-de-tests)), incluidos PDF reales en CI y la validación del PNG con casos conocidos. | ✅ |
| **IV. Integridad de datos** | El informe emitido no se edita ni se borra (`save`/`delete` bloqueados, sin admin); PDF e impresión desde la copia; la firma se copia al emitir; estudio, muestra y cliente con `PROTECT`. | ✅ |
| **V. Seguridad** | `LoginRequiredMiddleware`; «Mi firma» con `@permission_required(raise_exception=True)` y cada usuario solo edita la suya (`request.user`); la emisión revalida firma y permiso en el servicio; PNG validado en el servidor (tamaño, firma, dimensiones); POST con CSRF. | ✅ |
| **VI. Idioma y consistencia** | `FirmaProfesional`, `leer_firma`, `informes_emitidos`, `generar_pdf`, `matricula`; interfaz en español; ruff. | ✅ |
| **Interfaz (UI)** | Pantallas con `templates/ui/`; la hoja A4 propia es un documento, no una pantalla, y repite la paleta de SCRUM-67 en hex. | ✅ |

**Post-diseño (Phase 1)**: cumple todos los principios, sin excepciones nuevas.

## Diseño

### Flujo

```text
Menú Informes → Informes emitidos
GET  /informes/emitidos/?q=&desde=&hasta=     → informes_emitidos() sobre KT(contenido…) → tabla → Ver
GET  /informes/estudios/<pk>/informe/          → documento.html + firma.html · [Descargar PDF] [Imprimir]
GET  /informes/estudios/<pk>/informe/pdf/      → render impreso.html(pdf=True) → WeasyPrint + informe.css
                                                  → attachment INF-000001.pdf
GET  /informes/estudios/<pk>/informe/imprimir/ → impreso.html + <link informe.css> + imprimir.js (window.print)

Barra superior → Mi firma (solo emitir_informes)
GET|POST /informes/mi-firma/                   → canvas (firma.js) → data URL → leer_firma() → FirmaProfesional

Emisión (US 7.2, cambio)
vista_previa: armar_contenido(estudio, request.user) · sin firma → aviso «Cargar mi firma»
emitir_informe: permiso → firma (o EmitirInformeError) → estudio_listo_bloqueado → lock → número
                → armar_contenido(estudio, usuario) con contenido["firma"] → Informe → «Informe generado»
```

Rutas y mensajes en [contracts/consultar-exportar-informe-ui.md](./contracts/consultar-exportar-informe-ui.md);
modelo y formularios en [data-model.md](./data-model.md).

### Hoja A4 (`static/css/informe.css`)

```css
@page { size: A4; margin: 18mm 15mm 20mm;
        @bottom-center { content: string(numero) " · Página " counter(page) " de " counter(pages); } }
.inf-numero { string-set: numero content(); }
.inf-tabla thead { display: table-header-group; }
.inf-tabla tr, .inf-firma { break-inside: avoid; }
@media print { .inf-barra { display: none; } }
```

Solo CSS 2.1 + Paged Media, colores hex de la paleta, Inter por `@font-face` relativo (R2).

### Mapa de tests

| Escenario / requisito | Test | Archivo |
|---|---|---|
| US1 Esc. 1, FR-001/002 — menú, listado ordenado con columnas, paginado | `test_menu_informes_emitidos`, `test_listado_columnas_y_orden`, `test_paginacion_conserva_filtros` | `informes/tests/test_emitidos.py` |
| US1 Esc. 2, FR-003 — por número con y sin «INF-» y ceros | `test_busca_por_numero` (parametrizado: `INF-000002`, `inf-2`, `2`, `0002`) | `informes/tests/test_busqueda.py` |
| US1 Esc. 3, FR-003 — por nombre/razón social sin tildes y documento; usa la copia | `test_busca_por_cliente`, `test_busca_por_documento`, `test_busca_por_datos_guardados` | `informes/tests/test_busqueda.py` |
| US1 Esc. 4 — por N° PI | `test_busca_por_numero_pi` | `informes/tests/test_busqueda.py` |
| US1 Esc. 5, FR-004 — rango de fechas inclusivo, combinado | `test_filtra_por_fechas`, `test_fechas_y_busqueda_combinadas` | `informes/tests/test_busqueda.py` |
| US1 Esc. 6, Edge — sin coincidencias / sin informes | `test_listado_vacio` (parametrizado) | `informes/tests/test_emitidos.py` |
| US1 Esc. 7, FR-005 — abrir: documento desde la copia con exportar | `test_ver_ofrece_pdf_e_imprimir` | `informes/tests/test_ver.py` |
| US1 Esc. 8, FR-004 — fecha inválida o rango invertido | `test_fechas_invalidas` (parametrizado) | `informes/tests/test_emitidos.py` |
| US2 Esc. 1, FR-006 — PDF A4, adjunto con nombre | `test_pdf_descarga_a4` (`%PDF`, `Content-Disposition`, tamaño de página 595 × 842 pt) | `informes/tests/test_pdf.py` |
| US2 Esc. 2, FR-008, SC-002 — mismos datos en pantalla, impreso y PDF | `test_impreso_contiene_todo_el_contenido`, `test_pantalla_contiene_todo_el_contenido`, `test_pdf_sale_de_impreso` | `informes/tests/test_impreso.py`, `test_pdf.py` |
| US2 Esc. 3, FR-015 — firma, nombre, matrícula, fecha y número | `test_impreso_con_firma` | `informes/tests/test_impreso.py` |
| US2 Esc. 4, FR-010 — informe anterior «Sin firma registrada» | `test_sin_firma_registrada` (pantalla, impreso y PDF) | `informes/tests/test_impreso.py`, `test_pdf.py` |
| US2 Esc. 5, FR-007 — imprimir: página independiente, sin menú, con `informe.css` | `test_imprimir_pagina_independiente` | `informes/tests/test_impreso.py` |
| US2 Esc. 6, FR-009 — muchas pruebas: más de una hoja; reglas de corte y pie en la hoja | `test_pdf_varias_hojas`, `test_hoja_de_estilos_paged_media` | `informes/tests/test_pdf.py` |
| US2 Esc. 7, SC-004 — editar cliente, catálogo, settings o firma no cambia el PDF | `test_exportacion_no_cambia_al_editar` | `informes/tests/test_impreso.py` |
| US3 Esc. 1–2, FR-011/013 — Mi firma muestra y guarda | `test_mi_firma_muestra_actual`, `test_guarda_firma_y_matricula` | `informes/tests/test_mi_firma.py` |
| US3 Esc. 3, FR-012 — vacía, sin matrícula, inválida, grande | `test_rechaza_firma_invalida` (parametrizado), `test_leer_firma` (casos: prefijo, base64, tamaño, firma PNG, IHDR) | `informes/tests/test_mi_firma.py`, `test_firmas.py` |
| US3 Esc. 5 — reemplazar firma / solo matrícula; emitidos no cambian | `test_reemplaza_firma`, `test_solo_matricula_conserva_imagen` | `informes/tests/test_mi_firma.py` |
| US3 Esc. 6 — sin permiso: sin enlace y 403 | `test_mi_firma_sin_permiso_403`, `test_enlace_mi_firma_solo_con_permiso` | `informes/tests/test_mi_firma.py` |
| US3 Esc. 7, FR-014 — sin firma: aviso en vista previa y el servicio rechaza | `test_vista_previa_sin_firma_ofrece_cargarla`, `test_emitir_sin_firma_rechaza` | `informes/tests/test_vista_previa.py`, `test_servicio_emision.py` |
| US3 Esc. 8, FR-015/016 — al emitir copia firma, nombre (o correo) y matrícula; vista previa la muestra | `test_emitir_copia_firma`, `test_nombre_sin_full_name_usa_email`, `test_vista_previa_muestra_firma` | `informes/tests/test_servicio_emision.py`, `test_contenido.py`, `test_vista_previa.py` |
| US4 Esc. 1, FR-017 — sin admin; `save`/`delete` bloqueados | `test_informe_no_registrado_en_admin`, `test_informe_no_se_modifica`, `test_informe_no_se_borra` | `informes/tests/test_modelos.py` |
| US4 Esc. 2 — estudio, muestra y cliente protegidos | `test_no_se_borran_estudio_muestra_ni_cliente` | `informes/tests/test_modelos.py` |
| US4 Esc. 3, FR-018 — exportar no escribe nada | `test_exportar_no_modifica` (`django_assert_num_queries` sin escrituras / sin cambios) | `informes/tests/test_pdf.py` |
| Edge — informe inexistente → 404 en ver, pdf e imprimir | `test_sin_informe_404` (parametrizado) | `informes/tests/test_ver.py` |
| Edge — falla de WeasyPrint → aviso y log | `test_pdf_error_redirige` (parchea `informes.pdf.generar_pdf`) | `informes/tests/test_pdf.py` |
| Tests de la 7.2 — la fixture `bioquimico` emite: se le crea firma | ajustar `bioquimico` (o agregar `bioquimico_con_firma`) en `estudios/tests/conftest.py` | `estudios/tests/conftest.py` |

## Project Structure

### Documentation (this feature)

```text
specs/022-consultar-exportar-informe/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── consultar-exportar-informe-ui.md
├── checklists/
│   └── requirements.md
└── tasks.md              # /speckit-tasks
```

### Source Code (repository root)

```text
requirements.txt                               # + weasyprint==70.0
Dockerfile                                     # + apt: libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz-subset0 fonts-dejavu-core
.github/workflows/ci.yml                       # + mismas librerías (apt) antes de pip; paso «WeasyPrint instalado»
CLAUDE.md                                      # + sección «Consultar y exportar informe (US 7.3)»
static/css/informe.css                         # nuevo: hoja A4 propia (PDF e impresión), sin Tailwind
templates/base.html                            # + enlace «Mi firma» con permiso
templates/ui/menu.html                         # + «Informes emitidos»
templates/ui/iconos/                           # + download.svg, printer.svg, pen-line.svg (Lucide, ISC)
informes/
├── models.py                                  # + FirmaProfesional; Informe.save/delete bloqueados
├── migrations/0003_firmaprofesional.py        # nueva
├── firmas.py                                  # nuevo: leer_firma (data URL → bytes PNG validados)
├── forms.py                                   # nuevo: BuscarInformeForm, FirmaForm
├── busqueda.py                                # nuevo: informes_emitidos(q, desde, hasta)
├── pdf.py                                     # nuevo: generar_pdf(informe) con WeasyPrint
├── contenido.py                               # armar_contenido(estudio, firmante=None) → + "firma"
├── servicios.py                               # emitir_informe exige y copia la firma
├── views.py                                   # + emitidos, pdf, imprimir, mi_firma; ver y vista_previa cambian
├── urls.py                                    # + emitidos/, informe/pdf/, informe/imprimir/, mi-firma/
├── static/informes/firma.js                   # nuevo: canvas con Pointer Events
├── static/informes/imprimir.js                # nuevo: window.print() al cargar
├── templates/informes/
│   ├── emitidos.html                          # nuevo
│   ├── mi_firma.html                          # nuevo
│   ├── impreso.html                           # nuevo: documento HTML completo (PDF e impresión)
│   ├── documento_impreso.html                 # nuevo: parcial con clases inf-*
│   ├── firma.html                             # nuevo: bloque de firma, compartido
│   ├── documento.html                         # + firma.html; «Emitido por» desde contenido.firma
│   ├── ver.html                               # + Descargar PDF, Imprimir, Volver a informes emitidos
│   └── vista_previa.html                      # + aviso sin firma
└── tests/                                     # test_emitidos, test_busqueda, test_pdf, test_impreso, test_mi_firma,
                                               # test_firmas; ajustar test_ver, test_vista_previa, test_servicio_emision,
                                               # test_contenido, test_modelos
estudios/tests/conftest.py                     # bioquimico con firma (los tests de la 7.2 emiten)
```

**Structure Decision**: todo vive en la app `informes`: la firma existe solo para firmar informes,
así que `FirmaProfesional` va ahí y no en `usuarios`. `static/css/informe.css` queda en `static/`
(junto a `aqualab.css` y las fuentes) para que `../fuentes/` resuelva igual en el navegador y en
WeasyPrint.

## Complexity Tracking

Sin violaciones de la constitution.
