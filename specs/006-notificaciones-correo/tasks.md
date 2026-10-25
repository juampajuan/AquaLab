---

description: "Lista de tareas de la US 1.3 – Notificaciones por correo del alta de usuarios"
---

# Tasks: Notificaciones por correo del alta de usuarios

**Input**: `specs/006-notificaciones-correo/` (`plan.md`, `spec.md`, `research.md`, `data-model.md`,
`contracts/correos.md`, `contracts/admin-rechazo.md`, `quickstart.md`)

**Prerequisites**: `plan.md`, `spec.md`. El registro y la aprobación de cuentas de la US 1.1
(`usuarios.Usuario`, `RegistroForm`, `registro_confirmar`, `crear_usuario_pendiente`,
`UsuarioAdmin.aprobar_cuentas`), el login de la US 1.2, Docker y el CI ya están implementados y no
se recrean.

**Tests**: SÍ. La constitution (Principio III) exige al menos un test automatizado con
pytest-django por cada escenario de aceptación. Los tests siguen el "Mapa de tests" de `plan.md`,
van en `usuarios/tests/test_notificaciones.py` y se escriben **antes** de implementar cada historia
(deben fallar primero).

**Organization**: una fase por user story de la spec (US1 a US4). US1 y US2 tocan la misma vista,
así que se hacen en ese orden.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: se puede ejecutar en paralelo (archivos distintos, sin dependencias pendientes)
- **[Story]**: user story a la que pertenece la tarea (`[US1]` a `[US4]`)
- Rutas relativas a la raíz del repo (`usuarios/`, `config/`, `CLAUDE.md`)

## Convenciones para todas las tareas

- Textos de correos, mensajes y nombres en **español** (Principio VI). Asuntos y cuerpos copiados
  literalmente de `contracts/correos.md`; textos del admin, de `contracts/admin-rechazo.md`.
- Los avisos siempre se agendan con `transaction.on_commit(...)` desde el llamador (`research.md`
  R3). En los tests, envolver la acción con
  `with django_capture_on_commit_callbacks(execute=True):` y revisar `mailoutbox`.
- Ningún correo incluye `password`, su hash ni datos de otros usuarios (FR-012, FR-013).
- Comandos dentro de Docker: `docker compose exec web pytest usuarios`,
  `docker compose exec web ruff check .`, `docker compose exec web ruff format --check .`.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: confirmar que el entorno y la suite actual corren en verde en esta rama antes de tocar
código.

- [ ] T001 Verificar el entorno con `docker compose up -d`, `docker compose exec web python manage.py migrate` y `docker compose exec web pytest` (definidos en `docker-compose.yml`) para confirmar que la base y los tests actuales pasan sin errores.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: configuración de correo y logging, helper común de envío y fixtures de test que usan
las cuatro historias.

**⚠️ CRITICAL**: no empezar las fases 3 a 6 hasta terminar esta fase.

- [X] T002 Agregar la configuración de correo en `config/settings.py` según `research.md` R1 y la tabla "Configuración" de `contracts/correos.md`:
  - `EMAIL_BACKEND = os.environ.get("EMAIL_BACKEND", "django.core.mail.backends.console.EmailBackend")`.
  - `EMAIL_HOST` (por defecto `"localhost"`), `EMAIL_PORT` (`int`, por defecto `587`), `EMAIL_HOST_USER` y `EMAIL_HOST_PASSWORD` (por defecto `""`), `EMAIL_USE_TLS` (por defecto `True`, mismo parseo que `DEBUG`: `"1"`, `"true"` o `"yes"`), `EMAIL_TIMEOUT` (`int`, por defecto `10`).
  - `DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL", "AquaLab <no-responder@aqualab.local>")`.
  - `LOGGING` mínimo (`version: 1`, `disable_existing_loggers: False`) con un handler `console` (`logging.StreamHandler`) y el logger `"usuarios.notificaciones"` en nivel `INFO` hacia ese handler (`research.md` R6).
- [X] T003 [P] Documentar las variables de correo en `.env.example`: `EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend` y `DEFAULT_FROM_EMAIL=AquaLab <no-responder@aqualab.local>` activas, y un bloque comentado para SMTP con Gmail (`EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend`, `EMAIL_HOST=smtp.gmail.com`, `EMAIL_PORT=587`, `EMAIL_USE_TLS=True`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` con una contraseña de aplicación) tal como en `quickstart.md` paso 5, aclarando que las credenciales nunca se suben al repo.
- [X] T004 Crear `usuarios/notificaciones.py` con la base común (`research.md` R5 y R6, `contracts/correos.md` "Reglas comunes"):
  - `logger = logging.getLogger("usuarios.notificaciones")`.
  - `_enviar(tipo, destinatario, plantilla, contexto)`: arma el asunto con `render_to_string(f"usuarios/correos/{plantilla}_asunto.txt", contexto)` (sin saltos de línea, `strip()`) y el cuerpo con `render_to_string(f"usuarios/correos/{plantilla}_cuerpo.txt", contexto)`, y llama a `send_mail(asunto, cuerpo, settings.DEFAULT_FROM_EMAIL, [destinatario], fail_silently=False)` dentro de `try/except Exception`; ante una falla, `logger.exception("No se pudo enviar el aviso %s a %s", tipo, destinatario)` y retorna sin relanzar.
  - Cada mensaje va a un solo destinatario (FR-013).
- [X] T005 [P] Agregar en `usuarios/tests/conftest.py` las fixtures:
  - `otro_administrador`: superusuario activo `otra.admin@lab.com` (`first_name="Otra"`, `last_name="Admin"`).
  - `administrador_inactivo`: superusuario con `is_active=False` (`admin.inactivo@lab.com`).
  - `confirmar_registro(en_revision)`: función que hace `en_revision.post(reverse("usuarios:registro_confirmar"), {"accion": "confirmar"}, follow=True)` y devuelve la respuesta.

**Checkpoint**: `pytest usuarios` sigue en verde y `python manage.py check` no reporta errores.

---

## Phase 3: User Story 1 - Aviso a los administradores de una solicitud nueva (Priority: P1) 🎯 MVP

**Goal**: al confirmarse un registro, cada superusuario activo recibe un aviso con los datos del
solicitante y el enlace a su ficha en el admin.

**Independent Test**: con dos administradores activos y uno inactivo, confirmar un registro y
verificar que llegan exactamente dos avisos, uno por administrador activo, con nombre, apellido,
correo y enlace (`quickstart.md` paso 1).

### Tests for User Story 1 ⚠️

> **NOTE: escribir estos tests PRIMERO y verificar que FALLAN antes de implementar**

- [X] T006 [P] [US1] En `usuarios/tests/test_notificaciones.py`, escribir los tests de la US1 del "Mapa de tests" de `plan.md`:
  - `test_confirmar_registro_avisa_a_cada_administrador_activo`: con `administrador` y `otro_administrador`, confirmar el registro de `datos_registro`; hay un mensaje con asunto `"AquaLab: nueva solicitud de cuenta"` por cada administrador, cada uno con `to == [su correo]`, el cuerpo contiene `"Ana"`, `"Pérez"`, `"ana@lab.com"` y la URL absoluta de `reverse("admin:usuarios_usuario_change", args=[nuevo.pk])`.
  - `test_administrador_inactivo_no_recibe_aviso`: con `administrador` y `administrador_inactivo`, solo `admin@lab.com` recibe el aviso.
  - `test_cancelar_registro_no_envia_correos`: `accion=cancelar` en la revisión → `mailoutbox` vacío.
  - `test_registro_sin_confirmar_no_envia_correos`: solo el POST de `usuarios:registro` (sin confirmar) → `mailoutbox` vacío.
  - `test_registro_con_correo_tomado_no_envia_correos`: crear un usuario con `ana@lab.com` entre el paso 1 y la confirmación → no hay correos y no se crea una segunda cuenta.
  - `test_sin_administradores_registro_queda_pendiente`: sin administradores, la cuenta queda con `is_active=False`, no hay aviso de solicitud nueva y `caplog` tiene el `WARNING` "Solicitud de alta sin administradores activos para avisar".

### Implementation for User Story 1

- [X] T007 [P] [US1] Crear `usuarios/templates/usuarios/correos/solicitud_nueva_asunto.txt` y `solicitud_nueva_cuerpo.txt` con el texto literal de `contracts/correos.md` ("Solicitud nueva"), usando `{{ administrador.first_name }}`, `{{ usuario.first_name }}`, `{{ usuario.last_name }}`, `{{ usuario.email }}` y `{{ enlace_ficha }}`. Usar `{% autoescape off %}` en ambos (texto plano).
- [X] T008 [US1] En `usuarios/notificaciones.py`, implementar `avisar_solicitud_nueva(request, usuario)`: armar `enlace_ficha = request.build_absolute_uri(reverse("admin:usuarios_usuario_change", args=[usuario.pk]))`; recorrer `Usuario.objects.filter(is_superuser=True, is_active=True)` y llamar a `_enviar("solicitud_nueva", administrador.email, "solicitud_nueva", {...})` por cada uno; si no hay ninguno, `logger.warning("Solicitud de alta sin administradores activos para avisar")`.
- [X] T009 [US1] En `usuarios/views.py`, dentro de `registro_confirmar`, en la rama `else` del `try` (cuenta creada), guardar el resultado de `crear_usuario_pendiente(datos)` en `usuario` y agendar `transaction.on_commit(lambda: notificaciones.avisar_solicitud_nueva(request, usuario))`. Sin cambios en las ramas de cancelar, confirmación repetida, `IntegrityError` ni `DatabaseError`.

**Checkpoint**: los tests de la US1 pasan y `test_registro.py` sigue en verde.

---

## Phase 4: User Story 2 - Confirmación de solicitud recibida al solicitante (Priority: P1)

**Goal**: al confirmarse un registro, el solicitante recibe un único correo que confirma que su
solicitud está pendiente de aprobación.

**Independent Test**: confirmar un registro y verificar un único correo a `ana@lab.com` con el
asunto de solicitud recibida; repetir la confirmación no manda otro (`quickstart.md` paso 1).

### Tests for User Story 2 ⚠️

- [X] T010 [P] [US2] En `usuarios/tests/test_notificaciones.py`, escribir:
  - `test_confirmar_registro_envia_solicitud_recibida`: después de confirmar, hay exactamente un mensaje con `to == ["ana@lab.com"]` y asunto `"AquaLab: recibimos tu solicitud de cuenta"`, y el cuerpo menciona `"pendiente de aprobación"`.
  - `test_confirmacion_repetida_no_reenvia_avisos`: confirmar dos veces con el mismo cliente; el total de mensajes no cambia después del segundo POST.

### Implementation for User Story 2

- [X] T011 [P] [US2] Crear `usuarios/templates/usuarios/correos/solicitud_recibida_asunto.txt` y `solicitud_recibida_cuerpo.txt` con el texto literal de `contracts/correos.md` ("Solicitud recibida"), usando `{{ usuario.first_name }}` y `{% autoescape off %}`.
- [X] T012 [US2] En `usuarios/notificaciones.py`, implementar `avisar_solicitud_recibida(request, usuario)` con `_enviar("solicitud_recibida", usuario.email, "solicitud_recibida", {"usuario": usuario})`.
- [X] T013 [US2] En `usuarios/views.py`, en la misma rama de `registro_confirmar` que T009, agendar también `transaction.on_commit(lambda: notificaciones.avisar_solicitud_recibida(request, usuario))`.

**Checkpoint**: los tests de US1 y US2 pasan; el registro completo manda exactamente los dos tipos
de aviso.

---

## Phase 5: User Story 3 - Aviso de aprobación al solicitante (Priority: P1)

**Goal**: cuando una cuenta pasa de pendiente a aprobada, desde la acción masiva o la ficha, el
solicitante recibe un único aviso con el enlace al login.

**Independent Test**: aprobar una cuenta pendiente con la acción masiva y otra desde su ficha, y
verificar un aviso por cada una; aprobar de nuevo no manda nada (`quickstart.md` paso 2).

### Tests for User Story 3 ⚠️

- [X] T014 [P] [US3] En `usuarios/tests/test_notificaciones.py`, escribir:
  - `test_accion_aprobar_avisa_a_cada_solicitante`: dos pendientes aprobadas juntas con `cliente_admin` → dos mensajes con asunto `"AquaLab: tu cuenta fue aprobada"`, cada uno con `to` igual a un solo solicitante, y el cuerpo contiene la URL absoluta de `reverse("usuarios:login")`.
  - `test_aprobar_desde_ficha_envia_aviso`: POST al `admin:usuarios_usuario_change` de `usuario_pendiente` con todos los campos de la ficha e `is_active="on"` → un aviso de aprobación a `pendiente@lab.com`.
  - `test_accion_aprobar_no_reenvia_a_cuentas_aprobadas`: selección con `usuario_pendiente` y `usuario_aprobado` → un solo aviso, a `pendiente@lab.com`.
  - `test_guardar_ficha_de_cuenta_aprobada_no_envia_aviso`: guardar la ficha de `usuario_aprobado` cambiando solo `first_name` → `mailoutbox` vacío.
  - `test_alta_desde_admin_no_envia_avisos`: crear un usuario desde `admin:usuarios_usuario_add` → `mailoutbox` vacío.

### Implementation for User Story 3

- [X] T015 [P] [US3] Crear `usuarios/templates/usuarios/correos/aprobacion_asunto.txt` y `aprobacion_cuerpo.txt` con el texto literal de `contracts/correos.md` ("Aprobación"), usando `{{ usuario.first_name }}`, `{{ enlace_login }}` y `{% autoescape off %}`.
- [X] T016 [US3] En `usuarios/notificaciones.py`, implementar `avisar_aprobacion(request, usuario)` con `enlace_login = request.build_absolute_uri(reverse("usuarios:login"))` y `_enviar("aprobacion", usuario.email, "aprobacion", {...})`.
- [X] T017 [US3] En `usuarios/admin.py`, reescribir `aprobar_cuentas` (`research.md` R3): dentro de `transaction.atomic()`, `pendientes = list(queryset.filter(is_active=False).select_for_update())`, `Usuario.objects.filter(pk__in=[u.pk for u in pendientes]).update(is_active=True)`, y por cada uno `transaction.on_commit(partial(notificaciones.avisar_aprobacion, request, usuario))`. Mantener el mensaje `f"Se aprobaron {len(pendientes)} cuenta(s)."` con `messages.SUCCESS`, para que `test_admin.py` siga pasando.
- [X] T018 [US3] En `usuarios/admin.py`, sobrescribir `save_model(self, request, obj, form, change)`: si `change`, calcular `estaba_pendiente = Usuario.objects.select_for_update().filter(pk=obj.pk, is_active=False).exists()` antes de `super().save_model(...)`; después, si `estaba_pendiente and obj.is_active`, agendar `transaction.on_commit(partial(notificaciones.avisar_aprobacion, request, obj))`. Si no es `change` (alta desde el admin), no avisar.

**Checkpoint**: los tests de US1 a US3 pasan y `test_admin.py` sigue en verde.

---

## Phase 6: User Story 4 - Rechazo de una solicitud con aviso al solicitante (Priority: P2)

**Goal**: el administrador rechaza solicitudes pendientes con una página de confirmación; las
cuentas se eliminan, el correo queda libre y cada solicitante recibe el aviso.

**Independent Test**: rechazar una solicitud pendiente, volver una vez desde la confirmación y
confirmar la segunda; verificar el aviso, que el login falla y que el mismo correo puede
registrarse de nuevo (`quickstart.md` paso 3).

### Tests for User Story 4 ⚠️

- [X] T019 [P] [US4] En `usuarios/tests/test_notificaciones.py`, escribir los tests de la US4 del "Mapa de tests" de `plan.md`, usando `URL_LISTADO = "admin:usuarios_usuario_changelist"`:
  - `test_rechazar_muestra_confirmacion_sin_cambios`: POST con `action=rechazar_solicitudes` y `usuario_pendiente` → `200`, el HTML contiene `"Rechazar solicitudes"`, `"Pedro"`, `"Gómez"`, `"pendiente@lab.com"` y `"Sí, rechazar"`; la cuenta sigue existiendo y `mailoutbox` está vacío.
  - `test_volver_desde_confirmacion_no_rechaza`: el enlace `"No, volver"` apunta al listado y, sin el segundo POST, la cuenta sigue pendiente.
  - `test_confirmar_rechazo_elimina_y_avisa`: segundo POST con `confirmar=si` → la cuenta ya no existe, un mensaje a `pendiente@lab.com` con asunto `"AquaLab: tu solicitud de cuenta no fue aprobada"` y el listado muestra `"Se rechazaron 1 solicitud(es)."`.
  - `test_cuenta_rechazada_no_puede_iniciar_sesion`: después del rechazo, el login con `pendiente@lab.com` y `PASSWORD_EXISTENTE` muestra `"Usuario o contraseña incorrectos"`.
  - `test_correo_rechazado_puede_registrarse_de_nuevo`: después del rechazo, registrar y confirmar `pendiente@lab.com` crea una cuenta pendiente nueva.
  - `test_rechazo_ignora_cuentas_aprobadas`: confirmar el rechazo de `usuario_pendiente` y `usuario_aprobado` → solo se elimina la pendiente y solo ella recibe correo.
  - `test_rechazar_sin_pendientes_avisa_y_no_confirma`: aplicar la acción solo sobre `usuario_aprobado` → `302` al listado con `"No hay solicitudes pendientes en la selección."`, sin cambios ni correos.

### Implementation for User Story 4

- [X] T020 [P] [US4] Crear `usuarios/templates/usuarios/correos/rechazo_asunto.txt` y `rechazo_cuerpo.txt` con el texto literal de `contracts/correos.md` ("Rechazo"), usando `{{ nombre }}` y `{% autoescape off %}`.
- [X] T021 [P] [US4] Crear `usuarios/templates/admin/usuarios/usuario/rechazar_confirmacion.html` según `contracts/admin-rechazo.md` "Paso 1": extender `"admin/base_site.html"`, título `"Rechazar solicitudes"`, el texto de confirmación literal, la lista de `pendientes` (nombre, apellido y correo), el aviso de cuentas aprobadas si `hay_aprobadas`, y un formulario POST con `{% csrf_token %}`, `action=rechazar_solicitudes`, un `_selected_action` oculto por pendiente, `confirmar=si`, el botón `"Sí, rechazar"` y el enlace `"No, volver"` a `{% url "admin:usuarios_usuario_changelist" %}`.
- [X] T022 [US4] En `usuarios/notificaciones.py`, implementar `avisar_rechazo(nombre, email)` con `_enviar("rechazo", email, "rechazo", {"nombre": nombre})`.
- [X] T023 [US4] En `usuarios/admin.py`, agregar la acción `rechazar_solicitudes` con `@admin.action(description="Rechazar solicitudes seleccionadas", permissions=["delete"])` y sumarla a `actions` (`research.md` R4, `contracts/admin-rechazo.md`):
  - Sin `confirmar=si` en `request.POST`: si `queryset.filter(is_active=False)` está vacío, `self.message_user(request, "No hay solicitudes pendientes en la selección.", messages.WARNING)` y retornar `None`; si no, retornar `TemplateResponse` con `rechazar_confirmacion.html` y el contexto `{**self.admin_site.each_context(request), "title": "Rechazar solicitudes", "pendientes": ..., "hay_aprobadas": queryset.filter(is_active=True).exists(), "opts": self.model._meta}`.
  - Con `confirmar=si`: dentro de `transaction.atomic()`, `pendientes = list(queryset.filter(is_active=False).select_for_update())`, guardar `[(u.first_name, u.email) for u in pendientes]`, `self.log_deletions(request, pendientes)`, `Usuario.objects.filter(pk__in=[...]).delete()`, agendar `transaction.on_commit(partial(notificaciones.avisar_rechazo, nombre, email))` por cada una, y `self.message_user(request, f"Se rechazaron {len(pendientes)} solicitud(es).", messages.SUCCESS)`.

**Checkpoint**: todos los tests de US1 a US4 pasan.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: fallas de envío, privacidad de los correos, documentación y verificación final.

- [X] T024 [P] En `usuarios/tests/test_notificaciones.py`, escribir los tests transversales:
  - `test_falla_de_envio_no_impide_registro_y_queda_en_log`: con `monkeypatch` sobre `usuarios.notificaciones.send_mail` lanzando `SMTPException`, confirmar un registro → la respuesta muestra `"Registro recibido"`, la cuenta existe pendiente y `caplog` tiene `"No se pudo enviar el aviso"` en nivel `ERROR` para `solicitud_nueva` y `solicitud_recibida`.
  - `test_falla_de_envio_no_impide_aprobacion`: mismo `monkeypatch`, aprobar con la acción masiva → la cuenta queda aprobada y la falla queda en `caplog`.
  - `test_correos_no_incluyen_contrasena_ni_datos_de_terceros`: recorrer el circuito completo (registro, aprobación y rechazo de otra solicitud) y verificar que ningún cuerpo contiene `password_registro`, `PASSWORD_EXISTENTE` ni el prefijo del hash (`"pbkdf2_"`), que todos los asuntos empiezan con `"AquaLab"`, que el remitente es `settings.DEFAULT_FROM_EMAIL` y que cada mensaje tiene un solo destinatario en `to` y nada en `cc` ni `bcc`.
- [X] T025 [P] Agregar en `CLAUDE.md` una sección "Avisos por correo (US 1.3)" con: los avisos se llaman explícitamente desde `registro_confirmar`, `UsuarioAdmin.aprobar_cuentas`, `UsuarioAdmin.save_model` y `UsuarioAdmin.rechazar_solicitudes` (no hay señales, porque `update()` no las dispara); siempre con `transaction.on_commit`; rechazar elimina la cuenta pendiente; y los tests usan `django_capture_on_commit_callbacks(execute=True)` y `mailoutbox`.
- [ ] T026 Correr `docker compose exec web ruff check .`, `docker compose exec web ruff format --check .`, `docker compose exec web python manage.py makemigrations --check --dry-run` (no debe haber migraciones nuevas) y `docker compose exec web pytest`, y corregir lo que falle.
- [ ] T027 Recorrer manualmente `quickstart.md` pasos 1 a 3 con el backend de consola y confirmar los correos y mensajes esperados en `docker compose logs -f web`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: sin dependencias.
- **Foundational (Phase 2)**: depende de Setup. **Bloquea** todas las historias.
- **US1 (Phase 3)**: depende de Foundational.
- **US2 (Phase 4)**: depende de US1, porque T013 edita la misma rama de `registro_confirmar` que T009.
- **US3 (Phase 5)** y **US4 (Phase 6)**: dependen solo de Foundational; pueden hacerse en paralelo
  con US1/US2. Entre sí tocan `usuarios/admin.py`, así que conviene hacerlas en orden (T017–T018
  antes de T023).
- **Polish (Phase 7)**: depende de las cuatro historias.

### Within Each User Story

- Tests primero (deben fallar), después templates de correo, después la función de
  `notificaciones.py` y por último el punto de disparo (vista o admin).

### Parallel Opportunities

- T003 y T005 en paralelo con T002/T004 (archivos distintos).
- En cada historia, el test ([P]) y los templates ([P]) se pueden escribir a la vez.
- T020 y T021 en paralelo (templates distintos).
- T024 y T025 en paralelo.

---

## Parallel Example: User Story 4

```text
# En paralelo (archivos distintos):
T019 tests de rechazo                     → usuarios/tests/test_notificaciones.py
T020 templates del correo de rechazo      → usuarios/templates/usuarios/correos/rechazo_*.txt
T021 template de confirmación del admin   → usuarios/templates/admin/usuarios/usuario/rechazar_confirmacion.html

# Después, en orden:
T022 avisar_rechazo                       → usuarios/notificaciones.py
T023 acción rechazar_solicitudes          → usuarios/admin.py
```

---

## Implementation Strategy

### MVP First (US1 + US2)

1. Phase 1 y Phase 2.
2. Phase 3 (US1): los administradores se enteran de cada solicitud nueva. Ya destraba el circuito
   de alta.
3. Phase 4 (US2): el solicitante recibe la constancia de su solicitud.
4. **STOP y validar** con `quickstart.md` paso 1.

### Incremental Delivery

1. MVP (US1 + US2) → demo del registro con avisos.
2. US3 → aviso de aprobación por las dos vías del admin.
3. US4 → rechazo con confirmación y aviso.
4. Polish → fallas de envío, privacidad, `CLAUDE.md` y verificación final.

Todo va en un único PR "US 1.3 – Notificaciones por correo del alta de usuarios" (1 US = 1 spec =
1 PR, Principio I).
