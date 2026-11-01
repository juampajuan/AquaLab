---

description: "Lista de tareas de la US 7.1 – Seleccionar estudio y controlar pruebas pendientes"
---

# Tasks: Seleccionar estudio y controlar pruebas pendientes

**Input**: `specs/020-controlar-pruebas-pendientes/` (`plan.md`, `spec.md`, `research.md`,
`data-model.md`, `contracts/control-informe-ui.md`, `quickstart.md`)

**Prerequisites**: `plan.md`, `spec.md`; en `main`: `Estudio`, `PruebaEstudio`, `EstadoEstudio`,
`EstadoPruebaEstudio` (US 5.2), `BuscarEstudioForm` y la vista `estudios.views.buscar`, el filtro
`tipo_estado` (`config/ui.py`), los componentes de `templates/ui/`; fixtures `empleado`,
`cliente_a`, `muestra`, `catalogo`, `estudio_de`, `cliente_http` (`estudios/tests/conftest.py`) y
el helper `asignacion_de` (`estudios/tests/utiles.py`).

**Tests**: SÍ (constitution, principio III). Siguen el «Mapa de tests» de `plan.md` y se escriben
**antes** de la implementación de cada historia.

**Organization**: US1 (P1, seleccionar el estudio) y US2 (P1, controlar las pruebas y habilitar la
generación). La regla compartida va en la fase Foundational.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: se puede ejecutar en paralelo (archivos distintos, sin dependencias pendientes)
- **[Story]**: user story a la que pertenece la tarea
- Rutas relativas a la raíz del repo

## Convenciones para todas las tareas

- Textos y mensajes copiados **literalmente** de `contracts/control-informe-ui.md` y
  `data-model.md`.
- **Sin modelos ni migraciones** (data-model.md). `makemigrations --check` debe seguir limpio.
- Los tests ponen las pruebas en Completada con
  `PruebaEstudio.objects.filter(...).update(estado=EstadoPruebaEstudio.COMPLETADA)` y el informe
  emitido con `Estudio.objects.filter(pk=...).update(estado=EstadoEstudio.INFORME_GENERADO)`: `estado` es
  `editable=False` y US 7.2 no existe. Con US 6.4 ya en `main`, `test_flujo_con_validacion_real`
  (`informes/tests/test_control.py`) recorre el caso con `validar` y `corregir_mediciones` reales.
- Comandos dentro de Docker: `docker compose exec web pytest informes estudios`,
  `docker compose exec web ruff check .`, `docker compose exec web ruff format --check .`.

---

## Phase 1: Setup (Shared Infrastructure)

- [X] T001 **Gate de la constitution (principio I)**: confirmar que el equipo aprobó `specs/020-controlar-pruebas-pendientes/spec.md`, actualizar su `**Status**` a «Aprobada (fecha)» y, si se conoce, poner la clave de Jira en Supuestos. Ejecutar `docker compose exec web pytest` y `docker compose exec web python manage.py makemigrations --check --dry-run`: suite en verde y sin cambios.
- [X] T002 Crear la app `informes` sin modelos: `informes/__init__.py`, `informes/apps.py` (`InformesConfig`, `name = "informes"`, `verbose_name = "Informes"`), `informes/urls.py` con `app_name = "informes"` y `urlpatterns = []`, `informes/tests/__init__.py`; sumar `"informes"` al final de `INSTALLED_APPS` en `config/settings.py` y `path("informes/", include("informes.urls"))` en `config/urls.py` antes de la ruta de inicio.
- [X] T003 [P] Crear `informes/tests/conftest.py` que importe las fixtures de `estudios/tests/conftest.py` (`from estudios.tests.conftest import *  # noqa: F401,F403`), más una fixture `completar(estudio, *codigos)` que pase a Completada las asignaciones de esos códigos (todas si no se indican).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: la búsqueda compartida y la regla única de habilitación, que usan las dos historias.

- [X] T004 Extraer la búsqueda (research R4): crear `estudios/busqueda.py` con `filtro_busqueda(q) -> Q` que contenga **exactamente** la construcción del filtro de `estudios.views.buscar` (muestra, cliente, razón social, tipo con `unaccent__icontains`; número de estudio y N° PI si `q` es dígitos ASCII, con el tope `MAX_NUMERO_PI_SQL`; documento normalizado de 4 o más dígitos) y mover ahí `MAX_NUMERO_PI_SQL`. `estudios.views.buscar` pasa a usar `qs.filter(filtro_busqueda(q))`. `docker compose exec web pytest estudios/tests/test_consulta.py` sigue en verde.
- [X] T005 [P] Tests de la regla en `informes/tests/test_servicios.py`:
  - `test_motivo_para_no_informar` parametrizado sobre las filas de la tabla de `data-model.md`: informe emitido → «El informe de este estudio ya fue generado.»; sin asignaciones → «El estudio no tiene pruebas.»; 1 de 2 Completadas → «Hay 1 prueba sin completar.»; 0 de 3 → «Hay 3 pruebas sin completar.»; todas Completadas → `None`. Para «sin pruebas» basta con `estudio.pruebas_asignadas.all().delete()` en el test.
  - `test_cargadas_cuentan_como_sin_completar`: una Cargada y el resto Completadas → «Hay 1 prueba sin completar.».
  - `test_comprobar_generacion_ok` y `test_comprobar_generacion_rechaza`: devuelve el `Estudio` si está listo; si no, lanza `InformeNoDisponible` con el mismo texto que `motivo_para_no_informar`.
  - `test_comprobar_generacion_bloquea_estudio`: con `CaptureQueriesContext(connection)`, verificar que alguna consulta sobre `estudios_estudio` contiene `FOR UPDATE`.
- [X] T006 Implementar en `informes/servicios.py` (contrato «Servicio»):
  - `class InformeNoDisponible(Exception)`.
  - `motivo_para_no_informar(estudio, asignaciones) -> str | None`, con el orden de condiciones de `data-model.md` y el plural «Hay N pruebas sin completar.» / singular «Hay 1 prueba sin completar.».
  - `comprobar_generacion(estudio_pk) -> Estudio`: `transaction.atomic()`, `Estudio.objects.select_for_update().get(pk=estudio_pk)`, relee `estudio.pruebas_asignadas.all()` y lanza `InformeNoDisponible(motivo)` si hay motivo. Docstring: US 7.2 crea el informe dentro de esta misma transacción.

**Checkpoint**: T005 en verde.

---

## Phase 3: User Story 1 - Seleccionar el estudio a informar (Priority: P1) 🎯 MVP

**Goal**: sección «Informes» con el listado buscable de estudios, su estado, su avance y el filtro
«Solo listos para informar»; seleccionar abre el control.

**Independent Test**: con un estudio Finalizado (todas Completadas), uno En proceso y uno con
informe emitido, buscar cada uno por N° PI, ver estado y avance, y que «Solo listos» deja solo el
primero.

### Tests for User Story 1 ⚠️ (escribir primero, deben fallar)

- [X] T007 [P] [US1] Tests del servicio en `informes/tests/test_servicios.py`:
  - `test_estudios_para_informar_anota_avance`: un estudio de 3 pruebas con 1 Completada → `total_pruebas == 3`, `pruebas_completadas == 1`.
  - `test_filtro_listos_coincide_con_la_regla`: con los cinco casos de T005, `estudios_para_informar("", solo_listos=True)` devuelve exactamente los estudios con `motivo_para_no_informar(...) is None`.
- [X] T008 [P] [US1] Tests de la vista en `informes/tests/test_listar.py`:
  - `test_listado_muestra_estado_y_avance`: GET `informes:listar` → 200, cada estudio con N° de estudio, N° PI, cliente, tipo (snapshot), etiqueta de estado y «N de M pruebas completadas», y enlace «Seleccionar» a `informes:control`.
  - `test_listado_ordenado_y_paginado`: 21 estudios → la primera página tiene 20, del `pk` mayor al menor; `?page=2` tiene 1.
  - `test_busqueda_por_numero_pi_cliente_y_tipo` parametrizado (N° PI, número de estudio, nombre de cliente, razón social, documento del cliente con 4 o más dígitos, nombre de muestra, nombre de tipo) → solo el estudio que coincide.
  - `test_busqueda_sin_resultados`: `?q=zzz` → «No se encontraron estudios».
  - `test_busqueda_demasiado_larga`: `q` de 101 caracteres → «Ingresá como máximo 100 caracteres para buscar.».
  - `test_filtro_solo_listos`: `?listos=1` → solo el estudio con todas Completadas y sin informe; la casilla aparece marcada y la paginación conserva `listos=1` y `q`.
  - `test_menu_e_inicio_enlazan_informes`: GET `inicio` contiene `reverse("informes:listar")` en el menú (sección «Informes») y en un acceso rápido; en `informes:listar` el ítem del menú tiene `aria-current="page"`.
  - `test_listado_requiere_sesion`: cliente anónimo → redirige al login.

### Implementation for User Story 1

- [X] T009 [US1] En `informes/servicios.py`, `estudios_para_informar(q, solo_listos)`: `Estudio.objects.select_related("muestra", "muestra__cliente", "muestra__origen")`, `.annotate(total_pruebas=Count("pruebas_asignadas", distinct=True), pruebas_completadas=Count("pruebas_asignadas", filter=Q(pruebas_asignadas__estado=EstadoPruebaEstudio.COMPLETADA), distinct=True))`, filtro `filtro_busqueda(q)` si `q`, y si `solo_listos`: `total_pruebas__gt=0`, `pruebas_completadas=F("total_pruebas")`, `estado` distinto de `INFORME_GENERADO`; orden `Estudio._meta.ordering`. Comentario: las tres condiciones son las de `motivo_para_no_informar`.
- [X] T010 [US1] En `informes/views.py`, `listar(request)`: `BuscarEstudioForm(request.GET or None)`, `solo_listos = request.GET.get("listos") == "1"`, `Paginator(..., RESULTADOS_POR_PAGINA)` (importar la constante de `estudios.views`); contexto `form`, `page_obj`, `q`, `solo_listos` y `parametros = urlencode({"q": q} | ({"listos": "1"} if solo_listos else {}))` (querystring sin `page` que espera `ui/paginacion.html`). Ruta `path("", views.listar, name="listar")` en `informes/urls.py`; registrar también `path("estudios/<int:pk>/", views.control, name="control")` con una vista `control` provisoria (`HttpResponse` vacía) que T015 reemplaza, para que el template del listado pueda resolver el enlace.
- [X] T011 [US1] Template `informes/templates/informes/listar.html` según el contrato `GET /informes/`: encabezado con `ui/encabezado.html` (sección «Informes», título «Seleccionar estudio a informar»), formulario GET con el campo `q` (como `estudios/buscar.html`) y la casilla «Solo listos para informar» (`name="listos" value="1"`), tabla con estado vía `ui/estado.html` + `tipo_estado`, avance, «Seleccionar»; vacío con `ui/estado_vacio.html` («No se encontraron estudios»); paginación con `{% include "ui/paginacion.html" with parametros=parametros %}` para conservar `q` y `listos`.
- [X] T012 [P] [US1] Navegación: en `templates/ui/menu.html`, sección «Informes» (icono existente en `templates/ui/iconos/`, por ejemplo `file-text`) con el ítem «Seleccionar estudio», activo en `informes:listar` e `informes:control`; en `templates/inicio.html`, acceso rápido «Informes» («Controlá que las pruebas de un estudio estén completas antes de emitir su informe.», enlace «Seleccionar»).

**Checkpoint**: T007–T008 en verde. El enlace «Seleccionar» usa `{% url 'informes:control' %}`: hasta T015, T011 lo arma con la ruta registrada en T010 (ver abajo).

---

## Phase 4: User Story 2 - Controlar las pruebas pendientes y habilitar la generación (Priority: P1)

**Goal**: el control del estudio lista todas sus pruebas con estado, marca las que bloquean, y
«Generar informe» se habilita solo con el 100% Completadas; el POST revalida y rechaza.

**Independent Test**: estudio de 3 pruebas (2 Completadas, 1 Cargada) → «Hay 1 prueba sin
completar.», la Cargada con «Sin validar», botón deshabilitado; completar la que falta → habilitado.

### Tests for User Story 2 ⚠️ (escribir primero, deben fallar)

- [X] T013 [P] [US2] Tests en `informes/tests/test_control.py`:
  - `test_control_muestra_ficha_y_pruebas`: N° PI, muestra, cliente, `tipo_nombre_snapshot`, estado del estudio, y una fila por cada asignación (código, nombre, estado) ordenadas por código; «N de M pruebas completadas».
  - `test_control_marca_incompletas_y_sin_validar`: una Pendiente con «Incompleta», una Cargada (cargar con `cargar` de `estudios/tests/utiles.py`) con «Sin validar», una Completada sin etiqueta; aviso «Hay 2 pruebas sin completar.».
  - `test_boton_deshabilitado_con_pruebas_sin_completar`: `<button` con `disabled` y `aria-describedby="motivo-bloqueo"`; no hay `<form` con `action` a `informes:generar`.
  - `test_boton_habilitado_con_todas_completadas`: aviso «El estudio está listo para informar: todas sus pruebas están completadas.» y `<form method="post"` con `action` a `informes:generar` y `csrfmiddlewaretoken`.
  - `test_control_con_informe_emitido`: aviso «El informe de este estudio ya fue generado.» y ningún botón «Generar informe».
  - `test_control_muestra_motivo_sin_resultado`: `estudio_de("CA", "DUREZA-T", "MG")` con solo DUREZA-T cargada → MG figura «Incompleta» con el mismo texto de `calculo.motivo_sin_resultado` que muestra `estudios:detalle`.
  - `test_control_estudio_inexistente_404`.
  - `test_consultar_no_modifica`: valores de `estado` de estudio y asignaciones y conteo de `Medicion` iguales antes y después del GET del listado y del control.
  - `test_control_y_detalle_muestran_el_mismo_estado`: para cada asignación, el texto `get_estado_display` aparece en el control y en `estudios:detalle`.
  - `test_seleccionar_abre_control` (en `informes/tests/test_listar.py`): seguir el enlace «Seleccionar» del listado → 200 en `informes:control` del estudio.
  - `test_detalle_enlaza_control`: `estudios:detalle` contiene «Controlar para informe» con `reverse("informes:control", args=[pk])`.
- [X] T014 [P] [US2] Tests en `informes/tests/test_generar.py`:
  - `test_generar_rechaza_si_hay_pruebas_sin_completar`: POST → 302 a `informes:control` con el mensaje de error «Hay N pruebas sin completar.»; estados sin cambios.
  - `test_generar_revalida_con_datos_vigentes`: GET del control con todas Completadas (botón habilitado), luego pasar una a Cargada y POST → rechazado con «Hay 1 prueba sin completar.».
  - `test_generar_listo_avisa_proximamente`: todas Completadas → mensaje informativo «La generación del informe estará disponible próximamente.» y el estudio sin cambios.
  - `test_generar_con_informe_emitido_rechaza`: «El informe de este estudio ya fue generado.».
  - `test_generar_solo_post`: GET → 405.
  - `test_generar_estudio_inexistente_404`.
  - `test_generar_error_de_base`: con `comprobar_generacion` parcheado (`informes.servicios.comprobar_generacion`) para lanzar `DatabaseError` → «No se pudo verificar el estudio. Intentá nuevamente.».

### Implementation for User Story 2

- [X] T015 [US2] En `informes/views.py`, `control(request, pk)`: `get_object_or_404` con `select_related("muestra", "muestra__cliente", "muestra__origen")`; asignaciones `select_related("prueba").order_by("prueba__codigo", "pk")`; a cada asignación, `motivo_sin_resultado = calculo.motivo_sin_resultado(asignacion, todas)` con `todas = {a.prueba.codigo: a for a in asignaciones}` (igual que `estudios.views.detalle`, sin modificarla; el `select_related` suma `"medicion"` y `"resultado"`); `motivo = servicios.motivo_para_no_informar(estudio, asignaciones)`; contexto con `estudio`, `asignaciones`, `total_pruebas`, `pruebas_completadas`, `motivo`, `listo = motivo is None`, `informe_emitido = estudio.estado == EstadoEstudio.INFORME_GENERADO`. Ruta `path("estudios/<int:pk>/", views.control, name="control")`.
- [X] T016 [US2] En `informes/views.py`, `generar(request, pk)` con `@require_POST`: `get_object_or_404(Estudio, pk=pk)`; `servicios.comprobar_generacion(pk)` (llamar vía el módulo `servicios` para que el parche de T014 funcione); `InformeNoDisponible` → `messages.error(str(exc))`; `DatabaseError` → «No se pudo verificar el estudio. Intentá nuevamente.»; si pasa → `messages.info("La generación del informe estará disponible próximamente.")` con un comentario `# US 7.2: generar el informe acá.`; siempre `redirect("informes:control", pk=pk)`. Ruta `path("estudios/<int:pk>/generar/", views.generar, name="generar")`.
- [X] T017 [US2] Template `informes/templates/informes/control.html` según el contrato `GET /informes/estudios/<pk>/`: encabezado «Controlar pruebas del estudio N» con «Volver al listado» y «Ver detalle del estudio»; ficha con `ui/dato.html`; resumen «N de M pruebas completadas»; tabla con `ui/estado.html` + `tipo_estado` y la etiqueta «Incompleta» o «Sin validar» con el mismo componente y `tipo="warning"` en ambas (research R6), más `asignacion.motivo_sin_resultado` en texto chico si lo hay, como en `estudios/detalle.html`; aviso de éxito, advertencia o información según el caso (clases de `ui/mensajes.html`) con `id="motivo-bloqueo"` en el de advertencia; botón según el contrato (habilitado en `<form method="post">` con `{% csrf_token %}`, deshabilitado con `disabled aria-describedby="motivo-bloqueo"`, ausente con informe emitido).
- [X] T018 [P] [US2] En `estudios/templates/estudios/detalle.html`, enlace secundario «Controlar para informe» a `{% url 'informes:control' estudio.pk %}` junto a las acciones del encabezado.

**Checkpoint**: toda la suite de `informes` en verde.

---

## Phase 5: Polish & Cross-Cutting Concerns

- [X] T019 [P] Agregar en `CLAUDE.md` la sección «Control previo al informe (US 7.1)»: la app `informes`; `motivo_para_no_informar` es la única regla para informar (control, `comprobar_generacion` y, en SQL, `estudios_para_informar(solo_listos=True)`; un test compara ambas); **US 7.2** debe generar dentro de `comprobar_generacion` (estudio bloqueado) y reemplazar el aviso «próximamente» de `informes.views.generar`; `estudios/busqueda.py:filtro_busqueda` es la única búsqueda de estudios.
- [X] T020 Ejecutar `docker compose exec web pytest`, `docker compose exec web ruff check .`, `docker compose exec web ruff format --check .` y `docker compose exec web python manage.py makemigrations --check --dry-run`; anotar el resultado en este archivo.
  - **Resultado (2026-11-01, rebasado sobre `main` con US 6.4)**: `pytest` → **1101 passed** (45 de `informes`); `ruff check` y `ruff format --check` sin errores; `makemigrations --check` → «No changes detected».
- [ ] T021 Recorrido manual de `quickstart.md` (pasos 1–6) en el navegador; anotar lo observado y los ajustes.

---

## Dependencies & Execution Order

- **Setup (T001–T003)** → **Foundational (T004–T006)** → **US1 (T007–T012)** y **US2 (T013–T018)** → **Polish (T019–T021)**.
- US1 y US2 son independientes: la ruta `informes:control` se registra en T010 con una vista provisoria, y los tests que recorren listado → control (`test_seleccionar_abre_control`) están en US2.
- Dentro de cada historia: tests → servicio → vista → template.

## Parallel Opportunities

- T003 junto con T002 (después de crear el paquete `informes/tests/`).
- T005 en paralelo con T004.
- US1: T007, T008 y T012 en paralelo; T009 → T010 → T011 en orden.
- US2: T013, T014 y T018 en paralelo; T015 → T016 → T017.
- T019 en paralelo con T020.

## Implementation Strategy

1. **MVP**: Setup + Foundational + US1 → ya se puede elegir el estudio y ver cuáles están listos.
2. **Entrega completa**: US2 → control, botón habilitado/bloqueado y rechazo en el servidor.
3. Dos tandas de `/speckit-implement`, como recomienda la guía: (a) T001–T012, (b) T013–T021.
