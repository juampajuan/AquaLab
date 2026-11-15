# Data Model: Curva de calibración para pruebas por absorbancia

Migraciones: `pruebas/0004_curvas_calibracion.py` (tipo `CURVA`, constraint, `CurvaCalibracion`,
`PuntoCurva`) y `estudios/0012_resultado_curva.py` (depende de `pruebas.0004`).

## Prueba (cambios)

| Cambio | Regla |
|---|---|
| `TipoCalculo.CURVA` = «Curva de calibración» | Tercera opción de `tipo_calculo` (cabe en `max_length=10`) |
| Constraint `prueba_formula_segun_tipo` | `(tipo ∈ {DIRECTO, CURVA} y formula = "")` o `(tipo = FORMULA y formula ≠ "")` |
| `clean()` | Con `CURVA`: sin fórmula, `unidad` obligatoria, `es_calculada = False` |
| `curva_vigente` (propiedad) | `curvas.filter(vigente=True).first()` |

Formulario (`PruebaForm`): propone «Abs» en `unidad_medicion` al elegir Curva si está vacía (en el
servidor, al limpiar). `gestionar_prueba` rechaza cambiar de `CURVA` a otro tipo si hay curvas (R12).

## CurvaCalibracion (nuevo, app `pruebas`)

| Campo | Tipo | Regla |
|---|---|---|
| `prueba` | FK `Prueba`, `CASCADE`, `related_name="curvas"` | Solo pruebas con tipo `CURVA` (servicio) |
| `fecha_preparacion` | fecha | Obligatoria, ≤ hoy (zona del laboratorio) |
| `observacion` | texto, opcional | |
| `archivo_origen` | texto (255), vacío | Nombre del archivo importado, sin ruta |
| `pendiente` | `numeric(24, 12)` | ≠ 0 (CheckConstraint) |
| `ordenada` | `numeric(24, 12)` | |
| `r2` | `numeric(11, 10)` | 0 ≤ R² ≤ 1 |
| `concentracion_min`, `concentracion_max` | `numeric(18, 6)` | De los puntos; muestran el rango |
| `absorbancia_min`, `absorbancia_max` | `numeric(18, 6)` | De los puntos; definen «fuera de rango» |
| `vigente` | booleano | `UniqueConstraint(prueba, condition=vigente)`: a lo sumo una vigente |
| `usada` | booleano, default `False` | Pasa a `True` con el primer resultado; nunca vuelve (R6) |
| `cargada_por` | FK usuario, `PROTECT` | |
| `fecha_carga` | fecha y hora | `timezone.now()` al confirmar |
| `clave` | UUID, `unique` | Del borrador; evita guardar dos veces la misma confirmación (R7) |

Orden por defecto: `-fecha_carga`, `-pk`. Propiedades: `r2_bajo` (`r2 < R2_MINIMO`),
`concentracion(absorbancia)` = `(absorbancia − ordenada) / pendiente`.

## PuntoCurva (nuevo, app `pruebas`)

| Campo | Tipo | Regla |
|---|---|---|
| `curva` | FK `CurvaCalibracion`, `CASCADE`, `related_name="puntos"` | |
| `orden` | entero ≥ 1 | `UniqueConstraint(curva, orden)`; orden de carga |
| `concentracion` | `numeric(18, 6)` | ≥ 0; escrita con `leer_valor` |
| `absorbancia` | `numeric(18, 6)` | ≥ 0; escrita con `leer_valor` |

Al menos 3 por curva (servicio); réplicas (concentración repetida) permitidas.

## Resultado (cambios, app `estudios`)

| Campo | Tipo | Regla |
|---|---|---|
| `curva` | FK `CurvaCalibracion`, `PROTECT`, nula, `related_name="resultados"` | Con la que se calculó; nula si la prueba no es por curva. `formula` queda vacía |

## Estados de una curva

```text
(nueva) ──confirmar──▶ vigente ──otra confirmada──▶ histórica
   vigente / histórica, usada=False ──borrar──▶ (borrada; si era vigente, la anterior más reciente vuelve a vigente)
   usada=True: no se borra; no hay edición en ningún estado
```

## Reglas de cálculo

| Situación | Curva usada |
|---|---|
| Primera carga de la medición | Vigente (si no hay → «Falta curva de calibración.», sin resultado) |
| Corrección o recálculo por dependencias con resultado existente | `resultado.curva` (aunque haya otra vigente) |
| Corrección sin resultado previo (esperaba curva) | Vigente |
| Medición borrada y vuelta a cargar | Vigente (el resultado se descartó) |
| «Calcularlas con esta curva» al confirmar | La curva nueva |
| «Calcular con la curva vigente» desde el estudio (R14) | Vigente de cada prueba |

Motivos sin resultado de una prueba por curva con medición: sin vigente → «Falta curva de
calibración.»; con vigente → «Se cargó antes de la curva vigente.» (`curvas.motivo_curva`).
