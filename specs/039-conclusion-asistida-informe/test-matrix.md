# Estrategia y trazabilidad de pruebas — US 10.2

**Planificación, no resultados ejecutados.** 38 escenarios de la spec, 19 FR, 10 SC y nueve criterios originales cubiertos abajo. Los nombres de archivos/tests son propuestos y todavía no existen. Cada fila exige pytest-django aunque tenga además cobertura JS o revisión visual. Preparar primero los tests del comportamiento a construir y comprobar su fallo pertinente antes de implementar; no atribuir este orden como una frase literal de Constitution, cuyo requisito obligatorio es cobertura automatizada de cada escenario.

## Archivos propuestos

H = `informes/tests/test_conclusion_hechos.py`; R = `informes/tests/test_conclusion_revision.py`; E = `informes/tests/test_conclusion_emision.py`; I = `informes/tests/test_conclusion_ia.py`. Integración real con ORM PostgreSQL; transporte IA sustituido con monkeypatch. Ningún test depende de Groq ni correo real.

Identificadores USx.y referencian los recorridos y numeración de escenarios de [spec](spec.md); no son nuevas US de Jira.

| Escenario | Archivo / test propuesto | Oráculo obligatorio |
|---|---|---|
| US1.1 | H / test_dos_incumplimientos_exactos | Cada prueba una vez; valor Decimal, unidad, límite y norma vigentes exactos; botón autorizado. |
| US1.2 | H / test_todas_evaluables_cumplen | Cumplimiento total solo con todas evaluables; sin recomendaciones. |
| US1.3 | H / test_solo_validacion_vigente | Historial anulado no entra ni duplica. |
| US1.4 | H / test_catalogo_no_reemplaza_validacion | Cambiar min/max/norma del catálogo no cambia hechos normativos ni invalida por esos campos ajenos. |
| US1.5 | H / test_presentaciones_resultado | Parametrizar Ausente/Presente, Decimal/unidad y < LD; evaluación no recalculada. |
| US1.6 | R / test_proponer_no_emite_ni_valida | Propuesta solo escribe borrador; Informe, Resultado, Validacion y estado clínico sin cambios; no aprueba. |
| US1.7 | H / test_parcial_sin_vigente | Identificar prueba sin vigente; cero fallback normativo al catálogo; otra prueba conserva hechos. |
| US1.8 | H / test_parcial_sin_limite | Respeta evaluación sin límite comparable; no cumplimiento total. |
| US1.9 | H / test_parcial_sin_norma | Mantener valor/límite/evaluación conocidos; advertir norma ausente. |
| US1.10 | H / test_todas_no_evaluables | Borrador parcial identifica todas y motivos; no inventa ni afirma cumplimiento. |
| US2.1 | E / test_emite_texto_reescrito_aprobado | Copia texto final confirmado, no propuesta inicial. |
| US2.2 | E / test_emitir_sin_conclusion | Parametrizar sin fila, borrador, edición, aprobación invalidada; sin clave conclusion y reglas existentes. |
| US2.3 | R / test_propuesta_no_aprueba | Bloque de seis campos nulo tras propuesta correcta. |
| US2.4 | R / test_sin_grupo_ni_permiso_denegado | UI y POST proponer/aprobar denegados, consulta previa conservada. |
| US2.5 | R / test_sin_sesion_o_inactivo_denegado | Ambas acciones, sin escritura; redirección de sesión no es éxito JSON. |
| US2.6 | R / test_solo_grupo_denegado | Quitar permiso efectivo incluso al grupo en fixture aislada; no concederlo automáticamente. |
| US2.7 | R / test_solo_permiso_denegado | Proponer/aprobar denegados, emitir sin conclusión sigue autorizado con firma. |
| US2.8 | R / test_grupo_y_permiso_autorizados | Ambas acciones permitidas; otros permisos sin cambios. |
| US2.9 | R / test_edicion_invalida_aprobacion | Texto nuevo, revisión mayor y aprobación nula; emisión con versión antigua rechazada. |
| US2.10 | R / test_regeneracion_identica_invalida | Invalidar en reserva, también si respuesta repite texto. |
| US2.11 | E / test_cambio_fuentes_impide_conclusion_obsoleta | Parametrizar Resultado/fecha, vigente nueva, ausencia y LD auxiliar; invalidación persistida; sin conclusión aún posible si estudio listo. |
| US2.12 | R / test_borrador_persiste_al_volver_y_recargar | Guardado por POST, nueva consulta y nueva sesión del mismo autorizado recuperan texto no aprobado. Complementar prueba JS de flush/recarga. |
| US2.13 | R / test_recarga_preserva_aprobacion_vigente | Misma revisión/aprobación si sin cambios; invalidada no revive al restaurar valores. |
| US2.14 | E / test_reaprobacion_explicita_fuentes_actuales | Conflicto obliga revisar texto final y fuentes; solo nueva aprobación emite. |
| US2.15 | E / test_editar_aprobar_parcial_conserva_advertencias | Advertencias fuera de textarea, inalterables desde cliente, snapshot las contiene una vez. |
| US3.1 | E / test_snapshot_texto_y_trazabilidad | IDs estudio/pruebas/vigentes, ausencias, hashes, revisión y aprobador; todos escalares str. |
| US3.2 | E / test_snapshot_no_cambia_con_origen | Cambiar catálogo/perfil tras emisión: JSON y texto de copia idénticos. |
| US3.3 | E / test_misma_conclusion_todos_los_medios | Consultar, imprimir, HTML entregado a WeasyPrint, PDF real, correo txt/HTML y adjunto con idéntico texto; solo maquetación varía. |
| US3.4 | E / test_salidas_y_reenvio_no_llaman_ia | Dobles que fallan si se invoca IA; conservar destinatario actual, confirmación e idempotencia de envío. |
| US3.5 | E / test_historicos_sin_conclusion_intactos | Snapshot sin nueva clave y renders antes/después sin bloque/título vacío; ninguna escritura retrospectiva. |
| US3.6 | E / test_emitido_rechaza_mutar_conclusion | Todos los POST nuevos y guardias de modelo/copia; sin mutación de Informe. |
| US3.7 | E / test_otro_bioquimico_emite | Dos personas reales distintas; aprobador original congelado y emisor distinto. |
| US4.1 | I / test_timeout_total_ofrece_plantilla | Worker controlado sin responder, deadline acotado y respaldo; sin aprobación, sin locks externos retenidos. |
| US4.2 | I / test_fallos_proveedor_ofrecen_plantilla | Parametrizar red, cuota, credenciales y error proveedor; aviso seguro, mismos hechos, emisión sin conclusión disponible. |
| US4.3 | I / test_sin_configuracion_ofrece_plantilla | No llamar transporte; borrador editable y emisión no depende de clave IA. |
| US4.4 | I / test_respuesta_invalida_no_inventa | Vacío/JSON inválido, campos extra, texto inventado, refs omitidas/duplicadas/extra y cierres incompatibles: respaldo completo. |
| US4.5 | I / test_plantilla_todas_cumplen | Cierre correcto, edición y aprobación explícita mediante endpoints. |
| US4.6 | I / test_plantilla_parcial_mismos_hechos | Parametrizar tres ausencias aprobadas; mismos datos/advertencias y recorrido editar/aprobar/emitir o sin conclusión. |

## Requisitos, decisiones y validación

| Requisito | Estrategia técnica | Escenarios / validación |
|---|---|---|
| FR-001 | Vista previa + POST separado, R8/R9 | US1.1, US1.6 |
| FR-002 | Recolector canónico y render local R2/R3 | US1.1, US1.5, US1.7–10 |
| FR-003 | Validación vigente sin fallback R2 | US1.3–4 |
| FR-004 | Gramática cerrada R3, rechazo íntegro | US1.5, US4.4 |
| FR-005 | Clase local, cierre compatible R2/R3 | US1.2, US1.7–10, US4.5–6 |
| FR-006 | Borrador BD + guardado confirmado R5/R9 | US2.1, US2.12, US2.15; JS |
| FR-007 | Acciones separadas R5/R6 | US2.1–3 |
| FR-008 | Parámetro opcional compatible R10 | US2.2, US2.7, US4.1–3 |
| FR-009 | Guardia conjunta y reautorización R8 | US2.4–8, pruebas CSRF/directas |
| FR-010 | Revisión/hash, invalidez persistente, locks R6/R7 | US2.9–14, US3.7; carreras PostgreSQL |
| FR-011 | Copia autosuficiente de texto/hechos/aprobación R10 | US3.1–2, US3.7 |
| FR-012 | Mismo snapshot en parciales y correo txt R10 | US3.3 |
| FR-013 | Deadline + plantilla R4 | US4.1–2, US4.4 |
| FR-014 | Sin configuración usa respaldo R4 | US4.3, US4.5 |
| FR-015 | Salidas sin recolector/IA R10 | US3.4 |
| FR-016 | Clave opcional, sin backfill R10 | US3.5–6 |
| FR-017 | Extensión emisión existente R7/R8/R10 | US1.6, US2.2, US3.4; regresiones de dominio |
| FR-018 | Ausencias explícitas y advertencias protegidas R2/R9 | US1.7–10, US2.15, US4.6 |
| FR-019 | Cliente existente sin chat, refs mínimas R1/R3 | Capturar mensajes/transporte; cero datos personales/secretos y cero tools; regresión asistente |

Los SC se comprueban con estas mismas muestras, sin crear métricas externas: SC-001=US1.1/3/4/7–10; SC-002=US1.2/7–10+US4.5/6; SC-003=US2.1–3/9–14; SC-004=US3.3; SC-005=US4.1–6; SC-006=US3.5/6; SC-007=US3.1/7; SC-008=US2.4–8+prueba privacidad FR-019; SC-009=US2.9–14; SC-010=US1.7–10+US2.15+US4.6.

| Criterio original | Cobertura |
|---|---|
| Jira 1, proponer hechos fuera de norma | US1.1, US1.5–10 |
| Jira 2, datos vigentes / IA solo redacta | US1.3–5, US4.4, FR-019 |
| Jira 3, todas cumplen | US1.2, US4.5 |
| Jira 4, editable | US2.1, US2.12, US2.15 |
| Jira 5, aprobación opcional / emitir sin | US2.1–3, US2.9–14 |
| Jira 6, copia inmutable | US3.1–2, US3.6–7 |
| Jira 7, medios consistentes | US3.3–4 |
| Jira 8, plantilla | US4.1–6 |
| Jira 9, históricos intactos | US3.5–6 |

«Jira 1…9» es la posición de los criterios suministrados, no una clave Jira inventada. La referencia real es US 10.2.

## Controles técnicos complementarios obligatorios

- PostgreSQL real, TransactionTestCase/pytest.mark.django_db(transaction=True), conexiones independientes y Event/Barrier, sin sleeps como sincronización: editar frente a emitir; revalidar/recalcular frente a emitir; dos aprobaciones; doble emisión; dos propuestas fuera de orden; cambio de LD/identidad frente al snapshot. Probar rollback, ausencia de Informe parcial y persistencia de invalidación aun cuando se responde 409. A→B→A de Resultado/Validacion deja identidades/fecha distintas; divergencia detectada nunca revive aprobación.
- Revocar grupo/permiso o desactivar durante espera IA: fase B no persiste texto ni aprueba. Incluir Administradores y superusuario sin Bioquímicos. Guardar exige también la política conjunta. CSRF real con Client(enforce_csrf_checks=True); tres POST rechazan GET y acceso directo indebido. Ninguna prueba de permiso reutiliza accidentalmente la misma persona como autorizada y no autorizada.
- Restricciones de BorradorConclusion: fila única, revisión positiva, bloque de seis campos completo/nulo, revisión y hechos concordantes. GET sin fila no crea; GET que detecta obsolescencia invalida pero no toca datos clínicos. No expirar por tiempo; borrador tras proceso interrumpido en reserva sigue recuperable.
- Contar consultas con estudios de 1 y 30 pruebas: select_related/prefetch y locks por conjunto, número acotado independiente de N, sin evaluación perezosa por template. No fijar umbral de milisegundos sin medir; no IA dentro de atomic ni conexión ORM en workers.
- Adaptador: payload sin datos personales, gramática, caracteres hostiles como datos, 64 KiB con respaldo completo sin truncar, capacidad 2 y tercer llamado con respaldo inmediato, respuesta tardía sin escritura y liberación de semáforo solo al terminar worker. Cero registro de prompt/error sensible. Mismo cliente y configuración Groq, tools vacío.
- JS `informes/tests/js/conclusion.test.cjs`: autosave serial, flush antes de acciones/navegación, recarga y recuperación local, input invalida UI, 409 conserva ambas versiones para revisión, respuesta fuera de orden, logout/cambio de sesión limpia cache local, HTML login no es éxito, error de red visible. Usar node:test estándar como el repo. Backend pytest prueba la persistencia y las guardias, JS complementa interacción.
- Texto con tildes, signos <, & y HTML malicioso se conserva como texto escapado, LF consistente, sin strip silencioso; NUL rechazado; no doble bloque de advertencias. PDF real y conclusión multipágina sin recortes; validar HTML pasado al motor y comprobar PDF generado con herramientas ya disponibles, sin añadir parser de PDF como dependencia. Revisión visual del texto extraído/representado para complementar el test de contrato.
- Regresión de informes/asistente/validación/cálculo/envíos: reglas de estudio listo, firma/matrícula, emisión por permiso sin grupo cuando sin conclusión, destinatario actual, confirmación e idempotencia, chat sin nuevas facultades. Fixtures normales usan cargar/validar reales; completar sin Validacion solo para anomalía intencional. empleado y bioquimico pueden ser el mismo objeto en fixtures existentes: crear segundo usuario independiente para US3.7 y negativos.

## Orden y criterios de salida

Caracterizar comportamiento actual → tests de hechos/gramática → persistencia y permisos → carreras y emisión atómica → medios → JS/UI y regresión completa. Cada bloque debe disponer de tests antes de su implementación. No se generan tareas con este documento.

Antes de considerar lista la futura implementación: 38/38 escenarios ejecutados y aprobados, 19/19 FR demostrados, controles de concurrencia/seguridad y medios aprobados; pytest completo PostgreSQL, Ruff, Django, migraciones coherentes, CSS compilado y node:test. CI actual Node 20 enumera directorios y todavía no incluye informes/tests/js: agregar esa ruta en la implementación; no confundir un pase local Node 24 con cobertura del CI. Registrar comandos, commit y resultados reales cuando se ejecuten, sin reutilizar conteos de feature 033.
