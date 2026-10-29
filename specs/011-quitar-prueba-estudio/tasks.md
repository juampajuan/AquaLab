---

description: "Lista de tareas de la US 5.4 – Quitar prueba del estudio"
---

# Tasks: Quitar prueba del estudio

**Input**: `specs/011-quitar-prueba-estudio/` (`plan.md`, `spec.md`, `research.md`,
`data-model.md`, `contracts/quitar-prueba-ui.md`, `quickstart.md`)

**Prerequisites**: `plan.md`, `spec.md` y **US 5.3 implementada** (`specs/010-agregar-prueba-estudio/`):
`estudios:detalle` y `estudios/templates/estudios/detalle.html` (con la columna Acción vacía),
`Estudio.admite_modificaciones`, `GestionPruebasError` y `PruebaYaAsignada`, `agregar_prueba`,
las fixtures `estudio` y `prueba_extra`, la función auxiliar `capturar_estado` de
`estudios/tests/test_servicio_pruebas.py` y `estudios/tests/test_concurrencia_pruebas.py`.

**Tests**: SÍ. La constitution (Principio III) exige al menos un test con pytest-django por cada
escenario de aceptación. Los tests siguen el "Mapa de tests" de `plan.md` y se escriben **antes** de
la implementación de cada historia (deben fallar primero).

**Organization**: dos user stories de la spec — US1 (P1, quitar una prueba) y US2 (P2, impedir
quitas no permitidas).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: se puede ejecutar en paralelo (archivos distintos, sin dependencias pendientes)
- **[Story]**: user story a la que pertenece la tarea (`[US1]`, `[US2]`)
- Rutas relativas a la raíz del repo

## Convenciones para todas las tareas

- Textos de UI, mensajes y nombres de dominio en **español** (Principio VI).
- Mensajes al usuario copiados **literalmente** de `contracts/quitar-prueba-ui.md`.
- Mismo estilo que las vistas y templates de US 5.3 (`agregar_prueba`, `agregar_prueba_confirmar.html`):
  diseño de SCRUM-67 con `ui/encabezado.html`, `<dl class="resumen" data-componente="resumen">` y
  botones con `data-componente="acciones-confirmacion"`.
- **Actualización 2026-10-28**: la rama es `011-quitar-prueba-v2`, que sale de `010-agregar-prueba-v2`
  (US 5.3 implementada sobre US 5.2 y SCRUM-67). Jira: SCRUM-51. «Mediciones o resultados» se lee del
  estado individual de la prueba de US 5.2 (`Cargada` / `Completada`); solo `Pendiente` se quita.
- La vista `quitar_prueba` tapa el nombre del servicio, como en US 5.3: llama a
  `servicios.quitar_prueba` y los tests parchean `estudios.servicios.quitar_prueba`.
- **Sin migraciones**: ninguna tarea cambia campos ni constraints (ver `data-model.md`).
- Comandos dentro de Docker: `docker compose exec web pytest estudios`,
  `docker compose exec web ruff check .`, `docker compose exec web ruff format --check .`.

---

## Phase 1: Setup (Shared Infrastructure)

- [ ] T001 **Gate de la constitution (Principio I)**: confirmar que el equipo aprobó `specs/011-quitar-prueba-estudio/spec.md` y actualizar su `**Status**` a «Aprobada por el equipo» con la fecha, y que US 5.3 está implementada y en verde en esta rama (sale de `010-agregar-prueba-v2`); sin ambas condiciones no se ejecuta ninguna otra tarea. Después, ejecutar `docker compose exec web pytest` y `docker compose exec web python manage.py makemigrations --check --dry-run` y confirmar suite en verde y sin cambios.

---

## Phase 2: Foundational (Blocking Prerequisites)

**⚠️ CRITICAL**: ninguna historia empieza antes de terminar esta fase.

- [X] T002 [P] Agregar en `estudios/tests/conftest.py` la fixture `asignacion(estudio)`: la `PruebaEstudio` de `TEST-A` del estudio.
- [X] T003 [P] Agregar en `estudios/tests/test_modelos.py` `test_puede_quitarse_solo_pendiente`: una asignación recién creada (`Pendiente`) devuelve `True`; con `estado` forzado en memoria a `Cargada` o `Completada`, `False` (depende de T002).
- [X] T004 Agregar en `estudios/models.py`, en `PruebaEstudio`, el método `puede_quitarse(self)` que devuelve `self.estado == EstadoPruebaEstudio.PENDIENTE`, con un docstring breve: `Cargada` y `Completada` indican mediciones o resultados; las historias del Epic 6 cambian ese estado y sus tablas deben referenciar a `PruebaEstudio` con `on_delete=PROTECT` (FR-004, research R4). Sin cambiar campos ni `Meta`.
- [X] T005 [P] Agregar en `estudios/servicios.py` las subclases `PruebaYaQuitada` y `UltimaPrueba` de `GestionPruebasError`.
- [X] T006 Ejecutar `docker compose exec web pytest estudios` y dejar en verde T003 junto con los tests de US 5.1 y US 5.3 (depende de T002–T005).

---

## Phase 3: User Story 1 - Quitar una prueba que no se va a realizar (Priority: P1) 🎯 MVP

**Goal**: desde el detalle, quitar una prueba del estudio después de una confirmación explícita.

**Independent Test**: con el fixture `estudio` (TEST-A, TEST-B), quitar TEST-A con confirmación y
verificar que ya no figura en el detalle y que vuelve a ofrecerse en «Agregar prueba».

### Tests for User Story 1 ⚠️ (escribir primero, deben fallar)

- [X] T007 [P] [US1] Agregar en `estudios/tests/test_servicio_pruebas.py`:
  - `test_quitar_prueba_borra_asignacion`: `quitar_prueba(estudio.pk, asignacion.pk, empleado)` devuelve la `Prueba` TEST-A y la asignación ya no existe; TEST-B sigue.
  - `test_quitar_no_modifica_cabecera_tipo_ni_otros_estudios`: con `capturar_estado` de US 5.3, quita TEST-A y verifica que la cabecera, los snapshots, el tipo y un segundo estudio del mismo tipo no cambiaron.
  - `test_prueba_quitada_puede_agregarse_de_nuevo`: quitar TEST-A y volver a agregarla con `agregar_prueba` crea una asignación nueva con otro `pk`; `quitar_prueba` con el `pk` viejo lanza `PruebaYaQuitada` y la nueva sigue.
- [X] T008 [P] [US1] Crear `estudios/tests/test_quitar_prueba.py` (`pytestmark = pytest.mark.django_db`) con:
  - `test_detalle_ofrece_quitar_en_pruebas_quitables`: con TEST-A y TEST-B, cada fila tiene el enlace a `estudios:quitar_prueba` de su asignación.
  - `test_quitar_get_muestra_confirmacion_sin_borrar`: GET `estudios:quitar_prueba` → 200 con «Se quitará la prueba TEST-A · Prueba de test A del estudio N», el enlace **Cancelar** al `href` de `estudios:detalle`, y la asignación sigue existiendo (SC-004).
  - `test_confirmar_quita_prueba`: POST → 302 a `detalle`, mensaje «Prueba TEST-A · Prueba de test A quitada del estudio N.», la asignación no existe y TEST-A aparece en `estudios:agregar_prueba`.
  - `test_error_de_base_al_quitar_no_cambia_estudio`: con `estudios.servicios.quitar_prueba` parcheado para lanzar `DatabaseError`, POST → 302 a `detalle` con «No se pudo quitar la prueba. Intentá nuevamente.» y la asignación sigue.

### Implementation for User Story 1

- [X] T009 [US1] Implementar `quitar_prueba(estudio_pk, asignacion_pk, usuario)` en `estudios/servicios.py`: misma comprobación de sesión que `agregar_prueba`; dentro de `transaction.atomic()`: `Estudio.objects.select_for_update().filter(pk=estudio_pk).first()` (None → `GestionPruebasError("El estudio no está disponible.")`), `estudio.pruebas_asignadas.select_for_update().select_related("prueba").filter(pk=asignacion_pk).first()` (None → `PruebaYaQuitada("La prueba ya no forma parte del estudio.")`), `asignacion.delete()` y devolver `asignacion.prueba` (research R1, R5) (depende de T005).
- [X] T010 [US1] Crear la vista `quitar_prueba(request, pk, asignacion_pk)` en `estudios/views.py` según `contracts/quitar-prueba-ui.md`: `get_object_or_404` del estudio; GET → asignación inexistente o de otro estudio → 302 a `detalle` + `messages.info("La prueba ya no forma parte del estudio.")`; si no, `estudios/quitar_prueba_confirmar.html`. POST → `servicios.quitar_prueba(...)`, éxito y 302 a `detalle`; `PruebaYaQuitada` → `messages.info`; otro `GestionPruebasError` → `messages.error`; `DatabaseError` → «No se pudo quitar la prueba. Intentá nuevamente.». Registrar `path("<int:pk>/pruebas/<int:asignacion_pk>/quitar/", views.quitar_prueba, name="quitar_prueba")` en `estudios/urls.py` (depende de T009).
- [X] T011 [P] [US1] Crear `estudios/templates/estudios/quitar_prueba_confirmar.html` como `agregar_prueba_confirmar.html` (SCRUM-67): `ui/encabezado.html` (migas Estudios › Estudio N › Quitar prueba, título «Quitar prueba del estudio»), aviso de advertencia «Se quitará la prueba `código · nombre` del estudio N (muestra PI X). No se realizará ni se incluirá en el informe.», resumen con `data-componente="resumen"` (estudio, muestra, prueba) y acciones con `data-componente="acciones-confirmacion"`: `<form method="post">` con `{% csrf_token %}` y botón **Quitar prueba** (`btn btn-peligro`), y enlace **Cancelar** (`btn btn-secundario`) a `detalle` (depende de T010).
- [X] T012 [US1] Agregar en `static/src/aqualab.css`, dentro de `@layer components` junto a los `.btn`, el componente `.btn-chico { @apply px-3 py-1.5 text-xs; }` y recompilar con `docker compose exec -u "$(id -u):$(id -g)" web tailwindcss -i static/src/aqualab.css -o static/css/aqualab.css --minify` (README). En `estudios/templates/estudios/detalle.html`, completar la columna Acción con el botón-enlace **Quitar** (`btn btn-peligro btn-chico`) a `estudios:quitar_prueba` de cada asignación, visible si `estudio.admite_modificaciones` (depende de T010).
- [X] T013 [US1] Ejecutar `docker compose exec web pytest estudios` y dejar en verde T007–T008 sin romper US 5.3 (depende de T009–T012).

**Checkpoint**: se puede quitar una prueba con confirmación; falta blindar las reglas de US2.

---

## Phase 4: User Story 2 - Impedir quitas no permitidas (Priority: P2)

**Goal**: rechazar la quita de pruebas con mediciones, de la última prueba, en estudios no
modificables y por reenvío, también ante envíos simultáneos.

**Independent Test**: intentar quitar la última prueba, quitar una prueba con `puede_quitarse()`
falso, quitar en un estudio no modificable y reenviar la confirmación; verificar mensajes y que el
estudio no cambia indebidamente.

### Tests for User Story 2 ⚠️ (escribir primero, deben fallar)

- [X] T014 [P] [US2] Agregar en `estudios/tests/test_servicio_pruebas.py`:
  - `test_ultima_prueba_no_se_puede_quitar`: quitar TEST-B y luego TEST-A → `UltimaPrueba` con «El estudio debe conservar al menos una prueba.»; TEST-A sigue asignada (FR-011).
  - `test_quitar_rechaza_prueba_con_mediciones` (parametrizado con `cargada` y `completada`, guardados en la base con `PruebaEstudio.objects.filter(...).update(estado=...)`): `GestionPruebasError` con «La prueba tiene mediciones o resultados cargados y no se puede quitar.» y la asignación sigue con su estado (FR-004).
  - `test_estudio_no_modificable_rechaza_quitar` (parametrizado con `en_proceso`, `finalizado` e `informe_generado`, guardados en la base): `quitar_prueba` lanza `GestionPruebasError` con «Este estudio ya no admite cambios en sus pruebas.» y las asignaciones no cambian (FR-003).
- [X] T015 [P] [US2] Agregar en `estudios/tests/test_quitar_prueba.py`:
  - `test_vistas_quitar_prueba_requieren_sesion` (GET y POST): sin sesión → 302 al login y sin cambios (FR-001).
  - `test_reenvio_confirmar_quitar_informa_ya_quitada`: dos POST a `quitar_prueba` de la misma asignación (el primero con `follow=True`, para consumir su mensaje) → el segundo redirige con «La prueba ya no forma parte del estudio.» (nivel info) (FR-010).
  - `test_detalle_no_ofrece_quitar_ultima_prueba`: con una sola asignación, el detalle no tiene enlace a `quitar_prueba` y muestra «El estudio debe conservar al menos una prueba.».
  - `test_detalle_no_ofrece_quitar_prueba_con_mediciones`: con TEST-A guardada en `cargada`, el detalle no tiene el enlace a `quitar_prueba` de TEST-A y sí el de TEST-B; GET de `quitar_prueba` de TEST-A → 302 a `detalle` con «La prueba tiene mediciones o resultados cargados y no se puede quitar.».
  - `test_vistas_estudio_no_modificable_no_ofrecen_quitar`: con el estudio guardado en `en_proceso`, GET de `quitar_prueba` → 302 a `detalle` con «Este estudio ya no admite cambios en sus pruebas.» y el detalle no ofrece **Quitar**.
  - `test_quitar_estudio_inexistente_responde_404`: GET y POST de `quitar_prueba` con un `pk` de estudio inexistente → 404.
  - `test_quitar_asignacion_de_otro_estudio_rechazada`: GET y POST de `quitar_prueba` con el `pk` del estudio A y una asignación del estudio B → 302 al detalle de A con «La prueba ya no forma parte del estudio.» y la asignación de B sigue.
- [X] T016 [P] [US2] Agregar en `estudios/tests/test_concurrencia_pruebas.py` (mismo esquema de hilos que `test_agregados_concurrentes_no_duplican`):
  - `test_quitas_concurrentes_conservan_una_prueba`: con TEST-A y TEST-B, dos hilos quitan cada una; uno tiene éxito, el otro lanza `UltimaPrueba`; queda exactamente una asignación.
  - `test_quitas_concurrentes_misma_asignacion`: con TEST-A, TEST-B y TEST-C, dos hilos quitan la misma asignación de TEST-A; uno devuelve la prueba, el otro lanza `PruebaYaQuitada`; quedan TEST-B y TEST-C.

### Implementation for User Story 2

- [X] T017 [US2] Completar `quitar_prueba` en `estudios/servicios.py`: después de bloquear el estudio (y antes de buscar la asignación), `if not estudio.admite_modificaciones: raise GestionPruebasError("Este estudio ya no admite cambios en sus pruebas.")`; antes de borrar, si `estudio.pruebas_asignadas.count() <= 1` → `UltimaPrueba("El estudio debe conservar al menos una prueba.")`; si `not asignacion.puede_quitarse()` → `GestionPruebasError("La prueba tiene mediciones o resultados cargados y no se puede quitar.")`; traducir `ProtectedError` del `delete()` en ese mismo error (research R3) (depende de T009).
- [X] T018 [US2] En `estudios/views.py`, `quitar_prueba` (GET) redirige a `detalle` con el mensaje de error correspondiente si el estudio no es modificable, si es la última prueba o si `puede_quitarse()` es falso. La vista `detalle` no cambia: ya pasa `total_pruebas` (US 5.2) (depende de T010, T017).
- [X] T019 [US2] En `estudios/templates/estudios/detalle.html`, mostrar **Quitar** solo si además `asignacion.puede_quitarse` y `total_pruebas > 1`; con una sola asignación en un estudio modificable, mostrar «El estudio debe conservar al menos una prueba.» en su lugar; una prueba `Cargada` o `Completada` deja la celda vacía (depende de T012, T018).
- [X] T020 [US2] Ejecutar `docker compose exec web pytest estudios` y dejar en verde T014–T016 junto con US1 y US 5.3 (depende de T017–T019).

**Checkpoint**: US 5.4 completa; las reglas resisten reenvíos y concurrencia.

---

## Phase 5: Polish & Cross-Cutting Concerns

- [X] T021 [P] Ejecutar `docker compose exec web ruff check .`, `docker compose exec web ruff format --check .` y `docker compose exec web python manage.py makemigrations --check --dry-run`, y corregir lo que aparezca (Principios III y VI).
- [X] T022 Ejecutar la suite completa `docker compose exec web pytest` y confirmar todo en verde.
- [ ] T023 Recorrer los pasos 1 a 6 de validación manual de `specs/011-quitar-prueba-estudio/quickstart.md` y cronometrar una quita desde el detalle: menos de 1 minuto (SC-005).
- [X] T024 [P] Ampliar en `CLAUDE.md` la sección de pruebas de un estudio (creada en US 5.3) con lo no obvio de US 5.4: `quitar_prueba` cuenta las asignaciones bajo el bloqueo del estudio para sostener la regla de al menos una prueba y bloquea también la asignación para leer su estado; quitar borra la asignación (sin historial); `PruebaEstudio.puede_quitarse()` es «estado `Pendiente`», así que el **Epic 6** debe pasar la prueba a `Cargada`/`Completada` al registrar mediciones o resultados (bloqueando la asignación) y referenciar `PruebaEstudio` con `PROTECT`; `.btn-chico` es el botón para tablas. Actualizar la línea de US 5.3 que dice que US 5.4 completa la columna Acción. No tocar el pendiente del envío de informes por correo.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: `T001`; requiere US 5.3 implementada.
- **Foundational (Phase 2)**: depende de la fase 1. `T002` y `T005` en paralelo; `T003` tras `T002`; `T004`; `T006` al final. Bloquea las historias.
- **US1 (Phase 3)**: depende de la fase 2. Es el MVP.
- **US2 (Phase 4)**: depende de US1 (completa su servicio, su vista y el detalle).
- **Polish (Phase 5)**: depende de las dos historias.

### Dentro de cada historia

- Tests primero y fallando; luego servicio → vista + url → templates.
- `test_servicio_pruebas.py`, `test_quitar_prueba.py`, `servicios.py`, `views.py` y `detalle.html` se tocan en varias fases: las tareas que comparten archivo van en secuencia.

### Grafo

```text
T001 → T002 → T003 ─┐
       T004 ────────┼─→ T006
       T005 ────────┘     │
          ┌───────────────┘
          ▼
US1: T007, T008 → T009 → T010 → T011, T012 → T013
US2: T014, T015, T016 → T017 → T018 → T019 → T020
Polish: T021, T022, T023, T024
```

---

## Parallel Example: User Story 1

```bash
Task T007: "Tests del servicio en estudios/tests/test_servicio_pruebas.py"
Task T008: "Tests de vistas en estudios/tests/test_quitar_prueba.py"
```

## Parallel Example: User Story 2

```bash
Task T014: "Reglas en estudios/tests/test_servicio_pruebas.py"
Task T015: "Reglas y reenvíos en estudios/tests/test_quitar_prueba.py"
Task T016: "Concurrencia en estudios/tests/test_concurrencia_pruebas.py"
```

---

## Implementation Strategy

### En dos tandas (según `docs/guias/guia-sdd-paso-a-paso.md`)

1. **Tanda 1 (Fases 1 y 2 — `T001` a `T006`)**: aprobación, base de US 5.3, regla del modelo y
   excepciones; suite en verde. Frenar y revisar.
2. **Tanda 2 (Fases 3 a 5 — `T007` a `T024`)**: US1 (quitar, MVP) y US2 (reglas, reenvíos y
   concurrencia), cada una con sus tests escritos primero; cerrar con `ruff`, suite completa,
   recorrido manual y nota en `CLAUDE.md`.

### MVP

Fases 1–3 (US1). US2 debe entrar en el mismo PR: sin ella, quitar podría dejar un estudio sin
pruebas (FR-011).
