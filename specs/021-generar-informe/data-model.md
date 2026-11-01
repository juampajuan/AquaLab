# Data Model: Generar informe

**Feature**: `021-generar-informe` | **Plan**: [plan.md](./plan.md) | **Research**: [research.md](./research.md)

## Entidad nueva: `Informe` (`informes/models.py`)

| Campo | Tipo | Reglas |
|---|---|---|
| `numero` | `PositiveIntegerField(unique=True, editable=False)` | Correlativo desde 1 (máximo + 1 bajo advisory lock, R5). Se muestra `INF-` + 6 dígitos. |
| `estudio` | `OneToOneField(Estudio, on_delete=PROTECT, related_name="informe", editable=False)` | Un informe por estudio (FR-012). |
| `emitido_por` | `ForeignKey(AUTH_USER_MODEL, on_delete=PROTECT, related_name="informes_emitidos", editable=False)` | Usuario con el permiso. |
| `fecha_emision` | `DateTimeField(auto_now_add=True)` | |
| `contenido` | `JSONField(editable=False)` | Copia de todo lo mostrado (ver abajo). |

- `Meta.permissions = [("emitir_informes", "Puede emitir informes")]`; `ordering = ("-numero",)`;
  `verbose_name = "informe"`, `verbose_name_plural = "informes"`.
- `CheckConstraint(numero >= 1, name="informe_numero_positivo")`.
- Propiedad `numero_mostrado` → `f"INF-{numero:06d}"`.
- No se edita ni se borra (la inalterabilidad completa es de la US 7.3; acá no hay pantalla ni admin
  que lo modifique).

### Estructura de `contenido` (todo texto, ningún `float`)

```text
{
  "laboratorio": {nombre, direccion, matricula, responsable_tecnico, logo},   # logo: referencia ("aqualab" o ruta en static/)
  "cliente":     {nombre_completo, tipo_documento, numero_documento, domicilio, email},
  "muestra":     {numero_pi, nombre, origen, fecha_muestreo, fecha_ingreso, sitio_extraccion,
                  responsable_muestreo, tipo_vertido},          # fechas "dd/mm/aaaa", vertido con su etiqueta
  "estudio":     {numero, tipo},                                 # tipo = tipo_nombre_snapshot
  "pruebas": [
    {codigo, nombre, unidad, resultado, resultado_texto, limite_texto, limite_min, limite_max,
     norma, origen_limites, limite_deteccion, evaluacion, evaluacion_texto}
  ]
}
```

- `resultado`: `str(Resultado.valor)` exacto; `resultado_texto`: lo que se muestra (R3).
- `evaluacion`: `cumple` / `fuera_de_norma` / `sin_limite` de la `Validacion` vigente.
- Campos opcionales vacíos se guardan `""` y se muestran «—».

## Cambio en una estructura existente: `LimitesAplicables` (`pruebas/limites.py`)

- Suma `deteccion: str = ""` (texto del catálogo). `limites_aplicables` la completa con
  `prueba.limite_deteccion`.
- `evaluar`: con límite «Ausente»/«Ausencia», cumple si `valor == 0` o `valor < deteccion`
  (detección numérica) — FR-016. El resto de las reglas no cambia.

## Migraciones

- `informes/migrations/0001_initial.py`: modelo `Informe` y su permiso.
- `informes/migrations/0002_permiso_bioquimicos.py`: datos. `create_permissions` para `informes`,
  `Group.get_or_create("Bioquímicos")` y le agrega `emitir_informes`. Depende de
  `estudios.0008_grupo_bioquimicos` y de `informes.0001`. Reversa: quita el permiso del grupo.

## Transiciones de estado

| Entidad | Desde | Hacia | Cuándo |
|---|---|---|---|
| Estudio | Finalizado (todas Completadas) | **Informe generado** | Al emitir (misma transacción que crea el `Informe`) |
| Informe | — | Emitido | Al confirmar «Emitir informe» con el permiso y el estudio listo |

Con «Informe generado», `Estudio.admite_correcciones` es falso: no se corrigen ni borran mediciones
(US 6.3/6.5), así que la validación ya no puede anularse.
