# Cierre técnico — US 5.5 (012)

Fecha: 28/10/2026. Rama codex/012-gestionar-tipos-estudio, HEAD/base a95efb46db9b94a8913d44f8dbff8fd4c8482d81. Este cierre no realiza staging, commit ni publicación. La verificación general final concluyó correctamente; resultados y estado definitivo al final.

## Alcance y revisión técnica

Alta, edición, desactivación, reactivación y eliminación únicamente de tipos nunca utilizados. Reutiliza Prueba, TipoEstudio, TipoEstudioPrueba, Estudio y PruebaEstudio integrados, sin nuevos modelos o migraciones. Los cambios en archivos compartidos se limitan a fixtures adicionales, rutas y enlaces de gestión condicionados al permiso; los flujos de muestras/creación/consulta existentes no se reescribieron.

Se contrastaron spec, plan, investigación, modelo de datos, contratos UI/servicio, código y matriz de tareas. La matriz T044 de tasks.md identifica tests reales para los 19 FR, 11 SC y 33 escenarios (7 US1 + 11 US2 + 7 US3 + 8 reactivación/eliminación), sin requisitos sin cobertura identificados. Se revisó además el código y se reejecuta toda la suite; no se interpreta la matriz documental como sustituto de ejecución.

- Permiso estudios.gestionar_catalogo en GET/POST y en servicio; cuenta activa, sesión, CSRF y tokens separados por fase/usuario/sesión/acción/tipo/versión/digest. Sin autorización basada solo en staff o en ocultar enlaces.
- Escritor único gestionar_tipo_estudio: atomic y select_for_update sobre un tipo, versión esperada antes de validar/no-op. Un cambio efectivo de nombre/descripción/composición/disponibilidad incrementa una vez; no-op vigente sin DML, stale rechazado incluso con valores coincidentes. Errores de persistencia traducidos fuera de atomic.
- Creación de estudios conserva su orden advisory → tipo; administración toma solo el lock del tipo y nunca adquiere ese advisory después. Un único tipo por operación evita inversión de locks.
- Eliminación comprueba cualquier estudio asociado bajo lock; FK/PROTECT refuerzan integridad. Pruebas del catálogo e historial no se borran. Reactivación exige pruebas y no modifica estudios previos.
- Snapshots y asignaciones históricas pertenecen al estudio y no se reescriben al administrar el catálogo. No se duplican responsabilidades ni entidades de US 5.1/5.2.

## Evidencia y límites

T001: el usuario comunicó aprobación del equipo de la spec completa, incluidos FR-018/019, y autorización de implementar el 28/10/2026. No hay nombres, actas o enlaces inventados. Checklist de calidad documental: 16/16, sin cambiar sus marcadores para simular avance de código.

T047: el usuario informó nueve casos Chrome satisfactorios en QA US 5.5, puerto 8012/base aqualab_us55. Se registran en quickstart.md: alta, edición/versionado, duplicados/vacíos, desactivación, reactivación, historial, eliminación usada rechazada, eliminación nunca usada sin borrar pruebas y rechazo sin permiso. No hubo observación directa de Codex ni se aportaron capturas, tiempos o registros HTTP de esos casos. No se afirma validación manual adicional de cancelación, expiración, no-op o concurrencia.

Los tests PostgreSQL reales verifican concurrencia, rollback, idempotencia y conservación histórica con conexiones separadas; no son resultados de Chrome. El smoke HTTP de T046 es evidencia independiente, previa al reporte manual. No se extrapolan garantías de crash/recovery ni de escrituras SQL/admin que eludan el servicio soportado.

## Riesgos y pendientes administrativos

- Jira: clave/enlace no aportados; pendiente administrativo, sin inventar códigos.
- Futuro PR: CI remoto y revisión/aprobación de código por otro integrante todavía no realizados; la aprobación de spec no los sustituye. Resolverlos antes del merge según Constitution.
- No se consultó ni actualizó origin/main en este cierre: la base local sigue a95efb46; comprobar posibles avances y conflictos al preparar el PR, sin integrar ramas aquí.
- Datos académicos DEMO sin validez científica. QA, usuarios, contraseñas y datos de navegador/base permanecen fuera del commit. No hay proveedor científico externo pendiente.
- Metadatos de Draft/propuesto en los artefactos originales conservan el estado de generación; las autorizaciones posteriores están registradas en Notes/quickstart, sin cambiar requisitos o decisiones técnicas.

## Archivos y exclusiones

Inventario selectivo en inventario-commit.md. Sin cambios accidentales de modelos/migraciones, muestras, flujos de US 5.1/5.2, Constitution o instalación Spec Kit. Respaldos preservados, .env y cachés excluidos; .specify/feature.json es contexto local ignorado y no se incluye. Las contraseñas literales de fixtures son datos sintéticos de test, no credenciales QA.

## Resultado definitivo de T050

- Suite completa reejecutada en QA: **526 pytest aprobados en 346.77s** (28/10/2026), con concurrencia sobre PostgreSQL 16.15 real; sin fallos.
- **14 tests JavaScript aprobados** en la reejecución de cierre.
- Ruff check aprobado; Ruff format --check: 121 archivos conformes; Django check sin problemas; makemigrations --check --dry-run sin cambios; migrate --check con exit 0.
- git diff --check sin errores; staging vacío. Inventario exacto: **30 archivos**, 6 modificados versionados y 24 nuevos, sin datos/secretos QA ni respaldos. Ningún modelo o migración nuevo; archivos protegidos sin diff.
- T001–T050: **50/50 completadas**. Checklist documental **16/16** sin modificaciones. Revisión de requisitos/diseño/contratos/código/tests concluida sin bloqueos técnicos identificados. No hay extensions.yml, por lo tanto no hay hooks que ejecutar.

**Conclusión:** US 5.5 lista para realizar commit local y preparar PR contra main, con el inventario selectivo revisado. No se ha autorizado ni realizado commit, push, PR, merge o rebase en este cierre. CI remoto y aprobación de código por otro integrante siguen exigidos antes del merge; Jira administrativo pendiente. Validación manual limitada a los nueve casos informados por el usuario, sin capturas u observaciones adicionales inventadas.
