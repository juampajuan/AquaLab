# Data Model: Iniciar un estudio desde el asistente (US 10.3)

**Sin modelos ni migraciones nuevas.** Se usan sin cambios `Cliente`, `Origen`, `Muestra`,
`TipoEstudio` y `Estudio`. Todo lo nuevo vive en memoria durante una pregunta o en la URL.

## Pedido de registro (en memoria, por pregunta)

`asistente.registro.PedidoMuestra` (dataclass) arma una vuelta de `preparar_muestra`. Se
reconstruye en cada llamada a partir de los argumentos y nunca se guarda.

| Campo | Origen | Regla |
|---|---|---|
| `cliente` | `Cliente` activo | R3: `buscar_clientes`, exacta primero |
| `origen` / `origen_nuevo` | `Origen` del cliente / texto | R3; uno u otro, nunca los dos |
| `fecha_muestreo`, `fecha_ingreso` | `date` | R4: `leer_fecha` con la fecha del laboratorio |
| `tipo_estudio` / `solo_muestra` | `TipoEstudio` activo / bool | R3; con `solo_muestra` no hay tipo |
| `sitio_extraccion`, `tipo_vertido`, `nombre`, `responsable_muestreo` | texto | Solo si se dijeron; se precargan sin preguntar |

Estados derivados: `faltan` (datos sin decir), `problemas` (no coinciden o el formulario los
rechaza), `elegir` (qué opción falta elegir) y `listo` (sin faltantes ni problemas). Ver
[contracts/herramientas.md](contracts/herramientas.md).

`PedidoEstudio`: `muestra` (por N° PI) y `tipo_estudio` (activo).

## Enlace precargado (URL)

Parámetros GET de [contracts/enlaces-precargados.md](contracts/enlaces-precargados.md). Son
valores iniciales de un formulario: no reservan N° PI, no crean orígenes y no conceden permisos.

## Borrador de registro de muestra (sesión, existente)

`muestra_pendiente` en la sesión (US 4.1) suma una clave:

| Clave | Tipo | Uso |
|---|---|---|
| `tipo_estudio` | `int \| null` | Tipo pedido para el estudio siguiente; `registrar_muestra` lo ignora; `registrar_confirmar` lo usa para el enlace «Crear el estudio <tipo>» |

Los borradores viejos, sin la clave, se leen como `null`.

## Referencia (en memoria, `asistente/enlaces.py`)

| Campo nuevo | Tipo | Uso |
|---|---|---|
| `pk` | `int \| None` | `None` para pantallas sin pk (`registrar_muestra`, `crear_estudio`, `registrar_cliente`) y para opciones |
| `parametros` | `tuple[tuple[str, str], ...]` | Querystring (`urlencode`) del enlace precargado |
| `minimizar` | bool | El panel se minimiza al seguir el enlace (R7) |
| tipo `opcion` | — | Opción sin pantalla: botón sin URL ni ↗ |

`VISTAS` suma `registrar_muestra → muestras:registrar`, `crear_estudio → estudios:crear` y
`registrar_cliente → clientes:registrar`. `clave` pasa a ser `(tipo, pk, parametros, pregunta)`,
así dos opciones distintas sin pk no se toman como duplicadas.
