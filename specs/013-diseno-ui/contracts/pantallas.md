# Contrato: pantallas del alcance

Cada pantalla mantiene su URL, vista, formulario y textos (FR-012). Solo cambia el template.
Referencia visual: carpetas de `stitch/`; las pantallas sin maqueta propia se arman con los mismos
componentes.

| # | Pantalla | Template | Layout | Referencia Stitch | Componentes principales |
|---|---|---|---|---|---|
| 1 | Iniciar sesión | `usuarios/login.html` | acceso | `login/`, `login-pendiente/` | `errores_form`, `campo`, link "Crear cuenta". El error con código `pendiente_aprobacion` ("Tu cuenta está pendiente de aprobación") se muestra como advertencia (ámbar), el resto como error (rojo) |
| 2 | Registro de usuario | `usuarios/registro_form.html` | acceso | `crear-cuenta/` | `errores_form`, `campo` (nombre y apellido en una fila), link "Iniciar sesión" |
| 3 | Confirmar registro | `usuarios/registro_confirmar.html` | acceso | `confirmar-registro/` | aviso informativo, `resumen`, `acciones_confirmacion` |
| 4 | Registro recibido | `usuarios/registro_recibido.html` | acceso | `registro-recibido/` | ícono de espera, `mensajes`, botón "Iniciar sesión" |
| 5 | Inicio | `inicio.html` | interno | `inicio/` | banner con imagen, 4 accesos rápidos, 3 indicadores, `tabla` + `estado` + `estado_vacio` |
| 6 | Registrar cliente | `clientes/registro_form.html` | interno | `registrar-cliente/` | `encabezado`, 2 `seccion_form` (Identificación, Contacto), `campo`, `segmentado` (DNI / CUIT) |
| 7 | Confirmar cliente | `clientes/registro_confirmar.html` | interno | `confirmar-estudio/` | `resumen`, `acciones_confirmacion` |
| 8 | Buscar cliente | `clientes/buscar.html` | interno | `buscar-cliente/` | buscador, `tabla`, `iniciales`, `paginacion`, `estado_vacio` |
| 9 | Ficha del cliente | `clientes/detalle.html` | interno | `ficha-cliente/` | `encabezado` con `estado`, grilla de datos, botones |
| 10 | Editar cliente | `clientes/editar_form.html` | interno | `registrar-muestra/` | `seccion_form`, `campo` |
| 11 | Confirmar edición | `clientes/editar_confirmar.html` | interno | `confirmar-estudio/` | `resumen`, `acciones_confirmacion` |
| 12 | Registrar muestra | `muestras/registro_form.html` | interno | `registrar-muestra/` | 3 `seccion_form`, mini-ficha, `campo`, `segmentado` |
| 13 | Confirmar muestra | `muestras/registro_confirmar.html` | interno | `confirmar-estudio/` | `resumen` con `estado`, `acciones_confirmacion` |
| 14 | Crear estudio | `estudios/crear_form.html` | interno | `registrar-muestra/` | `seccion_form`, `campo` |
| 15 | Confirmar estudio | `estudios/crear_confirmar.html` | interno | `confirmar-estudio/` | `resumen` con `estado`, lista de pruebas, `acciones_confirmacion`; variante "Recuperar solicitud" |

## Panel de inicio (pantalla 5)

- Vista `config.views.inicio`, URL `""`, nombre `inicio` (sin cambios para el resto del sistema).
- Contexto: `muestras_sin_estudio`, `muestras_hoy`, `estudios_pendientes` (enteros) y
  `ultimas_muestras` (hasta 5 `Muestra`). Ver [../data-model.md](../data-model.md).
- Sin muestras: indicadores en 0 y `estado_vacio` con acceso a "Registrar muestra".
- Requiere sesión (middleware global, sin cambios).

## Admin de Django

No se rediseña. `templates/admin/base_site.html` sigue igual; el botón "Reintentar" de la guardia de
sesión dentro del admin queda sin estilo propio, como hoy.
