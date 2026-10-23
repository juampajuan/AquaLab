# Research: Editar cliente

**Feature**: `005-editar-cliente` | **Plan**: [plan.md](./plan.md)

## R1 — Reutilización del formulario de cliente y unicidad en edición

- **Decision**: reutilizar `RegistroClienteForm` en `clientes/forms.py` (exponiendo `EditarClienteForm`
  o instanciándolo con `instance=cliente`) y ajustar la consulta de unicidad en `clean()` para
  excluir `self.instance.pk` cuando `self.instance` ya existe en la base:
  `Cliente.objects.filter(tipo_documento=tipo, numero_documento=numero).exclude(pk=self.instance.pk).exists()`.
- **Rationale**: la edición valida exactamente los mismos campos (`CAMPOS_CLIENTE`: `nombre`,
  `razon_social`, `tipo_documento`, `numero_documento`, `email`, `telefono`, `domicilio`) y las
  mismas reglas de negocio que el alta (FR-004, FR-005, FR-006). Excluir `self.instance.pk` permite
  conservar el propio documento del cliente sin disparar un falso duplicado (Escenario 6) e impide
  asignar el documento de otro cliente registrado (FR-007, Escenario 5).
- **Alternatives**: crear un `Form` separado desde cero — duplica validaciones y normalizaciones;
  dejar la validación solo al `UniqueConstraint` en el paso de confirmación — posterga el error en
  lugar de mostrarlo junto al campo en el formulario (FR-008).

## R2 — Flujo de dos pasos con revisión y confirmación en sesión

- **Decision**: mantener el patrón de dos pasos renderizados en el servidor (como en `registrar` /
  `registrar_confirmar`), guardando los datos validados en `request.session[f"cliente_edicion_{pk}"]`
  (helper `clave_sesion_edicion(pk)`):
  - `GET /clientes/<int:pk>/editar/` (`clientes:editar`): si recibe `?volver=1` y existen datos en
    `session[f"cliente_edicion_{pk}"]`, precarga el formulario con ese borrador (FR-010); en
    cualquier otro `GET` (al entrar desde la ficha `clientes:detalle`), descarta cualquier borrador
    previo y precarga los datos vigentes del cliente desde la base (`instance=cliente`, FR-003).
  - `POST /clientes/<int:pk>/editar/`: si es válido, guarda `form.datos_para_sesion()` en
    `session[f"cliente_edicion_{pk}"]` y redirige a `clientes:editar_confirmar`; si es inválido,
    responde 200 con errores por campo conservando los valores ingresados (FR-008).
  - `GET/POST /clientes/<int:pk>/editar/confirmar/` (`clientes:editar_confirmar`): muestra el resumen
    de los cambios y procesa `accion=confirmar` o `accion=cancelar`.
- **Rationale**: cumple la sección Interfaz (UI) de la constitution (confirmación explícita antes de
  guardar), FR-009, FR-010 y FR-011. Usar una clave de sesión con el `pk` evita colisiones con el
  alta (`cliente_pendiente`) o entre ediciones de distintos clientes.
- **Alternatives**: guardar en el primer POST sin confirmación — incumple la constitution y FR-009;
  usar campos ocultos en la confirmación — obliga a revalidar todo el formulario y duplica lógica.

## R3 — Actualización transaccional, idempotencia y errores de base

- **Decision**: en `POST /clientes/<int:pk>/editar/confirmar/` con `accion=confirmar`:
  - `actualizar_cliente(cliente, datos)` asigna los campos de `CAMPOS_CLIENTE` y ejecuta
    `cliente.save()` dentro de `transaction.atomic()`.
  - Al completarse, borra `session[f"cliente_edicion_{pk}"]`, guarda
    `session["ultimo_cliente_editado_id"] = cliente.pk`, agrega el mensaje `success`
    `"Datos del cliente actualizados correctamente."` y redirige a `clientes:detalle` (`pk`).
  - Si llega un POST `accion=confirmar` repetido sin datos en sesión pero con
    `ultimo_cliente_editado_id == cliente.pk`, no vuelve a escribir en la base y redirige a
    `clientes:detalle` con mensaje `info` (Escenario 8).
  - Si ocurre `IntegrityError` (colisión concurrente de documento), conserva el borrador en sesión,
    informa `"Ya existe un cliente registrado con este tipo y número de documento."` y redirige a
    `/clientes/<pk>/editar/?volver=1`. Si ocurre otro `DatabaseError`, responde 200 en la pantalla de
    confirmación con `"No se pudo actualizar el cliente. Intentá nuevamente."`.
- **Rationale**: garantiza persistencia atómica, reflejo inmediato en consultas posteriores (FR-012)
  e idempotencia ante doble clic o reintentos (Escenario 8).
- **Alternatives**: tabla de tokens de idempotencia — innecesaria para el alcance del proyecto
  (Principio II, YAGNI).

## R4 — Clientes activos y protección de sesión

- **Decision**: todas las vistas de `clientes` quedan protegidas por `LoginRequiredMiddleware`
  (FR-001). Tanto `editar` como `editar_confirmar` buscan el cliente con
  `get_object_or_404(Cliente, pk=pk)` y, si `not cliente.activo`, limpian el borrador en sesión,
  emiten `messages.warning(request, "El cliente no está disponible.")` y redirigen a
  `clientes:buscar` (FR-013).
- **Rationale**: mantiene el mismo comportamiento que `clientes:detalle` (US 3.1) y respeta la baja
  lógica del Principio IV.
- **Alternatives**: devolver 404 para clientes inactivos — inconsistente con `clientes:detalle`.
