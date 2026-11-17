# Implementation Plan: Iniciar un estudio desde el asistente

**Branch**: `040-iniciar-estudio-asistente` | **Date**: 2026-11-17 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/040-iniciar-estudio-asistente/spec.md`

## Summary

US 10.3: el asistente de la 10.1 aprende a **preparar** el registro de una muestra (con o sin tipo
de estudio) y la creación de un estudio para una muestra existente. Sigue sin escribir nada: dos
herramientas nuevas de solo lectura (`preparar_muestra`, `preparar_estudio`) reciben en cada vuelta
todo lo que dijo el empleado como texto. AquaLab lo resuelve con las reglas de las pantallas
(clientes activos, orígenes del cliente, tipos activos), interpreta las fechas con la fecha del
laboratorio, valida con `RegistroMuestraForm` y devuelve qué falta, qué no coincide (con opciones
para elegir) o, cuando está todo, el enlace al formulario de siempre con los datos como valores
iniciales por GET. La muestra se confirma en `muestras:registrar` como siempre; si el pedido traía
tipo, el mensaje de éxito ofrece «Crear el estudio <tipo>» hacia `estudios:crear` con muestra y
tipo elegidos (dos confirmaciones, aclaración Q1). Sin modelos ni migraciones nuevas.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: Django 5.2 LTS. Sin dependencias nuevas; mismo servicio de IA de la 10.1
(Groq, `asistente/cliente_ia.py`).

**Storage**: PostgreSQL 16. Sin modelos ni migraciones. Solo cambia el borrador de sesión de
registro de muestra, que suma la clave `tipo_estudio`.

**Testing**: pytest-django con el servicio simulado (fixture `servicio_simulado` de
`asistente/tests/conftest.py`), tests de formularios y vistas de `muestras` y `estudios`, y
`node --test asistente/tests/js` para los botones sin URL y el minimizado al seguir el enlace.

**Target Platform**: servidor Linux (Docker, Render); navegador de escritorio.

**Project Type**: aplicación web Django renderizada en el servidor + el `fetch` JSON del panel.

**Performance Goals**: los de la 10.1 (presupuesto de 20 s por pregunta). Cada `preparar_*` hace
un número fijo de consultas (≤ 6: cliente, origen, tipo, muestra, validación sin base).

**Constraints**: mismos topes de la 10.1 (6 mensajes de historial, 6 vueltas, una herramienta por
vuelta). El ejemplo de la historia llega al enlace en ≤ 3 mensajes del empleado (SC-001). Opciones
≤ 10 por respuesta (`MAX_ENLACES`). Ningún dato de contacto hacia el servicio.

**Scale/Scope**: un laboratorio; decenas de clientes activos y de tipos de estudio.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Cumplimiento |
|---|---|
| I. Spec primero | Spec 040 con US 10.3 (SCRUM-85), 4 aclaraciones del 2026-11-17 resueltas. |
| II. Simplicidad / Django idiomático | Se reutilizan los formularios y las vistas de la US 4.1 y la US 5.1; precarga con `initial` por GET. Sin dependencias, sin SPA, sin app nueva (todo en `asistente`, `muestras` y `estudios`). |
| III. Tests obligatorios | Cada escenario de aceptación tiene un test: herramientas contra datos reales con el servicio simulado, formularios precargados, mensaje de éxito con «Crear el estudio», conteos de la base antes y después (SC-002). |
| IV. Integridad de los datos | El asistente no escribe: las herramientas corren en la transacción `READ ONLY` de la 10.1. El N° PI, los orígenes y los estudios se crean solo con `registrar_muestra` y la confirmación de crear estudio, sin cambios. Las validaciones siguen en los formularios (`RegistroMuestraForm` es la única regla de fechas y orígenes). |
| V. Seguridad | Sin vistas nuevas: las de siempre con `LoginRequiredMiddleware` y CSRF. El enlace GET no concede nada: solo valores iniciales saneados y revalidados al enviar. Lista blanca de datos hacia el servicio (R9). |
| VI. Idioma | Nombres en español (`preparar_muestra`, `valores_iniciales`, `PedidoMuestra`); ruff. |
| UI | La nota del tipo de estudio pendiente y el enlace «Crear el estudio» usan los componentes y mensajes existentes (`messages`, alerta de `ui/mensajes.html`). Los botones de opción y el botón principal del panel reutilizan `.btn`. Recompilar Tailwind si hay clases nuevas. |

**Resultado**: PASA, sin violaciones nuevas. La app `asistente` y los avisos por JSON ya están
justificados en el plan de la 10.1.

**Re-chequeo post-diseño**: PASA. El diseño (research R1–R9, contratos) no agrega modelos ni
vistas, no escribe desde el asistente y mantiene las pantallas de siempre como única forma de crear.

## Project Structure

### Documentation (this feature)

```text
specs/040-iniciar-estudio-asistente/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── herramientas.md          # preparar_muestra, preparar_estudio y mensajes fijos
│   └── enlaces-precargados.md   # parámetros GET de muestras:registrar y estudios:crear
├── checklists/requirements.md
└── tasks.md                     # /speckit-tasks
```

### Source Code (repository root)

```text
asistente/
├── fechas.py                    # NUEVO: leer_fecha(texto, hoy) (R4)
├── registro.py                  # NUEVO: PedidoMuestra/PedidoEstudio, resolución (R3),
│                                #   @registrar preparar_muestra y preparar_estudio
├── herramientas.py              # importa registro; puede_ver(…, "registro") (R8)
├── enlaces.py                   # Referencia sin pk, parametros, minimizar, tipo «opcion»;
│                                #   VISTAS registrar_muestra/crear_estudio/registrar_cliente (R7)
├── conversacion.py              # es_pedido_de_registro, MENSAJE_ALTA_CLIENTE,
│                                #   MENSAJE_SISTEMA y MENSAJE_SOLO_CONSULTA ampliados (R2)
└── tests/
    ├── test_fechas.py
    ├── test_registro.py         # resolución, faltan/problemas/opciones, enlace, privacidad
    ├── test_conversacion_registro.py  # guion del ejemplo (≤ 3 mensajes), corte por verbos
    ├── test_solo_lectura_registro.py  # conteos y próximo N° PI iguales (SC-002)
    └── js/asistente.test.cjs    # opción sin URL (sin ↗) y minimizar al seguir el enlace

muestras/forms.py                # valores_iniciales(query_dict); campo oculto tipo_estudio;
                                 #   datos_para_sesion suma tipo_estudio
muestras/views.py                # registrar usa valores_iniciales; mensaje_exito_muestra con
                                 #   «Crear el estudio <tipo>»; armar_resumen muestra el tipo
muestras/templates/muestras/registro_form.html, registro_confirmar.html  # nota del tipo
muestras/tests/test_precarga.py  # GET con parámetros válidos e inválidos, tipo en el borrador
estudios/forms.py                # valores_iniciales_estudio(query_dict)
estudios/views.py                # crear: initial de muestra y tipo por GET
estudios/tests/test_crear_precarga.py
static/js/aqualab.js             # asistenteEnlaces: opción sin url, data-asistente-minimizar
CLAUDE.md                        # sección «Iniciar un estudio desde el asistente (US 10.3)»
```

**Structure Decision**: no hay app nueva. Lo conversacional va en `asistente/registro.py`, que
lee de `clientes`, `muestras` y `estudios` con sus consultas y formularios. En `muestras` y
`estudios` solo cambia cómo se arman los valores iniciales de sus formularios (una función de saneo
por formulario) y el mensaje de éxito del registro de muestra.

## Complexity Tracking

Sin violaciones nuevas a la constitution.
