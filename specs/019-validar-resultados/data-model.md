# Data Model: Validar resultados

**Feature**: `019-validar-resultados` | **Plan**: [plan.md](./plan.md) | **Research**: [research.md](./research.md)

## Entidad nueva: `Validacion` (`estudios/models.py`)

Registro de que un bioquímico confirmó el resultado de una prueba del estudio. Existe si y solo
si la prueba está Completada (research R2).

| Campo | Tipo | Reglas |
|---|---|---|
| `asignacion` | `OneToOneField(PruebaEstudio, on_delete=PROTECT, related_name="validacion", editable=False)` | Una por prueba del estudio. |
| `validada_por` | `ForeignKey(AUTH_USER_MODEL, on_delete=PROTECT, related_name="validaciones", editable=False)` | Usuario de la sesión con el permiso. |
| `fecha_validacion` | `DateTimeField(auto_now_add=True)` | |
| `limite_min` | `CharField(50, blank=True, default="")` | Texto tal como estaba en el catálogo al validar. |
| `limite_max` | `CharField(50, blank=True, default="")` | Ídem. |
| `norma` | `CharField(150, blank=True, default="")` | Ídem. |
| `origen_limites` | `CharField(10, choices=OrigenLimites)` | `general`, `cloacal` o `canal`. |
| `evaluacion` | `CharField(20, choices=Evaluacion)` | `cumple`, `fuera_de_norma` o `sin_limite`. |

- `Meta.permissions = [("validar_resultados", "Puede validar resultados")]`.
- `verbose_name = "validación"`, `verbose_name_plural = "validaciones"`.
- No guarda el valor del resultado: mientras la validación existe, el resultado no puede cambiar
  (cualquier recálculo la borra, R2).

### Choices

- `Evaluacion` (`pruebas/limites.py`, R3): `CUMPLE = "cumple", "Cumple"`,
  `FUERA_DE_NORMA = "fuera_de_norma", "Fuera de norma"`,
  `SIN_LIMITE = "sin_limite", "Sin límite comparable"`.
- `OrigenLimites` (`estudios/models.py`): `GENERAL = "general", "Generales"`,
  `CLOACAL = "cloacal", "Cloacal"`, `CANAL = "canal", "Canal"`.

## Migraciones

- `estudios/migrations/0007_validacion.py`: crea `Validacion` y su permiso.
- `estudios/migrations/0008_grupo_bioquimicos.py`: datos. Crea los permisos de `estudios`
  (`create_permissions`), el grupo «Bioquímicos» y le asigna `validar_resultados`. Reversa: quita
  el permiso y borra el grupo solo si quedó vacío. Depende de `auth` y de `0007`.

## Entidades existentes que se usan

| Entidad | Uso en esta historia |
|---|---|
| `PruebaEstudio` | Cargada con resultado → Completada al validar. Sin campos nuevos. |
| `Resultado` (US 6.2) | Valor comparado con los límites. No cambia al validar. |
| `Estudio` | Pasa a Finalizado cuando todas sus pruebas están Completadas. `admite_correcciones` (sin informe emitido) habilita la validación. |
| `Muestra.tipo_vertido` | Elige los límites: Agua → generales; Cloacal/Canal → los del vertido si existen. |
| `Prueba` (SCRUM-64) | `limite_min`, `limite_max`, `norma`: límites generales como texto. |
| `LimiteVertido` (SCRUM-64) | `limite_min`, `limite_max`, `norma` por `tipo_vertido` (Cloacal/Canal). |
| `auth.Group` | Grupo «Bioquímicos». |

## Transiciones de estado

### Prueba del estudio

| Desde | Hacia | Cuándo | Historia |
|---|---|---|---|
| Cargada (con resultado) | **Completada** | Se valida | **US 6.4** (crea `Validacion`) |
| Completada | Cargada | Su resultado se recalcula | US 6.2/6.3 (borra `Validacion`, R2) |
| Completada | Pendiente / Cargada sin resultado | Se borra su medición o la de una referencia | US 6.5 (borra `Validacion`, R2) |

### Estudio

| Desde | Hacia | Cuándo | Historia |
|---|---|---|---|
| En proceso | **Finalizado** | Tras validar, todas sus pruebas están Completadas | **US 6.4** |
| Finalizado | En proceso / Pendiente de análisis | Alguna prueba deja de estar Completada | US 6.3/6.5 (sin cambios) |
| Cualquiera menos Informe generado | — | Con informe emitido no se valida | US 6.4 (rechazo) |

## Reglas de evaluación (FR-007)

| Límites aplicables | Evaluación |
|---|---|
| Ambos vacíos | Sin límite comparable |
| Alguno no comparable («SOE», «NE», «Ph-0,2», «Ph+0,2»…) | Sin límite comparable |
| Máximo «Ausente»/«Ausencia» | Cumple si el resultado es 0; si no, fuera de norma |
| Numéricos | Cumple si `mínimo ≤ resultado ≤ máximo` (con los que haya); si no, fuera de norma |

Casos reales del catálogo usados en los tests: pH general 6.4 / 8.5 y Cloacal 7.01 / 10.0;
Cloruro máx. 350.0; E. coli máx. «Ausente» (A/P, 0/1); Sólidos sedimentables y Coliformes fecales
máx. «Ausente»/«Ausencia»; Coliformes fecales Canal máx. 2000 (sin mínimo); Olor máx. «SOE»;
Cloro libre Cloacal máx. «NE» y general sin límites.
