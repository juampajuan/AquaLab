# Data Model: Agregar y quitar pruebas de un estudio

**Feature**: `009-gestionar-pruebas-estudio` | **Plan**: [plan.md](./plan.md)

Sin cambios de esquema y **sin migraciones**. La historia usa las tablas entregadas por US 5.1
(ver [data-model de US 5.1](../008-crear-estudio/data-model.md)) y agrega solo comportamiento.

## estudios.Estudio (existente)

| Elemento | Cambio |
|---|---|
| campos | Ninguno. Muestra, tipo, estado, autor, fecha, snapshots y clave no cambian al agregar o quitar pruebas (FR-011). |
| `admite_modificaciones` | **Nueva propiedad**. `True` solo si `estado == "pendiente_analisis"` (FR-003). Los estados que agreguen historias futuras quedan bloqueados salvo que su historia diga lo contrario. |

## estudios.PruebaEstudio (existente)

| Elemento | Cambio |
|---|---|
| campos | Ninguno: `estudio` FK PROTECT (`related_name="pruebas_asignadas"`), `prueba` FK PROTECT, `UniqueConstraint(estudio, prueba)` (FR-005). |
| `puede_quitarse()` | **Nuevo método**. Hoy devuelve `True`. US 6.1 y siguientes deben devolver `False` si la asignación tiene mediciones o resultados (FR-007). |
| alta | Una fila nueva por prueba agregada; queda pendiente de realizar igual que las precargadas (FR-006). No hay campo de origen (precargada o agregada) porque la spec no lo pide. |
| baja | `delete()` de la fila (Clarifications Q2, FR-010). Una prueba quitada puede agregarse de nuevo como fila nueva. |

## pruebas.Prueba y estudios.TipoEstudio (existentes)

Sin cambios. Agregar o quitar pruebas de un estudio **no** modifica `TipoEstudioPrueba` ni
`TipoEstudio.version` (edge cases de la spec).

## Invariantes

| Regla | Dónde se garantiza |
|---|---|
| Una prueba a lo sumo una vez por estudio | `UniqueConstraint` + comprobación en `agregar_prueba` bajo el bloqueo del estudio |
| Al menos una prueba por estudio (FR-014) | `quitar_prueba` cuenta las asignaciones bajo el bloqueo del estudio |
| Solo estudios modificables cambian (FR-003) | `Estudio.admite_modificaciones`, revalidado en el servicio |
| No se quita una prueba con mediciones o resultados (FR-007) | `PruebaEstudio.puede_quitarse()` + `PROTECT` de las futuras tablas de mediciones |
| La cabecera del estudio no cambia (FR-011) | Los servicios solo crean o borran filas de `PruebaEstudio` |

## Estados

Sin transiciones nuevas. `Pendiente de análisis` es el único estado y admite modificaciones.
