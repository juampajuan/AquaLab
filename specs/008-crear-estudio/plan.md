<!-- Estado vigente: implementación y validación cerradas; las notas de evolución al final son históricas. -->

> Estado vigente de cierre: implementación y 40/40 tareas completadas; recorrido Chrome y carga demo confirmados por el usuario, sin observación directa del asistente. Detalle y límites en [cierre-tecnico.md](cierre-tecnico.md). Las notas de evolución anteriores se conservan como historial. Sin commit ni PR.
# Implementation Plan: Crear estudio sobre una muestra

**Branch**: `codex/008-crear-estudio` | **Date**: 2026-10-27 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/008-crear-estudio/spec.md`.

**Estado**: Plan implementado bajo autorización expresa posterior del usuario; cierre automatizado y validación manual se documentan en quickstart.md/tasks.md. Las secciones de planificación conservadas debajo son históricas y no sustituyen el estado vigente. Elaborado con speckit-plan 1.2.0 y su template original sobre main 6b29f43. El setup identifica la feature como 008-crear-estudio; la rama Git real incluye codex/.

## Summary

Crear estudios sobre Muestra integrada con selección de tipo, resumen y confirmación, asignaciones propias y snapshots históricos. Incorporar solo el esquema mínimo compartido del catálogo; US 5.5 administrará esas entidades después. Sin datos de producción, CRUD de catálogo, cálculos, informes ni transiciones futuras. FR-013/014 son decisiones definitivas del proyecto; datos y demostración son ficticios FIUBA, sin fuente científica externa pendiente.

La investigación está en [research.md](research.md), los campos en [data-model.md](data-model.md), el contrato compartido en [contracts/catalogo-compartido.md](contracts/catalogo-compartido.md) y el flujo en [contracts/crear-estudio-ui.md](contracts/crear-estudio-ui.md).

## Technical Context

**Language/Version**: Python 3.12; Django 5.2.18.
**Primary Dependencies**: ORM, forms, auth, signing, sessions, messages, templates, psycopg y Bootstrap ya existentes. Sin nuevas dependencias.
**Storage**: PostgreSQL 16; transacciones explícitas, advisory lock propio de estudios y bloqueo de fila del tipo.
**Testing**: pytest-django; PostgreSQL real en tests; fixtures factories de pruebas genéricas aisladas y tests de concurrencia con conexiones separadas.
**Target Platform**: Docker Compose Linux, escritorio web.
**Project Type**: Monolito Django con templates server-side.
**Performance Goals**: Sin SLA numérico aprobado. Consultar solo tipos disponibles, prefetch de pruebas y evitar cargar el catálogo científico entero por muestra; optimización tras medir. No se inventa un objetivo de laboratorio.
**Constraints**: Un estudio por solicitud confirmada, no por muestra/tipo; atomicidad, snapshots coherentes, versión confirmada, sesión y CSRF; cero datos sintéticos en producción.
**Scale/Scope**: Cinco modelos de dominio incluyendo asociación explícita de composición; dos apps (pruebas y estudios), tres migraciones de esquema entregadas; formulario y dos pasos de registro. Volumen real pendiente; bloqueo global de confirmaciones elegido por simplicidad a esta escala, revisable si aparece evidencia de contención.

## Constitution Check

| Principio | Evidencia vigente |
|---|---|
| I: spec primero | Aprobación de la spec por el equipo declarada por el usuario; autorización de implementar documentada en T001. Sin actas ni revisores inventados. |
| II: simplicidad | Django/ORM/forms/signing y stack existente; sin nuevas dependencias. |
| III: tests | Cobertura de los 20 FR y escenarios; suite general y JS revalidadas en cierre-tecnico.md. |
| IV: integridad | FK PROTECT, UUID único, asignación única, snapshots y transacción con locks. |
| V: seguridad | Cuenta activa, sesión, CSRF y confirmación firmada; carga demo solo explícita en desarrollo/QA. |
| VI/UI | Español, Bootstrap/base.html y confirmación previa. Recorrido Chrome informado por el usuario. |

No se modifica Constitution. La aprobación de código por otro integrante y CI remoto corresponden al futuro PR, no se simulan en este cierre.

## Project Structure

### Documentation (this feature)

spec.md; checklists/requirements.md; plan.md; research.md; data-model.md; contracts/catalogo-compartido.md; contracts/crear-estudio-ui.md; quickstart.md. tasks.md contiene las 40 tareas y su evidencia de cierre.

### Source Code (repository root) — ubicaciones implementadas

- pruebas/models.py: Prueba mínima; pruebas/migrations/0001_initial.py prevista.
- estudios/models.py: TipoEstudio, TipoEstudioPrueba, Estudio, PruebaEstudio; estudios/migrations/0001_initial.py (catálogo) y 0002_estudio.py (estudios) previstas.
- estudios/forms.py, servicios.py, catalogo.py (lectura coherente), confirmaciones.py (firma/recuperación), urls.py, views.py; templates/estudios/crear_form.html y crear_confirmar.html dentro de la app.
- estudios/tests/conftest.py, test_modelos.py, test_registro.py, test_servicio.py, test_concurrencia.py, test_catalogo_contrato.py y test_confirmaciones.py.
- config/settings.py y urls.py: solo integración de apps y rutas al implementar; templates/base.html e inicio.html: enlace Crear estudio.
- muestras/, usuarios/ y clientes/: reutilizados; sin alterar contrato ni migraciones existentes.

**Structure Decision**: La asociación explícita TipoEstudioPrueba permite unicidad y protección de referencias. US 5.5 incorporará sus servicios/CRUD sobre esos mismos modelos y no recreará el esquema inicial.

## Flujo transaccional propuesto

1. Preparar resumen con UUID generado por servidor y token firmado ligado a usuario, sesión (huella HMAC, nunca sessionid expuesto), muestra, tipo y versión. Persistir borrador solo para edición; la prueba de qué se confirmó viaja en el token, no se infiere del borrador más reciente.
2. Confirmar: verificar sesión, CSRF, firma, vigencia de 1 hora y vínculo usuario/sesión. Un token vencido exige nueva revisión; jamás crea silenciosamente otra operación.
3. Dentro de atomic: tomar advisory transaction lock 5_100_001, diferente del de muestras; buscar Estudio por UUID. Si existe y corresponde al mismo creador/muestra/tipo, devolverlo sin revalidar catálogo ni cambiar snapshots. Si la misma clave se presenta para otra selección o usuario, rechazar.
4. Si no existe: bloquear TipoEstudio por select_for_update, verificar existencia/activo/versión exacta; consultar su composición y todas sus pruebas válidas. Muestra debe existir; no se filtra por cliente activo. No se llama registrar_muestra.
5. Si cambió versión: salir sin crear, obtener configuración coherente nueva, mostrar resumen nuevo y token nuevo conservando UUID lógico. Reenviar el token viejo nunca acepta la versión nueva. Si está inactivo/vacío/inexistente, informar y volver a selección.
6. Crear Estudio con snapshots desde la fila bloqueada, estado pendiente_analisis, creador/hora automáticos y UUID obligatorio; crear PruebaEstudio para cada referencia. Confirmar todo o revertir todo. Fallas DatabaseError se capturan fuera del atomic; no se tragan dentro de una transacción rota.
7. Tras commit: éxito con identificador y PI, formulario vacío. Reintentos con token vigente devuelven el mismo estudio aunque el catálogo haya cambiado después. Nueva solicitud obtiene otro UUID.

US 5.5 debe bloquear la misma fila del tipo antes de leer versión para editar, desactivar, reactivar o eliminar, y mantener bloqueo hasta terminar datos, composición y aumento de versión. No puede escribir M2M fuera del protocolo. Orden común: lock de solicitud (solo creación) antes del lock de tipo; nunca el inverso. Un único tipo por operación. Las pruebas científicas mínimas no tienen edición/eliminación desde esta historia; referencias PROTECT evitan pérdida de catálogo usado.

## Mapa previsto de tests

| Spec/escenario | Archivo previsto y comprobación |
|---|---|
| US1 1/2 | test_registro.py: selección por PI y ficha, solo tipos activos, resumen con pruebas exactas. |
| US1 3/4 | test_registro.py: nada antes de confirmar; estado, selección y éxito exactos. |
| US1 5 | test_registro.py: volver conserva; cancelar no crea cabecera/asignaciones. |
| US1 6 y FR-018 | test_catalogo_contrato.py: renombrar, editar/vaciar descripción, modificar composición y desactivar; historial y asignaciones permanecen; texto vacío preservado. |
| US1 7 | test_servicio.py: PK, creador y fecha/hora automáticos; ignorar/rechazar datos manipulados. |
| US1 8 y US2 7 | test_servicio.py: nuevas solicitudes de distinto o mismo tipo crean estudios independientes. |
| US2 1/2 | test_registro.py: cada faltante, muestra/tipo inexistentes, tipo vacío/inactivo y prueba inválida; conservar datos válidos. |
| US2 3 y FR-020 | test_registro.py: catálogo o muestras vacíos, sin propuestas ficticias. |
| US2 4 | test_servicio.py: falla al crear una asignación revierte cabecera, asignaciones y UUID; reintento funciona. |
| US2 5 | test_concurrencia.py: secuencial y concurrente mismo UUID → mismo identificador y un conjunto; UUID distintos → estudios distintos. |
| US2 6 | test_registro.py: anónimo, cuenta no aprobada y POST sin CSRF; sin registros. |
| US2 8 | test_registro.py: cliente ya inactivo o desactivado en revisión permite crear; no se reactiva. |
| US2 9/10 | test_registro.py: versión cambia, resumen/token nuevo; POST viejo sigue sin crear; nuevo token crea si sigue vigente. |
| US2 11 | test_concurrencia.py: coordinar ambas ordenaciones lock editor/creador; resultado anterior íntegro o conflicto, nunca mezcla. |
| FR-019 | test_modelos.py: constraints código/nombre, límites de campos, PROTECT, asignación duplicada, versión positiva. |
| Seguridad del contrato | test_registro.py: token manipulado, usuario/sesión distintos, token ausente/vencido; error sin creación ni exposición de otra solicitud. |
| Idempotencia tras éxito | test_servicio.py: reenvío después de desactivar tipo devuelve historial original; colisión clave con otra selección rechazada. |
| Textos durante revisión | test_registro.py: cambio solo nombre/descripcion incrementa versión y exige nueva aceptación. |

Pruebas concurrentes con django_db(transaction=True), conexiones por hilo, barreras/events con timeouts y join acotado; comprobar hilos terminados y errores recogidos. Helpers mutantes solo de test simulan el futuro escritor del catálogo conforme al protocolo; no implementan CRUD de US 5.5 ni validan que ese CRUD ya exista. Tests de aplicación y CI: pendientes, no ejecutados en este diseño.

## Complexity Tracking

Sin excepción implementativa a la Constitution. El esquema mínimo compartido está expresamente autorizado por usuario; no se implementa la gestión de US 5.5. El advisory lock global serializa confirmaciones, una limitación deliberada frente a mecanismos por clave más complejos. La aprobación formal del equipo no está acreditada y sigue siendo condición antes de código de producto.

## Dependencias abiertas y puerta siguiente

- Administración futura US 5.5 sobre el mismo esquema y protocolo atómico/versionado, sin duplicar catálogo. Su worktree no se modifica.
- Jira: referencia administrativa pendiente, no se inventa un código.
- Futuro PR: CI remoto y revisión de otro integrante según Constitution; no realizados ni requeridos para un commit local.
- No hay proveedor científico externo pendiente: el manifiesto académico fue aprobado y el usuario informa que la carga y recorrido Chrome funcionaron. Detalle y límites en cierre-tecnico.md.

## Precisión de revisión final

La confirmación firmada no reemplaza el estado pendiente por UUID para una operación aún no persistida: después de cancelar, un token viejo no crea otra vez. El lookup idempotente de resultado propio ocurre antes de exigir borrador pendiente; nunca depende de que la sesión se haya borrado. Para expiración, recuperar la misma operación conserva UUID y no crea automáticamente otra solicitud; ver contrato UI. Incluir tests de cancelación seguida de POST viejo, reintento tardío y recuperación con mismo UUID. Los agentes revisores no detectaron contradicciones bloqueantes entre modelo, locks y contratos; sus observaciones se documentan, no acreditan ejecución.

## Revisión técnica previa a tasks

Se separa el esquema de catálogo (estudios/0001_initial) del esquema consumidor (estudios/0002_estudio) para entregar infraestructura compartida antes de las tareas US1. Se precisan el resumen inmutable por versión y la acción de recuperación de token vencido, con identidad y UUID conservados; ver contrato UI. La generación de tareas documentales está autorizada en la instrucción actual; ninguna autorización de implementar se infiere de ello. No se modifica la Constitution ni US 5.5.

Generación documental de tasks autorizada en la revisión posterior: tasks.md contiene tareas pendientes, sin sustituir la aprobación formal previa a código. El análisis cruzado se ejecuta después de generar tareas conforme al skill original; no es evidencia de tests de aplicación.

## Confirmación vigente de implementación — 27/10/2026

El usuario confirma expresamente en este chat que la especificación fue aprobada por el equipo y autoriza implementar el plan/tareas revisados. Esta declaración es la evidencia disponible para T001; no se aportan ni inventan acta, enlace Jira o nombres de revisores. T001 no exige un comprobante externo específico. FR-013/014 quedan como decisiones funcionales definitivas del proyecto, sin atribuir validación al laboratorio; esta actualización sustituye sus etiquetas históricas de supuesto/validación pendiente. La precarga científica oficial y sus responsables siguen pendientes para uso real. Se autoriza desarrollo incremental sin commits/push/PR/merge ni cambios en US 5.5.


## Estado vigente de cierre técnico

La evidencia de aprobación es la confirmación del usuario en este chat, no un acta externa. FR-013 y FR-014 son decisiones funcionales definitivas del proyecto, sin atribuir validación directa al laboratorio; ya no requieren validación externa para implementar esta versión. La checklist documental está en 16/16. Continúan abiertas la fuente/responsable/mapeo de la precarga científica oficial, la referencia administrativa a Jira y la implementación futura del escritor US 5.5 conforme al contrato compartido. La validación manual Chrome queda pendiente; no se simula aprobación de código, CI remoto ni revisión de un compañero.

El mapa de escenarios se materializa en test_registro, test_servicio, test_confirmaciones, test_catalogo_contrato, test_modelos y test_concurrencia. La suite cubre selecciones/rechazos, solicitudes del mismo y distinto tipo, auditoría no manipulable, historial, rollback, reintento, seguridad y ambos órdenes del lock. La concurrencia exige PostgreSQL y base test_ mediante una fixture autouse, con conexiones independientes y sincronización por eventos/barrera. El escritor de catálogo de los tests solo acredita el protocolo requerido a US 5.5.

Límite técnico adoptado: hasta 20 resúmenes pendientes por sesión para acotar su tamaño; al alcanzarlo se informa un error sin crear. TTL firmado de una hora y recuperación conservando UUID según el contrato. El advisory lock global serializa las creaciones; medir contención si aumenta el volumen. No se incorporaron dependencias nuevas, seed de producción ni cambios en muestras.


## Aclaración académica vigente — decisión del usuario

AquaLab es un proyecto académico FIUBA. Los datos de desarrollo y demostración son ficticios y deben identificarse como DEMO, sin atribuirles validez científica. No hay laboratorio real ni catálogo científico oficial externo pendiente; las referencias anteriores a esa dependencia quedan sustituidas por esta decisión. Se mantienen las reglas funcionales, separación Prueba/TipoEstudio, snapshots y contrato con US 5.5. La carga demo será explícita, reproducible e idempotente, separada de migraciones y arranque; el mecanismo y manifiesto están propuestos en [propuesta-datos-demo.md](propuesta-datos-demo.md), pendientes de revisión antes de implementar o modificar datos. No se cargaron datos ni se completó T037 con esta actualización documental.


Actualización de ejecución demo: el usuario aprobó el manifiesto y el mecanismo; cargar_demo_us51 está implementado con simulación por defecto, guardas de desarrollo/QA y escritura únicamente mediante --aplicar. No se ejecutó --aplicar sobre la base local. La validación manual sigue pendiente; ver quickstart.md para comandos y pruebas. Esta nota sustituye el estado anterior de propuesta pendiente de revisión.
