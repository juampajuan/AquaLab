# Research: Seleccionar estudio y controlar pruebas pendientes

**Feature**: `020-controlar-pruebas-pendientes` | **Plan**: [plan.md](./plan.md)

## R1 — App `informes` nueva

- **Decision**: crear la app `informes` (sin modelos en esta historia) con el listado, el control y
  la acción de generar. US 7.2 le suma el modelo `Informe` y US 7.3 la consulta de informes.
- **Rationale**: la constitution fija una app por módulo e incluye `informes`; el Epic 7 completo
  vive ahí y no agranda `estudios`, que ya es la app más grande.
- **Alternatives considered**: sumar las vistas a `estudios` (mezcla dos épicas y obliga a mover
  todo con la US 7.2).

## R2 — Una sola regla «listo para informar»

- **Decision**: `informes/servicios.py:motivo_para_no_informar(estudio, asignaciones)` devuelve
  `None` si se puede informar o el texto del motivo:
  1. informe emitido → «El informe de este estudio ya fue generado.»;
  2. sin pruebas → «El estudio no tiene pruebas.»;
  3. alguna prueba no Completada → «Hay N pruebas sin completar.» («Hay 1 prueba sin completar.»).

  La usan el control (GET) y `comprobar_generacion`; el filtro «Listos para informar» del listado
  la expresa en SQL con las mismas tres condiciones y un test compara los dos resultados.
- **Rationale**: mismo patrón que `motivo_para_no_quitar` (US 5.4): una fuente para la vista y el
  servicio. Se cuentan las pruebas en vez de mirar `Estudio.estado == FINALIZADO` porque US 6.4
  todavía no está en `main` y porque el conteo es la definición del criterio de aceptación
  («100% de las pruebas»); con US 6.4 los dos coinciden.
- **Alternatives considered**: propiedad en `Estudio` (no recibe las asignaciones ya cargadas y
  duplicaría consultas); depender solo de `estado == FINALIZADO` (bloquea los tests hasta US 6.4 y
  confía en que todas las transiciones estén bien).

## R3 — Revalidar al generar, con el estudio bloqueado

- **Decision**: `comprobar_generacion(estudio_pk)` abre una transacción, bloquea el estudio con
  `select_for_update` (como `cargar_mediciones` y `corregir_mediciones`), relee las asignaciones y
  lanza `InformeNoDisponible(motivo)` si `motivo_para_no_informar` no es `None`. La vista
  `informes:generar` (solo POST) lo llama; si pasa, por ahora informa «La generación del informe
  estará disponible próximamente.» y vuelve al control. US 7.2 reemplaza ese aviso por la creación
  del informe dentro de la misma transacción.
- **Rationale**: FR-009 pide verificar con datos vigentes; el bloqueo del estudio es el que ya usan
  la carga, la corrección y la validación, así que una corrección simultánea no puede dejar pasar
  un estudio incompleto cuando la 7.2 genere.
- **Alternatives considered**: verificar solo en el GET (no cumple FR-009); advisory lock global
  (innecesario: el conflicto es por estudio).

## R4 — Reutilizar la búsqueda de estudios

- **Decision**: extraer de `estudios.views.buscar` la construcción del filtro a
  `estudios/busqueda.py:filtro_busqueda(q) -> Q`; `estudios:buscar` e `informes:listar` la usan.
  `BuscarEstudioForm` se reutiliza tal cual; el filtro «Listos para informar» es un parámetro GET
  `listos=1` aparte.
- **Rationale**: FR-003 pide los mismos criterios; los tests existentes de `test_consulta.py`
  cubren el refactor.
- **Alternatives considered**: copiar el filtro (dos reglas que divergen).

## R5 — Avance de pruebas en el listado

- **Decision**: anotar el queryset con `total_pruebas = Count("pruebas_asignadas")` y
  `pruebas_completadas = Count(..., filter=Q(pruebas_asignadas__estado=COMPLETADA))`; paginar de a
  20 (`RESULTADOS_POR_PAGINA`). Orden `-pk`, como `estudios:buscar`.
- **Rationale**: una consulta por página, sin N+1.

## R6 — Interfaz

- **Decision**: el control reutiliza `ui/estado.html` con el filtro `tipo_estado` para estudio y
  pruebas (mismos textos que el detalle, SC-004) y agrega una etiqueta por prueba que bloquea:
  «Incompleta» (Pendiente) o «Sin validar» (Cargada). «Generar informe» es un `<form method="post">`
  con CSRF; deshabilitado se dibuja como `<button disabled aria-describedby>` con el motivo visible.
  Sin JavaScript. El menú lateral suma la sección «Informes» y la pantalla de inicio un acceso
  rápido; el detalle del estudio, un enlace «Controlar para informe».
  «Incompleta» y «Sin validar» usan las dos el tipo `warning`: la spec solo pide destacarlas y el
  estado (con su color propio) ya las distingue.
- **Rationale**: principios de interfaz de la constitution (componentes de `templates/ui/`).
- **Confirmación**: «Generar informe» no guarda nada en esta historia; la confirmación (resumen y
  previsualización) es de US 7.2.

## R7 — Permisos

- **Decision**: sin permiso nuevo; `LoginRequiredMiddleware` exige la sesión.
- **Rationale**: supuesto de la spec; igual que el resto de las pantallas de estudios.
