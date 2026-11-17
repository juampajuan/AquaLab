# Contrato de redacción restringida — US 10.2

Contrato futuro de `informes/conclusion_ia.py`; no es una capacidad existente del chat. Implementa R1–R4 de [research](../research.md). Reutiliza `asistente.cliente_ia.enviar(mensajes, herramientas=[], timeout=..., config=...)` y `asistente.configuracion.actual()`, sin modificar esos módulos, sin SDK, herramientas ni conversación persistida.

## Datos y gramática

AquaLab calcula primero los hechos y clases del [modelo](../data-model.md). La IA recibe únicamente versión '1', clase global (`todas_cumplen`, `con_incumplimientos` o `parcial`) y referencias opacas h1…hN de las pruebas evaluables fuera de norma. No recibe nombres, normas, valores, contactos, identidad de personas, credenciales en mensajes, texto editorial ni historial del chat. Las credenciales siguen exclusivamente en el transporte existente. Las pruebas no evaluables se describen localmente en advertencias con todos sus hechos conocidos; no se omiten del borrador.

La IA redacta seleccionando variantes lingüísticas auditadas. Su respuesta debe ser un objeto JSON de claves exactas:

```json
{"version":"1","bloques":[{"hecho":"h1","redaccion":"F1"}],"cierre":"I1"}
```

No admite texto libre, Markdown, claves adicionales, tool_calls, referencias desconocidas, omisiones ni duplicados. Cada referencia enviada aparece exactamente una vez. Los bloques se materializan en el orden canónico del sistema, independientemente del orden de respuesta. Todos los valores de la respuesta son strings salvo bloques, que es lista; validación estricta de tipos. Un envoltorio desconocido o contenido vacío invalida toda la respuesta.

| Patrón | Plantilla local, con sustituciones exclusivas de AquaLab |
|---|---|
| F1 | «{codigo} — {nombre}: {resultado_con_unidad}; límite aplicado: {limite}; norma: {norma}. La validación vigente indica fuera de norma.» |
| F2 | «La prueba {codigo} — {nombre} está fuera de norma según su validación vigente: valor obtenido {resultado_con_unidad}, límite aplicado {limite}, norma {norma}.» |
| T1 | «Todas las pruebas del estudio son evaluables y cumplen según sus validaciones vigentes.» |
| T2 | «Las validaciones vigentes de todas las pruebas evaluables del estudio indican cumplimiento; no hay pruebas no evaluables.» |
| I1 | «Se identifican las pruebas fuera de norma detalladas en esta conclusión.» |
| I2 | «Las validaciones vigentes registran los incumplimientos indicados.» |
| P1 | «Conclusión parcial: existen pruebas no evaluables por la información insuficiente indicada en las advertencias.» |
| P2 | «La información disponible permite una conclusión parcial; las pruebas no evaluables y sus motivos se detallan en las advertencias.» |

T1/T2 solo para todas_cumplen; I1/I2 solo para con_incumplimientos sin ausencias; P1/P2 solo para parcial. Parcial puede tener cero bloques F. El cuerpo con incumplimientos nunca omite valor/unidad cuando corresponde, límite y norma registrados. Los textos se insertan como datos, nunca como instrucciones ni HTML seguro. Ausente/Presente y < LD conservan la presentación del informe sin recalcular cumplimiento. No se agregan recomendaciones.

Este contrato sacrifica prosa libre del proveedor para garantizar que no pueda introducir hechos. La edición profesional posterior sí es libre y no se restringe a esta gramática; conserva el bloque de advertencias. El profesional ve todo el texto final antes de aprobar. Esta es una decisión técnica de seguridad de datos, no una nueva regla de evaluación clínica.

## Respaldo, presupuesto y cancelación lógica

La plantilla fija usa F1 para cada referencia en orden canónico, T1/I1/P1 según la clase y las mismas advertencias. No vuelve a consultar fuentes durante la redacción. Si los hechos cambiaron al persistir, se rechaza la respuesta con conflicto; no se instala una plantilla de datos antiguos.

Sin configuración, error de proveedor/red/credenciales/cuota, respuesta inválida, presupuesto agotado, capacidad ocupada o entrada/respuesta por encima de 64 KiB: respaldo completo, aviso visible y código seguro de motivo. El límite es operativo del intercambio IA; no limita la cantidad de pruebas, texto editable o extensión del respaldo. Nunca truncar hechos. El tamaño de respuesta se verifica antes de parsear lo recibido; el cliente existente no limita la lectura HTTP bruta y esa limitación se registra como riesgo, sin afirmar una protección que no tiene.

Una solicitud como máximo, sin reintentos automáticos. Presupuesto total del llamador tomado de Configuracion.presupuesto (actualmente 20 s), timeout de transporte min(Configuracion.timeout, restante), actualmente 15 s. Un worker daemon de biblioteca estándar recibe solo configuración y mensajes inmutables, sin ORM ni request. Capacidad máxima dos workers por proceso, protegida con semáforo; la capacidad se libera cuando termina realmente el worker, no cuando el llamador vence. Cola de resultado y espera limitada por deadline monotónico; no join bloqueante ni context manager de executor que espere al salir. Saturación devuelve respaldo inmediato. Un worker tardío no persiste nada ni puede instalar una propuesta.

El transporte existente no garantiza cancelar una lectura lenta al vencer el deadline total. Dos workers atascados ocupan la capacidad y futuras peticiones usan plantilla; el flujo de emisión no llama a IA. Pruebas de este contrato usan dobles controlados, nunca Groq real. No registrar mensajes, configuración, texto profesional ni cuerpo de error; solo códigos y duración sin datos personales.

## Resultado interno

El adaptador devuelve texto editorial materializado, origen ia/plantilla y motivo de respaldo vacío/código. Hechos, advertencias y aprobación no son salidas confiadas al proveedor. La capa de persistencia agrega advertencias, verifica nuevamente autorización/revisión/huella y guarda; no aprueba. Ver [contrato de interacción](conclusiones-ui.md).
