# Data Model: Precargar el catálogo de pruebas de agua

App `pruebas`. Migración `pruebas/migrations/0002_catalogo_pruebas.py` (solo `AddField`, `CreateModel`
y `AddConstraint`, sin migración de datos). Decisiones en [research.md](./research.md).

## TipoCalculo (`TextChoices`)

| Valor | Etiqueta |
|---|---|
| `DIRECTO` | Directo |
| `FORMULA` | Fórmula |

## TipoVertido (`TextChoices`)

| Valor | Etiqueta |
|---|---|
| `cloacal` | Cloacal |
| `canal` | Canal |

## Prueba (modelo existente, ampliado)

| Campo | Tipo | Default | Columna CSV | Notas |
|---|---|---|---|---|
| `codigo` | `CharField(50, unique)` | — | `codigo` | Existente. Obligatorio, sin espacios laterales |
| `nombre` | `CharField(150)` | — | `nombre` | Existente. Obligatorio |
| `unidad` | `CharField(50, blank)` | `""` | `unidad` | Unidad del resultado |
| `unidad_medicion` | `CharField(50, blank)` | `""` | `unidad_medicion` | |
| `tipo_calculo` | `CharField(10, choices=TipoCalculo)` | `DIRECTO` | `tipo_calculo` | |
| `formula` | `CharField(255, blank)` | `""` | `formula` | Texto sin evaluar. `x` = valor medido; `{CODIGO}` = resultado de otra prueba |
| `es_calculada` | `BooleanField` | `False` | `es_calculada` (`si`/`no`) | Se calcula a partir de otras pruebas |
| `norma` | `CharField(150, blank)` | `""` | `norma` | |
| `limite_min` | `CharField(50, blank)` | `""` | `limite_min` | Texto tal cual |
| `limite_max` | `CharField(50, blank)` | `""` | `limite_max` | Texto tal cual |
| `limite_deteccion` | `CharField(50, blank)` | `""` | `limite_deteccion` | Texto tal cual |
| `activa` | `BooleanField` | `True` | `activa` (`si`/`no`) | |
| `observacion` | `TextField(blank)` | `""` | `observacion` | Nota interna |

**Restricciones (base de datos)**:

- Existentes: `prueba_codigo_no_vacio`, `prueba_nombre_no_vacio`.
- `prueba_formula_segun_tipo`: `(tipo_calculo=DIRECTO y formula="")` o `(tipo_calculo=FORMULA y
  formula<>"")`.
- `prueba_calculada_es_formula`: `es_calculada=False` o `tipo_calculo=FORMULA`.

**Validación (`clean`)**:

- `strip()` en todos los textos. Ya se hacía en `codigo` y `nombre`; `save()` también lo aplica.
- `es_calculada` es verdadero si y solo si `referencias_formula(formula)` no está vacío.
- La fórmula no puede referenciar el código de la propia prueba.

**Métodos**:

- `esta_en_uso() -> bool`: tiene algún `TipoEstudioPrueba` o algún `PruebaEstudio`.
- Función de módulo `referencias_formula(formula) -> set[str]`.

**Relaciones existentes (sin cambios)**: `estudios.TipoEstudioPrueba.prueba` y
`estudios.PruebaEstudio.prueba`, ambas con `PROTECT`.

## LimiteVertido (nuevo)

| Campo | Tipo | Columna CSV | Notas |
|---|---|---|---|
| `prueba` | `ForeignKey(Prueba, CASCADE, related_name="limites_vertido")` | `codigo` | El código debe existir en el catálogo resultante |
| `tipo_vertido` | `CharField(10, choices=TipoVertido)` | `tipo_vertido` | |
| `limite_min` | `CharField(50, blank, default="")` | `limite_min` | Texto tal cual |
| `limite_max` | `CharField(50, blank, default="")` | `limite_max` | Texto tal cual |
| `norma` | `CharField(150, blank, default="")` | `norma` | |

- `UniqueConstraint(prueba, tipo_vertido)` con el nombre `limite_vertido_unico`.
- `CASCADE`: es dato de referencia de la prueba, y una prueba solo puede borrarse si no está en uso.
- `Meta.ordering = ("prueba__codigo", "tipo_vertido")`; `__str__`: `"<codigo> · <Tipo de vertido>"`.

## Identidad en la importación

| Entidad | Clave | Si existe | Si no existe | Si no está en el archivo |
|---|---|---|---|---|
| Prueba | `codigo` | Se actualizan los campos (excepto `nombre` si está en uso: aviso) | Se crea | No se toca |
| LimiteVertido | (`codigo`, `tipo_vertido`) | Se actualizan los campos | Se crea | No se toca |
