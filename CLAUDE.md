# Notas para Claude Code — AquaLab

## Pendientes entre features

Cuando una feature resuelva un pendiente, borrar su línea.

- **Envío de informes (SCRUM-39):** el envío de informes por correo usa `Cliente.email`.

## Mensajes de commit

Conventional Commits en español, con la US en el mensaje: `tipo(ámbito): descripción`.

- Spec Kit: `docs(specs): spec de la US 3.2 – Editar cliente` (igual para `plan` y `tasks`).
- Código: `feat(<app>): US 3.2 – Editar cliente`; correcciones `fix(<app>): ...`.
- Infraestructura y configuración: `chore: ...`.

## Avisos por correo (US 1.3)

- Los avisos de `usuarios/notificaciones.py` se llaman explícitamente desde `registro_confirmar`,
  `UsuarioAdmin.aprobar_cuentas`, `UsuarioAdmin.save_model` y `UsuarioAdmin.rechazar_solicitudes`.
  No se usan señales: `queryset.update()` no las dispara.
- Siempre se agendan con `transaction.on_commit`; una falla de envío solo queda en el log
  `usuarios.notificaciones`. Rechazar elimina la cuenta pendiente para liberar el correo.
- En los tests: `django_capture_on_commit_callbacks(execute=True)` y `mailoutbox`.

## Autenticación integrada (US 1.2)

- Login/logout propios en usuarios; LOGIN_URL y ambos cierres llevan al login AquaLab.
- Se mantiene ModelBackend y aprobación mediante is_active. Diagnóstico de pendiente solo con
  contraseña correcta; decisiones en specs/002-inicio-cierre-sesion/research.md.
- Login y registro recibido ya incluyen los enlaces recíprocos; Registrar cliente está en navbar.
- La guardia de sesión comparte lógica entre layouts de AquaLab y admin; los permisos administrativos
  permanecen intactos. No exponer sessionid ni usar la huella HMAC como autorización.
- T027/navegador acreditada por reporte del usuario; T001/aprobación formal y T032 siguen pendientes. Consultar tasks.md antes de
  declarar cerrada la historia; implementación local autorizada por excepción documentada en plan.md.

## Registro de muestras (US 4.1)

- El N° PI lo asigna `muestras/servicios.py:registrar_muestra` (máximo + 1, desde 200001) bajo
  `pg_advisory_xact_lock`. No usar secuencias ni `AutoField`: dejan huecos ante un rollback.
- El origen nuevo se crea (o se reutiliza, sin distinguir mayúsculas) en la misma transacción que la
  muestra, después del lock; cancelar o fallar no deja orígenes huérfanos ni consume N° PI.
- Cada borrador lleva una `clave_borrador` (UUID, `unique` en `Muestra`); bajo el lock, si ya hay una
  muestra con esa clave se devuelve en vez de crear otra. Borrar el borrador de la sesión no alcanza:
  las sesiones de Django no se bloquean y dos confirmaciones simultáneas leen el mismo borrador.
- La ficha del cliente y sus orígenes se actualizan en vivo con
  `muestras/static/muestras/registro_muestra.js`; con un cliente ya elegido (errores o `?volver=1`)
  los renderiza el servidor. No hay buscador de clientes: se quitó tras la prueba manual.

## Consulta de estado del estudio y ficha de la muestra (US 5.2)

- `EstadoEstudio` (`pendiente_analisis`, `en_proceso`, `finalizado`, `informe_generado`) y
  `EstadoPruebaEstudio` (`pendiente`, `cargada`, `completada`) en `estudios/models.py`. Toda
  `PruebaEstudio` inicia en `pendiente`.
- Las vistas de consulta (`estudios:buscar`, `estudios:detalle` y `muestras:detalle`) muestran siempre
  `tipo_nombre_snapshot` y `tipo_descripcion_snapshot` para preservar la historia del estudio frente a
  ediciones posteriores del catálogo.

## Pruebas de un estudio (US 5.3 y US 5.4)

- `agregar_prueba` y `quitar_prueba` (`estudios/servicios.py`) bloquean la fila del estudio
  (`select_for_update`), no el advisory lock global de la creación; así `quitar_prueba` cuenta las
  asignaciones sin carreras y ningún estudio queda sin pruebas.
- `Estudio.admite_modificaciones` es la única regla de estudio modificable: la usan el detalle, la
  vista y el servicio (que la revalida bajo el bloqueo).
- Las vistas `agregar_prueba` y `quitar_prueba` tapan el nombre del servicio: llaman a
  `servicios.<nombre>` y en los tests se parchea `estudios.servicios.<nombre>`.
- Un reenvío de `confirmar` falla el formulario (la prueba ya no está entre las opciones); la vista
  lo detecta con `AgregarPruebaForm.prueba_ya_asignada()` y el servicio lo informa como aviso.
- Las pruebas agregadas nacen en estado Pendiente. Quitar borra la asignación (sin historial) y
  solo se permite si `PruebaEstudio.puede_quitarse()`, es decir, estado Pendiente.
- **Epic 6 (mediciones y resultados):** pasar la prueba a `Cargada`/`Completada` al registrar
  mediciones o resultados, con la asignación bloqueada (`quitar_prueba` la bloquea para leer el
  estado), y referenciar `PruebaEstudio` con `on_delete=PROTECT`.
- `motivo_para_no_quitar` es la única fuente de las reglas de quita: la usan la vista (GET) y el
  servicio. `.btn-chico` es el botón para filas de tablas.
