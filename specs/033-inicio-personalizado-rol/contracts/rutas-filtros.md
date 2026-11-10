# Contratos de Inicio, rutas y filtros — Feature 033

Diseño para implementación futura. Las rutas enumeradas ya existen; solo `pendiente` y la presentación de sus resultados son nuevos. No se agregan endpoints ni se cambia el contrato de escritura de las operaciones.

## Inicio e indicadores

`GET /` — nombre `inicio`, requiere sesión activa por la autenticación existente.

| Indicador / data-indicador propuesto | Visible | Unidad / fuente | Destino generado |
|---|---|---|---|
| Estudios con mediciones por cargar / mediciones-pendientes | Técnico y Bioquímico | Estudio distinto; estudios_con_mediciones_pendientes | reverse('estudios:buscar') + pendiente=mediciones |
| Resultados por validar / resultados-por-validar | Bioquímico por grupo | Resultado individual; resultados_por_validar | reverse('estudios:buscar') + pendiente=validaciones |
| Estudios listos para emitir / estudios-listos | Bioquímico por grupo | Estudio distinto; estudios_para_informar('', True) | reverse('informes:listar') + listos=1 |

Cada enlace se genera sin texto, fecha, estado ni página previos. Un valor cero conserva enlace y unidad; el listado mostrará vacío. Los tres indicadores generales se retiran sin segundo bloque. URL opcional en el parcial compartido: cuando no existe, se conserva la presentación no enlazada de otros consumidores.

`GET /informes/dashboard/` — nombre `informes:dashboard`. La tarjeta «Ver dashboard» usa el `has_perm('informes.ver_dashboard')` efectivo, independientemente de los indicadores profesionales; la vista conserva el mismo permiso. Un superusuario activo sin Bioquímicos conserva indicador de Técnico y tarjeta de dashboard conforme al backend actual.

## Búsqueda de estudios extendida

`GET /estudios/buscar/` — nombre `estudios:buscar`. Acceso de consulta existente para cuentas autenticadas; ni nuevo permiso ni exigencia de pertenencia a Bioquímicos. No se autoriza validar por poder abrir esta lista.

| Parámetro | Contrato |
|---|---|
| q | Existente, texto opcional, máximo 100, búsqueda de estudio/muestra/cliente/tipo y documentos mediante filtro_busqueda actual. |
| desde / hasta | Existentes, fechas de creación del estudio, días inclusivos en zona horaria del proyecto; validación y formatos actuales. |
| estado | Existente, vacío o valor de EstadoEstudio; sin estados nuevos. |
| pendiente | Nuevo, opcional: vacío (Todos), mediciones (Mediciones por cargar) o validaciones (Resultados por validar). Solo FiltrarEstudiosForm. Campo visible con ayuda breve. |
| page | Existente: Paginator.get_page, 20 estudios por página; conservar tratamiento actual de página no numérica, menor a uno o fuera de rango. |

### Combinación y normalización

- Con formulario válido, aplicar `q AND estado/fechas AND pendiente`; campos vacíos no restringen. No agregar filtro implícito de creador, usuario o fechas.
- `pendiente=mediciones`: seleccionar estudios con carga pendiente mediante Exists y estados permitidos. Mostrar total de estudios, sin duplicados ni lista de resultados de validación.
- `pendiente=validaciones`: seleccionar estudios que tengan al menos un Resultado canónico pendiente. Conservar orden de estudios actual (`-pk`) y paginación por estudio. Mostrar total de estudios y total de resultados en rótulos separados; dentro de cada estudio mostrar cada resultado pendiente por prueba, con valor y unidad del resultado. Orden estable de resultados por código de prueba y pk de asignación.
- Las restricciones por fecha/estado/texto se aplican al estudio contenedor. El total de resultados filtrado es el queryset canónico restringido a los estudios de esa selección completa, no solo de la página. No redefinir q como búsqueda de código de prueba.
- El formulario conserva la selección pendiente al enviar q/fechas/estado; al paginar conserva todos los parámetros existentes salvo page, que se sustituye. Incluir pendiente en hay_filtros/filtrado/con_filtros sin incorporarlo a CAMPOS_FILTRO global compartido por otros formularios.
- «Limpiar filtros» regresa a la ruta sin query string, como actualmente. Una combinación válida sin coincidencias es una lista vacía, no un error ni un fallback a todos los estudios.
- No dar semántica a claves GET adicionales desconocidas ni cambiar la política general de QueryDict para valores repetidos. El formulario usa el valor efectivo habitual de Django; los enlaces propios generan un solo valor por parámetro. Preservar el tratamiento actual de parámetros existentes.

### Errores y vacíos

Con valor no permitido de pendiente, fecha inválida, rango invertido, estado inválido o texto inválido, conservar la política actual de búsqueda: HTTP 200, errores en el formulario y listado general sin aplicar ningún filtro. No renderizar los resultados identificados del modo validación, su total ni un rótulo de selección aplicada cuando el formulario sea inválido. Mantener los valores introducidos y ofrecer limpiar. Este fallback es una política de búsqueda existente, no una excepción de autorización.

En una selección válida vacía mostrar el mensaje de ausencia de coincidencias y posibilidad de limpiar. Una categoría sin pendientes aporta cero. Sin pendiente, la búsqueda mantiene su presentación actual y no carga datos ni totales de resultados profesionales.

### Resultados individuales identificables

El parcial propuesto `_resultados_pendientes.html` se incluye en cada estudio solo en modo validaciones válido. Cada resultado aparece una vez, ligado a un único estudio y prueba, con identidad comprobable en HTML (data de Resultado.pk propuesta para tests), código y nombre de prueba, valor_mostrado y unidad guardada usando filtros comunes. Para A/P usar el formato actual de valores de presencia.

El acceso es «Ver estudio» mediante `estudios:detalle`; el detalle ya permite continuar la validación cuando existe permiso efectivo y trabajo elegible. No agregar botón ni formulario de validar en este parcial. Identificar los resultados dentro de la lista evita exigir que el usuario abra cada detalle solo para reconstruir el total.

### Correspondencia

Para los mismos datos estables y sin filtros manuales extra:

| Origen | Igualdad exigida al recorrer el destino |
|---|---|
| Cantidad de carga en Inicio | Número de identidades de Estudio distintas en todas las páginas con pendiente=mediciones. |
| Cantidad de validación en Inicio | Número de identidades de Resultado distintas identificadas en todas las páginas con pendiente=validaciones. No equivale al Paginator.count de estudios. |
| Cantidad de listos en Inicio | Número de estudios distintos en todas las páginas de Informes con listos=1. |

Ejemplo obligatorio: estudio A con 5 resultados, B con 1 y C con 0 → indicador 6 resultados; lista 2 estudios con 6 resultados identificables, sin C. Si el usuario filtra para ver A, la lista muestra 1 estudio y 5 resultados filtrados sin modificar el total global del inicio.

## Informes y operaciones existentes

`GET /informes/?listos=1` — `informes:listar`: reutilizar la consulta y paginación actuales. El contrato existente reconoce `q`, `listos=1` y `page`; no añadir aquí estado/fechas/pendiente ni inferir que los filtros de estudios se aplican automáticamente. La selección de Informes usa BuscarEstudioForm (texto), no FiltrarEstudiosForm. `informes:emitidos` sigue separado con sus filtros actuales de texto y fechas de emisión.

| Destino / acción | Autorización que se conserva |
|---|---|
| Inicio, buscar estudios, detalle, selección y control de Informes | Sesión activa existente; no nuevo requisito profesional. |
| Cargar mediciones | Sesión activa y reglas actuales de estudio/asignación; no permiso nuevo derivado del indicador. |
| Validar resultados | estudios.validar_resultados en vista y servicio; control de estado/datos y confirmación existentes. |
| Emitir informe | informes.emitir_informes y firma profesional con matrícula, más preparación de estudio y confirmación existentes. |
| Dashboard | informes.ver_dashboard efectivo, incluido comportamiento actual de superusuarios activos. |
| Gestionar tipos | estudios.gestionar_catalogo; acceso rápido vigente; política del menú de Administración intacta. |

Anonimato o cuenta inactiva en nueva consulta siguen el login existente. Un usuario activo sin permiso operativo conserva el HTTP 403 en las operaciones protegidas. No cambiar permisos ni escribir datos al navegar.

## Concurrencia y compatibilidad

No se garantiza igualdad entre instantes diferentes: una medición, validación o emisión puede cambiar la selección después de cargar Inicio. Recargar Inicio refleja el cambio; el listado consulta estado actual. No cachear, bloquear ni reservar pendientes. Los servicios actuales revalidan al confirmar.

La extracción del predicado de mediciones debe conservar los resultados actuales de `asignaciones_para_medir`. La búsqueda sin pendiente, los filtros de historial de clientes, el dashboard y la selección de Informes mantienen sus contratos. Regresiones específicas en [../test-matrix.md](../test-matrix.md).
