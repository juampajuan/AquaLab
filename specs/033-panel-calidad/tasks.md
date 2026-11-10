---

description: "Lista de tareas de SCRUM-76 – US 8.4 Panel de calidad del agua"
---

# Tasks: Panel de calidad del agua

**Input**: `specs/033-panel-calidad/` (`plan.md`, `spec.md`, `research.md`, `data-model.md`,
`contracts/calidad-ui.md`, `quickstart.md`)

**Prerequisites**: `main` con la US 6.4 (`Validacion` vigente ⇔ `Completada`, `evaluacion` con
`pruebas.limites.Evaluacion`: `cumple`, `fuera_de_norma`, `sin_limite`), US 3.3
(`clientes:historial`, rechaza inactivos), US 8.1 (`estudios:comparacion?cliente=&origen=`, solo
clientes activos), US 8.3 (`informes:dashboard`, `informes/tablero.py`: `Periodo`, `periodo`,
`variacion`, `fecha_local`, `con_coma`; `informes/variacion.html`; `informes/dashboard.js`;
`static/vendor/chart.umd.min.js`) y SCRUM-78 (`estudios.demo.cargar_demo(salida, ahora=...)`,
`demo.reloj(fecha)`). Fixtures de `estudios/tests/conftest.py`: `catalogo`, `empleado`,
`bioquimico` (tiene `ver_dashboard`), `cliente_bioquimico`, `cliente_a`, fábrica
`estudio_en_origen(origen, fecha_muestreo, numero_pi, {"CL-": "40"}, validar_todo=True,
usuario=None, tipo_vertido=TipoVertido.AGUA)`; en `informes/tests/test_dashboard.py`: `con_demo`,
`dia_2()`, `html_de`, `usuario_con`. Cloruro (`CL-`) es `x*10`: medición 40 → 400 mg/l. E. coli
(`ECOLI`) es A/P: 0 Ausente, 1 Presente.

**Tests**: SÍ (pedido del usuario y principio III). Cada historia tiene sus tests, escritos
**antes** de su implementación; deben fallar primero. Mapa completo en `plan.md` («Mapa de tests»).

**Organization**: cuatro user stories — US1 (P1, nivel de cumplimiento del período), US2 (P1,
pruebas que más fallan), US3 (P2, por tipo de vertido), US4 (P2, clientes y orígenes). Sin modelos,
migraciones ni permisos nuevos. Dos tandas:

- **Tanda 1** (Fases 1 a 4 — `T001` a `T017`): esqueleto de `informes/calidad.py`, sección en el
  dashboard, indicador general con variación y ranking de pruebas con su gráfico. Cierra el MVP
  (US1 + US2).
- **Tanda 2** (Fases 5 a 7 — `T018` a `T033`): cumplimiento por vertido, clientes y orígenes con
  enlaces, test con la demo, consultas, CLAUDE.md y CSS.
- **Tests de cada tanda** (solo estos): `docker compose exec web pytest informes estudios`,
  `node --test usuarios/tests/js config/tests/js estudios/tests/js`,
  `docker compose exec web ruff check .` y `docker compose exec web ruff format --check .`.
- **La suite completa no se corre en las tandas**: la corre el CI en el PR.
- **La prueba en el navegador (`T032`) la hace el usuario**: queda sin marcar.
- **El guion de la demo (`estudios/demo.py`) no cambia** (research R9).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: se puede ejecutar en paralelo (archivos distintos, sin dependencias pendientes)
- **[Story]**: user story a la que pertenece la tarea (`[US1]` … `[US4]`)
- Rutas relativas a la raíz del repo

## Convenciones para todas las tareas

- Textos de la interfaz en **español**, copiados **literalmente** de `spec.md` y
  `contracts/calidad-ui.md`.
- Cálculos **solo** en `informes/calidad.py`; la vista agrega el contexto y el template solo dibuja.
  `informes/tablero.py` **no se modifica**: se importan `Periodo`, `periodo`, `variacion`,
  `fecha_local` y `con_coma`.
- Solo `Validacion.objects.filter(anulada=False)`, por `fecha_validacion` en la zona del laboratorio
  (`fecha_local("fecha_validacion")` + `dia__range`). Se usa la `evaluacion` guardada: **nunca**
  importar ni llamar a `pruebas/limites.py` para evaluar (`Evaluacion` sí, para los valores).
- `Decimal` en todo el cálculo, nunca `float`: `porcentaje(parte, total)` =
  `(Decimal(parte) * 100 / Decimal(total)).quantize(Decimal("0.1"), ROUND_HALF_UP)`, `None` si
  `total == 0`. Para ordenar, la fracción exacta (`Fraction(fuera, evaluados)` o
  `Decimal(fuera) / Decimal(evaluados)` sin redondear). Porcentajes a Chart.js como texto (`"20.0"`).
- Constantes únicas en `calidad.py`: `MINIMO_EVALUADOS_RANKING = 5` y `TOPE_LISTA = 10`. El
  template muestra el mínimo con `{{ calidad.minimo_ranking }}`, nunca un «5» escrito.
- Para ubicar validaciones en un período anterior en los tests: armar la validación dentro de
  `demo.reloj(fecha)` o construir el `Periodo` a mano alrededor de hoy (`tablero.Periodo(...)`).
- Componentes de `templates/ui/` (`ui/ayuda.html`, `ui/estado.html`, `ui/estado_vacio.html`),
  `.tarjeta`, `.tabla`, `informes/variacion.html`; tokens `text-exito`/`text-peligro`/
  `text-tinta-suave`; nunca solo color. Si se agregan clases nuevas, recompilar el CSS (T030).
- Commits: `feat(informes): US 8.4 – Panel de calidad del agua` (Conventional Commits en español,
  CLAUDE.md).

---

## Phase 1: Setup (Tanda 1)

- [ ] T001 Confirmar que la rama `033-panel-calidad` sale de `main` actualizado y que
  `docker compose exec web pytest informes estudios` está en verde antes de empezar; actualizar el
  `**Status**` de `specs/033-panel-calidad/spec.md` a «Aprobada (fecha)» cuando el equipo la apruebe.

---

## Phase 2: Foundational (Tanda 1, bloquea todas las historias)

- [X] T002 Tests base en `informes/tests/test_calidad.py` (nuevo; importa las fixtures de
  `estudios/tests/conftest.py` como `informes/tests/conftest.py`): `test_porcentaje`
  (parametrizado: 4 de 40 → `Decimal("10.0")`; 1 de 3 → `33.3`; 2 de 3 → `66.7`; 1 de 8 → `12.5`;
  1 de 16 → `6.3` (mitad hacia arriba); 0 de 5 → `0.0`; 0 de 0 → `None`) y `test_conteo_texto`
  («20,0 % (2 de 10)»; sin evaluados «Sin resultados»).
- [X] T003 Crear `informes/calidad.py` con docstring de módulo (US 8.4, única fuente de la sección
  «Calidad», solo lectura, ver specs/033-panel-calidad/), las constantes `MINIMO_EVALUADOS_RANKING
  = 5` y `TOPE_LISTA = 10`, `porcentaje(parte, total)`, el dataclass `Conteo(fuera, evaluados)` con
  propiedades `porcentaje`, `fraccion` (exacta, para ordenar) y `texto` (data-model.md),
  `Lista(filas, restantes)` y `vigentes()` = `Validacion.objects.filter(anulada=False).annotate(
  dia=fecha_local("fecha_validacion"))`. Hace pasar T002.
- [X] T004 Enganche en el dashboard: `calidad.armar(p)` (por ahora devuelve `{"minimo_ranking":
  MINIMO_EVALUADOS_RANKING, "graficos": {}}`); en `informes/views.py:dashboard`, después de
  `tablero.armar`, `contexto["calidad"] = calidad.armar(contexto["periodo"])` y
  `contexto["datos_graficos"].update(contexto["calidad"]["graficos"])`; parcial nuevo
  `informes/templates/informes/calidad.html` con `<section class="tarjeta mb-6 p-5"
  aria-labelledby="titulo-calidad" data-calidad>`, `<h2 id="titulo-calidad">Calidad</h2>` con
  `ui/ayuda.html` (id `ayuda-calidad`, texto de `contracts/calidad-ui.md` §1) y el rango del período;
  incluirlo en `informes/templates/informes/dashboard.html` entre «Actividad semanal» y
  «Comparación histórica».

**Checkpoint**: el dashboard muestra la sección vacía y los tests existentes siguen en verde.

---

## Phase 3: User Story 1 — Nivel de cumplimiento del período (Priority: P1) 🎯 MVP (Tanda 1)

**Goal**: porcentaje fuera de norma de los resultados evaluados del período, con cantidades,
«sin límite comparable» aparte y variación en p. p. contra el período anterior.

**Independent Test**: con resultados validados en el período (fábrica `estudio_en_origen`), el
indicador muestra «10,0 % fuera de norma», «4 de 40 resultados» y la variación; cambiar el período
del selector cambia la sección.

### Tests (escribir primero; deben fallar)

- [X] T005 [P] [US1] En `informes/tests/test_calidad.py`: `test_indicador_general` (36 «cumple» y 4
  «fuera de norma» en el período → `actual.porcentaje == Decimal("10.0")`, `fuera == 4`,
  `evaluados == 40`; 3 `sin_limite` → `sin_limite == 3` y fuera del total);
  `test_cuenta_solo_validaciones_vigentes` (una anulada no cuenta; una prueba corregida y revalidada
  cuenta una vez con la evaluación nueva; un estudio con informe emitido cuenta);
  `test_no_reevalua_con_limites_actuales` (cambiar el `limite_max` de la prueba en el catálogo
  después de validar no cambia el conteo; además, `pruebas.limites` no se importa en
  `informes/calidad.py`); `test_usa_el_periodo_del_dashboard` (una validación fuera de
  `p.inicio..p.fin` no cuenta; una en el período anterior cuenta en `anterior`);
  `test_zona_horaria` (validación a las 23:30 hora del laboratorio del último día del período cuenta
  en el período).
- [X] T006 [P] [US1] En `informes/tests/test_calidad.py`: `test_variacion_del_porcentaje`
  (parametrizado: 10,0 vs 5,0 → «▲ +5,0 p. p.», tono `peligro`; 5,0 vs 10,0 → «▼ −5,0 p. p.»,
  `exito`; iguales → «= 0,0 p. p.», `neutro`; anterior sin evaluados → `variacion is None` y
  `anterior.evaluados == 0`; actual sin evaluados → `variacion is None`).
- [X] T007 [P] [US1] En `informes/tests/test_dashboard.py`: `test_indicador_calidad_en_pantalla`
  (`data-indicador="calidad"` con «10,0 % fuera de norma», «4 de 40 resultados», `data-tono`,
  `data-sin-limite` con «3 resultados sin límite comparable, fuera del cálculo»; con
  `?periodo=ultimos_6` usa ese período) y `test_seccion_sin_datos` (base vacía: «Sin resultados
  validados en el período»; nada falla).

### Implementation

- [X] T008 [US1] En `informes/calidad.py`: `IndicadorCalidad(actual, anterior, sin_limite,
  variacion)` e `indicador(p)` con **un** `aggregate` sobre `vigentes()` con `Count("pk",
  filter=Q(...))` para fuera/evaluados del período y del anterior y sin límite del período;
  `VariacionCalidad(tono, texto)` a partir de `tablero.variacion(actual.porcentaje,
  anterior.porcentaje, favorable_si_sube=False)` con texto `f"{v.simbolo} {con_signo(v.diferencia)}
  p. p."` (diferencia con un decimal y coma; usar `tablero.con_signo`); `None` si falta alguno de
  los porcentajes. `armar(p)` agrega `"indicador"`. Hace pasar T005–T006.
- [X] T009 [US1] En `informes/templates/informes/calidad.html`: bloque del indicador
  (`contracts/calidad-ui.md` §2) con `informes/variacion.html` para la variación; «Sin datos previos»
  cuando el anterior no tiene evaluados; «Sin resultados validados en el período» con
  `ui/estado_vacio.html` cuando el actual no tiene evaluados (y el resto de la sección con el mismo
  aviso). Hace pasar T007.

**Checkpoint**: US1 completa.

---

## Phase 4: User Story 2 — Pruebas que más fallan (Priority: P1) (Tanda 1)

**Goal**: ranking de pruebas con al menos 5 evaluados y algún fuera de norma, «20,0 % (2 de 10)»,
ordenado por porcentaje, con gráfico y «Ver datos».

**Independent Test**: con Cloruro 2 de 10, E. coli 2 de 8 y una prueba 3 de 4, el ranking es
E. coli, Cloruro (la de 4 evaluados no aparece), con su gráfico y tabla.

### Tests (escribir primero; deben fallar)

- [X] T010 [P] [US2] En `informes/tests/test_calidad.py`: `test_ranking_de_pruebas` (parametrizado
  o en casos: E. coli 2 de 8 antes que Cloruro 2 de 10, con `texto` «25,0 % (2 de 8)» y «20,0 %
  (2 de 10)»; 3 de 4 no entra y 3 de 5 sí; 0 de 10 no entra; mismo porcentaje → más fuera de norma
  primero (2 de 10 antes que 1 de 5), luego por código; 12 pruebas que cumplen la regla → 10 filas y
  `restantes == 2`; 2 de 6 y 5 de 15 (misma fracción) → desempata por fuera de norma: 5 de 15
  primero).
- [X] T011 [P] [US2] En `informes/tests/test_calidad.py`: `test_minimo_definido_en_un_solo_lugar`
  (`calidad.MINIMO_EVALUADOS_RANKING == 5`; con `monkeypatch.setattr` a 3, una prueba 2 de 3 entra;
  el texto «al menos 5» no está escrito en `informes/templates/informes/calidad.html` y ningún otro
  `.py` de `informes/` ni `estudios/` define `MINIMO_EVALUADOS_RANKING`).
- [X] T012 [P] [US2] En `informes/tests/test_dashboard.py`: `test_ranking_en_pantalla`
  (`data-ranking="pruebas"` con «Solo pruebas con al menos 5 resultados evaluados», fila «25,0 %
  (2 de 8)», `<canvas id="grafico-calidad-pruebas"`, tabla en `<details>` «Ver datos», «Y 2 pruebas
  más» cuando corresponde; `json_script` `datos-dashboard` con `calidad_pruebas.porcentajes` como
  texto `["25.0", "20.0"]`; vacío: «Ninguna prueba con al menos 5 resultados evaluados tuvo
  incumplimientos en el período.»).

### Implementation

- [X] T013 [US2] En `informes/calidad.py`: `FilaPrueba(codigo, nombre, conteo)` y `pruebas(p)`:
  una consulta `vigentes().filter(dia__range=(p.inicio, p.fin), evaluacion__in=(CUMPLE,
  FUERA_DE_NORMA)).values("asignacion__prueba", "asignacion__prueba__codigo",
  "asignacion__prueba__nombre").annotate(fuera=..., evaluados=...).filter(evaluados__gte=
  MINIMO_EVALUADOS_RANKING, fuera__gte=1).order_by()`; ordenar en Python por `(-fraccion, -fuera,
  codigo)`; `Lista(filas[:TOPE_LISTA], max(0, len - TOPE_LISTA))`. `armar` agrega `"pruebas"` y
  `graficos["calidad_pruebas"] = {"etiquetas": ["CODIGO · Nombre", ...], "porcentajes":
  [str(porcentaje), ...]}`. Hace pasar T010–T011.
- [X] T014 [US2] En `informes/templates/informes/calidad.html`: tarjeta «Pruebas que más fallan»
  (`contracts/calidad-ui.md` §3) en una grilla `xl:grid-cols-2` (la otra columna queda para US3),
  con canvas, `<details>` «Ver datos» (tabla Prueba / Incumplimiento), «Y N pruebas más» y
  `ui/estado_vacio.html` con el texto de vacío (que usa `{{ calidad.minimo_ranking }}`).
- [X] T015 [US2] En `informes/static/informes/dashboard.js`: si existe `grafico-calidad-pruebas`,
  barras horizontales (`indexAxis: "y"`) con `datos.calidad_pruebas`, porcentajes con `Number(...)`,
  color `--color-peligro` (respaldo `#dc2626`), eje X 0–100 con título «% fuera de norma», sin
  leyenda. Si `datos.calidad_pruebas` no existe, no hace nada. Hace pasar T012.

### Cierre de la tanda 1

- [X] T016 `docker compose exec web pytest informes estudios` y
  `node --test usuarios/tests/js config/tests/js estudios/tests/js` en verde.
- [ ] T017 `docker compose exec web ruff check .` y `docker compose exec web ruff format --check .`
  sin errores. Commit de la tanda 1.

**Checkpoint**: MVP (US1 + US2).

---

## Phase 5: User Story 3 — Cumplimiento por tipo de vertido (Priority: P2) (Tanda 2)

**Goal**: Agua, Cloacal y Canal, siempre los tres, con evaluados, cumple, fuera de norma y
porcentaje de cumplimiento, con gráfico y «Ver datos».

**Independent Test**: con resultados en muestras de agua y cloacal, la tabla muestra los tres tipos
con sus conteos y Canal con «Sin resultados».

### Tests (escribir primero; deben fallar)

- [ ] T018 [P] [US3] En `informes/tests/test_calidad.py`: `test_cumplimiento_por_vertido` (agua
  9 cumple + 1 fuera → `porcentaje_cumplimiento == Decimal("90.0")`; cloacal 1 fuera de 1 → `0.0`;
  canal sin evaluados → `conteo.evaluados == 0` y texto «Sin resultados»; el orden es siempre
  Agua, Cloacal, Canal; el vertido sale de `Muestra.tipo_vertido`, con
  `estudio_en_origen(..., tipo_vertido=TipoVertido.CLOACAL)`).
- [ ] T019 [P] [US3] En `informes/tests/test_dashboard.py`: `test_vertidos_en_pantalla`
  (`data-vertidos` con las tres filas, `<canvas id="grafico-calidad-vertidos"`, tabla Tipo /
  Evaluados / Cumple / Fuera de norma / Cumplimiento; `calidad_vertidos` en el `json_script` con
  `etiquetas == ["Agua", "Cloacal", "Canal"]` y listas `cumple`/`fuera` de enteros).

### Implementation

- [ ] T020 [US3] En `informes/calidad.py`: `FilaVertido(valor, etiqueta, conteo)` con `cumple` (=
  `evaluados - fuera`) y `porcentaje_cumplimiento` (`porcentaje(cumple, evaluados)`); `vertidos(p)`:
  una consulta agrupada por `asignacion__estudio__muestra__tipo_vertido`, completada con
  `muestras.models.TipoVertido.choices` (los que faltan, `Conteo(0, 0)`). `armar` agrega
  `"vertidos"` y `graficos["calidad_vertidos"]`. Hace pasar T018.
- [ ] T021 [US3] En `informes/templates/informes/calidad.html`: tarjeta «Cumplimiento por tipo de
  vertido» (`contracts/calidad-ui.md` §4) en la segunda columna de la grilla de T014.
- [ ] T022 [US3] En `informes/static/informes/dashboard.js`: si existe `grafico-calidad-vertidos`,
  barras apiladas (`scales.x.stacked`, `scales.y.stacked`) «Cumple» (`--color-exito`, respaldo
  `#16a34a`) y «Fuera de norma» (`--color-peligro`), `ticks.precision: 0`. Hace pasar T019.

---

## Phase 6: User Story 4 — Clientes y orígenes con más incumplimientos (Priority: P2) (Tanda 2)

**Goal**: listas de clientes y de orígenes con algún fuera de norma, ordenadas por cantidad, con
enlace al historial (3.3) y a la comparación histórica (8.1); inactivos marcados y sin enlace.

**Independent Test**: con incumplimientos en dos orígenes de un cliente activo y uno de un cliente
inactivo, las listas los ordenan por cantidad, los enlaces del activo llevan a su historial y a la
comparación, y el inactivo aparece «Inactivo» sin enlace.

### Tests (escribir primero; deben fallar)

- [ ] T023 [P] [US4] En `informes/tests/test_calidad.py`: `test_clientes_y_origenes` (cliente A con
  3 fuera de 12 antes que B con 2 de 4; empate en cantidad → mayor porcentaje primero, después
  nombre sin distinguir mayúsculas; clientes y orígenes sin fuera de norma no aparecen; 12 clientes
  con incumplimientos → 10 filas y `restantes == 2`; los orígenes incluyen su cliente) y
  `test_enlaces_de_clientes_y_origenes` (cliente activo → `url ==
  reverse("clientes:historial", args=[pk])`; origen → `reverse("estudios:comparacion") +
  f"?cliente={cliente.pk}&origen={origen.pk}"`; cliente inactivo → `url is None` en el cliente y en
  sus orígenes).
- [ ] T024 [P] [US4] En `informes/tests/test_dashboard.py`: `test_clientes_y_origenes_en_pantalla`
  (`data-ranking="clientes"` y `data-ranking="origenes"` con «3 de 12 · 25,0 %», los `href`
  esperados y que se abren con 200 para `cliente_bioquimico`; inactivo con «Inactivo» y sin `<a>`;
  vacío: «No hubo resultados fuera de norma en el período.»).

### Implementation

- [ ] T025 [US4] En `informes/calidad.py`: `FilaCliente(cliente, conteo, url)` y `FilaOrigen(origen,
  conteo, url)`; `clientes(p)` y `origenes(p)`: una consulta agrupada por
  `asignacion__estudio__muestra__cliente` (u `__origen`) con `fuera__gte=1`; después
  `Cliente.objects.in_bulk(ids)` / `Origen.objects.select_related("cliente").in_bulk(ids)` de
  **todas** las filas agrupadas (hacen falta los nombres para ordenar), orden `(-fuera, -fraccion,
  nombre.casefold(), pk)` (`Cliente.nombre_completo`, `Origen.nombre`), `Lista` con `TOPE_LISTA`;
  `url` según R6 (sin enlace si el cliente está inactivo). `armar` agrega `"clientes"` y
  `"origenes"`. Hace pasar T023.
- [ ] T026 [US4] En `informes/templates/informes/calidad.html`: tarjetas «Clientes con más
  incumplimientos» y «Orígenes con más incumplimientos» lado a lado (`contracts/calidad-ui.md` §5),
  con `ui/estado.html` «Inactivo» y sin enlace para inactivos, «Y N más» y vacío con
  `ui/estado_vacio.html`. Hace pasar T024.

---

## Phase 7: Polish & Cross-Cutting Concerns (Tanda 2)

- [ ] T027 [P] En `informes/tests/test_calidad.py`: `test_calidad_con_la_demo` (`catalogo` +
  `demo.cargar_demo(io.StringIO(), ahora=...)` con `ahora` fijo, y `calidad.armar(tablero.periodo(
  "ultimos_6", hoy))`: el ranking de pruebas tiene **al menos 3** filas y alguna con `conteo.fuera >=
  1`; ninguna fila con menos de `MINIMO_EVALUADOS_RANKING` evaluados; «Pozo 2» y «Tanque
  domiciliario» están en `origenes`). Sin modificar `estudios/demo.py`. Si «Pozo 2» o «Tanque
  domiciliario» no quedan fuera de norma con la demo, consultar al usuario antes de cambiar la
  aserción.
- [ ] T028 [P] En `informes/tests/test_dashboard.py`: ampliar `test_acceso` (sin permiso no aparece
  `data-calidad`; 403), `test_solo_lectura` (la sección no modifica nada: conteos de `Validacion`,
  `Medicion`, `Estudio` iguales antes y después) y `test_cantidad_de_consultas` (sumar las 7
  consultas de la sección al máximo: `25 + 1 + 7 + 6 * con_pendientes`).
- [ ] T029 [P] Agregar a `CLAUDE.md` la sección «Panel de calidad (US 8.4)»: `informes/calidad.py`
  es la única fuente; recibe el `Periodo` de `tablero`; solo validaciones vigentes por
  `fecha_validacion` con la evaluación guardada (nunca `pruebas/limites.py`); «sin límite
  comparable» fuera del porcentaje; `MINIMO_EVALUADOS_RANKING` y `TOPE_LISTA` solo ahí; orden por
  fracción exacta; variación en p. p.; inactivos sin enlace; con la demo el ranking se verifica con
  «Últimos 6 meses» (con «Este mes» solo pH llega a 5).
- [ ] T030 [P] Si se agregaron clases de Tailwind nuevas, recompilar `static/css/aqualab.css` con el
  CLI standalone (como en la 8.3) y commitearlo (`chore(ui): recompilar CSS`).
- [ ] T031 Revisar que no se creó nada fuera del plan: sin migraciones nuevas
  (`docker compose exec web python manage.py makemigrations --check --dry-run`), sin cambios en
  `informes/tablero.py` ni `estudios/demo.py`, sin rutas nuevas.
- [ ] T032 Prueba en el navegador según `specs/033-panel-calidad/quickstart.md` — **la hace el
  usuario**; no marcar.
- [ ] T033 Cierre: `docker compose exec web pytest informes estudios`,
  `node --test usuarios/tests/js config/tests/js estudios/tests/js`,
  `docker compose exec web ruff check .` y `docker compose exec web ruff format --check .` en verde.
  Commit de la tanda 2.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Fase 1)**: T001 primero.
- **Foundational (Fase 2)**: T002 → T003 → T004; bloquea todas las historias.
- **US1 (Fase 3)**: depende de la Fase 2. T005–T007 → T008 → T009.
- **US2 (Fase 4)**: depende de la Fase 2; independiente de US1 salvo el template (T014 va después de
  T009 en el mismo archivo). T010–T012 → T013 → T014 → T015. Cierra la tanda 1 (T016–T017).
- **US3 (Fase 5)**: depende de la Fase 2 y de la grilla de T014. T018–T019 → T020 → T021 → T022.
- **US4 (Fase 6)**: depende de la Fase 2. T023–T024 → T025 → T026.
- **Polish (Fase 7)**: T027 depende de US2 y US4; T028 de toda la sección; T032 y T033 al final.

### Within Each User Story

- Tests primero (deben fallar), después `calidad.py`, después template y JS.

### Parallel Opportunities

- T005, T006 y T007 en paralelo (T005/T006 en secciones distintas de `test_calidad.py`; T007 en
  `test_dashboard.py`).
- T010, T011 y T012 en paralelo.
- T018 y T019 en paralelo; T023 y T024 en paralelo.
- T027, T028, T029 y T030 en paralelo.
- US3 y US4 (lógica en `calidad.py`) se pueden hacer en paralelo si cada una agrega su función en
  una sección distinta; los templates van uno después del otro.

### Parallel Example: Tanda 1

```text
Juntos: T005 + T006 (test_calidad.py) · T007 (test_dashboard.py)
Juntos: T010 + T011 (test_calidad.py) · T012 (test_dashboard.py)
```

### Parallel Example: Tanda 2

```text
Juntos: T018 (test_calidad.py) · T019 (test_dashboard.py)
Juntos: T023 (test_calidad.py) · T024 (test_dashboard.py)
Juntos: T027 (demo) · T028 (dashboard) · T029 (CLAUDE.md) · T030 (CSS)
```

---

## Implementation Strategy

### MVP First (Tanda 1: US1 + US2)

1. Setup y Foundational (T001–T004): `calidad.py` con porcentaje y conteo; sección enganchada.
2. US1 (T005–T009): indicador general con variación.
3. US2 (T010–T015): ranking de pruebas con mínimo de 5 y gráfico.
4. **Validar** con `pytest informes estudios`, Node y ruff (T016–T017). Commit.

### Incremental Delivery (Tanda 2)

1. US3 (T018–T022): cumplimiento por tipo de vertido.
2. US4 (T023–T026): clientes y orígenes con enlaces.
3. Polish (T027–T033): test con la demo («Últimos 6 meses»), acceso y consultas, CLAUDE.md, CSS,
   revisión; cierre con `pytest informes estudios`, Node y ruff. La prueba en el navegador (T032)
   la hace el usuario y el CI corre la suite completa en el PR.
