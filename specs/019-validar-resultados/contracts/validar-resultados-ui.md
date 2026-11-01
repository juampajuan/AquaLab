# Contrato de interfaz: Validar resultados

**Feature**: `019-validar-resultados` | **Plan**: [plan.md](../plan.md)

Todas las rutas requieren sesión iniciada (sin sesión → 302 al login) y llevan CSRF en los POST.
Pantallas con `base.html` y los componentes de `templates/ui/`, como la carga y la corrección de
mediciones (specs 015 y 017). `<pk>` inexistente → **404**.

## `GET /estudios/<pk>/` — `estudios:detalle` (cambio)

- Columna **Resultado**: junto al valor, la evaluación con `ui/estado.html`:
  - «Cumple» → `success`; «Fuera de norma» → `danger`; «Sin límite comparable» → `neutral`;
  - debajo, en `text-xs text-tinta-suave`: «Límite: <mín> a <máx>», «Límite: máx. <máx>» o
    «Límite: mín. <mín>», tal como figura en el catálogo, con la norma y el origen si no es general
    («(Cloacal)»). Sin límites: «Sin límite en el catálogo».
  - Prueba Completada: la evaluación y los límites guardados al validar, y una línea más:
    «Validada por <nombre o correo> · <d/m/Y H:i>».
- Botón **Validar resultados** (`btn btn-primario`, ícono `check`), solo si el usuario tiene
  `perms.estudios.validar_resultados`, `estudio.admite_correcciones` y alguna prueba Cargada con
  resultado.

## `GET /estudios/<pk>/resultados/validar/` — `estudios:validar_resultados`

- Sin el permiso → **403** (`@permission_required(..., raise_exception=True)`).
- Informe emitido → 302 a `detalle` + error «El estudio ya tiene el informe emitido: sus
  resultados no se pueden validar.».
- Sin pruebas para validar → `ui/estado_vacio.html` con «No hay resultados para validar en este
  estudio.» y enlace al estudio.
- Tabla de las pruebas Cargadas con resultado, por código: **Validar** (`<input type="checkbox"
  name="validar_<asignacion_pk>">`, marcado solo si cumple), **Código**, **Prueba**,
  **Resultado** (`|valor_medicion` y unidad), **Límite** (como en el detalle) y **Evaluación**
  (etiqueta). Oculto `resultado_<asignacion_pk>` con `str(resultado.valor)`.
- Aviso arriba si hay fuera de norma: «Hay N resultados fuera de norma: revisalos antes de
  marcarlos.».
- Acciones: **Revisar validación** (`accion=revisar`), **Marcar todas** (`accion=marcar_todas`,
  `btn btn-secundario`) y **Cancelar** (enlace al detalle).

## `POST /estudios/<pk>/resultados/validar/`

Sin el permiso → 403. `accion` no reconocida → 302 a `detalle` + «La acción no es válida.». En
`revisar`, `editar` y `marcar_todas`, informe emitido → 302 a `detalle` con el error de arriba.

### `accion=marcar_todas`

200 con el formulario y todas las casillas marcadas.

### `accion=revisar`

- Ninguna marcada → 200 con el formulario y el error general «Elegí al menos un resultado para
  validar.».
- Válido → 200 `estudios/validar_resultados_confirmar.html`: aviso «Se validarán N resultados en el
  estudio X (muestra PI Y).» («Se validará 1 resultado…» con uno); tabla **Código / Prueba /
  Resultado / Límite / Evaluación** de las elegidas; si alguna no cumple, aviso de advertencia «No
  cumplen: COD · nombre, …. Se validarán igual.»; si con esto se completan todas, «El estudio
  quedará Finalizado.». Ocultos `validar_<pk>` y `resultado_<pk>` de las elegidas. Botones
  **Validar resultados** (`accion=confirmar`, evita el doble envío con `data-enviado`), **Volver a
  elegir** (`accion=editar`) y **Cancelar**.

### `accion=editar`

200 con el formulario y la selección reenviada.

### `accion=confirmar`

- Formulario inválido → 200 con el formulario y errores (nada cambia).
- Válido → `servicios.validar_resultados(...)` y 302 a `detalle` con:
  - éxito, si hubo validadas: «Se validaron N resultados del estudio X: COD1, COD2.» («Se validó 1
    resultado del estudio X: COD1.»); si pasó a Finalizado, otro éxito: «El estudio X quedó
    Finalizado.»;
  - advertencia por cada omitida: «COD: ya estaba validada.», «COD: ya no tenía resultado.» o
    «COD: cambió mientras se revisaba.»;
  - `ValidarResultadosError` → error con su mensaje; `DatabaseError` → «No se pudo validar los
    resultados. Intentá nuevamente.» y nada cambia.

## Servicio — `estudios.servicios.validar_resultados(estudio_pk, elegidas, usuario)`

- `elegidas`: `{asignacion_pk: valor_visto (str)}`. Los `pk` que no son del estudio se ignoran.
- Errores (`ValidarResultadosError`): sin sesión activa; sin el permiso «Se requiere permiso para
  validar resultados.»; estudio inexistente «El estudio no está disponible.»; informe emitido.
- Devuelve `ResultadoValidacion` con `validadas` (pruebas), `omitidas` (`(prueba, motivo)`) y
  `finalizado` (bool).
- Transacción única: el estudio bloqueado y después las asignaciones (mismo orden que carga,
  corrección y quita).

## Admin

- El grupo «Bioquímicos» aparece en Autenticación y autorización → Grupos con el permiso
  «estudios | validación | Puede validar resultados». Agregar una persona: Usuarios → la persona →
  Grupos.
