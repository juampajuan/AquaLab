# Implementation Plan: Envío del informe por correo

**Branch**: `029-enviar-informe` | **Date**: 2026-11-09 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/029-enviar-informe/spec.md` (SCRUM-79)

## Summary

El informe emitido (`informes:ver`) suma **Enviar por correo** para quien puede emitir informes. La
confirmación (`informes:enviar`, GET) muestra el número, el cliente, su correo actual y el último
envío; al confirmar (POST), `informes/envios.py:enviar_informe` bloquea la fila del informe, genera
el PDF con la misma función que la descarga, lo manda adjunto a `Cliente.email` y registra un
`EnvioInforme` (nuevo, inalterable) con quién, cuándo, a qué dirección y el resultado. Una clave
única por confirmación evita el doble envío; una falla de correo o de PDF queda como envío
«Falló», en el log `informes.envios` y en un mensaje al usuario. La pantalla del informe muestra el
historial de envíos.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: Django 5.2 LTS (`EmailMessage`, ORM con `select_for_update`, messages,
`permission_required`), WeasyPrint 70.0 (ya en uso por `informes/pdf.py`), Tailwind CSS 4 y
`templates/ui/`. Sin dependencias nuevas.

**Storage**: PostgreSQL 16. Tabla nueva `informes_envioinforme` (migración `informes.0005`); lee
`informes_informe` y `clientes_cliente`.

**Testing**: pytest + pytest-django con `mailoutbox` (correos capturados) y fixtures de
`informes/tests/conftest.py` (`bioquimico`, `emitir_de`, `tres_informes`, …); `generar_pdf` se
parchea para no depender de WeasyPrint en cada test y para comparar el adjunto (R5); un test real
del adjunto con WeasyPrint. Concurrencia del doble envío con `transaction=True` e hilos, como
`informes/tests/test_concurrencia_emision.py`. ruff.

**Target Platform**: Contenedor Linux (`web`) con Docker Compose; navegador de escritorio.

**Project Type**: Aplicación web Django monolítica con templates en el servidor (sin SPA).

**Performance Goals**: El envío termina en lo que tarde el servidor de correo, acotado por
`EMAIL_TIMEOUT` (10 s); la pantalla del informe suma una consulta para el historial.

**Constraints**: El informe emitido no cambia (FR-011, US 7.3); un envío por confirmación (FR-010);
la falla de correo nunca da una página de error (SC-003); sin enlaces que requieran sesión en el
correo (FR-004); CSS compilado al día (CI).

**Scale/Scope**: 1 modelo + migración, 1 servicio, 1 vista (GET/POST) + URL, 1 template nuevo + 2
plantillas de correo, cambio en `informes/ver.html`, logger nuevo en `LOGGING`, tests, sección en
`CLAUDE.md` y se borra el pendiente «Envío de informes (SCRUM-39)».

Decisiones en [research.md](./research.md) (R1–R8). No hay `NEEDS CLARIFICATION` pendientes.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Cumplimiento | Estado |
|---|---|---|
| **I. Spec primero (SDD)** | Spec de SCRUM-79 (commit `070016d`); la aprobación del equipo es requisito antes de `/speckit-implement`. PR: «SCRUM-79 – Envío del informe por correo». | ⚠️ aprobación pendiente |
| **II. Simplicidad y Django idiomático** | `EmailMessage` y el backend de correo de Django; reutiliza `generar_pdf`, el permiso existente y el patrón de confirmación; sin colas ni dependencias (R1). | ✅ |
| **III. Tests obligatorios** | Cada escenario y FR con test ([Mapa de tests](#mapa-de-tests)), incluida la concurrencia del doble envío. Sin cálculos. | ✅ |
| **IV. Integridad de datos** | El informe emitido no se modifica (solo se bloquea su fila); `EnvioInforme` es inalterable (`save`/`delete` rechazados, sin admin), FK `PROTECT`. | ✅ |
| **V. Seguridad** | Sesión obligatoria; permiso `informes.emitir_informes` en la vista (403) y revalidado en el servicio; POST con CSRF; el correo no lleva contraseñas ni enlaces; credenciales SMTP solo por `.env`. | ✅ |
| **VI. Idioma y consistencia** | `EnvioInforme`, `ResultadoEnvio`, `enviar_informe`, `destinatario`, `enviado_por`; textos en español; ruff. | ✅ |
| **Interfaz (UI)** | Acción que envía datos con **confirmación** previa; componentes `ui/encabezado`, `ui/dato`, `ui/estado`, `ui/estado_vacio`; mensajes con el framework de mensajes. | ✅ |

**Post-diseño (Phase 1)**: cumple todos los principios, sin excepciones. Riesgo aceptado documentado
en R2 (correo enviado y registro perdido ante una caída de la base en ese instante).

## Diseño

### Flujo

```text
GET  /informes/estudios/<pk>/informe/          informes:ver  (+ botón y «Envíos por correo»)
GET  /informes/estudios/<pk>/informe/enviar/   informes:enviar → enviar_confirmar.html (clave = uuid4)
POST /informes/estudios/<pk>/informe/enviar/   clave → envios.enviar_informe(pk, usuario, clave)
  transaction.atomic():
    Informe.select_for_update(estudio__pk=pk)        → 404 si no hay
    ¿EnvioInforme con esa clave? → ResultadoDelEnvio(envio, duplicado=True), sin enviar
    destinatario = informe.estudio.muestra.cliente.email
    try: pdf = generar_pdf(informe); correo(informe, destinatario, pdf).send()  → enviado
    except Exception: logger.exception(...)                                      → fallido
    EnvioInforme.objects.create(...)
  → redirect informes:ver + mensaje según el resultado
```

```python
# informes/envios.py (firmas)
def enviar_informe(estudio_pk, usuario, clave) -> ResultadoDelEnvio: ...
def mensaje_de_correo(informe, destinatario, pdf) -> EmailMessage: ...
def ultimo_envio_exitoso(informe) -> EnvioInforme | None: ...
```

Rutas, mensajes y correo en [contracts/enviar-informe-ui.md](./contracts/enviar-informe-ui.md);
modelo en [data-model.md](./data-model.md).

### Mapa de tests

| Escenario / requisito | Test | Archivo |
|---|---|---|
| US1 Esc. 1, FR-001 — botón solo con permiso | `test_ver_ofrece_enviar_con_permiso` (parametrizado) | `informes/tests/test_ver.py` |
| US1 Esc. 2, FR-002 — confirmación con número, cliente, correo; GET no envía | `test_confirmacion_muestra_datos_y_no_envia` | `informes/tests/test_envios.py` |
| US1 Esc. 3, FR-003, SC-004 — un correo al `Cliente.email`, adjunto = `generar_pdf(informe)`, aviso de éxito | `test_envia_con_pdf_adjunto` | `informes/tests/test_envios.py` |
| SC-004 — adjunto real es un PDF (WeasyPrint) | `test_adjunto_es_pdf_real` | `informes/tests/test_envios.py` |
| US1 Esc. 4 — cancelar vuelve sin enviar | `test_cancelar_no_envia` | `informes/tests/test_envios.py` |
| US1 Esc. 5, FR-004 — asunto y cuerpo en español, número, N° PI, estudio; sin enlaces ni contraseñas | `test_contenido_del_correo` | `informes/tests/test_envios.py` |
| US2 Esc. 1 — sin envíos | `test_historial_vacio` | `informes/tests/test_ver.py` |
| US2 Esc. 2–3, FR-005/006 — registro con usuario, fecha, destinatario, resultado; orden desc | `test_registra_envio`, `test_historial_ordenado` | `informes/tests/test_envios.py`, `informes/tests/test_ver.py` |
| US2 Esc. 4, FR-007 — reenvío; confirmación con último envío exitoso | `test_reenvio_muestra_ultimo_envio` | `informes/tests/test_envios.py` |
| FR-005 — `EnvioInforme` inalterable | `test_envio_no_se_modifica_ni_borra` | `informes/tests/test_modelos.py` |
| US3 Esc. 1, FR-008, SC-003 — falla de correo y de PDF: mensaje, «Falló», log, sin 500 | `test_falla_de_correo` , `test_falla_de_pdf` | `informes/tests/test_envios.py` |
| US3 Esc. 2, FR-009 — sin permiso: 403 en GET y POST, servicio rechaza, nada enviado ni registrado | `test_sin_permiso` (parametrizado), `test_servicio_revalida_permiso` | `informes/tests/test_envios.py` |
| SC-003 — error de base al registrar: mensaje, sin 500 | `test_error_de_base` | `informes/tests/test_envios.py` |
| Edge — informe sin firma: se envía igual | `test_informe_sin_firma` | `informes/tests/test_envios.py` |
| US3 Esc. 3 — estudio sin informe → 404 | `test_sin_informe_404` | `informes/tests/test_envios.py` |
| US3 Esc. 4, FR-010 — misma clave dos veces → un correo; clave inválida → sin envío | `test_misma_clave_no_reenvia`, `test_clave_invalida` | `informes/tests/test_envios.py` |
| FR-010 — dos POST simultáneos con la misma clave → un correo, un registro | `test_doble_envio_concurrente` | `informes/tests/test_concurrencia_envios.py` |
| FR-011 — el informe y el estado del estudio no cambian | `test_enviar_no_modifica_informe` | `informes/tests/test_envios.py` |
| Edge — correo del cliente cambiado después de emitir: va al actual | `test_usa_correo_actual_del_cliente` | `informes/tests/test_envios.py` |
| Edge — cliente inactivo: se puede enviar | `test_cliente_inactivo` | `informes/tests/test_envios.py` |
| Diseño — confirmación con componentes `templates/ui/` | `test_confirmacion_usa_componentes` | `informes/tests/test_envios.py` |

## Project Structure

### Documentation (this feature)

```text
specs/029-enviar-informe/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── enviar-informe-ui.md
├── checklists/
│   └── requirements.md
└── tasks.md              # /speckit-tasks
```

### Source Code (repository root)

```text
CLAUDE.md                                         # + «Envío del informe por correo (SCRUM-79)»; − pendiente SCRUM-39
config/settings.py                                # + logger "informes.envios" en LOGGING
informes/
├── models.py                                     # + ResultadoEnvio, EnvioInforme
├── migrations/0005_envioinforme.py               # nueva
├── envios.py                                     # nuevo: enviar_informe, mensaje_de_correo, ultimo_envio_exitoso
├── views.py                                      # + enviar; ver con envíos
├── urls.py                                       # + estudios/<pk>/informe/enviar/
├── templates/informes/
│   ├── ver.html                                  # + botón y «Envíos por correo»
│   ├── enviar_confirmar.html                     # nuevo
│   └── correos/
│       ├── informe_asunto.txt                    # nuevo
│       └── informe_cuerpo.txt                    # nuevo
└── tests/
    ├── test_envios.py                            # nuevo
    ├── test_concurrencia_envios.py               # nuevo
    ├── test_ver.py                               # + botón e historial
    └── test_modelos.py                           # + EnvioInforme inalterable
static/css/aqualab.css                            # recompilado si hay clases nuevas
```

**Structure Decision**: todo en la app `informes`: el envío es una acción sobre el informe emitido.
El servicio va en un módulo propio (`envios.py`), como `pdf.py` y `firmas.py`, para no mezclar el
correo con la emisión de `servicios.py`.

## Complexity Tracking

Sin violaciones a la constitution: no aplica.
