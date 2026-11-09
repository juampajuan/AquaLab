---

description: "Lista de tareas de SCRUM-61 – US 8.2 Notificar desvíos relevantes"
---

# Tasks: Notificar desvíos relevantes

**Input**: `specs/032-notificar-desvios/` (`plan.md`, `spec.md`, `research.md`, `data-model.md`,
`contracts/desvios-ui.md`, `quickstart.md`)

**Prerequisites**: `main` con la US 6.1–6.5 (`cargar_mediciones`, `corregir_mediciones`,
`calculo.recalcular`), US 6.4 (`Validacion` vigente ⇔ `Completada`, `servicios.validar_resultados`,
`ValidarResultadosForm`), US 8.1 (`estudios/comparacion.py`: `comparar`, `cambio`,
`numero`, `con_unidad`, `con_signo`, `texto_valor`, `HistorialPrueba`, `Punto`;
`estudios:comparacion` con `?estudio=&pruebas=&elegir=1`), US 8.3 (`informes:dashboard`,
`informes.ver_dashboard`) y SCRUM-78 (`estudios/demo.py`). Fixtures de
`estudios/tests/conftest.py`: `empleado`, `catalogo`, `bioquimico` (tiene `validar_resultados` y
`ver_dashboard`), `cliente_bioquimico`, `cliente_http` (el mismo `empleado`, sin permisos extra),
`cliente_a`, `pruebas_division` (`DIV = {DIV-A}/{DIV-B}`), fábrica
`estudio_en_origen(origen, fecha_muestreo, numero_pi, {"CL-": "10"}, validar_todo=True,
usuario=None)`; helpers `estudios.tests.utiles.cargar`, `validar`, `asignacion_de`. Cloruro (`CL-`)
es `x*10`: medición 10 → 100 mg/l, 11 → 110, 12 → 120, 16 → 160, 14,3 → 143, 14,35 → 143,5, 7,7 →
77, 7,69 → 76,9, 11,5 → 115, 20 → 200. E. coli (`ECOLI`) es A/P: 0 Ausente, 1 Presente.

**Tests**: SÍ (pedido del usuario y principio III). Cada historia tiene sus tests, escritos
**antes** de su implementación; deben fallar primero. Mapa completo en `plan.md` («Mapa de tests»).

**Organization**: cinco user stories — US1 (P1, ver el desvío en el estudio), US2 (P1, pendientes
en el dashboard), US3 (P1, revisar al validar), US4 (P2, no bloquea), US5 (P3, regla
configurable). No hay modelo `Desvio`: el desvío se calcula al vuelo. Dos tandas:

- **Tanda 1** (Fases 1 a 4 — `T001` a `T022`): configuración, campos nuevos de `Validacion`,
  `anteriores` en la 8.1, `estudios/desvios.py` (regla y detección al vuelo), marca en el detalle,
  dashboard y lista «Desvíos sin revisar». Cierra el MVP (US1 + US2).
- **Tanda 2** (Fases 5 a 8 — `T023` a `T042`): revisión al validar (formulario, servicio,
  pantallas, concurrencia), no bloqueo, regla configurable, demo, CLAUDE.md.
- **Tests de cada tanda** (solo las apps tocadas): `docker compose exec web pytest estudios
  informes`, `node --test usuarios/tests/js config/tests/js estudios/tests/js`, `docker compose
  exec web ruff check .` y `docker compose exec web ruff format --check .`.
- **La suite completa no se corre en las tandas**: la corre el CI en el PR.
- **La prueba en el navegador (`T041`) la hace el autor**: queda sin marcar.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: se puede ejecutar en paralelo (archivos distintos, sin dependencias pendientes)
- **[Story]**: user story a la que pertenece la tarea (`[US1]` … `[US5]`)
- Rutas relativas a la raíz del repo

## Convenciones para todas las tareas

- Textos de la interfaz en **español**, copiados **literalmente** de `spec.md` y
  `contracts/desvios-ui.md`.
- `Decimal` en todo el cálculo, nunca `float`; la decisión de desvío usa el valor completo
  (research R3). Porcentajes para mostrar con `comparacion.cambio` (0,1 `ROUND_HALF_UP`); valores
  con `comparacion.numero` (hasta 4 decimales).
- El historial sale **solo** de `comparacion.comparar` (FR-003); presencia solo con
  `estudios/mediciones.py` (`es_presencia`, `texto_presencia`).
- `estudios/desvios.py` es de **solo lectura**: no crea ni modifica nada. La constancia la escribe
  solo `servicios.validar_resultados` al crear la `Validacion`. **No se modifican** `calculo.py`,
  `cargar_mediciones` ni `corregir_mediciones`; no hay modelo `Desvio`, comando ni pantalla para
  «Marcar como revisado».
- `estudios` **no** importa de `informes` (dirección `informes → estudios`).
- Componentes de `templates/ui/` (`ui/estado.html`, `ui/icono.html`, `ui/ayuda.html`,
  `ui/campo.html` con `help_text`, `ui/paginacion.html`, `ui/estado_vacio.html`,
  `ui/encabezado.html`), `.tarjeta`, `.tabla`, tokens de color; ícono + texto, nunca solo color.
  Si se agregan clases nuevas, recompilar el CSS (T019, T038).
- Commits: `feat(estudios): US 8.2 – Notificar desvíos relevantes` (Conventional Commits en
  español, CLAUDE.md).

---

## Phase 1: Setup (Tanda 1)

- [X] T001 Confirmar que la spec de la US 8.2 (con los ajustes del 2026-11-09) está aprobada (principio I) y que se está en la rama `032-notificar-desvios`; si no, detenerse.
- [X] T002 En `config/settings.py`, debajo de `AQUALAB_LABORATORIO`, agregar `AQUALAB_DESVIOS = {"umbral": "30", "cantidad": 3}` con un comentario: regla inicial de la US 8.2 (umbral en % sobre el mediana de los últimos `cantidad` resultados validados del origen), a confirmar con el laboratorio; es el único lugar donde se define (research R7).

---

## Phase 2: Foundational (Tanda 1, bloquea todas las historias)

- [X] T003 En `estudios/models.py:Validacion` agregar `observacion = models.CharField("observación", max_length=500, blank=True, default="")`, `desvio_referencia = models.DecimalField("mediana histórica del desvío", max_digits=28, decimal_places=10, null=True, blank=True)` y `desvio_umbral = models.DecimalField("umbral del desvío", max_digits=5, decimal_places=2, null=True, blank=True)`; en `Meta.constraints` el `CheckConstraint` `validacion_desvio_completo` (`Q(desvio_referencia__isnull=True, desvio_umbral__isnull=True) | Q(desvio_referencia__isnull=False, desvio_umbral__isnull=False)`); propiedad `con_desvio` (`self.desvio_umbral is not None`). Actualizar el docstring (constancia de la revisión del desvío, US 8.2; nunca se modifica).
- [X] T004 Generar `estudios/migrations/0009_validacion_desvio.py` con `docker compose exec web python manage.py makemigrations estudios -n validacion_desvio` y revisar que solo agregue las tres columnas y la restricción.
- [X] T005 [P] En `estudios/tests/test_desvios_validacion.py` (nuevo, `pytestmark = pytest.mark.django_db`) escribir `test_restriccion_desvio_completo`: una `Validacion` con `desvio_referencia` sin `desvio_umbral` (o al revés) → `IntegrityError` (dentro de `transaction.atomic()`); ambos nulos o ambos con valor → se guarda; las validaciones creadas por `validar` sin desvío quedan con `observacion == ""` y desvío nulo.
- [X] T006 [P] En `estudios/tests/test_comparacion.py` agregar `test_anteriores_expuestos`: con 5 validados previos y un estudio de referencia, `historial.anteriores` es la tupla de los validados de muestras previas a la de referencia, en orden, sin otra unidad ni otros estudios de la misma muestra, y `historial.variacion.cantidad_anteriores == len(historial.anteriores)`; sin último, `anteriores == ()`.
- [X] T007 En `estudios/comparacion.py`: agregar a `HistorialPrueba` el campo `anteriores: tuple = ()` (docstring: «Validados de muestras previas a la del último, misma unidad, en orden; los usa la US 8.2») y en `historial_de_prueba` pasar `anteriores=tuple(anteriores)`. No cambiar nada más (la pantalla de la 8.1 queda igual; sus tests siguen en verde).

**Checkpoint**: migración aplicada, T005 y T006 en verde, tests de `test_comparacion*.py` sin cambios.

---

## Phase 3: User Story 1 — Ver el desvío en el estudio (Priority: P1) 🎯 MVP (Tanda 1)

**Goal**: el detalle del estudio marca los resultados sin validar con desvío (calculado al vuelo) y los validados con constancia.

**Independent Test**: Cloruro validado 100, 110, 120 en tres muestras previas del origen; cargar 16 (→ 160) en un estudio nuevo → el detalle muestra «Desvío» con «Observado 160 mg/l · Mediana de los últimos 3: 110 mg/l · ▲ +50 mg/l (+45,5 %)»; corregir a 11,5 (→ 115) → la marca desaparece.

### Tests for User Story 1

- [X] T008 [P] [US1] En `estudios/tests/test_desvios.py` (nuevo) agregar los tests puros (sin base): `test_es_desvio_bordes` (mediana 110: 143 y 77 → `False`; 143,5 y 76,9 → `True`; `umbral=Decimal("30")`), `test_mediana_cero` (`es_desvio(Decimal(5), Decimal(0), …)` → `True`; 0 contra 0 → `False`), `test_presencia` (con `Punto`s armados a mano: 3 Ausente + Presente → `Deteccion` con `referencia == 0`, `porcentaje is None` y texto «Presente (los últimos 3: Ausente)»; 2 Ausente + 1 Presente + Presente → `None`; 3 Presente + Ausente → desvío con `referencia == 1`), `test_mediana_de_los_ultimos_n` (anteriores 50, 60, 100, 110, 120 y valor 160 → mediana 110, `porcentaje == Decimal("45.5")`, `previos` = los 3 últimos), `test_un_pico_aislado_no_contamina` (14 / 4,1 / 4,3 y 4,2 → `None`; 4,1 / 4,3 / 4,2 y 14 → desvío contra 4,2), `test_mediana_con_cantidad_par`, `test_mediana`, `test_historial_insuficiente` (2 anteriores → `detectar` devuelve `None` y `historial_suficiente` es `False`), `test_regla` (`regla()` con la configuración por defecto → `Regla(Decimal("30"), 3)`).
- [X] T009 [P] [US1] En `estudios/tests/test_desvios.py` agregar tests con servicios reales (`pytest.mark.django_db`; crear un `Origen` de `cliente_a` y usar `estudio_en_origen` con fechas 1, 2 y 3 de marzo y el estudio a evaluar el 4 de marzo, sin validar): `test_evaluar_estudio` (CL- 16 → `Deteccion` con `valor=160`, `referencia=110`, `porcentaje=45.5`; CL- 14,3 → `None`; con solo 2 previos → `HISTORIAL_INSUFICIENTE`; una prueba sin resultado no aparece en el dict), `test_dependiente` (con `pruebas_division`: DIV validado 10, 10, 10 en tres muestras; cargar DIV-A=30, DIV-B=2 → `Deteccion` en DIV con 15, +50 %), `test_correccion_se_refleja` (con 160, `corregir_mediciones(estudio.pk, {cl.pk: (Decimal("16"), Decimal("11.5"))}, empleado)` → `None`; luego a 20 → `Deteccion` con 200; borrar con `nuevo=None` → sin entrada), `test_usa_historial_de_la_comparacion` (no cuentan: un resultado cargado sin validar, uno con validación anulada, uno de otro origen, uno de una muestra posterior, otro estudio de la misma muestra → con solo 2 previos válidos el resultado es `HISTORIAL_INSUFICIENTE`), `test_estudio_de_muestra_antigua` (validados en abril y un estudio de una muestra de enero → `HISTORIAL_INSUFICIENTE`), `test_calcular_no_escribe` (contar `Validacion`, `Resultado`, `PruebaEstudio` por estado y `Estudio.estado` antes y después de `evaluar_estudio` → iguales; con `CaptureQueriesContext` ninguna consulta empieza con `INSERT`/`UPDATE`/`DELETE`), `test_consultas_evaluar_estudio` (`django_assert_max_num_queries` sobre `evaluar_estudio` de un estudio con 1 y con 6 pruebas: la misma cantidad; fijar el número observado).
- [X] T010 [P] [US1] En `estudios/tests/test_desvios_vista.py` (nuevo) agregar `test_marca_en_detalle` (`estudios:detalle` del estudio con CL- 160 sin validar: la fila de CL- contiene «Desvío», el ícono, «Observado 160 mg/l», «Mediana de los últimos 3: 110 mg/l», «+45,5 %»; el enlace «Comparación histórica» a `estudios:comparacion?estudio=<pk>&pruebas=CL-&elegir=1` aparece con `cliente_bioquimico` y no con `cliente_http`; una prueba sin desvío no tiene la marca) y `test_revisado_en_detalle` (crear con `Validacion.objects.filter(...).update(observacion="Repetida", desvio_referencia=110, desvio_umbral=30)` una constancia sobre una prueba validada → la fila muestra «Desvío revisado», «Validado por …», la fecha, «Repetida», «mediana 110 mg/l, umbral 30 %»).

### Implementation for User Story 1

- [X] T011 [US1] Crear `estudios/desvios.py` con docstring (única regla y detección de desvíos; al vuelo y de solo lectura; usa el historial de `comparacion`): `Regla` (`dataclass(frozen=True)`: `umbral: Decimal`, `cantidad: int`); `regla()` (lee `settings.AQUALAB_DESVIOS`, `Decimal(str(umbral))`, `int(cantidad)`; `ImproperlyConfigured` si umbral ≤ 0 o cantidad < 1); `es_desvio(valor, referencia, umbral)` (`abs(valor - referencia) * 100 > umbral * abs(referencia)` si `referencia != 0`; si no, `valor != 0`); `mediana(valores)` (exacta; con N par, promedio de los dos centrales); `Deteccion` (`dataclass(frozen=True)`: `valor`, `unidad`, `referencia`, `diferencia`, `porcentaje`, `previos` (tupla de `Punto`), `presencia`); `HISTORIAL_INSUFICIENTE` (constante centinela); `historial_suficiente(historial, regla)`; `detectar(historial, regla)` (sin `historial.referencia` o con menos de `cantidad` anteriores → `None`; `ultimos = historial.anteriores[-cantidad:]`; presencia: desvío si todos los `ultimos` tienen el mismo valor y el de referencia es distinto, con `referencia` = ese valor común y `porcentaje=None`; si no, `referencia = mediana(ultimos)`, `es_desvio` para decidir y `comparacion.cambio` para la diferencia y el porcentaje); `evaluar_estudio(estudio, asignaciones, regla=None)` (asignaciones con resultado → una llamada a `comparacion.comparar(estudio.muestra.origen, estudio=estudio, codigos={…})` → dict `asignacion.pk → Deteccion | None | HISTORIAL_INSUFICIENTE`); `enlace_comparacion(estudio, codigo)` (`reverse("estudios:comparacion")` + `urlencode({"estudio": …, "pruebas": codigo, "elegir": 1})`); `texto_regla(regla)` y las propiedades de texto de `Deteccion` (`observado`, `referencia_texto`, `etiqueta_referencia`, `variacion_texto` con flecha y signo o «sin porcentaje (mediana previa 0)», en A/P «Presente (los últimos 3: Ausente)»); `constancia(asignacion, validacion, tipo_vertido)` (la `Deteccion` desde `desvio_referencia`), reutilizando `comparacion.numero`, `con_unidad`, `con_signo`, `texto_valor`, `cambio`.
- [X] T012 [US1] Crear `estudios/templates/estudios/desvio.html` (parcial; recibe `deteccion` o `validacion` + `estudio` y `codigo`): pendiente → badge con `ui/icono.html` (alerta) y «Desvío» (tono advertencia) y «Observado … · Mediana de los últimos N: … · ▲ … (… %)» (A/P: «Presente (los últimos 3: Ausente)»); revisado → badge «Desvío revisado» (tono neutro) y «Validado por {nombre} el {d/m/Y H:i} – {observación o «Sin observación»} · mediana …, umbral … %»; en ambos «Comparación histórica» solo con `perms.informes.ver_dashboard` y `ui/ayuda.html` con la regla vigente. Si hace falta, un filtro o `simple_tag` en `config/ui.py` que llame a los textos de `desvios`.
- [X] T013 [US1] En `estudios/views.py:detalle` llamar `desvios.evaluar_estudio(estudio, [a for a in pruebas_asignadas if a.estado == CARGADA])` y adjuntar `asignacion.deteccion` (solo si es `Deteccion`); para las Completadas usar `asignacion.validacion` (ya adjunta por `evaluar_asignaciones`) si `con_desvio`; pasar `regla_desvio = desvios.texto_regla(desvios.regla())`. En `estudios/templates/estudios/detalle.html` incluir `estudios/desvio.html` en la celda del resultado cuando hay `asignacion.deteccion` o `asignacion.validacion.con_desvio`.

**Checkpoint**: T008–T010 en verde; el detalle marca los desvíos y la corrección se refleja sola.

---

## Phase 4: User Story 2 — Desvíos pendientes en el dashboard (Priority: P1) (Tanda 1)

**Goal**: el Dashboard muestra la cantidad y los 10 más recientes; hay una lista completa paginada.

**Independent Test**: con 12 desvíos pendientes, el Dashboard muestra «12 pendientes», 10 filas y «Ver todos»; `estudios:desvios` muestra 12 en una página con todos los datos y enlaces.

### Tests for User Story 2

- [X] T014 [P] [US2] En `estudios/tests/test_desvios.py` agregar `test_pendientes` (de varios estudios y orígenes: incluye solo asignaciones Cargadas con `Deteccion`; excluye validadas, sin resultado, dentro del umbral y con historial insuficiente; orden por `resultado.fecha_calculo` descendente y pk; validar una o corregirla dentro del umbral la saca de la lista) y `test_consultas_pendientes` (`django_assert_max_num_queries`: con 1 estudio de 1 prueba y con 1 estudio de 6 pruebas, la misma cantidad; con 2 estudios crece en lo de un `comparar`; fijar los números observados).
- [X] T015 [P] [US2] En `estudios/tests/test_desvios_vista.py` agregar: `test_dashboard_contador_y_diez` (12 pendientes → «12 pendientes», 10 filas, enlace «Ver todos» a `estudios:desvios`; los más recientes primero; con 10 o menos no hay «Ver todos»), `test_dashboard_sin_desvios` («No hay desvíos sin revisar»), `test_dashboard_no_depende_del_periodo` (`?periodo=6_meses` y `?periodo=este_mes` con un pendiente calculado hace 3 meses —crear con `estudios.demo.reloj`— → aparece en ambos), `test_lista_completa_paginada` (30 pendientes → 25 en la página 1 y 5 en la 2), `test_enlaces` (fila: N° PI → `muestras:detalle`, cliente, origen, prueba, observado, mediana, porcentaje, fecha `d/m/Y`, «Ver estudio», «Comparación histórica» con `pruebas=CL-&elegir=1`, «Validar» → `estudios:validar_resultados` solo con `cliente_bioquimico`), `test_permisos_lista` (`estudios:desvios` sin sesión → login; `cliente_http` → 403; `POST` → 405).
- [X] T016 [P] [US2] En `informes/tests/test_dashboard.py` agregar `test_seccion_desvios_sin_revisar` (la sección con `aria-labelledby="titulo-desvios"` existe para `bioquimico` y el contador coincide con `len(desvios.pendientes())`).

### Implementation for User Story 2

- [X] T017 [US2] En `estudios/desvios.py` agregar `Pendiente` (`dataclass(frozen=True)`: `asignacion`, `estudio`, `muestra`, `prueba`, `deteccion`, `fecha_calculo`) y `pendientes(regla=None)`: `PruebaEstudio.objects.filter(estado=CARGADA, resultado__isnull=False).select_related("prueba", "resultado", "estudio__muestra__cliente", "estudio__muestra__origen")`, agrupar por estudio, `evaluar_estudio` por estudio, quedarse con las `Deteccion` y ordenar por `(fecha_calculo, pk)` descendente.
- [X] T018 [US2] Crear `estudios/templates/estudios/desvios_tabla.html` (parcial, recibe `pendientes`): `.tabla` con N° PI (enlace a `muestras:detalle`), Cliente · Origen, Prueba, Observado, Mediana, Variación (flecha y signo), Calculado (`d/m/Y`), Acciones («Ver estudio», «Comparación histórica» con `enlace_comparacion`, «Validar» con `perms.estudios.validar_resultados`); vacía: `ui/estado_vacio.html` «No hay desvíos sin revisar». En `estudios/views.py` agregar `desvios_pendientes` con `@permission_required("informes.ver_dashboard", raise_exception=True)` y `@require_GET`: `Paginator(desvios.pendientes(), 25)`, `page`, render de `estudios/templates/estudios/desvios.html` (encabezado «Desvíos sin revisar», «N pendientes», `ui/ayuda.html` con la regla y «Se revisan al validar la prueba», tabla, `ui/paginacion.html`); en `estudios/urls.py` `path("desvios/", views.desvios_pendientes, name="desvios")` antes de `<int:pk>/`.
- [X] T019 [US2] En `informes/views.py:dashboard` sumar `pendientes = desvios.pendientes()`, `desvios_cantidad = len(pendientes)`, `desvios_recientes = pendientes[:10]` y en `informes/templates/informes/dashboard.html` la sección «Desvíos sin revisar» (`<section class="tarjeta mb-6 p-5" aria-labelledby="titulo-desvios">`) con el contador «N pendientes», `{% include "estudios/desvios_tabla.html" with pendientes=desvios_recientes %}` y «Ver todos» si `desvios_cantidad > 10`. Sin relación con `periodo`. Recompilar el CSS si se usaron clases nuevas y versionar `static/css/aqualab.css`.

### Cierre de la Tanda 1

- [X] T020 Ejecutar `docker compose exec web pytest estudios informes` en verde (incluye los tests existentes de cálculo, corrección y comparación sin cambios de expectativa).
- [X] T021 Ejecutar `node --test usuarios/tests/js config/tests/js estudios/tests/js` en verde.
- [X] T022 Ejecutar `docker compose exec web ruff check .` y `docker compose exec web ruff format --check .` en verde. No correr la suite completa.

**Checkpoint (MVP)**: US1 + US2 completas; commit `feat(estudios): US 8.2 – Notificar desvíos relevantes (detección y dashboard)`.

---

## Phase 5: User Story 3 — Revisar el desvío al validar (Priority: P1) (Tanda 2)

**Goal**: la validación destaca los desvíos, admite una observación y guarda la constancia en la `Validacion`.

**Independent Test**: validar Cloruro con desvío y la observación «Se repitió la medición» → la `Validacion` tiene esa observación, `desvio_referencia=110` y `desvio_umbral=30`; el contador del dashboard baja en 1.

### Tests for User Story 3

- [ ] T023 [P] [US3] En `estudios/tests/test_desvios_validacion.py` agregar (servicio): `test_constancia_al_validar` (`validar_resultados(estudio.pk, elegidas, bioquimico, observaciones={pk: "  Se repitió la medición  "})` → la vigente tiene la observación recortada, `desvio_referencia == 110`, `desvio_umbral == 30`, `validada_por == bioquimico`; `resultado.con_desvio == [prueba]`), `test_sin_desvio_sin_constancia` (prueba sin desvío con observación enviada → se guarda la observación pero desvío nulo; sin observación → todo vacío), `test_no_elegida_no_guarda` (dos con desvío, se valida una → la otra sigue Cargada y en `pendientes()`), `test_omitida_no_guarda` (valor visto distinto → «cambió mientras se revisaba» y ninguna validación nueva; ya validada → «ya estaba validada» y la observación original no cambia), `test_validacion_fallida_no_guarda` (`mock.patch` que hace fallar `calculo.cambiar_estado` → no queda validación ni constancia), `test_constancia_inalterable` (después de validar, validar otro estudio del origen o cambiar `settings.AQUALAB_DESVIOS` no cambia `desvio_referencia`/`desvio_umbral` guardados), `test_correccion_posterior` (corregir el valor validado → la validación queda anulada con su constancia y la prueba vuelve a figurar en `pendientes()` si sigue con desvío), `test_evalua_al_confirmar` (validar con un historial que cambió después de abrir la pantalla → la constancia refleja la evaluación al confirmar).
- [ ] T024 [P] [US3] En `estudios/tests/test_desvios_vista.py` agregar (vista): `test_validacion_destaca_desvios` (GET de `estudios:validar_resultados` con `cliente_bioquimico`: «1 prueba con desvío», la fila de CL- con «Desvío», observado, mediana, «Comparación histórica» y el campo `observacion_<pk>` con su `help_text`; la fila sin desvío no tiene el campo), `test_historial_insuficiente_en_validacion` (prueba con 2 previos → «Historial insuficiente para detectar desvíos»), `test_confirmacion_cuenta_desvios_elegidos` (`accion=revisar` con 3 elegidas, 2 con desvío y una observación → «2 de los 3 resultados elegidos tienen desvío: quedarán revisados al validar.», la observación escrita y «Sin observación» en la otra; los `observacion_<pk>` viajan ocultos), `test_observacion_larga_no_avanza` (501 caracteres → la misma pantalla con el error junto al campo), `test_editar_conserva_observacion` (`accion=editar` vuelve con el texto), `test_confirmar_avisa_revisados` (`accion=confirmar` → mensaje de éxito existente y «Se revisó 1 desvío: CL-.»; el detalle muestra «Desvío revisado»), `test_permisos` (no existe URL de revisión aparte: `reverse("estudios:revisar_desvio", …)` lanza `NoReverseMatch`; `cliente_http` recibe 403 en la validación; «Validar» no aparece en la lista sin permiso).
- [ ] T025 [P] [US3] Crear `estudios/tests/test_desvios_concurrencia.py` (`pytestmark = pytest.mark.django_db(transaction=True)`, patrón de `estudios/tests/test_concurrencia_validacion.py` con `threading.Barrier` y `ThreadPoolExecutor`): `test_dos_validaciones_simultaneas` (dos bioquímicos validan CL- con observaciones distintas → una sola `Validacion` vigente con la observación del que validó y la constancia; el otro recibe «ya estaba validada»), `test_correccion_y_validacion_simultaneas` (corrección que cambia el valor vs validación del valor viejo → o se valida el viejo y la corrección anula la validación, o la validación se omite por «cambió mientras se revisaba»; nunca queda una validación vigente sobre un valor distinto del resultado).

### Implementation for User Story 3

- [ ] T026 [US3] En `estudios/servicios.py:validar_resultados` agregar el parámetro `observaciones=None`; después de obtener las asignaciones bloqueadas, `regla = desvios.regla()` y `evaluacion = desvios.evaluar_estudio(estudio, list(asignaciones), regla)`; en el `Validacion.objects.create` sumar `observacion=(observaciones or {}).get(asignacion.pk, "").strip()[:500]` y, si `isinstance(evaluacion.get(asignacion.pk), desvios.Deteccion)`, `desvio_referencia=deteccion.referencia`, `desvio_umbral=regla.umbral` y `resultado.con_desvio.append(prueba)`. Sumar `con_desvio: list = field(default_factory=list)` a `ResultadoValidacion`. Actualizar el docstring. Actualizar `estudios/tests/utiles.py:validar` para aceptar `observaciones=None` y pasarlo por código (`{"CL-": "…"}` → pk).
- [ ] T027 [US3] En `estudios/forms.py:ValidarResultadosForm` aceptar en cada fila `asignacion.deteccion` (`Deteccion` o `None`) y, solo para esas filas, crear `observacion_<pk>` = `forms.CharField(required=False, max_length=500, label=f"Observación {codigo}", help_text="Queda guardada en la validación de esta prueba como revisión del desvío. Solo la ve el laboratorio.", widget=forms.Textarea(attrs={"rows": 2}))`; métodos `observacion(asignacion)` (nombre del campo), `con_desvio()`, `elegidas_con_desvio()` (de `resumen()`), `observaciones()` (`{pk: texto}` solo de las elegidas con desvío). Incluir el campo en `filas()`.
- [ ] T028 [US3] En `estudios/views.py:validar_resultados`: antes de construir el formulario, `evaluacion = desvios.evaluar_estudio(estudio, filas)` y adjuntar `asignacion.deteccion` y `asignacion.historial_insuficiente`; contexto `desvios_en_pantalla` (cantidad) y `regla_desvio`; en `accion == "revisar"` pasar `elegidas_con_desvio`; al confirmar llamar `servicios.validar_resultados(estudio.pk, form.elegidas(), request.user, observaciones=form.observaciones())` y, si `resultado.con_desvio`, `messages.success` «Se revisó 1 desvío: CL-.» / «Se revisaron N desvíos: CL-, …».
- [ ] T029 [US3] En `estudios/templates/estudios/validar_resultados.html`: mensaje de advertencia con ícono «N prueba(s) con desvío» y la regla en `ui/ayuda.html`; filas con desvío destacadas (clase de advertencia + ícono + «Desvío») con `estudios/desvio.html` y el campo de observación vía `ui/campo.html`; filas con historial insuficiente con «Historial insuficiente para detectar desvíos». En `estudios/templates/estudios/validar_resultados_confirmar.html`: si hay elegidas con desvío, «N de los M resultados elegidos tienen desvío: quedarán revisados al validar.» y lista Prueba · Observado · Mediana · Observación («Sin observación» si está vacía); `observacion_<pk>` ocultos junto a `resultado_<pk>`.

---

## Phase 6: User Story 4 — La advertencia no bloquea (Priority: P2) (Tanda 2)

**Goal**: validar e informar funcionan igual con desvíos; nada sale al cliente.

**Independent Test**: validar Cloruro con desvío sin observación → validado, mismo valor, constancia con observación vacía; el informe emitido no menciona desvíos.

### Tests for User Story 4

- [ ] T030 [P] [US4] En `estudios/tests/test_desvios_validacion.py` agregar `test_validar_con_desvio_sin_observacion` (valida, `Resultado.valor` igual, prueba Completada, estudio Finalizado si era la última, constancia con `observacion == ""`).
- [ ] T031 [P] [US4] En `estudios/tests/test_desvios_vista.py` agregar `test_no_aparece_en_informe_pdf_ni_correo` (estudio validado con desvío y observación, emitido: `informes:vista_previa` (antes de emitir), `informes:ver`, `informes:imprimir`, el texto del correo de `informes/correos/` y `informes.contenido.armar_contenido` no contienen «Desvío», «desvío» ni la observación; parchear `informes.envios.generar_pdf`) y `test_control_sin_cambios` (`informes:control` no menciona desvíos).

### Implementation for User Story 4

- [ ] T032 [US4] Verificar contra T030–T031 que `informes/contenido.py`, `informes/templates/informes/documento*.html`, `impreso.html` y `correos/` no usan `observacion` ni `desvio_*`; si algún test falla, corregir el origen (no agregar filtros en `informes`).

---

## Phase 7: User Story 5 — Ajustar la regla con el laboratorio (Priority: P3) (Tanda 2)

**Goal**: umbral y cantidad en un solo lugar; las validaciones conservan el umbral usado.

**Independent Test**: con `settings.AQUALAB_DESVIOS = {"umbral": "50", "cantidad": 3}`, un pendiente de +45,5 % deja de figurar; una validación anterior con desvío sigue diciendo «umbral 30 %».

### Tests for User Story 5

- [ ] T033 [P] [US5] En `estudios/tests/test_desvios.py` agregar `test_regla_configurable` (fixture `settings`: umbral 50 → 160 contra 110 da `None`; cantidad 2 → con 2 previos se evalúa), `test_regla_invalida` (umbral "0" o cantidad 0 → `ImproperlyConfigured`), `test_texto_regla_vigente` (la ayuda de la lista y de la validación muestra «más de un 50 % respecto del mediana de los últimos 3 resultados validados del origen» con umbral 50) y `test_regla_en_un_solo_lugar` (recorrer los `.py` de `estudios/` e `informes/` sin `tests/` ni `migrations/`: solo `estudios/desvios.py` lee `AQUALAB_DESVIOS`).
- [ ] T034 [P] [US5] En `estudios/tests/test_desvios_vista.py` agregar `test_cambio_de_regla_conserva_constancia` (validación con desvío y umbral 30; cambiar a 50 → el detalle sigue mostrando «umbral 30 %»).

### Implementation for User Story 5

- [ ] T035 [US5] Revisar que todas las plantillas y vistas obtienen la regla con `desvios.regla()` / `texto_regla` (ninguna escribe «30 %» o «3» a mano) y que la marca «Desvío revisado» muestra `validacion.desvio_umbral`, no la regla vigente.

---

## Phase 8: Polish & Cross-Cutting Concerns (Tanda 2)

- [ ] T036 En `estudios/demo.py:cargar_estudio` pasar `observaciones` a `validar_resultados` para el estudio FQ de «pozo-2» del mes 1: `{asignación de CL-: "Se repitió la medición: el valor es correcto."}` (research R10). En `estudios/tests/test_demo.py` agregar `test_desvios_de_la_demo`: el Cloruro de Pozo 2 mes 0 figura en `desvios.pendientes()` con `valor == 430`, `referencia == 124` y `porcentaje == Decimal("246.8")`; la validación vigente del Cloruro de Pozo 2 mes 1 tiene esa observación, `desvio_umbral == 30` y `desvio_referencia == 121`; fijar `len(desvios.pendientes())` con el valor observado y que todos son de estudios PARCIAL/CARGADO del guion.
- [ ] T037 [P] En `CLAUDE.md` agregar la sección «Desvíos (US 8.2)»: `estudios/desvios.py` es la única regla y detección (`regla`, `es_desvio`, `detectar`, `evaluar_estudio`, `pendientes`), de solo lectura y al vuelo (no hay modelo de desvíos; no tocar `calculo.py`); regla en `settings.AQUALAB_DESVIOS`; historial = `comparacion.comparar` + `HistorialPrueba.anteriores[-N:]`; referencia = mediana de los últimos N (no el promedio: un pico aislado no la mueve); A/P por cambio de estado con el valor común como referencia; **validar es revisar**: `validar_resultados(..., observaciones)` reevalúa bajo el bloqueo y guarda `Validacion.observacion`, `desvio_referencia` y `desvio_umbral` (constancia; `CheckConstraint` ambos o ninguno); campo `observacion_<pk>` de `ValidarResultadosForm`; no hay pantalla aparte; casos de la demo (Pozo 2 mes 0 pendiente, mes 1 validado con observación). En la sección de la US 8.3 reemplazar «La 8.2 agrega acá la lista de desvíos sin revisar» por la referencia a esta sección; en la de la US 8.1 mencionar `anteriores`.
- [ ] T038 [P] Recompilar el CSS si se usaron clases nuevas en la tanda 2 (comando de `README.md`/`package.json`) y versionar `static/css/aqualab.css`; el CI verifica que esté al día.
- [ ] T039 [P] Actualizar `specs/032-notificar-desvios/quickstart.md` si algún texto o número cambió durante la implementación (p. ej. la cantidad de pendientes de la demo).
- [ ] T040 Verificar que `git diff main -- estudios/calculo.py` está vacío y que no hay modelo `Desvio`, comando `evaluar_desvios` ni URL `revisar_desvio` (`grep -rn "class Desvio\|evaluar_desvios\|revisar_desvio" estudios informes`).
- [ ] T041 **Prueba en el navegador (la hace el autor; no marcar)**: recorrer `quickstart.md` escenarios 1 a 7 con la demo cargada, incluido el técnico sin permiso de validar.
- [ ] T042 **Cierre de la tanda 2**: ejecutar `docker compose exec web pytest estudios informes`, `node --test usuarios/tests/js config/tests/js estudios/tests/js`, `docker compose exec web ruff check .` y `docker compose exec web ruff format --check .`: en verde. No correr la suite completa (la corre el CI en el PR «SCRUM-61 – 8.2 Notificar desvíos relevantes»).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Fase 1)**: T001 primero; T002 antes de cualquier test de regla.
- **Foundational (Fase 2)**: T003 → T004; T007 después de T006; bloquea todas las historias.
- **US1 (Fase 3)**: depende de la Fase 2. T011 → T012 → T013.
- **US2 (Fase 4)**: depende de T011 (`evaluar_estudio`) y T012 (no usa la marca, pero comparte textos). Cierra la tanda 1 (T020–T022).
- **US3 (Fase 5)**: depende de US1 (T011, T012); independiente de US2 salvo `test_no_elegida_no_guarda`, que usa `pendientes()` (T017). T026 → T027 → T028 → T029.
- **US4 (Fase 6)**: depende de US3 (valida con desvío).
- **US5 (Fase 7)**: depende de US1, US2 y US3 (textos de la regla en sus pantallas).
- **Polish (Fase 8)**: T036 depende de US3 (`observaciones`); T041 y T042 al final.

### Within Each User Story

- Tests primero (deben fallar), después `desvios.py`/servicio, después vistas y plantillas.

### Parallel Opportunities

- T005 y T006 en paralelo (archivos distintos).
- T008, T009 y T010 en paralelo (T008/T009 en `test_desvios.py` por secciones; T010 en `test_desvios_vista.py`).
- T014, T015 y T016 en paralelo (tres archivos).
- T023, T024 y T025 en paralelo (tres archivos).
- T030 y T031 en paralelo; T033 y T034 en paralelo.
- T037, T038 y T039 en paralelo.

### Parallel Example: Tanda 1

```text
Juntos: T005 (test_desvios_validacion.py) · T006 (test_comparacion.py)
Juntos: T008/T009 (test_desvios.py) · T010 (test_desvios_vista.py)
Juntos: T014 (test_desvios.py) · T015 (test_desvios_vista.py) · T016 (informes/tests/test_dashboard.py)
```

### Parallel Example: Tanda 2

```text
Juntos: T023 (servicio) · T024 (vista) · T025 (concurrencia)
Juntos: T037 (CLAUDE.md) · T038 (CSS) · T039 (quickstart)
```

---

## Implementation Strategy

### MVP First (Tanda 1: US1 + US2)

1. Setup y Foundational (T001–T007): configuración, campos de `Validacion` y migración,
   `anteriores`.
2. US1 (T008–T013): `estudios/desvios.py`, marca en el detalle.
3. US2 (T014–T019): `pendientes()`, lista `estudios:desvios` y sección del dashboard.
4. **Validar** con `pytest estudios informes`, `node --test …` y ruff (T020–T022). Commit.

### Incremental Delivery (Tanda 2)

1. US3 (T023–T029): validación con observación y constancia → validar revisa.
2. US4 (T030–T032) y US5 (T033–T035): no bloqueo y regla configurable.
3. Polish (T036–T040): demo, CLAUDE.md, CSS, quickstart, verificación de lo que no debe existir;
   cierre con los tests de `estudios` e `informes`, Node y ruff (T042). La prueba en el navegador
   (T041) la hace el autor y el CI corre la suite completa en el PR.
