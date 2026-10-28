---

description: "Lista de tareas de la US 5.3 y US 5.4 – Agregar y quitar pruebas de un estudio"
---

# Tasks: Agregar y quitar pruebas de un estudio

**Input**: `specs/009-gestionar-pruebas-estudio/` (`plan.md`, `spec.md`, `research.md`,
`data-model.md`, `contracts/pruebas-estudio-ui.md`, `quickstart.md`)

**Prerequisites**: `plan.md`, `spec.md`. Ya existen y no se recrean (US 5.1, PR #12):
`estudios.Estudio`, `estudios.PruebaEstudio` (`related_name="pruebas_asignadas"`,
`UniqueConstraint(estudio, prueba)` llamada `estudio_prueba_unica`), `estudios.EstadoEstudio`,
`pruebas.Prueba`, `estudios/servicios.py:crear_estudio`, `estudios/views.py:exito`,
`estudios/tests/conftest.py` (fixtures `empleado`, `cliente_a`, `muestra`, `pruebas`, `tipo`,
`datos`, `cliente_http`), `LoginRequiredMiddleware` y `templates/base.html`.

**Tests**: SÍ. La constitution (Principio III) exige al menos un test con pytest-django por cada
escenario de aceptación. Los tests siguen el "Mapa de tests" de `plan.md` y se escriben **antes** de
la implementación de cada historia (deben fallar primero).

**Organization**: tres user stories de la spec — US1 (P1, agregar una prueba), US2 (P1, quitar una
prueba) y US3 (P2, impedir modificaciones no permitidas).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: se puede ejecutar en paralelo (archivos distintos, sin dependencias pendientes)
- **[Story]**: user story a la que pertenece la tarea (`[US1]`, `[US2]`, `[US3]`)
- Rutas relativas a la raíz del repo

## Convenciones para todas las tareas

- Textos de UI, mensajes y nombres de dominio en **español** (Principio VI).
- Mensajes al usuario copiados **literalmente** de `contracts/pruebas-estudio-ui.md`.
- Estilo de vistas, formularios y templates igual al de US 5.1: vistas de función en
  `estudios/views.py`, `CrearEstudioForm` en `estudios/forms.py` (clase `form-select`), templates
  `estudios/templates/estudios/crear_*.html` (Bootstrap 5.3, `<dl class="row">`, botones
  `d-flex gap-2`).
- **Sin migraciones**: ninguna tarea cambia campos ni constraints (ver `data-model.md`).
- Comandos dentro de Docker: `docker compose exec web pytest estudios`,
  `docker compose exec web ruff check .`, `docker compose exec web ruff format --check .`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: confirmar que la base de US 5.1 está sana antes de tocar código.

- [ ] T001 **Gate de la constitution (Principio I)**: confirmar que el equipo aprobó `specs/009-gestionar-pruebas-estudio/spec.md` y actualizar su `**Status**` a «Aprobada por el equipo» con la fecha; sin aprobación no se ejecuta ninguna otra tarea. Después, verificar el entorno con `docker compose up -d`, `docker compose exec web python manage.py migrate` y `docker compose exec web pytest` (sobre `docker-compose.yml`) y confirmar que la suite actual pasa y que `docker compose exec web python manage.py makemigrations --check --dry-run` no detecta cambios.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: reglas del modelo, excepciones, fixtures y detalle de solo lectura del estudio, que
usan las tres historias.

**⚠️ CRITICAL**: ninguna historia empieza antes de terminar esta fase.

- [ ] T002 [P] Agregar en `estudios/tests/conftest.py` las fixtures:
  - `estudio(datos, empleado)`: crea un estudio con `crear_estudio(datos, empleado)` (queda con las pruebas `TEST-A` y `TEST-B` del fixture `tipo`).
  - `prueba_extra()`: `Prueba.objects.create(codigo="TEST-C", nombre="Prueba de test C")`, que no está en el tipo.
  - `asignacion(estudio)`: la `PruebaEstudio` de `TEST-A` del estudio.
- [ ] T003 [P] Agregar en `estudios/tests/test_modelos.py` `test_admite_modificaciones_solo_pendiente_analisis` (un estudio recién creado admite modificaciones; con `estado` forzado a otro valor en memoria, no) y `test_puede_quitarse_sin_mediciones` (una asignación recién creada devuelve `True`) (depende de T002).
- [ ] T004 Agregar en `estudios/models.py`:
  - en `Estudio`, la propiedad `admite_modificaciones` que devuelve `self.estado == EstadoEstudio.PENDIENTE_ANALISIS` (FR-003);
  - en `PruebaEstudio`, el método `puede_quitarse(self)` que devuelve `True`, con un docstring breve que indique que US 6.1 y siguientes deben devolver `False` cuando la asignación tenga mediciones o resultados, y que esas tablas deben referenciar a `PruebaEstudio` con `on_delete=PROTECT` (FR-007, research R5).
  Sin cambiar campos ni `Meta`; verificar que `makemigrations --check --dry-run` siga sin cambios.
- [ ] T005 Agregar en `estudios/servicios.py`, debajo de `crear_estudio`, la jerarquía de excepciones `GestionPruebasError(Exception)` y sus subclases `PruebaYaAsignada`, `PruebaYaQuitada` y `UltimaPrueba`; el mensaje de cada excepción es el texto que ve el empleado (plan, "Servicios").
- [ ] T006 Crear la vista `detalle(request, pk)` en `estudios/views.py` con `get_object_or_404(Estudio.objects.select_related("muestra__cliente", "muestra__origen", "creado_por"), pk=pk)` y las asignaciones `estudio.pruebas_asignadas.select_related("prueba").order_by("prueba__codigo")`; registrar `path("<int:pk>/", views.detalle, name="detalle")` en `estudios/urls.py` (depende de T004).
- [ ] T007 Crear `estudios/templates/estudios/detalle.html` extendiendo `base.html` según `contracts/pruebas-estudio-ui.md` ("GET /estudios/<pk>/"): `<dl class="row">` con Estudio N°, Muestra (`PI numero_pi`), Cliente (`nombre_completo`), Origen, Tipo (`tipo_nombre_snapshot`), Estado (`get_estado_display`), Creado por (`creado_por.get_full_name|default:creado_por.email`) y Fecha de creación (`d/m/Y H:i`); tabla `table` con Código, Nombre, Estado ("Pendiente") y una columna Acción vacía por ahora; si `not estudio.admite_modificaciones`, la alerta «Este estudio ya no admite cambios en sus pruebas.» (depende de T006).
- [ ] T008 Cambiar `exito` en `estudios/views.py` para que el mensaje sea `format_html('<a href="{}">Estudio {}</a> creado para la muestra PI {}.', reverse("estudios:detalle", args=[estudio.pk]), estudio.pk, estudio.muestra.numero_pi)`, sin cambiar la redirección a `estudios:crear` (research R1) (depende de T006).
- [ ] T009 Ejecutar `docker compose exec web pytest estudios` y dejar en verde T003 junto con los tests existentes de US 5.1 (depende de T002–T008).

**Checkpoint**: el detalle del estudio se ve desde el mensaje de éxito; las historias pueden empezar.

---

## Phase 3: User Story 1 - Agregar una prueba adicional a un estudio (Priority: P1) 🎯 MVP

**Goal**: desde el detalle, elegir una prueba del catálogo que el estudio no tenga, confirmar y
dejarla asignada una sola vez como pendiente (US 5.3).

**Independent Test**: con el fixture `estudio` (TEST-A, TEST-B) y `prueba_extra` (TEST-C), agregar
TEST-C con revisar → confirmar y verificar que figura una vez en el detalle, sin cambios en la
cabecera, los snapshots ni el tipo.

### Tests for User Story 1 ⚠️ (escribir primero, deben fallar)

- [ ] T010 [P] [US1] Crear `estudios/tests/test_servicio_pruebas.py` (`pytestmark = pytest.mark.django_db`) con:
  - `test_agregar_prueba_crea_asignacion`: `agregar_prueba(estudio.pk, prueba_extra.pk, empleado)` crea una `PruebaEstudio` y el estudio queda con TEST-A, TEST-B y TEST-C.
  - `test_agregar_no_modifica_cabecera_tipo_ni_otros_estudios`: guarda `muestra_id`, `tipo_id`, `estado`, `creado_por_id`, `fecha_creacion`, `tipo_nombre_snapshot`, `tipo_descripcion_snapshot`, `tipo_version_snapshot` del estudio, las pruebas y `version` del tipo, y las pruebas de un segundo estudio del mismo tipo; agrega TEST-C y verifica que nada de eso cambió (extraer la captura de esos datos a una función auxiliar del archivo para reutilizarla en US2).
- [ ] T011 [P] [US1] Crear `estudios/tests/test_gestion_pruebas.py` (`pytestmark = pytest.mark.django_db`) con:
  - `test_detalle_muestra_cabecera_pruebas_y_acciones`: GET `estudios:detalle` → 200 con N° del estudio, `PI 200001`, nombre del tipo, «Pendiente de análisis», TEST-A, TEST-B y el enlace a `estudios:agregar_prueba`.
  - `test_exito_creacion_enlaza_al_detalle`: confirmar una creación por la vista de US 5.1 deja un mensaje que contiene el `href` de `estudios:detalle` del estudio creado.
  - `test_agregar_ofrece_solo_pruebas_no_asignadas`: GET `estudios:agregar_prueba` → 200 con TEST-C entre las opciones y sin TEST-A ni TEST-B.
  - `test_revisar_muestra_confirmacion_sin_guardar`: POST `accion=revisar`, `prueba=<TEST-C>` → 200 con «Se agregará la prueba», el enlace **Cancelar** al `href` de `estudios:detalle` y sin nuevas `PruebaEstudio` (cancelar es volver al detalle sin enviar nada: SC-005).
  - `test_confirmar_agrega_prueba_una_vez`: POST `accion=confirmar` → 302 a `detalle`, mensaje «Prueba TEST-C · Prueba de test C agregada al estudio N.» y TEST-C asignada una sola vez.
  - `test_agregar_sin_pruebas_disponibles_informa`: sin otras pruebas en el catálogo (sin `prueba_extra`) → «No hay pruebas disponibles para agregar: todas ya forman parte del estudio.» y sin formulario.
  - `test_error_de_base_al_agregar_no_cambia_estudio`: con `agregar_prueba` parcheado para lanzar `DatabaseError`, POST `accion=confirmar` → 302 a `detalle` con «No se pudo agregar la prueba. Intentá nuevamente.» y sin asignaciones nuevas.

### Implementation for User Story 1

- [ ] T012 [US1] Implementar `agregar_prueba(estudio_pk, prueba_pk, usuario)` en `estudios/servicios.py`: rechaza con `GestionPruebasError("Se requiere una sesión activa.")` si `not usuario.is_authenticated or not usuario.is_active`; dentro de `transaction.atomic()`: `Estudio.objects.select_for_update().filter(pk=estudio_pk).first()` (None → `GestionPruebasError("El estudio no está disponible.")`), `Prueba.objects.filter(pk=prueba_pk).first()` (None → `GestionPruebasError("La prueba no está disponible.")`) y `PruebaEstudio.objects.create(estudio=estudio, prueba=prueba)`; devuelve la asignación (depende de T005).
- [ ] T013 [US1] Crear `AgregarPruebaForm(forms.Form)` en `estudios/forms.py`: `__init__(self, *args, estudio, **kwargs)` define `prueba = forms.ModelChoiceField(queryset=Prueba.objects.exclude(pk__in=estudio.pruebas_asignadas.values("prueba")), label="Prueba", empty_label="Elegí una prueba")` con `widget.attrs["class"] = "form-select"` (research R6).
- [ ] T014 [US1] Crear la vista `agregar_prueba(request, pk)` en `estudios/views.py` según `contracts/pruebas-estudio-ui.md` ("GET/POST /estudios/<pk>/pruebas/agregar/"): GET → formulario, o la alerta de «sin pruebas disponibles» si el queryset está vacío; POST `accion=revisar` → formulario inválido (200 con error) o `estudios/agregar_prueba_confirmar.html`; POST `accion=confirmar` → revalida el formulario y llama a `agregar_prueba`, mensaje de éxito y 302 a `detalle`; `GestionPruebasError` → `messages.error(str(exc))`; `DatabaseError` → «No se pudo agregar la prueba. Intentá nuevamente.»; otra `accion` → «La acción no es válida.». Registrar `path("<int:pk>/pruebas/agregar/", views.agregar_prueba, name="agregar_prueba")` en `estudios/urls.py` (depende de T012, T013).
- [ ] T015 [P] [US1] Crear `estudios/templates/estudios/agregar_prueba.html`: título «Agregar prueba al estudio N», identificación del estudio (N° y PI), `<form method="post">` con `{% csrf_token %}`, el `<select>` de `prueba` con `is-invalid` + `invalid-feedback` si tiene error, botón **Revisar** (`name="accion" value="revisar"`) y enlace **Cancelar** a `detalle`; si no hay pruebas para ofrecer, la alerta «No hay pruebas disponibles para agregar: todas ya forman parte del estudio.» y el enlace «Volver al estudio» en lugar del formulario (depende de T014).
- [ ] T016 [P] [US1] Crear `estudios/templates/estudios/agregar_prueba_confirmar.html` como `crear_confirmar.html`: «Se agregará la prueba `código · nombre` al estudio N (muestra PI X).», `<input type="hidden" name="prueba">`, botón **Confirmar** (`accion=confirmar`) y enlaces **Volver** (a `estudios:agregar_prueba`) y **Cancelar** (a `detalle`) (depende de T014).
- [ ] T017 [US1] En `estudios/templates/estudios/detalle.html`, agregar el botón-enlace **Agregar prueba** a `estudios:agregar_prueba`, visible solo si `estudio.admite_modificaciones` (depende de T007, T014).
- [ ] T018 [US1] Ejecutar `docker compose exec web pytest estudios` y dejar en verde T010–T011 (depende de T012–T017).

**Checkpoint**: US 5.3 funciona sola: se puede agregar una prueba con confirmación.

---

## Phase 4: User Story 2 - Quitar una prueba que no se va a realizar (Priority: P1)

**Goal**: desde el detalle, quitar una prueba del estudio después de una confirmación explícita, de
modo que deje de formar parte del estudio (US 5.4).

**Independent Test**: con el fixture `estudio` (TEST-A, TEST-B), quitar TEST-A con confirmación y
verificar que ya no figura en el detalle y que vuelve a ofrecerse en «Agregar prueba».

### Tests for User Story 2 ⚠️ (escribir primero, deben fallar)

- [ ] T019 [P] [US2] Agregar en `estudios/tests/test_servicio_pruebas.py`:
  - `test_quitar_prueba_borra_asignacion`: `quitar_prueba(estudio.pk, asignacion.pk, empleado)` devuelve la `Prueba` TEST-A y la asignación ya no existe; TEST-B sigue.
  - `test_prueba_quitada_puede_agregarse_de_nuevo`: quitar TEST-A y volver a agregarla crea una asignación nueva con otro `pk`.
  - `test_quitar_no_modifica_cabecera_tipo_ni_otros_estudios`: con la misma función auxiliar de T010, quita TEST-A y verifica que la cabecera, los snapshots, el tipo y el segundo estudio no cambiaron.
- [ ] T020 [P] [US2] Agregar en `estudios/tests/test_gestion_pruebas.py`:
  - `test_detalle_ofrece_quitar_en_pruebas_quitables`: con TEST-A y TEST-B, cada fila tiene el enlace a `estudios:quitar_prueba` de su asignación.
  - `test_quitar_get_muestra_confirmacion_sin_borrar`: GET `estudios:quitar_prueba` → 200 con «Se quitará la prueba TEST-A · Prueba de test A del estudio N», el enlace **Cancelar** al `href` de `estudios:detalle`, y la asignación sigue existiendo (SC-005).
  - `test_confirmar_quita_prueba`: POST → 302 a `detalle`, mensaje «Prueba TEST-A · Prueba de test A quitada del estudio N.», la asignación no existe y TEST-A aparece en `estudios:agregar_prueba`.

### Implementation for User Story 2

- [ ] T021 [US2] Implementar `quitar_prueba(estudio_pk, asignacion_pk, usuario)` en `estudios/servicios.py`: misma comprobación de sesión que `agregar_prueba`; dentro de `transaction.atomic()`: `select_for_update()` del estudio (None → `GestionPruebasError("El estudio no está disponible.")`), `estudio.pruebas_asignadas.select_related("prueba").filter(pk=asignacion_pk).first()` (None → `PruebaYaQuitada("La prueba ya no forma parte del estudio.")`), `asignacion.delete()` y devolver `asignacion.prueba` (research R3, R7) (depende de T005).
- [ ] T022 [US2] Crear la vista `quitar_prueba(request, pk, asignacion_pk)` en `estudios/views.py` según `contracts/pruebas-estudio-ui.md`: GET → 404 si el estudio no existe; asignación inexistente o de otro estudio → 302 a `detalle` + `messages.info("La prueba ya no forma parte del estudio.")`; si no, `estudios/quitar_prueba_confirmar.html`. POST → `quitar_prueba(...)`, éxito y 302 a `detalle`; `PruebaYaQuitada` → `messages.info`; otro `GestionPruebasError` → `messages.error`; `DatabaseError` → «No se pudo quitar la prueba. Intentá nuevamente.». Registrar `path("<int:pk>/pruebas/<int:asignacion_pk>/quitar/", views.quitar_prueba, name="quitar_prueba")` en `estudios/urls.py` (depende de T021).
- [ ] T023 [P] [US2] Crear `estudios/templates/estudios/quitar_prueba_confirmar.html`: título «Quitar prueba del estudio», «Se quitará la prueba `código · nombre` del estudio N (muestra PI X). No se realizará ni se incluirá en el informe.», `<form method="post">` con `{% csrf_token %}` y botón **Quitar prueba** (`btn btn-danger`), y enlace **Cancelar** a `detalle` (depende de T022).
- [ ] T024 [US2] En `estudios/templates/estudios/detalle.html`, completar la columna Acción con el botón-enlace **Quitar** (`btn btn-sm btn-outline-danger`) a `estudios:quitar_prueba` de cada asignación, visible si `estudio.admite_modificaciones` (depende de T007, T022).
- [ ] T025 [US2] Ejecutar `docker compose exec web pytest estudios` y dejar en verde T019–T020 sin romper US1 (depende de T021–T024).

**Checkpoint**: US 5.3 y US 5.4 funcionan; falta blindar las reglas de US3.

---

## Phase 5: User Story 3 - Impedir modificaciones no permitidas (Priority: P2)

**Goal**: rechazar duplicados, quitas de pruebas con mediciones, la quita de la última prueba,
cambios en estudios no modificables y reenvíos, también ante envíos simultáneos.

**Independent Test**: intentar agregar una prueba ya asignada, quitar la última prueba, quitar una
prueba con `puede_quitarse()` falso, modificar un estudio no modificable y reenviar
confirmaciones; verificar mensajes y que el estudio no cambia indebidamente.

### Tests for User Story 3 ⚠️ (escribir primero, deben fallar)

- [ ] T026 [P] [US3] Agregar en `estudios/tests/test_servicio_pruebas.py`:
  - `test_agregar_prueba_ya_asignada_rechazada`: `agregar_prueba` con TEST-A lanza `PruebaYaAsignada` y sigue habiendo una sola asignación de TEST-A.
  - `test_ultima_prueba_no_se_puede_quitar`: quitar TEST-B y luego TEST-A → `UltimaPrueba` con «El estudio debe conservar al menos una prueba.»; TEST-A sigue asignada (FR-014).
  - `test_quitar_rechaza_prueba_con_mediciones`: con `monkeypatch.setattr(PruebaEstudio, "puede_quitarse", lambda self: False)` → `GestionPruebasError` con «La prueba tiene mediciones o resultados cargados y no se puede quitar.» y la asignación sigue (FR-007).
  - `test_estudio_no_modificable_rechaza_cambios`: con `monkeypatch.setattr(Estudio, "admite_modificaciones", property(lambda self: False))`, `agregar_prueba` y `quitar_prueba` lanzan `GestionPruebasError` con «Este estudio ya no admite cambios en sus pruebas.» y las asignaciones no cambian (FR-003).
- [ ] T027 [P] [US3] Agregar en `estudios/tests/test_gestion_pruebas.py`:
  - `test_vistas_gestion_pruebas_requieren_sesion` (parametrizado: GET y POST de `detalle`, `agregar_prueba` y `quitar_prueba`): sin sesión → 302 al login y sin cambios (FR-001).
  - `test_revisar_prueba_ya_asignada_da_error_en_campo`: POST `accion=revisar` con TEST-A → 200 con error en el campo `prueba`.
  - `test_reenvio_confirmar_agregar_no_duplica`: dos POST `accion=confirmar` con TEST-C → el segundo redirige con «La prueba TEST-C ya forma parte del estudio.» (nivel info) y hay una sola asignación (FR-013).
  - `test_reenvio_confirmar_quitar_informa_ya_quitada`: dos POST a `quitar_prueba` de la misma asignación → el segundo redirige con «La prueba ya no forma parte del estudio.» (nivel info).
  - `test_detalle_no_ofrece_quitar_ultima_prueba`: con una sola asignación, el detalle no tiene enlace a `quitar_prueba` y muestra «El estudio debe conservar al menos una prueba.».
  - `test_agregar_prueba_inexistente_rechazada`: POST `accion=revisar` y `accion=confirmar` con `prueba=999999` → 200 con error en el campo `prueba` y sin asignaciones nuevas (US3 Esc. 7).
  - `test_vistas_estudio_no_modificable_redirigen`: con `monkeypatch.setattr(Estudio, "admite_modificaciones", property(lambda self: False))`, GET de `agregar_prueba` y de `quitar_prueba` → 302 a `detalle` con «Este estudio ya no admite cambios en sus pruebas.»; el detalle muestra esa alerta y no ofrece **Agregar prueba** ni **Quitar**.
  - `test_estudio_inexistente_responde_404`: GET `detalle`, `agregar_prueba` y `quitar_prueba` con un `pk` inexistente → 404.
  - `test_quitar_asignacion_de_otro_estudio_rechazada`: GET y POST de `quitar_prueba` con el `pk` del estudio A y una asignación del estudio B → 302 al detalle de A con «La prueba ya no forma parte del estudio.» y la asignación de B sigue.
- [ ] T028 [P] [US3] Crear `estudios/tests/test_concurrencia_pruebas.py` (`pytestmark = pytest.mark.django_db(transaction=True)`, mismo esquema de hilos, `threading.Barrier`, `close_old_connections` y `connection.close()` que `estudios/tests/test_concurrencia.py`):
  - `test_agregados_concurrentes_no_duplican`: dos hilos llaman a `agregar_prueba` con TEST-C sobre el mismo estudio; uno devuelve la asignación, el otro lanza `PruebaYaAsignada`; queda una sola asignación.
  - `test_quitas_concurrentes_conservan_una_prueba`: con TEST-A y TEST-B, dos hilos quitan cada una; uno tiene éxito, el otro lanza `UltimaPrueba`; queda exactamente una asignación.
  - `test_quitas_concurrentes_misma_asignacion`: con TEST-A, TEST-B y TEST-C, dos hilos quitan la misma asignación de TEST-A; uno devuelve la prueba, el otro lanza `PruebaYaQuitada`; quedan TEST-B y TEST-C.

### Implementation for User Story 3

- [ ] T029 [US3] Completar `agregar_prueba` en `estudios/servicios.py`: después de bloquear el estudio, `if not estudio.admite_modificaciones: raise GestionPruebasError("Este estudio ya no admite cambios en sus pruebas.")`; si `estudio.pruebas_asignadas.filter(prueba_id=prueba_pk).exists()` → `PruebaYaAsignada(f"La prueba {prueba.codigo} ya forma parte del estudio.")`; envolver el `create` en `transaction.atomic()` anidado y traducir el `IntegrityError` en el mismo `PruebaYaAsignada` (research R4) (depende de T012).
- [ ] T030 [US3] Completar `quitar_prueba` en `estudios/servicios.py`: después de bloquear el estudio, la misma comprobación de `admite_modificaciones`; antes de borrar, si `estudio.pruebas_asignadas.count() <= 1` → `UltimaPrueba("El estudio debe conservar al menos una prueba.")`; si `not asignacion.puede_quitarse()` → `GestionPruebasError("La prueba tiene mediciones o resultados cargados y no se puede quitar.")`; traducir `ProtectedError` del `delete()` en ese mismo error (depende de T021).
- [ ] T031 [US3] En `estudios/views.py`: `agregar_prueba` maneja `PruebaYaAsignada` con `messages.info` y `GET` de un estudio no modificable redirige a `detalle` con «Este estudio ya no admite cambios en sus pruebas.»; `quitar_prueba` (GET) redirige a `detalle` con el mensaje de error correspondiente si el estudio no es modificable, si es la última prueba o si `puede_quitarse()` es falso (depende de T014, T022, T029, T030).
- [ ] T032 [US3] En `estudios/templates/estudios/detalle.html`, mostrar **Quitar** solo si además `asignacion.puede_quitarse` y el estudio tiene más de una asignación; con una sola, mostrar «El estudio debe conservar al menos una prueba.» en su lugar (la vista pasa `puede_quitar_alguna = len(asignaciones) > 1`) (depende de T024).
- [ ] T033 [US3] Ejecutar `docker compose exec web pytest estudios` y dejar en verde T026–T028 junto con US1 y US2 (depende de T029–T032).

**Checkpoint**: las tres historias funcionan y las reglas resisten reenvíos y concurrencia.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [ ] T034 [P] Ejecutar `docker compose exec web ruff check .`, `docker compose exec web ruff format --check .` y `docker compose exec web python manage.py makemigrations --check --dry-run`, y corregir lo que aparezca (Principios III y VI).
- [ ] T035 Ejecutar la suite completa `docker compose exec web pytest` y confirmar todo en verde.
- [ ] T036 Recorrer los pasos 1 a 8 de validación manual de `specs/009-gestionar-pruebas-estudio/quickstart.md` y cronometrar un agregado y una quita desde el detalle: menos de 1 minuto cada uno (SC-006).
- [ ] T037 [P] Agregar en `CLAUDE.md` una sección breve "Pruebas de un estudio (US 5.3 y 5.4)" con lo no obvio: los servicios `agregar_prueba` y `quitar_prueba` bloquean la fila del estudio (`select_for_update`) para sostener la regla de al menos una prueba; quitar borra la asignación (sin historial); **US 6.1** debe hacer que `PruebaEstudio.puede_quitarse()` devuelva `False` con mediciones o resultados y referenciar `PruebaEstudio` con `PROTECT`; **US 5.2** debe ampliar `estudios:detalle` en vez de crear otra vista; la columna Estado de cada prueba es el texto fijo «Pendiente» hasta que US 5.2 / 6.4 agreguen el estado por prueba. No tocar el pendiente del envío de informes por correo.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: `T001`.
- **Foundational (Phase 2)**: depende de la fase 1. `T002` y `T005` en paralelo; `T003` tras `T002`; `T004` → `T006` → `T007`, `T008`; `T009` al final. Bloquea todas las historias.
- **US1 (Phase 3)**: depende de la fase 2. Es el MVP.
- **US2 (Phase 4)**: depende de la fase 2. Puede hacerse en paralelo con US1, salvo `T024`, que edita `detalle.html` después de `T017`, y los tests que comparten archivo con US1.
- **US3 (Phase 5)**: depende de US1 y US2 (completa sus servicios, vistas y el detalle).
- **Polish (Phase 6)**: depende de las tres historias.

### Dentro de cada historia

- Tests primero y fallando; luego servicio → formulario → vista + url → templates.
- `test_servicio_pruebas.py`, `test_gestion_pruebas.py`, `servicios.py`, `views.py` y `detalle.html` se tocan en varias fases: las tareas que comparten archivo van en secuencia.

### Grafo

```text
T001 → T002 ─→ T003 ─┐
       T005 ─────────┤
       T004 → T006 ─┬┴→ T007 ─┐
                    └─→ T008 ─┴─→ T009
                                   │
          ┌────────────────────────┘
          ▼
US1: T010, T011 → T012, T013 → T014 → T015, T016, T017 → T018
US2: T019, T020 → T021 → T022 → T023, T024 → T025
US3: T026, T027, T028 → T029, T030 → T031 → T032 → T033
Polish: T034, T035, T036, T037
```

---

## Parallel Example: User Story 1

```bash
# Tests de US1 en paralelo (archivos distintos):
Task T010: "Tests del servicio en estudios/tests/test_servicio_pruebas.py"
Task T011: "Tests de vistas en estudios/tests/test_gestion_pruebas.py"

# Templates de US1 en paralelo, después de T014:
Task T015: "Template estudios/templates/estudios/agregar_prueba.html"
Task T016: "Template estudios/templates/estudios/agregar_prueba_confirmar.html"
```

## Parallel Example: User Story 3

```bash
Task T026: "Reglas en estudios/tests/test_servicio_pruebas.py"
Task T027: "Reglas y reenvíos en estudios/tests/test_gestion_pruebas.py"
Task T028: "Concurrencia en estudios/tests/test_concurrencia_pruebas.py"
```

---

## Implementation Strategy

### En dos tandas (según `docs/guias/guia-sdd-paso-a-paso.md`)

1. **Tanda 1 (Fases 1 y 2 — `T001` a `T009`)**: reglas del modelo, excepciones, fixtures, detalle
   de solo lectura y enlace desde el mensaje de US 5.1; suite en verde. Frenar y revisar.
2. **Tanda 2 (Fases 3 a 6 — `T010` a `T037`)**: US1 (agregar, MVP), US2 (quitar) y US3 (reglas,
   reenvíos y concurrencia), cada una con sus tests escritos primero; cerrar con `ruff`, suite
   completa, recorrido manual y nota en `CLAUDE.md`.

### MVP

Fases 1–3 (US1): ya permite personalizar un estudio agregando pruebas. US2 y US3 deben entrar en el
mismo PR: sin US3, quitar podría dejar un estudio sin pruebas (FR-014).
