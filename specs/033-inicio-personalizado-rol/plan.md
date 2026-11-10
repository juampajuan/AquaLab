# Implementation Plan: Inicio personalizado por rol

**Branch**: `033-inicio-personalizado-rol` | **Date**: 2026-11-09 | **Spec**: [spec.md](spec.md)

**Input**: `specs/033-inicio-personalizado-rol/spec.md`, aprobada expresamente por el responsable al solicitar este plan: 27 escenarios, checklist 16/16 y tres aclaraciones incorporadas.

## Summary

Reemplazar los tres contadores generales de Inicio por pendientes según pertenencia a Bioquímicos; reagrupar accesos por Clientes → Muestras → Estudios → Informes y agregar «Ver dashboard» mediante su permiso efectivo existente. Conservar bienvenida, últimas muestras y autorizaciones actuales.

Compartir dos consultas canónicas de pendientes en un módulo pequeño del dominio Estudios. Extender la búsqueda existente con un selector GET y, para validaciones, identificar resultados individuales agrupados dentro de sus estudios. Reutilizar sin alterar `estudios_para_informar` y `listos=1`. No crear rutas, modelos, migraciones, dependencias, servicios externos ni una capa de servicios de escritura.

## Technical Context

**Language/Version**: Python 3.12, Django 5.2.18 según Dockerfile y requirements.txt actuales.

**Primary Dependencies**: ORM, formularios, autenticación y templates Django existentes; Tailwind standalone v4.3.3 ya fijado en Docker/CI. Sin dependencias nuevas.

**Storage**: PostgreSQL 16 existente. Solo lecturas para esta funcionalidad; sin cambios de esquema ni índices nuevos previstos.

**Testing**: pytest 9.1.1, pytest-django 4.14.0, PostgreSQL 16 y ruff existentes. Matriz de 27 escenarios en [test-matrix.md](test-matrix.md). Pruebas de consultas con CaptureQueriesContext.

**Target Platform**: aplicación web renderizada en servidor, escritorio, entorno Docker Compose actual; planificación realizada sobre checkout en E: sin moverlo.

**Project Type**: monolito Django por módulos del dominio; no API ni frontend nuevos.

**Performance Goals**: conteos SQL y cantidad de consultas constante al crecer filas dentro del mismo modo/página; evitar N+1. Conservar 20 estudios por página. Objetivo funcional de orientación de SC-005: 30 segundos, validable manualmente; no equivale a una latencia de servidor prometida.

**Constraints**: misma semántica de carga/validación/emisión; sin writes en GET, caché de conteos o autorización nueva. Identificación de cada resultado que aporta al contador. Datos vigentes sin prometer snapshot entre requests.

**Scale/Scope**: Inicio, extensión mínima de búsqueda de estudios, un parcial compartido y pruebas/regresiones. No hay volumen máximo de negocio documentado; las pruebas cubrirán varias páginas y varios resultados por estudio sin inventar un límite.

## Constitution Check

*Evaluación previa a investigación y repetida después del diseño de fase 1. Constitution vigente: 1.2.0.*

| Principio / gate | Antes | Después del diseño | Evidencia / resolución |
|---|---|---|---|
| I. Spec primero, una historia por spec | Conforme | Conforme | Aprobación explícita del responsable, 27 escenarios, 16/16. Solo diseño de 033. |
| I. Número de US del backlog en la spec | Brecha justificada para planificar | Brecha documental pendiente | No proporcionado. El responsable autoriza este plan sobre título, descripción y criterios aprobados, con el dato ya señalado como pendiente. No inferir una clave de 033. Completar antes del PR; no se declara cumplimiento íntegro de trazabilidad. |
| II. Simplicidad / Django idiomático | Conforme | Conforme | ORM, formularios y templates actuales; helper de consultas justificado por compartir predicados, sin repositorios, servicios externos o dependencias nuevos. |
| III. Tests obligatorios | Conforme en diseño | Conforme en diseño | Cada escenario tiene prueba asignada; regresiones, consultas y autorizaciones incluidas. No afirmar tests ejecutados en esta fase documental. |
| IV. Integridad del laboratorio | Conforme | Conforme | Sin writes, migraciones ni cambios en cálculos, validaciones, firma o emisión. Se preservan excepciones históricas documentadas para correcciones antes de emitir, sin ampliarlas. |
| V. Seguridad | Conforme | Conforme | Middleware, backend, permisos, CSRF y servicios protegidos intactos; sin credenciales en artefactos. |
| VI. Idioma / glosario | Conforme | Conforme | Documentación e interfaz en español, términos del dominio existentes. |
| Interfaz común y ayudas | Conforme | Conforme | Parciales actuales, enlace opcional compatible en indicador, campo nuevo con help_text y estilos del sistema; CSS compilado si cambia. |
| Workflow y gobierno | Conforme | Conforme | Rama 033, archivos de otras historias y Constitution preservados; tasks/implement y operaciones de publicación no ejecutadas. |

**Resultado del gate**: se permite continuar el diseño con la excepción documental explícita y acotada de trazabilidad anterior, autorizada por el pedido actual. No hay violaciones técnicas sin justificación ni incógnitas técnicas bloqueantes. No equivale a certificar cumplimiento total de Constitution para una futura entrega sin el número de US.

## Project Structure

### Documentation (this feature)

```text
specs/033-inicio-personalizado-rol/
├── spec.md                       # existente, sin cambios en esta fase
├── checklists/requirements.md     # existente, 16/16, sin cambios
├── plan.md
├── research.md
├── data-model.md
├── contracts/rutas-filtros.md
├── test-matrix.md
└── quickstart.md
```

`tasks.md` no se genera en este comando.

### Source Code (repository root)

Archivos previstos para la implementación futura, no creados ni modificados en este plan:

| Archivo | Cambio previsto |
|---|---|
| `config/views.py` | Rol por pertenencia, conteos canónicos, URL de cada indicador; últimas muestras intactas. |
| `templates/inicio.html` | Sustitución de contadores, grupos de accesos y tarjeta de dashboard por permiso efectivo. |
| `templates/ui/indicador.html` | URL opcional: enlace accesible cuando se provee, render actual cuando no; conservar data-indicador/data-valor. |
| `estudios/pendientes.py` (nuevo) | Solo consultas de carga y resultados pendientes, predicados compartidos y filtrado de estudios. |
| `estudios/forms.py` | Campo opcional pendiente solo en FiltrarEstudiosForm, con ayuda y validación; no extender CAMPOS_FILTRO global ni formulario base compartido. |
| `estudios/views.py` | Búsqueda con AND de filtros y pendiente, conteos y prefetch paginado; delegar asignaciones_para_medir en predicado compartido conservando comportamiento. |
| `estudios/templates/estudios/buscar.html` | Selector, estado de filtros, totales con unidad y resultados pendientes identificables. |
| `estudios/templates/estudios/_resultados_pendientes.html` (nuevo) | Presentación por estudio de prueba, valor/unidad y acceso existente al estudio; ningún formulario ni escritura. |
| `static/css/aqualab.css` | Solo regeneración con CLI existente si cambian las clases detectadas por Tailwind. |
| `config/tests/test_inicio.py`, `config/tests/test_inicio_roles.py` (nuevo) | Actualizar expectativas retiradas; cubrir roles, accesos, permisos y funciones conservadas. |
| `config/tests/test_componentes.py` | Compatibilidad del indicador con/sin URL, teclado y texto accesible. |
| `estudios/tests/test_pendientes.py`, `estudios/tests/test_pendientes_busqueda.py` (nuevos) | Conjuntos exactos, filtros, identidades y consultas. |
| `estudios/tests/test_filtros.py`, `estudios/tests/test_cargar_mediciones.py` | Compatibilidad de formularios y extracción del predicado. |
| `informes/tests/test_control.py`, `informes/tests/test_dashboard.py`, `informes/tests/test_permisos.py` | Reutilizar y ampliar solo si se necesita una comprobación de integración adicional; no cambiar expectativas de autorización. |

**Structure Decision**: mantener el monolito existente. No modificar URLs, modelos, migraciones, middleware, backend, formularios base compartidos con otras funcionalidades ni lógica de escritura. Una nueva consulta pura y un parcial son las únicas incorporaciones de producto previstas.

## Diseño de consultas y responsabilidades

1. `estudios/pendientes.py` define `asignaciones_con_mediciones_pendientes()` (Pendiente y no calculada), `estudios_con_mediciones_pendientes(qs)` (estados permitidos + Exists), `resultados_por_validar()` (raíz Resultado, Cargada, sin informe, sin validación vigente) y `estudios_con_resultados_pendientes(qs)` (Exists del queryset anterior). Nombres de diseño propuestos, todavía inexistentes.
2. La selección actual de mediciones delega en el primer queryset y conserva `.filter(estudio=...)`, select_related y orden por código/pk; el guard de `admite_mediciones` y los servicios de escritura no cambian. El filtro de estados se define en un único lugar del módulo de consultas con los valores actuales del dominio y un test de paridad con `admite_mediciones`; no se cambia la propiedad del modelo.
3. Inicio cuenta el queryset de estudios de carga; para Bioquímicos cuenta resultados y el servicio existente de listos. No cargar estudios o resultados en memoria para contarlos; no consultar conteos profesionales para Técnico. Construir enlaces mediante reverse y parámetros codificados, no URLs duplicadas en templates.
4. Búsqueda conserva su queryset base y aplica texto, estado y fechas de creación con funciones existentes; luego el modo pendiente. Para validaciones, el total usa `resultados_por_validar().filter(asignacion__estudio__in=qs_filtrado)`. El número de estudios es el del Paginator; no usarlo como total de resultados.
5. Después de paginar estudios, precargar únicamente asignaciones de la página cuyo Resultado pertenece a la consulta canónica, con `select_related('prueba', 'resultado')` y `Prefetch(..., to_attr=...)`. Mostrar cada resultado una vez por su asignación; código, nombre, valor y unidad existentes. No realizar consultas adicionales desde el parcial ni precargar todas las validaciones históricas.
6. Inicio y `/informes/?listos=1` llaman al mismo `informes.servicios.estudios_para_informar`; no se implementa otra definición de preparado para emisión. Firma y matrícula son requisitos del actor al emitir, no de la disponibilidad del estudio.

Ver contratos exactos y política de errores en [contracts/rutas-filtros.md](contracts/rutas-filtros.md).

## Interfaz y autorización

- Usar `ui/acceso_rapido.html`, `ui/indicador.html`, `ui/campo.html`, `ui/ayuda.html`, `ui/estado_vacio.html`, `ui/paginacion.html` y filtros de valor/unidad existentes. Mantener bloques data-componente de accesos y últimas muestras para regresiones.
- Los tres nombres estables propuestos de indicador son `mediciones-pendientes`, `resultados-por-validar` y `estudios-listos`. Los dos últimos solo aparecen si pertenece a Bioquímicos. No usar `puede_administrar` ni has_perm para inferir el rol.
- El indicador es enlace con nombre y cantidad accesibles y foco visible; otros consumidores sin URL mantienen el elemento no enlazado. No anidar enlaces ni usar JS para navegación.
- Conservar los accesos actuales en los cuatro grupos; Gestionar tipos queda en Estudios del inicio con su permiso vigente. El menú administrativo y su política no cambian. Dashboard se presenta aparte de esos grupos usando `request.user.has_perm('informes.ver_dashboard')` y reverse de `informes:dashboard`.
- Las consultas de pendientes conservan sesión como requisito de lectura; no incorporar permiso de validación o grupo como guard nuevo del buscador. Una cuenta común puede seguir consultando por URL directa. Las acciones de validar/emitir siguen protegidas en vistas y servicios; no se incorporan esas acciones al nuevo parcial, que enlaza al detalle existente.
- ModelBackend mantiene el tratamiento de inactivos y superusuarios. Probar sesión seguida de desactivación, no solo force_login sobre un usuario inactivo. Conservar huella de sesión y never-cache; grupos y permisos se consultan de nuevo en requests sucesivos.

## Consistencia, compatibilidad y concurrencia

- Igualdad de conjuntos para los mismos datos: carga y emisión cuentan estudios; validación cuenta identidades de Resultado. La suma de resultados identificados al recorrer todas las páginas sin filtros extra debe coincidir con Inicio.
- Filtros manuales reducen el universo y el destino muestra su total filtrado, no promete conservar el total global del inicio. Valores inválidos mantienen la política existente sin aparentar que una selección no aplicada está activa.
- No abrir transacciones ni locks nuevos para GET. Una operación confirmada entre Inicio y lista puede cambiar el número; se refresca al volver. Los locks y controles de concurrencia existentes de servicios siguen siendo la autoridad al operar. Un prefetch puede ver cambios concurrentes dentro de un request; se garantiza identidad bajo datos estables, no snapshot serializable.
- No alterar búsqueda general, historial de clientes, selección de informes ni dashboard. Los tests que esperaban contadores generales en Inicio deben actualizarse específicamente a su reemplazo; conservar el resto de regresiones.
- Riesgos: multiplicación por joins a historial (usar Exists), permisos cacheados en fixtures (instancias/request nuevos), muchas pruebas en un estudio (no hay límite aprobado), CSS compilado, y diferencias legítimas por actividad concurrente. Sin índices nuevos hasta contar con evidencia de rendimiento.

## Validación y resultado de fase 1

La estrategia en [test-matrix.md](test-matrix.md) cubre US1.1–US1.14, US2.1–US2.6, US3.1–US3.4 y US4.1–US4.3: 27/27. Incluye pruebas ORM y HTTP sobre PostgreSQL, permisos e inactivos, paginación y consultas, regresiones de módulos y revisión manual de SC-005. [quickstart.md](quickstart.md) define cómo ejecutarlas después de implementar; no se afirma que existan o pasen ahora.

Se completan investigación, modelo de lectura y contratos sin cambiar spec o checklist. No quedan decisiones técnicas abiertas. La trazabilidad de US sigue pendiente de información externa; revisar ese dato antes del PR. No hay `.specify/extensions.yml`: sin hooks previos o posteriores registrados.

## Complexity Tracking

| Excepción / costo | Justificación | Alternativa descartada |
|---|---|---|
| Número de US aún no informado | Se documenta la brecha; el responsable autorizó planificar la historia por su título, descripción y criterios aprobados. Completar antes del PR. No cambia Constitution. | Inventar una clave o asumir que 033 es la US rompe trazabilidad. |
| Módulo mínimo nuevo de consultas | Inicio, filtros y resultados identificables deben compartir el mismo predicado; dos reglas nuevas de lectura no tienen módulo canónico actual. | Duplicar condiciones en vistas permite inconsistencias; crear una capa de servicios o nuevos modelos es innecesario. |
