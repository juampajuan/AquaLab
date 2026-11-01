---

description: "Lista de tareas de la US 6.4 – Validar resultados"
---

# Tasks: Validar resultados

**Input**: `specs/019-validar-resultados/` (`plan.md`, `spec.md`, `research.md`, `data-model.md`,
`contracts/validar-resultados-ui.md`, `quickstart.md`)

**Prerequisites**: `plan.md`, `spec.md` y `main` con el PR #32 (Ausente/Presente): `PruebaEstudio`
con `EstadoPruebaEstudio`, `Medicion`, `Resultado`, `calculo.recalcular` / `calculo.descartar` /
`calculo.cambiar_estado`, `servicios.cargar_mediciones` / `corregir_mediciones` /
`estado_tras_correccion`, `Estudio.admite_correcciones`, `Prueba` y `LimiteVertido` con límites
como texto (SCRUM-64), filtros `|unidad` y `|valor_medicion` (`config/ui.py`), fixtures
`empleado`, `cliente_http`, `muestra`, `catalogo`, `estudio_de` y helpers `cargar` y
`asignacion_de` de `estudios/tests/utiles.py`.

**Tests**: SÍ. La constitution (principio III) exige un test por escenario de aceptación y casos
conocidos para los cálculos. Los tests siguen el «Mapa de tests» de `plan.md` y se escriben
**antes** de la implementación de cada historia (deben fallar primero).

**Organization**: tres user stories — US1 (P1, validar los resultados de un estudio), US2 (P2, ver
si cada resultado cumple en el detalle) y US3 (P3, habilitar a los bioquímicos).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: se puede ejecutar en paralelo (archivos distintos, sin dependencias pendientes)
- **[Story]**: user story a la que pertenece la tarea (`[US1]`, `[US2]`, `[US3]`)
- Rutas relativas a la raíz del repo

## Convenciones para todas las tareas

- Textos y mensajes en **español**, copiados **literalmente** de
  `contracts/validar-resultados-ui.md`.
- Mismo estilo que `corregir_mediciones` (vista, formulario y templates de US 6.3): diseño de
  SCRUM-67, `ui/encabezado.html`, `.tabla`, `ui/errores_form.html`, `ui/estado_vacio.html`,
  `data-componente="resumen"` y `data-componente="acciones-confirmacion"`; doble envío evitado con
  `data-enviado` (nunca deshabilitar los botones). Evaluaciones con `ui/estado.html`: «Cumple» →
  `success`, «Fuera de norma» → `danger`, «Sin límite comparable» → `neutral`. **Sin clases CSS
  nuevas** (el CI compila Tailwind y falla si `static/css/aqualab.css` cambia).
- La vista llama a `servicios.validar_resultados` y los tests parchean
  `estudios.servicios.validar_resultados`.
- Permiso: `estudios.validar_resultados`, mismo patrón que `gestionar_catalogo` (US 5.5):
  `@permission_required("estudios.validar_resultados", raise_exception=True)` en la vista,
  revalidado en el servicio y `{% if perms.estudios.validar_resultados %}` en templates.
- No se toca `estudios/admin.py` (el admin de estudios es otra tarea del sprint).
- Dos migraciones: `estudios/migrations/0007_validacion.py` y `0008_grupo_bioquimicos.py`.
- Comandos dentro de Docker: `docker compose exec web pytest estudios pruebas`,
  `docker compose exec web ruff check .`, `docker compose exec web ruff format --check .`.

---

## Phase 1: Setup (Shared Infrastructure)

- [ ] T001 **Gate de la constitution (principio I)**: confirmar que el equipo aprobó `specs/019-validar-resultados/spec.md`, completar la clave de Jira en su **Input** y en **Assumptions → Trazabilidad**, y actualizar su `**Status**` a «Aprobada (fecha)». Confirmar que la rama `019-validar-resultados` sale de `main` con el PR #32 y ejecutar `docker compose exec web pytest` y `docker compose exec web python manage.py makemigrations --check --dry-run`: suite en verde y sin cambios pendientes.

---

## Phase 2: Foundational (Blocking Prerequisites)

**⚠️ CRITICAL**: ninguna historia empieza antes de terminar esta fase.

- [X] T002 [P] Crear `pruebas/tests/test_limites.py` (sin base de datos donde se pueda) con: `test_leer_limite` parametrizado: `"8.5"` y `"7,01"` → `Decimal`; `""` y `"  "` → `None`; `"Ausente"`, `"ausencia"`, `" AUSENTE "` → `AUSENTE`; `"SOE"`, `"NE"`, `"Ph-0,2"`, `"Ph+0,2"` → `NO_COMPARABLE`. `test_evaluar` parametrizado con límites reales del catálogo: pH 6.4/8.5 con 7.4 → cumple, 6.4 y 8.5 → cumple (bordes inclusivos), 6.39 y 8.51 → fuera de norma; Cloruro máx. 350.0 con 350 → cumple y 400 → fuera; máx. «Ausente» con 0 → cumple y con 1 o 0.1 → fuera; máx. «Ausencia» con 0 → cumple y 3 → fuera; máx. «SOE» → sin límite; mín. «Ph-0,2» y máx. «Ph+0,2» → sin límite; ambos vacíos → sin límite; solo mínimo 0.1 con 0.05 → fuera; Cloruro máx. 350.0 con 350.00004 → fuera (se compara el valor completo aunque en pantalla se vea 350). `test_limites_aplicables` (con `@pytest.mark.django_db` y el fixture `catalogo` de `estudios/tests/conftest.py`, o creando `Prueba` y `LimiteVertido` a mano): PH con vertido `agua` → 6.4/8.5, origen `general`; `cloacal` → 7.01/10.0, origen `cloacal`; `canal` → 6.5/10, origen `canal`; COL-FEC `canal` → mín. vacío y máx. 2000 (reemplaza al general «Ausencia»); CL- `cloacal` sin fila de vertido → generales; norma copiada de la fila usada.
- [X] T003 Implementar `pruebas/limites.py` según research R3 hasta que pase T002: `AUSENTE` y `NO_COMPARABLE` (centinelas), `Evaluacion(TextChoices)` con `CUMPLE = "cumple", "Cumple"`, `FUERA_DE_NORMA = "fuera_de_norma", "Fuera de norma"`, `SIN_LIMITE = "sin_limite", "Sin límite comparable"`; `leer_limite(texto)` (número con punto o coma decimal y signo opcional; «Ausente»/«Ausencia» sin distinguir mayúsculas; vacío → `None`; otro texto → `NO_COMPARABLE`); un `LimitesAplicables` (dataclass `minimo`, `maximo`, `norma`, `origen`, con los textos tal como están en el catálogo) y `limites_aplicables(prueba, tipo_vertido)` que usa `prueba.limites_vertido.all()` (aprovecha `prefetch_related`) y, si hay fila para `tipo_vertido`, la usa completa; si no, los generales con origen `general`; `evaluar(valor, limites)` con las reglas de FR-007 (`data-model.md`, «Reglas de evaluación»). Sin `float` ni `eval` (principio IV).
- [X] T004 [P] Agregar en `estudios/models.py` `OrigenLimites(TextChoices)` (`GENERAL = "general", "Generales"`, `CLOACAL = "cloacal", "Cloacal"`, `CANAL = "canal", "Canal"`) y el modelo `Validacion` de `data-model.md`: «`asignacion = ForeignKey(PruebaEstudio, on_delete=PROTECT, related_name="validaciones", editable=False)`», «`validada_por = ForeignKey(AUTH_USER_MODEL, on_delete=PROTECT, related_name="validaciones", editable=False)`», «`fecha_validacion = DateTimeField(auto_now_add=True)`», «`limite_min`/`limite_max = CharField(50, blank=True, default="")`», «`norma = CharField(150, blank=True, default="")`», «`origen_limites = CharField(10, choices=OrigenLimites)`», «`evaluacion = CharField(20, choices=Evaluacion)`» (importado de `pruebas.limites`), «`anulada = BooleanField(default=False)`», «`fecha_anulacion = DateTimeField(null=True, blank=True)`», «`UniqueConstraint(fields=["asignacion"], condition=Q(anulada=False), name="validacion_vigente_unica")`», «`CheckConstraint` `validacion_anulacion_completa`: `anulada` y `fecha_anulacion` van juntos», `Meta.permissions = [("validar_resultados", "Puede validar resultados")]`, `verbose_name = "validación"`, `verbose_name_plural = "validaciones"` y `__str__`. Generar `estudios/migrations/0007_validacion.py` con `makemigrations`. Agregar en `estudios/tests/test_modelos.py` `test_validacion_una_vigente_por_asignacion` (una segunda `Validacion` no anulada para la misma asignación lanza `IntegrityError`; con la primera anulada se guarda), `test_validacion_anulacion_completa` (`anulada=True` sin `fecha_anulacion`, o al revés, lanza `IntegrityError`) y `test_validacion_protege_asignacion` (borrar la `PruebaEstudio` con validación lanza `ProtectedError`).
- [X] T005 Crear `estudios/migrations/0008_grupo_bioquimicos.py` (depende de `0007_validacion` y de `("auth", "0012_alter_user_first_name_max_length")` o la última de `auth`): `RunPython` que llama a `create_permissions(apps.get_app_config("estudios"), apps=apps, verbosity=0)`, crea con `get_or_create` el grupo «Bioquímicos» y le agrega el permiso `validar_resultados`; reversa que quita el permiso del grupo y lo borra solo si quedó sin permisos ni usuarios. Agregar `estudios/tests/test_validacion_permisos.py` con `test_grupo_bioquimicos_tiene_el_permiso`.
- [X] T006 Modificar `calculo.cambiar_estado(asignacion, estado)` en `estudios/calculo.py` según research R2: si la asignación sale de `COMPLETADA`, anular su `Validacion` vigente (`anulada=True`, `fecha_anulacion=timezone.now()`, `update_fields`) antes de guardar el estado nuevo; nunca borrarla (FR-017). Agregar en `estudios/tests/test_servicio_validacion.py` (nuevo) `test_correccion_anula_validacion` (validar a mano: `Validacion` + estado Completada; corregir con `servicios.corregir_mediciones` → vuelve a Cargada, la `Validacion` sigue existiendo con `anulada=True` y `fecha_anulacion`, y no hay ninguna vigente) y `test_borrado_anula_validacion` (lo mismo borrando la medición con `nuevo = None`, US 6.5). La suite existente debe seguir en verde.
- [X] T007 [P] Agregar en `estudios/tests/conftest.py` el fixture `bioquimico` (el `empleado` agregado al grupo «Bioquímicos») y `cliente_bioquimico` (cliente HTTP con sesión del bioquímico). El helper `validar` se agrega en `T011`, cuando exista el servicio.

**Checkpoint**: evaluación probada con el catálogo real, `Validacion` migrada con su permiso y su grupo, y la pérdida de validación conectada al recálculo.

---

## Phase 3: User Story 1 - Validar los resultados de un estudio (Priority: P1) 🎯 MVP

**Goal**: el bioquímico elige pruebas Cargadas con resultado, revisa un resumen y confirma; quedan Completadas con quién, cuándo, límites y evaluación, y el estudio pasa a Finalizado cuando no queda ninguna sin validar.

**Independent Test**: estudio de Agua con pH 7,4 y Cloruro 120; validar ambas → Completadas con «Cumple», «Validada por …» y estudio Finalizado.

### Tests for User Story 1 ⚠️ (escribir primero, deben fallar)

- [X] T008 [P] [US1] Agregar en `estudios/tests/test_servicio_validacion.py`: `test_confirmar_valida` (Completada + `Validacion` con `validada_por`, `fecha_validacion`), `test_validar_guarda_evaluacion_y_limites` (pH en muestra Cloacal guarda `limite_min="7.01"`, `limite_max="10.0"`, norma, `origen_limites="cloacal"`), `test_fuera_de_norma_se_valida` (Cloruro 400 → `evaluacion="fuera_de_norma"`), `test_ultima_validacion_finaliza`, `test_con_pendientes_sigue_en_proceso`, `test_informe_emitido_rechaza` (`ValidarResultadosError`, nada cambia), `test_omite_ya_validada`, `test_omite_sin_resultado`, `test_omite_si_cambio` (valor visto distinto del vigente), `test_reenvio_no_cambia` (mismo envío dos veces: la segunda solo omite y no cambia quién ni cuándo), `test_ignora_asignaciones_ajenas` y `test_validacion_no_modifica_otros_datos` (resultado, medición, muestra, `Prueba`, `LimiteVertido` y otro estudio iguales) y `test_revalidar_conserva_anulada` (validar, corregir, volver a validar → dos `Validacion`: una anulada y una vigente).
- [X] T009 [P] [US1] Crear `estudios/tests/test_validar_resultados.py` (con `cliente_bioquimico`): `test_detalle_ofrece_validar` (y no lo ofrece sin pruebas Cargadas con resultado ni con informe emitido), `test_formulario_lista_y_marca_las_que_cumplen` (pH y E. coli Ausente marcadas; Cloruro 400 y Olor sin marcar; ocultos `resultado_<pk>`; aviso «Hay N resultados fuera de norma…»), `test_sin_resultados_estado_vacio`, `test_marcar_todas`, `test_revisar_sin_elegir_rechaza` («Elegí al menos un resultado para validar.»), `test_revisar_muestra_resumen` (singular/plural, «No cumplen: …», «El estudio quedará Finalizado.» cuando corresponde), `test_editar_conserva_seleccion`, `test_confirmar_valida_y_redirige` (mensajes «Se validaron …» / «Se validó 1 …» y «El estudio X quedó Finalizado.»), `test_confirmar_informa_omitidas`, `test_vista_informe_emitido_rechaza`, `test_accion_invalida`, `test_estudio_inexistente_404` y `test_error_de_base_al_validar` (parchear `estudios.servicios.validar_resultados` con `DatabaseError`: mensaje y nada validado).
- [X] T010 [P] [US1] Agregar `estudios/tests/test_concurrencia_validacion.py` (`pytest.mark.django_db(transaction=True)`, `threading.Barrier(2)`, como `test_concurrencia_mediciones.py`): `test_validaciones_concurrentes`: dos bioquímicos confirman la misma prueba a la vez → una sola `Validacion` y la otra llamada la informa como «ya estaba validada».

### Implementation for User Story 1

- [X] T011 [US1] Agregar en `estudios/servicios.py` `ValidarResultadosError`, el dataclass `ResultadoValidacion(validadas, omitidas, finalizado)` y `validar_resultados(estudio_pk, elegidas, usuario)` según research R6 y el contrato (sección «Servicio»): sesión activa y `usuario.has_perm("estudios.validar_resultados")` («Se requiere permiso para validar resultados.»); `atomic` + `select_for_update` del estudio («El estudio no está disponible.»; informe emitido → «El estudio ya tiene el informe emitido: sus resultados no se pueden validar.»); asignaciones elegidas del estudio con `select_for_update(of=("self",))`, `select_related("prueba", "resultado")`, `prefetch_related("prueba__limites_vertido")`, orden por código; omisiones «ya estaba validada», «ya no tenía resultado», «cambió mientras se revisaba»; `limites_aplicables(prueba, estudio.muestra.tipo_vertido)` + `evaluar(resultado.valor, ...)`; crear `Validacion` y `calculo.cambiar_estado(asignacion, COMPLETADA)`; si no queda ninguna asignación del estudio fuera de Completada → `Finalizado`. Agregar además en `estudios/tests/utiles.py` el helper `validar(estudio, usuario, *codigos)` que llama a `servicios.validar_resultados` con `{asignacion_de(estudio, c).pk: str(resultado.valor)}` (lo usan US1 y US2). Hace pasar T008 y T010.
- [X] T012 [US1] Agregar en `estudios/views.py` el helper `evaluar_asignaciones(estudio, asignaciones)` que adjunta a cada asignación con resultado `limites` y `evaluacion`: de su `Validacion` vigente (no anulada) si está Completada; si no, `limites_aplicables` + `evaluar` en vivo (research R7). Lo usan la validación (US1) y el detalle (US2).
- [X] T013 [US1] Agregar en `estudios/forms.py` `ValidarResultadosForm(data, filas, marcar_todas=False)` según research R5: por fila un `BooleanField` opcional `validar_<pk>` (inicial `True` solo si `evaluacion == Evaluacion.CUMPLE`, o siempre con `marcar_todas`) y un `CharField` oculto `resultado_<pk>` con `str(resultado.valor)`; `clean()` exige al menos una marcada («Elegí al menos un resultado para validar.»); `elegidas()` → `{pk: valor_visto}`; `filas()`, `resumen()` y `fuera_de_norma()` para los templates.
- [X] T014 [US1] Agregar la vista `validar_resultados` en `estudios/views.py` con `@permission_required("estudios.validar_resultados", raise_exception=True)` y la URL `<int:pk>/resultados/validar/` (`name="validar_resultados"`) en `estudios/urls.py`, con las acciones `revisar` / `editar` / `marcar_todas` / `confirmar` y los mensajes del contrato (informe emitido, acción inválida, éxito singular/plural, «El estudio X quedó Finalizado.», omitidas, `ValidarResultadosError`, `DatabaseError`). Al confirmar, el formulario usa las asignaciones de los `resultado_<pk>` del POST (para informar reenvíos), como la corrección.
- [X] T015 [P] [US1] Crear `estudios/templates/estudios/validar_resultados.html`: encabezado, aviso de fuera de norma, tabla **Validar / Código / Prueba / Resultado / Límite / Evaluación** (resultado con `|valor_medicion` y `|unidad`; evaluación con `ui/estado.html`), ocultos, botones **Revisar validación**, **Marcar todas** y **Cancelar**, y `ui/estado_vacio.html` sin pruebas para validar.
- [X] T016 [P] [US1] Crear `estudios/templates/estudios/validar_resultados_confirmar.html`: resumen «Se validarán N resultados en el estudio X (muestra PI Y).», tabla **Código / Prueba / Resultado / Límite / Evaluación**, aviso «No cumplen: …. Se validarán igual.», «El estudio quedará Finalizado.» si corresponde, ocultos y botones **Validar resultados** (`data-enviado`), **Volver a elegir** y **Cancelar**.
- [X] T017 [US1] En `estudios/views.py` (`detalle`) y `estudios/templates/estudios/detalle.html`, agregar el botón **Validar resultados** (`btn btn-primario`, ícono `check`) solo con `perms.estudios.validar_resultados`, `estudio.admite_correcciones` y alguna prueba Cargada con resultado. Hace pasar T009.

**Checkpoint**: un bioquímico valida un estudio completo y lo deja Finalizado; MVP entregable.

---

## Phase 4: User Story 2 - Ver si cada resultado cumple (Priority: P2)

**Goal**: el detalle muestra la evaluación de cada resultado apenas existe, con el límite aplicado, y la guardada para las validadas.

**Independent Test**: muestra de Agua con Cloruro 400 → el detalle lo muestra «Fuera de norma» sin validar.

### Tests for User Story 2 ⚠️ (escribir primero, deben fallar)

- [X] T018 [P] [US2] Agregar en `estudios/tests/test_consulta.py`: `test_detalle_muestra_evaluacion` (parametrizado: pH 7,4 → «Cumple» con «Límite: 6.4 a 8.5»; Cloruro 400 → «Fuera de norma» con `data-estado="danger"`; E. coli Presente → «Fuera de norma»; Sólidos sedimentables 0 → «Cumple»; Olor 2 → «Sin límite comparable» con «máx. SOE»; Cloro libre sin límites → «Sin límite en el catálogo»; muestra Cloacal con Cloro libre 0,3 → «Sin límite comparable» con «máx. NE»), `test_detalle_usa_limites_del_vertido` (muestra Cloacal con pH 7 → «Fuera de norma», «(Cloacal)»; muestra de Agua con pH 7 → «Cumple») y `test_detalle_validada_usa_lo_guardado` (validar Cloruro 300 con máx. 350; cambiar `Prueba.limite_max` a «250»; el detalle sigue «Cumple», con «máx. 350.0» y «Validada por …»).

### Implementation for User Story 2

- [X] T019 [US2] En la vista `detalle` (`estudios/views.py`), cargar `prefetch_related("prueba__limites_vertido")` y `Prefetch("validaciones", queryset=Validacion.objects.filter(anulada=False).select_related("validada_por"), to_attr="validaciones_vigentes")` y llamar a `evaluar_asignaciones` (T012).
- [X] T020 [US2] En `estudios/templates/estudios/detalle.html`, columna Resultado: etiqueta de evaluación (`ui/estado.html`), la línea «Límite: …» con norma y origen si no es general, «Sin límite en el catálogo» sin límites, y «Validada por <nombre o correo> · <d/m/Y H:i>» en las Completadas (contrato, sección detalle). Hace pasar T018.

**Checkpoint**: la evaluación se ve en el detalle antes y después de validar.

---

## Phase 5: User Story 3 - Habilitar a los bioquímicos (Priority: P3)

**Goal**: solo quien está en el grupo «Bioquímicos» (o tiene el permiso) ve la acción y puede validar; el administrador lo asigna desde el admin.

**Independent Test**: un empleado sin el grupo no ve el botón y recibe 403; agregado al grupo, valida.

### Tests for User Story 3 ⚠️ (escribir primero, deben fallar)

- [X] T021 [P] [US3] Agregar en `estudios/tests/test_validacion_permisos.py`: `test_sin_permiso_no_ve_ni_valida` (sin botón en el detalle; GET y POST a `validar_resultados` → 403; el servicio lanza `ValidarResultadosError` «Se requiere permiso para validar resultados.»; nada cambia), `test_bioquimico_ve_y_valida` (agregar el empleado al grupo desde el ORM → ve el botón y valida), `test_quien_cargo_puede_validar` (el mismo usuario carga y valida, sin doble control) y `test_validar_requiere_sesion` (sin sesión → 302 al login).

### Implementation for User Story 3

- [X] T022 [US3] Verificar que T011, T014 y T017 cubren T021 (decorador, revalidación en el servicio y `perms` en el template); corregir lo que falte. Comprobar en `/admin/` que el grupo «Bioquímicos» muestra «estudios | validación | Puede validar resultados» y que se puede agregar una persona desde Usuarios → Grupos.

**Checkpoint**: las tres historias funcionan y se prueban por separado.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T023 [P] Actualizar `CLAUDE.md`: nueva sección «Validación de resultados (US 6.4)» (invariante «una `Validacion` vigente ⇔ Completada»; al perderse se anula, nunca se borra, desde el único punto `calculo.cambiar_estado`; mostrar siempre la vigente; `pruebas/limites.py` como única interpretación de límites; permiso `estudios.validar_resultados` y grupo «Bioquímicos» por migración; Finalizado lo pone `validar_resultados`); quitar la nota «**Epic 6 (validación, US 6.4)**» de la sección de US 5.3/5.4 y reemplazar «**US 6.4:** convertir los límites…» de la sección SCRUM-64 por una referencia a `pruebas/limites.py`.
- [X] T024 [P] Ejecutar `docker compose exec web ruff check .`, `docker compose exec web ruff format --check .`, `docker compose exec web python manage.py makemigrations --check --dry-run` y recompilar Tailwind (`docker compose exec -u "$(id -u):$(id -g)" web tailwindcss -i static/src/aqualab.css -o static/css/aqualab.css --minify`): `git status` no debe mostrar cambios en `static/css/aqualab.css`.
- [X] T025 Ejecutar la suite completa `docker compose exec web pytest`: todo en verde.
- [ ] T026 Recorrer `specs/019-validar-resultados/quickstart.md` en el navegador (pasos 1 a 9) y marcar el resultado en esta lista.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: `T001`.
- **Foundational (Phase 2)**: depende de la fase 1. `T002` y `T004` en paralelo; `T002` → `T003`; `T004` → `T005` → `T006`; `T007` (fixtures) cuando exista el grupo (`T005`); el helper `validar` va en `T011`.
- **US1 (Phase 3)**: depende de la fase 2. Es el MVP.
- **US2 (Phase 4)**: depende de `T012` (helper de evaluación) y `T011` (para el test de lo guardado).
- **US3 (Phase 5)**: depende de US1 (vista, servicio y botón ya protegidos); sus tests se pueden escribir en paralelo a US2.
- **Polish (Phase 6)**: depende de las tres historias.

### Grafo

```text
T001 → T002 → T003 ─┐
       T004 → T005 → T006 ┴─→ T007
                               │
          ┌────────────────────┘
          ▼
US1: T008, T009, T010 → T011 → T012 → T013 → T014 → T015, T016 → T017
US2: T018 → T019 → T020
US3: T021 → T022
Polish: T023, T024 → T025 → T026
```

---

## Parallel Example: User Story 1

```bash
Task T008: "Tests del servicio en estudios/tests/test_servicio_validacion.py"
Task T009: "Tests de vistas en estudios/tests/test_validar_resultados.py"
Task T010: "Concurrencia en estudios/tests/test_concurrencia_validacion.py"
# Después de T014:
Task T015: "estudios/templates/estudios/validar_resultados.html"
Task T016: "estudios/templates/estudios/validar_resultados_confirmar.html"
```

## Parallel Example: Phase 2

```bash
Task T002: "Tests de límites en pruebas/tests/test_limites.py"
Task T004: "Modelo Validacion y migración 0007 en estudios/"
```

---

## Implementation Strategy

### En dos tandas (según `docs/guias/guia-sdd-paso-a-paso.md`)

1. **Tanda 1 (Fases 1 y 2 — `T001` a `T007`)**: aprobación, evaluación de límites con casos
   reales, modelo `Validacion` con su permiso y su grupo, y la pérdida de validación conectada al
   recálculo; suite en verde.
2. **Tanda 2 (Fases 3 a 6 — `T008` a `T026`)**: US1 (validar, MVP), US2 (evaluación en el
   detalle) y US3 (permisos), cada una con sus tests escritos primero; cerrar con `ruff`, CSS sin
   cambios, suite completa, recorrido manual y `CLAUDE.md`.
