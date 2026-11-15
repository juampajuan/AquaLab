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
| 200 | `{"texto": "...", "enlaces": [{"etiqueta": "PI 200417", "url": "/muestras/12/"}]}` | Respuesta normal (incluye «no encontré», fuera de alcance y pedidos de cambio rechazados). |
| 400 | `{"error": "pregunta_invalida", "mensaje": "Escribí una pregunta de hasta 500 caracteres."}` | Vacía, > 500, JSON mal formado o historial inválido. No llama al servicio. |
| 429 | `{"error": "cuota", "mensaje": "Se alcanzó el límite de consultas del asistente. Probá más tarde; el resto de AquaLab funciona normalmente."}` | El servicio devolvió 429. |
| 503 | `{"error": "no_disponible", "mensaje": "El asistente no está disponible en este momento. Probá de nuevo más tarde o usá las pantallas de AquaLab."}` | Timeout, red, 5xx, 401/403, respuesta inválida, presupuesto agotado. |
| 503 | `{"error": "no_configurado", "mensaje": "El asistente no está configurado."}` | Falta `ASISTENTE_API_KEY`. |
| 200 | `{"texto": "No pude completar la consulta; probá con una pregunta más concreta.", "enlaces": []}` | Se superó el tope de vueltas o de herramientas. |
| 403 / 302 | (de Django) | Sin CSRF / sin sesión. |

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
- Mensajes con `textContent` y `white-space: pre-line`; enlaces como `<a>` con `href` del servidor
  y `textContent` de la etiqueta. Avisos (`error`) con el estilo de alerta, sin cerrar el panel.
- La conversación es un arreglo en memoria del script: recargar o cerrar el panel la borra.
