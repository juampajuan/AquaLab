# Modelo de datos — US 10.2

Diseño futuro, no modelos ni migraciones generados. Se agrega una sola tabla en `informes`. No se alteran Estudio, Resultado, Validacion, Informe o EnvioInforme ni se reescriben copias históricas. Ver decisiones [R2–R10](research.md).

## BorradorConclusion — nueva entidad persistente

Una fila compartida por estudio, creada por el primer POST válido de propuesta/guardado, no por abrir la vista previa. La autorización no se concede por ser autor del borrador: todas las acciones nuevas exigen la política conjunta aprobada.

| Campo propuesto | Tipo y restricción | Semántica |
|---|---|---|
| estudio | OneToOneField(Estudio), on_delete=PROTECT, obligatorio | Identidad de la conclusión en preparación; sin borrador por usuario. |
| revision | PositiveBigIntegerField, default=1, revision >= 1 | Versión de concurrencia de toda la fila. Aumenta al editar, reservar/finalizar propuesta, invalidar por hechos o aprobar; nunca se reduce. |
| texto_editorial | TextField, blank=True, default='' | Texto editable, sin máximo funcional nuevo. Unicode conservado, CRLF→LF antes de mostrar/guardar, sin strip silencioso; rechazar NUL, que no admite PostgreSQL. |
| texto_final | TextField, blank=True, default='' | Materialización exacta de texto editorial + advertencias canónicas, con LF. Es el texto visto y aprobado, no se reconstruye al emitir. |
| hechos | JSONField, default=dict | Documento canónico schema='1', solo dict/list/textos; sin floats ni datos de contacto. |
| huella_hechos | CharField(max_length=64), obligatorio, hexadecimal SHA256 en minúsculas | Hash del JSON canónico del estudio completo, no solo de las pruebas citadas. |
| advertencias | JSONField, default=list | Lista canónica por prueba, motivos y hechos conocidos; no editable por el navegador. |
| requiere_revision | BooleanField, default=False | Indica cambio de fuentes detectado: conserva texto previo pero exige revisarlo contra las fuentes actuales. No sustituye el chequeo de hashes. |
| origen_propuesta | CharField(max_length=10), choices=ia/plantilla/manual, obligatorio | Procedencia de la propuesta actual. Guardar una edición no borra la procedencia; primera escritura manual usa manual. |
| motivo_respaldo | CharField(max_length=24), blank=True, default='' | Código: sin_configuracion/no_disponible/cuota/respuesta_invalida/plazo/capacidad/tamano; vacío si no hubo respaldo. Nunca cuerpo HTTP o error con secretos. |
| solicitud_propuesta | UUIDField(null=True, blank=True) | Token de la última reserva de propuesta; no es autorización ni fecha de expiración. Permite descartar una respuesta que ya no corresponde. |
| editado_por | FK Usuario, PROTECT, obligatorio | Último actor de cambio explícito. Invalidación derivada no se atribuye falsamente a otro usuario. |
| fecha_edicion | DateTimeField, obligatorio | Fecha de la última escritura; no funciona como expiración. |
| aprobada_por | FK Usuario, PROTECT, null=True | Aprobador original, distinto del emisor cuando corresponda. |
| nombre_aprobador | TextField(blank=True, default='') | Nombre profesional o identificador local congelado al aprobar; no se obtiene del perfil al emitir. |
| fecha_aprobacion | DateTimeField(null=True) | Fecha de aprobación de esa versión; no caduca por tiempo. |
| revision_aprobada | PositiveBigIntegerField(null=True) | Debe ser igual a revision cuando hay aprobación vigente. |
| huella_texto_aprobado | CharField(max_length=64, blank=True, default='') | SHA256 UTF-8 de texto_final exacto, no de su HTML ni de texto editorial solo. |
| huella_hechos_aprobados | CharField(max_length=64, blank=True, default='') | Huella de los hechos revisados. |

Restricciones BD futuras: unicidad OneToOne; revision >= 1; los seis campos de aprobación están **todos ausentes o todos completos**: aprobada_por/fecha_aprobacion/revision_aprobada usan NULL; nombre_aprobador/huella_texto_aprobado/huella_hechos_aprobados usan cadena vacía y columnas NOT NULL; si completos, revision_aprobada=revision y huella_hechos_aprobados=huella_hechos; no puede coexistir aprobación con requiere_revision=True. Validación de formato de hashes, JSON y correspondencia de texto_final se realiza también en formulario/servicio. No registrar este modelo en un admin genérico que permita aprobar, editar aprobación o saltar su servicio.

El guardado o propuesta se realiza aun sin firma profesional; aprobar tampoco agrega ese requisito. Firma/matrícula siguen exigidas por emisión existente. Definir Meta.default_permissions=() en la entidad nueva para no generar permisos automáticos add/change/delete/view ni permisos custom: sus acciones usan grupo Bioquímicos + permiso efectivo existente `informes.emitir_informes`.

## Documento de hechos canónicos

Recolector nuevo: `informes/conclusion_hechos.py`. Contenido y origen:

| Parte | Campos conservados | Fuente |
|---|---|---|
| Encabezado | schema='1', estudio_id | Estudio; sin cliente, domicilio, email, documento ni identidad de usuarios. |
| Identidad por prueba | asignacion_id, prueba_id, codigo, nombre, estado_asignacion | PruebaEstudio y Prueba; identidad, no fuente de límites/evaluación. |
| Resultado | resultado_id, fecha_calculo, valor exacto, unidad, formula, curva_id | Resultado asociado, si existe; todos como textos. |
| Validación | validacion_id, fecha_validacion, limite_min, limite_max, norma, origen_limites, evaluacion | Solo Validacion vigente y asignación completada; nunca historial anulado ni fallback del catálogo. |
| Presentación auxiliar | resultado_texto, unidad_texto, limite_texto, ld_auxiliar | Formateadores existentes; LD actual solo para presentación de un resultado con vigente, según R2. No determina cumplimiento ni reemplaza límite/norma validado. |
| Disponibilidad | motivos, clase_conclusion | Calculada por AquaLab desde ausencia de vigente/resultado, evaluación guardada y norma vacía; ninguna clase viene de IA. |

Ausencias: usar texto vacío para un dato ausente y motivos explícitos, nunca ID o evaluación fabricados. Si no hay vigente, sus campos normativos quedan ausentes aunque el catálogo tenga valores. Si hay vigente sin norma, conservar evaluación/valor/límite conocidos y advertir sin_norma. Si la evaluación guardada es sin_limite, advertir sin_limite_comparable; no reinterpretar límites textuales para decidir cumplimiento.

Listas ordenadas por código y pk de asignación; motivos por orden fijo sin_validacion, sin_resultado, sin_limite_comparable, sin_norma. `todas_cumplen` solo si hay pruebas y todas son evaluables y su evaluación vigente es cumple. Las que carecen de información se identifican como no evaluables para la conclusión, conservando su evaluación registrada si existe; no se modifica esa evaluación en BD.

JSON serializado con claves ordenadas, separadores fijos y ensure_ascii=False. Todos los escalares se convierten a textos, fechas ISO con zona, Decimal con str, sin transformaciones de valor. El hash incluye identidades y fecha_calculo: dos validaciones distintas con iguales números no son los mismos hechos. No incluir datos de aprobación ni los límites/norma actuales del catálogo; tampoco el estado global finalizado→informe_generado, que cambia por la propia emisión.

## Advertencias y texto exacto

`advertencias` mantiene una entrada por prueba no evaluable con todos sus motivos y hechos conocidos; el renderizador produce un bloque legible que identifica código/nombre y ausencias. Ese bloque se incorpora a texto_final antes de mostrar la confirmación de aprobación. El campo editable contiene la parte editorial; el bloque de advertencias permanece visible y protegido. Las pruebas no evaluables con hechos parciales se describen en ese bloque una vez; la IA no debe duplicarlas en bloques editoriales.

Las afirmaciones automáticas de estado y las advertencias son de AquaLab. La edición profesional no cambia evaluaciones ni permite activar un cierre automático de cumplimiento total si hay no evaluables. El texto humano libre no se pasa a la gramática restrictiva de IA: su revisión es responsabilidad profesional. Conservar las advertencias evita que una edición de la parte editorial las elimine.

## Transiciones y control optimista

| Operación | Precondición | Cambio persistente |
|---|---|---|
| Cargar sin fila | Empleado autenticado consulta vista previa disponible | Sin creación. Usuario no autorizado no recibe el editor ni el borrador mutable. |
| Cargar fila autorizada | Comparar huella actual bajo lock | Si difiere: actualizar hechos/advertencias, preservar texto editorial, materializar texto_final, revision++, requiere_revision=True y vaciar aprobación (NULL en los tres campos nullable y cadena vacía en los tres textos)/token. Es invalidación derivada; no modifica datos clínicos. |
| Guardar | Ambas autorizaciones, estudio no emitido/disponible, revision_esperada y huella vista actuales | Crear si revisión esperada=0 y no hay fila, o revision++; texto nuevo, texto_final materializado, actor/fecha; vaciar aprobación (NULL en los tres campos nullable y cadena vacía en los tres textos)/token. Reintento exacto sin cambio puede ser no-op solo si el token de revisión sigue actual. |
| Reservar propuesta A | Mismas guardias, fuentes y revisión actuales | Crear o revision++, vaciar aprobación (NULL en los tres campos nullable y cadena vacía en los tres textos), token UUID nuevo; conservar editorial anterior como borrador y sus hechos actuales reconciliados. Capturar hechos/revisión/token para fuera de la transacción. |
| Finalizar propuesta B | Token/revisión/fuentes aún coincidentes; reautorizar; estudio no emitido | revision++, instalar texto generado o plantilla, hechos/advertencias y texto_final, origen/motivo, requiere_revision=False; limpiar token. Nunca aprobar. |
| Respuesta vieja | Alguna precondición de B difiere | 409; no instalar texto o plantilla sobre la revisión nueva. |
| Aprobar | Ambas autorizaciones, revisión y huellas vistas iguales a lo almacenado y fuentes actuales; confirmación expresa, texto_final no vacío | revision++; bloque de aprobación completo para nueva revisión y hashes exactos; requiere_revision=False, token nulo. No alterar texto ni reconstruirlo con otras fuentes después de aprobar. |
| Emitir con conclusión | Revisión aprobada solicitada, ambos permisos del emisor y aprobación aún coincidente bajo lock | Copiar fragmento autosuficiente al Informe en su transacción existente; estudiar datos una sola vez bajo bloqueo. No cambiar texto aprobado. |
| Emitir sin conclusión | Reglas existentes de emisión | Omitir clave conclusion; ninguna validación del borrador puede impedir este camino. |

Reconciliar fuentes antes de comparar la revisión del cliente; si la reconciliación cambia revisión, devolver conflicto con el texto preservado y fuentes actuales. Nunca incluir un texto porque la aprobación «volvió a coincidir» después de una divergencia detectada. Una nueva propuesta invalida incluso si termina en el mismo texto. No se define vencimiento temporal ni se reutilizan max_age de otros borradores.

El token pendiente no reserva el estudio ni bloquea nuevas ediciones/aprobaciones. Si el proceso se interrumpe tras A, queda el texto previo sin aprobación; una nueva propuesta o edición explícita puede continuar y hace inútil el token anterior.

## Fragmento opcional en Informe.contenido

Nuevo contrato schema='1' bajo `conclusion` únicamente cuando se emitió con aprobación vigente:

- `texto`: copia exacta de texto_final aprobado, incluidas advertencias.
- `advertencias`: lista de las advertencias aprobadas; solo para trazabilidad, no para volver a agregarlas en templates.
- `revision`, `huella_texto`, `huella_hechos`, `origen_propuesta`: textos.
- `aprobacion`: aprobador_id, nombre mostrado y fecha ISO; el nombre se copia al aprobar, no se consulta dinámicamente al mostrar el emitido. Usar nombre profesional o identificador local, no enviar esa identidad a IA.
- `hechos`: snapshot anterior con sus validacion_id y ausencias explícitas.

Todos los escalares son str, preservando el contrato de textos de armar_contenido. El bloque de aprobación conserva nombre_aprobador desde la aprobación, como se define arriba. No atribuir al emisor la aprobación de otro usuario. El emisor continúa registrado por Informe.emitido_por y su firma según el flujo actual.

No usar referencias vivas para representar esta copia. Si falta la clave conclusion, las salidas mantienen exactamente el comportamiento anterior. La migración futura solo crea BorradorConclusion: no completa ni altera Informe.contenido existente, no inventa validaciones y no agrega datos retrospectivos.

## Persistencia y concurrencia

Orden obligatorio uniforme: Estudio → Borrador → asignaciones por pk → Prueba por pk; advisory de numeración después, solo al emitir. La fila de Estudio serializa también la creación del OneToOne ausente. select_for_update en consultas separadas evita el outer join nullable de Resultado/Validacion. Los servicios actuales de resultados ya toman Estudio primero; no se cambia su regla.

Capturar hechos y copiar el contenido bajo los mismos locks de la rama con conclusión. Las filas Prueba se bloquean para impedir que cambie LD auxiliar o identidad entre verificación y snapshot. Ninguna llamada IA posee conexiones ORM o locks. La huella actual y las identidades/versiones de Resultado/Validacion son la garantía para las escrituras normales; no se promete detectar el historial de un LD auxiliar que cambió y volvió sin observación intermedia. Ver [R6](research.md).

## Adaptación técnica autorizada — 2026-11-16

El responsable autorizó representar ausencia en los tres textos mediante blank=True, default='' y sin null=True para cumplir Ruff DJ001 sin supresiones. No cambia el acto de aprobación ni su trazabilidad: constraint SQL exige simultáneamente tres NULL + tres cadenas vacías, o tres valores no nulos + tres textos no vacíos. Revisión/huella de hechos y requiere_revision conservan sus constraints. 0006 se revierte y reaplica solo en aqualab_us102 antes de publicarse; no se reescriben migraciones anteriores ni datos históricos.
