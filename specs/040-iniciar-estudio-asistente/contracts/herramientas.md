# Contrato: herramientas `preparar_muestra` y `preparar_estudio`

Se registran con `@registrar` en `asistente/herramientas.py` (o en un módulo
`asistente/registro.py` importado desde ahí) y corren como las de la 10.1: con el usuario que
pregunta, dentro de la transacción `READ ONLY` que siempre se deshace. Los argumentos se validan
con `argumentos_validos` (tipos JSON, sin claves de más).

## `preparar_muestra`

Descripción para el modelo: «Prepara el registro de una muestra. Llamala con **todos** los datos
que el empleado dijo hasta ahora en la conversación, como texto, aunque ya la hayas llamado.
AquaLab los busca en el sistema y dice qué falta o qué no coincide. No crea nada: cuando está
todo, AquaLab agrega el enlace al formulario».

| Argumento | Tipo | Notas |
|---|---|---|
| `cliente` | string | Nombre o razón social, como lo dijo el empleado |
| `origen` | string | «pozo 2», «tanque» |
| `origen_nuevo` | boolean | `true` solo si el empleado eligió «Registrarlo como origen nuevo» |
| `fecha_muestreo` | string | Texto tal cual: «ayer», «12/11», «2026-11-12» |
| `fecha_ingreso` | string | Ídem |
| `tipo_estudio` | string | Nombre del tipo |
| `solo_muestra` | boolean | `true` si eligió «Solo registrar la muestra» |
| `sitio_extraccion`, `tipo_vertido`, `nombre`, `responsable_muestreo` | string | Opcionales; solo si se dijeron |

Ninguno es obligatorio: sin argumentos devuelve todo en `faltan`.

### Salida (`datos`, lo que ve el modelo)

```json
{
  "encontrado": true,
  "listo": false,
  "resuelto": {"cliente": "Lácteos del Sur S.A.", "origen": "Pozo 2",
               "tipo_estudio": "Físico-químico básico"},
  "faltan": ["fecha de muestreo", "fecha de ingreso"],
  "problemas": [],
  "elegir": null
}
```

- `resuelto`: solo nombres (lista blanca, R9). Las fechas como `dd/mm/aaaa`; el origen nuevo
  como «Pozo 3 (origen nuevo)»; con `solo_muestra`, `tipo_estudio: "sin estudio"`.
- `faltan`: datos sin decir, en orden cliente → origen → tipo de estudio → fecha de muestreo →
  fecha de ingreso. Una fecha ilegible figura como «fecha de muestreo (no entendí «…»)».
- `problemas`: textos de AquaLab para lo que no coincide («No hay ningún cliente activo que
  coincida con «X».», «El tipo «Y» no está activo.») y los errores de `RegistroMuestraForm` en
  cliente, origen, origen nuevo y fechas.
- `elegir`: `"cliente" | "origen" | "tipo_estudio" | null`. Indica qué tiene que elegir el
  empleado entre las opciones (AquaLab las muestra como botones; el modelo no las repite, R7).
- `listo: true` solo si no hay `faltan` ni `problemas`. Además, debe haber un tipo activo o
  `solo_muestra`.

Se pregunta por grupos, en este orden: primero lo que hay que **elegir** (cliente, después origen,
después tipo), de a una elección; después las **dos fechas juntas** en un mismo mensaje. Así el
ejemplo con una elección llega al enlace en 3 mensajes (SC-001). Si el cliente no está resuelto, no
se busca el origen.

### Lo que queda en AquaLab (`Salida`)

- `opciones`: `Referencia` con `pregunta`, según `elegir`:
  - cliente: los clientes activos coincidentes (botón + ↗ a la ficha), pregunta «El cliente es
    <nombre>».
  - origen: los orígenes del cliente (`tipo="opcion"`), pregunta «El origen es <nombre>», y al
    final «Registrarlo como origen nuevo», pregunta «Registrar «<texto>» como origen nuevo».
  - tipo: **primero** «Solo registrar la muestra», pregunta «Solo registrar la muestra, sin
    estudio»; después los tipos activos, pregunta «El tipo de estudio es <nombre>».
- `primeras`: con `listo`, la referencia `registrar_muestra` con los parámetros de
  [enlaces-precargados.md](enlaces-precargados.md), etiqueta «Revisar y registrar la muestra»,
  `minimizar`. Con el cliente no encontrado, la referencia `registrar_cliente` («Registrar
  cliente»).
- `avisos` sin `listo` (U1, conversación larga): si hay algo en `resuelto`, el resumen fijo
  «Hasta ahora: Cliente: … · Origen: … · Tipo de estudio: … · Muestreo: dd/mm/aaaa · Ingreso:
  dd/mm/aaaa.» con solo los datos resueltos. Va al final del texto, queda en el historial que
  manda el navegador y así lo resuelto sobrevive aunque el primer mensaje salga de la ventana de 6.
  Igual en `preparar_estudio` («Hasta ahora: Muestra: PI … · Tipo de estudio: ….»).
- `avisos`: con `listo`, el texto fijo «La muestra se registra recién cuando confirmes en el
  formulario.».

## `preparar_estudio`

Descripción: «Prepara la creación de un estudio para una muestra ya registrada. Llamala con el N°
PI y el tipo de estudio que dijo el empleado. No crea nada».

| Argumento | Tipo |
|---|---|
| `numero_pi` | integer |
| `tipo_estudio` | string |

Salida con la misma forma (`listo`, `resuelto` con `muestra: "PI 200417 · Lácteos del Sur S.A. ·
Pozo 2"`, `faltan`, `problemas`, `elegir: "tipo_estudio" | null`). Si el N° PI no existe:
`problemas: ["No hay ninguna muestra con el N° PI …."]`, sin opciones ni enlace. Con `listo`:
`primeras` = referencia `crear_estudio` («Revisar y crear el estudio», `minimizar`) más la
referencia a la ficha de la muestra (10.1).

## Mensajes fijos (sin llamar al servicio)

- `MENSAJE_ALTA_CLIENTE`: «No doy de alta clientes desde el asistente. Podés hacerlo en
  «Registrar cliente».» y el enlace `clientes:registrar`. Se usa cuando la pregunta empieza con
  un verbo de registro y nombra «cliente» sin nombrar «muestra» ni «estudio».
- `MENSAJE_SOLO_CONSULTA` actualizado: «Puedo consultar muestras, estudios y clientes, y preparar
  el registro de una muestra o de un estudio para que lo confirmes. No cargo mediciones, no
  valido, no emito ni borro datos. …».
