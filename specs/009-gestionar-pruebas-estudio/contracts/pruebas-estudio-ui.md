# Contrato de interfaz: Agregar y quitar pruebas de un estudio

**Feature**: `009-gestionar-pruebas-estudio` | **Plan**: [plan.md](../plan.md)

Todas las rutas requieren sesión iniciada (sin sesión → 302 al login, FR-001) y llevan CSRF en los
POST. Las pantallas extienden `base.html` y los mensajes se muestran con el framework `messages`.
`<pk>` es el identificador del estudio; si no existe, todas las rutas responden **404**.

## `GET /estudios/<pk>/` — `estudios:detalle`

- **Respuesta**: 200, template `estudios/detalle.html`.
- **Cabecera** (`<dl>`): Estudio N° `pk`, Muestra `PI numero_pi`, Cliente, Origen, Tipo
  (`tipo_nombre_snapshot`), Estado, Creado por, Fecha de creación (zona del laboratorio).
- **Pruebas asignadas**: tabla ordenada por código con columnas Código, Nombre, Estado
  ("Pendiente") y Acción.
  - Botón-enlace **Quitar** en cada fila solo si `estudio.admite_modificaciones`,
    `asignacion.puede_quitarse()` y el estudio tiene más de una prueba.
  - Con una sola prueba, en lugar del botón: texto "El estudio debe conservar al menos una prueba."
- **Agregar prueba**: botón-enlace a `estudios:agregar_prueba` solo si
  `estudio.admite_modificaciones`.
- Si el estudio no admite modificaciones: alerta "Este estudio ya no admite cambios en sus
  pruebas." y ninguna acción.

## Mensaje de éxito de US 5.1 (cambio)

`estudios.views.exito` cambia el texto a «Estudio N creado para la muestra PI X.» con «Estudio N»
como enlace a `estudios:detalle`. La redirección a `estudios:crear` no cambia.

## `GET /estudios/<pk>/pruebas/agregar/` — `estudios:agregar_prueba`

- Estudio no modificable → 302 a `detalle` + error "Este estudio ya no admite cambios en sus
  pruebas."
- **Respuesta**: 200, template `estudios/agregar_prueba.html`, con el estudio identificado
  (N° y PI de la muestra).
- **Campo** `prueba`: `<select>` con las pruebas del catálogo que no están en el estudio, etiqueta
  `código · nombre`, opción vacía "Elegí una prueba".
- Sin pruebas para ofrecer: en lugar del formulario, alerta "No hay pruebas disponibles para
  agregar: todas ya forman parte del estudio." y enlace "Volver al estudio". (Un catálogo vacío no
  puede darse: el estudio conserva al menos una prueba, que está en el catálogo.)
- Botones: **Revisar** (`accion=revisar`) y enlace **Cancelar** a `detalle`.

## `POST /estudios/<pk>/pruebas/agregar/`

| `accion` | Condición | Resultado |
|---|---|---|
| `revisar` | formulario inválido (vacío, prueba inexistente o ya asignada) | 200, mismo formulario con error junto al campo |
| `revisar` | válido | 200, template `estudios/agregar_prueba_confirmar.html`: «Se agregará la prueba `código · nombre` al estudio N (muestra PI X).», `prueba` en campo oculto, botones **Confirmar** (`accion=confirmar`) y enlaces **Volver** (a agregar) y **Cancelar** (a `detalle`) |
| `confirmar` | prueba ya asignada (reenvío o agregado simultáneo) | 302 a `detalle` + info «La prueba `código` ya forma parte del estudio.» |
| `confirmar` | estudio no modificable o prueba inexistente | 302 a `detalle` + error con el motivo |
| `confirmar` | válido | `agregar_prueba(...)` → 302 a `detalle` + éxito «Prueba `código · nombre` agregada al estudio N.» |
| `confirmar` | `DatabaseError` | 302 a `detalle` + error «No se pudo agregar la prueba. Intentá nuevamente.» |
| otro valor | — | 302 a `detalle` + error «La acción no es válida.» |

## `GET /estudios/<pk>/pruebas/<asignacion_pk>/quitar/` — `estudios:quitar_prueba`

- Asignación que no pertenece al estudio o ya no existe → 302 a `detalle` + info «La prueba ya no
  forma parte del estudio.»
- Estudio no modificable, última prueba o `puede_quitarse()` falso → 302 a `detalle` + error con el
  motivo.
- **Respuesta**: 200, template `estudios/quitar_prueba_confirmar.html`: «Se quitará la prueba
  `código · nombre` del estudio N (muestra PI X). No se realizará ni se incluirá en el informe.»,
  botón **Quitar prueba** (`btn-danger`, POST) y enlace **Cancelar** a `detalle`.

## `POST /estudios/<pk>/pruebas/<asignacion_pk>/quitar/`

| Condición (revalidada bajo bloqueo) | Resultado |
|---|---|
| asignación inexistente (reenvío o quita simultánea) | 302 a `detalle` + info «La prueba ya no forma parte del estudio.» |
| estudio no modificable | 302 a `detalle` + error «Este estudio ya no admite cambios en sus pruebas.» |
| última prueba del estudio | 302 a `detalle` + error «El estudio debe conservar al menos una prueba.» |
| con mediciones o resultados (`puede_quitarse()` falso o `ProtectedError`) | 302 a `detalle` + error «La prueba tiene mediciones o resultados cargados y no se puede quitar.» |
| válido | `quitar_prueba(...)` → 302 a `detalle` + éxito «Prueba `código · nombre` quitada del estudio N.» |
| `DatabaseError` | 302 a `detalle` + error «No se pudo quitar la prueba. Intentá nuevamente.» |
