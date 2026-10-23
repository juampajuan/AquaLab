---

description: "Lista de tareas de la US 3.1 – Buscar cliente registrado"
---

# Tasks: Buscar cliente registrado

**Input**: `specs/004-buscar-cliente/` (plan.md, spec.md, research.md, data-model.md, contracts/busqueda-cliente-ui.md, quickstart.md)

**Prerequisites**: plan.md, spec.md. La infraestructura base (modelo `Cliente`, settings, Docker, `base.html`, `LoginRequiredMiddleware`, `clientes:detalle`) ya existe y no se recrea.

**Tests**: Incluidos. La constitution (Principio III) exige al menos un test pytest-django por escenario de aceptación. Escribirlos primero y verificar que fallen antes de implementar.

**Organization**: Tareas agrupadas por historia de usuario. US1 = P1 (buscar y ver datos), US2 = P2 (seleccionar para otros flujos).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: se puede ejecutar en paralelo (archivos distintos, sin dependencias pendientes)
- **[Story]**: US1 o US2

## Phase 1: Setup

No hay tareas: no se crean apps, dependencias ni configuración de proyecto nuevas (el único cambio de settings va en Foundational porque bloquea la búsqueda).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: habilitar la búsqueda sin distinguir tildes (FR-003, research R1)

**⚠️ CRITICAL**: US1 depende de esta fase.

- [X] T001 Agregar `"django.contrib.postgres"` a `INSTALLED_APPS` en `config/settings.py`
- [X] T002 Crear la migración `clientes/migrations/0002_unaccent.py` (dependencia `("clientes", "0001_initial")`) con `UnaccentExtension()` de `django.contrib.postgres.operations`; verificar que `python manage.py migrate` y la base de tests de pytest la aplican (depende de T001)

**Checkpoint**: el lookup `__unaccent` está disponible en el ORM.

---

## Phase 3: User Story 1 - Buscar clientes y ver sus datos (Priority: P1) 🎯 MVP

**Goal**: el empleado ingresa un texto en un campo único y obtiene la lista de clientes activos que coinciden por nombre, razón social o documento, con acceso a la ficha.

**Independent Test**: con clientes de prueba, buscar por nombre, razón social y documento (con/sin puntos y guiones, con otras mayúsculas/tildes) y verificar la lista, el mensaje sin resultados y la validación; abrir un resultado y ver sus datos.

### Tests for User Story 1 ⚠️ (escribir primero, deben fallar)

Todos en `clientes/tests/test_busqueda.py` (mismo archivo: no son [P] entre sí), usando `cliente_autenticado` de `clientes/tests/conftest.py` y `reverse("clientes:buscar")`. Agregar en `conftest.py` una fixture `clientes_busqueda` que cree clientes con `Cliente.objects.create(...)`: persona `Juan Pérez` (DNI `30123456`), empresa `Aguas del Sur S.A.` (CUIT `20123456786`), cliente solo con `razon_social`, cliente solo con `nombre`, y dos homónimos `María Gómez` con distinto documento.

- [X] T003 [US1] Agregar la fixture `clientes_busqueda` en `clientes/tests/conftest.py` según lo descrito arriba
- [X] T004 [US1] Test escenario 1: `?q=Pér` lista todos los clientes cuyo `nombre` contiene el texto, en `clientes/tests/test_busqueda.py`
- [X] T005 [US1] Test escenario 2: `?q=aguas` lista los clientes cuya `razon_social` contiene el texto, en `clientes/tests/test_busqueda.py`
- [X] T006 [US1] Test escenario 3: buscar `30123456`, `30.123.456`, `30-123-456` y el parcial `1234` lista al cliente por `numero_documento`; también CUIT `20-12345678-6`, en `clientes/tests/test_busqueda.py`
- [X] T007 [US1] Test escenario 4: cada resultado muestra `nombre_completo`, tipo y número de documento y `email`, en `clientes/tests/test_busqueda.py`
- [X] T008 [US1] Test escenario 6: `?q=zzzz` responde 200 con el mensaje «No se encontraron clientes» y el formulario disponible, en `clientes/tests/test_busqueda.py`
- [X] T009 [US1] Test escenario 7: `?q=PEREZ`, `?q=perez` y `?q=pérez` encuentran a `Juan Pérez` (mayúsculas y tildes), en `clientes/tests/test_busqueda.py`
- [X] T010 [US1] Tests de casos límite en `clientes/tests/test_busqueda.py`: (a) `?q=` y `?q=   ` no listan clientes y muestran el error de campo requerido; (b) `?q=a` muestra «Ingresá al menos 2 caracteres para buscar.»; (c) clientes con `activo=False` no aparecen; (d) clientes con solo `nombre` o solo `razon_social` se encuentran; (e) sin `q` se muestra el formulario sin resultados ni error; (f) con más de 20 coincidencias hay paginación, orden `razon_social, nombre, id` y los enlaces de página conservan `q`
- [X] T011 [US1] Test de acceso (FR-001): sin sesión, `GET /clientes/buscar/` responde 302 a `settings.LOGIN_URL`, en `clientes/tests/test_busqueda.py`
- [X] T012 [US1] Test escenario 5: el enlace «Ver ficha» de un resultado lleva a `clientes:detalle` y la ficha muestra nombre, razón social, tipo y número de documento, email, teléfono y domicilio vigentes (y refleja un cambio hecho en la base antes de consultar, FR-010), en `clientes/tests/test_busqueda.py`

### Implementation for User Story 1

- [X] T013 [P] [US1] Crear `BuscarClienteForm(forms.Form)` en `clientes/forms.py` con `q = forms.CharField(label="Nombre, razón social o documento", min_length=2, strip=True)`; mensajes en español: vacío → «Ingresá un nombre, razón social o número de documento para buscar.», menos de 2 caracteres → «Ingresá al menos 2 caracteres para buscar.»
- [X] T014 [US1] Agregar la vista `buscar(request)` en `clientes/views.py`: instanciar el form con `request.GET` solo si `"q"` está presente; con form válido, `Cliente.objects.filter(activo=True)` filtrado por `Q(nombre__unaccent__icontains=q) | Q(razon_social__unaccent__icontains=q)` y, si `normalizar_numero_documento(q)` es no vacío y `isdigit()`, `| Q(numero_documento__contains=q_doc)`; ordenar con `Cliente._meta.ordering`; paginar con `Paginator(qs, 20).get_page(request.GET.get("page"))`; renderizar `clientes/buscar.html` con `form`, `page_obj`, `q` y la cantidad (depende de T013, T002)
- [X] T015 [US1] Agregar `path("buscar/", views.buscar, name="buscar")` en `clientes/urls.py` (depende de T014)
- [X] T016 [US1] Crear `clientes/templates/clientes/buscar.html` extendiendo `base.html`, según `contracts/busqueda-cliente-ui.md`: título «Buscar cliente», formulario `method="get"` (sin `csrf_token`) con error junto al campo, `autofocus` y valor conservado, texto de ayuda, encabezado «N cliente(s) encontrado(s)», tabla Bootstrap con Cliente (`nombre_completo`), Documento (`tipo numero`), Correo electrónico y enlace «Ver ficha» a `{% url 'clientes:detalle' c.pk %}`, alerta `alert-info` «No se encontraron clientes para «{{ q }}».» y paginación Bootstrap con `?q=…&page=N` (depende de T014)
- [X] T017 [P] [US1] Agregar el enlace «Buscar cliente» (`{% url 'clientes:buscar' %}`) en la navbar de `templates/base.html`, junto a «Registrar cliente»
- [X] T018 [P] [US1] Agregar el botón «Buscar cliente» en `templates/inicio.html`
- [X] T019 [P] [US1] Agregar el enlace «Volver a la búsqueda» a `clientes:buscar` en `clientes/templates/clientes/detalle.html`
- [X] T020 [US1] Ejecutar `pytest clientes/tests/test_busqueda.py` y dejar T004–T012 en verde (depende de T015–T019)

**Checkpoint**: US1 funcional y probable de forma independiente (MVP).

---

## Phase 4: User Story 2 - Seleccionar un cliente para otros flujos (Priority: P2)

**Goal**: identificar de forma inequívoca al cliente elegido y no ofrecer datos de clientes no disponibles.

**Independent Test**: desde los resultados y desde la ficha, el cliente queda identificado por su `pk`/documento; un cliente inactivo no se muestra.

### Tests for User Story 2 ⚠️ (escribir primero, deben fallar)

- [X] T021 [P] [US2] Test escenario US2-1 en `clientes/tests/test_seleccion.py`: con dos clientes de datos parecidos, el enlace de cada resultado apunta a `reverse("clientes:detalle", args=[pk])` de ese cliente y la ficha abierta es la de ese cliente y no la del otro
- [X] T022 [P] [US2] Test escenario US2-2 en `clientes/tests/test_seleccion.py`: dos clientes con el mismo nombre y distinto documento aparecen ambos en los resultados, cada uno con su tipo y número de documento visibles
- [X] T023 [P] [US2] Test del edge case «cliente desactivado entre búsqueda y selección» en `clientes/tests/test_seleccion.py`: `GET clientes:detalle` de un cliente `activo=False` responde 302 a `clientes:buscar` con el mensaje «El cliente no está disponible.»; un `pk` inexistente sigue respondiendo 404

### Implementation for User Story 2

- [X] T024 [US2] Modificar `detalle` en `clientes/views.py`: si el cliente existe y `activo` es `False`, `messages.warning(request, "El cliente no está disponible.")` y `redirect("clientes:buscar")`; `get_object_or_404` se mantiene para `pk` inexistente
- [X] T025 [US2] Ejecutar `pytest clientes/tests/test_seleccion.py clientes/tests/test_registro.py` y confirmar que T021–T023 pasan y que la US 2.1 no se rompe (depende de T024)

**Checkpoint**: US1 y US2 funcionan; otros flujos pueden reutilizar `clientes:detalle`/`pk`.

---

## Phase 5: Polish & Cross-Cutting Concerns

- [X] T026 [P] Ejecutar `ruff check .` y `ruff format --check .` y corregir hallazgos (obligatorio para mergear, Principio III)
- [X] T027 Ejecutar la suite completa `pytest` y confirmar que no hay regresiones
- [ ] T028 Recorrer `specs/004-buscar-cliente/quickstart.md` (validación manual, pasos 1–10) en el navegador
- [X] T029 [P] Actualizar `CLAUDE.md`: borrar de «Pendientes entre features» lo resuelto por esta feature (la búsqueda de la US 3.1) y dejar el resto
- [ ] T030 Preparar el PR titulado «US 3.1 – Buscar cliente registrado» referenciando `specs/004-buscar-cliente/`

---

## Dependencies & Execution Order

- **Foundational (T001→T002)** bloquea US1.
- **US1**: T003 → tests T004–T012 (mismo archivo, secuenciales) → T013 → T014 → T015/T016 → T017–T019 [P] → T020.
- **US2**: depende de T015–T016 (necesita la búsqueda) y se puede empezar en paralelo con el final de US1 si es otra persona; T024 toca `clientes/views.py`, coordinarse con T014.
- **Polish**: después de US1 y US2.

### Parallel Opportunities

- T013 (forms.py) en paralelo con la escritura de tests T004–T012.
- T017, T018, T019 (tres templates distintos) en paralelo.
- T021, T022, T023 (mismo archivo `test_seleccion.py`, pero casos independientes) pueden repartirse si se redactan por separado y se unen; T026 y T029 en paralelo.

## Implementation Strategy

### MVP First (US1)

1. Foundational (T001–T002) → 2. tests de US1 en rojo → 3. implementación T013–T019 → 4. T020 en verde → **validar y mostrar** la búsqueda.

### Incremental Delivery

Agregar US2 (T021–T025) sobre el MVP y cerrar con Polish. Un solo PR por spec (Principio I).

## Notes

- Sin tareas de modelo: no hay cambios en `Cliente` (ver `data-model.md`).
- Textos de la UI en español; nombres del dominio según el Glosario.
- Commit tras cada tarea o grupo lógico; la spec, el plan y estas tareas se entregan con el código.
