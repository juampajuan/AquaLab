# Investigación técnica — Panel de administración

Fecha: 2026-11-03. Rama: `025-Panel-Administracion`. Investigación del workflow original con dos agentes de solo lectura para cuentas y UI/permisos/tests y consolidación posterior. Sin consultar bases de otra computadora.

Registro de investigación previo a implementar. Las decisiones se conservan; quickstart.md documenta el estado ejecutado.

## Evidencia del repositorio al investigar

| Área | Evidencia | Consecuencia |
| --- | --- | --- |
| Cuenta | usuarios/models.py y migraciones 0001–0002: Usuario propio; correo único; is_active etiquetado «aprobada» | Separar aprobación y habilitación sin cambiar identidad |
| Registro | usuarios/views.py:crear_usuario_pendiente y forms.py:RegistroForm | Ya hay confirmación y hashing; explicitar aprobación falsa |
| Admin | usuarios/admin.py:aprobar_cuentas, rechazar_solicitudes, save_model | Tres caminos que deben compartir transición; filtros actuales solo por is_active |
| Avisos | usuarios/notificaciones.py y tests/test_notificaciones.py | Reutilizar plantillas, callbacks y manejo de fallas |
| Login/sesión | usuarios/forms.py, context_processors.py, middleware.py y tests de sesión | Diagnóstico llama pendiente a toda inactiva; huella no autoriza |
| Bioquímicos | estudios/migrations/0008_grupo_bioquimicos.py e informes/migrations/0002_permiso_bioquimicos.py | Grupo/permisos ya creados, con patrón de creación histórica de permisos |
| Tipos | estudios/views_tipos.py, gestion_tipos.py, forms_tipos.py y confirmaciones_tipos.py | CRUD completo, permiso propio, versiones y confirmaciones; conservar |
| Pruebas | pruebas/models.py, admin.py y tests de modelo/importación/admin | Datos y edición protegida ya existen; agregar solo consulta HTML |
| UI | templates/base.html, ui/menu.html, inicio.html, ui/* y config/ui.py | Componentes, unidad, mensajes y acceso rápido reutilizables |
| Configuración/CI | config/settings.py, urls.py, .env.example, Compose, Dockerfile, pyproject.toml, .github/workflows/ci.yml | Sesión global, CSRF, entorno y checks ya establecidos |

## R1 — Autorización conjunta y canal admin independiente

**Decisión**: Permiso `usuarios.administrar_panel` en Meta de Usuario y grupo Administradores con ese permiso mediante migración. Política central del panel comprueba autenticación, activo, membresía explícita y asignación real del permiso por cualquier grupo o por usuario. Sin backend nuevo. Django Admin conserva is_staff y sus permisos normales.

**Motivo**: has_perm concede todos los permisos al superusuario activo; consultar las asignaciones auth existentes evita tanto superusuario fuera del grupo como grupo sin permiso. La migración no inscribe usuarios, no da is_staff y no altera Bioquímicos. Una instancia nueva del actor evita caché de permisos en escrituras.

**Alternativas descartadas**: Solo permission_required permite bypass; solo grupo ignora el permiso; cambiar ModelBackend afectaría otras funcionalidades. No modificar permisos de tipos.

## R2 — Estado mínimo y revisión optimista

**Decisión**: Agregar `aprobada` booleano y `version_administrativa` entero positivo. Estado derivado de aprobada/is_active; constraint activo implica aprobado. Conservar is_active como habilitación y corregir etiqueta/ayuda. Revisión detecta cambios obsoletos y secuencias A→B→A de las superficies coordinadas.

**Motivo**: is_active solo no distingue pendiente de suspendida. No se requiere fecha de aprobación histórica ni enum duplicando habilitación. Default final de aprobada verdadero conserva las creaciones directas activas actuales; registro fija ambos falsos, manager deriva aprobación de is_active salvo valor explícito, superusuario fuerza ambos verdaderos. La migración usa un default temporal falso antes del backfill para no aprobar inactivos heredados.

**Alternativas descartadas**: last_login, rol o actividad no prueban aprobación previa. Fecha de aprobación requeriría inventar fechas. Sin revisión, comparar solo el valor actual pierde cambios intermedios.

## R3 — Migración histórica conservadora

**Decisión**: Activos actuales quedan aprobados; todos los inactivos, sin evidencia separada fiable en el esquema, quedan pendientes. No cambiar is_active, PK, contraseñas, email, grupos, permisos o referencias. Dos migraciones previstas: estado/revisión/constraints y luego permiso/grupo sin miembros.

**Motivo**: Nadie obtiene acceso por migrar. El default temporal falso impide aprobar automáticamente inactivos. No inferir aprobación por last_login, superusuario, grupos o referencias. Una cuenta histórica así clasificada requiere revisión/aprobación autorizada, nunca reactivación como previamente aprobada.

**Alternativas descartadas**: Aprobar todos los inactivos habilitaría reactivaciones injustificadas; recrear usuarios perdería historia. Revertir esquema pierde la distinción nueva: respaldo previo y ningún cambio automático de is_active al revertir.

## R4 — Servicios, avisos y bloqueo

**Decisión**: Adaptadores autorizados de panel/admin llaman un núcleo privado de transiciones en usuarios. atomic, recarga de actor, filas actor/objetivo bloqueadas por PK ascendente y validación de revisión/estado antes de cambiar. Una resolución efectiva agenda una llamada existente con on_commit; reactivar no agenda aprobación. Acciones masivas ordenan igual y omiten cuentas ya resueltas.

**Motivo**: Las acciones actuales bloquean pero confunden desactivadas con pendientes; save_model avisa cada false→true. La transición compartida evita carreras panel/admin y reenvíos. Rechazo copia nombre/email antes de eliminar. Correo se ejecuta tras commit y su falla conserva la decisión, como hoy.

**Alternativas descartadas**: Copiar lógica en panel, señales (update masivo no las dispara), depender solo de borrar borrador de sesión, outbox/workers nuevos. on_commit no garantiza entrega SMTP exactamente una vez frente a caída del proceso: se conserva el alcance actual de no duplicación por transición/reenvío/carrera normal.

## R5 — Ficha de Django Admin

**Decisión**: En POST, wrapper público changeform_view adquiere transacción/bloqueo antes de cargar/bindear objeto. Formulario verifica revisión e instantánea firmadas al abrir y prepara estado coherente antes de constraints. Errores de conflicto se muestran antes de save_model. save_model/núcleo común persisten la propuesta fresca; save_related guarda M2M e incrementa revisión por cambios relevantes en la misma transacción. No exponer aprobada o versión para edición libre.

**Motivo**: La instancia actual puede cargarse antes del bloqueo y guardar después datos obsoletos. No usar save_model como veto tardío; no guardar dos veces una instancia vieja encima de la transición. Mantener aprobación desde ficha, alta admin sin avisos, password y permisos normales; revisar el orden real con tests de integración.

**Alternativas descartadas**: Quitar aprobación desde ficha rompe el flujo probado. Conservar su aviso false→true reenviaría correo en reactivaciones. Un bloqueo solo al final no detecta información que el operador revisó antes.

## R6 — Historial y rechazo impedido

**Decisión**: Solo pendientes elegibles se eliminan al rechazar; aprobadas se suspenden. La aclaración funcional I1 aprobada en spec.md (FR-008, FR-010, US2.9 y SC-002) formaliza el rechazo impedido. Mantener PROTECT desde muestras, estudios, mediciones, validaciones e informes. Si una pendiente histórica tiene esas referencias, informar el motivo y conservar íntegramente cuenta/correo/historial, sin aviso ni liberación de email. Comprobar también firma profesional: actualmente su FK es CASCADE y no se debe perder silenciosamente por la clasificación conservadora.

**Motivo**: Migrar una inactiva a pendiente no autoriza borrar su historial. Solicitudes nuevas sin actividad ni impedimentos conservan eliminación, liberación de email y aviso actuales. Un rechazo bloqueado no es una resolución efectiva: la cuenta sigue Pendiente y sin acceso; el administrador puede revisarla y, si corresponde, aprobarla mediante el flujo normal, sin aprobación previa supuesta ni activación automática. T034 verifica también esta continuación autorizada y la conservación de referencias/firma.

**Alternativas descartadas**: Relajar PROTECT, borrar referencias/firma o aprobar implícitamente por tener actividad. No crear estado nuevo ni sistema de rechazo persistido.

## R7 — Confirmaciones, roles y navegación

**Decisión**: Patrón de confirmaciones_tipos adaptado a usuarios, con salts y claves propios, TTL 3600 s y 20 borradores por sesión. Firma actor/sesión/objetivo/operación/revisión/instantánea/propuesta; volver a autorizar bajo bloqueo. Roles: solo add/remove de Bioquímicos, sin set ni editar permisos individuales; se permite rol propio.

**Motivo**: Firma no autoriza ni serializa operaciones. Versión e instantánea detectan propuestas antiguas y cambios de identidad. La versión aumenta en panel y ficha admin, incluidas membresías/permisos; las escrituras SQL manuales ajenas no reciben garantía universal de detección ABA.

**Alternativas descartadas**: ModelForm general expondría privilegios; compartir las claves de borrador de tipos acoplaría dominios; modificar tipos ampliaría alcance.

## R8 — Consultas y CSS

**Decisión**: Páginas de 20, orden estable, roles con Exists o prefetch; catálogo con icontains por código/nombre, incluye inactivas, usa filtro unidad y enlace admin existente. Menú usa política central; tipos se mueve sin cambiar sus rutas o permiso, e Inicio conserva tarjeta actual.

**Motivo**: Componentes ui/acciones_confirmacion y ui/paginacion ya resuelven los patrones. static/src/aqualab.css escanea `*/forms.py`, no automáticamente forms_administracion.py: reutilizar clases presentes en templates o ampliar source específicamente si hiciera falta. Recompilar CSS con el CLI fijado y CI existente.

**Alternativas descartadas**: Nuevo editor, nuevo frontend, otro permiso obligatorio para tipos, rediseñar Inicio o añadir infraestructura de pruebas distinta. SQLite no sirve para verificar bloqueos PostgreSQL.

## Fuentes primarias

- [Django 5.2: has_perm y superusuarios](https://docs.djangoproject.com/en/5.2/ref/contrib/auth/#django.contrib.auth.models.User.has_perm).
- [Django 5.2: caché de permisos](https://docs.djangoproject.com/en/5.2/topics/auth/default/#permission-caching): refresh_from_db no elimina la caché de permisos de una instancia.
- [Django 5.2: select_for_update](https://docs.djangoproject.com/en/5.2/ref/models/querysets/#select-for-update): transacciones y tests de bloqueo reales.
- [Django 5.2: on_commit](https://docs.djangoproject.com/en/5.2/topics/db/transactions/#performing-actions-after-commit): efectos después de commit y sus límites.
- [Django 5.2: hooks ModelAdmin](https://docs.djangoproject.com/en/5.2/ref/contrib/admin/#django.contrib.admin.ModelAdmin.save_model): validación y guardado por sus mecanismos apropiados.

Investigación cerrada; sin decisiones funcionales abiertas. Falta el identificador real Jira/US para completar trazabilidad antes del PR.
