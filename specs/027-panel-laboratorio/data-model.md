# Data Model: Panel del laboratorio

Sin entidades nuevas. Se agrega un permiso y se calculan valores a partir de modelos existentes.

## Permiso

| App | Codename | Nombre | Grupos (migración `informes.0004`) |
|---|---|---|---|
| `informes` (`Informe.Meta.permissions`) | `ver_dashboard` | Puede ver el dashboard | Bioquímicos, Administradores |

## Fuentes de cada indicador

| Indicador | Modelo y campo | Regla |
|---|---|---|
| Muestras ingresadas | `Muestra.fecha_ingreso` (fecha) | Dentro del período; una por muestra |
| Estudios creados | `Estudio.fecha_creacion` (fecha local) | Dentro del período |
| Informes emitidos | `Informe.fecha_emision` (fecha local) | Dentro del período |
| Tiempo de respuesta | `Informe.fecha_emision` − `Muestra.fecha_ingreso` | Promedio de días corridos de los informes emitidos en el período; 1 decimal |
| Estudios por estado | `Estudio.estado` | Hoy, sin período |
| Serie mensual | igual que tiempo de respuesta | Un valor por mes, últimos 6 (incluido el actual); `None` sin informes |
| Serie semanal | `Muestra.fecha_ingreso`, `Informe.fecha_emision` | 12 semanas lunes–domingo, incluida la actual |

## Alertas

| Alerta | Condición | Días que muestra |
|---|---|---|
| Estudios sin avanzar | Estado Pendiente de análisis o En proceso y última actividad < ahora − 7 días | Desde la última actividad |
| Finalizados sin informe | Estado Finalizado y sin `Informe` | Desde la última `Validacion` vigente |

**Última actividad** = la más reciente entre `Estudio.fecha_creacion`, `Medicion.fecha_carga`,
`Medicion.fecha_correccion` y `Validacion.fecha_validacion` de sus pruebas.

Cada fila: N° de estudio, N° PI, cliente (`nombre_completo`), estado, días y enlace a
`estudios:detalle`. Orden: de la más antigua a la más reciente.

## Períodos (research R2)

| Clave | Etiqueta | Período | Período anterior |
|---|---|---|---|
| `este_mes` | Este mes | 1 del mes → hoy | 1 del mes previo → mismo día (recortado) |
| `mes_anterior` | Mes anterior | mes previo completo | el mes anterior a ese, completo |
| `ultimos_3` | Últimos 3 meses | 1 del mes de hace 2 meses → hoy | mismo tramo, 3 meses antes |
| `ultimos_6` | Últimos 6 meses | 1 del mes de hace 5 meses → hoy | mismo tramo, 6 meses antes |

## Variación (research R4)

`diferencia` (entero o decimal), `porcentaje` (entero o «sin datos previos»), `sentido` (▲ / ▼ / =),
`tono`: `exito` si el cambio es favorable, `peligro` si no, `neutro` sin cambio. Favorable: subir en
muestras, estudios e informes; bajar en tiempo de respuesta.
