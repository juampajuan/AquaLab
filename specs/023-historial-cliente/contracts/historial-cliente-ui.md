# Contrato de interfaz: Consultar historial del cliente

**Feature**: `023-historial-cliente` | **Plan**: [plan.md](../plan.md)

Todas las rutas requieren sesión (`LoginRequiredMiddleware`; sin sesión → 302 al login). Prefijo
`clientes/` (US 2.1). `<pk>` de cliente inexistente → **404**.

## `GET /clientes/<pk>/` — `clientes:detalle` (cambio de la US 3.2)

- Nuevo botón **Historial** (`btn btn-secundario`, ícono `clock`, ya disponible en
  `templates/ui/iconos`) junto a «Editar cliente» → `clientes:historial cliente.pk`.

## `GET /clientes/<pk>/historial/` — `clientes:historial`

- Solo GET (`require_GET`); otro método → **405**.
- Cliente inactivo → 302 a `clientes:buscar` + aviso «El cliente no está disponible.»
  (`MENSAJE_NO_DISPONIBLE`, US 3.2).

### Parámetros (query string)

| Parámetro | Valor | Efecto |
|---|---|---|
| `desde` | fecha `AAAA-MM-DD` o `DD/MM/AAAA` | muestras con fecha de ingreso ≥ desde |
| `hasta` | ídem | muestras con fecha de ingreso ≤ hasta |
| `estado` | `pendiente_analisis`, `en_proceso`, `finalizado`, `informe_generado` o vacío | muestras con algún estudio en ese estado, mostrando solo esos estudios |
| `page` | número | página de 20 muestras |

Parámetro inválido (fecha mal escrita, `desde > hasta`, estado desconocido) → 200, error junto al
campo, **sin filtrar** (historial completo) y con «Limpiar filtros».
Mensajes: «La fecha desde no puede ser posterior a la fecha hasta.» (en `desde`), «Ingresá una fecha
válida (dd/mm/aaaa).» y «Elegí un estado de la lista.».

### Pantalla — `clientes/historial.html`

1. **Encabezado** (`ui/encabezado.html`): sección «Clientes», anterior «Ficha del cliente» →
   `clientes:detalle`, miga «Historial», título `cliente.nombre_completo`, subtítulo
   «{{ tipo_documento }} {{ numero_documento }}».
2. **Filtros** (form GET): «Ingreso desde», «Ingreso hasta», «Estado del estudio» (Todos + los
   cuatro estados); botones **Filtrar** (`btn btn-primario`) y, con algún filtro en la URL
   (`desde`, `hasta` o `estado` no vacíos, válidos o no), **Limpiar filtros**
   (`btn btn-secundario`, URL sin parámetros). Errores con
   `ui/errores_form.html` / `ui/campo.html`.
3. **Listado** (tabla, una fila por muestra; `data-muestra="<numero_pi>"`):
   - **N° PI** — enlace a `muestras:detalle muestra.pk`.
   - **Fecha de ingreso** — `d/m/Y`.
   - **Origen** — `muestra.origen.nombre`.
   - **Estudios** — por cada estudio de `estudios_historial` (`data-estudio="<pk>"`):
     enlace «Estudio N° {{ pk }} · {{ tipo_nombre_snapshot }}» → `estudios:detalle`, etiqueta
     `ui/estado.html` con `estudio.get_estado_display` y `estudio.estado|tipo_estado`, y, si el
     estudio tiene `Informe` (`{% if estudio.informe %}`), enlace
     **Ver informe {{ estudio.informe.numero_mostrado }}** → `informes:ver estudio.pk`. Sin estudios: «Sin estudios» (texto suave).
4. **Paginación**: `ui/paginacion.html` con `parametros` = query string actual sin `page`.

### Estados vacíos (`ui/estado_vacio.html`)

| Caso | Mensaje | Acción |
|---|---|---|
| Cliente sin muestras | «Este cliente no tiene muestras registradas.» | — |
| Filtros sin coincidencias | «Ninguna muestra coincide con los filtros.» | «Limpiar filtros» → historial sin parámetros |

### No hace

- No ofrece acciones que creen, modifiquen ni borren datos.
- No exporta ni imprime el historial.
