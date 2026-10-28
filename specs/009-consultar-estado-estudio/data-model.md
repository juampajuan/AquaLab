# Data Model: Consultar estado del estudio

**Feature**: `009-consultar-estado-estudio` | **Plan**: [plan.md](./plan.md)

Se extienden `estudios.EstadoEstudio` y `estudios.PruebaEstudio` para representar todos los estados generales del estudio y el estado individual de cada prueba asignada. Además, se consultan `estudios.Estudio`, `pruebas.Prueba`, `muestras.Muestra`, `muestras.Origen` y `clientes.Cliente`.

## 1. Extensión de `estudios.EstadoEstudio` y `estudios.Estudio`

`EstadoEstudio(models.TextChoices)`:

| Constante | Valor persistido | Etiqueta (`label`) | Descripción |
|---|---|---|---|
| `PENDIENTE_ANALISIS` | `"pendiente_analisis"` | `"Pendiente de análisis"` | Estado inicial al crear el estudio (US 5.1) |
| `EN_PROCESO` | `"en_proceso"` | `"En proceso"` | Al menos una prueba fue cargada o completada |
| `FINALIZADO` | `"finalizado"` | `"Finalizado"` | Todas las pruebas del estudio están completadas/validadas |
| `INFORME_GENERADO` | `"informe_generado"` | `"Informe generado"` | Se emitió el informe final del estudio (US 7.2) |

Campos de `Estudio` consultados:

| Campo | Uso en US 5.2 |
|---|---|
| `id` (`pk`) | Identificador numérico único del estudio; filtro exacto en búsqueda y parámetro de `estudios:detalle` |
| `muestra` | FK a `muestras.Muestra` (`related_name="estudios"`); acceso a N° PI, nombre, origen y cliente |
| `tipo_nombre_snapshot` | Nombre histórico del tipo de estudio mostrado en resultados, detalle de estudio y ficha de muestra |
| `tipo_descripcion_snapshot` | Descripción histórica del tipo de estudio mostrada en el detalle del estudio |
| `estado` | Estado general del estudio (`get_estado_display()`) |
| `creado_por` | Empleado que creó el estudio (mostrado en el detalle del estudio) |
| `fecha_creacion` | Fecha y hora de creación (mostrada en resultados, detalle y ficha de muestra) |

## 2. Extensión de `estudios.PruebaEstudio`

Nuevo `EstadoPruebaEstudio(models.TextChoices)`:

| Constante | Valor persistido | Etiqueta (`label`) | Descripción |
|---|---|---|---|
| `PENDIENTE` | `"pendiente"` | `"Pendiente"` | Estado por defecto al asignarse la prueba al estudio |
| `CARGADA` | `"cargada"` | `"Cargada"` | Medición cruda registrada pendiente de validación (US 6.1) |
| `COMPLETADA` | `"completada"` | `"Completada"` | Resultado validado por el responsable (US 6.4) |

Campos de `PruebaEstudio`:

| Campo | Diseño / Uso |
|---|---|
| `id` | `BigAutoField` (existente) |
| `estudio` | `FK` a `Estudio`, `on_delete=PROTECT`, `related_name="pruebas_asignadas"` (existente) |
| `prueba` | `FK` a `pruebas.Prueba`, `on_delete=PROTECT` (existente; se consultan `prueba.codigo` y `prueba.nombre`) |
| `estado` | **Nuevo**: `CharField("estado", max_length=20, choices=EstadoPruebaEstudio.choices, default=EstadoPruebaEstudio.PENDIENTE, editable=False)` |

## 3. Entidad consultada: `muestras.Muestra`

| Campo | Uso en US 5.2 |
|---|---|
| `id` (`pk`) | Parámetro de la URL `muestras:detalle` (`/muestras/<int:pk>/`) |
| `numero_pi` | Filtro exacto en el buscador de estudios (cuando `q` es numérico); visible en todas las pantallas |
| `nombre` | Filtro `unaccent` + `icontains` en el buscador; visible en búsqueda, detalle de estudio y ficha de muestra |
| `cliente` | FK a `clientes.Cliente`; sus campos `nombre`, `razon_social` y `numero_documento` participan del buscador |
| `origen` | FK a `muestras.Origen`; se muestra `origen.nombre` en el detalle del estudio y en la ficha de la muestra |
| `fecha_muestreo`, `fecha_ingreso`, `sitio_extraccion`, `tipo_vertido`, `responsable_muestreo`, `estado`, `registrada_por`, `fecha_registro` | Mostrados en la ficha de la muestra (`muestras:detalle`) |

## 4. Consultas principales (no persistidas)

### Búsqueda de estudios (`estudios:buscar`)

```text
Estudio.objects.select_related("muestra", "muestra__cliente", "muestra__origen")
  .filter(
      muestra__nombre ~ q
      OR muestra__cliente__nombre ~ q
      OR muestra__cliente__razon_social ~ q
      [OR pk = int(q) OR muestra__numero_pi = int(q)  si q.isdigit()]
      [OR muestra__cliente__numero_documento ∋ normalizar_numero_documento(q)  si solo dígitos]
  )
  .order_by("-pk")
```

Donde `~` es `unaccent__icontains`. Paginada de a 20 resultados por página.

### Ficha de la muestra (`muestras:detalle`)

```text
muestra.estudios.annotate(
    total_pruebas=Count("pruebas_asignadas"),
    pruebas_completadas=Count(
        "pruebas_asignadas",
        filter=Q(pruebas_asignadas__estado=EstadoPruebaEstudio.COMPLETADA),
    ),
).order_by("-pk")
```

## 5. Migración

- `estudios/migrations/0003_estados_estudio_y_prueba.py`:
  - `AlterField` en `Estudio.estado` con los 4 choices de `EstadoEstudio`.
  - `AddField` en `PruebaEstudio.estado` con `default="pendiente"` y los 3 choices de `EstadoPruebaEstudio`.

## 6. Reglas de validación del buscador (en `BuscarEstudioForm`)

- Se recortan espacios laterales (`strip=True`).
- Vacío → `"Ingresá un identificador de estudio, N° PI, muestra o cliente para buscar."`
- Menos de 2 caracteres y no numérico (`len(q) < 2 and not q.isdigit()`) → `"Ingresá al menos 2 caracteres para buscar."`
