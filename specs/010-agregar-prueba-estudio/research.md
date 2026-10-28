# Research: Agregar prueba al estudio

**Feature**: `010-agregar-prueba-estudio` | **Plan**: [plan.md](./plan.md)

No quedan `NEEDS CLARIFICATION`: la duda de la spec se resolvió en su sección *Clarifications*
(2026-10-27). Este documento fija las decisiones técnicas. US 5.4
([research](../011-quitar-prueba-estudio/research.md)) reutiliza R1, R3, R4 y R6.

## R1 — Detalle mínimo del estudio como punto de entrada

- **Decision**: vista `estudios:detalle` en `GET /estudios/<pk>/` (template
  `estudios/detalle.html`) con identificador, N° PI, cliente y origen de la muestra, nombre histórico
  del tipo (`tipo_nombre_snapshot`), estado, autor, fecha de creación y la tabla de pruebas asignadas
  ordenadas por código, con la acción "Agregar prueba" si corresponde. La tabla deja una columna
  Acción que US 5.4 completa con "Quitar". El mensaje de éxito de US 5.1 (`estudios.views.exito`)
  pasa a incluir un enlace a este detalle mediante `format_html`; la redirección a `estudios:crear`
  no cambia. Un estudio inexistente responde 404.
- **Rationale**: es lo que decidió la spec (FR-002, Clarifications). El enlace en el mensaje no
  cambia el flujo ni los tests de US 5.1. `format_html` escapa los datos y el `MessageEncoder` de
  Django conserva la marca de texto seguro al serializar el mensaje. Usar el snapshot del nombre
  respeta FR-009: el estudio muestra el tipo tal como se confirmó.
- **Alternatives**: redirigir a `detalle` después de crear — cambia el comportamiento aprobado de
  US 5.1; esperar la vista de US 5.2 — bloquea la historia; agregar búsqueda por identificador —
  pertenece a US 5.2.

## R2 — Confirmación en dos pasos sin borrador en sesión

- **Decision**: `GET /estudios/<pk>/pruebas/agregar/` muestra el formulario con el catálogo. El
  `POST` con `accion=revisar` valida y muestra la página de confirmación, con la prueba elegida en
  un campo oculto. El `POST` con `accion=confirmar` vuelve a validar el formulario y llama al
  servicio. "Cancelar" es un enlace al detalle.
- **Rationale**: a diferencia de US 5.1, la operación tiene un solo dato (la prueba) y no hay una
  configuración que pueda quedar desactualizada mientras se revisa. Un campo oculto revalidado en el
  servidor alcanza para cumplir FR-007/FR-008, sin el token firmado ni el borrador en sesión de
  `estudios/confirmaciones.py`.
- **Alternatives**: reutilizar `confirmaciones.preparar` — está atado a la creación de estudios
  (muestra, tipo, versión) y agrega vencimiento y recuperación que esta historia no necesita; un
  modal de Bootstrap — depende de JavaScript para confirmar y complica los tests.

## R3 — Servicio con bloqueo de fila del estudio

- **Decision**: `estudios/servicios.py` suma `GestionPruebasError(Exception)` (mensaje = texto para
  el empleado), su subclase `PruebaYaAsignada` y `agregar_prueba(estudio_pk, prueba_pk, usuario)`.
  Dentro de `transaction.atomic()`:
  1. `Estudio.objects.select_for_update().filter(pk=...).first()` (inexistente → error);
  2. revalida `admite_modificaciones` (R4);
  3. rechaza si la prueba no existe o ya está asignada (`PruebaYaAsignada`);
  4. crea la `PruebaEstudio`; un `IntegrityError` de `estudio_prueba_unica` se traduce también en
     `PruebaYaAsignada` como red de seguridad.
- **Rationale**: el bloqueo de la fila serializa las operaciones sobre un mismo estudio, lo que hace
  confiable la comprobación de "ya asignada" ante envíos simultáneos (edge cases, SC-002) y deja
  preparado el mismo esquema para la regla de "última prueba" de US 5.4. Las operaciones sobre
  estudios distintos no se bloquean entre sí, por eso no se usa el advisory lock global de la
  creación. Separar el servicio de la vista sigue el patrón de `crear_estudio`.
- **Alternatives**: confiar solo en la `UniqueConstraint` — funciona para duplicados, pero US 5.4
  necesita el bloqueo igual y conviene un único esquema; `pg_advisory_xact_lock` global —
  serializa estudios sin relación.

## R4 — Regla de estudio modificable en el modelo

- **Decision**: `Estudio.admite_modificaciones` (propiedad): `estado == EstadoEstudio.PENDIENTE_ANALISIS`.
  El detalle la usa para mostrar u ocultar las acciones; el servicio la vuelve a comprobar bajo el
  bloqueo.
- **Rationale**: la constitution (Principio IV) pide las reglas de negocio en el modelo o el
  formulario, no solo en el template. US 5.4 usa la misma propiedad (FR-003).
- **Alternatives**: comparar el estado en cada vista — repite la regla y la deja fuera del modelo.

## R5 — Catálogo disponible para agregar

- **Decision**: `AgregarPruebaForm(estudio)` con un `ModelChoiceField` cuyo queryset es
  `Prueba.objects.exclude(pk__in=estudio.pruebas_asignadas.values("prueba"))`, con etiqueta
  `código · nombre` (el `__str__` de `Prueba`). Si queda vacío, el formulario no se muestra y se
  informa "No hay pruebas disponibles para agregar". Un catálogo vacío no puede darse, porque el
  estudio se creó con al menos una prueba del catálogo.
- **Rationale**: cumple FR-004 y el escenario 2 de US 1 sin catálogo paralelo. Como el queryset se
  vuelve a evaluar en el `POST`, una prueba agregada por otro empleado en el medio falla la
  validación del formulario, y el servicio cubre la carrera restante (R3).
- **Alternatives**: mostrar todas las pruebas y rechazar las ya asignadas al confirmar — ofrece
  opciones que siempre fallan.

## R6 — Acceso y errores

- **Decision**: `LoginRequiredMiddleware` ya protege todas las vistas (FR-001). Estudio inexistente
  → 404 con `get_object_or_404`. Prueba inexistente → error del formulario. Estudio no modificable
  → redirección al detalle con `messages.error`. Reenvío ya aplicado → `messages.info`.
  `DatabaseError` → mensaje genérico de reintento, sin cambios.
- **Rationale**: mismo manejo de errores que US 5.1. Los reenvíos ya aplicados se informan como
  aviso y no como error, según el escenario 3 de US 2.
