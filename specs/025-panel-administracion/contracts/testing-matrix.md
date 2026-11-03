# Matriz de validación automatizada

Cobertura implementada y ejecutada; resultados en quickstart.md. USn.m identifica el escenario m del recorrido n de spec.md, sin inventar un identificador Jira. Hay **35 escenarios**: 6 + 9 + 11 + 5 + 4. Cada uno tiene al menos un test pytest-django concreto; las referencias parametrizadas incluyen sus variantes.

## Cobertura de aceptación

| Escenario | Test implementado y resultado observable |
| --- | --- |
| US1.1 | `usuarios/tests/test_administracion_navegacion.py::test_menu_autorizado_y_diseno`. Menú/diseño y GET autorizado con Administradores + permiso asignado |
| US1.2 | `usuarios/tests/test_administracion_permisos.py::test_http_sin_autorizacion_403_antes_de_objetivo`. Cada ruta GET/POST con grupo sin permiso, permiso sin grupo y ninguno: 403 sin cambios/exposición |
| US1.3 | `usuarios/tests/test_administracion_permisos.py::test_todas_las_rutas_anonimas_piden_login`. Anónimo redirige al login existente; no consulta listado protegido |
| US1.4 | `usuarios/tests/test_administracion_permisos.py::test_revocacion_entre_revision_y_confirmacion`. Revocar grupo o permiso entre revisión y confirmación: POST válido 403 y sin efecto |
| US1.5 | `usuarios/tests/test_administracion_permisos.py::test_http_sin_autorizacion_403_antes_de_objetivo`. Superusuario fuera del grupo: panel 403 y Django Admin sigue accesible |
| US1.6 | `usuarios/tests/test_administracion_migraciones.py::test_grupo_idempotente_conserva_miembros_y_otros_permisos`. Migración crea grupo/permiso y vínculo, idempotente, sin inscribir usuarios |
| US2.1 | `usuarios/tests/test_administracion_solicitudes.py::test_listado_solo_pendientes`. Identidad, botones, paginación y vacío de solicitudes |
| US2.2 | `usuarios/tests/test_administracion_solicitudes.py::test_resolucion_confirmada`. Confirmar aprobación habilita acceso y entrega un aviso con enlace correcto |
| US2.3 | `usuarios/tests/test_administracion_solicitudes.py::test_revision_cancelacion_y_reenvio`. Abrir rechazo muestra identidad/consecuencias, sin cambios/correos |
| US2.4 | `usuarios/tests/test_administracion_solicitudes.py::test_revision_cancelacion_y_reenvio`. Cancelar rechazo conserva pendiente, cero avisos |
| US2.5 | `usuarios/tests/test_administracion_solicitudes.py::test_resolucion_confirmada`. Rechazo efectivo de pendiente elegible sin impedimentos elimina, libera correo y permite nuevo registro; un aviso |
| US2.6 | `usuarios/tests/test_administracion_concurrencia.py::test_una_resolucion_y_un_aviso`. Reenvío y carreras aprobar/aprobar, aprobar/rechazar y rechazar/rechazar: una resolución y aviso |
| US2.7 | `usuarios/tests/test_administracion_avisos.py::test_fallo_smtp_conserva_decision`. SMTP falla: resolución persiste y logger registra falla |
| US2.8 | `usuarios/tests/test_administracion_solicitudes.py::test_listado_solo_pendientes`. Desactivadas fuera de pendientes; aprobar/rechazar por URL o admin no las resuelve |
| US2.9 | `usuarios/tests/test_administracion_solicitudes.py::test_historico_impedido_aprobacion_posterior`. T006/T034: rechazo de pendiente histórica con referencias protegidas o firma se impide con motivo; conserva cuenta/email/referencias/firma/historial/estado/versión, cero avisos y acceso denegado; revisión y aprobación normal posterior disponible sin automatismos |
| US3.1 | `usuarios/tests/test_administracion_usuarios.py::test_listado_estados_roles`. Usuarios muestra identidad, rol y tres estados, sin N+1 |
| US3.2 | `usuarios/tests/test_administracion_usuarios.py::test_rol_confirmado_y_cancelado_conserva_privilegios`. Rol propio/ajeno confirmado/cancelado; solo cambia Bioquímicos |
| US3.3 | `usuarios/tests/test_administracion_estados.py::test_suspension_conserva_historia_y_reactiva_sin_aviso`. Suspender otra activa conserva PK, grupos, permisos, firma y referencias históricas; sesión previa pierde acceso |
| US3.4 | `usuarios/tests/test_administracion_estados.py::test_suspension_conserva_historia_y_reactiva_sin_aviso`. Reactivar aprobada restaura acceso y no emite aviso de aprobación |
| US3.5 | `usuarios/tests/test_administracion_estados.py::test_cancelar_estado`. Cancelar estado conserva valores y versión, sin avisos |
| US3.6 | `usuarios/tests/test_administracion_estados.py::test_pendientes_y_propia_no_gestionables`. Cuenta propia sin botón; POST forjado y servicio directo impiden desactivación |
| US3.7 | `usuarios/tests/test_administracion_concurrencia.py::test_rol_frente_estado`. Versión antigua y carrera de rol/estado: no sobrescribir; incluir A→B→A y ficha admin contra panel |
| US3.8 | `usuarios/tests/test_administracion_estados.py::test_pendientes_y_propia_no_gestionables`. Pendiente no cambia rol ni se activa/suspende desde Usuarios y roles |
| US3.9 | `usuarios/tests/test_administracion_migraciones.py::test_backfill_conserva_identidades_permisos_y_referencias`. MigrationExecutor: activo conserva acceso; inactivo sin prueba sigue sin acceso, misma PK/referencias |
| US3.10 | `usuarios/tests/test_administracion_usuarios.py::test_rol_confirmado_y_cancelado_conserva_privilegios`. Administrador pasa a Bioquímico y conserva ambos grupos y otros permisos |
| US3.11 | `usuarios/tests/test_administracion_usuarios.py::test_rol_confirmado_y_cancelado_conserva_privilegios`. Retiro propio de Bioquímicos mantiene Administración, permisos individuales y otros grupos |
| US4.1 | `usuarios/tests/test_administracion_catalogo.py::test_catalogo_datos_busqueda_y_unidad`. Listado incluye activas/inactivas, cinco datos y enlace correcto |
| US4.2 | `usuarios/tests/test_administracion_catalogo.py::test_catalogo_datos_busqueda_y_unidad`. Código/nombre parcial, mayúsculas/minúsculas, q vacío y paginación con q |
| US4.3 | `usuarios/tests/test_administracion_catalogo.py::test_catalogo_vacio_y_solo_lectura`. Catálogo vacío/sin coincidencias y limpiar búsqueda |
| US4.4 | `usuarios/tests/test_administracion_catalogo_admin.py::test_enlace_no_concede_edicion`. URL de edición correcta; sin staff/permiso no concede edición, con permisos conserva reglas de PruebaAdmin |
| US4.5 | `usuarios/tests/test_administracion_catalogo.py::test_catalogo_datos_busqueda_y_unidad`. Unidad vacía/-- muestra Sin unidad mediante filtro existente |
| US5.1 | `usuarios/tests/test_administracion_tipos_menu.py::test_tipos_solo_en_administracion_con_ambos_permisos`. Enlace una sola vez bajo Administración, ausente de Estudios |
| US5.2 | `usuarios/tests/test_administracion_tipos_acceso.py::test_panel_sin_permiso_de_tipos_403`. Administrador sin gestionar_catalogo: enlace ausente y GET/POST tipos 403 |
| US5.3 | `usuarios/tests/test_administracion_tipos_acceso.py::test_gestor_solo_permiso_conserva_acceso`. Regresión completa tipos: confirmar/cancelar, editar, activar/desactivar, usadas y concurrencia |
| US5.4 | `usuarios/tests/test_administracion_tipos_menu.py::test_gestor_conserva_tarjeta_sin_panel`. Gestor con solo permiso de tipos: panel ausente/403 y tipos directo permitido; tarjeta Inicio conservada |

## Cobertura adicional necesaria

| Riesgo | Casos obligatorios |
| --- | --- |
| Bypass | Superusuario en grupo sin permiso real también 403; admin común no staff puede usar panel si cumple autorización |
| Autorización en profundidad | Servicios directos con actor inválido/inactivo, revocado y request.user con caché vieja; objetivos no consultados antes de autorizar |
| CSRF/métodos | Client(enforce_csrf_checks=True), POST sin CSRF 403; con CSRF válido se prueba autorización; GET no modifica dominio, métodos inválidos 405 |
| Tokens | Alterado, ajeno, otra sesión, otra cuenta, operación cruzada, caducado, borrador consumido, propuesta cambiada y límite 20 |
| Cancelación | Todas las operaciones, incluso rol propio, sin DML de dominio ni callbacks |
| Atomicidad | Error DB revierte estado/versión/grupos; callback no sale por rollback |
| Rechazo protegido | US2.9/T006/T034: parametrizar PROTECT y firma; conserva todo y no manda aviso ni libera email ni activa. Después, confirmar aprobación normal y verificar referencias/firma conservadas y un único aviso de aprobación, sin relajar restricciones |
| Ficha admin | Aprobar desde ficha un aviso; reactivar ninguno; token obsoleto error de formulario; creación sin aviso; M2M preservado |
| Concurrencia | Dos conexiones y barrera: panel/admin, panel/panel, ficha/acción; roles y estados simultáneos, objetivos cruzados con orden PK |
| Migraciones | Forward desde 0002 con activos/inactivos/superusuarios/grupos/permisos/referencias; constraints; ejecución de función de grupo repetida; reversión sin activar ni perder miembros; restaurar esquema final |
| Creación | Manager activo por defecto, pending is_active=False, superuser y registro coherentes; activo sin aprobado no válido |
| Login/privacidad | Contraseña correcta distingue pendiente/suspendida; incorrecta/no existente conserva mensaje genérico y comparación real/ficticia |
| Roles | Permisos duplicados por otras vías sobreviven retiro de Bioquímicos; usuarios desactivados cambian rol sin habilitarse |
| Rendimiento/UX | Roles sin N+1, orden/páginas estables, etiquetas, aria-current y confirmaciones; máximo tres acciones SC-005 |
| CSS | Clases compiladas, tokens visuales existentes; recompilación sin diff inesperado en CI |

## Requisitos y Jira

| Jira original | FR | Cobertura |
| --- | --- | --- |
| 1. Sección/grupo/permiso | 001–005 | US1.1–1.6, migraciones y bypass |
| 2. Solicitudes y aviso actual | 006–008, 010, 016–017 | US2.1–2.9 y carreras/callbacks |
| 3. Usuarios, roles, estados, cuenta propia | 009–012, 017 | US3.1–3.11 y migración conservadora |
| 4. Consulta de catálogo/enlace | 013–014 | US4.1–4.5 |
| 5. Reubicar tipos/mismo permiso | 004, 015 | US5.1–5.4 |
| 6. Acceso directo HTTP 403 | 003–004 | Cada GET/POST y servicios con matriz de autorización |

SC-001: matriz 403; SC-002: correos/rollback/carreras y US2.9 (T006/T034, conservación íntegra, motivo y ningún aviso de rechazo); SC-003: rol/estado/confirmación/cuenta propia; SC-004: catálogo conocido; SC-005: flujos directos y prueba manual de acciones; SC-006: navegación/regresión tipos; SC-007: estados y migración. Automatizar resultados y secuencias; revisión visual complementa, no reemplaza tests.

## Organización y ejecución posterior

Archivos previstos en usuarios/tests: test_administracion_permisos, test_administracion_solicitudes, test_administracion_usuarios, test_administracion_catalogo, test_administracion_confirmaciones, test_administracion_migraciones y test_administracion_concurrencia. Ampliar tests propios de admin/login/notificaciones; no modificar specs ajenas.

Reutilizar fixtures de usuarios y los mecanismos django_capture_on_commit_callbacks(execute=True) y mailoutbox. Para carreras usar pytest.mark.django_db(transaction=True), conexiones independientes por hilo, barreras/eventos y timeout acotado como estudios/tests/test_gestion_tipos_concurrencia.py. No sustituir carreras por mocks de bloqueo; no usar SQLite.

MigrationExecutor usa registro histórico, fixture dedicada y restauración del esquema final en finally. Tests transaction=True pueden vaciar grupos creados por migración: fixtures deben reconstruir Administradores/Bioquímicos y sus permisos con get_or_create, como el patrón existente. Diferenciar fixture administrador_panel de administrador actual, que representa un superusuario de Django Admin.

Regresiones mínimas completas: usuarios (registro/login/sesión/admin/avisos), pruebas, estudios (tipos y validación) e informes (emisión/firma y permisos). Finalmente pytest completo para clientes y muestras también. CI conserva ruff check, ruff format --check, makemigrations --check --dry-run, CSS compilado y pytest sobre PostgreSQL 16. Comandos y precondiciones en quickstart.md.


## Cierre de cobertura

35/35 escenarios con referencias concretas verificadas contra funciones existentes. US5.3 se acredita adicionalmente con la ejecución completa de estudios/tests/test_gestion_tipos_ui.py, test_gestion_tipos_servicio.py, test_gestion_tipos_confirmaciones.py y test_gestion_tipos_concurrencia.py (operaciones reales/confirmaciones/usadas/bloqueos), conservados sin modificaciones. US4.5 incluye también estudios/tests/test_modelos.py::test_filtro_unidad para vacío, -- y None; US4.4 se complementa con pruebas/tests/test_admin.py para restricciones del editor existente.

| Requisito | Pruebas concretas y escenarios que lo acreditan |
| --- | --- |
| FR-001 | test_menu_autorizado_y_diseno; US1.1 |
| FR-002 | test_grupo_idempotente_conserva_miembros_y_otros_permisos; US1.6 |
| FR-003 | test_http_sin_autorizacion_403_antes_de_objetivo, test_csrf_y_metodos_autorizados; US1.2 |
| FR-004 | test_grupo_y_permiso_real, test_panel_sin_permiso_de_tipos_403, test_gestor_solo_permiso_conserva_acceso; US1.5/US5.2/US5.4 |
| FR-005 | test_revision_cancelacion_y_reenvio, test_cancelar_estado, test_rol_confirmado_y_cancelado_conserva_privilegios; capturas evidence/ |
| FR-006 | test_listado_solo_pendientes, test_objetivo_ausente_y_resuelto; US2.1/US2.8 |
| FR-007 | test_resolucion_confirmada, test_aprobacion_unica_y_reactivacion_sin_aviso; US2.2 |
| FR-008 | test_resolucion_confirmada, test_historico_impedido_aprobacion_posterior; US2.3–US2.5/US2.9 |
| FR-009 | test_listado_estados_roles, test_rol_confirmado_y_cancelado_conserva_privilegios; US3.1/US3.2 |
| FR-010 | test_backfill_conserva_identidades_permisos_y_referencias, test_suspension_conserva_historia_y_reactiva_sin_aviso, test_pendientes_y_propia_no_gestionables; US3.3/US3.4/US3.8/US3.9 |
| FR-011 | test_panel_solo_modifica_pertenencia_bioquimicos, test_rol_confirmado_y_cancelado_conserva_privilegios (propia, ajena activa y desactivada, con permisos profesionales equivalentes por otras vías); US3.10/US3.11 |
| FR-012 | test_pendientes_y_propia_no_gestionables, test_ficha_no_desactiva_propio_admin; US3.6 |
| FR-013 | test_catalogo_datos_busqueda_y_unidad, test_paginacion_y_busqueda_conservada; US4.1–US4.3/US4.5 |
| FR-014 | test_enlace_no_concede_edicion y regresiones de pruebas/tests/test_admin.py; US4.4 |
| FR-015 | test_tipos_solo_en_administracion_con_ambos_permisos, test_gestor_conserva_tarjeta_sin_panel; US5.1/US5.4 |
| FR-016 | test_fallo_smtp_conserva_decision, test_reenvio_aprobacion_no_duplica, test_una_resolucion_y_un_aviso; US2.6/US2.7 |
| FR-017 | test_aba_rechaza_confirmacion, test_rol_frente_estado, test_panel_frente_admin, test_ficha_obsoleta_no_pierde_grupos, test_rol_invalido_y_contexto_obsoleto; US3.7 |

| Criterio de éxito | Evidencia verificable |
| --- | --- |
| SC-001 | Matriz GET/POST de 8 rutas y 5 combinaciones denegadas; test_grupo_y_permiso_real y prueba manual de superusuario fuera del grupo (evidence/superusuario-sin-grupo.jpg) |
| SC-002 | test_resolucion_confirmada, test_revision_cancelacion_y_reenvio, test_reenvio_aprobacion_no_duplica, test_una_resolucion_y_un_aviso y US2.9 (PROTECT/firma); callback tras commit real en test_aviso_solo_tras_commit_real |
| SC-003 | test_rol_confirmado_y_cancelado_conserva_privilegios, test_cancelar_estado y test_pendientes_y_propia_no_gestionables; flujos manuales propio/ajeno |
| SC-004 | test_catalogo_datos_busqueda_y_unidad, test_paginacion_y_busqueda_conservada, test_enlace_no_concede_edicion |
| SC-005 | test_resolucion_confirmada y helper resolver: revisar/confirmar desde listado (2 acciones). test_rol_confirmado_y_cancelado_conserva_privilegios usa la pantalla independiente con contexto firmado: Cambiar rol/Continuar/Confirmar (3 con la alternativa preseleccionada); test_pantalla_rol_solo_ofrece_alternativas comprueba que no se ofrece el rol actual. Comprobado además en navegador |
| SC-006 | test_tipos_solo_en_administracion_con_ambos_permisos, test_gestor_conserva_tarjeta_sin_panel y regresión completa de tipos |
| SC-007 | test_listado_estados_roles, test_listado_solo_pendientes, test_suspension_conserva_historia_y_reactiva_sin_aviso y test_backfill_conserva_identidades_permisos_y_referencias |

Total: 17/17 FR y 7/7 SC trazados; no hay un requisito o escenario sin prueba prevista convertida en prueba real. La revisión manual complementa los tests (no los sustituye). La entrega SMTP frente a una caída del proceso conserva el límite documentado de on_commit; no se promete entrega exactamente una vez fuera de las condiciones normales aprobadas.

Atomicidad de rol: usuarios/tests/test_administracion_usuarios.py::test_error_persistencia_rol_revierte_membresia verifica rollback real de pertenencia y revisión ante un error posterior a escribir; no sustituye locks por mocks. La prueba parametrizada de rol distingue asignaciones conservadas de permisos efectivos: una cuenta desactivada sigue sin acceso.
