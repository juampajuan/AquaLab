# Data Model: Registrar cliente

**Feature**: `003-registrar-cliente` | **Fecha**: 2026-10-19 | **Plan**: [plan.md](./plan.md)

## Entidad: `Cliente` (app `clientes`)

Modelo principal del módulo de clientes (`clientes.Cliente`). Hereda de `django.db.models.Model`.
Cubre las tres entidades clave de la spec (**Cliente**, **Identificación fiscal o personal** y
**Datos de contacto**) en una única tabla (`clientes_cliente`), ya que la identificación y los
datos de contacto tienen relación 1:1 con el cliente.

### Enumeración `TipoDocumento` (`models.TextChoices`)

| Constante | Valor guardado | Etiqueta |
|---|---|---|
| `DNI` | `"DNI"` | `"DNI"` |
| `CUIT` | `"CUIT"` | `"CUIT"` |

### Campos

| Campo | Tipo Django | Reglas |
|---|---|---|
| `id` | `BigAutoField` | PK (`DEFAULT_AUTO_FIELD`) |
| `nombre` | `CharField(max_length=200, blank=True)` | Opcional individualmente, pero obligatorio si `razon_social` está vacío (FR-002, FR-003). Sin espacios laterales (`strip()`). `verbose_name="nombre"` |
| `razon_social` | `CharField(max_length=200, blank=True)` | Opcional individualmente, pero obligatorio si `nombre` está vacío (FR-002, FR-003). Sin espacios laterales (`strip()`). `verbose_name="razón social"` |
| `tipo_documento` | `CharField(max_length=4, choices=TipoDocumento.choices)` | Obligatorio (`blank=False`). Valores permitidos: `"DNI"`, `"CUIT"` (FR-004). `verbose_name="tipo de documento"` |
| `numero_documento` | `CharField(max_length=11)` | Obligatorio (`blank=False`). Se guarda normalizado: solo dígitos ASCII, sin espacios, puntos ni guiones (FR-007, FR-016). `verbose_name="número de documento"` |
| `email` | `EmailField(max_length=254)` | Obligatorio (`blank=False`). Se guarda normalizado: `strip().lower()` (FR-005, FR-006). `verbose_name="correo electrónico"` |
| `telefono` | `CharField(max_length=30, blank=True)` | Opcional (`blank=True`). Sin espacios laterales. Si se informa, debe cumplir formato válido de teléfono (FR-005, FR-006). `verbose_name="teléfono"` |
| `domicilio` | `CharField(max_length=255, blank=True)` | Opcional (`blank=True`). Sin espacios laterales (FR-005). `verbose_name="domicilio"` |
| `activo` | `BooleanField(default=True)` | `True` al registrarse; permite asociar el cliente a muestras y desactivarlo en el futuro sin borrar historial (FR-014, Principio IV). `verbose_name="activo"` |
| `fecha_alta` | `DateTimeField(auto_now_add=True)` | Fecha y hora de creación del registro. `verbose_name="fecha de alta"` |

### Configuración del modelo (`Meta` y métodos)

- `Meta.verbose_name = "cliente"`, `Meta.verbose_name_plural = "clientes"`
- `Meta.ordering = ("razon_social", "nombre", "id")`
- `Meta.constraints`:
  1. `UniqueConstraint(fields=["tipo_documento", "numero_documento"], name="cliente_documento_unico", violation_error_message="Ya existe un cliente registrado con este tipo y número de documento.")`
  2. `CheckConstraint(condition=~Q(nombre="", razon_social=""), name="cliente_nombre_o_razon_social_obligatorio")`
- `__str__`: devuelve `f"{self.nombre_completo} ({self.tipo_documento} {self.numero_documento})"`,
  donde `nombre_completo` (propiedad) retorna `razon_social` si solo tiene razón social, `nombre`
  si solo tiene nombre, o `f"{razon_social} ({nombre})"` cuando ambos están cargados.
- `clean()`:
  - Normaliza `nombre`, `razon_social`, `telefono` y `domicilio` con `.strip()`, `email` con
    `.strip().lower()` y `numero_documento` con `normalizar_numero_documento()`.
  - Verifica que al menos uno entre `nombre` y `razon_social` no sea vacío (`ValidationError` general:
    `"Debés ingresar al menos el nombre o la razón social del cliente."`).
  - Valida `numero_documento` según `tipo_documento` (`validar_documento(tipo_documento, numero_documento)`).
  - Si `telefono` no está vacío, ejecuta `validar_telefono(telefono)`.

### Funciones de normalización y validación (`clientes/validators.py` o `clientes/models.py`)

| Función | Comportamiento | Requisito |
|---|---|---|
| `normalizar_numero_documento(valor)` | Elimina espacios (`\s`), puntos (`.`) y guiones (`-`): `re.sub(r"[\s.\-]", "", valor or "")`. Lo usan el formulario y `Cliente.clean()` | FR-007, Edge case 2 |
| `es_cuit_valido(cuit)` | Verifica que `cuit` tenga 11 dígitos numéricos y que el dígito 11 coincida con el cálculo módulo 11 con pesos `[5, 4, 3, 2, 7, 6, 5, 4, 3, 2]` (`resto = suma % 11`; `dv = 0` si `resto == 0`, `9` si `resto == 1`, `11 - resto` en otro caso) | FR-016, Escenario 8 |
| `validar_documento(tipo, numero)` | Si `tipo == "DNI"`: exige `numero.isdigit()` y `len(numero) in (7, 8)`; si falla, `ValidationError({"numero_documento": "El DNI debe tener 7 u 8 dígitos numéricos."})`. Si `tipo == "CUIT"`: exige `es_cuit_valido(numero)`; si falla, `ValidationError({"numero_documento": "El CUIT debe tener 11 dígitos y un dígito verificador válido."})` | FR-004, FR-016, Escenario 8 |
| `validar_telefono(valor)` | Si `valor` no es vacío: exige `re.fullmatch(r"[+\d\s\-()]+", valor)` y que `7 <= sum(c.isdigit() for c in valor) <= 15`. Si falla, `ValidationError("Ingresá un número de teléfono válido (entre 7 y 15 dígitos).")` | FR-006, Escenario 5 |

### Resumen de validaciones por requisito

| Regla | Dónde se valida | Requisito |
|---|---|---|
| Al menos uno entre `nombre` y `razon_social` | `RegistroClienteForm.clean()` + `Cliente.clean()` + `CheckConstraint` | FR-002, FR-003, Escenario 3, Edge case 1 |
| `tipo_documento`, `numero_documento` y `email` obligatorios | Campos del modelo (`blank=False`) + formulario | FR-004, FR-005, Escenario 3 |
| Formato de DNI (7 u 8 dígitos) y CUIT (11 dígitos + dígito verificador) | `RegistroClienteForm.clean()` + `Cliente.clean()` | FR-016, Escenario 8 |
| Unicidad de `(tipo_documento, numero_documento)` sin separadores | Normalización + `RegistroClienteForm.clean()` + `UniqueConstraint` en PostgreSQL | FR-007, Escenario 4 |
| Formato de `email` | `EmailField` de Django | FR-006, Escenario 5 |
| Formato de `telefono` (cuando se informa) | `RegistroClienteForm.clean_telefono()` + `Cliente.clean()` | FR-006, Escenario 5 |
| Eliminación de espacios laterales | `CharField(strip=True)` en formulario + `.strip()` en `Cliente.clean()` | Edge case 3 |

## Estados del cliente

```text
                   confirmar alta
    (no existe) ──────────────────▶ ACTIVO
                                    activo = True
                                    └─ disponible de inmediato para asociar
                                       a muestras (FR-014 / US 4.1)
```

- La desactivación (`activo = False`) y la edición de datos pertenecen a historias posteriores
  (FR-015).

## Datos transitorios: alta en revisión (sesión)

Vive en `request.session["cliente_pendiente"]` entre el paso del formulario y la confirmación
(ver [research.md R6](./research.md)):

| Clave | Contenido |
|---|---|
| `nombre` | Nombre sin espacios laterales (`""` si no se ingresó) |
| `razon_social` | Razón social sin espacios laterales (`""` si no se ingresó) |
| `tipo_documento` | `"DNI"` o `"CUIT"` |
| `numero_documento` | Número normalizado (solo dígitos) |
| `email` | Correo normalizado (`strip().lower()`) |
| `telefono` | Teléfono sin espacios laterales (`""` si no se ingresó) |
| `domicilio` | Domicilio sin espacios laterales (`""` si no se ingresó) |

- Se crea o reemplaza cuando el empleado envía un formulario válido en `clientes:registrar`.
- Se elimina al confirmar el alta o al cancelar en `clientes:registrar_confirmar`.
- Además, al confirmar con éxito se guarda `request.session["ultimo_cliente_creado_id"] = cliente.pk`
  para resolver confirmaciones repetidas de forma idempotente (ver [research.md R7](./research.md)).

## Contrato hacia otras features

- **US 3.1 / US 3.2 (Buscar y editar cliente)** y **US 3.3 (Historial del cliente)**: usan el modelo
  `clientes.Cliente` y su vista de detalle `clientes:detalle`.
- **US 4.1 (Registrar muestra)**: asocia cada `Muestra` a un `Cliente` activo
  (`Cliente.objects.filter(activo=True)`).
