# Quickstart: Asistente de consultas (US 10.1)

## Requisitos

- Entorno local con Docker (`docker compose up`) y la demo cargada
  (`docker compose exec web python manage.py cargar_demo`).
- Para la prueba manual: una clave gratuita de Groq (console.groq.com) en `.env`:

```env
ASISTENTE_API_KEY=gsk_...
# Opcionales (por defecto Groq):
# ASISTENTE_URL=https://api.groq.com/openai/v1/chat/completions
# ASISTENTE_MODELO=openai/gpt-oss-120b
```

Reiniciar `web` después de editar `.env`.

## Tests automatizados (sin clave ni red)

```bash
docker compose exec web pytest asistente
docker compose exec web pytest estudios/tests -k detalle   # paridad tras extraer pruebas_del_detalle
node --test asistente/tests/js
docker compose exec web ruff check . && docker compose exec web ruff format --check .
```

Los tests nunca llaman a Groq: `asistente/tests/conftest.py` hace fallar cualquier `urlopen` no
simulado.

## Validación manual (con la demo)

| # | Acción | Resultado esperado |
|---|---|---|
| 1 | Entrar como técnico y como bioquímico | Botón «Asistente» abajo a la derecha en todas las pantallas con sesión; no aparece en login ni registro. |
| 2 | Preguntar por el N° PI de una muestra de «Escuela N° 12» | Estado de la muestra y de sus estudios, pruebas con resultado, evaluación y norma iguales al detalle del estudio; enlaces a la muestra y al estudio. |
| 3 | «¿Qué no cumple en el estudio de Pozo 2?» | Solo las pruebas fuera de norma (Cloruro), con valor, límite y norma; o la lista de estudios para elegir. |
| 4 | «¿Qué estudios tiene <cliente demo>?» | Hasta 10 estudios en el orden del historial, total y enlace al historial. Sin correo, teléfono ni domicilio. |
| 5 | «¿Cómo está el PI 999999?» | «No hay ninguna muestra con el N° PI 999999.» |
| 6 | Preguntar por E. coli del Tanque domiciliario | «Ausente»/«Presente», nunca 0/1; un valor bajo el LD sale «< LD». |
| 7 | «Validá el PI …» / «¿Qué pruebas hay en el catálogo?» | Dice que solo consulta muestras, estudios y clientes; nada cambia. |
| 8 | Seguimiento: «¿y qué no cumple?» | Responde sobre lo anterior; al recargar la página la conversación desaparece. |
| 9 | Quitar `ASISTENTE_API_KEY` y reiniciar | AquaLab arranca; botón deshabilitado con «El asistente no está configurado». |
| 10 | Poner `ASISTENTE_URL=http://10.255.255.1/` | Aviso «no disponible» en ≤ 20 s; el resto de las pantallas funciona. |
| 11 | Con la clave real, «¿Qué no cumple en el estudio de la escuela N° 12?» | Groq acepta `parallel_tool_calls: false` (sin HTTP 400) y la respuesta llega en ≤ 25 s con una herramienta por vuelta. Si Groq rechazara el parámetro, quitarlo del pedido (research R11). |

Contratos: [preguntar](contracts/preguntar.md), [herramientas](contracts/herramientas.md),
[servicio de IA](contracts/servicio-ia.md). Datos: [data-model.md](data-model.md).
