# Contrato de interfaz y servicios — Administración

Contrato aprobado e implementado; pruebas y resultados en testing-matrix.md y quickstart.md. Namespace `administracion`, include desde config/urls.py a usuarios/urls_administracion.py. HTML Django, sesión y CSRF actuales. `/admin/` sigue siendo exclusivamente Django Admin.

## Rutas implementadas

| Ruta bajo /administracion/ | Nombre | Métodos y resultado |
| --- | --- | --- |
| solicitudes/ | solicitudes | GET 200: pendientes, identidad, Aprobar/Rechazar y estado vacío |
| solicitudes/<pk>/aprobar/ | aprobar | GET 200: confirmación; POST confirmar/cancelar |
| solicitudes/<pk>/rechazar/ | rechazar | GET 200: consecuencias y confirmación; POST confirmar/cancelar |
| usuarios/ | usuarios | GET 200: identidad, rol, estado y acciones permitidas |
| usuarios/<pk>/rol/ | cambiar_rol | GET formulario; POST revisar/confirmar/cancelar |
| usuarios/<pk>/desactivar/ | desactivar | GET confirmación; POST confirmar/cancelar |
| usuarios/<pk>/reactivar/ | reactivar | GET confirmación; POST confirmar/cancelar |
| pruebas/ | pruebas | Solo GET 200; q y page como parámetros |

No agregar endpoint de edición de pruebas, creación de usuarios, edición de grupos/permisos o gestión de Administradores.

## Autorización por canal

| Actor autenticado activo | Nuevo panel GET/POST | Gestión de tipos | Django Admin |
| --- | --- | --- | --- |
| Administradores y permiso administrativo asignado | Permitido | Solo si posee gestionar_catalogo | Solo con condiciones admin actuales |
| Administradores sin permiso asignado | 403 | Según permiso propio | Según política original |
| Permiso administrativo sin Administradores | 403 | Según permiso propio | Según política original |
| Ninguno | 403 | Según permiso propio | Según política original |
| Superusuario fuera de Administradores | 403 | Semántica vigente de Django | Acceso normal de superusuario |
| Superusuario en grupo pero sin asignación administrativa real por ninguna vía | 403 | Semántica vigente de Django | Acceso normal de superusuario |
| Solo gestionar_catalogo | 403 | Acceso directo conservado | No se concede acceso |

Sin sesión, redirección al login vigente con next. Cuenta desactivada deja de autenticarse mediante el backend actual, incluso con cookie anterior. Para un actor autenticado no autorizado, comprobar política antes de buscar el objetivo: no revelar si existe. CSRF sigue activo; la matriz 403 de autorización usa tokens CSRF válidos para aislar ese control. Métodos no admitidos devuelven 405 tras el control de acceso.

Tipos conserva `estudios:tipos_*`, permission_required y `estudios.gestionar_catalogo`, sin segundo permiso. Menú Administración aparece con la política conjunta; el enlace de tipos aparece dentro solo con su permiso. La tarjeta de Inicio y el acceso directo de gestores se conservan.

## Consultas y presentación

- Solicitudes: filtro aprobada falsa e is_active falso, orden -date_joined/-pk, 20 por página. Activas/desactivadas excluidas. Nombre, apellido y correo; sin contraseñas ni datos de seguridad.
- Usuarios: todos los estados, orden por apellido/nombre/email/PK y 20 por página. Rol derivado de Bioquímicos mediante Exists o prefetch sin N+1. Pendientes solo muestran acceso a Solicitudes, sin acciones de rol/estado. Cuenta propia no ofrece desactivación.
- Pruebas: Q(codigo__icontains=q) OR Q(nombre__icontains=q), q con espacios exteriores recortados, orden codigo/PK, 20 por página, preservando q. Vacío recupera todo. Sin filtro implícito de activa ni edición por POST.
- Cada prueba muestra código, nombre, tipo de cálculo legible, unidad del resultado y activa/inactiva. Filtro `unidad` existente convierte vacío/-- a «Sin unidad».
- Enlace a reverse(admin:pruebas_prueba_change, args=[pk]) siempre como destino solicitado. No dar is_staff ni permisos de edición; destino conserva redirecciones/403/restricciones propias y protección de código/nombre de pruebas usadas.
- Reutilizar base.html, ui/encabezado, campo, estado, estado_vacio, mensajes, acciones_confirmacion y paginacion; estilos de tabla/tarjeta/btn existentes. Botones y mensajes en español, foco/labels y aria-current como pantallas actuales.

SC-005 se valida sobre flujos directos desde listado: aprobar/rechazar/desactivar/reactivar abren confirmación y confirman (dos acciones). Para rol, Cambiar rol abre una pantalla independiente con el rol actual y las alternativas disponibles, excluyendo el rol actual. La única alternativa profesional actual queda preseleccionada: Cambiar rol, Continuar y Confirmar permiten completar el flujo en tres acciones. El contexto firmado se emite en esa pantalla; el listado no contiene selectores ni formularios inline. La propuesta no se guarda hasta la confirmación final.

## Confirmaciones

Campos POST permitidos: accion, token/contexto firmado y, solo al revisar rol, rol profesional con opciones común/bioquímico. PK/operación de URL deben coincidir con la firma. No aceptar aprobada, is_active, is_staff, is_superuser, grupos libres o permisos como propuesta del panel. Un envío manipulado se rechaza sin aplicar campos extra.

GET muestra identidad y consecuencias y emite contexto/token; no modifica dominio ni envía avisos. POST revisar valida rol, original firmado y estado, guarda borrador en sesión y muestra resumen. POST confirmar verifica firma/digest/sesión/actor/objetivo/acción/TTL y, dentro de atomic, autorización vigente y revisión/instantánea bajo bloqueo. POST cancelar descarta borrador sin cambiar dominio ni avisar.

La confirmación identifica cuenta, estado/rol anterior y propuesto. Rechazo explica eliminación y liberación de email exclusivamente si la solicitud es elegible y la resolución efectiva. Ante historial protegido, referencias impeditivas o firma, informar el impedimento y conservar cuenta/correo/historial, sin aviso ni cambio de estado/versión; no relajar PROTECT ni borrar referencias/firmas. Mantener disponible la revisión y aprobación normal posterior si corresponde, sin activación automática. Desactivación explica suspensión conservando datos. Sin transacción abierta entre pantallas. Token con salts propios, TTL 3600 s y límite 20; nunca sustituye autorización ni se expone sessionid.

| Situación | Respuesta observable |
| --- | --- |
| Confirmación efectiva | 302 al listado y mensaje de éxito; callback solo si corresponde |
| Cancelación | 302 al listado, sin cambios ni aviso |
| Formulario inválido | 200 con errores, sin transición |
| Firma ajena/alterada/caducada/borrador consumido | 302 al listado y aviso para iniciar revisión; sin cambio |
| Revisión/instantánea desactualizada | 302 al listado con aviso de cambio y revisión obligatoria |
| Solicitud ya resuelta | Mensaje «ya no está pendiente», sin transición ni aviso duplicado |
| Objetivo inexistente en GET autorizado | 404 |
| Eliminado después de revisar | Volver al listado con aviso de ausencia, sin transición |
| Pendiente enviada a rol/activación/desactivación | Mensaje de usar Solicitudes, sin cambios |
| Desactivación propia | Operación impedida con explicación, también llamando servicio |
| Pendiente histórica con historial protegido, referencias impeditivas o firma | Rechazo impedido, motivo informado; conserva cuenta, correo, referencias, firma e historial, sigue Pendiente sin acceso ni aviso; permite revisar/aprobar por flujo normal si corresponde |
| Error de persistencia | Rollback; mensaje de reintento, sin callback de éxito |
| Falla de correo tras commit | Decisión conservada y log existente, sin reintento automático nuevo |

## Contrato interno de dominio

Módulos implementados: permisos_administracion, servicios_administracion, confirmaciones_administracion, forms_administracion y views_administracion dentro de usuarios.

| Servicio público | Canal y precondiciones | Efecto |
| --- | --- | --- |
| aprobar_solicitud_panel | Política conjunta, pendiente, revisión vigente | Activa/aprobada, versión +1, aviso aprobación |
| rechazar_solicitud_panel | Política conjunta, pendiente sin historial, revisión vigente | Elimina y avisa tras commit |
| cambiar_rol_panel | Política conjunta, previamente aprobada, versión vigente | Solo add/remove Bioquímicos |
| cambiar_estado_panel | Política conjunta, previamente aprobada, versión vigente | Suspende ajena o reactiva, sin aviso inicial |
| resolver_solicitudes_admin | Staff activo + change/delete por operación | Mismo núcleo y avisos, IDs ordenados; no exige grupo nuevo |
| guardar_cuenta_admin | Staff activo + change, ficha validada/revisión vigente | Guarda propuesta fresca y aplica transición compartida sin doble guardado |

Los adaptadores admin no se exponen como rutas del panel ni se seleccionan con un parámetro del cliente. El núcleo privado recibe filas bloqueadas y aplica las mismas invariantes. Autorización no queda solo en decoradores o templates.

Orden: autorizar entrada; atomic; bloquear actor y objetivos en orden PK; recargar y reautorizar actor; comparar originales; validar transición/prohibición propia/historial; persistir y actualizar revisión; agendar callback; commit; limpiar borrador y redirigir. No llamar SMTP mientras se sostienen bloqueos.

En ficha admin, wrapper changeform_view obtiene el bloqueo antes de crear/formar objeto. UsuarioChangeForm valida contexto/versionado y prepara aprobada coherente para constraints. guardar_cuenta_admin recibe los campos validados y el original fresco, persiste una sola vez y agenda solo la transición inicial. save_model no vuelve a guardar después una instancia vieja; save_related guarda M2M e incrementa revisión por cambios relevantes. Altas siguen la vía actual sin avisos. Aprobación masiva/ficha/panel comparten núcleo y no duplican callbacks.

La versión aumenta en toda transición efectiva de estado/rol de panel/admin y en cambios de grupos/permisos de la ficha. Snapshot de identidad y membresías detecta cambios ajenos visibles; permisos actuales del actor se consultan de nuevo para revocaciones. No se añade un sistema de auditoría ni garantía de serialización de SQL manual externo.

## Compatibilidad de login y notificaciones

Registro público crea pendiente explícita y conserva los dos avisos actuales. Login mantiene backend y ruta; con contraseña correcta, pendiente conserva su mensaje y desactivada muestra suspensión. Con contraseña incorrecta/no existente no se revela estado ni se omite la comprobación real/ficticia existente.

Se mantienen avisar_aprobacion y avisar_rechazo, sus plantillas y logger; emisores se agendan únicamente en el núcleo por transición efectiva. Solicitud nueva sigue notificando superusuarios activos y conserva enlace admin según la spec. Sin nuevos destinatarios, señales, cola o almacenamiento de avisos.
