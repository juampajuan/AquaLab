# Contrato compartido: catálogo mínimo y US 5.5

> Estado vigente de cierre: implementación y 40/40 tareas completadas; recorrido Chrome y carga demo confirmados por el usuario, sin observación directa del asistente. Detalle y límites en [cierre-tecnico.md](../cierre-tecnico.md). Las notas de evolución anteriores se conservan como historial. Sin commit ni PR.

Estado: base persistente mínima implementada en US 5.1; gestión de US 5.5 pendiente. Fuente: contrato funcional adoptado por usuario y spec local de US 5.5 leída como referencia; no se modifica su rama ni se exige que esté integrada.

## Responsabilidades y lectura

- pruebas.Prueba es la única representación mínima: id estable, codigo único, nombre; no nuevo modelo científico completo.
- estudios.TipoEstudio y TipoEstudioPrueba son catálogo compartido; US 5.1 entrega su base persistente autorizada; US 5.5 añade gestión posteriormente sobre las mismas tablas.
- US 5.1 crea Estudio, PruebaEstudio y snapshots; US 5.5 no reescribe esas filas al editar tipos.
- Consulta de configuración devuelve tipo id, nombre, descripcion, version y conjunto de prueba id/codigo/nombre. La interfaz solo devuelve tipos activos; activo se valida bajo el lock y no se incluye en el resultado. Datos y conjunto deben leerse coherentemente bajo bloqueo al preparar/confirmar; el conjunto tiene al menos una prueba.

## Protocolo de escrituras obligatorio para futura US 5.5

atomic → bloquear TipoEstudio por PK → comparar versión revisada → validar valores y conjunto final → guardar textos/activo/composición y aumentar version una vez → commit. Desactualización devuelve conflicto y configuración actual, nunca sobrescribe. No escribir M2M fuera de este protocolo, ni mediante admin genérico o queryset.update no coordinado. La prueba científica no tiene mutaciones desde estas historias; su futura gestión debe preservar referencias y pasar por diseño propio.

El creador US 5.1 adquiere primero el advisory transaction lock 5_100_001 y después el lock de ese tipo. El escritor US 5.5 solo necesita el segundo; nunca adquiere el lock de creación después de tener el tipo. La fila se mantiene bloqueada hasta asignaciones y snapshots completos. Distintos tipos podrán editarse independientemente; confirmaciones de estudios se serializan inicialmente.

Desactivar invalida versión y nuevas confirmaciones; un estudio ya creado se conserva. Si se aprueba eliminación de nunca utilizados, bloquear tipo, comprobar estudios incluyendo históricos y eliminar dentro de la transacción; FK PROTECT es defensa adicional. La creación anterior gana y bloquea borrar, o borrar primero hace que crear rechace tipo inexistente. Reactivar/eliminar no se implementan en US 5.1.

## Confirmación de estudio

Entrada: selección de muestra/tipo, token firmado con UUID/usuario/huella sesión/versión. Snapshot siempre desde datos del servidor, no campos libres del cliente. Versión diferente exige resumen y token nuevos, sin crear. Cambios de textos, activo y composición aumentan versión; el protocolo es conservador y exige revisar incluso cambios de solo descripción para no guardar textos no revisados.

Tras éxito el UUID único identifica el estudio; el reenvío coincidente devuelve su ID sin sobrescribir historial. Mantener UUID al refrescar la misma solicitud por conflicto; generar otro al iniciar solicitud deliberada nueva. La firma anterior jamás se interpreta como aprobación de la nueva versión. Firma expirada exige revisión, no una creación automática.

## Compatibilidad y pendientes

US 5.5 debe reutilizar módulos, claves e invariantes de [data-model.md](../data-model.md), sin segunda Prueba/TipoEstudio, sin recrear migraciones iniciales y sin sembrar datos sintéticos. No se congelan fórmulas/unidades/límites: fuera del alcance acordado. Los textos históricos sí quedan congelados.

La spec de US 5.5 conserva orden anterior por restricción de no modificarla. Al retomarla deberá anotarse nueva secuencia y referenciar esta base; esa sincronización aún no ocurrió. Los escenarios de CRUD de US 5.5 no se declaran probados por helpers de test del consumidor.


## Interfaces y esquema entregados — cierre técnico

- pruebas.Prueba: id BigAutoField, codigo CharField(50) único exacto y recortado, nombre CharField(150) recortado. Sin atributos científicos adicionales.
- estudios.TipoEstudio: id, nombre CharField(150) único por Lower tras recorte, descripcion TextField opcional, activo, version PositiveBigInteger >=1 y pruebas mediante TipoEstudioPrueba con unicidad (tipo, prueba).
- Permiso declarado: estudios.gestionar_catalogo. No se asigna automáticamente ni habilita pantallas de gestión; crear estudios requiere autenticación activa, no ese permiso.
- estudios.catalogo.leer_configuracion(tipo_id): devuelve diccionario coherente id/nombre/descripcion/version/pruebas (cada prueba id/codigo/nombre) bajo atomic y select_for_update. Inactivo, inexistente o conjunto vacío: CatalogoNoDisponible.
- configuracion_bloqueada(tipo) es interna: exige que el llamador mantenga el lock del tipo dentro de atomic. crear_estudio usa esa misma lectura para validar la versión y copiar las asignaciones.
- Migraciones entregadas: pruebas/0001_initial.py, estudios/0001_initial.py (catálogo y composición), estudios/0002_estudio.py (Estudio y PruebaEstudio). Esta última depende de muestras/0002_clave_borrador y del usuario swappable. Ninguna contiene RunPython ni datos científicos.
- Estudio conserva tipo_nombre_snapshot, tipo_descripcion_snapshot y tipo_version_snapshot propios; UUID único persistente. PruebaEstudio tiene unicidad (estudio, prueba). No existe unicidad (muestra, tipo).

La versión no se incrementa automáticamente por save/M2M: US 5.5 debe implementar su escritor atómico con bloqueo, comparación de versión e incremento una vez por cambio efectivo de nombre, descripción, activo o composición. Sus no-op y rollback no incrementan versión. Los helpers que prueban este contrato son exclusivamente de tests; no acreditan que US 5.5 esté implementada. No usar admin genérico ni escrituras directas que evadan el protocolo. Esta obligación continúa abierta para la futura integración.


## Aclaración académica vigente — decisión del usuario

AquaLab es un proyecto académico FIUBA. Los datos de desarrollo y demostración son ficticios y deben identificarse como DEMO, sin atribuirles validez científica. No hay laboratorio real ni catálogo científico oficial externo pendiente; las referencias anteriores a esa dependencia quedan sustituidas por esta decisión. Se mantienen las reglas funcionales, separación Prueba/TipoEstudio, snapshots y contrato con US 5.5. La carga demo será explícita, reproducible e idempotente, separada de migraciones y arranque; el mecanismo y manifiesto están propuestos en [propuesta-datos-demo.md](../propuesta-datos-demo.md), pendientes de revisión antes de implementar o modificar datos. No se cargaron datos ni se completó T037 con esta actualización documental.


Actualización de ejecución demo: el usuario aprobó el manifiesto y el mecanismo; cargar_demo_us51 está implementado con simulación por defecto, guardas de desarrollo/QA y escritura únicamente mediante --aplicar. No se ejecutó --aplicar sobre la base local. La validación manual sigue pendiente; ver quickstart.md para comandos y pruebas. Esta nota sustituye el estado anterior de propuesta pendiente de revisión.
