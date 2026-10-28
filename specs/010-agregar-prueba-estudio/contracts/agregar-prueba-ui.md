# Contrato de interfaz: Agregar prueba al estudio

**Feature**: `010-agregar-prueba-estudio` (rama `010-agregar-prueba-v2`) | **Plan**: [plan.md](../plan.md)

Todas las rutas requieren sesión iniciada (sin sesión → 302 al login, FR-001) y llevan CSRF en los
POST. Las pantallas extienden `base.html` y los mensajes se muestran con el framework `messages`.
`<pk>` es el identificador del estudio; si no existe, todas las rutas responden **404**.

Las pantallas usan el layout y los componentes de SCRUM-67 (`templates/ui/`): `ui/encabezado.html`,
`ui/campo.html`, `ui/errores_form.html`, `<dl class="resumen" data-componente="resumen">` y
`ui/acciones_confirmacion.html` o su equivalente con `data-componente="acciones-confirmacion"`.

## `GET /estudios/<pk>/` — `estudios:detalle` (existente, US 5.2)

La vista y su cabecera ya existen. Esta historia solo cambia la sección **Pruebas asignadas**:

- **Agregar prueba**: botón-enlace a `estudios:agregar_prueba` en el encabezado de la sección, solo
  si `estudio.admite_modificaciones`.
- Si el estudio no admite modificaciones: aviso «Este estudio ya no admite cambios en sus
  pruebas.» en la sección y ninguna acción.
- La tabla suma una columna **Acción** a la derecha, vacía en esta historia; US 5.4 agrega ahí el
  botón **Quitar**.

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
  agregar: todas ya forman parte del estudio." y enlace "Volver al estudio".
- Botones: **Revisar** (`accion=revisar`) y enlace **Cancelar** a `detalle`.

## `POST /estudios/<pk>/pruebas/agregar/`

| `accion` | Condición | Resultado |
|---|---|---|
| `revisar` | formulario inválido (vacío, prueba inexistente o ya asignada) | 200, mismo formulario con error junto al campo |
| `revisar` | válido | 200, template `estudios/agregar_prueba_confirmar.html`: «Se agregará la prueba `código · nombre` al estudio N (muestra PI X).», `prueba` en campo oculto, botones **Confirmar** (`accion=confirmar`) y enlaces **Volver** (a agregar) y **Cancelar** (a `detalle`) |
| `confirmar` | prueba inexistente | 200, formulario con error junto al campo |
| `confirmar` | prueba ya asignada (reenvío o agregado simultáneo) | 302 a `detalle` + info «La prueba `código` ya forma parte del estudio.» |
| `confirmar` | estudio no modificable | 302 a `detalle` + error «Este estudio ya no admite cambios en sus pruebas.» |
| `confirmar` | válido | `agregar_prueba(...)` → 302 a `detalle` + éxito «Prueba `código · nombre` agregada al estudio N.» |
| `confirmar` | `DatabaseError` | 302 a `detalle` + error «No se pudo agregar la prueba. Intentá nuevamente.» |
| otro valor | — | 302 a `detalle` + error «La acción no es válida.» |
