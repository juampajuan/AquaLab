---

description: "Tareas de la US 9.1 – Ayuda en formularios"
---

# Tasks: Ayuda en formularios

**Input**: Documentos de diseño en `specs/024-ayuda-formularios/`

**Prerequisites**: [plan.md](./plan.md), [spec.md](./spec.md), [research.md](./research.md),
[data-model.md](./data-model.md), [contracts/ayuda-ui.md](./contracts/ayuda-ui.md),
[quickstart.md](./quickstart.md)

**Tests**: Pedidos para cada historia. Cada escenario de aceptación tiene un test de pytest (el
marcado) o de `node:test` (el comportamiento de `static/js/aqualab.js` con un DOM simulado, como
`usuarios/tests/js/sesion.test.cjs`). El lector de pantalla y el navegador real se verifican con el
recorrido de [quickstart.md](./quickstart.md).

**Organization**: dos tandas de implementación.

- **Tanda 1** (Fases 1 a 3): el componente, el parcial y el comportamiento.
  - Apps: `config` (componentes de `templates/ui/`, `static/`) y `usuarios` (registro).
  - Tests de la tanda: `pytest config usuarios` y `node --test config/tests/js/ayuda.test.cjs`.
- **Tanda 2** (Fases 4 y 5): los textos de los formularios y las búsquedas.
  - Apps: `clientes`, `muestras`, `estudios` e `informes`.
  - Tests de la tanda: `pytest clientes muestras estudios informes`.
- La suite completa corre **una sola vez**, al final (T041).

Todos los comandos de Python corren en el contenedor:
`docker compose exec web <comando>`. Node corre en el host (`node` v20; la imagen no lo trae),
como `sesion.test.cjs`.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Se puede hacer en paralelo (otro archivo, sin depender de tareas incompletas).
- **[Story]**: Historia de la spec (US1, US2).

---

## Phase 1: Setup (Tanda 1)

**Purpose**: Llevar a la spec el pedido nuevo (WCAG 1.4.13) antes del código (principio I) y
agregar el ícono.

- [X] T001 Actualizar `specs/024-ayuda-formularios/spec.md` con el pedido del 2026-11-03 sobre
  WCAG 1.4.13 (contenido al pasar el mouse: «se puede recorrer con el mouse»):
  - En `## Clarifications` → `### Session 2026-11-03`, sumar el bullet
    `- Q: ¿La ayuda se cierra si el mouse pasa del ícono al texto? → A: No (WCAG 1.4.13): sigue abierta mientras el mouse esté sobre el ícono o sobre el texto; se cierra al salir de ambos o con Escape.`
  - Agregar el escenario 9 a la US 1: «**Dada** una ayuda abierta con el mouse, **cuando** el
    empleado lleva el mouse del ícono al texto de la ayuda, **entonces** la ayuda sigue visible; **cuando**
    sale de ambos, **entonces** se oculta; **cuando** aprieta Escape, **entonces** se oculta aunque
    el mouse siga encima».
  - En FR-003, cambiar «al retirar el mouse» por «al retirar el mouse del ícono y del texto de la
    ayuda (pasar del ícono al texto no la cierra, WCAG 1.4.13)».
- [X] T002 Actualizar los documentos de diseño con el mismo pedido y con los tests de JS:
  - `specs/024-ayuda-formularios/contracts/ayuda-ui.md`, sección `ui/ayuda.html`: el texto visible
    recibe eventos del mouse (`pointer-events: auto`, nunca `pointer-events-none`); un puente
    invisible (`.ayuda-texto::before`) cubre el espacio entre el ícono y el texto, y `pointerleave`
    se escucha en `.ayuda` (el contenedor de los dos).
  - `specs/024-ayuda-formularios/research.md`: en R3, sumar esto y la regla de WCAG 1.4.13. En R8,
    reemplazar «se verifica a mano» por: el comportamiento de `aqualab.js` se prueba con `node:test`
    y un DOM simulado en `config/tests/js/ayuda.test.cjs`, siguiendo el esquema de
    `usuarios/tests/js/sesion.test.cjs` (sin dependencias); a mano quedan solo el navegador real y
    el lector de pantalla.
  - `specs/024-ayuda-formularios/plan.md`: actualizar Testing, el Mapa de tests (US1 esc. 3–5, 7 y 9
    → `ayuda.test.cjs`) y Complexity Tracking (la excepción al principio III queda solo para el
    lector de pantalla y el render del navegador).
  - `specs/024-ayuda-formularios/quickstart.md`: sumar el paso «pasar el mouse del ícono al texto:
    sigue abierta; salir de ambos: se cierra; Escape con el mouse encima: se cierra» y el comando
    `node --test config/tests/js/ayuda.test.cjs` en Tests automatizados.
- [X] T003 [P] Crear `templates/ui/iconos/circle-help.svg` con el mismo formato que
  `templates/ui/iconos/info.svg`: `class="{{ clase|default:'size-5' }}" aria-hidden="true" focusable="false"`,
  `viewBox="0 0 24 24"`, `fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"`
  y los trazos de Lucide `circle-help`: `<circle cx="12" cy="12" r="10" />`,
  `<path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />`, `<path d="M12 17h.01" />` (ISC, ya cubierta
  por `templates/ui/iconos/LICENSE.txt`).

---

## Phase 2: Foundational (Tanda 1)

**Purpose**: El componente y el parcial de los que dependen las dos historias.

**⚠️ CRITICAL**: La Tanda 2 no empieza hasta cerrar esta fase y la Fase 3.

- [X] T004 Crear `templates/ui/ayuda.html` según [contracts/ayuda-ui.md](./contracts/ayuda-ui.md):
  - Comentario de uso con los parámetros `texto`, `id` y `etiqueta` (obligatorios) y `lado`
    (`izquierda` por defecto, o `derecha`).
  - `<span class="ayuda" data-ayuda data-lado="{{ lado|default:'izquierda' }}">`, con dentro:
    - `<button type="button" class="ayuda-boton" aria-label="Ayuda: {{ etiqueta }}" aria-describedby="{{ id }}">`
      con `{% include "ui/icono.html" with nombre="circle-help" clase="size-4" %}`;
    - `<span role="tooltip" id="{{ id }}" class="ayuda-texto">{{ texto }}</span>`.
  - Sin espacios en blanco sobrantes dentro del botón.
- [X] T005 Agregar el filtro `describir` en `config/ui.py`: `describir(field, id_extra)` devuelve
  `field.as_widget(attrs={"aria-describedby": …})`. El valor junta, en este orden y sin
  duplicados:
  1. el `aria-describedby` propio del widget, si lo tiene (`field.field.widget.attrs`); si no, lo
     de `field.aria_describedby`;
  2. `id_extra`.

  Docstring con el uso: `{{ field|describir:"id_pruebas_instruccion" }}`.
- [X] T006 Modificar `templates/ui/campo.html` según el contrato (depende de T004 y T005):
  - Actualizar el comentario de uso con `ayuda_visible=True` e `instruccion="…"`, y mantener la
    lista de ganchos estables.
  - Con `field.help_text` y sin `ayuda_visible`:
    - la etiqueta (`<label>`) y `{% include "ui/ayuda.html" with texto=field.help_text|safe id=field.auto_id|add:"_helptext" etiqueta=field.label %}`
      van en `<div class="campo-cabecera">`;
    - el `<div class="campo-ayuda" id="…_helptext">` de abajo no se dibuja.
  - Sin `help_text`: el marcado de hoy.
  - Con `ayuda_visible`: el `<div class="campo-ayuda" id="{{ field.auto_id }}_helptext">` de hoy,
    sin ícono.
  - Radios (`radioselect`):
    - `<fieldset{% if field.aria_describedby %} aria-describedby="{{ field.aria_describedby }}"{% endif %}>`;
    - después del `<legend>` (fuera de él) va `ui/ayuda.html`;
    - el `<legend>` lleva además la clase `campo-leyenda`.
  - Con `instruccion`:
    - el control se dibuja con `{{ field|describir:instruccion_id }}`, con
      `instruccion_id = field.auto_id|add:"_instruccion"` (`{% with %}`);
    - debajo de los errores va `<p class="campo-ayuda" id="{{ field.auto_id }}_instruccion">{{ instruccion }}</p>`.
  - Sin cambios en el bloque de errores (`<div class="campo-error" id="…_error">`, un `<div>` por
    error).
- [X] T007 [P] Agregar en `static/src/aqualab.css`, en la capa de componentes y junto a
  `.campo-ayuda`, con los tokens del tema:
  - `.campo-cabecera` (`mb-1.5 flex items-center gap-1.5`; dentro, la `.campo-etiqueta` va con
    `mb-0`).
  - `.campo-leyenda` (`float-left`), y `clear-left` en el `.segmentado` que le sigue, para que el
    ícono quede al lado del legend.
  - `.ayuda` (`relative inline-flex items-center`).
  - `.ayuda-boton` (`inline-flex cursor-help items-center rounded-full text-tinta-suave`, hover y
    `focus-visible` en `text-cian-texto` con `outline-cian`).
  - `.ayuda-texto`:
    - caja: `invisible absolute bottom-full left-0 z-20 mb-2 w-72 max-w-[calc(100vw-2rem)] rounded-lg bg-marino px-3 py-2 text-xs font-normal leading-relaxed whitespace-normal text-white opacity-0 shadow-lg transition duration-150`;
    - con `[data-lado="derecha"]`: `right-0 left-auto`;
    - puente invisible para WCAG 1.4.13: `.ayuda-texto::before` con `content: ""`, `absolute`,
      `inset-x-0`, `top-full`, `h-2`.
  - Regla de visibilidad:
    `.ayuda:is(:hover, :has(:focus-visible), [data-abierta]):not([data-cerrada]) .ayuda-texto { @apply visible opacity-100; }`.
  - No usar `pointer-events-none` en `.ayuda-texto`.
- [X] T008 Recompilar `static/css/aqualab.css` (depende de T006 y T007; las clases nuevas tienen
  que estar en los templates):
  `docker compose exec -u "$(id -u):$(id -g)" web tailwindcss -i static/src/aqualab.css -o static/css/aqualab.css --minify`.

**Checkpoint**: `ui/campo.html` dibuja el ícono y el tooltip, que se abre con hover y foco solo con CSS.

---

## Phase 3: User Story 1 - Ver la ayuda de un campo (Priority: P1) 🎯 MVP (Tanda 1)

**Goal**: el componente se abre con mouse, teclado y toque; se cierra con Escape, al salir del
ícono y del texto (WCAG 1.4.13) o al tocar afuera; nunca hay dos abiertos; el lector de pantalla
lee la ayuda; los errores siguen visibles.

**Independent Test**: con un formulario de prueba con un campo con ayuda y otro sin ayuda:
`pytest config usuarios` (marcado) y `node --test config/tests/js/ayuda.test.cjs`
(comportamiento).

### Tests for User Story 1

> Escribirlos primero y verificar que fallan antes de T013–T015.

- [X] T009 [P] [US1] Crear `config/tests/test_ayuda.py` con un `forms.Form` de prueba: `origen`
  (`CharField`, con `help_text="Fuente de agua"`), `telefono` (sin `help_text`), `tipo` (`ChoiceField`
  con `RadioSelect` y `help_text`) y `pruebas` (con `help_text`). Dibujar `ui/campo.html` con
  `render_to_string` y probar:
  - **Esc. 1, FR-004**: hay `data-ayuda`, un `<button type="button" class="ayuda-boton" aria-label="Ayuda: Origen" aria-describedby="id_origen_helptext">`
    y un `<span role="tooltip" id="id_origen_helptext">` con el texto. No hay `div.campo-ayuda`.
  - **Esc. 2, FR-001**: `telefono` no tiene `data-ayuda`; con `help_text=""` tampoco.
  - **Esc. 6, FR-005**: el `<input>` de `origen` tiene `aria-describedby="id_origen_helptext"`;
    con un error, `"id_origen_helptext id_origen_error"`.
  - **Esc. 6, radios**: el `<fieldset>` tiene `aria-describedby="id_tipo_helptext"`.
  - **Caso borde del clic en la etiqueta**: el botón de ayuda no está dentro del `<label>` ni del
    `<legend>` (regex sobre el contenido de cada uno).
  - **Esc. 8, FR-012**: con un error, `<div class="campo-error" id="id_origen_error">` sigue y el
    ícono también.
  - **`ayuda_visible=True`**: `<div class="campo-ayuda" id="id_origen_helptext">` visible y sin
    `data-ayuda`.
  - **`instruccion="Usá Ctrl"`** en `pruebas`: `<p class="campo-ayuda" id="id_pruebas_instruccion">`
    y el control con `aria-describedby="id_pruebas_helptext id_pruebas_instruccion"`.
  - **`describir`**: si el widget ya trae `aria-describedby="otro"`, lo conserva y agrega el id sin
    duplicarlo.
  - **`ui/ayuda.html` con `lado="derecha"`**: `data-lado="derecha"`.
- [X] T010 [P] [US1] Agregar a `config/tests/test_ayuda.py` un test sobre el CSS compilado
  (`static/css/aqualab.css`, leído con `pathlib`): contiene `.ayuda-texto`, `.ayuda-boton` y
  `data-cerrada`, y no contiene `pointer-events:none` dentro de la regla de `.ayuda-texto`. Tiene
  que fallar si no se recompiló (T008).
- [X] T011 [P] [US1] Crear `config/tests/js/ayuda.test.cjs` con `node:test`, siguiendo el esquema
  de `usuarios/tests/js/sesion.test.cjs`:
  - Cargar `static/js/aqualab.js` con `vm.runInNewContext` y un `document` simulado que registre
    los `addEventListener`.
  - Armar elementos falsos (dos `.ayuda` con su `.ayuda-boton` y su `.ayuda-texto`) con
    `closest()`, `contains()`, `hasAttribute`/`setAttribute`/`removeAttribute`, y
    `querySelectorAll("[data-ayuda]")`.
  - Despachar los eventos a los manejadores registrados y probar:
    - **US1 esc. 5**: un clic en el botón pone `data-abierta`; otro clic lo quita; el evento no
      llama a nada que envíe el formulario.
    - **FR-003**: un clic fuera de toda `.ayuda` quita `data-abierta`.
    - **US1 esc. 4**: `keydown` con `Escape` pone `data-cerrada` en la ayuda que tiene el foco o el
      mouse y no llama a `blur()`; `focusout` y `pointerleave` de esa `.ayuda` lo quitan.
    - **US1 esc. 9, WCAG 1.4.13**:
      - `pointerleave` del botón hacia el texto (el `relatedTarget` queda dentro de la misma
        `.ayuda`) no pone `data-cerrada` ni quita `data-abierta`;
      - `pointerleave` de la `.ayuda` hacia afuera sí la cierra;
      - Escape con el mouse encima la cierra.
    - **US1 esc. 7, FR-006**: abrir la segunda ayuda (clic, `focusin` o `pointerenter`) deja la
      primera con `data-cerrada` y sin `data-abierta`.
    - Los manejadores existentes (`[data-cerrar-mensaje]`, `[data-menu-boton]`) siguen funcionando.
- [X] T012 [P] [US1] Crear `usuarios/tests/test_ayuda.py` (`@pytest.mark.django_db`, `client` y
  `reverse("usuarios:registro")`):
  - **US2 esc. 5**: los requisitos de contraseña de `password1` se ven en `div.campo-ayuda` con id
    `id_password1_helptext`, sin `data-ayuda`.
  - **US2 esc. 2**: nombre, apellido y correo del registro no tienen `data-ayuda`.
  - **Login**: `reverse("usuarios:login")` no tiene `data-ayuda`.
  - **Layouts**: los dos cargan `js/aqualab.js`.

### Implementation for User Story 1

- [X] T013 [US1] Agregar el comportamiento de la ayuda en `static/js/aqualab.js`, con delegación
  de eventos sobre `document` y sin dependencias. Una función `cerrarOtras(actual)` que, en
  todas las `[data-ayuda]` distintas de `actual`, quita `data-abierta` y pone `data-cerrada`.
  - `click` en `.ayuda-boton` → alterna `data-abierta` en su `.ayuda`, quita `data-cerrada` y
    llama a `cerrarOtras`. Va dentro del manejador `click` existente, antes de los otros casos.
  - `click` fuera de toda `.ayuda` → quita `data-abierta` de todas.
  - `keydown` `Escape` → pone `data-cerrada` en la `.ayuda` activa (la que contiene
    `document.activeElement` o la que tiene `data-abierta` o el puntero, guardada en
    `pointerenter`) y no mueve el foco.
  - `pointerenter` y `focusin` en una `.ayuda` → `cerrarOtras(esa)` y le quita `data-cerrada`
    a ella. Usar `pointerover` y `focusin` en `document`, porque `pointerenter` no burbujea.
  - `pointerleave` de la `.ayuda` (con `pointerout` en `document`, comprobando que
    `relatedTarget` no esté dentro de la misma `.ayuda`) → quita `data-abierta` y `data-cerrada`.
    Pasar del ícono al texto no la cierra (WCAG 1.4.13).
  - `focusout` (con `relatedTarget` fuera de la `.ayuda`) → quita `data-cerrada`.
  - Mantener el comentario de cabecera del archivo y sumar uno por bloque. T011 tiene que pasar.
- [X] T014 [US1] Pasar `ayuda_visible=True` a los dos includes de contraseña en
  `usuarios/templates/usuarios/registro_form.html` (`form.password1` y `form.password2`). Son
  instrucciones y quedan visibles como hoy (aclaración de la spec). T012 tiene que pasar.
- [X] T015 [US1] Recompilar el CSS si T013 o T014 sumaron clases (mismo comando que T008) y
  correr los tests de la Tanda 1:
  `docker compose exec web pytest config usuarios` y `node --test config/tests/js/ayuda.test.cjs`.
  Anotar en este archivo el resultado real (pasados y fallados). No correr la suite completa.

**Resultado de la Tanda 1 (2026-11-03)**:

- `docker compose exec web pytest config usuarios` → **194 passed** en 121,8 s.
- `node --test config/tests/js` → **12 passed, 0 failed**.
- `node --test usuarios/tests/js` → **1 passed, 13 failed** (13 de los 14 tests de `sesion.test.cjs`, con
  `eventos.blur is not a function`). La falla es anterior a esta feature: el commit `dff6505` sacó
  el manejador de `blur` de `usuarios/static/usuarios/sesion.js` sin actualizar el test, y estos
  tests no corrían en el CI. Corregido en `c60327e` (`fix(usuarios)`): el test se actualizó al
  comportamiento actual, sin tocar `sesion.js`. `node --test usuarios/tests/js config/tests/js`
  → **29 passed, 0 failed**.
- `ruff check` y `ruff format --check` sobre `config` y `usuarios`: sin errores.

Ajustes de diseño durante la tanda (ya reflejados en research R3 y en el contrato):

- El CSS muestra la ayuda con `:has(:focus-visible)` y no con `:focus-within`. Un clic del mouse
  deja el foco en el botón, y con `:focus-within` la ayuda seguiría abierta al retirar el mouse
  (FR-003). El navegador marca `:focus-visible` solo al llegar con el teclado.
- `pointerout` cierra la ayuda solo con `pointerType === "mouse"`: al levantar el dedo también hay
  `pointerout`, y la ayuda abierta con un toque se cerraba sola.
- El segundo toque en el ícono, además de quitar `data-abierta`, pone `data-cerrada`, porque el
  hover que emula el navegador táctil la mantendría visible.

**Checkpoint (fin de Tanda 1)**: componente completo y probado; cualquier `help_text` cargado ya
se ve como tooltip.

---

## Phase 4: User Story 2 - Textos de ayuda en los formularios existentes (Priority: P1) (Tanda 2)

**Goal**: los campos de FR-010 tienen su ayuda; las instrucciones (Ctrl/Cmd) quedan visibles; las
mediciones muestran el formato en el aviso y el significado en el encabezado.

**Independent Test**: `pytest clientes muestras estudios informes`: cada campo de FR-010 dibuja el
tooltip con su texto y los campos obvios no tienen ícono.

### Tests for User Story 2

> Escribirlos primero y verificar que fallan antes de T021–T029.

- [ ] T016 [P] [US2] Crear `clientes/tests/test_ayuda.py` (fixture `cliente_autenticado` de
  `clientes/tests/conftest.py`):
  - **Esc. 1**: parametrizado sobre `razon_social`, `tipo_documento`, `numero_documento` y `email`,
    en `clientes:registrar` y en `clientes:editar` (con `cliente_existente`), el HTML tiene
    `id="id_<campo>_helptext"` con `role="tooltip"` y texto no vacío.
  - **Esc. 2**: `nombre`, `telefono` y `domicilio` sin ayuda.
  - **Radios**: `tipo_documento` tiene el `aria-describedby` en el `<fieldset>`.
  - **FR-013**: `/admin/clientes/cliente/add/`, con un superusuario, no tiene `data-ayuda`.
- [ ] T017 [P] [US2] Crear `muestras/tests/test_ayuda.py` (fixtures `cliente_autenticado` y
  `cliente_a` de `muestras/tests/conftest.py`, GET de `muestras:registrar`):
  - **Esc. 1**: parametrizado sobre `origen`, `origen_nuevo`, `fecha_muestreo`, `fecha_ingreso`,
    `sitio_extraccion`, `tipo_vertido`, `nombre` y `responsable_muestreo` → tooltip con texto.
  - **Esc. 2**: `cliente` sin ayuda.
  - **Esc. 3**: el texto de `nombre` («Muestra 6») está en el tooltip y no en un `div.campo-ayuda`.
- [ ] T018 [P] [US2] Crear `estudios/tests/test_ayuda.py` (fixtures de `estudios/tests/conftest.py`):
  - **Crear estudio** (`estudios:crear`, `cliente_http`): `tipo` con tooltip; `muestra` sin
    tooltip.
  - **Agregar prueba** (`estudios:agregar_prueba`, `estudio`): `prueba` con tooltip.
  - **Esc. 4, tipos de estudio** (`estudios:tipos_crear`, con el usuario `gestor` logueado):
    - `pruebas` tiene el tooltip `id_pruebas_helptext`;
    - `<p class="campo-ayuda" id="id_pruebas_instruccion">` contiene «Ctrl»;
    - el `<select multiple>` tiene `aria-describedby="id_pruebas_helptext id_pruebas_instruccion"`;
    - no queda otro `<p>` suelto con «Ctrl».
  - **Esc. 6, mediciones**:
    - en `estudios:cargar_mediciones` y en `estudios:corregir_mediciones` (reusar el armado de
      `test_cargar_mediciones.py` y `test_corregir_mediciones.py`), el aviso `aviso-info`
      contiene «coma o punto» y «Ausente/Presente»;
    - el `<th>` «Medición» tiene `ui/ayuda.html` con `id="ayuda-medicion"` y `data-lado="derecha"`;
    - cada control de medición tiene `aria-describedby` que empieza con `ayuda-medicion`, y con un
      valor inválido enviado, `"ayuda-medicion id_<campo>_error"`.
- [ ] T019 [P] [US2] Actualizar `estudios/tests/test_cargar_mediciones.py:197`: la aserción
  `aria-describedby="id_{nombre}_error"` pasa a `aria-describedby="ayuda-medicion id_{nombre}_error"`.
- [ ] T020 [P] [US2] Crear `informes/tests/test_ayuda.py`, con `client.force_login(bioquimico)` y
  GET de `informes:mi_firma`:
  - `matricula` con tooltip;
  - la etiqueta «Firma» tiene `ui/ayuda.html` con `id="ayuda-firma"`;
  - el `<canvas data-firma>` tiene `aria-describedby="ayuda-firma"`;
  - la indicación visible «Firmá con el mouse o con el dedo» sigue.

### Implementation for User Story 2

Textos de FR-010: breves, en español, con los términos del Glosario, sin repetir la etiqueta (FR-011).

- [ ] T021 [P] [US2] En `clientes/forms.py`, `RegistroClienteForm.Meta.help_texts` (no en el
  modelo: generaría una migración):
  - `razon_social`: «Nombre legal de la empresa u organismo. Si el cliente es una persona, completá el nombre.»
  - `tipo_documento`: «DNI para personas; CUIT para empresas, organismos o personas que facturan.»
  - `numero_documento`: «Podés escribirlo con o sin puntos y guiones: se guardan solo los números.»
  - `email`: «A este correo se envían los informes del cliente.»

  Como `numero_documento` es un campo declarado, su `help_text` va en la declaración (los
  `Meta.help_texts` no se aplican a campos declarados).
- [ ] T022 [P] [US2] En `muestras/forms.py`, `help_text=` en `RegistroMuestraForm`:
  - `origen`: «Fuente de agua de la que se tomó la muestra (pozo, red, efluente). Permite comparar los resultados de un mismo origen a lo largo del tiempo.»
  - `origen_nuevo`: «Si la fuente no está en la lista, escribí su nombre. Si ya existe con otras mayúsculas, se usa la existente.»
  - `fecha_muestreo`: «Día en que se tomó la muestra.»
  - `fecha_ingreso`: «Día en que la muestra llegó al laboratorio.»
  - `sitio_extraccion`: «Punto exacto de donde se tomó, por ejemplo la canilla de la cocina o la boca del pozo.»
  - `tipo_vertido`: «Define con qué límites se evalúan los resultados: los del vertido elegido reemplazan a los generales.»
  - `responsable_muestreo`: «Persona que tomó la muestra.»
  - `nombre`: ya tiene su `help_text`, sin cambios.
- [ ] T023 [P] [US2] En `estudios/forms.py`:
  - `CrearEstudioForm.tipo`: `help_text=` «Define las pruebas con las que nace el estudio. Mientras no tenga mediciones se pueden agregar o quitar.»
  - `AgregarPruebaForm.__init__`: `help_text=` en el `ModelChoiceField` de `prueba`: «Solo se listan las pruebas del catálogo que el estudio todavía no tiene.»
  - `campo_medicion`: los dos widgets (`Select` y texto) con `attrs["aria-describedby"] = "ayuda-medicion"`.
  - En `CargarMedicionesForm` (≈ línea 112) y `CorregirMedicionesForm.full_clean` (≈ línea 222), el
    `aria-describedby` de error pasa a `f"ayuda-medicion {self[nombre].auto_id}_error"`.
- [ ] T024 [P] [US2] En `estudios/forms_tipos.py`, `TipoEstudioForm.pruebas`: `help_text=` «Pruebas
  con las que nacen los estudios nuevos de este tipo. Los estudios ya creados no cambian.»
- [ ] T025 [US2] En `estudios/templates/estudios/tipos/formulario.html` (depende de T024):
  - borrar el `<p class="campo-ayuda -mt-3">` de la línea 39;
  - pasar su texto al include:
    `{% include "ui/campo.html" with field=form.pruebas instruccion="Para elegir varias pruebas, mantené apretado Ctrl (o Cmd en Mac) mientras hacés clic." %}`.
- [ ] T026 [US2] En `estudios/templates/estudios/cargar_mediciones.html` y
  `estudios/templates/estudios/corregir_mediciones.html` (depende de T023):
  - al texto del `aviso aviso-info` sumarle «Escribí los decimales con coma o punto, sin separador
    de miles; en las pruebas Ausente/Presente elegí la opción de la lista.»;
  - el `<th>Medición</th>` pasa a
    `<th><span class="inline-flex items-center gap-1.5">Medición {% include "ui/ayuda.html" with texto="Valor leído en el análisis de cada prueba. A partir de él se calcula el resultado." id="ayuda-medicion" etiqueta="Medición" lado="derecha" %}</span></th>`.
- [ ] T027 [P] [US2] En `informes/forms.py`, `FirmaForm.matricula`: `help_text=` «Tu matrícula
  profesional, por ejemplo «MP 1234». Sale junto a tu firma en los informes.»
- [ ] T028 [US2] En `informes/templates/informes/mi_firma.html`:
  - el `<p class="campo-etiqueta">` de la firma va en un `<div class="campo-cabecera">` junto a
    `{% include "ui/ayuda.html" with texto="Dibujá tu firma en el recuadro. Se copia en cada informe que emitas; los ya emitidos no cambian." id="ayuda-firma" etiqueta="Firma" %}`;
  - el `<canvas data-firma>` suma `aria-describedby="ayuda-firma"`;
  - el resto no cambia.
- [ ] T029 [US2] Recompilar el CSS (mismo comando que T008) por las clases nuevas de T026 y T028.

**Checkpoint**: textos de FR-010 visibles en todas las pantallas de la lista.

---

## Phase 5: Búsquedas con el componente común (FR-007) (Tanda 2)

**Purpose**: Los dos tooltips hechos a mano pasan a `ui/ayuda.html`, para que haya un solo
componente.

- [ ] T030 [P] [US1] Actualizar `clientes/tests/test_busqueda.py:107-108` y
  `estudios/tests/test_consulta.py:393-394`: en lugar de `group-hover:visible`, comprobar que hay
  `data-ayuda`, `role="tooltip"` con el mismo texto que hoy y el `aria-describedby` del campo de
  búsqueda (`ayuda-busqueda-cliente` y `ayuda-busqueda-estudio`).
- [ ] T031 [P] [US1] En `clientes/templates/clientes/buscar.html`:
  - reemplazar el `<span class="group relative …" tabindex="0">` (líneas 12–19) por
    `{% include "ui/ayuda.html" with texto="Podés ingresar parte del nombre, de la razón social o del DNI/CUIT (con o sin puntos y guiones)." id="ayuda-busqueda-cliente" etiqueta=form.q.label %}`;
  - mantener el `<div class="mb-1.5 flex items-center gap-1.5">` con la etiqueta;
  - el campo `q` suma `aria-describedby="ayuda-busqueda-cliente"`: en
    `BuscarClienteForm.q.widget.attrs` (`clientes/forms.py`) o con
    `{{ form.q|describir:"ayuda-busqueda-cliente" }}`, según cómo se dibuje hoy.
- [ ] T032 [P] [US1] En `estudios/templates/estudios/buscar.html`, lo mismo que T031, con el texto
  actual del tooltip e `id="ayuda-busqueda-estudio"`.
- [ ] T033 Recompilar el CSS (mismo comando que T008) y correr los tests de la Tanda 2:
  `docker compose exec web pytest clientes muestras estudios informes`. Anotar el resultado real
  en este archivo. No correr la suite completa.

**Checkpoint (fin de Tanda 2)**: todas las pantallas con el componente común.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [ ] T034 Agregar en `CLAUDE.md` la sección «Ayuda en formularios (US 9.1)»:
  - `ui/ayuda.html` es el único componente de ayuda.
  - `ui/campo.html` lo usa con `help_text`. El tooltip lleva el id `<auto_id>_helptext`, al que
    Django ya apunta con `aria-describedby`; en los radios va en el `<fieldset>`.
  - `ayuda_visible=True` e `instruccion=` son para instrucciones, que van visibles (contraseña,
    Ctrl/Cmd); el filtro `describir` las asocia al control.
  - Los textos van en los formularios, no en los modelos (migraciones, admin).
  - Pasar del ícono al texto no cierra la ayuda (WCAG 1.4.13): `pointerout` con `relatedTarget`
    y el puente `::before`.
  - El JS se prueba con `node --test config/tests/js/ayuda.test.cjs`.
- [ ] T035 [P] Verificar que los `help_text` de los modelos no cambiaron:
  `docker compose exec web python manage.py makemigrations --check --dry-run` sin migraciones
  nuevas.
- [ ] T036 [P] `docker compose exec web ruff check .` y `docker compose exec web ruff format --check .`.
- [ ] T037 [P] Recompilar el CSS una última vez y comprobar que `git status static/css/aqualab.css`
  solo muestra cambios ya commiteados o a commitear juntos (como en el CI).
- [ ] T038 [P] `node --test config/tests/js/ayuda.test.cjs usuarios/tests/js/sesion.test.cjs`
  (el de sesión, porque `aqualab.js` se carga en los mismos layouts).
- [ ] T039 Recorrer [quickstart.md](./quickstart.md) en el navegador (Chrome y el modo táctil de
  sus herramientas, más un lector de pantalla: NVDA u Orca) y anotar en este archivo cada paso.
  Si es necesario, el usuario lo acredita como en US 1.2.
- [ ] T040 Actualizar `specs/024-ayuda-formularios/checklists/requirements.md` si la prueba manual
  cambió algún requisito, y la spec antes que el código (principio I).
- [ ] T041 Correr la **suite completa una sola vez**: `docker compose exec web pytest`. Anotar el
  resultado real (pasados, fallados y duración). Si falla, corregir y volver a correr solo los
  tests de la app afectada; la suite completa se repite solo si se tocó un archivo compartido
  (`templates/ui/`, `config/`, `static/`).

- [X] T042 [P] Agregar en `.github/workflows/ci.yml` el paso «Tests de JavaScript», después de
  `pytest`: `actions/setup-node@v4` con `node-version: "20"` (la versión con la que se escribieron
  los tests) y `node --test usuarios/tests/js config/tests/js`. Se hace en la Tanda 1, a pedido del
  usuario: los tests de Node de T011 quedan en el CI desde el primer PR.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Fase 1)**: T001 → T002 (la spec primero); T003 es independiente.
- **Foundational (Fase 2)**: depende de T003. T004 y T005 en paralelo → T006 → T007 → T008.
- **US1 (Fase 3)**: depende de la Fase 2. Tests T009–T012 en paralelo, antes de T013–T014; T015
  cierra la Tanda 1.
- **US2 (Fase 4)**: depende del fin de la Tanda 1 (T015). Tests T016–T020 en paralelo, antes de
  T021–T028; T029 al final.
- **Búsquedas (Fase 5)**: depende de la Fase 2 (usa `ui/ayuda.html`); va en la Tanda 2 para que
  sus tests corran con los de `clientes` y `estudios`. T033 cierra la Tanda 2.
- **Polish (Fase 6)**: depende de T033. T041 es el último.

### User Story Dependencies

- **US1**: no depende de otras historias. Es el MVP: con ella, cualquier `help_text` se ve como
  tooltip accesible.
- **US2**: depende de US1, porque los textos se ven con el componente. Sin US1, los `help_text`
  nuevos se verían como texto suelto.

### Within Each User Story

- Tests antes que la implementación, y verificar que fallan.
- Formularios (`forms.py`) antes que los templates que los usan (T024 → T025, T023 → T026).
- El CSS se recompila después de tocar templates con clases nuevas.

### Parallel Opportunities

- T004 ∥ T005 ∥ T007 (archivos distintos).
- T009 ∥ T010 ∥ T011 ∥ T012.
- T016 ∥ T017 ∥ T018 ∥ T019 ∥ T020; después T021 ∥ T022 ∥ T023 ∥ T024 ∥ T027.
- T030 ∥ T031 ∥ T032.
- T035 ∥ T036 ∥ T037 ∥ T038.

---

## Parallel Example: User Story 1

```text
T009 config/tests/test_ayuda.py          (marcado de ui/campo.html y ui/ayuda.html)
T011 config/tests/js/ayuda.test.cjs       (comportamiento de aqualab.js)
T012 usuarios/tests/test_ayuda.py         (contraseña visible)
```

## Parallel Example: User Story 2

```text
T021 clientes/forms.py      T022 muestras/forms.py      T023 estudios/forms.py
T024 estudios/forms_tipos.py                              T027 informes/forms.py
```

---

## Implementation Strategy

### Tanda 1: MVP (US1)

1. Fases 1 y 2: spec, ícono, componente, parcial y CSS.
2. Fase 3: tests de US1 → JS → contraseña visible.
3. **Validar**: `pytest config usuarios` + `node --test config/tests/js/ayuda.test.cjs` (T015).
   El nombre de la muestra ya se ve como tooltip.

### Tanda 2: textos y búsquedas (US2 + FR-007)

1. Fase 4: tests → textos en formularios → templates de tipos, mediciones y firma.
2. Fase 5: búsquedas al componente común.
3. **Validar**: `pytest clientes muestras estudios informes` (T033).

### Cierre

Fase 6: `CLAUDE.md`, migraciones, ruff, CSS, Node y prueba manual; al final, la suite completa una
sola vez (T041).

---

## Notes

- Un cambio en `templates/ui/campo.html` (Tanda 1) se ve en todas las apps; las que no se corren
  en la Tanda 1 (`clientes`, `muestras`, `estudios`, `informes`) se corren en la Tanda 2, y el
  resto de la suite en T041.
- Los ids `<auto_id>_helptext` y `<auto_id>_error` y la clase `is-invalid` son ganchos estables:
  no renombrarlos.
- Commit sugerido por tanda: `feat(ui): US 9.1 – Ayuda en formularios (componente)` y
  `feat(ui): US 9.1 – Ayuda en formularios (textos)`; los documentos,
  `docs(specs): tasks de la US 9.1 – Ayuda en formularios`.
