# Contrato UI e interfaz interna: Desvíos (SCRUM-61, US 8.2)

## Interfaz interna (`estudios/desvios.py`, solo lectura)

| Función | Contrato |
|---|---|
| `regla() -> Regla` | Única lectura de `settings.AQUALAB_DESVIOS`; `ImproperlyConfigured` si umbral ≤ 0 o cantidad < 1. |
| `es_desvio(valor, promedio, umbral) -> bool` | Pura, `Decimal`, exacta (research R3). |
| `detectar(historial, regla) -> Deteccion \| None` | Pura sobre un `HistorialPrueba` con referencia: `None` sin referencia, con menos de N `anteriores` o dentro del umbral. A/P por cambio de estado (R4). |
| `historial_suficiente(historial, regla) -> bool` | `len(historial.anteriores) >= regla.cantidad`. |
| `evaluar_estudio(estudio, asignaciones, regla=None) -> dict[asignacion_pk, Deteccion \| None \| HISTORIAL_INSUFICIENTE]` | Una llamada a `comparar(origen, estudio=estudio, codigos=…)` sobre las asignaciones con resultado; las que no tienen resultado no aparecen. No escribe. |
| `pendientes() -> list[Pendiente]` | Asignaciones Cargadas con resultado de todos los estudios, evaluadas por estudio; solo las con `Deteccion`; orden `fecha_calculo` descendente, pk. |
| `enlace_comparacion(estudio, codigo) -> str` | `reverse("estudios:comparacion") + "?estudio=…&pruebas=…&elegir=1"`. |
| `texto_regla(regla) -> str` | «más de un 30 % respecto del promedio de los últimos 3 resultados validados del origen». |
| textos | `texto_observado`, `texto_promedio`, `texto_variacion` («▲ +210,3333 mg/l (+95,8 %)» / «sin porcentaje (promedio previo 0)»), `texto_presencia` («Presente (los últimos 3: Ausente)»), y su versión desde una `Validacion` con constancia. |

`estudios/servicios.py`:

- `validar_resultados(estudio_pk, elegidas, usuario, observaciones=None)` — sin cambios en
  permisos, bloqueo ni omisiones. Después de bloquear, `desvios.evaluar_estudio(estudio,
  asignaciones)`; cada `Validacion` creada lleva `observacion=observaciones.get(pk, "").strip()` y,
  si hay `Deteccion`, `desvio_promedio` y `desvio_umbral=regla.umbral`. `ResultadoValidacion` suma
  `con_desvio: list[Prueba]` para el mensaje de éxito.

No hay URL, vista, formulario ni pantalla para «Marcar como revisado». No se modifican
`calculo.py`, `cargar_mediciones` ni `corregir_mediciones`.

## Pantallas

### Marca (`estudios/desvio.html`, parcial)

Recibe `deteccion` (pendiente) o `validacion` (con constancia) y el `estudio`/`codigo` para el
enlace.

- Pendiente: badge con ícono de alerta y «Desvío» (tono advertencia); «Observado 430 mg/l ·
  Promedio de los últimos 3: 219,6667 mg/l · ▲ +210,3333 mg/l (+95,8 %)» (A/P: «Presente (los últimos
  3: Ausente)»).
- Revisado: badge «Desvío revisado» (tono neutro); «Validado por Nombre el dd/mm/aaaa hh:mm –
  observación · promedio 219,6667 mg/l, umbral 30 %» («Sin observación» si está vacía).
- Ambos: enlace «Comparación histórica» solo con `perms.informes.ver_dashboard`; `ui/ayuda.html`
  con la regla vigente.

### `GET /estudios/<pk>/` — detalle (cambios)

- Columna «Resultado»: la marca para las asignaciones Cargadas con desvío y para las Completadas
  cuya validación vigente tiene constancia.

### `GET|POST /estudios/<pk>/resultados/validar/` (cambios)

- Arriba: «2 pruebas con desvío» (mensaje de advertencia con ícono) si hay filas con desvío, con la
  regla en la ayuda.
- Fila con desvío: destacada (fondo/borde de advertencia + ícono + «Desvío»), con la marca y el
  campo «Observación» (`ui/campo.html`, `observacion_<pk>`, opcional, ≤ 500, `help_text`: «Queda
  guardada en la validación de esta prueba como revisión del desvío. Solo la ve el
  laboratorio.»). Error junto al campo si supera 500.
- Fila sin desvío con historial insuficiente: «Historial insuficiente para detectar desvíos»
  (texto secundario).
- `accion=revisar` con observación inválida → la misma pantalla con el error (no avanza).

### Confirmación de la validación (cambios)

- Si alguna elegida tiene desvío: «2 de los 5 resultados elegidos tienen desvío: quedarán
  revisados al validar.» y una lista Prueba · Observado · Promedio · Observación («Sin
  observación» si está vacía).
- `observacion_<pk>` viaja oculto, como `resultado_<pk>`; «Editar» vuelve con lo escrito.
- Al confirmar: mensaje de éxito existente + «Se revisaron 2 desvíos: CL-, CONDUCT.» (o «Se revisó
  1 desvío: CL-.») según `con_desvio`; omitidas como hoy.

### `GET /estudios/desvios/` — `estudios:desvios`

- Permiso `informes.ver_dashboard` (403), `require_GET`.
- Encabezado «Desvíos sin revisar» con «N pendientes» y ayuda con la regla y «Se revisan al
  validar la prueba». Tabla (`estudios/desvios_tabla.html`, compartida con el dashboard): N° PI
  (enlace a `muestras:detalle`), Cliente · Origen, Prueba, Observado, Promedio, Variación,
  Calculado (dd/mm/aaaa), Acciones («Ver estudio», «Comparación histórica» y, con
  `estudios.validar_resultados`, «Validar» → `estudios:validar_resultados`). Paginada de a 25
  (`ui/paginacion.html`). Vacía: «No hay desvíos sin revisar».

### `GET /informes/dashboard/` (cambios)

- Sección «Desvíos sin revisar» (`aria-labelledby`), con el contador «N pendientes», la tabla de
  los 10 más recientes y «Ver todos» → `estudios:desvios` si N > 10. No depende de `periodo`.

### Nunca

- Informe en pantalla, vista previa, PDF, impresión, correo y control previo: sin desvíos ni
  observaciones.
