---

description: "Lista de tareas de SCRUM-60 – 8.1 Comparación histórica por origen"
---

# Tasks: Comparación histórica por origen

**Input**: `specs/031-comparacion-historica/` (`plan.md`, `spec.md`, `research.md`, `data-model.md`,
`contracts/comparacion-ui.md`, `quickstart.md`)

**Prerequisites**: `main` con la US 4.1 (`Origen`, `Muestra.fecha_muestreo`, `numero_pi`,
`tipo_vertido`), US 6.2–6.4 (`Resultado`, `Validacion` vigente ⇔ `Completada`,
`pruebas/limites.py`), US 8.3 (`informes:dashboard`, permiso `informes.ver_dashboard`,
`static/vendor/chart.umd.min.js`, `informes/static/informes/dashboard.js`) y SCRUM-78
(`estudios/demo.py`, `cargar_demo`). Fixtures de `estudios/tests/conftest.py`: `empleado`,
`catalogo`, `bioquimico` (tiene `ver_dashboard`), `cliente_bioquimico`, `cliente_http` (es el mismo
`empleado`), `staff_sin_permiso`; helpers `estudios.tests.utiles.cargar(estudio, usuario, {"CL-": "40"})`
y `validar(estudio, usuario, "CL-")`; `estudios.servicios.crear_estudio`. Cloruro (`CL-`) es
`x*10` con máximo 350 mg/l: una medición de 40 da 400.

**Tests**: SÍ. Principio III: un test por escenario de aceptación (ver «Mapa de tests» de
`plan.md`). Se escriben **antes** de la implementación de cada historia y deben fallar primero.
Incluyen los valores esperados del Pozo 2 (R12) y el caso Ausente/Presente del Tanque domiciliario
(R11).

**Organization**: cinco user stories — US1 (P1, revisar contra la historia desde el estudio), US2
(P1, variación), US3 (P2, elegir pruebas), US4 (P2, desde el Dashboard), US5 (P3, tabla y
contexto). Dos tandas de implementación:

- **Tanda 1** (Fases 1 a 4 — `T001` a `T021`): gate, cálculo (`estudios/comparacion.py`), pantalla
  desde el estudio con gráfico y variación. Cierra el MVP (US1 + US2).
  - Tests de la tanda: `docker compose exec web pytest estudios informes` y
    `node --test estudios/tests/js`.
- **Tanda 2** (Fases 5 a 8 — `T022` a `T040`): selección de pruebas, Dashboard, tabla «Ver
  datos», FR-017, CLAUDE.md, CI.
  - Tests de la tanda: `docker compose exec web pytest estudios informes` y
    `node --test usuarios/tests/js config/tests/js estudios/tests/js`.
- **La suite completa no se corre en las tandas**: la corre el CI en el PR.
- **La prueba en el navegador (`T039`) la hace el autor**: queda sin marcar.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: se puede ejecutar en paralelo (archivos distintos, sin dependencias pendientes)
- **[Story]**: user story a la que pertenece la tarea (`[US1]` … `[US5]`)
- Rutas relativas a la raíz del repo

## Convenciones para todas las tareas

- Textos de la interfaz en **español**, copiados **literalmente** de `spec.md` y
  `contracts/comparacion-ui.md`.
- Solo lectura (FR-016): la vista no llama a servicios que escriben ni usa `select_for_update`.
- `Decimal` en todo el servidor (FR-011): nunca `float`; al JSON los valores van como `str`.
- Límites solo con `pruebas/limites.py` (`limites_aplicables`, `leer_limite`, `evaluar`,
  `bajo_deteccion`); presencia solo con `estudios/mediciones.py` (`es_presencia`,
  `texto_presencia`). `estudios` **no** importa de `informes` (dirección `informes → estudios`).
- Componentes de `templates/ui/` (`ui/encabezado.html`, `ui/dato.html`, `ui/estado.html`,
  `ui/estado_vacio.html`, `ui/campo.html` con `help_text`), `.tarjeta`, `.tabla`, tokens de color;
  si se agregan clases nuevas, recompilar el CSS (T037).
- Commits: `feat(estudios): US 8.1 – Comparación histórica por origen` (Conventional Commits en
  español, CLAUDE.md).

---

## Phase 1: Setup (Tanda 1)

- [X] T001 *(Spec aprobada el 2026-11-09 a pedido del autor; rama sobre `22909fe`. La línea base de `pytest estudios informes` dio 514 en verde y cortó (`-x`) en `test_bioquimico_ve_y_valida` porque leyó `detalle.html` ya editado con el enlace a `estudios:comparacion` antes de que existiera la URL: no es una falla previa; el cierre de la tanda (T021) corre todo.)* **Gate de la constitution (principio I)**: confirmar que el equipo aprobó `specs/031-comparacion-historica/spec.md` y actualizar su `**Status**` a «Aprobada (fecha)». Confirmar que la rama `031-comparacion-historica` sale de `main` (`22909fe` o posterior) y que `docker compose exec web pytest estudios informes` está en verde antes de empezar (no correr la suite completa: la corre el CI).
- [X] T002 En `estudios/tests/conftest.py` agregar la fábrica `estudio_en_origen(empleado, catalogo)` con docstring («Estudio con resultados en un origen y fecha de muestreo dados (US 8.1)»): `crear(origen, fecha_muestreo, numero_pi, valores, *, validar_todo=True, usuario=None, tipo_vertido=TipoVertido.AGUA)` (el parámetro se llama `validar_todo` para no tapar el helper `validar`; un valor `None` deja esa prueba sin medición) crea la `Muestra` (`cliente=origen.cliente`, `fecha_ingreso=fecha_muestreo`, `sitio_extraccion="Sitio test"`, `registrada_por=empleado`, `tipo_vertido` si se pasa), un `TipoEstudio` con las pruebas de `valores` (`{"CL-": "40"}`), el estudio con `crear_estudio` (como `estudio_de`), carga con `estudios.tests.utiles.cargar` y, si `validar`, valida todas con `estudios.tests.utiles.validar` (con `usuario`, por defecto el mismo `empleado` en el grupo «Bioquímicos» vía `en_grupo_bioquimicos`). Devuelve el estudio.

---

## Phase 2: Foundational — cálculo del historial (Tanda 1)

**⚠️ CRITICAL**: es la base de todas las historias y de la US 8.2.

### Tests (deben fallar primero)

- [X] T003 Crear `estudios/tests/test_comparacion.py` con los tests de **historial** (FR-003, FR-004, FR-020, Edge Cases; `@pytest.mark.django_db`, `estudio_en_origen`): `test_historial_solo_validados` (un validado entra; uno cargado sin validar, uno con validación anulada —corregir la medición con `servicios.corregir_mediciones` tras validar—, uno de otro origen del mismo cliente y uno de otra prueba no entran: SC-004); `test_orden_por_fecha_de_muestreo_y_numero_pi` (fechas desordenadas al crear; misma fecha → menor N° PI primero; mismo N° PI → menor `estudio.pk`); `test_varios_estudios_de_una_muestra` (cada resultado validado es un punto); `test_otra_unidad_fuera_del_grafico` (cambiar `Resultado.unidad` de un validado con `Resultado.objects.filter(...).update(unidad="g/l")`: queda en `puntos` con `otra_unidad=True`, fuera de `tiene_historial` y de la variación); `test_estudio_de_otro_origen_es_error` (`comparar(origen, estudio=ajeno)` lanza `ValueError`); `test_pruebas_disponibles` (con estudio: las del estudio por código; sin estudio: las que tienen algún validado en el origen, por nombre).
- [X] T004 [P] En `estudios/tests/test_comparacion.py` agregar los tests de **franja** (FR-006, R6) sobre `franja(prueba, tipo_vertido)` sin base de datos donde se pueda (pruebas en memoria con `limites_vertido` precargados o del `catalogo`): solo máximo (Cloruro: `min=None`, `max=Decimal("350")`, texto «Máximo 350 mg/l · Límite general»); mínimo y máximo (pH 6,4–8,5); solo mínimo; «Ausente» (E. Coli: `presencia=True`, comparable); no comparable (`PH-SAT` «Ph-0,2»: `comparable=False`, «Sin límite comparable»); sin límites (Conductividad: «Sin límite comparable»); vertido (una prueba con `LimiteVertido` cloacal: usa esos límites e indica el vertido).
- [X] T005 [P] En `estudios/tests/test_comparacion.py` agregar `test_consultas_fijas` (SC-005): un origen con 6 muestras × 3 pruebas validadas y un estudio de referencia; `comparar(origen, estudio=...)` con `django_assert_max_num_queries(8)`, y que la cantidad no cambia al pasar a 12 muestras.

### Implementación

- [X] T006 Mover `validaciones_vigentes()` de `estudios/views.py` a `estudios/models.py` como función de módulo junto a `Validacion` (mismo `Prefetch(..., to_attr="validaciones_vigentes")`) y reimportarla en `estudios/views.py` e `informes/` donde se use (`grep -rn validaciones_vigentes`), sin cambiar comportamiento.
- [X] T007 Crear `estudios/comparacion.py` con docstring de módulo («Historial de resultados validados de un origen y su variación (US 8.1). Única definición: la usa la US 8.2.») y las `dataclass(frozen=True)` de `data-model.md`: `Punto` (`fecha_muestreo`, `numero_pi`, `muestra_pk`, `estudio_pk`, `valor: Decimal`, `texto`, `unidad`, `validado`, `evaluacion`, `es_referencia`, `otra_unidad`, propiedad `orden = (fecha_muestreo, numero_pi, estudio_pk)`), `Franja` (`limites`, `minimo`, `maximo`, `presencia`, `comparable`, `texto`), `Cambio`, `Variacion`, `HistorialPrueba`. Implementar `franja(prueba, tipo_vertido)` (R6: `limites_aplicables` + `leer_limite`; `NO_COMPARABLE` en un borde o ningún borde → `comparable=False`, texto «Sin límite comparable»; texto «Máximo … · Límite general» / «Mínimo …» / «Entre … y …» con coma decimal y unidad, «Límite general» o «Vertido <tipo>») y `texto_punto(resultado, limites)` («Ausente»/«Presente» con `texto_presencia`, «< LD» con `bajo_deteccion` como `informes.contenido.texto_resultado` —sin importarlo—, si no `valor_mostrado` con coma).
- [X] T008 En `estudios/comparacion.py` implementar `pruebas_disponibles(origen, estudio=None)` y `comparar(origen, *, estudio=None, codigos=None)` según R2–R3 y el plan: `ValueError` si `estudio.muestra.origen_id != origen.pk`; una consulta de `Resultado` con `asignacion__estado=EstadoPruebaEstudio.COMPLETADA`, `asignacion__estudio__muestra__origen=origen`, excluido `estudio`, filtrada por `codigos`, con `select_related("asignacion__estudio__muestra", "asignacion__prueba")` y `prefetch_related` de `validaciones_vigentes()` (sobre `asignacion`) y `asignacion__prueba__limites_vertido`; las asignaciones del estudio de referencia (con o sin resultado) con `select_related("prueba", "resultado")`; agrupar por código y ordenar por `Punto.orden`. Evaluación de cada punto: la de su validación vigente; la del de referencia sin validar, `evaluar` con `limites_aplicables` (como `evaluar_asignaciones`). Unidad de referencia: la del resultado de referencia, si no la del último validado; `otra_unidad` para el resto. Muestra de referencia para la franja: la del estudio o la del último validado. `sin_resultado=True` si hay estudio y esa prueba no tiene resultado. Orden de salida: el del estudio (`prueba__codigo`, `pk`) o por `prueba.nombre`.
- [X] T009 Ejecutar `docker compose exec web pytest estudios/tests/test_comparacion.py`: T003–T005 en verde (los de variación todavía no existen).

**Checkpoint**: `comparar()` devuelve historial, referencia y franja con consultas fijas.

---

## Phase 3: User Story 2 — Variación del último resultado (Priority: P1) (Tanda 1)

**Goal**: por cada prueba, la variación del último contra el anterior y contra el promedio de los anteriores (criterio 4). Va antes de la pantalla porque la pantalla la muestra y la US 8.2 la reutiliza.

**Independent Test**: con 100, 120, 140 validados y 210 de referencia, `+70 (+50,0 %)` contra el anterior y `+90 (+75,0 %)` contra el promedio 120; y los valores del Pozo 2 y el Tanque domiciliario con la demo.

### Tests (deben fallar primero)

- [X] T010 [US2] En `estudios/tests/test_comparacion.py` agregar los tests de **variación** (FR-008–FR-011): `test_variacion_contra_anterior_y_promedio` (Cloruro con mediciones 10, 12, 14 validadas y 21 de referencia → 100, 120, 140, 210 mg/l: `contra_anterior.diferencia == Decimal("70")`, `porcentaje == Decimal("50.0")`, texto «+70 mg/l (+50,0 %)», flecha «▲»; `promedio == Decimal("120")`, `contra_promedio` «+90 mg/l (+75,0 %)»); `test_baja_con_flecha_abajo` (texto «-… (-… %)», «▼»; igual → «=» y «0 mg/l (0,0 %)»); `test_un_solo_anterior` (las dos variaciones coinciden y existen); `test_sin_anteriores_sin_variacion` (`variacion is None`); `test_ultimo_sin_referencia_es_el_mas_reciente` (sin estudio: último = validado más reciente, anteriores = los previos a él); `test_anteriores_solo_de_muestras_previas` (estudio de referencia antiguo: los posteriores están en `puntos` pero no en la variación; otro estudio validado de la misma muestra tampoco cuenta); `test_referencia_sin_resultado` (sin último del estudio: `variacion is None` y `sin_resultado`); `test_base_cero_sin_porcentaje` (anterior 0 → `porcentaje is None`, texto «+5 mg/l (sin porcentaje: valor previo 0)»; con un parámetro de catálogo que admita 0, p. ej. `NH4`); `test_decimal_valor_completo` (resultados con más de 4 decimales: la diferencia usa el valor completo y el porcentaje se redondea a 0,1 con `ROUND_HALF_UP`; ningún campo es `float`).
- [X] T011 [P] [US2] En `estudios/tests/test_comparacion.py` agregar `test_variacion_presencia` (FR-010) sobre `variacion(..., presencia=True)` con puntos en memoria: Ausente → Presente da `cambio_presencia == "Cambió: Ausente → Presente"`, `presentes`; igual da «Sin cambios (Ausente)»; `contra_anterior is None` y `contra_promedio is None`.
- [X] T012 [P] [US2] Crear `estudios/tests/test_comparacion_demo.py` (fixture `cargada` como `estudios/tests/test_demo.py`: `demo.cargar_demo(io.StringIO(), ahora=dia_2_del_mes())`, importando `dia_2_del_mes`, `estudio` y `mes_de` de `test_demo.py` o moviéndolos a `estudios/tests/utiles.py`) con:
  - `test_pozo_2_cloruro_desde_estudio` (R12): origen «Pozo 2», estudio Físico-químico del mes 0 como referencia → Cloruro con 5 validados `[118, 121, 124, 120, 415]` en orden de fecha de muestreo y la referencia 430 `validado=False`, `es_referencia=True`; `contra_anterior` «+15 mg/l (+3,6 %)»; `promedio == Decimal("179.6")`, `contra_promedio` «+250,4 mg/l (+139,4 %)»; 415 y 430 fuera de norma; `franja.maximo == Decimal("350")`.
  - `test_pozo_2_cloruro_sin_referencia`: último 415; «+295 mg/l (+245,8 %)»; `promedio == Decimal("120.75")`, «+294,25 mg/l (+243,7 %)».
  - `test_tanque_domiciliario_ecoli` (R11): origen «Tanque domiciliario», sin referencia → E. Coli `presencia=True`, textos de los puntos `["Ausente", "Ausente", "Presente", "Ausente", "Ausente"]` (meses 5 a 1), `cambio_presencia == "Sin cambios (Ausente)"`, `presentes == 1` de 4; con el estudio del mes 3 como referencia → «Cambió: Ausente → Presente», `presentes == 0` de 2. Docstring: «Si un cambio del guion elimina este caso, agregarlo de nuevo al guion (CLAUDE.md, SCRUM-78)».
  - `test_comparar_no_modifica` (SC-007): estados de estudios, asignaciones y cantidad de validaciones iguales antes y después de `comparar`.

### Implementación

- [X] T013 [US2] En `estudios/comparacion.py` implementar `variacion(ultimo, anteriores, *, presencia=False)` (R4, R5): `None` sin anteriores; `promedio` en `decimal.localcontext()` con `prec=28`; `Cambio(diferencia, porcentaje, flecha, texto)` con porcentaje `(dif / base * 100).quantize(Decimal("0.1"), ROUND_HALF_UP)` o `None` si la base es 0; diferencia y promedio mostrados con la regla de `Resultado.valor_mostrado` (hasta 4 decimales, sin ceros finales), coma decimal, signo explícito («+», «-», sin signo en 0), unidad con el filtro de unidades si existe en Python (`config/ui.py`) o la misma regla («--»/vacío → sin unidad); presencia: `cambio_presencia` y `presentes`. Conectarla en `comparar` (`anteriores` = validados con la misma unidad y `(fecha_muestreo, numero_pi)` menor al del último; `fuera_de_franja` = evaluación del último `FUERA_DE_NORMA`).
- [X] T014 [US2] Ejecutar `docker compose exec web pytest estudios/tests/test_comparacion.py estudios/tests/test_comparacion_demo.py`: en verde.

**Checkpoint**: el cálculo completo, con los casos de la demo fijados.

---

## Phase 4: User Story 1 — Revisar contra la historia desde el estudio (Priority: P1) 🎯 MVP (Tanda 1)

**Goal**: desde el detalle del estudio se abre la comparación con el gráfico de cada prueba, el resultado actual destacado y la franja del límite.

**Independent Test**: con la demo, el estudio del mes 0 de «Pozo 2» → «Comparación histórica» → Cloruro con los 5 validados y el 430 «Sin validar» destacado, franja hasta 350 y la variación de T012.

### Tests (deben fallar primero)

- [X] T015 [US1] Crear `estudios/tests/test_comparacion_vista.py` con: `test_boton_en_detalle_solo_con_permiso` (con `cliente_bioquimico` el detalle tiene «Comparación histórica» con `href` a `reverse("estudios:comparacion") + "?estudio=<pk>"`; con un empleado sin `informes.ver_dashboard` no); `test_permisos` (sin sesión → redirección al login; `staff_sin_permiso` → 403; usuario del grupo «Administradores» y bioquímico → 200); `test_post_405`; `test_estudio_inexistente_404`; `test_desde_estudio` (encabezado con cliente y origen, ficha con N° PI, tipo (`tipo_nombre_snapshot`), estado y «Volver al estudio»; una tarjeta `data-prueba` por prueba; `<canvas id="grafico-CL-"` con `aria-label`; `datos-comparacion` en un `json_script` con el punto de referencia `"referencia": true, "validado": false`; textos de franja y variación de `contracts/comparacion-ui.md`; «Fuera de la franja del límite» cuando corresponde); `test_referencia_validada` («Validado»); `test_referencia_sin_resultado` («Sin resultado en este estudio» con el gráfico del historial); `test_prueba_sin_historial` («Sin historial para comparar», sin `<canvas>` para esa prueba); `test_json_sin_float` (los valores del JSON son `str`); `test_solo_lectura` (GET no cambia estados ni validaciones).
- [X] T016 [P] [US1] Crear `estudios/tests/js/comparacion.test.cjs` (`node:test`, `vm`, sin dependencias, como `config/tests/js/ayuda.test.cjs`) que cargue `estudios/static/estudios/comparacion.js` con un `window` simulado y pruebe las funciones puras expuestas en `window.AqualabComparacion`: `datasets(prueba, colores)` (línea «Validados» con `null` en el índice de la referencia; dataset «Este estudio» solo en ese índice, `pointStyle: "rectRot"`); `franja(...)` (min+max → `fill: "-1"`; solo máximo → `fill: "start"`; solo mínimo → `fill: "end"`; no comparable → sin datasets; presencia → banda ±0,25 alrededor de 0); `ejeY` en presencia con marcas «Ausente»/«Presente».

### Implementación

- [X] T017 [US1] En `estudios/views.py` agregar `comparacion` con `@permission_required("informes.ver_dashboard", raise_exception=True)` y `@require_GET`: con `estudio` (`get_object_or_404` con `select_related("muestra__cliente", "muestra__origen")`) arma `comparacion.comparar(estudio.muestra.origen, estudio=estudio)`; el contexto lleva `estudio`, `origen`, `cliente`, `historiales` y `datos_graficos` (dict del contrato: por prueba `codigo`, `nombre`, `unidad`, `presencia`, `franja` {`min`, `max` como `str` o `None`, `comparable`}, `puntos` sin los `otra_unidad`, con `etiqueta` «dd/mm/aaaa · PI n», `valor` `str`, `texto`, `validado`, `referencia`). Sin `estudio` (la parte de cliente/origen llega en T029) responder con la pantalla del selector vacía. En `estudios/urls.py`: `path("comparacion/", views.comparacion, name="comparacion")`.
- [X] T018 [US1] Crear `estudios/templates/estudios/comparacion.html` (extiende el layout de las demás pantallas de `estudios`, `ui/encabezado.html` «Comparación histórica», ficha con `ui/dato.html` y `ui/estado.html`), `estudios/templates/estudios/comparacion_prueba.html` (tarjeta `<section class="tarjeta" data-prueba="…">`: título «Nombre (CODIGO)», unidad con `|unidad`, texto de la franja, include de la variación, `<canvas id="grafico-{{ codigo }}" role="img" aria-label="Evolución de {{ nombre }} en {{ origen }}">` dentro de un contenedor con alto fijo como el dashboard; sin historial, `ui/estado_vacio.html` con el valor actual o «Sin resultado en este estudio» y «Sin historial para comparar») y `estudios/templates/estudios/variacion_historica.html` («Contra el anterior (dd/mm/aaaa): …», «Contra el promedio de N anteriores (…): …», en presencia `cambio_presencia` y «Presente en X de N»; `text-peligro` + «Fuera de la franja del límite» solo si `fuera_de_franja`; sin tonos «favorable»). Al final, `{{ datos_graficos|json_script:"datos-comparacion" }}`, `static 'vendor/chart.umd.min.js'` y `static 'estudios/comparacion.js'` con `defer`.
- [X] T019 [US1] Crear `estudios/static/estudios/comparacion.js` con el patrón de `informes/static/informes/dashboard.js` (IIFE, `"use strict"`, `color()` desde tokens CSS, sin Chart.js no hace nada): funciones puras `datasets`, `franja`, `ejeY` expuestas en `window.AqualabComparacion` (R7); por cada `canvas[id^="grafico-"]` dibuja un `line` con eje X de categorías (`etiqueta`), «Validados» (`spanGaps: true`, color `--color-marino`), «Este estudio» (`--color-cian`, radio mayor, etiqueta «Este estudio (Sin validar)» o «(Validado)»), la franja (`--color-exito` translúcido) y tooltip con `texto` + unidad + «Validado»/«Sin validar»; en presencia el eje Y de 0 a 1 con marcas «Ausente»/«Presente».
- [X] T020 [US1] En `estudios/templates/estudios/detalle.html` agregar el botón secundario «Comparación histórica» en la barra de acciones, dentro de `{% if perms.informes.ver_dashboard %}`, con `href="{% url 'estudios:comparacion' %}?estudio={{ estudio.pk }}"`.
- [X] T021 [US1] **Cierre de la tanda 1**: ejecutar `docker compose exec web pytest estudios informes` y `node --test estudios/tests/js`, más `docker compose exec web ruff check .` y `ruff format --check .`: en verde. No correr la suite completa.

**Checkpoint (MVP)**: desde un estudio se ve la evolución de cada prueba con la referencia destacada, la franja y la variación.

---

## Phase 5: User Story 3 — Elegir qué pruebas ver (Priority: P2) (Tanda 2)

**Goal**: elegir varias pruebas a la vez; la selección queda en el enlace.

**Independent Test**: estudio con varias pruebas → dejar Cloruro y Conductividad → «Aplicar» → solo esas dos tarjetas; abrir la URL resultante → las mismas.

### Tests (deben fallar primero)

- [ ] T022 [US3] En `estudios/tests/test_comparacion_vista.py` agregar: `test_seleccion_por_defecto` (sin `elegir`: todas las pruebas del estudio en orden de código, todas las casillas marcadas; sin estudio: las disponibles del origen por nombre); `test_seleccion_en_url` (`?estudio=<pk>&pruebas=CL-&pruebas=COND&elegir=1` → solo esas dos tarjetas y casillas marcadas); `test_seleccion_vacia` (`elegir=1` sin `pruebas` → «Elegí al menos una prueba para ver su evolución.» y ninguna tarjeta); `test_codigo_desconocido_ignorado`; `test_selector_accesible` (un `<fieldset>` con `<legend>` «Pruebas a mostrar», casillas con `<label>`, botón «Aplicar»; el form es GET y conserva `estudio` o `cliente`/`origen` en campos ocultos).
- [ ] T023 [P] [US3] En `estudios/tests/js/comparacion.test.cjs` agregar el test de los atajos «Todas»/«Ninguna» (marcan y desmarcan todas las casillas del `fieldset` simulado; quedan ocultos sin JS: el botón lleva `hidden` en el HTML y el JS lo quita).

### Implementación

- [ ] T024 [US3] En `estudios/forms.py` agregar `ElegirPruebasForm(forms.Form)` según `data-model.md`: `pruebas = forms.MultipleChoiceField(required=False, widget=forms.CheckboxSelectMultiple, label="Pruebas a mostrar", help_text="Marcá las pruebas cuya evolución querés ver.")`, `elegir = forms.CharField(required=False, widget=forms.HiddenInput)`; `__init__(self, *args, disponibles, **kwargs)` arma `choices` `(codigo, "Nombre (CODIGO)")`; `elegidas()` devuelve los códigos válidos (los desconocidos se descartan antes de validar, filtrando `data`); `clean()`: con `elegir` y sin pruebas → `ValidationError("Elegí al menos una prueba para ver su evolución.")`; sin `elegir` → todas.
- [ ] T025 [US3] En `estudios/views.py:comparacion` usar `ElegirPruebasForm` (`disponibles = comparacion.pruebas_disponibles(...)`) y pasar `codigos` a `comparar`; con error, no armar historiales. En `comparacion.html` dibujar el selector con `ui/campo.html` dentro de un `<form method="get">` con los ocultos, botones «Todas» / «Ninguna» (`type="button"`, `hidden`, `data-atajo="todas|ninguna"`) y «Aplicar».
- [ ] T026 [US3] En `estudios/static/estudios/comparacion.js` agregar los atajos: quita `hidden` a `[data-atajo]` y marca/desmarca las casillas del `fieldset`.

**Checkpoint**: la selección funciona y se comparte por enlace.

---

## Phase 6: User Story 4 — Consultar un origen desde el Dashboard (Priority: P2) (Tanda 2)

**Goal**: desde el Dashboard, cliente → origen → comparación sin estudio de referencia.

**Independent Test**: Dashboard → «Lácteos del Sur S.A.» → «Pozo 2» → «Ver evolución» → Cloruro sin punto destacado con las variaciones de `test_pozo_2_cloruro_sin_referencia`.

### Tests (deben fallar primero)

- [ ] T027 [US4] En `estudios/tests/test_comparacion_vista.py` agregar: `test_desde_origen` (`?cliente=&origen=` → sin ficha de estudio ni punto `referencia`; «Volver al dashboard»); `test_origen_de_otro_cliente` («El origen no pertenece al cliente elegido.» junto al campo, sin tarjetas); `test_solo_cliente_paso_dos` (`?cliente=<pk>` → selector con solo los orígenes de ese cliente); `test_cliente_inactivo_no_se_ofrece` (no está entre las opciones; un `?cliente=` inactivo da error); `test_origen_sin_validados` («Este origen todavía no tiene resultados validados» y «Volver al dashboard»); `test_sin_parametros` (solo el selector); `test_estudio_tiene_prioridad` (`?estudio=` con `origen=` de otro origen: usa el del estudio).
- [ ] T028 [P] [US4] En `informes/tests/test_dashboard.py` agregar `test_tarjeta_comparacion_historica`: el dashboard tiene la tarjeta «Comparación histórica» con un `<form method="get" action="/estudios/comparacion/">`, los campos `cliente` y `origen` (orígenes en `<optgroup>` por cliente), el botón «Ver evolución» y el `json_script` `origenes-por-cliente` (`{cliente_pk: [[origen_pk, nombre], …]}` solo de clientes activos); y en `estudios/tests/test_comparacion_demo.py` agregar `test_vista_tanque_domiciliario` (con `cliente_bioquimico` y la demo cargada: `?cliente=&origen=` del Tanque domiciliario muestra «Sin cambios (Ausente)», «Presente en 1 de 4» y los puntos con texto «Ausente»/«Presente», nunca «0»/«1» en la tabla).
- [ ] T029 [P] [US4] En `estudios/tests/js/comparacion.test.cjs` (o un `elegir_origen.test.cjs` vecino) agregar el test de `estudios/static/estudios/elegir_origen.js`: al cambiar el cliente, el `<select>` de orígenes queda solo con los de ese cliente (más la opción vacía) y conserva el elegido si sigue siendo válido.

### Implementación

- [ ] T030 [US4] En `estudios/forms.py` agregar `ElegirOrigenForm(forms.Form)`: `cliente = forms.ModelChoiceField(queryset=Cliente.objects.filter(activo=True), label="Cliente", help_text="Cliente dueño del punto de muestreo.")`, `origen = forms.ModelChoiceField(queryset=Origen.objects.select_related("cliente"), label="Origen", help_text="Punto de muestreo cuya evolución querés ver.")` con `<optgroup>` por cliente (choices agrupadas); `clean()`: si `origen.cliente_id != cliente.pk` → error en `origen` «El origen no pertenece al cliente elegido.»; con solo `cliente`, el queryset de `origen` se limita a sus orígenes (paso 2). Método `origenes_por_cliente()` para el `json_script`.
- [ ] T031 [US4] En `estudios/views.py:comparacion` completar el camino sin `estudio`: `ElegirOrigenForm(request.GET or None)`; válido → `comparar(origen)`; inválido o incompleto → solo el selector con errores. Mensaje «Este origen todavía no tiene resultados validados» si no hay historial. Crear `estudios/templates/estudios/elegir_origen.html` (form GET a `estudios:comparacion`, campos con `ui/campo.html`, botón «Ver evolución», `json_script` `origenes-por-cliente`, `static 'estudios/elegir_origen.js'` con `defer`) e incluirlo en `comparacion.html` cuando no hay origen.
- [ ] T032 [US4] Crear `estudios/static/estudios/elegir_origen.js` (patrón de `muestras/static/muestras/registro_muestra.js`): lee `origenes-por-cliente` y, al cambiar `cliente`, deja en `origen` solo sus orígenes (sin `<optgroup>`).
- [ ] T033 [US4] En `informes/views.py:dashboard` sumar `ElegirOrigenForm()` al contexto (`form_origen`) y en `informes/templates/informes/dashboard.html` agregar la tarjeta «Comparación histórica» con `{% include "estudios/elegir_origen.html" with form=form_origen %}`.

**Checkpoint**: se llega a la comparación de un origen desde el Dashboard, con y sin JavaScript.

---

## Phase 7: User Story 5 — Leer los datos sin gráfico y en contexto (Priority: P3) (Tanda 2)

**Goal**: tabla «Ver datos» por gráfico con enlaces a la muestra y al estudio; nada de esto llega al cliente.

**Independent Test**: «Ver datos» de Cloruro → filas con fecha, N° PI enlazado, «< LD» cuando corresponde, evaluación y estado; el informe emitido no muestra nada de la comparación.

### Tests (deben fallar primero)

- [ ] T034 [US5] En `estudios/tests/test_comparacion_vista.py` agregar: `test_tabla_ver_datos` (`<details>` con `<summary>` «Ver datos» y tabla Fecha de muestreo / N° PI / Resultado / Evaluación / Estado en el orden del gráfico; N° PI enlaza a `muestras:detalle`; la fila de referencia lleva «Este estudio» y enlace a `estudios:detalle`; un resultado bajo el límite de detección se lee «< LD …»; una fila `otra_unidad` lleva «Otra unidad (g/l), no se compara»); `test_no_aparece_en_informe_pdf_ni_correo` (FR-017: con un informe emitido del origen, `informes:ver`, `informes:imprimir` y el texto del correo de `informes/correos/` no contienen «Comparación histórica» ni «Contra el anterior»; parchear `informes.envios.generar_pdf` si hace falta).

### Implementación

- [ ] T035 [US5] En `estudios/templates/estudios/comparacion_prueba.html` agregar el `<details class="mt-4 text-sm">` «Ver datos» con la tabla (`.tabla`, `data-tabla="{{ codigo }}"`) como en `informes/dashboard.html`: fecha `d/m/Y`, N° PI con enlace a `muestras:detalle`, `texto` + unidad (`|unidad`), evaluación con `estudios/evaluacion.html`, «Validado»/«Sin validar», «Este estudio» con enlace al estudio; filas `otra_unidad` con el aviso. Debe leerse sin JavaScript.

**Checkpoint**: todas las historias completas.

---

## Phase 8: Polish & Cross-Cutting Concerns (Tanda 2)

- [ ] T036 [P] En `.github/workflows/ci.yml` cambiar el paso de JS a `node --test usuarios/tests/js config/tests/js estudios/tests/js`.
- [ ] T037 [P] Recompilar el CSS si se usaron clases nuevas (el comando de compilación de `README.md`/`package.json`) y versionar `static/css/aqualab.css`; el CI verifica que esté al día.
- [ ] T038 [P] En `CLAUDE.md` agregar la sección «Comparación histórica (US 8.1)»: `estudios/comparacion.py` es la única fuente del historial y la variación (`comparar`, `variacion`, `franja`; la usa la 8.2); historial = asignaciones Completadas del origen ordenadas por `(fecha_muestreo, numero_pi, estudio)`; «anteriores» = muestras previas a la del último; `Decimal`, porcentaje a 0,1; la vista `estudios:comparacion` es GET de solo lectura con el permiso `informes.ver_dashboard`; Chart.js sin plugins (franja con `fill`); el caso A/P de la demo es el Tanque domiciliario (E. Coli Presente en el mes 3). En la sección de la US 8.3 actualizar «La 8.2 agrega acá la lista de desvíos sin revisar» si cambió algo. Actualizar las rutas de `node --test` en «Ayuda en formularios».
- [ ] T039 **Prueba en el navegador (la hace el autor; no marcar)**: recorrer `quickstart.md` escenarios 1 a 8 con la demo cargada, incluidos sin JavaScript y con el técnico sin permiso.
- [ ] T040 **Cierre de la tanda 2**: ejecutar `docker compose exec web pytest estudios informes`, `node --test usuarios/tests/js config/tests/js estudios/tests/js`, `ruff check .` y `ruff format --check .`: en verde. No correr la suite completa (la corre el CI en el PR «SCRUM-60 – 8.1 Comparación histórica por origen»).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Fase 1)**: T001 primero; T002 (fábrica de tests) antes de cualquier test.
- **Foundational (Fase 2)**: depende de T002; bloquea todas las historias.
- **US2 (Fase 3)**: depende de la fase 2 (completa `comparar` con la variación).
- **US1 (Fase 4)**: depende de US2 (la pantalla muestra la variación). Cierra la tanda 1.
- **US3 (Fase 5)**: depende de US1 (vista y template).
- **US4 (Fase 6)**: depende de US1; independiente de US3 salvo que los dos tocan `views.py:comparacion` y `comparacion.html` (hacer US3 antes evita conflictos).
- **US5 (Fase 7)**: depende de US1; independiente de US3 y US4.
- **Polish (Fase 8)**: después de las historias.

### Within Each User Story

- Tests primero (deben fallar), después implementación, después ejecutar los tests de `estudios` e `informes`.
- `comparacion.py` → formulario → vista y URL → templates → JS.

### Parallel Opportunities

- T004 y T005 en paralelo con T003 (mismo archivo, secciones distintas: escribir juntos o en orden).
- T011 y T012 en paralelo con T010 (`test_comparacion_demo.py` es otro archivo).
- T016 (JS) en paralelo con T015 (Python).
- T023 y T029 (JS) en paralelo con T022 y T027.
- T028 (`informes/tests/test_dashboard.py`) en paralelo con T027.
- T036, T037 y T038 en paralelo.

### Parallel Example: Tanda 1

```text
Juntos: T010 (variación en test_comparacion.py) · T012 (demo en test_comparacion_demo.py)
Juntos: T015 (test_comparacion_vista.py) · T016 (comparacion.test.cjs)
```

## Implementation Strategy

### MVP First (Tanda 1: US2 + US1)

1. Fase 1 (gate y fábrica) y fase 2 (`comparar` con historial, franja y consultas fijas).
2. Fase 3: variación, con los valores del Pozo 2 y el caso A/P del Tanque domiciliario.
3. Fase 4: pantalla desde el estudio.
4. **Validar** con `pytest estudios informes` y `node --test estudios/tests/js` (T021).

### Incremental Delivery (Tanda 2)

1. US3 → selección de pruebas.
2. US4 → acceso desde el Dashboard (con y sin JS).
3. US5 → tablas «Ver datos» y verificación de que el cliente no lo ve.
4. Polish → CI, CSS, `CLAUDE.md`; cierre con los tests de `estudios` e `informes` (T040). La prueba en el navegador (T039) la hace el autor y el CI corre la suite completa en el PR.
