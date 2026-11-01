---

description: "Lista de tareas de la US 6.5 – Borrar mediciones"
---

# Tasks: Borrar mediciones

**Input**: `specs/018-borrar-mediciones/` (`plan.md`, `spec.md`, `research.md`, `data-model.md`,
`contracts/borrar-mediciones-ui.md`, `quickstart.md`)

**Prerequisites**: `plan.md`, `spec.md` y la rama `017-modificar-mediciones` (US 6.3, PR #30), de
la que sale esta rama: `CorregirMedicionesForm`, `corregir_mediciones` y `ResultadoCorreccion`,
la vista `corregir_mediciones` y sus templates, `calculo.afectadas`, `recalcular_resultados` y
`calculo.descartar` (US 6.2); fixtures `estudio_de`, `catalogo`, `pruebas_division`, `empleado`,
`cliente_http`; helpers `cargar`, `asignacion_de` (`estudios/tests/utiles.py`), `corregir`
(`test_servicio_correccion.py`) y `envio` (`test_corregir_mediciones.py`).

**Tests**: SÍ (constitution, principio III). Los tests siguen el «Mapa de tests» de `plan.md` y se
escriben **antes** de la implementación de cada historia.

**Organization**: US1 (P1, borrar), US2 (P2, efectos en dependientes y en el estado del estudio) y
US3 (P3, informe emitido, atomicidad y concurrencia).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: se puede ejecutar en paralelo (archivos distintos, sin dependencias pendientes)
- **[Story]**: user story a la que pertenece la tarea
- Rutas relativas a la raíz del repo

## Convenciones para todas las tareas

- Mensajes copiados **literalmente** de `contracts/borrar-mediciones-ui.md` y, para lo que no
  cambia, de `specs/017-modificar-mediciones/contracts/corregir-mediciones-ui.md`.
- **Sin migraciones ni cambios en `estudios/calculo.py`**: el borrado se apoya en
  `recalcular_resultados` → `calculo.recalcular` → `descartar` (research R2).
- Un valor nuevo `None` en `cambios` significa borrar (research R1).
- Las reglas de concurrencia (original, «ya no tenía medición») van en el MVP (US1), como se
  aprendió en el análisis de US 6.3.
- Comandos dentro de Docker: `docker compose exec web pytest estudios`,
  `docker compose exec web ruff check .`, `docker compose exec web ruff format --check .`.

---

## Phase 1: Setup (Shared Infrastructure)

- [ ] T001 **Gate de la constitution (principio I)**: confirmar que el equipo aprobó `specs/018-borrar-mediciones/spec.md` y que SCRUM-72 entra en el sprint; actualizar su `**Status**` a «Aprobada (fecha)». Si el PR #30 ya se mergeó, rebasar la rama sobre `main`. Ejecutar `docker compose exec web pytest` y `docker compose exec web python manage.py makemigrations --check --dry-run`: suite en verde y sin cambios.

---

## Phase 2: Foundational (Blocking Prerequisites)

- [ ] T002 [P] Ampliar los helpers de test: en `estudios/tests/test_servicio_correccion.py`, `corregir(estudio, usuario, originales=None, borrar=(), **por_codigo)` agrega `{pk: (original, None)}` por cada código de `borrar`; en `estudios/tests/test_corregir_mediciones.py`, `envio(accion, estudio, borrar=(), **por_codigo)` agrega `borrar_<pk>="on"` por cada código de `borrar`. Los tests existentes de US 6.3 siguen en verde.

---

## Phase 3: User Story 1 - Borrar una medición cargada por error (Priority: P1) 🎯 MVP

**Goal**: marcar «Borrar» en la corrección, ver «se borra» en el resumen y, al confirmar, que la
medición y su resultado desaparezcan y la prueba vuelva a Pendiente.

**Independent Test**: con CL- y PH cargados, borrar CL-: queda Pendiente sin medición ni resultado
y vuelve a ofrecerse en la carga; PH no cambia.

### Tests for User Story 1 ⚠️ (escribir primero, deben fallar)

- [ ] T003 [P] [US1] Agregar en `estudios/tests/test_servicio_correccion.py`:
  - `test_borrar_medicion`: `estudio_de("CL-", "PH")` con CL- = 2.35 y PH = 7.20; `corregir(..., borrar=("CL-",))` → no existe `Medicion` ni `Resultado` de CL-, la asignación está `pendiente`, `ResultadoCorreccion.borradas == [CL-]`, PH sin cambios.
  - `test_borrar_y_corregir_en_un_envio`: borrar CL- y corregir PH a 7.30 en el mismo `corregir` → los dos aplicados.
  - `test_borrar_y_corregir_referencias_de_la_misma_calculada`: `estudio_de("CA", "DUREZA-T", "MG")` con CA = 80 y DUREZA-T = 15; en el mismo `corregir`, borrar CA y corregir DUREZA-T a 20 → DUREZA-T vale 20 con resultado 400, CA sin medición y `pendiente`, MG sin `Resultado` y `pendiente` (caso límite de la spec).
  - `test_borrar_omite_si_cambio`: `originales={"CL-": "2.35"}` con la medición ya en `2.60` (actualizada antes) → no se borra y `omitidas == [(CL-, "cambió mientras se editaba")]`.
  - `test_borrar_omite_si_ya_no_existe`: borrar CL- y repetir el borrado con `originales={"CL-": "2.35"}` (la medición ya no existe, así que el helper no puede leer el vigente) → la segunda informa `[(CL-, "ya no tenía medición")]`.
- [ ] T004 [P] [US1] Agregar en `estudios/tests/test_corregir_mediciones.py`:
  - `test_formulario_ofrece_borrar`: GET → un `checkbox` `borrar_<pk>` por fila, con su `label`, y el texto «Para quitar una medición cargada por error, marcá Borrar.».
  - `test_revisar_muestra_borrado`: `revisar` con `borrar=("CL-",)` → la fila CL- con «2,35» y «se borra», aviso «Se aplicará 1 cambio en el estudio N (muestra PI 200001).», oculto `borrar_<pk>` y nada borrado.
  - `test_confirmar_borra_y_vuelve_a_ofrecerse`: `confirmar` con `borrar=("CL-",)` → 302 con «Se borró 1 medición del estudio N: CL-.»; GET de `estudios:cargar_mediciones` ofrece el campo de CL-.
  - `test_borrado_prevalece_sobre_el_valor` (parametrizado `""`, `"abc"`, `"9"` en CL- con `borrar=("CL-",)`) → `revisar` sin errores de campo y «se borra» en el resumen.
  - `test_solo_borrados_no_es_sin_cambios`: `revisar` solo con `borrar=("CL-",)` no muestra «No hay cambios para guardar.».
  - `test_mensajes_borrado_y_correccion`: `confirmar` borrando CL- y corrigiendo PH → mensajes «Se corrigió 1 medición del estudio N: PH.» y «Se borró 1 medición del estudio N: CL-.».
  - `test_otro_empleado_puede_borrar`: un empleado activo distinto del que cargó borra CL- por la vista con éxito (FR-001).
  - `test_reenvio_de_borrado`: dos `confirmar` iguales con `borrar=("CL-",)` (el primero con `follow=True`) → el segundo redirige con «CL-: ya no tenía medición.».

### Implementation for User Story 1

- [ ] T005 [US1] En `CorregirMedicionesForm` (`estudios/forms.py`), research R4: por fila, `BooleanField(required=False)` `borrar_<pk>` con `label` «Borrar la medición de COD»; `medicion_<pk>` pasa a `required=False`; el `initial` del valor y del original se toma de la medición solo si existe (`hasattr(asignacion, "medicion")`); en `clean()`, para las filas marcadas no se lee ni valida el valor (y se quitan sus errores de campo si los hubiera), y para las no marcadas un valor vacío agrega «La medición no puede quedar vacía.»; `cambios()` incluye `(asignacion, original, None)` por cada fila marcada; `filas()` devuelve también el campo `borrar_<pk>`; `borrados()` → lista de asignaciones marcadas.
- [ ] T006 [US1] En `estudios/servicios.py` (research R1, R5): `ResultadoCorreccion` suma `borradas: list = field(default_factory=list)`. En `corregir_mediciones`, buscar las asignaciones del estudio con esos pk (con `select_for_update(of=("self",))` y la medición si existe, en orden de código) en lugar de las mediciones; por cada una: sin medición → `omitidas.append((prueba, "ya no tenía medición"))`; vigente distinto del original → «cambió mientras se editaba»; `nuevo is None` → `medicion.delete()` y `borradas.append(prueba)`; vigente igual al nuevo → «ya tenía ese valor»; si no, corregir como en US 6.3. Llamar a `recalcular_resultados` con las asignaciones corregidas **y** borradas (depende de T005).
- [ ] T007 [US1] En `estudios/views.py`, `corregir_mediciones`: al confirmar, armar el formulario con `estudio.pruebas_asignadas.filter(pk__in=<pks de original_* del POST>)` (tengan o no medición); `revisar` y `editar` siguen con las que tienen medición. Mensajes: éxito de borradas «Se borraron N mediciones del estudio X: COD1, COD2.» / «Se borró 1 medición del estudio X: COD1.» además del de corregidas. Templates: en `corregir_mediciones.html`, columna **Borrar** con el checkbox y el texto del aviso; en `corregir_mediciones_confirmar.html`, «se borra» en «Valor nuevo» para las filas con `nuevo` `None`, el aviso «Se aplicarán N cambios…» / «Se aplicará 1 cambio…» cuando hay borrados (si no, el de US 6.3) y el oculto `borrar_<pk>` de las filas marcadas (depende de T005, T006).
- [ ] T008 [US1] Ejecutar `docker compose exec web pytest estudios` y dejar en verde T003–T004 sin romper US 6.1–6.3 (depende de T005–T007).

**Checkpoint**: se pueden borrar mediciones con confirmación, sin pisar cambios ajenos; MVP.

---

## Phase 4: User Story 2 - Que el borrado arrastre a lo que depende de la medición (Priority: P2)

**Goal**: dependientes sin resultado y en Pendiente; estudio a Pendiente de análisis o En proceso.

**Independent Test**: con CA, DUREZA-T y MG, borrar CA (MG Pendiente y avisa que falta CA); borrar
DUREZA-T (el estudio vuelve a Pendiente de análisis y ofrece «Agregar prueba»).

### Tests for User Story 2 ⚠️ (escribir primero, deben fallar)

- [ ] T009 [P] [US2] Agregar en `estudios/tests/test_servicio_correccion.py`:
  - `test_borrar_deja_dependientes_pendientes`: `estudio_de("CA", "DUREZA-T", "MG")` con CA = 80 y DUREZA-T = 15; borrar CA → MG sin `Resultado` y `pendiente`; DUREZA-T conserva valor y `fecha_calculo`; el estudio sigue `en_proceso`.
  - `test_borrar_validada`: con todas `completada`, borrar CA → CA y MG `pendiente`, DUREZA-T `completada`.
  - `test_borrar_todo_vuelve_a_pendiente_de_analisis`: borrar CA y DUREZA-T → estudio `pendiente_analisis` y `admite_modificaciones`.
  - `test_borrar_en_finalizado_reabre`: con todas `completada` y el estudio `finalizado`, borrar CA → estudio `en_proceso`.
- [ ] T010 [P] [US2] Agregar en `estudios/tests/test_corregir_mediciones.py`:
  - `test_revisar_avisa_validacion_por_borrado`: con CA y MG `completada`, `revisar` con `borrar=("CA",)` → «Perderán la validación: CA · Calcio (Ca), MG · Magnesio (Mg).».
  - `test_detalle_tras_borrar_todo`: borrar todas las mediciones por la vista → el detalle ofrece `estudios:agregar_prueba` y enlaces a `estudios:quitar_prueba` (las pruebas Pendientes se pueden quitar otra vez), y no «Corregir mediciones»; MG muestra «Faltan resultados de: …» o «Falta la medición.» según corresponda.

### Implementation for User Story 2

- [ ] T011 [US2] En `corregir_mediciones` (`estudios/servicios.py`), research R3: al final, con el estudio bloqueado, si no queda ninguna asignación `cargada` ni `completada` → `estado = pendiente_analisis`; si no, la regla de US 6.3 (Finalizado con alguna sin validar → `en_proceso`). Guardar con `save(update_fields=["estado"])` solo si cambió (depende de T006).
- [ ] T012 [US2] Ejecutar `docker compose exec web pytest estudios` y dejar en verde T009–T010 junto con US1 (depende de T011).

**Checkpoint**: ningún resultado queda calculado con una medición borrada.

---

## Phase 5: User Story 3 - Proteger lo emitido y los borrados simultáneos (Priority: P3)

**Goal**: probar el rechazo con informe emitido, la atomicidad del envío y el borrado concurrente.

**Independent Test**: con informe emitido no se borra; si el recálculo falla, nada se borra;
corregir y borrar la misma medición a la vez aplica solo una de las dos.

### Tests for User Story 3 ⚠️

- [ ] T013 [P] [US3] Agregar en `estudios/tests/test_servicio_correccion.py`:
  - `test_borrar_con_informe_emitido_rechaza`: con `informe_generado` → `CorregirMedicionesError` con el mensaje de informe emitido y la medición sigue.
  - `test_falla_en_recalculo_no_borra`: con `estudios.servicios.recalcular_resultados` parcheado para lanzar `RecalculoError("x")`, borrar CL- → `CorregirMedicionesError` y la `Medicion` y su `Resultado` siguen (FR-011).
  - `test_borrado_no_modifica_otros_datos`: otro estudio del mismo tipo con las mismas pruebas cargadas no cambia.
- [ ] T014 [P] [US3] Agregar en `estudios/tests/test_concurrencia_mediciones.py`: `test_borrado_y_correccion_concurrentes`: dos hilos sobre CA (original 80): uno lo borra y otro lo corrige a 50; exactamente uno se aplica y el otro queda en `omitidas` («cambió mientras se editaba» o «ya no tenía medición»); el estado final es coherente (o no hay medición y MG está `pendiente`, o CA vale 50 y MG está recalculado).

### Implementation for User Story 3

- [ ] T015 [US3] Ejecutar `docker compose exec web pytest estudios` y dejar en verde T013–T014; si alguno falla, corregirlo en `corregir_mediciones` (`estudios/servicios.py`) sin abrir transacciones nuevas (depende de T013, T014).

**Checkpoint**: US 6.5 completa.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [ ] T016 [P] Ejecutar `docker compose exec web ruff check .`, `docker compose exec web ruff format --check .` y `docker compose exec web python manage.py makemigrations --check --dry-run` (debe decir «No changes detected»); recompilar el CSS si los templates usan clases nuevas.
- [ ] T017 Ejecutar la suite completa `docker compose exec web pytest` y confirmar todo en verde.
- [ ] T018 Recorrer los pasos 1 a 6 de `specs/018-borrar-mediciones/quickstart.md` y cronometrar un borrado (menos de 1 minuto, SC-001).
- [ ] T019 [P] En `CLAUDE.md`, sección «Corrección de mediciones (US 6.3)»: el borrado (US 6.5) va en el mismo envío con `nuevo = None`; las reglas de omisión suman «ya no tenía medición»; al confirmar el formulario incluye las asignaciones sin medición para que un reenvío lo informe; el borrado se apoya en `calculo.descartar` (sin reglas propias); un estudio sin pruebas Cargadas ni Completadas vuelve a Pendiente de análisis. Quitar la línea «Borrar mediciones es US 6.5 (SCRUM-72), en su propia spec.».

---

## Dependencies & Execution Order

- **Setup (T001)** → **Foundational (T002)** → **US1** (MVP) → **US2** → **US3** → **Polish**.
- US2 y US3 dependen de US1 (servicio, formulario y vista); comparten archivos de test, así que van en secuencia.

```text
T001 → T002
US1: T003, T004 → T005 → T006 → T007 → T008
US2: T009, T010 → T011 → T012
US3: T013, T014 → T015
Polish: T016, T017, T018, T019
```

## Parallel Example: User Story 1

```bash
Task T003: "Tests del servicio en estudios/tests/test_servicio_correccion.py"
Task T004: "Tests de vistas en estudios/tests/test_corregir_mediciones.py"
```

## Implementation Strategy

Una sola tanda: la historia es chica y no tiene esquema nuevo. US1 entrega el borrado con sus
protecciones; US2 cierra los efectos en el estado del estudio; US3 prueba los casos límite; se
cierra con `ruff`, suite completa, recorrido manual y `CLAUDE.md`.
