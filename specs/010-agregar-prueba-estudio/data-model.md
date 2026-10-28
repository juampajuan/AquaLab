# Data Model: Agregar prueba al estudio

**Feature**: `010-agregar-prueba-estudio` | **Plan**: [plan.md](./plan.md)

Sin cambios de esquema y **sin migraciones**. La historia usa las tablas entregadas por US 5.1
(ver [data-model de US 5.1](../008-crear-estudio/data-model.md)) y agrega solo comportamiento.

## estudios.Estudio (existente)

| Elemento | Cambio |
|---|---|
| campos | Ninguno. Muestra, tipo, estado, autor, fecha, snapshots y clave no cambian al agregar pruebas (FR-009). |
| `admite_modificaciones` | **Nueva propiedad**. `True` solo si `estado == "pendiente_analisis"` (FR-003). La usa también US 5.4. Los estados que agreguen historias futuras quedan bloqueados salvo que su historia diga lo contrario. |

## estudios.PruebaEstudio (existente)

| Elemento | Cambio |
|---|---|
| campos | Ninguno: `estudio` FK PROTECT (`related_name="pruebas_asignadas"`), `prueba` FK PROTECT, `UniqueConstraint(estudio, prueba)` llamada `estudio_prueba_unica` (FR-005). |
| alta | Una fila nueva por prueba agregada; queda pendiente de realizar igual que las precargadas (FR-006). No hay campo de origen (precargada o agregada) porque la spec no lo pide. |

## pruebas.Prueba y estudios.TipoEstudio (existentes)

Sin cambios. Agregar pruebas a un estudio **no** modifica `TipoEstudioPrueba` ni
`TipoEstudio.version` (edge cases de la spec).

## Invariantes

| Regla | Dónde se garantiza |
|---|---|
| Una prueba a lo sumo una vez por estudio | `UniqueConstraint` + comprobación en `agregar_prueba` bajo el bloqueo del estudio |
| Solo estudios modificables cambian (FR-003) | `Estudio.admite_modificaciones`, revalidado en el servicio |
| La cabecera del estudio no cambia (FR-009) | El servicio solo crea filas de `PruebaEstudio` |

## Estados

Sin transiciones nuevas. `Pendiente de análisis` es el único estado y admite modificaciones.
