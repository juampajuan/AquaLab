# Contrato UI e interfaz interna: Desvíos (SCRUM-61, US 8.2)

## Interfaz interna (`estudios/desvios.py`)

| Función | Contrato |
|---|---|
| `regla() -> Regla` | Única lectura de `settings.AQUALAB_DESVIOS`; `ImproperlyConfigured` si umbral ≤ 0 o cantidad < 1. |
| `es_desvio(valor, promedio, umbral) -> bool` | Pura, `Decimal`, exacta (research R4). |
| `detectar(historial, regla) -> Deteccion \| None` | Pura sobre un `HistorialPrueba` con referencia: `None` sin referencia, con menos de N `anteriores` o dentro del umbral. A/P por cambio de estado (R5). |
| `historial_suficiente(historial, regla) -> bool` | `len(historial.anteriores) >= regla.cantidad`. |
| `reevaluar(estudio, cambiadas, sin_resultado) -> None` | Exige el estudio bloqueado por el llamador. Una llamada a `comparar`; aplica la tabla de R7. Solo la llaman `calculo.recalcular` y el comando. |
| `revisar_al_validar(asignacion, validacion, observacion) -> bool` | Exige el estudio y la asignación bloqueados (lo llama solo `validar_resultados`, después de crear la `Validacion`). Revisa el desvío vigente sin revisar, si hay; `True` si revisó uno. Nunca pisa una revisión existente. |
| `pendientes() -> QuerySet[Desvio]` | Vigentes sin revisar, `-fecha_deteccion`, con `select_related` para la lista. Única consulta del dashboard y de la lista. |
| `del_estudio(estudio) -> dict[asignacion_pk, Desvio]` | El vigente de cada asignación, con `validacion__validada_por` (para marcar filas). |
| `enlace_comparacion(desvio) -> str` | `reverse("estudios:comparacion") + "?estudio=…&pruebas=…&elegir=1"`. |

`estudios/servicios.py`:

- `validar_resultados(estudio_pk, elegidas, usuario, observaciones=None)` — sin cambios en
  permisos, bloqueo ni omisiones; por cada prueba validada llama a `desvios.revisar_al_validar`
  con `observaciones.get(pk, "")` (recortada). `ResultadoValidacion` suma `revisados: list[Prueba]`
  para el mensaje de éxito.

`estudios/calculo.py`:

- `recalcular` llama a `desvios.reevaluar(estudio, cambiadas, sin_resultado)` al final (R1, R2).

Comando: `python manage.py evaluar_desvios` → «Desvíos detectados: N. Resultados evaluados: M.»

No hay URL, vista, formulario ni pantalla para «Marcar como revisado».

## Pantallas

### Marca (`estudios/desvio.html`, parcial)

Recibe `desvio` (vigente). Badge con ícono de alerta y texto «Desvío» (tono advertencia) o «Desvío
revisado» (tono neutro). Debajo: «Observado 430 mg/l · Promedio de los últimos 3: 219,67 mg/l · ▲
+210,33 mg/l (+95,8 %)» (A/P: «Presente (los últimos 3: Ausente)») y enlace «Comparación
histórica» (solo con `informes.ver_dashboard`). Revisado: «Revisado por Nombre el dd/mm/aaaa hh:mm
– observación». Ayuda (`ui/ayuda.html`) con la regla vigente.

### `GET /estudios/<pk>/` — detalle (cambios)

- Columna «Resultado»: incluye la marca para las asignaciones con desvío vigente.
- Sección «Desvíos» (si el estudio tuvo alguno): tabla Prueba · Observado · Promedio · Variación ·
  Detectado · Estado («Sin revisar», «Revisado por … el … – observación», «Resuelto por corrección
  el …», «Reemplazado por un nuevo valor el …», «Sin resultado desde …»), con umbral y cantidad
  aplicados («umbral 30 %, últimos 3») y los previos (N° PI y valor) en un `<details>`.

### `GET|POST /estudios/<pk>/resultados/validar/` (cambios)

- Arriba: «2 pruebas con desvío» (mensaje de advertencia con ícono) si hay filas con desvío vigente
  sin revisar, con la regla en la ayuda.
- Fila con desvío: destacada (borde/fondo de advertencia + ícono + texto «Desvío»), con la marca
  (observado, promedio, variación, «Comparación histórica») y el campo «Observación»
  (`ui/campo.html`, `observacion_<pk>`, opcional, ≤ 500, `help_text`: «Queda guardada con la
  revisión del desvío al validar esta prueba. Solo la ve el laboratorio.»). Error junto al campo si
  supera 500.
- Fila sin desvío: «Historial insuficiente para detectar desvíos» (texto secundario) si
  `anteriores < N`; nada si el historial alcanza y no hay desvío.
- `accion=revisar` con observación inválida → la misma pantalla con el error (no avanza).

### Confirmación de la validación (cambios)

- Si alguna elegida tiene desvío vigente sin revisar: «2 de los 5 resultados elegidos tienen
  desvío: quedarán revisados al validar.» y una lista Prueba · Observado · Promedio · Observación
  («Sin observación» si está vacía).
- `observacion_<pk>` de las filas con desvío viaja oculto, como `resultado_<pk>`; «Editar» vuelve
  a la pantalla con lo escrito.
- Al confirmar: mensaje de éxito existente + «Se revisaron 2 desvíos: CL-, CONDUCT.» si
  corresponde; omitidas como hoy (su desvío no cambia).

### `GET /estudios/desvios/` — `estudios:desvios`

- Permiso `informes.ver_dashboard` (403), `require_GET`.
- Encabezado «Desvíos sin revisar» con «N pendientes» y ayuda con la regla y «Se revisan al
  validar la prueba». Tabla (`estudios/desvios_tabla.html`, compartida con el dashboard): N° PI
  (enlace a `muestras:detalle`), Cliente · Origen, Prueba, Observado, Promedio, Variación,
  Detectado (dd/mm/aaaa), Acciones («Ver estudio», «Comparación histórica» y, con
  `estudios.validar_resultados`, «Validar» → `estudios:validar_resultados`). Paginada de a 25
  (`ui/paginacion`). Vacía: «No hay desvíos sin revisar».

### `GET /informes/dashboard/` (cambios)

- Sección «Desvíos sin revisar» (`aria-labelledby`), con el contador «N pendientes», la tabla de
  los 10 más recientes y «Ver todos» → `estudios:desvios` si N > 10. No depende de `periodo`.

### Nunca

- Informe en pantalla, vista previa, PDF, impresión y correo: sin desvíos ni observaciones.
- Control previo al informe: sin cambios.
