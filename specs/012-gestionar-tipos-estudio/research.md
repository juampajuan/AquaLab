# Research — US 5.5 / 012

Fecha: 28/10/2026. Investigación de fase 0 del speckit-plan original. Fuentes: código integrado a95efb46, spec/checklist 012 y contrato consumidor de US 5.1. Dos agentes de investigación realizaron análisis solo lectura de transacciones y UI; sus recomendaciones se revisaron y consolidaron aquí. No ejecutaron cambios ni tests de producto.

## R1 — Base única sin migraciones

**Decisión**: reutilizar pruebas.Prueba, estudios.TipoEstudio/TipoEstudioPrueba y las referencias Estudio/PruebaEstudio existentes. Mantener el lector consumidor catalogo.py y crear módulos administrativos separados en estudios. No se prevén modelos o migraciones nuevos.
**Motivo**: persistencia, unicidad, permiso y snapshots ya entregados; esta historia añade comportamiento de gestión.
**Alternativas**: segundo catálogo, mover tablas o recrear migraciones: rechazadas por duplicar responsabilidades y romper identidades.

## R2 — Servicio único y validaciones por operación

**Decisión**: gestionar_tipo_estudio en gestion_tipos.py es la única entrada de escritura administrativa para crear/editar/desactivar/reactivar/eliminar. Usa atomic y, para tipo existente, lock de fila antes de versión y validaciones. Crear/editar/reactivar exigen conjunto no vacío y referencias válidas. Desactivar/eliminar pueden retirar un tipo legado inválido sin exigir repararlo: no añaden referencias inválidas ni habilitan nuevos estudios. Crear siempre activo; editar conserva activo; disponibilidad solo por acciones explícitas.
**Motivo**: evitar caminos parciales de escritura o transacciones repartidas entre vistas.
**Alternativas**: ModelForm.save, admin genérico o signals como escritor: no garantizan coordinación completa; validación exclusivamente UI: evadible.

## R3 — Versión y no-op

**Decisión**: alta completa version=1. Edición efectiva de nombre (recortado pero conservando mayúsculas), descripción exacta o conjunto de IDs y cambio efectivo de activo incrementan una sola vez; cambios combinados también una vez. Reordenar/deduplicar IDs o recortar solo espacios laterales sin cambiar el nombre almacenado es no-op. Descripción conserva texto, incluida vacía: strip=False en su formulario. Un cambio solo de mayúsculas en nombre sí es efectivo, aunque no sea duplicado de otro nombre.

La versión esperada se comprueba ANTES de validar/no-op. Stale siempre conflicto, incluso si el payload coincide con el estado actual. No-op vigente válido: resultado sin_cambios, sin DML ni incremento. Fallas: rollback de datos, M2M y versión. Eliminar exige versión y uso pero no escribe una versión posterior: la entidad deja de existir. Operación sobre inexistente: error controlado, no recreación.
**Motivo**: publicar una identidad de configuración para los consumidores sin generar conflictos por cambios inexistentes ni aceptar consentimientos antiguos.
**Alternativas**: incrementar cada save/M2M o aceptar stale si coincide: viola semántica de versión y contrato.

## R4 — Locks y eliminación

**Decisión**: el escritor toma solo el lock de su TipoEstudio y lo mantiene hasta terminar datos, composición y versión/eliminación. Crear_estudio ya toma advisory 5_100_001 y luego el mismo lock. US 5.5 nunca adquiere ese advisory después de bloquear el tipo. Una operación modifica un solo tipo; no bloquea sus estudios para borrarlos.

Eliminar: lock tipo → versión → estudios.exists sin filtrar estado/fecha/activo → delete si nunca utilizado. Si crear gana primero, el estudio se ve y borrar rechaza. Si eliminar gana primero, crear espera y rechaza el tipo inexistente. FK y PROTECT son defensa adicional. Eliminar solo borra tipo y through, nunca Prueba, Estudio ni PruebaEstudio.
**Motivo**: mismo protocolo de coordinación, sin nuevo lock global para catálogo ni deadlocks por orden inverso.
**Alternativas**: exists fuera de atomic, bloqueo solo del M2M, advisory global nuevo para todas las ediciones: respectivamente carreras o serialización innecesaria.

## R5 — Autorización

**Decisión**: permiso estudios.gestionar_catalogo en TODOS los GET/POST antes de consultar datos, y en la entrada del servicio. Usar infraestructura login existente y permission_required(..., raise_exception=True): anónimo a login; usuario activo sin permiso 403. Servicio exige usuario autenticado/activo y has_perm. is_staff no es autorización. Superusuarios conservan la semántica de has_perm del backend existente; no se crea rol ni backend nuevo. Enlace oculto sin permiso es solo presentación. No se asignan permisos automáticamente.
**Motivo**: impedir bypass por URL/POST directo y por llamadas internas al escritor.
**Alternativas**: confiar solo en menú, is_staff o permisos model default distintos: no cumple la autorización específica.

## R6 — Confirmación y versión desde apertura

**Decisión**: módulo confirmaciones_tipos.py independiente de US 5.1. Token de contexto de edición ligado a usuario/sesión/acción/tipo/versión capturada al abrir GET; POST preparar conserva esa versión y detecta stale, sin recapturar silenciosamente la actual. Token distinto de fase confirmación liga UUID de borrador, operación, tipo, versión y digest del payload canónico guardado en sesión. Copia inmutable del resumen, mapa por UUID, TTL 3600s y máximo 20 pendientes (decisiones técnicas, no requisitos de laboratorio). Antes de preparar/acceder se purgan borradores vencidos usando metadato temporal de servidor; el límite cuenta solo pendientes vigentes para evitar bloqueo por resúmenes abandonados. Salt separados tipos.edicion.v1 y tipos.confirmacion.v1; huella HMAC con salt propio, nunca sessionid expuesto.

Firma/payload/usuario/sesión/acción/tipo deben coincidir. Confirmar no acepta nuevos campos libres para cambiar lo revisado. Cancelar descarta el UUID; volver conserva propuesta y versión. Un conflicto muestra propuesta y configuración vigente separadas, sin guardar ni sustituir el consentimiento. Revisar nueva base exige GET de edición vigente, preparar y confirmar nuevamente. Expirado/inválido no guarda ni se recupera para escribir: volver a iniciar revisión sin mutar catálogo. No prometer revocar una confirmación concurrente ya iniciada.
**Alternativas**: solo hidden version sin firma; refrescar automáticamente versión al preparar; usar el último borrador global: rechazadas por permitir sobreescrituras o mezclar pestañas.

## R7 — Reintentos y errores

**Decisión**: sin modelo nuevo de idempotencia administrativa. Alta repetida no duplica nombre: UNIQUE es la defensa persistente y un segundo envío puede devolver duplicado. Edición efectiva repetida obtiene conflicto; eliminación repetida, inexistente; no-op vigente puede repetirse sin DML. No prometer el mismo resultado exitoso persistente de US 5.1. El UUID del borrador es identidad UI, no clave persistente de operación del catálogo.

Validación previa mejora errores; constraint tipo_estudio_nombre_unico_ci resuelve carreras de nombres. IntegrityError, ProtectedError y DatabaseError se traducen fuera del atomic fallido; no continuar consultas en una transacción rota. Mensaje de éxito solo al salir del atomic; no autocrear otra solicitud ni reintentar escrituras silenciosamente. Datos deben releerse tras rollback para no mostrar objetos mutados en memoria como persistidos.
**Alternativas**: quitar validaciones para retries o añadir registro persistente no pedido: inseguro o fuera de alcance.

## R8 — Validación y DEMO

**Decisión**: TDD por escenario de spec; PostgreSQL real, django_db(transaction=True), conexiones por hilo, eventos/barreras y timeout en DB/futures para concurrencia. Fixtures sintéticas aisladas. Chrome usa cargador US 5.1 explícito y tipos nuevos [DEMO FIUBA US55], sin alterar el manifiesto base ni inventar definiciones científicas. No se ejecutaron estas validaciones durante plan.
**Alternativas**: SQLite para locks, sleeps como sincronización, datos productivos o nuevas semillas: no acreditan garantías o duplican infraestructura.

## Fuentes primarias consultadas

- [Django 5.2: transacciones y captura de errores fuera de atomic](https://docs.djangoproject.com/en/5.2/topics/db/transactions/).
- [Django 5.2: select_for_update y pruebas transaccionales](https://docs.djangoproject.com/en/5.2/ref/models/querysets/#select-for-update).
- [Django 5.2: autorización por permiso](https://docs.djangoproject.com/en/5.2/topics/auth/default/#the-permission-required-decorator).
- [PostgreSQL 16: bloqueo de filas, deadlocks y advisory locks](https://www.postgresql.org/docs/16/explicit-locking.html).

No quedan incógnitas técnicas bloqueantes para fase 1. La aprobación formal del equipo sigue sin acreditarse y es puerta previa a implementar, no una afirmación obtenida por estos agentes ni por generar plan. Al generar esta investigación, tasks aún no estaba autorizado. Posteriormente el usuario autorizó $speckit-tasks, ya ejecutado con 50 tareas verificadas y pendientes. La implementación sigue sin autorización y la aprobación formal del equipo continúa pendiente (T001). No se modificó código ni se ejecutaron tests de producto en este trabajo documental.
