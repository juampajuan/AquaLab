# Data Model: Consultar historial del cliente

**Feature**: `023-historial-cliente` | **Plan**: [plan.md](./plan.md)

Esta historia **no crea ni modifica modelos ni migraciones**. Solo lee:

| Entidad | Modelo | Campos que se usan |
|---|---|---|
| Cliente | `clientes.Cliente` | `pk`, `activo`, `nombre_completo`, `tipo_documento`, `numero_documento` |
| Muestra | `muestras.Muestra` (`cliente` → `related_name="muestras"`) | `pk`, `numero_pi`, `fecha_ingreso`, `origen` |
| Origen | `muestras.Origen` | `nombre` |
| Estudio | `estudios.Estudio` (`muestra` → `related_name="estudios"`) | `pk` (número), `tipo_nombre_snapshot`, `estado` (`EstadoEstudio`) |
| Informe | `informes.Informe` (`estudio` → OneToOne, `related_name="informe"`) | `numero_mostrado` |

## Consulta: `clientes/historial.py`

```text
muestras_del_historial(cliente, desde=None, hasta=None, estado="") -> QuerySet[Muestra]
  Muestra.objects.filter(cliente=cliente)
    [+ fecha_ingreso__gte=desde] [+ fecha_ingreso__lte=hasta]
    [+ estudios__estado=estado, .distinct()]
    .select_related("origen")
    .prefetch_related(Prefetch(
        "estudios",
        queryset=Estudio.objects[.filter(estado=estado)].select_related("informe").order_by("-pk"),
        to_attr="estudios_historial"))
    .order_by("-fecha_ingreso", "-numero_pi")
```

- Cada muestra de la página trae `estudios_historial` (lista, posiblemente vacía sin filtro de
  estado; nunca vacía con filtro de estado).
- Con informe emitido, `estudio.informe` ya viene cargado (sin consulta extra).

## Formulario: `HistorialClienteForm` (GET)

| Campo | Tipo | Reglas |
|---|---|---|
| `desde` | `DateField`, opcional | `%Y-%m-%d` o `%d/%m/%Y`; widget `SelectorFecha` |
| `hasta` | `DateField`, opcional | ídem |
| `estado` | `ChoiceField`, opcional | `""` (Todos) + `EstadoEstudio.choices` |
| `clean()` | — | `desde > hasta` → error en `desde`: «La fecha desde no puede ser posterior a la fecha hasta.» |

Formulario no enviado o inválido → la consulta va sin filtros.

## Estados mostrados

Los de `EstadoEstudio` con la etiqueta de `config/ui.py:tipo_estado`: Pendiente de análisis,
En proceso, Finalizado, Informe generado. No hay transiciones: la historia no cambia estados.
