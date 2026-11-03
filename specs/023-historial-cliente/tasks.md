---

description: "Lista de tareas de la US 3.3 – Consultar historial del cliente"
---

# Tasks: Consultar historial del cliente

**Input**: `specs/023-historial-cliente/` (`plan.md`, `spec.md`, `research.md`, `data-model.md`,
`contracts/historial-cliente-ui.md`, `quickstart.md`)

**Prerequisites**: `plan.md`, `spec.md` y `main` con la US 7.2 (PR #35): `informes.Informe`
(OneToOne `estudio` con `related_name="informe"`, `numero_mostrado`) y la vista `informes:ver`
(`/informes/estudios/<pk>/informe/`); de la US 3.2, `clientes.views.detalle` con
`MENSAJE_NO_DISPONIBLE` y `clientes/detalle.html`; de la US 5.2, `estudios:detalle`,
`muestras:detalle` y `EstadoEstudio`; `muestras.forms.SelectorFecha`; el filtro
`config/ui.py:tipo_estado`; los componentes `ui/encabezado.html`, `ui/estado.html`,
`ui/estado_vacio.html`, `ui/paginacion.html`, `ui/campo.html`, `ui/errores_form.html`; fixtures
`empleado`, `cliente_autenticado` y `cliente_existente` de `clientes/tests/conftest.py`.

**Tests**: SÍ. La constitution (principio III) exige un test por escenario de aceptación. Los tests
siguen el «Mapa de tests» de `plan.md` y se escriben **antes** de la implementación de cada historia
(deben fallar primero).

**Organization**: tres user stories — US1 (P1, ver el historial), US2 (P2, filtrar por fechas y
estado) y US3 (P2, ir al detalle del estudio, de la muestra o al informe).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: se puede ejecutar en paralelo (archivos distintos, sin dependencias pendientes)
- **[Story]**: user story a la que pertenece la tarea (`[US1]`, `[US2]`, `[US3]`)
- Rutas relativas a la raíz del repo

## Convenciones para todas las tareas

- Textos y mensajes en **español**, copiados **literalmente** de `contracts/historial-cliente-ui.md`.
- Diseño de SCRUM-67 con `templates/ui/` (`.tarjeta`, `.tabla`, `btn btn-primario`,
  `btn btn-secundario`); el estado del estudio siempre con
  `{% include "ui/estado.html" with estado=estudio.get_estado_display tipo=estudio.estado|tipo_estado %}`.
  Preferir clases ya usadas; si se agrega alguna, recompilar el CSS (T018).
- Pantalla de **solo lectura**: ningún POST, ninguna escritura (FR-013).
- Tipo de estudio siempre con `tipo_nombre_snapshot` (nunca `estudio.tipo.nombre`).
- Imports de `muestras`, `estudios` e `informes` solo en `clientes/historial.py`, `clientes/views.py`,
  `clientes/forms.py` y los tests; **nunca** en `clientes/models.py` (evita ciclos).
- Commits en Conventional Commits en español: `feat(clientes): US 3.3 – Consultar historial del cliente`.
- Comandos dentro de Docker: `docker compose exec web pytest clientes`,
  `docker compose exec web ruff check .`, `docker compose exec web ruff format --check .`.

---

## Phase 1: Setup (Shared Infrastructure)

- [ ] T001 *(Suite base en verde —1152 tests— y `makemigrations --check` sin cambios el 2026-11-02. Implementación iniciada a pedido del autor antes de la aprobación formal; responsable (Manuelklly) y clave de Jira (SCRUM-46) cargados; falta la aprobación del equipo.)* **Gate de la constitution (principio I)**: confirmar que el equipo aprobó `specs/023-historial-cliente/spec.md`, completar la clave de Jira en su **Input** y en **Assumptions → Trazabilidad** (y el responsable) y actualizar su `**Status**` a «Aprobada (fecha)». Confirmar que la rama `023-historial-cliente` sale de `main` con la US 7.2 y ejecutar `docker compose exec web pytest` y `docker compose exec web python manage.py makemigrations --check --dry-run`: suite en verde y sin cambios pendientes.

---

## Phase 2: Foundational (Blocking Prerequisites)

**⚠️ CRITICAL**: ninguna historia empieza antes de terminar esta fase.

- [X] T002 [P] Agregar en `clientes/tests/conftest.py` dos fixtures fábrica para los tests del historial: `muestra_de(cliente, fecha_ingreso, numero_pi, origen="Pozo 1")` crea (o reutiliza por nombre) el `Origen` del cliente y la `Muestra` con `fecha_muestreo=fecha_ingreso`, `sitio_extraccion="Sitio test"`, `registrada_por=empleado`; `estudio_en(muestra, estado=EstadoEstudio.PENDIENTE_ANALISIS, tipo="Agua de red", con_informe=False)` crea un `TipoEstudio` y un `Estudio` directo (`creado_por=empleado`, `tipo_nombre_snapshot=tipo`, `tipo_version_snapshot=1`, `clave_idempotencia=uuid4()`), le fija el estado con `Estudio.objects.filter(pk=...).update(estado=estado)` (el campo es `editable=False`) y, con `con_informe=True`, deja el estado en `INFORME_GENERADO` y crea `Informe(numero=<siguiente>, estudio=..., emitido_por=empleado, contenido={})` como en `informes/tests/test_modelos.py`. Devolver el estudio recargado de la base.
- [X] T003 Crear `clientes/tests/test_historial_consulta.py` (sin HTTP) con los tests de `clientes.historial.muestras_del_historial(cliente)` sin filtros: `test_solo_muestras_del_cliente` (otro cliente con una muestra no aparece; SC-003), `test_orden_del_historial` (ingresos 15/09, 10/10, 25/10 → 25/10, 10/10, 15/09; dos muestras el mismo día → primero el N° PI mayor; estudios de una muestra por `-pk`; FR-005), `test_trae_estudios_e_informe` (cada muestra expone `estudios_historial`; una sin estudios → `[]`; el estudio con informe trae `estudio.informe.numero_mostrado` sin consulta extra, usando `django_assert_num_queries(0)` al leerlo) y `test_sin_informe_no_consulta` (un estudio sin informe: evaluar `{% if estudio.informe %}` con `django.template.Template` no hace consultas). Estos tests no usan HTTP.
- [X] T004 Crear `clientes/historial.py` con `muestras_del_historial(cliente, desde=None, hasta=None, estado="")` según `data-model.md` y research R2, R3 y R5 hasta que pase T003: «`Muestra.objects.filter(cliente=cliente)`», filtros «`fecha_ingreso__gte=desde`» / «`fecha_ingreso__lte=hasta`» si vienen, con `estado` «`estudios__estado=estado`» + `.distinct()`, `.select_related("origen")`, «`Prefetch("estudios", queryset=Estudio.objects[.filter(estado=estado)].select_related("informe").order_by("-pk"), to_attr="estudios_historial")`» y «`.order_by("-fecha_ingreso", "-numero_pi")`». Docstring que diga que es la única consulta del historial (US 3.3) y que no modifica nada.

**Checkpoint**: la consulta del historial (orden, pertenencia, estudios e informe prefetcheados) está probada sin vistas.

---

## Phase 3: User Story 1 - Ver el historial del cliente (Priority: P1) 🎯 MVP

**Goal**: desde la ficha del cliente, el empleado ve todas sus muestras, de la más reciente a la más antigua, con sus estudios y estados.

**Independent Test**: cliente con tres muestras (una con dos estudios, una con uno, una sin estudios) y otro cliente con una muestra → el historial del primero muestra solo sus tres muestras, en orden, con estudios y estados.

### Tests for User Story 1 ⚠️ (escribir primero, deben fallar)

- [X] T005 [P] [US1] Crear `clientes/tests/test_historial.py` con: `test_ficha_ofrece_historial` (la ficha tiene un enlace a `reverse("clientes:historial", args=[pk])` con el texto «Historial»; US1 Esc. 1, FR-001), `test_lista_muestras_del_cliente` (200; cada muestra aparece con `data-muestra="<numero_pi>"`, N° PI, fecha de ingreso «dd/mm/aaaa» y origen; cada estudio con `data-estudio="<pk>"`, «Estudio N° <pk>», tipo y la etiqueta de estado; la muestra de otro cliente no aparece; US1 Esc. 2, FR-003/004), `test_muestra_tipo_guardado` (renombrar el `TipoEstudio` después de crear el estudio: se ve `tipo_nombre_snapshot`), `test_orden_en_pantalla` (los `data-muestra` aparecen en el orden de FR-005), `test_muestra_sin_estudios` («Sin estudios»; US1 Esc. 4), `test_cliente_sin_muestras` («Este cliente no tiene muestras registradas.»; US1 Esc. 5, FR-009), `test_encabezado_identifica_cliente` (nombre completo, «<tipo_documento> <numero_documento>» y enlace a `clientes:detalle`; US1 Esc. 6), `test_cliente_inactivo` (302 a `clientes:buscar` con «El cliente no está disponible.»; FR-002), `test_cliente_inexistente_404`, `test_requiere_sesion` (sin sesión → 302 al login), `test_historial_solo_lectura` (POST → 405 y la cantidad de muestras, estudios e informes no cambia; FR-013) y `test_consultas_acotadas` (con `django.test.utils.CaptureQueriesContext`: el GET al historial de un cliente con 1 muestra (un estudio con informe) hace **la misma** cantidad de consultas que el de un cliente con 100 muestras con un estudio con informe cada una (primera página de 20); sin límite numérico fijo; SC-004).

### Implementation for User Story 1

- [X] T006 [US1] Agregar en `clientes/views.py` la vista `historial(request, pk)` con `@require_GET` según research R7: `get_object_or_404(Cliente, pk=pk)`; si no está activo, `messages.warning(request, MENSAJE_NO_DISPONIBLE)` y `redirect("clientes:buscar")`; `Paginator(muestras_del_historial(cliente), RESULTADOS_POR_PAGINA).get_page(request.GET.get("page"))`; `sin_muestras = not page_obj.object_list and not cliente.muestras.exists()` (research R6); render de `clientes/historial.html` con `cliente`, `page_obj`, `sin_muestras`. Agregar en `clientes/urls.py` «`path("<int:pk>/historial/", views.historial, name="historial")`».
- [X] T007 [US1] Crear `clientes/templates/clientes/historial.html` según `contracts/historial-cliente-ui.md` (secciones 1, 3 y 4 y estados vacíos): encabezado con `ui/encabezado.html` (sección «Clientes», anterior «Ficha del cliente», miga «Historial», título `cliente.nombre_completo`, subtítulo con el documento); tabla `.tabla` dentro de `.tarjeta` con columnas **N° PI**, **Fecha de ingreso** (`|date:"d/m/Y"`), **Origen** y **Estudios** (por estudio: «Estudio N° {{ estudio.pk }} · {{ estudio.tipo_nombre_snapshot }}» y `ui/estado.html`; sin estudios: «Sin estudios»); `data-muestra` y `data-estudio`; `ui/paginacion.html`; con `sin_muestras`, `ui/estado_vacio.html` «Este cliente no tiene muestras registradas.». Los enlaces del N° PI, del estudio y «Ver informe» quedan para US3.
- [X] T008 [US1] Agregar en `clientes/templates/clientes/detalle.html` el botón **Historial** (`btn btn-secundario`, ícono `clock`) después de «Editar cliente», con `href="{% url 'clientes:historial' cliente.pk %}"` (FR-001). Correr T005 y T003: en verde.

**Checkpoint**: el historial se ve desde la ficha, completo y ordenado (MVP).

---

## Phase 4: User Story 2 - Filtrar el historial por fechas y estado (Priority: P2)

**Goal**: acotar el historial por rango de fecha de ingreso y por estado del estudio.

**Independent Test**: muestras de septiembre y octubre con estudios en distintos estados → filtrar por octubre, por «Informe generado» y combinados deja solo lo que corresponde.

### Tests for User Story 2 ⚠️ (escribir primero, deben fallar)

- [X] T009 [P] [US2] Agregar en `clientes/tests/test_historial_consulta.py`: `test_filtro_fechas` (parametrizado: solo desde, solo hasta, ambos; los extremos son inclusivos — una muestra ingresada justo el día «desde» y otra el día «hasta» aparecen; FR-006), `test_filtro_estado` (muestra con un estudio En proceso y otro Finalizado + muestra solo Pendiente: con `estado="en_proceso"` queda solo la primera, una sola vez, con `estudios_historial` de un elemento; FR-007) y `test_filtros_combinados` (US2 Esc. 3).
- [X] T010 [P] [US2] Agregar en `clientes/tests/test_historial.py`: `test_formulario_de_filtros` (el form tiene «Ingreso desde», «Ingreso hasta» y «Estado del estudio» con «Todos» + las cuatro etiquetas de `EstadoEstudio`; con `?desde=...&estado=...` los valores quedan cargados), `test_filtros_invalidos` (parametrizado: `desde` posterior a `hasta` → «La fecha desde no puede ser posterior a la fecha hasta.»; `desde=31/02/2026` → error de fecha; `estado=otro` → error de opción; en los tres casos 200, se ven **todas** las muestras y se ofrece «Limpiar filtros»; FR-006, US2 Esc. 4), `test_sin_coincidencias` («Ninguna muestra coincide con los filtros.» y enlace «Limpiar filtros» a la URL sin parámetros; no aparece el mensaje de cliente sin muestras; US2 Esc. 5, FR-009), `test_limpiar_filtros_solo_con_filtros` (sin parámetros, o con `desde`, `hasta` y `estado` vacíos, no se ofrece «Limpiar filtros»; con alguno no vacío, válido o no, sí) y `test_paginacion_conserva_filtros` (25 muestras de octubre con `?estado=pendiente_analisis&desde=2026-10-01`: la página 1 tiene 20 `data-muestra`, el enlace «Siguiente» lleva `estado=pendiente_analisis`, `desde=2026-10-01` y `page=2`, la página 2 tiene 5; una muestra con 3 estudios muestra sus 3 `data-estudio` en la misma página; FR-008/012, US2 Esc. 6).

### Implementation for User Story 2

- [X] T011 [US2] Agregar en `clientes/forms.py` `HistorialClienteForm(forms.Form)` según `data-model.md` y research R4: «`desde = DateField(label="Ingreso desde", required=False, input_formats=["%Y-%m-%d", "%d/%m/%Y"], widget=SelectorFecha())`», «`hasta`» igual con label «Ingreso hasta», «`estado = ChoiceField(label="Estado del estudio", required=False, choices=[("", "Todos"), *EstadoEstudio.choices])`»; `clean()`: si `desde > hasta`, `add_error("desde", "La fecha desde no puede ser posterior a la fecha hasta.")`. La decisión de mostrar «Limpiar filtros» no va en el form: la toma la vista (T012). Importar `SelectorFecha` de `muestras.forms` y `EstadoEstudio` de `estudios.models`.
- [X] T012 [US2] Actualizar `historial` en `clientes/views.py`: `form = HistorialClienteForm(request.GET or None)`; si el form es válido, pasar `desde`, `hasta` y `estado` de `cleaned_data` a `muestras_del_historial`; si no se envió o es inválido, sin filtros. `parametros` = `request.GET.copy()` sin `page`, `.urlencode()`. Agregar al contexto `form`, `parametros` y `hay_filtros = any(request.GET.get(c, "").strip() for c in ("desde", "hasta", "estado"))`: según los parámetros recibidos, **válidos o no**, para que un filtro inválido se pueda limpiar.
- [X] T013 [US2] Actualizar `clientes/templates/clientes/historial.html` (sección 2 del contrato y tabla de estados vacíos): formulario GET con los tres campos (`ui/campo.html` y `ui/errores_form.html`), botón **Filtrar** (`btn btn-primario`) y, con `hay_filtros`, **Limpiar filtros** (`btn btn-secundario`, `{% url 'clientes:historial' cliente.pk %}`); `ui/paginacion.html` con `parametros=parametros`; si la página está vacía y no es `sin_muestras`, `ui/estado_vacio.html` «Ninguna muestra coincide con los filtros.» con `accion_texto="Limpiar filtros"` y `accion_url` al historial sin parámetros. Correr T009 y T010: en verde.

**Checkpoint**: el historial filtra y pagina conservando los filtros.

---

## Phase 5: User Story 3 - Ir al detalle del estudio, de la muestra o al informe (Priority: P2)

**Goal**: desde el historial se llega al detalle del estudio, a la ficha de la muestra y al informe emitido.

**Independent Test**: un estudio En proceso y otro con informe → cada estudio enlaza a su detalle, el N° PI a la muestra y solo el que tiene informe ofrece «Ver informe INF-…».

### Tests for User Story 3 ⚠️ (escribir primero, deben fallar)

- [X] T014 [P] [US3] Agregar en `clientes/tests/test_historial.py`: `test_enlaces_a_detalles` (el N° PI enlaza a `reverse("muestras:detalle", args=[muestra.pk])` y cada estudio a `reverse("estudios:detalle", args=[estudio.pk])`; seguir los enlaces devuelve 200; US3 Esc. 1–2, FR-010) y `test_ver_informe_solo_con_informe` (el estudio con informe muestra «Ver informe INF-000001» enlazado a `reverse("informes:ver", args=[estudio.pk])`; el estudio En proceso no muestra «Ver informe»; un estudio en «Informe generado» **sin** `Informe` (dato inconsistente armado con `update`) tampoco; US3 Esc. 3–4, FR-011).

### Implementation for User Story 3

- [X] T015 [US3] Actualizar `clientes/templates/clientes/historial.html`: el N° PI como enlace a `{% url 'muestras:detalle' muestra.pk %}`; «Estudio N° … · …» como enlace a `{% url 'estudios:detalle' estudio.pk %}`; si el estudio tiene `Informe` (`{% if estudio.informe %}`, ya traído por el `select_related` de T004, sin consulta extra; no decidir por el estado), enlace **Ver informe {{ estudio.informe.numero_mostrado }}** (ícono `file-text`) a `{% url 'informes:ver' estudio.pk %}` (research R5). Correr T014: en verde.

**Checkpoint**: las tres historias funcionan y se prueban por separado.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T016 [P] Agregar en `clientes/tests/test_diseno.py` `test_historial_usa_componentes`: el HTML del historial incluye `data-componente="estado-vacio"` en un cliente sin muestras, la etiqueta `data-estado` de `ui/estado.html` en un estudio y el `nav` de paginación con más de 20 muestras.
- [X] T017 [P] Agregar en `CLAUDE.md` la sección «Historial del cliente (US 3.3)»: `clientes/historial.py:muestras_del_historial` es la única consulta del historial (pagina muestras y trae estudios con `Prefetch` a `estudios_historial`, con `informe` en `select_related`); el filtro de estado se aplica a muestras y al prefetch; tipo con `tipo_nombre_snapshot`; vista de solo lectura (`require_GET`) que rechaza clientes inactivos como la ficha; los imports de otras apps no van en `clientes/models.py`.
- [X] T018 Recompilar el CSS si el template agregó clases de Tailwind nuevas: `docker compose exec -u "$(id -u):$(id -g)" web tailwindcss -i static/src/aqualab.css -o static/css/aqualab.css --minify` y commitear `static/css/aqualab.css` (el CI verifica que esté al día).
- [X] T019 Ejecutar `docker compose exec web ruff check .` y `docker compose exec web ruff format --check .`: sin errores.
- [X] T020 Ejecutar la suite completa `docker compose exec web pytest`: todo en verde.
- [ ] T021 Recorrer `specs/023-historial-cliente/quickstart.md` en el navegador (pasos 1 a 9) y marcar el resultado en esta lista.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: `T001`.
- **Foundational (Phase 2)**: depende de la fase 1. `T002` → `T003` (usa sus fixtures) → `T004`.
- **US1 (Phase 3)**: depende de la fase 2. MVP.
- **US2 (Phase 4)**: depende de US1 (vista y template). Sus tests (`T009`, `T010`) se pueden escribir en paralelo a US1.
- **US3 (Phase 5)**: depende de US1 (template). Independiente de US2: se puede hacer antes o en paralelo (mismo template: coordinar si lo hacen dos personas).
- **Polish (Phase 6)**: depende de las tres historias.

### Grafo

```text
T001 → T002 → T003 → T004
                 │
US1: T005 → T006 → T007 → T008
US2: T009, T010 → T011 → T012 → T013
US3: T014 → T015
Polish: T016, T017 → T018 → T019 → T020 → T021
```

---

## Parallel Example: Polish

```bash
Task T016: "Test de diseño en clientes/tests/test_diseno.py"
Task T017: "Sección del historial en CLAUDE.md"
```

## Parallel Example: User Story 2

```bash
Task T009: "Tests de filtros de la consulta en clientes/tests/test_historial_consulta.py"
Task T010: "Tests de filtros de la vista en clientes/tests/test_historial.py"
```

---

## Implementation Strategy

### En dos tandas (según `docs/guias/guia-sdd-paso-a-paso.md`)

1. **Tanda 1 (Fases 1 a 3 — `T001` a `T008`)**: aprobación, consulta del historial y pantalla con el
   botón en la ficha (MVP: el historial completo y ordenado); suite en verde.
2. **Tanda 2 (Fases 4 a 6 — `T009` a `T021`)**: filtros (US2) y enlaces a estudio, muestra e informe
   (US3), cada uno con sus tests escritos primero; cerrar con diseño, `CLAUDE.md`, CSS, `ruff`, suite
   completa y recorrido manual.
