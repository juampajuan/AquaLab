# Modelo de datos de lectura — Feature 033

No se crean entidades persistentes, campos, índices ni migraciones. Este documento describe las relaciones existentes y los conjuntos derivados que se consultarán; no propone modificar el modelo de dominio.

## Entidades existentes

| Entidad | Identidad y relaciones relevantes | Datos utilizados |
|---|---|---|
| Usuario | pk; grupos y permisos existentes | is_active, pertenencia a Bioquímicos, has_perm de dashboard y operaciones; Administradores independiente. |
| Muestra | pk / numero_pi único; Cliente y Origen | nombre, fecha_ingreso, cliente y origen para últimas muestras y listados. |
| Estudio | pk; Muestra, TipoEstudio y PruebaEstudio | estado; fecha_creacion para filtros; tipo_nombre_snapshot para conservar historia. |
| Prueba | pk / código único | código, nombre, es_calculada, unidad; no confundir tipo de fórmula con si admite medición propia. |
| PruebaEstudio | pk; Estudio y Prueba; pareja estudio/prueba única | estado Pendiente, Cargada o Completada; enlaces a medicion, resultado y validaciones. |
| Medicion | pk; OneToOne con PruebaEstudio, protegida | dato de entrada; no es la raíz del contador de validación. |
| Resultado | pk; OneToOne con PruebaEstudio, protegida | valor Decimal y unidad guardada; valor_mostrado para presentación. Una identidad de resultado aporta una unidad al conteo. |
| Validacion | pk; ForeignKey a PruebaEstudio | anulada; a lo sumo una no anulada por asignación. Historial preservado. |
| Informe | pk / número; relación con Estudio | emisión existente; la regla canónica para listo excluye estado Informe generado. |
| FirmaProfesional | relación con Usuario | firma/matrícula necesarias al emitir; no filtran los estudios preparados. |

## Conjuntos derivados canónicos

### Asignaciones que admiten carga pendiente

Predicado de asignación existente: `estado=PENDIENTE` y `prueba.es_calculada=False`. Se comparte con `asignaciones_para_medir` actual sin alterar orden ni filtros de dominio. Un estudio cuenta si `admite_mediciones` (Pendiente de análisis o En proceso) y existe alguna de esas asignaciones del estudio. Identidad contada: **Estudio.pk**, una sola vez incluso con varias asignaciones.

No agregar filtros por Prueba.activa, tipo de fórmula, cliente activo o creador. Tampoco deducir el pendiente por ausencia de Resultado. Los estados y `es_calculada` de la regla actual son la autoridad; no se inventa otro estado de carga.

### Resultados pendientes de validar

Raíz: Resultado existente. Su asignación debe estar Cargada, el estudio no debe estar en Informe generado y no debe existir una validación vigente (`anulada=False`) de esa asignación. Identidad contada: **Resultado.pk**. Resultado sin validación vigente no basta si la asignación no está Cargada.

Incluir pruebas calculadas con resultado y resultados recalculados que volvieron a Cargada. Excluir asignaciones sin resultado y resultados ya validados. Las validaciones anuladas no bloquean el retorno al pendiente. No unir todas las validaciones para contar: usar ausencia por Exists evita multiplicación de filas históricas.

Para mostrar agrupado, restringir las asignaciones a aquellas cuyo resultado esté en este queryset. Cada resultado tiene exactamente una asignación y cada asignación un solo resultado; por ello agrupar por estudio no modifica la cantidad total. Identificar estudio y código/nombre de Prueba en el destino.

### Estudios preparados para informar

Usar `informes.servicios.estudios_para_informar('', True)`: `total_pruebas > 0`, `pruebas_completadas = total_pruebas`, estado distinto de Informe generado. Identidad contada: **Estudio.pk**. No reemplazar por Finalizado ni exigir firma del usuario en este conjunto. Se verifica paridad con `motivo_para_no_informar` sin copiar ni cambiar la regla de emisión.

## Relaciones e invariantes conservados

- Un Estudio puede contar una vez para mediciones y aportar varios Resultados a validación al mismo tiempo. Las unidades no se suman como si fueran equivalentes.
- Una prueba Completada tiene validación vigente según el flujo actual; Cargada con resultado requiere validación. Una combinación anómala Cargada con validación vigente se excluye del nuevo contador conforme al contrato, sin intentar reparar datos desde un GET.
- Corregir o borrar mediciones antes de emitir puede recalcular o retirar resultados y anular validaciones, siguiendo los servicios existentes. No se introducen transiciones nuevas. Inicio solo refleja las transiciones ya confirmadas.
- Emitir sigue cambiando el Estudio a Informe generado; deja de participar en los tres pendientes y se mantienen sus protecciones.
- No cambiar Decimal, unidades, snapshots, constraints, on_delete ni historial.

## Estructuras transitorias para vistas

- **Indicador**: nombre estable, título en español, cantidad entera no negativa, URL producida con reverse. Solo los correspondientes al rol se calculan y renderizan.
- **Selección de búsqueda**: formulario con q, desde, hasta, estado, pendiente; valores validados y query string para paginación. No se persiste ni modifica sesión para recordar filtros.
- **Totales**: Paginator.count es estudios; en modo validaciones un total separado se calcula desde Resultado para el mismo queryset de estudios filtrado, antes de paginar.
- **Resultados de página**: lista en `to_attr` de cada estudio, obtenida mediante Prefetch y relaciones seleccionadas. No es un campo del modelo ni se guarda. Cada fila permite leer prueba, valor y unidad sin consultar por fila.

El contrato de rutas, casos vacíos y autorización está en [contracts/rutas-filtros.md](contracts/rutas-filtros.md); sus pruebas se detallan en [test-matrix.md](test-matrix.md).
