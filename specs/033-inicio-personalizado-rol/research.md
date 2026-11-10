# Investigación técnica — Inicio personalizado por rol

**Fecha**: 2026-11-09. **Base inspeccionada**: `d42bd3a4868ea5a88e4346ce9ecae6e3a8384fe2`.
Investigación del código local, con dos agentes de investigación de consultas y autorización/tests, conforme a la fase 0 del workflow original. Sin instalaciones ni cambios de producto.

## R1. Distinguir rol de autorización

- **Decisión**: consultar pertenencia efectiva a `Bioquímicos` una vez por request de Inicio. No crear modelo, rol, permiso ni servicio de autorización nuevo. `Administradores`, `is_staff`, `is_superuser` y permisos individuales no sustituyen esa pertenencia para los indicadores profesionales.
- **Fundamento**: `usuarios/forms_administracion.py:RolForm`, `usuarios/servicios_administracion.py:cambiar_rol_panel` y FR-002. `config/settings.py` conserva AuthenticationMiddleware, LoginRequiredMiddleware y ModelBackend implícito. Las consultas de Inicio, búsqueda y selección de Informes requieren sesión; no tienen un permiso profesional adicional de lectura.
- **Efecto**: un bioquímico sin permiso de validación/emisión puede consultar pendientes, pero no ejecutar esas operaciones. Un superusuario activo fuera de Bioquímicos tiene indicadores de Técnico y acceso al dashboard por `has_perm`, como ya exige `informes/tests/test_dashboard.py`. No usar la política de Administración, que es diferente.
- **Alternativas descartadas**: mostrar por `has_perm` los indicadores profesionales contradice la decisión aprobada; exigir Bioquímicos en los destinos quitaría accesos existentes a otros usuarios.

## R2. Fuente de carga pendiente

- **Decisión**: extraer el predicado de `estudios/views.py:asignaciones_para_medir` a un pequeño módulo de consultas de dominio `estudios/pendientes.py`; la función actual seguirá delegando allí y conservando su orden y relaciones. Seleccionar pruebas asignadas Pendientes con `prueba.es_calculada=False`. Filtrar estudios por los dos estados que admite `Estudio.admite_mediciones` y por `Exists` de esas asignaciones.
- **Fundamento**: una carga parcial está En proceso y debe contar; un estudio con varias asignaciones cuenta una vez. `tipo_calculo=FORMULA` no equivale a `es_calculada=True`: algunas fórmulas admiten medición propia. No agregar un filtro por Prueba.activa ni inferir el pendiente por ausencia de Resultado.
- **Alternativas descartadas**: contar solo Pendiente de análisis omite carga parcial; copiar el predicado en Inicio y búsqueda permite divergencias; joins ordinarios multiplican estudios.

## R3. Fuente de resultados individuales

- **Decisión**: queryset canónico `resultados_por_validar()` basado en `Resultado`, con asignación Cargada, estudio sin estado Informe generado y `NOT EXISTS` de una `Validacion` no anulada de esa asignación. El resultado existe por ser la raíz del queryset. Contar sus filas, no estudios.
- **Fundamento**: `estudios/views.py:validar_resultados` usa Cargada con resultado; `Validacion` tiene unicidad parcial de vigente y conserva anulaciones. La conjunción explícita responde a FR-004 sin inventar estados. Resultados calculados y recalculados cuentan si satisfacen la misma regla.
- **Alternativas descartadas**: contar estudios pierde el caso 5+1=6; excluir cualquier validación histórica oculta resultados recalculados; unir validaciones históricas puede duplicar filas. La validación de escritura y su servicio quedan intactos.

## R4. Lista de destino y filtros

- **Decisión**: extender `/estudios/buscar/` con `pendiente=mediciones|validaciones`, opcional, en `FiltrarEstudiosForm`. Conservar las 20 filas de estudios por página. En modo validaciones, mostrar cada resultado pendiente identificado por código/nombre de prueba dentro de su estudio y los totales separados de resultados y estudios. No crear otra ruta ni pantalla.
- **Fundamento**: `buscar` ya combina texto, estado y fechas; la spec permite agrupar resultados y exige identificarlos. Se aplican los filtros existentes al estudio y luego la selección canónica. El queryset de resultados, restringido a esos estudios, proporciona el total filtrado y el prefetch de la página. `CAMPOS_FILTRO` y `FiltrosEstudioForm` compartidos con historial no incorporan el nuevo campo.
- **Errores**: conservar el comportamiento actual de filtros inválidos: errores y listado completo sin filtros; no presentarlo como una selección válida ni mostrar totales de pendientes. Los enlaces generados desde Inicio son siempre válidos y no llevan filtros adicionales.
- **Alternativas descartadas**: un listado que muestre solo estudios no demuestra el total de resultados; otra pantalla duplica navegación; paginar resultados cambiaría la unidad de paginación existente.

## R5. Listos para emitir

- **Decisión**: Inicio usa `informes.servicios.estudios_para_informar(q="", solo_listos=True).count()`; enlace a `/informes/?listos=1`. No copiar esa regla a `estudios/pendientes.py` ni cambiar Informes.
- **Fundamento**: ese servicio replica la regla de `motivo_para_no_informar`: al menos una prueba, todas Completadas, sin estado Informe generado. `informes:emitidos` contiene documentos ya emitidos y no es el destino correcto.
- **Alternativas descartadas**: filtrar solo Finalizado cambia el contrato; exigir firma al conteo mezcla preparación del estudio con habilitación del emisor. Permiso, firma y matrícula siguen comprobándose en el flujo existente.

## R6. Rendimiento y concurrencia

- **Decisión**: consultas ORM lazy, `Exists`/`OuterRef`, conteos SQL y relaciones de muestra/cliente/origen con `select_related`. Para validaciones, `Prefetch` de asignaciones cuyos resultados están en el queryset canónico, con prueba y resultado seleccionados, `to_attr` y solo para estudios de la página. No precargar historial de validaciones ni ejecutar `count` por fila. No consultar los dos indicadores profesionales para Técnico.
- **Fundamento**: patrones actuales en `estudios/models.py:validaciones_vigentes`, búsqueda e informes; pruebas de consultas en `config/tests/test_inicio.py`. Comparar cantidad de consultas a distinto volumen en el mismo modo, no fijar un total frágil afectado por middleware.
- **Límite**: página de estudios acota padres, no el número de pruebas de un estudio; no existe máximo de negocio que podamos inventar. Si las mediciones de implementación muestran un problema, evaluarlo antes de agregar índices o infraestructura.
- **Concurrencia**: no hay writes en GET ni locks nuevos. Inicio y destino son consultas sucesivas; el estado puede cambiar entre ellas o entre sentencias bajo el aislamiento actual. No se promete snapshot global. Los servicios existentes revalidan bajo sus bloqueos al confirmar.
- **Alternativas descartadas**: caché global de contadores puede quedar obsoleta y mezcla perfiles; snapshots o bloqueos de lectura introducen complejidad sin requisito.

## R7. Interfaz y verificación

- **Decisión**: ampliar `ui/indicador.html` con URL opcional, conservando el render no enlazado para sus otros consumidores; usar `ui/acceso_rapido.html` para dashboard, títulos y componentes comunes para grupos y pendientes. Compilar el CSS con el Tailwind standalone ya disponible si las nuevas clases lo requieren. No sumar JavaScript ni dependencias.
- **Fundamento**: Constitution 1.2.0, `templates/inicio.html`, `templates/ui/*`, Dockerfile y CI. Tests con pytest-django y PostgreSQL 16; la matriz enlaza cada uno de los 27 escenarios con verificaciones futuras.
- **Alternativas descartadas**: un componente paralelo de tarjetas o un frontend nuevo duplicaría el sistema visual. Cambiar todo indicador compartido a enlace rompería dashboard y otros consumidores.

## Cierre de investigación

Las decisiones técnicas están resueltas. No hacen falta migraciones, dependencias, servicios externos, nuevos permisos ni nuevas rutas. `estudios/pendientes.py` es un módulo mínimo de consultas para compartir predicados, no una capa nueva de servicios de negocio. La falta del número de US es una brecha documental de trazabilidad, tratada expresamente en el chequeo de Constitution del plan; no se inventa el dato.
