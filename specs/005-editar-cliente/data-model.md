# Data Model: Editar cliente

**Feature**: `005-editar-cliente` | **Plan**: [plan.md](./plan.md)

La feature actualiza registros existentes de `clientes.Cliente` (creado en la US 2.1).

## Entidad actualizada: `Cliente` (`clientes.Cliente`)

| Campo | Tipo Django | Reglas en la edición |
|---|---|---|
| `id` | `BigAutoField` (PK) | Identifica al cliente en la URL (`/clientes/<int:pk>/editar/`); no se modifica |
| `nombre` | `CharField(max_length=200, blank=True)` | `.strip()`. Obligatorio si `razon_social` está vacío (FR-004, FR-005) |
| `razon_social` | `CharField(max_length=200, blank=True)` | `.strip()`. Obligatorio si `nombre` está vacío (FR-004, FR-005) |
| `tipo_documento` | `CharField(max_length=4, choices=TipoDocumento.choices)` | Obligatorio (`"DNI"` o `"CUIT"`, FR-004, FR-005) |
| `numero_documento` | `CharField(max_length=11)` | Obligatorio. Normalizado con `normalizar_numero_documento` (solo dígitos) y validado según `tipo_documento` (`validar_documento`). Único junto con `tipo_documento` excluyendo `cliente.pk` (FR-006, FR-007) |
| `email` | `EmailField(max_length=254)` | Obligatorio. Normalizado con `.strip().lower()` y formato válido (FR-005, FR-006) |
| `telefono` | `CharField(max_length=30, blank=True)` | Opcional (`blank=True`). `.strip()`. Si se informa, validado con `validar_telefono` (7 a 15 dígitos, FR-005, FR-006) |
| `domicilio` | `CharField(max_length=255, blank=True)` | Opcional (`blank=True`). `.strip()` (FR-004, FR-005) |
| `activo` | `BooleanField(default=True)` | Solo se editan clientes con `activo=True` (FR-013) |
| `fecha_alta` | `DateTimeField(auto_now_add=True)` | No se modifica |

## Validaciones en `EditarClienteForm` / `RegistroClienteForm`

| Regla | Mensaje de error | Requisito |
|---|---|---|
| `nombre` y `razon_social` ambos vacíos | `"Debés ingresar al menos el nombre o la razón social del cliente."` | FR-005, Esc. 3 |
| `tipo_documento`, `numero_documento` o `email` vacío | `"Este campo es obligatorio."` | FR-005, Esc. 3 |
| DNI que no tiene 7 u 8 dígitos numéricos | `"El DNI debe tener 7 u 8 dígitos numéricos."` | FR-006, Esc. 4 |
| CUIT sin 11 dígitos o con dígito verificador inválido | `"El CUIT debe tener 11 dígitos y un dígito verificador válido."` | FR-006, Esc. 4 |
| `(tipo_documento, numero_documento)` ya usado por otro `Cliente` (`pk != cliente.pk`) | `"Ya existe un cliente registrado con este tipo y número de documento."` | FR-007, Esc. 5 y 6 |
| `email` con formato inválido | `"Introduzca una dirección de email válida."` | FR-006, Esc. 4 |
| `telefono` no vacío con formato inválido | `"Ingresá un número de teléfono válido (entre 7 y 15 dígitos)."` | FR-006, Esc. 4 |

## Datos transitorios en sesión

Clave: `request.session[f"cliente_edicion_{cliente.pk}"]`

Contiene el diccionario normalizado de `CAMPOS_CLIENTE` (`nombre`, `razon_social`, `tipo_documento`,
`numero_documento`, `email`, `telefono`, `domicilio`) entre el envío válido del formulario y la
confirmación o cancelación. Al confirmar con éxito se guarda
`request.session["ultimo_cliente_editado_id"] = cliente.pk`.
