# Data Model: Panel de calidad del agua

Sin tablas ni migraciones nuevas. La sección lee datos existentes y arma estructuras en memoria.

## Datos que se leen

| Modelo | Campos usados | Para qué |
|---|---|---|
| `estudios.Validacion` | `fecha_validacion`, `evaluacion`, `anulada`, `asignacion` | Resultado evaluado y su fecha (solo `anulada=False`) |
| `estudios.PruebaEstudio` | `prueba`, `estudio` | Puente a la prueba y a la muestra |
| `pruebas.Prueba` | `codigo`, `nombre` | Filas del ranking (nombre inmutable si está en uso) |
| `muestras.Muestra` | `tipo_vertido`, `cliente`, `origen` | Agrupar por vertido, cliente y origen |
| `clientes.Cliente` | `nombre_completo`, `activo` | Nombre y si lleva enlace al historial |
| `muestras.Origen` | `nombre`, `cliente` | Nombre, cliente y enlace a la comparación |

`Evaluacion` (`pruebas/limites.py`): `cumple`, `fuera_de_norma` (evaluados) y `sin_limite`
(contado aparte).

## Estructuras de `informes/calidad.py`

Constantes: `MINIMO_EVALUADOS_RANKING = 5`, `TOPE_LISTA = 10`.

### `Conteo`

| Campo | Tipo | Regla |
|---|---|---|
| `fuera` | int | Validaciones vigentes `fuera_de_norma` |
| `evaluados` | int | `cumple` + `fuera_de_norma` |
| `porcentaje` | `Decimal \| None` | `fuera * 100 / evaluados`, 1 decimal, `ROUND_HALF_UP`; `None` si `evaluados == 0` |
| `texto` | str (propiedad) | «20,0 % (2 de 10)»; «Sin resultados» sin evaluados |

Para el orden se usa la fracción exacta `fuera / evaluados` (no el porcentaje redondeado).

### `IndicadorCalidad`

| Campo | Tipo | Regla |
|---|---|---|
| `actual` | `Conteo` | Período elegido |
| `anterior` | `Conteo` | Período anterior del mismo `Periodo` (8.3) |
| `sin_limite` | int | Validaciones vigentes `sin_limite` del período |
| `variacion` | objeto con `tono`, `texto` \| None | `tablero.variacion(actual.porcentaje, anterior.porcentaje, favorable_si_sube=False)`; texto «▲ +5,0 p. p.»; `None` si falta alguno (el template distingue «sin datos previos») |

### Filas

- `FilaPrueba`: `codigo`, `nombre`, `conteo`. Solo con `evaluados >= MINIMO_EVALUADOS_RANKING` y
  `fuera >= 1`. Orden `(-fuera/evaluados, -fuera, codigo)`.
- `FilaVertido`: `valor`, `etiqueta`, `conteo`, `cumple` (= `evaluados - fuera`). Siempre Agua,
  Cloacal, Canal en el orden de `TipoVertido.choices`; `porcentaje_cumplimiento` = 100 − porcentaje
  de incumplimiento (calculado sobre `cumple`, mismo redondeo).
- `FilaCliente`: `cliente`, `conteo`, `url` (`clientes:historial` si `cliente.activo`, si no
  `None`). Solo `fuera >= 1`. Orden `(-fuera, -fuera/evaluados, nombre.casefold(), pk)`.
- `FilaOrigen`: `origen` (con `cliente`), `conteo`, `url` (`estudios:comparacion?cliente=&origen=`
  si el cliente está activo, si no `None`). Mismo filtro y orden que clientes (nombre del origen).

### `Lista`

`filas` (hasta `TOPE_LISTA`) y `restantes` (cuántas más cumplen la regla).

### `armar(periodo)` → dict del contexto `calidad`

```text
{
  "indicador": IndicadorCalidad,
  "pruebas": Lista[FilaPrueba],
  "vertidos": [FilaVertido ×3],
  "clientes": Lista[FilaCliente],
  "origenes": Lista[FilaOrigen],
  "minimo_ranking": MINIMO_EVALUADOS_RANKING,
  "graficos": {"calidad_pruebas": {...}, "calidad_vertidos": {...}},   # se suma a datos_graficos
}
```

Ninguna función escribe en la base.
