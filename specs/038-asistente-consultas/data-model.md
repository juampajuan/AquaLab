# Data Model: Asistente de consultas (US 10.1)

**No hay modelos ni migraciones nuevas.** Todo vive en memoria durante un pedido; la conversación,
en el `sessionStorage` de la pestaña mientras el panel está abierto (FR-019): nada va a la base.

## Estructuras en memoria

### Configuración (`asistente/configuracion.py`, desde `settings.ASISTENTE`)

| Campo | Origen | Por defecto |
|---|---|---|
| `clave` | `ASISTENTE_API_KEY` | vacío → asistente deshabilitado |
| `url` | `ASISTENTE_URL` | `https://api.groq.com/openai/v1/chat/completions` |
| `modelo` | `ASISTENTE_MODELO` | `openai/gpt-oss-120b` |
| `timeout` | constante | 15 s por llamada |
| `presupuesto` | constante | 20 s por pregunta (SC-007) |
| `max_vueltas` / `max_herramientas` | constantes | 6 / 8 |
| `max_espera_reintento` / `margen_reintento` | constantes | 5 s / 1 s (reintento único ante 429) |

`habilitado` = `bool(clave)`.

### Pregunta (`PreguntaForm`, entrada del navegador)

- `pregunta`: texto, obligatorio, recortado, 1–500 caracteres.
- `historial`: lista de a lo sumo 6 `{rol: "usuario"|"asistente", texto: str ≤ 4000}`; roles
  desconocidos o de más se rechazan (400). El navegador ya recorta cada texto a 4000 caracteres
  antes de mandarlo.

### Referencia (`asistente/enlaces.py`)

`Referencia(tipo, pk, etiqueta, claves, patron, pregunta)` con `tipo` ∈ {`muestra`, `estudio`,
`cliente`, `historial`, `informe`}. `pregunta` (opcional) la marca como opción para elegir: el
enlace sale con `{"pregunta": …}` y el panel lo muestra como botón (research R12). `url()` con `reverse`: `muestras:detalle`, `estudios:detalle`, `clientes:detalle`,
`clientes:historial`, `informes:ver` (este último con el pk del estudio). Las de clientes inactivos
no se generan (sus pantallas los rechazan).

### Respuesta (salida al navegador)

- `texto`: texto plano del modelo (se muestra con `textContent`), o `MENSAJE_SOLO_CONSULTA` si no
  se usó ninguna herramienta (research R3); con una muestra de más de 5 estudios, termina con el
  aviso de FR-009a.
- `enlaces`: lista ≤ 10 de `{etiqueta, url}` armada con las referencias (research R8).

## Datos leídos (existentes, solo lectura)

| Entidad | Campos que salen hacia el servicio | Nunca salen |
|---|---|---|
| Cliente | `pk`, nombre para mostrar, `activo` | `email`, `telefono`, `domicilio`, `numero_documento`, `tipo_documento` |
| Origen | nombre | — |
| Muestra | `pk`, `numero_pi`, nombre, fechas de muestreo e ingreso, tipo de vertido (etiqueta), sitio de extracción | estado (SCRUM-82 lo sacó de la ficha), `responsable_muestreo`, `registrada_por`, `clave_borrador` |
| Estudio | `pk`, `tipo_nombre_snapshot`, estado (etiqueta), fecha de creación, si tiene informe (y su número) | `creado_por` |
| Prueba del estudio | código, nombre, estado (etiqueta), resultado como texto de pantalla + unidad (`|unidad`), motivo sin resultado, aviso fuera de rango de curva, evaluación (etiqueta), límite como texto, norma, origen de los límites, validada sí/no y fecha | quién cargó, corrigió o validó; observaciones de validación |

## Reglas

- Ninguna estructura se persiste. El logger `asistente` registra solo el tipo de falla.
- La evaluación es la de `evaluar_asignaciones` (validación vigente si está Completada; si no, el
  catálogo) y el texto del resultado el de `informes.contenido.texto_resultado`.
