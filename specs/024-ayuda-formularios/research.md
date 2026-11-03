# Research: Ayuda en formularios

**Feature**: `024-ayuda-formularios` (US 9.1, SCRUM-68) | **Date**: 2026-11-03

No había `NEEDS CLARIFICATION` en el contexto técnico. Estas son las decisiones de diseño, revisadas
contra el código actual y contra Django 5.2.18 (la versión de `requirements.txt`, inspeccionada en
la imagen `aqualab-web`).

## R1. Asociación de la ayuda al control (lector de pantalla)

- **Decision**: El texto del tooltip es el elemento con `id="<auto_id>_helptext"` (el mismo id que
  hoy usa `ui/campo.html`) y lleva `role="tooltip"`. No se agrega `aria-describedby` a mano en los
  controles comunes: Django 5.2 ya lo pone solo (`BoundField.aria_describedby` devuelve
  `"<auto_id>_helptext <auto_id>_error"` según haya ayuda y errores), así el lector anuncia la
  etiqueta, la ayuda y el error al llegar al control (FR-005, FR-012).
- **Rationale**: Reutiliza el comportamiento del framework (principio II) y el gancho de ids que
  `ui/campo.html` declara como estable. La descripción accesible incluye el contenido de elementos
  referenciados aunque estén ocultos (`visibility: hidden`), así que la ayuda se anuncia sin
  abrirla (SC-003).
- **Excepción, grupos de opciones**: Django no pone `aria-describedby` en los widgets con
  `use_fieldset` (radios: tipo de documento, tipo de vertido). `ui/campo.html` lo pone en el
  `<fieldset>` con `{{ field.aria_describedby }}`.
- **Alternatives considered**: `aria-describedby` armado en cada formulario (repetido y fácil de
  olvidar); `title` en el ícono (no se abre con teclado ni con toque, y los lectores lo leen de
  forma despareja).

## R2. Significado (tooltip) e instrucción (texto visible)

- **Decision**: `ui/campo.html` distingue tres casos con parámetros del `include`, sin cambiar los
  formularios de Django:
  1. **Por defecto**, `help_text` → ícono + tooltip (significado del campo).
  2. **`ayuda_visible=True`**, `help_text` → texto visible debajo del campo, como hoy, sin ícono.
     Lo usan `password1` y `password2` del registro: sus `help_text` son los requisitos que trae
     Django y son instrucciones (aclaración de la spec).
  3. **`instruccion="…"`** → texto visible debajo del campo con `id="<auto_id>_instruccion"`, además
     del tooltip del `help_text`. Lo usa el campo de pruebas de tipos de estudio para la
     indicación de Ctrl/Cmd, que hoy es un `<p>` suelto en `estudios/tipos/formulario.html`.
- Para que el lector también lea la instrucción, el control se dibuja con un filtro nuevo,
  `{{ field|describir:id_instruccion }}` (`config/ui.py`), que llama a
  `field.as_widget(attrs={"aria-describedby": "<lo de Django> <id_instruccion>"})`. Django respeta
  el `aria-describedby` que llega por `attrs` y lo mezcla con los atributos del widget
  (`class`, etc.). Solo se usa cuando hay `instruccion`; el resto sigue con `{{ field }}`.
- **Rationale**: Un único parcial resuelve los tres casos (FR-007); el formulario sigue
  declarando solo `help_text`, que es lo que pide la constitution 1.2.0.
- **Alternatives considered**: poner la instrucción también en `help_text` con un marcador
  (mezcla dos textos en uno y obliga a partirlo en el template); `aria-describedby` fijo en el
  widget del formulario (Django deja de agregar el id del error, y el error quedaría sin anunciar).

## R3. Componente de ayuda y comportamiento sin librerías

- **Decision**: Parcial nuevo `templates/ui/ayuda.html` (`texto`, `id`, `etiqueta`, `lado`
  opcional). Dibuja un `<span class="ayuda" data-ayuda>` con:
  - un `<button type="button" class="ayuda-boton">` con el ícono `circle-help`,
    `aria-label="Ayuda: <etiqueta>"` y `aria-describedby="<id>"` (FR-004);
  - el texto `<span role="tooltip" id="<id>" class="ayuda-texto">`.
- **CSS** (`static/src/aqualab.css`, capa de componentes, con los tokens del tema): el texto está
  oculto con `invisible opacity-0` y se muestra con
  `.ayuda:is(:hover, :focus-within, [data-abierta]):not([data-cerrada]) .ayuda-texto`. Así,
  sin JavaScript igual se abre con mouse y teclado (caso borde).
- **JS** (`static/js/aqualab.js`, que ya cargan los dos layouts, `base.html` y
  `base_acceso.html`), con delegación de eventos como el resto del archivo:
  - clic o toque en `.ayuda-boton` → alterna `data-abierta` (FR-002, táctil);
  - clic o toque fuera → cierra la abierta (FR-003);
  - `Escape` → pone `data-cerrada` en la ayuda activa sin mover el foco; se limpia en
    `focusout` / `pointerleave` (FR-003);
  - al abrir una ayuda (hover, foco o toque), las demás quedan con `data-cerrada` y sin
    `data-abierta`: nunca hay dos visibles (FR-006).
- `aria-expanded` no se usa: es un tooltip (descripción), no un panel que el botón controla.
- **Rationale**: Sin dependencias (FR-008, principio II); un solo lugar para el comportamiento.
- **Alternatives considered**: Popover API de HTML (`popover`/`popovertarget`), que no se abre al
  pasar el mouse ni al enfocar sin JS y tiene soporte parejo recién en navegadores recientes;
  `<details>` (no es un tooltip y mueve el diseño).

## R4. Ubicación del ícono respecto de la etiqueta

- **Decision**: El ícono va **al lado** de `<label>` y `<legend>`, nunca adentro: una fila
  `flex items-center gap-1.5` con la etiqueta y `ui/ayuda.html`. En los grupos de opciones el
  `<legend>` es `float-left` y la ayuda queda después del legend; `.segmentado` lleva `clear-left`.
- **Rationale**: Un botón dentro del `<label>` cambia el nombre accesible del control («Origen
  Ayuda: Origen») y un clic en el ícono enfocaría el control. Afuera, el clic en la etiqueta sigue
  enfocando el control (caso borde) y el nombre accesible no cambia.
- **Alternatives considered**: ícono dentro de la etiqueta con `aria-hidden` (deja la ayuda fuera
  del teclado).

## R5. Posición y bordes de pantalla

- **Decision**: El texto se abre arriba del ícono, alineado a su borde izquierdo (`lado`
  `izquierda`, el valor por defecto) o al derecho (`lado="derecha"`, para el encabezado
  «Medición», que está sobre el borde derecho de la tabla). Ancho `w-72` con tope
  `max-w-[calc(100vw-2rem)]`, `whitespace-normal`, `z-20`.
- **Rationale**: Las etiquetas están a la izquierda de cada tarjeta y la columna «Medición» a la
  derecha: con dos alineaciones fijas el texto nunca se corta ni genera desplazamiento horizontal
  (FR-009), sin calcular posiciones en JS.
- **Alternatives considered**: calcular la posición en JS (más código para un caso que dos
  alineaciones ya cubren).

## R6. Dónde viven los textos de ayuda

- **Decision**: Los textos van en los **formularios**: `help_text=` en los campos declarados y
  `Meta.help_texts` en `RegistroClienteForm` (que también usa la edición del cliente). No se
  tocan los `help_text` de los modelos.
- **Rationale**: Cambiar `help_text` en un campo de modelo genera una migración (`AlterField`), y
  el CI corre `makemigrations --check`. Además, el admin no cambia (FR-013).
- **Excepciones**:
  - **Mi firma, campo Firma**: es un `HiddenInput` y el canvas; la etiqueta es un `<p>`. Se incluye
    `ui/ayuda.html` junto a esa etiqueta, y el canvas suma `aria-describedby` al id del tooltip.
  - **Columna «Medición»** (cargar y corregir): `ui/ayuda.html` en el `<th>`. Los inputs de la
    columna ya arman su `aria-describedby` en `estudios/forms.py` (`<auto_id>_error`); se agrega
    siempre el id de la ayuda (`ayuda-medicion`) delante del error. El formato del valor va en el
    aviso de información visible de arriba de la tabla (aclaración de la spec).
  - **Muestra, nombre**: su `help_text` actual (`muestras/forms.py`) no cambia; pasa a tooltip solo
    por el cambio del parcial.

## R7. Tooltips hechos a mano que ya existen

- **Decision**: Los tooltips de `clientes/buscar.html` y `estudios/buscar.html` (un `<span
  tabindex="0">` con el ícono `info`, solo hover y foco, sin Escape ni toque) pasan a
  `ui/ayuda.html`, con el mismo texto.
- **Rationale**: Es el mismo componente; dejarlos aparte rompería «una única vez» (FR-007) y la
  regla de componentes reutilizables de la constitution. No cambia qué se ve ni dónde.
- **Alternatives considered**: dejarlos como están (dos patrones distintos para lo mismo).

## R8. Verificación del comportamiento en el navegador

- **Decision**: pytest cubre el marcado: ícono solo con ayuda; ids y `aria-describedby` en
  controles, grupos de opciones, la instrucción y la tabla; `button type="button"`; ayuda visible
  de la contraseña; textos de FR-010 y el aviso de mediciones. El comportamiento con mouse,
  teclado, toque y lector de pantalla (US 1, escenarios 3 a 7) se verifica a mano con
  [quickstart.md](./quickstart.md), como `registro_muestra.js` (US 4.1) y `firma.js` (US 7.3).
- **Rationale**: El proyecto no tiene ejecución de JS en los tests y agregarla (Playwright, Node)
  sería una dependencia nueva para unas 40 líneas de JS. La excepción al principio III se justifica
  en [plan.md](./plan.md#complexity-tracking).
