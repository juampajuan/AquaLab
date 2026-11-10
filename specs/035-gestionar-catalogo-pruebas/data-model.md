# Data Model: Gestionar catálogo de pruebas

## Prueba (cambios)

| Campo | Tipo | Regla |
|---|---|---|
| `reemplazada_por` | FK `Prueba`, `PROTECT`, nulo | Prueba que la reemplazó al desactivarla (R11) |
| `version` | entero ≥ 1, default 1 | Sube en cada operación de `gestionar_prueba`; concurrencia optimista |
| `creada_por` | FK usuario, `PROTECT`, nulo | Quién la creó desde la app; nulo en existentes/importadas |
| `fecha_creacion` | fecha y hora, nula | Cuándo |
| `modificada_por` | FK usuario, `PROTECT`, nulo | Última edición, desactivación o reactivación |
| `fecha_modificacion` | fecha y hora, nula | Cuándo |

Sin cambios: código, nombre, unidades, tipo de cálculo, fórmula, `es_calculada` (se deduce de la
fórmula), norma, límites generales, límite de detección, observación, activa. `LimiteVertido`
(cloacal y canal: mín, máx, norma) sin cambios.

## Reglas por estado

| Situación | Editable | Eliminar | Desactivar |
|---|---|---|---|
| Sin uso y sin dependientes | Todo | Sí | Sí |
| Sin uso con dependientes | Todo menos el código | No (lista dependientes) | Sí, con aviso |
| En uso | Límites (generales y vertido), norma, LD, observación | No | Sí, con avisos (dependientes y tipos) |

«En uso» = `Prueba.esta_en_uso()` (tipo de estudio o estudio). «Dependientes» = pruebas cuya fórmula
referencia `{CODIGO}` de esta.

## Reemplazo (desactivar con «Reemplazar por»)

| Paso | Efecto |
|---|---|
| Validar candidata | Activa, misma `unidad` del resultado, distinta, no la referencia directa ni indirectamente |
| Prueba vieja | `activa=False`, `reemplazada_por=nueva`, auditoría, `version += 1` |
| Pruebas dependientes | `{VIEJO}` → `{NUEVO}` en la fórmula, `full_clean()`, `version += 1` |
| Tipos de estudio | vieja → nueva (o se quita la vieja si ya estaba la nueva), `version += 1` |
| Estudios anteriores | Sin cambios; al recalcular, `{NUEVO}` se resuelve con la asignación de la vieja |

## Validación de límites

Mín y máx (generales y por vertido): vacío, número (coma o punto) o «Ausente»/«Ausencia». Otro
texto → «Escribí un número o “Ausente”». Si ambos son números: mín ≤ máx → si no, «El mínimo no
puede superar al máximo».

## Efecto de `activa = False`

| Lugar | Comportamiento |
|---|---|
| Armar o editar tipo de estudio | No se ofrece; las que el tipo ya tiene se conservan marcadas |
| Agregar prueba a un estudio | No se ofrece; el servicio la rechaza |
| Crear estudio | Se asignan solo las activas del tipo; sin ninguna → error |
| Estudios existentes | Sin cambios: carga, cálculo, corrección, validación, informe |
| Listado del catálogo | «Inactiva»; las activas que la referencian se marcan |
