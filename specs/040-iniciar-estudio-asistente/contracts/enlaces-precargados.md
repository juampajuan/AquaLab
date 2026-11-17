# Contrato: formularios precargados por GET

Los parámetros son **solo valores iniciales** de un formulario sin enviar (R5). Nunca se crea
nada en el GET. Cada parámetro inválido se descarta en silencio (el campo queda como sin
precargar) y nunca produce un error de página. La misma URL armada a mano produce lo mismo.

## `GET muestras:registrar`

| Parámetro | Valor | Se descarta si… |
|---|---|---|
| `cliente` | pk | no es un entero o el cliente no existe o está inactivo |
| `origen` | pk | no hay cliente válido o el origen no es de ese cliente |
| `origen_nuevo` | texto ≤ 150 | viene junto con un `origen` válido |
| `fecha_muestreo`, `fecha_ingreso` | `aaaa-mm-dd` | no es una fecha válida |
| `sitio_extraccion` | texto ≤ 200 | se pasa del largo |
| `tipo_vertido` | `TipoVertido` | no es una de las opciones |
| `nombre` | texto ≤ 100 | se pasa del largo |
| `responsable_muestreo` | texto ≤ 150 | se pasa del largo |
| `tipo_estudio` | pk | no es un tipo activo |

- Saneo: `muestras.forms.valores_iniciales(query_dict) -> dict`, única función.
- Con `?volver=1` gana el borrador de la sesión, como hoy, y los demás parámetros se ignoran.
  Sin `volver=1`, el borrador anterior se descarta como en cualquier registro nuevo.
- Con un cliente precargado, la ficha y los orígenes los dibuja el servidor (como con
  `?volver=1`).
- `tipo_estudio` válido: campo oculto y la nota «Después de registrar la muestra se ofrecerá
  crear el estudio «<tipo>».», también en la pantalla de confirmación.
- Fechas no precargadas: el `initial` de siempre (hoy). El asistente siempre manda las dos.

## `POST muestras:registrar` / `registrar_confirmar`

- Sin cambios de validación. `tipo_estudio` inválido o inactivo en el POST se descarta (no da error
  de formulario); queda en el borrador como `tipo_estudio: <pk> | null`.
- Mensaje de éxito: el de siempre, más « <a>Crear el estudio <tipo></a>.» →
  `estudios:crear?muestra=<pk de la muestra>&tipo=<pk>` si el borrador tenía un tipo y sigue
  activo.

## `GET estudios:crear`

| Parámetro | Valor | Se descarta si… |
|---|---|---|
| `muestra` | pk | (como hoy) |
| `tipo` | pk | no es un tipo activo |

- Saneo: `estudios.forms.valores_iniciales_estudio(query_dict)`. Con `volver=<clave>` gana el
  borrador, como hoy.
