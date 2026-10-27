# Contrato de interfaz: Registrar muestra

**Feature**: `007-registrar-muestra` | **Plan**: [plan.md](./plan.md)

Todas las rutas requieren sesión iniciada (sin sesión → 302 al login, FR-001) y llevan CSRF en los
POST. Los mensajes se muestran con el framework `messages` en `base.html`.

## `GET /muestras/registrar/` — `muestras:registrar`

- Sin `?volver=1`: descarta `session["muestra_pendiente"]` y muestra el formulario vacío.
- Con `?volver=1` y borrador en sesión: precarga el formulario con el borrador.
- **Respuesta**: 200, template `muestras/registro_form.html`.

### Campos del formulario (en este orden)

| Campo (`name`) | Control | Obligatorio | Valor inicial |
|---|---|---|---|
| `buscar_cliente` | texto (no se envía al servidor, solo filtra) | — | vacío |
| `cliente` | `<select>` con clientes activos; etiqueta `nombre_completo · TIPO número` | Sí | ninguno |
| — | ficha del cliente elegido: razón social (o nombre), tipo y número de documento, correo | — | la renderiza el servidor si hay cliente elegido; si no, oculta hasta elegir |
| `origen` | `<select>` con los orígenes del cliente elegido | Uno de los dos | ninguno |
| `origen_nuevo` | texto, visible al pulsar "Dar de alta un origen nuevo" | Uno de los dos | vacío |
| `fecha_muestreo` | `<input type="date">` | Sí | hoy |
| `fecha_ingreso` | `<input type="date">` | Sí | hoy |
| `sitio_extraccion` | texto | Sí | vacío |
| `tipo_vertido` | `<select>`: Agua, Cloacal, Canal | Sí | Agua |
| `nombre` | texto; ayuda: "Si lo dejás vacío se usa «Muestra 1»." | No | vacío |
| `responsable_muestreo` | texto | No | vacío |

Datos para el script (con `json_script`, id `clientes-muestra`): por cada cliente activo
`{"id", "nombre_completo", "razon_social_o_nombre", "tipo_documento", "numero_documento", "email",
"origenes": [{"id", "nombre"}]}`.

Comportamiento del script `muestras/registro_muestra.js` (sin él, el formulario igual funciona):

- Al escribir en `buscar_cliente`, oculta las opciones de `cliente` cuyo texto no coincide
  (sin distinguir mayúsculas ni tildes; los dígitos se comparan sin puntos, guiones ni espacios).
- Al cambiar `cliente`: muestra su ficha, reemplaza las opciones de `origen` por las suyas y vacía
  `origen`. Si el cliente no tiene orígenes, abre directamente `origen_nuevo`.
- Al escribir en `origen_nuevo`, vacía `origen`; al elegir un `origen`, vacía `origen_nuevo`.

## `POST /muestras/registrar/`

| Caso | Respuesta |
|---|---|
| Válido | Guarda el borrador normalizado en sesión y responde 302 a `muestras:registrar_confirmar` |
| Inválido | 200 con el formulario, los valores ingresados y el error junto a cada campo (`is-invalid` / `invalid-feedback`), con la ficha del cliente elegido y solo sus orígenes en `origen` |

### Mensajes de validación

| Situación | Campo | Mensaje |
|---|---|---|
| Falta cliente, fecha, sitio o tipo de vertido | el campo | "Este campo es obligatorio." |
| Cliente inactivo o inexistente | `cliente` | Mensaje de opción inválida de Django |
| Ni origen ni origen nuevo | `origen` | "Elegí un origen del cliente o ingresá uno nuevo." |
| Origen y origen nuevo a la vez | `origen_nuevo` | "Elegí un origen existente o ingresá uno nuevo, no ambos." |
| Origen de otro cliente | `origen` | Mensaje de opción inválida de Django |
| Fecha posterior a hoy | la fecha | "La fecha no puede ser posterior a hoy." |
| Muestreo posterior al ingreso | `fecha_muestreo` | "La fecha de muestreo no puede ser posterior a la fecha de ingreso." |
| Campo de texto obligatorio solo con espacios | el campo | "Este campo es obligatorio." |

## `GET /muestras/registrar/confirmar/` — `muestras:registrar_confirmar`

- Sin borrador → 302 a `muestras:registrar`.
- Con borrador → 200, template `muestras/registro_confirmar.html`, con el aviso "Revisá los datos de
  la muestra antes de confirmar el registro." y el resumen: cliente (nombre completo, documento,
  correo), origen (con la marca "(nuevo)" si corresponde), fecha de muestreo, fecha de ingreso,
  sitio de extracción, tipo de vertido, nombre de la muestra, responsable del muestreo ("—" si está
  vacío). Nota: "El N° PI se asigna al confirmar."
- Botones: [Confirmar] (`accion=confirmar`, se deshabilita al enviar), [Volver y editar]
  (`/muestras/registrar/?volver=1`), [Cancelar] (`accion=cancelar`).

## `POST /muestras/registrar/confirmar/`

| `accion` / estado | Efecto | Respuesta |
|---|---|---|
| `cancelar` | Borra el borrador; no crea nada | 302 a `muestras:registrar` + info "Registro de muestra cancelado." |
| `confirmar` con borrador válido | `registrar_muestra(...)`; borra el borrador; guarda `ultima_muestra_pi` | 302 a `muestras:registrar` + success "Muestra registrada con N° PI {n}." |
| `confirmar` sin borrador y con `ultima_muestra_pi` | Nada (doble envío) | 302 a `muestras:registrar` + info "Muestra registrada con N° PI {n}." |
| `confirmar` sin borrador ni `ultima_muestra_pi` | Nada | 302 a `muestras:registrar` |
| `confirmar` con cliente desactivado u origen ya no válido | Nada; conserva el borrador | 302 a `muestras:registrar?volver=1` + warning "El cliente no está disponible." / "El origen no pertenece al cliente seleccionado." |
| `confirmar` con error de base | Rollback completo | 200 en la confirmación + error "No se pudo registrar la muestra. Intentá nuevamente." |
| otra / ausente | Nada | 302 a `muestras:registrar_confirmar` |

## Navegación

- `templates/base.html`: enlace "Registrar muestra" (`muestras:registrar`) en la barra.
- `templates/inicio.html`: botón "Registrar muestra".
