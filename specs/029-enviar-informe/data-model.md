# Data Model: Envío del informe por correo

**Feature**: `029-enviar-informe` | **Plan**: [plan.md](./plan.md)

## EnvioInforme (nuevo, `informes.EnvioInforme`)

Cada envío confirmado de un informe por correo, exitoso o fallido. Inalterable.

| Campo | Tipo | Reglas |
|---|---|---|
| `informe` | `ForeignKey(Informe, on_delete=PROTECT, related_name="envios")` | obligatorio, `editable=False` |
| `enviado_por` | `ForeignKey(AUTH_USER_MODEL, on_delete=PROTECT, related_name="envios_de_informes")` | obligatorio, `editable=False` |
| `fecha` | `DateTimeField(auto_now_add=True)` | fecha y hora del intento |
| `destinatario` | `EmailField(max_length=254)` | el `Cliente.email` vigente al confirmar |
| `resultado` | `CharField(max_length=10, choices=ResultadoEnvio)` | `enviado` («Enviado») o `fallido` («Falló») |
| `clave` | `UUIDField(unique=True, editable=False)` | la clave de la confirmación (un envío por confirmación) |

- `Meta.ordering = ("-fecha", "-pk")`; `verbose_name` «envío de informe» / «envíos de informes».
- `CheckConstraint`: `resultado` en (`enviado`, `fallido`).
- `save()` sobre un registro existente y `delete()` lanzan `ValueError` (como `Informe`); sin admin.
- Migración `informes.0005_envioinforme`.

## Informe (US 7.2/7.3) — sin cambios

Se lee `numero_mostrado`, `contenido` (cliente, muestra, estudio, laboratorio) y
`estudio.muestra.cliente.email`. Se bloquea su fila con `select_for_update()` durante el envío, sin
modificarla.

## Cliente (US 2.1) — sin cambios

`email` (obligatorio en la ficha) es el destino.
