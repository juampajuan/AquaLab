---

description: "Lista de tareas de la US 5.3 – Agregar prueba al estudio"
---

# Tasks: Agregar prueba al estudio

**Input**: `specs/010-agregar-prueba-estudio/` (`plan.md`, `spec.md`, `research.md`,
`data-model.md`, `contracts/agregar-prueba-ui.md`, `quickstart.md`)

**Prerequisites**: `plan.md`, `spec.md`. Ya existen y no se recrean (US 5.1, PR #12):
`estudios.Estudio`, `estudios.PruebaEstudio` (`related_name="pruebas_asignadas"`,
`UniqueConstraint(estudio, prueba)` llamada `estudio_prueba_unica`), `estudios.EstadoEstudio`,
`pruebas.Prueba`, `estudios/servicios.py:crear_estudio`, `estudios/views.py:exito`,
`estudios/tests/conftest.py` (fixtures `empleado`, `cliente_a`, `muestra`, `pruebas`, `tipo`,
`datos`, `cliente_http`), `LoginRequiredMiddleware` y `templates/base.html`.

**Tests**: SÍ. La constitution (Principio III) exige al menos un test con pytest-django por cada
escenario de aceptación. Los tests siguen el "Mapa de tests" de `plan.md` y se escriben **antes** de
la implementación de cada historia (deben fallar primero).

**Organization**: dos user stories de la spec — US1 (P1, agregar una prueba) y US2 (P2, impedir
agregados no permitidos).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: se puede ejecutar en paralelo (archivos distintos, sin dependencias pendientes)
- **[Story]**: user story a la que pertenece la tarea (`[US1]`, `[US2]`)
- Rutas relativas a la raíz del repo

## Convenciones para todas las tareas

- Textos de UI, mensajes y nombres de dominio en **español** (Principio VI).
- Mensajes al usuario copiados **literalmente** de `contracts/agregar-prueba-ui.md`.
- Estilo de vistas y formularios igual al de US 5.1: vistas de función en `estudios/views.py`,
  `CrearEstudioForm` en `estudios/forms.py` (clase `form-select`). Templates con el diseño de
  SCRUM-67 como `estudios/templates/estudios/crear_*.html`: `ui/encabezado.html`, `ui/campo.html`,
  `<dl class="resumen" data-componente="resumen">` y botones con `data-componente="acciones-confirmacion"`.
- **Actualización 2026-10-28**: la rama es `010-agregar-prueba-v2` (parte de `013-diseno-ui`). La
  ficha del estudio ya existe (US 5.2): T006 queda cubierta y T007 pasa a ampliar esa ficha.
- **Sin migraciones**: ninguna tarea cambia campos ni constraints (ver `data-model.md`).
- Comandos dentro de Docker: `docker compose exec web pytest estudios`,
  `docker compose exec web ruff check .`, `docker compose exec web ruff format --check .`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: aprobación de la spec y base de US 5.1 sana antes de tocar código.

- [X] T001 **Gate de la constitution (Principio I)**: confirmar que el equipo aprobó `specs/010-agregar-prueba-estudio/spec.md` y actualizar su `**Status**` a «Aprobada por el equipo» con la fecha; sin aprobación no se ejecuta ninguna otra tarea. Después, verificar el entorno con `docker compose up -d`, `docker compose exec web python manage.py migrate` y `docker compose exec web pytest` (sobre `docker-compose.yml`) y confirmar que la suite actual pasa y que `docker compose exec web python manage.py makemigrations --check --dry-run` no detecta cambios.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: regla del modelo, excepciones, fixtures y detalle de solo lectura del estudio.

**⚠️ CRITICAL**: ninguna historia empieza antes de terminar esta fase.

- [X] T002 [P] Agregar en `estudios/tests/conftest.py` las fixtures:
  - `estudio(datos, empleado)`: crea un estudio con `crear_estudio(datos, empleado)` (queda con las pruebas `TEST-A` y `TEST-B` del fixture `tipo`).
  - `prueba_extra()`: `Prueba.objects.create(codigo="TEST-C", nombre="Prueba de test C")`, que no está en el tipo.
- [X] T003 [P] Agregar en `estudios/tests/test_modelos.py` `test_admite_modificaciones_solo_pendiente_analisis`: un estudio recién creado admite modificaciones; con `estado` forzado a otro valor en memoria, no (depende de T002).
- [X] T004 Agregar en `estudios/models.py`, en `Estudio`, la propiedad `admite_modificaciones` que devuelve `self.estado == EstadoEstudio.PENDIENTE_ANALISIS` (FR-003, research R4). Sin cambiar campos ni `Meta`; verificar que `makemigrations --check --dry-run` siga sin cambios.
- [X] T005 [P] Agregar en `estudios/servicios.py`, debajo de `crear_estudio`, `GestionPruebasError(Exception)` y su subclase `PruebaYaAsignada`; el mensaje de cada excepción es el texto que ve el empleado (plan, "Servicio"). US 5.4 sumará otras subclases.
- [X] T006 ~~Crear la vista `detalle`~~ Cubierta por US 5.2: `estudios.views.detalle` y la ruta `estudios:detalle` ya existen en `main`.
- [X] T007 En `estudios/templates/estudios/detalle.html` (existente, US 5.2), sección **Pruebas asignadas**: sumar la columna **Acción** a la derecha de la tabla (vacía en esta historia; la completa US 5.4) y, si `not estudio.admite_modificaciones`, el aviso «Este estudio ya no admite cambios en sus pruebas.» (depende de T004).
- [X] T008 Cambiar `exito` en `estudios/views.py` para que el mensaje sea `format_html('<a href="{}">Estudio {}</a> creado para la muestra PI {}.', reverse("estudios:detalle", args=[estudio.pk]), estudio.pk, estudio.muestra.numero_pi)`, sin cambiar la redirección a `estudios:crear` (research R1).
- [X] T009 Ejecutar `docker compose exec web pytest estudios` y dejar en verde T003 junto con los tests existentes de US 5.1 (depende de T002–T008).

**Checkpoint**: el detalle del estudio se ve desde el mensaje de éxito; las historias pueden empezar.

---

## Phase 3: User Story 1 - Agregar una prueba adicional a un estudio (Priority: P1) 🎯 MVP

**Goal**: desde el detalle, elegir una prueba del catálogo que el estudio no tenga, confirmar y
dejarla asignada una sola vez como pendiente.

**Independent Test**: con el fixture `estudio` (TEST-A, TEST-B) y `prueba_extra` (TEST-C), agregar
TEST-C con revisar → confirmar y verificar que figura una vez en el detalle, sin cambios en la
cabecera, los snapshots ni el tipo.

### Tests for User Story 1 ⚠️ (escribir primero, deben fallar)

- [X] T010 [P] [US1] Crear `estudios/tests/test_servicio_pruebas.py` (`pytestmark = pytest.mark.django_db`) con:
  - `test_agregar_prueba_crea_asignacion`: `agregar_prueba(estudio.pk, prueba_extra.pk, empleado)` crea una `PruebaEstudio` en estado `EstadoPruebaEstudio.PENDIENTE` y el estudio queda con TEST-A, TEST-B y TEST-C (FR-006).
  - `test_agregar_no_modifica_cabecera_tipo_ni_otros_estudios`: guarda `muestra_id`, `tipo_id`, `estado`, `creado_por_id`, `fecha_creacion`, `tipo_nombre_snapshot`, `tipo_descripcion_snapshot`, `tipo_version_snapshot` del estudio, las pruebas y `version` del tipo, y las pruebas de un segundo estudio del mismo tipo; agrega TEST-C y verifica que nada de eso cambió. Extraer la captura de esos datos a una función auxiliar del archivo (`capturar_estado(estudio, otro)`) para que US 5.4 la reutilice.
- [X] T011 [P] [US1] Crear `estudios/tests/test_agregar_prueba.py` (`pytestmark = pytest.mark.django_db`) con:
  - `test_detalle_ofrece_agregar_prueba`: GET `estudios:detalle` → 200 con TEST-A, TEST-B y el enlace a `estudios:agregar_prueba` (la cabecera ya la prueban los tests de US 5.2).
  - `test_exito_creacion_enlaza_al_detalle`: confirmar una creación por la vista de US 5.1 deja un mensaje que contiene el `href` de `estudios:detalle` del estudio creado.
  - `test_agregar_ofrece_solo_pruebas_no_asignadas`: GET `estudios:agregar_prueba` → 200 con TEST-C entre las opciones y sin TEST-A ni TEST-B.
  - `test_revisar_muestra_confirmacion_sin_guardar`: POST `accion=revisar`, `prueba=<TEST-C>` → 200 con «Se agregará la prueba», el enlace **Cancelar** al `href` de `estudios:detalle` y sin nuevas `PruebaEstudio` (cancelar es volver al detalle sin enviar nada: SC-004).
  - `test_confirmar_agrega_prueba_una_vez`: POST `accion=confirmar` → 302 a `detalle`, mensaje «Prueba TEST-C · Prueba de test C agregada al estudio N.» y TEST-C asignada una sola vez.
  - `test_agregar_sin_pruebas_disponibles_informa`: sin otras pruebas en el catálogo (sin `prueba_extra`) → «No hay pruebas disponibles para agregar: todas ya forman parte del estudio.» y sin formulario.
  - `test_error_de_base_al_agregar_no_cambia_estudio`: con `agregar_prueba` parcheado para lanzar `DatabaseError`, POST `accion=confirmar` → 302 a `detalle` con «No se pudo agregar la prueba. Intentá nuevamente.» y sin asignaciones nuevas.

### Implementation for User Story 1

- [X] T012 [US1] Implementar `agregar_prueba(estudio_pk, prueba_pk, usuario)` en `estudios/servicios.py`: rechaza con `GestionPruebasError("Se requiere una sesión activa.")` si `not usuario.is_authenticated or not usuario.is_active`; dentro de `transaction.atomic()`: `Estudio.objects.select_for_update().filter(pk=estudio_pk).first()` (None → `GestionPruebasError("El estudio no está disponible.")`), `Prueba.objects.filter(pk=prueba_pk).first()` (None → `GestionPruebasError("La prueba no está disponible.")`) y `PruebaEstudio.objects.create(estudio=estudio, prueba=prueba)`; devuelve la asignación (depende de T005).
- [X] T013 [US1] Crear `AgregarPruebaForm(forms.Form)` en `estudios/forms.py`: `__init__(self, *args, estudio, **kwargs)` define `prueba = forms.ModelChoiceField(queryset=Prueba.objects.exclude(pk__in=estudio.pruebas_asignadas.values("prueba")), label="Prueba", empty_label="Elegí una prueba")` con `widget.attrs["class"] = "form-select"` (research R5).
- [X] T014 [US1] Crear la vista `agregar_prueba(request, pk)` en `estudios/views.py` según `contracts/agregar-prueba-ui.md` ("GET/POST /estudios/<pk>/pruebas/agregar/"): GET → formulario, o la alerta de «sin pruebas disponibles» si el queryset está vacío; POST `accion=revisar` → formulario inválido (200 con error) o `estudios/agregar_prueba_confirmar.html`; POST `accion=confirmar` → revalida el formulario (inválido → 200 con error) y llama a `agregar_prueba`, mensaje de éxito y 302 a `detalle`; `GestionPruebasError` → `messages.error(str(exc))`; `DatabaseError` → «No se pudo agregar la prueba. Intentá nuevamente.»; otra `accion` → «La acción no es válida.». Registrar `path("<int:pk>/pruebas/agregar/", views.agregar_prueba, name="agregar_prueba")` en `estudios/urls.py` (depende de T012, T013).
- [X] T015 [P] [US1] Crear `estudios/templates/estudios/agregar_prueba.html` con el diseño de SCRUM-67: `ui/encabezado.html` (migas Estudios > Estudio N > Agregar prueba, título «Agregar prueba al estudio N», subtítulo con la muestra PI), `<form method="post">` con `{% csrf_token %}`, el campo `prueba` con `ui/campo.html`, botón **Revisar** (`name="accion" value="revisar"`) y enlace **Cancelar** a `detalle`; si no hay pruebas para ofrecer, `ui/estado_vacio.html` con «No hay pruebas disponibles para agregar: todas ya forman parte del estudio.» y acción «Volver al estudio» en lugar del formulario (depende de T014).
- [X] T016 [P] [US1] Crear `estudios/templates/estudios/agregar_prueba_confirmar.html` como `crear_confirmar.html`: aviso «Se agregará la prueba `código · nombre` al estudio N (muestra PI X).», resumen con `data-componente="resumen"`, `<input type="hidden" name="prueba">` y botones con `data-componente="acciones-confirmacion"`: **Confirmar** (`accion=confirmar`), **Volver** (a `estudios:agregar_prueba`) y **Cancelar** (a `detalle`) (depende de T014).
- [X] T017 [US1] En la sección **Pruebas asignadas** de `estudios/templates/estudios/detalle.html`, agregar el botón **Agregar prueba** a `estudios:agregar_prueba`, visible solo si `estudio.admite_modificaciones` (depende de T007, T014).
- [X] T018 [US1] Ejecutar `docker compose exec web pytest estudios` y dejar en verde T010–T011 (depende de T012–T017).

**Checkpoint**: se puede agregar una prueba con confirmación.

---

## Phase 4: User Story 2 - Impedir agregados no permitidos (Priority: P2)

**Goal**: rechazar duplicados, agregados en estudios no modificables y reenvíos, también ante
envíos simultáneos.

**Independent Test**: intentar agregar una prueba ya asignada, agregar en un estudio no modificable
y reenviar la confirmación; verificar mensajes y que el estudio no cambia indebidamente.

### Tests for User Story 2 ⚠️ (escribir primero, deben fallar)

- [X] T019 [P] [US2] Agregar en `estudios/tests/test_servicio_pruebas.py`:
  - `test_agregar_prueba_ya_asignada_rechazada`: `agregar_prueba` con TEST-A lanza `PruebaYaAsignada` y sigue habiendo una sola asignación de TEST-A.
  - `test_estudio_no_modificable_rechaza_agregar` (parametrizado con los estados de US 5.2 `en_proceso`, `finalizado` e `informe_generado`, guardados en la base): `agregar_prueba` lanza `GestionPruebasError` con «Este estudio ya no admite cambios en sus pruebas.» y las asignaciones no cambian (FR-003).
- [X] T020 [P] [US2] Agregar en `estudios/tests/test_agregar_prueba.py`:
  - `test_vistas_agregar_prueba_requieren_sesion` (parametrizado: GET de `detalle`, GET y POST de `agregar_prueba`): sin sesión → 302 al login y sin cambios (FR-001).
  - `test_revisar_prueba_ya_asignada_da_error_en_campo`: POST `accion=revisar` con TEST-A → 200 con error en el campo `prueba`.
  - `test_reenvio_confirmar_agregar_no_duplica`: dos POST `accion=confirmar` con TEST-C → el segundo redirige con «La prueba TEST-C ya forma parte del estudio.» (nivel info) y hay una sola asignación (FR-011).
  - `test_agregar_prueba_inexistente_rechazada`: POST `accion=revisar` y `accion=confirmar` con `prueba=999999` → 200 con error en el campo `prueba` y sin asignaciones nuevas.
  - `test_vistas_estudio_no_modificable_no_ofrecen_agregar`: con el estudio guardado en `en_proceso`, GET de `agregar_prueba` → 302 a `detalle` con «Este estudio ya no admite cambios en sus pruebas.»; el detalle muestra ese aviso y no ofrece **Agregar prueba**.
  - `test_estudio_inexistente_responde_404`: GET `detalle` y `agregar_prueba` con un `pk` inexistente → 404.
- [X] T021 [P] [US2] Crear `estudios/tests/test_concurrencia_pruebas.py` (`pytestmark = pytest.mark.django_db(transaction=True)`, mismo esquema de hilos, `threading.Barrier`, `close_old_connections` y `connection.close()` que `estudios/tests/test_concurrencia.py`) con `test_agregados_concurrentes_no_duplican`: dos hilos llaman a `agregar_prueba` con TEST-C sobre el mismo estudio; uno devuelve la asignación, el otro lanza `PruebaYaAsignada`; queda una sola asignación.

### Implementation for User Story 2

- [X] T022 [US2] Completar `agregar_prueba` en `estudios/servicios.py`: después de bloquear el estudio, `if not estudio.admite_modificaciones: raise GestionPruebasError("Este estudio ya no admite cambios en sus pruebas.")`; si `estudio.pruebas_asignadas.filter(prueba_id=prueba_pk).exists()` → `PruebaYaAsignada(f"La prueba {prueba.codigo} ya forma parte del estudio.")`; envolver el `create` en un `transaction.atomic()` anidado y traducir el `IntegrityError` en el mismo `PruebaYaAsignada` (research R3) (depende de T012).
- [X] T023 [US2] En `estudios/views.py`, `agregar_prueba` maneja `PruebaYaAsignada` con `messages.info` y, en GET, redirige a `detalle` con «Este estudio ya no admite cambios en sus pruebas.» si el estudio no es modificable (depende de T014, T022).
- [X] T024 [US2] Ejecutar `docker compose exec web pytest estudios` y dejar en verde T019–T021 junto con US1 (depende de T022–T023).

**Checkpoint**: US 5.3 completa; las reglas resisten reenvíos y concurrencia.

---

## Phase 5: Polish & Cross-Cutting Concerns

- [X] T025 [P] Ejecutar `docker compose exec web ruff check .`, `docker compose exec web ruff format --check .` y `docker compose exec web python manage.py makemigrations --check --dry-run`, y corregir lo que aparezca (Principios III y VI).
- [X] T026 Ejecutar la suite completa `docker compose exec web pytest` y confirmar todo en verde.
- [ ] T027 Recorrer los pasos 1 a 7 de validación manual de `specs/010-agregar-prueba-estudio/quickstart.md` y cronometrar un agregado desde el detalle: menos de 1 minuto (SC-005).
- [X] T028 [P] Agregar en `CLAUDE.md` una sección breve "Pruebas de un estudio (US 5.3)" con lo no obvio: `agregar_prueba` bloquea la fila del estudio (`select_for_update`) y US 5.4 usa el mismo esquema; `Estudio.admite_modificaciones` es la única regla de estudio modificable; **US 5.4** completa la columna Acción de `estudios:detalle`; las pruebas agregadas nacen en estado Pendiente. No tocar el pendiente del envío de informes por correo.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: `T001`.
- **Foundational (Phase 2)**: depende de la fase 1. `T002` y `T005` en paralelo; `T003` tras `T002`; `T004` → `T007`; `T008` sin dependencias (T006 cubierta por US 5.2); `T009` al final. Bloquea las historias.
- **US1 (Phase 3)**: depende de la fase 2. Es el MVP.
- **US2 (Phase 4)**: depende de US1 (completa su servicio y su vista).
- **Polish (Phase 5)**: depende de las dos historias.
- **US 5.4** (`specs/011-quitar-prueba-estudio/`): depende de esta historia completa.

### Dentro de cada historia

- Tests primero y fallando; luego servicio → formulario → vista + url → templates.
- `test_servicio_pruebas.py`, `test_agregar_prueba.py`, `servicios.py`, `views.py` y `detalle.html` se tocan en varias fases: las tareas que comparten archivo van en secuencia.

### Grafo

```text
T001 → T002 ─→ T003 ─┐
       T005 ─────────┤
       T004 ──────┬┴→ T007 ─┐
                    └─→ T008 ─┴─→ T009
                                   │
          ┌────────────────────────┘
          ▼
US1: T010, T011 → T012, T013 → T014 → T015, T016, T017 → T018
US2: T019, T020, T021 → T022 → T023 → T024
Polish: T025, T026, T027, T028
```

---

## Parallel Example: User Story 1

```bash
# Tests de US1 en paralelo (archivos distintos):
Task T010: "Tests del servicio en estudios/tests/test_servicio_pruebas.py"
Task T011: "Tests de vistas en estudios/tests/test_agregar_prueba.py"

# Templates de US1 en paralelo, después de T014:
Task T015: "Template estudios/templates/estudios/agregar_prueba.html"
Task T016: "Template estudios/templates/estudios/agregar_prueba_confirmar.html"
```

## Parallel Example: User Story 2

```bash
Task T019: "Reglas en estudios/tests/test_servicio_pruebas.py"
Task T020: "Reglas y reenvíos en estudios/tests/test_agregar_prueba.py"
Task T021: "Concurrencia en estudios/tests/test_concurrencia_pruebas.py"
```

---

## Implementation Strategy

### En dos tandas (según `docs/guias/guia-sdd-paso-a-paso.md`)

1. **Tanda 1 (Fases 1 y 2 — `T001` a `T009`)**: aprobación, regla del modelo, excepciones,
   fixtures, detalle de solo lectura y enlace desde el mensaje de US 5.1; suite en verde. Frenar y
   revisar.
2. **Tanda 2 (Fases 3 a 5 — `T010` a `T028`)**: US1 (agregar, MVP) y US2 (reglas, reenvíos y
   concurrencia), cada una con sus tests escritos primero; cerrar con `ruff`, suite completa,
   recorrido manual y nota en `CLAUDE.md`.

### MVP

Fases 1–3 (US1): ya permite personalizar un estudio agregando pruebas. US2 entra en el mismo PR.
