---

description: "Lista de tareas de la US 6.3 – Modificar las mediciones"
---

# Tasks: Modificar las mediciones

**Input**: `specs/017-modificar-mediciones/` (`plan.md`, `spec.md`, `research.md`, `data-model.md`,
`contracts/corregir-mediciones-ui.md`, `quickstart.md`)

**Prerequisites**: `plan.md`, `spec.md` y la rama `016-calcular-resultado` (US 6.2, PR #29), de la
que sale esta rama: `Medicion` con `valor_ingresado`, `leer_valor`, `CargarMedicionesForm` y la
vista `cargar_mediciones` como modelo del flujo revisar/editar/confirmar; `Resultado`,
`calculo.recalcular`, `servicios.recalcular_resultados` y `RecalculoError`;
`Estudio.admite_correcciones`; el filtro `|unidad`; fixtures `estudio_de`, `catalogo`,
`pruebas_division`, `empleado`, `cliente_http` y los helpers `cargar` y `asignacion_de` de
`estudios/tests/utiles.py`.

**Tests**: SÍ. La constitution (principio III) exige un test por escenario de aceptación. Los
tests siguen el «Mapa de tests» de `plan.md` y se escriben **antes** de la implementación de cada
historia (deben fallar primero).

**Organization**: tres user stories — US1 (P1, corregir y recalcular), US2 (P2, validar los
valores corregidos) y US3 (P3, revalidación, informe emitido y correcciones simultáneas).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: se puede ejecutar en paralelo (archivos distintos, sin dependencias pendientes)
- **[Story]**: user story a la que pertenece la tarea (`[US1]`, `[US2]`, `[US3]`)
- Rutas relativas a la raíz del repo

## Convenciones para todas las tareas

- Textos y mensajes en **español**, copiados **literalmente** de
  `contracts/corregir-mediciones-ui.md`.
- Mismo estilo que `cargar_mediciones` (vista, formulario y templates de US 6.1): diseño de
  SCRUM-67, `ui/encabezado.html`, `.tabla`, `ui/errores_form.html`, `ui/estado_vacio.html`,
  `data-componente="resumen"` y `data-componente="acciones-confirmacion"`; doble envío evitado con
  `data-enviado` (nunca deshabilitar los botones: no enviarían la `accion`). Unidades con `|unidad`.
- La vista llama a `servicios.corregir_mediciones` y los tests parchean
  `estudios.servicios.corregir_mediciones`.
- El recálculo se hace siempre con `servicios.recalcular_resultados` en la misma transacción que
  actualiza la medición (acuerdo con US 6.2); nunca llamando directo a `calculo.recalcular`.
- Una sola migración: `estudios/migrations/0006_medicion_correccion.py`.
- Comandos dentro de Docker: `docker compose exec web pytest estudios`,
  `docker compose exec web ruff check .`, `docker compose exec web ruff format --check .`.

---

## Phase 1: Setup (Shared Infrastructure)

- [X] T001 **Gate de la constitution (principio I)**: confirmar que el equipo aprobó `specs/017-modificar-mediciones/spec.md` y actualizar su `**Status**` a «Aprobada (fecha)». Confirmar que la rama sale de `016-calcular-resultado` (o de `main` si el PR #29 ya se mergeó) y ejecutar `docker compose exec web pytest` y `docker compose exec web python manage.py makemigrations --check --dry-run`: suite en verde y sin cambios pendientes.

---

## Phase 2: Foundational (Blocking Prerequisites)

**⚠️ CRITICAL**: ninguna historia empieza antes de terminar esta fase.

- [X] T002 [P] Agregar en `estudios/tests/test_modelos.py`: `test_medicion_correccion_completa`: una `Medicion` con `corregida_por` y sin `fecha_correccion` (o al revés) lanza `IntegrityError`; con los dos o con ninguno se guarda. Y en `estudios/tests/test_calculo.py`: `test_afectadas`: con `estudio_de("CA", "DUREZA-T", "MG", "PH")`, `afectadas(por_codigo(estudio), {"CA"}) == {"CA", "MG"}` y `afectadas(..., {"PH"}) == {"PH"}`.
- [X] T003 Agregar en `estudios/models.py`, en `Medicion` (data-model §1): `corregida_por = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.PROTECT, related_name="mediciones_corregidas", editable=False)`, `fecha_correccion = models.DateTimeField("fecha de corrección", null=True, blank=True)` y en `Meta.constraints` `models.CheckConstraint(condition=Q(corregida_por__isnull=True, fecha_correccion__isnull=True) | Q(corregida_por__isnull=False, fecha_correccion__isnull=False), name="medicion_correccion_completa")`.
- [X] T004 Generar `estudios/migrations/0006_medicion_correccion.py` con `docker compose exec -u "$(id -u):$(id -g)" web python manage.py makemigrations estudios --name medicion_correccion` y verificar que solo agrega los dos campos y el constraint (depende de T003).
- [X] T005 [P] En `estudios/calculo.py`, extraer de `recalcular` la función `afectadas(todas, codigos) -> set[str]` (los códigos dados más sus dependientes directos o indirectos, con `dependientes(todas)`) y usarla dentro de `recalcular` sin cambiar su comportamiento (research R5).
- [X] T006 Ejecutar `docker compose exec web pytest estudios` y dejar en verde T002 sin romper US 6.1 ni US 6.2 (depende de T002–T005).

**Checkpoint**: la medición puede registrar su corrección y el cálculo expone las afectadas.

---

## Phase 3: User Story 1 - Corregir mediciones cargadas (Priority: P1) 🎯 MVP

**Goal**: desde el detalle, corregir una o varias mediciones con confirmación; el valor nuevo
reemplaza al anterior, queda quién y cuándo corrigió, y los resultados se recalculan.

**Independent Test**: con CL- = 2,35 cargado, corregir a 2,53 y verificar medición 2,53, resultado
25,3 mg/l y «Corregida por …» en el detalle.

### Tests for User Story 1 ⚠️ (escribir primero, deben fallar)

- [X] T007 [P] [US1] Crear `estudios/tests/test_servicio_correccion.py` (`pytestmark = pytest.mark.django_db`; helper `corregir(estudio, usuario, **por_codigo)` que arma `{pk: (valor_ingresado actual, Decimal(nuevo))}` y llama a `corregir_mediciones`):
  - `test_corregir_mediciones_actualiza_la_misma_fila`: cargar CL- = 2.35 con `empleado` y corregir a 2.53 con otro usuario activo: misma `Medicion` (mismo `pk`), `valor == Decimal("2.53")`, `decimales == 2`, `cargada_por == empleado`, `fecha_carga` sin cambios, `corregida_por == otro`, `fecha_correccion` entre antes y después; `ResultadoCorreccion.corregidas` la contiene.
  - `test_confirmar_recalcula_dependientes`: `estudio_de("CA", "DUREZA-T", "MG")` con CA = 80 y DUREZA-T = 15; corregir CA a 40 → resultado de CA 40 y de MG `Decimal("48.6")`; DUREZA-T conserva valor y `fecha_calculo`.
  - `test_corregir_en_estudio_finalizado`: con el estudio en `finalizado` (`update`) la corrección se aplica.
  - `test_informe_emitido_rechaza`: con `informe_generado` → `CorregirMedicionesError` con «El estudio ya tiene el informe emitido: sus mediciones y resultados no se pueden cambiar.» y la medición sin cambios (FR-009; en el MVP).
  - `test_omite_si_cambio_mientras_se_editaba`: cambios con original `80` para CA cuando la medición ya vale `90` (actualizada antes) → CA no cambia y `omitidas == [(CA, "cambió mientras se editaba")]`; otra medición del mismo envío se corrige (FR-010; en el MVP).
  - `test_omite_si_ya_tenia_ese_valor`: original `80`, nuevo `40`, vigente `40` → `omitidas == [(CA, "ya tenía ese valor")]` y `fecha_correccion` no cambia.
  - `test_correccion_no_modifica_otros_datos`: con otro estudio del mismo tipo y otra medición del mismo estudio, solo cambia la corregida; la muestra, el catálogo y el otro estudio no cambian.
- [X] T008 [P] [US1] Crear `estudios/tests/test_corregir_mediciones.py` (`pytestmark = pytest.mark.django_db`; helpers `url_corregir`, `url_detalle`, `mensajes`, como en `test_cargar_mediciones.py`):
  - `test_detalle_ofrece_corregir` y `test_detalle_no_ofrece_corregir` (parametrizado: estudio sin mediciones; estudio con informe emitido).
  - `test_formulario_precargado`: con CL- = 2,35 y PH = 7,20 cargados, GET → 200 con `value="2,35"` y `value="7,20"` en `medicion_<pk>`, ocultos `original_<pk>` con `2.35` y `7.20`, unidad «ml»/«UpH», nombre del empleado y fecha de carga.
  - `test_revisar_muestra_solo_cambios`: POST `revisar` cambiando CL- a `2,53` y dejando PH igual → 200 con `corregir_mediciones_confirmar.html`, «Se corregirá 1 medición en el estudio N (muestra PI 200001).», la fila CL- con «2,35» y «2,53», sin fila de PH, enlace Cancelar al detalle y ninguna medición cambiada.
  - `test_editar_conserva_valores`: POST `editar` → formulario con `value="2,53"`.
  - `test_confirmar_corrige_y_recalcula`: POST `confirmar` → 302 al detalle con «Se corrigió 1 medición del estudio N: CL-.»; el detalle muestra «2,53 ml», «25,3 mg/l» y «Corregida por».
  - `test_otro_empleado_puede_corregir`: otro empleado activo (no el que cargó) corrige con éxito.
  - `test_vista_informe_emitido_rechaza`: con `informe_generado`, GET y POST `revisar` → 302 al detalle con el mensaje de informe emitido.
  - `test_corregir_requiere_sesion` (GET y POST) y `test_corregir_estudio_inexistente_404`.
  - `test_sin_mediciones_estado_vacio`: GET en un estudio sin mediciones → «Este estudio no tiene mediciones para corregir.».
  - `test_reenvio_informa_ya_tenia_ese_valor`: dos POST `confirmar` iguales (el primero con `follow=True`) → el segundo redirige con «CL-: ya tenía ese valor.» y la medición no vuelve a cambiar.
  - `test_confirmar_con_cambio_ajeno_se_informa`: abrir el formulario (original 2,35), cambiar la medición a 2,60 directamente en la base y confirmar 2,53 → 302 con «CL-: cambió mientras se editaba.» (no «No hay cambios para guardar.») y CL- sigue en 2,60; con el cambio ajeno a 2,53 (el mismo valor) → «CL-: ya tenía ese valor.».
  - `test_error_de_base_al_corregir`: con `estudios.servicios.corregir_mediciones` parcheado para lanzar `DatabaseError` → 302 con «No se pudieron guardar las correcciones. Intentá nuevamente.» y nada cambia.

### Implementation for User Story 1

- [X] T009 [US1] Agregar en `estudios/forms.py` `CorregirMedicionesForm(forms.Form)` (research R2): `__init__(self, *args, asignaciones, **kwargs)` con asignaciones que tienen medición; por cada una, `CharField(max_length=40)` `medicion_<pk>` con `initial` = `valor_ingresado` como texto con coma (`str(v).replace(".", ",")`) y `widget.attrs` como en la carga, y `CharField(widget=HiddenInput)` `original_<pk>` con `initial = str(valor_ingresado)`; `clean()` lee cada valor con `leer_valor` (los errores van al campo con `is-invalid` y `aria-describedby`, como `CargarMedicionesForm`); `originales()` → `{pk: Decimal(original_<pk>)}` (el valor que se vio al abrir); `cambios()` → lista de `(asignacion, anterior: Decimal, nuevo: Decimal)` de las filas cuyo `str(nuevo)` difiere de `str(original)` — **nunca** del valor vigente en la base: si otro empleado la cambió mientras tanto, el servicio lo detecta e informa (research R3), en lugar de que la fila desaparezca sin aviso; `filas()` como en la carga.
- [X] T010 [US1] Agregar en `estudios/servicios.py` `class CorregirMedicionesError(Exception)`, `@dataclass ResultadoCorreccion(corregidas, omitidas, sin_calcular)` (listas con `default_factory`) y `corregir_mediciones(estudio_pk, cambios, usuario)` (research R4): sesión activa («Se requiere una sesión activa.»); `transaction.atomic()`; estudio con `select_for_update()` (None → «El estudio no está disponible.»); `if not estudio.admite_correcciones: raise CorregirMedicionesError("El estudio ya tiene el informe emitido: sus mediciones y resultados no se pueden cambiar.")`; `Medicion.objects.select_for_update(of=("self",)).select_related("asignacion__prueba").filter(asignacion__estudio=estudio, asignacion__pk__in=cambios)` en orden de código; por cada una, comparar `str(medicion.valor_ingresado)` con `str(original)` y `str(nuevo)` (research R3): igual al nuevo → `omitidas.append((prueba, "ya tenía ese valor"))`; distinto del original → `omitidas.append((prueba, "cambió mientras se editaba"))`; solo si coincide con el original, `valor = nuevo`, `decimales = max(0, -nuevo.as_tuple().exponent)`, `corregida_por = usuario`, `fecha_correccion = timezone.now()`, `save(update_fields=[...])`; después `resultado.sin_calcular = recalcular_resultados(estudio.pk, [pks corregidas], usuario)` si hubo corregidas, convirtiendo un `RecalculoError` en `CorregirMedicionesError(str(exc))` (`raise ... from exc`) para que la vista nunca reciba una excepción que no captura (depende de T003).
- [X] T011 [US1] Crear la vista `corregir_mediciones(request, pk)` en `estudios/views.py` según el contrato, con la misma estructura que `cargar_mediciones`: `get_object_or_404`; en GET, `revisar` y `editar`, si `not estudio.admite_correcciones` → 302 al detalle con el mensaje de informe emitido; asignaciones con medición (`medicion__isnull=False`, `select_related("prueba", "medicion", "medicion__cargada_por", "medicion__corregida_por")`, por código); `accion` inválida → «La acción no es válida.»; `revisar` válido → `corregir_mediciones_confirmar.html` con `form.cambios()`; `confirmar` válido → `servicios.corregir_mediciones(estudio.pk, {a.pk: (form.originales()[a.pk], nuevo) for a, _, nuevo in form.cambios()}, request.user)` y mensajes del contrato (éxito con singular/plural; `messages.warning` «COD: motivo.» por cada omitida; `CorregirMedicionesError` → error; `DatabaseError` → «No se pudieron guardar las correcciones. Intentá nuevamente.»). Registrar `path("<int:pk>/mediciones/corregir/", views.corregir_mediciones, name="corregir_mediciones")` en `estudios/urls.py` (depende de T009, T010).
- [X] T012 [P] [US1] Crear `estudios/templates/estudios/corregir_mediciones.html` (como `cargar_mediciones.html`): encabezado con migas «Estudios › Estudio N › Corregir mediciones», tabla Código / Prueba / Unidad (`|unidad`) / Cargada por (y «Corregida por …» si corresponde) / Medición (campo y oculto `original_<pk>`), errores junto al campo, `ui/errores_form.html`, estado vacío «Este estudio no tiene mediciones para corregir.» y botones **Revisar cambios** (`accion=revisar`) y **Cancelar** (depende de T011).
- [X] T013 [P] [US1] Crear `estudios/templates/estudios/corregir_mediciones_confirmar.html` (como `cargar_mediciones_confirmar.html`): aviso «Se corregirán N mediciones en el estudio X (muestra PI Y).» / «Se corregirá 1 medición…», resumen del estudio y la muestra, tabla Código / Prueba / Valor anterior / Valor nuevo / Unidad, ocultos `medicion_<pk>` y `original_<pk>` de **todas** las filas del formulario, y acciones **Guardar correcciones** (`accion=confirmar`), **Volver a editar** (`accion=editar`) y **Cancelar** (depende de T011).
- [X] T014 [US1] En `estudios/views.py`, `detalle`: sumar `"medicion__corregida_por"` al `select_related` y `hay_mediciones` al contexto. En `estudios/templates/estudios/detalle.html`: botón **Corregir mediciones** (`btn btn-secundario`, ícono `pencil`) si `estudio.admite_correcciones and hay_mediciones`, y en la columna Medición, si `asignacion.medicion.corregida_por`, la línea «Corregida por {{ nombre o correo }} · {{ fecha_correccion|date:"d/m/Y H:i" }}» (depende de T003, T011).
- [X] T015 [US1] Ejecutar `docker compose exec web pytest estudios` y dejar en verde T007–T008 (depende de T009–T014).

**Checkpoint**: se pueden corregir mediciones con confirmación y recálculo; MVP de la US 6.3.

---

## Phase 4: User Story 2 - Validar los valores corregidos (Priority: P2)

**Goal**: el valor corregido pasa las mismas validaciones que la carga; campo vacío y envío sin
cambios se informan.

**Independent Test**: corregir con `abc`, `0,1234567`, un campo vacío y sin cambios; ver los
mensajes junto a cada campo y que nada cambia.

### Tests for User Story 2 ⚠️ (escribir primero, deben fallar)

- [X] T016 [P] [US2] Agregar en `estudios/tests/test_corregir_mediciones.py`:
  - `test_revisar_con_valor_invalido_no_guarda`: `abc` en CL- y `0,1234567` en PH → 200 con «Ingresá un número válido (usá coma o punto para los decimales).» y «Ingresá como máximo 6 decimales.» en sus bloques `<auto_id>_error`, valores conservados y nada cambia.
  - `test_confirmar_con_valor_invalido_no_guarda`: el mismo envío con `accion=confirmar` → 200 y el servicio parcheado no se llama.
  - `test_campo_vacio_rechazado` (parametrizado `""` y `"   "`): «La medición no puede quedar vacía.» junto al campo.
  - `test_sin_cambios`: `revisar` con todos los valores iguales → «No hay cambios para guardar.».
  - `test_cambio_de_decimales_es_cambio`: PH cargado `7,20` y corregido a `7,2` → aparece en el resumen como cambio y, al confirmar, `decimales == 1`.

### Implementation for User Story 2

- [X] T017 [US2] En `CorregirMedicionesForm` (`estudios/forms.py`): los campos `medicion_<pk>` son obligatorios con `error_messages={"required": "La medición no puede quedar vacía."}` (un texto solo con espacios cuenta como vacío: `strip=True`); `clean()` agrega el error general «No hay cambios para guardar.» si no hay errores de campo y `cambios()` está vacío (depende de T009).
- [X] T018 [US2] Ejecutar `docker compose exec web pytest estudios` y dejar en verde T016 junto con US1 (depende de T017).

**Checkpoint**: ningún valor inválido reemplaza a uno bueno.

---

## Phase 5: User Story 3 - Revalidar lo que cambió y proteger lo emitido (Priority: P3)

**Goal**: avisar antes de confirmar quién pierde la validación, reabrir el estudio Finalizado y
probar las correcciones simultáneas (la regla del valor original ya está en el MVP, T010).

**Independent Test**: con CA y MG validados, corregir CA: el resumen avisa que ambos pierden la
validación y después quedan Cargada; dos correcciones a la vez de la misma medición aplican una
sola.

### Tests for User Story 3 ⚠️ (escribir primero, deben fallar)

- [X] T019 [P] [US3] Agregar en `estudios/tests/test_servicio_correccion.py`:
  - `test_correccion_quita_validacion_y_reabre_estudio`: `estudio_de("CA", "DUREZA-T", "MG")` cargado, todas las asignaciones `completada` y el estudio `finalizado` (`update`); corregir CA → CA y MG `cargada`, DUREZA-T sigue `completada` y el estudio pasa a `en_proceso`.
- [X] T020 [P] [US3] Agregar en `estudios/tests/test_corregir_mediciones.py`:
  - `test_revisar_avisa_perdida_de_validacion`: con CA y MG `completada`, `revisar` corrigiendo CA → «Perderán la validación: CA · Calcio (Ca), MG · Magnesio (Mg).»; sin validadas afectadas, no aparece el aviso.
  - `test_correccion_a_division_por_cero_advierte`: con `pruebas_division`, DIV-A = 6 y DIV-B = 2; corregir DIV-B a 0 → mensajes incluyen «DIV: no se pudo calcular el resultado (división por cero).» y el detalle muestra «No se pudo calcular: división por cero.».
- [X] T021 [P] [US3] Agregar en `estudios/tests/test_concurrencia_mediciones.py`: `test_correcciones_concurrentes`: dos hilos corrigen CA (original 80) a 50 y a 60 a la vez; queda uno de los dos valores, el otro resultado tiene CA en `omitidas` con «cambió mientras se editaba», y MG corresponde al valor que quedó.

### Implementation for User Story 3

- [X] T022 [US3] En `corregir_mediciones` (`estudios/servicios.py`): después del recálculo, si el estudio está `finalizado` y alguna asignación no está `completada`, pasarlo a `en_proceso` (`save(update_fields=["estado"])`) (FR-008) (depende de T010).
- [X] T023 [US3] En `estudios/views.py`, `corregir_mediciones`: en `revisar` válido, calcular las pruebas que perderán la validación con `calculo.afectadas(todas, códigos de form.cambios())` filtradas por `estado == completada` y pasarlas al template; en `confirmar`, `messages.warning` «COD: no se pudo calcular el resultado (motivo).» por cada `sin_calcular` (las omitidas ya las informa T011); el éxito solo si hubo corregidas. En `corregir_mediciones_confirmar.html`, el aviso de advertencia «Perderán la validación: COD · nombre, …» si la lista no está vacía (depende de T005, T011, T022).
- [X] T024 [US3] Ejecutar `docker compose exec web pytest estudios` y dejar en verde T019–T021 junto con US1 y US2 (depende de T022–T023).

**Checkpoint**: US 6.3 completa.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T025 [P] Ejecutar `docker compose exec web ruff check .`, `docker compose exec web ruff format --check .` y `docker compose exec web python manage.py makemigrations --check --dry-run`, y corregir lo que aparezca; recompilar el CSS si los templates usan clases nuevas (`tailwindcss -i static/src/aqualab.css -o static/css/aqualab.css --minify`).
- [X] T026 Ejecutar la suite completa `docker compose exec web pytest` y confirmar todo en verde.
- [X] T027 Aplicar la migración en la base de desarrollo (`migrate`) y recorrer los pasos 1 a 5 de `specs/017-modificar-mediciones/quickstart.md`, cronometrando una corrección (menos de 1 minuto, SC-001).
- [X] T028 [P] En `CLAUDE.md`: sección «Corrección de mediciones (US 6.3)» con lo no obvio: corregir actualiza la misma fila de `Medicion` (`corregida_por`, `fecha_correccion`; sin historial); concurrencia optimista con el valor original (`original_<pk>`), con los motivos «cambió mientras se editaba» y «ya tenía ese valor»; `corregir_mediciones` recalcula siempre con `recalcular_resultados` en la misma transacción y reabre un estudio Finalizado; `calculo.afectadas` es la única definición de pruebas afectadas (aviso y recálculo); borrar mediciones es US 6.5 (SCRUM-72). Quitar la nota **US 6.3** de la sección de US 6.2, que queda cumplida.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: `T001`.
- **Foundational (Phase 2)**: depende de la fase 1. `T002` y `T005` en paralelo; `T003` → `T004`; `T006` al final.
- **US1 (Phase 3)**: depende de la fase 2. Es el MVP.
- **US2 (Phase 4)**: depende de US1 (completa su formulario).
- **US3 (Phase 5)**: depende de US1 (completa su servicio, su vista y su template); puede ir antes o después de US2, pero comparten `test_corregir_mediciones.py` y `views.py`, así que conviene en secuencia.
- **Polish (Phase 6)**: depende de las tres historias.

### Grafo

```text
T001 → T002, T005 ─┐
       T003 → T004 ┴─→ T006
                         │
          ┌──────────────┘
          ▼
US1: T007, T008 → T009 → T010 → T011 → T012, T013 → T014 → T015
US2: T016 → T017 → T018
US3: T019, T020, T021 → T022 → T023 → T024
Polish: T025, T026, T027, T028
```

---

## Parallel Example: User Story 1

```bash
Task T007: "Tests del servicio en estudios/tests/test_servicio_correccion.py"
Task T008: "Tests de vistas en estudios/tests/test_corregir_mediciones.py"
# Después de T011:
Task T012: "estudios/templates/estudios/corregir_mediciones.html"
Task T013: "estudios/templates/estudios/corregir_mediciones_confirmar.html"
```

## Parallel Example: User Story 3

```bash
Task T019: "Reglas del servicio en estudios/tests/test_servicio_correccion.py"
Task T020: "Avisos y reenvío en estudios/tests/test_corregir_mediciones.py"
Task T021: "Concurrencia en estudios/tests/test_concurrencia_mediciones.py"
```

---

## Implementation Strategy

### En dos tandas (según `docs/guias/guia-sdd-paso-a-paso.md`)

1. **Tanda 1 (Fases 1 y 2 — `T001` a `T006`)**: aprobación, campos de corrección con su migración
   y `afectadas()`; suite en verde.
2. **Tanda 2 (Fases 3 a 6 — `T007` a `T028`)**: US1 (corregir, MVP, ya rechaza con informe
   emitido y no pisa correcciones ajenas), US2 (validación) y US3 (validación perdida, reapertura y concurrencia), cada una con
   sus tests escritos primero; cerrar con `ruff`, suite completa, recorrido manual y `CLAUDE.md`.
