# Guía de validación — Feature 033

Registro histórico de planificación: al redactar la guía todavía no se habían iniciado Docker, bases ni tests nuevos. La implementación y su evidencia efectiva se registran al final; los comandos de esta primera sección son la receta general de desarrollo.

## Prerrequisitos

- Checkout de la rama 033 con implementación y tests, Docker Compose actual y `.env` local configurado por el responsable, sin copiar secretos a documentación.
- PostgreSQL 16 del proyecto, con credenciales de desarrollo que permitan a pytest crear y borrar su base de test separada. No apuntar pruebas a producción.
- Reutilizar imagen y dependencias existentes; no instalar otro entorno ni mover el proyecto de E:. Si es necesario construir la imagen por primera vez, avisar que Docker y su caché pueden consumir varios GB y verificar que su almacenamiento esté configurado en E:; no cambiar configuración de Windows/Docker sin autorización.
- Mantener la base de desarrollo y usar fixtures de pytest para datos de pruebas. Esta feature no requiere migraciones nuevas ni comandos de carga demo.

## Ejecución automatizada

Desde la raíz del repositorio, con servicios ya disponibles:

```powershell
docker compose ps
docker compose exec web pytest config/tests/test_inicio.py config/tests/test_inicio_roles.py config/tests/test_componentes.py estudios/tests/test_pendientes.py estudios/tests/test_pendientes_busqueda.py
docker compose exec web pytest config/tests estudios/tests informes/tests usuarios/tests clientes/tests
docker compose exec web pytest
docker compose exec web ruff check .
docker compose exec web ruff format --check .
docker compose exec web python manage.py makemigrations --check --dry-run
```

Si los servicios aún no están iniciados, usar el flujo de desarrollo documentado en README (`docker compose up -d`) con la imagen existente; no reconstruir ni descargar dependencias innecesariamente. El último comando verifica ausencia de migraciones sin generarlas. Resultado esperado: suite nueva y regresiones pasan, formato correcto y ningún cambio de esquema pendiente.

Si se incorporan clases nuevas de Tailwind, regenerar el estático con el CLI existente y versión fijada por Docker/CI:

```powershell
docker compose exec web tailwindcss -i static/src/aqualab.css -o static/css/aqualab.css --minify
git diff -- static/css/aqualab.css
```

En Linux seguir además la convención de UID/GID del README para evitar cambiar la propiedad del archivo. No descargar otro compilador. Como regresión completa de CI, si Node ya está disponible:

```powershell
node --test usuarios/tests/js config/tests/js estudios/tests/js
```

Los tests de queries, roles y correspondencia deben cumplir [test-matrix.md](test-matrix.md); no basta que las páginas respondan 200. Los tests obtienen los datos mediante fixtures, sin requerir que una base manual contenga un catálogo específico.

## Verificación manual sobre datos controlados de desarrollo

1. Preparar cuentas separadas de Técnico y Bioquímico y las variantes administrativas, usando los mecanismos actuales. No modificar permisos de cuentas reales para probar. Usar los conjuntos de [data-model.md](data-model.md) y la matriz de autorización.
2. Abrir Inicio con cada perfil: un indicador o tres según rol, bienvenida y últimas muestras conservadas; sin bloque de contadores anteriores. Verificar los cuatro grupos de accesos y gestionar tipos solo con su permiso vigente.
3. Seguir carga pendiente: incluir sin iniciar y parcial, excluir solo calculadas; comparar todos los estudios de todas las páginas con el contador, sin mutaciones ni filtros extra.
4. Para validación usar el caso 5+1+0: Inicio indica 6 resultados; la lista identifica las seis pruebas/resultados en dos estudios. Aplicar texto/estado/fechas y comprobar que el total filtrado cambia, sin confundirse con el global. Recorrer varias páginas preservando el modo.
5. Seguir emisión a `listos=1`: contrastar sin pruebas, incompleto, completo e informado. La cuenta sin firma conserva los listos y el flujo existente exige firma/matrícula para emitir; no emitir documentos reales para esta revisión.
6. Verificar vacíos y filtros inválidos conforme a [contracts/rutas-filtros.md](contracts/rutas-filtros.md), con mensajes en español y controles de limpieza.
7. Revisar dashboard con y sin permiso efectivo y superusuario fuera de Bioquímicos. Verificar también la denegación del acceso directo sin permiso. Ninguna tarjeta habilita validación o emisión restringida.
8. Navegar con teclado, comprobar foco y nombres de enlaces; revisar escritorio con los componentes comunes. Cronometrar que técnico y bioquímico identifican su pendiente y abren la lista en hasta 30 segundos, sin asistencia ni búsqueda manual.
9. Resolver un pendiente mediante el flujo existente en datos de prueba y volver a consultar Inicio/listado: reflejan el estado nuevo. No exigir que dos requests separados con actividad concurrente tengan el mismo número.

## Registro de resultados y cierre

Registrar comandos, salidas, 27 escenarios cubiertos, comprobaciones de consultas, revisión de teclado y SC-005. Revisar que el diff de implementación sea acotado y que no aparezcan migraciones, dependencias, cambios de autorización o escrituras nuevas. Completar la trazabilidad de US antes del PR, sin inventarla. Esta guía no autoriza commit, push, PR ni merge. Registro histórico: al generar esta guía se detuvo el workflow antes de tareas; tareas y análisis fueron posteriormente completados y la implementación fue autorizada el 2026-11-10.

## Ejecución de implementación — 2026-11-10

- Base: d42bd3a4868ea5a88e4346ce9ecae6e3a8384fe2, rama 033-inicio-personalizado-rol. Solo existían los nueve documentos de 033 sin seguimiento; preservados. Otros dos worktrees intactos. I1 corregido identificando los registros históricos sin cambios funcionales.
- Checklist requirements.md: 16/16; se mantiene sin modificar. Sin extensions.yml ni hooks de implementación.
- Ignorados verificados: .gitignore y .dockerignore cubren entornos, cachés, secretos y respaldos. Sin dependencias nuevas previstas.
- Entorno: Docker existente en E:, inicialmente daemon detenido. Inicio de Docker Desktop existente autorizado para pruebas; no se modificó configuración de Windows ni de almacenamiento.
- Fixtures: se reutilizan empleado, muestra y servicios reales de cargar/validar. Las cuentas profesionales de prueba serán identidades separadas; se crearán datos sintéticos exclusivamente en bases de test/revisión aisladas.
- Entorno aislado: proyecto Compose aqualab-us33-review, PostgreSQL 16 en tmpfs (sin volúmenes compartidos), DATABASE_URL sintética aqualab_us33_review. Imagen existente carecía de WeasyPrint; se construyó aqualab-us33-review-web:local con Dockerfile/requirements vigentes, sin cambiarlos.
- T004–T010 rojo: pytest de consultas y componentes: 8 failed, 7 passed (módulo aún inexistente y enlace opcional ausente). T006 de preparación para emitir pasó sin modificar el servicio existente.
- T012 verde: pytest estudios/tests/test_pendientes.py estudios/tests/test_cargar_mediciones.py config/tests/test_componentes.py informes/tests/test_dashboard.py -q --tb=short: 60 passed in 42.64s, PostgreSQL temporal. Consultas/delegación y componente implementados; T001–T012 verificadas.
- T019 rojo de Inicio: 14 failed, 9 passed in 11.76s (contadores/rótulos antiguos y ausencia de consultas nuevas en la vista).
- T022 verde: pytest config/tests/test_inicio_roles.py config/tests/test_inicio.py config/tests/test_componentes.py -q --tb=short: 30 passed in 11.81s. T013–T022 verificadas para el alcance de la fase; agrupación/dashboard y correspondencia completa se validan en fases siguientes.
- T029 rojo de filtros/navegación: 12 failed, 41 passed in 23.14s. Fallos esperados por selector ausente, estudios no filtrados y resultados individuales no identificables; listos=1 y compatibilidad anterior ya aprobaban.
- T034 verde: consultas, filtros, navegación, Inicio, control/búsqueda de informes e historial de clientes: 126 passed in 57.15s. T030–T034 verificadas; incluyen paginación de resultados y listos, historial sin duplicados y consultas constantes por página.
- T036 rojo de accesos: 3 failed, 2 passed, 17 deselected in 5.46s. T038 verde de Inicio y permisos/menú de tipos: 46 passed in 16.63s. T035–T038 verificadas.
- T040 rojo de tarjeta: 6 failed, 2 passed, 22 deselected in 6.08s. T042 verde: Inicio/roles y dashboard existente: 54 passed in 43.69s. T039–T042 verificadas sin cambios de autorización.
- Presentación: los pendientes se ubican inmediatamente después de la bienvenida para evitar que la agrupación de accesos los relegue al final. Se conservan componentes y demás funciones.
- T043 suite focal integrada: 104 passed in 35.28s. Los 27 escenarios cuentan con tests concretos; se inicia la suite completa de regresión PostgreSQL.

### Hallazgos y controles finales

- Primera suite completa: `pytest -q --tb=short`: **1 failed, 1903 passed in 888.98s**. El único fallo estaba en el nuevo test de paginación: buscar por un ID numérico podía coincidir también con el DNI de su cliente, conforme a la búsqueda existente. Se sustituyó por el nombre sintético único del tipo y se reforzó la aserción con las identidades exactas de los dos resultados esperados. No se modificó la búsqueda ni se relajaron reglas de dominio. Verificación puntual posterior (paginación, conservación por ambos roles y componente): **4 passed in 4.74s**.
- Revisión visual: el tooltip del último filtro excedía el borde derecho en escritorio; en angosto debía alinearse al izquierdo. Se conservó el tooltip accesible exigido por Constitution usando clases responsivas en ese campo, sin modificar componentes compartidos. Se alineó al derecho la ayuda de texto de esta búsqueda y se posicionó relativamente el encabezado que contiene su texto sr-only para contenerlo dentro de la tabla desplazable. Prueba de render observada en rojo y verde; última verificación puntual: **1 passed in 1.42s**.
- Durante la revisión se interrumpió una repetición al reiniciar el servidor; las siguientes se aislaron del servidor y se descartaron las iniciadas antes de estabilizar el template y su prueba. Ninguna ejecución interrumpida se cuenta como aprobada. La ejecución final corre en contenedor temporal separado. Durante ella se completó un último ajuste exclusivo de presentación en el ancho intermedio, conservando consultas/comportamiento: ayudas responsivas compartidas por Desde y Trabajo pendiente; se observó su test en rojo y se volvió a ejecutar el módulo completo de componentes con la aserción reforzada: **8 passed in 1.41s**. No se ejecutaron dos suites de base simultáneamente; este módulo de render no usa base.
- Ruff: `ruff check .` → **All checks passed!**; `ruff format --check .` → **257 files already formatted**. Solo se formatearon archivos de esta feature.
- Django: `python manage.py check` → **System check identified no issues (0 silenced)**; `python manage.py makemigrations --check --dry-run` → **No changes detected**. Settings y modelos permanecen intactos.
- Tailwind: CLI existente **v4.3.3**, dos compilaciones sucesivas desde static/src/aqualab.css producen SHA256 **D7D69C45C16AF473C65A7C3A36D8038A3A495B19ED32F16C98CAA84BB81AF650**. El diff legítimo del CSS compilado se conserva; no se agregan estilos fuente, compilador ni dependencias. La detección source(none) del proyecto excluye specs y respaldos.
- JavaScript: Node existente **v24.13.0**. La invocación del CI por directorios no resolvió módulos en esta versión/Windows. El mismo conjunto se ejecutó enumerando sus archivos: **42 tests, 42 pass, 0 fail**, 344.2483 ms. Sin instalación de Node ni dependencias. La equivalencia de casos se verifica localmente; no se afirma ejecución remota ni identidad de entorno con Node 20/Linux del CI.
- WeasyPrint existente en requirements/Dockerfile: **70.0**; smoke del CI generó un PDF en memoria de **2379 bytes**. Sin modificar dependencias.

### Revisión visual y teclado

Base descartable **aqualab_us33_review**, separada de **test_aqualab_us33_review** y de cualquier base real. Se ejecutaron exclusivamente migraciones existentes para preparar su esquema y un seed sintético local, sin generar archivos de migración. Email usa locmem. PostgreSQL usa tmpfs y se pierde al recrear su contenedor.

| Verificación observada en navegador | Resultado |
|---|---|
| Técnico sin permisos profesionales | 2 estudios de carga; sin tarjeta Dashboard ni contadores anteriores. |
| Bioquímico habitual | 2 estudios de carga, 6 resultados, 1 estudio listo; tarjeta Dashboard presente. |
| Carga | Enlace pendiente=mediciones muestra estudios #5 sin iniciar y #2 parcial. |
| Validaciones | Enlace pendiente=validaciones muestra 6 resultados, agrupados en 2 estudios; código, nombre, valor y unidad de cada prueba. |
| Emisión | Enlace listos=1 muestra únicamente estudio #3; excluye el ya informado. |
| Dashboard | Tarjeta abre el dashboard existente, sin alterar autorización. Denegación y combinaciones de permisos verificadas por tests HTTP. |
| Filtros y vacío | Estado Finalizado con validaciones conserva selección y muestra ausencia de coincidencias y limpieza. |
| Navegación | Clientes → Muestras → Estudios → Informes; menú activo, bienvenida y últimas muestras conservados. |
| Teclado | Tab llega al siguiente indicador con focus-visible; Return abre la lista correcta. Return también abre carga desde Técnico. |
| Ancho final | 490, 768 y 1366 px: documento sin desbordamiento; la tabla conserva su desplazamiento interno. Tooltip nuevo completo dentro del ancho visible en una, dos y cuatro columnas. Overrides de viewport restablecidos. |

SC-005: recorrido de revisión por el agente, desde observar Inicio y elegir el pendiente hasta abrir el destino: **Técnico 4.068 s; Bioquímico 5.502 s**. Ambos perfiles sintéticos permiten abrir el trabajo en una acción y menos de 30 s. Estos tiempos incluyen la interacción del revisor; **no son un estudio de usabilidad con empleados reales** ni tiempos de pytest. Validar la orientación con empleados sigue siendo recomendable.

Evidencias locales ignoradas: `.local-backups/us33-review/inicio-tecnico.jpg`, `inicio-bioquimico.jpg`, `resultados-pendientes.jpg` y `filtro-final.jpg`. El último corresponde al template final. No se agregan capturas ni datos sintéticos al código versionado.

### Reproducir esta revisión local

El entorno de esta sesión permanece separado en `.local-backups/us33-review/compose.yml` (ignorado). Los comandos ejecutados utilizan siempre ese proyecto, no el Compose habitual conectado a datos de desarrollo:

```powershell
docker compose -p aqualab-us33-review -f .local-backups/us33-review/compose.yml ps
docker compose -p aqualab-us33-review -f .local-backups/us33-review/compose.yml run --rm --no-deps web pytest -q --tb=short
docker compose -p aqualab-us33-review -f .local-backups/us33-review/compose.yml exec -T web ruff check .
docker compose -p aqualab-us33-review -f .local-backups/us33-review/compose.yml exec -T web ruff format --check .
docker compose -p aqualab-us33-review -f .local-backups/us33-review/compose.yml exec -T web python manage.py check
docker compose -p aqualab-us33-review -f .local-backups/us33-review/compose.yml exec -T web python manage.py makemigrations --check --dry-run
docker compose -p aqualab-us33-review -f .local-backups/us33-review/compose.yml exec -T web tailwindcss -i static/src/aqualab.css -o static/css/aqualab.css --minify
$tests033 = @(rg --files usuarios/tests/js config/tests/js estudios/tests/js -g '*.test.js')
node --test @tests033
git diff --check
```

Abrir `http://127.0.0.1:8033/`. Las cuentas y credenciales **exclusivamente sintéticas y locales** están en el seed ignorado `.local-backups/us33-review/seed.py`: Técnico tecnico033@example.com y Bioquímico validador033@example.com. No reutilizar estas cuentas fuera de la base descartable. El seed tiene guard de nombre de base exacto y exige base vacía; no volver a ejecutarlo sobre la revisión ya cargada. Para otro checkout seguir los prerrequisitos generales y las fixtures de pytest, que no necesitan este seed.

### Auditoría de alcance y límites

- Rama y HEAD preservados; no commit, push, PR, merge ni staging. Los nueve documentos previos de 033 se preservaron; solo spec (I1/estado), quickstart, matriz y tareas se actualizan para evidencias/seguimiento.
- Producto: nuevo módulo de consultas puras y parcial; vistas, formulario específico, Inicio y componente de indicador modificados conforme a plan. Fixtures ampliadas localmente, sin reordenar la infraestructura general.
- Sin cambios en Constitution, checklist, otras historias, modelos, rutas, middleware, permisos, servicios de escritura, lógica de emisión ni dependencias. `estudios_para_informar` sigue siendo la única regla de preparación para emitir.
- Existe trazabilidad concreta de **27/27** escenarios con las funciones de la matriz, más parametrizaciones y regresiones. Se comprobó por lectura que todas las funciones nombradas existen. SQL usa Exists y prefetch de página; tests comparan cantidades de consultas con pocas/muchas filas para detectar N+1.
- Las igualdades de contadores/listados requieren los mismos datos estables. Actividad concurrente entre requests puede cambiar los totales; no se promete snapshot ni se introducen bloqueos/caché. Un estudio con muchas pruebas sigue mostrando todas sus pruebas pendientes, según alcance aprobado.
- **Clave Jira y número de US pendientes de información externa**, como excepción de trazabilidad ya justificada en plan. No inventados; completar antes del PR. La aprobación del equipo y CI remoto también corresponden al futuro PR.

### Inventario de archivos de la entrega

| Estado local | Archivos | Propósito |
|---|---|---|
| Nuevos (2 de producto) | estudios/pendientes.py; estudios/templates/estudios/_resultados_pendientes.html | Selecciones canónicas de lectura e identificación de resultados. |
| Nuevos (3 de tests) | config/tests/test_inicio_roles.py; estudios/tests/test_pendientes.py; estudios/tests/test_pendientes_busqueda.py | Roles, permisos, conjuntos, navegación, historial y rendimiento. |
| Modificados (7 de producto) | config/views.py; estudios/forms.py; estudios/views.py; estudios/templates/estudios/buscar.html; templates/inicio.html; templates/ui/indicador.html; static/css/aqualab.css | Inicio, filtros, presentación y CSS compilado. |
| Modificados (4 de tests) | config/tests/test_componentes.py; config/tests/test_inicio.py; estudios/tests/conftest.py; estudios/tests/test_filtros.py | Compatibilidad, fixtures locales, cobertura de sustitución y filtros. |
| Documentos previos actualizados | specs/033-inicio-personalizado-rol/spec.md; quickstart.md; test-matrix.md; tasks.md (estos últimos en la misma carpeta) | I1/estado, evidencia, trazabilidad y seguimiento. |
| Documentos previos preservados | specs/033-inicio-personalizado-rol/checklists/requirements.md; contracts/rutas-filtros.md; data-model.md; plan.md; research.md | Sin cambios durante implementación; permanecen sin seguimiento como al inicio de esta sesión. |

Los nueve documentos ya existían sin seguimiento al empezar y siguen así porque no se autorizó commit/staging. El inventario distingue archivos nuevos de implementación de documentos preexistentes; Git muestra ambos grupos como untracked.

### Cierre verificado

- **T044:** suite completa final `docker compose -p aqualab-us33-review -f .local-backups/us33-review/compose.yml run --rm --no-deps web pytest -q --tb=short` → **1906 passed in 932.87s (0:15:32)**, exit code 0. Incluye config, estudios, informes, usuarios, clientes y demás módulos; ninguna regresión pendiente.
- **T045–T048:** Ruff check/format, Django check, migraciones dry-run, CSS idempotente, WeasyPrint y 42 tests JS aprobados con los comandos/versiones registrados. No se afirma CI remoto ejecutado; en un futuro commit debe incluirse el CSS regenerado para el control de archivo actualizado del CI.
- **T049:** revisión visual, teclado, vacíos, permisos por perfil y SC-005 documentados con sus límites. El ajuste de dos columnas se confirmó también a 768 px, además de 490/1366.
- **T050:** matriz concreta 27/27, comandos, resultados y contrato contrastados sin cambios funcionales aprobados.
- **T051:** diff de los 16 archivos de producto/tests/CSS y nueve documentos preexistentes revisado contra plan; sin cambios ajenos ni staging. `git diff --check` sin errores (solo aviso de normalización LF/CRLF del CSS en Windows, sin cambio de contenido por recompilar). Constitution y checklist mantienen sus hashes originales.
- **T052:** 52 tareas verificadas; cuatro criterios Jira cubiertos; ningún pendiente de implementación. Checklist permanece 16/16 sin editar. Comprobación posterior del workflow: `.specify/extensions.yml` ausente, por lo que no hay hooks after_implement registrados.
- **Preparación:** feature lista para revisión local y preparación de commit con código/spec juntos cuando el responsable lo autorice. No se creó commit, push, PR ni merge. Antes del PR vincular Jira/US reales, ejecutar CI remoto y obtener aprobación del equipo conforme a Constitution.
