# Contrato de UI: ayuda en formularios

Contrato de los parciales que usan las pantallas y los tests. Los nombres de clases, atributos
`data-*` e ids son estables: los usan `static/js/aqualab.js` y los tests.

## `templates/ui/ayuda.html` (nuevo)

```django
{% include "ui/ayuda.html" with texto="…" id="id_origen_helptext" etiqueta="Origen" %}
{% include "ui/ayuda.html" with texto="…" id="ayuda-medicion" etiqueta="Medición" lado="derecha" posicion="abajo" %}
```

| Parámetro | Obligatorio | Uso |
|---|---|---|
| `texto` | sí | Texto de la ayuda, dibujado con el autoescape normal. `ui/campo.html` pasa `field.help_text\|safe`, como hoy, porque los `help_text` de Django pueden traer HTML. |
| `id` | sí | Id del tooltip; el control (o la tabla) lo referencia con `aria-describedby`. |
| `etiqueta` | sí | Completa el nombre accesible del botón: «Ayuda: <etiqueta>». |
| `lado` | no | `izquierda` (por defecto) o `derecha`: borde del ícono al que se alinea el texto. |
| `posicion` | no | `arriba` (por defecto) o `abajo`: hacia dónde se abre el texto. `abajo` va en los encabezados de tabla, donde el contenedor con desplazamiento recorta lo que sale por arriba; el puente de WCAG 1.4.13 queda del lado de arriba. |

Marcado resultante:

```html
<span class="ayuda" data-ayuda data-lado="izquierda" data-posicion="arriba">
  <button type="button" class="ayuda-boton" aria-label="Ayuda: Origen"
          aria-describedby="id_origen_helptext">
    <svg … aria-hidden="true" focusable="false">…circle-help…</svg>
  </button>
  <span role="tooltip" id="id_origen_helptext" class="ayuda-texto">…texto…</span>
</span>
```

- `button type="button"`: nunca envía el formulario.
- Estados (los pone el JS): `data-abierta` (abierta por clic o toque) y `data-cerrada` (cerrada
  con Escape o porque se abrió otra; tiene prioridad sobre hover y foco).
- Visible si `.ayuda:is(:hover, :has(:focus-visible), [data-abierta]):not([data-cerrada])`.
- Oculto con `visibility: hidden` (no `display: none`), con transición de opacidad.
- WCAG 1.4.13: el texto visible recibe eventos del mouse (`pointer-events: auto`, nunca
  `pointer-events-none`); un puente invisible (`.ayuda-texto::before`) cubre el espacio entre el
  ícono y el texto, y la salida del mouse se escucha en `.ayuda` (el contenedor de los dos):
  pasar del ícono al texto no la cierra.

## `templates/ui/campo.html` (modificado)

```django
{% include "ui/campo.html" with field=form.origen %}
{% include "ui/campo.html" with field=form.password1 ayuda_visible=True %}
{% include "ui/campo.html" with field=form.pruebas instruccion="Para elegir varias pruebas, …" %}
```

| Parámetro | Nuevo | Uso |
|---|---|---|
| `field`, `clase`, `sin_obligatorio` | no | Sin cambios. |
| `ayuda_visible` | sí | El `help_text` se ve como texto debajo del campo (como hoy) y no hay ícono. |
| `instruccion` | sí | Texto visible debajo del campo (`<p class="campo-ayuda" id="<auto_id>_instruccion">`); el control lo suma a su `aria-describedby`. Se combina con el tooltip del `help_text`. |

Reglas:

1. Con `help_text` y sin `ayuda_visible`: la etiqueta y `ui/ayuda.html` van en una fila
   (`.campo-cabecera`), y el tooltip lleva `id="<auto_id>_helptext"`. El `<div class="campo-ayuda">`
   de debajo no se dibuja.
2. Sin `help_text`: el marcado es el de hoy, sin `data-ayuda`.
3. El ícono nunca va dentro del `<label>` ni del `<legend>`.
4. Radios (`widget_type == "radioselect"`): `<fieldset aria-describedby="{{ field.aria_describedby }}">`
   si hay ayuda o errores; el `<legend>` flota a la izquierda y la ayuda va después.
5. Sin cambios en los ganchos: `<div class="campo-error" id="<auto_id>_error">` con un `<div>` por
   error, clase `is-invalid`, y el id `<auto_id>_helptext` (ahora el del tooltip, o el del texto
   visible con `ayuda_visible`).

## Filtro `describir` (`config/ui.py`)

```django
{{ field|describir:"id_pruebas_instruccion" }}
```

Dibuja el widget con `aria-describedby` = lo que devuelve `field.aria_describedby` (ayuda y error)
más el id recibido, separados por espacios y sin duplicados. Si el widget ya trae
`aria-describedby` propio, lo conserva y le agrega el id.

## Tabla de mediciones (cargar y corregir)

- El aviso `aviso-info` de arriba suma una oración con el formato: coma o punto decimal, sin
  separador de miles; en las pruebas Ausente/Presente se elige la opción de la lista.
- `<th>` «Medición»: texto + `ui/ayuda.html` con `id="ayuda-medicion"`, `lado="derecha"`, `posicion="abajo"` y el
  significado: el valor leído en el análisis, a partir del cual se calcula el resultado.
- Cada control de la columna: `aria-describedby="ayuda-medicion"` y, con error,
  `"ayuda-medicion <auto_id>_error"`.

## Mi firma

- La etiqueta «Firma» (o «Dibujar una firma nueva») va en una fila con `ui/ayuda.html`
  (`id="ayuda-firma"`): cómo dibujarla y que se copia en cada informe que se emita.
- El `<canvas data-firma>` suma `aria-describedby="ayuda-firma"`.
- La indicación visible «Firmá con el mouse o con el dedo…» no cambia.

## Búsquedas (clientes y estudios)

El `<span tabindex="0">` con el ícono `info` y el tooltip hecho a mano se reemplaza por
`ui/ayuda.html`, con el mismo texto, junto a la etiqueta; el campo de búsqueda suma
`aria-describedby` al id de la ayuda (`ayuda-busqueda-cliente`, `ayuda-busqueda-estudio`).
