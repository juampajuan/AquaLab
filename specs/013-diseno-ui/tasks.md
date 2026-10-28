---

description: "Tareas de SCRUM-67 – Diseño de la interfaz"
---

# Tasks: Diseño de la interfaz

**Input**: Design documents from `/specs/013-diseno-ui/`

**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md),
[data-model.md](data-model.md), [contracts/](contracts/), [quickstart.md](quickstart.md)

**Tests**: obligatorios por el principio III de la constitution. Cada escenario nuevo tiene test; la
suite existente debe seguir pasando sin cambios salvo la aserción indicada en T029 (research R8).

**Organization**: tareas agrupadas por historia de usuario de la spec.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: se puede hacer en paralelo (archivos distintos, sin dependencias pendientes)
- **[Story]**: historia de la spec (US1–US4)

---

## Phase 1: Setup (infraestructura de estilos)

**Purpose**: compilar Tailwind sin Node y servir recursos propios.

- [X] T001 Agregar al `Dockerfile` la descarga del CLI standalone de Tailwind 4 a `/usr/local/bin/tailwindcss`, con `ARG TAILWIND_VERSION` (última 4.x estable) y selección del binario por arquitectura (`linux-x64` / `linux-arm64`) (research R1)
- [X] T002 Agregar `STATICFILES_DIRS = [BASE_DIR / "static"]` en `config/settings.py` (research R2)
- [X] T003 [P] Copiar `InterVariable.woff2` (OFL) a `static/fuentes/` (research R5)
- [X] T004 [P] Convertir las 4 imágenes de `specs/013-diseno-ui/stitch/imagenes/` a WebP optimizado (ancho máx. 1600 px, ≈ 150–200 KB) en `static/img/acceso/`, con Pillow en un contenedor temporal (`docker run --rm -v "$PWD":/w python:3.12-slim ...`), sin agregar Pillow a `requirements.txt`; solo se commitean los `.webp` con nombres `laboratorio.webp`, `mesada-muestras.webp`, `toma-de-muestra.webp`, `tubos-pipeta.webp` (research R6, R6b)
- [X] T005 [P] Copiar los íconos SVG de Lucide (ISC) que usan las maquetas a `templates/ui/iconos/` (inicio, usuarios, buscar, agregar usuario, matraz, microscopio, cerrar sesión, flecha, reloj, alerta, info, check, lápiz, x, sobre, calendario, gota, documento, menú, ojo) (research R5)
- [X] T006 Crear `static/src/aqualab.css`: `@import "tailwindcss" source(none)`, `@source` de `templates/`, `*/templates/`, `*/forms.py` y `*/static/**/*.js`, `@font-face` de Inter y `@theme` con los tokens de `stitch/DESIGN.md` (colores, tipografía, radios, sombras, colores de estado) (research R3, R4)
- [X] T007 Agregar al job `ruff-y-tests` de `.github/workflows/ci.yml` un paso que descarga el mismo binario (misma `TAILWIND_VERSION`), recompila `static/css/aqualab.css` y falla con `git diff --exit-code` si difiere (research R2)

---

## Phase 2: Foundational (componentes base)

**Purpose**: clases de componentes y parciales que usan todas las pantallas.

**⚠️ CRITICAL**: ninguna pantalla se migra antes de terminar esta fase.

- [ ] T008 Definir en `@layer components` de `static/src/aqualab.css`: `btn`, `btn-primario`, `btn-secundario`, `btn-peligro`, `btn-link`, `tarjeta`, `tabla`, `segmentado` y los nombres heredados `form-control`, `form-select`, `is-invalid` (campos con borde visible, foco visible en cian, error en rojo) (contracts/componentes-ui.md, research R7)
- [ ] T009 [P] Crear `templates/ui/icono.html` (incluye `ui/iconos/<nombre>.svg` con clase opcional) y `templates/ui/iniciales.html`
- [ ] T010 [P] Crear `templates/ui/estado.html` (etiqueta con `tipo` success/neutral/info/warning/danger) (data-model: estados y colores)
- [ ] T011 [P] Crear `templates/ui/campo.html` conservando `id="{{ field.auto_id }}_error"` con un `<div>` por error y `{{ field.auto_id }}_helptext`; asterisco si `field.field.required`; soporte de `RadioSelect` como `segmentado`
- [ ] T012 [P] Crear `templates/ui/errores_form.html` (`non_field_errors`) y `templates/ui/mensajes.html` (éxito, error, advertencia, info; botón cerrar)
- [ ] T013 [P] Crear `static/js/aqualab.js`: cerrar mensajes y abrir/cerrar el menú en pantallas angostas (research R11)
- [ ] T014 Compilar por primera vez `static/css/aqualab.css` y commitearlo

**Checkpoint**: tema, componentes y parciales base listos.

---

## Phase 3: User Story 1 - Navegar con una estructura clara (Priority: P1) 🎯 MVP

**Goal**: layout interno con menú por módulo y layout de acceso con imágenes que alternan.

**Independent Test**: iniciar sesión y recorrer todas las secciones desde el menú; abrir login y
registro sin sesión.

### Tests for User Story 1

- [ ] T015 [P] [US1] Crear `config/tests/__init__.py` y `config/tests/test_layout.py`: pantalla interna muestra menú con Inicio, Buscar cliente, Registrar cliente, Registrar muestra y Crear estudio, nombre del usuario y "Cerrar sesión"; el subítem de la URL actual tiene `aria-current="page"` (probar con buscar cliente y registrar muestra); login y registro no muestran el menú; ninguna página carga recursos de `cdn.jsdelivr.net`, `cdn.tailwindcss.com` ni `fonts.googleapis.com`; todas enlazan `css/aqualab.css`
- [ ] T016 [P] [US1] En `config/tests/test_layout.py`: el login renderiza las 4 imágenes de `img/acceso/` y el CSS compilado contiene la regla `prefers-reduced-motion` (FR-022)
- [ ] T017 [P] [US1] En `usuarios/tests/`: con cuenta pendiente, el login marca el aviso como advertencia (clase/atributo de advertencia) y con credenciales inválidas como error; el texto de ambos no cambia (FR-023, research R14)

### Implementation for User Story 1

- [ ] T018 [P] [US1] Crear `templates/ui/menu.html` con `request.resolver_match` y `aria-current="page"` en el subítem activo (research R9)
- [ ] T019 [P] [US1] Crear `templates/ui/encabezado.html` (migas, título, subtítulo)
- [ ] T020 [US1] Reescribir `templates/base.html`: menú lateral fijo desde `lg`, barra superior con `ui/iniciales.html` + nombre + "Cerrar sesión" (form POST con CSRF), botón de menú en pantallas angostas, `ui/mensajes.html`, bloques `title`/`encabezado`/`content`; conservar `data-contenido-sensible` y los includes de la guardia de sesión; quitar Bootstrap (research R11, R12)
- [ ] T021 [US1] Crear `templates/base_acceso.html`: panel izquierdo con las 4 imágenes apiladas y animación CSS de 28 s (7 s c/u, fundido ~1 s), `prefers-reduced-motion` con imagen fija, degradado, textura de puntos, logo y frase; contenido a la derecha; guardia de sesión (research R6b)
- [ ] T022 [US1] Ajustar las clases del botón "Reintentar" en `templates/includes/guardia_sesion.html` a `btn btn-primario`
- [ ] T023 [US1] Agregar a `FormularioInicioSesion` en `usuarios/forms.py` la propiedad `cuenta_pendiente` (research R14)
- [ ] T024 [US1] Migrar `usuarios/templates/usuarios/login.html` a `base_acceso.html` (maquetas `stitch/login/` y `stitch/login-pendiente/`): aviso ámbar si `form.cuenta_pendiente`, rojo en otro caso; link "¿No tenés cuenta? Crear cuenta"

**Checkpoint**: navegación y acceso con el nuevo diseño; T015–T017 en verde.

---

## Phase 4: User Story 2 - Formularios y confirmaciones consistentes (Priority: P1)

**Goal**: todas las altas, la edición y sus confirmaciones con los mismos componentes.

**Independent Test**: recorrer cada flujo con datos válidos e inválidos; confirmar, volver y cancelar.

### Tests for User Story 2

- [ ] T025 [P] [US2] En `clientes/tests/`: registrar y editar cliente dibujan `tipo_documento` como radios DNI / CUIT sin opción vacía, y un alta con CUIT sigue funcionando (research R8)
- [ ] T026 [P] [US2] En `muestras/tests/`: `tipo_vertido` se dibuja como radios con Agua `checked` por defecto
- [ ] T053 [P] [US2] En `config/tests/test_componentes.py`: los campos obligatorios llevan el marcador de obligatorio y los opcionales no (registrar cliente: Tipo de documento, Número de documento y Correo electrónico sí, Teléfono y Domicilio no; registrar muestra: Sitio de extracción sí, Nombre de la muestra no; crear cuenta: todos sí) (US2 escenario 1)
- [ ] T054 [P] [US2] En `config/tests/test_componentes.py`: las 5 confirmaciones (registro de usuario, alta y edición de cliente, muestra y estudio) contienen `data-componente="resumen"` y `data-componente="acciones-confirmacion"`; la contraseña no aparece en el resumen del registro (US2 escenario 3)
- [ ] T055 [P] [US2] En `config/tests/test_componentes.py`: un mensaje de éxito, uno de error y uno de información se dibujan con `data-nivel="exito"`, `"error"` e `"info"` respectivamente, cada uno con botón de cerrar (US2 escenario 5, FR-010)

### Implementation for User Story 2

- [ ] T027 [P] [US2] Crear `templates/ui/seccion_form.html`, `templates/ui/resumen.html` y `templates/ui/acciones_confirmacion.html` (contracts/componentes-ui.md)
- [ ] T028 [P] [US2] `clientes/forms.py`: `tipo_documento` con `RadioSelect` y opciones DNI / CUIT sin vacío (research R8)
- [ ] T029 [P] [US2] `muestras/forms.py`: `tipo_vertido` con `RadioSelect`; adaptar en `muestras/tests/test_registro.py` (línea ~87) la aserción del valor por defecto de `<select>` a radio `agua` `checked` (research R8)
- [ ] T030 [P] [US2] Migrar `usuarios/templates/usuarios/registro_form.html` a `base_acceso.html` (maqueta `stitch/crear-cuenta/`): nombre y apellido en una fila, link "¿Ya tenés cuenta? Iniciar sesión"
- [ ] T031 [P] [US2] Migrar `usuarios/templates/usuarios/registro_confirmar.html` (maqueta `stitch/confirmar-registro/`), conservando el input oculto `accion` y el botón que se deshabilita al enviar
- [ ] T032 [P] [US2] Migrar `usuarios/templates/usuarios/registro_recibido.html` (maqueta `stitch/registro-recibido/`): ícono de espera grande, mensaje, botón "Iniciar sesión" y el contenido alternativo sin registro en curso
- [ ] T033 [P] [US2] Migrar `clientes/templates/clientes/registro_form.html` (maqueta `stitch/registrar-cliente/`): secciones Identificación y Contacto
- [ ] T034 [P] [US2] Migrar `clientes/templates/clientes/registro_confirmar.html` con `ui/resumen.html` y `ui/acciones_confirmacion.html`
- [ ] T035 [P] [US2] Migrar `clientes/templates/clientes/editar_form.html` y `clientes/templates/clientes/editar_confirmar.html`
- [ ] T036 [US2] Migrar `muestras/templates/muestras/registro_form.html` (maqueta `stitch/registrar-muestra/`): 3 secciones, mini-ficha, `segmentado`; conservar `id="ficha-cliente"`, `data-ficha`, `clientes-muestra`, `mostrar-origen-nuevo`, `bloque-origen-nuevo`; borrar `muestras/templates/muestras/_campo.html` y usar `ui/campo.html`
- [ ] T037 [P] [US2] Migrar `muestras/templates/muestras/registro_confirmar.html` (badge "Ingresada")
- [ ] T038 [P] [US2] Migrar `estudios/templates/estudios/crear_form.html` y `estudios/templates/estudios/crear_confirmar.html` (maqueta `stitch/confirmar-estudio/`), incluida la variante "Recuperar solicitud"

**Checkpoint**: todos los formularios y confirmaciones migrados; suite completa en verde.

---

## Phase 5: User Story 3 - Consultar información de un vistazo (Priority: P2)

**Goal**: búsqueda, ficha y estados legibles.

**Independent Test**: buscar con y sin resultados, paginar, abrir fichas de clientes activos e inactivos.

### Tests for User Story 3

- [ ] T039 [P] [US3] En `clientes/tests/`: la ficha de un cliente inactivo muestra la etiqueta "Inactivo" con el tipo `neutral` y la de uno activo "Activo" con `success`; la búsqueda sin resultados muestra el estado vacío (`data-componente="estado-vacio"`) con el texto actual; la búsqueda con resultados muestra la cantidad y un link "Ver ficha" por fila (US3 escenarios 1, 2 y 4)
- [ ] T056 [P] [US3] En `clientes/tests/`: la ficha tiene un encabezado `<h1>` con el nombre o razón social del cliente y, junto a él, su etiqueta de estado; los datos vacíos se muestran como "—"; están los botones "Editar cliente" y "Volver a la búsqueda" (US3 escenario 3)

### Implementation for User Story 3

- [ ] T040 [P] [US3] Crear `templates/ui/estado_vacio.html` y `templates/ui/paginacion.html`
- [ ] T041 [US3] Migrar `clientes/templates/clientes/buscar.html` (maqueta `stitch/buscar-cliente/`): tabla en tarjeta con `overflow-x-auto`, iniciales, "Ver ficha" sin cortes de línea, paginación y estado vacío
- [ ] T042 [US3] Migrar `clientes/templates/clientes/detalle.html` (maqueta `stitch/ficha-cliente/`): encabezado con nombre y estado, migas "Clientes > Buscar cliente > Ficha del cliente", grilla de datos con "—" en vacíos, botones

**Checkpoint**: consulta de clientes con el nuevo diseño.

---

## Phase 6: User Story 4 - Panel de inicio (Priority: P3)

**Goal**: accesos rápidos, tres indicadores y últimas muestras.

**Independent Test**: con datos cargados los valores coinciden; con base vacía, ceros y estado vacío.

### Tests for User Story 4 (escribir primero, deben fallar)

- [ ] T043 [P] [US4] `config/tests/test_inicio.py`: los 4 accesos rápidos enlazan a sus URLs; "Muestras sin estudio" cuenta solo muestras sin estudios; "Muestras ingresadas hoy" usa `timezone.localdate()` y excluye otras fechas; "Estudios pendientes de análisis" cuenta ese estado; la tabla muestra las 5 más recientes por N° PI descendente con PI, cliente, origen, fecha `d/m/Y` y estado; sin muestras: indicadores en 0 y estado vacío con link a "Registrar muestra"; el inicio sigue exponiendo `huella_sesion` en el contexto; sin sesión redirige al login; la cantidad de consultas del inicio es la misma con 1 y con 6 muestras (sin N+1; `django_assert_num_queries` comparando ambos casos)

### Implementation for User Story 4

- [ ] T044 [US4] Crear `config/views.py` con la vista `inicio` (consultas de data-model.md) y cambiar en `config/urls.py` la ruta `""` a `views.inicio` con `name="inicio"` (research R10)
- [ ] T045 [US4] Reescribir `templates/inicio.html` (maqueta `stitch/inicio/`): banner con `img/acceso/laboratorio.webp` y degradado, 4 tarjetas con bloque de color e ícono, 3 indicadores, tabla de últimas muestras con `ui/estado.html` y `ui/estado_vacio.html`

**Checkpoint**: las cuatro historias funcionan; suite completa en verde.

---

## Phase 7: Polish & cierre

- [ ] T046 Recompilar `static/css/aqualab.css`, verificar que `git diff --exit-code` no reporte cambios tras recompilar y que pese menos de 60 KB
- [ ] T047 [P] `README.md`: stack con Tailwind CSS 4, sección "Estilos (Tailwind)" (compilar, `--watch`, recompilar antes de commitear, componentes de `templates/ui/` y clases heredadas `form-control`/`form-select`/`is-invalid`), estructura con todas las apps y corrección de "una app por módulo"
- [ ] T048 ~~`CLAUDE.md`~~ Eliminada: por decisión del equipo `CLAUDE.md` solo lista pendientes de US; la guía de estilos va en el README (T047)
- [ ] T049 Correr `pytest`, `ruff check .` y `ruff format --check .` en Docker
- [ ] T050 Recorrer [quickstart.md](quickstart.md) en el navegador (pasos 1–14), incluidas ventana de 375 px, modo sin red, navegación con teclado, imágenes que alternan y contraste con Lighthouse (SC-006)
- [ ] T051 Traer `main` a la rama y, solo para las US 5.2–5.5 ya mergeadas en ese momento, adaptar con los componentes de `templates/ui/` las pantallas de las US 5.2–5.5 que ya estén integradas; resolver el conflicto de `templates/base.html` agregando sus links a `templates/ui/menu.html` (research R16)
- [ ] T052 Abrir el PR "SCRUM-67 – Diseño de la interfaz" referenciando `specs/013-diseno-ui/` y la enmienda v1.1.0 de la constitution (requiere aprobación de la mayoría del equipo)

---

## Dependencies & Execution Order

- **Setup (T001–T007)** → **Foundational (T008–T014)** → historias.
- **US1 (T015–T024)** primero: `base.html` y `base_acceso.html` son la base de todas las pantallas.
- **US2, US3 y US4** dependen de US1 y son independientes entre sí.
- Dentro de cada historia: tests antes que implementación.
- **Polish (T046–T052)** al final; T051 depende de lo que el equipo haya mergeado.

```text
T001 ─┬─ T006 ─ T008 ─ T014 ─ US1 ─┬─ US2
T002 ─┤                            ├─ US3
T003..T005 ─┘                      └─ US4 ─ Polish
T007 (CI) en paralelo con Phase 2
```

## Parallel Example

```text
Phase 2: T009, T010, T011, T012, T013 a la vez.
US2:     T030, T031, T032, T033, T034, T035, T037, T038 a la vez (un template cada uno).
Tests:   T053, T054, T055 (US2) y T039, T056 (US3) se escriben juntos antes de migrar las pantallas.
```

## Implementation Strategy

1. **MVP**: Setup + Foundational + US1 → la app ya tiene el layout nuevo y el login.
2. Sumar US2 (formularios) → US3 (consulta) → US4 (panel), corriendo la suite al terminar cada una.
3. Cierre: CSS al día, documentación, quickstart y adaptación de 5.2–5.5 antes del PR.
