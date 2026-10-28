# Diagnóstico previo a plan — US 5.5 (012)

Fecha: 28/10/2026. Se registran hechos comprobados del repositorio y decisiones ya confirmadas, no un nuevo diseño ni ejecución de speckit-plan. [Spec vigente](spec.md), [checklist](checklists/requirements.md), [contrato consumidor integrado](../008-crear-estudio/contracts/catalogo-compartido.md).

## Git y preservación

- Worktree conservado: E:/Codex/worktrees/us55-tipos-estudio/AquaLab. Rama codex/012-gestionar-tipos-estudio.
- Base anterior 2541b85760583250f99f5bf660ebaf2f655be6b5; origin/main descargado y base actual a95efb46db9b94a8913d44f8dbff8fd4c8482d81. Se comprobó relación de ancestro: 0 commits propios divergentes y 28 commits entrantes. Actualización con git reset --keep exclusivamente al descendiente comprobado, sin merge, rebase ni nuevos commits.
- US 5.1: commit 0616c755121dbb10c24c95a4bc79c250c1a837e0 integrado por PR #12 (07b89bc). US 5.2 también está integrada por PR #16. US 5.3/5.4 presentes como documentación; no se confunde con código de agregar/quitar pruebas ya implementado.
- Borradores y contexto respaldados con hashes verificados en .local-backups/us55-antes-main-20261028-124711/. Se preserva además el respaldo anterior de renumeración us55-009-a-012-20261028-124010/. Nunca deben añadirse al commit.
- Tras actualizar la base se comprobó que spec, checklist y .specify/feature.json conservaban exactamente sus hashes originales. Luego solo se editaron documentos de esta feature. El manifiesto preserva HEAD, estados y hashes de los otros worktrees para comprobar que no se alteraron.

## Infraestructura existente que se reutiliza

| Elemento real | Contrato actual comprobado | Reutilización / límite |
|---|---|---|
| pruebas.Prueba | id BigAutoField; codigo CharField(50), único exacto, recorte lateral; nombre CharField(150), recorte lateral; checks no vacío | Una sola definición compartida. US 5.5 selecciona existentes: no crea otro catálogo, fórmulas o normas. |
| estudios.TipoEstudio | id; nombre CharField(150) recortado; UniqueConstraint Lower(nombre); descripcion TextField blank/default vacío; activo; version PositiveBigInteger desde 1 con check >=1 | Campos y constraints ya existen. Tildes y espacios internos distinguen; falta el flujo administrativo de escritura. |
| estudios.TipoEstudioPrueba | M2M explícita; unique(tipo, prueba); tipo CASCADE y prueba PROTECT | Impide asociaciones duplicadas y protege Prueba referenciada. No impide por sí sola que un tipo quede vacío. |
| Permiso estudios.gestionar_catalogo | Declarado en Meta y migración inicial | Reutilizarlo, sin asignarlo automáticamente ni crear rol de dominio. La declaración no implementa autorización de endpoints administrativos. |
| estudios.Estudio | FK tipo PROTECT, related_name estudios; muestra; UUID único; creador/hora; tipo_nombre_snapshot, tipo_descripcion_snapshot y tipo_version_snapshot | Ya impide borrar un tipo con estudios asociados por ORM. US 5.5 necesita además comprobar uso/versión concurrentemente; no crea ni modifica historial. |
| estudios.PruebaEstudio | Asignaciones propias, unique(estudio, prueba); FK Prueba/Estudio PROTECT; estado inicial pendiente incorporado por US 5.2 | Cambiar el M2M del tipo no cambia esas filas. No implementar aquí agregar/quitar pruebas de estudios. |
| estudios.catalogo.leer_configuracion(tipo_id) | atomic + select_for_update del tipo; rechaza inexistente/inactivo/vacío; devuelve id/nombre/descripcion/version/pruebas(id,codigo,nombre) | Lector consumidor coherente ya implementado. No devuelve activo: exige que sea verdadero. No sirve sin adaptación como lector administrativo de tipos inactivos; faltará la consulta de gestión correspondiente sobre las mismas entidades. |
| estudios.servicios.crear_estudio | atomic; advisory transaction lock 5_100_001; UUID persistente; lock del tipo; versión; snapshots y asignaciones en la misma transacción | Mantenerlo sin cambios en este diagnóstico. Coordinación del nuevo escritor con ese mismo lock de tipo. |
| Migraciones existentes | pruebas/0001_initial; estudios/0001_initial (catálogo); estudios/0002_estudio (estudios); estudios/0003_estados_estudio_y_prueba (US 5.2) | No recrear tablas ni migraciones iniciales; no se generó ni aplicó ninguna nueva. |
| Datos sintéticos/demo | Factories aisladas en estudios/tests/conftest.py y comando explícito cargar_demo_us51 | Reutilizar preparación existente con las guardas documentadas, sin cargar automáticamente ni considerar sus asociaciones científicamente válidas. |

Los tests existentes del consumidor cubren historial, rollback, idempotencia y ordenaciones de concurrencia; sus helpers de edición son solo de test. No acreditan un escritor administrativo US 5.5, que todavía no existe. No se ejecutó pytest, Docker ni una base de datos en este diagnóstico documental.

## Contrato de coordinación ya acordado

US 5.5 posee funcionalmente el catálogo y extiende su base entregada por US 5.1. El contrato integrado exige atomic, lock de la fila TipoEstudio, comparación de versión revisada, validación de campos y conjunto final, escritura de datos/composición y aumento de versión una vez por cambio efectivo de nombre, descripción, activo o composición. No-op no incrementa; rollback no publica una versión. save/M2M NO implementan automáticamente ese protocolo: es trabajo real pendiente de US 5.5.

La creación de estudios toma primero su advisory lock y luego el tipo. El escritor de catálogo necesita el lock del tipo, sin tomar después el advisory de creación; debe respetar ese orden para no introducir interbloqueos. Mantener el lock hasta terminar el conjunto y la versión. Reactivar/desactivar también invalidan ediciones y revisiones anteriores cuando hay cambio efectivo.

Eliminar nunca usados exige comprobar utilización y versión manteniendo coordinación con la creación de estudios: si crear gana se protege el tipo; si eliminar gana crear rechaza referencia inexistente. La relación PROTECT es defensa adicional, no reemplaza autorización, confirmación ni la coordinación. Ninguna operación de gestión reescribe Estudio/PruebaEstudio ni sus snapshots.

## Funcionalidades aún no implementadas

1. Gestión de tipos con navegación, selección de pruebas existentes, formularios, resumen/confirmación, volver/cancelar y mensajes; no un admin genérico como sustituto de reglas del contrato.
2. Enforcement del permiso específico tanto al acceder como en cada envío directo; sin asumir que is_staff equivale al permiso ni alterar quién puede crear estudios en US 5.1.
3. Alta atómica con nombre normalizado/único y una o más pruebas válidas; preservar valores válidos y no publicar un tipo incompleto si falla la composición.
4. Edición atómica con detección de versión obsoleta, revisión del conflicto e incremento coordinado; al menos una prueba final; sin asignaciones duplicadas ni cambios históricos.
5. Desactivación y reactivación confirmadas, con versión vigente y validaciones, sin modificar estudios existentes.
6. Eliminación definitiva de tipos nunca usados, rechazo de cualquier uso histórico y alternativa de desactivación, con integridad concurrente.
7. Tests automatizados de esas operaciones, autorización, doble envío/conflictos entre editores, dos ordenaciones con creación de estudios, rollback y conservación histórica; y pasos de validación manual. Los tests actuales son infraestructura, no esos nuevos tests de aceptación.

Las rutas, organización concreta del escritor, confirmaciones y su validación, manejo de errores y matriz detallada de tests se definirán en plan después de revisar el diagnóstico. No se implementaron ni se simulan artefactos de diseño aquí.

## Revisión de los tres controles pendientes

La checklist anterior confundía aprobación formal con definición de requisitos y suponía un proveedor científico/modelos inexistentes. La confirmación actual del usuario cierra las decisiones funcionales, incluidas FR-018/019. Los escenarios y SC existentes cubren sus condiciones. Se actualiza a 16/16 documental con evidencia explícita, conservando íntegramente las notas anteriores bajo encabezado histórico.

Esto NO acredita aprobación formal global por el equipo ni permiso de implementar. La spec sigue Draft para revisión. La guía SDD pide revisar la spec antes de plan; Constitution exige aprobación del equipo antes de código de producto. No se inventa una puerta de aprobación externa para la calidad de la checklist ni un bloqueo por catálogo científico oficial.

## Preparación de speckit-plan

- Skill original leída en .agents/skills/speckit-plan/SKILL.md; no sustituida. No hay extensions.yml ni hooks registrados en este checkout.
- El contexto .specify/feature.json apunta a specs/012-gestionar-tipos-estudio. El verificador original --json --paths-only debe resolver esa feature sin escribir documentos.
- setup-plan.sh --json es el setup original del workflow, pero NO se ejecutó: copiaría el template de plan y el usuario pidió revisar primero. Tampoco se generaron research.md, data-model.md, contracts/, quickstart.md ni tasks.md de US 5.5.
- Preparación técnica completa: se puede ejecutar $speckit-plan cuando el usuario revise y autorice avanzar. La revisión/aprobación formal del equipo no se da por acreditada; deberá resolverse antes de implementar. Jira continúa pendiente administrativo, no una incógnita funcional para este diseño.
