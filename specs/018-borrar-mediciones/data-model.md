# Data Model: Borrar mediciones

**Feature**: `018-borrar-mediciones` | **Plan**: [plan.md](./plan.md)

**Sin cambios de esquema ni migraciones.** Se borran filas existentes de `estudios.Medicion` y
`estudios.Resultado` y cambian estados.

## 1. `estudios.Medicion` (US 6.1/6.3)

- Se borra la fila completa. No hay historial (US 6.3), así que no queda rastro del valor.
- `PruebaEstudio` → `Medicion` es uno a uno; sin medición, la asignación vuelve a ofrecerse en
  `cargar_mediciones` (filtra pendientes no calculadas, US 6.1).

## 2. `estudios.Resultado` (US 6.2)

- El de la prueba borrada y los de sus dependientes que ya no se pueden calcular los borra
  `calculo.descartar` dentro de `recalcular`.

## 3. Transiciones

### `PruebaEstudio`

| Desde | Hacia | Cuándo |
|---|---|---|
| `cargada` o `completada` | `pendiente` | Se borra su medición |
| `cargada` o `completada` (calculada) | `pendiente` | Pierde una referencia por un borrado (US 6.2) |

### `Estudio`

| Desde | Hacia | Cuándo |
|---|---|---|
| `en_proceso` o `finalizado` | `pendiente_analisis` | Después del envío no queda ninguna prueba `cargada` ni `completada` |
| `finalizado` | `en_proceso` | Quedan pruebas `cargada`/`completada` pero no todas `completada` (US 6.3) |

`informe_generado` no admite borrados (`Estudio.admite_correcciones`, US 6.2).

## Reglas de validación

| Regla | Dónde | Origen |
|---|---|---|
| Fila marcada «Borrar» no se valida y prevalece | `CorregirMedicionesForm.clean()` | FR-003 |
| Campo vacío sin «Borrar» → error | `CorregirMedicionesForm.clean()` | US 6.3 |
| Un borrado cuenta como cambio | `CorregirMedicionesForm.cambios()` | FR-003 |
| Sin informe emitido | servicio, bajo bloqueo | FR-008 |
| Original igual al vigente; medición existente | servicio, bajo bloqueo | FR-009 |
| Todo el envío en una transacción | servicio + `recalcular_resultados` | FR-011 |
