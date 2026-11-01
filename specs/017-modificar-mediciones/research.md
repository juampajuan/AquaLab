# Research: Modificar las mediciones

**Feature**: `017-modificar-mediciones` | **Plan**: [plan.md](./plan.md)

No quedan `NEEDS CLARIFICATION`: el historial, los permisos y el borrado (separado en US 6.5,
SCRUM-72) se resolvieron en la sección *Clarifications* de la spec.

Punto de partida (rama `016-calcular-resultado`, PR #29): `Medicion` uno a uno con
`PruebaEstudio` (US 6.1), `leer_valor`, el flujo revisar/editar/confirmar de `cargar_mediciones`,
`Resultado`, `calculo.recalcular` y el servicio `recalcular_resultados`, que rechaza con informe
emitido y está pensado para llamarse en la misma transacción que actualiza la medición (US 6.2).

## R1 — La misma fila de `Medicion`, con quién la corrigió

- **Decision**: `Medicion` suma `corregida_por = ForeignKey(AUTH_USER_MODEL, null=True,
  blank=True, on_delete=PROTECT, related_name="mediciones_corregidas", editable=False)` y
  `fecha_correccion = DateTimeField(null=True, blank=True)`. Corregir actualiza `valor`,
  `decimales`, `corregida_por` y `fecha_correccion`; `cargada_por` y `fecha_carga` no cambian.
- **Rationale**: Clarifications: solo el valor vigente, sin historial, con quién cargó y quién
  corrigió por última vez (FR-006, FR-012). `CLAUDE.md` ya pide actualizar la fila en US 6.3 en
  lugar de crear otra (uno a uno con `PruebaEstudio`).
- **Alternatives**: tabla de historial (descartada en Clarifications); campos de texto con el
  valor anterior (sería un historial a medias).

## R2 — Una pantalla para todas, con el mismo flujo que la carga

- **Decision**: vista `corregir_mediciones` en `/estudios/<pk>/mediciones/corregir/` con
  `accion` = `revisar` / `editar` / `confirmar`, como `cargar_mediciones` (US 6.1, research R5).
  `CorregirMedicionesForm(data, asignaciones)` crea por cada asignación con medición un
  `CharField` **obligatorio** `medicion_<pk>` precargado con el valor tal como se escribió (coma
  decimal) y un oculto `original_<pk>` con el valor vigente al abrir. `clean()` usa `leer_valor`;
  vacío → «La medición no puede quedar vacía.»; sin ningún cambio → error general «No hay cambios
  para guardar.». `cambios()` devuelve `(asignacion, anterior, nuevo)` solo de las filas cuyo
  valor escrito difiere del vigente (contando los decimales: `7,2` ≠ `7,20`).
- **Rationale**: el empleado ya conoce el flujo de la carga; reutiliza `leer_valor`, los
  componentes y los mensajes. Los datos viajan en el POST, sin borrador en sesión.
- **Alternatives**: una pantalla por medición (más clics, y corregir varias exige varias
  confirmaciones, contra SC-001); edición en línea con JavaScript (la constitution prefiere
  templates en el servidor).

## R3 — Detectar que otro corrigió mientras se editaba

- **Decision**: concurrencia optimista con el valor original. El formulario lleva `original_<pk>`
  (texto canónico del valor al abrir, con sus decimales). Al confirmar, bajo el bloqueo del
  estudio, el servicio compara el valor vigente con el original: si difieren y el vigente es el
  nuevo → omitida «ya tenía ese valor» (reenvío o mismo cambio simultáneo); si difieren de otra
  forma → omitida «cambió mientras se editaba»; si coinciden → se corrige.
- **Rationale**: FR-010 y SC-005 sin campos de versión: el valor (con sus decimales) es lo que
  importa al empleado. Un reenvío de la misma confirmación no vuelve a cambiar nada.
- **Alternatives**: columna de versión en `Medicion` (más esquema para el mismo resultado);
  comparar `fecha_correccion` (no distingue un reenvío propio de un cambio ajeno).

## R4 — Servicio que corrige y recalcula en una transacción

- **Decision**: `corregir_mediciones(estudio_pk, cambios, usuario) -> ResultadoCorreccion` en
  `estudios/servicios.py`, con `cambios = {asignacion_pk: (original, nuevo)}`. Dentro de
  `transaction.atomic()`: sesión activa → `select_for_update()` del estudio → si
  `not estudio.admite_correcciones` lanza `CorregirMedicionesError` con el mensaje de US 6.2 →
  mediciones del estudio de esas asignaciones con `select_for_update()` → por cada una, regla de
  R3 → actualizar las que corresponde → `recalcular_resultados(estudio.pk, corregidas, usuario)`
  en la misma transacción (US 6.2) → si el estudio estaba `finalizado` y alguna prueba ya no está
  `completada`, pasarlo a `en_proceso`. Devuelve `corregidas`, `omitidas` (pares `(Prueba,
  motivo)`) y `sin_calcular` (de US 6.2).
- **Rationale**: FR-007 (todo o nada), FR-008, FR-009. Mismo orden de bloqueo que carga, quita y
  recálculo (estudio → filas), así no hay bloqueos cruzados. `recalcular_resultados` vuelve a
  bloquear el estudio dentro de la misma transacción, lo que en PostgreSQL no espera.
- **Alternatives**: llamar directo a `calculo.recalcular` (se saltea la regla del informe que la
  6.2 dejó en `recalcular_resultados`, el punto de entrada acordado).

## R5 — Avisar antes de confirmar quién pierde la validación

- **Decision**: extraer de `calculo.recalcular` la función `afectadas(todas, codigos)` (las
  cambiadas y sus dependientes, directos o indirectos) y usarla también en la vista de revisión:
  las afectadas en estado `completada` se listan en el resumen («Perderán la validación: COD ·
  nombre, …»).
- **Rationale**: FR-005 y US3 Esc. 1. Una sola definición de «afectada» para el aviso y para el
  recálculo.

## R6 — Dónde se ve

- **Decision**: en `detalle`, botón **Corregir mediciones** (`btn btn-secundario`, ícono
  `pencil`) si `estudio.admite_correcciones` y hay al menos una medición; en la columna Medición,
  debajo de «cargada por», una línea «Corregida por <nombre> · <fecha>» si la medición fue
  corregida.
- **Rationale**: FR-002, FR-012; componentes existentes, sin CSS nuevo.
