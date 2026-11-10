# Checklist de calidad de especificación: Inicio personalizado por rol

**Propósito**: Validar la calidad y completitud de los requisitos antes de planificar.
**Creada**: 2026-11-09
**Feature**: [spec.md](../spec.md)

## Calidad del contenido

- [x] Sin detalles de implementación (lenguajes, frameworks, APIs).
- [x] Centrada en el valor para el usuario y las necesidades del negocio.
- [x] Escrita para interesados no técnicos.
- [x] Todas las secciones obligatorias completas.

## Completitud de requisitos

- [x] No quedan marcadores de aclaración pendientes.
- [x] Los requisitos son comprobables y no ambiguos.
- [x] Los criterios de éxito son medibles.
- [x] Los criterios de éxito son independientes de la tecnología.
- [x] Todos los escenarios de aceptación están definidos.
- [x] Los casos límite están identificados.
- [x] El alcance está claramente delimitado.
- [x] Las dependencias y supuestos están identificados.

## Preparación de la funcionalidad

- [x] Todos los requisitos funcionales tienen criterios de aceptación cerrados.
- [x] Los escenarios cubren los flujos principales del usuario.
- [x] La especificación define resultados verificables en los criterios de éxito.
- [x] No se filtran detalles de implementación en la especificación.

## Notas

- Revisión inicial: **13/16** criterios satisfechos. Las marcas evalúan calidad de requisitos, no implementación ni tests ejecutados.
- FR-002: «¿Técnico corresponde a Usuario común…?» deja abierta la matriz de presentación para membresías y permisos excepcionales.
- FR-004: «¿El valor cuenta resultados individuales pendientes o estudios distintos…?» deja abierta la unidad de validación y su correspondencia con el listado.
- FR-013: «¿Los indicadores actuales… se reemplazan… o se conservan…?» deja abierto el alcance de los indicadores generales y sus enlaces.
- Los escenarios están definidos para los cuatro criterios de Jira; los afectados por estas decisiones no tienen todavía todos sus resultados cerrados. Los tres ítems incompletos requieren resolver las aclaraciones antes de planificar. Se detiene para revisión por instrucción expresa del responsable, como en la revisión inicial de la feature 025; el siguiente paso es `$speckit-clarify`.
- Clave Jira y número de US no informados: se conserva título y descripción sin inventar identificadores. Es información de trazabilidad pendiente, adicional a las tres decisiones funcionales.

### Evidencia de la revisión del repositorio

- Base: `main` y `origin/main` sincronizadas en `d42bd3a4868ea5a88e4346ce9ecae6e3a8384fe2`. Rama 033 creada desde ese commit; numeración comprobada libre en ramas locales/remotas y specs. No se reutilizó 025 ni se trasladaron cambios de otra historia.
- `config/views.py:inicio` cuenta muestras sin estudio, muestras del día y estudios en `pendiente_analisis`; `templates/inicio.html` presenta esos indicadores sin enlace y las últimas cinco muestras. `templates/ui/indicador.html` y `templates/ui/acceso_rapido.html` son componentes existentes. No hay un listado general de muestras que represente los dos indicadores de muestras.
- `estudios/models.py:Estudio.admite_mediciones` permite Pendiente de análisis y En proceso; `estudios/views.py:asignaciones_para_medir` selecciona pruebas Pendientes no calculadas. `estudios/servicios.py:cargar_mediciones` aplica la regla de carga. El indicador general actual omite la carga parcial En proceso y no equivale al pendiente solicitado.
- `estudios/views.py:validar_resultados` selecciona pruebas Cargadas con resultado; exige `estudios.validar_resultados`. `estudios/servicios.py:validar_resultados` revalida permiso y datos. `estudios/calculo.py` y `estado_tras_correccion` manejan recálculo y pérdida de validación; `Validacion` conserva anulaciones.
- `estudios:buscar`, en `/estudios/buscar/`, usa `FiltrarEstudiosForm`, `filtro_busqueda` y `filtro_estado_fechas`; admite `q`, `desde`, `hasta`, `estado` y paginación. No existen parámetros específicos de carga o validación pendientes. Se documenta la brecha funcional sin inventar nombres de parámetros ni rutas nuevas.
- `informes:listar`, en `/informes/`, reconoce `listos=1` y utiliza `informes/servicios.py:estudios_para_informar`. `motivo_para_no_informar` y ese filtro comparten las tres condiciones de preparación: pruebas existentes, todas completadas y estado distinto de Informe generado. Emisión exige `informes.emitir_informes` y `FirmaProfesional`; no se redefine la regla usando únicamente el estado Finalizado.
- `informes:emitidos`, en `/informes/emitidos/`, consulta informes ya emitidos y no es el destino de estudios listos para emitir. `informes/busqueda.py:informes_emitidos` busca por número de informe, cliente, documento o N° PI y fechas de emisión (`q`, `desde`, `hasta`), sobre el contenido conservado del informe; no corresponde duplicar esa búsqueda para pendientes.
- `usuarios/forms_administracion.py:RolForm` ofrece Usuario común y Bioquímico; el cambio de rol en `usuarios/servicios_administracion.py` solo agrega o retira Bioquímicos. No hay un grupo Técnico en las definiciones revisadas. No se consultó una base de usuarios desplegada; las conclusiones corresponden a reglas y migraciones versionadas.
- `estudios.0008` asigna validar resultados a Bioquímicos; `informes.0002` asigna emitir informes; `informes.0004` asigna `informes.ver_dashboard` a Bioquímicos y Administradores. Los permisos pueden existir por otras vías y sus verificaciones no equivalen a exigir esos grupos.
- El dashboard corresponde a `informes:dashboard`, `/informes/dashboard/`, implementado en `informes/views.py:dashboard` y `informes/tablero.py` (spec 027). Su vista y el menú comprueban `informes.ver_dashboard`. Administración (spec 025) usa una política diferente: Administradores más `usuarios.administrar_panel`.
- `config/settings.py` aplica `LoginRequiredMiddleware`. No se modifican autenticación ni autorizaciones existentes.
- Se leyó Constitution 1.2.0, el workflow original y la feature 025. Se resolvió la plantilla con `.specify/scripts/bash/resolve-template.sh spec-template --json` y se creó el borrador mediante `create-new-feature.sh --number 33 --short-name inicio-personalizado-rol --json`. El script original actualiza el puntero local ignorado `.specify/feature.json`; la rama se creó explícitamente conforme al pedido, ya que no hay hook de creación registrado.
- Se comprobó que `.specify/extensions.yml` no existe: no hay hooks previos ni posteriores de specify registrados que ejecutar.
- Esta entrega contiene especificación y checklist. No se ejecutan clarify, plan, tasks ni implement; no se genera código, migraciones, commit, push, PR ni merge.
