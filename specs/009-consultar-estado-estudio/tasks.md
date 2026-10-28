---

description: "Lista de tareas de la US 5.2 – Consultar estado del estudio"
---

# Tasks: Consultar estado del estudio

**Input**: `specs/009-consultar-estado-estudio/` (`plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/consulta-estudio-ui.md`, `quickstart.md`)

**Prerequisites**: `plan.md`, `spec.md`. Las apps `estudios`, `pruebas`, `muestras` y `clientes`, junto con la extensión `unaccent` de PostgreSQL, ya existen en el proyecto.

**Tests**: Incluidos. La constitución (Principio III) exige tests automatizados con `pytest-django` para cada escenario de aceptación y caso límite.

**Organization**: Tareas agrupadas por historia de usuario:
- **US1 (P1)**: Buscar estudios por identificador, muestra o cliente y consultar su detalle con el estado general y el listado de pruebas asignadas con su estado individual (Tanda 1).
- **US2 (P2)**: Consultar la ficha de la muestra con todos sus datos vigentes y el listado de sus estudios asignados (Tanda 2).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: se puede ejecutar en paralelo (archivos distintos, sin dependencias pendientes)
- **[Story]**: `[US1]` o `[US2]`

## Phase 1: Setup

- [ ] T001 Verificar contenedores Docker activos (`docker compose ps`) y migraciones al día (`docker compose exec web python manage.py migrate`) desde la raíz del proyecto

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: definir los estados generales completos de `Estudio` y el estado individual de cada prueba en `PruebaEstudio` (`research.md` R1, `data-model.md`)

**⚠️ CRITICAL**: tanto US1 como US2 dependen de esta fase.

- [ ] T002 Completar `EstadoEstudio(models.TextChoices)` con `PENDIENTE_ANALISIS = "pendiente_analisis", "Pendiente de análisis"`, `EN_PROCESO = "en_proceso", "En proceso"`, `FINALIZADO = "finalizado", "Finalizado"`, `INFORME_GENERADO = "informe_generado", "Informe generado"`, y agregar `EstadoPruebaEstudio(models.TextChoices)` (`PENDIENTE = "pendiente", "Pendiente"`, `CARGADA = "cargada", "Cargada"`, `COMPLETADA = "completada", "Completada"`) junto con el campo `estado = models.CharField("estado", max_length=20, choices=EstadoPruebaEstudio.choices, default=EstadoPruebaEstudio.PENDIENTE, editable=False)` en `PruebaEstudio`, en `estudios/models.py`
- [ ] T003 Generar y aplicar la migración `estudios/migrations/0003_estados_estudio_y_prueba.py` (dependencia `("estudios", "0002_estudio")`) verificando `docker compose exec web python manage.py migrate` (depende de T002)
- [ ] T004 Actualizar `test_uuid_obligatorio_y_identificador_propio` en `estudios/tests/test_modelos.py` para verificar los 4 choices de `EstadoEstudio` y el campo `estado` de `PruebaEstudio` (`default="pendiente"`, `editable=False` y los 3 choices de `EstadoPruebaEstudio`), ejecutando `docker compose exec web pytest estudios/tests/test_modelos.py` (depende de T003)

**Checkpoint**: `Estudio.estado` y `PruebaEstudio.estado` están disponibles en el modelo y migrados en PostgreSQL.

---

## Phase 3: User Story 1 - Buscar estudios y consultar su estado y pruebas asignadas (Priority: P1) 🎯 MVP

**Goal**: permitir buscar estudios desde un único campo por identificador, muestra (N° PI o nombre) o cliente (nombre, razón social o DNI/CUIT) y abrir la vista de detalle del estudio con su estado general y el listado de pruebas asignadas con el estado individual de cada una.

**Independent Test**: con estudios de prueba en distintos estados y pruebas en estados `Pendiente`, `Cargada` y `Completada`, buscar por cada criterio en `/estudios/buscar/`, verificar las columnas de resultados, abrir `/estudios/<pk>/` y comprobar la cabecera, el estado general, el resumen de avance y la tabla de pruebas asignadas.

### Tests for User Story 1 ⚠️ (escribir primero, deben fallar)

Todos en `estudios/tests/test_consulta.py` (mismo archivo: secuenciales).

- [ ] T005 [US1] Crear las fixtures de escenario en `estudios/tests/test_consulta.py` con clientes (`Juan Pérez` DNI `30123456`, empresa `Aguas del Sur S.A.` CUIT `20123456786`), muestras con distintos N° PI y nombres, y estudios en los 4 estados (`Pendiente de análisis`, `En proceso`, `Finalizado`, `Informe generado`) con pruebas asignadas en estados `Pendiente`, `Cargada` y `Completada`
- [ ] T006 [US1] Tests de los escenarios US1-1 y US1-2 en `estudios/tests/test_consulta.py`: búsqueda por identificador numérico del estudio (`?q=<pk>`) y búsqueda por N° PI (`?q=200001`) o por parte del nombre de la muestra
- [ ] T007 [US1] Tests de los escenarios US1-3 y US1-6 en `estudios/tests/test_consulta.py`: búsqueda por nombre, por razón social (ignorando mayúsculas y tildes) y por número de documento DNI/CUIT del cliente (con o sin puntos, guiones o espacios)
- [ ] T008 [US1] Test del escenario US1-4 en `estudios/tests/test_consulta.py`: cada resultado en `/estudios/buscar/` muestra el identificador del estudio, el N° PI y nombre de la muestra, el cliente y su documento, el nombre histórico del tipo de estudio (`tipo_nombre_snapshot`), la fecha de creación y el estado general (`get_estado_display`)
- [ ] T009 [US1] Test del escenario US1-5 en `estudios/tests/test_consulta.py`: la vista `/estudios/<pk>/` (`estudios:detalle`) muestra la cabecera completa (identificador, muestra con N° PI, nombre y origen, cliente y documento, nombre y descripción históricos del tipo de estudio, usuario creador, fecha de creación y estado general), el resumen de avance (total, completadas, cargadas y pendientes) y todas las pruebas asignadas ordenadas por código con su código, nombre y estado individual (`Pendiente`, `Cargada`, `Completada`)
- [ ] T010 [US1] Test del escenario US1-7 en `estudios/tests/test_consulta.py`: una búsqueda sin coincidencias (`?q=zzzz`) responde 200 con el mensaje `"No se encontraron estudios para «zzzz»."` y mantiene disponible el formulario
- [ ] T011 [US1] Tests de validación del buscador en `estudios/tests/test_consulta.py`: sin parámetro `q` muestra formulario vacío sin resultados ni error; `?q=` o solo espacios muestra `"Ingresá un identificador de estudio, N° PI, muestra o cliente para buscar."`; texto no numérico de 1 carácter (`?q=a`) muestra `"Ingresá al menos 2 caracteres para buscar."`; número de 1 dígito (`?q=1`) es válido
- [ ] T012 [US1] Tests de casos límite en `estudios/tests/test_consulta.py`: preservación de `tipo_nombre_snapshot` y `tipo_descripcion_snapshot` tras renombrar, editar o desactivar el tipo de estudio; búsqueda y detalle de estudios de un cliente con `activo=False`; orden `-pk` y paginación de a 20 resultados conservando `q`
- [ ] T013 [US1] Tests de acceso y existencia (FR-001) en `estudios/tests/test_consulta.py`: sin sesión activa, `GET /estudios/buscar/` y `GET /estudios/<pk>/` responden 302 hacia `settings.LOGIN_URL`; un `pk` inexistente en `estudios:detalle` responde 404

### Implementation for User Story 1

- [ ] T014 [P] [US1] Agregar `BuscarEstudioForm(forms.Form)` en `estudios/forms.py` con `q = forms.CharField(label="Identificador, muestra (N° PI / nombre) o cliente", required=False, strip=True)` y validación en `clean_q()` con los mensajes `"Ingresá un identificador de estudio, N° PI, muestra o cliente para buscar."` (vacío) e `"Ingresá al menos 2 caracteres para buscar."` (menos de 2 caracteres y `not q.isdigit()`)
- [ ] T015 [US1] Implementar las vistas `buscar(request)` y `detalle(request, pk)` en `estudios/views.py` según `research.md` (R2, R3, R4) y `data-model.md` (depende de T003, T014)
- [ ] T016 [US1] Agregar las rutas `path("buscar/", views.buscar, name="buscar")` y `path("<int:pk>/", views.detalle, name="detalle")` en `estudios/urls.py` (depende de T015)
- [ ] T017 [P] [US1] Crear `estudios/templates/estudios/buscar.html` extendiendo `base.html` según `contracts/consulta-estudio-ui.md` (formulario GET con campo `q`, tabla de resultados con estado general, alerta sin coincidencias y paginación Bootstrap conservando `q`)
- [ ] T018 [P] [US1] Crear `estudios/templates/estudios/detalle.html` extendiendo `base.html` según `contracts/consulta-estudio-ui.md` (cabecera con snapshots del tipo, datos de muestra y cliente, estado general, resumen de avance y tabla de pruebas asignadas con código, nombre y estado individual)
- [ ] T019 [P] [US1] Agregar el enlace `"Buscar estudio"` (`{% url 'estudios:buscar' %}`) en la barra de navegación de `templates/base.html`
- [ ] T020 [P] [US1] Agregar el botón `"Buscar estudio"` (`{% url 'estudios:buscar' %}`) en `templates/inicio.html`
- [ ] T021 [US1] Ejecutar `docker compose exec web pytest estudios/tests/test_consulta.py` y dejar todos los tests T005–T013 en verde (depende de T016–T020)

**Checkpoint (Fin de Tanda 1)**: el buscador de estudios y la vista de detalle del estudio con el estado general e individual de las pruebas son completamente funcionales y verificables en el navegador.

---

## Phase 4: User Story 2 - Consultar la lista de estudios asignados desde la ficha de la muestra (Priority: P2)

**Goal**: proveer la ficha de la muestra (`/muestras/<pk>/`) mostrando todos los datos vigentes de la muestra y la lista de sus estudios asignados con su estado general, el avance de pruebas y el acceso al detalle de cada estudio, enlazando muestras y estudios entre sí.

**Independent Test**: abrir `/muestras/<pk>/` para una muestra con varios estudios y para otra sin estudios; comprobar que se muestran todos los datos vigentes de la muestra, la tabla de estudios asignados con su estado y conteo de pruebas completadas (o el aviso de que aún no tiene estudios) y que los enlaces permiten navegar entre la ficha de la muestra y el detalle de cada estudio.

### Tests for User Story 2 ⚠️ (escribir primero, deben fallar)

Todos en `muestras/tests/test_detalle.py` (mismo archivo: secuenciales).

- [ ] T022 [US2] Test del escenario US2-1 en `muestras/tests/test_detalle.py`: `GET /muestras/<pk>/` (`muestras:detalle`) responde 200 y muestra todos los datos vigentes de la muestra (`numero_pi`, `nombre`, cliente con razón social/nombre, documento y correo, `origen`, `fecha_muestreo`, `fecha_ingreso`, `sitio_extraccion`, `get_tipo_vertido_display`, `responsable_muestreo`, `get_estado_display`, `registrada_por` y `fecha_registro`)
- [ ] T023 [US2] Test del escenario US2-2 en `muestras/tests/test_detalle.py`: para una muestra con varios estudios asignados, la ficha lista todos los estudios ordenados del más reciente al más antiguo (`-pk`), mostrando para cada uno su identificador, `tipo_nombre_snapshot`, fecha de creación, estado general (`get_estado_display`), conteo `<pruebas_completadas> / <total_pruebas>` y enlace a `estudios:detalle`
- [ ] T024 [US2] Test del escenario US2-3 en `muestras/tests/test_detalle.py`: para una muestra sin estudios asignados, la ficha muestra el mensaje `"Esta muestra aún no tiene estudios asignados."` y ofrece el enlace a `estudios:crear`
- [ ] T025 [US2] Test del escenario US2-4 en `muestras/tests/test_detalle.py`: desde `estudios:detalle` y desde los resultados de `estudios:buscar` se enlaza a `muestras:detalle` de la muestra asociada, y desde `muestras:detalle` se enlaza a `estudios:detalle` de cada estudio asignado
- [ ] T026 [US2] Tests de acceso, existencia y casos límite en `muestras/tests/test_detalle.py`: sin sesión activa, `GET /muestras/<pk>/` responde 302 a `settings.LOGIN_URL`; un `pk` inexistente responde 404; muestra con `responsable_muestreo` vacío muestra `"No especificado"`; muestra cuyo cliente está inactivo (`activo=False`) se visualiza correctamente

### Implementation for User Story 2

- [ ] T027 [US2] Implementar la vista `detalle(request, pk)` en `muestras/views.py` obteniendo la muestra con `get_object_or_404(Muestra.objects.select_related("cliente", "origen", "registrada_por"), pk=pk)` y sus estudios anotados con `total_pruebas` y `pruebas_completadas` en orden `-pk`, según `research.md` (R5) y `data-model.md`
- [ ] T028 [US2] Agregar la ruta `path("<int:pk>/", views.detalle, name="detalle")` en `muestras/urls.py` (depende de T027)
- [ ] T029 [US2] Crear `muestras/templates/muestras/detalle.html` extendiendo `base.html` según `contracts/consulta-estudio-ui.md` y enlazar la muestra hacia `muestras:detalle` en `estudios/templates/estudios/buscar.html` y `estudios/templates/estudios/detalle.html` (depende de T028)
- [ ] T030 [US2] Ejecutar `docker compose exec web pytest muestras/tests/test_detalle.py estudios/tests/test_consulta.py` y confirmar que todos los tests de US1 y US2 pasan en verde (depende de T029)

**Checkpoint (Fin de Tanda 2)**: US1 y US2 están integradas de punta a punta.

---

## Phase 5: Polish & Cross-Cutting Concerns

- [ ] T031 [P] Actualizar `CLAUDE.md` incorporando las rutas y modelos de `009-consultar-estado-estudio` (US 5.2)
- [ ] T032 Ejecutar `docker compose exec web ruff check .` y `docker compose exec web ruff format --check .` y corregir cualquier hallazgo de estilo o formato
- [ ] T033 Ejecutar la suite completa `docker compose exec web pytest` y confirmar que todos los tests del repositorio pasan sin regresiones
- [ ] T034 Recorrer la validación manual de `specs/009-consultar-estado-estudio/quickstart.md` (pasos 1 a 11) en el navegador

---

## Dependencies & Execution Order

- **Phase 1 (T001)** → **Phase 2 Foundational (T002 → T003 → T004)** bloquea US1 y US2.
- **Phase 3 (US1 - Tanda 1)**: T005–T013 (tests en `estudios/tests/test_consulta.py`) → T014 (`forms.py`) → T015 (`views.py`) → T016 (`urls.py`) → T017–T020 [P] (templates y enlaces) → T021 (`pytest`).
- **Phase 4 (US2 - Tanda 2)**: T022–T026 (tests en `muestras/tests/test_detalle.py`) → T027 (`muestras/views.py`) → T028 (`muestras/urls.py`) → T029 (`muestras/detalle.html` y enlaces cruzados) → T030 (`pytest`).
- **Phase 5 (Polish)**: T031–T034 después de completar US1 y US2.

### Parallel Opportunities

- En **US1**: T014 (`estudios/forms.py`) puede escribirse en paralelo con los tests T005–T013; los templates T017 (`estudios/buscar.html`), T018 (`estudios/detalle.html`), T019 (`templates/base.html`) y T020 (`templates/inicio.html`) tocan archivos distintos y son paralelizable (`[P]`).
- **US2** toca la app `muestras` (`muestras/views.py`, `muestras/urls.py`, `muestras/templates/muestras/detalle.html`, `muestras/tests/test_detalle.py`), independiente de `estudios/forms.py` y `estudios/views.py`.

## Implementation Strategy

### Tanda 1 — MVP (Phase 1 + Phase 2 + Phase 3 / US1)

1. Completar los estados de `Estudio` y `PruebaEstudio` y aplicar la migración (T001–T004).
2. Escribir los tests de búsqueda y detalle de estudio en `estudios/tests/test_consulta.py` (T005–T013).
3. Implementar `BuscarEstudioForm`, las vistas `estudios:buscar` y `estudios:detalle`, las URLs y los templates (T014–T021).
4. **Pausa de revisión manual**: probar en el navegador la búsqueda por ID, muestra y cliente y la vista de detalle del estudio.

### Tanda 2 — Ficha de la muestra y cierre (Phase 4 / US2 + Phase 5)

1. Escribir los tests de la ficha de la muestra y su lista de estudios asignados en `muestras/tests/test_detalle.py` (T022–T026).
2. Implementar `muestras:detalle`, su template y la navegación cruzada con `estudios` (T027–T030).
3. Actualizar `CLAUDE.md`, pasar `ruff` y la suite completa de `pytest` (T031–T034).
