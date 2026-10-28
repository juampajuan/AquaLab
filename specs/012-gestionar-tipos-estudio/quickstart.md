# Quickstart — validación de US 5.5

Estado actual: implementación autorizada el 28/10/2026; rutas y módulos implementados, con verificaciones automáticas registradas al final. Chrome sigue pendiente. Los comandos previstos durante plan se conservan como guía; su ejecución real se distingue en el registro posterior. No se ejecutaron comandos de Docker, cargas, migraciones ni tests de producto durante la fase de plan. [Plan](plan.md), [UI](contracts/gestion-tipos-ui.md), [servicio](contracts/gestion-tipos-servicio.md).

## Entorno aislado y prerrequisitos

1. T001 satisfecha: aprobación formal y autorización comunicadas por el usuario el 28/10/2026, registradas en Notes de tasks.md. Este quickstart no amplía esa autorización ni acredita validación manual.
2. Usar el worktree US 5.5, su configuración local de desarrollo/QA y PostgreSQL 16. No reutilizar contenedores/volúmenes del otro worktree por el nombre default aqualab. Proyecto Compose dedicado aqualab-us55, puerto de navegador 8012 y su volumen propio. No copiar datos, dumps ni contraseñas al repo. Configurar .env local según .env.example con DEBUG=True y DATABASE_URL al db de ESTE proyecto (host db en su red, no una base externa).
3. Tener cuentas existentes activas: dos gestores para editar en paralelo y una sin permiso para verificar rechazo. Asignar estudios.gestionar_catalogo explícitamente desde la administración autorizada existente; no crear un rol nuevo ni darlo a todos. No basta is_staff; para pruebas de ausencia de permiso usar cuenta no superusuaria. Verificar permiso con nueva petición/sesión tras cambiarlo para no confundir caches del backend en objetos de tests.
4. La infraestructura y migraciones compartidas de main deben estar aplicadas en esa base QA. US 5.5 no añade migraciones en este diseño. Cualquier diferencia de makemigrations requiere revisar diseño, no regenerar iniciales.

Comandos previstos para preparar el proyecto aislado (ejecución real registrada al final):

    docker compose -p aqualab-us55 build web
    docker compose -p aqualab-us55 up -d db
    docker compose -p aqualab-us55 run --rm --no-deps web python manage.py migrate --plan
    docker compose -p aqualab-us55 run --rm --no-deps web python manage.py migrate --noinput

Build solo si falta la imagen de este proyecto o cambió su contenido; usa las dependencias del repo, ninguna nueva propuesta. El proyecto dedicado puede consumir una imagen/volumen adicional; conservarlo para validar, sin borrar automáticamente volúmenes o respaldos. Comprobar destino DATABASE_URL antes de ejecutar migrate o carga. No confundir esto con permiso para modificar bases en la fase actual de plan.

## Datos académicos DEMO

Usar únicamente el cargador ya existente de US 5.1, explícitamente y sobre QA. Reemplazar CORREO_EXISTENTE por una cuenta activa ya creada; el cargador no crea usuarios ni otorga permisos:

    docker compose -p aqualab-us55 run --rm --no-deps -e AQUALAB_ENTORNO=qa web python manage.py cargar_demo_us51 --usuario CORREO_EXISTENTE --dry-run
    docker compose -p aqualab-us55 run --rm --no-deps -e AQUALAB_ENTORNO=qa web python manage.py cargar_demo_us51 --usuario CORREO_EXISTENTE --aplicar

Revisar plan antes de --aplicar; repeat idéntico no cambia nada. Datos visibles: [DEMO FIUBA US51] y DEMO-US51-P01/P02/P03. No fórmulas, límites o normas. El cargador no precarga estudios. Si existe divergencia, aborta; no usarlo como reset. No alterar sus cuatro tipos base para esta validación: crear nuevos tipos [DEMO FIUBA US55] desde la futura gestión y reutilizar esas Prueba.

Para Chrome, lanzar el web de este proyecto en puerto distinto, sin recrear el servicio del otro checkout:

    docker compose -p aqualab-us55 run --rm --no-deps -p 127.0.0.1:8012:8000 web

Abrir http://localhost:8012. La configuración del proyecto ya usa runserver en 0.0.0.0:8000; no modificar sus archivos para seguir la guía. Mantener el proceso durante pruebas. Si el puerto está ocupado, elegir otro puerto local libre y registrar cuál, sin apagar servicios ajenos.

## Recorrido Chrome reproducible

Registrar ejecutor, fecha, entorno y resultado por caso. Una observación manual no reemplaza los tests PostgreSQL concurrentes. No marcar como probado hasta ejecutarlo.

| Paso | Acción y resultado esperado |
|---|---|
| 1. Autorización | Sin login, /estudios/tipos/ redirige a login. Cuenta sin permiso: no enlace y acceso directo GET/POST rechazado 403. Gestor: acceso al listado, incluidos inactivos. |
| 2. Alta | Crear [DEMO FIUBA US55] Historial, descripción DEMO y P01/P02. Revisar conjunto, volver y conservar, cancelar sin fila; repetir y confirmar. Nuevo tipo activo con versión 1 y dos pruebas. |
| 3. Validaciones | Vacío/espacios, nombre duplicado con caso/espacios laterales y conjunto vacío rechazan sin cambios. Descripción vacía válida; nombres con tildes o espacios internos distintos se conservan. |
| 4. Historial | Desde crear estudio de US 5.1, crear uno sobre ese tipo y muestra DEMO, con texto/versión originales. US 5.2 permite ver detalle y pruebas. No crear estudio desde el cargador. |
| 5. Edición | Editar tipo propio a otro nombre/descripcion y P02/P03. Resumen, confirmar: incremento una vez. Estudio previo conserva nombre/descripcion/asignaciones; un estudio nuevo recibe la configuración confirmada actual. |
| 6. No-op | Abrir versión vigente y reenviar mismos datos o reordenar selección: mensaje sin cambios y misma versión; no publicación nueva. Comprobar versión/ausencia de DML también mediante tests de servicio, sin depender de campos ocultos del navegador. |
| 7. Conflicto desde formulario | Gestores A/B abren misma versión. A confirma cambio; B intenta preparar o confirmar su edición antigua: conflicto, propuesta y vigente separadas, ningún overwrite. Revisar nueva base y confirmar explícitamente; no aceptación automática. |
| 8. Conflicto con creación | En otra pestaña iniciar creación de estudio y dejar resumen. Editar nombre/descripcion/composición del tipo propio y confirmar. Enviar resumen viejo de estudio: nueva revisión/confirmación obligatoria, no estudio con otra configuración. |
| 9. Desactivar/reactivar | Preparar desactivación y cancelar: sin efecto. Confirmar: tipo deja de ofrecerse para nuevos estudios; existente intacto. Gestor reactiva desde resumen vigente: vuelve a ofrecerse, sin tocar historial. No usar ni modificar el tipo inactivo del manifiesto base. |
| 10. Protección de uso | Sobre tipo propio con estudio histórico: eliminar rechazado; alternativa de desactivación. Estar inactivo no habilita borrar. |
| 11. Eliminar nunca usado | Crear [DEMO FIUBA US55] Eliminable con P01 y no crear estudios. Preparar/cancelar: intacto; preparar/confirmar: desaparece solo tipo/composición, P01 sigue existiendo. Reenvío no recrea ni borra otro tipo. |
| 12. Seguridad y pestañas | Borradores distintos no se cruzan; cancelado reenviado no guarda. Token vencido/manipulado o de otra sesión no guarda. Revocar permiso antes de confirmar impide operación. Los casos no realizables manualmente se verifican por tests y se registran sin inventar evidencia. |

No es necesario dejar adrede un tipo vacío en QA para demostrar reactivación inválida: ese legado/ref inválida se prepara en fixtures aisladas. Para carreras reales y fallo a mitad de M2M usar los tests automatizados; no ejecutar SQL destructivo ni introducir herramientas administrativas adicionales solo para forzar el caso manual.

## Comandos de verificación

Sobre el mismo proyecto aislado y después de implementación:

    docker compose -p aqualab-us55 run --rm --no-deps web python manage.py check
    docker compose -p aqualab-us55 run --rm --no-deps web python manage.py makemigrations --check --dry-run
    docker compose -p aqualab-us55 run --rm --no-deps web pytest estudios/tests/test_gestion_tipos_servicio.py estudios/tests/test_gestion_tipos_ui.py estudios/tests/test_gestion_tipos_confirmaciones.py estudios/tests/test_gestion_tipos_concurrencia.py
    docker compose -p aqualab-us55 run --rm --no-deps web pytest
    docker compose -p aqualab-us55 run --rm --no-deps web ruff check .
    docker compose -p aqualab-us55 run --rm --no-deps web ruff format --check .
    node --test usuarios/tests/js/sesion.test.cjs

El primer grupo corresponde a los tests administrativos implementados. Concurrencia debe verificar connection.vendor=postgresql, base aislada test_, conexiones por hilo y eventos/barreras con tiempos acotados, además de lock_timeout/statement_timeout en test. Acreditar ambas ordenaciones de escritor/creador y eliminador/creador y nombres duplicados simultáneos; no usar SQLite.

## Registro histórico de la fase de plan

Solo setup-plan original y verificación documental. Ningún comando anterior se ejecutó ni acredita funcionalidad implementada de US 5.5. Mantener respaldos fuera de commits. No existe laboratorio ni fuente científica externa pendiente. La preparación de datos requiere cuentas/configuración QA propias y permisos expresamente otorgados, no inferidos ni cargados automáticamente. Para pasar a tasks: revisión del diseño y autorización posterior del usuario; antes de implementar, aprobación formal del equipo y autorización de implementación.


## Ejecución de implementación — 28/10/2026

T001: aprobación completa del equipo comunicada por el usuario (incluye FR-018/019) y autorización de implementar registradas en tasks.md. Rama 012-Gestionar-Catalogo-Estudios, HEAD a95efb46; base integrada US 5.1/5.2. Se reutilizan modelos y constraints existentes sin modificaciones. Respaldos preservados y excluidos por .gitignore/.dockerignore.

QA: proyecto aqualab-us55; volumen aqualab-us55_postgres_data; base aqualab_us55, host db; runner aqualab-us55-qa. .env propio ignorado, generado localmente sin copiar secretos de otros worktrees. Docker build y up -d db ejecutados; migraciones existentes aplicadas con migrate --noinput. Ningún contenedor ajeno modificado.

T004/T005: rojo inicial por módulos gestion_tipos y confirmaciones_tipos ausentes; tras T006/T007, 7 tests aprobados en PostgreSQL. T008–T010: rojo inicial por escritor gestionar_tipo_estudio ausente. Primera ejecución US1: 28 aprobados y un fallo de helper por argumento duplicado, corregido antes de continuar. No se atribuye ese fallo a producto.

T019: `docker exec aqualab-us55-qa pytest -q estudios/tests/test_gestion_tipos_servicio.py estudios/tests/test_gestion_tipos_ui.py estudios/tests/test_gestion_tipos_confirmaciones.py`: 29 passed (21.08s). Incluye alta, pruebas existentes, rollback, permisos, CSRF, resumen/volver/cancelar y reenvío.

T020–T023: rojo de edición (11 fallos por operación/rutas ausentes), luego corrección de un enlace Volver y una assertion de template. T031: `docker exec aqualab-us55-qa pytest -q estudios/tests/test_gestion_tipos_servicio.py estudios/tests/test_gestion_tipos_ui.py estudios/tests/test_gestion_tipos_confirmaciones.py estudios/tests/test_gestion_tipos_concurrencia.py estudios/tests/test_servicio.py estudios/tests/test_registro.py`: 80 passed (71.08s). Incluye PostgreSQL real con pg_blocking_pids para comprobar espera efectiva, ambas ordenaciones edición/creación, dos editores, nombres equivalentes, no-op sin DML, rollback e historial. Tests de integridad del contexto ya estaban satisfechos por la infraestructura fundacional; no se simula rojo adicional.

T032–T035: rojo previo de disponibilidad/eliminación: 26 fallos por operaciones/rutas aún ausentes; 56 tests existentes aprobados. Tras implementar, T042: UI/confirmaciones 37 passed (23.59s). T043: `docker exec aqualab-us55-qa pytest -q estudios/tests/test_gestion_tipos_servicio.py estudios/tests/test_gestion_tipos_concurrencia.py estudios/tests/test_servicio.py estudios/tests/test_consulta.py muestras/tests/test_detalle.py --tb=short`: 116 passed (126.27s). Ambas ordenaciones reales de edición/desactivación/reactivación/eliminación frente a creación; eliminación protegida en todos los estados históricos, rollback tras delete y tipo legado vacío. Guardias y tokens de operaciones nuevas reutilizan infraestructura ya probada.


## Resultado automatizado final — 28/10/2026

`docker exec aqualab-us55-qa pytest -q --tb=short`: **526 passed in 301.97s** sobre PostgreSQL 16.15. Ruff check aprobado, Ruff format --check: 121 archivos conformes; Django check sin problemas; makemigrations --check --dry-run sin cambios y migrate --check con exit 0. Las migraciones existentes se aplicaron correctamente sobre la base QA nueva. JavaScript: `node --test usuarios/tests/js/sesion.test.cjs`, 14 aprobados. No se crearon modelos ni migraciones. Ver trazabilidad de los 33 escenarios, 19 FR y 11 SC en Notes de tasks.md.

Las pruebas de concurrencia usan base test_aqualab_us55, conexiones por hilo, eventos/barreras y pg_blocking_pids para demostrar espera efectiva. Ninguna base de otro checkout se utilizó. Validación Chrome pendiente; estos resultados son automatizados y no acreditan recorrido manual, CI remoto ni aprobación de un PR.

## Registro previo de preparación pendiente (antes de completar T046)

Servidor US 5.5 levantado y verificado en **http://127.0.0.1:8012/estudios/tipos/**; contenedor `aqualab-us55-web-qa`, proyecto `aqualab-us55`. La comprobación HTTP sin sesión devuelve 302 al login; esto es un smoke check HTTP, no una validación manual en Chrome. Los contenedores `aqualab-web-1`/`aqualab-db-1` siguen intactos y el puerto 8000 del otro entorno se conserva.

La base QA propia está nueva: se verificaron **0 cuentas**. No se copiaron usuarios, credenciales ni datos de otros worktrees; no se crearon cuentas automáticamente ni se ejecutó el cargador DEMO. T046 permanece parcialmente pendiente por esos prerrequisitos.

Pasos explícitos para el usuario, desde este worktree:

1. Crear su administrador QA con la herramienta existente (solicita correo/contraseña de manera interactiva; no guardarlos en documentación):

       docker exec -it aqualab-us55-qa python manage.py createsuperuser

2. Abrir http://127.0.0.1:8012/admin/ y preparar dos cuentas activas de gestión y una activa sin permiso usando la administración de usuarios existente. Las dos gestoras deben tener explícitamente `estudios.gestionar_catalogo` ("Puede gestionar el catálogo de tipos de estudio"); para verificar autorización específica, no hacerlas superusuarias. La cuenta de control no debe tener ese permiso ni ser superusuaria. No se requiere `is_staff` para gestionar tipos desde la aplicación. No se modificó esta administración.

3. Sustituir `CORREO_QA_EXISTENTE` por una cuenta activa realmente creada. Simular primero; revisar la salida y aplicar explícitamente sobre esta base QA:

       docker exec aqualab-us55-qa python manage.py cargar_demo_us51 --usuario CORREO_QA_EXISTENTE --dry-run
       docker exec aqualab-us55-qa python manage.py cargar_demo_us51 --usuario CORREO_QA_EXISTENTE --aplicar

   El `.env` propio ya identifica QA y DEBUG=True; el cargador valida esos controles. No crea usuarios ni estudios y no sobrescribe registros divergentes. No fue ejecutado en esta implementación por faltar la cuenta. Mantener sin edición los tipos base [DEMO FIUBA US51].

4. Completar los 12 pasos de la tabla "Recorrido Chrome reproducible", con tipos nuevos **[DEMO FIUBA US55]** y las pruebas DEMO-US51 existentes. Usar sesiones independientes para los dos gestores. Reportar fecha, cuentas/roles utilizados (sin contraseñas), casos y resultados, incluidos pendientes o errores. Los casos de concurrencia PostgreSQL y rollback ya tienen evidencia automatizada; no atribuirlos a Chrome.

Para volver a iniciar el web si el contenedor no está activo (no ejecutar si ya está levantado):

    docker compose -p aqualab-us55 run -d --rm --no-deps --name aqualab-us55-web-qa -p 127.0.0.1:8012:8000 web

**Pendientes de cierre**: completar T046 con cuentas/carga efectiva, T047 con el recorrido real del usuario, T048 con evidencia manual y automática consolidada, T049 con inventario final selectivo y T050 con revisión final. No marcar ninguno como completado por tener esta guía. No existe dependencia de un catálogo científico externo ni aprobación formal de spec pendiente: T001 ya está satisfecha. Jira sigue sin clave aportada y no se inventa.

## T046 completada — preparación real de QA, 28/10/2026

La preparación anterior se conserva como historial. El usuario autorizó ahora crear las dos cuentas exclusivamente en QA y ejecutar la carga. T046 quedó completada; T047 (recorrido personal en Chrome) sigue pendiente. No se modificó código, modelos, migraciones ni la gestión de usuarios.

### Aislamiento comprobado

- Rama: 012-Gestionar-Catalogo-Estudios; worktree E:/Codex/worktrees/us55-tipos-estudio/AquaLab.
- Compose: aqualab-us55; red exclusiva aqualab-us55_default; PostgreSQL aqualab_us55, host db; volumen aqualab-us55_postgres_data.
- Volumen del otro proyecto: aqualab_postgres_data, diferente. No se conectó a esa base ni se modificaron sus contenedores.
- Servidor: http://127.0.0.1:8012/estudios/tipos/; contenedor aqualab-us55-web-qa. Runner de comandos: aqualab-us55-qa.

### Cuentas y contraseñas

| Usuario (correo de login) | Activo | gestionar_catalogo | Staff / superusuario |
|---|---|---|---|
| gestor.us55@aqualab.test | Sí | Sí, permiso específico directo | No / No |
| comun.us55@aqualab.test | Sí | No; sin grupos que lo concedan | No / No |

Se ejecutó un script por stdin con el comando `docker exec -i aqualab-us55-web-qa python -`: comprobó primero motor/base/entorno, creó las dos cuentas mediante get_user_model().objects.create_user dentro de transaction.atomic y asignó al gestor Permission(codename=gestionar_catalogo, content_type.app_label=estudios) mediante user_permissions.add. Abortaba si ya existía alguna identidad, sin sobrescribir datos. No se crearon otras cuentas ni se alteraron modelos o administración.

Las contraseñas iniciales se generaron con secrets.token_urlsafe únicamente en memoria del proceso, se usaron para comprobar login y no se imprimieron ni guardaron en archivos. Django conserva los hashes normales en la base QA. No hay contraseñas para copiar desde documentación o Git.

**Para usarlas en Chrome, establecer contraseñas propias de manera interactiva en una terminal local:**

    docker exec -it aqualab-us55-qa python manage.py changepassword gestor.us55@aqualab.test
    docker exec -it aqualab-us55-qa python manage.py changepassword comun.us55@aqualab.test

Django solicita y confirma cada contraseña con entrada oculta. No añadir contraseñas a los argumentos del comando ni a este documento. Después ingresar con el correo correspondiente en http://127.0.0.1:8012/usuarios/login/.

Para probar el conflicto entre editores, se pueden abrir dos sesiones independientes de la gestora (perfiles distintos o sesión normal/incógnito) sobre la misma versión. Solo se crearon las dos cuentas solicitadas; ninguna es superusuaria.

### Comandos de datos ejecutados y resultados

1. `docker exec aqualab-us55-qa python manage.py cargar_demo_us51 --usuario gestor.us55@aqualab.test --dry-run`: exit 0; salida SIMULACIÓN, entorno=qa, base=aqualab_us55, motor=postgresql. Propuesta únicamente del manifiesto US51, sin escrituras.
2. Tras revisar ese destino y manifiesto: `docker exec aqualab-us55-qa python manage.py cargar_demo_us51 --usuario gestor.us55@aqualab.test --aplicar`: exit 0; altas completadas, sin crear estudios.
3. Se repitió el comando de simulación: exit 0, REUTILIZAR para todos los registros, sin divergencias ni nuevas altas propuestas. No se ejecutó una segunda aplicación.
4. Consulta ORM de solo lectura en QA: conteos exactos 2 clientes, 2 orígenes, 2 muestras, 3 pruebas, 4 tipos y 0 estudios; 0 tipos con prefijo [DEMO FIUBA US55]. Permisos y flags de ambas cuentas comprobados de nuevo.

| Datos disponibles | Detalle |
|---|---|
| Clientes y orígenes | Cliente activo / Origen A; cliente inactivo / Origen B, todos [DEMO FIUBA US51]. |
| Muestras | PI 200001 (cliente activo) y PI 200002 (cliente inactivo). |
| Pruebas | DEMO-US51-P01, DEMO-US51-P02 y DEMO-US51-P03; genéricas, sin fórmulas ni normas. |
| Tipos base US51 | Bacteriológico, Físico-Químico y Vuelco a canal activos; Tipo desactivado inactivo. Asociaciones ficticias del manifiesto existente. |
| Estudios / tipos US55 | Ninguno precargado; crearlos personalmente desde Chrome. |

### Verificaciones de acceso realizadas (HTTP, no Chrome)

El mismo script utilizó urllib, cookies y CSRF reales contra el web QA para iniciar sesión con cada cuenta, sin imprimir contraseñas, cookies ni tokens. Login correcto para ambas; GET /estudios/tipos/ devolvió 200 al gestor y 403 a la cuenta común. POST /estudios/tipos/confirmar/ con sesión común y CSRF válido devolvió 403. No confirmó ni creó estudios o tipos. La comprobación desde el host con `curl.exe -s -o NUL -w '%{http_code} %{redirect_url}' http://127.0.0.1:8012/estudios/tipos/` devolvió 302 al login sin sesión.

Estos son smoke checks HTTP y consultas QA; no sustituyen T047 ni se presentan como pruebas manuales de Chrome. No fue necesario reejecutar pytest/JavaScript porque esta preparación solo modificó datos QA y documentación; sus resultados anteriores permanecen registrados en la sección de verificación automatizada. El usuario debe ejecutar el recorrido de 12 pasos y comunicar sus resultados para el cierre T047–T050.

## T047 — Validación manual informada por el usuario (28/10/2026)

El usuario confirma resultados satisfactorios en Chrome, en QA US 5.5 (http://127.0.0.1:8012, proyecto aqualab-us55, base aqualab_us55), para los nueve casos siguientes:

1. Creación de un tipo con pruebas existentes.
2. Edición de nombre, descripción y composición con actualización de versión.
3. Rechazo de nombres duplicados y conjuntos vacíos.
4. Desactivación y exclusión de nuevas creaciones.
5. Reactivación y recuperación de disponibilidad.
6. Conservación de pruebas y textos históricos de un estudio anterior.
7. Rechazo de eliminación de un tipo utilizado.
8. Eliminación de un tipo nunca utilizado sin borrar pruebas.
9. Rechazo del acceso de una cuenta sin permiso.

Fuente: confirmación expresa del usuario recibida el 28/10/2026. No fue observación directa de Codex. No se aportaron capturas, tiempos, cuentas concretas utilizadas por caso ni registros HTTP del recorrido; no se inventan. El reporte cubre estos nueve casos, no afirma que se ejecutaron individualmente los doce pasos originales de la guía. Cancelación, expiración/manipulación de tokens, no-op y conflictos concurrentes tienen evidencia automatizada; no se atribuyen a esta validación manual.

T001: aprobación completa del equipo, incluidos FR-018/019, y autorización de implementar comunicadas por el usuario el 28/10/2026, registradas en Notes de tasks.md. No se inventan revisores, actas ni enlaces. Los textos anteriores de estados pendientes son registros históricos, sustituidos por las entradas posteriores fechadas.

La concurrencia real, locks, atomicidad, rollback y protección frente a creación simultánea de estudios corresponden a los tests PostgreSQL (base test_aqualab_us55, conexiones independientes y pg_blocking_pids); Chrome no prueba esas garantías por sí solo. Jira permanece sin clave/enlace aportados. CI remoto y revisión/aprobación de código de otro integrante corresponden al futuro PR y no se declaran obtenidos. La aprobación de la especificación no los sustituye.

## Resultado final de cierre — 28/10/2026

Reejecución: `docker exec aqualab-us55-qa pytest -q --tb=short`: **526 passed in 346.77s**. PostgreSQL QA aislado, incluidos tests de concurrencia reales. `ruff check .` aprobado; `ruff format --check .`: 121 archivos conformes; `manage.py check` sin problemas; `makemigrations --check --dry-run`: No changes detected; `migrate --check`: exit 0. `node --test usuarios/tests/js/sesion.test.cjs`: **14 aprobados, 0 fallos**. No nuevas migraciones ni código de producto en esta etapa.

La evidencia manual de nueve casos fue informada por el usuario y está delimitada arriba. La cobertura completa de 19 FR / 11 SC / 33 escenarios combina esa confirmación con los tests automatizados, no atribuye todas las garantías al navegador. Ver inventario-commit.md (30 archivos) y cierre-tecnico.md. Sin bloqueos técnicos detectados para commit local y preparación del PR; CI remoto, Jira y revisión de código siguen pendientes administrativos. No se efectuó staging ni commit.
