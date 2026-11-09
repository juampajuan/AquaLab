# Implementation Plan: Comparación histórica por origen

**Branch**: `031-comparacion-historica` | **Date**: 2026-11-09 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/031-comparacion-historica/spec.md` (SCRUM-60, US 8.1)

## Summary

Nueva pantalla de solo lectura `estudios:comparacion` (`GET /estudios/comparacion/`), a la que se
llega desde el detalle del estudio (`?estudio=<pk>`, con el estudio como referencia) o desde una
tarjeta nueva del Dashboard que elige cliente y origen (`?cliente=&origen=`). El cálculo vive en
un módulo puro, `estudios/comparacion.py` (`comparar` y `variacion`), que la US 8.2 reutiliza: por
cada prueba arma el historial de resultados validados del origen ordenado por fecha de muestreo,
el punto destacado del estudio actual (validado o no), la franja de límites (con
`pruebas/limites.py`) y la variación del último contra el anterior y contra el promedio de los
anteriores, en `Decimal`. Los gráficos se dibujan con el Chart.js 4.4.7 ya vendorizado, con el
patrón de `dashboard.js` (`json_script` + tabla «Ver datos» por gráfico). Acceso con el permiso del
Dashboard (`informes.ver_dashboard`). Sin tablas ni migraciones.

## Technical Context

**Language/Version**: Python 3.12; JavaScript sin dependencias propias (solo Chart.js).

**Primary Dependencies**: Django 5.2 LTS (ORM, `Prefetch`, formularios, `permission_required`),
Tailwind CSS 4 y `templates/ui/`, Chart.js 4.4.7 en `static/vendor/chart.umd.min.js` (sin
dependencias nuevas: ni adaptador de fechas ni plugin de anotaciones, R7).

**Storage**: PostgreSQL 16. Sin cambios de esquema.

**Testing**: pytest + pytest-django con las fixtures de `estudios/tests/conftest.py`
(`catalogo`, `empleado`, `bioquimico`, `cliente_bioquimico`), los helpers
`estudios.tests.utiles.cargar` y `validar` (servicios reales) más una fábrica nueva
`estudio_en_origen(origen, fecha_muestreo, numero_pi, valores, validar=True)`, la demo de SCRUM-78
(`cargar_demo` con `ahora` fijo) para los casos integrales, `node --test` para la lógica de
datasets del JS (`estudios/tests/js/`), ruff.

**Target Platform**: Contenedor `web` (Docker Compose) y Render; navegador de escritorio.

**Project Type**: Aplicación web Django monolítica con templates en el servidor.

**Performance Goals**: < 2 s con 6 meses y 20 pruebas (SC-005): cantidad fija de consultas
(estudio de referencia + asignaciones, historial del origen con `select_related` y `Prefetch` de la
validación vigente, límites por vertido), sin N+1; un test lo fija con
`django_assert_max_num_queries`.

**Constraints**: Solo lectura (FR-016); valores en `Decimal`, nunca `float` en el servidor (FR-011);
gráficos con tabla equivalente y color nunca como única señal; nada en informe/PDF/correo (FR-017);
CSS compilado al día (CI).

**Scale/Scope**: `estudios/comparacion.py`, dos formularios, vista, URL, templates
`estudios/comparacion.html` + parciales, `estudios/static/estudios/comparacion.js` y
`elegir_origen.js`, botón en `estudios/detalle.html`, tarjeta en `informes/dashboard.html`,
tests (Python y JS), CI (`node --test` suma `estudios/tests/js`), CLAUDE.md.

Decisiones en [research.md](./research.md) (R1–R12). No hay `NEEDS CLARIFICATION` pendientes.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Cumplimiento | Estado |
|---|---|---|
| **I. Spec primero (SDD)** | Spec de US 8.1 en Draft; el código espera su aprobación (y la de `/speckit-clarify` si se corre). | ✅ |
| **II. Simplicidad y Django idiomático** | Sin app ni modelos nuevos; vista de función GET + formularios Django; un módulo de cálculo; reutiliza Chart.js y el patrón del Dashboard; sin plugins (R7). | ✅ |
| **III. Tests obligatorios** | Cada FR y escenario con test (ver [Mapa de tests](#mapa-de-tests)), incluidos los cálculos de R12 y el caso A/P de R11. | ✅ |
| **IV. Integridad de datos** | Solo lectura; `Decimal` sobre el valor completo; respeta el invariante validación vigente ⇔ Completada; los límites se interpretan solo con `pruebas/limites.py`. | ✅ |
| **V. Seguridad** | `LoginRequiredMiddleware` + `@permission_required("informes.ver_dashboard", raise_exception=True)` + `@require_GET`; accesos visibles solo con el permiso; no se expone a clientes (FR-017). | ✅ |
| **VI. Idioma y consistencia** | `comparacion.py`, `comparar`, `HistorialPrueba`, `Variacion`, `Franja`, `ElegirOrigenForm`; interfaz en español; ruff. | ✅ |
| **Interfaz (UI)** | `ui/campo.html` (con `help_text`), `ui/encabezado.html`, `ui/dato.html`, `ui/estado.html`, `ui/estado_vacio.html`, `.tarjeta`, `.tabla`; colores por tokens; acción sin confirmación porque no guarda datos. | ✅ |

**Post-diseño (Phase 1)**: cumple todos los principios, sin excepciones.

## Diseño

```text
estudios:detalle ──[Comparación histórica]──┐  (perms.informes.ver_dashboard)
informes:dashboard ─[cliente → origen]──────┤
                                            ▼
GET /estudios/comparacion/?estudio=|cliente=&origen=  &pruebas=…&elegir=1
  ├─ sin sesión → login; sin permiso → 403; POST → 405; estudio inexistente → 404
  ├─ sin origen válido → ElegirOrigenForm con errores (paso 2 sin JS)
  └─ comparacion.comparar(origen, estudio=…, codigos=elegidas)
        consulta única: Resultado ← asignación Completada ← estudio ← muestra(origen)   (R2)
        + asignaciones del estudio de referencia (con o sin resultado)
        por prueba → HistorialPrueba
            puntos ordenados (fecha_muestreo, N° PI, estudio)                      (R3)
            franja = limites_aplicables(prueba, muestra_ref.tipo_vertido)          (R6)
            variacion(ultimo, anteriores) — Decimal / presencia                     (R4, R5)
     → template estudios/comparacion.html + json_script "datos-comparacion"
     → estudios/comparacion.js (Chart.js: línea + punto destacado + franja)        (R7)
```

### `estudios/comparacion.py` (interfaz para la US 8.2)

- `comparar(origen, *, estudio=None, codigos=None) -> list[HistorialPrueba]`: si `estudio` no es
  `None`, debe ser de `origen` (`ValueError` si no). `codigos=None` → todas las disponibles
  (FR-013). Orden: el del estudio (`prueba__codigo`) o por nombre de prueba.
- `pruebas_disponibles(origen, estudio=None) -> list[Prueba]` para el formulario.
- `variacion(ultimo, anteriores, *, presencia=False) -> Variacion | None` (pura, sin base).
- `franja(prueba, tipo_vertido) -> Franja` (pura sobre `limites_aplicables`).
- Las estructuras son `dataclass(frozen=True)` (ver [data-model.md](./data-model.md)); la 8.2
  podrá usar `HistorialPrueba.variacion` sin tocar la pantalla.

### Archivos

```text
estudios/
├── comparacion.py                 # NUEVO: cálculo (R1–R6)
├── forms.py                       # + ElegirOrigenForm, ElegirPruebasForm
├── views.py                       # + comparacion (GET); validaciones_vigentes() reutilizado
├── urls.py                        # + path("comparacion/", …, name="comparacion")
├── templates/estudios/
│   ├── comparacion.html           # NUEVO
│   ├── comparacion_prueba.html    # NUEVO: tarjeta por prueba (gráfico + Ver datos)
│   ├── variacion_historica.html   # NUEVO: textos de la variación
│   ├── elegir_origen.html         # NUEVO: parcial del selector (lo incluye también el dashboard)
│   └── detalle.html               # + botón «Comparación histórica»
├── static/estudios/
│   ├── comparacion.js             # NUEVO (patrón dashboard.js; funciones puras exportables)
│   └── elegir_origen.js           # NUEVO (filtra orígenes por cliente)
└── tests/
    ├── test_comparacion.py        # NUEVO: cálculo
    ├── test_comparacion_vista.py  # NUEVO: vista, formularios, permisos, accesos
    ├── test_comparacion_demo.py   # NUEVO: Pozo 2 y Tanque domiciliario (R11, R12)
    └── js/comparacion.test.cjs    # NUEVO: datasets, franja, presencia
informes/
├── views.py                       # dashboard: + ElegirOrigenForm y orígenes por cliente
└── templates/informes/dashboard.html  # + tarjeta «Comparación histórica»
.github/workflows/ci.yml           # node --test … estudios/tests/js
static/css/aqualab.css             # recompilado si hay clases nuevas
CLAUDE.md                          # sección «Comparación histórica (US 8.1)»
```

**Structure Decision**: aplicación Django existente; la funcionalidad vive en `estudios` (dueño de
`Resultado` y `Validacion`) y el Dashboard (`informes`) solo incluye el selector, respetando la
dirección de dependencias `informes → estudios → muestras`.

### Demo (pedido del usuario)

La demo **ya tiene** un origen con una prueba Ausente/Presente que cambia de estado: «Tanque
domiciliario», E. Coli Presente en el mes 3 y Ausente en el resto, todo validado (R11). No se
modifica el guion; `test_comparacion_demo.py` fija ese caso para que, si un cambio futuro del guion
lo elimina, el test falle y se agregue al guion (y a `test_demo.py`), como indica CLAUDE.md.

## Mapa de tests

| Requisito / escenario | Test |
|---|---|
| FR-003, Edge «validación anulada», SC-004 | `test_comparacion.py::test_historial_solo_validados` (cargada, anulada, otro origen, otra prueba fuera) |
| FR-004, Edge «fechas iguales» | `::test_orden_por_fecha_de_muestreo_y_numero_pi` |
| FR-005, US1 2–4 | `::test_referencia_destacada_validada_y_sin_validar`, `::test_referencia_sin_resultado` |
| FR-007, US1 5 | `::test_prueba_sin_historial` |
| FR-008, US2 1–4, SC-003 | `::test_variacion_contra_anterior_y_promedio` (100,120,140 → 210), `::test_un_solo_anterior` |
| US2 2 | `::test_ultimo_sin_referencia_es_el_mas_reciente` |
| Edges «referencia antigua», «misma muestra» | `::test_anteriores_solo_de_muestras_previas` |
| FR-009 | `::test_base_cero_sin_porcentaje` |
| FR-010, US2 6 | `::test_variacion_presencia` |
| FR-011 | `::test_decimal_valor_completo` (sin `float`, redondeo 0,1 %) |
| FR-006, Edges límites | `::test_franja_min_max_solo_uno_no_comparable_y_vertido` |
| FR-020 | `::test_otra_unidad_fuera_del_grafico` |
| SC-005 | `::test_consultas_fijas` (`django_assert_max_num_queries`) |
| FR-001, FR-002, US1 1 | `test_comparacion_vista.py::test_boton_en_detalle_solo_con_permiso`, `::test_desde_estudio` |
| FR-012, FR-013, US3 | `::test_seleccion_por_defecto`, `::test_seleccion_en_url`, `::test_seleccion_vacia`, `::test_codigo_desconocido_ignorado` |
| FR-014, US5 | `::test_tabla_ver_datos` (LD, enlaces, «Este estudio»), `::test_json_sin_float` |
| FR-015, US4 | `::test_selector_dashboard`, `::test_origen_de_otro_cliente`, `::test_solo_cliente_paso_dos`, `::test_origen_sin_validados` |
| FR-016, SC-007 | `::test_solo_lectura` (estado de estudios, asignaciones y validaciones igual), `::test_post_405` |
| FR-017 | `::test_no_aparece_en_informe_pdf_ni_correo` |
| FR-018 | `::test_permisos` (sin sesión, sin permiso 403, bioquímico y administrador 200), `::test_estudio_inexistente_404` |
| SC-002, R11, R12 | `test_comparacion_demo.py::test_pozo_2_cloruro`, `::test_tanque_domiciliario_ecoli` |
| R7 | `estudios/tests/js/comparacion.test.cjs` (franja con min/max/uno/ninguno, presencia, punto destacado, `null` en la línea) |

## Complexity Tracking

Sin violaciones de la constitution.
