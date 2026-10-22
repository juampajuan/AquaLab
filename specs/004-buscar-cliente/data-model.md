# Data Model: Buscar cliente registrado

**Feature**: `004-buscar-cliente` | **Plan**: [plan.md](./plan.md)

No se crean ni modifican modelos ni columnas. La feature **lee** `clientes.Cliente` (US 2.1).

## Entidad consultada: Cliente

| Campo | Uso en la búsqueda |
|---|---|
| `nombre` | Filtro `unaccent` + `icontains`; se muestra en el resultado |
| `razon_social` | Filtro `unaccent` + `icontains`; se muestra en el resultado |
| `numero_documento` | Filtro `contains` con el texto normalizado (solo dígitos); se muestra |
| `tipo_documento` | Solo se muestra (no se filtra) |
| `email` | Se muestra en el resultado |
| `telefono`, `domicilio` | Solo en la ficha (`clientes:detalle`) |
| `activo` | Se filtra siempre `activo=True` |
| `id` | Identifica al cliente seleccionado (URL de la ficha) y desempata el orden |

`nombre_completo` (propiedad) se usa como título de cada resultado.

## Consulta (no persistida)

```text
Cliente.objects.filter(activo=True)
  .filter( nombre ~ q  OR  razon_social ~ q  [OR numero_documento ∋ normalizar(q) si es solo dígitos] )
  .order_by(*Cliente._meta.ordering)      # razon_social, nombre, id
```

`~` = `unaccent` + `icontains`. Página de 20 resultados.

## Migración

`clientes/migrations/0002_unaccent.py`: `UnaccentExtension()` (`CREATE EXTENSION IF NOT EXISTS
unaccent`). No altera datos ni esquema de `clientes_cliente`.

## Reglas de validación del texto (en `BuscarClienteForm`)

- Se recortan espacios; vacío → "Ingresá un nombre, razón social o número de documento para buscar."
- Menos de 2 caracteres → "Ingresá al menos 2 caracteres para buscar."
