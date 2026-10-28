# Data model — reutilización de base US 5.1 / US 5.5

Estado: diseño para revisión, sin código nuevo ni migraciones generadas/aplicadas. Base a95efb46. La propiedad funcional de catálogo corresponde a US 5.5; la persistencia ya fue entregada por US 5.1. No cambiar nombres de tablas, PK, relaciones o migraciones iniciales.

## Entidades existentes

| Entidad/campo | Constraint existente y contrato a respetar |
|---|---|
| pruebas.Prueba.id | BigAutoField, identidad estable. |
| Prueba.codigo | CharField(50), obligatorio, unique exacto, espacios laterales recortados; Check no vacío. |
| Prueba.nombre | CharField(150), obligatorio, recortado; Check no vacío. |
| estudios.TipoEstudio.id | BigAutoField, identidad estable. |
| TipoEstudio.nombre | CharField(150), obligatorio, recortado; UniqueConstraint Lower(nombre), Check no vacío. Mayúsculas no distinguen para unicidad; tildes y espacios internos sí. |
| TipoEstudio.descripcion | TextField(blank=True, default=""), no NULL; opcional. No introducir límite de caracteres o contenido científico nuevo. |
| TipoEstudio.activo | BooleanField(default=True). No editable desde formulario general; acciones explícitas cambian disponibilidad. |
| TipoEstudio.version | PositiveBigIntegerField(default=1, editable=False), Check >=1. No incremento automático en save/M2M. |
| TipoEstudio.pruebas | ManyToManyField a pruebas.Prueba mediante TipoEstudioPrueba. Conjunto final no vacío para crear/editar/reactivar; debe validarlo el escritor. |
| TipoEstudioPrueba | id BigAutoField; tipo FK CASCADE, prueba FK PROTECT; UniqueConstraint(tipo, prueba). |
| Estudio.tipo | FK TipoEstudio PROTECT, related_name estudios; cualquier estado de estudio protege uso histórico. No filtrar estado al consultar uso. |
| Estudio snapshots | tipo_nombre_snapshot CharField(150), tipo_descripcion_snapshot TextField opcional, tipo_version_snapshot PositiveBigInteger >=1; pertenecen al estudio y no son campos editables del catálogo. |
| PruebaEstudio | Asignaciones propias, unique(estudio, prueba), FK Prueba y Estudio PROTECT; no cambiar esas filas ni sus estados. |

Meta de TipoEstudio declara gestionar_catalogo; la comprobación concreta será has_perm("estudios.gestionar_catalogo"). No nuevos roles ni asignación automática. No se modifica Usuario.

## Migraciones

Se reutilizan pruebas/0001_initial, estudios/0001_initial, estudios/0002_estudio y estudios/0003_estados_estudio_y_prueba. No migración nueva prevista: este diseño modifica comportamiento, no esquema. Si posteriormente aparece necesidad real, detener su generación automática y revisar alcance/diseño; no recrear base compartida ni sembrar datos mediante migración.

## Estado canónico y versión

Comparar nombre ya strip (con caso conservado), descripción exacta normalizada a cadena no NULL, activo y conjunto de IDs positivos de pruebas existentes. El orden y repeticiones de IDs no cambian composición. Forma canónica para digest: JSON con claves ordenadas, lista de IDs ordenada sin duplicados y UTF-8; no incluir datos científicos ni confiar en snapshots del cliente.

- Crear: activo=True, version=1, un tipo + asociaciones completos dentro de atomic.
- Editar: conservar id y activo; validar nombre/descripcion/pruebas; si cambia uno o más valores efectivos, version +=1 una vez.
- Desactivar/reactivar: conservar nombre/descripcion/composición; cambiar solo activo y version si corresponde. Reactivar exige al menos una prueba válida; desactivar puede retirar tipo legado vacío.
- No-op: versión esperada vigente y validaciones de operación satisfechas; ninguna escritura ni incremento. Cambiar solo el caso del nombre sí es efectivo por cambiar el texto mostrado a estudios futuros.
- Eliminar: versión vigente, cero estudios asociados, borrar tipo y su composición; no versión posterior y no borrar Prueba. No exigir composición válida para borrar un nunca usado.
- Stale: conflicto antes de evaluar no-op; no DML. Fallas de cualquier operación revierten datos/M2M/versión completos.

## Datos efímeros de confirmación — sin modelos nuevos

Contexto formulario firmado: fase=edicion, usuario, huella HMAC de sesión, acción, tipo_id y version_esperada desde GET. En alta tipo/version son null. Contexto existente válido no puede convertirse en token de confirmación.

Borrador de revisión por UUID en mapa de sesión tipos_pendientes: acción, tipo_id, version_esperada, payload propuesto (solo nombre/descripcion/IDs para alta/edición o estado destino fijo para disponibilidad), copia de configuración revisada/uso informativo y token de fase confirmacion con digest del payload. Usuario/sesión/acción/tipo/version/digest deben coincidir. Guardar creado_en como metadato de servidor; TTL 3600s y purga de vencidos al acceder/preparar, antes de contar el máximo de 20 pendientes vigentes. Borrar borrador al cancelar o después de éxito. Contextos no son autorización de negocio ni idempotencia persistente; revalidar permiso/versión/uso al guardar.

No guardamos versiones históricas adicionales de TipoEstudio: US 5.1 ya conserva los textos/asignaciones que necesitan sus estudios. No hay nueva tabla de auditoría o de idempotencia administrativa solicitada.
