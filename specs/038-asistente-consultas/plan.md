# Implementation Plan: Asistente de consultas en lenguaje natural

**Branch**: `038-asistente-consultas` | **Date**: 2026-11-15 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/038-asistente-consultas/spec.md`

## Summary

US 10.1: un asistente, abierto desde un botón flotante en todas las pantallas con sesión, que
responde en español preguntas sobre muestras, estudios y clientes. Para que no invente datos, el
modelo de Groq no responde de memoria: AquaLab le ofrece **herramientas de solo lectura**
(function calling de la API compatible con OpenAI) que se ejecutan en Django con el usuario que
pregunta y reutilizan las consultas de las pantallas (detalle del estudio, ficha de la muestra,
historial del cliente, búsquedas), así lo que dice coincide con lo que se ve, incluidos «< LD»,
«Ausente» y «Presente». Los enlaces los arma AquaLab con `reverse` a partir de lo que devolvieron
las herramientas; el texto del modelo se muestra como texto plano. La llamada a Groq usa `urllib`
de la librería estándar (sin dependencias nuevas), con timeout, tope de vueltas y avisos distintos
para «no disponible» y «límite de consultas alcanzado». No se guarda nada en la base.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: Django 5.2 LTS. Sin dependencias nuevas: HTTP con `urllib.request` y
`json` de la librería estándar. Groq (API compatible con OpenAI, `chat/completions` con `tools`),
modelo por defecto `openai/gpt-oss-120b` (research R2).

**Storage**: PostgreSQL 16, solo lectura. Sin modelos ni migraciones nuevas.

**Testing**: pytest-django (servicio de IA simulado parcheando `asistente.cliente_ia.enviar`;
nunca se llama a Groq) y `node --test asistente/tests/js` para el panel (DOM simulado, como
`config/tests/js`).

**Target Platform**: servidor Linux (Docker local, Render); navegador de escritorio.

**Project Type**: aplicación web Django renderizada en el servidor + un pedido `fetch` JSON.

**Performance Goals**: respuesta en menos de 15 s con el servicio disponible (SC-003); aviso de
falla en menos de 20 s (SC-007). Cada herramienta, número fijo de consultas (sin N+1).

**Constraints**: preguntas ≤ 500 caracteres; el navegador manda como mucho los últimos 6 mensajes;
timeout de 15 s por llamada HTTP (recortado a lo que queda) y presupuesto total de 25 s por
pregunta; a lo sumo 6 vueltas de herramientas y 8 ejecuciones por pregunta; una herramienta por
vuelta, sin depender de llamadas en paralelo (`parallel_tool_calls: false`, research R11); ningún
dato de contacto ni de usuarios hacia Groq.

**Scale/Scope**: un laboratorio, decenas de usuarios; cuota del plan gratuito de Groq (demo).

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Cumplimiento |
|---|---|
| I. Spec primero | Spec 038 con US 10.1, aclaraciones del 2026-11-15 resueltas. Clave Jira pendiente (SCRUM-??). |
| II. Simplicidad / Django idiomático | Sin SPA: el panel es un parcial de `templates/ui/` + JS sin librerías en `static/js/aqualab.js`. Sin dependencias nuevas (`urllib`). App nueva `asistente`: ver Complexity Tracking. |
| III. Tests obligatorios | Cada escenario de la spec tiene test; el servicio se simula siempre. Paridad con las pantallas probada comparando herramienta y vista sobre los mismos datos. JS con `node:test` (ya en el CI). |
| IV. Integridad de los datos | Solo lectura: las herramientas corren en una transacción `READ ONLY` (una escritura falla); no se guardan conversaciones. Los valores salen de `Decimal` con los textos de pantalla (`texto_resultado`), nunca `float`. |
| V. Seguridad | `LoginRequiredMiddleware` + vista `require_POST` con CSRF. Clave solo en `.env` (`ASISTENTE_API_KEY`). Permisos replicados de las vistas en cada herramienta. La respuesta se muestra con `textContent` (sin HTML del modelo). Datos de contacto excluidos por construcción (lista blanca de campos). |
| VI. Idioma | Interfaz, mensajes, nombres (`asistente`, `herramientas`, `preguntar`) en español; ruff. |
| UI | Botón y panel con tokens del tema, parcial reutilizable `ui/asistente.html`, ícono existente (`ui/icono.html`). No guarda ni elimina datos: no requiere confirmación. Recompilar Tailwind si hay clases nuevas. |

**Resultado**: PASA, con una justificación (app nueva fuera de la lista de la constitution).

**Re-chequeo post-diseño**: PASA. El diseño (research R1–R11, contratos) no agrega modelos, no
escribe en la base y no suma dependencias.

## Project Structure

### Documentation (this feature)

```text
specs/038-asistente-consultas/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── preguntar.md        # POST asistente:preguntar (JSON de ida y vuelta)
│   ├── herramientas.md     # herramientas ofrecidas al modelo y su salida
│   └── servicio-ia.md      # llamada a Groq y traducción de errores
├── checklists/requirements.md
└── tasks.md                # /speckit-tasks
```

### Source Code (repository root)

```text
asistente/                       # app nueva (US 10.1)
├── __init__.py
├── apps.py
├── configuracion.py             # lee settings.ASISTENTE (habilitado, url, modelo, timeouts)
├── cliente_ia.py                # enviar(mensajes, herramientas) con urllib; errores tipados
├── herramientas.py              # definiciones JSON + ejecución de solo lectura, con el usuario
├── conversacion.py              # responder(usuario, pregunta, historial): vueltas y enlaces
├── enlaces.py                   # Referencia(tipo, pk, etiqueta) → url con reverse
├── forms.py                     # PreguntaForm (pregunta ≤ 500, historial ≤ 6 mensajes)
├── context_processors.py        # asistente_habilitado para base.html
├── urls.py                      # asistente:preguntar
├── views.py                     # preguntar (POST, JSON)
└── tests/
    ├── conftest.py              # servicio_simulado, respuestas guionadas
    ├── test_herramientas.py     # contra datos de prueba y paridad con las pantallas
    ├── test_conversacion.py     # vueltas, topes, enlaces, no encontrado, varias coincidencias
    ├── test_privacidad.py       # nada de correo/teléfono/domicilio/documento en lo enviado
    ├── test_solo_lectura.py     # transacción READ ONLY, base igual antes y después
    ├── test_cliente_ia.py       # urllib simulado: timeout, red, 429, 401, 5xx, JSON inválido
    ├── test_vista.py            # POST, CSRF, sesión, códigos y avisos
    ├── test_layout.py           # botón en base.html, deshabilitado sin clave
    └── js/asistente.test.cjs    # panel: abrir/cerrar, envío, historial, textContent, avisos

estudios/views.py                # se extrae pruebas_del_detalle(estudio) de detalle()
config/settings.py               # INSTALLED_APPS, ASISTENTE, context processor, logger
config/urls.py                   # path("asistente/", include("asistente.urls"))
templates/base.html              # {% include "ui/asistente.html" %} si hay sesión
templates/ui/asistente.html      # botón flotante + panel
static/js/aqualab.js             # comportamiento del panel (fetch)
static/src/aqualab.css → static/css/aqualab.css   # recompilado si hay clases nuevas
.env.example                     # ASISTENTE_API_KEY, ASISTENTE_URL, ASISTENTE_MODELO
.github/workflows/*.yml          # suma asistente/tests/js a node --test
CLAUDE.md                        # sección «Asistente de consultas (US 10.1)»
```

**Structure Decision**: una app Django nueva, `asistente`, que no tiene modelos: lee de
`muestras`, `estudios`, `clientes` e `informes` a través de sus consultas existentes. El único
cambio en otras apps es extraer `pruebas_del_detalle` de `estudios.views.detalle` para que la
pantalla y la herramienta usen exactamente el mismo cálculo.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| App `asistente` fuera de la lista de apps del principio II | El asistente cruza muestras, estudios y clientes y tiene su propia integración externa (Groq); no pertenece a ninguno de esos módulos | Ponerlo en `estudios` mezclaría la integración externa con la lógica del laboratorio y haría que `estudios` dependa de `clientes` e `informes` para algo ajeno a su dominio |
