# Contrato técnico — escritor único de tipos

Estado: propuesto para revisión, no implementado. [Plan](../plan.md), [modelo existente](../data-model.md), [investigación](../research.md). No altera servicios.py:crear_estudio ni catalogo.py.

## Entradas y resultados

Módulo propuesto estudios/gestion_tipos.py. Entrada pública gestionar_tipo_estudio con argumentos nombrados usuario, operacion, tipo_id, version_esperada y datos. Operaciones permitidas: crear, editar, desactivar, reactivar, eliminar. No operaciones batch.

| Operación | Entrada autorizada |
|---|---|
| crear | usuario; nombre/descripcion/prueba_ids. tipo_id/version_esperada ausentes; activo fijo True. |
| editar | usuario; tipo_id y versión revisada obligatorios; nombre/descripcion/prueba_ids. No tomar activo del POST. |
| desactivar/reactivar | usuario; tipo_id/versión revisada; destino definido por la operación, sin reemplazar textos o composición por campos del cliente. |
| eliminar | usuario; tipo_id/versión revisada; uso siempre consultado de nuevo bajo lock, no un booleano del cliente. |

Validar usuario autenticado/activo y permiso antes de consultar el tipo. Operación inválida o datos mal tipados: error controlado, no consultas/mutaciones arbitrarias. Normalizar IDs a conjunto de enteros positivos, rechazar referencias inexistentes; nombre strip obligatorio <=150, comparación de unicidad case-insensitive con excepción de su propia PK; descripción opcional, cadena vacía en lugar de NULL, sin strip automático ni cambios científicos. La forma web valida pero no sustituye estas reglas de servicio.

Resultado propuesto: estructura inmutable con estado creado/actualizado/desactivado/reactivado/eliminado/sin_cambios, tipo_id y version_final; para eliminado, version_final=null (puede conservar versión previa como dato informativo separado). Salir del atomic antes de devolver éxito. Nunca devolver una instancia en memoria alterada por un rollback como si fuera persistida.

Errores de dominio: NoAutorizado, TipoNoExiste, DatosTipoInvalidos (errores por campo), VersionTipoDesactualizada (configuración vigente coherente, sin guardar), TipoUtilizado y FalloPersistencia. Los nombres exactos forman parte del futuro código de este módulo; no requieren nuevas clases de modelos. La vista traduce el resultado después de commit y no hace escrituras adicionales de catálogo.

## Algoritmo acordado

1. Verificar usuario/permiso y forma de entrada, sin confiar en flags de autorización de la vista.
2. Dentro de atomic, crear nuevo tipo solo tras validar datos o cargar tipo existente con select_for_update, sin joins que bloqueen otras entidades innecesarias. Inexistente → error.
3. Para existente, comparar version_esperada con version actual ANTES de no-op/guardado. Diferencia → copiar configuración vigente completa bajo el lock y lanzar conflicto fuera sin DML. El lector administrativo admite activo=False y conjunto vacío para poder informar/reparar/retirar.
4. Crear/editar/reactivar: validar una o más pruebas existentes. Crear/editar validan nombre/descripcion y unicidad. Desactivar conserva composición incluso si es inválida; eliminar no necesita repararla. La existencia final también queda respaldada por FK: una Prueba que se borre concurrentemente antes de asociar produce rechazo/rollback controlado.
5. Eliminar: tipo.estudios.exists sin filtro de estado o fecha, manteniendo lock del tipo. Si hay cualquiera, TipoUtilizado y alternativa de desactivación. Si no, delete del tipo con su through; no borrar Prueba ni ninguna fila de estudio. PROTECT sigue vigente.
6. Otras operaciones: comparar configuración canónica; si no cambia, devolver sin_cambios sin DML; si cambia, escribir campos, reemplazar composición solo en alta/edición y publicar versión +1 exactamente una vez. Alta version=1.
7. Si cualquier validación o persistencia falla, salir del atomic mediante excepción. Capturar/traducir IntegrityError, ProtectedError o DatabaseError FUERA del bloque fallido; reconsultar estado si la UI necesita mostrarlo. No continuar usando una transacción rota. No autocommit parcial ni mensajes de éxito anticipados.

## Concurrencia y reintentos

- Unicidad en altas/ediciones de tipos distintos: prevalidación no reemplaza UNIQUE Lower(nombre); la transacción perdedora recibe error de nombre duplicado sin datos parciales.
- Dos modificaciones efectivas sobre la misma versión: lock serializa; primera publica v+1 y segunda rechaza stale. Dos no-op vigentes pueden devolver sin_cambios; no son dos cambios aceptados ni publican versiones.
- Versión vieja cuyos datos coinciden con los actuales: siempre conflicto. No-op se valida después de comprobar versión y reglas de operación.
- Crear estudio toma advisory 5_100_001 → lock TipoEstudio. El escritor toma solo lock TipoEstudio, nunca advisory después de ese lock. Mantener orden; transacción sobre un tipo.
- Crear antes de borrar: exists ve la asociación y rechaza. Borrar antes de crear: lectura bloqueada del consumidor ve inexistencia y rechaza. Igual coordinación para editar/desactivar y consumir versiones.
- Retrys: alta repetida puede dar duplicado; edición/disponibilidad repetida con versión anterior, conflicto; borrado repetido, inexistente; no-op vigente repetido, sin_cambios. No se implementa un UUID UNIQUE administrativo ni se promete recuperar un resultado exitoso persistente como en US 5.1.

## Historial y lector administrativo

No escrituras sobre Estudio/PruebaEstudio, snapshots, autor/fecha, Prueba ni modelos de muestras. Listado de gestión puede ser lectura normal paginada; preparación/resumen y estado para conflicto usan lector administrativo coherente sobre las mismas tablas y lock del tipo. No usar leer_configuracion para administrar inactivos: su contrato consumidor exige activo/no vacío y debe permanecer sin cambios.

## Verificación futura del contrato

Tests de servicio prueban campos, constraints, no-op con captura de queries sin UPDATE/INSERT/DELETE, rollback después de cabecera/M2M, uso histórico y tipos inactivos. Concurrencia en PostgreSQL transaccional por hilos, ambas ordenaciones del lock e IntegrityError de nombres. Ver la matriz del plan; estos tests todavía no existen ni se ejecutaron en esta fase documental.
