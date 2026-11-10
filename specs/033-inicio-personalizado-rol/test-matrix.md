# Matriz de pruebas — Feature 033

Cada fila corresponde a un escenario de la spec aprobada y a una función de test implementada. Se conservaron los nombres planificados; las parametrizaciones agregan casos sin reemplazar escenarios. La evidencia de ejecución y sus límites están en quickstart.md.

## Patrones y datos

- pytest-django sobre PostgreSQL 16; no SQLite para filtros con unaccent ni servicios que usan bloqueos PostgreSQL. Usar fixtures locales existentes de `estudios/tests/conftest.py` y utilidades `estudios/tests/utiles.py:cargar` y `validar` para estados reales.
- Crear un técnico separado al comparar perfiles: `bioquimico` y `empleado` pueden referir a la misma instancia en fixtures actuales. Importar solo fixtures necesarias; no reorganizar todos los conftest.
- Para cuentas sin permiso, eliminar concesiones por usuario y por todos los grupos relevantes, no solo una asignación individual. Recargar instancia o usar request nuevo para evitar cachés de permisos. Crear grupos/permisos explícitos cuando tests transaccionales vacíen datos de migraciones.
- Mantener pares con resultados calculados/ausentes, validación vigente/anulada y estudio informado/sin informar. Usar servicios reales para pruebas de transición; manipulación directa de estados se limita a fixtures explícitamente anómalas o casos aislados de consulta y regla de preparación, sin presumir que representan un flujo real.
- Comparar IDs esperados fijados por el caso y estado de negocio, no calcular el esperado llamando al mismo helper que se prueba. Añadir además pruebas de integración que demuestren que Inicio y lista usan la misma selección.
- Dataset de volumen: más de 20 estudios elegibles, varios resultados por estudio y algunas validaciones anuladas históricas, para demostrar paginación, no duplicación y ausencia de N+1.

## Cobertura de aceptación: 27/27

| Escenario | Archivo y test implementado | Comprobación observable |
|---|---|---|
| US1.1 | config/tests/test_inicio_roles.py::test_carga_sin_iniciar_y_parcial | Un Pendiente de análisis y un En proceso elegibles dan 2 estudios. |
| US1.2 | config/tests/test_inicio_roles.py::test_tecnico_solo_mediciones | Solo indicador de carga; sin acciones profesionales restringidas. |
| US1.3 | config/tests/test_inicio_roles.py::test_bioquimico_tres_unidades | Tres indicadores, unidades y enlaces correctos. |
| US1.4 | estudios/tests/test_pendientes.py::test_carga_distinta_y_no_calculadas | Varias asignaciones cuentan un estudio; solo calculada no cuenta; fórmula con medición propia no se excluye por tipo FORMULA. |
| US1.5 | estudios/tests/test_pendientes.py::test_resultados_existentes_y_recalculados | Cargada con Resultado sin vigente sí; sin Resultado o con vigente no; recálculo devuelve al pendiente según servicio existente. |
| US1.6 | estudios/tests/test_pendientes.py::test_listos_paridad_regla_existente | Sin pruebas, incompleto, completo e informado; mismo resultado de preparación que motivo_para_no_informar. |
| US1.7 | config/tests/test_inicio_roles.py::test_ceros_con_enlaces | Ceros visibles por perfil; seguir cada URL válida produce lista vacía. |
| US1.8 | config/tests/test_inicio_roles.py::test_firma_no_cambia_listos | Cuenta autorizada sin firma conserva conteo; flujo de emisión continúa exigiéndola, sin generar informe. |
| US1.9 | config/tests/test_inicio_roles.py::test_administrador_comun | Administradores sin Bioquímicos tiene presentación técnica. |
| US1.10 | config/tests/test_inicio_roles.py::test_administrador_bioquimico | Ambos grupos producen tres indicadores. |
| US1.11 | config/tests/test_inicio_roles.py::test_permisos_no_sustituyen_grupo | Parametrizar permiso individual, otro grupo y superusuario; sin Bioquímicos conserva presentación técnica y accesos existentes autorizados. |
| US1.12 | config/tests/test_inicio_roles.py::test_bioquimico_sin_permiso_operativo | Consulta permitida, detalle sin acciones restringidas; accesos directos de validación/emisión denegados sin cambios. |
| US1.13 | config/tests/test_inicio_roles.py::test_validacion_cinco_mas_uno | Contador 6 para estudios con 5+1+0 resultados pendientes. |
| US1.14 | config/tests/test_inicio.py::test_reemplazo_conserva_otras_funciones | Ausencia de contadores anteriores y duplicados; bienvenida, últimas cinco muestras, navegación y dashboard según autorización. |
| US2.1 | estudios/tests/test_pendientes_busqueda.py::test_enlace_carga_conjunto_exacto | Seguir URL de Inicio; IDs de estudios coinciden con pendientes esperados, incluida carga parcial. |
| US2.2 | estudios/tests/test_pendientes_busqueda.py::test_resultados_identificables | Ver seis Resultado.pk distintos, estudio, prueba, valor/unidad; excluir validados/no calculados y distinguir total de dos estudios. |
| US2.3 | config/tests/test_inicio_roles.py::test_enlace_listos_reusa_filtro | href con listos=1; seguirlo recupera todos y solo estudios preparados, nunca emitidos. |
| US2.4 | estudios/tests/test_pendientes_busqueda.py::test_cambio_entre_requests | Capturar Inicio, resolver pendiente por servicio real, seguir enlace y recargar Inicio: ambos reflejan el nuevo estado; sin sleeps/hilos. Parametrizar carga/validación/emisión cuando aplique. |
| US2.5 | estudios/tests/test_pendientes_busqueda.py::test_paginacion_conserva_filtros | Más de 20 estudios; pendiente, q, desde, hasta y estado se conservan en enlaces; total no es longitud de página. |
| US2.6 | estudios/tests/test_pendientes_busqueda.py::test_union_resultados_todas_paginas | Recorrer páginas estables; unión de Resultado.pk sin repetidos, cantidad igual a Inicio sin filtros extra y a total filtrado con criterios manuales. |
| US3.1 | config/tests/test_inicio_roles.py::test_orden_grupos | Clientes, Muestras, Estudios, Informes una vez y en ese orden de DOM. |
| US3.2 | config/tests/test_inicio_roles.py::test_accesos_por_modulo | Pertenencia de cada acceso actual al grupo y URL reverse correcta. |
| US3.3 | config/tests/test_inicio_roles.py::test_gestion_tipos_permiso | Acceso rápido solo por gestionar_catalogo, dentro de Estudios; menú/entrada directa conservan políticas previas. |
| US3.4 | config/tests/test_inicio_roles.py::test_navegacion_no_muta | Abrir destinos existentes con actor permitido; sin nuevas mediciones, resultados, validaciones o informes; autorizaciones previas intactas. |
| US4.1 | config/tests/test_inicio_roles.py::test_tarjeta_dashboard_autorizado | Tarjeta titulada Ver dashboard con reverse correcto y destino 200 con permiso efectivo. |
| US4.2 | config/tests/test_inicio_roles.py::test_sin_dashboard | Sin permiso no hay tarjeta; URL directa 403 para usuario activo. |
| US4.3 | config/tests/test_inicio_roles.py::test_dashboard_independiente_rol | Cuenta común con permiso individual sí; bioquímico sin permiso efectivo no; superusuario activo sin Bioquímicos conserva acceso estándar. |

## Matriz de autorización parametrizada

Cada combinación se verifica en requests nuevos. Los permisos profesionales del grupo habitual se mantienen salvo en el caso que explícitamente los retira.

| Cuenta activa | Indicadores | Lectura de búsqueda/selección | Validar / emitir | Tarjeta dashboard |
|---|---|---|---|---|
| Común sin permisos profesionales | Carga | Permitida | Denegado / denegado | Solo si permiso efectivo, habitualmente no. |
| Bioquímicos habitual | Tres | Permitida | Por permisos efectivos | Por permiso efectivo habitual. |
| Administradores sin Bioquímicos | Carga | Permitida | Por permisos efectivos, no por Administradores | Por permiso efectivo habitual. |
| Administradores y Bioquímicos | Tres | Permitida | Por permisos efectivos | Por permiso efectivo. |
| Común con permisos individuales/otro grupo | Carga | Permitida | Conservar permisos concedidos | Independiente por permiso efectivo. |
| Bioquímicos sin validar/emitir efectivos | Tres | Permitida | Denegado en cada operación sin permiso | Independiente por permiso efectivo. |
| Superusuario fuera de Bioquímicos | Carga | Permitida | Conservar backend estándar | Sí por has_perm efectivo. |
| Superusuario en Bioquímicos | Tres | Permitida | Conservar backend estándar | Sí por has_perm efectivo. |
| Cuenta inactiva o sesión ausente | Sin Inicio protegido | Redirección a login | Sin acceso autenticado | No expuesta. |

Para inactivos: comprobar login rechazado y también iniciar sesión activa, desactivar en base, hacer nuevo GET a Inicio/listas/dashboard y verificar redirección. Conservar diferencias entre login requerido y 403 de una cuenta activa sin permiso. No introducir una prueba que asuma que RequestFactory ejecuta middleware automáticamente.

## Casos complementarios obligatorios

- **Consultas canónicas**: paridad de carga con `admite_mediciones` y `asignaciones_para_medir`; resultados calculados sin medición propia, cero valores válidos, validaciones anuladas históricas sin duplicados, anomalía Cargada con vigente excluida sin reparar datos. Informe generado excluido en todos los pendientes. Prueba validada fuera de norma no agrega bloqueo de preparación.
- **Filtros**: probar vacío, cada modo y combinación AND con q/estado/fechas; fechas inclusivas y zona horaria actual; combinación incompatible devuelve cero. Al agregar filtros, total de resultados filtrados se distingue del global.
- **Errores y compatibilidad**: modo desconocido, texto largo, fechas inválidas, rango invertido y estado inválido conservan errores y listado completo sin aplicar modo ni rótulo de selección. Sin pendiente conserva salida general. Historial de clientes y BuscarEstudioForm de Informes no reciben el campo nuevo. Mantener el tratamiento actual de page.
- **Rendimiento**: CaptureQueriesContext compara pocas/muchas muestras en Inicio, pocos/muchos estudios y resultados en una misma página para búsqueda; consultas no crecen por fila. No exigir el mismo número entre modo general y validaciones. Verificar que Técnico no ejecuta conteos profesionales y el template no consulta relaciones por fila.
- **Componentes**: indicador con/sin URL, data-indicador/data-valor, texto accesible y enlace nativo; ausencia de enlaces anidados. Regresión del dashboard al usar el parcial sin URL. Revisión de teclado, foco, orden de lectura y estados vacíos.
- **Sesión y cambios de autorización**: huella de sesión y never-cache conservadas; alta/baja de Bioquímicos, revocación de dashboard y desactivación visibles en siguiente request. No alterar política administrativa especial.
- **SC-005**: tests HTTP prueban navegación en una acción sin búsquedas; la meta de 30 segundos requiere revisión manual cronometrada con técnico y bioquímico, no un assert artificial de tiempo de ejecución de pytest.

## Regresiones y evidencia de ejecución

Actualizar acotadamente los tests de contadores antiguos en `config/tests/test_inicio.py`; conservar bienvenida, accesos, últimas muestras, vacío, sesión y rendimiento. Ejecutar las suites existentes de estudios (carga, cálculo, corrección, validación, filtros y concurrencia), informes (control, búsqueda, permisos y dashboard), usuarios (autenticación, sesión y administración) y clientes (historial/filtros). La suite completa protege los efectos indirectos.

Comandos y verificación manual: [quickstart.md](quickstart.md). Al implementar, registrar versión/base usada, comandos, resultados y fallos; no marcar esta matriz como ejecutada desde la fase de planificación. Los tests de escritura existentes conservan sus invariantes, confirmaciones, CSRF y locks; esta feature no agrega nuevas escrituras ni necesita tests de carreras artificiales para GET.

## Resultado de implementación — 2026-11-10

- **27/27 escenarios ejecutados y aprobados** mediante las funciones de la tabla, sin reemplazar decisiones aprobadas. La correspondencia de los 27 nombres con funciones reales se comprobó por lectura.
- Suite focal integrada: **104 passed in 35.28s**. Suite completa final sobre PostgreSQL 16: **1906 passed in 932.87s (0:15:32)**, exit code 0. Incluye regresiones de todos los módulos, permisos y concurrencia existentes.
- US1.14 se parametrizó para Técnico/Bioquímico: `config/tests/test_inicio.py::test_reemplazo_conserva_otras_funciones[False]` y `[True]`. US1.11 se parametrizó con individual/grupo/superusuario; US2.4 con mediciones/validaciones/listos; US3.3 con False/True; US4.3 con individual/administrador/otro_grupo/superusuario/bio_sin_permiso. Los nombres de función de la tabla siguen siendo selectores válidos de pytest que agrupan esos casos.
- Cobertura complementaria: tests de historial sin duplicados, resultado calculado/cero/vigente, cuatro estados de carga, roles y revocación en request siguiente, filtros inválidos y AND, más de 20 estudios y unión de resultados, consultas constantes y ausencia de conteos profesionales para Técnico. La batería final de componentes tras el último ajuste visual pasó **8/8 en 1.41s**, sin acceso a base.
- Los cuatro criterios Jira quedan cubiertos respectivamente por US1, US2, US3 y US4. No se afirma porcentaje de cobertura de líneas; 27/27 es cobertura de escenarios de aceptación.
- SC-005 y teclado: revisión en navegador con perfiles sintéticos, Técnico 4.068 s y Bioquímico 5.502 s para observar/elegir/abrir pendiente. Es revisión por agente, no estudio con empleados reales; detalles y capturas en quickstart.md.
