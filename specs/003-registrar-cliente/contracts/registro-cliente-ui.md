# Contrato UI: Registro de cliente

**Feature**: `003-registrar-cliente` | **Plan**: [../plan.md](../plan.md)

Pantallas renderizadas en el servidor con templates de Django + Bootstrap 5.3, extendiendo
`base.html`. Todas requieren sesión iniciada de empleado (protegidas por `LoginRequiredMiddleware`,
FR-001) y todos los formularios incluyen `{% csrf_token %}`. Prefijo de URLs: `/clientes/`
(namespace `clientes`).

## Rutas

| Nombre de URL | Método | Ruta | Resultado |
|---|---|---|---|
| `clientes:registrar` | GET | `/clientes/registrar/` | Formulario vacío, o precargado si hay `cliente_pendiente` en la sesión. Sin sesión → **302** a `settings.LOGIN_URL` |
| `clientes:registrar` | POST | `/clientes/registrar/` | Válido → guarda datos normalizados en `session["cliente_pendiente"]` y **302** a `clientes:registrar_confirmar`. Inválido → **200** con errores junto a cada campo y datos válidos conservados |
| `clientes:registrar_confirmar` | GET | `/clientes/registrar/confirmar/` | Resumen de los datos para revisar antes de guardar. Sin `cliente_pendiente` en sesión → **302** a `clientes:registrar` |
| `clientes:registrar_confirmar` | POST `accion=confirmar` | `/clientes/registrar/confirmar/` | Crea el `Cliente` → **302** a `clientes:detalle` (`pk` del cliente creado) con mensaje de éxito `"Cliente registrado correctamente."` |
| `clientes:registrar_confirmar` | POST `accion=cancelar` | `/clientes/registrar/confirmar/` | Borra `cliente_pendiente` de la sesión sin crear el cliente → **302** a `clientes:registrar` con mensaje `"Registro de cliente cancelado."` |
| `clientes:detalle` | GET | `/clientes/<int:pk>/` | Ficha del cliente con todos los datos registrados (Escenario 2). Si `pk` no existe → **404** |

"Volver y editar" en la pantalla de confirmación es un link (GET) a `clientes:registrar`: como
`cliente_pendiente` sigue en la sesión, el formulario se muestra con todos los valores precargados.

## Acceso desde el inicio

- En `templates/inicio.html` se incluye un enlace/botón a `{% url 'clientes:registrar' %}` con el
  texto **"Registrar cliente"** (así no se modifica `templates/base.html`, que toca la US 1.2 en
  paralelo).

## Pantalla 1 — Formulario de alta (`clientes/registro_form.html`)

Título: **"Registrar cliente"** (`{% block title %}Registrar cliente · AquaLab{% endblock %}`).
Texto de ayuda: *"Ingresá el nombre o la razón social (al menos uno de los dos) y los datos de identificación y contacto."*

| Campo (`name`) | Etiqueta | Widget | Obligatorio |
|---|---|---|---|
| `nombre` | Nombre | texto (`max_length=200`) | Al menos uno entre `nombre` y `razon_social` |
| `razon_social` | Razón social | texto (`max_length=200`) | Al menos uno entre `nombre` y `razon_social` |
| `tipo_documento` | Tipo de documento | select (`DNI`, `CUIT`) | Sí |
| `numero_documento` | Número de documento | texto | Sí |
| `email` | Correo electrónico | email | Sí |
| `telefono` | Teléfono | texto (`max_length=30`) | No |
| `domicilio` | Domicilio | texto (`max_length=255`) | No |

Botón: **Continuar** (no guarda en la base; lleva a la instancia de revisión).

### Mensajes de error (junto al campo con `is-invalid` / `invalid-feedback`, o alerta general)

| Caso | Ubicación | Mensaje exacto |
|---|---|---|
| `tipo_documento`, `numero_documento` o `email` vacío | Campo correspondiente | `"Este campo es obligatorio."` (estándar de Django con `LANGUAGE_CODE="es-ar"`) |
| `nombre` y `razon_social` ambos vacíos | Error general del formulario (`non_field_errors`) | `"Debés ingresar al menos el nombre o la razón social del cliente."` |
| `tipo_documento == "DNI"` y el número normalizado no tiene 7 u 8 dígitos numéricos | `numero_documento` | `"El DNI debe tener 7 u 8 dígitos numéricos."` |
| `tipo_documento == "CUIT"` y el número normalizado no tiene 11 dígitos o su dígito verificador es inválido | `numero_documento` | `"El CUIT debe tener 11 dígitos y un dígito verificador válido."` |
| Ya existe un `Cliente` con el mismo `tipo_documento` y `numero_documento` normalizado | `numero_documento` | `"Ya existe un cliente registrado con este tipo y número de documento."` |
| `email` con formato inválido | `email` | `"Introduzca una dirección de email válida."` (estándar de Django con `LANGUAGE_CODE="es-ar"`) |
| `telefono` informado pero con formato inválido | `telefono` | `"Ingresá un número de teléfono válido (entre 7 y 15 dígitos)."` |

Reglas:
- Todos los valores ingresados por el empleado se conservan en el formulario cuando debe corregir
  algún error (FR-009).
- No se crea ningún registro `Cliente` desde esta pantalla.

## Pantalla 2 — Revisión y confirmación (`clientes/registro_confirmar.html`)

Título: **"Confirmar alta de cliente"** (`{% block title %}Confirmar cliente · AquaLab{% endblock %}`).

Texto de aviso:
> `"Revisá los datos del cliente antes de confirmar el registro."`

Muestra todos los datos normalizados que están en `session["cliente_pendiente"]`:
- **Nombre** (o `"—"` si no fue informado)
- **Razón social** (o `"—"` si no fue informada)
- **Tipo de documento** (`DNI` o `CUIT`)
- **Número de documento** (normalizado, solo dígitos)
- **Correo electrónico**
- **Teléfono** (o `"—"` si no fue informado)
- **Domicilio** (o `"—"` si no fue informado)

### Acciones en la pantalla de revisión

| Acción | Elemento | Efecto |
|---|---|---|
| Confirmar | form POST con `<input type="hidden" name="accion" value="confirmar">` y botón **Confirmar** | Crea el cliente. El botón se deshabilita en el `submit` para prevenir doble clic |
| Volver y editar | link GET a `{% url 'clientes:registrar' %}` (**Volver y editar**) | Vuelve al formulario con todos los datos precargados desde la sesión; no guarda nada |
| Cancelar | form POST con `<input type="hidden" name="accion" value="cancelar">` y botón **Cancelar** | Borra `cliente_pendiente` de la sesión sin crear el cliente y redirige a `clientes:registrar` |

### Comportamiento del POST en `clientes:registrar_confirmar`

| Situación | Respuesta |
|---|---|
| `accion=confirmar` con datos en sesión y documento disponible | Crea `Cliente(activo=True)`, borra `cliente_pendiente`, guarda `ultimo_cliente_creado_id = cliente.pk`, agrega mensaje `success` `"Cliente registrado correctamente."` y redirige (**302**) a `clientes:detalle` |
| `accion=confirmar` sin `cliente_pendiente` pero con `ultimo_cliente_creado_id` válido en sesión (confirmación repetida tras el éxito) | No crea nada; agrega mensaje `info` `"Cliente registrado correctamente."` y redirige (**302**) a `clientes:detalle` de ese cliente |
| `accion=confirmar` sin `cliente_pendiente` ni `ultimo_cliente_creado_id` | No crea nada; redirige (**302**) a `clientes:registrar` |
| `accion=confirmar` y el documento ya existe en la base (`IntegrityError`) | No crea un segundo cliente; agrega mensaje `error` `"Ya existe un cliente registrado con este tipo y número de documento."` y redirige (**302**) a `clientes:registrar` (conservando `cliente_pendiente` para editar) |
| `accion=confirmar` y ocurre otro `DatabaseError` | No crea el cliente; conserva `cliente_pendiente` y responde **200** en la pantalla de revisión con el mensaje `error` `"No se pudo completar el registro del cliente. Intentá nuevamente."` |
| `accion=cancelar` | Borra `cliente_pendiente` y `ultimo_cliente_creado_id` de la sesión; agrega mensaje `info` `"Registro de cliente cancelado."` y redirige (**302**) a `clientes:registrar` |
| Cualquier otro valor de `accion` | Redirige (**302**) a `clientes:registrar_confirmar` |

## Pantalla 3 — Ficha de consulta del cliente (`clientes/detalle.html`)

Título: **"Ficha del cliente"** (`{% block title %}Cliente · AquaLab{% endblock %}`).

Muestra los mensajes del framework de mensajes (heredados de `base.html`, p. ej.
`"Cliente registrado correctamente."`) y la tarjeta con todos los datos registrados del `Cliente`
(Escenario 2):
- **Nombre**
- **Razón social**
- **Tipo de documento** y **Número de documento**
- **Correo electrónico**
- **Teléfono**
- **Domicilio**
- **Estado**: `"Activo"` (`activo=True`)

Incluye un botón/enlace **"Registrar otro cliente"** hacia `{% url 'clientes:registrar' %}`.
