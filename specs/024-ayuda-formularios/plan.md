# Implementation Plan: Ayuda en formularios

**Branch**: `024-ayuda-formularios` | **Date**: 2026-11-03 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/024-ayuda-formularios/spec.md` (US 9.1, SCRUM-68)

## Summary

Un componente nuevo, `templates/ui/ayuda.html`, dibuja un ícono de ayuda (botón con
`circle-help`) y su tooltip (`role="tooltip"`). Se abre con mouse, foco o toque, se cierra con
Escape, al salir o al tocar afuera, y nunca hay dos abiertos. `ui/campo.html` lo usa siempre que el
campo tenga `help_text`, así que cualquier pantalla con el parcial lo obtiene sin código propio.
El tooltip conserva el id `<auto_id>_helptext`, al que Django 5.2 ya apunta con `aria-describedby`:
el lector anuncia la ayuda sin abrirla.

Las instrucciones para completar bien un campo siguen visibles debajo del campo:
- `ayuda_visible=True` para los requisitos de contraseña del registro;
- `instruccion="…"` para la indicación de Ctrl/Cmd de tipos de estudio, asociada al control con el
  filtro `describir`.

El comportamiento lo agregan unas líneas de CSS (componente del tema, funciona sin JS con hover y
foco) y de `static/js/aqualab.js` (toque, Escape, una sola abierta), sin librerías.

Los textos de FR-010 se cargan como `help_text` en los formularios (no en los modelos: no hay
migraciones). En carga y corrección de mediciones, el aviso de información suma el formato del
valor y el encabezado «Medición» lleva un tooltip con su significado. Los dos tooltips hechos a
mano de las búsquedas pasan al componente nuevo.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: Django 5.2.18 (forms: `help_text`, `BoundField.aria_describedby`,
`as_widget(attrs=…)`), Tailwind CSS 4 (CLI standalone, CSS compilado y versionado), componentes de
`templates/ui/` (`campo`, `icono`), `static/js/aqualab.js`. Sin dependencias nuevas.

**Storage**: N/A. Sin modelos, tablas ni migraciones: los textos viven en los formularios.

**Testing**: pytest 9.1.1 + pytest-django 4.14.0. Tests de marcado con `render_to_string` y un
formulario de prueba para `ui/campo.html` y `ui/ayuda.html` (`config/tests/`), y tests de cada
pantalla con el cliente de pruebas y los fixtures existentes. Comportamiento de `aqualab.js` con
`node:test` y un DOM simulado (`config/tests/js/ayuda.test.cjs`, como
`usuarios/tests/js/sesion.test.cjs`), en el CI con `node --test usuarios/tests/js config/tests/js`.
Navegador real y lector de pantalla con [quickstart.md](./quickstart.md) (ver
[Complexity Tracking](#complexity-tracking)); ruff 0.17.1.

**Target Platform**: Contenedor Linux (`web`) con Docker Compose; navegador de escritorio y
pantallas táctiles (tablets del laboratorio).

**Project Type**: Aplicación web Django monolítica con templates en el servidor (sin SPA).

**Performance Goals**: N/A: no hay consultas nuevas; el JS se carga en el mismo archivo que ya
está en los dos layouts.

**Constraints**:
- Ids estables de `ui/campo.html` (`<auto_id>_helptext`, `<auto_id>_error`, `is-invalid`).
- El ícono nunca va dentro de `<label>` ni `<legend>`.
- Sin desplazamiento horizontal.
- Admin sin cambios (FR-013).
- CSS compilado al día (CI) y `makemigrations --check` en verde.

**Scale/Scope**:
- 2 parciales: `ui/ayuda.html` nuevo y `ui/campo.html` modificado.
- 1 ícono SVG nuevo, 1 filtro, unas 40 líneas de JS y unas 30 de CSS.
- Textos en 6 formularios y 9 templates ajustados, más la sección en `CLAUDE.md` y los tests.

Decisiones en [research.md](./research.md) (R1–R8). No hay `NEEDS CLARIFICATION` pendientes.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Cumplimiento | Estado |
|---|---|---|
| **I. Spec primero (SDD)** | Spec de la US 9.1 (commit `e7b045a`), con aclaraciones del 2026-11-03; la aprobación del equipo es requisito antes de `/speckit-implement`. PR: «US 9.1 – Ayuda en formularios». Jira: SCRUM-68. | ⚠️ aprobación pendiente |
| **II. Simplicidad y Django idiomático** | Usa `help_text` y el `aria-describedby` que Django 5.2 ya genera; un parcial, un filtro y JS por delegación en el archivo existente; sin librerías, modelos ni migraciones (YAGNI). | ✅ |
| **III. Tests obligatorios** | Cada escenario con test de marcado (ver [Mapa de tests](#mapa-de-tests)); la interacción en el navegador (US 1, esc. 3–7), con recorrido manual. Sin cálculos nuevos. | ⚠️ excepción justificada |
| **IV. Integridad de datos** | No toca datos ni reglas: solo textos y marcado. | ✅ |
| **V. Seguridad** | Sin vistas nuevas. Los textos de ayuda son literales del código; `help_text` se sigue marcando `safe` solo porque los requisitos de contraseña de Django traen HTML. | ✅ |
| **VI. Idioma y consistencia** | `ayuda`, `instruccion`, `ayuda_visible`, `describir`; textos en español con los términos del Glosario (FR-011); ruff. | ✅ |
| **Interfaz (UI)** | Cumple la regla nueva de la 1.2.0: `help_text` mostrado como tooltip accesible desde `ui/campo.html`. Componente reutilizable con tokens del tema; errores junto al campo sin cambios; CSS compilado. | ✅ |

**Post-diseño (Phase 1)**: cumple todos los principios; la única excepción es la del principio III,
registrada abajo.

## Diseño

### Flujo de render

```text
{% include "ui/campo.html" with field=… [ayuda_visible=True] [instruccion="…"] %}
  ├─ fila etiqueta: <label>/<legend> + (help_text y no ayuda_visible) → ui/ayuda.html
  │                                       id=<auto_id>_helptext, etiqueta=field.label
  ├─ control: {{ field }}  ó  {{ field|describir:"<auto_id>_instruccion" }}  si hay instruccion
  │           (radios: <fieldset aria-describedby="{{ field.aria_describedby }}">)
  ├─ errores: <div id="<auto_id>_error">           (sin cambios)
  ├─ ayuda_visible: <div class="campo-ayuda" id="<auto_id>_helptext">   (como hoy)
  └─ instruccion:  <p class="campo-ayuda" id="<auto_id>_instruccion">
```

### Comportamiento (CSS + `aqualab.js`)

```text
visible  = (:hover | :has(:focus-visible) | [data-abierta]) y no [data-cerrada]
clic en .ayuda-boton      → alterna data-abierta; cierra las demás
clic/toque fuera          → quita data-abierta
Escape                    → data-cerrada en la activa (el foco queda en el botón)
focusout / pointerleave   → quita data-cerrada
abrir una (hover/foco)    → las demás: data-cerrada, sin data-abierta   (una sola visible)
```

Detalle de marcado, parámetros y clases en [contracts/ayuda-ui.md](./contracts/ayuda-ui.md).

### Textos de ayuda (FR-010)

| Formulario (archivo) | Campo | Dónde |
|---|---|---|
| `RegistroClienteForm` (`clientes/forms.py`; registro y edición) | `razon_social`, `tipo_documento`, `numero_documento`, `email` | `Meta.help_texts` |
| `RegistroMuestraForm` (`muestras/forms.py`) | `origen`, `origen_nuevo`, `fecha_muestreo`, `fecha_ingreso`, `sitio_extraccion`, `tipo_vertido`, `responsable_muestreo`; `nombre` ya la tiene | `help_text=` |
| `CrearEstudioForm` (`estudios/forms.py`) | `tipo` | `help_text=` |
| `AgregarPruebaForm` (`estudios/forms.py`) | `prueba` | `help_text=` |
| `TipoEstudioForm` (`estudios/forms_tipos.py`) | `pruebas` (+ `instruccion` Ctrl/Cmd en el template) | `help_text=` |
| `FirmaForm` (`informes/forms.py`) | `matricula` | `help_text=` |
| `mi_firma.html` | Firma (canvas) | `ui/ayuda.html` junto a la etiqueta |
| `cargar_mediciones.html`, `corregir_mediciones.html` | Columna «Medición» | `ui/ayuda.html` en el `<th>` + aviso visible con el formato |

Los textos definitivos salen de la tabla FR-010 de la spec, en una o dos oraciones, sin repetir la
etiqueta (FR-011). La redacción concreta queda en `tasks.md`.

## Project Structure

### Documentation (this feature)

```text
specs/024-ayuda-formularios/
├── plan.md              # este archivo
├── research.md          # R1–R8
├── data-model.md        # sin entidades nuevas: dónde vive cada texto
├── quickstart.md        # recorrido manual en el navegador
├── contracts/
│   └── ayuda-ui.md      # contrato de ui/ayuda.html y de ui/campo.html
├── checklists/
│   └── requirements.md
└── tasks.md             # /speckit-tasks
```

### Source Code (repository root)

```text
templates/ui/
├── ayuda.html                      # nuevo: ícono + tooltip
├── campo.html                      # ayuda, ayuda_visible, instruccion, aria en fieldset
└── iconos/circle-help.svg          # nuevo (Lucide, ISC, como los demás)
config/
├── ui.py                           # filtro describir
└── tests/test_ayuda.py             # nuevo: ui/ayuda.html y ui/campo.html
static/
├── src/aqualab.css                 # .ayuda, .ayuda-boton, .ayuda-texto; legend flotante
├── css/aqualab.css                 # recompilado
└── js/aqualab.js                   # toque, Escape, una sola abierta
clientes/forms.py                   # Meta.help_texts
clientes/templates/clientes/buscar.html        # tooltip a mano → ui/ayuda.html
muestras/forms.py                   # help_text
estudios/forms.py                   # help_text; aria-describedby de mediciones con ayuda-medicion
estudios/forms_tipos.py             # help_text de pruebas
estudios/templates/estudios/
├── buscar.html                     # tooltip a mano → ui/ayuda.html
├── tipos/formulario.html           # instruccion= en lugar del <p> suelto
├── cargar_mediciones.html          # aviso con el formato + ayuda en «Medición»
└── corregir_mediciones.html        # ídem
informes/forms.py                   # help_text de matricula
informes/templates/informes/mi_firma.html      # ayuda junto a «Firma»; canvas describido
usuarios/templates/usuarios/registro_form.html # ayuda_visible=True en password1 y password2
<app>/tests/…                       # tests de cada pantalla (ver mapa)
CLAUDE.md                           # sección «Ayuda en formularios (US 9.1)»
```

**Structure Decision**: El componente es transversal y vive en `templates/ui/` y `config/` (filtro
y tests de componentes), como el resto del sistema visual de la spec 013. Cada app solo carga sus
textos y ajusta sus templates; no hay app nueva.

## Mapa de tests

| Escenario / FR | Test |
|---|---|
| US1 esc. 1–2, FR-001, FR-004 | `config/tests/test_ayuda.py`: campo con `help_text` → `button type="button"` con `aria-label="Ayuda: <etiqueta>"` y tooltip `role="tooltip"` `id="id_x_helptext"`; sin `help_text` → sin `data-ayuda`. |
| US1 esc. 6, FR-005 | Control con `aria-describedby` que incluye `id_x_helptext` (y `id_x_error` con errores); radios → `<fieldset aria-describedby=…>`; ícono fuera del `<label>`/`<legend>`. |
| US1 esc. 8, FR-012 | Con errores y ayuda: el bloque de error sigue visible y el ícono también. |
| US1 esc. 3–5, 7 y 9, FR-002/003/006, WCAG 1.4.13 | `config/tests/js/ayuda.test.cjs` (`node:test`, DOM simulado); test de que el CSS compilado incluye `.ayuda-texto` sin `pointer-events:none`; render real en [quickstart.md](./quickstart.md). |
| US2 esc. 1, FR-010 | Por pantalla (`clientes`, `muestras`, `estudios`, `informes`): parametrizado por campo, el HTML incluye el tooltip con texto no vacío. |
| US2 esc. 2 | Campos obvios (nombre, correo del registro, teléfono, domicilio) sin `data-ayuda`. |
| US2 esc. 3 | Registro de muestra: «Nombre de la muestra» con tooltip y sin `div.campo-ayuda` visible. |
| US2 esc. 4 | Tipos de estudio: tooltip de pruebas y `<p id="id_pruebas_instruccion">` visible; el `<select>` describe ambos ids. |
| US2 esc. 5 | Registro de usuario: requisitos de contraseña en `div.campo-ayuda` visible, sin ícono. |
| US2 esc. 6 | Cargar y corregir mediciones: aviso con el formato; `<th>` «Medición» con tooltip `ayuda-medicion`; inputs con `aria-describedby` que la incluye (y el error si lo hay). |
| FR-007 (búsquedas) | `clientes:buscar` y `estudios:buscar` dibujan `ui/ayuda.html` con el mismo texto que antes. |
| FR-013 | El formulario del admin de `Cliente` no muestra `data-ayuda`. |

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| Principio III: el render del navegador real (CSS `:hover`/`:focus-visible` aplicado) y el anuncio del lector de pantalla se verifican con recorrido manual. | La lógica de JS sí tiene tests (`node:test`); lo que un DOM simulado no reproduce es el CSS aplicado y el lector. Se recorre [quickstart.md](./quickstart.md) antes del PR. | Playwright o un lector automatizado son dependencias nuevas (principio II) para un componente chico; no lo pide ninguna spec. |
