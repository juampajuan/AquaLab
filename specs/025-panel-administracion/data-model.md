# Modelo de datos previsto — Panel de administración

Diseño posterior a aclaraciones. No se crean modelos paralelos de usuarios, solicitudes, roles ni avisos.

## Usuario existente

| Atributo | Diseño | Regla |
| --- | --- | --- |
| PK, email, nombre, apellido, contraseña y fechas | Sin cambios de identidad/almacenamiento | Conservar normalización y unicidad de email |
| is_active | Booleano existente, etiqueta «Activa» | Habilitación para ModelBackend, default verdadero existente |
| aprobada | Booleano nuevo, default final verdadero | Aprobación previa; no editable libremente |
| version_administrativa | PositiveBigIntegerField nuevo, default 1, no editable | Incremento ante cambios efectivos de estado/rol y ediciones administrativas relevantes |
| groups/user_permissions/is_staff/is_superuser | Sin sustitución | Panel solo modifica pertenencia a Bioquímicos |
| estado_cuenta | Propiedad derivada que devuelve EstadoCuenta, no columna duplicada | Tabla siguiente |

Constraints: `is_active=False OR aprobada=True` y versión >=1, además de unicidad actual de email. No introducir fecha de aprobación desconocida ni historial nuevo; suspender nunca vuelve aprobación a falso.

## Estados

| aprobada | is_active | Estado | Operaciones del panel |
| --- | --- | --- | --- |
| Falso | Falso | Pendiente | Aprobar/rechazar solo desde Solicitudes |
| Verdadero | Verdadero | Activa | Cambiar rol, desactivar salvo cuenta propia |
| Verdadero | Falso | Desactivada | Cambiar rol, reactivar |
| Falso | Verdadero | Inválido | Impedido por constraint |

| Origen | Acción confirmada | Resultado | Aviso |
| --- | --- | --- | --- |
| Sin cuenta | Registro | Pendiente | Solicitud nueva/recibida existentes |
| Pendiente | Aprobar | Activa, versión +1 | Una aprobación tras commit |
| Pendiente elegible sin historial protegido, relaciones impeditivas ni firma | Rechazar | Eliminada, email libre | Un rechazo tras commit |
| Pendiente histórica con referencias protegidas/firma | Intentar rechazar | Rechazo impedido con motivo; conserva todo, sigue Pendiente sin acceso | Ninguno, email no liberado |
| Activa ajena | Desactivar | Desactivada, versión +1 | Ninguno nuevo |
| Desactivada | Reactivar | Activa, versión +1 | No reenviar aprobación |
| Activa/Desactivada | Cambiar rol | Mismo estado, versión +1 si cambia | Ninguno nuevo |
| Cualquiera | Cancelar/token inválido/conflicto | Sin cambio | Ninguno |

No-op sin incremento ni aviso. Propuesta con revisión antigua exige nueva revisión incluso tras A→B→A; resolución ya consumida se informa sin repetirla. Pendientes no se gestionan desde Usuarios y roles.

Tras un rechazo impedido (US2.9), el administrador puede revisar y aprobar la cuenta por la transición normal Pendiente→Activa si corresponde: conserva referencias/firma, incrementa versión y agenda únicamente el aviso de aprobación de esa resolución efectiva. No cambiar estado/versión por el intento de rechazo, no asumir aprobación previa ni activar automáticamente. No relajar PROTECT ni eliminar referencias o firmas para permitir rechazo.

## Migraciones del primer bloque fundacional

0003 y 0004 ya se generaron y validaron forward/backward en PostgreSQL 16 local mediante la base de test; no se aplicaron a bases compartidas ni a la base de aplicación. Ver resultados y límites del incremento en quickstart.md. Los servicios y confirmaciones se implementaron y verificaron en los incrementos posteriores; ver quickstart.md para evidencia actual.

### 0003_estado_aprobacion

Depende de usuarios.0002_alter_usuario_date_joined_alter_usuario_is_active. Una migración atómica agrega aprobación con default temporal falso y versión 1; RunPython con modelos históricos marca aprobada verdadera solo donde is_active es verdadero. Luego fija default final de aprobada verdadero, ajusta etiqueta/ayuda de is_active y agrega constraints. No alterar is_active ni ninguna identidad/referencia/grupo/permiso/contraseña.

| Histórico | Resultado |
| --- | --- |
| Activo | Aprobado y activo |
| Inactivo sin evidencia separada fiable | No aprobado, sigue inactivo y requiere aprobación |
| Superusuario inactivo, con last_login o grupos | Misma regla: esos atributos no prueban aprobación |
| Con referencias anteriores | Misma PK y relaciones; sin activar ni borrar durante migración |

El esquema actual no tiene evidencia independiente fiable de aprobación de inactivos; por ello se aplica la clasificación conservadora a todos. No inferir por actividad ni consultar bases antiguas. Revisar manualmente esos casos mediante el flujo autorizado. Respaldo antes de despliegue; revertir pierde distinción nueva pero no debe activar ni modificar is_active. Tests de migración restauran esquema final.

### 0004_grupo_administradores

Depende de 0003 y estado auth necesario. Meta de Usuario declara `administrar_panel` («Puede administrar el panel de AquaLab»). Crear/resolver permiso con ContentType de Usuario y modelos históricos antes de asignarlo, siguiendo las migraciones Bioquímicos que resuelven post_migrate. get_or_create de Administradores, añadir solo ese permiso sin reemplazar los existentes y sin usuarios.

Reversión: quitar solo la asignación; no borrar grupo con miembros u otros permisos, ni eliminar permiso si está asignado por otras vías. No requiere cambiar Bioquímicos ni dependencias de estudios/informes. Verificar nombres 0003/0004 disponibles al implementar.

## Creación compatible

- Registro público fija aprobada e is_active falsos; hashing y confirmación actuales intactos.
- create_user deriva aprobada del is_active efectivo si no se especifica; activo por defecto conserva altas activas actuales, is_active falso sigue creando pendientes. Rechazar combinación activo sin aprobar.
- create_superuser fuerza ambos verdaderos; no agrega Administradores.
- Alta Django Admin sigue activa/aprobada y sin correo inicial.
- Creaciones directas de Usuario activo son compatibles con default aprobado verdadero; creaciones directas de pendientes deben explicitar aprobada falsa. No inferir aprobación en save al activar: se debe pasar por la transición.

## Relaciones

Administradores y Bioquímicos independientes. Rol profesional deriva de pertenecer o no a Bioquímicos; add/remove conserva otros grupos y permisos individuales. Catálogo Prueba y TipoEstudio sin cambios de esquema o autorización.

Mantener PROTECT de muestras/estudios/mediciones/validaciones/informes hacia Usuario. Comprobar firma profesional antes de rechazar pendientes históricas, pues su relación actual es CASCADE y la clasificación conservadora no habilita perderla.

## Datos efímeros de confirmación

Sesión, sin tabla nueva: UUID del borrador, actor, huella HMAC de sesión, operación, PK objetivo, versión original, instantánea de identidad/estado/rol/grupos/permisos relevantes, propuesta canónica, creación y token firmado. Salt propio, TTL 3600 s, máximo 20 borradores; sin contraseña ni sessionid expuesto.

Al confirmar se verifican firma, identidad, sesión, operación, objetivo y digest. Dentro de atomic se recargan actor/objetivo, se bloquean por PK ascendente, se reautoriza y se compara revisión/instantánea. Solo entonces se aplica transición y se agenda aviso. No mantener transacción abierta mientras el operador decide ni ejecutar SMTP bajo bloqueo.

Panel y admin comparten orden de bloqueo. Guardado de grupos/permisos desde ficha admin incrementa versión en la misma transacción. Cambios globales del permiso de un grupo no requieren incrementar todos los usuarios: se reevalúa autorización del actor al confirmar. SQL manual externo a los canales coordinados queda fuera de la detección universal de ABA.
