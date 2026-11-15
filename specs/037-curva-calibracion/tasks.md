---

description: "Lista de tareas de la US 6.6 (SCRUM-38) – Curva de calibración para pruebas por absorbancia"
---

# Tasks: Curva de calibración para pruebas por absorbancia

**Input**: `specs/037-curva-calibracion/` (`plan.md`, `spec.md`, `research.md`, `data-model.md`,
`contracts/curvas-ui.md`, `quickstart.md`)

**Prerequisites**: `main` con la gestión del catálogo (SCRUM-73: `pruebas/gestion.py`
`gestionar_prueba`/`autorizar`, `pruebas/confirmaciones.py`, `pruebas/views.py`, `pruebas/urls.py`
namespace `catalogo`, `templates/pruebas/ficha.html`), el cálculo de resultados (US 6.2:
`estudios/calculo.py` `calcular`/`recalcular`/`motivo_sin_resultado`/`descartar`), la corrección y el
borrado (US 6.3/6.5: `servicios.corregir_mediciones`), la validación (US 6.4:
`servicios.validar_resultados`, `views.evaluar_asignaciones`), `estudios/mediciones.py:leer_valor`,
`usuarios.permisos_administracion.administracion_requerida`, Chart.js en
`static/vendor/chart.umd.min.js` y las fixtures de `pruebas/tests/conftest.py`
(`administrador_catalogo`, `cliente_catalogo`) y `estudios/tests/conftest.py` (`catalogo`,
`estudio_de`, `bioquimico`, `cliente_bioquimico`, `empleado`, `cliente_http`).

**Tests**: SÍ (constitution, principio III). Siguen el «Mapa de tests» de `plan.md` y se escriben
**antes** de la implementación de cada historia (deben fallar primero). Los valores esperados de la
recta y de la conversión son los del caso de referencia de `research.md` R2.

**Organization**: por historia de la spec, en orden de prioridad: US1 (P1, tipo «Curva»), US2 (P1,
carga manual), US4 (P1, cálculo con la curva), US3 (P2, importar archivo), US5 (P2, corrección con
la misma curva), US6 (P2, consulta y borrado) y US7 (P2, permisos).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: se puede ejecutar en paralelo (archivos distintos, sin dependencias pendientes)
- **[Story]**: user story a la que pertenece (`[US1]` a `[US7]`)
- Rutas relativas a la raíz del repo

## Convenciones para todas las tareas

- Textos y mensajes en **español**, copiados **literalmente** de `contracts/curvas-ui.md`.
- Todo número en `Decimal`; nunca `float` (salvo el que entrega openpyxl, convertido al leer, R8).
- Las reglas de curvas viven en `pruebas/curvas.py` (`ajustar`, `curva_para`, `fuera_de_rango`,
  `pendientes_de_curva`, `guardar_curva`, `borrar_curva`); el cálculo de resultados sigue siendo
  solo `estudios/calculo.py`. Las vistas arman formularios, resúmenes y mensajes; los servicios
  revalidan permiso y estado siempre.
- Orden de bloqueos (R5): estudios (por pk) → `pg_advisory_xact_lock(6_600_001, prueba_id)` →
  `Prueba`/curva. Las cargas toman el lock compartido (`pg_advisory_xact_lock_shared`).
- Componentes de `templates/ui/` (`encabezado`, `campo`, `ayuda`, `estado`, `acciones_confirmacion`,
  `mensajes`); ayudas con `help_text` en los formularios, nunca en los modelos (US 9.1).
- Comandos dentro de Docker: `docker compose exec web pytest …`, `docker compose exec web ruff
  check .`, `docker compose exec web ruff format --check .`.

---

## Phase 1: Setup

- [ ] T001 **Gate de la constitution (principio I)**: confirmar que el equipo aprobó
  `specs/037-curva-calibracion/spec.md` y la dependencia `openpyxl` (plan, Complexity Tracking);
  actualizar el `**Status**` de la spec a «Aprobada (fecha)»; confirmar que `pytest` está en verde en
  la rama.
- [X] T002 Agregar `openpyxl==3.1.5` y `et-xmlfile==2.0.0` a `requirements.txt` (research R9);
  `docker compose build web` y verificar `docker compose exec web python -c "import openpyxl"`.
- [X] T003 [P] En `.github/workflows/ci.yml` (paso de `node --test`, línea ~93) sumar
  `pruebas/tests/js` al comando: `node --test usuarios/tests/js config/tests/js estudios/tests/js
  pruebas/tests/js`. Crear `pruebas/tests/js/` (vacío por ahora; T020 agrega el test).
- [X] T004 [P] Crear `pruebas/urls_curvas.py` (`app_name = "curvas"`, sin rutas por ahora) e
  incluirlo en `config/urls.py` con `path("pruebas/", include("pruebas.urls_curvas"))`, después de
  `administracion/pruebas/`.

---

## Phase 2: Foundational (bloquea todas las historias)

- [X] T005 Modelos en `pruebas/models.py` (data-model.md):
  - `TipoCalculo.CURVA = "CURVA", "Curva de calibración"`.
  - Constraint `prueba_formula_segun_tipo`: «`(tipo ∈ {DIRECTO, CURVA} y formula = "")` o
    `(tipo = FORMULA y formula ≠ "")`».
  - `CurvaCalibracion`: `prueba` FK `Prueba` `CASCADE` `related_name="curvas"`;
    `fecha_preparacion` (DateField); `observacion` (TextField, `blank`, default ""); `archivo_origen`
    (CharField 255, `blank`, default ""); `pendiente` y `ordenada` `DecimalField(max_digits=24,
    decimal_places=12)`; `r2` `DecimalField(max_digits=11, decimal_places=10)`;
    `concentracion_min`/`concentracion_max`/`absorbancia_min`/`absorbancia_max`
    `DecimalField(max_digits=18, decimal_places=6)`; `vigente` (bool, default False); `usada` (bool,
    default False); `cargada_por` FK usuario `PROTECT` `related_name="+"`; `fecha_carga`
    (DateTimeField); `clave` (UUIDField, `unique`). `Meta.ordering = ("-fecha_carga", "-pk")`;
    constraints: `UniqueConstraint(fields=("prueba",), condition=Q(vigente=True),
    name="curva_vigente_unica")`, `CheckConstraint(~Q(pendiente=0), name="curva_pendiente_no_cero")`,
    `CheckConstraint(Q(r2__gte=0) & Q(r2__lte=1), name="curva_r2_entre_0_y_1")`. Propiedades
    `r2_bajo` (usa `curvas.R2_MINIMO`) y `concentracion(absorbancia)`.
  - `PuntoCurva`: `curva` FK `CASCADE` `related_name="puntos"`; `orden` (PositiveSmallIntegerField ≥
    1); `concentracion`/`absorbancia` `DecimalField(max_digits=18, decimal_places=6)`;
    `UniqueConstraint(curva, orden)`, `CheckConstraint` ambos ≥ 0; `ordering = ("orden",)`.
  - Propiedad `Prueba.curva_vigente` (`self.curvas.filter(vigente=True).first()`).
  - Migración `pruebas/migrations/0004_curvas_calibracion.py` (`makemigrations pruebas`).
- [X] T006 En `estudios/models.py`, `Resultado.curva = ForeignKey("pruebas.CurvaCalibracion",
  on_delete=PROTECT, null=True, blank=True, editable=False, related_name="resultados")`; migración
  `estudios/migrations/0012_resultado_curva.py` (depende de `pruebas.0004`).
- [X] T007 Crear `pruebas/curvas.py` con la constante `R2_MINIMO = Decimal("0.995")`, la excepción
  `CurvaInvalida(errores)` (dict campo/fila → mensaje), `NoEsPruebaPorCurva`, `CurvaUsada`, y la
  función `bloquear(prueba_id, *, compartido=False)` que ejecuta
  `pg_advisory_xact_lock[_shared](6_600_001, %s)` (research R5). Sin más lógica todavía.
- [X] T008 Fixtures en `estudios/tests/conftest.py` (así las ven `estudios` y `pruebas`):
  `prueba_curva` (crea `NO2-C` «Nitritos (curva)», `tipo_calculo=CURVA`, `unidad="mg/l"`,
  `unidad_medicion="Abs"`) y `curva_de` (fábrica `curva_de(prueba, puntos=None, *, vigente=True,
  usuario=None, fecha=None)` que crea la `CurvaCalibracion` y sus `PuntoCurva` directamente en la
  base, sin `ajustar`, pasando a histórica la vigente anterior). Por defecto `puntos = [("0",
  "0.001"), ("0.2", "0.101"), ("0.4", "0.201")]` (concentración, absorbancia), con pendiente 0,5,
  ordenada 0,001 y R² 1 escritos a mano; los rangos salen de los puntos: concentración 0–0,4 y
  absorbancia 0,001–0,201. Con otros `puntos`, recibe también `pendiente`, `ordenada` y `r2`.
  Comprobar que `pytest` sigue en verde tras T005–T008.

**Checkpoint**: modelos, migraciones y fixtures listos; la suite existente pasa.

---

## Phase 3: User Story 1 – Definir una prueba por curva de calibración (Priority: P1) 🎯 MVP

**Goal**: el catálogo ofrece «Curva de calibración» y la ficha indica si hay curva vigente.

**Independent Test**: crear `NO2-C` con tipo Curva y unidad mg/l desde la app; la ficha la muestra
sin fórmula, con «Abs» y «Sin curva vigente».

### Tests for User Story 1 ⚠️

- [X] T009 [P] [US1] En `pruebas/tests/test_curvas_catalogo.py`: `test_prueba_por_curva_opcion`
  (el formulario ofrece las tres opciones, US1 Esc. 1); `test_prueba_por_curva_reglas` (unidad del
  resultado obligatoria, fórmula rechazada, `unidad_medicion` vacía → «Abs», `es_calculada=False`,
  Esc. 2; también `Prueba.full_clean()` y la constraint de base); `test_prueba_por_curva_ficha`
  («Sin curva vigente» y «Nueva curva» en la ficha, Esc. 3); `test_en_uso_no_pasa_a_curva` (prueba
  en un estudio → rechazo con `gestion.MENSAJE_EN_USO`, Esc. 4); `test_cambio_tipo_con_curvas`
  (prueba sin uso con una curva → «Tiene curvas de calibración cargadas: borralas antes de cambiar
  el tipo de cálculo.», R12); `test_eliminar_borra_curvas` (eliminar sin uso borra sus curvas y
  puntos); `test_importacion_acepta_curva` (`importar_catalogo_pruebas` con un CSV que trae `CURVA`
  la crea sin curva vigente).

### Implementation for User Story 1

- [X] T010 [US1] `Prueba.clean()` en `pruebas/models.py`: con `CURVA`, fórmula prohibida («Una
  prueba por curva de calibración no lleva fórmula.»), `unidad` obligatoria («Indicá la unidad del
  resultado (la de la concentración).») y `es_calculada` debe ser `False`.
- [X] T011 [US1] `pruebas/formularios.py` (`PruebaForm`): incluir la opción nueva, `help_text` del
  tipo («Curva de calibración: la medición es la absorbancia y el resultado se calcula con la curva
  vigente.») y, en `clean()`, `unidad_medicion = "Abs"` si el tipo es Curva y viene vacía.
- [X] T012 [US1] `pruebas/gestion.py`: en `_editar`, si la prueba tiene curvas y el tipo deja de
  ser `CURVA`, `DatosInvalidos({"tipo_calculo": "Tiene curvas de calibración cargadas: borralas
  antes de cambiar el tipo de cálculo."})` (R12). `_eliminar` funciona con `CASCADE`.
- [X] T013 [US1] `pruebas/templates/pruebas/ficha.html` y `views.ficha`: sección «Curvas de
  calibración» solo para pruebas `CURVA`: vigente (fecha de preparación, R², cantidad de puntos) o
  «Sin curva vigente»; botón «Nueva curva» (`catalogo:nueva_curva`, enlace inactivo hasta T024) y
  «Ver curvas» (`curvas:listar`, hasta T044). Hace pasar T009.

**Checkpoint**: US1 completa.

---

## Phase 4: User Story 2 – Cargar una curva a mano (Priority: P1)

**Goal**: el administrador carga puntos, ve la recta y el gráfico, confirma y la curva queda vigente.

**Independent Test**: los 5 puntos de R2 → pendiente 0,499000000000, ordenada 0,001200000000, R²
0,9996025692; confirmar → vigente; la anterior → histórica.

### Tests for User Story 2 ⚠️

- [X] T014 [P] [US2] En `pruebas/tests/test_curvas_calculo.py`: `test_ajustar_caso_referencia`
  (valores exactos de R2, más `concentracion_min/max` 0 y 0,4 y `absorbancia_min/max` 0 y 0,199);
  `test_ajustar_replicas` (concentraciones repetidas entran todas; blanco 0 no fuerza el origen);
  `test_ajustar_rechaza` (parametrizado: 2 puntos, concentraciones iguales, absorbancias iguales,
  pendiente que redondea a 0, valor negativo → `CurvaInvalida` con el mensaje del contrato);
  `test_r2_bajo` (R² 0,9949… → `r2_bajo`; exactamente 0,995 → sin aviso); `test_concentracion`
  (pendiente 0,5, ordenada 0,001, absorbancia 0,126 → 0,25).
- [X] T015 [P] [US2] En `pruebas/tests/test_curvas_servicio.py`: `test_guardar_curva_crea`
  (guarda puntos en orden, pendiente/ordenada/R²/rangos, `cargada_por`, `fecha_carga`, observación,
  `archivo_origen` vacío, `vigente=True`, FR-013); `test_guardar_curva_reemplaza_vigente` (la
  anterior queda `vigente=False`, FR-014); `test_guardar_curva_prueba_no_curva` (prueba Directa →
  `NoEsPruebaPorCurva`); `test_guardar_curva_fecha_futura` (rechazada); `test_clave_repetida` (dos
  llamadas con la misma `clave` → una sola curva, devuelve la misma).
- [X] T016 [P] [US2] En `pruebas/tests/test_curvas_vistas.py`: `test_carga_manual_formulario`
  (fecha, observación, 3 filas vacías, «Agregar fila», «Calcular recta», sin «Guardar» al inicio;
  US2 Esc. 1); `test_carga_manual_filas` (`agregar_fila` suma una fila y `quitar_<n>` la quita
  conservando lo escrito); `test_carga_manual_calcular` (muestra pendiente, ordenada, R², el
  `json_script` del gráfico y «Guardar», Esc. 2); `test_carga_manual_errores` (menos de 3 puntos,
  fila sin absorbancia, negativa, fecha de mañana → errores junto al campo/fila, Esc. 3–5 y 8);
  `test_carga_manual_r2_bajo` (aviso en el cálculo y en el resumen, Esc. 9);
  `test_carga_manual_resumen` (`guardar` → 302 a `catalogo:confirmar_curva` con el resumen del
  contrato, Esc. 6); `test_carga_manual_confirmar` (POST confirmar → curva vigente, mensaje «Curva
  guardada: es la vigente de <prueba>.», redirige a la ficha, Esc. 7); `test_carga_manual_cancelar`
  (vuelve al formulario con los puntos, no guarda nada); `test_borrador_invalido` (token alterado o
  vencido → mensaje del contrato, nada guardado).
- [X] T017 [P] [US2] En `pruebas/tests/test_curvas_concurrencia.py` (`transaction=True`):
  `test_concurrencia_guardar` (dos `guardar_curva` simultáneos con claves distintas → dos curvas,
  una sola vigente, la última en confirmar).

### Implementation for User Story 2

- [X] T018 [US2] `pruebas/curvas.py:ajustar(puntos)` (research R2): `localcontext(prec=40)`,
  fórmulas cerradas, pendiente y ordenada `quantize(Decimal("1E-12"), ROUND_HALF_UP)`, R² a
  `1E-10`; devuelve un `Ajuste` (dataclass: pendiente, ordenada, r2, rangos, `r2_bajo`) o lanza
  `CurvaInvalida` con los mensajes del contrato. Hace pasar T014.
- [X] T019 [US2] `pruebas/curvas.py:guardar_curva(usuario, prueba_id, datos, clave,
  calcular_pendientes=False)` (sin pendientes todavía: T031): `transaction.atomic()` → `gestion.autorizar`
  → `bloquear(prueba_id)` → `Prueba` `select_for_update` (tipo `CURVA` o `NoEsPruebaPorCurva`) → si
  existe una curva con `clave`, devolverla → validar fecha ≤ hoy (`timezone.localdate()`) →
  `ajustar` → vigente anterior `vigente=False` → crear curva + `PuntoCurva` (orden 1..n). Devuelve
  un resultado con la curva y `anterior`. Hace pasar T015 y T017.
- [X] T020 [P] [US2] `pruebas/static/pruebas/curva.js` (funciones puras exportables `datasets(datos)`
  y `extremos(datos)` + inicialización que lee el `json_script` `datos-curva` y dibuja con Chart.js
  un scatter de puntos y la recta entre los extremos calculados por el servidor) y
  `pruebas/tests/js/curva.test.js` (`node --test`, DOM simulado como `estudios/tests/js`).
- [X] T021 [US2] `pruebas/formularios_curvas.py`: `CurvaForm` (fecha con `help_text` «Día en que se
  prepararon los estándares.», observación), `PuntoForm` (concentración y absorbancia leídas con
  `leer_valor`, ≥ 0, mensajes del contrato) y `PuntoFormSet` (`formset_factory`, `extra=0`,
  mínimo 3 filas visibles, máximo 50, `clean` que arma la lista de puntos y llama a `ajustar`).
- [X] T022 [US2] `pruebas/confirmaciones.py`: operación `curva` (borrador con `prueba_id`, fecha,
  observación, puntos como textos, `archivo_origen`, `clave` UUID nueva), reutilizando `cargar`,
  `crear_contexto`/`leer_contexto`, `digest` y `pendientes`.
- [X] T023 [US2] `pruebas/views_curvas.py` y rutas en `pruebas/urls.py`: `nueva_curva`
  (`<int:pk>/curvas/nueva/`, GET/POST con `accion` `agregar_fila`, `quitar_<n>`, `calcular`,
  `guardar`; prueba no `CURVA` → 302 a la ficha con «Esta prueba no se calcula con curva de
  calibración.») y `confirmar_curva` (`<int:pk>/curvas/confirmar/`, GET resumen / POST confirmar o
  cancelar), ambas con `@administracion_requerida`.
- [X] T024 [US2] Templates `pruebas/templates/pruebas/curvas/formulario.html` (tabla de puntos con
  unidades en el encabezado, botones, bloque de resultados con aviso de R², `<canvas>` +
  `json_script` + `chart.umd.min.js` y `curva.js` con `defer`) y `confirmar.html` (resumen del
  contrato con `ui/acciones_confirmacion.html`). Activar «Nueva curva» en la ficha. Hace pasar T016.

**Checkpoint**: US1 + US2: se cargan curvas a mano y quedan vigentes.

---

## Phase 5: User Story 4 – Calcular el resultado con la curva vigente (Priority: P1)

**Goal**: la absorbancia cargada se convierte con la curva vigente y el resultado guarda la curva.

**Independent Test**: con `curva_de(prueba_curva)` (pendiente 0,5, ordenada 0,001), cargar 0,126 →
resultado 0,25 mg/l con «Curva del <fecha> · R² …» en el detalle.

### Tests for User Story 4 ⚠️

- [X] T025 [P] [US4] En `estudios/tests/test_calculo_curva.py`: `test_calculo_con_curva`
  (`cargar_mediciones` con 0,126 → `Resultado.valor` 0,25, `unidad` mg/l, `formula` vacía,
  `curva` = la vigente, `curva.usada=True`; con la curva de R2 → 0,2501002004, US4 Esc. 1);
  `test_detalle_muestra_curva` (columna Resultado con fecha de preparación, R² y enlace a
  `curvas:detalle`, sin N+1 con `django_assert_max_num_queries`, Esc. 2); `test_sin_curva`
  (medición guardada, sin resultado, «Falta curva de calibración.» en el detalle, no aparece en
  `estudios:validar_resultados` y `validar_resultados` la omite, Esc. 3–4); `test_fuera_de_rango`
  (parametrizado con la curva por defecto de `curva_de`: absorbancia 0,0005 y 0,25 → aviso «Fuera
  del rango de la curva (0–0,4 mg/l)»; 0,001 y 0,201 (bordes) → sin aviso; en detalle y validación;
  validar igual funciona, Esc. 5); `test_concentracion_negativa` (absorbancia 0 → concentración
  −0,002, con aviso de fuera de rango y, con límite de detección en la prueba, «< LD» en el
  informe como cualquier resultado; edge case); `test_prueba_desactivada_sigue_calculando`
  (desactivar `NO2-C` con un estudio que la tiene → la carga sigue calculando con la vigente y sus
  curvas siguen en `curvas:listar`; edge case);
  `test_formula_usa_concentracion` (prueba Fórmula `{NO2-C}*2` → 0,5, Esc. 6);
  `test_curva_nueva_no_recalcula` (resultado con curva A, validación e informe emitido; cargar la
  curva B no cambia `Resultado`, `Validacion` ni `Informe.contenido`, Esc. 7 y SC-006).
- [X] T026 [P] [US4] En `pruebas/tests/test_curvas_servicio.py`: `test_pendientes_resumen`
  (2 mediciones sin resultado en 2 estudios → «2 mediciones en 2 estudios esperan curva» y la
  casilla, Esc. 8); `test_pendientes_calcular` (con la casilla: resultados con la curva nueva,
  estudio «En proceso», mensaje con la cantidad, Esc. 9); `test_pendientes_sin_casilla` (siguen sin
  resultado, ahora con «Se cargó antes de la curva vigente.»); `test_pendientes_excluye_informados`
  (estudios Finalizados o con informe no se cuentan ni se tocan, Esc. 10).
- [X] T027a [P] [US4] En `estudios/tests/test_calculo_curva.py`: `test_calcular_con_curva_motivo`
  (medición cargada sin curva, después curva vigente → el detalle muestra «Se cargó antes de la
  curva vigente.» y el botón «Calcular con la curva vigente»; sin vigente sigue «Falta curva de
  calibración.» y sin botón, US4 Esc. 11); `test_calcular_con_curva_confirmar` (GET lista los
  códigos; POST → resultados con la vigente de cada prueba y sus dependientes, mensaje «Se
  calcularon N resultados con la curva vigente.», Esc. 12); `test_calcular_con_curva_reenvio` (segundo
  POST → «No quedaban mediciones para calcular: ya se calcularon.», sin cambios);
  `test_calcular_con_curva_estudio_cerrado` (estudio que no admite mediciones → 302 al detalle con
  el motivo y el servicio lo rechaza); `test_calcular_con_curva_sin_sesion` (login).
- [X] T027 [P] [US4] En `pruebas/tests/test_curvas_concurrencia.py` (`transaction=True`):
  `test_concurrencia_carga` (una carga de medición con el estudio bloqueado mientras otro hilo
  confirma una curva con «Calcularlas» → sin deadlock; la medición se calcula una sola vez y con una
  sola curva).

### Implementation for User Story 4

- [X] T028 [US4] `pruebas/curvas.py:curva_para(asignacion, *, bloquear=False)`: si
  `asignacion.resultado.curva_id` existe → esa; si no, con `bloquear=True` toma el lock compartido y
  devuelve `asignacion.prueba.curva_vigente` (o `None`). Y `fuera_de_rango(resultado)` (absorbancia
  de la medición fuera de `[absorbancia_min, absorbancia_max]`, bordes inclusivos).
- [X] T029 [US4] `estudios/calculo.py`: `calcular(asignacion, todas, valores, curva=None)` con la
  rama `TipoCalculo.CURVA` (si `curva` es `None` usa `curvas.curva_para(asignacion)`; sin curva →
  `FaltanDatos("Falta curva de calibración.")`; valor = `curva.concentracion(x)`); en `recalcular`,
  para pruebas `CURVA` obtener la curva con `curva_para(..., bloquear=True)`, pasarla a `calcular`,
  guardar `curva` en los `defaults` de `Resultado` (y `None` para las demás) y marcar
  `CurvaCalibracion.objects.filter(pk=…, usada=False).update(usada=True)`. `por_codigo` suma
  `resultado__curva` al `select_related`. Hace pasar la parte de cálculo de T025.
- [X] T030 [US4] `estudios/views.py` (detalle y validar) y templates
  `estudios/templates/estudios/detalle.html` y `validar_resultados.html`: debajo del resultado,
  «Curva del <dd/mm/aaaa> · R² <4 decimales>» enlazado a `curvas:detalle` y, si
  `curvas.fuera_de_rango`, el aviso del contrato con `ui/estado.html`; `select_related` de la
  curva en las consultas de asignaciones. Hace pasar T025.
- [X] T031 [US4] `pruebas/curvas.py:pendientes_de_curva(*, prueba=None, estudio=None)`
  (asignaciones de pruebas `CURVA` con medición, sin resultado, en estudios con `admite_mediciones`,
  filtradas por prueba o por estudio; con `estudio`, solo las de pruebas con vigente) y la opción en `guardar_curva`
  (research R5/R10): si `calcular_pendientes`, antes del lock exclusivo bloquear los estudios
  candidatos ordenados por pk; tras crear la curva, por estudio volver a consultar sus pendientes y
  llamar a `calculo.recalcular(estudio, pendientes)`; devolver la cantidad calculada. En
  `confirmar_curva` y `confirmar.html`: «N mediciones en M estudios esperan curva» + casilla
  «Calcularlas con esta curva» (desmarcada) y mensaje « Se calcularon N resultados.». Hace pasar
  T026 y T027.
- [X] T031a [US4] `pruebas/curvas.py:motivo_curva(asignacion)` («Se cargó antes de la curva
  vigente.» si la prueba es `CURVA`, tiene medición, no tiene resultado y hay vigente; si no,
  `None`), consultado primero por `estudios/calculo.py:motivo_sin_resultado` (research R14).
- [X] T031b [US4] `estudios/servicios.py:calcular_con_curva(estudio_pk, usuario)` (R14: sesión
  activa → estudio `select_for_update` → `admite_mediciones` o `CalcularConCurvaError` →
  `pendientes_de_curva(estudio=…)` bajo el bloqueo → `calculo.recalcular` → cantidad); vista
  `calcular_con_curva` en `estudios/views.py` (llama a `servicios.calcular_con_curva`), ruta
  `<int:pk>/mediciones/calcular-con-curva/` en `estudios/urls.py`, template
  `estudios/templates/estudios/calcular_con_curva_confirmar.html` (`ui/acciones_confirmacion`,
  `data-enviado`) y el botón en `detalle.html` solo si hay pendientes y el estudio admite
  mediciones. Hace pasar T027a.

**Checkpoint**: MVP completo (US1 + US2 + US4): curva cargada a mano y resultados calculados con ella.

---

## Phase 6: User Story 3 – Importar los puntos desde un archivo (Priority: P2)

**Goal**: los puntos se leen de `.csv`/`.xlsx` y se cargan en la misma tabla.

**Independent Test**: importar la plantilla con una fila de título → 5 puntos editables; guardar →
`archivo_origen` registrado.

### Tests for User Story 3 ⚠️

- [X] T032 [P] [US3] En `pruebas/tests/test_curvas_importacion.py` (archivos armados en el test;
  `.xlsx` con `openpyxl.Workbook`): `test_leer_csv` (parametrizado: separador `;`, `,` y
  tabulador; UTF-8 con y sin BOM; Latin-1; coma y punto decimal); `test_leer_xlsx` (primera hoja,
  números y textos, `float` → `Decimal` a 6 decimales); `test_leer_ignora` (títulos, filas vacías,
  celdas con texto); `test_detectar_columnas` (encabezados «Concentración (mg/l)»/«ABS» sin tildes ni
  mayúsculas; sin encabezados o dos candidatas → pide elegir); `test_elegir_columnas` (columnas
  elegidas → puntos; misma columna dos veces → «Elegí dos columnas distintas.»);
  `test_archivo_invalido` (parametrizado: `.ods`, > 1 MB, binario ilegible, vacío, «La fila 4 no
  tiene absorbancia.», «La fila 3 no tiene concentración.», valor inválido, 2 puntos → mensaje del
  contrato y ningún punto); `test_limites` (más de 1000 filas o 50 puntos).
- [X] T033 [P] [US3] En `pruebas/tests/test_curvas_vistas.py`: `test_importar_carga_tabla`
  (`accion=importar` → puntos en el formset, editables, mensaje «Se leyeron N puntos de <archivo>.
  Revisalos antes de calcular.», US3 Esc. 2); `test_importar_error_no_cambia_tabla` (con puntos ya
  escritos, un archivo inválido deja la tabla igual, Esc. 6–8); `test_importar_elegir_columnas`
  (pantalla con vista previa de 5 filas y los dos selectores, Esc. 5); `test_plantilla`
  (`catalogo:plantilla_curva` → CSV UTF-8 con BOM, `;`, coma decimal, encabezado
  `Concentración;Absorbancia` y los 5 puntos; al importarla da los mismos puntos, Esc. 1);
  `test_archivo_origen` (importar, editar un punto, guardar → `archivo_origen` = nombre del archivo
  y puntos editados; el resumen muestra «Archivo: <nombre>», Esc. 9).

### Implementation for User Story 3

- [X] T034 [US3] `pruebas/importacion_curvas.py` (research R8): `ArchivoInvalido(motivo)`,
  `leer_archivo(archivo)` (extensión, tamaño ≤ 1 MB, CSV con `csv.Sniffer` entre `;`, `,`, `\t` y
  codificación UTF-8-sig → Latin-1; XLSX con `load_workbook(read_only=True, data_only=True)`, primera
  hoja, `Decimal(repr(valor))` a 6 decimales; máx. 1000 filas; cualquier excepción → «No se pudo
  leer el archivo.»), `detectar_columnas(tabla)`, `extraer_puntos(tabla, columnas)` (con
  `leer_valor`, numeración de fila del archivo, máx. 50 puntos, mín. 3) y `plantilla()`. Hace pasar
  T032.
- [X] T035 [US3] `pruebas/formularios_curvas.py`: campo `archivo` (`FileField`, `help_text` «CSV o
  Excel (.xlsx) con una columna de concentración y otra de absorbancia.») y `ElegirColumnasForm`
  (dos `ChoiceField` sobre las columnas de la tabla, distintas).
- [X] T036 [US3] `pruebas/views_curvas.py`: acciones `importar` (lee, y si las columnas son dudosas
  guarda la tabla en el borrador de sesión y muestra la elección) y `elegir_columnas`; los puntos
  leídos reemplazan los del formset solo si no hubo error; `archivo_origen` viaja en el formulario
  (campo oculto firmado) y en el borrador. Vista `plantilla_curva`
  (`curvas/plantilla.csv`, `@administracion_requerida`, `require_GET`). Template
  `curvas/formulario.html`: bloque de archivo, enlace «Descargar plantilla» y pantalla de elección
  de columnas. Hace pasar T033.

**Checkpoint**: US3 completa.

---

## Phase 7: User Story 5 – Corregir una medición manteniendo la curva (Priority: P2)

**Goal**: una corrección recalcula con la curva con la que se había calculado.

**Independent Test**: resultado con la curva A, cargar la B, corregir → resultado con la A.

### Tests for User Story 5 ⚠️

- [X] T037 [P] [US5] En `estudios/tests/test_calculo_curva.py`: `test_correccion_misma_curva`
  (curva A, luego B vigente; `corregir_mediciones` a 0,150 → valor con A y `resultado.curva` = A,
  US5 Esc. 1); `test_correccion_sin_resultado_previo` (sin curva al cargar, después curva vigente,
  corregir → calcula con la vigente, Esc. 2); `test_correccion_borrada_y_recargada` (borrar la
  medición con `nuevo=None`, cargar curva B, volver a cargar → usa B, Esc. 3);
  `test_correccion_pierde_validacion` (resultado validado; corregir → validación anulada y prueba
  Cargada, Esc. 4); `test_recalculo_dependencias_misma_curva` (corregir otra prueba de la que
  depende una fórmula que usa la prueba por curva no cambia la curva usada).

### Implementation for User Story 5

- [X] T038 [US5] Verificar que T037 pasa con T029 (la corrección reutiliza `Resultado` con
  `update_or_create` y `curva_para` toma `resultado.curva`); si algún caso falla, corregirlo solo en
  `estudios/calculo.py` o `pruebas/curvas.py`, sin tocar `servicios.corregir_mediciones`.

**Checkpoint**: US5 completa.

---

## Phase 8: User Story 6 – Consultar y borrar curvas (Priority: P2)

**Goal**: cualquier empleado ve la vigente y las históricas; el administrador borra las no usadas.

**Independent Test**: con dos curvas, un técnico ve ambas y el detalle; un administrador borra la no
usada y la otra vuelve a ser vigente; la usada no ofrece «Borrar».

### Tests for User Story 6 ⚠️

- [X] T039 [P] [US6] En `pruebas/tests/test_curvas_vistas.py`: `test_consulta_listar` (vigente
  destacada, históricas de la más nueva a la más vieja con fecha, R², cargada por y cuándo, «Usada en
  resultados», o «Sin curva vigente», US6 Esc. 1); `test_consulta_detalle` (puntos, pendiente,
  ordenada, R² con aviso si < 0,995, `json_script` del gráfico, rango, observación, archivo,
  estado, Esc. 2); `test_consulta_desde_estudio` (el enlace del detalle del estudio abre la curva
  usada aunque sea histórica, Esc. 3); `test_consulta_sin_opciones` (empleado sin permiso: sin «Nueva
  curva» ni «Borrar curva»).
- [X] T040 [P] [US6] En `pruebas/tests/test_curvas_servicio.py`: `test_borrar_curva_vigente`
  (sin usar y vigente → borrada con sus puntos; la anterior más reciente vuelve a vigente; mensaje
  del contrato, Esc. 4); `test_borrar_curva_unica` (queda «Sin curva vigente»);
  `test_borrar_curva_historica` (la vigente no cambia); `test_borrar_curva_usada` (`usada=True`,
  aunque su resultado se haya descartado → `CurvaUsada` y la vista GET redirige con «Esta curva ya
  se usó en resultados: no se puede borrar.», POST directo también rechazado, Esc. 5).
- [X] T041 [P] [US6] En `pruebas/tests/test_curvas_concurrencia.py` (`transaction=True`):
  `test_concurrencia_borrar` (un hilo calcula con la curva vigente dentro de `recalcular` mientras
  otro intenta borrarla → el borrado espera y termina rechazado por `usada`; sin `IntegrityError`).

### Implementation for User Story 6

- [X] T042 [US6] `pruebas/curvas.py:borrar_curva(usuario, curva_id)` (research R5/R6):
  `transaction.atomic()` → `gestion.autorizar` → `bloquear(prueba_id)` → curva `select_for_update`
  → `usada` → `CurvaUsada` → borrar → si era vigente, marcar vigente la más reciente que quede
  (`-fecha_carga`, `-pk`); devuelve la nueva vigente o `None`. Hace pasar T040 y T041.
- [X] T043 [US6] Vista `borrar_curva` en `pruebas/views_curvas.py` y ruta
  `curvas/<int:pk>/borrar/` en `pruebas/urls.py` (GET confirmación o 302 con el motivo; POST →
  servicio → mensaje del contrato → `curvas:listar`), `@administracion_requerida`; template
  `pruebas/templates/pruebas/curvas/borrar.html`.
- [X] T044 [US6] Vistas de consulta `listar` (`<int:pk>/curvas/`) y `detalle` (`curvas/<int:pk>/`)
  en `pruebas/views_curvas.py`, con `require_GET` y solo sesión; rutas en `pruebas/urls_curvas.py`;
  templates `pruebas/templates/pruebas/curvas/listar.html` y `detalle.html` (gráfico con `curva.js`,
  tabla de puntos como «Ver datos»; «Nueva curva»/«Borrar curva» solo si el usuario pasa
  `autorizar_administracion` y la curva no está usada).
- [X] T045 [US6] Enlazar «Ver curvas» desde la ficha de gestión (T013) y verificar el enlace del
  detalle del estudio (T030). Hace pasar T039.

**Checkpoint**: US6 completa.

---

## Phase 9: User Story 7 – Solo quien gestiona el catálogo carga curvas (Priority: P2)

**Goal**: carga, importación, plantilla, confirmación y borrado solo para Administradores.

**Independent Test**: técnico, bioquímico y superusuario fuera del grupo → 403 en todas las rutas de
carga; consulta OK; sin sesión → login.

### Tests for User Story 7 ⚠️

- [X] T046 [P] [US7] En `pruebas/tests/test_curvas_vistas.py`: `test_acceso` (parametrizado sobre
  `catalogo:nueva_curva` GET/POST con cada `accion`, `catalogo:confirmar_curva`,
  `catalogo:plantilla_curva` y `catalogo:borrar_curva`: sin sesión → login; `empleado`,
  `bioquimico` fuera del grupo y superusuario fuera del grupo → 403 sin crear ni borrar nada;
  `administrador_catalogo` → 200/302; `curvas:listar` y `curvas:detalle` → 200 para cualquier
  empleado con sesión, US7 Esc. 1–3) y `test_servicio_revalida` (`guardar_curva` y `borrar_curva`
  con un usuario sin permiso → `NoAutorizado`, sin cambios).

### Implementation for User Story 7

- [X] T047 [US7] Revisar que todas las vistas de carga de `pruebas/views_curvas.py` tengan
  `@administracion_requerida` y `require_GET`/`require_POST` según el contrato, y que los servicios
  llamen a `gestion.autorizar`. Hace pasar T046.

**Checkpoint**: todas las historias completas.

---

## Phase 10: Polish & Cross-Cutting Concerns

- [X] T048 [P] `CLAUDE.md`: sección «Curvas de calibración (US 6.6)»: modelos y vigente única;
  `curvas.ajustar` en `Decimal` (12/12/10 decimales, el resultado se calcula con lo guardado);
  `curva_para` (la del resultado o la vigente) y la rama `CURVA` de `calculo`; `usada` nunca vuelve
  a `False` y la usada no se borra; orden de bloqueos y advisory lock `6_600_001`; importación
  (`importacion_curvas`, `leer_valor`, `float` de openpyxl convertido); «Calcularlas con esta curva»;
  `servicios.calcular_con_curva` y `curvas.motivo_curva` («Se cargó antes de la curva vigente.»);
  fuera de rango al vuelo; fixtures `prueba_curva` y `curva_de`.
- [X] T049 Comprobar que los tests existentes de `pruebas` (gestión, importación, admin), de
  `estudios` (cálculo, corrección, validación, desvíos, demo) y de `informes` siguen en verde.
- [X] T050 Ejecutar `docker compose exec web ruff check .`, `docker compose exec web ruff format
  --check .` y `docker compose exec web python manage.py makemigrations --check --dry-run`.
- [X] T051 Recompilar el CSS si los templates agregaron clases de Tailwind nuevas: `docker compose
  exec -u "$(id -u):$(id -g)" web tailwindcss -i static/src/aqualab.css -o static/css/aqualab.css
  --minify` y commitear `static/css/aqualab.css` (el CI verifica que esté al día).
- [X] T052 Ejecutar `node --test usuarios/tests/js config/tests/js estudios/tests/js pruebas/tests/js`:
  todo en verde.
- [X] T053 Ejecutar la suite completa `docker compose exec web pytest`: todo en verde.
- [ ] T054 Recorrer `specs/037-curva-calibracion/quickstart.md` en el navegador (pasos 1 a 9) y
  marcar el resultado en esta lista.

---

## Dependencies & Execution Order

- **Setup (T001–T004)** → **Foundational (T005–T008)** → historias.
- **US1 (T009–T013)** agrega el tipo y la sección de la ficha que usan las demás.
- **US2 (T014–T024)** depende de US1 (prueba por curva). **US4 (T025–T031b)** solo necesita las
  fixtures `curva_de` para el cálculo (T025, T028–T030) y puede empezar después de T008 en paralelo
  con US2; T031 (pendientes) necesita `guardar_curva` (T019) y `confirmar_curva` (T023–T024); T031b necesita T031 y T031a.
- **US3 (T032–T036)** depende de la pantalla de carga (T023–T024).
- **US5 (T037–T038)** depende de T029.
- **US6 (T039–T045)**: la consulta (T044) solo necesita los modelos; el borrado (T042–T043) necesita
  T007 y `curva_para` (T028) para el test de concurrencia.
- **US7 (T046–T047)** después de que existan todas las vistas (T023, T036, T043, T044).
- **Polish (T048–T054)** al final.

## Parallel Example

```text
# Base
T003 (CI), T004 (urls_curvas)
# Tests de cada historia (archivos distintos)
T014 + T015 + T016 + T017      (US2)
T025 + T026 + T027 + T027a    (US4)
T032 + T033                    (US3)
T039 + T040 + T041             (US6)
# Implementación independiente
T020 (curva.js) en paralelo con T018–T019
T028–T030 (cálculo, US4) en paralelo con T021–T024 (pantalla, US2)
```

## Implementation Strategy

1. **MVP = US1 + US2 + US4**: tipo «Curva», carga manual y resultados calculados con la curva
   vigente y trazados (los tres P1).
2. **US3** suma la importación desde archivo; **US5** verifica la corrección con la misma curva;
   **US6** suma la consulta para todos y el borrado de curvas sin usar; **US7** cierra los permisos
   (aunque `administracion_requerida` se pone desde T023).
3. Documentación, controles del CI (ruff, migraciones, CSS, Node), suite completa y recorrido manual.
