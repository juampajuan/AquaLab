# Investigación y decisiones — US 10.2

Fecha: 2026-11-16. Base inspeccionada: c5a0030a06de65fc56949b8716c36506a2e2bf46. Rama Git real: `39-Conclucion-Asistida`. Investigación de código y documentación oficial, sin ejecutar producto, tests o servicios externos de IA. Las tres investigaciones paralelas del workflow se consolidan aquí; solo se generan documentos de esta feature.

## R1 — Reutilización real y límites de las interfaces

**Decision**: mantener Python 3.12, Django 5.2.18, PostgreSQL 16, WeasyPrint 70 y Tailwind v4.3.3 existentes. El único acceso a IA seguirá siendo `asistente.cliente_ia.enviar(mensajes, [], timeout, config)` con `asistente.configuracion.actual()`; un adaptador nuevo de `informes` implementará el recorrido de conclusión. No modificar US 10.1.

**Rationale**: cliente_ia.py:36 acepta herramientas vacías y traduce fallos de red, cuota y credenciales. `test_sin_herramientas_no_manda_tools` ya caracteriza esa capacidad. Configuración actual: `ASISTENTE_API_KEY`, `ASISTENTE_URL`, `ASISTENTE_MODELO`; Groq y openai/gpt-oss-120b por defecto. `conversacion.responder` está diseñado para consultas con herramientas y rechaza acciones; no es un servicio de conclusiones.

**Alternatives considered**: nuevo SDK/proveedor, nuevas variables o adaptar el chat: descartados por redundancia y cambio de otra historia. No se instala nada para planificar ni se agrega dependencia al diseño.

## R2 — Hechos autoritativos y presentación auxiliar

**Decision**: nuevo recolector puro `informes/conclusion_hechos.py`, raíz en las asignaciones del estudio, `Resultado` asociado y exclusivamente `Validacion(anulada=False)`. Por prueba conservar ID de asignación/prueba, código/nombre, ID y fecha de cálculo del resultado, valor exacto y unidad guardados, ID/fecha de validación y sus min/max/norma/origen/evaluación. Sin vigente: evaluación y límites normativos de conclusión ausentes; nunca consultar catálogo para suplirlos. Motivos canónicos: `sin_validacion`, `sin_limite_comparable`, `sin_norma`; anomalía sin Resultado: `sin_resultado` como información faltante, sin crear un hecho nuevo. No recalcular cumplimiento.

**Rationale**: `estudios/models.py:190–206` guarda valor, unidad, fórmula, curva y fecha_calculo en Resultado; Validacion:232–258 guarda límites/norma/evaluación, no valor/unidad/LD. `informes/contenido.py:45–58` tiene fallback al catálogo y no sirve directamente como recolector estricto. La clasificación normativa se copia de la vigente; `limite_min/max` vacíos no significan por sí solos «sin límite»: se conserva `evaluacion` guardada, sin reinterpretarla con leer_limite/evaluar.

Para respetar US1.5, reutilizar `texto_resultado`, `texto_limite` y los filtros de unidad solo como formateadores, construyendo los límites desde la vigente. El LD actual de Prueba se permite únicamente como **presentación auxiliar heredada** de `texto_resultado`; no es un límite normativo histórico, no se entrega al modelo ni determina evaluación/norma. Guardar LD auxiliar y resultado_texto en la huella para detectar cambios de presentación. Para una prueba sin vigente, no fabricar límites o presentación «< LD» desde el catálogo; mostrar los hechos verificables disponibles y la advertencia. No se historiza retrospectivamente un LD inexistente en Validacion.

**Alternatives considered**: usar armar_contenido/limites_y_evaluacion sin distinguir el fallback; reevaluar el catálogo; exigir nuevas validaciones a todos los informes: descartados. Tampoco agregar LD histórico a Validacion o cambiar las reglas de validación de otra historia solo para este alcance.

## R3 — Respuesta de IA verificable, no una promesa del prompt

**Decision**: redacción controlada mediante un contrato JSON de referencias opacas y patrones de frase permitidos. AquaLab determina qué pruebas requieren mención, el estado global y las advertencias. El proveedor elige variantes de redacción; los datos reales se insertan localmente. Ver [contrato IA](contracts/redaccion-ia.md).

**Rationale**: instrucciones de «no inventar», cotejar solo números o consultar un segundo modelo no garantizan que la prosa no invierta el sentido. Una gramática cerrada permite rechazar cualquier dato, referencia o afirmación ajena y hacer fallback determinístico. No se requiere una extensión JSON especial de Groq ni modificar el cliente compartido. El compromiso técnico explícito es redacción asistida con variantes controladas, no aceptar prosa arbitraria del modelo. La edición humana posterior sí es libre; no pasa por la gramática de IA.

**Alternatives considered**: regex semántica, libre prosa confiada, segundo modelo verificador: descartados. Nunca truncar pruebas para entrar en el contexto. Pedido y respuesta de contenido controlado: tope operacional 64 KiB UTF-8 cada uno; ante exceso se usa plantilla completa, sin límite funcional nuevo de pruebas por estudio o de extensión del texto profesional.

## R4 — Presupuesto de espera real y respaldo

**Decision**: una llamada, sin reintentos automáticos nuevos, con timeout=min(config.timeout, presupuesto restante); ante cualquier ErrorServicio, cuota, excepción de protocolo, contenido inválido, falta de clave o saturación, plantilla con todos los hechos. Presupuesto de espera del adaptador: config.presupuesto (20 s actual), timeout de transporte 15 s actual. Ninguna llamada bajo transacción o lock del estudio.

El cliente actual pasa timeout a urlopen y luego read(); eso no implementa un reloj total. Para garantizar retorno del adaptador, aislar la llamada existente en un hilo daemon sin ORM, limitado mediante semáforo a **2 llamadas activas por proceso**, y esperar su cola solo hasta el presupuesto. Saturación o vencimiento devuelve plantilla; la respuesta tardía no escribe nada. No liberar el permiso del semáforo al vencer el solicitante: lo libera el trabajador al terminar. No hacer join bloqueante ni usar un context manager de executor que espere al salir. Cada trabajador recibe solo configuración y mensajes inmutables, jamás request, modelos o conexión de BD. Sus errores se capturan y sus resultados tardíos se descartan.

**Rationale**: el timeout de urllib afecta operaciones de bloqueo, no acredita un plazo global de toda lectura ([Python 3.12](https://docs.python.org/3.12/library/urllib.request.html#urllib.request.urlopen)). Los hilos daemon permiten que el proceso termine sin esperarlos; no son cancelación de red y no deben poseer recursos transaccionales ([threading 3.12](https://docs.python.org/3.12/library/threading.html#thread-objects)). La cota de dos evita crecimiento ilimitado: si ambos quedan pendientes, el resto usa plantilla y la emisión sigue independiente. No es infraestructura de jobs, cola externa ni dependencia nueva.

**Alternatives considered**: prometer 20 s solo por urlopen; mantener locks mientras responde; lanzar hilos ilimitados; instalar una cola distribuida: descartados. Riesgo conocido: el transporte subyacente puede continuar tras el vencimiento; no se declara cancelado. El cliente existente tampoco limita bytes HTTP antes de read; el contrato rechaza contenido excesivo después de recibirlo. Conservar ese límite de integración, sin afirmar protección general frente a un proveedor hostil.

## R5 — Un borrador compartido por estudio

**Decision**: nuevo `BorradorConclusion` en informes: OneToOne a Estudio, texto editorial exacto, hechos canónicos, advertencias protegidas, revisión monotónica, token de propuesta y bloque completo o nulo de aprobación. No crear un registro solo por abrir una vista previa sin borrador. Otra persona autorizada puede revisar/emitir la versión compartida; dos pestañas no se sobrescriben sin detectar conflicto. Ver [modelo](data-model.md).

**Rationale**: sesión o almacenamiento del navegador como autoridad no permiten emitir desde otra cuenta ni persistir de forma confiable. El snapshot de Informe conserva la aprobación usada al emitir; la spec no exige un historial completo de todas las ediciones o aprobaciones descartadas.

**Alternatives considered**: borrador por usuario, FK viva desde el informe, historial genérico de documentos/aprobaciones: innecesarios o incompatibles. Se prevé una migración futura **aditiva de esta única tabla**, sin backfill de informes/validaciones; no se genera en plan.

## R6 — Huellas, invalidación y límites de observación

**Decision**: JSON canónico con claves ordenadas, listas por código/pk, Decimal/fechas como textos y sin floats; SHA256 del contenido exacto. Incluir `Validacion.pk`, Resultado.pk/fecha_calculo y sus datos pertinentes, no solo escalares. No incluir min/max/norma actuales ni Prueba.version global. Un cambio detectado limpia aprobación de forma persistente, aumenta revisión y nunca la revive al restaurar valores. Recálculo/revalidación A→B→A cambia identidades/fecha y sigue siendo inválido.

En vista previa autorizada, si existe borrador, la lectura puede **materializar la invalidación derivada** bajo el mismo lock cuando detecta divergencia; no crea borrador ni cambia texto editorial o datos clínicos, no genera propuesta ni aprobación. Actualiza hechos/advertencias y materializa el texto final con las advertencias actuales, como define data-model. Es mantenimiento de vigencia ya perdida, no un nuevo acto de aprobación. Guardar/aprobar/proponer/emitir también reconcilian. No confiar solo en una comparación virtual que después vuelva a true.

**Rationale**: calculo.cambiar_estado:227–239 anula mediante QuerySet.update; señales no son suficientes. La rama de lectura de informes emitidos jamás reconcilia un borrador ni mira fuentes actuales. Cambios normativos del catálogo posteriores a validar no cambian los hechos de la vigente.

**Alternatives considered**: hash solo del valor o estado de aprobación calculado en memoria: insuficientes. Triggers/contadores en todos los writers de catálogo: fuera del mínimo. Límite explícito: un LD auxiliar A→B→A sin observación intermedia ni cambio de datos validados no se detecta retrospectivamente; el LD no es un hecho normativo historizado. Se garantiza comparación del estado actual y persistencia de cualquier divergencia observada, no auditoría universal de escrituras directas.

## R7 — Transacciones y respuesta IA tardía

**Decision**: orden único en todas las operaciones nuevas: Estudio → Borrador existente/creación serializada por Estudio → asignaciones por pk → filas Prueba por pk. Evitar locks por joins nullable; usar consultas separadas y select_for_update(of=('self',)) donde corresponda. No bloquear tablas de catálogo de límites no usadas por la conclusión. Para emitir con conclusión, tomar luego el advisory lock de numeración existente; no duplicar emitir_informe ni su numeración.

Proponer: transacción breve A autoriza, comprueba disponibilidad, compara revisión, invalida aprobación e incrementa revisión/token aunque la propuesta termine idéntica. Conserva el texto anterior como borrador y captura hechos para la solicitud fuera de BD. Llamada IA sin locks. Transacción breve B reautoriza, relee hechos y verifica token/revisión/fuentes antes de instalar la propuesta o plantilla; si hubo edición, otra propuesta, cambios o emisión, 409 sin sobrescribir. Un trabajador tardío no ejecuta B: solo el hilo de la solicitud puede hacerlo.

Guardar: reconcilia hechos antes de comparar revisión esperada y actual; si estos cambiaron devuelve conflicto con texto editorial previo preservado y advertencias actuales. La revisión expresa puede guardar de nuevo sobre la revisión/fuente actual. Aprobar exige que el usuario haya visto la misma revisión y hechos actuales. Emisión con conclusión compara una vez más bajo los locks y construye la copia en esa misma transacción. Invalidación y respuesta 409 se confirman sin lanzar dentro de atomic una excepción que revierta la invalidación. Sin conclusión conserva el camino previo.

**Rationale**: las escrituras normales de estudios ya bloquean Estudio primero (estudios/servicios.py:199,256,325,424). El catálogo no bloquea Estudio: bloquear Prueba durante captura/aprobación/emisión evita una ventana de cambio de presentación. Los locks de fila duran hasta fin de transacción ([Django 5.2](https://docs.djangoproject.com/en/5.2/ref/models/querysets/#select-for-update), [PostgreSQL 16](https://www.postgresql.org/docs/16/explicit-locking.html#LOCKING-ROWS)). Probar concurrencia con PostgreSQL real, no SQLite.

**Alternatives considered**: confiar en IDs/hash enviados por navegador; una transacción durante toda la llamada; alterar servicios de escritura de mediciones/validaciones: descartados. No se serializan modificaciones administrativas directas ajenas a los contratos normales como si fueran flujos soportados.

## R8 — Autorización nueva, emisión anterior preservada

**Decision**: guardia nueva en vista y servicio: usuario autenticado y activo, grupo Bioquímicos y has_perm('informes.emitir_informes'), con instancia fresca al confirmar la escritura o volver de IA. Aplicar a proponer/guardar/aprobar e incorporar conclusión aprobada. No utilizar esa guardia para restringir vista previa general, validar resultados, emitir **sin conclusión** o enviar. El permiso individual o ser superusuario fuera del grupo no habilita proponer/aprobar.

**Rationale**: hoy generar y emitir_informe exigen permiso efectivo, no grupo; copiar simplemente esa autorización incumple Q1, pero cambiar el camino antiguo incumple FR-017. La aprobación conserva quién la realizó; al emitir otra persona se verifica autorización del emisor, sin suplantar al aprobador ni exigir que ambos sean la misma cuenta. No se introduce una regla nueva de caducidad o revocación retrospectiva del aprobador.

**Alternatives considered**: nuevo permiso/grupo, confiar en ocultar botones o tratar Administradores como Bioquímicos: descartados.

## R9 — Edición persistente y advertencias protegidas

**Decision**: guardar cambios con revisión optimista y acuse visible. JS de esta feature mantiene recuperación mínima en sessionStorage por pestaña/estudio/usuario/huella de sesión, solo texto pendiente y revisión base; la BD es autoridad. Antes de Volver, proponer, aprobar o emitir, completar la barrera de guardado. Para recarga inmediata, recuperar texto pendiente y pedir guardado sobre revisión actual sin sobreescribir una versión ajena. Limpiar recuperación al confirmar guardado, salir de sesión, detectar sesión distinta o perder autorización; nunca guardar tokens, hechos completos ni contactos. Si el navegador no permite recuperación y no se puede guardar, avisar y no aparentar conservación confirmada.

El texto profesional es libre, sin normalización Unicode ni strip silencioso; normalizar CRLF a LF al recibir y devolver antes de aprobar. Advertencias las genera AquaLab desde los hechos y se muestran separadas, no editables. Materializar `texto_final` (texto editorial + bloque de advertencias, si hay) **antes** de aprobar; el profesional ve el texto final exacto. Un cambio local deshabilita inmediatamente «Emitir con conclusión» hasta recibir el acuse y volver a aprobar. La pérdida de conexión no es una edición compartida confirmada; no se promete conocer teclas no recibidas desde otro equipo.

**Alternatives considered**: guardar solo al aprobar; depender de pagehide/sendBeacon; restringir la edición humana a patrones IA: descartados. Recuperación de navegación ordinaria no equivale a garantizar recuperación ante cierre forzado de pestaña, borrado de almacenamiento o caída del navegador antes del acuse; documentar el estado «sin guardar» con claridad.

## R10 — Snapshot inmutable y todos los formatos

**Decision**: ampliar en implementación `emitir_informe(estudio_pk, usuario, *, incluir_conclusion=False, revision_conclusion=None)` y `armar_contenido(..., conclusion=None)` de forma retrocompatible; ninguna de esas opciones existe hoy. El fragmento opcional `contenido['conclusion']` almacena texto final exacto, advertencias, hechos, revisión, huellas, aprobador y fecha; hojas escalares como textos para conservar el contrato actual. Sin conclusión se omite la clave, no se agrega None/encabezado vacío a informes antiguos.

Pantalla usa documento.html y PDF/impresión documento_impreso.html: son documentos distintos que deben consumir un parcial común de texto escapado. Los cuerpos txt/HTML del correo consumen el mismo texto final, no lo reconstruyen. envios.py ya pasa la copia y genera el PDF adjunto: no cambia destinatario vigente, confirmación, idempotencia ni envío sincrónico. PDF no consulta IA ni borrador. Advertencias ya forman parte de lo aprobado; no añadirlas después.

**Alternatives considered**: FK viva al borrador, generar al enviar, agregar conclusión solo al adjunto, |safe sobre texto profesional o migrar contenido histórico: descartados.

## Cierre de fase 0

Las incógnitas de arquitectura quedan resueltas por R1–R10. No hay decisiones funcionales nuevas ni puntos pendientes que impidan fase 1. Riesgos de transporte tardío, navegación sin acuse, alta cantidad de pruebas, presentación auxiliar LD y conflictos concurrentes quedan delimitados y tienen validación prevista. La clave Jira sigue sin informarse; US 10.2 satisface la trazabilidad por número de US de Constitution.
