# Data Model: Modificar las mediciones

**Feature**: `017-modificar-mediciones` | **Plan**: [plan.md](./plan.md)

Una migración nueva en `estudios` (`0006_medicion_correccion`): dos campos en `Medicion`.

## 1. `estudios.Medicion` (existente, US 6.1) — campos nuevos

| Campo | Tipo | Reglas |
|---|---|---|
| `corregida_por` | `ForeignKey(AUTH_USER_MODEL, null=True, blank=True, on_delete=PROTECT, related_name="mediciones_corregidas", editable=False)` | Último empleado que la corrigió; `NULL` si nunca se corrigió |
| `fecha_correccion` | `DateTimeField(null=True, blank=True)` | Fecha y hora de la última corrección; `NULL` si nunca se corrigió |

Al corregir se actualizan `valor`, `decimales` (con las reglas de `leer_valor`, US 6.1),
`corregida_por` y `fecha_correccion`. `cargada_por`, `fecha_carga` y `unidad` no cambian.
No hay historial de valores anteriores (Clarifications).

**Constraint nuevo** `medicion_correccion_completa`: los dos campos van juntos,
`Q(corregida_por__isnull=True, fecha_correccion__isnull=True) |
Q(corregida_por__isnull=False, fecha_correccion__isnull=False)`.

## 2. `estudios.Estudio` (existente) — transición nueva

| Desde | Hacia | Cuándo |
|---|---|---|
| `finalizado` | `en_proceso` | Una corrección deja alguna prueba del estudio fuera de `completada` (FR-008) |

Regla de corrección: `Estudio.admite_correcciones` (US 6.2): todo estado salvo
`informe_generado`.

## 3. `estudios.PruebaEstudio` y `estudios.Resultado` (existentes)

Sin cambios de esquema. Las transiciones al recalcular (`completada` → `cargada`, calculada →
`pendiente` si ya no se puede calcular) las aplica `calculo.recalcular` (US 6.2).

## Reglas de validación

| Regla | Dónde | Origen |
|---|---|---|
| Formato del valor corregido | `leer_valor` (US 6.1) en `CorregirMedicionesForm` | FR-004 |
| Campo vacío rechazado | `CorregirMedicionesForm` (campo obligatorio) | FR-004 |
| Al menos un cambio | `CorregirMedicionesForm.clean()` | US2 Esc. 4 |
| Sin informe emitido | `Estudio.admite_correcciones`, bajo bloqueo en el servicio | FR-009 |
| Valor vigente igual al original al confirmar | servicio, bajo bloqueo | FR-010 |
| Corrección y recálculo en una transacción | servicio + `recalcular_resultados` | FR-007 |
| Quién y cuándo corrigió, juntos | `CheckConstraint` | FR-006 |
