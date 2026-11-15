# Data Model: Asistente de consultas (US 10.1)

**No hay modelos ni migraciones nuevas.** Todo vive en memoria durante un pedido; la conversación,
en la página abierta del navegador (FR-019).

## Estructuras en memoria

### Configuración (`asistente/configuracion.py`, desde `settings.ASISTENTE`)

| Campo | Origen | Por defecto |
|---|---|---|
| `clave` | `ASISTENTE_API_KEY` | vacío → asistente deshabilitado |
| `url` | `ASISTENTE_URL` | `https://api.groq.com/openai/v1/chat/completions` |
| `modelo` | `ASISTENTE_MODELO` | `openai/gpt-oss-120b` |
| `timeout` | constante | 15 s por llamada |
| `presupuesto` | constante | 25 s por pregunta |
| `max_vueltas` / `max_herramientas` | constantes | 6 / 8 |

`habilitado` = `bool(clave)`.

### Pregunta (`PreguntaForm`, entrada del navegador)

- `pregunta`: texto, obligatorio, recortado, 1–500 caracteres.
- `historial`: lista de a lo sumo 6 `{rol: "usuario"|"asistente", texto: str ≤ 4000}`; roles
  desconocidos o de más se rechazan (400).

### Referencia (`asistente/enlaces.py`)

`Referencia(tipo, pk, etiqueta)` con `tipo` ∈ {`muestra`, `estudio`, `cliente`, `historial`,
`informe`}. `url()` con `reverse`: `muestras:detalle`, `estudios:detalle`, `clientes:detalle`,
`clientes:historial`, `informes:ver` (este último con el pk del estudio). Las de clientes inactivos
no se generan (sus pantallas los rechazan).

### Respuesta (salida al navegador)

- `texto`: texto plano del modelo (se muestra con `textContent`).
- `enlaces`: lista ≤ 10 de `{etiqueta, url}` armada con las referencias (research R8).

## Datos leídos (existentes, solo lectura)

| Entidad | Campos que salen hacia el servicio | Nunca salen |
|---|---|---|
| Cliente | `pk`, nombre para mostrar, `activo` | `email`, `telefono`, `domicilio`, `numero_documento`, `tipo_documento` |
| Origen | nombre | — |
| Muestra | `pk`, `numero_pi`, nombre, estado (etiqueta), fechas de muestreo e ingreso, tipo de vertido (etiqueta), sitio de extracción | `responsable_muestreo`, `registrada_por`, `clave_borrador` |
| Estudio | `pk`, `tipo_nombre_snapshot`, estado (etiqueta), fecha de creación, si tiene informe (y su número) | `creado_por` |
| Prueba del estudio | código, nombre, estado (etiqueta), resultado como texto de pantalla + unidad (`|unidad`), motivo sin resultado, aviso fuera de rango de curva, evaluación (etiqueta), límite como texto, norma, origen de los límites, validada sí/no y fecha | quién cargó, corrigió o validó; observaciones de validación |

## Reglas

- Ninguna estructura se persiste. El logger `asistente` registra solo el tipo de falla.
- La evaluación es la de `evaluar_asignaciones` (validación vigente si está Completada; si no, el
  catálogo) y el texto del resultado el de `informes.contenido.texto_resultado`.
