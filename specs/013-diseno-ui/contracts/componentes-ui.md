# Contrato: componentes de interfaz reutilizables

Todos los elementos repetidos se definen una sola vez (FR-013). Las pantallas actuales y las de las
US 5.2–5.5 los usan así.

## Layouts

| Template | Uso | Bloques |
|---|---|---|
| `templates/base.html` | Pantallas internas: menú lateral, barra superior con usuario y "Cerrar sesión", mensajes y contenido | `title`, `encabezado` (migas, título, subtítulo, acciones), `content` |
| `templates/base_acceso.html` | Login y registro: pantalla partida, panel izquierdo con 4 imágenes que alternan (CSS, research R6b), degradado, textura de puntos, logo y frase; contenido a la derecha; sin menú. Es la única definición del panel: las 4 pantallas de acceso lo comparten idéntico | `title`, `content` |

Ambos cargan solo `static/css/aqualab.css`, `static/js/aqualab.js` y mantienen los includes de la
guardia de sesión (`includes/estilo_sesion.html`, `includes/guardia_sesion.html`) y el atributo
`data-contenido-sensible` sobre el contenido.

## Parciales (`templates/ui/`)

| Parcial | Parámetros | Qué dibuja |
|---|---|---|
| `menu.html` | — (usa `request.resolver_match`) | Menú lateral agrupado: Inicio; Clientes (Buscar cliente, Registrar cliente); Muestras (Registrar muestra); Estudios (Crear estudio). Destaca el subítem actual |
| `mensajes.html` | — (usa `messages`) | Avisos de éxito, error, advertencia e información, con botón para cerrar. Cada aviso lleva `data-nivel="exito|error|advertencia|info"` |
| `encabezado.html` | `titulo`, `subtitulo` (opc.), `migas` (opc., lista de `(texto, url)`) | Migas de pan, título y subtítulo de la página |
| `campo.html` | `field`, `ancho` (opc.) | Etiqueta (con marcador `<span data-obligatorio>*</span>` si es obligatorio), control, errores en `<div id="{{ field.auto_id }}_error">` con un `<div>` por error, y ayuda en `{{ field.auto_id }}_helptext` |
| `errores_form.html` | `form` | Errores generales (`non_field_errors`) arriba del formulario |
| `seccion_titulo.html` | `titulo`, `icono` | Título de una sección de formulario. La sección es `<section class="tarjeta seccion-form">` (un `{% include %}` no puede envolver contenido) |
| `dato.html` | `etiqueta`, `valor`, `extra` (opc.), `clase` (opc.) | Un dato de un resumen o ficha; vacío → "—". El contenedor es `<dl class="resumen" data-componente="resumen">` |
| `acciones_confirmacion.html` | `texto_confirmar`, `url_volver`, `token` y `accion_confirmar` (flujo de estudios) | Botón principal "Confirmar…", "Volver y editar" y "Cancelar" (rojo, separado). Raíz con `data-componente="acciones-confirmacion"` |
| `tabla.html` (patrón documentado, no parcial) | — | Tarjeta + `<table>` con clases `tabla`, encabezado, filas y `overflow-x-auto` |
| `estado_vacio.html` | `mensaje`, `accion_texto` (opc.), `accion_url` (opc.) | Ilustración/ícono, mensaje y acción opcional. Raíz con `data-componente="estado-vacio"` |
| `paginacion.html` | `page_obj`, `parametros` (query string sin `page`) | "Anterior", "Página X de Y", "Siguiente" |
| `estado.html` | `estado` (texto visible), `tipo` (`success`, `neutral`, `info`, `warning`, `danger`) | Etiqueta de estado de color fijo |
| `icono.html` | `nombre`, `clase` (opc.) | SVG en línea de `ui/iconos/<nombre>.svg` (Lucide) |
| `iniciales.html` | `texto` | Círculo con las iniciales (usuario logueado, filas de clientes) |

## Clases de componentes (`@layer components` en `static/src/aqualab.css`)

| Clase | Uso |
|---|---|
| `btn`, `btn-primario`, `btn-secundario`, `btn-peligro`, `btn-link` | Botones y links con forma de botón |
| `form-control`, `form-select`, `is-invalid` | **Nombres heredados**: los asignan los `forms.py` (ver research R7). No renombrar |
| `segmentado` | Grupo de radios dibujado como botones segmentados (tipo de vertido) |
| `tarjeta` | Superficie blanca con borde y sombra nivel 1 |
| `tabla` | Tabla con encabezado en mayúsculas pequeñas y filas con hover |

## Ganchos que NO se pueden cambiar (los usan JS y tests)

- `id="{{ field.auto_id }}_error"` con un `<div>` por error, y la clase `is-invalid` en el control.
- Registrar muestra: `id="ficha-cliente"` con `data-ficha="razon_social_o_nombre|documento|email"`,
  `<script id="clientes-muestra">` (json_script), `id="mostrar-origen-nuevo"`,
  `id="bloque-origen-nuevo"`, y el uso del atributo `hidden`.
- Guardia de sesión: `data-contenido-sensible`, `#sesion-aviso`, `#sesion-mensaje`,
  `#sesion-reintentar`.
- Textos de botones, links y mensajes actuales (los verifican tests y la spec, FR-012).
