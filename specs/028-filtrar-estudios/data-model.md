# Data Model: Filtrar estudios por estado y fecha

**Feature**: `028-filtrar-estudios` | **Plan**: [plan.md](./plan.md)

Sin modelos, campos ni migraciones nuevas. La tarea solo lee datos existentes.

## Estudio (`estudios.Estudio`, US 5.1/5.2) — campos que se leen

| Campo | Tipo | Uso |
|---|---|---|
| `estado` | `CharField` con `EstadoEstudio` (`pendiente_analisis`, `en_proceso`, `finalizado`, `informe_generado`) | Filtro **Estado**: igualdad con el estado actual |
| `fecha_creacion` | `DateTimeField(auto_now_add=True)`, con zona (`USE_TZ`) | Filtros **Desde**/**Hasta**: días completos en `TIME_ZONE` ([research R2](./research.md#r2-rango-de-fechas-sobre-un-datetimefield)) |

El orden (`Meta.ordering = ("-pk",)`), las relaciones que se muestran (muestra, cliente, origen) y
la búsqueda por texto (`estudios/busqueda.py:filtro_busqueda`) no cambian.

## Formularios (sin persistencia)

| Formulario | Campos | Reglas |
|---|---|---|
| `estudios.forms.FiltrosEstudioForm` (nuevo, base) | `desde`, `hasta` (`DateField`, `AAAA-MM-DD` o `DD/MM/AAAA`, `SelectorFecha`), `estado` (`ChoiceField`: «Todos» + `EstadoEstudio.choices`), todos opcionales | `desde > hasta` → error en `desde`; fecha inválida → «Ingresá una fecha válida (dd/mm/aaaa).»; estado desconocido → «Elegí un estado de la lista.»; campos con error llevan `is-invalid` |
| `clientes.forms.HistorialClienteForm` (US 3.3) | hereda la base | solo cambia las etiquetas; comportamiento idéntico |
| `estudios.forms.FiltrarEstudiosForm` (nuevo) | `BuscarEstudioForm` (`q`) + la base | etiquetas «Desde», «Hasta», «Estado»; ayuda en `desde`/`hasta` |
