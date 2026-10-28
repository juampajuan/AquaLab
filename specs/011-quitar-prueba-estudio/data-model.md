# Data Model: Quitar prueba del estudio

**Feature**: `011-quitar-prueba-estudio` | **Plan**: [plan.md](./plan.md)

Sin cambios de esquema y **sin migraciones**. La historia usa las tablas de US 5.1 y la propiedad
`Estudio.admite_modificaciones` de [US 5.3](../010-agregar-prueba-estudio/data-model.md), y agrega
solo comportamiento.

## estudios.PruebaEstudio (existente)

| Elemento | Cambio |
|---|---|
| campos | Ninguno: `estudio` FK PROTECT (`related_name="pruebas_asignadas"`), `prueba` FK PROTECT, `estado` (`EstadoPruebaEstudio`, US 5.2), `UniqueConstraint(estudio, prueba)`. |
| `puede_quitarse()` | **Nuevo método**: `estado == EstadoPruebaEstudio.PENDIENTE`. `Cargada` (medición) y `Completada` (resultado) no se quitan (FR-004). |
| baja | `delete()` de la fila (Clarifications, FR-007). Una prueba quitada puede agregarse de nuevo (US 5.3) como fila nueva, con otro `pk`. |

## estudios.Estudio (existente)

Sin cambios. Usa `admite_modificaciones` de US 5.3 (FR-003). Muestra, tipo, estado, autor, fecha,
snapshots y clave no cambian al quitar pruebas (FR-008).

## pruebas.Prueba y estudios.TipoEstudio (existentes)

Sin cambios. Quitar una prueba de un estudio **no** modifica `TipoEstudioPrueba` ni
`TipoEstudio.version` (edge cases de la spec).

## Invariantes

| Regla | Dónde se garantiza |
|---|---|
| Al menos una prueba por estudio (FR-011) | `quitar_prueba` cuenta las asignaciones bajo el bloqueo del estudio |
| Solo estudios modificables cambian (FR-003) | `Estudio.admite_modificaciones`, revalidado en el servicio |
| No se quita una prueba con mediciones o resultados (FR-004) | `PruebaEstudio.puede_quitarse()` sobre la asignación bloqueada + `PROTECT` de las futuras tablas de mediciones |
| La cabecera del estudio no cambia (FR-008) | El servicio solo borra filas de `PruebaEstudio` |

## Estados

Sin transiciones nuevas.
