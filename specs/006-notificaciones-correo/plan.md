# Implementation Plan: Notificaciones por correo del alta de usuarios

**Branch**: `006-notificaciones-correo` | **Date**: 2026-10-24 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/006-notificaciones-correo/spec.md` (US 1.3 / SCRUM-66)

## Summary

Cuatro avisos por correo en el circuito de alta de cuentas de la app `usuarios`: solicitud nueva
(a cada superusuario activo) y solicitud recibida (al solicitante) al confirmar el registro;
aprobación al pasar una cuenta de pendiente a aprobada desde el admin (acción masiva o ficha); y
rechazo, con una acción nueva del admin que pide confirmación y elimina la solicitud pendiente
para dejar libre el correo. Se usa el framework de correo de Django, configurado por variables de
entorno (consola por defecto, SMTP opcional). Los avisos se disparan con llamadas explícitas
desde la vista de registro y el `UsuarioAdmin`, se envían en `transaction.on_commit` y una falla de
envío solo queda en el log, sin afectar la operación.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: Django 5.2 LTS (`django.core.mail`, admin, auth, templates, logging).
Sin dependencias nuevas.

**Storage**: PostgreSQL 16 en Docker (`DATABASE_URL`). Sin modelos ni migraciones nuevas; se usa
`Usuario.is_active` como estado de la solicitud ([data-model.md](./data-model.md)).

**Testing**: pytest-django con el test client de Django, los fixtures `mailoutbox` y
`django_capture_on_commit_callbacks`, y `caplog` para el log de fallas. ruff (lint + format).

**Target Platform**: Contenedor Linux (`web`) con Docker Compose; correos a la consola del
contenedor o a un servidor SMTP externo.

**Project Type**: Aplicación web Django monolítica con templates en el servidor (sin SPA).

**Performance Goals**: Rechazar una solicitud con confirmación en menos de 30 segundos (SC-003). El
envío no agrega esperas perceptibles al registro en desarrollo; con SMTP, `EMAIL_TIMEOUT=10` acota
el peor caso.

**Constraints**: Una sola vez por evento (FR-010) con `select_for_update` y `on_commit`; falla de
envío sin efecto sobre la operación (FR-011); sin contraseñas ni datos de terceros en los correos
(FR-012, FR-013); credenciales SMTP solo en `.env` (Principio V); textos en español (Principio VI).

**Scale/Scope**: Módulo nuevo `usuarios/notificaciones.py`, 8 templates de correo, 1 template de
confirmación del admin, cambios en `usuarios/views.py`, `usuarios/admin.py`, `config/settings.py` y
`.env.example`, y tests en `usuarios/tests/test_notificaciones.py`.

Decisiones documentadas en [research.md](./research.md) (R1–R6). No hay `NEEDS CLARIFICATION`
pendientes.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Cumplimiento | Estado |
|---|---|---|
| **I. Spec primero (SDD)** | Spec con US 1.3 / SCRUM-66 en `specs/006-notificaciones-correo/spec.md`. El PR se titulará "US 1.3 – Notificaciones por correo del alta de usuarios" y referenciará la spec. | ✅ |
| **II. Simplicidad y Django idiomático** | Usa `django.core.mail`, el admin (acciones y página intermedia como "Eliminar seleccionados"), templates y `logging`. Sin dependencias ni modelos nuevos; el código queda en la app `usuarios`. | ✅ |
| **III. Tests obligatorios** | Cada escenario de aceptación (US 1 a US 4) y caso borde tiene un test en `usuarios/tests/test_notificaciones.py` (ver [Mapa de tests](#mapa-de-tests)). | ✅ |
| **IV. Integridad de datos** | Se elimina solo una cuenta **pendiente**, que nunca operó y no tiene historial (no hay `ForeignKey` a `Usuario`); las cuentas aprobadas no se pueden rechazar. La baja queda en el historial del admin. | ✅ |
| **V. Seguridad** | Credenciales SMTP solo por variables de entorno. Acciones del admin con sesión, permisos (`delete_usuario` para rechazar) y CSRF. Los correos no incluyen contraseñas, hashes ni datos de terceros, y cada uno va a un solo destinatario. | ✅ |
| **VI. Idioma y consistencia** | Correos, mensajes, acciones y nombres (`notificaciones`, `avisar_aprobacion`, `rechazar_solicitudes`) en español. Formato con ruff. | ✅ |
| **Interfaz (UI)** | El rechazo (elimina datos) pide confirmación en una página propia del admin; los resultados se informan con el framework de mensajes. | ✅ |

**Post-diseño (Phase 1)**: cumple todos los principios sin requerir excepciones en *Complexity
Tracking*.

## Diseño

### Flujo de los avisos

```text
POST /usuarios/registro/confirmar/  accion=confirmar
  └─ crear_usuario_pendiente(datos)  (sin cambios)
     └─ on_commit → avisar_solicitud_nueva(request, usuario)    → cada superusuario activo
                    avisar_solicitud_recibida(request, usuario) → solicitante

POST /admin/usuarios/usuario/  action=aprobar_cuentas
  └─ atomic: pendientes = selección.filter(is_active=False).select_for_update()
             update(is_active=True)
     └─ on_commit → avisar_aprobacion(request, u) por cada pendiente aprobada

POST /admin/usuarios/usuario/<pk>/change/  is_active=on
  └─ save_model: estaba_pendiente = Usuario.filter(pk, is_active=False).select_for_update().exists()
                 super().save_model(...)
     └─ si estaba_pendiente y obj.is_active → on_commit → avisar_aprobacion(request, obj)

POST /admin/usuarios/usuario/  action=rechazar_solicitudes
  ├─ sin confirmar=si → página "Rechazar solicitudes" (solo pendientes)
  └─ confirmar=si → atomic: pendientes con select_for_update, guardar (nombre, email),
                            log_deletions, delete()
                    └─ on_commit → avisar_rechazo(nombre, email) por cada una
```

Detalles en [contracts/correos.md](./contracts/correos.md) y
[contracts/admin-rechazo.md](./contracts/admin-rechazo.md).

### Cambios de configuración

- `config/settings.py`: variables `EMAIL_*` y `DEFAULT_FROM_EMAIL` leídas del entorno (R1) y un
  `LOGGING` mínimo que manda el logger `usuarios.notificaciones` a la consola (R6).
- `.env.example`: las mismas variables, con la consola por defecto y un bloque comentado para SMTP.
- `CLAUDE.md`: nota sobre los avisos del alta (dónde se disparan y por qué no se usan señales).

### Mapa de tests

| Escenario / requisito | Test (en `usuarios/tests/test_notificaciones.py`) |
|---|---|
| US1 Esc. 1 — cada administrador activo recibe un aviso con los datos del solicitante y el enlace a su ficha | `test_confirmar_registro_avisa_a_cada_administrador_activo` |
| US1 Esc. 2 — un administrador inactivo no recibe el aviso | `test_administrador_inactivo_no_recibe_aviso` |
| US1 Esc. 3 / US2 Esc. 3 — cancelar o abandonar el registro no manda correos | `test_cancelar_registro_no_envia_correos`, `test_registro_sin_confirmar_no_envia_correos` |
| US1 Esc. 4 — correo ya registrado al confirmar no manda correos | `test_registro_con_correo_tomado_no_envia_correos` |
| US2 Esc. 1 — el solicitante recibe la confirmación de solicitud recibida | `test_confirmar_registro_envia_solicitud_recibida` |
| US2 Esc. 2 — confirmación repetida no reenvía | `test_confirmacion_repetida_no_reenvia_avisos` |
| US3 Esc. 1 y 3 — la acción masiva avisa a cada solicitante aprobado, por separado | `test_accion_aprobar_avisa_a_cada_solicitante` |
| US3 Esc. 2 — aprobar desde la ficha avisa al solicitante | `test_aprobar_desde_ficha_envia_aviso` |
| US3 Esc. 4 / FR-010 — cuentas ya aprobadas no reciben un aviso nuevo | `test_accion_aprobar_no_reenvia_a_cuentas_aprobadas` |
| US3 Esc. 5 — guardar la ficha de una cuenta aprobada no manda correo | `test_guardar_ficha_de_cuenta_aprobada_no_envia_aviso` |
| US4 Esc. 1 — rechazar muestra confirmación con las pendientes y no cambia nada | `test_rechazar_muestra_confirmacion_sin_cambios` |
| US4 Esc. 2 — volver desde la confirmación no rechaza | `test_volver_desde_confirmacion_no_rechaza` |
| US4 Esc. 3 — confirmar rechaza, avisa e informa la cantidad | `test_confirmar_rechazo_elimina_y_avisa` |
| US4 Esc. 4 — la cuenta rechazada no puede iniciar sesión | `test_cuenta_rechazada_no_puede_iniciar_sesion` |
| US4 Esc. 5 — el correo rechazado puede volver a registrarse | `test_correo_rechazado_puede_registrarse_de_nuevo` |
| US4 Esc. 6 / FR-009 — el rechazo no toca cuentas aprobadas | `test_rechazo_ignora_cuentas_aprobadas`, `test_rechazar_sin_pendientes_avisa_y_no_confirma` |
| FR-011 / Edge — una falla de envío no afecta la operación y queda en el log | `test_falla_de_envio_no_impide_registro_y_queda_en_log`, `test_falla_de_envio_no_impide_aprobacion` |
| Edge — sin administradores activos la solicitud queda pendiente y se registra en el log | `test_sin_administradores_registro_queda_pendiente` |
| FR-012 / FR-013 — sin contraseña ni hash, en español, un destinatario por mensaje | `test_correos_no_incluyen_contrasena_ni_datos_de_terceros` |
| Edge — crear un usuario desde el admin no manda avisos | `test_alta_desde_admin_no_envia_avisos` |

Los tests de registro y admin ya existentes (`test_registro.py`, `test_admin.py`) deben seguir
pasando sin cambios.

## Project Structure

### Documentation (this feature)

```text
specs/006-notificaciones-correo/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── correos.md
│   └── admin-rechazo.md
├── checklists/
│   └── requirements.md
└── tasks.md             # lo genera /speckit-tasks
```

### Source Code (repository root)

```text
config/
└── settings.py                        # + EMAIL_* , DEFAULT_FROM_EMAIL, LOGGING
.env.example                           # + variables de correo
CLAUDE.md                              # + nota de avisos del alta
usuarios/
├── notificaciones.py                  # nuevo: avisar_* y _enviar
├── views.py                           # registro_confirmar agenda los dos avisos con on_commit
├── admin.py                           # aprobar_cuentas y save_model avisan; + rechazar_solicitudes
├── templates/
│   ├── usuarios/correos/              # nuevo: {solicitud_nueva,solicitud_recibida,aprobacion,rechazo}_{asunto,cuerpo}.txt
│   └── admin/usuarios/usuario/
│       └── rechazar_confirmacion.html # nuevo
└── tests/
    └── test_notificaciones.py         # nuevo
```

**Structure Decision**: Todo queda en la app `usuarios` existente (Principio II: una app por
módulo), porque los avisos pertenecen al circuito de alta de cuentas que ya vive ahí.

## Complexity Tracking

Sin violaciones de la constitution.
