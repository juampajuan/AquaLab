# Datos demo académicos — propuesta aprobada e implementada

> Estado vigente de cierre: implementación y 40/40 tareas completadas; recorrido Chrome y carga demo confirmados por el usuario, sin observación directa del asistente. Detalle y límites en [cierre-tecnico.md](cierre-tecnico.md). Las notas de evolución anteriores se conservan como historial. Sin commit ni PR.

## Decisión y alcance

Fuente: aclaración expresa del usuario en este chat. AquaLab es un proyecto académico FIUBA; todos los datos de desarrollo/demostración son ficticios. No existe un proveedor científico externo ni un catálogo oficial pendiente. Esta decisión sustituye esa dependencia en la documentación anterior, preservada como historial. No cambia FR-013/014/015, snapshots, idempotencia ni el contrato con US 5.5.

El usuario aprobó expresamente esta propuesta y autorizó implementar el comando y sus tests. El comando está implementado; no se ejecutó --aplicar sobre la base local. T037/T039/T040 siguen pendientes de validación manual. La evidencia actualizada está en quickstart.md.

## Revisión de mecanismos existentes

Hay factories de pytest en estudios/tests/conftest.py, sin fixtures JSON, seeds ni management commands propios de carga encontrados. Las factories usan force_login, PI fijo 200001 y una base aislada; no se importarán ni ejecutarán contra desarrollo. Django loaddata es una herramienta existente, pero las fixtures con PK fijas pueden colisionar/sobrescribir y no ofrecen aquí las claves naturales/protocolo de negocio necesarios. Se reutilizarán ORM, atomic, full_clean y muestras.servicios.registrar_muestra. No se añaden dependencias, modelos ni migraciones.

## Mecanismo propuesto

Un único comando: estudios/management/commands/cargar_demo_us51.py, con tests separados. Implementado tras la aprobación del usuario. No se conecta a startup, migrate, señales, Docker entrypoint ni CI. Sin flush, reset, borrados, update_or_create ni opciones para forzar sobrescrituras.

Comandos implementados (reemplazar CORREO_EXISTENTE; DEBUG=True debe estar ya configurado en desarrollo/QA):

    docker compose exec -T -e AQUALAB_ENTORNO=desarrollo web python manage.py cargar_demo_us51 --usuario CORREO_EXISTENTE --dry-run
    docker compose exec -T -e AQUALAB_ENTORNO=desarrollo web python manage.py cargar_demo_us51 --usuario CORREO_EXISTENTE --aplicar

--dry-run será el comportamiento por defecto: solo consultas, validaciones y plan de altas/reutilizaciones; no crear siquiera filas temporales ni consumir secuencias. --aplicar es obligatorio para escribir y vuelve a validar todo dentro de una transacción. --dry-run y --aplicar mutuamente excluyentes. Base default del entorno Compose local; mostrar nombre/alias de base y motor sin credenciales. Rechazar entorno no declarado: AQUALAB_ENTORNO solo acepta desarrollo o qa; además se exige DEBUG=True, PostgreSQL y usuario existente/activo. También se comprueban estas condiciones en simulación. No crear usuarios, cambiar contraseñas, aprobar cuentas ni otorgar permisos.

## Manifiesto ficticio v1 propuesto

Todos los nombres/descripciones llevan [DEMO FIUBA US51] y advierten que las asociaciones son arbitrarias para demostrar software, sin validez científica. Correos de clientes bajo example.invalid. Fecha de ambas muestras: 2026-10-27 para ingreso y muestreo, siempre iguales y reproducibles. Sitio y responsable de extracción también identificados como DEMO.

| Entidad | Identidad estable y contenido |
|---|---|
| Cliente A | DNI ficticio 99000001; [DEMO FIUBA US51] Cliente activo; demo-us51-activo@example.invalid. |
| Cliente B | DNI ficticio 99000002; [DEMO FIUBA US51] Cliente inactivo; demo-us51-inactivo@example.invalid. |
| Origen A/B | Uno por cliente: [DEMO FIUBA US51] Origen A/B. |
| Muestras A/B | Una por cliente/origen, nombre [DEMO FIUBA US51] Muestra A/B; clave_borrador UUIDv5 determinista por demo-fiuba-us51:v1:muestra:A/B y namespace fijo declarado en el comando. PI asignado por el servicio existente, nunca reservado ni fijado. |
| Pruebas | DEMO-US51-P01/P02/P03; nombres [DEMO FIUBA US51] Prueba A/B/C. Solo código y nombre; sin fórmulas, unidades, límites, resultados ni normas. |
| Tipo A | [DEMO FIUBA US51] Bacteriológico; pruebas P01 + P02. |
| Tipo B | [DEMO FIUBA US51] Físico-Químico; pruebas P02 + P03. |
| Tipo C | [DEMO FIUBA US51] Vuelco a canal; pruebas P01 + P03. |
| Tipo D | [DEMO FIUBA US51] Tipo desactivado; prueba P01; activo=False. |

Totales iniciales: 2 clientes, 2 orígenes, 2 muestras, 3 pruebas y 4 tipos con 7 asociaciones. Cero estudios precargados: se crean desde Chrome. Las composiciones propuestas no representan prácticas científicas ni exhaustividad del catálogo.

## Idempotencia, colisiones y concurrencia

- Identificar clientes por documento, pruebas por código, tipos por nombre normalizado como el modelo, orígenes por cliente/nombre y muestras por UUID de borrador. Nunca por PK fija, PI o nombre de muestra solamente.
- Una segunda carga idéntica no crea, actualiza, reactiva ni restablece nada. Compara contenidos y relaciones del manifiesto; ante diferencia o identidad ocupada por datos ajenos, error explícito con rollback completo. No adueñarse de registros por coincidir solamente su clave. No modificar estudios ni snapshots.
- La carga real mantiene atomic y un advisory lock exclusivo del cargador; registrar_muestra conserva su lock propio y asignación de PI. Tomar locks de tipos existentes en orden estable para comprobarlos. No adquirir el lock global de creación de estudios después del lock del tipo. Las constraints son defensa adicional; cualquier colisión concurrente revierte la carga completa y permite reintentar.
- Para B, registrar la muestra mientras el cliente DEMO recién creado está activo y desactivarlo en la misma transacción al terminar. Si ya existe la configuración B esperada, reutilizarla sin reactivarlo. Nunca eludir ni modificar las reglas de US 4.1.
- Mantener full_clean y comprobaciones finales, incluyendo conjunto no vacío. Una base con datos parciales conflictivos se informa y no se repara automáticamente. Nunca escribir sobre registros ajenos a la demo.
- Tras experimentos que modifiquen tipos demo, repetir el cargador informa divergencias; no restaura el catálogo ni modifica versiones/historial. No habrá limpieza automática.

## Preparación de T037

1. Tras aprobar/implementar/probar el comando, ejecutar dry-run, revisar el resumen y ejecutar --aplicar explícitamente; repetir para verificar cero altas y mismos IDs/PI/versiones.
2. Con usuario activo existente, abrir Chrome en http://localhost:8000/estudios/crear/. Reconocer nombres DEMO, PI dinámico, cliente y origen; comprobar que tipo D no se ofrece.
3. Muestra A + tipo A: revisar las dos pruebas previstas, volver/editar y cancelar sin crear. Confirmar una nueva solicitud, comprobar ID/PI, reenvío/doble clic y una nueva solicitud deliberada independiente del mismo tipo. Probar también tipo B sobre la misma muestra.
4. Muestra B de cliente inactivo + tipo C: permitir creación sin reactivar cliente ni cambiar la muestra.
5. Campos faltantes, navegación sin sesión, claridad visual de errores, pestañas separadas y recuperación de token vencido: registrar resultados. La concurrencia real sigue acreditada por pytest/PostgreSQL.
6. Para cambios durante revisión y conservación histórica, preparar después de la aprobación un guion explícito de manage.py shell limitado a estos tipos DEMO: atomic, lock de tipo, comparación de versión e incremento por cambio efectivo de nombre/descripción/composición/activo. No forma parte de la carga inicial ni se ejecuta automáticamente; no crea pantallas de US 5.5. Revisar cada cambio antes de ejecutarlo. Un POST viejo debe exigir nuevo resumen; desactivación debe rechazar; el estudio anterior conserva snapshots/asignaciones. No se simula que este guion ni estos casos manuales ya se ejecutaron.

## Pruebas del cargador implementadas

Dry-run sin escrituras; primera carga exacta; segunda carga sin cambios; dos cargas simultáneas sin duplicados sobre PostgreSQL; colisión con datos existentes y rollback íntegro; usuario inválido/inactivo; bloqueo fuera de entorno local; PI asignado sin colisionar con muestras previas; muestra B sin cambiar reglas de registro; ausencia de estudios precargados y de campos científicos inventados. Verificar además que la carga no se ejecuta con migrate ni al arrancar la aplicación.

## Estado de la aprobación y archivos

Mecanismo y manifiesto aprobados por el usuario en este chat. Entrega: estudios/management/__init__.py, estudios/management/commands/__init__.py, estudios/management/commands/cargar_demo_us51.py, estudios/tests/test_demo_us51.py y documentación US 5.1. Sin tocar modelos, migraciones, muestras ni US 5.5. La ejecución de --aplicar en la base local aún no está autorizada. No existe dependencia científica externa. T037/T039/T040 continúan pendientes hasta evidencia manual y cierre correspondiente; no se aumentan las 37/40 tareas actuales por esta propuesta.


El namespace de muestras elegido es uuid.NAMESPACE_URL, fijo por estándar y declarado como NAMESPACE_DEMO; la cadena exacta sigue siendo demo-fiuba-us51:v1:muestra:A/B. Las fechas de alta/registro y PI se asignan al crear; una repetición los conserva. Cambiar --usuario respecto del creador inicial provoca divergencia de trazabilidad de las muestras, sin reasignarla.
