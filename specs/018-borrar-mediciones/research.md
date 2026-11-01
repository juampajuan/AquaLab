# Research: Borrar mediciones

**Feature**: `018-borrar-mediciones` | **Plan**: [plan.md](./plan.md)

No hay `NEEDS CLARIFICATION`: las decisiones de interfaz y de estado las tomó el usuario al
especificar la US 6.3 y están en SCRUM-72.

Punto de partida (rama `017-modificar-mediciones`, PR #30): `CorregirMedicionesForm` (campos
`medicion_<pk>` y `original_<pk>`, `cambios()` contra el original), el servicio
`corregir_mediciones` (estudio bloqueado, concurrencia optimista, `recalcular_resultados` en la
misma transacción, Finalizado → En proceso), el aviso «Perderán la validación» con
`calculo.afectadas`, y en US 6.2 `calculo.recalcular`, cuya función `descartar` ya borra el
resultado de una prueba que no se puede calcular y la deja Pendiente si no tiene medición.

## R1 — Borrar es una corrección más, en el mismo envío

- **Decision**: el servicio sigue siendo `corregir_mediciones(estudio_pk, cambios, usuario)`; en
  `cambios = {asignacion_pk: (original, nuevo)}` un `nuevo = None` significa borrar.
  `ResultadoCorreccion` suma `borradas: list[Prueba]`. Correcciones y borrados se aplican en la
  misma transacción y se recalculan juntos (FR-011).
- **Rationale**: misma pantalla, mismo bloqueo, misma regla del original y mismo recálculo; un
  servicio aparte duplicaría todo eso y obligaría a dos transacciones para un mismo envío.
- **Alternatives**: servicio `borrar_mediciones` separado (dos confirmaciones o dos
  transacciones); vista de borrado por fila (una confirmación por medición, contra SC-001).

## R2 — El recálculo de US 6.2 ya resuelve los efectos

- **Decision**: el servicio borra la `Medicion` y llama a `recalcular_resultados` con las
  asignaciones corregidas **y** borradas. Para una borrada, `calculo.recalcular` encuentra
  «Falta la medición.» (`FaltanDatos`) y `descartar` borra su `Resultado` y la pasa a Pendiente
  (también desde Completada); sus calculadas dependientes quedan sin referencias y siguen el mismo
  camino (FR-005, FR-006). Sin cambios en `calculo.py`.
- **Rationale**: una sola definición de qué pasa cuando falta un dato (US 6.2); el borrado no
  inventa reglas propias. `Resultado` tiene `PROTECT` hacia la asignación, no hacia la medición,
  así que borrar la medición no choca con el resultado.

## R3 — Estado del estudio después del envío

- **Decision**: al final del servicio, con el estudio bloqueado: si no queda ninguna asignación
  `cargada` ni `completada` → `pendiente_analisis`; si no, si estaba `finalizado` y alguna no está
  `completada` → `en_proceso` (regla de US 6.3).
- **Rationale**: FR-007 y la definición de «En proceso» de US 5.2. Con `pendiente_analisis`,
  `admite_modificaciones` vuelve a ser verdadero y el detalle ofrece otra vez «Agregar prueba» y
  «Quitar», sin código nuevo.

## R4 — Formulario: casilla `borrar_<pk>` y validación condicional

- **Decision**: `CorregirMedicionesForm` suma por fila `BooleanField(required=False)`
  `borrar_<pk>`. El campo `medicion_<pk>` pasa a `required=False` y `clean()` exige el valor
  solo si la fila no está marcada («La medición no puede quedar vacía.», como en US 6.3); una fila
  marcada no se valida y su texto se ignora (FR-003). `cambios()` devuelve `(asignacion, anterior,
  None)` para las marcadas, así «No hay cambios para guardar.» no aparece si hay al menos un
  borrado.
- **Rationale**: la regla «prevalece el borrado» tiene que impedir que un campo vacío o inválido
  de esa fila frene el envío; con `required=True` Django agregaría el error antes de `clean()`.

## R5 — Reenvío y borrados simultáneos

- **Decision**: al confirmar, la vista arma el formulario con las asignaciones del estudio cuyo
  `original_<pk>` llegó en el POST, tengan o no medición (al abrir y al revisar, solo las que
  tienen). El servicio, bajo el bloqueo: medición inexistente → omitida «ya no tenía medición»;
  vigente distinto del original → «cambió mientras se editaba»; si no, borra.
- **Rationale**: FR-009. Si el formulario de confirmación solo tomara las que tienen medición, un
  reenvío de un borrado ya aplicado daría «No hay cambios para guardar.» en lugar del aviso
  correcto (el mismo problema que el hallazgo I1 de US 6.3).
- **Alternatives**: ignorar en silencio los borrados ya aplicados (no cumple FR-009/FR-010).
