# Research: Agregar y quitar pruebas de un estudio

**Feature**: `009-gestionar-pruebas-estudio` | **Plan**: [plan.md](./plan.md)

No quedan `NEEDS CLARIFICATION`: las tres dudas de la spec se resolvieron en su sección
*Clarifications* (2026-10-27). Este documento fija las decisiones técnicas.

## R1 — Detalle mínimo del estudio como punto de entrada

- **Decision**: vista `estudios:detalle` en `GET /estudios/<pk>/` (template
  `estudios/detalle.html`) con identificador, N° PI, cliente y origen de la muestra, nombre histórico
  del tipo (`tipo_nombre_snapshot`), estado, autor, fecha de creación y la tabla de pruebas asignadas
  ordenadas por código, con las acciones "Agregar prueba" y "Quitar" según corresponda. El mensaje de
  éxito de US 5.1 (`estudios.views.exito`) pasa a incluir un enlace a este detalle mediante
  `format_html`; la redirección a `estudios:crear` no cambia. Un estudio inexistente responde 404.
- **Rationale**: es lo que decidió la spec (FR-002, Clarifications Q1). El enlace en el mensaje no
  cambia el flujo ni los tests de US 5.1. `format_html` escapa los datos y el `MessageEncoder` de
  Django conserva la marca de texto seguro al serializar el mensaje en la sesión. Usar el snapshot del
  nombre respeta FR-011: el estudio muestra el tipo tal como se confirmó.
- **Alternatives**: redirigir a `detalle` después de crear — cambia el comportamiento aprobado de
  US 5.1; esperar la vista de US 5.2 — bloquea la historia; agregar búsqueda por identificador —
  pertenece a US 5.2.

## R2 — Confirmación en dos pasos sin borrador en sesión

- **Decision**:
  - Agregar: `GET /estudios/<pk>/pruebas/agregar/` muestra el formulario con el catálogo. El
    `POST` con `accion=revisar` valida y muestra la página de confirmación, con la prueba elegida en
    un campo oculto. El `POST` con `accion=confirmar` vuelve a validar el formulario y llama al
    servicio. "Cancelar" es un enlace al detalle.
  - Quitar: `GET /estudios/<pk>/pruebas/<asignacion_pk>/quitar/` muestra la confirmación. El `POST`
    llama al servicio. "Cancelar" es un enlace al detalle.
- **Rationale**: a diferencia de US 5.1, la operación tiene un solo dato (la prueba o la
  asignación) y no hay una configuración que pueda quedar desactualizada mientras se revisa. Un campo
  oculto revalidado en el servidor alcanza para cumplir FR-008/FR-009, sin el token firmado ni el
  borrador en sesión de `estudios/confirmaciones.py`.
- **Alternatives**: reutilizar `confirmaciones.preparar` — está atado a la creación de estudios
  (muestra, tipo, versión) y agrega vencimiento y recuperación que esta historia no necesita; un
  modal de Bootstrap — depende de JavaScript para confirmar y complica los tests.

## R3 — Quitar identifica la asignación, no la prueba

- **Decision**: la URL de quitar usa el `pk` de `PruebaEstudio` y el servicio lo busca dentro del
  estudio (`estudio.pruebas_asignadas.filter(pk=...)`).
- **Rationale**: si la prueba se quita y después se vuelve a agregar, la nueva asignación tiene otro
  `pk`; un reenvío de la confirmación vieja no quita la asignación nueva y se informa "ya no forma
  parte del estudio" (FR-013). Filtrar por estudio impide quitar asignaciones de otro estudio
  cambiando la URL.
- **Alternatives**: usar el `pk` de `Prueba` — un reenvío tardío quitaría una prueba agregada otra
  vez a propósito.

## R4 — Servicios con bloqueo de fila del estudio

- **Decision**: `estudios/servicios.py` suma `agregar_prueba(estudio_pk, prueba_pk, usuario)` y
  `quitar_prueba(estudio_pk, asignacion_pk, usuario)`. Cada uno trabaja en `transaction.atomic()`:
  1. `Estudio.objects.select_for_update().get(pk=...)` (inexistente → `GestionPruebasError`);
  2. revalida que el estudio admite modificaciones (R5);
  3. agregar: rechaza si la prueba no existe o ya está asignada (`PruebaYaAsignada`) y crea la
     `PruebaEstudio`. Un `IntegrityError` de `estudio_prueba_unica` se traduce también en
     `PruebaYaAsignada` como red de seguridad;
  4. quitar: rechaza si la asignación ya no existe (`PruebaYaQuitada`), si es la última del estudio
     (`UltimaPrueba`, FR-014) o si `puede_quitarse()` es falso; si no, la borra. Un `ProtectedError`
     (futuras mediciones con `PROTECT`) se traduce en el mismo rechazo.
  Las excepciones heredan de `GestionPruebasError` y su mensaje es el texto que ve el empleado.
- **Rationale**: el bloqueo de la fila serializa todas las operaciones sobre un mismo estudio, lo que
  hace confiables la comprobación de "última prueba" y de "ya asignada" ante envíos simultáneos
  (edge cases, SC-002). Las operaciones sobre estudios distintos no se bloquean entre sí, por eso no
  se usa el advisory lock global de la creación. Separar el servicio de la vista sigue el patrón de
  `crear_estudio` y permite testearlo solo.
- **Alternatives**: confiar solo en la `UniqueConstraint` — no protege la regla de la última prueba
  (dos quitas simultáneas de pruebas distintas dejarían el estudio vacío); `pg_advisory_xact_lock`
  global — serializa estudios sin relación.

## R5 — Reglas de negocio en el modelo

- **Decision**:
  - `Estudio.admite_modificaciones` (propiedad): `estado == EstadoEstudio.PENDIENTE_ANALISIS`.
  - `PruebaEstudio.puede_quitarse()`: hoy devuelve `True` (no existen mediciones ni resultados).
    Su docstring indica que US 6.1 y siguientes deben devolver `False` cuando la asignación tenga
    mediciones o resultados, y que esas tablas deben apuntar a `PruebaEstudio` con `PROTECT`.
  - El detalle usa ambas para mostrar u ocultar las acciones; el servicio las vuelve a comprobar
    bajo el bloqueo.
- **Rationale**: la constitution (Principio IV) pide las reglas de negocio en el modelo o el
  formulario, no solo en el template. Dejar el método ahora fija el punto de extensión de FR-007 sin
  inventar modelos de mediciones (YAGNI). Se agrega una nota en `CLAUDE.md` para US 6.1.
- **Alternatives**: un campo booleano `tiene_mediciones` — duplica un dato que se podrá calcular;
  crear ya el modelo `Medicion` — fuera del alcance.

## R6 — Catálogo disponible para agregar

- **Decision**: `AgregarPruebaForm(estudio)` con un `ModelChoiceField` cuyo queryset es
  `Prueba.objects.exclude(pk__in=estudio.pruebas_asignadas.values("prueba"))`, con etiqueta
  `código · nombre` (el `__str__` de `Prueba`). Si queda vacío, el formulario no se muestra y se
  informa "No hay pruebas disponibles para agregar". Un catálogo vacío no puede darse, porque el
  estudio conserva al menos una prueba (FR-014) y esa prueba está en el catálogo.
- **Rationale**: cumple FR-004 y el escenario 2 de US 1 sin catálogo paralelo. Como el queryset se
  vuelve a evaluar en el `POST`, una prueba agregada por otro empleado en el medio falla la
  validación del formulario, y el servicio cubre la carrera restante (R4).
- **Alternatives**: mostrar todas las pruebas y rechazar las ya asignadas al confirmar — ofrece
  opciones que siempre fallan.

## R7 — Borrado real de la asignación

- **Decision**: quitar hace `delete()` de la `PruebaEstudio`. No hay migración.
- **Rationale**: es la decisión de la spec (Clarifications Q2, FR-010). La asignación sin mediciones
  no tiene historial, así que el Principio IV no exige conservarla. Al no existir la fila, las
  historias de mediciones e informe no la ven, sin filtros adicionales.
- **Alternatives**: marca lógica de quitada — descartada en la spec.

## R8 — Acceso y errores

- **Decision**: `LoginRequiredMiddleware` ya protege todas las vistas (FR-001). Estudio inexistente
  → 404 con `get_object_or_404`. Asignación o prueba inexistente, estudio no modificable o regla
  violada → redirección al detalle con `messages.error` (o `messages.info` para los reenvíos ya
  aplicados). `DatabaseError` → mensaje genérico de reintento, sin cambios.
- **Rationale**: mismo manejo de errores que US 5.1. Los reenvíos ya aplicados se informan como
  aviso y no como error, según el escenario 4 de US 3.
