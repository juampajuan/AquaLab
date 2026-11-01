# Data Model: Cargar mediciones

**Feature**: `015-cargar-mediciones` | **Plan**: [plan.md](./plan.md)

Una migración nueva en `estudios` (`0004_medicion`): crea `Medicion`. `Estudio` y `PruebaEstudio`
no cambian de esquema; solo cambian sus valores de `estado`.

## 1. `estudios.Medicion` (nuevo)

| Campo | Tipo | Reglas |
|---|---|---|
| `asignacion` | `OneToOneField(PruebaEstudio, on_delete=PROTECT, related_name="medicion", editable=False)` | Una medición por prueba del estudio (FR-012). `PROTECT`: la asignación no se borra si tiene medición (US 5.4) |
| `valor` | `DecimalField(max_digits=18, decimal_places=6)` | Valor exacto ingresado; hasta 12 cifras enteras y 6 decimales; admite signo y cero |
| `decimales` | `PositiveSmallIntegerField` | Cantidad de decimales escritos (0–6), sale del exponente del `Decimal` leído |
| `unidad` | `CharField(max_length=50, blank=True, default="")` | Copia de `Prueba.unidad_medicion` al cargar; no cambia si después cambia el catálogo |
| `cargada_por` | `ForeignKey(AUTH_USER_MODEL, on_delete=PROTECT, related_name="mediciones_cargadas", editable=False)` | Usuario de la sesión |
| `fecha_carga` | `DateTimeField(auto_now_add=True)` | Fecha y hora de la carga |

**Constraints**: `CheckConstraint(decimales__lte=6, name="medicion_decimales_validos")`.

**Propiedad**: `valor_ingresado` → `valor.quantize(Decimal(1).scaleb(-decimales))`: el número tal
como se escribió (`7.20`, no `7.200000` ni `7.2`).

**`__str__`**: `"<asignacion> = <valor_ingresado> <unidad>"`.

Sin `ordering` propio: se lee siempre desde la asignación.

## 2. `estudios.Estudio` (existente)

- **Nueva propiedad** `admite_mediciones` → `estado in (PENDIENTE_ANALISIS, EN_PROCESO)` (R7).
- **Transición nueva** (FR-011): `pendiente_analisis` → `en_proceso` en la misma transacción que la
  primera medición guardada. Desde ahí `admite_modificaciones` es `False` (US 5.3/5.4 sin cambios).

```text
Pendiente de análisis ──(primera medición)──▶ En proceso ──(US 6.4)──▶ Finalizado ──▶ Informe generado
  admite_modificaciones                         admite_mediciones
  admite_mediciones
```

## 3. `estudios.PruebaEstudio` (existente)

- **Transición nueva** (FR-010): `pendiente` → `cargada` en la misma transacción que crea su
  `Medicion`. `Completada` queda para US 6.4.
- `puede_quitarse()` no cambia: una prueba `Cargada` ya no se puede quitar.
- Las pruebas calculadas (`prueba.es_calculada`) nunca reciben `Medicion` y siguen `pendiente` hasta
  US 6.2.

## 4. `pruebas.Prueba` (existente, solo lectura)

Se leen `codigo`, `nombre`, `unidad_medicion` (unidad que se muestra y se copia) y `es_calculada`
(prueba sin medición propia).

## Reglas de validación

| Regla | Dónde | Origen |
|---|---|---|
| Formato numérico con coma o punto, signo opcional, ≤ 12 enteros, ≤ 6 decimales | `leer_valor` (`estudios/mediciones.py`), usada por el formulario | FR-006, R4 |
| Al menos un valor por envío; si un valor es inválido no se guarda nada | `CargarMedicionesForm.clean()` | FR-005, FR-007 |
| Estudio en "Pendiente de análisis" o "En proceso" | `Estudio.admite_mediciones` (detalle, vista y servicio bajo bloqueo) | FR-003 |
| Solo pruebas `Pendiente`, no calculadas, que sigan en el estudio | servicio, bajo bloqueo de estudio y asignaciones | FR-004, FR-012 |
| Una medición por asignación | `OneToOneField` (base) | FR-012 |
| Decimales 0–6 | `CheckConstraint` | Clarifications |
