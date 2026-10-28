# Data Model: Diseño de la interfaz (013)

Esta feature **no crea ni modifica modelos ni migraciones**. Solo el panel de inicio lee datos
existentes.

## Lecturas del panel de inicio

| Dato del panel | Fuente | Regla |
|---|---|---|
| Muestras sin estudio | `muestras.Muestra` + relación inversa `estudios` (`estudios.Estudio.muestra`, `related_name="estudios"`) | Muestras sin ningún estudio: `Muestra.objects.filter(estudios__isnull=True).count()` |
| Muestras ingresadas hoy | `Muestra.fecha_ingreso` (fecha, sin hora) | `fecha_ingreso == timezone.localdate()` (zona `America/Argentina/Buenos_Aires`, ya configurada en `TIME_ZONE`) |
| Estudios pendientes de análisis | `estudios.Estudio.estado` | `estado == EstadoEstudio.PENDIENTE_ANALISIS` |
| Últimas muestras registradas | `Muestra` con `cliente` y `origen` | Las 5 primeras por `-numero_pi` (el N° PI se asigna en orden de registro), con `select_related("cliente", "origen")` |

Columnas de la tabla: N° PI (`numero_pi`), Cliente (`cliente.nombre_completo`), Origen
(`origen.nombre`), Fecha de ingreso (`fecha_ingreso`, formato `d/m/Y`) y Estado
(`get_estado_display`, como etiqueta).

Las consultas son de solo lectura (FR-021) y se ejecutan en cada carga del inicio: 4 consultas en
total, sin N+1.

## Estados y su color (FR-009)

| Estado | Entidad | Color de etiqueta |
|---|---|---|
| Activo | Cliente (`activo=True`) | Verde (`success`) |
| Inactivo | Cliente (`activo=False`) | Gris (`neutral`) |
| Ingresada | Muestra (`EstadoMuestra.INGRESADA`) | Cian (`info`) |
| Pendiente de análisis | Estudio (`EstadoEstudio.PENDIENTE_ANALISIS`) | Ámbar (`warning`) |

El color se elige en un único lugar (parcial `ui/estado.html`, ver
[contracts/componentes-ui.md](contracts/componentes-ui.md)); los estados que agreguen otras US se suman
ahí.
