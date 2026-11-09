---

description: "Lista de tareas de SCRUM-74 – Filtrar estudios por estado y fecha"
---

# Tasks: Filtrar estudios por estado y fecha

**Input**: `specs/028-filtrar-estudios/` (`plan.md`, `spec.md`, `research.md`, `data-model.md`,
`contracts/buscar-estudio-ui.md`, `quickstart.md`)

**Prerequisites**: `plan.md`, `spec.md` y `main` con la US 3.3 (historial del cliente:
`clientes.forms.HistorialClienteForm`, `clientes.views.historial`, `CAMPOS_FILTRO_HISTORIAL`) y la
US 9.1 (`ui/campo.html` dibuja `help_text` como tooltip); de la US 5.2, `estudios.views.buscar`,
`estudios.forms.BuscarEstudioForm`, `estudios/busqueda.py:filtro_busqueda` y
`estudios/templates/estudios/buscar.html`; `muestras.forms.SelectorFecha`; componentes
`ui/campo.html`, `ui/estado_vacio.html`, `ui/paginacion.html`, `ui/icono.html`; fixtures
`empleado`, `muestra`, `tipo`, `cliente_http` de `estudios/tests/conftest.py`.

**Tests**: SÍ. La constitution (principio III) exige un test por escenario de aceptación. Los tests
siguen el «Mapa de tests» de `plan.md` y se escriben **antes** de la implementación de cada historia
(deben fallar primero).

**Organization**: tres user stories — US1 (P1, filtrar por estado), US2 (P1, filtrar por fecha de
creación) y US3 (P2, combinar, paginar y limpiar).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: se puede ejecutar en paralelo (archivos distintos, sin dependencias pendientes)
- **[Story]**: user story a la que pertenece la tarea (`[US1]`, `[US2]`, `[US3]`)
- Rutas relativas a la raíz del repo

## Convenciones para todas las tareas

- Textos y mensajes en **español**, copiados **literalmente** de `contracts/buscar-estudio-ui.md`.
- Diseño de SCRUM-67 con `templates/ui/`; preferir clases ya usadas en `clientes/historial.html`
  (`grid gap-4 sm:grid-cols-3`, `btn btn-primario`, `btn btn-secundario`); si se agrega alguna,
  recompilar el CSS (T016).
- Pantalla de **solo lectura** (GET). `informes:listar` y `BuscarEstudioForm` **no cambian**.
- Textos de ayuda en el formulario (`help_text`), nunca en los modelos (US 9.1).
- Commits en Conventional Commits en español: `feat(estudios): SCRUM-74 – Filtrar estudios por estado y fecha`.
- Comandos dentro de Docker: `docker compose exec web pytest estudios clientes`,
  `docker compose exec web ruff check .`, `docker compose exec web ruff format --check .`.

---

## Phase 1: Setup (Shared Infrastructure)

- [ ] T001 **Gate de la constitution (principio I)**: confirmar que el equipo aprobó `specs/028-filtrar-estudios/spec.md` y actualizar su `**Status**` a «Aprobada (fecha)». Confirmar que la rama `028-filtrar-estudios` sale de `main` (`dcb8b3c` o posterior) y ejecutar `docker compose exec web pytest` y `docker compose exec web python manage.py makemigrations --check --dry-run`: suite en verde y sin cambios pendientes.

---

## Phase 2: Foundational (Blocking Prerequisites)

**⚠️ CRITICAL**: ninguna historia empieza antes de terminar esta fase. Es el refactor que comparte
el formulario del historial (research R1); los tests actuales del historial lo cubren.

- [ ] T002 En `estudios/forms.py` agregar, antes de `BuscarEstudioForm`, las constantes `FORMATOS_FECHA = ["%Y-%m-%d", "%d/%m/%Y"]` y `MENSAJE_FECHA_INVALIDA = "Ingresá una fecha válida (dd/mm/aaaa)."` y la clase base `FiltrosEstudioForm(forms.Form)` movida desde `clientes.forms.HistorialClienteForm`, con su docstring adaptado: campos `desde` y `hasta` (`forms.DateField(required=False, input_formats=FORMATOS_FECHA, widget=SelectorFecha(), error_messages={"invalid": MENSAJE_FECHA_INVALIDA})`, `SelectorFecha` importado de `muestras.forms`), `estado` (`forms.ChoiceField(required=False, choices=[("", "Todos"), *EstadoEstudio.choices], error_messages={"invalid_choice": "Elegí un estado de la lista."})`, `EstadoEstudio` de `.models`), etiquetas por defecto «Desde», «Hasta» y «Estado»; el `__init__` que pone `form-select`/`form-control` en `widget.attrs["class"]`, el `full_clean` que suma ` is-invalid` a los campos con error y el `clean` que con `desde > hasta` hace `add_error("desde", "La fecha desde no puede ser posterior a la fecha hasta.")`. Agregar la constante `CAMPOS_FILTRO = ("desde", "hasta", "estado")`.
- [ ] T003 En `clientes/forms.py` reemplazar el cuerpo de `HistorialClienteForm` por `class HistorialClienteForm(FiltrosEstudioForm)` que solo fija las etiquetas en `__init__` (`self.fields["desde"].label = "Ingreso desde"`, `"hasta"` → «Ingreso hasta», `"estado"` → «Estado del estudio»), conservando el docstring sobre «Limpiar filtros». Importar `FiltrosEstudioForm` desde `estudios.forms`; borrar de `clientes/forms.py` las constantes `FORMATOS_FECHA` y `MENSAJE_FECHA_INVALIDA` y los imports que queden sin uso (`EstadoEstudio`, `SelectorFecha`) solo si ya no se usan en el archivo (verificar con `ruff check`). En `clientes/views.py` reemplazar `CAMPOS_FILTRO_HISTORIAL` por `CAMPOS_FILTRO` importado de `estudios.forms` (o dejar el alias). Verificar que `clientes/historial.html` y los labels no cambian.
- [ ] T004 Ejecutar `docker compose exec web pytest clientes estudios informes`: todo en verde sin tocar tests (el refactor no cambia comportamiento).

**Checkpoint**: el historial funciona igual con la base compartida.

---

## Phase 3: User Story 1 — Filtrar por estado (Priority: P1) 🎯 MVP

**Goal**: «Buscar estudio» ofrece Estado (Todos + 4) y lista solo los estudios en ese estado.

**Independent Test**: con estudios en los cuatro estados, elegir «En proceso» → solo esos; «Todos» → todos.

### Tests for User Story 1 ⚠️

- [ ] T005 [US1] Crear `estudios/tests/test_filtros.py` con: un helper `estudio_creado(muestra, tipo, usuario, estado=EstadoEstudio.PENDIENTE_ANALISIS, creado=None)` que llama a `estudios.servicios.crear_estudio({"clave": str(uuid.uuid4()), "muestra": muestra.pk, "tipo": tipo.pk, "version": tipo.version}, usuario)` y después fija `estado` y, si se pasa, `fecha_creacion` (datetime consciente de zona) con `Estudio.objects.filter(pk=...).update(...)` (`fecha_creacion` es `auto_now_add`; ver plan → Testing) y devuelve el estudio recargado; un fixture `un_estudio_por_estado(muestra, tipo, empleado)` que crea uno por cada valor de `EstadoEstudio` y los devuelve en un dict por estado. Tests (usando `cliente_http` y `reverse("estudios:buscar")`):
  - `test_muestra_los_filtros` (US1 Esc. 1, FR-001): el HTML tiene `name="estado"` con las opciones «Todos», «Pendiente de análisis», «En proceso», «Finalizado», «Informe generado» (los `get_estado_display`), «Todos» seleccionado, y los campos `name="desde"` y `name="hasta"` de tipo `date` con etiquetas «Desde» y «Hasta».
  - `test_filtra_por_estado` parametrizado por los cuatro `EstadoEstudio` (US1 Esc. 2, FR-002): `object_list` es exactamente `[el estudio de ese estado]` y el encabezado dice «1 estudio encontrado».
  - `test_estado_todos_no_restringe` (US1 Esc. 3): `{"estado": ""}` lista los cuatro.
  - `test_filtros_invalidos` parametrizado (US1 Esc. 4, US2 Esc. 3–4, FR-005), con casos `{"estado": "otro"}` → «Elegí un estado de la lista.», `{"desde": "31/02/2026"}` y `{"hasta": "no-es-fecha"}` → «Ingresá una fecha válida (dd/mm/aaaa).», `{"desde": "2026-11-10", "hasta": "2026-11-01"}` → «La fecha desde no puede ser posterior a la fecha hasta.»: status 200, el mensaje aparece, el campo con error lleva `is-invalid`, el valor recibido queda en el formulario y `page_obj.paginator.count` es el total (listado sin filtrar). Agregar el caso combinado `{"estado": "en_proceso", "desde": "x"}` → también sin filtrar por estado.
- [ ] T006 [US1] Ejecutar `docker compose exec web pytest estudios/tests/test_filtros.py`: los tests de T005 fallan (todavía no hay filtros).

### Implementation for User Story 1

- [ ] T007 [US1] En `estudios/busqueda.py` agregar `filtro_estado_fechas(desde=None, hasta=None, estado="")` que devuelve un `Q`: `Q()` vacío sin criterios; con `estado`, `Q(estado=estado)`. (Las fechas se completan en T012.) Docstring: «Filtro por estado actual y días completos de `fecha_creacion` en la zona del laboratorio (SCRUM-74).»
- [ ] T008 [US1] En `estudios/forms.py` agregar `class FiltrarEstudiosForm(BuscarEstudioForm, FiltrosEstudioForm)` con docstring «Búsqueda de estudios con filtros (SCRUM-74): texto (US 5.2), estado y fecha de creación». En `__init__`, después de `super().__init__`, fijar `self.fields["desde"].help_text = self.fields["hasta"].help_text = "Fecha en que se creó el estudio. El día indicado se incluye."`. Verificar que `q` sigue con sus validaciones (`clean_q`) y que `BuscarEstudioForm` no cambió (lo usa `informes:listar`).
- [ ] T009 [US1] En `estudios/views.py` cambiar `buscar` para usar `FiltrarEstudiosForm(request.GET or None)`: armar `qs` como hoy; si el formulario es válido, filtrar por `filtro_busqueda(q)` (si hay `q`) y por `filtro_estado_fechas(**{c: form.cleaned_data[c] for c in CAMPOS_FILTRO})`; si no es válido, `q = ""` y **no filtrar** (research R3). Siempre paginar (`page_obj` nunca es `None`). Contexto: `form`, `page_obj`, `q`, `parametros` (`request.GET.copy()`, `pop("page", None)`, `urlencode()`), `hay_filtros` (`any(request.GET.get(c, "").strip() for c in ("q", *CAMPOS_FILTRO))`) `filtrado` (formulario válido con `q` o algún valor de `CAMPOS_FILTRO`) y `con_filtros` (formulario válido con algún valor de `CAMPOS_FILTRO`; lo usa el estado vacío de T016). Quitar el import de `BuscarEstudioForm` si queda sin uso.
- [ ] T010 [US1] En `estudios/templates/estudios/buscar.html`, debajo de la fila de búsqueda, agregar `<div class="mt-4 grid gap-4 sm:grid-cols-3">` con `{% include "ui/campo.html" with field=form.estado %}`, `form.desde` y `form.hasta`. Encabezado del listado: «encontrado(s)» si `filtrado`, «registrado(s)» si no. Paginación: `{% include "ui/paginacion.html" with parametros=parametros %}` (reemplaza el `with qq=q|urlencode`). Mantener el campo `q`, su ayuda y sus errores como están.
- [ ] T011 [US1] Ejecutar `docker compose exec web pytest estudios/tests/test_filtros.py -k "estado or muestra_los_filtros or invalidos"`: pasan los de estado; los inválidos de fecha pasan por la validación del formulario.

**Checkpoint**: US1 funciona sola (MVP).

---

## Phase 4: User Story 2 — Filtrar por fecha de creación (Priority: P1)

**Goal**: Desde/Hasta filtran por `fecha_creacion` con los dos días completos en la zona del laboratorio.

**Independent Test**: estudios creados el 1, el 5 y el 10 → del 5 al 10 aparecen el 5 y el 10; solo Desde / solo Hasta.

### Tests for User Story 2 ⚠️

- [ ] T012 [P] [US2] En `estudios/tests/test_filtros.py` agregar un fixture `estudios_por_fecha` con tres estudios creados (con `estudio_creado(..., creado=...)`) el 1, el 5 y el 10 de noviembre de 2026 a las 12:00 en `zoneinfo.ZoneInfo(settings.TIME_ZONE)`, y los tests:
  - `test_filtro_fechas` parametrizado (US2 Esc. 1–2, FR-003): `desde=2026-11-05, hasta=2026-11-10` → 5 y 10; solo `desde=2026-11-05` → 5 y 10; solo `hasta=2026-11-05` → 1 y 5; `desde=hasta=2026-11-05` → 5; formato `05/11/2026` también aceptado.
  - `test_bordes_del_dia_en_zona_del_laboratorio` (Edge cases): un estudio creado el 05/11/2026 00:00:00 local y otro el 05/11/2026 23:59:59 local entran con `desde=hasta=2026-11-05`; uno del 04/11 23:59:59 y otro del 06/11 00:00:00 local, no. (23:59 local del 05/11 es 02:59 UTC del 06/11: el test prueba que el día se cuenta en la zona del laboratorio, no en UTC.)
  - `test_filtro_estado_fechas_vacio`: `Estudio.objects.filter(filtro_estado_fechas())` devuelve todos.
  - `test_ayuda_en_fechas` (US 9.1): el HTML tiene `role="tooltip"` con id `id_desde_helptext` y texto «Fecha en que se creó el estudio. El día indicado se incluye.» y el input `id_desde` lo referencia en `aria-describedby`; ídem `hasta`.

### Implementation for User Story 2

- [ ] T013 [US2] En `estudios/busqueda.py` completar `filtro_estado_fechas` (research R2): con `desde`, `Q(fecha_creacion__gte=inicio_del_dia(desde))`; con `hasta`, `Q(fecha_creacion__lt=inicio_del_dia(hasta + timedelta(days=1)))`, donde `inicio_del_dia(fecha)` es `timezone.make_aware(datetime.combine(fecha, time.min), timezone.get_default_timezone())` (zona `TIME_ZONE` del laboratorio). No usar `__date` ni `float`.
- [ ] T014 [US2] Ejecutar `docker compose exec web pytest estudios/tests/test_filtros.py`: US1 y US2 en verde.

**Checkpoint**: US1 y US2 funcionan juntas e independientes.

---

## Phase 5: User Story 3 — Combinar, paginar y limpiar (Priority: P2)

**Goal**: texto + estado + fechas combinados (AND), la paginación los conserva y «Limpiar filtros» reemplaza a «Ver todos».

**Independent Test**: más de 20 estudios que cumplen los tres criterios → página 2 conserva los filtros; «Limpiar filtros» vuelve al listado completo.

### Tests for User Story 3 ⚠️

- [ ] T015 [P] [US3] En `estudios/tests/test_filtros.py` agregar:
  - `test_filtros_combinados_con_texto` (US3 Esc. 1, FR-004): dos muestras de clientes distintos (crear un segundo `Cliente`, `Origen` y `Muestra` con `numero_pi=200002`) y estudios en distintos estados y fechas; `q=<nombre del cliente>` + `estado` + rango → solo el que cumple los tres.
  - `test_paginacion_conserva_filtros` (US3 Esc. 2, FR-006): 21 estudios «En proceso» creados el 05/11/2026 y 2 «Pendiente de análisis»; con `q="Muestra test"`, `estado=en_proceso`, `desde=2026-11-01`, `hasta=2026-11-30`, el enlace «Siguiente» contiene `q=Muestra+test`, `estado=en_proceso`, `desde=2026-11-01`, `hasta=2026-11-30` y `page=2` sin `page` duplicado; la página 2 tiene 1 estudio y el formulario conserva los valores.
  - `test_limpiar_filtros` parametrizado (US3 Esc. 3, FR-007): con `{"q": "Muestra"}`, `{"estado": "en_proceso"}`, `{"desde": "2026-11-01"}` y `{"desde": "x"}` (inválido) el HTML tiene un enlace «Limpiar filtros» a `reverse("estudios:buscar")`; sin parámetros (y con `{"q": "  "}`) no lo tiene; en ningún caso aparece «Ver todos».
  - `test_sin_coincidencias_con_filtros` (US3 Esc. 4, FR-008): con estudios pero un rango sin ninguno → «Ningún estudio coincide con la búsqueda y los filtros.» con la acción «Limpiar filtros»; sin estudios y sin parámetros → «Aún no hay estudios registrados.»; solo `q="zzzz"` → «No se encontraron estudios para «zzzz».» (sin cambios).
  - `test_formulario_comparte_reglas_con_historial` (FR-010): `HistorialClienteForm` es subclase de `FiltrosEstudioForm`, y para `{"desde": "2026-11-10", "hasta": "2026-11-01"}` y `{"estado": "otro"}` los dos formularios (`FiltrarEstudiosForm`, `HistorialClienteForm`) dan los mismos mensajes de error.

### Implementation for User Story 3

- [ ] T016 [US3] En `estudios/templates/estudios/buscar.html`: reemplazar `{% if q %}…Ver todos…{% endif %}` por `{% if hay_filtros %}<a href="{% url 'estudios:buscar' %}" class="btn btn-secundario">{% include "ui/icono.html" with nombre="x" clase="size-4" %} Limpiar filtros</a>{% endif %}`; en los estados vacíos (`{% url 'estudios:buscar' as url_buscar %}`): si hay resultados → la tabla; si no y `con_filtros` → `{% include "ui/estado_vacio.html" with icono="search" mensaje="Ningún estudio coincide con la búsqueda y los filtros." accion_texto="Limpiar filtros" accion_url=url_buscar %}`; si no y `q` → el mensaje actual «No se encontraron estudios para «…».»; si no → «Aún no hay estudios registrados.». Si alguna clase de Tailwind es nueva, recompilar con `docker compose exec -u "$(id -u):$(id -g)" web tailwindcss -i static/src/aqualab.css -o static/css/aqualab.css --minify` y commitear `static/css/aqualab.css`.
- [ ] T017 [US3] En `estudios/tests/test_consulta.py` ajustar los tres tests de texto inválido (research R3): `test_busqueda_un_caracter_no_numerico_rechazada`, `test_busqueda_numero_invalido_o_fuera_de_rango_muestra_error` y `test_busqueda_supera_longitud_maxima_muestra_error` siguen verificando el mensaje y pasan a verificar `resp.context["page_obj"].paginator.count == 4` (listado completo, sin filtrar) en lugar de `page_obj is None`.
- [ ] T018 [US3] Ejecutar `docker compose exec web pytest estudios clientes informes`: todo en verde.

**Checkpoint**: las tres historias funcionan juntas; historial e informes sin cambios.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [ ] T019 [P] En `CLAUDE.md` agregar la sección «## Filtrar estudios (SCRUM-74)» con: `estudios.forms.FiltrosEstudioForm` es la única definición de los filtros desde/hasta/estado (la heredan `HistorialClienteForm` y `FiltrarEstudiosForm`; `BuscarEstudioForm` sigue solo con `q` porque lo usa `informes:listar`); `estudios/busqueda.py:filtro_estado_fechas` cuenta los días de `fecha_creacion` en la zona del laboratorio con límites `>= inicio(desde)` y `< inicio(hasta + 1)`; con cualquier valor inválido `estudios:buscar` muestra el listado completo sin filtrar (como el historial); la paginación usa `parametros` (GET sin `page`) y «Limpiar filtros» depende de los parámetros recibidos. Mantener el estilo breve de las otras secciones.
- [ ] T020 Ejecutar `docker compose exec web pytest`, `docker compose exec web ruff check .`, `docker compose exec web ruff format --check .` y `docker compose exec web python manage.py makemigrations --check --dry-run`: todo en verde, sin migraciones.
- [ ] T021 Prueba manual según `specs/028-filtrar-estudios/quickstart.md` (pasos 1–8, con `cargar_demo`), incluido el historial del cliente como regresión. La acredita el autor.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: sin dependencias.
- **Foundational (Phase 2)**: depende de T001; bloquea todas las historias (la base `FiltrosEstudioForm`).
- **US1 (Phase 3)**: depende de la fase 2. Crea el formulario, la vista y la fila de filtros que usan US2 y US3.
- **US2 (Phase 4)**: depende de US1 (T007–T010: misma función, formulario y vista); solo completa las fechas en `filtro_estado_fechas`.
- **US3 (Phase 5)**: depende de US1 (vista y template); independiente de US2 salvo `test_paginacion_conserva_filtros`, que usa fechas.
- **Polish (Phase 6)**: después de las historias.

### Within Each User Story

- Tests primero (deben fallar), después implementación, después ejecutar los tests.
- `estudios/busqueda.py` → `estudios/forms.py` → `estudios/views.py` → template.

### Parallel Opportunities

- T012 (tests de US2) y T015 (tests de US3) se pueden escribir en paralelo una vez terminada US1, aunque comparten `estudios/tests/test_filtros.py` (secciones distintas al final del archivo).
- T019 (`CLAUDE.md`) en paralelo con T020.

## Parallel Example: después de US1

```text
Task: "T012 [US2] tests de fechas en estudios/tests/test_filtros.py"
Task: "T015 [US3] tests de combinar/paginar/limpiar en estudios/tests/test_filtros.py"
```

## Implementation Strategy

### MVP First (User Story 1)

1. Fase 1 (gate) y fase 2 (base compartida, historial en verde).
2. Fase 3: filtro por estado en «Buscar estudio».
3. **Validar**: «En proceso» lista solo esos estudios.

### Incremental Delivery

1. US1 → filtro por estado (MVP).
2. US2 → rango de fechas.
3. US3 → combinar, paginar, «Limpiar filtros» y estados vacíos.
4. Polish → `CLAUDE.md`, suite completa, prueba manual y PR «SCRUM-74 – Filtrar estudios por estado y fecha».
