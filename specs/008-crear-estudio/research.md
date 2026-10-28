# Research: US 5.1 — decisiones de diseño

> Estado vigente de cierre: implementación y 40/40 tareas completadas; recorrido Chrome y carga demo confirmados por el usuario, sin observación directa del asistente. Detalle y límites en [cierre-tecnico.md](cierre-tecnico.md). Las notas de evolución anteriores se conservan como historial. Sin commit ni PR.

Fecha: 2026-10-27. Investigación basada en código de main 6b29f43, Constitution, specs locales y documentación primaria. No cambia código. Las elecciones de campos/locks son diseño revisable, no decisiones científicas del laboratorio.

## R1 — Base compartida mínima

**Decisión**: pruebas.Prueba con identidad/código único/nombre; estudios.TipoEstudio y asociación explícita TipoEstudioPrueba; estudios.Estudio y PruebaEstudio. US 5.5 es dueña funcional del catálogo y reutiliza estas entidades.
**Motivo**: Una app por módulo, sin duplicación ni dependencia de CRUD futuro. El usuario autoriza que US 5.1 entregue ese prerrequisito.
**Alternativas**: catálogo JSON sin persistencia o modelos duplicados en cada feature: rechazados por integridad y futura migración incompatible. Modelo científico completo: fuera de alcance y datos no disponibles.

## R2 — Idempotencia persistente

**Decisión**: UUID obligatorio único en Estudio y advisory xact lock global 5_100_001 antes de cualquier lectura/creación por solicitud. Verificar identidad creador/muestra/tipo; reenvío válido devuelve el resultado previo.
**Motivo**: No hay fila de Estudio aún para bloquear en la primera confirmación. La unicidad es defensa persistente; lock serializa decisiones y evita carreras de lectura. No depende de borrar la sesión.
**Alternativas**: solo sesión o botón deshabilitado: no protegen requests simultáneos. Tabla de solicitudes separada: innecesaria para este alcance; por-clave hash locks: más complejidad que el patrón ya usado en muestras, revisable por carga. No reutilizar el lock de muestras.

## R3 — Catálogo coherente y snapshots

**Decisión**: bloquear fila TipoEstudio en atomic, comprobar versión y copiar datos/asignaciones bajo ese bloqueo. Todos los escritores futuros deben tomar el mismo lock antes de datos o M2M y aumentar versión.
**Motivo**: Bloquear solo lectura de la relación o comparar fuera de atomic permite configuraciones mezcladas. Snapshots de texto y relaciones PruebaEstudio independientes preservan historial; snapshots científicos completos no solicitados.
**Alternativas**: lectura dinámica M2M para estudios: rompe historial. Signals para incrementar versión: no garantizan todos los caminos de escritura y no sustituyen protocolo.

## R4 — Confirmación firmada

**Decisión**: token de Django signing con salt estudios.creacion.v1, UUID, usuario, huella HMAC de sesión, muestra, tipo y versión; vigencia técnica propuesta de 3600 s. No exponer sessionid ni snapshots enviados por cliente como fuente de verdad. Firma se valida además de sesión y CSRF.
**Motivo**: Tras refrescar resumen por conflicto, un POST viejo no debe confirmar silenciosamente el nuevo borrador. La versión firmada prueba qué configuración revisó el usuario; el servidor copia los valores desde el catálogo bloqueado.
**Alternativas**: solo request.session actual: no distingue confirmación vieja. Token cliente sin firma: manipulable. El plazo es decisión técnica revisable, no requisito del laboratorio.

## R5 — Código/longitudes y permisos

**Decisión**: código Prueba 50, nombre Prueba 150, nombre tipo 150, descripción TextField blank; versión positiva desde 1. Código se recorta y compara exacto; tipo ignora mayúsculas y espacios laterales conforme a decisión del usuario. Conservar diferencias de tildes/espacios internos.
**Motivo**: Límites acotados consistentes con dominio existente; no inferir convención científica de códigos. No añadir active/validación científica a Prueba sin requisitos.
**Alternativas**: códigos case-insensitive inventados: no acordados. Crear rol responsable técnico: innecesario; permiso específico futuro gestionar_catalogo. Crear estudios exige solo cuenta activa autenticada, no permiso catálogo.

## R6 — Migraciones y datos

**Decisión**: tres migraciones de esquema previstas (pruebas inicial, catálogo inicial y consumidor estudios); ninguna de datos sintéticos. Tests factories en estudios/tests/conftest.py con códigos TEST-*, nombres Prueba de test A/B y Tipo de test; no análisis reales, valores ni fórmulas.
**Motivo**: Tests estructurales no requieren contenido científico aprobado. US 5.5 extenderá migraciones existentes sin recrear tablas. Nada se aplica ahora.
**Alternativas**: fixtures autoload o seeds en producción: rechazados. Esperar CRUD completo: bloqueo innecesario. Precarga oficial continúa independiente.

## Fuentes primarias consultadas

- [Django 5.2: atomic y límites de transacción](https://docs.djangoproject.com/en/5.2/topics/db/transactions/).
- [Django 5.2: select_for_update y tests transaccionales](https://docs.djangoproject.com/en/5.2/ref/models/querysets/#select-for-update).
- [Django 5.2: firma criptográfica](https://docs.djangoproject.com/en/5.2/topics/signing/).
- [PostgreSQL 16: locks de fila y advisory locks](https://www.postgresql.org/docs/16/explicit-locking.html).

No quedan incógnitas técnicas bloqueantes: las decisiones anteriores fijan un diseño para revisión. Las validaciones externas no se declaran obtenidas. Se consultaron agentes de investigación de catálogo/concurrencia conforme al skill; no editaron archivos.

## R7 — Correcciones de revisión previa a tareas

**Decisión**: tres migraciones de esquema previstas: pruebas/0001_initial, estudios/0001_initial (catálogo) y estudios/0002_estudio (consumidor). Resumen y token proceden de la misma copia coherente; GET no mezcla una configuración nueva con una firma vieja. Recuperación expiración usa acción separada sin guardar y conserva UUID.
**Motivo**: evita dependencias hacia modelos aún no definidos en la fase compartida y aceptación incorrecta de datos no revisados.
**Alternativas**: una sola migración estudios requiere terminar todos los modelos antes de validar catálogo; recuperación implícita en confirmar oculta la separación entre consulta y escritura.


## Aclaración académica vigente — decisión del usuario

AquaLab es un proyecto académico FIUBA. Los datos de desarrollo y demostración son ficticios y deben identificarse como DEMO, sin atribuirles validez científica. No hay laboratorio real ni catálogo científico oficial externo pendiente; las referencias anteriores a esa dependencia quedan sustituidas por esta decisión. Se mantienen las reglas funcionales, separación Prueba/TipoEstudio, snapshots y contrato con US 5.5. La carga demo será explícita, reproducible e idempotente, separada de migraciones y arranque; el mecanismo y manifiesto están propuestos en [propuesta-datos-demo.md](propuesta-datos-demo.md), pendientes de revisión antes de implementar o modificar datos. No se cargaron datos ni se completó T037 con esta actualización documental.


Actualización de ejecución demo: el usuario aprobó el manifiesto y el mecanismo; cargar_demo_us51 está implementado con simulación por defecto, guardas de desarrollo/QA y escritura únicamente mediante --aplicar. No se ejecutó --aplicar sobre la base local. La validación manual sigue pendiente; ver quickstart.md para comandos y pruebas. Esta nota sustituye el estado anterior de propuesta pendiente de revisión.
