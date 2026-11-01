# Data Model: Cálculo automático del resultado

**Feature**: `016-calcular-resultado` | **Plan**: [plan.md](./plan.md)

Una migración nueva en `estudios` (`0005_resultado`): crea `Resultado`. `Medicion`, `Estudio` y
`PruebaEstudio` no cambian de esquema. `pruebas.Prueba` no cambia de esquema (solo su `clean()`).

## 1. `estudios.Resultado` (nuevo)

| Campo | Tipo | Reglas |
|---|---|---|
| `asignacion` | `OneToOneField(PruebaEstudio, on_delete=PROTECT, related_name="resultado", editable=False)` | Un resultado por prueba del estudio. `PROTECT`: no se borra la asignación con resultado |
| `valor` | `DecimalField(max_digits=28, decimal_places=10)` | Valor calculado completo (redondeado a 10 decimales, `ROUND_HALF_UP`); puede ser negativo o cero |
| `unidad` | `CharField(max_length=50, blank=True, default="")` | Copia de `Prueba.unidad` (unidad del resultado) al calcular |
| `formula` | `CharField(max_length=255, blank=True, default="")` | Copia de `Prueba.formula` al calcular; vacía para tipo Directo |
| `fecha_calculo` | `DateTimeField(auto_now=True)` | Última vez que se calculó |

**Propiedad**: `valor_mostrado` → `valor` redondeado a 4 decimales (`ROUND_HALF_UP`), sin ceros
finales y sin `-0` (Clarifications).

**`__str__`**: `"<asignacion> = <valor_mostrado> <unidad>"` sin espacio final.

Sin fila = sin resultado. El motivo de una prueba sin resultado no se guarda (research R4).

## 2. `estudios.Estudio` (existente)

- **Nueva propiedad** `admite_correcciones` → `estado != EstadoEstudio.INFORME_GENERADO`.
  Mediciones y resultados se pueden cambiar (y recalcular) hasta que se emite el informe.

## 3. `estudios.PruebaEstudio` (existente) — transiciones nuevas

| Desde | Hacia | Cuándo |
|---|---|---|
| `pendiente` (calculada) | `cargada` | Obtiene su resultado (FR-003) |
| `cargada` (calculada) | `pendiente` | Un recálculo ya no la puede calcular (se borra su resultado) |
| `completada` | `cargada` | Se recalcula por una medición corregida antes del informe: pierde la validación (FR-009) |

Una prueba medida queda `cargada` con o sin resultado (tiene medición, US 6.1).

## 4. `pruebas.Prueba` (existente)

`clean()` suma `validar_formula(self.formula)` para las de tipo Fórmula: una fórmula que no se
podría evaluar se rechaza en el admin y en la importación (research R1).

## Gramática de fórmulas (`pruebas/formulas.py`)

```text
expresion := termino (("+" | "-") termino)*
termino   := factor (("*" | "/") factor)*
factor    := ("+" | "-") factor | numero | "x" | "{" CODIGO "}" | "sqrt" "(" expresion ")" | "(" expresion ")"
numero    := \d+ ("." \d+)?
CODIGO    := uno o más caracteres distintos de "{" y "}" (se recortan espacios)
```

Espacios permitidos entre tokens. Cualquier otro carácter o estructura → `FormulaInvalida`.

## Reglas de validación

| Regla | Dónde | Origen |
|---|---|---|
| Fórmula con la gramática admitida | `validar_formula` en `Prueba.clean()` | FR-002 |
| Evaluación exacta con `Decimal`, sin `float` | `evaluar_formula` | FR-002, principio IV |
| Una prueba se calcula solo con sus referencias resueltas en el mismo estudio | `estudios.calculo` | FR-003, FR-006 |
| Solo se recalculan las afectadas por un cambio, en orden de dependencia | `recalcular` | FR-008 |
| Sin cambios con informe emitido | `Estudio.admite_correcciones` en `recalcular_resultados`, bajo bloqueo | FR-009 |
| Un resultado por asignación | `OneToOneField` | R2 |
