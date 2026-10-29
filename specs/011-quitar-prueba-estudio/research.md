# Research: Quitar prueba del estudio

**Feature**: `011-quitar-prueba-estudio` | **Plan**: [plan.md](./plan.md)

No quedan `NEEDS CLARIFICATION`: las dudas de la spec se resolvieron en su sección *Clarifications*
(2026-10-27). Se reutilizan de [US 5.3](../010-agregar-prueba-estudio/research.md) el detalle del
estudio (R1), el bloqueo de fila (R3), `Estudio.admite_modificaciones` (R4) y el manejo de errores
(R6).

> **Actualización 2026-10-28**: US 5.2 ya guarda el estado individual de cada prueba asignada
> (`Pendiente`, `Cargada`, `Completada`) y US 5.3 está implementada en `010-agregar-prueba-v2`. R2
> pasa a los componentes de SCRUM-67 y R4 se apoya en ese estado.

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
- **Alternatives**: un modal con JavaScript — depende de JavaScript y complica los tests.
- **Interfaz**: la confirmación se arma con `ui/encabezado.html`, el resumen y las acciones de
  confirmación de SCRUM-67, como `agregar_prueba_confirmar.html` de US 5.3.

## R3 — Servicio con bloqueo de fila y regla de la última prueba

- **Decision**: `estudios/servicios.py` suma las subclases `PruebaYaQuitada` y `UltimaPrueba` de
  `GestionPruebasError` (US 5.3) y `quitar_prueba(estudio_pk, asignacion_pk, usuario)`. Dentro de
  `transaction.atomic()`:
  1. `Estudio.objects.select_for_update().filter(pk=...).first()` (inexistente → error);
  2. revalida `admite_modificaciones`;
  3. asignación del estudio con `select_for_update()`; inexistente o de otro estudio →
     `PruebaYaQuitada`;
  4. `pruebas_asignadas.count() <= 1` → `UltimaPrueba` (FR-011);
  5. `puede_quitarse()` falso → rechazo (R4);
  6. `delete()`; un `ProtectedError` (futuras mediciones con `PROTECT`) se traduce en el mismo
     rechazo que el paso 5.
- **Rationale**: el bloqueo de la fila del estudio serializa las quitas sobre un mismo estudio, así
  que dos quitas simultáneas de las dos únicas pruebas no pueden dejarlo vacío (edge case, SC-003):
  la segunda cuenta después de que la primera hizo commit. Es el mismo esquema de `agregar_prueba`.
  Bloquear también la asignación hace que su estado se lea sin carreras: si una historia del Epic 6
  la pasa a `Cargada` al mismo tiempo, una de las dos operaciones espera a la otra (edge case de
  mediciones cargadas mientras se confirma).
- **Alternatives**: confiar en una constraint — una restricción simple no puede contar filas
  relacionadas; `pg_advisory_xact_lock` global — serializa estudios sin relación.

## R4 — Punto de extensión para mediciones en el modelo

- **Decision**: `PruebaEstudio.puede_quitarse()` devuelve `self.estado == EstadoPruebaEstudio.PENDIENTE`.
  `Cargada` significa una medición registrada y `Completada` un resultado validado (US 5.2), así que
  ninguno de los dos se puede quitar. Su docstring indica que las historias del Epic 6 deben cambiar
  ese estado al cargar mediciones o resultados y que esas tablas deben apuntar a `PruebaEstudio`
  con `PROTECT`. El detalle lo usa para mostrar u ocultar «Quitar»; el servicio lo vuelve a
  comprobar con la asignación bloqueada.
- **Rationale**: la constitution (Principio IV) pide las reglas de negocio en el modelo. El estado ya
  existe, así que FR-004 se cumple sin inventar modelos de mediciones (YAGNI); el `PROTECT` futuro
  es una segunda barrera. Se agrega una nota en `CLAUDE.md` para el Epic 6.
- **Alternatives**: devolver siempre `True` hasta US 6.1 — ignora el estado que US 5.2 ya guarda;
  un campo booleano `tiene_mediciones` — duplica lo que dice el estado; crear ya el modelo
  `Medicion` — fuera del alcance.

## R5 — Borrado real de la asignación

- **Decision**: quitar hace `delete()` de la `PruebaEstudio`. No hay migración.
- **Rationale**: es la decisión de la spec (Clarifications, FR-007). La asignación sin mediciones no
  tiene historial, así que el Principio IV no exige conservarla. Al no existir la fila, las
  historias de mediciones e informe no la ven, sin filtros adicionales.
- **Alternatives**: marca lógica de quitada — descartada en la spec.
