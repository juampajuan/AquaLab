# Contrato UI: Edición de cliente

**Feature**: `005-editar-cliente` | **Plan**: [../plan.md](../plan.md)

Pantallas renderizadas en el servidor con templates de Django + Bootstrap 5.3, extendiendo
`base.html`. Todas requieren sesión iniciada (`LoginRequiredMiddleware`, FR-001) y todos los
formularios POST incluyen `{% csrf_token %}`. Namespace: `clientes` (`/clientes/`).

## Rutas

| Nombre de URL | Método | Ruta | Resultado |
|---|---|---|---|
| `clientes:detalle` | GET | `/clientes/<int:pk>/` | Ficha del cliente con todos sus datos vigentes y botón **"Editar cliente"** hacia `clientes:editar` (FR-002) |
| `clientes:editar` | GET | `/clientes/<int:pk>/editar/` | Con `?volver=1` y datos en `session[f"cliente_edicion_{pk}"]` → precarga el borrador en sesión (FR-010). Sin `?volver=1` → limpia borrador previo de ese `pk` y precarga los datos vigentes del `Cliente` (FR-003). Si `pk` no existe → **404**. Si `not cliente.activo` → **302** a `clientes:buscar` con warning `"El cliente no está disponible."` |
| `clientes:editar` | POST | `/clientes/<int:pk>/editar/` | Válido → guarda datos normalizados en `session[f"cliente_edicion_{pk}"]`, limpia `ultimo_cliente_editado_id` y **302** a `clientes:editar_confirmar`. Inválido → **200** con errores junto a cada campo y valores ingresados conservados (FR-008) |
| `clientes:editar_confirmar` | GET | `/clientes/<int:pk>/editar/confirmar/` | Resumen de los datos modificados para revisar antes de guardar. Sin datos en `session[f"cliente_edicion_{pk}"]` → **302** a `clientes:editar`. Si `pk` no existe → **404**. Si `not cliente.activo` → **302** a `clientes:buscar` con warning `"El cliente no está disponible."` |
| `clientes:editar_confirmar` | POST `accion=confirmar` | `/clientes/<int:pk>/editar/confirmar/` | Actualiza el `Cliente` → **302** a `clientes:detalle` (`pk`) con mensaje `success` `"Datos del cliente actualizados correctamente."` |
| `clientes:editar_confirmar` | POST `accion=cancelar` | `/clientes/<int:pk>/editar/confirmar/` | Borra `session[f"cliente_edicion_{pk}"]` sin modificar el cliente → **302** a `clientes:detalle` (`pk`) con mensaje `info` `"Edición de cliente cancelada."` |

## Acceso desde la ficha del cliente (`clientes/detalle.html`)

En `clientes/templates/clientes/detalle.html` se agrega el botón/enlace **"Editar cliente"** hacia
`{% url 'clientes:editar' cliente.pk %}`.

## Pantalla 1 — Formulario de edición (`clientes/editar_form.html`)

Título: **"Editar cliente"** (`{% block title %}Editar cliente · AquaLab{% endblock %}`).
Texto de ayuda: *"Modificá los datos del cliente y continuá para revisar los cambios antes de guardarlos."*

| Campo (`name`) | Etiqueta | Widget | Obligatorio |
|---|---|---|---|
| `nombre` | Nombre | texto (`max_length=200`) | Al menos uno entre `nombre` y `razon_social` |
| `razon_social` | Razón social | texto (`max_length=200`) | Al menos uno entre `nombre` y `razon_social` |
| `tipo_documento` | Tipo de documento | select (`DNI`, `CUIT`) | Sí |
| `numero_documento` | Número de documento | texto | Sí |
| `email` | Correo electrónico | email | Sí |
| `telefono` | Teléfono | texto (`max_length=30`) | No |
| `domicilio` | Domicilio | texto (`max_length=255`) | No |

Acciones:
- Botón submit primario: **Continuar** (valida y lleva a la pantalla de revisión).
- Enlace secundario: **Cancelar** (`{% url 'clientes:detalle' cliente.pk %}`), que vuelve a la ficha sin guardar cambios.

## Pantalla 2 — Revisión y confirmación (`clientes/editar_confirmar.html`)

Título: **"Confirmar edición de cliente"** (`{% block title %}Confirmar edición · AquaLab{% endblock %}`).
Texto de aviso: `"Revisá los datos modificados del cliente antes de confirmar los cambios."`

Muestra todos los datos normalizados en `session[f"cliente_edicion_{cliente.pk}"]` (Nombre, Razón
social, Tipo de documento, Número de documento, Correo electrónico, Teléfono y Domicilio, usando
`"—"` cuando un campo opcional está vacío).

### Acciones en la pantalla de revisión

| Acción | Elemento | Efecto |
|---|---|---|
| Confirmar | form POST con `<input type="hidden" name="accion" value="confirmar">` y botón **Confirmar** | Actualiza el cliente. El botón se deshabilita en el `submit` |
| Volver y editar | link GET a `{% url 'clientes:editar' cliente.pk %}?volver=1` (**Volver y editar**) | Vuelve al formulario con los datos modificados precargados desde la sesión |
| Cancelar | form POST con `<input type="hidden" name="accion" value="cancelar">` y botón **Cancelar** | Borra `session[f"cliente_edicion_{pk}"]` y redirige a `clientes:detalle` (`pk`) con `"Edición de cliente cancelada."` |

### Comportamiento del POST en `clientes:editar_confirmar`

| Situación | Respuesta |
|---|---|
| `accion=confirmar` con datos en sesión y documento disponible | Actualiza `Cliente`, borra `session[f"cliente_edicion_{pk}"]`, guarda `ultimo_cliente_editado_id = cliente.pk`, agrega mensaje `success` `"Datos del cliente actualizados correctamente."` y redirige (**302**) a `clientes:detalle` |
| `accion=confirmar` sin datos en sesión pero con `ultimo_cliente_editado_id == cliente.pk` | No modifica la base; agrega mensaje `info` `"Datos del cliente actualizados correctamente."` y redirige (**302**) a `clientes:detalle` |
| `accion=confirmar` sin datos en sesión ni `ultimo_cliente_editado_id == cliente.pk` | Redirige (**302**) a `clientes:editar` |
| `accion=confirmar` y el documento colisiona con otro cliente (`IntegrityError`) | Conserva datos en sesión, agrega mensaje `error` `"Ya existe un cliente registrado con este tipo y número de documento."` y redirige (**302**) a `/clientes/<pk>/editar/?volver=1` |
| `accion=confirmar` y ocurre otro `DatabaseError` | Conserva datos en sesión y responde **200** en la pantalla de confirmación con el mensaje `error` `"No se pudo actualizar el cliente. Intentá nuevamente."` |
| `accion=cancelar` | Borra `session[f"cliente_edicion_{pk}"]` y `ultimo_cliente_editado_id`, agrega mensaje `info` `"Edición de cliente cancelada."` y redirige (**302**) a `clientes:detalle` |
| Cualquier otro valor de `accion` | Redirige (**302**) a `clientes:editar_confirmar` |
