# Contrato UI: Búsqueda de cliente

**Feature**: `004-buscar-cliente` | **Plan**: [../plan.md](../plan.md)

Pantallas renderizadas en el servidor (templates de Django + Bootstrap 5.3) que extienden
`base.html`. Requieren sesión de empleado (`LoginRequiredMiddleware`; sin sesión → **302** a
`settings.LOGIN_URL`). Namespace `clientes`.

## Rutas

| Nombre de URL | Método | Ruta | Resultado |
|---|---|---|---|
| `clientes:buscar` | GET | `/clientes/buscar/` | Sin `q`: formulario vacío, sin resultados. Con `q` válido: lista de coincidencias (**200**). Con `q` inválido: **200** con error junto al campo, sin resultados |
| `clientes:buscar` | GET `?q=…&page=N` | `/clientes/buscar/` | Página `N` de los resultados; `page` fuera de rango → última página (comportamiento de `Paginator.get_page`) |
| `clientes:detalle` | GET | `/clientes/<int:pk>/` | Ficha del cliente activo (existente). `pk` inexistente → **404**. Cliente inactivo → mensaje `"El cliente no está disponible."` y **302** a `clientes:buscar` |

## Pantalla — Buscar cliente (`clientes/buscar.html`)

Título: **"Buscar cliente"** (`{% block title %}Buscar cliente · AquaLab{% endblock %}`).

Formulario `method="get"` (sin `csrf_token`, no modifica datos):

| Campo (`name`) | Etiqueta | Widget | Reglas |
|---|---|---|---|
| `q` | "Nombre, razón social o documento" | texto, `autofocus`, valor conservado | Obligatorio, mínimo 2 caracteres tras recortar espacios |

Botón **"Buscar"**. Texto de ayuda: *"Podés ingresar parte del nombre, de la razón social o del
DNI/CUIT (con o sin puntos y guiones)."*

### Resultados

- Encabezado con la cantidad: *"N cliente(s) encontrado(s)"*.
- Tabla Bootstrap (`table table-hover`) con columnas: **Cliente** (`nombre_completo`), **Documento**
  (`DNI 30123456`), **Correo electrónico**, y acción **"Ver ficha"** (enlace a `clientes:detalle`
  con el `pk`). Toda la fila identifica de forma inequívoca al cliente por tipo + número de documento.
- Sin coincidencias: alerta `alert-info` *"No se encontraron clientes para «{q}»."* y el formulario
  queda disponible para buscar de nuevo.
- Más de 20 resultados: paginación Bootstrap (`pagination`) con enlaces `?q=…&page=N`.

## Accesos

- `templates/base.html`: enlace **"Buscar cliente"** en la navbar (junto a "Registrar cliente").
- `templates/inicio.html`: botón **"Buscar cliente"**.
- `clientes/detalle.html`: enlace **"Volver a la búsqueda"** a `clientes:buscar`.
