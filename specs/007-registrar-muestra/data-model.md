# Data Model: Registrar muestra

**Feature**: `007-registrar-muestra` | **Plan**: [plan.md](./plan.md)

App nueva `muestras`. `Cliente` (app `clientes`) y `Usuario` (app `usuarios`) no cambian.

```text
Cliente 1 ──< Origen 1 ──< Muestra >── 1 Usuario (registrada_por)
   1 ─────────────────────────< Muestra
```

## Origen (`muestras.Origen`)

Fuente de agua de un cliente (ej. "Pozo N°2"), reutilizable en sus próximas muestras.

| Campo | Tipo | Reglas |
|---|---|---|
| `cliente` | FK → `clientes.Cliente` | Obligatorio. `on_delete=PROTECT`, `related_name="origenes"` |
| `nombre` | `CharField(150)` | Obligatorio; se guarda sin espacios laterales |
| `fecha_alta` | `DateTimeField(auto_now_add)` | Automático |

- **Unicidad**: `UniqueConstraint(Lower("nombre"), F("cliente"), name="origen_nombre_unico_por_cliente")`
  — el mismo nombre no se repite en un cliente sin distinguir mayúsculas (FR-006). Distintos
  clientes sí pueden tener orígenes con el mismo nombre.
- **Orden**: `("nombre",)`. `__str__` → `nombre`.
- Se crea solo al confirmar el registro de una muestra (FR-005, FR-018). Editar o desactivar orígenes
  queda fuera de alcance.

## Muestra (`muestras.Muestra`)

| Campo | Tipo | Reglas |
|---|---|---|
| `numero_pi` | `PositiveIntegerField` | Único, `editable=False`. Último + 1; la primera es 200001 (FR-012, FR-013) |
| `nombre` | `CharField(100)` | Opcional en el formulario; vacío → `"Muestra N"` al confirmar, N = muestras del cliente + 1 (FR-011) |
| `cliente` | FK → `clientes.Cliente` | Obligatorio, activo al registrar. `PROTECT`, `related_name="muestras"` |
| `origen` | FK → `Origen` | Obligatorio; debe pertenecer a `cliente`. `PROTECT`, `related_name="muestras"` |
| `fecha_muestreo` | `DateField` | Obligatorio; por defecto hoy; ≤ hoy; ≤ `fecha_ingreso` (FR-008, FR-009) |
| `fecha_ingreso` | `DateField` | Obligatorio; por defecto hoy; ≤ hoy |
| `sitio_extraccion` | `CharField(200)` | Obligatorio; texto libre, sin espacios laterales (FR-007a) |
| `tipo_vertido` | `CharField(10, choices=TipoVertido)` | Obligatorio; por defecto `agua` (FR-010) |
| `responsable_muestreo` | `CharField(150, blank=True)` | Opcional; texto libre (FR-011) |
| `estado` | `CharField(20, choices=EstadoMuestra)` | `default="ingresada"`, `editable=False` (FR-015) |
| `registrada_por` | FK → `settings.AUTH_USER_MODEL` | `PROTECT`, `editable=False`, `related_name="muestras_registradas"` (FR-014) |
| `fecha_registro` | `DateTimeField(auto_now_add)` | Automático (FR-014) |

**Choices**

- `TipoVertido`: `AGUA = "agua", "Agua"`, `CLOACAL = "cloacal", "Cloacal"`, `CANAL = "canal", "Canal"`.
- `EstadoMuestra`: `INGRESADA = "ingresada", "Ingresada"` (los demás estados llegan con otras US).

**Constraints de base**

- `numero_pi` `unique=True`.
- `CheckConstraint(numero_pi__gte=200001, name="muestra_numero_pi_desde_200001")`.
- `CheckConstraint(fecha_muestreo__lte=F("fecha_ingreso"), name="muestra_muestreo_no_posterior_a_ingreso")`.

**Validaciones en `Muestra.clean()`** (Principio IV: reglas en el modelo/formulario)

- `origen.cliente_id == cliente_id` → si no: error en `origen`, "El origen no pertenece al cliente
  seleccionado."
- `fecha_muestreo <= fecha_ingreso` → si no: error en `fecha_muestreo`.

**Orden**: `("-numero_pi",)`. `__str__` → `f"N° PI {numero_pi} – {nombre}"`.

## Estado de la muestra

```text
(alta confirmada) ──► Ingresada
```

Esta historia solo crea muestras en "Ingresada"; no hay transiciones.

## Borrador en sesión (`session["muestra_pendiente"]`)

Datos ya validados y normalizados entre el formulario y la confirmación (no se guardan en la base
hasta confirmar):

```python
{
    "cliente": 12,                 # pk
    "origen": 5,                   # pk, o None si es un origen nuevo
    "origen_nuevo": "",            # nombre del origen nuevo, o "" si se eligió uno existente
    "fecha_muestreo": "2026-10-27",
    "fecha_ingreso": "2026-10-27",
    "sitio_extraccion": "Canilla de salida del tanque",
    "tipo_vertido": "agua",
    "nombre": "",                  # vacío → "Muestra N" al confirmar
    "responsable_muestreo": "",
}
```

Otras claves: `session["ultima_muestra_pi"]` (N° PI recién registrado, para la confirmación
repetida).

## Servicio `registrar_muestra(datos, usuario) -> Muestra`

En `transaction.atomic()`:

1. `pg_advisory_xact_lock` con clave fija (serializa registros, R2).
2. Revalida: cliente activo; si `origen`, que pertenezca al cliente. Si falla → `MuestraNoDisponible`.
3. Si `origen_nuevo`: busca `Origen` del cliente con `nombre__iexact`; si no existe, lo crea.
4. `numero_pi = (Max("numero_pi") or 200000) + 1`; si `nombre` está vacío,
   `nombre = f"Muestra {cliente.muestras.count() + 1}"`.
5. Crea la `Muestra` con `registrada_por=usuario` y `estado="ingresada"`.

Cualquier excepción revierte todo: no queda origen nuevo ni N° PI consumido (FR-018, SC-005).
