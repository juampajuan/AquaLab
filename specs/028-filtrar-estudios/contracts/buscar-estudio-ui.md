# Contrato de interfaz: Buscar estudio con filtros

**Feature**: `028-filtrar-estudios` | **Plan**: [plan.md](../plan.md)

Requiere sesión (`LoginRequiredMiddleware`; sin sesión → 302 al login). Cambia solo
`GET /estudios/buscar/` — `estudios:buscar` (US 5.2). `informes:listar` (US 7.1) no cambia.

## Parámetros (query string)

| Parámetro | Valor | Efecto |
|---|---|---|
| `q` | texto (US 5.2, sin cambios) | `filtro_busqueda(q)` |
| `estado` | `pendiente_analisis`, `en_proceso`, `finalizado`, `informe_generado` o vacío («Todos») | estudios con ese estado actual |
| `desde` | fecha `AAAA-MM-DD` o `DD/MM/AAAA` | `fecha_creacion` ≥ 00:00 de ese día (zona del laboratorio) |
| `hasta` | ídem | `fecha_creacion` < 00:00 del día siguiente |
| `page` | número | página de 20 estudios (número fuera de rango → última página, como hoy) |

Todos opcionales y combinables (AND). Cualquier valor inválido → 200, error junto al campo con el
valor recibido y **listado completo sin filtrar**.

Mensajes: «La fecha desde no puede ser posterior a la fecha hasta.» (en `desde`), «Ingresá una fecha
válida (dd/mm/aaaa).», «Elegí un estado de la lista.» y los de `q` de la US 5.2.

## Pantalla — `estudios/buscar.html`

1. **Formulario GET** (tarjeta, `novalidate`):
   - Fila de búsqueda (sin cambios): campo `q` con su ayuda (`ayuda-busqueda-estudio`).
   - Fila de filtros (`grid sm:grid-cols-3`, `ui/campo.html`): **Estado** (select, «Todos» +
     los cuatro estados), **Desde**, **Hasta** (selector de fecha, con ayuda «Fecha en que se creó el
     estudio. El día indicado se incluye.»).
   - Botones: **Buscar** (`btn btn-primario`) y, si llegó `q`, `estado`, `desde` o `hasta` no vacíos
     (válidos o no), **Limpiar filtros** (`btn btn-secundario`, ícono `x`, → `estudios:buscar` sin
     parámetros). Ya no existe «Ver todos».
   - Errores: los de `q` como hoy; los de los filtros con `ui/campo.html`.
2. **Listado**: columnas, orden (`-pk`), enlaces y estado sin cambios. Encabezado
   «N estudio(s) encontrado(s)» con texto o filtros aplicados; «N estudio(s) registrado(s)» sin
   ninguno.
3. **Paginación**: `ui/paginacion.html` con `parametros` = query string actual sin `page`.

## Estados vacíos (`ui/estado_vacio.html`)

| Caso | Mensaje | Acción |
|---|---|---|
| No hay estudios | «Aún no hay estudios registrados.» | — |
| Solo texto, sin coincidencias | «No se encontraron estudios para «{q}».» | — |
| Algún filtro aplicado, sin coincidencias | «Ningún estudio coincide con la búsqueda y los filtros.» | «Limpiar filtros» → `estudios:buscar` |

## Historial del cliente (`clientes:historial`)

Sin cambios visibles: mismas etiquetas, mensajes y comportamiento; su formulario pasa a heredar
`FiltrosEstudioForm`.
