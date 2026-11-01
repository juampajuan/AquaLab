---

description: "Lista de tareas de la US 7.2 – Generar informe"
---

# Tasks: Generar informe

**Input**: `specs/021-generar-informe/` (`plan.md`, `spec.md`, `research.md`, `data-model.md`,
`contracts/generar-informe-ui.md`, `quickstart.md`)

**Prerequisites**: `plan.md`, `spec.md` y `main` con la US 7.1 (PR #34): app `informes` con
`servicios.motivo_para_no_informar`, `comprobar_generacion`, `estudios_para_informar`, las vistas
`listar`, `control` y `generar` (POST que hoy avisa «próximamente»), `control.html` y sus tests; de
la US 6.4, `Validacion` vigente, `pruebas/limites.py` (`LimitesAplicables`, `limites_aplicables`,
`evaluar`), `views.texto_limite`, `views.validaciones_vigentes()` y el grupo «Bioquímicos»
(`estudios.0008`); del ajuste A/P, `texto_presencia` y el filtro `|valor_medicion`; fixtures
`empleado`, `cliente_http`, `estudio_de`, `catalogo`, `bioquimico`, `cliente_bioquimico` y helpers
`cargar`, `validar`, `asignacion_de` (los tests de `informes` importan `estudios/tests/conftest.py`).

**Tests**: SÍ. La constitution (principio III) exige un test por escenario de aceptación. Los tests
siguen el «Mapa de tests» de `plan.md` y se escriben **antes** de la implementación de cada historia
(deben fallar primero).

**Organization**: tres user stories — US1 (P1, previsualizar), US2 (P1, emitir) y US3 (P2, solo
emiten los bioquímicos).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: se puede ejecutar en paralelo (archivos distintos, sin dependencias pendientes)
- **[Story]**: user story a la que pertenece la tarea (`[US1]`, `[US2]`, `[US3]`)
- Rutas relativas a la raíz del repo

## Convenciones para todas las tareas

- Textos y mensajes en **español**, copiados **literalmente** de `contracts/generar-informe-ui.md`.
- Diseño de SCRUM-67 con `templates/ui/` (`ui/encabezado.html`, `.tarjeta`, `.tabla`,
  `ui/estado.html`, `aviso`); doble envío evitado con `data-enviado`. Evaluaciones: «Cumple» →
  `success`, «Fuera de norma» → `danger`, «Sin límite comparable» → `neutral`. Preferir clases ya
  usadas; si se agrega alguna, recompilar el CSS (T024).
- La vista `generar` llama a `servicios.emitir_informe` y los tests parchean
  `informes.servicios.emitir_informe`.
- Valores numéricos del informe siempre como texto de `Decimal` (nunca `float`).
- Permiso: `informes.emitir_informes` (`@permission_required(..., raise_exception=True)` en
  `generar`, revalidado en el servicio, `{% if perms.informes.emitir_informes %}` en templates).
- Commits a nombre de la responsable, sin `Co-Authored-By`.
- Comandos dentro de Docker: `docker compose exec web pytest informes estudios pruebas`,
  `docker compose exec web ruff check .`, `docker compose exec web ruff format --check .`.

---

## Phase 1: Setup (Shared Infrastructure)

- [ ] T001 **Gate de la constitution (principio I)**: confirmar que el equipo aprobó `specs/021-generar-informe/spec.md`, completar la clave de Jira en su **Input** y en **Assumptions → Trazabilidad**, y actualizar su `**Status**` a «Aprobada (fecha)». Confirmar que la rama `021-generar-informe` sale de `main` con la US 7.1 y ejecutar `docker compose exec web pytest` y `docker compose exec web python manage.py makemigrations --check --dry-run`: suite en verde y sin cambios pendientes.

---

## Phase 2: Foundational (Blocking Prerequisites)

**⚠️ CRITICAL**: ninguna historia empieza antes de terminar esta fase.

- [ ] T002 [P] Agregar en `pruebas/tests/test_limites.py`, a `test_evaluar`, un parámetro de límite de detección y los casos de FR-016: máx. «Ausente» con LD «0.1» y resultado 0.05 → cumple; 0.1 → fuera de norma; 0 → cumple; máx. «Ausencia» con LD «1.0» y 0.5 → cumple; máx. «Ausente» con LD «Ausente» (E. coli) y 1 → fuera de norma (LD no numérico no aplica); límites numéricos con LD no cambian (pH 7,4 cumple, Cloruro 400 fuera). En `test_limites_aplicables`, comprobar `deteccion` («0.1» para SS10 en `agua` y en `canal`: los límites por vertido no tienen detección propia). Y en `estudios/tests/test_servicio_validacion.py`: `test_validar_ausente_bajo_ld_cumple` (estudio con SS10 cargado en 0.05 → la `Validacion` guarda `evaluacion="cumple"`).
- [ ] T003 Implementar FR-016 en `pruebas/limites.py` según research R4 hasta que pase T002: `LimitesAplicables` suma «`deteccion: str = ""`» (último campo, con valor por defecto para no romper `estudios/views.py:evaluar_asignaciones`); `limites_aplicables` la completa con `prueba.limite_deteccion` en las dos ramas; `evaluar`, con límite `AUSENTE`: cumple si `valor == 0` o (`leer_limite(limites.deteccion)` es `Decimal` y `valor < deteccion`). Actualizar el docstring y la regla en `CLAUDE.md` (sección US 6.4).
- [ ] T004 [P] Agregar en `config/settings.py` `AQUALAB_LABORATORIO` según research R9: diccionario con `nombre`, `direccion`, `matricula`, `responsable_tecnico`, `telefono` y `correo`, todos de ejemplo y marcados «(DEMO)», con un comentario que diga que se reemplazan cuando el laboratorio los envíe (FR-006).
- [ ] T005 Crear `informes/models.py` con `Informe` de `data-model.md`: «`numero = PositiveIntegerField(unique=True, editable=False)`», «`estudio = OneToOneField(Estudio, on_delete=PROTECT, related_name="informe", editable=False)`», «`emitido_por = ForeignKey(AUTH_USER_MODEL, on_delete=PROTECT, related_name="informes_emitidos", editable=False)`», «`fecha_emision = DateTimeField(auto_now_add=True)`», «`contenido = JSONField(editable=False)`», `Meta.permissions = [("emitir_informes", "Puede emitir informes")]`, `ordering = ("-numero",)`, `verbose_name`/`verbose_name_plural`, `CheckConstraint(numero >= 1, name="informe_numero_positivo")`, propiedad `numero_mostrado` → `f"INF-{numero:06d}"` y `__str__`. Generar `informes/migrations/0001_initial.py` con `makemigrations`. Agregar `informes/tests/test_modelos.py`: `test_numero_mostrado` (1 → «INF-000001», 123 → «INF-000123»), `test_un_informe_por_estudio` (`IntegrityError`), `test_numero_unico` y `test_estudio_con_informe_protegido` (`ProtectedError`).
- [ ] T006 Crear `informes/migrations/0002_permiso_bioquimicos.py` (depende de `informes.0001` y `estudios.0008_grupo_bioquimicos`), con el mismo patrón que `estudios/migrations/0008_grupo_bioquimicos.py` (`create_permissions` con `models_module`): obtiene o crea el grupo «Bioquímicos» y le agrega `emitir_informes`; reversa que lo quita. Agregar `informes/tests/test_permisos.py` con `test_grupo_bioquimicos_puede_emitir` (ejecuta la función de la migración, como `estudios/tests/test_validacion_permisos.py`). En `estudios/tests/conftest.py`, el fixture `bioquimico` agrega también `Permission.objects.get(codename="emitir_informes")` al grupo.
- [ ] T007 [P] Crear `informes/tests/test_contenido.py` (con `estudio_de`, `cargar`, `validar`, `bioquimico`): `test_armar_contenido_datos` (laboratorio = `settings.AQUALAB_LABORATORIO`; cliente con nombre completo, documento, domicilio y correo; muestra con N° PI, nombre, origen, fechas «dd/mm/aaaa», sitio, responsable y tipo de vertido con su etiqueta; estudio con número y `tipo_nombre_snapshot`), `test_armar_contenido_pruebas` (pH 7.4 «7,4» cumple con «6.4 a 8.5»; Cloruro 40 → «400» fuera de norma con «máx. 350.0»; E. coli 0 → «Ausente»; SS10 0.05 → «< 0,1» cumple; orden por código), `test_armar_contenido_usa_la_validacion` (cambiar el límite del catálogo después de validar: el contenido usa el de la `Validacion`), `test_armar_contenido_sin_float` (ningún valor del diccionario es `float`) y `test_armar_contenido_vacios` (domicilio y responsable vacíos → `""`).
- [ ] T008 Crear `informes/contenido.py` con `armar_contenido(estudio)` según research R2/R3 y la estructura de `data-model.md` hasta que pase T007: asignaciones con `select_related("prueba", "resultado")` y `validaciones_vigentes()`; `resultado` = `str(resultado.valor)`; `resultado_texto` = `texto_presencia` en A/P, «< » + LD con coma si el LD es numérico y el resultado es menor, si no `valor_mostrado` con coma; `limite_texto` con `texto_limite` (mover `texto_limite` de `estudios/views.py` a `pruebas/limites.py` y usarlo en ambos lugares); evaluación y su etiqueta de la `Validacion` vigente.

**Checkpoint**: regla «< LD» ajustada, modelo `Informe` con su permiso en «Bioquímicos», datos institucionales y armado del contenido probados.

---

## Phase 3: User Story 1 - Previsualizar el informe (Priority: P1) 🎯 MVP

**Goal**: desde el control, cualquier empleado ve el informe completo como borrador, sin cambios.

**Independent Test**: estudio con pH 7,4 y Cloruro 400 mg/l validados → la vista previa muestra todos los datos y «BORRADOR», y el estudio sigue Finalizado.

### Tests for User Story 1 ⚠️ (escribir primero, deben fallar)

- [ ] T009 [P] [US1] Crear `informes/tests/test_vista_previa.py`: `test_vista_previa_muestra_documento` (encabezado institucional, cliente, muestra, estudio, tabla con resultado, unidad, límite, norma, evaluación, fila fuera de norma resaltada, «< 0,1», «Ausente», «BORRADOR» y el aviso «Vista previa: este informe todavía no fue emitido.»), `test_vista_previa_no_cambia_nada` (sin `Informe`, estado del estudio igual), `test_vista_previa_rechaza_no_listo` (parametrizado: prueba sin completar, informe ya emitido → 302 al control con el motivo de la US 7.1), `test_vista_previa_emitir_solo_con_permiso` (con `cliente_bioquimico` aparece el form a `informes:generar`; con `cliente_http` sin el grupo, no, y aparece «Solo un integrante del grupo Bioquímicos puede emitir el informe.») y `test_vista_previa_404`.

### Implementation for User Story 1

- [ ] T010 [P] [US1] Crear el parcial `informes/templates/informes/documento.html` según el contrato (secciones 1 a 6), que recibe `contenido` y opcionalmente `informe` (número, fecha y emitido por) o `borrador=True`; datos vacíos como «—».
- [ ] T011 [US1] Agregar la vista `vista_previa` en `informes/views.py`, la URL `estudios/<int:pk>/vista-previa/` (`name="vista_previa"`) en `informes/urls.py` y `informes/templates/informes/vista_previa.html` (aviso, documento con `borrador=True`, «Emitir informe» con `data-enviado` solo con permiso, «Volver al control»). Si `motivo_para_no_informar` no es `None` → 302 a `informes:control` con `messages.error(motivo)`. Hace pasar T009.
- [ ] T012 [US1] En `informes/templates/informes/control.html`, «Generar informe» (listo) pasa de form POST a enlace a `informes:vista_previa`. Ajustar `informes/tests/test_control.py` (el enlace reemplaza a la acción POST a `informes:generar`).

**Checkpoint**: la vista previa funciona sola (MVP de revisión).

---

## Phase 4: User Story 2 - Emitir el informe (Priority: P1)

**Goal**: un bioquímico emite: número correlativo, copia de los datos, estudio en «Informe generado» y enlaces «Ver informe».

**Independent Test**: emitir el estudio anterior → INF-000001, estudio en «Informe generado», el informe emitido igual a la vista previa.

### Tests for User Story 2 ⚠️ (escribir primero, deben fallar)

- [ ] T013 [P] [US2] Crear `informes/tests/test_servicio_emision.py`: `test_emitir_crea_informe_y_cambia_estado` (número 1, `emitido_por`, `fecha_emision`, `contenido == armar_contenido` del momento, estudio «Informe generado»), `test_numeracion_correlativa` (dos estudios → 1 y 2), `test_falla_no_deja_huecos` (parchear `armar_contenido` para que falle en una emisión: no queda informe ni cambio de estado y la siguiente recibe el número que correspondía), `test_emitir_revalida` (estudio con una prueba que deja de estar Completada → `InformeNoDisponible` con el motivo), `test_segundo_intento_rechaza` («El informe de este estudio ya fue generado.»), `test_estudio_inexistente` («El estudio no está disponible.»), `test_sin_permiso_rechaza` (`EmitirInformeError` «Se requiere permiso para emitir informes.») y `test_emision_no_modifica_otros_datos` (pruebas, mediciones, resultados, validaciones, muestra, cliente, catálogo y otro estudio iguales).
- [ ] T014 [P] [US2] Crear `informes/tests/test_emitir.py` (vista): `test_emitir_redirige_al_informe` (302 a `informes:ver` y mensaje «Se emitió el informe INF-000001 del estudio X.»), `test_emitir_no_listo_vuelve_al_control` (302 al control con el motivo), `test_sin_permiso_403`, `test_emitir_requiere_post` (GET → 405) y `test_error_de_base_al_emitir` (parchear `informes.servicios.emitir_informe` con `DatabaseError`: «No se pudo emitir el informe. Intentá nuevamente.»).
- [ ] T015 [P] [US2] Crear `informes/tests/test_ver.py`: `test_emitido_igual_a_vista_previa` (mismo bloque de datos y tabla; con número, fecha y «Emitido por …» y sin «BORRADOR»), `test_informe_no_cambia_al_editar` (después de emitir, cambiar domicilio del cliente y `limite_max` del Cloruro: el informe muestra los valores anteriores), `test_ver_sin_informe_404` y `test_control_y_detalle_ofrecen_ver_informe` (con informe, el control y `estudios:detalle` enlazan `informes:ver`; sin informe, no).
- [ ] T016 [P] [US2] Crear `informes/tests/test_concurrencia_emision.py` (`pytest.mark.django_db(transaction=True)`, `threading.Barrier(2)`, como `estudios/tests/test_concurrencia_validacion.py`): `test_emisiones_concurrentes` — dos bioquímicos emiten el mismo estudio a la vez → un solo `Informe` y la otra llamada recibe `InformeNoDisponible`.

### Implementation for User Story 2

- [ ] T017 [US2] En `informes/servicios.py`: extraer `estudio_listo_bloqueado(estudio_pk)` de `comprobar_generacion` (bloquea, revalida, lanza `InformeNoDisponible`; estudio inexistente → «El estudio no está disponible.») y hacer que `comprobar_generacion` lo use; agregar `EmitirInformeError`, `CLAVE_LOCK_NUMERO_INFORME = 7_200_001`, `siguiente_numero()` (máximo + 1, desde 1) y `emitir_informe(estudio_pk, usuario)` según research R6 (permiso → `atomic` → `estudio_listo_bloqueado` → `pg_advisory_xact_lock` → número → `armar_contenido` → `Informe.objects.create` → estudio `INFORME_GENERADO`). Hace pasar T013 y T016.
- [ ] T018 [US2] En `informes/views.py`, `generar` pasa a emitir: `@permission_required("informes.emitir_informes", raise_exception=True)` + `@require_POST`, llama a `servicios.emitir_informe` y maneja éxito, `InformeNoDisponible`, `EmitirInformeError` y `DatabaseError` como dice el contrato. Quitar el aviso «próximamente» y actualizar `informes/tests/test_generar.py` (el test `test_generar_listo_avisa_proximamente` pasa a comprobar la emisión; los de rechazo siguen igual con `cliente_bioquimico`).
- [ ] T019 [US2] Agregar la vista `ver` en `informes/views.py`, la URL `estudios/<int:pk>/informe/` (`name="ver"`) y `informes/templates/informes/ver.html` (documento desde `informe.contenido`, con número, fecha y emitido por; «Volver al control» y «Ver detalle del estudio»); 404 sin informe.
- [ ] T020 [US2] «Ver informe» (FR-017): en `informes/templates/informes/control.html` con informe emitido (reemplaza el aviso solo informativo) y en `estudios/templates/estudios/detalle.html` si el estudio tiene informe (`btn btn-secundario`, ícono `file-text`). Hace pasar T014 y T015.

**Checkpoint**: emisión completa y verificable de punta a punta.

---

## Phase 5: User Story 3 - Solo emiten los bioquímicos (Priority: P2)

**Goal**: solo quien tiene «Puede emitir informes» emite; el resto ve la vista previa sin la acción.

**Independent Test**: empleado sin el grupo → vista previa sin «Emitir informe» y POST 403; agregado al grupo, emite.

### Tests for User Story 3 ⚠️ (escribir primero, deben fallar)

- [ ] T021 [P] [US3] Agregar en `informes/tests/test_permisos.py`: `test_sin_permiso_no_emite` (vista previa sin el form de emisión; POST 403; servicio rechaza; sin `Informe`) y `test_agregado_al_grupo_emite` (agregar al grupo desde el ORM → emite).

### Implementation for User Story 3

- [ ] T022 [US3] Verificar que T011, T017 y T018 cubren T021 (decorador, revalidación en el servicio y `perms` en el template); corregir lo que falte. Comprobar en `/admin/` que «Bioquímicos» muestra «informes | informe | Puede emitir informes».

**Checkpoint**: las tres historias funcionan y se prueban por separado.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [ ] T023 [P] Actualizar `CLAUDE.md`: nueva sección «Generar informe (US 7.2)» (`armar_contenido` único para vista previa y emitido; copia en `Informe.contenido`, todo texto; numeración con `pg_advisory_xact_lock(7_200_001)`; `emitir_informe` dentro de `estudio_listo_bloqueado`; permiso `informes.emitir_informes` en «Bioquímicos» por migración; datos institucionales en `settings.AQUALAB_LABORATORIO`; «< LD» con límite «Ausente» cumple) y reemplazar la nota «**US 7.2:** crear el informe…» de la sección de la US 7.1 por una referencia a la nueva sección.
- [ ] T024 [P] Ejecutar `docker compose exec web ruff check .`, `docker compose exec web ruff format --check .`, `docker compose exec web python manage.py makemigrations --check --dry-run` y recompilar Tailwind (`docker compose exec -u "$(id -u):$(id -g)" web tailwindcss -i static/src/aqualab.css -o static/css/aqualab.css --minify`); si `static/css/aqualab.css` cambia, commitearlo.
- [ ] T025 Ejecutar la suite completa `docker compose exec web pytest`: todo en verde.
- [ ] T026 Recorrer `specs/021-generar-informe/quickstart.md` en el navegador (pasos 1 a 8) y marcar el resultado en esta lista.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: `T001`.
- **Foundational (Phase 2)**: depende de la fase 1. `T002`, `T004` y `T005` en paralelo; `T002` → `T003`; `T005` → `T006`; `T007` (tests) cuando existan `T003` y `T004`; `T007` → `T008`.
- **US1 (Phase 3)**: depende de la fase 2. MVP de revisión.
- **US2 (Phase 4)**: depende de US1 (usa el documento y la vista previa).
- **US3 (Phase 5)**: depende de US1 y US2 (vista previa y emisión ya protegidas); sus tests se pueden escribir en paralelo a US2.
- **Polish (Phase 6)**: depende de las tres historias.

### Grafo

```text
T001 → T002 → T003 ─┐
       T004 ────────┼→ T007 → T008
       T005 → T006 ─┘          │
          ┌────────────────────┘
          ▼
US1: T009 → T010, T011 → T012
US2: T013, T014, T015, T016 → T017 → T018 → T019 → T020
US3: T021 → T022
Polish: T023, T024 → T025 → T026
```

---

## Parallel Example: User Story 2

```bash
Task T013: "Tests del servicio en informes/tests/test_servicio_emision.py"
Task T014: "Tests de la vista en informes/tests/test_emitir.py"
Task T015: "Tests del informe emitido en informes/tests/test_ver.py"
Task T016: "Concurrencia en informes/tests/test_concurrencia_emision.py"
```

## Parallel Example: Phase 2

```bash
Task T002: "Casos FR-016 en pruebas/tests/test_limites.py"
Task T004: "AQUALAB_LABORATORIO en config/settings.py"
Task T005: "Modelo Informe y migración 0001 en informes/"
```

---

## Implementation Strategy

### En dos tandas (según `docs/guias/guia-sdd-paso-a-paso.md`)

1. **Tanda 1 (Fases 1 y 2 — `T001` a `T008`)**: aprobación, regla «< LD», modelo `Informe` con su
   permiso, datos institucionales y armado del contenido; suite en verde.
2. **Tanda 2 (Fases 3 a 6 — `T009` a `T026`)**: US1 (vista previa), US2 (emisión, numeración y
   «Ver informe») y US3 (permisos), cada una con sus tests escritos primero; cerrar con `ruff`, CSS,
   suite completa, recorrido manual y `CLAUDE.md`.
