---

description: "Lista de tareas de la US 6.2 – Cálculo automático del resultado"
---

# Tasks: Cálculo automático del resultado

**Input**: `specs/016-calcular-resultado/` (`plan.md`, `spec.md`, `research.md`, `data-model.md`,
`contracts/calculo-resultado.md`, `quickstart.md`)

**Prerequisites**: `plan.md`, `spec.md` y US 6.1 en `main` (PR #28): `estudios.Medicion` con
`valor_ingresado`, `cargar_mediciones` y `ResultadoCarga` en `estudios/servicios.py`, la vista
`cargar_mediciones` y la columna Medición de `detalle.html`; catálogo de SCRUM-64
(`importar_catalogo_pruebas`, `referencias_formula`, `TipoCalculo`); fixtures `empleado`,
`muestra` y `cliente_http` de `estudios/tests/conftest.py`; esquema de hilos de
`estudios/tests/test_concurrencia_mediciones.py`.

**Tests**: SÍ. La constitution (principio III) exige un test por escenario de aceptación y probar
los cálculos con casos conocidos y valores esperados explícitos. Los tests siguen el «Mapa de
tests» de `plan.md` y se escriben **antes** de la implementación de cada historia.

**Organization**: tres user stories de la spec — US1 (P1, resultado al cargar la medición), US2
(P2, pruebas calculadas a partir de otras) y US3 (P3, recálculo al cambiar una medición).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: se puede ejecutar en paralelo (archivos distintos, sin dependencias pendientes)
- **[Story]**: user story a la que pertenece la tarea (`[US1]`, `[US2]`, `[US3]`)
- Rutas relativas a la raíz del repo

## Convenciones para todas las tareas

- Textos de UI, mensajes y nombres de dominio en **español** (principio VI). Mensajes y motivos
  copiados **literalmente** de `contracts/calculo-resultado.md`.
- **Nunca `float`**: todo número de una fórmula se construye con `Decimal(texto)`; las cuentas
  corren dentro de `decimal.localcontext()` con `prec = 34` (research R1).
- `recalcular` siempre se llama con el estudio ya bloqueado (`select_for_update`) dentro de la
  transacción del llamador; nunca abre su propia transacción.
- Una sola migración: `estudios/migrations/0005_resultado.py` (generada con `makemigrations`).
- Comandos dentro de Docker: `docker compose exec web pytest pruebas estudios`,
  `docker compose exec web ruff check .`, `docker compose exec web ruff format --check .`.

---

## Phase 1: Setup (Shared Infrastructure)

- [X] T001 **Gate de la constitution (principio I)**: confirmar que el equipo aprobó `specs/016-calcular-resultado/spec.md` (incluida la excepción al principio IV de *Complexity Tracking* en `plan.md`) y actualizar su `**Status**` a «Aprobada (fecha)»; sin esa aprobación no se ejecuta ninguna otra tarea. Después, ejecutar `docker compose exec web pytest` y `docker compose exec web python manage.py makemigrations --check --dry-run` y confirmar suite en verde y sin cambios pendientes.

---

## Phase 2: Foundational (Blocking Prerequisites)

**⚠️ CRITICAL**: ninguna historia empieza antes de terminar esta fase.

### Tests (escribir primero, deben fallar)

- [X] T002 [P] Crear `pruebas/tests/test_formulas.py` (sin base de datos salvo donde se indica):
  - `test_evaluar_formula_casos_conocidos` (parametrizado): cada fila de la tabla «Casos conocidos» de `contracts/calculo-resultado.md` evaluada con `evaluar_formula(formula, x, resultados)`, comparando con el `Decimal` exacto calculado aparte (por ejemplo, NA con x = 0,5 → `Decimal("1.170850714285714285714285714285714")`, RAS → el valor de `(Decimal(46) / ((Decimal(80) + Decimal("24.3")) / 2).sqrt())` con `prec = 34`); más una fila por cada fórmula distinta del CSV que no esté en la tabla (`x*20`, `{CO3}/30`, `{HCO3}/61`, `{CL-}/35.5`, `{COND}/{CATIONES}`, `{ALC-BO3}*1.22`, `{ALC-CO3}*0.6`, `{NA}/23`, `{K}/39.1`, `{CA}/20`, `{MG}/12.2`, `({NA-MEQ}+{K-MEQ}+{CA-MEQ}+{MG-MEQ})`) con valores elegidos y su esperado exacto (SC-001);
  - `test_evaluar_formula_operadores`: `-x+3` con x = 1 → `Decimal("2")`; `2*(3+4)` → 14; `10/4` → `Decimal("2.5")`; `sqrt(16)` → 4; `{ A }` con espacios recorta el código;
  - `test_evaluar_formula_division_por_cero`: `{CATIONES}` = 0 en `{COND}/{CATIONES}` → `CalculoImposible` con `motivo == "división por cero"`;
  - `test_evaluar_formula_raiz_negativa`: `sqrt(x)` con x = -1 → `motivo == "raíz cuadrada de un número negativo"`;
  - `test_evaluar_formula_sin_x`: `x*10` con `x=None` → `CalculoImposible` (motivo «la fórmula usa el valor medido y la prueba no tiene medición»);
  - `test_validar_formula_rechaza` (parametrizado): `""`, `"__import__('os')"`, `"x**2"`, `"1e3"`, `"abs(x)"`, `"{}"`, `"(x+1"`, `"x+"`, `"x y"`, `"1,5*x"`, `"y*2"` → `FormulaInvalida`;
  - `test_formulas_del_catalogo_validas`: leer `pruebas/datos/catalogo_pruebas_agua.csv` con `csv.DictReader` y llamar a `validar_formula` en cada fórmula no vacía (las 25);
  - `test_prueba_clean_rechaza_formula_invalida` (`django_db`): `Prueba(codigo="T", nombre="T", tipo_calculo="FORMULA", formula="x**2").full_clean()` lanza `ValidationError` con la clave `formula`.
- [X] T003 [P] Agregar en `estudios/tests/test_modelos.py`:
  - `test_valor_mostrado` (parametrizado): `Decimal("23.5")`→`Decimal("23.5")`, `Decimal("0.00412")`→`Decimal("0.0041")`, `Decimal("1234.5")`→`Decimal("1234.5")`, `Decimal("1000")`→ se ve «1000» con `django.utils.formats.localize`, `Decimal("0")`→ `Decimal("0")`, `Decimal("-0.00001")`→ `Decimal("0")` (sin signo), `Decimal("1.17085")` → `Decimal("1.1709")`;
  - `test_un_resultado_por_asignacion`: un segundo `Resultado` para la misma asignación lanza `IntegrityError`;
  - `test_asignacion_con_resultado_protegida`: borrar una `PruebaEstudio` con `Resultado` lanza `ProtectedError`;
  - `test_admite_correcciones_por_estado` (parametrizado): `True` salvo en `informe_generado`;
  - `test_filtro_unidad` (parametrizado): `config.ui.unidad("mg/l")` → `"mg/l"`; `""`, `"--"`, `" -- "` y `None` → `"Sin unidad"`.

### Implementación

- [X] T004 [P] Crear `pruebas/formulas.py` (research R1, data-model «Gramática de fórmulas»): `class FormulaInvalida(ValidationError)`; `class CalculoImposible(Exception)` con atributo `motivo`; un tokenizador con `re.compile(r"\s*(\d+(?:\.\d+)?|x|\{[^{}]+\}|sqrt|[-+*/()])")` que exige consumir todo el texto; un analizador descendente recursivo (`expresion`, `termino`, `factor`) que arma un árbol de tuplas; `validar_formula(texto)` (solo analiza; `FormulaInvalida("La fórmula no es válida: …")` con la posición) y `evaluar_formula(texto, x, resultados)` que evalúa el árbol dentro de `localcontext()` con `prec = 34`, convirtiendo `decimal.DivisionByZero`/`InvalidOperation` en `CalculoImposible("división por cero")` y raíz de negativo en `CalculoImposible("raíz cuadrada de un número negativo")`; `x` con `x is None` → `CalculoImposible("la fórmula usa el valor medido y la prueba no tiene medición")`; `{CODIGO}` se toma de `resultados[codigo.strip()]` (el llamador garantiza que están; `KeyError` → `CalculoImposible("falta el resultado de CODIGO")`).
- [X] T005 En `pruebas/models.py`, `Prueba.clean()`: si `tipo_calculo == FORMULA` y hay fórmula, llamar a `validar_formula(self.formula)` y convertir `FormulaInvalida` en `ValidationError({"formula": ...})`, antes de las validaciones de referencias existentes (depende de T004).
- [X] T006 Agregar en `estudios/models.py` (data-model §1–2): propiedad `Estudio.admite_correcciones` → `self.estado != EstadoEstudio.INFORME_GENERADO`; modelo `Resultado` con `asignacion = models.OneToOneField(PruebaEstudio, on_delete=models.PROTECT, related_name="resultado", editable=False)`, `valor = models.DecimalField("valor", max_digits=28, decimal_places=10)`, `unidad = models.CharField("unidad", max_length=50, blank=True, default="")`, `formula = models.CharField("fórmula", max_length=255, blank=True, default="")`, `fecha_calculo = models.DateTimeField("fecha de cálculo", auto_now=True)`; `verbose_name` «resultado» / «resultados»; propiedad `valor_mostrado` (`valor.quantize(Decimal("0.0001"), ROUND_HALF_UP)`, `normalize()`, y `Decimal(0)` si es cero); `__str__` como `Medicion`.
- [X] T007 [P] Agregar en `config/ui.py` el filtro `@register.filter def unidad(texto)`: devuelve `"Sin unidad"` si `(texto or "").strip()` está vacío o es `"--"`, si no el texto. Reemplazar `|default:"Sin unidad"` por `|unidad` en `estudios/templates/estudios/cargar_mediciones.html`, `cargar_mediciones_confirmar.html` y en la columna Medición de `detalle.html` (US 6.1 mostraba «--» para Sodio o Potasio).
- [X] T008 Generar `estudios/migrations/0005_resultado.py` con `docker compose exec -u "$(id -u):$(id -g)" web python manage.py makemigrations estudios --name resultado` y verificar que solo crea `Resultado` (depende de T006).
- [X] T009 [P] Agregar en `estudios/tests/conftest.py`:
  - fixture `catalogo`: `call_command("importar_catalogo_pruebas", stdout=io.StringIO())` y devuelve `{p.codigo: p for p in Prueba.objects.all()}`;
  - fixture `pruebas_division()`: crea `DIV-A` y `DIV-B` (Directo, unidad «u») y `DIV` (`tipo_calculo=FORMULA`, `formula="{DIV-A}/{DIV-B}"`, `es_calculada=True`, unidad «u»), para los casos de división por cero;
  - fixture `estudio_de(muestra, empleado, catalogo)`: fábrica `crear(*codigos)` que arma un `TipoEstudio` con `Prueba.objects.filter(codigo__in=codigos)` (así sirve también para pruebas de test creadas en el test; nombre del tipo único por llamada) y devuelve el estudio creado con `crear_estudio`;
  - helper `cargar(estudio, usuario, valores=None, **por_nombre)` (función en `estudios/tests/utiles.py`): llama a `cargar_mediciones` con `{asignacion.pk: Decimal(texto)}` buscando cada código; acepta un `dict` `{codigo: texto}` (para códigos con `/` como `COND/CATIONES`) y argumentos con nombre, donde los `_` se leen como `-` (`CL_` → `CL-`, `DUREZA_T` → `DUREZA-T`).
- [X] T010 Ejecutar `docker compose exec web pytest pruebas estudios` y dejar en verde T002–T003, la importación del catálogo (SCRUM-64) y US 6.1 (depende de T002–T009).

**Checkpoint**: fórmulas evaluables y validadas, modelo `Resultado` listo.

---

## Phase 3: User Story 1 - Obtener el resultado de cada prueba al cargar su medición (Priority: P1) 🎯 MVP

**Goal**: al guardar la medición de una prueba Directa o de Fórmula (sin referencias), se guarda su
resultado con unidad y fórmula, y el detalle lo muestra.

**Independent Test**: cargar PH = 7,20 y CL- = 2,35 y verificar `Resultado` 7.2 UpH y 23.5 mg/l y
el detalle «7,2 UpH» y «23,5 mg/l».

### Tests for User Story 1 ⚠️ (escribir primero, deben fallar)

- [X] T011 [P] [US1] Crear `estudios/tests/test_calculo.py` (`pytestmark = pytest.mark.django_db`):
  - `test_carga_calcula_resultado_directo_y_formula`: con `estudio_de("PH", "CL-", "NTK-T")`, cargar PH = 7.20, CL- = 2.35 y NTK-T = 10: `Resultado` de PH con `valor == Decimal("7.2")`, `unidad == "UpH"`, `formula == ""`; de CL- con `Decimal("23.5")`, `"mg/l"`, `"x*10"`; de NTK-T con `Decimal("211.2")`; las asignaciones siguen `cargada`.
  - `test_resultado_conserva_formula_y_unidad`: después de calcular CL-, cambiar en el catálogo su fórmula a `x*100` y su unidad a `g/l`: el `Resultado` conserva `x*10`, `mg/l` y `23.5` (FR-010).
  - `test_calculo_no_modifica_otros_datos`: con otro estudio del mismo tipo, cargar CL- en el primero no cambia la `Medicion` (valor y decimales), la muestra, los snapshots, el catálogo ni el otro estudio (FR-012).
- [X] T012 [P] [US1] Agregar en `estudios/tests/test_cargar_mediciones.py`: `test_detalle_muestra_resultado`: con `estudio_de("PH", "CL-")` cargado por la vista, el detalle tiene la columna «Resultado» con «7,2 UpH», «23,5 mg/l» y «Fórmula: x*10»; la medición de PH sigue «7,20 UpH». Con `estudio_de("NA")` cargado (unidad de medición `--`), la columna Medición muestra «Sin unidad» y nunca «--».

### Implementation for User Story 1

- [X] T013 [US1] Crear `estudios/calculo.py` con `recalcular(estudio, asignaciones)` en su versión para pruebas con medición (research R3, paso 4): por cada asignación, ordenada por código, con `prueba.tipo_calculo == DIRECTO` → valor = `medicion.valor`; con `FORMULA` → `evaluar_formula(prueba.formula, medicion.valor, {})`; guardar con `Resultado.objects.update_or_create(asignacion=..., defaults={valor (quantize a 10 decimales, ROUND_HALF_UP), unidad: prueba.unidad, formula: prueba.formula})`; resultado con más de 18 cifras enteras → tratarlo como `CalculoImposible("el resultado es demasiado grande")`; si falla, devolver `(prueba, motivo)` en la lista sin crear `Resultado`. Devuelve la lista de fallas (depende de T006).
- [X] T014 [US1] En `estudios/servicios.py`, `ResultadoCarga` suma `sin_calcular: list = field(default_factory=list)`; `cargar_mediciones` llama a `calculo.recalcular(estudio, [m.asignacion for m in resultado.guardadas])` antes de cerrar la transacción (si hubo guardadas) y guarda las fallas en `sin_calcular`. En `estudios/views.py`, `cargar_mediciones` (confirmar) agrega `messages.warning(f"{prueba.codigo}: no se pudo calcular el resultado ({motivo}).")` por cada par de `resultado.sin_calcular` (FR-013; así el MVP no las descarta en silencio) (depende de T013).
- [X] T015 [US1] En `estudios/views.py`, `detalle`: sumar `"resultado"` al `select_related` de las asignaciones. En `estudios/templates/estudios/detalle.html`: columna **Resultado** entre Medición y Estado: con resultado, `<span class="numeros font-semibold text-tinta">{{ asignacion.resultado.valor_mostrado }} {{ asignacion.resultado.unidad|unidad }}</span>` y, si tiene fórmula, `<span class="block text-xs text-tinta-suave">Fórmula: {{ asignacion.resultado.formula }}</span>`; sin resultado, «—» por ahora (US2 agrega el motivo) (depende de T006).
- [X] T016 [US1] Ejecutar `docker compose exec web pytest pruebas estudios` y dejar en verde T011–T012 sin romper US 6.1 (depende de T013–T015).

**Checkpoint**: las pruebas medidas obtienen su resultado al guardarse; MVP de la US 6.2.

---

## Phase 4: User Story 2 - Calcular las pruebas que dependen de otras (Priority: P2)

**Goal**: las pruebas calculadas se resuelven en cuanto tienen sus referencias, en orden de
dependencia; el detalle explica cada resultado faltante y la carga advierte las fórmulas que fallan.

**Independent Test**: con CA, DUREZA-T y MG, cargar CA (MG advierte que falta DUREZA-T), cargar
DUREZA-T (MG = 24,3 y Cargada).

### Tests for User Story 2 ⚠️ (escribir primero, deben fallar)

- [X] T017 [P] [US2] Agregar en `estudios/tests/test_calculo.py`:
  - `test_calculada_se_calcula_al_completar_referencias`: `estudio_de("CA", "DUREZA-T", "MG")`; cargar CA = 80 → MG sin `Resultado` y `pendiente`; cargar DUREZA-T = 15 (resultado 300 por `x*20`) → MG con `Decimal("24.3")`, `unidad "mg/l"`, fórmula `({DUREZA-T}-{CA}*2.5)*0.243` y estado `cargada`.
  - `test_cadena_de_calculadas`: `estudio_de("NA", "K", "CA", "DUREZA-T", "MG", "NA-MEQ", "K-MEQ", "CA-MEQ", "MG-MEQ", "CATIONES")`; cargar todas las medidas en un solo `cargar` → `CATIONES` tiene el valor esperado calculado aparte con `Decimal` (suma de los cuatro Meq/l) y todas las calculadas están `cargada`.
  - `test_motivo_sin_resultado` (parametrizado): sin medición (PH sin cargar) → «Falta la medición.»; MG con CA cargado y sin DUREZA-T → «Faltan resultados de: DUREZA-T · Dureza Total.»; `estudio_de("CA", "MG")` con CA cargado → «No forma parte del estudio: DUREZA-T · Dureza Total.»; con `pruebas_division`, `estudio_de("DIV-A", "DIV-B", "DIV")` con DIV-A = 5 y DIV-B = 0 → «No se pudo calcular: división por cero.».
  - `test_falla_de_calculo_no_impide_guardar`: en el caso de división por cero, las `Medicion` de DIV-A y DIV-B existen con su `Resultado`, DIV no tiene `Resultado` y sigue `pendiente`, y `ResultadoCarga.sin_calcular` contiene `(DIV, "división por cero")`.
  - `test_referencias_circulares`: crear dos pruebas calculadas de test (`CIRC-A` con `{CIRC-B}*1` y `CIRC-B` con `{CIRC-A}*1`, más una medida que no participa) y un estudio con ellas; `recalcular` con el estudio bloqueado las deja sin resultado y el motivo es «No se pudo calcular: referencias circulares.».
- [X] T018 [P] [US2] Agregar en `estudios/tests/test_cargar_mediciones.py`: `test_mensaje_carga_advierte_falla_de_calculo`: confirmar por la vista la carga que produce la división por cero → mensajes incluyen «DIV: no se pudo calcular el resultado (división por cero).» y no incluyen advertencias por pruebas que solo esperan referencias; el detalle muestra los motivos de la tabla del contrato.

### Implementation for User Story 2

- [X] T019 [US2] Completar `estudios/calculo.py` (research R3, pasos 1–3 y 5): cargar todas las asignaciones del estudio con `select_related("prueba", "medicion", "resultado")`; `por_codigo = {a.prueba.codigo: a}`; grafo de dependientes con `referencias_formula`; afectadas = las cambiadas + clausura de dependientes; orden topológico (Kahn) sobre las afectadas; las que no salen del orden quedan con `CalculoImposible("referencias circulares")`. Para cada afectada: si alguna referencia no está en `por_codigo` o no tiene resultado (todavía), no se calcula ni se informa como falla; las calculadas se evalúan con `x=None` y `resultados={codigo: resultado.valor}`; si se calcula, `update_or_create` del `Resultado` y, si es calculada y `pendiente`, pasarla a `cargada`. Mantener actualizado en memoria el resultado de cada asignación para las siguientes del orden (depende de T013).
- [X] T020 [US2] Agregar en `estudios/calculo.py` `motivo_sin_resultado(asignacion, por_codigo)` (research R4): devuelve `None` si tiene resultado; si no, en este orden: prueba no calculada sin medición → «Falta la medición.»; referencias ausentes del estudio → «No forma parte del estudio: COD · nombre, …» (nombre del catálogo, en orden de código); referencias sin resultado → «Faltan resultados de: COD · nombre, …»; si no, evaluar y devolver «No se pudo calcular: <motivo>.». Para las ausentes del estudio buscar el nombre en `Prueba.objects.filter(codigo__in=...)`; si el código no existe en el catálogo, mostrar solo el código (depende de T019).
- [X] T021 [US2] En `estudios/views.py`: `detalle` calcula `asignacion.motivo_sin_resultado` con `calculo.motivo_sin_resultado` para cada asignación sin resultado y el template lo muestra en `text-xs text-tinta-suave` en lugar de «—» (las advertencias de la carga ya las agrega T014) (depende de T014, T020).
- [X] T022 [US2] Ejecutar `docker compose exec web pytest pruebas estudios` y dejar en verde T017–T018 junto con US1 (depende de T019–T021).

**Checkpoint**: las calculadas se resuelven solas y cada faltante explica su motivo.

---

## Phase 5: User Story 3 - Recalcular al cambiar una medición (Priority: P3)

**Goal**: el servicio que usará US 6.3 recalcula la prueba cambiada y sus dependientes, quita la
validación de los recalculados y rechaza cambios con informe emitido.

**Independent Test**: con CA, DUREZA-T y MG calculados, cambiar la medición de CA y llamar a
`recalcular_resultados`: CA y MG cambian, DUREZA-T no.

### Tests for User Story 3 ⚠️ (escribir primero, deben fallar)

- [X] T023 [P] [US3] Agregar en `estudios/tests/test_calculo.py` (helper `corregir(asignacion, texto)` que actualiza `Medicion.valor` y `decimales` como lo hará US 6.3 y llama a `recalcular_resultados(estudio.pk, [asignacion.pk], empleado)` dentro de `transaction.atomic()`):
  - `test_recalcular_actualiza_dependientes_y_no_otras`: `estudio_de("CA", "DUREZA-T", "MG", "PH")` cargado; corregir CA de 80 a 40 → CA = 40 y MG = `(300 - 100) * 0.243` = `Decimal("48.6")`; DUREZA-T y PH conservan valor y `fecha_calculo`.
  - `test_recalculo_quita_validacion`: con MG y CA en `completada` (`update`), corregir CA → ambos pasan a `cargada` con el valor nuevo; DUREZA-T, también `completada`, sigue `completada`.
  - `test_recalcular_con_informe_emitido_rechaza`: con el estudio en `informe_generado`, corregir CA dentro de `transaction.atomic()` → `RecalculoError` con «El estudio ya tiene el informe emitido: sus mediciones y resultados no se pueden cambiar.», y al revertir la transacción la `Medicion` y los resultados quedan como estaban.
  - `test_calculada_que_deja_de_calcularse_vuelve_a_pendiente`: con `pruebas_division`, DIV-A = 6 y DIV-B = 2 (DIV = 3, `cargada`); corregir DIV-B a 0 → DIV pierde su `Resultado`, vuelve a `pendiente` y el servicio devuelve `[(DIV, "división por cero")]`.
  - `test_recalcular_resultados_requiere_sesion_activa`: con `AnonymousUser` → `RecalculoError` con «Se requiere una sesión activa.».
- [X] T024 [P] [US3] Agregar en `estudios/tests/test_concurrencia_mediciones.py`: `test_cargas_concurrentes_calculan_una_vez`: dos hilos cargan a la vez CA = 80 y DUREZA-T = 15 en `estudio_de("CA", "DUREZA-T", "MG")`; al final hay un solo `Resultado` de MG, con `Decimal("24.3")`, y MG está `cargada`.

### Implementation for User Story 3

- [X] T025 [US3] En `estudios/calculo.py`, `recalcular`: si una afectada que tenía `Resultado` ya no se puede calcular (por referencias o por `CalculoImposible`), borrar su `Resultado`; si es calculada vuelve a `pendiente`, si es medida queda `cargada`. Si se calcula y estaba `completada`, pasa a `cargada` (research R3, paso 4; FR-009) (depende de T019).
- [X] T026 [US3] Agregar en `estudios/servicios.py` `class RecalculoError(Exception)` y `recalcular_resultados(estudio_pk, asignacion_pks, usuario)` (research R5): sesión activa (`RecalculoError("Se requiere una sesión activa.")`); `transaction.atomic()`; `Estudio.objects.select_for_update().filter(pk=estudio_pk).first()` (None → «El estudio no está disponible.»); `if not estudio.admite_correcciones: raise RecalculoError("El estudio ya tiene el informe emitido: sus mediciones y resultados no se pueden cambiar.")`; asignaciones del estudio con esos pk; devolver `calculo.recalcular(estudio, asignaciones)`. Docstring: US 6.3 lo llama en la misma transacción en que actualiza la medición (depende de T025).
- [X] T027 [US3] Ejecutar `docker compose exec web pytest pruebas estudios` y dejar en verde T023–T024 junto con US1 y US2 (depende de T025–T026).

**Checkpoint**: US 6.2 completa; el recálculo queda listo para US 6.3.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T028 [P] Agregar en `estudios/tests/test_calculo.py` `test_comando_calcular_resultados` (escribir primero, debe fallar): crear `Medicion` sin `Resultado` directamente en la base (como quedaron las de US 6.1), correr `call_command("calcular_resultados", stdout=salida)` → resultados creados y salida «Resultados calculados: N. Sin calcular: 0.»; segunda corrida → «Resultados calculados: 0. Sin calcular: 0.» (FR-011).
- [X] T029 Crear `estudios/management/commands/calcular_resultados.py` (research R7): por cada estudio con mediciones sin resultado, en una transacción, bloquear el estudio y llamar a `calculo.recalcular` con esas asignaciones; imprimir «Resultados calculados: N. Sin calcular: M.» y dejar en verde T028 (depende de T028, T027).
- [X] T030 [P] Ejecutar `docker compose exec web ruff check .`, `docker compose exec web ruff format --check .` y `docker compose exec web python manage.py makemigrations --check --dry-run`, y corregir lo que aparezca.
- [X] T031 Ejecutar la suite completa `docker compose exec web pytest` y confirmar todo en verde.
- [X] T032 Aplicar la migración y el comando en la base de desarrollo (`migrate` y `calcular_resultados`) y recorrer los pasos 1 a 5 de `specs/016-calcular-resultado/quickstart.md`.
- [X] T033 [P] En `CLAUDE.md`: sección «Cálculo de resultados (US 6.2)» con lo no obvio: el evaluador de `pruebas/formulas.py` es la única forma de evaluar fórmulas (nunca `eval`, `ast` ni `float`) y `Prueba.clean()` lo usa para validarlas; `Resultado` es uno a uno con `PruebaEstudio` (`PROTECT`) y guarda unidad y fórmula usadas; `calculo.recalcular` exige el estudio bloqueado por el llamador y solo toca las afectadas, en orden de dependencia; el motivo sin resultado no se guarda (`motivo_sin_resultado`); un recálculo quita la validación (excepción al principio IV justificada en el plan) y `Estudio.admite_correcciones` bloquea todo con informe emitido; US 6.3 debe actualizar la `Medicion` y llamar a `recalcular_resultados` en la misma transacción; el comando `calcular_resultados` completa resultados faltantes. Reescribir la nota **Epic 6** del catálogo («convertir los límites a número y evaluar las fórmulas»): las fórmulas ya se evalúan; los límites siguen como texto hasta US 6.4. Actualizar la nota **Epic 6 (resultados)** de «Pruebas de un estudio» si hace falta.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: `T001`.
- **Foundational (Phase 2)**: depende de la fase 1. `T002`, `T003`, `T004`, `T007` y `T009` en paralelo; `T004` → `T005`; `T006` → `T008`; `T010` al final. Bloquea las historias.
- **US1 (Phase 3)**: depende de la fase 2. Es el MVP.
- **US2 (Phase 4)**: depende de US1 (extiende `recalcular`, la vista y el template).
- **US3 (Phase 5)**: depende de US2 (usa el grafo de dependientes de `recalcular`).
- **Polish (Phase 6)**: depende de las tres historias.

### Dentro de cada historia

- Tests primero y fallando; luego `calculo.py` → servicio → vista → template.
- `estudios/calculo.py`, `servicios.py`, `views.py`, `detalle.html`, `test_calculo.py` y `test_cargar_mediciones.py` se tocan en varias fases: las tareas que comparten archivo van en secuencia.

### Grafo

```text
T001 → T002, T003, T004, T007, T009 ─┐
       T004 → T005                   ├─→ T010
       T006 → T008 ──────────────────┘     │
          ┌────────────────────────────────┘
          ▼
US1: T011, T012 → T013 → T014 → T015 → T016
US2: T017, T018 → T019 → T020 → T021 → T022
US3: T023, T024 → T025 → T026 → T027
Polish: T028 → T029; T030, T031, T032, T033
```

---

## Parallel Example: Foundational

```bash
Task T002: "Tests de fórmulas en pruebas/tests/test_formulas.py"
Task T003: "Tests de Resultado en estudios/tests/test_modelos.py"
Task T004: "Evaluador en pruebas/formulas.py"
Task T007: "Filtro unidad en config/ui.py y templates de US 6.1"
Task T009: "Fixtures en estudios/tests/conftest.py"
```

## Parallel Example: User Story 2

```bash
Task T017: "Cálculo de calculadas y motivos en estudios/tests/test_calculo.py"
Task T018: "Advertencias de la carga en estudios/tests/test_cargar_mediciones.py"
```

## Parallel Example: User Story 3

```bash
Task T023: "Recálculo en estudios/tests/test_calculo.py"
Task T024: "Concurrencia en estudios/tests/test_concurrencia_mediciones.py"
```

---

## Implementation Strategy

### En dos tandas (según `docs/guias/guia-sdd-paso-a-paso.md`)

1. **Tanda 1 (Fases 1 y 2 — `T001` a `T010`)**: aprobación, evaluador de fórmulas con sus casos
   conocidos, validación en el catálogo y modelo `Resultado`; suite en verde. Frenar y revisar:
   es la parte de mayor riesgo (cálculo).
2. **Tanda 2 (Fases 3 a 6 — `T011` a `T033`)**: US1 (resultado al cargar, MVP), US2 (calculadas,
   motivos y advertencias) y US3 (recálculo para US 6.3), cada una con sus tests escritos primero;
   cerrar con el comando para mediciones previas, `ruff`, suite completa, recorrido manual y nota
   en `CLAUDE.md`.
