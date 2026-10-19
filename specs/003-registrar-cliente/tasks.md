---

description: "Lista de tareas de la US 2.1 – Registrar cliente"
---

# Tasks: Registrar cliente

**Input**: Documentos de diseño en `specs/003-registrar-cliente/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/registro-cliente-ui.md,
quickstart.md

**Tests**: SÍ. La constitution (Principio III) exige al menos un test automatizado con
pytest-django por cada escenario de aceptación. Los tests siguen el "Mapa de tests" de `plan.md` y
se escriben **antes** de la implementación (deben fallar primero).

**Alcance**: el setup de infraestructura ya está mergeado en esta rama (`config/settings.py`,
`LoginRequiredMiddleware`, modelo `usuarios.Usuario`, `templates/base.html` con mensajes, Docker y
CI). **No hay tareas para recrearlo**: esta feature crea la nueva app `clientes` y agrega solo el
registro en `INSTALLED_APPS`, `config/urls.py` y el enlace en `templates/inicio.html`.

**Organization**: la spec tiene una sola user story (US1, P1); todas las tareas de producto están
en su fase.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: se puede hacer en paralelo (archivos distintos, sin dependencias pendientes)
- **[Story]**: user story a la que pertenece la tarea (`[US1]`)
- Rutas relativas a la raíz del repo (`config/`, `templates/`, `clientes/`)

## Convenciones para todas las tareas

- Textos de UI, mensajes, `verbose_name` y nombres de modelos/funciones/variables del dominio en
  **español** siguiendo el Glosario (Principio VI).
- Los mensajes al usuario se copian **literalmente** de `contracts/registro-cliente-ui.md`.
- Comandos dentro de Docker: `docker compose exec web pytest clientes`,
  `docker compose exec web ruff check .`, `docker compose exec web ruff format --check .`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: confirmar que el entorno actual funciona en esta rama antes de agregar la app
`clientes`.

- [ ] T001 Verificar el entorno en `docker-compose.yml`: correr `docker compose up -d --build`, `docker compose exec web python manage.py migrate` y `docker compose exec web pytest` para confirmar que la base y los tests existentes pasan sin errores. No modificar archivos del setup.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: crear la app `clientes`, el modelo `Cliente` con sus validadores y constraints, la
migración inicial y las fixtures que necesitan tanto los tests como la implementación de la US1.

**⚠️ CRITICAL**: no empezar la fase 3 hasta terminar esta fase.

- [ ] T002 Crear la estructura base de la app `clientes` (`clientes/__init__.py`, `clientes/apps.py` con `ClientesConfig` donde `name = "clientes"`, `verbose_name = "Clientes"` y `default_auto_field = "django.db.models.BigAutoField"`, `clientes/migrations/__init__.py`, `clientes/tests/__init__.py`) y agregar `"clientes"` a `INSTALLED_APPS` en `config/settings.py`.
- [ ] T003 Implementar en `clientes/models.py` el modelo `Cliente`, la enumeración `TipoDocumento` y las funciones de normalización y validación según `data-model.md` (depende de T002):
  - `TipoDocumento(models.TextChoices)` con `DNI = "DNI", "DNI"` y `CUIT = "CUIT", "CUIT"`.
  - `normalizar_numero_documento(valor)`: elimina espacios, puntos y guiones con `re.sub(r"[\s.\-]", "", valor or "")`.
  - `es_cuit_valido(cuit)`: comprueba que `cuit` tenga 11 dígitos numéricos y que su undécimo dígito coincida con el cálculo módulo 11 con pesos `[5, 4, 3, 2, 7, 6, 5, 4, 3, 2]` (`resto = suma % 11`; `dv = 0` si `resto == 0`, `9` si `resto == 1`, `11 - resto` en otro caso).
  - `validar_documento(tipo, numero)`: si `tipo == "DNI"`, exige `numero.isdigit()` y `len(numero) in (7, 8)` o levanta `ValidationError({"numero_documento": "El DNI debe tener 7 u 8 dígitos numéricos."})`; si `tipo == "CUIT"`, exige `es_cuit_valido(numero)` o levanta `ValidationError({"numero_documento": "El CUIT debe tener 11 dígitos y un dígito verificador válido."})`.
  - `validar_telefono(valor)`: si `valor` no es vacío, exige `re.fullmatch(r"[+\d\s\-()]+", valor)` y entre 7 y 15 dígitos numéricos o levanta `ValidationError("Ingresá un número de teléfono válido (entre 7 y 15 dígitos).")`.
  - Campos de `Cliente` con las restricciones exactas de `data-model.md`:
    - `nombre = models.CharField("nombre", max_length=200, blank=True)` (sin espacios laterales; obligatorio si `razon_social` está vacío).
    - `razon_social = models.CharField("razón social", max_length=200, blank=True)` (sin espacios laterales; obligatorio si `nombre` está vacío).
    - `tipo_documento = models.CharField("tipo de documento", max_length=4, choices=TipoDocumento.choices)` (obligatorio, `blank=False`, valores `"DNI"` o `"CUIT"`).
    - `numero_documento = models.CharField("número de documento", max_length=11)` (obligatorio, `blank=False`, guardado normalizado solo con dígitos).
    - `email = models.EmailField("correo electrónico", max_length=254)` (obligatorio, `blank=False`, guardado normalizado con `strip().lower()`).
    - `telefono = models.CharField("teléfono", max_length=30, blank=True)` (opcional, `blank=True`, sin espacios laterales).
    - `domicilio = models.CharField("domicilio", max_length=255, blank=True)` (opcional, `blank=True`, sin espacios laterales).
    - `activo = models.BooleanField("activo", default=True)`.
    - `fecha_alta = models.DateTimeField("fecha de alta", auto_now_add=True)`.
  - `Meta`: `verbose_name = "cliente"`, `verbose_name_plural = "clientes"`, `ordering = ("razon_social", "nombre", "id")`, `UniqueConstraint(fields=["tipo_documento", "numero_documento"], name="cliente_documento_unico", violation_error_message="Ya existe un cliente registrado con este tipo y número de documento.")` y `CheckConstraint(condition=~Q(nombre="", razon_social=""), name="cliente_nombre_o_razon_social_obligatorio")`.
  - Propiedad `nombre_completo`, `__str__` y `clean()` que normaliza los campos, verifica que al menos uno entre `nombre` y `razon_social` no esté vacío (`"Debés ingresar al menos el nombre o la razón social del cliente."`) y ejecuta `validar_documento` y `validar_telefono`.
- [ ] T004 Generar la migración inicial `clientes/migrations/0001_initial.py` con `docker compose exec web python manage.py makemigrations clientes` y aplicarla con `docker compose exec web python manage.py migrate` (depende de T003).
- [ ] T005 [P] Crear `clientes/urls.py` con `app_name = "clientes"` y `urlpatterns = []`, y registrar `path("clientes/", include("clientes.urls"))` en `config/urls.py` (depende de T002).
- [ ] T006 [P] Crear `clientes/tests/conftest.py` con fixtures compartidas para los tests de `clientes` (depende de T003):
  - `empleado`: usuario activo creado con `django_user_model.objects.create_user(email="empleado@lab.com", password="Clave-Valida-123", first_name="Laura", last_name="Martínez", is_active=True)`.
  - `cliente_autenticado`: `Client` con `force_login(empleado)`.
  - `datos_cliente_persona`: dict válido con `nombre="Juan Pérez"`, `razon_social=""`, `tipo_documento="DNI"`, `numero_documento="30.123.456"`, `email="juan@ejemplo.com"`, `telefono="+54 11 4321-5678"`, `domicilio="Av. Corrientes 1234"`.
  - `datos_cliente_empresa`: dict válido con `nombre=""`, `razon_social="Aguas del Sur S.A."`, `tipo_documento="CUIT"`, `numero_documento="20-12345678-6"`, `email="contacto@aguassur.com"`, `telefono=""`, `domicilio=""`.
  - `cliente_existente`: `Cliente.objects.create(razon_social="Aguas del Sur S.A.", tipo_documento="CUIT", numero_documento="20123456786", email="contacto@aguassur.com")`.
  - `en_revision`: ejecuta `cliente_autenticado.post(reverse("clientes:registrar"), datos_cliente_empresa)` y devuelve `cliente_autenticado` con `session["cliente_pendiente"]` cargado.

**Checkpoint**: migración `0001_initial.py` aplicada, tabla `clientes_cliente` creada con sus constraints y fixtures listas.

---

## Phase 3: User Story 1 - Registrar cliente (Priority: P1) 🎯 MVP

**Goal**: un empleado con sesión activa ingresa los datos identificatorios y de contacto de un
cliente, los revisa en la instancia de confirmación y confirma el alta; se crea un único registro
`Cliente` (`activo=True`) que puede consultarse de inmediato en su ficha de detalle.

**Independent Test**: `docker compose exec web pytest clientes` en verde (escenarios 1–8 del Mapa
de tests) + validación manual de `quickstart.md` (pasos 1–12).

### Tests for User Story 1 ⚠️

> **NOTE: escribir estos tests PRIMERO y verificar que FALLAN antes de implementar las vistas y el formulario.**
> Todos con `pytestmark = pytest.mark.django_db`, usando las fixtures de T006 y `reverse()` con los
> nombres de URL del contrato (`clientes:registrar`, `clientes:registrar_confirmar`,
> `clientes:detalle`).

- [ ] T007 [P] [US1] Crear tests unitarios del modelo, normalización, validadores y constraints en `clientes/tests/test_modelo.py`:
  - `test_normaliza_campos_y_documento` (Edge cases 2 y 3): `Cliente(nombre="  Juan Pérez ", razon_social="  ", tipo_documento="CUIT", numero_documento=" 20-12345678-6 ", email="  Juan@Lab.COM ", telefono=" +54 11 4321-5678 ", domicilio=" Calle 123 ").clean()` deja `nombre="Juan Pérez"`, `razon_social=""`, `numero_documento="20123456786"`, `email="juan@lab.com"`, `telefono="+54 11 4321-5678"`, `domicilio="Calle 123"`.
  - `test_validador_cuit_modulo_11` (FR-016, Esc. 8): verifica `es_cuit_valido` con CUITs válidos (`"20123456786"`, `"27234567891"`, `"30712345620"` con resto 0) e inválidos (`"20123456780"` con dígito verificador erróneo, `"2012345678"` de 10 dígitos, `"201234567860"` de 12 dígitos y `"2012345678A"` con letras).
  - `test_constraint_documento_unico` (FR-007, R4): con `cliente_existente` en la base, `Cliente(razon_social="Otra", tipo_documento="CUIT", numero_documento="20123456786", email="otra@lab.com").save()` levanta `IntegrityError` dentro de `pytest.raises(IntegrityError)` + `transaction.atomic()`.
  - `test_constraint_nombre_o_razon_social_obligatorio` (FR-003, R2): `Cliente(nombre="", razon_social="", tipo_documento="DNI", numero_documento="30123456", email="a@b.com").full_clean()` levanta `ValidationError`, y `.save()` directo levanta `IntegrityError` por el `CheckConstraint` `cliente_nombre_o_razon_social_obligatorio`.
- [ ] T008 [P] [US1] Crear tests del formulario y validaciones de entrada (paso 1) en `clientes/tests/test_registro.py`:
  - `test_vistas_requieren_sesion_activa` (FR-001): GET y POST sin sesión a `clientes:registrar`, `clientes:registrar_confirmar` y GET a `clientes:detalle` (con `cliente_existente.pk`) responden 302 hacia el login.
  - `test_formulario_incompleto_no_avanza` (Esc. 3, FR-003, FR-004, FR-005, SC-002), parametrizado por: `nombre` y `razon_social` ambos vacíos (muestra `"Debés ingresar al menos el nombre o la razón social del cliente."`), `tipo_documento` vacío, `numero_documento` vacío, `email` vacío y formulario totalmente vacío (`"Este campo es obligatorio."`): respuesta 200, sin `cliente_pendiente` en la sesión y `Cliente.objects.count() == 0`.
  - `test_dni_formato_invalido_rechazado` (Esc. 8, FR-016, SC-005), parametrizado con `"123456"` (6 dígitos), `"123456789"` (9 dígitos) y `"12A45678"`: respuesta 200, error `"El DNI debe tener 7 u 8 dígitos numéricos."` en `numero_documento`, sin `cliente_pendiente` en sesión y `Cliente.objects.count() == 0`.
  - `test_cuit_formato_o_digito_verificador_invalido_rechazado` (Esc. 8, FR-016, SC-005), parametrizado con `"2012345678"` (10 dígitos), `"201234567890"` (12 dígitos), `"20-12345678-0"` (dígito verificador inválido) y `"20-1234567A-6"`: respuesta 200, error `"El CUIT debe tener 11 dígitos y un dígito verificador válido."` en `numero_documento`, sin `cliente_pendiente` en sesión y `Cliente.objects.count() == 0`.
  - `test_documento_duplicado_con_separadores_rechazado` (Esc. 4, FR-007, SC-003), usando `cliente_existente` y parametrizado con `"20123456786"`, `"20-12345678-6"`, `"20.123.456.786"` y `" 20 12345678 6 "`: respuesta 200, el error `"Ya existe un cliente registrado con este tipo y número de documento."` aparece **una sola vez**, sin `cliente_pendiente` en sesión y `Cliente.objects.count() == 1`.
  - `test_correo_invalido_rechazado` (Esc. 5, FR-006), parametrizado con `"cliente@"`, `"cliente.com"` y `"cliente@@lab.com"`: respuesta 200, error `"Introduzca una dirección de email válida."` en `email`, sin `cliente_pendiente` en sesión, `Cliente.objects.count() == 0`, y un GET posterior a `clientes:registrar_confirmar` redirige (302) a `clientes:registrar`.
  - `test_telefono_invalido_rechazado` (Esc. 5, FR-006), parametrizado con `"12345"` (menos de 7 dígitos), `"telefono-abc"` y `"+54 11 123456789012345"` (más de 15 dígitos): respuesta 200, error `"Ingresá un número de teléfono válido (entre 7 y 15 dígitos)."` en `telefono`, sin `cliente_pendiente` en sesión y `Cliente.objects.count() == 0`.
  - `test_errores_conservan_datos_validos` (FR-008, FR-009): POST con `numero_documento` inválido conserva en el HTML de respuesta los valores válidos ingresados en `nombre`, `razon_social`, `email`, `telefono` y `domicilio`.
- [ ] T009 [US1] Agregar tests de revisión, confirmación, idempotencia y ficha de detalle (pasos 2 y 3) en `clientes/tests/test_registro.py` (mismo archivo que T008, hacer después):
  - `test_confirmar_crea_cliente_persona_con_dni` (Esc. 1, FR-002, FR-010, FR-013, FR-014, SC-001, SC-004): POST válido con `datos_cliente_persona` → 302 a `clientes:registrar_confirmar`; GET de la revisión muestra `"Revisá los datos del cliente antes de confirmar el registro."`, `"Juan Pérez"`, `"DNI"`, `"30123456"`, `"juan@ejemplo.com"`, `"+54 11 4321-5678"`, `"Av. Corrientes 1234"`; POST `accion=confirmar` → 302 a `clientes:detalle`; existe exactamente 1 `Cliente` con `activo=True` y `numero_documento == "30123456"`; `cliente_pendiente` ya no está en la sesión; con `follow=True` aparece `"Cliente registrado correctamente."`.
  - `test_confirmar_crea_cliente_empresa_con_cuit` (Esc. 1, Edge cases 1 y 4): flujo completo con `datos_cliente_empresa` (solo `razon_social`, `CUIT` con guiones, sin `telefono` ni `domicilio`) crea 1 `Cliente` con `razon_social == "Aguas del Sur S.A."`, `nombre == ""`, `numero_documento == "20123456786"`, `telefono == ""`, `domicilio == ""` y `activo=True`.
  - `test_detalle_muestra_todos_los_datos_registrados` (Esc. 2, SC-004): GET a `clientes:detalle` muestra todos los datos registrados del cliente y el estado `"Activo"`; GET con un `pk` inexistente devuelve 404.
  - `test_volver_y_editar_precarga_datos_sin_crear_cliente` (Esc. 6, FR-011): con `en_revision`, GET a `clientes:registrar` devuelve 200 con los datos precargados desde la sesión y `Cliente.objects.count() == 0`.
  - `test_cancelar_borra_sesion_y_no_crea_cliente` (Esc. 6, FR-011, SC-002): con `en_revision`, POST `accion=cancelar` → 302 a `clientes:registrar`, mensaje `"Registro de cliente cancelado."`, sin `cliente_pendiente` en la sesión, `Cliente.objects.count() == 0`, y luego GET a `clientes:registrar_confirmar` redirige (302) a `clientes:registrar`.
  - `test_confirmacion_repetida_crea_un_solo_cliente` (Esc. 7, FR-012): con `en_revision`, dos POST `accion=confirmar` seguidos → el segundo responde 302 a `clientes:detalle` del mismo cliente, muestra `"Cliente registrado correctamente."` con `follow=True` y `Cliente.objects.count() == 1`.
  - `test_integrity_error_al_confirmar_no_duplica_cliente` (Esc. 7, FR-007, FR-012, R7): con `en_revision`, crear directamente `Cliente.objects.create(razon_social="Otra", tipo_documento="CUIT", numero_documento="20123456786", email="otra@lab.com")` antes del POST `accion=confirmar` → el POST responde 302 a `clientes:registrar`, muestra `"Ya existe un cliente registrado con este tipo y número de documento."` y `Cliente.objects.count() == 1`.
  - `test_error_de_base_al_confirmar_informa_sin_crear` (FR-013, Edge case 6, R8): con `en_revision`, `monkeypatch` de `clientes.views.crear_cliente` para que levante `DatabaseError` → responde 200 en la revisión con `"No se pudo completar el registro del cliente. Intentá nuevamente."`, `Cliente.objects.count() == 0` y `cliente_pendiente` sigue en la sesión.

### Implementation for User Story 1

- [ ] T010 [US1] Implementar `RegistroClienteForm(forms.ModelForm)` en `clientes/forms.py` según `data-model.md` y `contracts/registro-cliente-ui.md` (depende de T003):
  - `Meta.model = Cliente`, `Meta.fields = ("nombre", "razon_social", "tipo_documento", "numero_documento", "email", "telefono", "domicilio")`.
  - Redefinir en el formulario `numero_documento = forms.CharField(label="Número de documento", max_length=30, strip=True)` para que `MaxLengthValidator(11)` del modelo no rechace entradas con puntos, guiones o espacios (p. ej. `"20-12345678-6"` de 13 caracteres) antes de normalizarlas.
  - Etiquetas exactas del contrato: `"Nombre"`, `"Razón social"`, `"Tipo de documento"`, `"Número de documento"`, `"Correo electrónico"`, `"Teléfono"`, `"Domicilio"`.
  - Limpieza de espacios laterales (`strip=True`), `clean_email` (`strip().lower()`), `clean_telefono` (`validar_telefono`) y `clean()` que valida: (1) al menos uno entre `nombre` y `razon_social` no vacío (`ValidationError("Debés ingresar al menos el nombre o la razón social del cliente.")`), (2) normalización de `numero_documento` con `normalizar_numero_documento` y formato según `tipo_documento` con `validar_documento`, y (3) unicidad de `(tipo_documento, numero_documento)` con `Cliente.objects.filter(tipo_documento=..., numero_documento=...).exists()` agregando error en `numero_documento`: `"Ya existe un cliente registrado con este tipo y número de documento."` (evitando duplicar el error en `validate_unique` / `validate_constraints`).
  - Método `datos_para_sesion()` que devuelve el dict con las 7 claves normalizadas (`nombre`, `razon_social`, `tipo_documento`, `numero_documento`, `email`, `telefono`, `domicilio`).
- [ ] T011 [US1] Implementar las vistas `registrar`, `registrar_confirmar`, `detalle` y el helper `crear_cliente(datos)` en `clientes/views.py` según `contracts/registro-cliente-ui.md` (depende de T010):
  - Constantes `CLAVE_SESION = "cliente_pendiente"` y `CLAVE_ULTIMO_ID = "ultimo_cliente_creado_id"`. Todas las vistas requieren sesión activa (`LoginRequiredMiddleware`).
  - `crear_cliente(datos)`: dentro de `transaction.atomic()`, ejecuta `Cliente.objects.create(**datos, activo=True)` y devuelve el cliente.
  - `registrar` (GET/POST): GET inicializa `RegistroClienteForm(initial=request.session.get(CLAVE_SESION))`; POST válido guarda `request.session[CLAVE_SESION] = form.datos_para_sesion()`, elimina `CLAVE_ULTIMO_ID` de la sesión si existía y redirige a `clientes:registrar_confirmar`; POST inválido responde 200 con el formulario y sus errores.
  - `registrar_confirmar` (GET/POST):
    - Si `request.method == "GET"`: sin `CLAVE_SESION` redirige a `clientes:registrar`; con datos, renderiza `clientes/registro_confirmar.html` pasando `datos`.
    - Si `accion == "cancelar"`: elimina `CLAVE_SESION` y `CLAVE_ULTIMO_ID` de la sesión, agrega `messages.info(request, "Registro de cliente cancelado.")` y redirige a `clientes:registrar`.
    - Si `accion == "confirmar"`: si no hay `CLAVE_SESION` en la sesión, busca `ultimo_id = request.session.get(CLAVE_ULTIMO_ID)` y si existe ese `Cliente` en la base agrega `messages.info(request, "Cliente registrado correctamente.")` y redirige a `clientes:detalle` (`pk=ultimo_id`), o a `clientes:registrar` en caso contrario. Si hay `CLAVE_SESION`, llama a `crear_cliente(datos)`: en éxito borra `CLAVE_SESION`, guarda `request.session[CLAVE_ULTIMO_ID] = cliente.pk`, agrega `messages.success(request, "Cliente registrado correctamente.")` y redirige a `clientes:detalle` (`pk=cliente.pk`); si levanta `IntegrityError`, agrega `messages.error(request, "Ya existe un cliente registrado con este tipo y número de documento.")` y redirige a `clientes:registrar`; si levanta otro `DatabaseError`, agrega `messages.error(request, "No se pudo completar el registro del cliente. Intentá nuevamente.")` y renderiza 200 `clientes/registro_confirmar.html`.
    - Cualquier otro valor de `accion` redirige a `clientes:registrar_confirmar`.
  - `detalle` (GET): obtiene `cliente = get_object_or_404(Cliente, pk=pk)` y renderiza `clientes/detalle.html`.
- [ ] T012 [US1] Registrar las rutas en `clientes/urls.py` (`app_name = "clientes"`): `path("registrar/", views.registrar, name="registrar")`, `path("registrar/confirmar/", views.registrar_confirmar, name="registrar_confirmar")` y `path("<int:pk>/", views.detalle, name="detalle")` (depende de T005 y T011).
- [ ] T013 [P] [US1] Crear `clientes/templates/clientes/registro_form.html` extendiendo `base.html`: `{% block title %}Registrar cliente · AquaLab{% endblock %}`, título `"Registrar cliente"`, `<form method="post" novalidate>` con `{% csrf_token %}`, alerta `alert-danger` para `form.non_field_errors`, los 7 campos renderizados con `<label>`, clase `form-control` / `form-select`, `is-invalid` y `<div class="invalid-feedback">` con los errores del campo, y botón **Continuar**.
- [ ] T014 [P] [US1] Crear `clientes/templates/clientes/registro_confirmar.html` extendiendo `base.html`: `{% block title %}Confirmar cliente · AquaLab{% endblock %}`, aviso `"Revisá los datos del cliente antes de confirmar el registro."`, resumen de Nombre, Razón social, Tipo de documento, Número de documento, Correo electrónico, Teléfono y Domicilio (mostrando `"—"` cuando un campo opcional está vacío), form POST con `{% csrf_token %}`, `<input type="hidden" name="accion" value="confirmar">` y botón **Confirmar** que se deshabilita en el `submit`, link **Volver y editar** a `{% url 'clientes:registrar' %}` y form POST con `{% csrf_token %}`, `<input type="hidden" name="accion" value="cancelar">` y botón **Cancelar**.
- [ ] T015 [P] [US1] Crear `clientes/templates/clientes/detalle.html` extendiendo `base.html`: `{% block title %}Cliente · AquaLab{% endblock %}`, título `"Ficha del cliente"`, lista de definición con todos los datos registrados del cliente (Nombre, Razón social, Tipo de documento, Número de documento, Correo electrónico, Teléfono, Domicilio y Estado `"Activo"` / `"Inactivo"`) y botón **"Registrar otro cliente"** hacia `{% url 'clientes:registrar' %}`.
- [ ] T016 [P] [US1] Configurar `ClienteAdmin` en `clientes/admin.py` con `@admin.register(Cliente)`: `list_display = ("nombre_completo", "tipo_documento", "numero_documento", "email", "telefono", "activo", "fecha_alta")`, `list_filter = ("tipo_documento", "activo")`, `search_fields = ("nombre", "razon_social", "numero_documento", "email")` y `readonly_fields = ("fecha_alta",)` (depende de T003).
- [ ] T017 [P] [US1] Agregar en `templates/inicio.html` un botón/enlace `"Registrar cliente"` que apunte a `{% url 'clientes:registrar' %}` (depende de T012).
- [ ] T018 [US1] Correr `docker compose exec web pytest clientes` y `docker compose exec web pytest` y dejar en verde todos los tests de T007–T009 junto con la suite completa del proyecto (depende de T007–T017).

**Checkpoint**: la US 2.1 funciona completa y es verificable de forma independiente (tests automatizados + quickstart).

---

## Phase 4: Polish & Cross-Cutting Concerns

**Purpose**: calidad de código, validación manual de punta a punta y notas entre features.

- [ ] T019 [P] Correr `docker compose exec web ruff check .` y `docker compose exec web ruff format --check .` y corregir cualquier observación de lint o formato en todo el repositorio (Principio III y VI).
- [ ] T020 Ejecutar la validación manual siguiendo `specs/003-registrar-cliente/quickstart.md` (pasos 1 a 12).
- [ ] T021 [P] Actualizar `CLAUDE.md` (sección "Pendientes entre features") documentando para las US 3.1/3.2 y US 4.1 que el modelo `clientes.Cliente` (con `activo=True`) y la vista `clientes:detalle` ya están disponibles, y recordando la decisión pendiente sobre el campo "persona de contacto" antes de la US 3.2 (Assumptions de `spec.md`).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: sin dependencias.
- **Foundational (Phase 2)**: depende de T001. Bloquea la US1.
- **User Story 1 (Phase 3)**: depende de la fase 2 completa.
- **Polish (Phase 4)**: depende de la US1 completa (T018).

### Dentro de la fase 2

- T002 → T003 → T004 (crear app → definir modelo `Cliente` → generar y aplicar migración).
- T005 depende de T002; T006 depende de T003.

### Dentro de la User Story 1

- **Tests primero**: T007 y T008 en paralelo; T009 después de T008 (mismo archivo `test_registro.py`).
- Verificar que los tests fallan antes de escribir la implementación.
- Cadena de backend: T010 (`forms.py`) → T011 (`views.py`) → T012 (`urls.py`).
- En paralelo con T010–T012: T013, T014 y T015 (templates) y T016 (`admin.py`).
- T017 (`templates/inicio.html`) después de T012.
- T018 al final de la fase para validar toda la suite en verde.

### Grafo

```text
T001 → T002 → T003 → T004 ─┐
              │      T005 ─┼→ T007 T008 → T009 ─┐
              └────→ T006 ─┘                    │
                     T003 ─→ T010 → T011 → T012 → T017 ─┼→ T018 → T019 T020 T021
                             T013   T014   T015 ────────┤
                             T016 ──────────────────────┘
```

---

## Parallel Example: User Story 1

```bash
# Tests (archivos distintos):
Task: "Tests del modelo en clientes/tests/test_modelo.py"
Task: "Tests del formulario y registro en clientes/tests/test_registro.py"

# Implementación en paralelo con la cadena forms → views → urls:
Task: "Template clientes/templates/clientes/registro_form.html"
Task: "Template clientes/templates/clientes/registro_confirmar.html"
Task: "Template clientes/templates/clientes/detalle.html"
Task: "Configuración de ClienteAdmin en clientes/admin.py"
```

---

## Implementation Strategy

### En dos tandas (según `docs/guias/guia-sdd-paso-a-paso.md`)

1. **Tanda 1 (Fases 1 y 2 — T001 a T006)**: verificar entorno, crear app `clientes`, modelo
   `Cliente` con validadores y constraints, migración `0001_initial.py`, `clientes/urls.py` base y
   fixtures en `clientes/tests/conftest.py`. Frenar, revisar y hacer commit.
2. **Tanda 2 (Fases 3 y 4 — T007 a T021)**: escribir primero los tests (`T007`–`T009`) y comprobar
   que fallan; luego implementar `forms.py`, `views.py`, `urls.py`, templates, `admin.py` e
   `inicio.html`; dejar `pytest` y `ruff` en verde, actualizar `CLAUDE.md` y hacer commit.
