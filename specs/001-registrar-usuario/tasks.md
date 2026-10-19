---

description: "Lista de tareas de la US 1.1 – Registrar usuario"
---

# Tasks: Registrar usuario

**Input**: Documentos de diseño en `specs/001-registrar-usuario/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/registro-ui.md,
contracts/admin-aprobacion.md, quickstart.md

**Tests**: SÍ. La constitution (principio III) exige al menos un test automatizado con
pytest-django por escenario de aceptación. Los tests siguen el "Mapa de tests" de `plan.md` y se
escriben **antes** de la implementación (tienen que fallar primero).

**Alcance**: el setup de infraestructura ya está mergeado en esta rama (modelo `Usuario`,
`UsuarioManager`, migración `0001_initial`, `AUTH_USER_MODEL`, settings, `LoginRequiredMiddleware`,
`templates/base.html` con mensajes, `usuarios/admin.py` mínimo, `usuarios/urls.py` vacío con
`app_name`, Docker y CI). **No hay tareas para recrearlo**: solo las de la columna "Lo hace esta
feature" del "Reparto setup ↔ feature" del plan.

**Organization**: la spec tiene una sola user story (US1, P1); todas las tareas de producto están
en su fase.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: se puede hacer en paralelo (archivos distintos, sin dependencias pendientes)
- **[Story]**: user story a la que pertenece la tarea (US1)
- Rutas relativas a la raíz del repo (proyecto Django único: `config/`, `templates/`, `usuarios/`)

## Convenciones para todas las tareas

- Textos de UI, mensajes, `verbose_name` y nombres de funciones/variables propias en **español**;
  lo heredado de Django (`first_name`, `last_name`, `email`, `is_active`) queda como es.
- Los mensajes al usuario se copian **literalmente** de `contracts/registro-ui.md` y
  `contracts/admin-aprobacion.md`.
- Comandos: `docker compose exec web pytest usuarios`, `docker compose exec web ruff check .`,
  `docker compose exec web ruff format .`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: confirmar que la base del setup funciona en esta rama antes de empezar.

- [X] T001 Verificar el entorno: `docker compose up -d --build`, `docker compose exec web python manage.py migrate` y `docker compose exec web pytest usuarios` deben terminar sin errores con el código actual (`usuarios/tests/test_setup.py` en verde). No modificar archivos del setup.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: piezas que necesitan tanto los tests como la implementación de la US1.

**⚠️ CRITICAL**: no empezar la fase 3 hasta terminar esta.

- [X] T002 Redefinir en `usuarios/models.py` (clase `Usuario`) los campos heredados para que el admin muestre los conceptos del dominio, sin cambiar su comportamiento: `is_active = models.BooleanField("aprobada", default=True, help_text="Indica si un administrador aprobó la cuenta. Las cuentas pendientes de aprobación no pueden iniciar sesión.")` y `date_joined = models.DateTimeField("fecha de registro", default=timezone.now)` (importar `django.utils.timezone`). `default=True` se mantiene a propósito: `create_user` sigue creando cuentas activas y el **registro** pasa `is_active=False` explícitamente (data-model.md, `UsuarioManager`).
- [X] T003 Generar la migración con `docker compose exec web python manage.py makemigrations usuarios` → `usuarios/migrations/0002_...py` (solo `AlterField` de `is_active` y `date_joined`, sin cambios de esquema en la base). No editar `0001_initial.py`. Correr `migrate` (depende de T002).
- [X] T004 [P] Crear `usuarios/forms.py` y **mover** ahí `UsuarioChangeForm` y `UsuarioCreationForm` desde `usuarios/admin.py` sin cambiar su contenido; en `usuarios/admin.py` importarlos con `from .forms import UsuarioChangeForm, UsuarioCreationForm` (plan, "Componentes": los formularios del admin viven en `forms.py`).
- [X] T005 [P] Crear `usuarios/tests/conftest.py` con fixtures compartidas (todas usan `django_user_model` / `Usuario`):
  - `datos_registro`: dict válido para el POST del formulario: `first_name="Ana"`, `last_name="Pérez"`, `email="ana@lab.com"`, `password1` y `password2` iguales a una contraseña que pase los validadores por defecto y sea fácil de buscar en el HTML (p. ej. `"Clave-Secreta-Unica-987"`).
  - `password_registro`: la contraseña en texto plano de `datos_registro` (para buscarla en respuestas y probar `authenticate`).
  - `usuario_pendiente`: `Usuario.objects.create_user(email="pendiente@lab.com", password=..., first_name="Pedro", last_name="Gómez", is_active=False)`.
  - `usuario_aprobado`: igual pero con `is_active=True` y otro correo.
  - `administrador`: superusuario creado con `create_superuser(email="admin@lab.com", password=..., first_name="Admin", last_name="AquaLab")`.
  - `cliente_admin`: `Client` con `force_login(administrador)`.
  - `en_revision`: hace `client.post(reverse("usuarios:registro"), datos_registro)` y devuelve el `client` (deja los datos en `session["registro_pendiente"]`).

**Checkpoint**: migración aplicada, admin funcionando igual que antes (`/admin/usuarios/usuario/`), fixtures disponibles.

---

## Phase 3: User Story 1 - Registrar usuario (Priority: P1) 🎯 MVP

**Goal**: una persona sin sesión completa el formulario, revisa sus datos y confirma; se crea una
única cuenta pendiente de aprobación (`is_active=False`) que no puede iniciar sesión hasta que un
administrador la apruebe desde el admin de Django.

**Independent Test**: `docker compose exec web pytest usuarios` en verde (escenarios 1–8 del Mapa
de tests) + validación manual de `quickstart.md` (pasos 1–9 y 11): registros válidos, incompletos,
duplicados y con correo inválido; volver, cancelar y confirmar dos veces; aprobar desde el admin.

### Tests for User Story 1 ⚠️

> **NOTE: escribir estos tests PRIMERO y verificar que FALLAN antes de implementar.**
> Todos con `pytestmark = pytest.mark.django_db`, usando las fixtures de T005 y `reverse()` con los
> nombres de URL del contrato (`usuarios:registro`, `usuarios:registro_confirmar`,
> `usuarios:registro_recibido`). Para mensajes del framework, usar `follow=True` o
> `django.contrib.messages.get_messages`.

- [X] T006 [P] [US1] Tests del modelo en `usuarios/tests/test_modelo.py` y limpieza de duplicados en `usuarios/tests/test_setup.py`:
  - `test_normaliza_email_y_nombres` (edge case "espacios laterales"): `create_user(email="  Ana@Lab.COM ")` guarda `"ana@lab.com"`; `Usuario(email="  Ana@Lab.COM ", ...).clean()` deja `"ana@lab.com"`; `RegistroForm` con `first_name="  Ana "`, `last_name=" Pérez  "`, `email="  Ana@Lab.com "` deja en `cleaned_data` `"Ana"`, `"Pérez"`, `"ana@lab.com"`.
  - `test_constraint_email_case_insensitive` (R2): con `ana@lab.com` existente, `Usuario(email="ANA@lab.com", first_name="X", last_name="Y").save()` (salteando formulario y manager) levanta `IntegrityError` dentro de `pytest.raises` + `transaction.atomic()`.
  - `test_create_superuser_activo_y_staff`: `is_active`, `is_staff` e `is_superuser` en `True`.
  - Mover `test_create_user_normaliza_el_email` y `test_create_superuser_crea_usuario_activo_y_staff` de `usuarios/tests/test_setup.py` a estos tests (borrarlos de `test_setup.py`; dejar `test_inicio_sin_sesion_redirige_al_login`).
- [X] T007 [P] [US1] Tests de autenticación en `usuarios/tests/test_autenticacion.py`:
  - `test_cuenta_pendiente_no_autentica` (Esc. 7): `authenticate(email=..., password=...)` con `usuario_pendiente` devuelve `None` y `client.login(...)` devuelve `False`.
  - `test_cuenta_aprobada_autentica` (Esc. 8): con `usuario_aprobado`, `authenticate(...)` devuelve el usuario y `client.login(...)` devuelve `True`.
  - `test_cuenta_registrada_y_aprobada_autentica` (Esc. 7→8 de punta a punta): registrar con el flujo completo (POST formulario + POST `accion=confirmar`), verificar que `authenticate` da `None`, poner `is_active=True` y verificar que ahora autentica con el correo y la contraseña registrados.
- [X] T008 [P] [US1] Tests del admin en `usuarios/tests/test_admin.py` (con `cliente_admin`, URL `reverse("admin:usuarios_usuario_changelist")`):
  - `test_accion_aprobar_activa_cuentas` (Esc. 8, FR-013): POST con `action="aprobar_cuentas"` y `_selected_action=[pk1, pk2]` de dos cuentas pendientes → ambas quedan `is_active=True` y aparece el mensaje "Se aprobaron 2 cuenta(s).".
  - `test_accion_aprobar_es_idempotente`: aplicar la acción a una cuenta ya aprobada no la modifica y no falla.
  - `test_filtro_aprobada_lista_pendientes`: GET con `?is_active__exact=0` muestra el correo de `usuario_pendiente` y no el de `usuario_aprobado`; la página contiene "Aprobada" y "Aprobar cuentas seleccionadas".
- [X] T009 [P] [US1] Tests del formulario (paso 1) en `usuarios/tests/test_registro.py`:
  - `test_registro_accesible_sin_sesion` (FR-001): GET de `usuarios:registro` sin sesión → 200 (no redirige al login). También GET de `usuarios:registro_recibido` → 200.
  - `test_formulario_incompleto_no_avanza` (Esc. 2), parametrizado por `first_name`, `last_name`, `email`, `password1`, `password2` (cada uno vacío) + formulario totalmente vacío: respuesta 200, "Este campo es obligatorio." en el campo, sin `registro_pendiente` en la sesión y `Usuario.objects.count() == 0`.
  - `test_correo_invalido_rechazado` (Esc. 4), parametrizado con `"ana@"`, `"ana.lab.com"`, `"ana@@lab.com"`: 200, error en `email` ("Introduzca una dirección de email válida.", mensaje estándar de Django con `LANGUAGE_CODE="es-ar"`), sin `registro_pendiente`, sin cuentas; además GET de `usuarios:registro_confirmar` → 302 a `usuarios:registro` (no permite confirmar).
  - `test_correo_duplicado_rechazado` (Esc. 3), parametrizado por cuenta existente pendiente **y** aprobada con correo `ana@lab.com`, y por ingreso `"ANA@lab.com"`, `"  ana@lab.com  "`, `"Ana@Lab.Com"`: 200, el error "Este correo no está disponible." aparece **una sola vez**, sin `registro_pendiente` y el count sigue en 1.
  - `test_password_invalida_rechazada` (FR-016), parametrizado con contraseña corta (menos de 8 caracteres), solo números, de uso común (p. ej. `"password123"`) y `password1`/`password2` distintas: 200, error en el campo de contraseña correspondiente, sin `registro_pendiente` y `Usuario.objects.count() == 0`.
  - `test_errores_conservan_datos_validos` (FR-007): POST con correo inválido (y otro con contraseñas distintas) → el HTML conserva los valores de nombre, apellido (y correo cuando es válido).
- [X] T010 [US1] Tests de revisión y confirmación en `usuarios/tests/test_registro.py` (mismo archivo que T009, hacer después):
  - `test_confirmar_crea_cuenta_pendiente` (Esc. 1): POST válido → 302 a `usuarios:registro_confirmar`; GET de la revisión muestra "Ana", "Pérez", "ana@lab.com" y el aviso "Revisá tus datos. Al confirmar, tu cuenta quedará pendiente de aprobación por un administrador."; POST `accion=confirmar` → 302 a `usuarios:registro_recibido`; existe exactamente 1 `Usuario` con `is_active=False`, `is_staff=False`, `is_superuser=False`, `check_password(password_registro)` verdadero; `registro_pendiente` ya no está en la sesión; con `follow=True` aparece "Registro recibido. Vas a poder ingresar cuando un administrador apruebe tu cuenta.".
  - `test_volver_precarga_datos_sin_password` (Esc. 5): con `en_revision`, GET de `usuarios:registro` → 200 con nombre, apellido y correo precargados, los inputs de contraseña sin `value`, y `Usuario.objects.count() == 0`.
  - `test_cancelar_no_crea_cuenta` (Esc. 5, SC-003): con `en_revision`, POST `accion=cancelar` → 302 a `usuarios:registro`, mensaje "Registro cancelado.", sin `registro_pendiente`, count 0; luego GET de `usuarios:registro_confirmar` → 302 a `usuarios:registro`.
  - `test_confirmacion_repetida_crea_una_cuenta` (Esc. 6): dos POST `accion=confirmar` seguidos → el segundo es 302 a `usuarios:registro_recibido`, con `follow=True` muestra "Registro recibido. Vas a poder ingresar cuando un administrador apruebe tu cuenta." y el count es 1.
  - `test_integrity_error_no_crea_segunda_cuenta` (Esc. 6, R7): con `en_revision`, crear directamente `create_user(email="ana@lab.com", ...)` (simula la otra solicitud), luego POST `accion=confirmar` → 302 a `usuarios:registro`, mensaje "Este correo no está disponible." y el count es 1.
  - `test_error_de_base_informa_sin_crear` (FR-011, R8, edge case "si el alta no puede completarse"): con `en_revision`, `monkeypatch` de `usuarios.views.crear_usuario_pendiente` para que levante `DatabaseError` → 200 con la revisión y "No se pudo completar el registro. Intentá nuevamente.", count 0 y `registro_pendiente` sigue en la sesión.
  - `test_password_no_aparece_en_respuestas` (FR-014): la contraseña en texto plano no aparece en `response.content` del formulario con error (p. ej. contraseñas distintas), de la revisión ni de la página de registro recibido.
  - `test_sesion_guarda_hash` (FR-014): tras el POST válido, `session["registro_pendiente"]["password"]` es distinto de la contraseña, `check_password(password_registro, hash)` es verdadero y las claves son exactamente `first_name`, `last_name`, `email`, `password`.

### Implementation for User Story 1

- [X] T011 [US1] Implementar `RegistroForm(BaseUserCreationForm)` en `usuarios/forms.py` (depende de T004):
  - `Meta.model = Usuario`, `Meta.fields = ("first_name", "last_name", "email")`; `password1`/`password2` vienen de `BaseUserCreationForm` (aplica `AUTH_PASSWORD_VALIDATORS` y la coincidencia).
  - Etiquetas del contrato: "Nombre", "Apellido", "Correo electrónico", "Contraseña", "Repetir contraseña". Los cinco campos obligatorios (`required=True`; nombre y apellido ya son `blank=False` en el modelo: "Obligatorio. Sin espacios laterales", `max_length=150`).
  - `clean_email`: normalizar con `UsuarioManager.normalizar_email` (`strip().lower()`) y, si existe `Usuario.objects.filter(email__iexact=email)`, levantar `ValidationError("Este correo no está disponible.")`. Verificar que no se sume un segundo error de unicidad del modelo/constraint (el campo con error queda excluido de `validate_unique`/`validate_constraints`).
  - Método `datos_para_sesion()` que devuelve `{"first_name", "last_name", "email", "password": make_password(cleaned_data["password1"])}` — nunca la contraseña original (data-model, "Datos transitorios").
- [X] T012 [US1] Implementar las vistas en `usuarios/views.py` (vistas de función, todas con `@login_not_required`; constante `CLAVE_SESION = "registro_pendiente"`; depende de T011), según `contracts/registro-ui.md`:
  - `crear_usuario_pendiente(datos)`: dentro de `transaction.atomic()`, `Usuario.objects.create(first_name=..., last_name=..., email=..., password=datos["password"], is_active=False)` (la contraseña ya está hasheada: **no** usar `create_user`, que la volvería a hashear). Devuelve el usuario; deja propagar `IntegrityError`.
  - `registro` (GET/POST): GET → `RegistroForm(initial=...)` con nombre, apellido y correo de la sesión si existen (nunca contraseña). POST válido → `request.session[CLAVE_SESION] = form.datos_para_sesion()` y redirect a `usuarios:registro_confirmar`. POST inválido → 200 con el mismo formulario y sus errores. Nunca crea un `Usuario`.
  - `registro_confirmar` (GET/POST): sin datos en sesión → GET redirige a `usuarios:registro`; POST `accion=confirmar` agrega `messages.info(request, "Registro recibido. Vas a poder ingresar cuando un administrador apruebe tu cuenta.")` y redirige a `usuarios:registro_recibido` sin crear nada (confirmación repetida, R7). GET con datos → render de la revisión con nombre, apellido y correo. POST `accion=cancelar` → borrar `CLAVE_SESION`, `messages.info(request, "Registro cancelado.")`, redirect a `usuarios:registro`. POST `accion=confirmar` → `crear_usuario_pendiente`; éxito: borrar `CLAVE_SESION`, `messages.success(request, "Registro recibido. Vas a poder ingresar cuando un administrador apruebe tu cuenta.")`, redirect a `usuarios:registro_recibido`; `IntegrityError`: `messages.error(request, "Este correo no está disponible.")`, redirect a `usuarios:registro` (los datos quedan en sesión para precargar el formulario); otro `DatabaseError`: `messages.error(request, "No se pudo completar el registro. Intentá nuevamente.")` y render 200 de la revisión. Cualquier otro valor de `accion` → redirect a `usuarios:registro_confirmar`.
  - `registro_recibido` (GET): render de la página de resultado.
- [X] T013 [US1] Agregar las rutas en `usuarios/urls.py` (mantener `app_name = "usuarios"`): `path("registro/", views.registro, name="registro")`, `path("registro/confirmar/", views.registro_confirmar, name="registro_confirmar")`, `path("registro/recibido/", views.registro_recibido, name="registro_recibido")` (depende de T012).
- [X] T014 [P] [US1] Crear `usuarios/templates/usuarios/registro_form.html`: extiende `base.html`, `{% block title %}Registrarse – AquaLab{% endblock %}`, título "Crear cuenta", `<form method="post" novalidate>` con `{% csrf_token %}`, los cinco campos renderizados uno por uno con `<label>`, clase `form-control` y `is-invalid` + `<div class="invalid-feedback">` con los errores del campo cuando los tiene; `form.non_field_errors` como alerta; botón **Continuar**. `novalidate` para que los errores los muestre el servidor (y los tests/validación manual los vean). No renderizar nunca el valor de los campos de contraseña.
- [X] T015 [P] [US1] Crear `usuarios/templates/usuarios/registro_confirmar.html`: extiende `base.html`; aviso "Revisá tus datos. Al confirmar, tu cuenta quedará pendiente de aprobación por un administrador."; lista con Nombre, Apellido y Correo electrónico (sin contraseña ni máscara); acciones: form POST con `{% csrf_token %}`, `<input type="hidden" name="accion" value="confirmar">` y botón **Confirmar** que se deshabilita en el evento `submit` del form (una línea de JS; como `accion` va en un input oculto, deshabilitar el botón no la saca del POST); link **Volver y editar** a `{% url 'usuarios:registro' %}`; otro form POST con `{% csrf_token %}`, `accion=cancelar` oculto y botón **Cancelar**.
- [X] T016 [P] [US1] Crear `usuarios/templates/usuarios/registro_recibido.html`: extiende `base.html` (que ya renderiza `messages` como alertas: no volver a iterarlos acá). Si no hay mensajes (`{% if not messages %}`), mostrar un texto neutro ("No hay un registro en curso.") con link a `{% url 'usuarios:registro' %}`.
- [X] T017 [US1] Completar `UsuarioAdmin` en `usuarios/admin.py` según `contracts/admin-aprobacion.md` (depende de T002–T004):
  - `list_display = ("email", "first_name", "last_name", "is_active", "date_joined")` (columnas "Correo electrónico, Nombre, Apellido, Aprobada, Fecha de registro").
  - `list_filter = ("is_active", "is_staff")`; `search_fields = ("email", "first_name", "last_name")`; `ordering = ("-date_joined",)`.
  - Acción `aprobar_cuentas` con `@admin.action(description="Aprobar cuentas seleccionadas", permissions=["change"])`: `aprobadas = queryset.filter(is_active=False).update(is_active=True)` y `self.message_user(request, f"Se aprobaron {aprobadas} cuenta(s).", messages.SUCCESS)`; `actions = ["aprobar_cuentas"]`. Idempotente: las ya aprobadas no se tocan.
  - `fieldsets`: "Datos personales" (`email`, `first_name`, `last_name`), contraseña (`password`, con el link estándar de Django), "Estado" (`is_active`, que se ve como "Aprobada"), "Permisos" (`is_staff`, `is_superuser`, `groups`, `user_permissions`), "Fechas importantes" (`last_login`, `date_joined`). Mantener `form`, `add_form` y `add_fieldsets` actuales. Quitar el docstring "Admin mínimo…".
- [X] T018 [US1] Correr `docker compose exec web pytest usuarios` y dejar en verde todos los tests de T006–T010; corregir la implementación (no los tests) salvo que un test contradiga el contrato.

**Checkpoint**: la US1 funciona completa y se puede probar sola (tests + quickstart).

---

## Phase 4: Polish & Cross-Cutting Concerns

**Purpose**: calidad, validación final y documentación.

- [X] T019 [P] Correr `docker compose exec web ruff check .` y `docker compose exec web ruff format --check .` y corregir todo (la CI falla con errores de ruff, principio III).
- [X] T020 Validación manual con `specs/001-registrar-usuario/quickstart.md`, pasos 1–9 y 11 (los pasos 10 y 12 esperan a la US 1.2). En el paso 4 revisar también el código fuente de la página de revisión: la contraseña no tiene que aparecer.
- [X] T021 [P] Actualizar los pendientes de `CLAUDE.md` (sección "Pendientes entre features") con lo que esta feature deja para la US 1.2: agregar un link "Iniciar sesión" en `usuarios/templates/usuarios/registro_recibido.html` y un link a `usuarios:registro` desde la pantalla de login. No borrar los pendientes existentes (esta feature no los resuelve).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: sin dependencias.
- **Foundational (Phase 2)**: depende de T001. Bloquea la US1.
- **User Story 1 (Phase 3)**: depende de la fase 2.
- **Polish (Phase 4)**: depende de la US1 completa.

### Dentro de la fase 2

- T002 → T003 (la migración necesita el cambio del modelo).
- T004 y T005 son independientes entre sí y de T002/T003.

### Dentro de la User Story 1

- Tests primero: T006, T007, T008 y T009 en paralelo; T010 después de T009 (mismo archivo).
- Verificar que fallan antes de implementar.
- T011 (formulario) → T012 (vistas) → T013 (rutas).
- T014, T015 y T016 (templates) en paralelo entre sí y con T011–T013; los nombres de URL que usan son los del contrato.
- T017 (admin) solo depende de la fase 2: se puede hacer en paralelo con T011–T016.
- T018 al final de la fase.

### Grafo

```text
T001 → T002 → T003 ─┐
       T004 ────────┼→ T006 T007 T008 T009 → T010 ─┐
       T005 ────────┘                              │
       T004 ───────→ T011 → T012 → T013 ───────────┤
                     T014  T015  T016 ─────────────┼→ T018 → T019 T020 T021
                     T017 ─────────────────────────┘
```

---

## Parallel Example: User Story 1

```bash
# Tests (archivos distintos):
Task: "Tests del modelo en usuarios/tests/test_modelo.py"
Task: "Tests de autenticación en usuarios/tests/test_autenticacion.py"
Task: "Tests del admin en usuarios/tests/test_admin.py"
Task: "Tests del formulario en usuarios/tests/test_registro.py"

# Implementación (archivos distintos), en paralelo con la cadena forms → views → urls:
Task: "Template usuarios/templates/usuarios/registro_form.html"
Task: "Template usuarios/templates/usuarios/registro_confirmar.html"
Task: "Template usuarios/templates/usuarios/registro_recibido.html"
Task: "UsuarioAdmin + acción aprobar_cuentas en usuarios/admin.py"
```

---

## Implementation Strategy

### MVP (la única user story)

1. Fase 1: verificar el entorno del setup.
2. Fase 2: migración de etiquetas, `forms.py` y fixtures.
3. Fase 3: tests (fallando) → formulario → vistas → rutas → templates → admin → tests en verde.
4. **STOP y VALIDAR**: `pytest usuarios` + quickstart.
5. Fase 4: ruff, CLAUDE.md y PR "US 1.1 – Registrar usuario" referenciando `specs/001-registrar-usuario/`.

### Entrega incremental dentro de la US1

1. Formulario + revisión + confirmación (Esc. 1–6) → ya se pueden registrar cuentas pendientes.
2. Admin con la acción de aprobar (Esc. 8) → cuentas aprobables sin entrar ficha por ficha.
3. Esc. 7 no necesita código propio (`ModelBackend` rechaza `is_active=False`): solo sus tests.

---

## Notes

- [P] = archivos distintos y sin dependencias pendientes.
- Commit después de cada tarea o grupo lógico.
- No tocar lo del setup salvo lo que indican T002–T004 (campos con etiquetas del dominio, migración
  `0002` y mover los formularios del admin).
- La contraseña nunca se guarda en texto plano en la sesión ni se reenvía al navegador (FR-014,
  principio V).
