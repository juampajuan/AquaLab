---

description: "Lista de tareas de la US 3.2 – Editar cliente"
---

# Tasks: Editar cliente

**Input**: `specs/005-editar-cliente/` (`plan.md`, `spec.md`, `research.md`, `data-model.md`,
`contracts/edicion-cliente-ui.md`, `quickstart.md`)

**Prerequisites**: `plan.md`, `spec.md`. La infraestructura base y el módulo de clientes (modelo
`clientes.Cliente`, `RegistroClienteForm`, `clientes:detalle`, `clientes:buscar`,
`LoginRequiredMiddleware`, `templates/base.html`, Docker y CI) ya están implementados y no se
recrean.

**Tests**: SÍ. La constitution (Principio III) exige al menos un test automatizado con
pytest-django por cada escenario de aceptación. Los tests siguen el "Mapa de tests" de `plan.md` y
se escriben **antes** de implementar las vistas y templates (deben fallar primero).

**Organization**: la spec tiene una sola user story (US1, P1: editar datos de un cliente
registrado); todas las tareas de producto están en su fase.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: se puede ejecutar en paralelo (archivos distintos, sin dependencias pendientes)
- **[Story]**: user story a la que pertenece la tarea (`[US1]`)
- Rutas relativas a la raíz del repo (`clientes/`, `CLAUDE.md`)

## Convenciones para todas las tareas

- Textos de UI, mensajes y nombres de dominio en **español** siguiendo el Glosario (Principio VI).
- Mensajes al usuario copiados literalmente de `contracts/edicion-cliente-ui.md`.
- Comandos dentro de Docker: `docker compose exec web pytest clientes`,
  `docker compose exec web ruff check .`, `docker compose exec web ruff format --check .`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: confirmar que el entorno actual y la suite existente de `clientes` corren en verde en
esta rama antes de tocar código.

- [X] T001 Verificar el entorno con `docker compose up -d`, `docker compose exec web python manage.py migrate` y `docker compose exec web pytest` sobre `docker-compose.yml` para confirmar que la base y los tests actuales pasan sin errores.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: habilitar en el formulario de clientes la validación de unicidad excluyendo al propio
cliente editado (`research.md` R1) y preparar las fixtures de edición para los tests.

**⚠️ CRITICAL**: no empezar la fase 3 hasta terminar esta fase.

- [X] T002 Actualizar `RegistroClienteForm.clean()` y definir `EditarClienteForm` en `clientes/forms.py` según `data-model.md` y `research.md` R1:
  - Mantener `CAMPOS_CLIENTE = ("nombre", "razon_social", "tipo_documento", "numero_documento", "email", "telefono", "domicilio")` con sus restricciones (`nombre` y `razon_social` `max_length=200`, `blank=True`, al menos uno obligatorio; `tipo_documento` obligatorio con opciones `"DNI"` y `"CUIT"`; `numero_documento` obligatorio normalizado sin espacios, puntos ni guiones, DNI de 7 u 8 dígitos y CUIT de 11 dígitos con dígito verificador módulo 11; `email` obligatorio `max_length=254` en minúsculas; `telefono` opcional `max_length=30` de 7 a 15 dígitos; `domicilio` opcional `max_length=255`).
  - Al verificar unicidad de `(tipo_documento, numero_documento)`, armar el queryset `qs = Cliente.objects.filter(tipo_documento=tipo, numero_documento=numero)` y, si `self.instance and self.instance.pk`, aplicar `qs = qs.exclude(pk=self.instance.pk)` antes de `.exists()`.
  - Definir `EditarClienteForm = RegistroClienteForm` (o subclase equivalente que herede `datos_para_sesion()`).
- [X] T003 [P] Agregar en `clientes/tests/conftest.py` las fixtures reutilizables para edición:
  - `otro_cliente`: `Cliente.objects.create(nombre="Juan Pérez", tipo_documento="DNI", numero_documento="30123456", email="juan@ejemplo.com", telefono="+54 11 4321-5678", domicilio="Av. Corrientes 1234")`.
  - `datos_edicion_validos`: dict válido con datos modificados para `cliente_existente` (`nombre="Roberto Gómez"`, `razon_social="Aguas del Sur S.A."`, `tipo_documento="CUIT"`, `numero_documento="20-12345678-6"`, `email="nuevo@aguassur.com"`, `telefono="+54 11 5555-6666"`, `domicilio="Av. Paseo Colón 850"`).

**Checkpoint**: `EditarClienteForm(instance=cliente)` valida unicidad excluyendo `cliente.pk` y las fixtures de edición están disponibles.

---

## Phase 3: User Story 1 - Editar datos de un cliente registrado (Priority: P1) 🎯 MVP

**Goal**: un empleado con sesión activa accede desde la ficha de un cliente activo a su formulario
de edición precargado, modifica sus datos, los revisa en la pantalla de confirmación y confirma o
cancela la operación; si confirma, el cliente se actualiza de forma atómica e idempotente y los
cambios se ven de inmediato en su ficha y en las búsquedas.

**Independent Test**: `docker compose exec web pytest clientes/tests/test_edicion.py` en verde
(escenarios 1–8 y casos borde del Mapa de tests) + validación manual de `quickstart.md` (pasos
1–10).

### Tests for User Story 1 ⚠️ (escribir primero, deben fallar)

> **NOTE: escribir T004 y T005 PRIMERO y verificar que FALLAN antes de implementar T006–T010.**
> Ambos tocan `clientes/tests/test_edicion.py` (ejecutar secuencialmente), con
> `pytestmark = pytest.mark.django_db`.

- [X] T004 [US1] Crear en `clientes/tests/test_edicion.py` los tests de acceso, precarga y validaciones del formulario de edición (paso 1):
  - `test_vistas_edicion_requieren_sesion_activa` (FR-001): GET y POST sin sesión a `clientes:editar` y `clientes:editar_confirmar` responden 302 hacia `settings.LOGIN_URL`.
  - `test_editar_cliente_inexistente_devuelve_404` (FR-013): GET y POST a `clientes:editar` y `clientes:editar_confirmar` con `pk=99999` responden 404.
  - `test_editar_cliente_inactivo_redirige_con_advertencia` (FR-013, Edge case 5): con un cliente `activo=False`, GET y POST a `clientes:editar` y `clientes:editar_confirmar` responden 302 a `clientes:buscar` con el mensaje `"El cliente no está disponible."` y limpian cualquier borrador en sesión.
  - `test_get_editar_precarga_datos_vigentes_y_ficha_tiene_link` (Esc. 1, FR-002, FR-003): GET a `clientes:detalle` incluye el enlace `"Editar cliente"` hacia `reverse("clientes:editar", args=[cliente_existente.pk])`; GET a `clientes:editar` responde 200 con todos los datos vigentes precargados en el formulario y descarta cualquier borrador viejo si no se pasa `?volver=1`.
  - `test_edicion_campos_obligatorios_faltantes_no_modifica` (Esc. 3, FR-005, FR-008, SC-003), parametrizado por: `nombre` y `razon_social` ambos vacíos (`"Debés ingresar al menos el nombre o la razón social del cliente."`), `tipo_documento` vacío, `numero_documento` vacío y `email` vacío (`"Este campo es obligatorio."`): responde 200, no guarda borrador en sesión y el cliente en la base conserva sus datos originales.
  - `test_edicion_formatos_invalidos_rechazados_y_conserva_datos` (Esc. 4, FR-006, FR-008, SC-003), parametrizado para `email` inválido (`"mal@"`), `telefono` inválido (`"123"`), DNI inválido (`"12345"`) y CUIT con dígito verificador inválido (`"20-12345678-0"`): responde 200 con el mensaje de error exacto del contrato, conserva en el HTML los demás valores ingresados y no modifica al cliente en la base.
  - `test_edicion_documento_de_otro_cliente_rechazado` (Esc. 5, FR-007, SC-003): intentando editar `cliente_existente` con el DNI de `otro_cliente` (`"30123456"`, `"30.123.456"`, `"30-123-456"`, `" 30 123 456 "`), responde 200 con el error `"Ya existe un cliente registrado con este tipo y número de documento."` una sola vez y no modifica la base.
  - `test_edicion_mismo_documento_propio_con_o_sin_separadores_permitido` (Esc. 6, Edge case 1, FR-007): enviando en `clientes:editar` el mismo CUIT de `cliente_existente` (`"20123456786"` o `"20-12345678-6"` o `"20.123.456.786"`) y cambiando otros datos, responde 302 hacia `clientes:editar_confirmar` y guarda el borrador normalizado en `session[f"cliente_edicion_{cliente_existente.pk}"]`.
- [X] T005 [US1] Agregar en `clientes/tests/test_edicion.py` los tests de revisión, confirmación, cancelación, idempotencia y errores de base de datos (paso 2, depende de T004):
  - `test_confirmar_edicion_actualiza_cliente_y_refleja_en_detalle` (Esc. 2, FR-009, FR-012, SC-001, SC-002): POST válido a `clientes:editar` → 302 a `clientes:editar_confirmar`; GET de la confirmación muestra `"Revisá los datos modificados del cliente antes de confirmar los cambios."` y el resumen de datos; POST `accion=confirmar` → 302 a `clientes:detalle`, mensaje `"Datos del cliente actualizados correctamente."`, `cliente_existente.refresh_from_db()` refleja todos los datos nuevos, el borrador ya no está en la sesión y la ficha muestra los datos actualizados.
  - `test_edicion_permite_vaciar_telefono_y_domicilio` (Edge case 4, FR-005): sobre `otro_cliente` (que tiene `telefono` y `domicilio` cargados), editar dejando `telefono=""` y `domicilio=""` y confirmar actualiza ambos campos a `""` en la base.
  - `test_volver_y_editar_conserva_borrador_sin_modificar_bd` (Esc. 7, FR-010): con borrador en sesión, GET a `/clientes/<pk>/editar/?volver=1` devuelve 200 precargando los valores modificados de la sesión, mientras en la base siguen los valores originales.
  - `test_cancelar_en_confirmacion_borra_sesion_y_no_modifica_cliente` (Esc. 7, FR-011, SC-004): con borrador en sesión, POST `accion=cancelar` a `clientes:editar_confirmar` responde 302 a `clientes:detalle` con el mensaje `"Edición de cliente cancelada."`, borra `session[f"cliente_edicion_{pk}"]` y mantiene intactos los datos del cliente en la base; luego un GET a `clientes:editar_confirmar` redirige (302) a `clientes:editar`.
  - `test_confirmacion_repetida_es_idempotente` (Esc. 8): tras confirmar una edición, un segundo POST `accion=confirmar` a `clientes:editar_confirmar` responde 302 a `clientes:detalle` con `"Datos del cliente actualizados correctamente."` sin lanzar errores ni alterar los datos guardados.
  - `test_integrity_error_al_confirmar_edicion_informa_duplicado` (Esc. 8, FR-007, R3): con borrador en sesión que cambia el documento a un DNI libre `"31222333"`, si otro registro toma ese DNI antes del POST `accion=confirmar`, el POST captura `IntegrityError`, responde 302 a `/clientes/<pk>/editar/?volver=1` con el mensaje `"Ya existe un cliente registrado con este tipo y número de documento."`, conserva el borrador en sesión y no modifica al cliente.
  - `test_error_de_base_al_confirmar_edicion_informa_sin_modificar` (Edge case 6, R3): con borrador en sesión y `monkeypatch` de `clientes.views.actualizar_cliente` para que levante `DatabaseError`, el POST `accion=confirmar` responde 200 en la pantalla de confirmación con `"No se pudo actualizar el cliente. Intentá nuevamente."`, conserva el borrador en sesión y no modifica al cliente en la base.

### Implementation for User Story 1

- [X] T006 [US1] Implementar en `clientes/views.py` las funciones `clave_sesion_edicion(pk)`, `actualizar_cliente(cliente, datos)`, `editar(request, pk)` y `editar_confirmar(request, pk)` según `contracts/edicion-cliente-ui.md` y `research.md` R2–R4 (depende de T002):
  - Constantes: `CLAVE_ULTIMO_EDITADO_ID = "ultimo_cliente_editado_id"`, `MENSAJE_EDICION_EXITO = "Datos del cliente actualizados correctamente."`, `MENSAJE_EDICION_CANCELADA = "Edición de cliente cancelada."`, `MENSAJE_ERROR_BD_EDICION = "No se pudo actualizar el cliente. Intentá nuevamente."`.
  - `clave_sesion_edicion(pk)`: devuelve `f"cliente_edicion_{pk}"`.
  - `actualizar_cliente(cliente, datos)`: dentro de `transaction.atomic()`, asigna los campos de `CAMPOS_CLIENTE` en `cliente`, ejecuta `cliente.save()` y devuelve `cliente`.
  - `editar(request, pk)`: obtiene `cliente = get_object_or_404(Cliente, pk=pk)`; si `not cliente.activo`, borra `clave_sesion_edicion(pk)` de la sesión, agrega `messages.warning(request, MENSAJE_NO_DISPONIBLE)` y redirige a `clientes:buscar`. En POST instancia `EditarClienteForm(request.POST, instance=cliente)`; si es válido, guarda `request.session[clave_sesion_edicion(pk)] = form.datos_para_sesion()`, elimina `CLAVE_ULTIMO_EDITADO_ID` y redirige a `clientes:editar_confirmar` (`pk=cliente.pk`). En GET, si `request.GET.get("volver") == "1"` y existe borrador en `request.session.get(clave_sesion_edicion(pk))`, instancia `EditarClienteForm(initial=datos, instance=cliente)`; en otro caso elimina cualquier borrador previo `request.session.pop(clave_sesion_edicion(pk), None)` e instancia `EditarClienteForm(instance=cliente)`. Renderiza `clientes/editar_form.html` con `{"form": form, "cliente": cliente}`.
  - `editar_confirmar(request, pk)`: obtiene `cliente = get_object_or_404(Cliente, pk=pk)`; si `not cliente.activo`, borra `clave_sesion_edicion(pk)`, agrega `messages.warning(request, MENSAJE_NO_DISPONIBLE)` y redirige a `clientes:buscar`. Procesa POST (`accion=cancelar`, `accion=confirmar`, `IntegrityError`, `DatabaseError`, confirmación repetida con `CLAVE_ULTIMO_EDITADO_ID`) y GET según la tabla de `contracts/edicion-cliente-ui.md`, renderizando `clientes/editar_confirmar.html` con `{"cliente": cliente, "datos": resumen}`.
- [X] T007 [US1] Registrar en `clientes/urls.py` las rutas `path("<int:pk>/editar/", views.editar, name="editar")` y `path("<int:pk>/editar/confirmar/", views.editar_confirmar, name="editar_confirmar")` (depende de T006).
- [X] T008 [P] [US1] Crear `clientes/templates/clientes/editar_form.html` extendiendo `base.html` según `contracts/edicion-cliente-ui.md`: `{% block title %}Editar cliente · AquaLab{% endblock %}`, título `"Editar cliente"`, texto de ayuda `"Modificá los datos del cliente y continuá para revisar los cambios antes de guardarlos."`, alerta `alert-danger` para `form.non_field_errors`, formulario `<form method="post" novalidate>` con `{% csrf_token %}`, los 7 campos con sus etiquetas y `<div class="invalid-feedback">`, botón primario **Continuar** y enlace **Cancelar** hacia `{% url 'clientes:detalle' cliente.pk %}`.
- [X] T009 [P] [US1] Crear `clientes/templates/clientes/editar_confirmar.html` extendiendo `base.html` según `contracts/edicion-cliente-ui.md`: `{% block title %}Confirmar edición · AquaLab{% endblock %}`, título `"Confirmar edición de cliente"`, alerta `alert-info` `"Revisá los datos modificados del cliente antes de confirmar los cambios."`, lista `<dl class="row">` con Nombre, Razón social, Tipo de documento, Número de documento, Correo electrónico, Teléfono y Domicilio (`default:"—"`), form POST `accion=confirmar` con botón **Confirmar** (deshabilitado en `onsubmit`), enlace **Volver y editar** hacia `{% url 'clientes:editar' cliente.pk %}?volver=1` y form POST `accion=cancelar` con botón **Cancelar**.
- [X] T010 [P] [US1] Agregar en `clientes/templates/clientes/detalle.html` el botón/enlace `"Editar cliente"` que apunte a `{% url 'clientes:editar' cliente.pk %}` (FR-002).
- [X] T011 [US1] Ejecutar `docker compose exec web pytest clientes/tests/test_edicion.py` y `docker compose exec web pytest` y confirmar que todos los tests de T004–T005 y el resto del proyecto quedan en verde (depende de T004–T010).

**Checkpoint**: la US 3.2 funciona completa y es verificable de forma independiente (tests automatizados + quickstart).

---

## Phase 4: Polish & Cross-Cutting Concerns

**Purpose**: lint/formato, validación manual de punta a punta y limpieza de pendientes en `CLAUDE.md`.

- [X] T012 [P] Ejecutar `docker compose exec web ruff check .` y `docker compose exec web ruff format --check .` y corregir cualquier observación de lint o formato (Principios III y VI).
- [X] T013 Recorrer los pasos 1 a 10 de validación manual de `specs/005-editar-cliente/quickstart.md`.
- [X] T014 [P] Actualizar `CLAUDE.md`: borrar la línea de pendiente de la **US 3.2** en la sección `"Pendientes entre features"`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: sin dependencias (`T001`).
- **Foundational (Phase 2)**: depende de `T001`. `T002` y `T003` se pueden hacer en paralelo y bloquean la fase 3.
- **User Story 1 (Phase 3)**: depende de la fase 2 completa (`T002`, `T003`).
- **Polish (Phase 4)**: depende de `T011`.

### Dentro de la User Story 1

- **Tests primero**: `T004` → `T005` (mismo archivo `clientes/tests/test_edicion.py`). Verificar que fallan antes de implementar `T006`–`T010`.
- **Backend**: `T006` (`clientes/views.py`) → `T007` (`clientes/urls.py`).
- **Templates en paralelo**: `T008` (`editar_form.html`), `T009` (`editar_confirmar.html`) y `T010` (`detalle.html`) tocan archivos distintos y son `[P]`.
- **Verificación**: `T011` corre toda la suite de `pytest` al terminar `T007`–`T010`.

### Grafo

```text
T001 ─┬─→ T002 ─┐
      └─→ T003 ─┴─→ T004 → T005 ─┬─→ T006 → T007 ─┬─→ T011 ─┬─→ T012
                                 ├─→ T008 ────────┤         ├─→ T013
                                 ├─→ T009 ────────┤         └─→ T014
                                 └─→ T010 ────────┘
```

---

## Parallel Example: User Story 1

```bash
# Fase 2 en paralelo (archivos distintos):
Task T002: "Actualizar RegistroClienteForm / EditarClienteForm en clientes/forms.py"
Task T003: "Agregar fixtures otro_cliente y datos_edicion_validos en clientes/tests/conftest.py"

# Fase 3 templates en paralelo con views/urls:
Task T008: "Template clientes/templates/clientes/editar_form.html"
Task T009: "Template clientes/templates/clientes/editar_confirmar.html"
Task T010: "Botón Editar cliente en clientes/templates/clientes/detalle.html"
```

---

## Implementation Strategy

### En dos tandas (según `docs/guias/guia-sdd-paso-a-paso.md`)

1. **Tanda 1 (Fases 1 y 2 — `T001` a `T003`)**: verificar el entorno en Docker, ajustar
   `RegistroClienteForm` / `EditarClienteForm` en `clientes/forms.py` y agregar las fixtures en
   `clientes/tests/conftest.py`. Frenar y revisar.
2. **Tanda 2 (Fases 3 y 4 — `T004` a `T014`)**: escribir primero los tests en
   `clientes/tests/test_edicion.py` (`T004`–`T005`) y comprobar que fallan; luego implementar
   `clientes/views.py`, `clientes/urls.py` y los templates (`T006`–`T010`); dejar `pytest` y `ruff`
   en verde (`T011`–`T012`), indicar los pasos de prueba manual (`T013`) y limpiar el pendiente de
   `CLAUDE.md` (`T014`).
