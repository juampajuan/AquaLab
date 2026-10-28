# Data Model: US 5.1 y base compartida

> Estado vigente de cierre: implementación y 40/40 tareas completadas; recorrido Chrome y carga demo confirmados por el usuario, sin observación directa del asistente. Detalle y límites en [cierre-tecnico.md](cierre-tecnico.md). Las notas de evolución anteriores se conservan como historial. Sin commit ni PR.

Modelo implementado y migraciones generadas/aplicadas. [Spec](spec.md), [plan](plan.md).

## pruebas.Prueba

| Campo | Diseño |
|---|---|
| id | BigAutoField, identidad estable. |
| codigo | CharField(50), obligatorio, unique, espacios laterales recortados, comparación exacta (mayúsculas distinguen); Check no vacío. |
| nombre | CharField(150), obligatorio, recortado; Check no vacío. |

Solo representación mínima, sin estado científico, fórmulas, unidades, resultados o límites. No hay pantallas de alta/edición. Los futuros importadores deberán validar identidades y unicidad. La normalización exacta del código es elección técnica acordada para el catálogo académico, no estándar científico supuesto.

## estudios.TipoEstudio

| Campo | Diseño |
|---|---|
| id | BigAutoField. |
| nombre | CharField(150), obligatorio, recortado; UniqueConstraint Lower(nombre), Check no vacío. Tildes/espacios internos distinguen. |
| descripcion | TextField(blank=True, default=""), no NULL; opcional. |
| activo | BooleanField(default=True). |
| version | PositiveBigIntegerField(default=1), Check >=1. |
| pruebas | ManyToManyField a pruebas.Prueba mediante TipoEstudioPrueba. |

El escritor futuro de US 5.5 debe aumentar version una vez por mutación efectiva de nombre, descripción, activo o composición al commit; save/M2M no lo hacen automáticamente. Un no-op no aumenta versión. El servicio compartido valida al menos una prueba y todas existentes; una restricción CHECK simple no puede contar filas relacionadas. El conjunto no vacío es invariante de la configuración publicable, validada en lectura y futuro escritor; no se promete que un M2M directo por fuera del protocolo la garantice.

## estudios.TipoEstudioPrueba

id BigAutoField; tipo FK TipoEstudio CASCADE; prueba FK Prueba PROTECT. UniqueConstraint(tipo, prueba). CASCADE al eliminar un tipo nunca utilizado podrá borrar solo su composición, jamás la definición Prueba. No tiene campos científicos ni orden requerido.

## estudios.Estudio

| Campo | Diseño |
|---|---|
| id | BigAutoField; identificador numérico único, huecos permitidos. No es el PI. |
| muestra | FK muestras.Muestra PROTECT, related_name="estudios". |
| tipo | FK TipoEstudio PROTECT, related_name="estudios". |
| estado | CharField(30), choice pendiente_analisis / Pendiente de análisis, default y editable=False. Solo estado inicial. |
| creado_por | FK AUTH_USER_MODEL PROTECT, related_name="estudios_creados", editable=False. |
| fecha_creacion | DateTimeField(auto_now_add=True). |
| tipo_nombre_snapshot | CharField(150), obligatorio, editable=False. |
| tipo_descripcion_snapshot | TextField(blank=True, default=""), editable=False. |
| tipo_version_snapshot | PositiveBigIntegerField, Check >=1, editable=False. |
| clave_idempotencia | UUIDField(unique=True, null=False, editable=False), generado por servidor al preparar solicitud. |

Sin restricción única muestra/tipo: nuevas solicitudes iguales son válidas. No se duplican cliente ni origen: se consultan desde Muestra. Snapshots nunca se actualizan por editar catálogo. Identificador, estado, autor, hora, snapshots y clave son controlados por servidor. full_clean verifica límites y constraints aplicables; la obligatoriedad UUID está respaldada por NOT NULL/UNIQUE y el estado se fija en el servicio (editable=False no valida todos sus valores en full_clean); servicio realiza validación de negocio bajo lock y transacción. Bypass ORM no es un contrato público soportado.

## estudios.PruebaEstudio

id BigAutoField; estudio FK Estudio PROTECT; prueba FK Prueba PROTECT; UniqueConstraint(estudio, prueba), related_name="pruebas_asignadas" en estudio. Sin mediciones, resultados, fórmulas ni estados de ensayo en esta historia. Un fallo en asignaciones revierte el estudio entero; no se expone borrar estudios. Desactivación futura del tipo no elimina ni reescribe estas filas.

## Migraciones entregadas

1. pruebas/0001_initial.py: Prueba, sus constraints.
2. estudios/0001_initial.py: TipoEstudio, TipoEstudioPrueba, M2M y constraints; depende de pruebas/0001_initial.
3. estudios/0002_estudio.py: Estudio y PruebaEstudio y sus constraints; depende de estudios/0001_initial, muestras/0002_clave_borrador, pruebas/0001_initial y swappable_dependency(AUTH_USER_MODEL).
4. Permiso gestionar_catalogo en Meta de TipoEstudio previsto en esquema inicial para reutilización; no asignación automática, no CRUD ni admin editable. Los permisos default de Django no reemplazan autorización del flujo US 5.1.

No migraciones de datos ni modificación de muestras. Futuras migraciones US 5.5 extienden este esquema ya entregado.

## Estados y límites

Estudio: alta confirmada → Pendiente de análisis; sin transiciones posteriores. Tipo: activo para consumo, lectura de inactivo rechazada en nueva creación; sus mutaciones quedan a US 5.5. Cliente inactivo no impide Estudio por decisión definitiva FR-014. Reenvío idempotente exitoso no revalida activo/tipo; devuelve historial existente.


## Aclaración académica vigente — decisión del usuario

AquaLab es un proyecto académico FIUBA. Los datos de desarrollo y demostración son ficticios y deben identificarse como DEMO, sin atribuirles validez científica. No hay laboratorio real ni catálogo científico oficial externo pendiente; las referencias anteriores a esa dependencia quedan sustituidas por esta decisión. Se mantienen las reglas funcionales, separación Prueba/TipoEstudio, snapshots y contrato con US 5.5. La carga demo será explícita, reproducible e idempotente, separada de migraciones y arranque; el mecanismo y manifiesto están propuestos en [propuesta-datos-demo.md](propuesta-datos-demo.md), pendientes de revisión antes de implementar o modificar datos. No se cargaron datos ni se completó T037 con esta actualización documental.


Actualización de ejecución demo: el usuario aprobó el manifiesto y el mecanismo; cargar_demo_us51 está implementado con simulación por defecto, guardas de desarrollo/QA y escritura únicamente mediante --aplicar. No se ejecutó --aplicar sobre la base local. La validación manual sigue pendiente; ver quickstart.md para comandos y pruebas. Esta nota sustituye el estado anterior de propuesta pendiente de revisión.
