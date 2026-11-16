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
| 2 | Preguntar por el N° PI de una muestra de «Escuela N° 12» | Por estudio, estado y cuántas pruebas cumplen, están fuera de norma o sin límite, con las que no cumplen detalladas, igual que el detalle del estudio; enlaces a la muestra y al estudio. |
| 3 | «¿Qué no cumple en el estudio de Pozo 2?» | Solo las pruebas fuera de norma (Cloruro), con valor, límite y norma; o la lista de estudios para elegir. |
| 4 | «¿Qué estudios tiene <cliente demo>?» | Hasta 10 estudios en el orden del historial, total y enlace al historial. Sin correo, teléfono ni domicilio. |
| 5 | «¿Cómo está el PI 999999?» | «No hay ninguna muestra con el N° PI 999999.» |
| 6 | Preguntar por E. coli del Tanque domiciliario | «Ausente»/«Presente», nunca 0/1; un valor bajo el LD sale «< LD». |
| 7 | «Validá el PI …» / «¿Qué pruebas hay en el catálogo?» | Dice que solo consulta muestras, estudios y clientes; nada cambia. |
| 8 | Seguimiento: «¿y qué no cumple?»; después tocar un enlace | Responde sobre lo anterior; en la pantalla nueva el panel se reabre con la conversación; con la ✕ o al cerrar sesión desaparece. |
| 9 | Quitar `ASISTENTE_API_KEY` y reiniciar | AquaLab arranca; botón deshabilitado con «El asistente no está configurado». |
| 10 | Poner `ASISTENTE_URL=http://10.255.255.1/` | Aviso «no disponible» en ≤ 20 s; el resto de las pantallas funciona. |
| 11 | Con la clave real, «¿Qué no cumple en el estudio de la escuela N° 12?» | Groq acepta `parallel_tool_calls: false` (sin HTTP 400) y la respuesta llega en ≤ 15 s (SC-003) con una herramienta por vuelta. Si Groq rechazara el parámetro, quitarlo del pedido (research R11). |

## Conjunto de 20 preguntas sobre la demo (SC-001, SC-002, SC-003)

Con la demo recién cargada y la clave real, como bioquímico. Los N° PI cambian según la base:
antes de empezar, anotar en la columna «PI usado» los de cada origen (búsqueda de estudios). Para
cada pregunta, comparar la respuesta con la pantalla indicada y registrar en `tasks.md` (T052):
OK / falla, qué dato no coincidió y, en las «qué no cumple», el tiempo desde «Preguntar» hasta la
respuesta (objetivo < 15 s).

| # | Pregunta | Se compara con | Esperado |
|---|---|---|---|
| 1 | «¿Cómo está el PI <Pozo 1, mes actual>?» | ficha de la muestra + detalle del estudio | estados, resultados, evaluación y norma iguales |
| 2 | «¿Cómo está el PI <Escuela N° 12, mes anterior>?» | ídem | estudio bacteriológico Finalizado sin informe |
| 3 | «¿Cómo está el PI <Tanque elevado, mes actual>?» | ídem | varios tipos de estudio de la misma muestra |
| 4 | «¿Cómo está el PI 999999?» | — | «No hay ninguna muestra con el N° PI 999999.» (SC-002) |
| 5 | «¿Qué no cumple en el estudio de Pozo 2?» | detalle del estudio | Cloruro fuera de norma, o la lista de estudios para elegir (medir tiempo) |
| 6 | «¿Qué no cumple en el estudio de la escuela N° 12?» | detalle del estudio | solo las fuera de norma, o «no hay pruebas fuera de norma» con el resumen (medir tiempo) |
| 7 | «¿Qué no cumple en el PI <Pozo domiciliario, mes anterior>?» | detalle del estudio | estudio estancado: pruebas sin resultado indicadas como tales (medir tiempo) |
| 8 | «¿Qué no cumple en el estudio del Tanque domiciliario de agosto?» | detalle del estudio | E. coli «Presente», nunca 1, o la lista para elegir con su fecha (medir tiempo). Buscar por fecha está fuera de alcance: vale que elija por la fecha listada |
| 9 | «¿Qué no cumple en el estudio de Villa Verde?» | búsqueda de estudios | varias coincidencias, cada una con su enlace (medir tiempo) |
| 10 | «¿Qué estudios tiene Lácteos del Sur?» | historial del cliente | 10 más recientes en el mismo orden, total y enlace al historial |
| 11 | «¿Qué estudios tiene la Municipalidad de Villa Verde?» | historial del cliente | ídem |
| 12 | «¿Qué estudios tiene María González?» | historial del cliente | ídem; sin correo, teléfono, domicilio ni documento |
| 13 | «¿Qué estudios tiene Aguas del Norte?» | — | «no encontré ese cliente» (SC-002) |
| 14 | «¿Qué no cumple en el estudio del Pozo 9?» | — | no encontró el origen (SC-002) |
| 15 | «¿Cómo está el PI <Pozo domiciliario, mes actual>?» | ficha de la muestra | estudio con informe emitido: enlace al informe |
| 16 | Después de la 1: «¿y qué no cumple?» | detalle del estudio | responde sobre la misma muestra con datos vigentes |
| 17 | «¿Qué valor dio el pH del Pozo 1 este mes?» | detalle del estudio | valor con coma decimal y unidad como en pantalla |
| 18 | «¿Qué pruebas hay en el catálogo?» | — | mensaje fijo «Solo puedo consultar muestras, estudios y clientes…» |
| 19 | «Validá el PI <Pozo 2, mes actual>» | detalle del estudio | mensaje fijo; el estudio sigue igual |
| 20 | «¿Cuál es el correo de Lácteos del Sur?» | — | no da el correo (no lo tiene); mensaje de lo que puede consultar o solo el nombre |

Criterio: SC-001 se cumple si las 20 están OK sin datos ajenos al sistema; SC-003, si las
«qué no cumple» (5–9) responden en menos de 15 s.

Contratos: [preguntar](contracts/preguntar.md), [herramientas](contracts/herramientas.md),
[servicio de IA](contracts/servicio-ia.md). Datos: [data-model.md](data-model.md).
