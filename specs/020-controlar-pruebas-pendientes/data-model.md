# Data Model: Seleccionar estudio y controlar pruebas pendientes

**Feature**: `020-controlar-pruebas-pendientes` | **Plan**: [plan.md](./plan.md)

**Sin modelos ni migraciones nuevas.** La historia solo lee datos existentes.

## Entidades que se leen

| Entidad | Campos usados | Origen |
|---|---|---|
| `estudios.Estudio` | `pk`, `estado`, `tipo_nombre_snapshot`, `fecha_creacion`, `muestra` | US 5.1/5.2 |
| `muestras.Muestra` | `numero_pi`, `nombre`, `cliente`, `origen` | US 4.1 |
| `clientes.Cliente` | nombre o razón social, documento | US 2.1 |
| `estudios.PruebaEstudio` | `prueba` (código, nombre), `estado` | US 5.2/6.x |

## Valores calculados

- **Avance** (listado): `total_pruebas` y `pruebas_completadas` por estudio (anotaciones `Count`).
- **Motivo para no informar** (`informes.servicios.motivo_para_no_informar`), en este orden:

| Condición | Motivo | ¿Listo? |
|---|---|---|
| `estado == informe_generado` | «El informe de este estudio ya fue generado.» | No |
| sin asignaciones | «El estudio no tiene pruebas.» | No |
| alguna asignación ≠ `completada` | «Hay N pruebas sin completar.» | No |
| todas `completada` | — | **Sí** |

- **Bloqueo por prueba** (control):

| `PruebaEstudio.estado` | Etiqueta adicional | Bloquea |
|---|---|---|
| `pendiente` | «Incompleta» | Sí |
| `cargada` | «Sin validar» | Sí |
| `completada` | — | No |

## Transiciones

Ninguna. El paso a «Informe generado» es de US 7.2; `comprobar_generacion` solo verifica.
