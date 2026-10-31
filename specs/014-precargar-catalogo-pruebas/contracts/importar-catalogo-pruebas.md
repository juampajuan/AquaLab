# Contrato: comando `importar_catalogo_pruebas`

Archivo: `pruebas/management/commands/importar_catalogo_pruebas.py`. La lógica está en
`pruebas/importacion.py` (`importar(ruta_catalogo, ruta_limites) -> Resumen`).

## Uso

```text
python manage.py importar_catalogo_pruebas [--catalogo RUTA] [--limites RUTA]
```

| Opción | Default |
|---|---|
| `--catalogo` | `pruebas/datos/catalogo_pruebas_agua.csv` (resuelto desde `BASE_DIR`) |
| `--limites` | `pruebas/datos/limites_vertido.csv` |

## Formato de entrada

UTF-8 (se acepta BOM), separado por coma y con encabezado. Las columnas de más se ignoran; si falta
una obligatoria se rechaza el archivo.

- **Catálogo**: `codigo,nombre,unidad,unidad_medicion,tipo_calculo,formula,es_calculada,norma,
  limite_min,limite_max,limite_deteccion,activa,observacion`
- **Límites**: `codigo,tipo_vertido,limite_min,limite_max,norma`

Los valores se recortan con `strip()`. `es_calculada` y `activa` aceptan `si` o `no`, sin distinguir
mayúsculas. `tipo_calculo` acepta `DIRECTO` o `FORMULA`, y `tipo_vertido` acepta `cloacal` o `canal`.

## Salida exitosa (código 0)

```text
Catálogo importado: 90 pruebas (90 creadas, 0 actualizadas) y 18 límites por tipo de vertido (18 creados, 0 actualizados).
```

Si hubo avisos (nombre distinto de una prueba en uso), se agregan después, uno por línea, con
`self.stdout.write(self.style.WARNING(...))`:

```text
Aviso: la prueba PH está en uso; se conserva el nombre «pH» (el archivo dice «pH del agua»).
```

"Actualizadas" cuenta las filas existentes que vuelven a escribirse, aunque no cambie ningún valor;
volver a correr la importación con los mismos archivos informa `0 creadas`.

## Errores (código distinto de 0, `CommandError`, sin cambios en la base)

```text
No se importó nada: el archivo tiene 2 errores.
catalogo_pruebas_agua.csv, línea 7: tipo de cálculo «CURVA» inválido (DIRECTO o FORMULA).
limites_vertido.csv, línea 3: la prueba «XX» no existe en el catálogo.
```

| Caso | Mensaje (motivo) |
|---|---|
| Archivo inexistente o ilegible | `no se puede leer <ruta>` |
| Falta una columna obligatoria | `faltan las columnas: <lista>` |
| Código vacío o nombre vacío | Mensaje de `full_clean` del campo |
| Código repetido en el catálogo | `el código «X» está repetido (también en la línea N)` |
| `(codigo, tipo_vertido)` repetido en límites | `límite repetido para «X» (<tipo>)` |
| Valor sí/no inválido | `<columna>: «V» inválido (si o no)` |
| Tipo de cálculo o de vertido inválido | `tipo de cálculo «V» inválido (DIRECTO o FORMULA)` / `tipo de vertido «V» inválido (cloacal o canal)` |
| Fórmula incoherente con el tipo o con `es_calculada` | Mensaje de `full_clean` (R3) |
| Referencia `{X}` inexistente | `la fórmula referencia «X», que no existe en el catálogo` |
| Límite de un código inexistente | `la prueba «X» no existe en el catálogo` |
| Texto más largo que el máximo | Mensaje de `full_clean` del campo |

## Garantías

- Es idempotente (FR-007): repetir la importación con los mismos archivos no cambia cantidades ni
  valores.
- Es todo o nada (FR-009): o se valida y se escribe todo, o no se escribe nada.
- Nunca borra ni desactiva pruebas ni límites (FR-008), y no toca asignaciones de tipos de estudio o
  estudios.
