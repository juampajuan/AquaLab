# Contrato de interfaz: Quitar prueba del estudio

**Feature**: `011-quitar-prueba-estudio` | **Plan**: [plan.md](../plan.md)

Todas las rutas requieren sesión iniciada (sin sesión → 302 al login, FR-001) y llevan CSRF en los
POST. Las pantallas extienden `base.html` y los mensajes se muestran con el framework `messages`.
`<pk>` es el identificador del estudio; si no existe, las rutas responden **404**.

## `GET /estudios/<pk>/` — `estudios:detalle` (de US 5.3, cambio)

La columna Acción de la tabla de pruebas, vacía en US 5.3, pasa a mostrar:

- Botón-enlace **Quitar** (`btn btn-sm btn-outline-danger`) a `estudios:quitar_prueba` de la
  asignación, solo si `estudio.admite_modificaciones`, `asignacion.puede_quitarse()` y el estudio
  tiene más de una prueba.
- Con una sola prueba, en lugar del botón: texto «El estudio debe conservar al menos una prueba.»

El resto del detalle no cambia (ver
[contrato de US 5.3](../../010-agregar-prueba-estudio/contracts/agregar-prueba-ui.md)).

## `GET /estudios/<pk>/pruebas/<asignacion_pk>/quitar/` — `estudios:quitar_prueba`

- Asignación que no pertenece al estudio o ya no existe → 302 a `detalle` + info «La prueba ya no
  forma parte del estudio.»
- Estudio no modificable, última prueba o `puede_quitarse()` falso → 302 a `detalle` + error con el
  motivo (mismos textos que el POST).
- **Respuesta**: 200, template `estudios/quitar_prueba_confirmar.html`: «Se quitará la prueba
  `código · nombre` del estudio N (muestra PI X). No se realizará ni se incluirá en el informe.»,
  botón **Quitar prueba** (`btn-danger`, POST) y enlace **Cancelar** a `detalle`.

## `POST /estudios/<pk>/pruebas/<asignacion_pk>/quitar/`

| Condición (revalidada bajo bloqueo) | Resultado |
|---|---|
| asignación inexistente o de otro estudio (reenvío o quita simultánea) | 302 a `detalle` + info «La prueba ya no forma parte del estudio.» |
| estudio no modificable | 302 a `detalle` + error «Este estudio ya no admite cambios en sus pruebas.» |
| última prueba del estudio | 302 a `detalle` + error «El estudio debe conservar al menos una prueba.» |
| con mediciones o resultados (`puede_quitarse()` falso o `ProtectedError`) | 302 a `detalle` + error «La prueba tiene mediciones o resultados cargados y no se puede quitar.» |
| válido | `quitar_prueba(...)` → 302 a `detalle` + éxito «Prueba `código · nombre` quitada del estudio N.» |
| `DatabaseError` | 302 a `detalle` + error «No se pudo quitar la prueba. Intentá nuevamente.» |
