# Data Model: Notificar desvíos relevantes (SCRUM-61, US 8.2)

## `estudios.Desvio` (nuevo, migración `estudios.0009_desvio`)

Aviso de que el resultado de una prueba de un estudio se aleja del historial de su origen.

| Campo | Tipo | Notas |
|---|---|---|
| `asignacion` | FK `PruebaEstudio`, `PROTECT`, `related_name="desvios"`, `editable=False` | la prueba del estudio |
| `valor` | `Decimal(28, 10)` | resultado observado completo (copia de `Resultado.valor`) |
| `unidad` | `CharField(50)`, blank | copia de `Resultado.unidad` |
| `promedio` | `Decimal(28, 10)`, null | promedio de los últimos N; `None` en Ausente/Presente |
| `porcentaje` | `Decimal(9, 1)`, null | con signo, 0,1 `ROUND_HALF_UP` (solo para mostrar); `None` si el promedio es 0 o es A/P |
| `previos` | `JSONField` | lista ordenada de los N usados: `{"estudio": pk, "muestra": pk, "numero_pi": int, "fecha_muestreo": "aaaa-mm-dd", "valor": "texto Decimal"}` |
| `umbral` | `Decimal(5, 2)` | umbral aplicado (%) |
| `cantidad` | `PositiveSmallIntegerField` | N aplicado |
| `fecha_deteccion` | `DateTimeField(auto_now_add)` | |
| `vigente` | `BooleanField(default=True)` | |
| `fecha_cierre` | `DateTimeField`, null | |
| `motivo_cierre` | `CharField(20, choices=MotivoCierre)`, blank | |
| `validacion` | FK `Validacion`, `PROTECT`, null, `related_name="desvios_revisados"` | la validación con la que se revisó (quién = `validada_por`, cuándo = `fecha_validacion`) |
| `observacion` | `CharField(500)`, blank | |

`MotivoCierre` (`TextChoices`): `corregido` «Resuelto por corrección», `reemplazado` «Reemplazado
por un nuevo valor», `sin_resultado` «Sin resultado».

**Restricciones**

- `UniqueConstraint(fields=["asignacion"], condition=Q(vigente=True), name="desvio_vigente_unico")`.
- `CheckConstraint` `desvio_cierre_completo`: `vigente=True, fecha_cierre IS NULL, motivo_cierre=''`
  o `vigente=False, fecha_cierre IS NOT NULL, motivo_cierre<>''`.
- `CheckConstraint` `desvio_observacion_revisado`: `observacion=''` si `validacion IS NULL`.
- `Meta.ordering = ["-fecha_deteccion", "-pk"]`; índice `(vigente, validacion)` para
  `pendientes()`.

**Propiedades / métodos**

- `diferencia` → `valor − promedio` (`None` si A/P).
- `presencia` → `es_presencia(unidad)`.
- `revisado` → `validacion_id is not None`; `revisado_por` / `fecha_revision` → de `validacion`
  (la vista hace `select_related("validacion__validada_por")`).
- `textos()` (o propiedades): valor con `texto_valor` («< LD», «Ausente»), promedio con unidad,
  cambio «▲ +250,4 mg/l (+95,8 %)» o «sin porcentaje (promedio previo 0)», o «Presente (los
  últimos 3: Ausente)». Reutiliza `comparacion.numero`, `con_unidad`, `con_signo`.
- Sin `save()`/`delete()` especiales: solo lo escriben `desvios.reevaluar` (crear, cerrar) y
  `desvios.revisar_al_validar`, llamada solo desde `servicios.validar_resultados` (revisar). Sin
  admin.

**Estados**

```text
            reevaluar: desvío
   (nada) ───────────────────────► VIGENTE · sin revisar ──validar_resultados──► VIGENTE · revisado
                                        │                                       │
                                        └──── reevaluar (valor cambió) ─────────────┤
                                                                                    ▼
                         CERRADO (corregido | reemplazado | sin_resultado), conserva la revisión
```

Un desvío cerrado nunca vuelve a vigente; si el valor vuelve a desviarse se crea otro.
Invariante: una prueba Completada no tiene desvío vigente sin revisar.

## Cambios a estructuras existentes

- `estudios.comparacion.HistorialPrueba`: campo nuevo `anteriores: tuple = ()` — los puntos que
  `historial_de_prueba` ya pasa a `variacion` (validados de muestras previas a la del último, misma
  unidad, ordenados). Sin cambios en la pantalla de la 8.1.
- `settings.AQUALAB_DESVIOS = {"umbral": "30", "cantidad": 3}`.
- `ValidarResultadosForm`: campo `observacion_<pk>` (`CharField(max_length=500, required=False)`)
  solo para las filas con desvío vigente sin revisar; `observaciones()` → `{pk: texto}` de las
  elegidas.
- `servicios.validar_resultados(estudio_pk, elegidas, usuario, observaciones=None)`.

## Estructuras derivadas (no se guardan)

- `desvios.Regla(umbral: Decimal, cantidad: int)` — de `regla()`.
- `desvios.Deteccion(valor, unidad, promedio, porcentaje, previos, presencia)` — resultado puro de
  `detectar(historial, regla)`, o `None` si no hay desvío. `SinHistorial` (o `None` + bandera) para
  «Historial insuficiente».

## Relaciones

```text
Origen 1─* Muestra 1─* Estudio 1─* PruebaEstudio 1─1 Resultado
                                       │
                                       ├─* Validacion   (vigente ⇔ Completada)
                                       └─* Desvio       (≤ 1 vigente) ── validacion → Validacion (revisión)
```
