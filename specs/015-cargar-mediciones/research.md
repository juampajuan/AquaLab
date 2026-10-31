# Research: Cargar mediciones

**Feature**: `015-cargar-mediciones` | **Plan**: [plan.md](./plan.md)

No quedan `NEEDS CLARIFICATION`: el paso a "En proceso" y la precisión se resolvieron en la sección
*Clarifications* de la spec (2026-10-31). Se reutilizan de US 5.3/5.4 el bloqueo de la fila del
estudio, el flujo revisar/confirmar sin borrador y el manejo de errores.

## R1 — La medición vive en la app `estudios`

- **Decision**: modelo nuevo `Medicion` en `estudios/models.py`, con relación uno a uno a
  `PruebaEstudio`.
- **Rationale**: la medición pertenece a la prueba *del estudio*, no a la prueba del catálogo. La
  constitution fija las apps por módulo (`usuarios`, `clientes`, `muestras`, `estudios`, `pruebas`,
  `informes`, `comparacion`) y no prevé una app de mediciones. Ponerla en `estudios` evita
  dependencias circulares con `PruebaEstudio` y deja el servicio junto a `agregar_prueba` y
  `quitar_prueba`.
- **Alternatives**: app nueva `mediciones` (no está en la constitution); modelo en `pruebas` (esa
  app es el catálogo y tendría que importar `estudios`).

## R2 — Una medición por prueba del estudio, con `PROTECT`

- **Decision**: `Medicion.asignacion = OneToOneField(PruebaEstudio, on_delete=PROTECT,
  related_name="medicion")`.
- **Rationale**: la unicidad la garantiza la base (FR-012, SC-004). `PROTECT` es lo que pidió US 5.4
  (`CLAUDE.md`, nota Epic 6): `quitar_prueba` ya captura `ProtectedError`, así que nunca se borra
  una asignación con medición aunque el estado fallara. US 6.3 (modificar) actualizará esta fila en
  lugar de crear otra.
- **Alternatives**: `ForeignKey` + `UniqueConstraint` — equivalente pero menos expresivo; guardar el
  valor en `PruebaEstudio` — mezcla la asignación con el dato primario y pierde usuario y fecha
  propios de la carga.

## R3 — Valor exacto con sus decimales escritos

- **Decision**: `valor = DecimalField(max_digits=18, decimal_places=6)` más
  `decimales = PositiveSmallIntegerField()` (0–6, `CheckConstraint`). La propiedad
  `Medicion.valor_ingresado` devuelve `valor.quantize(Decimal(1).scaleb(-decimales))`, que es el
  número tal como se escribió ("7,20" → `Decimal("7.20")`).
- **Rationale**: la constitution exige `Decimal` (principio IV) y la clarificación pide conservar
  los ceros finales. Una columna `numeric(18, 6)` rellena a 6 decimales (7.200000), así que la
  cantidad escrita se guarda aparte. 12 cifras enteras y 6 decimales cubren con margen pH,
  volúmenes, absorbancias y conductividades. El `decimales` sale del exponente del `Decimal`
  parseado, no se pide al usuario.
- **Alternatives**: guardar el texto (no es `Decimal`; cada lectura tendría que convertir);
  `DecimalField` sin escala fija (Django exige `decimal_places`); `FloatField` (prohibido).

## R4 — Formato de entrada

- **Decision**: función `leer_valor(texto) -> Decimal` en `estudios/mediciones.py`. Quita espacios
  al principio y al final, acepta `^[+-]?(\d+([.,]\d+)?|[.,]\d+)$`, reemplaza la coma por punto y
  construye el `Decimal` desde el texto. Rechaza (con `ValidationError` y mensaje en español): más
  de 12 cifras enteras, más de 6 decimales y cualquier otro formato (letras, `1.234,5`, `1e3`,
  espacios internos, `%`). Vacío → `None` (no se carga esa prueba).
- **Rationale**: una expresión regular explícita evita lo que `Decimal()` acepta y el laboratorio
  no usa (`NaN`, `Infinity`, `1E3`, `_`). Al no aceptar separador de miles no hay ambigüedad entre
  "1.234" (decimal) y miles. Una función pura se prueba con casos conocidos (principio III).
- **Alternatives**: `forms.DecimalField` con `localize=True` — con `es-ar` toma el punto como
  separador de miles y no acepta los dos separadores.

## R5 — Formulario dinámico, revisar y confirmar sin borrador

- **Decision**: una vista `cargar_mediciones` con `accion` = `revisar` / `editar` / `confirmar`
  por POST, como `agregar_prueba` (US 5.3). `CargarMedicionesForm(data, asignaciones=...)` crea un
  `CharField` opcional `medicion_<asignacion_pk>` por prueba; `clean()` usa `leer_valor` en cada
  campo y exige al menos un valor (error general). La confirmación reenvía los textos en campos
  ocultos; «Volver a editar» vuelve al formulario con los valores.
- **Rationale**: los datos viajan en el POST y se revalidan al confirmar; no hace falta guardar un
  borrador en la sesión. Si hay errores se re-renderiza el formulario con los valores (FR-006,
  FR-007).
- **Alternatives**: borrador en sesión con token firmado (como US 5.1) — innecesario: no hay
  identificador a reservar y el reenvío ya es idempotente por el estado (R6); `formset` de Django
  — agrega management form y complica las etiquetas por prueba.
- **Asignaciones del formulario**: al abrir, revisar y editar, las pendientes que no son calculadas.
  Al confirmar, todas las no calculadas del estudio (cualquier estado), para que un valor de una
  prueba que mientras tanto quedó Cargada llegue al servicio y se informe como omitido en lugar de
  perderse en silencio. Los campos enviados de asignaciones que ya no existen se cuentan
  (`form.pruebas_quitadas()`) y se informan.

## R6 — Servicio con el estudio bloqueado

- **Decision**: `cargar_mediciones(estudio_pk, valores, usuario) -> ResultadoCarga` en
  `estudios/servicios.py`. Dentro de `transaction.atomic()`: `select_for_update()` del estudio →
  `admite_mediciones` → asignaciones del estudio con `select_for_update(of=("self",))` → por cada
  valor, en orden de código: omitir si no existe, si no está `Pendiente` o si la prueba es
  calculada; si no, crear la `Medicion` (unidad copiada de `prueba.unidad_medicion`) y pasar la
  asignación a `Cargada`. Si se guardó al menos una y el estudio está "Pendiente de análisis", pasa
  a "En proceso".
- **Rationale**: es el mismo orden de bloqueo que `agregar_prueba` y `quitar_prueba` (estudio →
  asignación): una carga y una quita simultáneas se serializan y nunca queda una medición de una
  prueba quitada; dos cargas simultáneas de la misma prueba guardan una sola. El reenvío de una
  confirmación encuentra las pruebas ya `Cargada` y las informa como omitidas sin cambiar nada
  (FR-012). Todo el envío es una transacción: si la base falla, no queda nada a medias.
- **Alternatives**: advisory lock global (como la creación de estudios) — bloquea cargas de
  estudios distintos sin necesidad; rechazar todo el envío si una prueba ya está cargada — obliga a
  reingresar valores válidos (la spec pide guardar el resto).
- **Errores**: `CargarMedicionesError` para rechazos de todo el envío (sin sesión, estudio
  inexistente, estudio que no admite carga). Las omisiones por prueba no son excepciones: vuelven
  en `ResultadoCarga.omitidas` como pares `(prueba, motivo)`.

## R7 — Una sola regla de estudio que admite carga

- **Decision**: `Estudio.admite_mediciones` (estado `pendiente_analisis` o `en_proceso`), usado por
  el detalle, la vista y el servicio (que lo revalida bajo el bloqueo), igual que
  `admite_modificaciones`.
- **Rationale**: evita reglas distintas en template, vista y servicio (`CLAUDE.md`, US 5.3).

## R8 — Mostrar valores con coma

- **Decision**: los templates muestran `medicion.valor_ingresado`; con `LANGUAGE_CODE = "es-ar"`
  Django localiza el `Decimal` con coma decimal y conserva sus decimales (sin separador de miles,
  `USE_THOUSAND_SEPARATOR` queda en `False`). Una prueba sin unidad muestra «Sin unidad».
- **Rationale**: sin filtros nuevos; coincide con cómo escribe el analista.
