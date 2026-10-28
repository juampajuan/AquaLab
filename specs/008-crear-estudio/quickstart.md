# Validación de US 5.1

Implementación disponible en la rama codex/008-crear-estudio. La evidencia automatizada se registra al final; el recorrido manual fue confirmado por el usuario; detalle y límites en cierre-tecnico.md. [Plan](plan.md) y [contratos](contracts/crear-estudio-ui.md).

## Prerrequisitos

- Spec aprobada por el equipo según confirmación del usuario en este chat; plan/tareas autorizados. No se aportaron actas ni enlaces externos.
- Implementación sobre Muestra integrada de main 6b29f43 y base compartida única.
- Docker Compose con PostgreSQL 16; nunca SQLite para acreditar locks.
- Fixtures factories solo en estudios/tests/conftest.py: códigos TEST-A/TEST-B y nombres Prueba de test A/B, Tipo de test. Creadas por pytest en base aislada, sin fórmulas, unidades, límites, casos normativos ni composiciones reales. No fixtures con autoload productivo, ni seed ni migración de datos ficticios.

## Comandos de verificación

Desde la raíz del checkout de US 5.1:

```text
docker compose exec web python manage.py check
docker compose exec web python manage.py makemigrations --check --dry-run
docker compose exec web pytest estudios pruebas
docker compose exec web pytest
docker compose exec web ruff check .
docker compose exec web ruff format --check .
node --test usuarios/tests/js/sesion.test.cjs
```

Las tres migraciones de esquema autorizadas se aplicaron en desarrollo y en la base aislada de pytest; migrate --check confirma que no quedan pendientes. Ningún comando de test debe precargar contenido sintético en la base normal. Las factories de pytest se destruyen con la base de test.

## Casos y resultados esperados

| Caso | Resultado esperado |
|---|---|
| Elegir muestra por PI, tipo con dos pruebas genéricas | Resumen exacto; cero estudios hasta confirmar. |
| Confirmar resumen | Un estudio Pendiente de análisis, creador/hora automáticos, dos asignaciones y snapshots correctos; PI de muestra intacto. |
| Nueva solicitud misma muestra/tipo | Otro estudio y otro UUID; no unicidad muestra/tipo (decisión funcional del proyecto FR-013). |
| Cliente inactivo desde antes o durante revisión | Crear sobre muestra registrada sin reactivar cliente (decisión funcional del proyecto FR-014). |
| Cancelar o volver | Nada guardado por cancelar; volver permite editar selección. |
| Reenviar misma confirmación secuencial/concurrentemente | Mismo ID, un estudio y un conjunto; no cambia autor/hora. |
| Cambiar composición antes de confirmar | POST viejo no crea; nuevo resumen/token exige aceptación. Reenviar POST viejo tras ver resumen nuevo tampoco crea. |
| Cambiar solo nombre/descripcion | Nueva revisión; estudio anterior conserva textos históricos, incluida descripción vacía. |
| Editar/desactivar después de éxito y reenviar token vigente | Mismo estudio; no reescritura de snapshots. |
| Catálogo vacío/inactivo, referencia inválida o campo faltante | Mensaje específico, cero filas parciales, sin completar automáticamente datos ni ofrecer pruebas fuera del catálogo cargado. |
| Firma manipulada, otra sesión/usuario o sin CSRF | Rechazo, sin filas ni exposición de otra solicitud. |
| Falla al crear asignación | Rollback de cabecera/asignaciones; reintento con UUID crea una sola vez. |

## Concurrencia verificable

Tests django_db(transaction=True), hilos con conexiones independientes y timeouts. Cubrir dos ordenaciones: editor mantiene lock antes del creador → conflicto; creador mantiene lock antes del editor → estudio conserva conjunto anterior íntegro y edición aplica solo a futuros. Capturar errores y asegurar terminación de hilos; no usar sleeps como única sincronización. Helpers de tests mutan catálogo bajo el protocolo compartido y no son CRUD de producto US 5.5.

## Contexto académico y datos de demostración

No existe una fuente científica externa pendiente: AquaLab es académico y los datos serán ficticios. Se propone un catálogo explícitamente DEMO, sin validación científica. Las factories TEST-* continúan aisladas en pytest; la carga demo local está implementada como mecanismo separado, explícito e idempotente; su ejecución local de escritura espera revisión del usuario. Reactivación, eliminación y edición administrativa de US 5.5 requieren su propia implementación y pruebas posteriores.

Casos adicionales de identidad: cancelar y luego enviar el token anterior no crea; expirar token y recuperar la misma solicitud conserva UUID y exige revisión o devuelve solo el resultado propio; no se asigna UUID nuevo automáticamente por expiración. Verificar que un token válido de una solicitud ya creada no necesita borrador pendiente para devolver el resultado.


## Guía manual en Chrome — recorrido confirmado por el usuario

Abrir http://localhost:8000 en Chrome con los contenedores existentes. Usar una cuenta activa autorizada. No hay pantallas administrativas de catálogo en US 5.1. Para el recorrido completo se propone cargar el manifiesto DEMO local descrito en propuesta-datos-demo.md, mediante el comando ya aprobado e implementado, cuando el usuario autorice ejecutar la carga local. No hay que esperar un catálogo oficial externo. No ejecutar las factories de pytest contra desarrollo ni cargar datos automáticamente. Si el catálogo está vacío, solo puede verificarse su mensaje de indisponibilidad.

1. Entrar sin sesión a /estudios/crear/: redirección al login. Iniciar sesión y comprobar el enlace Crear estudio en inicio y navegación.
2. Seleccionar muestra: reconocer PI, cliente y origen. Seleccionar tipo activo. Omitir cada campo: error junto al campo y conservación del valor válido.
3. Pulsar Revisar estudio: comprobar muestra, tipo, descripción, pruebas y estado inicial. No debe crearse nada antes de confirmar.
4. Volver: conservar selección. Editarla y revisar otra vez. Cancelar: regresar sin crear. Reenviar un token cancelado no crea.
5. Confirmar: mensaje con identificador del estudio y PI; formulario vacío. Doble clic/reenvío de esa confirmación: mismo estudio. Una solicitud nueva deliberada del mismo tipo crea otro estudio.
6. Con muestra ya registrada de cliente inactivo, repetir la creación: funciona y no reactiva ni altera al cliente/muestra. No cambia las reglas para registrar muestras nuevas.
7. En QA controlado, con un escritor que respete el contrato de lock/version (US 5.5 aún pendiente), cambiar composición, nombre o descripción durante revisión: el POST previo no crea y exige aceptar el resumen actualizado. Desactivar: rechaza la nueva creación. Tras crear, editar el tipo no cambia textos ni asignaciones históricos.
8. Comprobar expiración y recuperación del resumen: recuperar renueva revisión de la misma solicitud sin crear automáticamente; una cancelada no se revive. Verificar claridad visual de errores, botones y mensajes.

Resultado manual vigente: el usuario confirmó el recorrido indicado en cierre-tecnico.md. No se atribuye observación directa al asistente. Los casos adicionales sin reporte individual conservan evidencia exclusivamente automatizada.


## Evidencia de cierre técnico — 27/10/2026

Entorno: checkout E:/Martino-Codex/AquaLab, rama codex/008-crear-estudio, HEAD y referencia local origin/main 6b29f434f31898c6b90290a8efd03fac475721a6. Python 3.12.15, Django 5.2.18, pytest 9.1.1, PostgreSQL 16.15 en el servicio db existente de Docker Compose. No se reiniciaron ni apagaron los contenedores en este cierre.

| Comando ejecutado desde el checkout | Resultado real |
|---|---|
| docker compose exec -T web pytest | 343 passed in 154.73s; suite general completa, no solo tests nuevos. |
| docker compose exec -T web ruff check . | All checks passed. |
| docker compose exec -T web ruff format --check . | 118 files already formatted; aplica las exclusiones existentes de pyproject.toml, incluidas migrations. |
| docker compose exec -T web python manage.py check | 0 issues, 0 silenced. |
| docker compose exec -T web python manage.py makemigrations --check --dry-run | No changes detected. |
| docker compose exec -T web python manage.py migrate --noinput | Migraciones de esquema aplicadas OK en desarrollo. |
| docker compose exec -T web python manage.py migrate --check | Sin migraciones pendientes de aplicar. |
| docker compose exec -T web python manage.py showmigrations pruebas estudios muestras | Todas las migraciones de esas apps marcadas X. |
| node --test usuarios/tests/js/sesion.test.cjs | 14 passed, 0 failed. |
| git diff --check | Sin errores de whitespace. |

La suite final incluye 70 tests de estudios/pruebas y 273 de las apps existentes. Los cinco casos concurrentes usan django_db(transaction=True), conexiones por hilo y PostgreSQL real; la fixture autouse exige connection.vendor=postgresql, SELECT version() y base con prefijo test_. El servicio ejecuta pg_advisory_xact_lock y select_for_update; no hay mocks de locks ni SQLite.

Historial de este cierre: primera suite general 336 passed. Al ampliar validaciones hubo una ejecución intermedia con 343 passed / 2 failed por expectativas incorrectas de los tests sobre full_clean en campos editable=False. Se corrigieron los tests para verificar el estado fijado por servicio/metadatos y el UUID obligatorio mediante IntegrityError real. La suite completa final posterior pasó sin fallos. Ruff detectó inicialmente saltos de línea mixtos en config/settings.py y config/urls.py; se normalizaron y el control posterior pasó. No se ocultaron errores ni se añadieron ignores.

Migraciones nuevas: pruebas/0001_initial.py, estudios/0001_initial.py y estudios/0002_estudio.py. Solo esquema, sin RunPython/RunSQL ni precarga. El entorno de desarrollo también tenía pendientes clientes/0002_unaccent y muestras/0001_initial + 0002_clave_borrador, ya integradas en main: se aplicaron sin modificar sus archivos. Comprobación posterior en la base de desarrollo: Prueba=0, TipoEstudio=0, Estudio=0. Los datos sintéticos se crearon únicamente en la base aislada de pytest.

Inspección de alcance: cuatro archivos existentes modificados (config/settings.py, config/urls.py, templates/base.html, templates/inicio.html), apps nuevas estudios/pruebas y documentación specs/008-crear-estudio. Sin diff en muestras, Constitution o recursos de Spec Kit. Los hashes de spec/checklist de US 5.5 coinciden con los preservados; no se modificó su worktree. .local-backups contiene respaldos previos conservados y debe excluirse de la selección de archivos del futuro commit, sin borrarlos.


## Aclaración académica vigente — decisión del usuario

AquaLab es un proyecto académico FIUBA. Los datos de desarrollo y demostración son ficticios y deben identificarse como DEMO, sin atribuirles validez científica. No hay laboratorio real ni catálogo científico oficial externo pendiente; las referencias anteriores a esa dependencia quedan sustituidas por esta decisión. Se mantienen las reglas funcionales, separación Prueba/TipoEstudio, snapshots y contrato con US 5.5. La carga demo será explícita, reproducible e idempotente, separada de migraciones y arranque; el mecanismo y manifiesto están propuestos en [propuesta-datos-demo.md](propuesta-datos-demo.md), pendientes de revisión antes de implementar o modificar datos. No se cargaron datos ni se completó T037 con esta actualización documental.


## Cargador demo disponible — ejecución explícita

Aprobación: el usuario aprobó el manifiesto v1 y el comando en este chat. Implementación aislada en estudios/management/commands/cargar_demo_us51.py; tests en estudios/tests/test_demo_us51.py. No se agregan modelos, migraciones, dependencias ni hooks. No se ejecutó --aplicar en desarrollo; las ejecuciones de aplicación de los tests ocurrieron exclusivamente en la base de pytest.

Requisitos: Docker/PostgreSQL existentes, migraciones aplicadas, usuario activo ya creado y DEBUG=True. Identificar el entorno explícitamente con AQUALAB_ENTORNO=desarrollo (o qa); cualquier otro valor o DEBUG=False rechaza tanto simulación como escritura. Esta identificación es una configuración declarada por quien ejecuta el comando: no detecta por sí misma que alguien haya etiquetado incorrectamente una base de producción. No modificar esas guardas para sortear un rechazo.

Simulación por defecto:

    docker compose exec -T -e AQUALAB_ENTORNO=desarrollo web python manage.py cargar_demo_us51 --usuario CORREO_EXISTENTE

Simulación explícita equivalente:

    docker compose exec -T -e AQUALAB_ENTORNO=desarrollo web python manage.py cargar_demo_us51 --usuario CORREO_EXISTENTE --dry-run

Carga, SOLO después de revisar y autorizar su ejecución sobre esa base:

    docker compose exec -T -e AQUALAB_ENTORNO=desarrollo web python manage.py cargar_demo_us51 --usuario CORREO_EXISTENTE --aplicar

Para QA, sustituir únicamente el valor declarado por AQUALAB_ENTORNO=qa y usar su configuración autorizada; también se exige DEBUG=True. No se crea ni se imprime contraseña. Revisar el nombre de base/motor y las líneas ALTA/REUTILIZAR/COMPOSICIÓN. La simulación no predice ni reserva PI; la carga imprime los PI realmente asignados. Repetir con el mismo usuario debe reutilizar las identidades sin INSERT/UPDATE/DELETE.

El manifiesto aprobado contiene dos clientes y sus orígenes/muestras (B queda inactivo), tres Prueba genéricas, cuatro TipoEstudio (uno inactivo) y siete asociaciones. Reconocer [DEMO FIUBA US51] y DEMO-US51-P01/P02/P03. Las composiciones ficticias están en propuesta-datos-demo.md. No se crean estudios: confirmar desde Chrome. El test test_datos_permiten_t037 verifica el resumen y la creación sobre la muestra del cliente inactivo usando los datos demo en la base de pytest; no sustituye la validación manual de T037.

Ante divergencias se aborta toda la carga, sin restaurar ni editar datos demo existentes o ajenos. Tampoco hay limpieza automática. Una falla de escritura puede dejar huecos en secuencias de PostgreSQL, que no son transaccionales; no implica filas parciales ni autoriza reiniciar PI. La simulación no consume secuencias. No cambiar de usuario para reasignar trazabilidad: se rechaza la divergencia. Una configuración demo modificada para probar conflictos no se restaura reejecutando el cargador.

Casos automatizados: simulación implícita/explícita sin DML ni nextval/setval; manifiesto inicial; repetición sin cambios; colisiones y rollback; divergencias de versión/composición; producción/no declarado/DEBUG=False; usuario inexistente o inactivo; QA explícito; falla después de registrar muestra; preservación de datos ajenos y PI; flujo de T037 con cliente inactivo; cargas concurrentes con conexiones PostgreSQL independientes. Suite del cargador: 18 passed. Ruff check, Ruff format --check (122 archivos), Django check y makemigrations --check --dry-run pasan.


Resultado final de la infraestructura demo: docker compose exec -T web pytest → 361 passed in 161.17s (suite completa, incluidos los 18 tests demo). Ruff check: All checks passed; Ruff format --check: 122 files already formatted; manage.py check: 0 issues; makemigrations --check --dry-run: No changes detected. La ayuda CLI se verificó con cargar_demo_us51 --help. La consulta de solo lectura a desarrollo confirmó Prueba=0, TipoEstudio=0, Estudio=0 y muestras con prefijo DEMO=0. No se ejecutó --aplicar fuera de pytest. T037/T039/T040 permanecen abiertos (37/40 tareas originales completas). Sin commit/push/PR/merge; US 5.5 intacta.


## Validación manual informada por el usuario

Confirmación recibida en este chat el 27/10/2026 (America/Buenos_Aires). Ejecutor informado: el usuario. Entorno informado: Chrome con AquaLab local y datos DEMO FIUBA; Docker/PostgreSQL son el entorno de desarrollo documentado. No se aportaron versión de Chrome, hora exacta de ejecución, capturas, HAR ni logs. El asistente no observó la sesión del navegador ni volvió a ejecutar la carga sobre la base local.

| Caso informado | Resultado declarado por el usuario |
|---|---|
| Selección de muestra PI 200001 | Correcta. |
| Bacteriológico y precarga de 2 pruebas | Correcta. |
| Resumen y volver a editar | Datos correctos y conservados. |
| Confirmación | Éxito y estado Pendiente de análisis. |
| Reenvío de la misma solicitud | No se observó duplicación manualmente. |
| Segunda solicitud deliberada del mismo tipo | Otro estudio independiente. |
| PI 200002, cliente inactivo | Creación permitida. |
| Cancelación | Sin guardar. |
| Tipo desactivado | No disponible. |
| cargar_demo_us51 --aplicar | Usuario informa carga correcta del manifiesto, sin estudios precargados. |

Esta declaración acredita T037. No convierte un reenvío observado en Chrome en prueba de confirmaciones concurrentes. Los locks, rollback, colisiones UUID, conservación histórica, cambios de catálogo y expiración se respaldan con tests automatizados; no se inventa evidencia manual individual de esos casos adicionales.

Los recuentos anteriores 37/40 y las menciones a carga aún no ejecutada son históricos: el usuario informa la carga y validación posteriores. El cierre actual de tareas se registra en tasks.md.


## Revalidación final posterior al reporte manual

Suite general: 361 passed in 180.10s; JavaScript: 14 passed. Ruff check y format --check (122 archivos), Django check, makemigrations --check --dry-run, migrate --check y git diff --check pasaron. No se volvió a aplicar la carga ni se alteraron datos locales. T037/T039/T040 completadas: 40/40. Inventario exacto de 50 archivos en inventario-commit.md; el cierre y los límites de la evidencia están en cierre-tecnico.md.
