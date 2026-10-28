# Contrato UI — gestión de tipos de estudio

Estado: propuesto, no implementado. Templates Django/Bootstrap en español; [servicio](gestion-tipos-servicio.md), [plan](../plan.md). No API REST ni admin editable nuevo.

## Autorización y rutas

Todas las rutas requieren sesión activa y permiso estudios.gestionar_catalogo ANTES de consultar datos, tanto GET como POST y también en el servicio. Middleware/login existente redirige anónimos; permission_required con raise_exception=True responde 403 a autenticados sin permiso. is_staff solo no basta. El backend mantiene sus reglas actuales de superusuario; no nueva política de roles. Verificar permiso de nuevo al confirmar: haber abierto un resumen no lo conserva si fue revocado en una petición posterior.

Propuesta de rutas dentro del namespace estudios, estáticas tipos/ antes de <int:pk>/ existente:

| Ruta | Método | Comportamiento |
|---|---|---|
| /estudios/tipos/ — tipos_listar | GET | Listado paginado 20, orden nombre/pk, disponibilidad, conteo de pruebas y uso informativo. Activos/inactivos; filtro estado=todos/activos/inactivos, default todos. Acciones según estado. Sin mutación de catálogo. |
| /estudios/tipos/crear/ — tipos_crear | GET | Formulario vacío y pruebas existentes; aviso si catálogo Prueba vacío. |
| misma | POST | Validar y preparar resumen, guardar solo borrador de sesión y redirigir al GET de confirmación. Nunca crear tipo aquí. |
| /estudios/tipos/<pk>/editar/ — tipos_editar | GET | Leer configuración administrativa coherente, cargar formulario y token de contexto con versión de apertura. Admitir inactivos sin reactivarlos. |
| misma | POST | Validar contexto de apertura y datos, comparar esa versión; preparar resumen solo si sigue vigente. No refrescar versión automáticamente. |
| /estudios/tipos/<pk>/desactivar/ — tipos_desactivar | GET | Preparar resumen con versión y estado destino fijo; no desactivar. |
| /estudios/tipos/<pk>/reactivar/ — tipos_reactivar | GET | Preparar resumen y validación de pruebas; no reactivar. |
| /estudios/tipos/<pk>/eliminar/ — tipos_eliminar | GET | Resumen con uso informativo y advertencia de eliminación definitiva; si usado explicar rechazo/alternativa. No eliminar. |
| /estudios/tipos/confirmar/?solicitud=UUID — tipos_confirmar | GET | Mostrar copia revisada propia; sin regenerar catálogo/token de forma silenciosa. Borrador ajeno/no disponible: mensaje genérico y listado. |
| /estudios/tipos/confirmar/ — tipos_confirmar | POST | accion=confirmar o cancelar; token válido. Acción de negocio se toma del token/borrador, no de un campo libre. Confirmar llama escritor único. Cancelar retira borrador sin DML de catálogo. |

Limitar métodos (GET/POST declarados); no mutaciones por GET. Sesiones pueden guardar borradores en GET de acciones: la garantía es no mutar tablas de dominio. CSRF en cada POST; ningún enlace GET confirma ni guarda por sí solo.

## Formularios y revisión

TipoEstudioForm: nombre requerido <=150, strip=True; descripcion opcional Textarea strip=False; pruebas ModelMultipleChoiceField requerido sobre Prueba existente (orden código/pk), sin campo Prueba.activo inexistente. Sin activo/version/usuario/snapshots editables. Unicidad al crear/editar excluye la PK propia; no confundir validación previa con defensa de base.

Resumen muestra nombre/descripcion, pruebas código/nombre y estado/disponibilidad relevantes, operación y versión revisada; eliminación muestra identidad/uso e irreversibilidad sin prometer que el conteo quede vigente. Volver conserva propuesta y versión. Repreparar crea borrador/token nuevos e invalida el anterior después de validar correctamente, sin confundir pestañas. Solo confirmar modifica catálogo. Éxito/no-op después del servicio redirige al listado con mensaje específico; formulario no guarda mediante ModelForm.save.

## Tokens de fase y conflictos

- Contexto firmado desde GET de edición: fase, usuario, HMAC sesión, tipo, acción, versión de apertura. Salt tipos.edicion.v1; en alta no hay versión de entidad. Nunca aceptar un token de contexto como confirmación.
- Borrador UUID en tipos_pendientes: propuesta canónica, copia íntegra de resumen y versión. Token con salt tipos.confirmacion.v1 contiene fase, UUID, usuario, huella, tipo, acción, versión y digest SHA256 del JSON canónico; usar Django signing y HMAC de sesión con salt propio. No exponer sessionid ni aceptar hash suministrado como prueba de identidad.
- TTL 3600s en ambas fases; guardar creado_en de servidor y purgar borradores expirados al acceder/preparar antes del máximo de 20 pendientes vigentes. No quedar bloqueado por 20 resúmenes abandonados. Expirado o inválido: mensaje y nueva revisión explícita, ninguna escritura. No añadir recuperación automática con semántica distinta de US 5.1.
- POST confirmar verifica firma/TTL/identidad/digest, permiso vigente, borrador pendiente y coincidencia de acción/tipo/versión. Campos extra no alteran lo revisado. El servicio revalida datos/reglas de negocio bajo lock.
- Conflicto al preparar o confirmar: mostrar propuesta anterior y configuración vigente separadas, con versión vigente informativa. No guardar ni reemplazar silenciosamente el consentimiento antiguo. El usuario debe abrir/revisar nueva base, preparar una propuesta nueva y volver a confirmar; el token anterior sigue inválido por versión.
- Tipo eliminado: 404 en su apertura o error controlado al confirmar; no recrear. Tipo usado al confirmar borrar: rechazo y enlace a preparar desactivación. Error de base: mensaje sin éxito, conservar propuesta recuperable para volver/revisar; si expiró o ya no existe, iniciar nueva revisión explícita.
- Cancelar invalida el UUID pendiente; un token cancelado no crea ni modifica nada al reenviarlo. No revoca una petición concurrente ya iniciada. Tras éxito se descarta borrador; si dos confirmaciones ya estaban en vuelo, UNIQUE/versión/protección del servicio son la defensa, no la sesión.

## Resultados HTTP propuestos

GET válidos y formularios con errores: 200. Preparación y éxito/cancelación: redirección 302 a resumen/listado. Sin permiso: 403; CSRF: 403; entidad ausente al abrir: 404; método no permitido: 405. Conflicto se renderiza como 200 con mensaje y sin guardado (convención HTML del proyecto), no como éxito ni sobrescritura. Falta/invalidación de token: mensaje seguro y redirección a listado/revisión propia. No exponer existencia o datos a usuarios sin autorización.

## Navegación y compatibilidad

Enlaces en base.html/inicio.html solo si perms.estudios.gestionar_catalogo. No cambiar crear_estudio, consultar estudios ni sus permisos actuales. Editar composición de tipo no es agregar/quitar pruebas de un estudio (US 5.3/5.4). Los nombres/rutas aquí son propuestas de diseño para revisión, no endpoints ya disponibles.
