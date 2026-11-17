---
description: "Tareas de implementación de US 10.2 — Conclusión asistida del informe"
---

# Tasks: US 10.2 — Conclusión asistida del informe

**Estado final — 2026-11-16: 101/101 completadas; 0 pendientes.** Evidencia y resultados consolidados al final y en quickstart. Los contadores de las secciones históricas describen etapas anteriores.

**Input**: documentos aprobados de `/specs/039-conclusion-asistida-informe/`.
**Prerequisites**: [spec](spec.md), [plan](plan.md), [research](research.md), [modelo](data-model.md), [contrato UI](contracts/conclusiones-ui.md), [contrato IA](contracts/redaccion-ia.md), [matriz](test-matrix.md), [quickstart](quickstart.md), checklist y Constitution 1.2.0.
**Rama**: `39-Conclucion-Asistida`; base `c5a0030a06de65fc56949b8716c36506a2e2bf46`. Fecha de generación: 2026-11-16.
**Tests**: obligatorios por spec/Constitution y pedido expreso. Se escriben antes de modificar el comportamiento correspondiente; comprobar fallo pertinente, no aceptar fallo por configuración rota. Los tests de caracterización de comportamiento existente deben comenzar verdes. Si un test posterior caracteriza comportamiento ya cubierto, registrar que ya pasa; no romper código artificialmente para lograr rojo.
**Organization**: US1–US4 son los cuatro recorridos P1 de una única US 10.2, no nuevas historias Jira. Se conservan 19 FR, diez SC, 38 escenarios y nueve criterios originales. Clave Jira propia no informada.

## Format: `[ID] [P?] [Story] Description`

Los checkboxes reflejan el avance verificado; las tareas sin marcar siguen pendientes. Cada línea tiene checkbox, ID consecutivo, etiqueta de recorrido cuando corresponde, archivos y dependencias. `[P]` indica posibilidad de trabajar en archivos distintos una vez satisfechas **todas** las dependencias indicadas, no permiso para saltarlas. Mismo archivo se modifica en serie. Las descripciones son acciones **futuras**, no ejecución autorizada en esta generación documental.

## Path Conventions

Rutas relativas a la raíz de AquaLab. Código nuevo en informes, UI Django/Tailwind existente; no nuevo proyecto, SDK o dependencias. Paths de tests/módulos nuevos son destinos propuestos, no archivos presentes. Única migración futura `informes/migrations/0006_borradorconclusion.py`, con hoja actual 0005 verificada. `.local-validacion/us102/` es evidencia local ignorada en E:, no publicable. `$us102Compose` se define en quickstart y apunta al Compose aislado; todos los comandos de ejecución pertenecen a la futura implementación.

**Guardias de alcance**: no cambiar US 10.1, Constitution, requisitos/escenarios, permisos generales, históricos ni otras features; no contactos/credenciales a IA. Sin commit/push/PR/merge/rebase en estas tareas sin autorización posterior. No marcar nada completado por generar este documento.

---

## Phase 1: Setup — preparación y caracterización

**Goal**: Establecer baseline y entorno aislado del proyecto existente, sin inicializar apps, instalar dependencias o alterar datos reales.

**Independent Test / Checkpoint**: Caracterización del flujo anterior verde antes de modificarlo; comandos y árbol probado registrados.

### Implementación / preparación

- [X] T001 Preparar el entorno futuro aislado PostgreSQL 16 descrito en `specs/039-conclusion-asistida-informe/quickstart.md`, comprobar rama/base/árbol y herramientas existentes, sin instalar dependencias ni tocar otras bases; registrar comando Compose y baseline en `.local-validacion/us102/resultados.md`. No ejecutar builds o tests hasta autorizar implementación. **Depende de**: ninguna.

### Tests — escribir antes del comportamiento

- [X] T002 Escribir tests de caracterización en `informes/tests/test_conclusion_caracterizacion.py`: vista previa actual, permiso de emisión sin grupo, estudio listo/firma/matrícula, JSON de solo textos, copia histórica sin conclusion, PDF/impresión y correo txt/HTML con destinatario/confirmación/idempotencia; capturar comportamiento antes de tocar servicios/templates. Usar datos sintéticos, IA anulada y correo locmem. **Depende de**: T001.

### Validación — ejecutar solo en implementación

- [X] T003 Ejecutar caracterización con `docker compose -p aqualab-us102 -f $us102Compose run --rm web pytest informes/tests/test_conclusion_caracterizacion.py`; registrar baseline y firmas reales de `informes/servicios.py`, `informes/contenido.py`, `informes/pdf.py`, `informes/envios.py` en `.local-validacion/us102/resultados.md`; no reutilizar conteos de feature 033. **Depende de**: T002.

---

## Phase 2: Foundational — prerrequisitos compartidos

**Goal**: Persistencia mínima, política conjunta y adaptador común probados antes de integrar recorridos.

**Independent Test / Checkpoint**: Modelo/migración, guardia y adaptador pasan sus tests sobre PostgreSQL aislado; decisión GET revisada. Esta fase bloquea los cuatro recorridos.

### Tests — escribir antes del comportamiento

- [X] T004 [P] Escribir en `informes/tests/test_borrador_conclusion.py` tests de fila única por estudio, defaults, tipos, PROTECT, revisión positiva, seis campos de aprobación todos completos/nulos, revisión/hash coherentes, sin permisos automáticos ni backfill; probar la futura migración con copia histórica idéntica. **Depende de**: T003.
- [X] T005 [P] Escribir en `informes/tests/test_conclusion_autorizacion.py` tests de guardia central con sesión activa + grupo exacto Bioquímicos + has_perm('informes.emitir_informes'); negativos independientes: sin sesión/inactivo, solo grupo, solo permiso, Administradores, is_staff y superusuario sin grupo; no otorgar permisos ni alterar consulta/emisión sin conclusión. **Depende de**: T003.
- [X] T006 [P] Escribir en `informes/tests/test_conclusion_adaptador.py` tests puros del contrato IA: herramientas vacías y misma configuración Groq, referencias opacas y patrones F/T/I/P, JSON estricto, cero datos personales, fallback completo por todos los motivos, 64 KiB sin truncar hechos, deadline monotónico de configuración, semáforo 2 y workers tardíos sin ORM; eventos controlados y cero Groq real. Cubrir también errores/limpieza/logs seguros antes de crear adaptador. **Depende de**: T003.

### Decisión técnica y revisión

- [X] T007 Documentar en la sección «Decisiones técnicas de revisión» de `specs/039-conclusion-asistida-informe/tasks.md` y posteriormente evidenciar en `.local-validacion/us102/resultados.md` la decisión GET ya diseñada: solo autorizado y con borrador existente materializa invalidación derivada bajo lock, nunca crea/aprueba ni escribe datos clínicos; lectura repetida sin cambios es no-op y no depende de JS. Confirmar efectos de caché/prefetch y rollback 409 antes de integrar. Cambio a POST u otra política exige revisión de diseño, no improvisación. Si se detectan múltiples vigentes, invalidar aprobación/token y aumentar revisión/requiere_revision sin construir hechos canónicos arbitrarios; conservar últimos hechos solo como referencia obsoleta no emitible, devolver conflicto seguro y mantener emisión sin conclusión bajo sus reglas actuales. Es una salvaguarda técnica ante corrupción, no una nueva evaluación del laboratorio. **Depende de**: T003.

### Implementación / preparación

- [X] T008 Agregar solo BorradorConclusion en `informes/models.py`, campos y restricciones literales: estudio: «OneToOneField(Estudio), on_delete=PROTECT, obligatorio» (Identidad de la conclusión en preparación; sin borrador por usuario.); revision: «PositiveBigIntegerField, default=1, revision >= 1» (Versión de concurrencia de toda la fila. Aumenta al editar, reservar/finalizar propuesta, invalidar por hechos o aprobar; nunca se reduce.); texto_editorial: «TextField, blank=True, default=''» (Texto editable, sin máximo funcional nuevo. Unicode conservado, CRLF→LF antes de mostrar/guardar, sin strip silencioso; rechazar NUL, que no admite PostgreSQL.); texto_final: «TextField, blank=True, default=''» (Materialización exacta de texto editorial + advertencias canónicas, con LF. Es el texto visto y aprobado, no se reconstruye al emitir.); hechos: «JSONField, default=dict» (Documento canónico schema='1', solo dict/list/textos; sin floats ni datos de contacto.); huella_hechos: «CharField(max_length=64), obligatorio, hexadecimal SHA256 en minúsculas» (Hash del JSON canónico del estudio completo, no solo de las pruebas citadas.); advertencias: «JSONField, default=list» (Lista canónica por prueba, motivos y hechos conocidos; no editable por el navegador.); requiere_revision: «BooleanField, default=False» (Indica cambio de fuentes detectado: conserva texto previo pero exige revisarlo contra las fuentes actuales. No sustituye el chequeo de hashes.). **Depende de**: T004, T007.
- [X] T009 Completar BorradorConclusion en `informes/models.py`, restricciones literales: origen_propuesta: «CharField(max_length=10), choices=ia/plantilla/manual, obligatorio» (Procedencia de la propuesta actual. Guardar una edición no borra la procedencia; primera escritura manual usa manual.); motivo_respaldo: «CharField(max_length=24), blank=True, default=''» (Código: sin_configuracion/no_disponible/cuota/respuesta_invalida/plazo/capacidad/tamano; vacío si no hubo respaldo. Nunca cuerpo HTTP o error con secretos.); solicitud_propuesta: «UUIDField(null=True, blank=True)» (Token de la última reserva de propuesta; no es autorización ni fecha de expiración. Permite descartar una respuesta que ya no corresponde.); editado_por: «FK Usuario, PROTECT, obligatorio» (Último actor de cambio explícito. Invalidación derivada no se atribuye falsamente a otro usuario.); fecha_edicion: «DateTimeField, obligatorio» (Fecha de la última escritura; no funciona como expiración.). **Depende de**: T008.
- [X] T010 Completar bloque de aprobación en `informes/models.py`, restricciones literales: aprobada_por: «FK Usuario, PROTECT, null=True» (Aprobador original, distinto del emisor cuando corresponda.); nombre_aprobador: «TextField(blank=True, default='')» (Nombre profesional o identificador local congelado al aprobar; no se obtiene del perfil al emitir.); fecha_aprobacion: «DateTimeField(null=True)» (Fecha de aprobación de esa versión; no caduca por tiempo.); revision_aprobada: «PositiveBigIntegerField(null=True)» (Debe ser igual a revision cuando hay aprobación vigente.); huella_texto_aprobado: «CharField(max_length=64, blank=True, default='')» (SHA256 UTF-8 de texto_final exacto, no de su HTML ni de texto editorial solo.); huella_hechos_aprobados: «CharField(max_length=64, blank=True, default='')» (Huella de los hechos revisados.). **Depende de**: T009.
- [X] T011 Agregar constraints en `informes/models.py`: «revision >= 1»; seis campos de aprobación «todos ausentes o todos completos (tres NULL y tres textos vacíos, o tres valores no nulos y tres textos no vacíos)»; «revision_aprobada=revision» y «huella_hechos_aprobados=huella_hechos» si completos; «no puede coexistir aprobación con requiere_revision=True». Validar hashes hex de 64 caracteres/JSON/texto en servicio/formulario; Meta.default_permissions=(), sin permisos custom ni registro en admin genérico. No modificar Informe ni modelos clínicos. **Depende de**: T010.
- [X] T012 Generar y revisar únicamente `informes/migrations/0006_borradorconclusion.py` mediante `python manage.py makemigrations informes --name borradorconclusion` en contenedor aislado; verificar que 0005_envioinforme sigue siendo la hoja antes de generar; si cambió, detener y revisar el nombre/dependencia. Solo nueva tabla y constraints, sin RunPython/backfill ni cambios históricos. **Depende de**: T011.

### Validación — ejecutar solo en implementación

- [X] T013 Aplicar migración futura en PostgreSQL aislado y ejecutar `pytest informes/tests/test_borrador_conclusion.py`, `python manage.py migrate --plan` y `python manage.py makemigrations --check --dry-run`; verificar rollback/forward del esquema solo en base de pruebas y ausencia de cambios en Informe.contenido. Registrar en `.local-validacion/us102/resultados.md`. **Depende de**: T012.

### Implementación / preparación

- [X] T014 [P] Implementar guardia central reutilizable en `informes/conclusiones.py`: usuario fresco activo/autenticado, grupo exacto Bioquímicos y permiso efectivo de emisión; no confiar en cache de permisos ni is_staff/superusuario/Administradores. Exponer chequeo para servicios/UI, sin firma adicional para guardar/proponer/aprobar ni cambios en permisos actuales. **Depende de**: T005, T013.
- [X] T015 [P] Crear `informes/conclusion_ia.py` reutilizando asistente.cliente_ia.enviar y configuracion.actual sin modificar US 10.1: gramática cerrada, render local y plantilla íntegra; una llamada, ningún retry nuevo; tope operativo 64 KiB, timeout min(config.timeout, restante), presupuesto config.presupuesto, 2 workers daemon por proceso sin ORM y cola con deadline. Liberar semáforo solo al terminar worker; sin join/executor bloqueante; logs solo códigos. No prometer cancelación física ni límite de lectura HTTP bruta. **Depende de**: T006, T013.

### Validación — ejecutar solo en implementación

- [X] T016 Ejecutar en secuencia `pytest informes/tests/test_borrador_conclusion.py informes/tests/test_conclusion_autorizacion.py informes/tests/test_conclusion_adaptador.py` en PostgreSQL aislado; registrar pruebas y decisiones GET de `informes/conclusiones.py` en `.local-validacion/us102/resultados.md`; no avanzar con errores. **Depende de**: T014, T015.

---

## Phase 3: User Story 1 — Obtener un borrador con hechos verificados (P1) — MVP de revisión

**Goal**: Desde vista previa, proponer un borrador persistente con todos los hechos verificables y ausencias, sin emitir ni aprobar.

**Independent Test / Checkpoint**: Diez escenarios US1.1–US1.10 y controles mixto/duplicados/consultas; botón conectado a POST y respuesta real simulada. Verificar independientemente sin emitir; plantilla incluida por adaptador compartido.

### Tests — escribir antes del comportamiento

- [X] T017 [P] [US1] Escribir `test_dos_incumplimientos_exactos` en `informes/tests/test_conclusion_hechos.py` para **US1.1**: Cada prueba una vez; valor Decimal, unidad, límite y norma vigentes exactos; botón autorizado. Usar pytest-django y el oráculo de `specs/039-conclusion-asistida-informe/test-matrix.md`; preparar el test antes de modificar su comportamiento. **Depende de**: T016.
- [X] T018 [US1] Escribir `test_todas_evaluables_cumplen` en `informes/tests/test_conclusion_hechos.py` para **US1.2**: Cumplimiento total solo con todas evaluables; sin recomendaciones. Usar pytest-django y el oráculo de `specs/039-conclusion-asistida-informe/test-matrix.md`; preparar el test antes de modificar su comportamiento. **Depende de**: T017.
- [X] T019 [US1] Escribir `test_solo_validacion_vigente` en `informes/tests/test_conclusion_hechos.py` para **US1.3**: Historial anulado no entra ni duplica. Usar pytest-django y el oráculo de `specs/039-conclusion-asistida-informe/test-matrix.md`; preparar el test antes de modificar su comportamiento. **Depende de**: T018.
- [X] T020 [US1] Escribir `test_catalogo_no_reemplaza_validacion` en `informes/tests/test_conclusion_hechos.py` para **US1.4**: Cambiar min/max/norma del catálogo no cambia hechos normativos ni invalida por esos campos ajenos. Usar pytest-django y el oráculo de `specs/039-conclusion-asistida-informe/test-matrix.md`; preparar el test antes de modificar su comportamiento. **Depende de**: T019.
- [X] T021 [US1] Escribir `test_presentaciones_resultado` en `informes/tests/test_conclusion_hechos.py` para **US1.5**: Parametrizar Ausente/Presente, Decimal/unidad y < LD; evaluación no recalculada. Usar pytest-django y el oráculo de `specs/039-conclusion-asistida-informe/test-matrix.md`; preparar el test antes de modificar su comportamiento. **Depende de**: T020.
- [X] T022 [P] [US1] Escribir `test_proponer_no_emite_ni_valida` en `informes/tests/test_conclusion_revision.py` para **US1.6**: Propuesta solo escribe borrador; Informe, Resultado, Validacion y estado clínico sin cambios; no aprueba. Usar pytest-django y el oráculo de `specs/039-conclusion-asistida-informe/test-matrix.md`; preparar el test antes de modificar su comportamiento. **Depende de**: T016.
- [X] T023 [US1] Escribir `test_parcial_sin_vigente` en `informes/tests/test_conclusion_hechos.py` para **US1.7**: Identificar prueba sin vigente; cero fallback normativo al catálogo; otra prueba conserva hechos. Usar pytest-django y el oráculo de `specs/039-conclusion-asistida-informe/test-matrix.md`; preparar el test antes de modificar su comportamiento. **Depende de**: T021.
- [X] T024 [US1] Escribir `test_parcial_sin_limite` en `informes/tests/test_conclusion_hechos.py` para **US1.8**: Respeta evaluación sin límite comparable; no cumplimiento total. Usar pytest-django y el oráculo de `specs/039-conclusion-asistida-informe/test-matrix.md`; preparar el test antes de modificar su comportamiento. **Depende de**: T023.
- [X] T025 [US1] Escribir `test_parcial_sin_norma` en `informes/tests/test_conclusion_hechos.py` para **US1.9**: Mantener valor/límite/evaluación conocidos; advertir norma ausente. Usar pytest-django y el oráculo de `specs/039-conclusion-asistida-informe/test-matrix.md`; preparar el test antes de modificar su comportamiento. **Depende de**: T024.
- [X] T026 [US1] Escribir `test_todas_no_evaluables` en `informes/tests/test_conclusion_hechos.py` para **US1.10**: Borrador parcial identifica todas y motivos; no inventa ni afirma cumplimiento. Usar pytest-django y el oráculo de `specs/039-conclusion-asistida-informe/test-matrix.md`; preparar el test antes de modificar su comportamiento. **Depende de**: T025.
- [X] T027 [US1] Agregar `test_parcial_mixta_conserva_incumplimientos_y_ausencias` y `test_vigentes_duplicadas_no_se_eligen` en `informes/tests/test_conclusion_hechos.py`: varios incumplimientos y no evaluables simultáneos, todos una vez; si recolector recibe >1 vigente para asignación rechazar fuente ambigua, no [0]/latest/azar ni IA. Test de DB confirma constraint existente impide duplicación; test puro entrega estructura corrupta sin desactivar constraints PostgreSQL. **Depende de**: T026, T022.
- [X] T028 [P] [US1] Agregar pruebas en `informes/tests/test_conclusion_consultas.py` de consultas por conjunto para 1 y 30 pruebas, sin N+1 ni lazy reads en template; propuesta fuera de atomic/locks y sin escritura clínica; no fijar latencia BD arbitraria. **Depende de**: T016.
- [X] T029 [P] [US1] Escribir tests node:test iniciales de propuesta en `informes/tests/js/conclusion.test.cjs`: POST con CSRF/revisión/huella, mostrar borrador y advertencias sin aprobación, plantilla sin clave, rechazo de HTML login/conflicto y protección contra respuesta vieja. No crear todavía autosave/aprobación. **Depende de**: T016.

### Implementación / preparación

- [X] T030 [US1] Crear recolector en `informes/conclusion_hechos.py`: asignaciones + Resultado + solo Validacion vigente de completadas, select_related/prefetch por conjunto; nunca limites_y_evaluacion con fallback al catálogo ni reevaluar cumplimiento. Conservar IDs/fecha/Decimal/unidad/límites/norma/evaluación, ausencias sin inventar y rechazo explícito de fuentes ambiguas. **Depende de**: T027, T028.
- [X] T031 [US1] Completar `informes/conclusion_hechos.py` con JSON canónico schema='1', escalares str, fechas con zona, Decimal exacto y SHA256; orden código/pk y motivos fijo, sin Prueba.version global/minmaxnorma actuales/estado global emitido. Reusar solo formateadores de presentación (LD auxiliar huellado, no normativo); advertencias íntegras de cada no evaluable y cierres locales, sin duplicar parciales. **Depende de**: T030.
- [X] T032 [US1] Implementar proponer en `informes/conclusiones.py`: locks Estudio→Borrador→asignaciones pk→Prueba pk; fase A crea/reserva revisión/token e invalida incluso texto idéntico, conserva editorial; IA fuera de transacción; fase B reautoriza y verifica token/revisión/huella/estudio antes de guardar texto_final con advertencias. Respuesta tardía/conflicto 409 sin pisar ni crear Informe; fuente ambigua rechaza conclusión, nunca elige vigente arbitraria. **Depende de**: T031.
- [X] T033 [US1] Crear POST proponer en `informes/views_conclusiones.py`: guardia central en HTTP y servicio, CSRF, método POST, 400/403/404/409, JSON nunca cacheable; entrada revisión_esperada/huella vista, no confiar hechos/autores del navegador; respuesta incluye revisión/textos/huellas/advertencias/estado y origen/motivo seguro para respaldo. **Depende de**: T032.
- [X] T034 [US1] Registrar `informes:conclusion_proponer` en `informes/urls.py` para `/informes/estudios/<pk>/conclusion/proponer/`; preservar rutas existentes y no habilitar GET ni facultades al chat. **Depende de**: T033.
- [X] T035 [US1] Crear integración mínima de propuesta en `informes/static/informes/conclusion.js`: enlazar botón Proponer, enviar CSRF/revisión/huella al POST, renderizar editorial/advertencias como texto, estado de borrador y aviso plantilla; manejar conflicto/login sin marcar éxito ni aprobación. No esperar US2 para conectar el botón con el servicio. **Depende de**: T034, T029.
- [X] T036 [US1] Integrar lectura inicial revisión 0/huella y botón Proponer conclusión en `informes/views.py` y `informes/templates/informes/vista_previa.html`; reutilizar componentes/confirmación y mensaje; mostrar resultado como borrador sin aprobación, hechos y advertencias protegidas, plantilla disponible aun sin clave. Consulta general conserva autorización existente; no crear borrador por abrir página. **Depende de**: T035.

### Validación — ejecutar solo en implementación

- [X] T037 [US1] Ejecutar `pytest informes/tests/test_conclusion_hechos.py::test_dos_incumplimientos_exactos informes/tests/test_conclusion_hechos.py::test_todas_evaluables_cumplen informes/tests/test_conclusion_hechos.py::test_solo_validacion_vigente informes/tests/test_conclusion_hechos.py::test_catalogo_no_reemplaza_validacion informes/tests/test_conclusion_hechos.py::test_presentaciones_resultado informes/tests/test_conclusion_revision.py::test_proponer_no_emite_ni_valida informes/tests/test_conclusion_hechos.py::test_parcial_sin_vigente informes/tests/test_conclusion_hechos.py::test_parcial_sin_limite informes/tests/test_conclusion_hechos.py::test_parcial_sin_norma informes/tests/test_conclusion_hechos.py::test_todas_no_evaluables informes/tests/test_conclusion_hechos.py::test_parcial_mixta_conserva_incumplimientos_y_ausencias informes/tests/test_conclusion_hechos.py::test_vigentes_duplicadas_no_se_eligen informes/tests/test_conclusion_consultas.py` y `node --test informes/tests/js/conclusion.test.cjs`; verificar propuesta conectada/persistente y cero mutaciones clínicas. Registrar nombres/resultados exactos en `.local-validacion/us102/resultados.md`. **Depende de**: T036.

---

## Phase 4: User Story 2 — Editar y aprobar expresamente la incorporación (P1)

**Goal**: Guardar y recuperar borrador compartido, aprobar versión exacta y emitir opcionalmente solo si continúa vigente.

**Independent Test / Checkpoint**: Quince escenarios US2.1–US2.15, cuatro acciones autorizadas independientemente, guardado entre personas, aprobación sin firma adicional, GET derivado, conflictos y recuperación. La copia ya incluye fragmento para emisión; todos los medios se completan en US3.

### Tests — escribir antes del comportamiento

- [X] T038 [P] [US2] Escribir `test_emite_texto_reescrito_aprobado` en `informes/tests/test_conclusion_emision.py` para **US2.1**: Copia texto final confirmado, no propuesta inicial. Usar pytest-django y el oráculo de `specs/039-conclusion-asistida-informe/test-matrix.md`; preparar el test antes de modificar su comportamiento. **Depende de**: T037.
- [X] T039 [US2] Escribir `test_emitir_sin_conclusion` en `informes/tests/test_conclusion_emision.py` para **US2.2**: Parametrizar sin fila, borrador, edición, aprobación invalidada; sin clave conclusion y reglas existentes. Usar pytest-django y el oráculo de `specs/039-conclusion-asistida-informe/test-matrix.md`; preparar el test antes de modificar su comportamiento. **Depende de**: T038.
- [X] T040 [P] [US2] Escribir `test_propuesta_no_aprueba` en `informes/tests/test_conclusion_revision.py` para **US2.3**: Bloque de seis campos ausente tras propuesta correcta. Usar pytest-django y el oráculo de `specs/039-conclusion-asistida-informe/test-matrix.md`; preparar el test antes de modificar su comportamiento. **Depende de**: T037.
- [X] T041 [US2] Escribir `test_sin_grupo_ni_permiso_denegado` en `informes/tests/test_conclusion_revision.py` para **US2.4**: UI y POST proponer/aprobar denegados, consulta previa conservada. Usar pytest-django y el oráculo de `specs/039-conclusion-asistida-informe/test-matrix.md`; preparar el test antes de modificar su comportamiento. **Depende de**: T040.
- [X] T042 [US2] Escribir `test_sin_sesion_o_inactivo_denegado` en `informes/tests/test_conclusion_revision.py` para **US2.5**: Ambas acciones, sin escritura; redirección de sesión no es éxito JSON. Usar pytest-django y el oráculo de `specs/039-conclusion-asistida-informe/test-matrix.md`; preparar el test antes de modificar su comportamiento. **Depende de**: T041.
- [X] T043 [US2] Escribir `test_solo_grupo_denegado` en `informes/tests/test_conclusion_revision.py` para **US2.6**: Quitar permiso efectivo incluso al grupo en fixture aislada; no concederlo automáticamente. Usar pytest-django y el oráculo de `specs/039-conclusion-asistida-informe/test-matrix.md`; preparar el test antes de modificar su comportamiento. **Depende de**: T042.
- [X] T044 [US2] Escribir `test_solo_permiso_denegado` en `informes/tests/test_conclusion_revision.py` para **US2.7**: Proponer/aprobar denegados, emitir sin conclusión sigue autorizado con firma. Usar pytest-django y el oráculo de `specs/039-conclusion-asistida-informe/test-matrix.md`; preparar el test antes de modificar su comportamiento. **Depende de**: T043.
- [X] T045 [US2] Escribir `test_grupo_y_permiso_autorizados` en `informes/tests/test_conclusion_revision.py` para **US2.8**: Ambas acciones permitidas; otros permisos sin cambios. Usar pytest-django y el oráculo de `specs/039-conclusion-asistida-informe/test-matrix.md`; preparar el test antes de modificar su comportamiento. **Depende de**: T044.
- [X] T046 [US2] Escribir `test_edicion_invalida_aprobacion` en `informes/tests/test_conclusion_revision.py` para **US2.9**: Texto nuevo, revisión mayor y aprobación nula; emisión con versión antigua rechazada. Usar pytest-django y el oráculo de `specs/039-conclusion-asistida-informe/test-matrix.md`; preparar el test antes de modificar su comportamiento. **Depende de**: T045.
- [X] T047 [US2] Escribir `test_regeneracion_identica_invalida` en `informes/tests/test_conclusion_revision.py` para **US2.10**: Invalidar en reserva, también si respuesta repite texto. Usar pytest-django y el oráculo de `specs/039-conclusion-asistida-informe/test-matrix.md`; preparar el test antes de modificar su comportamiento. **Depende de**: T046.
- [X] T048 [US2] Escribir `test_cambio_fuentes_impide_conclusion_obsoleta` en `informes/tests/test_conclusion_emision.py` para **US2.11**: Parametrizar Resultado/fecha, vigente nueva, ausencia y LD auxiliar; invalidación persistida; sin conclusión aún posible si estudio listo. Usar pytest-django y el oráculo de `specs/039-conclusion-asistida-informe/test-matrix.md`; preparar el test antes de modificar su comportamiento. **Depende de**: T039.
- [X] T049 [US2] Escribir `test_borrador_persiste_al_volver_y_recargar` en `informes/tests/test_conclusion_revision.py` para **US2.12**: Guardado por POST, nueva consulta y nueva sesión del mismo autorizado recuperan texto no aprobado. Complementar prueba JS de flush/recarga. Usar pytest-django y el oráculo de `specs/039-conclusion-asistida-informe/test-matrix.md`; preparar el test antes de modificar su comportamiento. **Depende de**: T047.
- [X] T050 [US2] Escribir `test_recarga_preserva_aprobacion_vigente` en `informes/tests/test_conclusion_revision.py` para **US2.13**: Misma revisión/aprobación si sin cambios; invalidada no revive al restaurar valores. Usar pytest-django y el oráculo de `specs/039-conclusion-asistida-informe/test-matrix.md`; preparar el test antes de modificar su comportamiento. **Depende de**: T049.
- [X] T051 [US2] Escribir `test_reaprobacion_explicita_fuentes_actuales` en `informes/tests/test_conclusion_emision.py` para **US2.14**: Conflicto obliga revisar texto final y fuentes; solo nueva aprobación emite. Usar pytest-django y el oráculo de `specs/039-conclusion-asistida-informe/test-matrix.md`; preparar el test antes de modificar su comportamiento. **Depende de**: T048.
- [X] T052 [US2] Escribir `test_editar_aprobar_parcial_conserva_advertencias` en `informes/tests/test_conclusion_emision.py` para **US2.15**: Advertencias fuera de textarea, inalterables desde cliente, snapshot las contiene una vez. Usar pytest-django y el oráculo de `specs/039-conclusion-asistida-informe/test-matrix.md`; preparar el test antes de modificar su comportamiento. **Depende de**: T051.
- [X] T053 [P] [US2] Agregar matriz independiente para guardar/proponer/aprobar/emitir con conclusión en `informes/tests/test_conclusion_autorizacion.py`, tanto servicio como HTTP, CSRF real y GET 405; revocar permiso/grupo/desactivar durante IA; solo permiso emite sin conclusión con firma. Aprobación sin firma adicional permitida; emitir sin firma/matrícula sigue fallando. **Depende de**: T037.
- [X] T054 [US2] Agregar `test_get_invalida_solo_borrador_existente`, `test_get_repetido_no_escribe` y `test_borrador_compartido_entre_bioquimicos` en `informes/tests/test_conclusion_revision.py`: GET autorizado persiste invalidez observada sin tocar texto editorial/Resultado/Validacion/Informe, sin fila no crea, usuario común no escribe ni recibe borrador; otro autorizado recupera guardado; sin cache, posterior emisión obsoleta rechazada y A→B→A detectado no revive. **Depende de**: T052, T050.
- [X] T055 [P] [US2] Escribir carreras en `informes/tests/test_conclusion_concurrencia.py`: dos guardados/aprobaciones, propuestas fuera de orden, edición durante IA, revocación y proceso interrumpido tras reserva. PostgreSQL real, transaction=True, conexiones independientes, close_old_connections y Event/Barrier; cero mocks de locks y cero sleeps de sincronización. **Depende de**: T037.
- [X] T056 [P] [US2] Ampliar `informes/tests/js/conclusion.test.cjs` con node:test: confirmación al habilitar edición, autosave serial, barrera antes de Volver/proponer/aprobar/emitir, input deshabilita aprobación, 409 conserva texto local, respuesta fuera de orden, recuperación por recarga sin confundir ack, storage deshabilitado, logout/cambio sesión limpia, HTML login no es éxito y errores visibles. **Depende de**: T037.

### Implementación / preparación

- [X] T057 [US2] Extender `informes/forms.py` con revisión_esperada entero >=0 (0 solo sin fila), huellas hex64, texto editorial libre sin máximo nuevo/strip/normalización Unicode, CRLF→LF y rechazo NUL; aprobación recibe revisión/huellas/confirmación, no texto nuevo ni autor/hechos. Mensajes/help_text españoles. **Depende de**: T053, T054, T055, T056.
- [X] T058 [US2] Implementar guardar/reconciliar en `informes/conclusiones.py`: fuente actual antes de revisión cliente; huella distinta actualiza metadatos/advertencias y requiere_revision, preserva editorial, vacía seis campos/token y aumenta revisión; 409 confirma invalidación sin rollback accidental. Guardar edición invalida, reintento idéntico solo no-op con revisión vigente; fila compartida recuperable sin expiración. **Depende de**: T057.
- [X] T059 [US2] Implementar aprobar en `informes/conclusiones.py`: misma revisión y hashes vistos, fuentes actuales bajo locks, confirmación expresa y texto_final no vacío; aumentar revisión, congelar aprobador/nombre/fecha, revision_aprobada y hashes; limpiar token/requiere_revision. No firmar ni emitir; parcial mantiene advertencias; reaprobar explícitamente, nunca revivir al coincidir valores. **Depende de**: T058.
- [X] T060 [US2] Integrar en `informes/views.py` carga de borrador y reconciliación derivada de GET según decisión: guardia conjunta, no crear fila, no-op si vigente, persistir solo invalidez derivada bajo locks/no caché y no tocar datos clínicos. Fuentes ambiguas/obsoletas deshabilitan incorporación; consulta general y emisión sin conclusión permanecen. **Depende de**: T059.
- [X] T061 [US2] Agregar guardar/aprobar en `informes/views_conclusiones.py` y `informes/urls.py`, nombres conclusion_guardar/conclusion_aprobar y rutas `/informes/estudios/<pk>/conclusion/guardar/` y aprobar/; misma guardia en servicio y vista, CSRF/POST, validación, respuestas sin cache y 409 con estado actual, sin confiar hashes del cliente como autoridad. **Depende de**: T060.
- [X] T062 [US2] Extender `informes/contenido.py` con parámetro opcional conclusion=None y copiar fragmento autosuficiente: texto_final exacto con advertencias, hechos/ausencias, revisión/huellas/origen y aprobador/nombre congelados/fecha; todos escalares str. Sin conclusión omitir clave, sin cambiar helpers/fallback anteriores ni contenido histórico; ninguna dependencia viva para representar conclusión emitida. **Depende de**: T061.
- [X] T063 [US2] Extender `informes/servicios.py` con incluir_conclusion=False y revision_conclusion=None: camino sin conclusión idéntico; con conclusión exige guardia conjunta y aprobación/revisión/huellas/fuentes bajo mismos locks y transacción de emisión. Advisory numeración después de locks uniformes, copiar texto sin reconstruir/aprobar; conflicto confirma invalidez sin Informe parcial ni autoomisión. Conservar firma/matrícula y permitir otro emisor autorizado. **Depende de**: T062.
- [X] T064 [US2] Integrar incluir_conclusion explícito y revisión aprobada en `informes/views.py`, manteniendo confirmación y HTML del flujo generar; opción ausente=false conserva clientes anteriores. 409 explica obsolescencia sin emitir; acción separada Emitir sin conclusión nunca depende de IA/validez del borrador. Rechazar manipulación directa de opción/revisión. **Depende de**: T063.
- [X] T065 [US2] Crear `informes/templates/informes/_editor_conclusion.html` e incluir desde vista_previa.html: confirmación para habilitar edición/autosave, textarea editorial, bloque protegido y texto_final exacto antes de aprobar, acciones separadas, estado sin guardar/conflicto/aprobado y opción de emisión; templates/ui/campo.html con help_text y framework de mensajes; ocultar acciones no autorizadas. **Depende de**: T064.
- [X] T066 [US2] Ampliar `informes/static/informes/conclusion.js` según contrato: autosave serial/ack y barrera de navegación/acciones, revisión optimista y descarte tardío, protección de advertencias. Recovery mínimo sessionStorage pestaña/estudio/usuario/huella de sesión, sin hechos/contactos/tokens; limpiar ack/logout/cambio sesión/pérdida autorización, no inventar eventos en usuarios/sesion.js; nunca aprobación desde storage ni éxito por HTML login. **Depende de**: T065.

### Validación — ejecutar solo en implementación

- [X] T067 [US2] Ejecutar en secuencia `pytest informes/tests/test_conclusion_revision.py`, `pytest informes/tests/test_conclusion_autorizacion.py`, `pytest informes/tests/test_conclusion_emision.py`, `pytest informes/tests/test_conclusion_concurrencia.py` y `node --test informes/tests/js/conclusion.test.cjs`, con pytest sobre PostgreSQL aislado usando `docker compose -p aqualab-us102 -f $us102Compose run --rm web` como prefijo de cada comando pytest. Verificar US2.1–US2.15, guardado por usuario A/lectura por B, aprobación sin firma y conflicto persistente. Registrar comandos/resultados exactos en `.local-validacion/us102/resultados.md`. **Depende de**: T066.

---

## Phase 5: User Story 3 — Conservar el texto aprobado en todos los medios (P1)

**Goal**: Mostrar la misma copia inmutable en consulta/PDF/impresión/correo sin alterar históricos ni depender de IA.

**Independent Test / Checkpoint**: Siete escenarios US3.1–US3.7, carreras de emisión y comparación de texto en todas las salidas; dos personas distintas para aprobar/emitir, PDF real sintético.

### Tests — escribir antes del comportamiento

- [X] T068 [US3] Escribir `test_snapshot_texto_y_trazabilidad` en `informes/tests/test_conclusion_emision.py` para **US3.1**: IDs estudio/pruebas/vigentes, ausencias, hashes, revisión y aprobador; todos escalares str. Usar pytest-django y el oráculo de `specs/039-conclusion-asistida-informe/test-matrix.md`; preparar el test antes de modificar su comportamiento. **Depende de**: T067.
- [X] T069 [US3] Escribir `test_snapshot_no_cambia_con_origen` en `informes/tests/test_conclusion_emision.py` para **US3.2**: Cambiar catálogo/perfil tras emisión: JSON y texto de copia idénticos. Usar pytest-django y el oráculo de `specs/039-conclusion-asistida-informe/test-matrix.md`; preparar el test antes de modificar su comportamiento. **Depende de**: T068.
- [X] T070 [US3] Escribir `test_misma_conclusion_todos_los_medios` en `informes/tests/test_conclusion_emision.py` para **US3.3**: Consultar, imprimir, HTML entregado a WeasyPrint, PDF real, correo txt/HTML y adjunto con idéntico texto; solo maquetación varía. Usar pytest-django y el oráculo de `specs/039-conclusion-asistida-informe/test-matrix.md`; preparar el test antes de modificar su comportamiento. **Depende de**: T069.
- [X] T071 [US3] Escribir `test_salidas_y_reenvio_no_llaman_ia` en `informes/tests/test_conclusion_emision.py` para **US3.4**: Dobles que fallan si se invoca IA; conservar destinatario actual, confirmación e idempotencia de envío. Usar pytest-django y el oráculo de `specs/039-conclusion-asistida-informe/test-matrix.md`; preparar el test antes de modificar su comportamiento. **Depende de**: T070.
- [X] T072 [US3] Escribir `test_historicos_sin_conclusion_intactos` en `informes/tests/test_conclusion_emision.py` para **US3.5**: Snapshot sin nueva clave y renders antes/después sin bloque/título vacío; ninguna escritura retrospectiva. Usar pytest-django y el oráculo de `specs/039-conclusion-asistida-informe/test-matrix.md`; preparar el test antes de modificar su comportamiento. **Depende de**: T071.
- [X] T073 [US3] Escribir `test_emitido_rechaza_mutar_conclusion` en `informes/tests/test_conclusion_emision.py` para **US3.6**: Todos los POST nuevos y guardias de modelo/copia; sin mutación de Informe. Usar pytest-django y el oráculo de `specs/039-conclusion-asistida-informe/test-matrix.md`; preparar el test antes de modificar su comportamiento. **Depende de**: T072.
- [X] T074 [US3] Escribir `test_otro_bioquimico_emite` en `informes/tests/test_conclusion_emision.py` para **US3.7**: Dos personas reales distintas; aprobador original congelado y emisor distinto. Usar pytest-django y el oráculo de `specs/039-conclusion-asistida-informe/test-matrix.md`; preparar el test antes de modificar su comportamiento. **Depende de**: T073.
- [X] T075 [P] [US3] Ampliar `informes/tests/test_conclusion_concurrencia.py`: edición/revalidación/recálculo vs emitir, cambio LD/identidad vs snapshot, dos emisiones y rollback; PostgreSQL/conexiones/transacciones reales, orden locks y advisory, cero copia parcial y 409 no revierte invalidación; verificar datos/IDs completos en snapshot. **Depende de**: T067.
- [X] T076 [US3] Agregar a `informes/tests/test_conclusion_emision.py` tests de escaping/Unicode/LF/texto extenso, advertencias una vez, mismo string en documento pantalla/impreso/correo txt/HTML y entrada a WeasyPrint, PDF real y adjunto; histórico sin clave no agrega título/bloque ni writes. No instalar parser nuevo para suplir revisión visual. **Depende de**: T074.

### Implementación / preparación

- [X] T077 [US3] Crear `informes/templates/informes/_conclusion.html` que represente únicamente snapshot.conclusion.texto escapado, saltos preservados y sin duplicar advertencias; condición de ausencia no produce encabezado/bloque. No usar safe ni reconstruir desde borrador/fuentes/IA. **Depende de**: T076, T075.
- [X] T078 [US3] Incluir parcial opcional en `informes/templates/informes/documento.html`; revisar consulta/ver y vista previa sin confundir borrador no aprobado con copia emitida. Mantener toda salida histórica sin nueva clave y contratos existentes. **Depende de**: T077.
- [X] T079 [US3] Incluir mismo parcial en `informes/templates/informes/documento_impreso.html` y ajustar solo si hace falta `static/css/informe.css` para saltos y conclusión multipágina sin recortes; `informes/pdf.py`/impreso.html continúan leyendo copia, sin IA ni nuevo parámetro. **Depende de**: T078.
- [X] T080 [US3] Agregar snapshot.conclusion.texto en `informes/templates/informes/correos/informe_cuerpo.txt` y parcial escapado en informe_cuerpo.html; sin resumir ni agregar advertencias dos veces; conservar asunto/destinatario actual/confirmación/idempotencia/PDF adjunto de `informes/envios.py`, sin modificar ese servicio innecesariamente. **Depende de**: T079.

### Validación — ejecutar solo en implementación

- [X] T081 [US3] Ejecutar en secuencia `pytest informes/tests/test_conclusion_emision.py informes/tests/test_conclusion_concurrencia.py`; comparar copia/todas las salidas y reenviar con IA bloqueada, inspeccionar PDF real sintético y ausencia de mutaciones históricas. Registrar evidencia preliminar en `.local-validacion/us102/resultados.md`. **Depende de**: T080.

---

## Phase 6: User Story 4 — Continuar ante fallos o ausencia de IA (P1)

**Goal**: Integrar y demostrar resiliencia completa con plantilla, edición/aprobación y salida sin conclusión.

**Independent Test / Checkpoint**: Seis escenarios US4.1–US4.6 y fallos/saturación/respuestas tardías con dobles controlados; mismos hechos, avisos seguros y cero IA real. El adaptador básico completo se construye antes porque US1 lo necesita; aquí se verifica el recorrido de fallo integral.

### Tests — escribir antes del comportamiento

- [X] T082 [US4] Escribir `test_timeout_total_ofrece_plantilla` en `informes/tests/test_conclusion_ia.py` para **US4.1**: Worker controlado sin responder, deadline acotado y respaldo; sin aprobación, sin locks externos retenidos. Usar pytest-django y el oráculo de `specs/039-conclusion-asistida-informe/test-matrix.md`; preparar el test antes de modificar su comportamiento. **Depende de**: T081.
- [X] T083 [US4] Escribir `test_fallos_proveedor_ofrecen_plantilla` en `informes/tests/test_conclusion_ia.py` para **US4.2**: Parametrizar red, cuota, credenciales y error proveedor; aviso seguro, mismos hechos, emisión sin conclusión disponible. Usar pytest-django y el oráculo de `specs/039-conclusion-asistida-informe/test-matrix.md`; preparar el test antes de modificar su comportamiento. **Depende de**: T082.
- [X] T084 [US4] Escribir `test_sin_configuracion_ofrece_plantilla` en `informes/tests/test_conclusion_ia.py` para **US4.3**: No llamar transporte; borrador editable y emisión no depende de clave IA. Usar pytest-django y el oráculo de `specs/039-conclusion-asistida-informe/test-matrix.md`; preparar el test antes de modificar su comportamiento. **Depende de**: T083.
- [X] T085 [US4] Escribir `test_respuesta_invalida_no_inventa` en `informes/tests/test_conclusion_ia.py` para **US4.4**: Vacío/JSON inválido, campos extra, texto inventado, refs omitidas/duplicadas/extra y cierres incompatibles: respaldo completo. Usar pytest-django y el oráculo de `specs/039-conclusion-asistida-informe/test-matrix.md`; preparar el test antes de modificar su comportamiento. **Depende de**: T084.
- [X] T086 [US4] Escribir `test_plantilla_todas_cumplen` en `informes/tests/test_conclusion_ia.py` para **US4.5**: Cierre correcto, edición y aprobación explícita mediante endpoints. Usar pytest-django y el oráculo de `specs/039-conclusion-asistida-informe/test-matrix.md`; preparar el test antes de modificar su comportamiento. **Depende de**: T085.
- [X] T087 [US4] Escribir `test_plantilla_parcial_mismos_hechos` en `informes/tests/test_conclusion_ia.py` para **US4.6**: Parametrizar tres ausencias aprobadas; mismos datos/advertencias y recorrido editar/aprobar/emitir o sin conclusión. Usar pytest-django y el oráculo de `specs/039-conclusion-asistida-informe/test-matrix.md`; preparar el test antes de modificar su comportamiento. **Depende de**: T086.
- [X] T088 [US4] Agregar en `informes/tests/test_conclusion_ia.py` integración de saturación/deadline y respuesta tardía: worker sin ORM, dos ocupados→tercera plantilla inmediata, liberar solo al acabar, revocación o edición durante espera→409 sin sobrescritura ni aprobación; payload adversarial/exceso→respaldo completo; emisión sin conclusión continúa. Dobles/Event y limpiar workers de test. **Depende de**: T087.
- [X] T089 [P] [US4] Ampliar `informes/tests/js/conclusion.test.cjs` con aviso de respaldo seguro, plantilla normal/parcial editable sin autoaprobación, fin del estado de espera en timeout/error, conflicto tardío y emisión sin conclusión accesible; no mostrar cuerpo HTTP/configuración sensible. **Depende de**: T081.

### Implementación / preparación

- [X] T090 [US4] Completar integración de origen/motivo y mensajes de respaldo en `informes/views_conclusiones.py` y `informes/templates/informes/_editor_conclusion.html`; mismos hechos del adaptador y warnings, ningún dato técnico/secretos en mensajes; fallo IA no deshabilita emisión sin conclusión. Ajustar únicamente la conexión con el adaptador ya probado, no duplicar transporte ni modificar US 10.1. **Depende de**: T088, T089.
- [X] T091 [US4] Completar estados de respaldo/fin de espera en `informes/static/informes/conclusion.js`, manteniendo guardado/revisión y edición/aprobación explícitas; no instalar respuesta vieja ni convertir error de autorización/conflicto en respaldo sobre datos ajenos. Sin cambiar las reglas de plantilla/gramática ya compartidas. **Depende de**: T090.

### Validación — ejecutar solo en implementación

- [X] T092 [US4] Ejecutar `pytest informes/tests/test_conclusion_adaptador.py informes/tests/test_conclusion_ia.py` y `node --test informes/tests/js/conclusion.test.cjs`, secuencialmente; demostrar seis escenarios US4 con proveedor simulado y emisión con plantilla aprobada o sin conclusión. Registrar en `.local-validacion/us102/resultados.md`. **Depende de**: T091.

---

## Phase 7: Polish — validación integral y revisión humana

**Goal**: Cerrar integración, CI y evidencia sobre el árbol final sin publicar.

**Independent Test / Checkpoint**: Suite PostgreSQL, Node 20, lint, esquema/CSS y revisión humana de medios; estados se completan únicamente con evidencia real.

### Implementación / preparación

- [X] T093 Agregar `informes/tests/js` a la lista explícita node --test de `.github/workflows/ci.yml`, conservar Node 20/PostgreSQL 16 y pasos existentes; verificar inclusión real de conclusion.test.cjs, sin paquetes npm ni cambios de otras features. **Depende de**: T092.

### Validación — ejecutar solo en implementación

- [X] T094 Ejecutar `ruff check .`, `ruff format --check .` y `python manage.py check` en contenedor aislado mediante comandos de `specs/039-conclusion-asistida-informe/quickstart.md`; registrar resultados en `.local-validacion/us102/resultados.md` y corregir solo alcance US10.2. **Depende de**: T093.
- [X] T095 Ejecutar `python manage.py makemigrations --check --dry-run` y `python manage.py migrate --plan` tras aplicar única migración de informes; inspeccionar `informes/migrations/0006_borradorconclusion.py`, ausencia de backfill/permisos nuevos/dependencias y copia histórica intacta; registrar en `.local-validacion/us102/resultados.md`. **Depende de**: T094.
- [X] T096 Compilar/verificar `static/css/aqualab.css` con Tailwind v4.3.3 existente: `tailwindcss -i static/src/aqualab.css -o static/css/aqualab.css --minify`; comprobar hash repetible y coherencia con templates, revisar `static/css/informe.css`, sin instalar herramientas; registrar en `.local-validacion/us102/resultados.md`. **Depende de**: T095.
- [X] T097 Ejecutar Node 20 y `node --test usuarios/tests/js config/tests/js estudios/tests/js pruebas/tests/js asistente/tests/js informes/tests/js`; si Node 24 local requiere archivos explícitos usar variante rg del quickstart y registrar diferencia, sin afirmar paridad CI hasta validar Node 20. Evidencia en `.local-validacion/us102/resultados.md`. **Depende de**: T096.
- [X] T098 Ejecutar `pytest` completo una vez sobre PostgreSQL aislado y árbol final, en secuencia después de migraciones/otras suites; incluir todos los tests de feature, informes/asistente/estudios y controles de consultas, concurrencia y permisos. Usar comandos de `specs/039-conclusion-asistida-informe/quickstart.md`; registrar 38 escenarios/nombres reales y resultados en `.local-validacion/us102/resultados.md`, sin Groq/correo real ni conteos heredados. **Depende de**: T097.
- [X] T099 Solicitar revisión humana de recorridos de `specs/039-conclusion-asistida-informe/quickstart.md` después de preparar evidencia sintética: editor/recarga/borrador compartido, parcial mixto, conflicto, otro emisor, todos los formatos y PDF multipágina/históricos. Registrar aprobación o incidencias reales en `.local-validacion/us102/resultados.md`; no autodeclarar aprobación profesional/equipo. **Depende de**: T098.

### Implementación / preparación

- [X] T100 Actualizar exclusivamente evidencia de implementación en `specs/039-conclusion-asistida-informe/quickstart.md` y estados de `specs/039-conclusion-asistida-informe/tasks.md` con comandos, árbol/SHA probado, 38/38 y controles realmente ejecutados; conservar requisitos/escenarios, decisiones y Constitution. Clave Jira propia/revisión de PR siguen pendientes hasta información real, sin inventar. **Depende de**: T099.

### Validación — ejecutar solo en implementación

- [X] T101 Auditar `git diff --check`, `git status --short --untracked-files=all` y diff de alcance; verificar que `.env`, bases, logs, `.local-validacion/us102/`, capturas y secretos no se preparen, sin cambios a US10.1/otras historias/Constitution. Registrar conclusión en `specs/039-conclusion-asistida-informe/tasks.md`; detenerse sin commit/push/PR/merge, que requieren autorización aparte. **Depende de**: T100.

---

## Dependencies & Execution Order

### Phase Dependencies

`Setup → Foundational → US1 → US2 → US3 → US4 → Polish` es el orden seguro por defecto. Las historias tienen dependencias reales: propuesta requiere persistencia y adaptador; aprobación requiere propuesta/guardado; salidas requieren copia emitida aprobada; pruebas de resiliencia integral requieren el recorrido completo. No presentar los cuatro recorridos como desplegables sin integración.

- Setup: T001 → T002 → T003.
- Foundational: T004/T005/T006 parten de T003; T007 fija límite técnico. Modelo T008→T009→T010→T011→T012→T013; guardia T014 y adaptador T015 → T016.
- US1: barrera T016; tests de cada archivo en serie, otros archivos en paralelo; hechos→huella→reserva/instalación→POST→rutas→JS→UI→T037.
- US2: barrera T037; tests→forms→guardar→aprobar→GET→POST/rutas→fragmento→emisión→view→editor→JS→T067.
- US3: barrera T067; tests de medios y carreras→parcial→pantalla→impresión→correo→T081. La trazabilidad/copia ya se integra en US2 porque es necesaria para sus escenarios; aquí se valida y representa en todos los medios, sin una segunda implementación de emisión.
- US4: barrera T081; tests integrales del respaldo→integración de avisos/estados→T092; no duplicar adaptador creado en T015.
- Polish: T093→T094→T095→T096→T097→T098→T099→T100→T101.

Las listas «Depende de» de cada tarea son el grafo vinculante; todos sus IDs existen y apuntan hacia atrás. Un test de aceptación se puede escribir antes de que exista su módulo y se pone verde al completar su responsable de implementación. No ejecutar migraciones, suites PostgreSQL ni suite integral en paralelo sobre una base compartida; solo escritura de archivos disjuntos tiene oportunidades marcadas. Si se modifica un archivo después de validarlo, repetir únicamente checks afectados y la regresión necesaria sobre el árbol final.

### Parallel Examples por recorrido

| Ámbito | Ejemplo real tras satisfacer dependencias | Límite |
|---|---|---|
| Foundational | T004, T005, T006 en archivos de tests separados; después T014 y T015 en módulos separados | Modelo/migración y ejecución de BD secuenciales. |
| US1 | T017 (hechos), T022 (revisión), T028 (consultas), T029 (JS) | Continuaciones dentro de test_conclusion_hechos.py o revision.py en serie. |
| US2 | T038 (emisión), T040 (revisión), T053 (autorización), T055 (concurrencia), T056 (JS) | Esperar T037; después todos los tests del mismo archivo se serializan. |
| US3 | T068 (emisión) y T075 (concurrencia) | T075 está marcado [P]; no paralelizar tests que escriben el mismo archivo de emisión. |
| US4 | T082 (IA) y T089 (JS) | T089 está marcado [P]; pruebas IA del mismo archivo en serie. |

No se solicita ni se ejecuta delegación por agentes en este workflow. Paralelismo es una opción de ejecución futura por archivos, no paralelismo automático de bases/suites.

## Decisiones técnicas de revisión

1. **GET de vista previa**: conservar lo diseñado, no crear un endpoint nuevo durante tasks. Solo usuario conjunto y borrador existente permiten materializar invalidez ya ocurrida; no hay aprobación positiva, edición editorial ni escritura clínica. Sin cambios es no-op, sin fila no crear, empleado común no escribe. El GET nunca es la garantía exclusiva: cada POST y emisión con conclusión revalida bajo locks. Respuestas no cacheables; invalidez observada queda persistida y no revive al restaurar valores. T007/T054/T060 documentan, prueban e integran. Revisión humana de esta decisión antes de implementar, por efecto lateral de GET, sin decisión funcional nueva.
2. **Validaciones duplicadas**: la BD ya tiene unicidad de vigente; no desactivar esa protección para fabricar la prueba. Probar su constraint real y el recolector puro con colección ambigua. Nunca escoger [0]/última/azar: conflicto técnico de integridad, sin IA ni nueva aprobación; invalidar aprobación existente si se detecta, conservar referencia anterior como obsoleta y no emitirla. No reparar historia ni reinterpretar como cumplimiento. No cambiar reglas de emisión sin conclusión (T027/T007/T030).
3. **Fuentes y huella**: vigente aporta evaluación/límites/norma; Resultado valor/unidad/fecha. LD actual solo presentación auxiliar huellada, no norma histórica; limitación A→B→A auxiliar no observado permanece explícita. No Prueba.version global ni catálogo para suplir ausencias.
4. **Persistencia y permisos**: un borrador compartido, revisión monotónica y seis campos de aprobación completos/nulos. Las cuatro operaciones nuevas exigen usuario activo/autenticado + grupo Bioquímicos + permiso efectivo; aprobar sin firma adicional, emitir con firma/matrícula existentes. Otro emisor autorizado conserva al aprobador original.
5. **Emisión**: validar/copiar dentro de una transacción, locks Estudio→Borrador→asignaciones pk→Prueba pk y advisory de numeración después. Un conflicto confirma invalidación sin Informe parcial; no lanzar dentro de atomic una excepción que la revierta. Sin conclusión no consultar validez de borrador ni IA.
6. **Proveedor**: redacción restringida, hechos locales, plantilla completa. Worker no cancela físicamente lectura HTTP, y cliente compartido no limita bytes brutos; capacidad 2 evita crecimiento de hilos, sin afirmar que corrige esa limitación de transporte. Recovery local no equivale a ack de BD. Verificar/registrar límites y riesgos; no cambiar US10.1 como solución improvisada.

No quedan decisiones funcionales abiertas. Revisión de GET, evidencia de carreras, PDF extenso y compatibilidad Node 20 son controles técnicos/humanos obligatorios; la clave Jira real sigue pendiente administrativa. Si alguna solución exige variar el diseño aprobado, detener esa modificación y presentar evidencia para revisión, sin alterar requisitos unilateralmente.

## Cobertura de aceptación — 38 escenarios

Cada fila vincula el escenario al test pytest-django concreto y su tarea. La ruta y oráculo completos constan en la tarea y en [test-matrix](test-matrix.md). Todos los tests de UI tienen además backend; JS no reemplaza pytest.

| Escenario | Tarea de test | Test concreto | Responsables funcionales | Prerrequisito de escritura |
|---|---|---|---|---|
| US1.1 | T017 | `informes/tests/test_conclusion_hechos.py::test_dos_incumplimientos_exactos` | T030, T031, T032, T036 | T016 |
| US1.2 | T018 | `informes/tests/test_conclusion_hechos.py::test_todas_evaluables_cumplen` | T030, T031, T032, T036 | T017 |
| US1.3 | T019 | `informes/tests/test_conclusion_hechos.py::test_solo_validacion_vigente` | T030, T031, T032, T036 | T018 |
| US1.4 | T020 | `informes/tests/test_conclusion_hechos.py::test_catalogo_no_reemplaza_validacion` | T030, T031, T032, T036 | T019 |
| US1.5 | T021 | `informes/tests/test_conclusion_hechos.py::test_presentaciones_resultado` | T030, T031, T032, T036 | T020 |
| US1.6 | T022 | `informes/tests/test_conclusion_revision.py::test_proponer_no_emite_ni_valida` | T030, T031, T032, T036 | T016 |
| US1.7 | T023 | `informes/tests/test_conclusion_hechos.py::test_parcial_sin_vigente` | T030, T031, T032, T036 | T021 |
| US1.8 | T024 | `informes/tests/test_conclusion_hechos.py::test_parcial_sin_limite` | T030, T031, T032, T036 | T023 |
| US1.9 | T025 | `informes/tests/test_conclusion_hechos.py::test_parcial_sin_norma` | T030, T031, T032, T036 | T024 |
| US1.10 | T026 | `informes/tests/test_conclusion_hechos.py::test_todas_no_evaluables` | T030, T031, T032, T036 | T025 |
| US2.1 | T038 | `informes/tests/test_conclusion_emision.py::test_emite_texto_reescrito_aprobado` | T058, T059, T060, T063, T066 | T037 |
| US2.2 | T039 | `informes/tests/test_conclusion_emision.py::test_emitir_sin_conclusion` | T058, T059, T060, T063, T066 | T038 |
| US2.3 | T040 | `informes/tests/test_conclusion_revision.py::test_propuesta_no_aprueba` | T058, T059, T060, T063, T066 | T037 |
| US2.4 | T041 | `informes/tests/test_conclusion_revision.py::test_sin_grupo_ni_permiso_denegado` | T058, T059, T060, T063, T066 | T040 |
| US2.5 | T042 | `informes/tests/test_conclusion_revision.py::test_sin_sesion_o_inactivo_denegado` | T058, T059, T060, T063, T066 | T041 |
| US2.6 | T043 | `informes/tests/test_conclusion_revision.py::test_solo_grupo_denegado` | T058, T059, T060, T063, T066 | T042 |
| US2.7 | T044 | `informes/tests/test_conclusion_revision.py::test_solo_permiso_denegado` | T058, T059, T060, T063, T066 | T043 |
| US2.8 | T045 | `informes/tests/test_conclusion_revision.py::test_grupo_y_permiso_autorizados` | T058, T059, T060, T063, T066 | T044 |
| US2.9 | T046 | `informes/tests/test_conclusion_revision.py::test_edicion_invalida_aprobacion` | T058, T059, T060, T063, T066 | T045 |
| US2.10 | T047 | `informes/tests/test_conclusion_revision.py::test_regeneracion_identica_invalida` | T058, T059, T060, T063, T066 | T046 |
| US2.11 | T048 | `informes/tests/test_conclusion_emision.py::test_cambio_fuentes_impide_conclusion_obsoleta` | T058, T059, T060, T063, T066 | T039 |
| US2.12 | T049 | `informes/tests/test_conclusion_revision.py::test_borrador_persiste_al_volver_y_recargar` | T058, T059, T060, T063, T066 | T047 |
| US2.13 | T050 | `informes/tests/test_conclusion_revision.py::test_recarga_preserva_aprobacion_vigente` | T058, T059, T060, T063, T066 | T049 |
| US2.14 | T051 | `informes/tests/test_conclusion_emision.py::test_reaprobacion_explicita_fuentes_actuales` | T058, T059, T060, T063, T066 | T048 |
| US2.15 | T052 | `informes/tests/test_conclusion_emision.py::test_editar_aprobar_parcial_conserva_advertencias` | T058, T059, T060, T063, T066 | T051 |
| US3.1 | T068 | `informes/tests/test_conclusion_emision.py::test_snapshot_texto_y_trazabilidad` | T062, T077, T078, T079, T080 | T067 |
| US3.2 | T069 | `informes/tests/test_conclusion_emision.py::test_snapshot_no_cambia_con_origen` | T062, T077, T078, T079, T080 | T068 |
| US3.3 | T070 | `informes/tests/test_conclusion_emision.py::test_misma_conclusion_todos_los_medios` | T062, T077, T078, T079, T080 | T069 |
| US3.4 | T071 | `informes/tests/test_conclusion_emision.py::test_salidas_y_reenvio_no_llaman_ia` | T062, T077, T078, T079, T080 | T070 |
| US3.5 | T072 | `informes/tests/test_conclusion_emision.py::test_historicos_sin_conclusion_intactos` | T062, T077, T078, T079, T080 | T071 |
| US3.6 | T073 | `informes/tests/test_conclusion_emision.py::test_emitido_rechaza_mutar_conclusion` | T062, T077, T078, T079, T080 | T072 |
| US3.7 | T074 | `informes/tests/test_conclusion_emision.py::test_otro_bioquimico_emite` | T062, T077, T078, T079, T080 | T073 |
| US4.1 | T082 | `informes/tests/test_conclusion_ia.py::test_timeout_total_ofrece_plantilla` | T015, T090, T091 | T081 |
| US4.2 | T083 | `informes/tests/test_conclusion_ia.py::test_fallos_proveedor_ofrecen_plantilla` | T015, T090, T091 | T082 |
| US4.3 | T084 | `informes/tests/test_conclusion_ia.py::test_sin_configuracion_ofrece_plantilla` | T015, T090, T091 | T083 |
| US4.4 | T085 | `informes/tests/test_conclusion_ia.py::test_respuesta_invalida_no_inventa` | T015, T090, T091 | T084 |
| US4.5 | T086 | `informes/tests/test_conclusion_ia.py::test_plantilla_todas_cumplen` | T015, T090, T091 | T085 |
| US4.6 | T087 | `informes/tests/test_conclusion_ia.py::test_plantilla_parcial_mismos_hechos` | T015, T090, T091 | T086 |

## Cobertura de requisitos, éxito y criterios originales

| Requisito | Responsables técnicos | Validación |
|---|---|---|
| FR-001 | T033, T036 | T017, T022 |
| FR-002 | T030, T031 | T017, T021, T027 |
| FR-003 | T030 | T019, T020 |
| FR-004 | T015 | T006, T085 |
| FR-005 | T031, T015 | T018, T026, T086, T087 |
| FR-006 | T058, T065, T066 | T038, T049, T056, T054 |
| FR-007 | T032, T059 | T039, T040 |
| FR-008 | T063, T064 | T039, T044 |
| FR-009 | T014, T033, T061, T063 | T005, T053, T041, T045 |
| FR-010 | T058, T059, T060, T063 | T046, T047, T048, T055, T075 |
| FR-011 | T062, T063 | T068, T074 |
| FR-012 | T077, T078, T079, T080 | T070, T076 |
| FR-013 | T015, T090, T091 | T082, T083, T085, T088 |
| FR-014 | T015, T090 | T084, T086 |
| FR-015 | T078, T079, T080 | T071 |
| FR-016 | T012, T062, T077 | T004, T072, T073 |
| FR-017 | T063, T064, T080 | T002, T053, T071 |
| FR-018 | T030, T031, T065 | T023, T024, T025, T026, T052, T087, T027 |
| FR-019 | T015, T014 | T006, T053 |

| Criterio de éxito | Evidencia/tareas |
|---|---|
| SC-001 | T017, T019, T020, T027 |
| SC-002 | T018, T026, T086, T087 |
| SC-003 | T038, T039, T046, T047, T048, T075 |
| SC-004 | T070, T076, T099 |
| SC-005 | T082, T083, T084, T088 |
| SC-006 | T072, T073, T004 |
| SC-007 | T068, T074 |
| SC-008 | T053, T005, T006 |
| SC-009 | T046, T047, T048, T049, T050, T051, T056 |
| SC-010 | T023, T024, T025, T026, T052, T087, T027 |

| Criterio original por posición | Requisitos/tareas |
|---|---|
| 1, proponer hechos fuera de norma | FR-001/002, T030, T036 |
| 2, fuentes vigentes e IA solo redacta | FR-003/004/019, T006, T030, T015 |
| 3, todas cumplen | FR-005, T018, T086 |
| 4, borrador editable | FR-006, T058, T065, T066 |
| 5, aprobación y opción sin conclusión | FR-007/008/009/010, T059, T063, T053 |
| 6, copia inmutable | FR-011, T062, T068, T073 |
| 7, medios iguales | FR-012/015, T070, T080, T076 |
| 8, respaldo ante IA | FR-013/014, T015, T092 |
| 9, históricos intactos | FR-016/017, T004, T072 |

Las posiciones 1–9 no son identificadores Jira. Los diez controles adicionales solicitados se ubican así: autorización independiente=T053; parcial mixta=T027; duplicadas=T027/T007; GET obsoleto=T054/T060; borrador compartido=T054; firma=T053; IA tardía=T055/T088; recovery=T056; igualdad medios=T070/T076; históricos=T072/T004.

## Implementation Strategy

### MVP First

Completar Setup, Foundational y US1 para una **demo de borrador** verificable sin emitir. No presentar ese MVP como entrega integral ni desplegarlo como US10.2 completa: faltan edición/aprobación, todos los medios y aceptación de resiliencia. El mínimo entregable funcional completo exige los cuatro recorridos más Polish, manteniendo los nueve criterios originales.

### Incremental Delivery

Tests primero para cada comportamiento → modelo/guardia/adaptador → hechos y propuesta conectada → edición/aprobación/emisión con fragmento → representación en medios → fallos integrales → validación final. A cada checkpoint ejecutar pruebas relacionadas, corregir y continuar solo con evidencia. No aplazar conexiones entre UI y servicios para después del cierre de su recorrido. Un test fallando en el checkpoint deja el recorrido pendiente.

### Ejecución secuencial y puntos humanos

Aprovechar únicamente los grupos de archivos disjuntos de la tabla de paralelismo. Ejecutar migraciones, carreras PostgreSQL y suites sobre la misma base en serie. Mantener autorización para emitir sin conclusión incluso si falla IA, hay fuentes incompletas o aprobación inválida. Revisión humana de GET antes de integrar, revisión visual del PDF/impresión y aprobación funcional del responsable después de evidencia concreta; CI/PR/revisión del equipo no se inventan ni se consideran hechos consumados.

## Notes y resumen validable

- Phase 1: **3** tareas, 1 de escritura de tests y 1 controles de ejecución/revisión.
- Phase 2: **13** tareas, 3 de escritura de tests y 2 controles de ejecución/revisión.
- Phase 3: **21** tareas, 13 de escritura de tests y 1 controles de ejecución/revisión.
- Phase 4: **30** tareas, 19 de escritura de tests y 1 controles de ejecución/revisión.
- Phase 5: **14** tareas, 9 de escritura de tests y 1 controles de ejecución/revisión.
- Phase 6: **11** tareas, 8 de escritura de tests y 1 controles de ejecución/revisión.
- Phase 7: **9** tareas, 0 de escritura de tests y 7 controles de ejecución/revisión.

**Total: 101 tareas; 53 tareas de escritura/ampliación de tests automatizados y 14 controles adicionales de ejecución o revisión.** No confundir tareas de tests con cantidad final de casos parametrizados. 16 tareas marcadas [P]. Resto: 31 de implementación, una de preparación, una de decisión técnica y una documental. La generación inicial no completó tareas ni ejecutó tests; el avance posterior está registrado en los checkboxes y en la evidencia local.

Generado con setup-tasks.sh --json y estructura de tasks-template.md originales sin modificarlos. spec, checklist, plan, research, modelo, contratos, matriz y quickstart aprobados permanecen intactos durante esta fase; sus declaraciones sobre workflows anteriores son históricas, no anulan la autorización actual. No modificar Constitution ni deducir clave Jira de SCRUM-79.


## Historial de ejecución — US4 T082–T091 implementadas; validación pendiente

T001–T066, T068–T080 y T082–T091 implementadas/completadas: 89/101; T067, T081 y T092–T101 pendientes: 12. US2, US3 y US4 no se declaran validadas ni cerradas: sus checkpoints siguen sin ejecutar. Los checkboxes de tareas de tests representan escritura, no escenarios de aceptación aprobados.

En este incremento se escribieron los tests de US4 y después se integraron avisos seguros de origen/motivo, plantilla normal/parcial, espera accesible y finalización en éxito/fallback/error. El adaptador T015 se reutiliza sin modificaciones. La interfaz conserva texto local, guardado serial, conflictos, recuperación y aprobación expresa. La acción explícita de emitir sin conclusión puede continuar sin esperar una propuesta en curso; respuestas pendientes no se instalan después de esa decisión. Sin cambios en modelo, permisos, emisión ni salidas de US3.

Por instrucción expresa del usuario se difiere la batería de validaciones hasta finalizar US1–US4 y Polish, sin cambiar los 101 IDs ni el grafo de dependencias. En este incremento no se ejecutaron T067, T081, T092, pytest, Node tests, Ruff, Django checks, migraciones, builds ni validaciones integrales. Solo se realizó inspección estática y git diff --check. Backend/plantillas, PostgreSQL, workers, interacción, PDF y revisión visual siguen pendientes; los tests escritos no constituyen evidencia de aprobación. Los resultados anteriores no certifican este árbol nuevo.

Se detiene el trabajo al finalizar T091. No se comenzó Polish T093–T101 ni se modificaron requisitos, Constitution, cuerpos de tests anteriores o dependencias. El entorno simulado de los tests JS se amplió para los controles nuevos. No hubo operaciones de publicación. Detalle de archivos, decisiones y limitaciones en .local-validacion/us102/resultados.md.

## Historial de ejecución — T093 implementada; validación pendiente

Por autorización expresa del usuario se implementó únicamente T093 sin ejecutar su dependencia T092; no se modificó el grafo aprobado. Se agregó informes/tests/js una sola vez al comando node --test existente de .github/workflows/ci.yml. El archivo conclusion.test.cjs existe en ese directorio y corresponde al descubrimiento recursivo del runner Node 20. Se conservaron los cinco directorios anteriores, todos los pasos, Node 20 y PostgreSQL 16. Verificación únicamente estática, sin ejecutar Node ni CI.

Estado actualizado: **90/101 implementadas; 11 pendientes: T067, T081, T092 y T094–T101**. Los 101 IDs, requisitos, escenarios y dependencias permanecen intactos. No se ejecutaron T067/T081/T092/T094–T099, pytest, Node tests, Ruff, Django checks, migraciones, builds ni CI local/remoto. No se declara validado ningún recorrido ni escenario. Se detiene el trabajo en T093, sin comenzar tareas posteriores ni realizar operaciones de publicación. Detalle en .local-validacion/us102/resultados.md.

## Historial previo al cierre — implementación funcional terminada; validación diferida

Por instrucción más reciente del responsable se detuvieron la suite integral y el servidor de revisión. No se agregan funcionalidades, capas ni controles nuevos. La autorización general de implementación es suficiente para decisiones técnicas rutinarias; no se solicita otra aprobación para dar por escrita la funcionalidad.

**97/101 tareas completadas.** US1–US4 están implementadas. Se completaron además T067, T081, T092 y T094–T097 con resultados reales registrados localmente. Los ajustes posteriores de presentación se comprobaron en navegador; no se atribuye un pase integral al último árbol.

No quedan tareas de funcionalidad por construir entre los cuatro pendientes:

| Tarea pendiente | Naturaleza | Tratamiento actual |
|---|---|---|
| T098 | Validación integral | Diferida. La última pasada se interrumpió por pedido del usuario; no tiene resultado final aprobado. |
| T099 | Revisión humana/formal | Diferida a la etapa de validación. No bloquea la implementación ni exige nuevas confirmaciones técnicas. La revisión visual parcial realizada no se presenta como aprobación del usuario/equipo. |
| T100 | Documentación de resultados finales | Se actualiza el estado real, pero el cierre con 38/38 y suite completa queda pendiente de evidencia. |
| T101 | Auditoría final de Git/publicación | Se reserva para la entrega/publicación futura. No agrega comportamiento funcional. |

No se marcan estas tareas como aprobadas ni se alteran sus IDs o dependencias. No corresponde ampliar concurrencia, workers o infraestructura: se conserva lo ya aprobado y necesario para vincular texto, aprobación y emisión.

Correcciones concretas de esta etapa: atributos del editor solo para usuarios autorizados; espacio inferior para que el asistente flotante no tape Emitir sin conclusión; tooltip del campo de conclusión sin desborde en pantalla reducida; formato de tres archivos de tests y CSS compilado actualizado. Sin cambios a US10.1, permisos generales, modelos, migraciones, dependencias, Constitution ni otras historias.

La implementación funcional está terminada; la validación integral final sigue pendiente. Sin git add, commit, push, PR, merge o rebase. Resultados previos y limitaciones en .local-validacion/us102/resultados.md.

### Simplificación de interfaz solicitada — 2026-11-16

Ajuste explícito del responsable sobre la presentación de T065/T066, sin cambiar spec, criterios Jira, los 101 IDs o sus dependencias. Sustituye en la interfaz el modo de edición y los paneles técnicos del diseño original: un único campo siempre editable, advertencias no editables y estado Pendiente/Aprobada. Solo quedan Proponer, Aprobar y las dos emisiones explícitas; sin Guardar manual ni casilla de incorporación. Se confirma la propuesta cuando reemplaza contenido existente; la primera propuesta vacía es directa. Persistencia/autoguardado y recuperación continúan internamente sin mensajes de éxito o sincronización.

Se preservan política conjunta, huellas/revisión internas, aprobación del texto exacto con advertencias, invalidación, barreras de guardado, descarte de respuestas tardías y verificación transaccional existente. Un conflicto conserva la edición local y exige una nueva propuesta confirmada; nunca sobrescribe automáticamente la otra versión. Sin modelos, campos, endpoints, dependencias o cambios en servicios IA/emisión/salidas ni en US10.1/asistente flotante.

Verificación acotada realizada: 47 tests JS del editor con Node 20.19.0 PASS; 27 tests backend seleccionados de interfaz, revisión y emisión PASS en PostgreSQL aislado. Ruff check/format de los dos Python afectados PASS y CSS recompilado con Tailwind existente. No se repitió la suite integral. Estado de tareas: 97/101; T098–T101 continúan diferidas para la siguiente etapa. Detalle de comandos y archivos en .local-validacion/us102/resultados.md. Sin commit ni push.

## Cierre definitivo — 2026-11-16

**101/101 tareas completadas; cero pendientes funcionales y de validación local.** Se mantienen los 101 IDs consecutivos y sus dependencias.

- T098: integral PostgreSQL aislado: 2634 PASS y 2 FAIL (1464.36 s), ambos por expectativas antiguas de interfaz en test_vista_previa.py. Se adaptaron esas dos assertions a las emisiones y al controlador aprobados, sin cambios funcionales. Repetición del archivo completo: 9 PASS (12.83 s), Ruff check/format PASS. Resultado consolidado por ID exacto: 2636/2636 PASS, sin sumar repeticiones ni declarar verde la primera integral. No se repite la suite larga porque el código funcional no cambió. Los 38 escenarios de la matriz pasaron en la integral; 19 FR y nueve criterios cubiertos.
- T099: el responsable confirmó expresamente sus pruebas manuales de todos los recorridos, incluida la interfaz simplificada, sin incidencias. La revisión sintética previa de PDF multipágina, impresión, conflicto y otro emisor está registrada localmente. No se inventa revisión del equipo ni se pide otra confirmación.
- T100: quickstart actualizado con funciones reales, interfaz definitiva, resultados/comandos, identidad del árbol, límites e inventario exacto de 53 archivos (17 modificados y 36 nuevos). Los documentos aprobados y Constitution permanecen intactos. La presentación de T056/T065/T066 se sustituyó por la simplificación solicitada expresamente; sus protecciones permanecen y tienen tests.
- T101: auditoría final de alcance e inventario; git diff --check y controles de archivos nuevos sin errores de whitespace, sin archivos sensibles/locales ni cambios a US10.1, otras historias, Constitution, dependencias o main. Índice vacío; publicación no ejecutada.

Controles vigentes: 121/121 JS Node20 (47 editor); Ruff check/format completos (324 archivos), Django sin incidencias, migraciones sin cambios/operaciones pendientes en el entorno aislado y CSS compilado idéntico con Tailwind4.3.3. La única migración aditiva de la feature es 0006, sin backfill/permisos nuevos. Los tests de proveedor y correo usan dobles, sin afirmar disponibilidad externa.

US10.2 terminada localmente, lista para revisión del informe y posterior autorización de commit/publicación. Clave Jira propia, CI remoto y revisión del equipo/PR quedan para la publicación; no se declara merge ni DONE en Jira. Sin git add, commit, push, PR, merge ni rebase.
