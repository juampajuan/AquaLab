# Research: Quitar prueba del estudio

**Feature**: `011-quitar-prueba-estudio` | **Plan**: [plan.md](./plan.md)

No quedan `NEEDS CLARIFICATION`: las dudas de la spec se resolvieron en su sección *Clarifications*
(2026-10-27). Se reutilizan de [US 5.3](../010-agregar-prueba-estudio/research.md) el detalle del
estudio (R1), el bloqueo de fila (R3), `Estudio.admite_modificaciones` (R4) y el manejo de errores
(R6).

## R1 — Quitar identifica la asignación, no la prueba

- **Decision**: la URL de quitar usa el `pk` de `PruebaEstudio` y el servicio lo busca dentro del
  estudio (`estudio.pruebas_asignadas.filter(pk=...)`).
- **Rationale**: si la prueba se quita y después se vuelve a agregar (US 5.3), la nueva asignación
  tiene otro `pk`; un reenvío de la confirmación vieja no quita la asignación nueva y se informa
  "ya no forma parte del estudio" (FR-010, edge case). Filtrar por estudio impide quitar
  asignaciones de otro estudio cambiando la URL.
- **Alternatives**: usar el `pk` de `Prueba` — un reenvío tardío quitaría una prueba agregada otra
  vez a propósito.

## R2 — Confirmación GET/POST sin borrador

- **Decision**: `GET /estudios/<pk>/pruebas/<asignacion_pk>/quitar/` muestra la confirmación; el
  `POST` a la misma URL llama al servicio. "Cancelar" es un enlace al detalle.
- **Rationale**: la operación tiene un solo dato, que ya está en la URL; no hace falta formulario ni
  sesión. Es el patrón habitual de Django para confirmar un borrado y cumple la regla de la
  constitution de confirmar antes de eliminar (FR-005).
- **Alternatives**: modal de Bootstrap — depende de JavaScript y complica los tests.

## R3 — Servicio con bloqueo de fila y regla de la última prueba

- **Decision**: `estudios/servicios.py` suma las subclases `PruebaYaQuitada` y `UltimaPrueba` de
  `GestionPruebasError` (US 5.3) y `quitar_prueba(estudio_pk, asignacion_pk, usuario)`. Dentro de
  `transaction.atomic()`:
  1. `Estudio.objects.select_for_update().filter(pk=...).first()` (inexistente → error);
  2. revalida `admite_modificaciones`;
  3. asignación inexistente o de otro estudio → `PruebaYaQuitada`;
  4. `pruebas_asignadas.count() <= 1` → `UltimaPrueba` (FR-011);
  5. `puede_quitarse()` falso → rechazo (R4);
  6. `delete()`; un `ProtectedError` (futuras mediciones con `PROTECT`) se traduce en el mismo
     rechazo que el paso 5.
- **Rationale**: el bloqueo de la fila del estudio serializa las quitas sobre un mismo estudio, así
  que dos quitas simultáneas de las dos únicas pruebas no pueden dejarlo vacío (edge case, SC-003):
  la segunda cuenta después de que la primera hizo commit. Es el mismo esquema de `agregar_prueba`.
- **Alternatives**: confiar en una constraint — una restricción simple no puede contar filas
  relacionadas; `pg_advisory_xact_lock` global — serializa estudios sin relación.

## R4 — Punto de extensión para mediciones en el modelo

- **Decision**: `PruebaEstudio.puede_quitarse()` devuelve hoy `True` (no existen mediciones ni
  resultados). Su docstring indica que US 6.1 y siguientes deben devolver `False` cuando la
  asignación tenga mediciones o resultados, y que esas tablas deben apuntar a `PruebaEstudio` con
  `PROTECT`. El detalle lo usa para mostrar u ocultar «Quitar»; el servicio lo vuelve a comprobar
  bajo el bloqueo.
- **Rationale**: la constitution (Principio IV) pide las reglas de negocio en el modelo. Dejar el
  método ahora fija FR-004 sin inventar modelos de mediciones (YAGNI); el `PROTECT` futuro es una
  segunda barrera. Se agrega una nota en `CLAUDE.md` para US 6.1.
- **Alternatives**: un campo booleano `tiene_mediciones` — duplica un dato que se podrá calcular;
  crear ya el modelo `Medicion` — fuera del alcance.

## R5 — Borrado real de la asignación

- **Decision**: quitar hace `delete()` de la `PruebaEstudio`. No hay migración.
- **Rationale**: es la decisión de la spec (Clarifications, FR-007). La asignación sin mediciones no
  tiene historial, así que el Principio IV no exige conservarla. Al no existir la fila, las
  historias de mediciones e informe no la ven, sin filtros adicionales.
- **Alternatives**: marca lógica de quitada — descartada en la spec.
