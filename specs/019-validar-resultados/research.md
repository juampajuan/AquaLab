# Research: Validar resultados

**Feature**: `019-validar-resultados` | **Plan**: [plan.md](./plan.md)

No quedan `NEEDS CLARIFICATION`: permisos, selección inicial, reglas de evaluación y límites no
comparables se resolvieron en la sección *Clarifications* de la spec (11 respuestas).

Punto de partida (`main` con el PR #32): `PruebaEstudio` con estados Pendiente / Cargada /
Completada (US 5.2), `Medicion` (US 6.1, 6.3, 6.5), `Resultado` y `calculo.recalcular` /
`calculo.descartar` (US 6.2), `estado_tras_correccion` (Finalizado → En proceso, US 6.3), el
catálogo con límites como texto y `LimiteVertido` por Cloacal/Canal (SCRUM-64) y Ausente/Presente
guardado como 0/1 (PR #32). Ninguna historia anterior pasa una prueba a Completada ni un estudio a
Finalizado: eso es esta historia.

## R1 — Una entidad `Validacion` aparte, con una sola vigente por prueba del estudio

- **Decision**: modelo nuevo `estudios.Validacion` con `asignacion = ForeignKey(PruebaEstudio,
  on_delete=PROTECT, related_name="validaciones")`, `anulada` y `fecha_anulacion`, una restricción
  única parcial (una sola no anulada por asignación), quién y cuándo validó, los límites usados (texto
  tal como estaban en el catálogo), su origen (general / cloacal / canal) y la evaluación. Detalle
  en [data-model.md](./data-model.md).
- **Rationale**: `Resultado` se crea y se pisa con `update_or_create` en cada recálculo (US 6.2);
  si la validación viviera ahí, cada recálculo tendría que acordarse de vaciar seis campos. Una
  fila aparte expresa directamente «esta prueba fue validada» y, cuando deja de serlo, se anula sin
  borrarse (R2), así una prueba revalidada acumula su historial. `CLAUDE.md` pide referenciar `PruebaEstudio` con `PROTECT`.
- **Alternatives**: campos en `Resultado` (acoplado al recálculo); campos en `PruebaEstudio`
  (mezcla la asignación con la validación y obliga a muchos `null`); `OneToOneField` borrando la
  fila al perderse (descartado en el análisis: borra historial, principio IV).

## R2 — Invariante: hay una `Validacion` vigente si y solo si la prueba está Completada

- **Decision**: `calculo.cambiar_estado(asignacion, estado)` anula la `Validacion` vigente
  (`anulada=True`, `fecha_anulacion=now`) cuando la asignación sale de Completada. Es el único lugar por donde una prueba cambia de estado después
  de la carga (`recalcular` y `descartar` lo usan), así que corregir (US 6.3) y borrar (US 6.5)
  quitan la validación sin tocar sus servicios. El servicio de esta historia crea la `Validacion`
  y pasa la prueba a Completada en la misma transacción.
- **Rationale**: un solo punto mantiene el invariante; la pérdida de la validación ya es la
  excepción al principio IV justificada en `specs/016-calcular-resultado/plan.md`, y anular en vez de
  borrar cumple «no se borran registros con historial» (FR-017).
- **Alternatives**: borrar la fila (pierde quién validó antes); anularla en `corregir_mediciones` y en el borrado (dos lugares que se pueden
  olvidar en una historia futura); `on_delete=CASCADE` desde `Resultado` (no cubre el recálculo,
  que conserva la fila).

## R3 — Evaluación pura en `pruebas/limites.py`

- **Decision**: módulo nuevo sin acceso a la base:
  - `leer_limite(texto)` → número `Decimal`, `AUSENTE` («Ausente»/«Ausencia», sin distinguir
    mayúsculas), `None` (vacío) o `NO_COMPARABLE` (cualquier otro texto: «SOE», «NE»,
    «Ph-0,2»…). Acepta punto o coma decimal («8.5», «7,01»).
  - `limites_aplicables(prueba, tipo_vertido)` → mínimo, máximo, norma y origen: los de
    `prueba.limites_vertido` para Cloacal/Canal si existe esa fila (reemplaza a los generales
    completos); si no, los generales de la prueba. Agua usa siempre los generales.
  - `evaluar(valor, limites)` → `Evaluacion.CUMPLE`, `FUERA_DE_NORMA` o `SIN_LIMITE`, con las
    reglas de FR-007: si algún límite es `NO_COMPARABLE` o ambos están vacíos → sin límite
    comparable; `AUSENTE` → cumple solo si `valor == 0`; numéricos → `min <= valor <= max` con los
    extremos que haya (bordes inclusivos).
  - `Evaluacion` es un `TextChoices` (`cumple`, `fuera_de_norma`, `sin_limite`).
- **Rationale**: CLAUDE.md (SCRUM-64) deja a la US 6.4 «convertir los límites a número para
  comparar». El principio III exige casos conocidos: funciones puras se prueban con los límites
  reales del catálogo sin base de datos. Vive en `pruebas` porque interpreta el catálogo, igual
  que `pruebas/formulas.py`. Compara con `Resultado.valor` completo, no con el redondeado.
- **Alternatives**: convertir los límites a columnas numéricas en el catálogo (cambia SCRUM-64 y
  la importación; los textos no comparables igual necesitarían otra columna); evaluar en el
  template (las reglas de negocio no van en templates, principio IV).

## R4 — Permiso en `Validacion` y grupo «Bioquímicos» por migración

- **Decision**: `Validacion.Meta.permissions = [("validar_resultados", "Puede validar
  resultados")]`, creado por la migración del modelo. Una migración de datos aparte crea el grupo
  «Bioquímicos» con ese permiso: llama a `create_permissions` para la app `estudios` (los permisos
  se crean recién en `post_migrate`) y hace `Group.objects.get_or_create`. La reversa quita el
  permiso del grupo y borra el grupo solo si quedó sin permisos ni usuarios.
- **Rationale**: mismo patrón que `gestionar_catalogo` (US 5.5): permiso de Django, vista con
  `@permission_required(..., raise_exception=True)`, servicio que lo revalida y `{% if
  perms.estudios.validar_resultados %}` en los templates. Con la migración el grupo existe en cada
  máquina y en el deploy sin pasos manuales (FR-002); asignar personas queda en el admin.
- **Alternatives**: crear el grupo a mano en el admin (cada integrante y el deploy lo olvidan);
  un comando de management (un paso más para recordar); un campo «es bioquímico» en el usuario
  (rol nuevo, la constitution prefiere lo que trae Django).

## R5 — Una pantalla para todas, con el flujo de carga y corrección

- **Decision**: vista `validar_resultados` en `/estudios/<pk>/resultados/validar/` con `accion` =
  `revisar` / `editar` / `marcar_todas` / `confirmar`, como `cargar_mediciones` y
  `corregir_mediciones`. `ValidarResultadosForm(data, filas)` crea por cada prueba Cargada con
  resultado un `BooleanField` `validar_<pk>` (inicial: marcado solo si la evaluación es «Cumple»)
  y un oculto `resultado_<pk>` con el valor que se vio (`str(resultado.valor)`). Exige al menos
  una marcada. «Marcar todas» es un botón del formulario que vuelve a mostrarlo con todas
  marcadas: sin JavaScript.
- **Rationale**: el equipo ya conoce el flujo revisar/editar/confirmar y sus componentes; el
  valor oculto es la misma concurrencia optimista que `original_<pk>` en la US 6.3 (SC-006).
- **Alternatives**: validar desde el detalle con un botón por fila (no permite el resumen ni la
  selección inicial pedida); JavaScript para «Marcar todas» (la constitution prioriza templates
  del servidor y no hace falta).

## R6 — Servicio `validar_resultados`

- **Decision**: `servicios.validar_resultados(estudio_pk, elegidas, usuario)` con `elegidas =
  {asignacion_pk: valor_visto}`:
  1. Rechaza sin sesión activa o sin el permiso (`ValidarResultadosError`).
  2. `atomic` + bloquea el estudio (`select_for_update`), como la carga; rechaza si no existe o si
     no `admite_correcciones` (informe emitido).
  3. Bloquea las asignaciones elegidas del estudio (`of=("self",)`, orden por código) con
     `prueba`, `prueba__limites_vertido`, `resultado`.
  4. Por cada una, omite e informa: «ya estaba validada» (Completada), «ya no tenía resultado»
     (sin resultado), «cambió mientras se revisaba» (`str(resultado.valor) != valor_visto`).
  5. Si no, evalúa con los límites vigentes (R3), crea la `Validacion` y la pasa a Completada.
  6. Si ninguna asignación del estudio queda fuera de Completada, el estudio pasa a Finalizado.
  Devuelve `ResultadoValidacion(validadas, omitidas, finalizado)`.
- **Rationale**: mismo orden de bloqueos que carga, corrección y quita (estudio, después filas):
  no hay inversión de locks y dos validaciones simultáneas se serializan; la segunda informa «ya
  estaba validada» (FR-014). La evaluación se toma al confirmar, que es lo que queda guardado.
- **Alternatives**: validar fuera de la transacción del estudio (carreras con una corrección);
  fallar todo el envío ante una omisión (la spec pide validar el resto).

## R7 — Evaluación visible en el detalle

- **Decision**: la vista `detalle` adjunta a cada asignación su evaluación: para Completada, la
  guardada en la `Validacion` vigente (FR-012); para las que tienen resultado y no están validadas,
  `limites_aplicables` + `evaluar` en vivo (FR-008). El template muestra una etiqueta
  `ui/estado.html` (Cumple → `success`, Fuera de norma → `danger`, Sin límite comparable →
  `neutral`), el límite como figura en el catálogo y, si está validada, «Validada por … · fecha».
  El botón «Validar resultados» aparece con el permiso, sin informe emitido y con alguna prueba
  Cargada con resultado.
- **Rationale**: reusa los componentes de SCRUM-67 sin CSS nuevo (`etiqueta-danger` ya existe),
  así el CSS compilado no cambia. Una sola consulta extra (`prefetch_related` de los límites).
- **Alternatives**: guardar la evaluación en vivo en la base (se desactualiza si cambia el
  catálogo antes de validar).

## R8 — Estados del estudio

- **Decision**: esta historia solo agrega la transición a **Finalizado** (R6, paso 6). La vuelta a
  En proceso o a Pendiente de análisis ya la hace `estado_tras_correccion` (US 6.3 y 6.5) y no se
  toca. Las pruebas calculadas cuentan igual que las medidas.
- **Rationale**: cada historia es dueña de las transiciones que provoca (acuerdo de las US 6.2 y
  6.3).
- **Alternatives**: recalcular el estado del estudio en un método único para todas las historias
  (refactor fuera de alcance).
