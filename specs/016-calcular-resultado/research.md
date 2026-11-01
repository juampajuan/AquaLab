# Research: Cálculo automático del resultado

**Feature**: `016-calcular-resultado` | **Plan**: [plan.md](./plan.md)

No quedan `NEEDS CLARIFICATION`: la precisión al mostrar, los avisos de la carga y el recálculo de
resultados validados se resolvieron en la sección *Clarifications* de la spec (2026-10-31).

Punto de partida: `estudios.Medicion` (US 6.1, uno a uno con `PruebaEstudio`), el servicio
`cargar_mediciones` (bloquea el estudio) y el catálogo de SCRUM-64: 25 pruebas de tipo Fórmula,
13 de ellas calculadas a partir de otras, con fórmulas de texto (`x` = valor medido, `{CODIGO}` =
resultado de otra prueba) que hoy nadie evalúa (`CLAUDE.md`, «Epic 6»).

## R1 — Evaluador propio de fórmulas con `Decimal`

- **Decision**: módulo `pruebas/formulas.py` con un analizador descendente recursivo pequeño:
  tokens = números (`\d+(\.\d+)?`), `x`, `{CODIGO}`, `sqrt`, `+ - * /`, paréntesis y signo
  unario. Dos funciones públicas: `validar_formula(texto)` (solo sintaxis; `ValidationError` en
  español) y `evaluar_formula(texto, x, resultados)` → `Decimal`, con `x: Decimal | None` y
  `resultados: dict[codigo, Decimal]`. Los números se construyen con `Decimal(texto)`, nunca
  pasan por `float`. Se evalúa dentro de `decimal.localcontext(prec=34)`; `sqrt` usa
  `Decimal.sqrt()`.
- **Rationale**: la constitution prohíbe `float` para mediciones y resultados (principio IV) y
  exige tests de cálculo con valores conocidos (principio III). `eval()` es inseguro y usa `float`;
  `ast.parse` también convierte las constantes a `float`. La gramática del catálogo es mínima
  (verificado sobre las 25 fórmulas de `pruebas/datos/catalogo_pruebas_agua.csv`), así que un
  analizador de ~80 líneas la cubre completa y rechaza todo lo demás (FR-002).
- **Alternatives**: `eval` con `__builtins__` vacío (inseguro, `float`); `ast` con lista blanca
  (constantes `float`); librerías como `simpleeval` o `sympy` (dependencias nuevas sin acuerdo del
  equipo, principio II).
- **Errores**: `FormulaInvalida` (sintaxis, en `validar_formula`) y `CalculoImposible(motivo)` al
  evaluar: «división por cero», «raíz cuadrada de un número negativo», «la fórmula usa el valor
  medido y la prueba no tiene medición». Las referencias faltantes no se evalúan: las detecta antes
  el motor (R3).
- **Uso en el catálogo**: `Prueba.clean()` llama a `validar_formula`, así el admin y la importación
  (`importar_catalogo_pruebas` usa `full_clean`) rechazan fórmulas que después no se podrían
  calcular. Un test verifica que las 25 fórmulas del CSV son válidas.

## R2 — Un resultado por prueba del estudio, con lo usado para calcularlo

- **Decision**: modelo `estudios.Resultado` con `asignacion = OneToOneField(PruebaEstudio,
  on_delete=PROTECT, related_name="resultado")`, `valor = DecimalField(max_digits=28,
  decimal_places=10)`, `unidad` y `formula` copiadas de la prueba al calcular, y
  `fecha_calculo = DateTimeField(auto_now=True)`. Al recalcular se actualiza la misma fila.
- **Rationale**: igual que `Medicion` (US 6.1): uno a uno, `PROTECT` (US 5.4 ya captura
  `ProtectedError` al quitar), y la unidad y la fórmula guardadas para que un cambio del catálogo
  no altere ni reinterprete resultados (FR-004, FR-010). Diez decimales guardados sobran para
  mostrar cuatro (Clarifications) y para encadenar cálculos sin perder precisión visible; 18
  cifras enteras cubren los valores del catálogo (NTK total es del orden de miles).
- **Alternatives**: guardar el resultado en `Medicion` (las calculadas no tienen medición);
  calcularlo siempre al vuelo sin guardarlo (la US 6.4 valida y el informe necesita un valor
  fijo, y no habría fecha de cálculo ni fórmula usada).
- **Sin resultado no hay fila**: si una prueba no se puede calcular, no tiene `Resultado`. El
  motivo no se guarda: se obtiene al vuelo (R4), así nunca queda un motivo viejo.

## R3 — Motor de cálculo: solo lo afectado, en orden de dependencia

- **Decision**: `estudios/calculo.py` con `recalcular(estudio, asignaciones_cambiadas) ->
  list[(Prueba, motivo)]`, que debe llamarse con el estudio ya bloqueado (`select_for_update`)
  dentro de la transacción del llamador. Pasos:
  1. Carga todas las asignaciones del estudio con `prueba`, `medicion` y `resultado`, y arma el
     grafo «prueba → pruebas calculadas que la referencian» con `referencias_formula`.
  2. Afectadas = las cambiadas + todas sus dependientes, directas o indirectas.
  3. Las recorre en orden topológico (Kahn); las que quedan en un ciclo se tratan como «no se
     puede calcular: referencias circulares».
  4. Por cada una: si se puede calcular (R1), crea o actualiza su `Resultado`; si estaba
     `Completada` pasa a `Cargada` (pierde la validación, Clarifications); si es calculada y
     estaba `Pendiente` pasa a `Cargada`. Si no se puede, borra el `Resultado` que tuviera; una
     calculada vuelve a `Pendiente` y una medida queda `Cargada` (tiene medición).
  5. Devuelve las que fallaron por `CalculoImposible` (no las que esperan referencias), para el
     mensaje de la carga (FR-013).
- **Rationale**: recalcular solo las afectadas cumple «las demás no cambian» (FR-008) sin tocar
  la fecha ni la validación de resultados ajenos al cambio. El orden topológico resuelve cadenas de
  cualquier largo (Sodio → Meq/l de Sodio → Total Cationes → CE/Sumatoria). Al correr bajo el
  bloqueo del estudio, igual que `cargar_mediciones` y `quitar_prueba`, dos cargas simultáneas no
  calculan con datos a medias.
- **Directo**: resultado = valor medido, `formula = ""`. **Fórmula sin referencias**: `x` = valor
  medido. **Calculada**: sin `x`, con los resultados de sus referencias.
- **Alternatives**: recalcular todo el estudio en cada cambio (más simple pero rompe FR-008 y le
  quitaría la validación a resultados que no cambiaron); señales de Django (`CLAUDE.md` ya evita
  señales en US 1.3 por `queryset.update()`; aquí las llamadas son explícitas).

## R4 — Motivo de una prueba sin resultado, al vuelo

- **Decision**: `estudios.calculo.motivo_sin_resultado(asignacion, por_codigo)` → texto o `None`,
  la misma lógica de evaluación que usa el motor pero sin escribir. Motivos, en este orden:
  «Falta la medición.»; «No forma parte del estudio: COD · nombre.» (referencias ausentes);
  «Faltan resultados de: COD · nombre, …»; o el motivo de `CalculoImposible`. La vista `detalle`
  lo calcula para cada prueba sin resultado.
- **Rationale**: una sola fuente de las reglas (como `motivo_para_no_quitar` en US 5.4) y sin
  motivos guardados que puedan quedar viejos (FR-006). Con ≤ 90 pruebas por estudio es barato.

## R5 — Puntos de entrada

- **Decision**:
  - `cargar_mediciones` (US 6.1) llama a `recalcular(estudio, guardadas)` antes de cerrar su
    transacción y suma `ResultadoCarga.sin_calcular` (pares `(Prueba, motivo)`); la vista los
    muestra como advertencias «COD: no se pudo calcular el resultado (motivo).» (FR-013).
  - Servicio nuevo `recalcular_resultados(estudio_pk, asignacion_pks, usuario)` en
    `estudios/servicios.py`: sesión activa → bloquea el estudio → si
    `not estudio.admite_correcciones` lanza `RecalculoError("El estudio ya tiene el informe
    emitido: sus mediciones y resultados no se pueden cambiar.")` → `recalcular(...)`. US 6.3 lo
    llamará en la misma transacción en que actualiza la medición, así un rechazo deshace también
    el cambio de la medición (FR-008, FR-009).
  - Propiedad `Estudio.admite_correcciones` → `estado != INFORME_GENERADO` (Clarifications).
- **Rationale**: la 6.2 entrega el recálculo y la regla del informe; la 6.3 solo agrega la
  pantalla y la actualización de la fila de `Medicion` (acuerdo en SCRUM-54/55). Los tests de la
  US3 cambian el valor de la medición directamente y llaman al servicio.
- **Finalizado**: si un recálculo devuelve una prueba a `Cargada` en un estudio `Finalizado`, el
  estado del estudio no se toca aquí (spec, casos límite: lo define US 6.4).

## R6 — Mostrar el resultado

- **Decision**: propiedad `Resultado.valor_mostrado` → `valor` redondeado a 4 decimales
  (`ROUND_HALF_UP`) y sin ceros finales (`normalize()`, con `0` en lugar de `-0`). Los templates lo
  muestran con la localización `es-ar` (coma decimal; `numberformat` usa formato `f`, así que
  `1E+3` se ve «1000»). Unidades: filtro `unidad` en `config/ui.py` que devuelve «Sin unidad» si el
  texto está vacío o es `--` (el catálogo usa `--` para «sin unidad»); lo usan el resultado, la
  medición y las pantallas de carga de US 6.1, que hoy mostraban «--».
- **Rationale**: Clarifications («hasta 4 decimales, sin ceros finales»); sin filtros nuevos.

## R7 — Mediciones cargadas antes de esta historia

- **Decision**: comando `python manage.py calcular_resultados` (`estudios/management/commands/`):
  por cada estudio con mediciones, bloquea el estudio y llama a `recalcular` con las asignaciones
  medidas que no tienen resultado. Es idempotente (una segunda corrida no cambia nada) y se
  documenta en el quickstart.
- **Rationale**: FR-011. Todavía no hay deploy (Render llega en la semana 5); solo hay bases de
  desarrollo con mediciones de la 6.1. Un comando reutiliza el motor real; una migración de datos
  tendría que duplicarlo con modelos históricos.
- **Alternatives**: `RunPython` en la migración (duplica el motor); calcular al abrir el detalle
  (escribiría en un GET).

## R8 — Excepción al principio IV (Governance)

- **Decision**: un resultado validado se reemplaza y pierde la validación cuando se recalcula por
  una medición corregida antes del informe (Clarifications). Se registra en *Complexity Tracking*.
- **Rationale**: el principio IV busca que lo emitido al cliente sea inalterable y trazable. La
  excepción no permite editar un resultado a mano ni conservar una validación sobre datos que
  cambiaron: el resultado se recalcula con la fórmula y debe validarse de nuevo, y todo queda
  bloqueado al emitir el informe, que es lo que recibe el cliente. Coincide con SCRUM-55
  («los nuevos valores deben reemplazar a los anteriores y revalidarse»).
