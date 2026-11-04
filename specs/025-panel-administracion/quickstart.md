# Guía de validación posterior a la implementación

La implementación funcional está completa. El registro final al pie de esta guía documenta las verificaciones, la revisión visual y el estado de cierre; los registros de incrementos previos se conservan como historial y no describen pendientes actuales. Consultar [modelo](data-model.md), [contrato](contracts/administracion.md) y [matriz de aceptación](contracts/testing-matrix.md).

## Precondiciones en esta notebook

Desde la raíz del checkout actual, sin rutas de otra computadora:

```powershell
git branch --show-current
git status --short
git worktree list
docker version
docker compose version
docker context show
```

Esperado: rama 025-Panel-Administracion y contexto Docker local elegido conscientemente. No cambiar worktrees ni limpiar cambios. No apuntar a una base de producción o una instancia anterior para pruebas de migración/concurrencia.

Si no existe .env, copiar el ejemplo; si existe, conservarlo:

```powershell
if (-not (Test-Path -LiteralPath .env)) { Copy-Item -LiteralPath .env.example -Destination .env }
```

Completar SECRET_KEY propia y credenciales locales; DATABASE_URL dentro de Compose debe usar el servicio db. Mantener backend de correo de consola para validación manual. No pegar secretos en documentos ni versionar .env. No se presupone ningún volumen existente. Con datos reales, hacer respaldo antes de aplicar migraciones; los tests usan una base de test separada.

## Arranque futuro

```powershell
docker compose config --quiet
docker compose up -d --build db web
docker compose exec web python manage.py check
docker compose exec web python manage.py showmigrations usuarios
docker compose exec web python manage.py migrate --plan
```

Revisar el plan y el entorno local antes de aplicar:

```powershell
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
```

Las migraciones futuras deben crear campos/constraints y Administradores con permiso; no asignar usuarios ni activar inactivos. El superusuario creado mantiene Django Admin pero **no entra al panel nuevo** hasta pertenecer expresamente al grupo con permiso. Si ya hay superusuario local no crearlo de nuevo.

Desde Django Admin local, configurar cuentas de validación mediante sus herramientas existentes: administrador_panel activo con Administradores y permiso, usuario común activo, bioquímico, cuenta pendiente por registro y cuenta aprobada suspendida mediante el flujo implementado. No dar staff ni permisos de edición a quienes solo necesiten panel. Para probar tipos, asignar estudios.gestionar_catalogo de forma independiente.

Si la base local no tiene catálogo y se necesita un conjunto representativo, el importador existente sigue siendo opcional:

```powershell
docker compose exec web python manage.py importar_catalogo_pruebas
```

No modifica las reglas de la nueva consulta ni reemplaza las fixtures de tests.

## Checks y tests futuros

```powershell
docker compose exec web ruff check .
docker compose exec web ruff format --check .
docker compose exec web python manage.py makemigrations --check --dry-run
docker compose exec web pytest usuarios/tests
docker compose exec web pytest pruebas/tests estudios/tests informes/tests
docker compose exec web pytest
```

Esperado: migraciones de modelo coherentes, todos los escenarios de la matriz automatizados y regresiones completas en verde. En usuarios/tests deben incluirse los tests futuros de migración y concurrencia; pytest-django crea su propia base y requiere permiso local para crearla. No configurar reuse-db como supuesto ni reemplazar PostgreSQL por SQLite.

Los tests de correo usan mailoutbox/callbacks, nunca SMTP real. Los de carreras usan conexiones distintas y transaction=True; deben demostrar una sola resolución efectiva y ninguna sobrescritura obsoleta. MigrationExecutor restaura esquema final. No declarar completada una carrera si solo se simuló un select_for_update.

CSS, con el mismo CLI incluido por Dockerfile:

```powershell
docker compose exec web tailwindcss -i static/src/aqualab.css -o static/css/aqualab.css --minify
git diff -- static/css/aqualab.css
```

Revisar el resultado y versionarlo durante la implementación autorizada, nunca hacer commit desde esta guía. CI recompila el mismo archivo y exige que no cambie. Evitar clases nuevas presentes solo en forms_administracion.py sin source correspondiente.

## Recorridos manuales de validación

1. Entrar con administrador_panel: sección Administración y tres listados con diseño común. Sin ambos controles, menú ausente y URLs/POST protegidos 403. Superusuario fuera de grupo puede usar /admin/ y no el panel.
2. Solicitud nueva: aprobar confirmando, un aviso y login habilitado; repetir sin nuevo aviso. Rechazar otra elegible sin historial protegido, relaciones impeditivas ni firma solo tras confirmar; cancelar conserva pendiente; rechazo efectivo elimina y libera correo para otro registro, con un aviso de rechazo.
3. Usuarios y roles: comprobar tres estados. Desactivar cuenta ajena conserva historia y bloquea acceso con sesión previa. Reactivar recupera acceso sin aviso inicial. Cuenta pendiente no ofrece acciones de rol/estado fuera de Solicitudes.
4. Cambiar rol propio/ajeno, cancelar y confirmar: solo cambia Bioquímicos; Administradores, permisos individuales y otros grupos siguen. Intentar desactivación propia por UI y POST: impedida.
5. Abrir dos confirmaciones sobre la misma cuenta; resolver una y confirmar la otra: advertencia de cambio, sin sobrescritura. Repetir cruzando ficha admin/panel y comprobar correos.
6. Pruebas: código/nombre parcial, mayúsculas, limpiar, páginas, activas/inactivas, tipo/unidad y Sin unidad. Enlace abre ficha admin, que conserva sus permisos y restricciones; no hay editor nuevo.
7. Tipos: enlace solo en Administración si cumple ambos controles de navegación, fuera de Estudios; gestor sin acceso al panel conserva tarjeta de Inicio y URL directa con su permiso. Repetir los flujos existentes de tipos.
8. Migración sobre base de prueba histórica y US2.9: inactivos no obtienen acceso ni pierden referencias. Intentar rechazar una pendiente histórica con referencias protegidas o firma: se informa el motivo, conserva íntegramente cuenta/correo/referencias/firma/historial/estado/versión y sigue sin acceso; no hay aviso ni liberación de correo. Revisar el caso y confirmar su aprobación por el flujo normal si corresponde: conserva historial/firma y recibe solo el aviso de aprobación; nunca se activa por el rechazo impedido ni se relajan PROTECT o borran referencias/firmas. Verificar variantes automatizadas previstas en T006/T034. No probar esto sobre una base compartida o real.

Validar SC-005 con flujos directos del contrato: dos acciones para confirmar cambios de estado/resolución y tres para rol desde su pantalla independiente con la alternativa preseleccionada. Revisión visual de encabezados, tablas, mensajes, etiquetas y foco en escritorio; no sustituye tests automatizados.

## CI y condiciones de cierre

El CI existente usa Python 3.12/PostgreSQL 16, librerías WeasyPrint, ruff, revisión de migraciones, compilación Tailwind v4.3.3 y pytest. La cobertura prevista comprende 35 escenarios, 17 FR y 7 criterios de éxito; la implementación debe acreditar sus tests y verificaciones concretas. No necesita nuevos servicios ni dependencias. Antes del PR, completar el identificador real Jira/US y enlazar esta spec; no inventarlo.

## Registro del primer bloque fundacional — 2026-11-03

Alcance de esta ejecución de speckit-implement: T001/T002/T005/T008/T009/T010/T011 completas, 7/68; restantes 61 sin marcar. Fixtures y tests de rol/servicios/HTTP que exceden este corte siguen pendientes, aunque se haya preparado parte de sus archivos. No se publicaron rutas o pantallas del panel.

Preparación: rama 025-Panel-Administracion, un worktree, HEAD/origin/main en 8792ec0 tras fetch, sin diferencias remotas. Se preservaron los documentos locales. `.gitignore` y `.dockerignore` ya cubrían los patrones necesarios y no se modificaron. Checklist de requisitos 16/16, sin modificar marcadores.

Docker está disponible mediante el socket local fuera del sandbox. Se creó .env local ignorado por Git desde el ejemplo, sin sobrescribir archivos previos, y se construyó la imagen usando Dockerfile/requirements existentes. Proyecto Compose explícito `aqualab`, servicio `db`, volumen propio `aqualab_postgres_data`, PostgreSQL real **16.15**. No se usó ni modificó `court_booking_db` (otro proyecto, PostgreSQL 17). No hay dependencias nuevas.

Los tests se ejecutaron mediante contenedores efímeros: `docker compose -p aqualab run --rm -T --no-deps web ...`. pytest-django creó y eliminó su base `test_aqualab`; MigrationExecutor probó forward/backward y restauró el esquema final. Las migraciones nuevas no se aplicaron a la base de aplicación `aqualab`: se aplicaron/revirtieron en la base de test. No se accedió a bases compartidas o de producción. Al detener este bloque queda el servicio db local disponible; no se inició un servidor web permanente.

| Verificación ejecutada | Resultado |
| --- | --- |
| Fase roja: política antes de crear módulo | Error de colección por módulo inexistente, esperado |
| Fase roja: modelo antes de campos | 1 fallo por estado_cuenta inexistente, esperado |
| Primer conjunto modelo/permisos/migraciones | 47 passed in 9.52s |
| Primera regresión completa de usuarios | 9 failed, 160 passed in 40.53s; detectó activaciones antiguas y etiqueta anterior |
| Regresión tras adaptación mínima de compatibilidad | 176 passed in 41.53s |
| Suite final usuarios, con casos adicionales de permisos y reversión | **180 passed in 43.28s**, sin skips |
| python manage.py check, final | System check identified no issues (0 silenced) |
| python manage.py makemigrations --check --dry-run, final | No changes detected |
| ruff check . | All checks passed! |
| ruff format --check . | 205 files already formatted |
| Ruff check y format --check de las dos migraciones nuevas, explícitos | En verde; 2 files already formatted |

La revisión automática rechazó inicialmente makemigrations por la prohibición de la etapa documental anterior; tras comprobar la autorización actual explícita de generar migraciones, aceptó el mismo comando. No se eludió el rechazo ni se sustituyó por generación indirecta.

Adaptaciones de integración necesarias para que el constraint no rompiera caminos existentes: registro fija aprobada=False; acciones admin aprueban ambos conceptos y no tratan desactivadas como pendientes; ficha preserva aprobación y evita aviso inicial al reactivar; login distingue pendiente/desactivada solo con contraseña correcta. Los tests antiguos de autenticación ahora aprueban mediante la acción real del admin en vez de escribir is_active aislado; el filtro admin espera su nueva etiqueta Activa y distingue que lista todas las inactivas.

Esto **no completa T012–T019**: faltan núcleo compartido, bloqueo previo al binding, revisión firmada, guardas de desactivación propia/concurrencia y la protección completa de rechazo histórico de I1 en los canales administrativos. El rechazo existente no se considera validado para pendientes históricas con firma. No desplegar la feature ni asumir todas sus reglas operativas hasta cerrar ese incremento; no se implementaron pantallas para exponerlo. La versión actual registra cambios de estado del admin, pero la revisión completa de cambios M2M corresponde al siguiente bloque.

T003 conserva trabajo pendiente de fixtures compartidas para recorridos posteriores; T004 aún no cubre operaciones de rol inexistentes y T020 no cubre endpoints HTTP aún no implementados. Por eso siguen sin marcarse, igual que T007/T015 pese a los ajustes parciales de compatibilidad. Próximo trabajo: completar esas dependencias y pruebas T006/T007, después T012–T016, y finalmente confirmaciones T017–T019 antes de las interfaces. La ejecución se detuvo por el límite solicitado, sin commit, push, PR ni merge.

## Segundo incremento — Servicios e integración administrativa — 2026-11-03

Continuación autorizada mediante el workflow original speckit-implement, en la misma rama y worktree. Se preservó el primer bloque. Checklist 16/16, ignorados existentes adecuados y sin extensions.yml ni hooks registrados. Sin nuevas dependencias, migraciones adicionales o pantallas/rutas del panel; únicamente se adaptó la confirmación existente del admin.

El núcleo de servicios recarga y autoriza al actor antes de consultar objetivos, bloquea actor/objetivos en orden PK, vuelve a autorizar y compara revisión/instantánea dentro de atomic. Los adaptadores del panel exigen su política conjunta; los del admin conservan staff y change/delete. Aprobar, rechazar y guardar la ficha comparten reglas de transición y callbacks existentes tras commit. Reactivación y no-op no envían aprobación inicial. El cambio de rol solo agrega/retira Bioquímicos, incluso para el propio actor; la desactivación propia se impide por servicio y ficha.

I1: se impide el rechazo ante PROTECT o firma profesional (aunque su relación sea CASCADE), con motivo, sin aviso ni cambio de cuenta/correo/estado/versión/historial. El savepoint revierte también el log de eliminación si PROTECT impide borrar. La aprobación normal posterior conserva las referencias y firma. Los lotes pueden resolver las solicitudes elegibles e informar individualmente las impedidas.

La ficha se bloquea antes de cargar/bindear. Su formulario valida contexto firmado y prepara aprobación coherente antes de constraints. El núcleo guarda una instancia recargada una sola vez con los campos modificados, preservando valores actuales ajenos a la propuesta; save_related conserva el mecanismo M2M de Django y registra cambios de grupos/permisos en la misma transacción. El cambio de contraseña usa el mismo orden de locks y aumenta revisión, invalidando fichas anteriores. No se reemplaza la autorización normal del admin ni el flujo de altas.

Las confirmaciones del panel usan salts/clave de sesión propios, actor y huella HMAC de sesión, operación/objetivo/revisión, instantánea y digest de propuesta cerrada. TTL 3600 s y máximo 20 borradores, purga de vencidos, rechazo de manipulación/reutilización y cancelación sin escritura de dominio. La preparación captura la instantánea bajo bloqueo; confirmar reautoriza y comprueba revisión, incluyendo A→B→A. No se almacenan contraseñas ni se exponen identificadores de sesión. Tipos de estudio permanece intacto.

| Regla verificada por tests del incremento | Referencias concretas |
| --- | --- |
| Resolución única, rechazo efectivo/rollback y aprobación posterior a rechazo impedido | test_administracion_servicios.py: test_aprobacion_unica_y_reactivacion_sin_aviso, test_rechazo_libera_correo_y_rollback_no_avisa, test_rechazo_impedido_y_aprobacion_posterior (PROTECT/firma) |
| Autorizaciones independientes, actor revocado, propia y revisión ABA | test_administracion_servicios.py: test_adaptadores_admin_conservan_autorizacion_independiente, test_servicio_reautoriza_actor_revocado, test_autorizacion_estado_y_revision |
| Bioquímicos sin pérdida de otras membresías/permisos | test_administracion_modelo.py: test_panel_solo_modifica_pertenencia_bioquimicos |
| Ficha antigua/otra sesión/sin firma, M2M, propia, contraseña e I1 por admin | test_administracion_ficha.py y regresiones test_notificaciones.py/test_administracion_compatibilidad.py |
| Firma/digest/identidad/sesión/operación, TTL/cota, consumido, cancelación y ABA | test_administracion_confirmaciones.py |
| Cuatro pares de resoluciones y panel contra acción/ficha con conexiones independientes | test_administracion_concurrencia.py: test_una_resolucion_y_un_aviso y test_panel_frente_admin; se comprueba espera real con pg_blocking_pids y timeouts |
| Correo fuera de atomic tras commit real | test_administracion_concurrencia.py: test_aviso_solo_tras_commit_real |

Las carreras no usan SQLite ni mocks de locks. La sustitución de la función de aviso en el último test solo observa in_atomic_block y llama al emisor real. Los tests históricos del admin ahora obtienen el contexto firmado mediante GET/confirmación real; no se incorporó una excepción para POST sin firma. Se corrigieron fixtures de número PI y preservación de microsegundos de date_joined, además de una incidencia transitoria de codificación UTF-8 al editar desde Windows.

Esta evidencia cubre fundamentos, no los 35 recorridos completos de UI. T020 y siguientes continúan pendientes: faltan endpoints, navegación y listados del panel, recorridos HTTP, concurrencia posterior de roles/estados, catálogo, traslado de tipos y cierre integral. No se publica ni despliega la feature; sigue pendiente el identificador real Jira/US antes de preparar el PR.

### Resultados y corte verificado

| Ejecución | Resultado exacto |
| --- | --- |
| Fase roja del núcleo | Error de colección esperado: servicios_administracion aún no existía |
| Regresión inicial del incremento | 8 failed, 178 passed in 52.21s; fixture sin PI, selección confirmada y codificación, corregidos |
| Núcleo/ficha/confirmaciones/avisos tras correcciones | 1 failed, 46 passed in 22.50s; se corrigió el helper que truncaba date_joined, sin alterar las reglas de versión |
| Ficha y seis carreras PostgreSQL | 12 passed in 8.83s |
| Suite intermedia usuarios | 210 passed in 59.36s |
| Suite completa del repositorio | **1367 passed in 415.41s (0:06:55)** |
| Suite final usuarios | **218 passed in 65.90s (0:01:05)**, sin fallos ni skips |
| manage.py check final | System check identified no issues (0 silenced) |
| makemigrations --check --dry-run final | No changes detected |
| ruff check . / ruff format --check . | All checks passed! / 211 files already formatted |
| git diff --check | Sin errores |

La suite completa comenzó antes de añadir los últimos cinco casos de usuarios y de cerrar los ajustes de mensajes/contextos/IDs de la ficha; la ejecución final de usuarios verifica todos esos casos y ajustes. Las suites se ejecutaron secuencialmente sobre test_aqualab, sin competir entre sí. Los tests de migración/concurrencia siguen usando PostgreSQL 16.15 real y restaurando/limpiando la base de test; no se aplicaron migraciones a la base de aplicación.

Completadas en este incremento **T003, T004, T006, T007 y T012–T019**. Total acumulado **19/68 completas**, **49 pendientes**. No se marcaron tareas de historias posteriores por disponer anticipadamente de un adaptador del núcleo. Próximo bloque: US1 T020–T025 (política HTTP y navegación incremental con enlaces efectivos), seguido de Solicitudes T026–T037 según dependencias; no se ejecutó ese bloque.

Inventario de este incremento, aparte de los cambios preservados del primero:

- Nuevos: usuarios/servicios_administracion.py, usuarios/confirmaciones_administracion.py; usuarios/tests/test_administracion_servicios.py, test_administracion_ficha.py, test_administracion_confirmaciones.py y test_administracion_concurrencia.py.
- Modificados: usuarios/admin.py, usuarios/forms.py, usuarios/templates/admin/usuarios/usuario/rechazar_confirmacion.html; usuarios/tests/conftest.py, test_notificaciones.py, test_administracion_modelo.py y test_administracion_compatibilidad.py.
- Seguimiento: specs/025-panel-administracion/tasks.md y quickstart.md. Checklist no modificada; spec/plan/research/data-model/contratos y otras features se preservan.

Sin extensiones ni hooks after_implement registrados. Sin nuevas migraciones, dependencias, commit, push, PR, merge o servidor web permanente. Se detiene aquí por el límite autorizado del incremento.

## Cierre integral de la implementación — 2026-11-03

El usuario autorizó completar T020–T068 autónomamente mediante speckit-implement original. Se preservaron los dos incrementos anteriores y se mantuvieron exactamente los 35 escenarios, FR-001–FR-017 y SC-001–SC-007. La actualización de spec/plan/research/data-model/contratos registra el estado ejecutado; no altera decisiones funcionales o diseño. Checklist 16/16 intacta. No hay extensions.yml ni hooks registrados.

### Funciones y checkpoints

- Acceso y navegación: decorador conjunto, ocho rutas bajo /administracion/, permiso real sin bypass de superusuario, navegación con tres listados efectivos y estados activos. Anónimos usan el login existente; usuarios autenticados sin autorización reciben 403 antes de buscar objetivos. Métodos y CSRF verificados por separado.
- Solicitudes: pendientes exclusivamente, orden/páginas de 20, confirmación/cancelación, aprobación y rechazo efectivos con avisos existentes tras commit, reenvíos sin duplicación, ausencia/conflicto y rollback con mensaje. I1 impide rechazar cuentas con PROTECT o firma, conservando todo sin correo, con aprobación posterior normal.
- Usuarios/roles: tres estados y rol derivado sin N+1, orden estable y páginas de 20. Selección en pantalla independiente con original firmado; cambio propio permitido, desactivación propia impedida y pendientes excluidas de gestión. Solo cambia Bioquímicos; conserva grupos/permisos equivalentes por otras vías, identidad y estado. Desactivadas admiten cambio de rol sin habilitar acceso. Error de persistencia revierte también las membresías.
- Catálogo: consulta de activas/inactivas, búsqueda parcial por código/nombre, espacios/limpiar, unidad legible, tipo de cálculo, estado y paginación que conserva q. Enlace al editor normal, sin permisos nuevos ni endpoint de edición.
- Tipos: enlace reubicado bajo Administración únicamente con ambas autorizaciones de navegación. Servicios/rutas/permisos de tipos e Inicio intactos. Gestor sin panel conserva acceso directo y tarjeta; administrador sin gestionar_catalogo recibe 403.

### Ejecuciones de este cierre

Todos los comandos se ejecutaron con `docker compose -p aqualab run --rm -T --no-deps web ...`, salvo operaciones explícitas sobre la base separada de revisión visual. pytest usa test_aqualab en PostgreSQL 16.15, sin SQLite ni mocks de locks. No se ejecutaron suites concurrentes sobre esa base.

| Verificación | Resultado |
| --- | --- |
| Fase roja de navegación | 2 failed, 1 passed; namespace administrativo inexistente, esperado |
| Primera navegación/solicitudes | 9 passed in 5.86s |
| Solicitudes/avisos/matriz inicial | 76 passed in 12.71s |
| Regresión usuarios tras roles/estados y nuevas carreras | 271 passed in 80.28s |
| Catálogo/tipos y regresiones de tipos | 129 passed in 30.06s |
| Usuarios con matriz HTTP completa de ocho rutas | 370 passed in 93.46s |
| Primera suite completa de cierre | 1524 passed in 567.97s (0:09:27) |
| Rol inline y permisos profesionales equivalentes | 5 passed in 4.57s |
| Rol de cuenta desactivada y rollback de membresías, cierre de auditoría | 7 passed in 6.18s |
| Suite completa definitiva | **1526 passed in 461.37s (0:07:41)**; sin fallos ni skips |
| Ruff check . final | All checks passed! |
| Ruff format --check . final | 223 files already formatted |
| manage.py check final | System check identified no issues (0 silenced) |
| makemigrations --check --dry-run final | No changes detected |
| Tailwind CLI fijado | v4.3.3; compilación correcta y comparación exacta con salida temporal |
| WeasyPrint (paso adicional de CI) | PDF generado correctamente |
| git diff --check | Sin errores |

El CSS generado reutiliza clases ya existentes: no tiene diferencias lógicas contra main. Se verificó reproducibilidad byte a byte en un contenedor y se restauraron los finales de línea CRLF esperados por core.autocrlf=true en Windows, sin cambiar configuración Git. El chequeo de contenido normalizado equivale al checkout LF de CI; el archivo CSS queda limpio en git status. CI remoto no se ejecutó: no se hizo commit/push/PR.

Problemas detectados y resueltos: fases rojas por rutas todavía no registradas; una expectativa inicial de paginación comparaba entidades HTML en vez del href interpretado, corregida sin alterar el componente existente; el buscador usaba una clase sin estilo, corregida a form-control durante inspección visual. La auditoría agregó aserciones sobre permisos profesionales equivalentes, flujo de rol inline, cuentas desactivadas y rollback M2M. En la prueba nueva se distinguió explícitamente conservar asignaciones de habilitar permisos: ModelBackend sigue denegando permisos efectivos a cuentas inactivas. No se relajó ninguna regla para hacer pasar tests.

### Revisión visual y SC-005

Revisión real en navegador local de escritorio, viewport temporal 1366×900 restaurado al terminar, exclusivamente sobre **aqualab_panel_revision** (base nueva creada para esta revisión). Cuenta y catálogo sintéticos; correo de consola. La base de aplicación aqualab y bases de otros proyectos no se modificaron. Se aplicaron las migraciones existentes a esta base nueva, sin generar otras.

Se comprobaron menú/selección activa, identidad, labels, foco visible del buscador, tablas y estados vacíos; aprobación en 2 acciones, cancelación de rechazo, rechazo impedido con motivo, rol propio de ida/vuelta en 3 acciones, persistencia de Administración, ausencia de desactivación propia y rechazo de su URL directa, desactivación/reactivación ajena en 2 acciones, catálogo/búsqueda/páginas y acceso normal a tipos. Superusuario fuera del grupo recibió 403 en el panel y pudo abrir Django Admin. El rechazo efectivo y la liberación de correo quedan acreditados por los tests automatizados; no se borraron datos reales durante la revisión visual.

Capturas de evidencia (solo datos sintéticos):

- **Histórica, interfaz sustituida:** [Usuarios y roles](evidence/usuarios-y-roles.jpg), con el antiguo selector inline y «Revisar rol». No representa el listado actual.
- **Histórica para la navegación lateral:** [Rechazo impedido](evidence/rechazo-impedido.jpg), conservada para acreditar cuenta preservada y motivo informado; precede al ajuste de alineación del menú.
- **Histórica para la navegación lateral:** [Catálogo y búsqueda](evidence/catalogo-busqueda.jpg), conservada para acreditar búsqueda, foco, datos y destino admin; precede al ajuste de alineación del menú.
- **Histórica, estilo sustituido:** [Catálogo vacío](evidence/catalogo-vacio.jpg), anterior a la corrección del estilo del buscador. No representa el control actual.
- [Superusuario sin grupo](evidence/superusuario-sin-grupo.jpg): respuesta HTTP 403.

### Abrir y reiniciar la revisión local

Queda disponible el contenedor **aqualab-panel-revision**, conectado solo a la base de revisión y publicado en **127.0.0.1:8000**. La pestaña entregada conserva la sesión de la cuenta sintética panel@revision.local. Abrir [Usuarios y roles](http://127.0.0.1:8000/administracion/usuarios/), [Solicitudes](http://127.0.0.1:8000/administracion/solicitudes/) o [Catálogo](http://127.0.0.1:8000/administracion/pruebas/).

Si se detuvo Docker o el contenedor:

```powershell
docker compose -p aqualab up -d db
docker start aqualab-panel-revision
```

Para detener solo esta vista de prueba: `docker stop aqualab-panel-revision`. No se eliminan contenedores, volúmenes o bases ajenos. Si se necesita una cuenta propia, `docker exec -it aqualab-panel-revision python manage.py createsuperuser`, iniciar sesión en /admin/ y asignar a esa cuenta el grupo Administradores desde la ficha de usuarios. Ser superusuario por sí solo no habilita el panel. No se guardan contraseñas ni credenciales en esta documentación.

Para un entorno de aplicación distinto de esta revisión, usar los comandos de precondiciones/arranque al comienzo de esta guía: verificar DATABASE_URL y respaldo antes de aplicar migraciones a datos reales; no confundir la base de revisión con una compartida o de producción.

### Riesgos y notas para el futuro PR

Título provisional: **Panel de administración: solicitudes, usuarios y catálogo**. Referencia a specs/025-panel-administracion/spec.md; completar la clave Jira/US real cuando la proporcione el equipo, sin inventarla. Descripción revisable: las tareas cotidianas pasan a vistas protegidas con el diseño común, conservando el admin existente, permisos independientes de tipos y avisos. El rechazo histórico se impide sin perder información; roles profesionales y Administración permanecen independientes.

Validación: usar los resultados finales anteriores y la trazabilidad 35/35, 17/17 y 7/7 de contracts/testing-matrix.md; adjuntar la evidencia visual. Migraciones 0003/0004 conservadoras, previamente verificadas forward/backward en base de test; respaldo antes de desplegar. Revertir el esquema pierde la distinción nueva y no activa cuentas automáticamente.

Límites conservados: la aprobación de inactivos históricos requiere revisión humana, sin inferirla por actividad/grupos; on_commit evita duplicados normales pero no incorpora una cola de entrega exactamente una vez ante caída de proceso. Las fichas antiguas requieren nueva revisión después de cambios. SQL manual fuera de los canales coordinados no tiene garantía universal de detección ABA. No hay dependencias nuevas ni cambios a CI, Constitution, otras features, editor de pruebas o gestión de tipos.

La preparación técnica es local. No se creó commit, push, PR ni merge; antes del PR faltan el identificador Jira/US real, revisión del equipo y CI remoto cuando el usuario autorice publicar.

### Inventario acumulado frente a main

Incluye los incrementos anteriores preservados. Los documentos de 025 eran locales sin commit al iniciar; se listan como nuevos frente a main. No se incluyen archivos ignorados de entorno ni bases/volúmenes Docker.


**Archivos existentes modificados**

- `config/urls.py`
- `templates/ui/menu.html`
- `usuarios/admin.py`
- `usuarios/context_processors.py`
- `usuarios/forms.py`
- `usuarios/models.py`
- `usuarios/templates/admin/usuarios/usuario/rechazar_confirmacion.html`
- `usuarios/tests/conftest.py`
- `usuarios/tests/test_admin.py`
- `usuarios/tests/test_autenticacion.py`
- `usuarios/tests/test_formulario_login.py`
- `usuarios/tests/test_notificaciones.py`
- `usuarios/views.py`

**Archivos nuevos**

- `specs/025-panel-administracion/checklists/requirements.md`
- `specs/025-panel-administracion/contracts/administracion.md`
- `specs/025-panel-administracion/contracts/testing-matrix.md`
- `specs/025-panel-administracion/data-model.md`
- `specs/025-panel-administracion/evidence/catalogo-busqueda.jpg`
- `specs/025-panel-administracion/evidence/catalogo-vacio.jpg`
- `specs/025-panel-administracion/evidence/rechazo-impedido.jpg`
- `specs/025-panel-administracion/evidence/superusuario-sin-grupo.jpg`
- `specs/025-panel-administracion/evidence/usuarios-y-roles.jpg`
- `specs/025-panel-administracion/plan.md`
- `specs/025-panel-administracion/quickstart.md`
- `specs/025-panel-administracion/research.md`
- `specs/025-panel-administracion/spec.md`
- `specs/025-panel-administracion/tasks.md`
- `usuarios/confirmaciones_administracion.py`
- `usuarios/forms_administracion.py`
- `usuarios/migrations/0003_estado_aprobacion.py`
- `usuarios/migrations/0004_grupo_administradores.py`
- `usuarios/permisos_administracion.py`
- `usuarios/servicios_administracion.py`
- `usuarios/templates/usuarios/administracion/confirmar.html`
- `usuarios/templates/usuarios/administracion/pruebas.html`
- `usuarios/templates/usuarios/administracion/rol.html`
- `usuarios/templates/usuarios/administracion/solicitudes.html`
- `usuarios/templates/usuarios/administracion/usuarios.html`
- `usuarios/tests/test_administracion_avisos.py`
- `usuarios/tests/test_administracion_catalogo.py`
- `usuarios/tests/test_administracion_catalogo_admin.py`
- `usuarios/tests/test_administracion_compatibilidad.py`
- `usuarios/tests/test_administracion_concurrencia.py`
- `usuarios/tests/test_administracion_confirmaciones.py`
- `usuarios/tests/test_administracion_estados.py`
- `usuarios/tests/test_administracion_ficha.py`
- `usuarios/tests/test_administracion_migraciones.py`
- `usuarios/tests/test_administracion_modelo.py`
- `usuarios/tests/test_administracion_navegacion.py`
- `usuarios/tests/test_administracion_permisos.py`
- `usuarios/tests/test_administracion_servicios.py`
- `usuarios/tests/test_administracion_solicitudes.py`
- `usuarios/tests/test_administracion_tipos_acceso.py`
- `usuarios/tests/test_administracion_tipos_menu.py`
- `usuarios/tests/test_administracion_usuarios.py`
- `usuarios/urls_administracion.py`
- `usuarios/views_administracion.py`

### Estado final

**68/68 tareas completas y verificadas, 0 pendientes**. Se conserva el número original de tareas y los 35 escenarios aprobados. La suite definitiva incluye los últimos casos de rol/desactivadas/rollback y los flujos inline; no quedan verificaciones locales automáticas o visuales sin ejecutar dentro de este alcance. La clave Jira/US real y CI/revisión remotos son pasos previos al PR, no requisitos inventados ni publicaciones realizadas. Se ejecuta a continuación el análisis documental final original, sin escrituras automáticas.

### Primera corrección de UX (histórica; sustituida por el flujo siguiente)

Se renombró el botón a **Revisar cambio**, tanto inline como en el formulario alternativo. Se conserva el flujo de revisión y confirmación existente. Las acciones tienen una estructura de dos filas: selector y revisión arriba, Desactivar/Reactivar debajo alineado con el selector y con el mismo ancho. La cuenta propia conserva el espacio sin ofrecer desactivación; los correos largos pueden ajustarse al ancho disponible. Gestionar tipos usa el mismo padding izquierdo que los demás accesos de Administración.

Verificación del marcado definitivo: **16 passed in 9.38s** en usuarios/roles, estados, navegación y menú de tipos. Tailwind v4.3.3 recompilado y salida reproducible; git diff --check correcto. La suite completa de 1526 tests corresponde al cierre previo; para esta corrección visual se ejecutó el conjunto afectado, sin cambios de lógica de dominio ni nuevos tests que reproduzcan CSS.

En navegador, una cuenta sintética mostró **121 px de alto tanto Activa como Desactivada**, posiciones idénticas de controles respecto de la fila y cero desbordamiento horizontal de la tabla. Gestionar tipos y los demás accesos comparten left=12 px y padding-left=12 px. Se restauró la cuenta sintética al estado inicial. Las capturas se recortaron a esa cuenta, sin incluir los datos que el usuario agregó posteriormente a la base de revisión: [Activa](evidence/ux-usuarios-activa.jpg) y [Desactivada](evidence/ux-usuarios-desactivada.jpg).

Archivos de esta corrección: usuarios/templates/usuarios/administracion/usuarios.html, rol.html, templates/ui/menu.html y static/css/aqualab.css, más este registro, tasks.md y las dos capturas. No se modifican los requisitos aprobados ni el número de tareas.


### Flujo vigente de cambio de rol solicitado por el usuario

Se retira el selector inline. El listado muestra el rol como texto y el enlace **Cambiar rol**, junto a Desactivar/Reactivar en una fila compacta. El enlace abre una pantalla independiente que identifica la cuenta, muestra su rol actual y ofrece exclusivamente los otros roles profesionales disponibles. Actualmente hay dos roles profesionales: Usuario común y Bioquímico; Administradores sigue siendo una pertenencia independiente, no una opción de rol profesional.

La alternativa disponible está preseleccionada, sin guardarse: **Cambiar rol → Continuar → Confirmar**. Cancelar conserva el estado original. Un contexto obsoleto se comprueba antes de validar las alternativas y nuevamente bajo bloqueo al preparar/confirmar, para no interpretar un cambio concurrente como una selección inválida.

Verificaciones de esta versión: **374 passed in 85.00s** en usuarios/tests, Ruff correcto, tres archivos Python modificados con formato correcto y manage.py check sin incidencias. Los tests nuevos comprobaron primero el fallo de la versión anterior y luego las alternativas para ambos roles. Se recompiló Tailwind. La suite general de 1526 tests documentada arriba pertenece al cierre previo; esta modificación ejecutó la suite completa del módulo afectado.

Revisión real en navegador: cero selectores en el listado, **73 px por fila** frente a 121 px de la versión anterior y cero desbordamiento horizontal en el ancho probado. Se verificaron la pantalla de selección, la confirmación y la cancelación usando solo la cuenta sintética. Evidencia sin datos personales añadidos por el usuario: [Listado compacto](evidence/ux-usuarios-compacto.jpg) y [Pantalla de cambio](evidence/ux-cambiar-rol-pantalla.jpg).

Archivos del ajuste: usuarios/forms_administracion.py, usuarios/views_administracion.py, usuarios/templates/usuarios/administracion/usuarios.html, rol.html, usuarios/tests/test_administracion_usuarios.py y static/css/aqualab.css; sincronización de contrato/matriz/tareas y estas notas. No cambia el alcance funcional aprobado ni la cantidad de tareas. Sin commit, push ni PR.

### Identificación de administradores en el listado

Por solicitud del usuario, las cuentas del grupo Administradores muestran la etiqueta **Administrador** debajo del nombre, separada del rol profesional. La consulta usa Exists, sin consultas adicionales por cada fila. Ser superusuario fuera del grupo no agrega esta etiqueta ni cambia la autorización existente.

Verificado con **9 passed in 6.62s** en test_administracion_usuarios.py, incluida la distinción grupo/superusuario y el control de consultas constantes. Ruff correcto; CSS existente actualizado y reproducible. En navegador se comprobó la etiqueta en la cuenta sintética, manteniendo la fila en 73 px y sin desbordamiento horizontal. [Evidencia recortada](evidence/ux-etiqueta-administrador.jpg).

### Clasificación de evidencias para la publicación de la rama

Se conservan estas diez capturas pertinentes a la validación y a las correcciones solicitadas. Todas contienen datos sintéticos; ninguna contiene credenciales, información personal incorporada posteriormente a la base de revisión ni metadatos EXIF. Las históricas documentan decisiones anteriores y no deben presentarse como representación de la interfaz vigente.

| Archivo | Clasificación y propósito |
| --- | --- |
| catalogo-busqueda.jpg | Histórica para el menú lateral; evidencia de consulta y búsqueda del catálogo. |
| catalogo-vacio.jpg | Histórica; estado vacío anterior a corregir el estilo del buscador. |
| rechazo-impedido.jpg | Histórica para el menú lateral; evidencia de rechazo impedido con cuenta conservada. |
| superusuario-sin-grupo.jpg | Vigente para la política: respuesta 403 al superusuario fuera de Administradores. |
| usuarios-y-roles.jpg | Histórica; listado con selector inline y «Revisar rol», ambos sustituidos. |
| ux-cambiar-rol-pantalla.jpg | Vigente: pantalla independiente, rol actual y alternativas disponibles. |
| ux-etiqueta-administrador.jpg | Vigente: etiqueta Administrador separada del rol profesional. |
| ux-usuarios-activa.jpg | Histórica; distribución en dos filas con «Revisar cambio», sustituida por el listado compacto. |
| ux-usuarios-compacto.jpg | Vigente: listado sin selector inline, con enlace Cambiar rol y acción de estado. |
| ux-usuarios-desactivada.jpg | Histórica; versión de dos filas con «Revisar cambio», sustituida por el listado compacto. |

La auditoría previa a esta publicación ejecutó nuevamente **1528 tests en PostgreSQL, todos aprobados en 398.03s**, incluidos los cambios visuales y la etiqueta de administrador. Los resultados menores que figuran en los registros anteriores son históricos. No se integró main: la base de esta feature sigue siendo 8792ec0; origin/main avanzó a 0ba781e con la feature 024, y la integración posterior requiere resolver el CSS generado y validar el conjunto.
