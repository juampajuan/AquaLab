# Tasks: Inicio personalizado por rol

**Input**: documentos aprobados de specs/033-inicio-personalizado-rol/: spec.md, plan.md, research.md, data-model.md, contracts/rutas-filtros.md, test-matrix.md y quickstart.md.
**Rama**: 033-inicio-personalizado-rol. **Fecha**: 2026-11-09.
**Prerequisites**: Constitution 1.2.0; spec de 27 escenarios, checklist 16/16 y plan aprobados expresamente por el responsable.
**Tests**: obligatorios por pedido del responsable y principio III. Escribir primero y observar el fallo esperado antes de cambiar producto; las caracterizaciones de comportamientos existentes pueden pasar desde el comienzo.
**Organization**: fases por User Story con las prioridades de spec.md. Todos los archivos de las tareas son relativos a la raíz del repositorio.

## Formato y reglas de ejecución

Cada línea de tarea usa checkbox vacío, ID consecutivo, [P] solo cuando está justificado, [USn] solo en fases de historia y archivos concretos. Las denominaciones “Prueba automatizada”, “Calidad” y “Documentación” dentro de la descripción permiten distinguir creación/ejecución de pruebas de las tareas funcionales.

No se ha ejecutado ninguna tarea de esta lista al generarla. No hacer commit, push, PR, merge, cambios de Constitution, historias ajenas, permisos, modelos o migraciones; tampoco instalar dependencias o inventar la US. La brecha de trazabilidad por número de US sigue documentada en plan.md y debe completarse cuando el equipo lo proporcione, antes del PR.

[P] permite exclusivamente trabajo en archivos distintos con prerrequisitos comunes ya satisfechos. No implica ejecutar pytest en paralelo sobre la misma base. Todos los comandos de tests, fixtures con escritura y operaciones sobre PostgreSQL se ejecutan en serie; sin xdist ni bases nuevas por trabajador. No editar simultáneamente config/tests/test_inicio_roles.py, estudios/tests/test_pendientes.py, estudios/views.py o templates/inicio.html desde varias tareas.

## Phase 1: Setup y compatibilidad

**Purpose**: confirmar entorno, base y contratos aprobados sin crear infraestructura nueva.

- [x] T001 Verificar rama 033, git status, HEAD y cambios existentes; contrastar spec/checklist/plan aprobados y registrar la base y cualquier cambio ajeno en specs/033-inicio-personalizado-rol/quickstart.md sin sobrescribirlos; conservar la brecha de US de specs/033-inicio-personalizado-rol/plan.md sin inventar identificadores.
- [x] T002 Verificar compatibilidad del entorno existente definido en docker-compose.yml, Dockerfile, requirements.txt, pyproject.toml y .github/workflows/ci.yml: PostgreSQL 16, pytest-django, Ruff y Tailwind fijados; documentar disponibilidad y comandos en specs/033-inicio-personalizado-rol/quickstart.md sin leer secretos en la salida, instalar paquetes ni reconstruir imágenes innecesariamente; si una construcción imprescindible consume varios GB, informar primero y respetar almacenamiento en E:.
- [x] T003 Identificar las fixtures reutilizables en estudios/tests/conftest.py, estudios/tests/utiles.py y config/tests/test_inicio.py y fijar en specs/033-inicio-personalizado-rol/test-matrix.md cuentas separadas, resultados 5+1+0, más de 20 estudios y validaciones anuladas; evitar que empleado y bioquimico sean la misma identidad al comparar perfiles y reconstruir grupos/permisos en fixtures cuando corresponda.

**Checkpoint**: entorno y fixtures definidos; aprobación y 16/16 confirmadas; ninguna dependencia, base o autorización nueva. T001 → T002 → T003.

## Phase 2: Fundamentos compartidos

**Purpose**: consultas canónicas reutilizables y compatibilidad del indicador. No iniciar producto de las User Stories hasta cerrar T012.

### Pruebas primero

- [x] T004 [P] Prueba automatizada: crear en estudios/tests/test_pendientes.py test_carga_distinta_y_no_calculadas y casos de paridad con Estudio.admite_mediciones y asignaciones_para_medir para US1.4; incluir carga parcial, varias pruebas por estudio, solo calculadas, fórmula con medición propia y estados no admitidos; escribir los esperados por IDs conocidos y comprobar fallo por API de consulta aún inexistente antes de T007.
- [x] T005 Prueba automatizada: agregar en estudios/tests/test_pendientes.py test_resultados_existentes_y_recalculados para US1.5 y variantes de Resultado existente/ausente, Cargada/Completada, vigente/anulada, estudio informado, valor cero y calculada sin medición propia; crear múltiples validaciones anuladas históricas y verificar identidades únicas y count sin multiplicación, incluida anomalía Cargada con vigente excluida sin reparar datos; observar fallo antes de T008. Depende de T004 por archivo.
- [x] T006 Prueba automatizada: agregar en estudios/tests/test_pendientes.py test_listos_paridad_regla_existente para US1.6, contrastando estudios_para_informar con motivo_para_no_informar en sin pruebas, incompleto, todas Completadas, fuera de norma validado e Informe generado; proteger las condiciones “total_pruebas > 0” y “pruebas_completadas = total_pruebas”, sin exigir firma ni solo Finalizado. Caracterización del servicio existente, puede pasar sin cambios; depende de T005.

### Consultas y compatibilidad

- [x] T007 Crear en estudios/pendientes.py asignaciones_con_mediciones_pendientes y estudios_con_mediciones_pendientes(qs), compartiendo los predicados “estado=PENDIENTE” y “prueba.es_calculada=False” y estados de admite_mediciones con Exists/OuterRef; devolver queryset lazy de Estudio.pk únicos, sin filtros por creador, fecha, Prueba.activa o ausencia de Resultado; sin alterar modelos. Depende de T004 y su fallo observado.
- [x] T008 Agregar en estudios/pendientes.py resultados_por_validar y estudios_con_resultados_pendientes(qs): raíz Resultado, asignación Cargada, estudio sin Informe generado y NOT EXISTS de Validacion con “anulada=False”; respetar “Una identidad de resultado aporta una unidad al conteo.” y “a lo sumo una no anulada por asignación.”, sin joins que multipliquen historial ni estados nuevos. Depende de T005 y T007; pruebas T005.
- [x] T009 Delegar estudios/views.py:asignaciones_para_medir en el queryset compartido de estudios/pendientes.py conservando filtro por estudio, select_related, orden código/pk y guard actual de carga; mantener intactos servicios de escritura y validar paridad con estudios/tests/test_cargar_mediciones.py y T004. Depende de T007.
- [x] T010 [P] Prueba automatizada: ampliar config/tests/test_componentes.py para indicador con URL opcional y sin URL, enlace nativo con nombre/cantidad, data-indicador/data-valor, ausencia de enlaces anidados y compatibilidad del consumidor de dashboard; observar el fallo nuevo antes de T011. Puede redactarse junto con T004 sin ejecutar ambos pytest simultáneamente.
- [x] T011 Extender templates/ui/indicador.html con URL opcional y foco accesible, conservando render actual cuando no se provee, estilos y atributos existentes; no crear otra tarjeta ni agregar JavaScript. Depende de T010; pruebas de compatibilidad T010.
- [x] T012 Prueba automatizada: ejecutar en serie sobre PostgreSQL los tests de estudios/tests/test_pendientes.py, estudios/tests/test_cargar_mediciones.py, config/tests/test_componentes.py e informes/tests/test_dashboard.py; registrar resultados en specs/033-inicio-personalizado-rol/quickstart.md y corregir exclusivamente los cambios de T007–T011 hasta pasar. Depende de T006, T008, T009 y T011.

**Checkpoint**: predicados compartidos y componente compatibles; listos siguen usando el servicio existente, sin una tercera regla en pendientes.py. Las consultas no cambian relaciones, Decimal, unidades, snapshots ni historial.

## Phase 3: User Story 1 — Reconocer el trabajo pendiente según el rol (Priority: P1)

**Goal**: conteos y presentación por rol con permisos de operación intactos; reemplazo de indicadores generales.

**Independent Test**: contrastar IDs y conteos de un técnico y un bioquímico con datos conocidos y variantes administrativas. Esta fase valida conteos y URLs generadas; la comprobación completa de los destinos nuevos se cierra en US2. La preservación integral de US1.14 se confirma también al terminar US3 y US4.

### Tests for User Story 1

- [x] T013 [P] [US1] Prueba automatizada: crear en config/tests/test_inicio_roles.py test_carga_sin_iniciar_y_parcial, test_tecnico_solo_mediciones, test_bioquimico_tres_unidades, test_ceros_con_enlaces y test_validacion_cinco_mas_uno para US1.1, US1.2, US1.3, US1.7 y US1.13; comprobar estudios 2 y resultados 5+1+0=6, unidades, URLs sin filtros previos y ausencia de duplicaciones; usar resultados de T004–T006 sin deducir esperados del helper probado.
- [x] T014 [US1] Prueba automatizada: agregar en config/tests/test_inicio_roles.py test_administrador_comun, test_administrador_bioquimico y test_permisos_no_sustituyen_grupo para US1.9–US1.11; parametrizar permisos individuales, otro grupo y superusuario con/sin Bioquímicos, sin usar is_staff ni Administradores como rol profesional. Depende de T013 por archivo.
- [x] T015 [US1] Prueba automatizada: agregar en config/tests/test_inicio_roles.py test_bioquimico_sin_permiso_operativo para US1.12 y variantes sin sesión, login inactivo rechazado y sesión seguida de desactivación; verificar consultas existentes permitidas, operaciones de validar/emitir denegadas con HTTP 403 para activo sin permiso, sin mutaciones, cambios de grupo en siguiente request, huella y never-cache; no crear un guard profesional de lectura. Depende de T014.
- [x] T016 [US1] Prueba automatizada: agregar en config/tests/test_inicio_roles.py test_firma_no_cambia_listos para US1.8; validar contador inalterado sin firma y restricción de emisión vigente mediante patrones de informes/tests/test_permisos.py, sin relajar firma/matrícula ni emitir documentos reales. Depende de T015.
- [x] T017 [P] [US1] Prueba automatizada: actualizar config/tests/test_inicio.py retirando solo expectativas de tres contadores generales y agregando test_reemplazo_conserva_otras_funciones para US1.14; conservar bienvenida, últimas cinco muestras y sus datos/orden, vacío, sesión y accesos no modificados; dejar la comprobación integrada de agrupación/dashboard para T035/T039 y gate final. Puede redactarse con T013, en archivo distinto.
- [x] T018 [US1] Prueba automatizada: ampliar config/tests/test_inicio_roles.py con comparación CaptureQueriesContext a distinto volumen para cada perfil, verificando que Técnico no evalúa conteos profesionales y que últimas muestras no introduce N+1; no imponer un mismo total entre perfiles ni un número frágil de consultas de middleware. Depende de T016.
- [x] T019 [US1] Prueba automatizada: ejecutar tests de config/tests/test_inicio_roles.py y config/tests/test_inicio.py correspondientes a esta fase antes de T020/T021 y registrar fallos esperados por rol/conteos/reemplazo en specs/033-inicio-personalizado-rol/quickstart.md; diferenciar defectos de configuración de fallos de comportamiento, sin silenciar asserts ni marcar xfail. Depende de T017 y T018.

### Implementation for User Story 1

- [x] T020 [US1] Actualizar config/views.py:inicio para comprobar pertenencia a Bioquímicos una vez por request, contar carga con estudios/pendientes.py y solo para Bioquímico resultados canónicos y informes/servicios.py:estudios_para_informar("", True); generar URLs con reverse y parámetros codificados, conservar consulta de últimas muestras y autenticación; no crear permisos ni duplicar reglas de emisión. Depende de T019; pruebas T013–T018 y T004–T006.
- [x] T021 [US1] Reemplazar en templates/inicio.html el bloque general por indicadores mediciones-pendientes, resultados-por-validar y estudios-listos según rol, con URL opcional del parcial y ceros navegables; eliminar el segundo bloque general, conservar bienvenida/últimas muestras y no incorporar acciones de carga/validación/emisión. Depende de T020 y T011; pruebas T013–T018.
- [x] T022 [US1] Prueba automatizada: ejecutar sobre PostgreSQL config/tests/test_inicio.py, casos US1 de config/tests/test_inicio_roles.py y config/tests/test_componentes.py, comprobar los 14 escenarios en la parte habilitada por esta fase y registrar resultado en specs/033-inicio-personalizado-rol/quickstart.md; seguir los enlaces de destino y la integración completa de US1.14 quedan exigidos por US2–US4 y T043. Depende de T021; no declarar terminada la feature.

**Checkpoint**: una cuenta común ve solo carga; Bioquímicos ve tres contadores con las unidades correctas; Administración y permisos no conceden un rol profesional nuevo. Sin writes, cambios de backend ni pérdida de últimas muestras.

## Phase 4: User Story 2 — Abrir la lista del pendiente (Priority: P1)

**Goal**: destinos que representan exactamente los estudios o resultados contados, combinables con búsqueda y paginación existentes.

**Independent Test**: llamar cada URL directamente con sesión y seguir también los enlaces de Inicio; comprobar conjuntos de IDs esperados en todas las páginas, con y sin filtros manuales.

### Tests for User Story 2

- [x] T023 [US2] Prueba automatizada: agregar en estudios/tests/test_filtros.py casos de pendiente vacío/mediciones/validaciones, elección inválida, “máximo 100” para q, fechas inclusivas/rango inválido, estado válido/inválido y AND con filtros actuales; verificar fallback existente de formulario inválido a listado general sin selección aplicada y que FiltrosEstudioForm, CAMPOS_FILTRO e Informes no reciben el campo nuevo. Mantener el tratamiento actual de QueryDict y page.
- [x] T024 [US2] Prueba automatizada: crear en estudios/tests/test_pendientes_busqueda.py test_enlace_carga_conjunto_exacto y test_resultados_identificables para US2.1–US2.2 y destinos vacíos de US1.7; recuperar IDs de Resultado identificables por estudio/prueba, unidades, 6 resultados en 2 estudios, solo calculada pendiente excluida de carga y ausencia de resultados no calculados/validados, sin agregar permisos de consulta.
- [x] T025 [US2] Prueba automatizada: agregar en estudios/tests/test_pendientes_busqueda.py test_paginacion_conserva_filtros y test_union_resultados_todas_paginas para US2.5–US2.6; usar más de 20 estudios, varias pruebas y validaciones históricas, verificar unión sin duplicados, totales diferenciados antes de paginar y correspondencia exacta con Inicio para datos estables; con filtros extra comparar contra total filtrado y conservar q/desde/hasta/estado/pendiente al navegar. Depende de T024.
- [x] T026 [US2] Prueba automatizada: agregar en estudios/tests/test_pendientes_busqueda.py test_cambio_entre_requests para US2.4 con servicios reales de carga, validación y emisión sobre fixtures controladas; obtener Inicio, resolver, consultar destino y recargar Inicio; no usar sleeps, locks nuevos ni exigir snapshot entre requests. Depende de T025.
- [x] T027 [US2] Prueba automatizada: agregar en estudios/tests/test_pendientes_busqueda.py verificaciones CaptureQueriesContext de pocas/muchas filas y resultados por página, sin consultas por resultado/validación histórica, sin prefetch profesional en búsqueda general y con relaciones del parcial ya resueltas; incluir muchas pruebas de un mismo estudio sin imponer un máximo de negocio. Depende de T026.
- [x] T028 [US2] Prueba automatizada: agregar en config/tests/test_inicio_roles.py test_enlace_listos_reusa_filtro para US2.3, recorriendo también varias páginas de /informes/?listos=1 y comparando Estudio.pk con el contador; mantener informes/tests/test_control.py como referencia de regla, sin cambiar rutas ni el servicio de emisión. Depende de T022 por archivo.
- [x] T029 [US2] Prueba automatizada: ejecutar en PostgreSQL los nuevos casos de estudios/tests/test_filtros.py y estudios/tests/test_pendientes_busqueda.py y el caso US2.3 de config/tests/test_inicio_roles.py antes de T030–T033; registrar los fallos esperados de contrato/listado en specs/033-inicio-personalizado-rol/quickstart.md. Depende de T023–T028.

### Implementation for User Story 2

- [x] T030 [US2] Extender solamente estudios/forms.py:FiltrarEstudiosForm con pendiente opcional “vacío (Todos), mediciones (Mediciones por cargar) o validaciones (Resultados por validar)”, help_text y errores/estilos comunes; conservar “fechas de creación del estudio, días inclusivos en zona horaria del proyecto” y “20 estudios por página”, sin tocar el formulario base compartido ni CAMPOS_FILTRO. Depende de T029; pruebas T023.
- [x] T031 [US2] Extender estudios/views.py:buscar para aplicar q/estado/fechas actuales AND consultas canónicas de pendiente; preservar fallback inválido, orden -pk y Paginator.get_page; calcular total de Resultado para todos los estudios filtrados y Prefetch solo de asignaciones de la página con prueba/resultado seleccionados y to_attr, sin multiplicar historial; mantener los flags, URLs de página y autorización actual, sin rutas ni writes nuevos. Depende de T030 y T008; pruebas T023–T027.
- [x] T032 [US2] Crear estudios/templates/estudios/_resultados_pendientes.html para resultados de to_attr con identidad Resultado.pk comprobable, estudio/prueba, código, nombre, valor_mostrado y unidad guardada usando filtros comunes incluida presencia A/P; enlazar únicamente al detalle existente, sin consultas por fila ni formulario/botón de validar nuevo. Depende de T031; pruebas T024, T025 y T027.
- [x] T033 [US2] Actualizar estudios/templates/estudios/buscar.html con selector/ayuda, resultados del parcial solo en modo validaciones válido, totales diferenciados de estudios/resultados, vacíos comprensibles y limpieza; conservar filtro al enviar/paginar mediante templates/ui/paginacion.html existente, sin mostrar un modo activo si no se aplicó por errores. Depende de T032; pruebas T023–T027.
- [x] T034 [US2] Prueba automatizada: ejecutar en serie estudios/tests/test_pendientes.py, estudios/tests/test_filtros.py, estudios/tests/test_pendientes_busqueda.py, config/tests/test_inicio_roles.py (US1/US2 escritos hasta aquí), informes/tests/test_control.py e informes/tests/test_busqueda.py y regresiones de filtros de clientes/tests; registrar resultados en specs/033-inicio-personalizado-rol/quickstart.md y comprobar 6/6 escenarios US2 y ceros navegables sin cambios de dominio. Depende de T028 y T033.

**Checkpoint**: contador/lista coinciden por identidad para los mismos datos; carga y listos cuentan estudios, validación cuenta resultados. Filtros manuales muestran su universo reducido y no un falso total global. Este es el MVP útil de pendientes completos: US1 + US2.

## Phase 5: User Story 3 — Encontrar los accesos por módulo (Priority: P2)

**Goal**: accesos existentes agrupados por el orden de trabajo, sin cambiar sus destinos o permisos.

**Independent Test**: inspeccionar pertenencia y orden de grupos del DOM; seguir accesos con actor permitido y comparar datos antes/después de GET.

### Tests for User Story 3

- [x] T035 [US3] Prueba automatizada: agregar en config/tests/test_inicio_roles.py test_orden_grupos, test_accesos_por_modulo, test_gestion_tipos_permiso y test_navegacion_no_muta para US3.1–US3.4; comprobar Clientes → Muestras → Estudios → Informes, miembros/destinos de la spec, Gestionar tipos solo con permiso vigente y menú/directo intactos; verificar que navegar no crea mediciones, resultados, validaciones ni informes, y completar esta parte de US1.14 en config/tests/test_inicio.py. Depende de T034 por archivo.
- [x] T036 [US3] Prueba automatizada: ejecutar los cuatro casos US3 de config/tests/test_inicio_roles.py antes de T037 y registrar fallo esperado por agrupación en specs/033-inicio-personalizado-rol/quickstart.md sin alterar los permisos de referencia. Depende de T035.

### Implementation for User Story 3

- [x] T037 [US3] Reagrupar templates/inicio.html usando templates/ui/acceso_rapido.html y títulos comunes: Clientes (Buscar/Registrar), Muestras (Registrar), Estudios (Crear/Buscar y Gestionar tipos si corresponde), Informes (selección de estudios); conservar URLs y atributos de componentes, bienvenida/últimas muestras y menú común, sin duplicar accesos ni agregar funciones. Depende de T036; pruebas T035.
- [x] T038 [US3] Prueba automatizada: ejecutar casos US3 y preservación de Inicio en config/tests/test_inicio_roles.py y config/tests/test_inicio.py, junto con regresiones de menú y tipos en usuarios/tests; registrar resultados en specs/033-inicio-personalizado-rol/quickstart.md. Depende de T037.

**Checkpoint**: 4/4 escenarios US3 pasan; grupos, permisos y navegación existentes conservados.

## Phase 6: User Story 4 — Entrar al dashboard autorizado (Priority: P2)

**Goal**: tarjeta Ver dashboard según autorización efectiva independiente del rol profesional.

**Independent Test**: comparar tarjeta y acceso directo para grupos, permiso individual, sin permiso y superusuario activo; incluir revocación y desactivación en request posterior.

### Tests for User Story 4

- [x] T039 [US4] Prueba automatizada: agregar en config/tests/test_inicio_roles.py test_tarjeta_dashboard_autorizado, test_sin_dashboard y test_dashboard_independiente_rol para US4.1–US4.3; parametrizar Bioquímicos, Administradores, permiso individual/otro grupo, ausencia/revocación y superusuario sin Bioquímicos; comprobar tarjeta/200, ausencia/403 para activo sin permiso y login para inactivo/sin sesión; completar US1.14 integrado en config/tests/test_inicio.py sin cambiar expectativas de informes/tests/test_dashboard.py. Depende de T038 por archivos.
- [x] T040 [US4] Prueba automatizada: ejecutar casos US4 en config/tests/test_inicio_roles.py y la autorización existente de informes/tests/test_dashboard.py antes de T041; registrar fallo esperado de tarjeta y comportamiento ya vigente del destino en specs/033-inicio-personalizado-rol/quickstart.md. Depende de T039.

### Implementation for User Story 4

- [x] T041 [US4] Agregar en templates/inicio.html tarjeta Ver dashboard con templates/ui/acceso_rapido.html y reverse de informes:dashboard, condicionada exclusivamente a permiso efectivo informes.ver_dashboard como el menú existente; ubicarla aparte de los cuatro grupos y no cambiar informes/views.py, política administrativa, backend ni grupos. Depende de T040; pruebas T039.
- [x] T042 [US4] Prueba automatizada: ejecutar casos US4 y preservación de Inicio en config/tests/test_inicio_roles.py, config/tests/test_inicio.py e informes/tests/test_dashboard.py; registrar resultados en specs/033-inicio-personalizado-rol/quickstart.md y verificar 3/3 escenarios sin escalamiento. Depende de T041.

**Checkpoint**: cuatro criterios Jira implementados y verificables, sujetos a validación integral; superusuario fuera de Bioquímicos conserva presentación técnica y acceso estándar al dashboard.

## Phase 7: Validación integral y documentación

**Purpose**: verificar la integración completa, rendimiento y calidad del cambio; no agregar alcance.

- [x] T043 Prueba automatizada: ejecutar secuencialmente en PostgreSQL la suite focal de config/tests/test_inicio.py, config/tests/test_inicio_roles.py, config/tests/test_componentes.py, estudios/tests/test_pendientes.py, estudios/tests/test_pendientes_busqueda.py y estudios/tests/test_filtros.py; registrar cobertura 27/27 incluida US1.14 completa y consultas sin N+1 en specs/033-inicio-personalizado-rol/quickstart.md. Depende de T042.
- [x] T044 Prueba automatizada: ejecutar regresiones de config/tests, estudios/tests (carga/cálculo/corrección/validación/concurrencia), informes/tests (control/búsqueda/emisión/dashboard/permisos), usuarios/tests y clientes/tests, y luego pytest completo sobre PostgreSQL mediante docker compose exec web pytest; registrar comandos/salidas en specs/033-inicio-personalizado-rol/quickstart.md y corregir solo regresiones introducidas, sin debilitar asserts de dominio. Depende de T043.
- [x] T045 Calidad: ejecutar docker compose exec web ruff check . y ruff format --check . conforme pyproject.toml, corregir únicamente archivos de esta feature y registrar resultados en specs/033-inicio-personalizado-rol/quickstart.md. Depende de T044.
- [x] T046 Calidad: ejecutar docker compose exec web python manage.py check y python manage.py makemigrations --check --dry-run; contrastar config/settings.py y estudios/models.py/informes/models.py sin modificarlos y registrar en specs/033-inicio-personalizado-rol/quickstart.md ausencia de errores/cambios de esquema; no generar migraciones para hacer pasar el check. Depende de T045.
- [x] T047 Calidad: con CLI Tailwind y versión existentes de Dockerfile/.github/workflows/ci.yml, recompilar static/css/aqualab.css desde static/src/aqualab.css si corresponde a los templates cambiados; revisar diff y segunda compilación idempotente contra la primera salida, sin exigir ausencia del diff legítimo respecto de HEAD ni descargar otro compilador; registrar verificación en specs/033-inicio-personalizado-rol/quickstart.md. Depende de T046.
- [x] T048 Prueba automatizada: ejecutar node --test usuarios/tests/js config/tests/js estudios/tests/js con Node existente y cotejar que todas las comprobaciones de .github/workflows/ci.yml hayan sido reproducidas localmente por T043–T048, incluida consistencia CSS de T047; registrar resultado o bloqueo concreto en specs/033-inicio-personalizado-rol/quickstart.md sin instalar herramientas ni declarar CI remoto ejecutado. Depende de T047.
- [x] T049 Calidad: realizar la revisión visual y de teclado de templates/inicio.html y estudios/templates/estudios/buscar.html descrita en specs/033-inicio-personalizado-rol/quickstart.md, con estados vacíos, filtros conservados, menú activo, foco, ausencia de contadores retirados, roles y dashboard; cronometrar SC-005 con Técnico/Bioquímico (hasta 30 segundos para identificar y abrir pendiente) y registrar evidencia, sin sustituirlo por tiempos artificiales de pytest. Depende de T048.
- [x] T050 Documentación: completar specs/033-inicio-personalizado-rol/test-matrix.md con nombres reales de tests y correspondencia 27/27 y specs/033-inicio-personalizado-rol/quickstart.md con comandos, resultados, límites y evidencia manual; contrastar con contracts/rutas-filtros.md sin alterar decisiones aprobadas y sin marcar calidad o tareas como cumplidas por mera existencia del código. Depende de T049.
- [x] T051 Calidad: auditar diff completo contra specs/033-inicio-personalizado-rol/plan.md y los archivos previstos; confirmar sin cambios en Constitution, otras historias, permisos, rutas, modelos, migraciones o dependencias y sin lógica de emisión duplicada; documentar la brecha de US y cualquier limitación real en specs/033-inicio-personalizado-rol/quickstart.md, sin inventar Jira ni hacer commit/publicación. Depende de T050.
- [x] T052 Documentación: registrar cierre por checkpoints y tareas realmente verificadas en specs/033-inicio-personalizado-rol/tasks.md, contrastar las 27 filas de cobertura con specs/033-inicio-personalizado-rol/test-matrix.md y los cuatro criterios Jira de spec.md; informar pruebas, fallos o bloqueos al responsable y detenerse sin commit, push, PR o merge. Depende de T051; no tocar marcadores de checklists/requirements.md desde implement.

**Checkpoint final**: pruebas y calidad con evidencia, correspondencia por identidad, permisos y dominio conservados. Una validación no ejecutada o fallida debe informarse y permanecer pendiente; nunca declarar completada por anticipado.

## Dependencies & Execution Order

### Dependencias de fases

Setup T001–T003 → fundamentos T004–T012 → US1 T013–T022 → US2 T023–T034 → US3 T035–T038 → US4 T039–T042 → validación T043–T052.

Este orden de integración respeta P1 antes de P2 y evita escrituras concurrentes en los mismos templates y tests. US2 usa las consultas compartidas y se prueba también por URL directa. US3 y US4 son funcionalmente comprobables sin los otros flujos, pero se integran secuencialmente por compartir templates/inicio.html y config/tests/test_inicio_roles.py.

### Dependencias dentro de cada fase

- Fundamentos: T004 → T005 → T006 para redactar tests del mismo archivo; T004 → T007; T005 + T007 → T008; T007 → T009; T010 → T011. T012 depende de T006/T008/T009/T011 y cierra la fase.
- US1: T013 → T014 → T015 → T016 → T018 comparten archivo; T017 es independiente de esa redacción. T019 depende de ambos bloques; T020 → T021 → T022 después del rojo. Los fallos de destino se resuelven en US2, sin llamarlos defectos de conteo.
- US2: T024 → T025 → T026 → T027 comparten archivo. T023 y T028 también deben estar escritos antes de T029; T029 → T030 → T031 → T032 → T033 → T034. T031 no se completa sin conservar errores, filtros y prefetch de la misma regla canónica.
- US3: T035 → T036 → T037 → T038. US4: T039 → T040 → T041 → T042. Mantener serialización por template y archivo de tests.
- Final: T043 → T044 → T045 → T046 → T047 → T048 → T049 → T050 → T051 → T052; los comandos de base y los editores del mismo quickstart no se solapan.

### Asociación de tareas funcionales con pruebas

| Cambio funcional | Pruebas que lo gobiernan |
|---|---|
| T007 carga canónica | T004; ejecución T012 y T043. |
| T008 resultados y estudios con resultados | T005; integración T024–T027; ejecución T012/T034/T043. |
| T009 extracción compatible | T004 y regresión de carga en T012/T044. |
| T011 indicador con URL opcional | T010; regresión dashboard T012/T042. |
| T020/T021 Inicio | T013–T018, T004–T006; ejecución T022 y T043. |
| T030 formulario | T023; ejecución T029/T034. |
| T031 búsqueda, totales y prefetch | T023–T027; ejecución T034/T043. |
| T032/T033 resultados identificables y presentación | T024/T025/T027 y estados inválidos/vacíos T023; ejecución T034/T043. |
| Enlace de listos reutilizado | T006/T016/T028; ejecución T034/T043. |
| T037 agrupación | T035; ejecución T038/T043. |
| T041 dashboard | T039 y tests existentes del destino; ejecución T042/T043. |

## Parallel Examples

### Fundamentos

Tras T003, solo la redacción de T004 en estudios/tests/test_pendientes.py y T010 en config/tests/test_componentes.py puede hacerse en paralelo ([P]). Ambos tienen contratos fijados y archivos distintos. Observar sus fallos y ejecutar suites se hace en serie; no correr migraciones/fixtures contra una misma base simultáneamente.

### User Story 1

Tras T012, solo la redacción de T013 en config/tests/test_inicio_roles.py y T017 en config/tests/test_inicio.py puede hacerse en paralelo ([P]). T014–T018 esperan la tarea previa que modifica su archivo. T019 espera ambos bloques y ejecuta tests en serie.

### User Story 2

Se elige ejecución serial sin [P]: formularios, integración de querysets, parcial y template están acoplados al contrato de contexto; los tests de listado comparten archivo y base. No se promete paralelismo por el mero hecho de pertenecer a otra historia.

### User Stories 3 y 4

Sin [P]: ambas editan config/tests/test_inicio_roles.py y templates/inicio.html. Completar y verificar US3 antes de integrar US4 evita conflictos. La revisión manual no corre en paralelo con cambios de interfaz.

## Implementation Strategy

### MVP e incrementos

1. Completar Setup y fundamentos con pruebas de predicados y compatibilidad.
2. Completar US1 y validar conteos/presentación por separado. Este incremento no se presenta como feature entregable con enlaces completos todavía.
3. Completar US2: MVP coherente de pendientes por rol con destinos correctos y conteo individual verificable.
4. Completar US3 y US4 conservando los cuatro criterios Jira y validando cada historia de forma independiente.
5. Ejecutar validación integral y documentación. Estos checkpoints son revisiones locales; no autorizan despliegue ni publicación.

### Disciplina de pruebas y alcance

Mantener la secuencia tests → fallo por comportamiento nuevo → cambio mínimo → verde en cada bloque. Las caracterizaciones de emisión/autorización existentes no deben forzarse a fallar. Usar fixtures con invariantes reales, Decimal y servicios de dominio ya existentes para cambios de estado; no duplicar sus implementaciones en tests ni cambiar las reglas para acomodar un contador.

Se conservan la unidad Estudio.pk para carga/listos y Resultado.pk para validaciones; la paginación sigue contando estudios y la suma de resultados de todas las páginas coincide con el total canónico bajo datos estables. No prometer snapshot entre requests ni añadir locks o caché.

## Matriz exacta de trazabilidad de aceptación

Los nombres de test se conservan de test-matrix.md aprobado. Si durante implementación una función se parametriza o se divide, T050 debe registrar el node ID real equivalente, preservando todas las aserciones del escenario.

| Escenario | Tarea que crea o completa la prueba | Test exacto planificado |
|---|---|---|
| US1.1 | T013 | config/tests/test_inicio_roles.py::test_carga_sin_iniciar_y_parcial |
| US1.2 | T013 | config/tests/test_inicio_roles.py::test_tecnico_solo_mediciones |
| US1.3 | T013 | config/tests/test_inicio_roles.py::test_bioquimico_tres_unidades |
| US1.4 | T004 | estudios/tests/test_pendientes.py::test_carga_distinta_y_no_calculadas |
| US1.5 | T005 | estudios/tests/test_pendientes.py::test_resultados_existentes_y_recalculados |
| US1.6 | T006 | estudios/tests/test_pendientes.py::test_listos_paridad_regla_existente |
| US1.7 | T013, T024 | config/tests/test_inicio_roles.py::test_ceros_con_enlaces |
| US1.8 | T016 | config/tests/test_inicio_roles.py::test_firma_no_cambia_listos |
| US1.9 | T014 | config/tests/test_inicio_roles.py::test_administrador_comun |
| US1.10 | T014 | config/tests/test_inicio_roles.py::test_administrador_bioquimico |
| US1.11 | T014 | config/tests/test_inicio_roles.py::test_permisos_no_sustituyen_grupo |
| US1.12 | T015 | config/tests/test_inicio_roles.py::test_bioquimico_sin_permiso_operativo |
| US1.13 | T013 | config/tests/test_inicio_roles.py::test_validacion_cinco_mas_uno |
| US1.14 | T017, T035, T039 | config/tests/test_inicio.py::test_reemplazo_conserva_otras_funciones |
| US2.1 | T024 | estudios/tests/test_pendientes_busqueda.py::test_enlace_carga_conjunto_exacto |
| US2.2 | T024 | estudios/tests/test_pendientes_busqueda.py::test_resultados_identificables |
| US2.3 | T028 | config/tests/test_inicio_roles.py::test_enlace_listos_reusa_filtro |
| US2.4 | T026 | estudios/tests/test_pendientes_busqueda.py::test_cambio_entre_requests |
| US2.5 | T025 | estudios/tests/test_pendientes_busqueda.py::test_paginacion_conserva_filtros |
| US2.6 | T025 | estudios/tests/test_pendientes_busqueda.py::test_union_resultados_todas_paginas |
| US3.1 | T035 | config/tests/test_inicio_roles.py::test_orden_grupos |
| US3.2 | T035 | config/tests/test_inicio_roles.py::test_accesos_por_modulo |
| US3.3 | T035 | config/tests/test_inicio_roles.py::test_gestion_tipos_permiso |
| US3.4 | T035 | config/tests/test_inicio_roles.py::test_navegacion_no_muta |
| US4.1 | T039 | config/tests/test_inicio_roles.py::test_tarjeta_dashboard_autorizado |
| US4.2 | T039 | config/tests/test_inicio_roles.py::test_sin_dashboard |
| US4.3 | T039 | config/tests/test_inicio_roles.py::test_dashboard_independiente_rol |

T043 y T044 ejecutan la cobertura integrada de todas las filas; las tareas específicas escriben los tests antes de sus cambios funcionales. T049 agrega la validación manual de SC-005 y accesibilidad, sin reemplazar la cobertura automatizada.

## Resumen y estado al generar

| Fase | Rango | Cantidad |
|---|---|---|
| Setup y compatibilidad | T001–T003 | 3 |
| Fundamentos compartidos | T004–T012 | 9 |
| US1: indicadores personalizados (P1) | T013–T022 | 10 |
| US2: navegación a pendientes (P1) | T023–T034 | 12 |
| US3: accesos por módulo (P2) | T035–T038 | 4 |
| US4: dashboard (P2) | T039–T042 | 4 |
| Validación integral y documentación | T043–T052 | 10 |
| Total | T001–T052 | 52 |

30 tareas de pruebas automatizadas (escritura, caracterización o ejecución): T004–T006, T010, T012–T019, T022–T029, T034–T036, T038–T040, T042–T044 y T048. Además, T045–T047, T049 y T051 son cinco tareas de controles de calidad, incluidas revisión manual y auditoría del diff. El número de tareas de testing no equivale al número de tests: hay 27 escenarios más parametrizaciones y regresiones.

No hay bloqueos técnicos nuevos identificados. Permanecen como riesgos a verificar el historial multivaluado, N+1, cantidad de pruebas por estudio, caché de permisos en fixtures y CSS compilado; quedan cubiertos por tareas concretas. La brecha de trazabilidad US permanece sin inventar el dato; disponibilidad de Docker/PostgreSQL/Node y evidencias manuales deberán comprobarse al implementar.

Al generar se comprobó que .specify/extensions.yml no existe: no hay hooks before_tasks/after_tasks registrados. Todas las tareas permanecen [ ] y la siguiente fase sugerida es $speckit-analyze; este documento no ejecuta ni autoriza $speckit-implement por sí solo.

## Cierre de implementación — 2026-11-10

Registro anterior conservado como estado histórico de generación. El responsable autorizó posteriormente $speckit-implement y se verificaron **T001–T052: 52/52 completadas, 0 pendientes**, incluidas las 30 tareas de pruebas automatizadas y los cinco controles adicionales.

Checkpoints: fundamentos 60 tests aprobados; US1 30; US2 126; US3 46; US4 54; integración focal 104; suite completa final PostgreSQL **1906 passed in 932.87s**, más **8 tests de componentes** del último ajuste visual y **42 tests JS**. Estas cifras son ejecuciones con alcances solapados, no deben sumarse como tests únicos. Rojo/verde, controles de calidad, incidencias y límites están registrados en quickstart.md.

La matriz test-matrix.md vincula **27/27** escenarios con tests reales y los cuatro criterios Jira. Sin nuevos permisos, migraciones, dependencias, cambios en Constitution u otras historias. Checklist de requisitos intacta 16/16. No hay extensions.yml ni hooks after_implement. Sin commit, push, PR ni merge; completar la trazabilidad Jira/US antes del futuro PR.
