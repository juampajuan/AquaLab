# Data Model: Notificar desvíos relevantes (SCRUM-61, US 8.2)

No hay tabla de desvíos: el desvío se calcula al vuelo (research R1). Solo se amplía `Validacion`.

## `estudios.Validacion` (existente; migración `estudios.0009_validacion_desvio`)

Campos nuevos:

| Campo | Tipo | Notas |
|---|---|---|
| `observacion` | `CharField(max_length=500, blank=True, default="")` | opcional; la escribe el bioquímico en la pantalla de validación para una prueba con desvío |
| `desvio_promedio` | `DecimalField(max_digits=28, decimal_places=10, null=True, blank=True)` | promedio de los últimos N con que se comparó si había desvío al validar (en A/P, el valor común 0 o 1) |
| `desvio_umbral` | `DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)` | umbral (%) aplicado si había desvío al validar |

**Restricción**: `CheckConstraint` `validacion_desvio_completo`:
`Q(desvio_promedio__isnull=True, desvio_umbral__isnull=True) | Q(desvio_promedio__isnull=False,
desvio_umbral__isnull=False)`.

**Propiedades**: `con_desvio` → `desvio_umbral is not None`. Quién revisó = `validada_por`;
cuándo = `fecha_validacion`.

Las validaciones existentes quedan con `observacion=""` y desvío nulo (sin desvío registrado). Los
campos se escriben solo al crear la validación en `servicios.validar_resultados`; nunca se
modifican después (una validación se anula, no se edita ni se borra).

## Estructuras derivadas (`estudios/desvios.py`, no se guardan)

- `Regla(umbral: Decimal, cantidad: int)` — de `regla()`, única lectura de
  `settings.AQUALAB_DESVIOS = {"umbral": "30", "cantidad": 3}`.
- `Deteccion(valor, unidad, promedio, porcentaje, previos, presencia)` — resultado puro de
  `detectar(historial, regla)` cuando hay desvío; `porcentaje` es `None` con promedio 0 o en A/P;
  `previos` es la tupla de `Punto` usados.
- `Evaluacion` de una asignación (dict de `evaluar_estudio`): `Deteccion`, `None` (sin desvío) o
  la marca `HISTORIAL_INSUFICIENTE`.
- `Pendiente(asignacion, estudio, muestra, prueba, deteccion, fecha_calculo)` — una fila de la
  lista «Desvíos sin revisar».

## Cambios a estructuras existentes

- `estudios.comparacion.HistorialPrueba`: campo nuevo `anteriores: tuple = ()` — los puntos que
  `historial_de_prueba` ya pasa a `variacion`. Sin cambios en la pantalla de la 8.1.
- `ValidarResultadosForm`: campo `observacion_<pk>` (`CharField(max_length=500, required=False)`)
  solo para las filas con desvío; `observaciones()` → `{pk: texto}` de las elegidas.
- `servicios.validar_resultados(estudio_pk, elegidas, usuario, observaciones=None)`;
  `ResultadoValidacion.con_desvio: list[Prueba]`.

## Ciclo

```text
resultado calculado (Cargada) ──[se muestra]──► evaluar_estudio → Deteccion | None | insuficiente
        │                                              (al vuelo, sin escribir)
        ├── corrección → nuevo valor → se evalúa de nuevo en la próxima vista
        └── validar_resultados (bloqueo) → evaluar_estudio → Validacion(observacion,
                                            desvio_promedio, desvio_umbral)  ← constancia
                     │
                     └── corrección posterior → validación anulada (conserva la constancia)
                                              → la prueba vuelve a Cargada y se evalúa de nuevo
```

## Relaciones

```text
Origen 1─* Muestra 1─* Estudio 1─* PruebaEstudio 1─1 Resultado
                                       └─* Validacion (vigente ⇔ Completada; + observacion,
                                                       desvio_promedio, desvio_umbral)
```
