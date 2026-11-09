---

description: "Lista de tareas de SCRUM-79 – Envío del informe por correo"
---

# Tasks: Envío del informe por correo

**Input**: `specs/029-enviar-informe/` (`plan.md`, `spec.md`, `research.md`, `data-model.md`,
`contracts/enviar-informe-ui.md`, `quickstart.md`)

**Prerequisites**: `plan.md`, `spec.md` y `main` con la US 7.3 (`informes.Informe` inalterable,
`numero_mostrado`, `contenido`; `informes/pdf.py:generar_pdf`; vistas `informes:ver` y `informes:pdf`),
la US 1.3 (configuración de correo en `config/settings.py`: `EMAIL_*`, `DEFAULT_FROM_EMAIL`,
`LOGGING`) y el permiso `informes.emitir_informes` (migración `informes.0002`, grupo «Bioquímicos»).
Fixtures de `informes/tests/conftest.py` (que importa las de `estudios/tests/conftest.py`):
`empleado`, `bioquimico` (con firma y permiso), `cliente_bioquimico`, `cliente_comun` (empleado sin permiso, nuevo en
`informes/tests/conftest.py`: el usuario de `cliente_http` es el mismo `empleado` que `bioquimico`), `estudio_de`, `catalogo`, `firma_de`; helpers `estudios.tests.utiles.cargar` y `validar`;
`informes.servicios.emitir_informe`; fixture `mailoutbox` de pytest-django.

**Tests**: SÍ. La constitution (principio III) exige un test por escenario de aceptación. Los tests
siguen el «Mapa de tests» de `plan.md` y se escriben **antes** de la implementación de cada historia
(deben fallar primero).

**Organization**: tres user stories — US1 (P1, enviar el informe al cliente), US2 (P2, historial de
envíos) y US3 (P2, fallas y casos que impiden el envío).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: se puede ejecutar en paralelo (archivos distintos, sin dependencias pendientes)
- **[Story]**: user story a la que pertenece la tarea (`[US1]`, `[US2]`, `[US3]`)
- Rutas relativas a la raíz del repo

## Convenciones para todas las tareas

- Textos y mensajes en **español**, copiados **literalmente** de `contracts/enviar-informe-ui.md`.
- Diseño de SCRUM-67 con `templates/ui/`; preferir clases ya usadas en
  `estudios/templates/estudios/quitar_prueba_confirmar.html` e `informes/ver.html`; si se agrega
  alguna, recompilar el CSS (T022).
- `Informe` no se modifica nunca (FR-011, US 7.3): solo `select_for_update()` para bloquear su fila.
- En los tests, parchear `informes.envios.generar_pdf` (con `monkeypatch.setattr`) para no depender
  de WeasyPrint, salvo en `test_adjunto_es_pdf_real`.
- Commits en Conventional Commits en español: `feat(informes): SCRUM-79 – Envío del informe por correo`.
- Comandos dentro de Docker: `docker compose exec web pytest informes`,
  `docker compose exec web ruff check .`, `docker compose exec web ruff format --check .`.

---

## Phase 1: Setup (Shared Infrastructure)

- [ ] T001 *(Suite base en verde —1629 tests sobre `main` `dcb8b3c`, corrida el 2026-11-08— y `makemigrations --check` sin cambios el 2026-11-09. Implementación iniciada a pedido del autor antes de la aprobación formal; falta la aprobación del equipo.)* **Gate de la constitution (principio I)**: confirmar que el equipo aprobó `specs/029-enviar-informe/spec.md` y actualizar su `**Status**` a «Aprobada (fecha)». Confirmar que la rama `029-enviar-informe` sale de `main` (`dcb8b3c` o posterior) y ejecutar `docker compose exec web pytest` y `docker compose exec web python manage.py makemigrations --check --dry-run`: suite en verde y sin cambios pendientes.

---

## Phase 2: Foundational (Blocking Prerequisites)

**⚠️ CRITICAL**: ninguna historia empieza antes de terminar esta fase.

- [X] T002 En `informes/tests/test_modelos.py` agregar `test_envio_no_se_modifica_ni_borra` (FR-005; importar `EnvioInforme` dentro del test, así el archivo se sigue cargando antes de T003 y los tests de `Informe` no se caen): crear un `EnvioInforme` de un informe emitido (con `estudio_de`, `cargar`, `validar` y `emitir_informe`, como los tests vecinos) y verificar que `envio.save()` lanza `ValueError` con «Un envío de informe no se puede modificar.» y `envio.delete()` con «Un envío de informe no se puede borrar.»; que `EnvioInforme` no está registrado en el admin (`admin.site.is_registered`), y que `clave` es única (`IntegrityError` al repetirla dentro de `transaction.atomic()`).
- [X] T003 En `informes/models.py` agregar `class ResultadoEnvio(models.TextChoices)` con `ENVIADO = "enviado", "Enviado"` y `FALLIDO = "fallido", "Falló"`, y `class EnvioInforme(models.Model)` con docstring («Cada envío confirmado de un informe por correo (SCRUM-79), exitoso o fallido. Inalterable.»), según `data-model.md`: `informe = ForeignKey(Informe, on_delete=models.PROTECT, related_name="envios", editable=False)`, `enviado_por = ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="envios_de_informes", editable=False)`, `fecha = DateTimeField("fecha", auto_now_add=True)`, `destinatario = EmailField("enviado a", max_length=254)`, `resultado = CharField("resultado", max_length=10, choices=ResultadoEnvio.choices)`, `clave = UUIDField(unique=True, editable=False)`; `Meta`: `verbose_name="envío de informe"`, `verbose_name_plural="envíos de informes"`, `ordering=("-fecha", "-pk")`, `constraints=[CheckConstraint(condition=Q(resultado__in=ResultadoEnvio.values), name="envio_informe_resultado_valido")]`. `save()` lanza `ValueError("Un envío de informe no se puede modificar.")` si `self.pk` ya existe (`not self._state.adding`); `delete()` lanza `ValueError("Un envío de informe no se puede borrar.")`. No registrarlo en `informes/admin.py`.
- [X] T004 Generar la migración con `docker compose exec -u "$(id -u):$(id -g)" web python manage.py makemigrations informes --name envioinforme` (debe quedar `informes/migrations/0005_envioinforme.py`), revisarla, aplicar `migrate` y ejecutar `docker compose exec web pytest informes/tests/test_modelos.py`: en verde.
- [X] T005 [P] En `config/settings.py` agregar a `LOGGING["loggers"]` la entrada `"informes.envios": {"handlers": ["console"], "level": "INFO"}`.

**Checkpoint**: el modelo existe, es inalterable y la migración está aplicada.

---

## Phase 3: User Story 1 — Enviar el informe al cliente (Priority: P1) 🎯 MVP

**Goal**: desde el informe emitido, confirmar y enviar un correo al `Cliente.email` con el PDF adjunto.

**Independent Test**: con un informe emitido, abrir el informe → «Enviar por correo» → confirmar: un único correo a la dirección del cliente con el PDF adjunto y el aviso de éxito.

### Tests for User Story 1 ⚠️

- [X] T006 [US1] Crear `informes/tests/test_envios.py` con `pytestmark = pytest.mark.django_db`; un fixture `informe` (`estudio = estudio_de("PH")`, `cargar(estudio, empleado, PH="7.4")`, `validar(estudio, bioquimico, "PH")`, `emitir_informe(estudio.pk, bioquimico)`); un fixture `pdf_falso(monkeypatch)` que parchea `informes.envios.generar_pdf` con una función que devuelve `b"%PDF-falso"` y registra el informe recibido; un helper `enviar(cliente, informe, clave=None)` que hace POST a `reverse("informes:enviar", args=[informe.estudio.pk])` con `{"clave": clave or str(uuid.uuid4())}`. Tests:
  - `test_confirmacion_muestra_datos_y_no_envia` (US1 Esc. 2, FR-002): GET con `cliente_bioquimico` → 200; el HTML tiene «Se enviará el informe INF-… por correo a <email>, con el PDF adjunto.», el nombre del cliente, «Nunca se envió», un `<input type="hidden" name="clave"` con un UUID válido, el botón «Enviar informe» y el enlace «Cancelar» a `informes:ver`; `mailoutbox` vacío y `EnvioInforme.objects.count() == 0`. Dos GET dan claves distintas.
  - `test_envia_con_pdf_adjunto` (US1 Esc. 3, FR-003, SC-004): POST → 302 a `informes:ver`; `len(mailoutbox) == 1`; `mailoutbox[0].to == [informe.estudio.muestra.cliente.email]`; `from_email == settings.DEFAULT_FROM_EMAIL`; un adjunto `("INF-….pdf", b"%PDF-falso", "application/pdf")` y `generar_pdf` recibió ese mismo informe; mensaje de éxito «Se envió el informe INF-… a <email>.» al seguir la redirección.
  - `test_cancelar_no_envia` (US1 Esc. 4): el enlace «Cancelar» de la confirmación apunta a `informes:ver`; un GET a esa URL no envía ni registra.
  - `test_contenido_del_correo` (US1 Esc. 5, FR-004): asunto «Informe INF-… – AquaLab»; el cuerpo tiene el nombre del cliente, «INF-…», «N° PI <numero_pi>», «N° <estudio.pk>», el tipo de estudio y el nombre del laboratorio de `settings.AQUALAB_LABORATORIO`; no tiene `http://` ni `https://` ni «contraseña».
  - `test_enviar_no_modifica_informe` (FR-011): `contenido`, `numero` y `fecha_emision` del informe y el `estado` del estudio son los mismos antes y después del envío.
  - `test_usa_correo_actual_del_cliente` (Edge): cambiar `Cliente.email` con `Cliente.objects.filter(pk=...).update(email="nuevo@ejemplo.com")` después de emitir → el correo va a `nuevo@ejemplo.com` (y la confirmación lo muestra).
  - `test_cliente_inactivo` (Edge): con el cliente `activo=False` (por `update`), la confirmación responde 200 y el envío sale.
  - `test_adjunto_es_pdf_real` (SC-004): sin parchear `generar_pdf`, el adjunto empieza con `b"%PDF"` y su nombre es `f"{informe.numero_mostrado}.pdf"`.
  - `test_confirmacion_usa_componentes` (Diseño): la confirmación tiene `data-componente="resumen"`, `data-componente="acciones-confirmacion"` y el encabezado de `ui/encabezado.html` con «Enviar informe por correo».
  - `test_informe_sin_firma` (Edge): un informe sin firma registrada (quitar `"firma"` de `contenido` con `Informe.objects.filter(pk=...).update(contenido=...)`) se envía igual: un correo con el adjunto y registro «enviado».
- [X] T007 [US1] En `informes/tests/test_ver.py` agregar `test_ver_ofrece_enviar_con_permiso` parametrizado (US1 Esc. 1, FR-001): con `cliente_bioquimico` el HTML de `informes:ver` tiene «Enviar por correo» con enlace a `reverse("informes:enviar", args=[pk])`; con `cliente_comun` (sin permiso) no lo tiene.
- [X] T008 [US1] Ejecutar `docker compose exec web pytest informes/tests/test_envios.py informes/tests/test_ver.py`: los tests nuevos fallan (todavía no hay vista ni servicio).

### Implementation for User Story 1

- [X] T009 [US1] Crear `informes/templates/informes/correos/informe_asunto.txt` (una sola línea: `Informe {{ numero }} – AquaLab`) e `informes/templates/informes/correos/informe_cuerpo.txt` (texto plano) con el texto de `contracts/enviar-informe-ui.md → Correo`: saludo «Hola, {{ contenido.cliente.nombre_completo }}:», «Le enviamos el informe {{ numero }} del estudio N° {{ contenido.estudio.numero }} ({{ contenido.estudio.tipo }}) de la muestra N° PI {{ contenido.muestra.numero_pi }} ({{ contenido.muestra.nombre }}).», «El informe está adjunto en PDF.», «Saludos,» y `{{ contenido.laboratorio.nombre }}`. Sin enlaces. Agregar `{% autoescape off %}` (texto plano).
- [X] T010 [US1] Crear `informes/envios.py` con docstring (único envío de informes por correo, SCRUM-79; lo llama `informes:enviar`), `logger = logging.getLogger("informes.envios")`, `from .pdf import generar_pdf` (importado a nivel de módulo para que los tests lo parcheen como `informes.envios.generar_pdf`) y:
  - `class EnviarInformeError(Exception)`.
  - `@dataclass(frozen=True) class ResultadoDelEnvio`: `envio: EnvioInforme`, `duplicado: bool = False`.
  - `mensaje_de_correo(informe, destinatario, pdf)`: arma `EmailMessage(subject=" ".join(render_to_string("informes/correos/informe_asunto.txt", ctx).split()), body=render_to_string("informes/correos/informe_cuerpo.txt", ctx), from_email=settings.DEFAULT_FROM_EMAIL, to=[destinatario])` con `ctx = {"numero": informe.numero_mostrado, "contenido": informe.contenido}` y `attach(f"{informe.numero_mostrado}.pdf", pdf, "application/pdf")`.
  - `ultimo_envio_exitoso(informe)`: el `EnvioInforme` más reciente con `resultado=ENVIADO`, o `None`.
  - `enviar_informe(estudio_pk, usuario, clave)` (research R1–R2, R6): si `not usuario.has_perm("informes.emitir_informes")` → `PermissionDenied`; dentro de `transaction.atomic()`: `informe = Informe.objects.select_for_update().select_related("estudio__muestra__cliente").get(estudio__pk=estudio_pk)` (`Informe.DoesNotExist` → `Http404`); si `EnvioInforme.objects.filter(clave=clave).first()` existe → `ResultadoDelEnvio(envio, duplicado=True)` sin enviar; `destinatario = informe.estudio.muestra.cliente.email`; `try: mensaje_de_correo(informe, destinatario, generar_pdf(informe)).send(fail_silently=False); resultado = ENVIADO` / `except Exception: logger.exception("No se pudo enviar el informe %s a %s", informe.numero_mostrado, destinatario); resultado = FALLIDO`; `envio = EnvioInforme.objects.create(informe=informe, enviado_por=usuario, destinatario=destinatario, resultado=resultado, clave=clave)`; devolver `ResultadoDelEnvio(envio)`.
- [X] T011 [US1] En `informes/views.py` agregar la vista `enviar(request, pk)` con `@permission_required("informes.emitir_informes", raise_exception=True)` y `@require_http_methods(["GET", "POST"])`: `informe = get_object_or_404(Informe.objects.select_related("estudio__muestra__cliente"), estudio__pk=pk)`. GET: renderiza `informes/enviar_confirmar.html` con `informe`, `estudio`, `cliente = informe.estudio.muestra.cliente`, `ultimo = envios.ultimo_envio_exitoso(informe)` y `clave = uuid.uuid4()`. POST: leer `clave` con `uuid.UUID(request.POST.get("clave", ""))` (`ValueError` → `messages.error(request, "La confirmación no es válida. Volvé a intentarlo.")` y redirect a `informes:enviar`); llamar `envios.enviar_informe(pk, request.user, clave)` (por el módulo, para que los tests parcheen `informes.envios.*`); `DatabaseError` → `messages.error(request, "No se pudo registrar el envío. Intentá nuevamente.")`; según el resultado: duplicado → `messages.info(..., f"El informe {numero} ya se había enviado con esta confirmación.")`, enviado → `messages.success(..., f"Se envió el informe {numero} a {destinatario}.")`, fallido → `messages.error(..., f"No se pudo enviar el informe a {destinatario}. Intentá nuevamente.")`; siempre redirect a `informes:ver`. En `informes/urls.py` agregar `path("estudios/<int:pk>/informe/enviar/", views.enviar, name="enviar")`.
- [X] T012 [US1] Crear `informes/templates/informes/enviar_confirmar.html` siguiendo `estudios/templates/estudios/quitar_prueba_confirmar.html`: encabezado (`ui/encabezado.html` con `seccion="Informes"`, `anterior_texto="Informe "|add:informe.numero_mostrado`, `anterior_url` = `informes:ver`, `miga="Enviar por correo"`, `titulo="Enviar informe por correo"`); aviso `aviso aviso-advertencia` con ícono `mail` y «Se enviará el informe {{ informe.numero_mostrado }} por correo a {{ cliente.email }}, con el PDF adjunto.»; tarjeta con `<dl class="resumen" data-componente="resumen">` y `ui/dato.html` para Informe, Cliente (`cliente.nombre_completo`), Correo y Último envío (`{{ ultimo.fecha|date:"d/m/Y H:i" }} a {{ ultimo.destinatario }}` o «Nunca se envió»); `<div class="mt-6 flex flex-wrap items-center gap-3" data-componente="acciones-confirmacion">` con un `<form method="post" onsubmit="this.querySelector('button').disabled = true;">` (`csrf_token`, `<input type="hidden" name="clave" value="{{ clave }}">`, botón `btn btn-primario` con ícono `mail` y «Enviar informe») y el enlace «Cancelar» (`btn btn-secundario`) a `informes:ver`.
- [X] T013 [US1] En `informes/templates/informes/ver.html`, después de «Descargar PDF», agregar `{% if perms.informes.emitir_informes %}<a href="{% url 'informes:enviar' estudio.pk %}" class="btn btn-secundario">{% include "ui/icono.html" with nombre="mail" clase="size-4" %} Enviar por correo</a>{% endif %}`.
- [X] T014 [US1] Ejecutar `docker compose exec web pytest informes/tests/test_envios.py informes/tests/test_ver.py`: los tests de US1 en verde.

**Checkpoint**: US1 funciona sola (MVP).

---

## Phase 4: User Story 2 — Historial de envíos (Priority: P2)

**Goal**: el informe muestra cada envío (fecha, destinatario, usuario, resultado) y se puede reenviar.

**Independent Test**: enviar dos veces (una con éxito y otra con falla simulada) → el informe muestra las dos filas, la más reciente primero.

### Tests for User Story 2 ⚠️

- [X] T015 [US2] En `informes/tests/test_envios.py` agregar:
  - `test_registra_envio` (US2 Esc. 2, FR-005): tras el POST hay un `EnvioInforme` con `informe`, `enviado_por == bioquimico`, `destinatario` = correo del cliente, `resultado == "enviado"`, la `clave` enviada y `fecha` no nula.
  - `test_reenvio_muestra_ultimo_envio` (US2 Esc. 4, FR-007): tras un envío exitoso, la confirmación muestra «<d/m/Y H:i> a <email>» del último envío exitoso (y no uno fallido posterior, creado con `EnvioInforme.objects.create(..., resultado="fallido")`); un segundo POST con otra clave envía otro correo (`len(mailoutbox) == 2`) y deja dos registros.
- [X] T016 [US2] En `informes/tests/test_ver.py` agregar `test_historial_vacio` (US2 Esc. 1): `informes:ver` muestra «Este informe todavía no se envió por correo.» (con `cliente_comun` y con `cliente_bioquimico`); y `test_historial_ordenado` (US2 Esc. 3, FR-006): con tres `EnvioInforme` creados directamente (dos «enviado», uno «fallido», con `fecha` distintas fijadas por `EnvioInforme.objects.filter(pk=...).update(fecha=...)`), la sección «Envíos por correo» lista las tres filas en orden de fecha descendente, cada una con fecha `d/m/Y H:i`, destinatario, nombre del usuario y la etiqueta «Enviado» (`data-estado="success"`) o «Falló» (`data-estado="danger"`).

### Implementation for User Story 2

- [X] T017 [US2] En `informes/views.py`, en `ver`, agregar al contexto `envios = list(informe.envios.select_related("enviado_por"))` (orden del `Meta`). En `informes/templates/informes/ver.html`, después de los botones, agregar `<section class="tarjeta overflow-hidden" data-componente="envios">` con el título «Envíos por correo» (`px-4 py-4 text-sm font-semibold text-marino sm:px-5`) y, si hay envíos, una `<table class="tabla">` con columnas Fecha, Enviado a, Enviado por (`envio.enviado_por.get_full_name|default:envio.enviado_por.email`) y Resultado (`{% include "ui/estado.html" with estado=envio.get_resultado_display tipo=... %}` con `"success"` para `enviado` y `"danger"` para `fallido`); si no, `{% include "ui/estado_vacio.html" with icono="mail" mensaje="Este informe todavía no se envió por correo." %}`.
- [X] T018 [US2] Ejecutar `docker compose exec web pytest informes/tests/test_envios.py informes/tests/test_ver.py`: US1 y US2 en verde.

**Checkpoint**: US1 y US2 funcionan juntas.

---

## Phase 5: User Story 3 — Fallas y casos que impiden el envío (Priority: P2)

**Goal**: fallas de correo o PDF, permisos, informe inexistente y doble envío se manejan sin errores ni envíos de más.

**Independent Test**: simular una falla del servidor de correo → mensaje de error, envío «Falló», log y el informe intacto; sin permiso → sin botón y 403.

### Tests for User Story 3 ⚠️

- [X] T019 [US3] En `informes/tests/test_envios.py` agregar:
  - `test_falla_de_correo` (US3 Esc. 1, FR-008, SC-003): parchear `django.core.mail.EmailMessage.send` para que lance `SMTPException("caído")`; el POST da 302 a `informes:ver`, el mensaje «No se pudo enviar el informe a <email>. Intentá nuevamente.», un `EnvioInforme` con `resultado == "fallido"`, `mailoutbox` vacío y un registro `ERROR` en el logger `informes.envios` (`caplog`, con el número de informe).
  - `test_falla_de_pdf` (US3 Esc. 1): `informes.envios.generar_pdf` lanza `RuntimeError` → mismo mensaje, registro «fallido», ningún correo, log.
  - `test_sin_permiso` parametrizado por método (US3 Esc. 2, FR-009): con `cliente_comun` (sin `informes.emitir_informes`), GET y POST a `informes:enviar` dan 403, sin correos ni registros.
  - `test_servicio_revalida_permiso` (FR-009): `envios.enviar_informe(pk, empleado, uuid4())` lanza `PermissionDenied` sin enviar ni registrar.
  - `test_sin_informe_404` (US3 Esc. 3): un estudio sin informe (`estudio_de("PH")`) → GET y POST dan 404.
  - `test_misma_clave_no_reenvia` (US3 Esc. 4, FR-010): dos POST con la misma clave → un solo correo, un solo registro y el segundo muestra «El informe INF-… ya se había enviado con esta confirmación.».
  - `test_clave_invalida` (FR-010): POST sin `clave` o con `clave="x"` → redirect a `informes:enviar` con «La confirmación no es válida. Volvé a intentarlo.», sin correo ni registro.
  - `test_error_de_base` (SC-003): parchear `informes.envios.enviar_informe` para que lance `DatabaseError` → 302 a `informes:ver` con «No se pudo registrar el envío. Intentá nuevamente.», sin página de error.
- [X] T020 [P] [US3] Crear `informes/tests/test_concurrencia_envios.py` con `pytestmark = pytest.mark.django_db(transaction=True)` y `test_doble_envio_concurrente` (FR-010) siguiendo `informes/tests/test_concurrencia_emision.py` (`threading.Barrier(2)`, `ThreadPoolExecutor`, `close_old_connections()` y `connection.close()` en cada hilo): con `generar_pdf` parcheado, dos hilos llaman `enviar_informe(pk, bioquimico, misma_clave)` a la vez → `EnvioInforme.objects.filter(clave=clave).count() == 1`, `len(mailoutbox) == 1` y exactamente un resultado con `duplicado=True`. (Con `transaction=True` la base se vacía: el fixture `bioquimico` crea el grupo si falta, ver `CLAUDE.md`.)

### Implementation for User Story 3

- [X] T021 [US3] Verificar en `informes/envios.py` e `informes/views.py`, con los tests de T019–T020, que: (a) una excepción de `generar_pdf` se registra como `fallido` igual que una de `send` (el `try` cubre las dos llamadas); (b) la vista **no** atrapa `PermissionDenied` ni `Http404` (Django los convierte en 403 y 404); (c) `select_for_update()` del `Informe` va antes de buscar el `EnvioInforme` por `clave`; (d) la vista atrapa `DatabaseError` alrededor de `envios.enviar_informe` con el mensaje del contrato. Corregir lo que falte.
- [X] T022 [US3] Recompilar el CSS con `docker compose exec -u "$(id -u):$(id -g)" web tailwindcss -i static/src/aqualab.css -o static/css/aqualab.css --minify`; si `static/css/aqualab.css` cambia (clases nuevas en `enviar_confirmar.html` o `ver.html`), commitearlo.
- [X] T023 [US3] Ejecutar `docker compose exec web pytest informes`: todo en verde.

**Checkpoint**: las tres historias funcionan juntas.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T024 [P] En `CLAUDE.md`: borrar la línea del pendiente «**Envío de informes (SCRUM-39):** …» (y la sección «Pendientes entre features» queda sin ítems) y agregar la sección «## Envío del informe por correo (SCRUM-79)» con: `informes/envios.py:enviar_informe` es el único envío (lo llama `informes:enviar`); sincrónico, con el PDF de `generar_pdf` adjunto y destino `Cliente.email` vigente; `EnvioInforme` es inalterable (`save`/`delete` lanzan `ValueError`, sin admin; en los tests, cambiarlo con `filter(...).update(...)`); un envío por confirmación con la `clave` oculta, bajo `select_for_update` del `Informe`; una falla de correo o PDF se registra como «fallido» y va al logger `informes.envios`; en los tests, parchear `informes.envios.generar_pdf`; permiso `informes.emitir_informes`.
- [X] T025 Ejecutar `docker compose exec web pytest`, `docker compose exec web ruff check .`, `docker compose exec web ruff format --check .` y `docker compose exec web python manage.py makemigrations --check --dry-run`: todo en verde, sin migraciones pendientes además de `0005`.
- [X] T026 Prueba manual según `specs/029-enviar-informe/quickstart.md` (pasos 1–8, con `cargar_demo`). La acredita el autor.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: sin dependencias.
- **Foundational (Phase 2)**: depende de T001; bloquea todas las historias (modelo y migración).
- **US1 (Phase 3)**: depende de la fase 2. Crea el servicio, la vista y la confirmación que usan US2 y US3.
- **US2 (Phase 4)**: depende de US1 (los envíos se crean con el servicio de US1); solo agrega la sección del historial.
- **US3 (Phase 5)**: depende de US1 (servicio y vista); independiente de US2.
- **Polish (Phase 6)**: después de las historias.

### Within Each User Story

- Tests primero (deben fallar), después implementación, después ejecutar los tests.
- Modelo → servicio (`envios.py`) → vista y URL → templates.

### Parallel Opportunities

- T005 (`config/settings.py`) en paralelo con T002–T004 (archivos distintos).
- T006 (`test_envios.py`) y T007 (`test_ver.py`) tocan archivos distintos, pero son de la misma historia y conviene escribirlos juntos.
- T020 (`test_concurrencia_envios.py`) en paralelo con T019 (`test_envios.py`).
- T024 (`CLAUDE.md`) en paralelo con T025.

## Implementation Strategy

### MVP First (User Story 1)

1. Fase 1 (gate) y fase 2 (modelo inalterable y migración).
2. Fase 3: enviar con confirmación y PDF adjunto.
3. **Validar**: un correo al cliente con el PDF.

### Incremental Delivery

1. US1 → envío (MVP).
2. US2 → historial en el informe y reenvío.
3. US3 → fallas, permisos y doble envío.
4. Polish → `CLAUDE.md`, suite completa, prueba manual y PR «SCRUM-79 – Envío del informe por correo».
