# Cierre técnico — US 5.1 Crear estudio

Rama codex/008-crear-estudio; HEAD 6b29f434f31898c6b90290a8efd03fac475721a6, con cambios locales sin commit. Fecha de recepción y revisión: 27/10/2026. Este cierre no autoriza commit, push, PR ni merge.

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

## Revisión final de consistencia (T040)

Se aplicó el análisis de la skill original speckit-analyze en modo lectura, usando check-prerequisites.sh --json --require-spec --require-tasks --include-tasks. No hay .specify/extensions.yml ni hooks que ejecutar. La actualización documental de cierre se realiza por instrucción expresa del usuario, separada del análisis.

| Hallazgo | Severidad | Acción de cierre |
|---|---|---|
| D1: secciones vigentes aún trataban FR-013/014 como provisionales y FR-012/020 exigían catálogo oficial, contradiciendo decisiones posteriores del usuario. | Media documental | Se alinearon escenarios, requisitos de datos y dependencias de spec con las decisiones definitivas y el contexto FIUBA. Las aclaraciones anteriores se conservan bajo encabezado histórico. No cambió funcionalidad. |
| D2: encabezados de modelo/contrato/plan y notas de cierre decían no implementado o pendiente manual. | Media documental | Se actualizaron los estados principales y se añadió este registro vigente; el historial mantiene fechas y evidencia previas, sin atribuir pruebas nuevas a ejecuciones anteriores. |

No se detectaron contradicciones técnicas bloqueantes, conflictos con Constitution ni requisitos sin tareas. Métricas: 20 FR + 7 SC, 40 tareas originales; cobertura documental 100% de FR/SC (mapa completo en tasks.md). No hay tareas sin relación funcional: setup, documentación y controles respaldan requisitos transversales. El cargador demo es la extensión expresamente autorizada de preparación de T037, no una implementación del CRUD US 5.5. No se agregan tareas completadas ficticias al denominador.

| Requisitos | Evidencia de implementación y tests |
|---|---|
| FR-001/002/003/006/007/011 | forms, views, urls y templates; test_registro/test_confirmaciones: sesión, CSRF, selección, resumen, volver/cancelar, errores y éxito. |
| FR-004/005/008/009/016/017 | servicios y modelos; test_servicio/test_modelos: asignación exacta, estado/auditoría, identificador, rollback y UUID único persistente. |
| FR-010/015/018 | catálogo, snapshots, lock de tipo y versión; test_catalogo_contrato/test_concurrencia/test_registro: ambas ordenaciones, nueva confirmación y conservación histórica. |
| FR-013/014 | Ausencia de unicidad muestra/tipo y de filtro cliente activo; test_servicio/test_registro/test_concurrencia y confirmación manual del usuario. |
| FR-012/019/020 | Prueba/TipoEstudio/composición separados; tres migraciones solo de esquema; cargador DEMO explícito y test_demo_us51. Sin definiciones científicas arbitrarias. |
| SC-001 a SC-007 | Casos anteriores más pruebas de seguridad y concurrencia PostgreSQL; mapa tarea/requisito detallado en tasks.md. |

UUID requerido y UNIQUE en PostgreSQL; reutilizar la clave compara creador/muestra/tipo. Transacción: advisory lock de estudios, lookup persistente, lock del tipo, configuración/versiones validadas, snapshots y asignaciones, commit único. PruebaEstudio impide pares duplicados. Se conserva la Muestra integrada de US 4.1 y sus migraciones. El escritor futuro de US 5.5 debe usar las mismas entidades y protocolo de bloqueo/versión; save/M2M no incrementan versión automáticamente.

## Controles automatizados y protección de archivos

Ejecución general anterior: 361 passed in 161.17s; 18 corresponden al cargador demo. Pruebas anteriores JS: 14 passed. La revalidación de este cierre se registra al terminar, con su propio resultado; no se confunde con la declaración manual.

Ruff check pasó; Ruff format --check: 122 archivos ya formateados (con exclusiones originales de pyproject.toml). Django check: 0 issues. makemigrations --check --dry-run: No changes detected. migrate --check: sin migraciones pendientes. Node: 14 tests aprobados, 0 fallos. git diff --check: sin errores. No se aplicaron migraciones ni se modificaron datos de desarrollo en esta revisión.

Sin cambios staged. Los cuatro archivos existentes modificados son integración de apps/rutas y enlaces de navegación. El inventario exhaustivo está en inventario-commit.md. Se excluyen .local-backups, .env, cachés, bytecode, volúmenes/bases, dumps y archivos de otros worktrees. No se hizo git add ni git add .; la selección futura debe limitarse al inventario.

Sin diff contra HEAD en muestras, Constitution, .specify, .agents o .codex; sin archivos nuevos no ignorados en esos recursos protegidos. US 5.5 conserva HEAD 2541b85; SHA256 de su spec: D00EFE9C7F523D1827B88EEFE45945845169ABD3BB1FC103222628BD0C84B3BC; checklist: E29BB2925F05B63CB3E45714802B8622C73FA521775E801B35FB547EF2A1C8E4, coincidentes con la referencia preservada. No se modificó su worktree.

## Límites y trabajo posterior

- No se verifica exactitud científica: datos y asociaciones son ficticios para un proyecto académico FIUBA. No hay catálogo externo pendiente.
- El bloqueo global serializa creación de estudios: correcto para este alcance, sin benchmark de carga ni SLA acreditado.
- Futuro US 5.5: implementar su escritor coordinado y reutilizar las tablas/migraciones entregadas; no se declara que su CRUD exista ni esté probado.
- Tokens ligados a sesión, vigencia de una hora y recuperación controlada; no se promete continuidad después de logout/rotación de sesión ni cancelar una petición concurrente ya iniciada.
- Cargador demo: requiere entorno declarado desarrollo/QA y DEBUG=True; no repara ni sobrescribe datos divergentes. El etiquetado correcto del entorno es responsabilidad de su configuración.
- Jira: clave/enlace pendientes administrativos; no bloquean el commit local. Para el PR siguen siendo necesarios CI remoto y aprobación de otro integrante según Constitution. No existen todavía PR, CI remoto ni aprobación de código inventados.


## Resultado final de la revalidación

**361 passed in 180.10s** en la suite general PostgreSQL; **14 tests JavaScript aprobados**. Controles estáticos y migraciones indicados arriba correctos. Estado final: **40/40 tareas**, incluyendo T037 basada en declaración del usuario, T039 y T040. Inventario final: **50 archivos** (4 existentes modificados, 46 nuevos: 26 de estudios, 7 de pruebas, 13 documentales). Ningún cambio funcional en esta revisión. Lista exacta en inventario-commit.md. Listo para commit local y preparación posterior del PR, sujetos a autorización del usuario; no equivale a autorización para hacerlos ni a merge aprobado.
