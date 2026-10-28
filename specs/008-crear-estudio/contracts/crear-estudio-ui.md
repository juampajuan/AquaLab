# Contrato UI: Crear estudio

> Estado vigente de cierre: implementación y 40/40 tareas completadas; recorrido Chrome y carga demo confirmados por el usuario, sin observación directa del asistente. Detalle y límites en [cierre-tecnico.md](../cierre-tecnico.md). Las notas de evolución anteriores se conservan como historial. Sin commit ni PR.

Contrato de rutas y comportamiento implementado. Extiende base.html con guardia de sesión existente; sesión activa y CSRF obligatorios.

| Ruta/acción prevista | Resultado |
|---|---|
| GET /estudios/crear/ | Formulario vacío con muestras registradas (incluidos clientes inactivos), etiqueta PI/cliente/origen y tipos activos; sin crear registros. |
| POST /estudios/crear/ | Validar selección; inválido devuelve errores por campo. Válido prepara UUID y configuración coherente, borrador de edición y token firmado, redirige al resumen. |
| GET /estudios/crear/confirmar/ | Resumen de selección, nombre/descripción del tipo y conjunto de pruebas revisado, Confirmar/Volver/Cancelar. No regenerar silenciosamente el token de versión vieja al procesar un POST viejo. |
| POST confirmar | Token firmado identifica exactamente la versión revisada; aplicar protocolo transaccional del plan. Éxito redirige a formulario vacío con estudio ID y PI; UUID repetido devuelve mismo ID. |
| POST confirmar con versión vieja | Sin creación; mensaje de cambio, resumen nuevo completo y token nuevo, mismo UUID lógico. Nueva confirmación necesaria. |
| GET volver/editar | Recuperar selección; una edición enviada válidamente se trata como nueva solicitud con UUID nuevo. No modificar un estudio ya creado. |
| POST cancelar | Descartar borrador local de la solicitud y volver al formulario, sin filas nuevas. No se promete revocar una confirmación que ya se envió simultáneamente desde otra pestaña; una cancelación no borra estudios ya confirmados. |

Token: Django signing salt estudios.creacion.v1, TTL 3600s, campos UUID, usuario, huella HMAC de sesión, muestra_id, tipo_id y version. Firma/TTL/usuario/sesión se verifican antes del servicio. No incluir sessionid literal; token firmado no es cifrado. Ningún snapshot del POST se guarda como fuente autorizada.

Errores: faltantes por campo; tipo inexistente/inactivo/vacío informa no disponible; conflicto de catálogo informa cambio y exige nuevo resumen; firma inválida/ajena/vencida rechaza sin crear y ofrece volver a revisar; DatabaseError informa fallo sin éxito y permite reintento. Mostrar solo datos accesibles al empleado, nunca revelar otra solicitud al reutilizar claves.

Permisos: cualquier cuenta activa autenticada crea estudios. gestionar_catalogo es exclusivo de administración futura de tipos, no requisito del alta de estudios; no nuevas asignaciones de roles ni admin de catálogo.

Reenvío del mismo token tras éxito: hasta expirar se reconoce por UUID y devuelve mismo estudio incluso si el tipo cambió o quedó inactivo; verificar primero usuario/muestra/tipo, no revalidar versión para crear de nuevo. Token expirado nunca crea automáticamente otra solicitud. No se garantiza sobrevivir logout/session rotation; se vuelve a revisar sin alterar registros existentes.

## Continuidad de la solicitud y cancelación

El borrador de edición se identifica por UUID dentro de un mapa de solicitudes pendientes en sesión, para no confundir pestañas. Confirmar una solicitud todavía no registrada requiere además que siga pendiente; borrar el borrador al cancelar impide usar después su token para crear. Primero se reconoce un resultado ya persistido que corresponda al mismo usuario/selección; no se exige que siga pendiente para devolver ese resultado. La sesión no es la garantía de idempotencia, que sigue en la clave única y el lock de base. No se promete revocar un request que ya comenzó concurrentemente antes de cancelar.

Un token vencido nunca se usa para crear. Si su firma criptográfica sigue siendo válida y se identifica la misma solicitud/usuario/sesión, la recuperación solo permite consultar el resultado propio existente o volver a revisar una solicitud aún pendiente y emitir un token vigente conservando el mismo UUID. La comprobación de firma para recuperar identidad no equivale a aceptar un token vencido para guardar. Una solicitud nueva con otro UUID requiere una acción deliberada; no se genera automáticamente otro UUID por timeout o reintento tardío. Si no puede recuperarse la identidad, se informa que la solicitud no es recuperable y no se crean registros sin iniciar explícitamente otra operación.

## Precisiones de revisión técnica antes de tasks

Al preparar un resumen, leer bajo bloqueo del tipo una configuración completa y guardar en sesión por UUID los textos, referencias de pruebas y versión que se mostrarán. El GET del resumen muestra esa copia revisada, no combina catálogo actual con token de versión anterior. Si se desea refrescar, regenerar juntos resumen y token mediante lectura coherente. El servicio copia al confirmar desde catálogo bloqueado solo si coincide la versión firmada; una lista de pruebas enviada libremente por el cliente no es autoridad.

POST /estudios/crear/confirmar/ con accion=recuperar es la única vía de recuperación de un token expirado: comprueba firma sin aceptar su antigüedad como autorización de escritura, sesión/usuario/selección, y devuelve resultado propio existente o nuevo resumen con el mismo UUID pendiente y token vigente. accion=confirmar con token expirado siempre rechaza la creación y ofrece recuperar. Token con firma inválida o de otra identidad no permite lookup de resultados. Cancelar retira UUID del mapa pendiente; recuperar no revive solicitudes canceladas. Una solicitud deliberada nueva o una selección editada recibe otro UUID.

La identidad de operación para reutilizar UUID persistido es creador + muestra + tipo. La versión no se compara con el catálogo actual al devolver un éxito anterior, porque el UUID también se mantiene al refrescar un resumen antes de crearse. Nunca se devuelve un estudio de otra identidad ni se sobrescriben autor, hora o snapshots al reintentar.
