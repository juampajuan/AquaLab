---

description: "Lista de tareas de la US 8.3 – Panel del laboratorio"
---

# Tasks: Panel del laboratorio

**Input**: `specs/027-panel-laboratorio/` (`plan.md`, `spec.md`, `research.md`, `data-model.md`,
`contracts/dashboard-ui.md`, `quickstart.md`)

**Prerequisites**: rama `026-datos-demo` (SCRUM-78): `estudios.demo.cargar_demo(salida, ahora=...)`
para los tests integrales; de `main`, el grupo «Bioquímicos» (`estudios.0008`), «Administradores»
(`usuarios.0004`), `Informe` con `fecha_emision` (US 7.2), `Medicion.fecha_carga`/`fecha_correccion`,
`Validacion.fecha_validacion` (US 6.4), `templates/ui/` (`indicador.html`, `estado.html`,
`estado_vacio.html`, `encabezado.html`) y las fixtures de `estudios/tests/conftest.py`.

**Tests**: SÍ. La constitution (principio III) exige un test por escenario. Siguen el «Mapa de
tests» de `plan.md` y se escriben **antes** de la implementación de cada historia (deben fallar
primero).

**Organization**: US1 (P1, volumen del período), US2 (P1, tiempo de respuesta y actividad), US3
(P1, alertas) y US4 (P2, acceso).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: se puede ejecutar en paralelo (archivos distintos, sin dependencias pendientes)
- **[Story]**: user story a la que pertenece la tarea (`[US1]` a `[US4]`)
- Rutas relativas a la raíz del repo

## Convenciones para todas las tareas

- Textos en **español**, copiados **literalmente** de `contracts/dashboard-ui.md`.
- Cálculos solo en `informes/tablero.py`; la vista arma el contexto y el template solo dibuja.
- Fechas en la zona del laboratorio: `TruncDate`/`TruncMonth`/`TruncWeek` con
  `tzinfo=timezone.get_current_timezone()`; `hoy = timezone.localdate()`. Nunca `float`: promedios
  con `Decimal` redondeado a 1 decimal.
- Las funciones de `tablero.py` reciben `hoy`/`ahora` como parámetro para probarlas con fechas fijas.
- Componentes de `templates/ui/`; colores con tokens del tema (`text-exito`, `text-peligro`,
  `text-tinta-suave`). Si se agregan clases nuevas, recompilar el CSS (T022).
- Commits a nombre de la responsable, sin `Co-Authored-By`.
- Comandos dentro de Docker: `docker compose exec web pytest informes`,
  `docker compose exec web ruff check .`, `docker compose exec web ruff format --check .`.

---

## Phase 1: Setup

- [ ] T001 **Gate de la constitution (principio I)**: confirmar que el equipo aprobó
  `specs/027-panel-laboratorio/spec.md` y actualizar su `**Status**` a «Aprobada (fecha)»; confirmar
  que la rama sale de `026-datos-demo` (o de `main` si ya se mergeó) y que `pytest` está en verde.
- [ ] T002 [P] Descargar Chart.js 4.4.7 (`https://cdn.jsdelivr.net/npm/chart.js@4.4.7/dist/chart.umd.min.js`)
  a `static/vendor/chart.umd.min.js`, conservando su cabecera de licencia MIT; verificar que no
  carga nada externo.
- [ ] T003 [P] Agregar `templates/ui/iconos/chart-column.svg` (Lucide «chart-column», mismo formato
  que `clock.svg`: `class="{{ clase|default:'size-5' }}" aria-hidden="true" focusable="false"`).

---

## Phase 2: Foundational (bloquea las cuatro historias)

- [ ] T004 Permiso: en `informes/models.py` agregar `("ver_dashboard", "Puede ver el dashboard")` a
  `Informe.Meta.permissions`; generar `informes/migrations/0004_permiso_dashboard.py` con
  `makemigrations` y agregarle una `RunPython` (patrón de `informes/migrations/0002_permiso_bioquimicos.py`:
  `create_permissions` con `models_module` restaurado) que asigna el permiso a «Bioquímicos» y
  «Administradores» (get_or_create de cada grupo); reversa que lo quita. Dependencias:
  `estudios.0008_grupo_bioquimicos` y `usuarios.0004_grupo_administradores`. En
  `estudios/tests/conftest.py`, el fixture `bioquimico` agrega `ver_dashboard` al grupo.
- [ ] T005 Esqueleto de `informes/tablero.py` y su test, según research R2/R4:
  `PERIODOS = {"este_mes": "Este mes", "mes_anterior": "Mes anterior", "ultimos_3": "Últimos 3 meses",
  "ultimos_6": "Últimos 6 meses"}`; `periodo(clave, hoy)` → `Periodo(clave, etiqueta, inicio, fin,
  inicio_anterior, fin_anterior)` (clave inválida → `este_mes`); `variacion(actual, anterior,
  favorable_si_sube=True)` → `Variacion(diferencia, porcentaje, sentido, simbolo, tono)`. En
  `informes/tests/test_tablero.py`: `test_periodos` (parametrizado: 8/11 este mes → 1–8/11 y 1–8/10;
  1/11 → 1/11 y 1/10; 31/3 este mes → anterior 1–28/2 (o 29 en bisiesto); mes anterior;
  últimos 3 al 8/11 → 1/9–8/11 y 1/6–8/8; últimos 6; clave inválida) y `test_variacion`
  (parametrizado: 10 vs 8 → +2, 25 %, ▲, exito; 8 vs 10 → ▼, peligro; 5 vs 5 → =, neutro; 3 vs 0 →
  porcentaje None; tiempo 12,5 vs 10,0 con favorable_si_sube=False → ▲, peligro).

---

## Phase 3: User Story 1 – Ver el volumen de trabajo del período (P1) 🎯 MVP

**Goal**: el panel con los tres indicadores del período elegido, su variación y los estudios por
estado.

**Independent Test**: con datos de fechas conocidas, los conteos y variaciones de cada período
coinciden con el conteo manual (`quickstart.md` pasos 1–3).

### Tests (escribir primero; deben fallar)

- [ ] T006 [P] [US1] En `informes/tests/test_tablero.py`: `test_indicadores_cuentan_por_fecha`
  (muestras por `fecha_ingreso`, estudios por `fecha_creacion`, informes por `fecha_emision`, dentro
  y fuera del período y del anterior; una muestra con dos estudios cuenta 1 muestra y 2 estudios;
  fechas fijadas con `estudios.demo.reloj`), `test_estudios_por_estado` (los 4 estados con su
  cantidad, sin depender del período) y `test_zona_horaria` (un informe emitido el día 31 a las
  23:30 hora de Argentina cuenta en ese día y ese mes).
- [ ] T007 [P] [US1] En `informes/tests/test_dashboard.py`: `test_selector_de_periodo` (sin parámetro
  y con `?periodo=xyz` → «Este mes» elegido; con `ultimos_6` → elegido y textos del rango del
  contrato) y `test_indicadores_en_pantalla` (4 tarjetas con `data-indicador`, variación con flecha,
  signo, `data-tono` y la clase de color del contrato; «sin datos previos» cuando corresponde).

### Implementation

- [ ] T008 [US1] En `informes/tablero.py`: `indicadores(periodo)` (3 `aggregate` con `Count(filter=...)`
  para período y anterior, research R3) y `estudios_por_estado()`. Hace pasar T006.
- [ ] T009 [US1] Vista `dashboard` en `informes/views.py` (`@permission_required("informes.ver_dashboard",
  raise_exception=True)`, `@require_GET`, lee `periodo` del GET), URL `dashboard/` (`name="dashboard"`)
  en `informes/urls.py`, y `informes/templates/informes/dashboard.html` con las secciones 1–3 del
  contrato (encabezado con selector, 4 indicadores, estudios por estado). Hace pasar T007.

**Checkpoint**: el panel muestra el volumen del período (sin gráficos ni alertas todavía).

---

## Phase 4: User Story 2 – Seguir el tiempo de respuesta y la actividad (P1)

**Goal**: tiempo de respuesta del período con variación y los dos gráficos fijos, con sus tablas.

**Independent Test**: promedios y series coinciden con el cálculo manual y no cambian con el período
(`quickstart.md` pasos 3–4, 7).

- [ ] T010 [P] [US2] En `informes/tests/test_tablero.py`: `test_tiempo_de_respuesta` (informes con
  ingreso 1/10 → emisión 11/10 (10 días) y 1/10 → 14/10 (13 días) → 11,5; período sin informes →
  None; variación con `favorable_si_sube=False`) y `test_series_fijas` (6 meses con un valor por mes
  y `None` sin informes; 12 semanas lunes–domingo con muestras e informes por semana; mismo
  resultado para cualquier período).
- [ ] T011 [P] [US2] En `informes/tests/test_dashboard.py`: `test_graficos_y_tablas` (los dos
  `<canvas>` con `role="img"` y `aria-label`, `json_script` `datos-dashboard` con las dos series,
  tablas «Ver datos» con 6 y 12 filas, script `vendor/chart.umd.min.js` servido desde `static`, sin
  URLs externas) y «Sin informes en el período» en la tarjeta de tiempo de respuesta.
- [ ] T012 [US2] En `informes/tablero.py`: `tiempo_respuesta(desde, hasta)` (`Avg` de la fecha local
  de emisión menos `fecha_ingreso`, redondeado a 1 decimal con `Decimal`), `serie_mensual(hoy)` (6
  meses, `TruncMonth`) y `serie_semanal(hoy)` (12 semanas, `TruncWeek`), research R5/R6. Hace pasar
  T010.
- [ ] T013 [US2] Secciones 4–5 del contrato en `informes/templates/informes/dashboard.html` (tarjeta
  de tiempo de respuesta, `<canvas>`, `<details>` con tablas, `json_script`) y
  `informes/static/informes/dashboard.js` (lee `datos-dashboard`; línea de tiempo de respuesta y
  barras agrupadas de muestras e informes con los colores del tema; si `window.Chart` no existe, no
  hace nada y quedan las tablas). Cargar `vendor/chart.umd.min.js` y `informes/dashboard.js` solo en
  esta página. Hace pasar T011.

---

## Phase 5: User Story 3 – Alertas de estudios demorados (P1)

**Goal**: las dos listas de alertas, completas, con enlace a cada estudio.

**Independent Test**: con la demo, «Pozo domiciliario» y «Escuela N° 12» aparecen en su alerta
(`quickstart.md` paso 5).

- [ ] T014 [P] [US3] En `informes/tests/test_tablero.py`: `test_sin_avanzar` (estudio creado hace 10
  días sin pruebas cargadas → aparece; con una carga, una corrección o una validación hace 3 días →
  no; uno Finalizado o con informe → no; días calculados; orden del más antiguo),
  `test_finalizados_sin_informe` (Finalizado sin informe → aparece con días desde la última
  validación vigente; con informe → no) y `test_alertas_con_la_demo` (`cargar_demo` con `ahora` en
  el día 2 del mes: «Pozo domiciliario» del mes anterior en sin avanzar y «Escuela N° 12» en
  finalizados sin informe).
- [ ] T015 [P] [US3] En `informes/tests/test_dashboard.py`: `test_alertas_en_pantalla` (títulos con el
  total, columnas del contrato, enlace «Ver estudio» a `estudios:detalle`, contenedor con
  `data-alerta`; vacías → «No hay estudios en esta situación.»).
- [ ] T016 [US3] En `informes/tablero.py`: `alertas(ahora)` → `sin_avanzar` y `finalizados_sin_informe`
  según research R7 (`Greatest` + `Subquery(Max(...))`, `select_related("muestra__cliente")`, sin
  N+1). Sección 6 del contrato en `informes/templates/informes/dashboard.html` (lista con altura
  máxima y desplazamiento). Hace pasar T014 y T015.

---

## Phase 6: User Story 4 – Solo para Bioquímicos y Administradores (P2)

**Goal**: el panel y su enlace solo con el permiso.

**Independent Test**: técnico sin enlace y con 403; bioquímico y administrador con acceso
(`quickstart.md` pasos 1 y 6).

- [ ] T017 [P] [US4] En `informes/tests/test_dashboard.py`: `test_acceso` (parametrizado: sin sesión →
  302 al login; usuario común → 403 y sin enlace en el menú; solo «Bioquímicos» → 200; solo
  «Administradores» → 200 y enlace debajo de «Inicio» con `aria-current` en el panel) y
  `test_permiso_en_grupos` (ejecuta la función de la migración `0004` y comprueba el permiso en los
  dos grupos).
- [ ] T018 [US4] Enlace «Dashboard» en `templates/ui/menu.html` justo después de «Inicio», dentro de
  `{% if perms.informes.ver_dashboard %}`, con ícono `chart-column` y resaltado con
  `vista == 'informes:dashboard'` (research R9). Hace pasar T017.

---

## Phase 7: Polish & Cross-Cutting Concerns

- [ ] T019 [P] En `informes/tests/test_dashboard.py`: `test_base_vacia` (sin datos: indicadores en 0,
  «Sin informes en el período», tablas con «—» y alertas vacías, 200), `test_solo_lectura` (mismas
  cantidades de filas antes y después de abrir el panel) y `test_cantidad_de_consultas`
  (`django_assert_max_num_queries(15)` con la demo cargada).
- [ ] T020 [P] `CLAUDE.md`: sección «Panel del laboratorio (US 8.3)» (`informes/tablero.py` única
  fuente de los cálculos; períodos y período anterior; última actividad; permiso
  `informes.ver_dashboard` por migración; Chart.js en `static/vendor/` solo en esta página; tablas
  «Ver datos»; la 8.2 suma acá la lista de desvíos).
- [ ] T021 Medir el panel con la demo (< 2 s) y con 10.000 estudios generados en una base local
  (< 5 s), SC-004; anotar el resultado en esta lista.
- [ ] T022 Ejecutar `ruff check .`, `ruff format --check .`, `python manage.py makemigrations --check
  --dry-run` y recompilar Tailwind; si `static/css/aqualab.css` cambia, commitearlo.
- [ ] T023 Ejecutar la suite completa `docker compose exec web pytest`: todo en verde.
- [ ] T024 Recorrer `specs/027-panel-laboratorio/quickstart.md` (pasos 1 a 7) y marcar el resultado aquí.

---

## Dependencies & Execution Order

- **Setup (T001–T003)** → **Foundational (T004–T005)** → historias.
- **US1 (T006–T009)** crea la vista y el template; **US2 (T010–T013)** y **US3 (T014–T016)** agregan
  secciones al mismo template y funciones a `tablero.py`, así que sus implementaciones van después de
  T009 y en orden (mismo archivo). Sus tests pueden escribirse en paralelo.
- **US4 (T017–T018)** depende solo de T004 y T009.
- **Polish (T019–T024)** al final.

```text
T001 → T002/T003 → T004 → T005 → (T006, T007, T010, T011, T014, T015, T017 tests [P])
     → T008 → T009 → T012 → T013 → T016 → T018 → T019/T020 → T021 → T022 → T023 → T024
```

## Parallel Example

```text
# Tests de las cuatro historias (dos archivos: test_tablero.py y test_dashboard.py)
T006, T010, T014   # test_tablero.py
T007, T011, T015, T017   # test_dashboard.py
# Setup
T002 (Chart.js), T003 (ícono)
```

## Implementation Strategy

1. **MVP = US1**: el panel con indicadores, variación y estados ya cumple el objetivo de volumen.
2. **US2** suma el tiempo de respuesta y los gráficos; **US3** las alertas (lo accionable).
3. **US4** cierra el acceso (el permiso existe desde T004, así que la vista ya está protegida).
4. Controles de rendimiento, CI, suite completa y recorrido manual.
