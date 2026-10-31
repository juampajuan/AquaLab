# Contrato de interfaz: Cargar mediciones

**Feature**: `015-cargar-mediciones` | **Plan**: [plan.md](../plan.md)

Todas las rutas requieren sesión iniciada (sin sesión → 302 al login, FR-001) y llevan CSRF en los
POST. Las pantallas extienden `base.html`, usan los componentes de `templates/ui/` (SCRUM-67) y los
mensajes van por el framework `messages`. `<pk>` es el estudio; si no existe → **404**.

## `GET /estudios/<pk>/` — `estudios:detalle` (existente, cambio)

- En la cabecera de «Pruebas asignadas», botón **Cargar mediciones** (`btn btn-primario`, ícono de
  carga) a `estudios:cargar_mediciones`, solo si `estudio.admite_mediciones` y hay al menos una
  prueba `Pendiente` no calculada (`pruebas_para_medir > 0` en el contexto).
- La tabla suma la columna **Medición**: para una prueba con medición, el valor tal como se escribió
  con coma decimal y la unidad (o «Sin unidad»), y debajo, en texto chico, quién la cargó y la fecha
  y hora (`d/m/Y H:i`). Sin medición: «—». Prueba calculada sin resultado: «Se calcula».
- Al pasar el estudio a "En proceso" desaparecen «Agregar prueba» y «Quitar» por la regla existente
  (`admite_modificaciones`).

## `GET /estudios/<pk>/mediciones/cargar/` — `estudios:cargar_mediciones`

- Estudio que no admite carga → 302 a `detalle` + error «Este estudio ya no admite carga de
  mediciones.»
- Pantalla `estudios/cargar_mediciones.html`, encabezado con migas «Estudios › Estudio N › Cargar
  mediciones» y aviso con el estudio y la muestra (PI).
- Tabla de pruebas `Pendiente` no calculadas, ordenadas por código: **Código**, **Prueba**,
  **Unidad** (o «Sin unidad») y **Medición**: `<input type="text" inputmode="decimal"
  autocomplete="off" name="medicion_<asignacion_pk>">`, con el error debajo (`campo-error`, id
  `<auto_id>_error`, clase `is-invalid` y `aria-describedby`).
- Si hay pruebas calculadas pendientes: bloque «Se calculan a partir de otras pruebas» con su código
  y nombre, sin campos.
- Sin pruebas para medir: `ui/estado_vacio.html` con «No hay mediciones para cargar en este
  estudio.» y enlace al estudio; no hay botón de guardar.
- Acciones: **Revisar mediciones** (`accion=revisar`) y **Cancelar** (enlace al detalle).

## `POST /estudios/<pk>/mediciones/cargar/`

`accion` no reconocida → 302 a `detalle` + error «La acción no es válida.»

### `accion=revisar`

- Formulario inválido → 200 con el mismo formulario, los valores ingresados y:
  - por campo, el mensaje de `leer_valor` (ver tabla);
  - sin ningún valor: error general «Ingresá al menos una medición.» (`ui/errores_form.html`).
- Válido → 200 `estudios/cargar_mediciones_confirmar.html`: resumen con estudio y muestra, tabla
  **Código / Prueba / Valor / Unidad** solo con las pruebas que tienen valor, y la cantidad («Se
  guardarán N mediciones»). Campos ocultos `medicion_<pk>` con el texto ingresado.
  Botones: **Guardar mediciones** (`accion=confirmar`, se deshabilita al enviar), **Volver a
  editar** (`accion=editar`) y **Cancelar** (enlace al detalle, no guarda nada).

### `accion=editar`

200 con el formulario y los valores reenviados.

### `accion=confirmar`

- Se revalida el formulario (con todas las asignaciones no calculadas del estudio). Inválido → 200
  con el formulario y errores (no se guarda nada).
- Válido → `servicios.cargar_mediciones(...)` y 302 a `detalle` con:
  - éxito: «Se guardaron N mediciones del estudio X: COD1, COD2.»;
  - por cada omitida, advertencia «COD: <motivo>.» con motivo «ya tenía una medición cargada»,
    «ya no forma parte del estudio» o «se calcula a partir de otras pruebas»;
  - campos enviados de asignaciones que ya no existen: advertencia «N prueba(s) ya no forman parte
    del estudio; su medición no se guardó.»;
  - `CargarMedicionesError` → error con su mensaje; `DatabaseError` → error «No se pudieron guardar
    las mediciones. Intentá nuevamente.» (nada guardado).

## Mensajes de `leer_valor`

| Entrada | Resultado |
|---|---|
| `7,25` · `7.25` · ` 7,20 ` · `-0,013` · `0` · `,5` | Válido (`7.25`, `7.25`, `7.20`, `-0.013`, `0`, `0.5`) |
| vacío o solo espacios | Sin valor (la prueba queda Pendiente) |
| `abc` · `1.234,5` · `1,2,3` · `1e3` · `7 25` · `7%` · `NaN` | «Ingresá un número válido (usá coma o punto para los decimales).» |
| `0,1234567` | «Ingresá como máximo 6 decimales.» |
| `1234567890123` | «El valor es demasiado grande (máximo 12 cifras enteras).» |
