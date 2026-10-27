---

description: "Lista de tareas de la US 4.1 – Registrar muestra"
---

# Tasks: Registrar muestra

**Input**: `specs/007-registrar-muestra/` (`plan.md`, `spec.md`, `research.md`, `data-model.md`,
`contracts/registro-muestra-ui.md`, `quickstart.md`)

**Prerequisites**: `plan.md`, `spec.md`. Ya existen y no se recrean: `clientes.Cliente` (con
`activo`, `nombre_completo`, `normalizar_numero_documento`), `usuarios.Usuario`
(`AUTH_USER_MODEL`), `LoginRequiredMiddleware`, `templates/base.html`, `templates/inicio.html`,
Docker y CI.

**Tests**: SÍ. La constitution (Principio III) exige al menos un test con pytest-django por cada
escenario de aceptación. Los tests siguen el "Mapa de tests" de `plan.md` y se escriben **antes** de
la implementación de cada historia (deben fallar primero).

**Organization**: tres user stories de la spec — US1 (P1, registrar con origen conocido), US2 (P2,
origen nuevo desde el formulario) y US3 (P3, impedir datos incompletos o inconsistentes).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: se puede ejecutar en paralelo (archivos distintos, sin dependencias pendientes)
- **[Story]**: user story a la que pertenece la tarea (`[US1]`, `[US2]`, `[US3]`)
- Rutas relativas a la raíz del repo

## Convenciones para todas las tareas

- Textos de UI, mensajes y nombres de dominio en **español** según el Glosario (Principio VI).
- Mensajes al usuario copiados **literalmente** de `contracts/registro-muestra-ui.md`.
- Estilo de formularios, vistas y templates igual al de `clientes/forms.py`, `clientes/views.py` y
  `clientes/templates/clientes/registro_*.html` (clases Bootstrap, `is-invalid`/`invalid-feedback`,
  constantes `MENSAJE_*` y `CLAVE_*` arriba de `views.py`).
- Comandos dentro de Docker: `docker compose exec web pytest muestras`,
  `docker compose exec web ruff check .`, `docker compose exec web ruff format --check .`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: entorno verificado y app `muestras` creada y conectada (`research.md` R1, R8).

- [X] T001 Verificar el entorno con `docker compose up -d`, `docker compose exec web python manage.py migrate` y `docker compose exec web pytest` (sobre `docker-compose.yml`) y confirmar que la suite actual pasa antes de tocar código.
- [X] T002 Crear el esqueleto de la app `muestras`: `muestras/__init__.py`, `muestras/apps.py` (`MuestrasConfig`, `name = "muestras"`, `verbose_name = "Muestras"`, `default_auto_field = "django.db.models.BigAutoField"` igual que `clientes/apps.py`), `muestras/migrations/__init__.py`, `muestras/tests/__init__.py` y `muestras/urls.py` con `app_name = "muestras"` y `urlpatterns = []`.
- [X] T003 Agregar `"muestras"` al final de `INSTALLED_APPS` en `config/settings.py` y `path("muestras/", include("muestras.urls"))` en `config/urls.py` (antes de la ruta `""` de inicio) (depende de T002).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: modelos, migración, admin y fixtures que usan las tres historias (`data-model.md`).

**⚠️ CRITICAL**: no empezar ninguna user story hasta terminar esta fase.

- [X] T004 Crear `muestras/models.py` según `data-model.md`:
  - `TipoVertido(models.TextChoices)`: `AGUA = "agua", "Agua"`, `CLOACAL = "cloacal", "Cloacal"`, `CANAL = "canal", "Canal"`.
  - `EstadoMuestra(models.TextChoices)`: `INGRESADA = "ingresada", "Ingresada"`.
  - Constantes `NUMERO_PI_INICIAL = 200001` y `NOMBRE_MUESTRA_POR_DEFECTO = "Muestra 1"`.
  - `Origen`: `cliente` FK a `"clientes.Cliente"` (`on_delete=models.PROTECT`, `related_name="origenes"`, `verbose_name="cliente"`); `nombre = CharField("nombre", max_length=150)`; `fecha_alta = DateTimeField("fecha de alta", auto_now_add=True)`. `Meta`: `verbose_name="origen"`, `verbose_name_plural="orígenes"`, `ordering=("nombre",)`, `constraints=[UniqueConstraint(Lower("nombre"), F("cliente"), name="origen_nombre_unico_por_cliente", violation_error_message="El cliente ya tiene un origen con ese nombre.")]`. `__str__` → `self.nombre`. `clean()` aplica `strip()` a `nombre`.
  - `Muestra`: `numero_pi = PositiveIntegerField("N° PI", unique=True, editable=False)`; `nombre = CharField("nombre", max_length=100, default=NOMBRE_MUESTRA_POR_DEFECTO)`; `cliente` FK a `"clientes.Cliente"` (`PROTECT`, `related_name="muestras"`); `origen` FK a `Origen` (`PROTECT`, `related_name="muestras"`); `fecha_muestreo = DateField("fecha de muestreo")`; `fecha_ingreso = DateField("fecha de ingreso")`; `sitio_extraccion = CharField("sitio de extracción", max_length=200)`; `tipo_vertido = CharField("tipo de vertido", max_length=10, choices=TipoVertido.choices, default=TipoVertido.AGUA)`; `responsable_muestreo = CharField("responsable del muestreo", max_length=150, blank=True)`; `estado = CharField("estado", max_length=20, choices=EstadoMuestra.choices, default=EstadoMuestra.INGRESADA, editable=False)`; `registrada_por` FK a `settings.AUTH_USER_MODEL` (`PROTECT`, `editable=False`, `related_name="muestras_registradas"`, `verbose_name="registrada por"`); `fecha_registro = DateTimeField("fecha de registro", auto_now_add=True)`.
  - `Muestra.Meta`: `verbose_name="muestra"`, `verbose_name_plural="muestras"`, `ordering=("-numero_pi",)`, `constraints=[CheckConstraint(condition=Q(numero_pi__gte=NUMERO_PI_INICIAL), name="muestra_numero_pi_desde_200001"), CheckConstraint(condition=Q(fecha_muestreo__lte=F("fecha_ingreso")), name="muestra_muestreo_no_posterior_a_ingreso")]`.
  - `Muestra.__str__` → `f"N° PI {self.numero_pi} – {self.nombre}"`. `Muestra.clean()`: si `origen` y `cliente` están cargados y `origen.cliente_id != cliente_id` → `ValidationError({"origen": "El origen no pertenece al cliente seleccionado."})`; si `fecha_muestreo > fecha_ingreso` → `ValidationError({"fecha_muestreo": "La fecha de muestreo no puede ser posterior a la fecha de ingreso."})`.
- [X] T005 Generar `muestras/migrations/0001_initial.py` con `docker compose exec web python manage.py makemigrations muestras` y aplicarla con `migrate`; verificar `makemigrations --check --dry-run` sin cambios pendientes (depende de T003, T004).
- [X] T006 [P] Crear `muestras/admin.py` registrando `Origen` (`list_display=("nombre", "cliente", "fecha_alta")`, `search_fields=("nombre", "cliente__razon_social", "cliente__nombre")`, `readonly_fields=("fecha_alta",)`) y `Muestra` (`list_display=("numero_pi", "nombre", "cliente", "origen", "fecha_ingreso", "tipo_vertido", "estado", "registrada_por", "fecha_registro")`, `list_filter=("tipo_vertido", "estado")`, `search_fields=("numero_pi", "nombre", "cliente__razon_social", "cliente__nombre", "origen__nombre")`, `readonly_fields=("numero_pi", "estado", "registrada_por", "fecha_registro")`, `has_add_permission`, `has_change_permission` y `has_delete_permission` → `False`, para que el admin solo muestre las muestras: el alta es por la pantalla de la US 4.1, y la edición y la desactivación quedan fuera de alcance (FR-020)) (depende de T004).
- [X] T007 [P] Crear `muestras/tests/conftest.py` con fixtures (mismo estilo que `clientes/tests/conftest.py`):
  - `empleado` y `cliente_autenticado` (usuario activo `empleado@lab.com` con `force_login`).
  - `cliente_a`: `Cliente(razon_social="Aguas del Sur S.A.", tipo_documento="CUIT", numero_documento="20123456786", email="contacto@aguassur.com")`; `cliente_b`: `Cliente(nombre="Juan Pérez", tipo_documento="DNI", numero_documento="30123456", email="juan@ejemplo.com")`; `cliente_inactivo`: `Cliente(razon_social="Cooperativa Río Claro", tipo_documento="CUIT", numero_documento="30500010911", email="coop@ejemplo.com", activo=False)`.
  - `origen_a`: `Origen(cliente=cliente_a, nombre="Pozo N°2")`; `origen_b`: `Origen(cliente=cliente_b, nombre="Tanque elevado")`.
  - `hoy`: `timezone.localdate()`.
  - `datos_muestra_validos(cliente_a, origen_a, hoy)`: dict de POST con `cliente=cliente_a.pk`, `origen=origen_a.pk`, `origen_nuevo=""`, `fecha_muestreo=hoy.isoformat()`, `fecha_ingreso=hoy.isoformat()`, `sitio_extraccion="Canilla de salida del tanque"`, `tipo_vertido="agua"`, `nombre=""`, `responsable_muestreo=""`.
  - `crear_muestra`: factoría `(numero_pi, **extra)` que crea una `Muestra` válida de `cliente_a`/`origen_a` registrada por `empleado` (para preparar "último N° PI").
- [X] T008 [P] Crear `muestras/tests/test_modelos.py` (con `pytestmark = pytest.mark.django_db`):
  - `test_constraint_origen_unico_por_cliente` (FR-006): crear `"Pozo N°2"` y luego `"pozo n°2"` para el mismo cliente levanta `IntegrityError`; para otro cliente se permite.
  - `test_constraint_fechas_muestra` (FR-009): crear una `Muestra` con `fecha_muestreo > fecha_ingreso` levanta `IntegrityError`; `full_clean()` informa el error en `fecha_muestreo`.
  - `test_constraint_numero_pi_minimo_y_unico` (FR-012): `numero_pi=200000` levanta `IntegrityError`; dos muestras con el mismo `numero_pi` también.
  - `test_muestra_clean_rechaza_origen_de_otro_cliente` (FR-004): `full_clean()` con `origen_b` y `cliente_a` informa `"El origen no pertenece al cliente seleccionado."`.
  - `test_valores_por_defecto_muestra`: sin indicar `nombre`, `tipo_vertido` ni `estado` quedan `"Muestra 1"`, `"agua"` e `"ingresada"`.
  (depende de T004, T007).

**Checkpoint**: `pytest muestras/tests/test_modelos.py` en verde; las tablas y el admin existen.

---

## Phase 3: User Story 1 - Registrar el ingreso de una muestra con un origen ya conocido (Priority: P1) 🎯 MVP

**Goal**: un empleado elige un cliente activo (lista filtrable con su ficha), uno de sus orígenes,
completa fechas, sitio y tipo de vertido, revisa el resumen y confirma; la muestra queda registrada
con N° PI = máximo + 1 (200001 la primera), estado "Ingresada", usuario y fecha de registro, y
vuelve al formulario vacío mostrando el N° PI.

**Independent Test**: con `cliente_a` y `origen_a`, `docker compose exec web pytest
muestras/tests/test_servicio.py muestras/tests/test_registro.py -k "not origen_nuevo"` en verde +
pasos 1–3 y 7–9 de `quickstart.md`.

### Tests for User Story 1 ⚠️ (escribir primero, deben fallar)

- [ ] T009 [P] [US1] Crear `muestras/tests/test_servicio.py` (`pytestmark = pytest.mark.django_db`) con tests de `muestras.servicios`:
  - `test_primera_muestra_recibe_pi_200001` (US1 Esc. 6): sin muestras, `registrar_muestra(datos, empleado)` devuelve una muestra con `numero_pi == 200001`.
  - `test_pi_es_maximo_mas_uno` (FR-012): con `crear_muestra(200001)` y `crear_muestra(200007)`, la siguiente recibe `200008`.
  - `test_registrar_guarda_estado_usuario_y_fecha` (FR-014, FR-015): `estado == "ingresada"`, `registrada_por == empleado` y `fecha_registro` no nulo y cercano a `timezone.now()`.
  - `test_registrar_rechaza_cliente_inactivo_u_origen_ajeno` (Edge case): con el cliente desactivado o un `origen` de otro cliente, `registrar_muestra` levanta `MuestraNoDisponible` y no crea nada.
  - `test_error_al_guardar_no_consume_pi` (FR-018, SC-005): con `monkeypatch` sobre `Muestra.objects.create` levantando `DatabaseError`, no queda `Muestra` creada y, al reintentar sin el parche, el N° PI asignado es el mismo que hubiera correspondido.
  - `test_registros_concurrentes_no_repiten_pi` (FR-013): marcado `@pytest.mark.django_db(transaction=True)`; 5 `threading.Thread` esperan en una `threading.Barrier(5)` compartida y luego llaman a `registrar_muestra(datos, empleado)` (al hilo se le pasan solo pks y dicts, sin objetos del ORM); cada hilo guarda el `numero_pi` en una lista y cierra su conexión con `connection.close()` en un `finally`; tras los `join`, los 5 números son distintos y coinciden con `range(200001, 200006)`.
- [ ] T010 [P] [US1] Crear `muestras/tests/test_registro.py` (`pytestmark = pytest.mark.django_db`) con los tests de vistas de la US1:
  - `test_vistas_registro_muestra_requieren_sesion` (FR-001): GET y POST sin sesión a `muestras:registrar` y `muestras:registrar_confirmar` responden 302 hacia `settings.LOGIN_URL`.
  - `test_formulario_inicial_propone_hoy_y_agua` (US1 Esc. 1, FR-008, FR-010): GET a `muestras:registrar` responde 200; los inputs `fecha_muestreo` y `fecha_ingreso` tienen `value="<hoy ISO>"`, la opción `agua` de `tipo_vertido` está `selected` y `nombre`/`responsable_muestreo` vacíos.
  - `test_formulario_lista_solo_clientes_activos_con_sus_datos` (US1 Esc. 2, FR-002, FR-003): el `<select name="cliente">` incluye `cliente_a` y `cliente_b` y no `cliente_inactivo`; el `json_script` `clientes-muestra` (leído con `json.loads` del contenido del `<script id="clientes-muestra">`) trae por cada cliente activo `razon_social_o_nombre`, `tipo_documento`, `numero_documento`, `email` y `origenes`.
  - `test_formulario_ofrece_solo_origenes_del_cliente` (US1 Esc. 3, FR-004): en el `json_script`, `cliente_a` tiene solo `origen_a` y `cliente_b` solo `origen_b`; tras un POST inválido con `cliente=cliente_a.pk`, el `<select name="origen">` renderizado contiene `origen_a` y no `origen_b`.
  - `test_formulario_con_cliente_elegido_muestra_ficha_y_origenes` (US1 Esc. 2–3, FR-003): POST inválido (sin `sitio_extraccion`) con `cliente=cliente_a.pk` → el HTML dentro de `id="ficha-cliente"` contiene `"Aguas del Sur S.A."`, `"CUIT"`, `"20123456786"` y `"contacto@aguassur.com"`, y el `<select name="origen">` tiene `origen_a` y no `origen_b`; lo mismo con GET `?volver=1` y el borrador en sesión.
  - `test_post_valido_guarda_borrador_y_muestra_resumen` (US1 Esc. 4, FR-017): POST con `datos_muestra_validos` → 302 a `muestras:registrar_confirmar`; `session["muestra_pendiente"]` tiene los datos normalizados (`nombre == "Muestra 1"`); GET de la confirmación muestra `"Revisá los datos de la muestra antes de confirmar el registro."`, la razón social, el CUIT, el correo, `"Pozo N°2"`, ambas fechas, el sitio, `"Agua"`, `"Muestra 1"` y `"El N° PI se asigna al confirmar."`; no hay ninguna `Muestra` creada.
  - `test_confirmar_registra_muestra_con_pi_siguiente_y_datos_automaticos` (US1 Esc. 5, FR-012, FR-014, FR-015, FR-019, Q5): con `crear_muestra(200001)`, confirmar → 302 a `muestras:registrar`; existe la muestra `200002` con `cliente_a`, `origen_a`, estado `"ingresada"`, `registrada_por == empleado`; mensaje `"Muestra registrada con N° PI 200002."`; el borrador ya no está en sesión y el GET siguiente muestra el formulario vacío.
  - `test_volver_y_editar_conserva_borrador` (US1 Esc. 7): con borrador, GET `/muestras/registrar/?volver=1` precarga los valores de la sesión; GET sin `volver` muestra el formulario vacío y descarta el borrador.
  - `test_cancelar_no_registra_ni_consume_pi` (US1 Esc. 7, SC-005): con borrador, POST `accion=cancelar` → 302 a `muestras:registrar` con `"Registro de muestra cancelado."`, sin muestras creadas y sin borrador; la siguiente muestra confirmada recibe `200001`.
  - `test_confirmacion_repetida_registra_una_sola_muestra` (Edge case): dos POST `accion=confirmar` seguidos → una sola `Muestra`; el segundo responde 302 a `muestras:registrar` con el mensaje informativo `"Muestra registrada con N° PI 200001."`.
  - `test_cliente_desactivado_antes_de_confirmar_no_registra` (Edge case): con borrador, desactivar `cliente_a` y confirmar → 302 a `/muestras/registrar/?volver=1` con `"El cliente no está disponible."`, sin muestras, borrador conservado.
  - `test_error_de_base_al_confirmar_informa_sin_registrar` (Edge case): `monkeypatch` de `muestras.views.registrar_muestra` levantando `DatabaseError` → 200 en la confirmación con `"No se pudo registrar la muestra. Intentá nuevamente."`, borrador conservado.
  - `test_navbar_tiene_enlace_registrar_muestra` (R8): GET a `inicio` contiene un enlace a `reverse("muestras:registrar")` con el texto `"Registrar muestra"`.
- [ ] T011 [P] [US1] Crear `muestras/tests/js/registro_muestra.test.cjs` con `node:test` siguiendo el esquema de `usuarios/tests/js/sesion.test.cjs` (carga el script con `vm.runInNewContext`), probando la función pura `coincide(texto, cliente)` que expone el script: `"aguas del sur"` y `"AGUAS"` coinciden con `"Aguas del Sur S.A."`; `"perez"` coincide con `"Juan Pérez"`; `"20-12345678"` y `"2012345"` coinciden con el CUIT `20123456786`; `"xyz"` no coincide; texto vacío coincide con todos.

### Implementation for User Story 1

- [ ] T012 [US1] Crear `muestras/servicios.py` (depende de T004):
  - `class MuestraNoDisponible(Exception)` con atributo `mensaje` (`"El cliente no está disponible."` o `"El origen no pertenece al cliente seleccionado."`).
  - `CLAVE_LOCK_NUMERO_PI`: entero fijo (p. ej. `4_100_001`, documentado como "US 4.1 – N° PI").
  - `siguiente_numero_pi()`: `(Muestra.objects.aggregate(m=Max("numero_pi"))["m"] or NUMERO_PI_INICIAL - 1) + 1`.
  - `registrar_muestra(datos, usuario)`: dentro de `transaction.atomic()`: ejecutar `SELECT pg_advisory_xact_lock(%s)` con `CLAVE_LOCK_NUMERO_PI` vía `connection.cursor()`; obtener el cliente con `Cliente.objects.filter(pk=datos["cliente"], activo=True).first()` (si no hay → `MuestraNoDisponible`); si `datos["origen"]`, obtener `Origen.objects.filter(pk=datos["origen"], cliente=cliente).first()` (si no hay → `MuestraNoDisponible`); dejar un punto de extensión para `origen_nuevo` (se completa en T024); crear la `Muestra` con `numero_pi=siguiente_numero_pi()`, los campos del borrador (fechas con `date.fromisoformat`) y `registrada_por=usuario`; devolverla.
- [ ] T013 [US1] Crear `muestras/forms.py` con `RegistroMuestraForm(forms.Form)` según `plan.md` ("Formulario") y `contracts/registro-muestra-ui.md` (depende de T004):
  - `CAMPOS_MUESTRA = ("cliente", "origen", "origen_nuevo", "fecha_muestreo", "fecha_ingreso", "sitio_extraccion", "tipo_vertido", "nombre", "responsable_muestreo")`.
  - `cliente = ModelChoiceField(queryset=Cliente.objects.filter(activo=True), label="Cliente", empty_label="Elegí un cliente")` con `label_from_instance` → `f"{c.nombre_completo} · {c.tipo_documento} {c.numero_documento}"`.
  - `origen = ModelChoiceField(queryset=Origen.objects.none(), required=False, label="Origen", empty_label="Elegí un origen")`; en `__init__` limitar el queryset a `Origen.objects.filter(cliente_id=<cliente de data o initial>)` si el valor es un entero válido.
  - Propiedad `cliente_elegido`: el `Cliente` activo cuyo pk viene en `data` o `initial` (el mismo valor que limita el queryset de `origen`), o `None`.
  - `origen_nuevo = CharField(label="Origen nuevo", max_length=150, required=False, strip=True)`.
  - `fecha_muestreo` y `fecha_ingreso = DateField(widget=DateInput(attrs={"type": "date"}, format="%Y-%m-%d"), initial=timezone.localdate)` con etiquetas "Fecha de muestreo" y "Fecha de ingreso".
  - `sitio_extraccion = CharField(label="Sitio de extracción", max_length=200, strip=True)`.
  - `tipo_vertido = ChoiceField(label="Tipo de vertido", choices=TipoVertido.choices, initial=TipoVertido.AGUA)`.
  - `nombre = CharField(label="Nombre de la muestra", max_length=100, required=False, strip=True, help_text="Si lo dejás vacío se usa «Muestra 1».")`; `clean_nombre` → `NOMBRE_MUESTRA_POR_DEFECTO` si queda vacío.
  - `responsable_muestreo = CharField(label="Responsable del muestreo", max_length=150, required=False, strip=True)`.
  - `clean()` de esta tarea: si no hay `origen` → error en `origen` `"Elegí un origen del cliente o ingresá uno nuevo."` (la variante con `origen_nuevo` se completa en T023).
  - Clases `form-select`/`form-control` e `is-invalid` como en `RegistroClienteForm`.
  - `datos_para_sesion()`: `{"cliente": pk, "origen": pk o None, "origen_nuevo": str, "fecha_muestreo": iso, "fecha_ingreso": iso, ...}` (formato del borrador en `data-model.md`).
  - `datos_clientes()` (función de módulo): lista para el `json_script` con `id`, `nombre_completo`, `razon_social_o_nombre` (`razon_social or nombre`), `tipo_documento`, `numero_documento`, `email` y `origenes` (`[{"id", "nombre"}]`) de cada cliente activo, usando `prefetch_related("origenes")`.
- [ ] T014 [US1] Crear `muestras/views.py` con `registrar` y `registrar_confirmar` según la tabla de `contracts/registro-muestra-ui.md` (depende de T012, T013):
  - Constantes: `CLAVE_SESION = "muestra_pendiente"`, `CLAVE_ULTIMO_PI = "ultima_muestra_pi"`, `MENSAJE_EXITO = "Muestra registrada con N° PI {numero_pi}."`, `MENSAJE_CANCELADO = "Registro de muestra cancelado."`, `MENSAJE_ERROR_BD = "No se pudo registrar la muestra. Intentá nuevamente."`.
  - `registrar`: POST válido → guarda `form.datos_para_sesion()` en sesión, borra `CLAVE_ULTIMO_PI` y redirige a `muestras:registrar_confirmar`; GET con `volver=1` y borrador → form con `initial` del borrador; GET sin `volver` → `pop` del borrador y form vacío. Contexto: `form`, `cliente_elegido = form.cliente_elegido` y `clientes_datos = datos_clientes()`. Template `muestras/registro_form.html`.
  - `registrar_confirmar`: `cancelar` → `pop` del borrador, `messages.info`, redirige a `muestras:registrar`; `confirmar` sin borrador → si hay `CLAVE_ULTIMO_PI`, `messages.info(MENSAJE_EXITO)` y redirige; si no, redirige a `muestras:registrar`; `confirmar` con borrador → `registrar_muestra(datos, request.user)`; `MuestraNoDisponible` → `messages.warning(exc.mensaje)` y redirige a `/muestras/registrar/?volver=1`; `DatabaseError` → `messages.error(MENSAJE_ERROR_BD)` y renderiza la confirmación (200); éxito → borra borrador, guarda `CLAVE_ULTIMO_PI`, `messages.success(MENSAJE_EXITO.format(...))` y redirige a `muestras:registrar`; otra acción → redirige a la confirmación. GET sin borrador → redirige a `muestras:registrar`; con borrador → arma el resumen (objetos `Cliente`/`Origen`, etiqueta de `tipo_vertido`, fechas como `date`) y renderiza `muestras/registro_confirmar.html`.
- [ ] T015 [US1] Registrar en `muestras/urls.py` `path("registrar/", views.registrar, name="registrar")` y `path("registrar/confirmar/", views.registrar_confirmar, name="registrar_confirmar")` (depende de T014).
- [ ] T016 [P] [US1] Crear `muestras/templates/muestras/registro_form.html` extendiendo `base.html` (como `clientes/templates/clientes/registro_form.html`): título `"Registrar muestra"`; `<form method="post" novalidate>` con `{% csrf_token %}`; input de texto `buscar_cliente` (sin `name`, `id="buscar-cliente"`, etiqueta "Buscar cliente", placeholder "Nombre, razón social o documento") arriba del `<select>` de `cliente`; bloque `id="ficha-cliente"` con Razón social/Nombre, Documento y Correo electrónico, renderizado con los datos de `cliente_elegido` y visible si existe (si no, con `hidden`); `<select>` de `origen`, enlace "Dar de alta un origen nuevo" (`id="mostrar-origen-nuevo"`) y contenedor del campo `origen_nuevo` (`id="bloque-origen-nuevo"`, visible si tiene valor o error); resto de campos en el orden del contrato con `invalid-feedback` y `form-text`; botón primario **Continuar**; `{{ clientes_datos|json_script:"clientes-muestra" }}`; `<script src="{% static 'muestras/registro_muestra.js' %}" defer></script>` en `{% block content %}` (agregar `{% load static %}`).
- [ ] T017 [P] [US1] Crear `muestras/templates/muestras/registro_confirmar.html` como `clientes/templates/clientes/registro_confirmar.html`: título `"Confirmar registro de muestra"`, alerta `alert-info` `"Revisá los datos de la muestra antes de confirmar el registro."`, `<dl class="row">` con Cliente (nombre completo), Documento, Correo electrónico, Origen (con `"(nuevo)"` si corresponde), Fecha de muestreo, Fecha de ingreso (formato `d/m/Y`), Sitio de extracción, Tipo de vertido, Nombre de la muestra y Responsable del muestreo (`default:"—"`); texto `"El N° PI se asigna al confirmar."`; botones **Confirmar** (`accion=confirmar`, deshabilitado en `onsubmit`), **Volver y editar** (`{% url 'muestras:registrar' %}?volver=1`) y **Cancelar** (`accion=cancelar`).
- [ ] T018 [P] [US1] Crear `muestras/static/muestras/registro_muestra.js` (IIFE, sin librerías, comentarios en español como `usuarios/static/usuarios/sesion.js`): `normalizar(texto)` (minúsculas, `normalize("NFD")` sin diacríticos); `coincide(texto, cliente)` (vacío → `true`; coincide si el texto normalizado está en `nombre_completo` normalizado, o si los dígitos del texto sin `.`, `-` ni espacios están en `numero_documento`); al escribir en `#buscar-cliente`, ocultar (`hidden`) las `<option>` de `cliente` que no coinciden; al cambiar `cliente`, completar `#ficha-cliente` desde `clientes-muestra`, reemplazar las opciones de `origen` por las del cliente y vaciar `origen`; si el cliente no tiene orígenes, mostrar `#bloque-origen-nuevo`; exponer `coincide` para el test de Node (p. ej. `globalThis.registroMuestra = { coincide }`) sin romper si faltan elementos del DOM.
- [ ] T019 [P] [US1] Agregar el enlace `"Registrar muestra"` (`{% url 'muestras:registrar' %}`) en la barra de `templates/base.html` (después de "Registrar cliente") y el botón `"Registrar muestra"` en `templates/inicio.html` (depende de T015).
- [ ] T020 [US1] Ejecutar `docker compose exec web pytest muestras` y `node --test muestras/tests/js/` y dejar en verde los tests de T009–T011 (depende de T012–T019).

**Checkpoint**: la US1 funciona sola: se registran muestras con orígenes existentes y el N° PI correcto (MVP demostrable).

---

## Phase 4: User Story 2 - Dar de alta un origen nuevo desde el registro de muestra (Priority: P2)

**Goal**: desde el mismo formulario se ingresa un origen nuevo; al confirmar se crea asociado al
cliente junto con la muestra (o se reutiliza el existente con el mismo nombre), y queda disponible
solo para ese cliente.

**Independent Test**: `docker compose exec web pytest muestras -k origen_nuevo` en verde + pasos 4,
6, 9–11 y 13 de `quickstart.md`.

### Tests for User Story 2 ⚠️ (escribir primero, deben fallar)

- [ ] T021 [P] [US2] Agregar en `muestras/tests/test_servicio.py`:
  - `test_registrar_con_origen_nuevo_crea_origen` (US2 Esc. 1, FR-005): `datos` con `origen=None` y `origen_nuevo="Pozo N°3"` crea un `Origen` de `cliente_a` y la muestra queda asociada a él.
  - `test_origen_nuevo_repetido_reutiliza_existente` (US2 Esc. 4, FR-006): con `origen_a` (`"Pozo N°2"`), `origen_nuevo="  pozo n°2 "` no crea otro origen y la muestra usa `origen_a`.
  - `test_error_al_guardar_no_deja_origen_nuevo` (FR-018): con `Muestra.objects.create` parcheado para levantar `DatabaseError` y `origen_nuevo="Pozo N°3"`, no queda ningún `Origen` nuevo.
- [ ] T022 [P] [US2] Agregar en `muestras/tests/test_registro.py`:
  - `test_confirmar_con_origen_nuevo_crea_origen_del_cliente` (US2 Esc. 1): POST con `origen=""` y `origen_nuevo="Pozo N°3"` → resumen con `"Pozo N°3 (nuevo)"`; confirmar crea el origen y la muestra.
  - `test_origen_nuevo_disponible_solo_para_su_cliente` (US2 Esc. 2–3, SC-004): tras registrar con origen nuevo para `cliente_a`, el `json_script` del siguiente GET lo lista en `cliente_a` y no en `cliente_b`.
  - `test_cancelar_con_origen_nuevo_no_crea_origen` (US2 Esc. 5): con borrador con `origen_nuevo`, `accion=cancelar` no crea el `Origen`.
  - `test_origen_o_origen_nuevo_exactamente_uno` (R4): sin ninguno → error `"Elegí un origen del cliente o ingresá uno nuevo."` en `origen`; con ambos → error `"Elegí un origen existente o ingresá uno nuevo, no ambos."` en `origen_nuevo`; ambos casos 200 sin borrador.

### Implementation for User Story 2

- [ ] T023 [US2] Completar `RegistroMuestraForm.clean()` en `muestras/forms.py`: ni `origen` ni `origen_nuevo` → error en `origen` `"Elegí un origen del cliente o ingresá uno nuevo."`; ambos → error en `origen_nuevo` `"Elegí un origen existente o ingresá uno nuevo, no ambos."`; `datos_para_sesion()` guarda `origen=None` cuando se usa `origen_nuevo` (depende de T013).
- [ ] T024 [US2] Completar `registrar_muestra` en `muestras/servicios.py`: si `datos["origen_nuevo"]`, buscar `Origen.objects.filter(cliente=cliente, nombre__iexact=nombre).first()` y, si no existe, `Origen.objects.create(cliente=cliente, nombre=nombre)`, todo dentro de la misma transacción y después del advisory lock (depende de T012).
- [ ] T025 [US2] En `muestras/views.py`, incluir en el resumen de `registrar_confirmar` el origen nuevo (nombre del borrador con la marca `es_nuevo=True`) y en `muestras/templates/muestras/registro_confirmar.html` mostrar `"(nuevo)"` junto al origen cuando corresponda (depende de T014, T017).
- [ ] T026 [US2] En `muestras/static/muestras/registro_muestra.js`: el enlace `#mostrar-origen-nuevo` muestra `#bloque-origen-nuevo` y vacía `origen`; escribir en `origen_nuevo` vacía `origen` y elegir un `origen` vacía `origen_nuevo` (depende de T018).
- [ ] T027 [US2] Ejecutar `docker compose exec web pytest muestras` y dejar en verde T021–T022 sin romper la US1 (depende de T023–T026).

**Checkpoint**: US1 y US2 funcionan; la primera muestra de un cliente nuevo se puede registrar.

---

## Phase 5: User Story 3 - Impedir el registro de muestras incompletas o inconsistentes (Priority: P3)

**Goal**: el formulario rechaza datos obligatorios faltantes, fechas inválidas, valores fuera de
opción y orígenes/clientes no válidos, indicando el campo y conservando lo ingresado; aplica los
valores por defecto de nombre y responsable.

**Independent Test**: `docker compose exec web pytest muestras/tests/test_registro.py -k
"obligatorios or fechas or vertido or otro_cliente or inactivo or espacios or nombre_vacio or
responsable"` en verde + pasos 5 y 12 de `quickstart.md`.

### Tests for User Story 3 ⚠️ (escribir primero, deben fallar)

- [ ] T028 [US3] Agregar en `muestras/tests/test_registro.py`:
  - `test_campos_obligatorios_faltantes_indican_cada_campo` (US3 Esc. 1, FR-007, FR-016, SC-003), parametrizado por `cliente`, `fecha_muestreo`, `fecha_ingreso`, `sitio_extraccion` y `tipo_vertido` vacíos: 200, `"Este campo es obligatorio."` junto al campo (`is-invalid`), los demás valores conservados en el HTML, sin borrador ni muestras.
  - `test_textos_solo_espacios_son_vacios` (Edge case): `sitio_extraccion="   "` → `"Este campo es obligatorio."`; `origen_nuevo="   "` sin `origen` → `"Elegí un origen del cliente o ingresá uno nuevo."`.
  - `test_nombre_vacio_se_registra_como_muestra_1` (US3 Esc. 2, Q1): `nombre=""` → la muestra confirmada tiene `nombre == "Muestra 1"`; con `nombre="Muestra cisterna"` se guarda ese valor.
  - `test_responsable_opcional_texto_libre` (US3 Esc. 3, Q4): vacío → `responsable_muestreo == ""`; `"Carlos Ruiz (externo)"` se guarda tal cual.
  - `test_fechas_invalidas_rechazadas` (US3 Esc. 4, FR-009), parametrizado: `fecha_muestreo` mañana → `"La fecha no puede ser posterior a hoy."` en `fecha_muestreo`; `fecha_ingreso` mañana → mismo mensaje en `fecha_ingreso`; muestreo `hoy` e ingreso `ayer` → `"La fecha de muestreo no puede ser posterior a la fecha de ingreso."` en `fecha_muestreo`; muestreo hace 30 días e ingreso ayer → válido (302).
  - `test_origen_de_otro_cliente_rechazado` (US3 Esc. 5): `cliente=cliente_a`, `origen=origen_b` → 200 con error en `origen`, sin borrador.
  - `test_cliente_inactivo_o_inexistente_rechazado` (US3 Esc. 5): `cliente=cliente_inactivo.pk` y `cliente=99999` → 200 con error en `cliente`.
  - `test_tipo_vertido_fuera_de_opciones_rechazado` (FR-010): `tipo_vertido="pluvial"` → 200 con error en `tipo_vertido`.

### Implementation for User Story 3

- [ ] T029 [US3] Completar `RegistroMuestraForm` en `muestras/forms.py`: `clean_fecha_muestreo` y `clean_fecha_ingreso` rechazan fechas `> timezone.localdate()` con `"La fecha no puede ser posterior a hoy."`; en `clean()`, si ambas fechas son válidas y `fecha_muestreo > fecha_ingreso` → `add_error("fecha_muestreo", "La fecha de muestreo no puede ser posterior a la fecha de ingreso.")`; verificar que los textos solo con espacios queden vacíos (`strip=True`) y que el queryset de `origen` limitado al cliente rechace el origen ajeno (depende de T023).
- [ ] T030 [US3] Revisar `muestras/templates/muestras/registro_form.html` para que todos los campos con error muestren `is-invalid` + `invalid-feedback` y que `#bloque-origen-nuevo` quede visible cuando `origen_nuevo` tiene valor o error (depende de T016).
- [ ] T031 [US3] Ejecutar `docker compose exec web pytest muestras` y dejar en verde T028 junto con US1 y US2 (depende de T029–T030).

**Checkpoint**: las tres historias funcionan y se prueban de forma independiente.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [ ] T032 [P] Ejecutar `docker compose exec web ruff check .`, `docker compose exec web ruff format --check .` y `docker compose exec web python manage.py makemigrations --check --dry-run`, y corregir lo que aparezca (Principios III y VI).
- [ ] T033 Ejecutar la suite completa `docker compose exec web pytest` y `node --test usuarios/tests/js/ muestras/tests/js/` y confirmar todo en verde.
- [ ] T034 Recorrer los pasos 1 a 15 de validación manual de `specs/007-registrar-muestra/quickstart.md` (incluye revisar en el admin estado, usuario y fecha de registro) y cronometrar un registro con origen existente, desde abrir el formulario hasta ver el N° PI: menos de 1 minuto (SC-001).
- [ ] T035 [P] Agregar en `CLAUDE.md` una sección breve "Registro de muestras (US 4.1)" con lo no obvio: el N° PI se calcula en `muestras/servicios.py` bajo `pg_advisory_xact_lock` (no usar secuencias ni `AutoField`, dejan huecos); el origen nuevo se crea en la misma transacción que la muestra; el filtro de clientes es `muestras/static/muestras/registro_muestra.js` y su test de Node no corre en CI. No tocar el pendiente del envío de informes por correo (pertenece a otra US de SCRUM-39, no a esta).

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: `T001` → `T002` → `T003`.
- **Foundational (Phase 2)**: depende de la fase 1. `T004` → `T005`; `T006`, `T007` en paralelo tras `T004`; `T008` tras `T007`. Bloquea todas las historias.
- **US1 (Phase 3)**: depende de la fase 2. Es el MVP.
- **US2 (Phase 4)**: depende de US1 (extiende `forms.py`, `servicios.py`, `views.py`, el template de confirmación y el script creados en US1).
- **US3 (Phase 5)**: depende de US1 y de `T023` (US2) porque completa el mismo `clean()`; sus tests (`T028`) pueden escribirse en paralelo con la fase 4.
- **Polish (Phase 6)**: depende de las tres historias.

### Dentro de cada historia

- Tests primero y fallando; luego modelos/servicio → formulario → vistas → urls → templates/script.
- `test_registro.py` y `test_servicio.py` se tocan en varias fases: dentro de una misma fase, las tareas que comparten archivo van en secuencia.

### Grafo

```text
T001 → T002 → T003 → T004 ─┬─→ T005
                           ├─→ T006
                           └─→ T007 → T008
                                       │
          ┌────────────────────────────┘
          ▼
US1: T009 ─┐
     T010 ─┼─→ T012 ─┐
     T011 ─┘   T013 ─┴─→ T014 → T015 ─┬─→ T019 ─┐
                         T016 ─────────┤         │
                         T017 ─────────┤         ├─→ T020
                         T018 ─────────┘─────────┘
US2: T021, T022 → T023, T024 → T025, T026 → T027
US3: T028 → T029 → T030 → T031
Polish: T032, T033, T034, T035
```

---

## Parallel Example: User Story 1

```bash
# Tests de US1 en paralelo (archivos distintos):
Task T009: "Tests del servicio en muestras/tests/test_servicio.py"
Task T010: "Tests de vistas en muestras/tests/test_registro.py"
Task T011: "Test del filtro en muestras/tests/js/registro_muestra.test.cjs"

# Interfaz de US1 en paralelo, después de T014:
Task T016: "Template muestras/templates/muestras/registro_form.html"
Task T017: "Template muestras/templates/muestras/registro_confirmar.html"
Task T018: "Script muestras/static/muestras/registro_muestra.js"
```

## Parallel Example: User Story 2

```bash
Task T021: "Tests de origen nuevo en muestras/tests/test_servicio.py"
Task T022: "Tests de origen nuevo en muestras/tests/test_registro.py"
```

---

## Implementation Strategy

### En dos tandas (según `docs/guias/guia-sdd-paso-a-paso.md`)

1. **Tanda 1 (Fases 1 y 2 — `T001` a `T008`)**: app `muestras` conectada, modelos con sus
   constraints, migración, admin y fixtures; `test_modelos.py` en verde. Frenar y revisar.
2. **Tanda 2 (Fases 3 a 6 — `T009` a `T035`)**: US1 completa (MVP: registrar con origen existente y
   N° PI), luego US2 (origen nuevo) y US3 (validaciones), cada una con sus tests escritos primero;
   cerrar con `ruff`, suite completa, pasos de prueba manual y nota en `CLAUDE.md`.

### MVP

Fases 1–3 (US1): ya permite registrar muestras de clientes con orígenes cargados (por el admin o
de muestras anteriores) con N° PI, estado, usuario y fecha. La US2 es necesaria para el primer
ingreso de un cliente sin orígenes desde la pantalla, por eso conviene entregar US1 + US2 juntas en
la demo.
