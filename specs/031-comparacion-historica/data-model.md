# Data Model: Comparación histórica por origen (SCRUM-60, US 8.1)

**Sin tablas ni migraciones nuevas.** Todo se deriva de `Muestra`, `PruebaEstudio`, `Resultado`
y `Validacion`. Las estructuras de abajo son `dataclass(frozen=True)` de
`estudios/comparacion.py` (R1), que reutiliza la US 8.2.

## Fuentes existentes

| Modelo | Campos usados | Para |
|---|---|---|
| `muestras.Origen` | `pk`, `nombre`, `cliente` | agrupar el historial |
| `muestras.Muestra` | `origen`, `fecha_muestreo`, `numero_pi`, `tipo_vertido` | orden (R3), límites (R6) |
| `estudios.Estudio` | `pk`, `muestra`, `estado`, `tipo_nombre_snapshot` | referencia y enlaces |
| `estudios.PruebaEstudio` | `estado` (`completada` ⇔ validada), `prueba` | filtro del historial (R2) |
| `estudios.Resultado` | `valor` (10 decimales), `unidad`, `valor_mostrado` | valores |
| `estudios.Validacion` | vigente: `limite_min/max`, `norma`, `origen_limites`, `evaluacion` | evaluación de cada punto |
| `pruebas.Prueba` | `codigo`, `nombre`, `limite_deteccion`, `limites_vertido` | identidad y franja |

## Punto

Un resultado en el gráfico y en la tabla «Ver datos».

| Campo | Tipo | Regla |
|---|---|---|
| `fecha_muestreo` | `date` | de la muestra |
| `numero_pi` | `int` | de la muestra; enlace a `muestras:detalle` |
| `estudio_pk` | `int` | enlace a `estudios:detalle` |
| `valor` | `Decimal` | `Resultado.valor` completo (FR-011) |
| `texto` | `str` | «< LD», «Ausente»/«Presente» o `valor_mostrado` con coma |
| `unidad` | `str` | `Resultado.unidad` |
| `validado` | `bool` | asignación Completada |
| `evaluacion` | `Evaluacion` | la de la validación vigente; sin validar, `evaluar` con el catálogo |
| `es_referencia` | `bool` | es el resultado del estudio de referencia |
| `otra_unidad` | `bool` | `unidad` ≠ unidad de referencia → fuera de gráfico y variación (FR-020) |
| `orden` | tupla | `(fecha_muestreo, numero_pi, estudio_pk)` (R3) |

## Franja

| Campo | Tipo | Regla |
|---|---|---|
| `limites` | `LimitesAplicables` | `limites_aplicables(prueba, muestra_ref.tipo_vertido)` |
| `minimo`, `maximo` | `Decimal \| None` | `leer_limite`; `AUSENTE` → `presencia=True` |
| `comparable` | `bool` | `False` si algún borde es `NO_COMPARABLE` o no hay bordes |
| `texto` | `str` | p. ej. «Máximo 350 mg/l · Límite general» o «Sin límite comparable» |

## Variacion

| Campo | Tipo | Regla |
|---|---|---|
| `ultimo` | `Punto` | referencia (si tiene resultado) o validado más reciente |
| `anterior` | `Punto` | el último de `anteriores` |
| `cantidad_anteriores` | `int` | ≥ 1 (sin anteriores no hay `Variacion`) |
| `promedio` | `Decimal \| None` | media simple de `anteriores` (`None` en presencia) |
| `contra_anterior`, `contra_promedio` | `Cambio \| None` | `None` en presencia |
| `cambio_presencia` | `str \| None` | «Sin cambios (Ausente)» / «Cambió: Ausente → Presente» |
| `presentes` | `int \| None` | cuántos anteriores fueron Presente |

`Cambio`: `diferencia: Decimal`, `porcentaje: Decimal | None` (1 decimal; `None` si la base es 0),
`flecha` («▲», «▼», «=»), `texto` («+15 mg/l (+3,6 %)», «+5 mg/l (sin porcentaje: valor previo 0)»).

## HistorialPrueba

Lo que devuelve `comparar()` por prueba, en el orden de FR-013.

| Campo | Tipo | Regla |
|---|---|---|
| `prueba` | `Prueba` | |
| `presencia` | `bool` | `es_presencia(unidad)` |
| `unidad` | `str` | de la referencia; si no, del último validado |
| `puntos` | `list[Punto]` | validados del origen + el de referencia, ordenados (FR-003, FR-004) |
| `referencia` | `Punto \| None` | resultado del estudio de referencia |
| `sin_resultado` | `bool` | hay estudio de referencia y esa prueba no tiene resultado |
| `tiene_historial` | `bool` | algún validado (sin contar la referencia) con la misma unidad |
| `franja` | `Franja` | |
| `variacion` | `Variacion \| None` | FR-008 |
| `fuera_de_franja` | `bool` | el último está fuera de norma (solo para el color) |

## Formularios (`estudios/forms.py`)

- **`ElegirOrigenForm`**: `cliente` (`ModelChoiceField`, clientes activos), `origen`
  (`ModelChoiceField`, todos; `clean()` exige `origen.cliente == cliente`, error en `origen`:
  «El origen no pertenece al cliente elegido.»). Con `help_text` en los dos campos (US 9.1).
- **`ElegirPruebasForm`**: `pruebas` (`MultipleChoiceField`, `CheckboxSelectMultiple`, opciones =
  códigos disponibles con su nombre, `required=False`), `elegir` (`HiddenInput`). Con `elegir` y
  sin pruebas → error «Elegí al menos una prueba para ver su evolución.»; sin `elegir` → todas.

## Reglas de estado

Solo lectura: ninguna transición. La pantalla no llama a servicios ni bloqueos (FR-016).
