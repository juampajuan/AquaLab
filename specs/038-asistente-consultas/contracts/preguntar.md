# Contrato: `POST /asistente/preguntar/` (`asistente:preguntar`)

Vista `asistente.views.preguntar`: `require_POST`, sesión obligatoria (`LoginRequiredMiddleware`),
CSRF (cabecera `X-CSRFToken` desde la cookie `csrftoken`). Respuesta siempre JSON.

## Pedido

```json
{
  "pregunta": "¿Qué no cumple en el estudio de la escuela N° 12?",
  "historial": [
    {"rol": "usuario", "texto": "¿Cómo está el PI 200417?"},
    {"rol": "asistente", "texto": "La muestra PI 200417 ..."}
  ]
}
```

## Respuestas

| HTTP | Cuerpo | Cuándo |
|---|---|---|
| 200 | `{"texto": "...", "enlaces": [{"etiqueta": "PI 200417", "url": "/muestras/12/"}]}` | Respuesta normal, apoyada en al menos una herramienta de esa pregunta (incluye «no encontré» y varias coincidencias). |
| 200 | `{"texto": "Solo puedo consultar muestras, estudios y clientes de AquaLab; no creo, modifico, valido, emito ni borro datos. Probá, por ejemplo: «¿Cómo está el PI 200417?», «¿Qué estudios tiene Lácteos del Sur?» o «¿Qué no cumple en el estudio de la escuela N° 12?».", "enlaces": []}` | La respuesta final no usó ninguna herramienta: fuera de alcance, pedido de cambio o respuesta «de memoria». AquaLab descarta el texto del modelo (research R3). |
| 400 | `{"error": "pregunta_invalida", "mensaje": "Escribí una pregunta de hasta 500 caracteres."}` | Vacía, > 500, JSON mal formado o historial inválido. No llama al servicio. |
| 429 | `{"error": "cuota", "mensaje": "Se alcanzó el límite de consultas del asistente. Probá más tarde; el resto de AquaLab funciona normalmente."}` | El servicio devolvió 429. |
| 503 | `{"error": "no_disponible", "mensaje": "El asistente no está disponible en este momento. Probá de nuevo más tarde o usá las pantallas de AquaLab."}` | Timeout, red, 5xx, 401/403, respuesta inválida o presupuesto de 20 s agotado por demora del servicio. |
| 503 | `{"error": "no_configurado", "mensaje": "El asistente no está configurado."}` | Falta `ASISTENTE_API_KEY`. |
| 200 | `{"texto": "No pude completar la consulta; probá con una pregunta más concreta.", "enlaces": []}` | Se superó el tope de vueltas (6) o de ejecuciones (8); el servicio sí respondió. |
| 403 / 302 | (de Django) | Sin CSRF / sin sesión (la sesión venció: `LoginRequiredMiddleware` redirige al login). |

Muestra con más de 5 estudios (FR-009a): el `texto` termina con «La muestra PI N tiene T estudios;
se detallan los 5 más recientes. El resto está en la ficha de la muestra.» y el primer enlace es el
de la ficha de la muestra. Lo agrega AquaLab, no el modelo.

GET devuelve 405. La vista no escribe en la base ni en la sesión.

## Interfaz (`templates/ui/asistente.html` + `static/js/aqualab.js`)

- Botón flotante `[data-asistente-abrir]` abajo a la derecha, en `base.html` solo con sesión;
  sin configuración se dibuja con `aria-disabled="true"` y el aviso «El asistente no está
  configurado» (ayuda de `ui/ayuda.html`).
- Panel `[data-asistente]` (`role="dialog"`, `aria-label="Asistente"`) fijo abajo a la derecha,
  por debajo de la barra superior (no la tapa), con ejemplos de preguntas, lista de mensajes
  (`aria-live="polite"`), campo con contador (500) y botón «Preguntar». Escape lo cierra; el
  foco vuelve al botón.
- Mientras espera: «Consultando…» y el envío deshabilitado (evita dobles envíos).
- Sesión vencida: si `response.redirected` es verdadero o la respuesta no es JSON
  (`Content-Type` distinto de `application/json` o falla `response.json()`), el panel muestra el
  aviso «Tu sesión venció; volvé a iniciar sesión» y no agrega nada a la conversación.
- Historial que se manda: los últimos 6 mensajes, cada texto recortado a sus primeros 4000
  caracteres (así una respuesta larga nunca hace fallar la pregunta siguiente con 400).
- Mensajes con `textContent` y `white-space: pre-line`; enlaces como `<a>` con `href` del servidor
  y `textContent` de la etiqueta. Avisos (`error`) con el estilo de alerta, sin cerrar el panel.
- La conversación es un arreglo en memoria del script: recargar o cerrar el panel la borra.
