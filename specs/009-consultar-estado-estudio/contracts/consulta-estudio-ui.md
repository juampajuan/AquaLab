# Contrato UI: Consulta de estado del estudio y ficha de la muestra

**Feature**: `009-consultar-estado-estudio` | **Plan**: [../plan.md](../plan.md)

Pantallas renderizadas en el servidor (templates de Django + Bootstrap 5.3) que extienden `base.html`. Requieren sesión activa de empleado (`LoginRequiredMiddleware`; sin sesión → **302** a `settings.LOGIN_URL`).

## Rutas

| Nombre de URL | Método | Ruta | Resultado |
|---|---|---|---|
| `estudios:buscar` | GET | `/estudios/buscar/` | Sin `q`: formulario vacío, sin resultados. Con `q` válido: lista de estudios coincidentes (**200**). Con `q` inválido: **200** con error junto al campo, sin resultados |
| `estudios:buscar` | GET `?q=…&page=N` | `/estudios/buscar/` | Página `N` de los resultados (20 por página) |
| `estudios:detalle` | GET | `/estudios/<int:pk>/` | Detalle del estudio con su estado general y lista de pruebas asignadas (**200**). `pk` inexistente → **404** |
| `muestras:detalle` | GET | `/muestras/<int:pk>/` | Ficha de la muestra con todos sus datos vigentes y su lista de estudios asignados (**200**). `pk` inexistente → **404** |

## 1. Pantalla — Buscar estudio (`estudios/buscar.html`)

Título: **"Buscar estudio"** (`{% block title %}Buscar estudio · AquaLab{% endblock %}`).

Formulario `method="get"` (sin `csrf_token`, operación de solo lectura):

| Campo (`name`) | Etiqueta | Widget | Reglas |
|---|---|---|---|
| `q` | `"Identificador, muestra (N° PI / nombre) o cliente"` | texto, `autofocus`, valor conservado | Obligatorio; acepta cualquier entero positivo (identificador o N° PI) o un texto de al menos 2 caracteres |

Botón **"Buscar"**. Texto de ayuda: *"Podés buscar por N° de estudio, N° PI o nombre de la muestra, o por nombre, razón social o DNI/CUIT del cliente."*

### Resultados

- Encabezado con la cantidad: *"N estudio(s) encontrado(s)"*.
- Tabla Bootstrap (`table table-hover align-middle`) con columnas:
  - **Estudio**: `#<id>`
  - **Muestra**: `N° PI <numero_pi>` y `nombre` (enlace a `muestras:detalle`)
  - **Cliente**: `nombre_completo` y `<tipo_documento> <numero_documento>`
  - **Tipo de estudio**: `tipo_nombre_snapshot`
  - **Fecha de creación**: `fecha_creacion` (`d/m/Y H:i`)
  - **Estado**: etiqueta (`get_estado_display`) con badge visual según el estado (`Pendiente de análisis`, `En proceso`, `Finalizado`, `Informe generado`)
  - **Acción**: botón/enlace **"Ver estudio"** a `estudios:detalle` (`pk`)
- Sin coincidencias: alerta `alert-info` *"No se encontraron estudios para «{q}»."*
- Más de 20 resultados: paginación Bootstrap (`pagination`) conservando `?q=…&page=N`.

## 2. Pantalla — Detalle del estudio (`estudios/detalle.html`)

Título: **"Estudio #{{ estudio.pk }}"** (`{% block title %}Estudio #{{ estudio.pk }} · AquaLab{% endblock %}`).

### Cabecera del estudio

- **Identificador**: `Estudio #<pk>`
- **Estado general**: `estudio.get_estado_display` (badge destacado)
- **Tipo de estudio**: `estudio.tipo_nombre_snapshot` y, si no está vacía, `estudio.tipo_descripcion_snapshot`
- **Muestra**: `N° PI <numero_pi> – <nombre>` (enlace a `muestras:detalle`) y **Origen**: `<origen.nombre>`
- **Cliente**: `<nombre_completo>` (`<tipo_documento> <numero_documento>`, enlace a `clientes:detalle` si el cliente está activo)
- **Creado por**: nombre completo o email de `creado_por`
- **Fecha de creación**: `fecha_creacion` (`d/m/Y H:i`)

### Avance y lista de pruebas asignadas

- Resumen numérico de avance: total de pruebas asignadas, cuántas están **Completadas**, cuántas **Cargadas** y cuántas **Pendientes**.
- Tabla Bootstrap con todas las filas de `pruebas_asignadas` ordenadas por `prueba.codigo`:
  - **Código**: `asignacion.prueba.codigo`
  - **Prueba**: `asignacion.prueba.nombre`
  - **Estado individual**: `asignacion.get_estado_display` (`Pendiente`, `Cargada` o `Completada`)

### Acciones de navegación

- Enlace **"Ver ficha de la muestra"** (`muestras:detalle`).
- Enlace **"Buscar estudios"** (`estudios:buscar`).

## 3. Pantalla — Ficha de la muestra (`muestras/detalle.html`)

Título: **"Muestra N° PI {{ muestra.numero_pi }}"** (`{% block title %}Muestra N° PI {{ muestra.numero_pi }} · AquaLab{% endblock %}`).

### Datos de la muestra

Tarjeta con todos los atributos vigentes de `Muestra`:
- **N° PI**: `muestra.numero_pi`
- **Nombre**: `muestra.nombre`
- **Estado**: `muestra.get_estado_display`
- **Cliente**: `muestra.cliente.nombre_completo` (`tipo_documento` `numero_documento` y `email`, con enlace a `clientes:detalle` si está activo)
- **Origen**: `muestra.origen.nombre`
- **Sitio de extracción**: `muestra.sitio_extraccion`
- **Tipo de vertido**: `muestra.get_tipo_vertido_display`
- **Fecha de muestreo** y **Fecha de ingreso** (`d/m/Y`)
- **Responsable del muestreo**: `muestra.responsable_muestreo` (o `"No especificado"` si está vacío)
- **Registrada por** y **Fecha de registro** (`d/m/Y H:i`)

### Sección — Estudios asignados

- Si la muestra tiene estudios asignados: tabla ordenada del más reciente al más antiguo (`-pk`) con columnas:
  - **Estudio**: `#<id>`
  - **Tipo de estudio**: `tipo_nombre_snapshot`
  - **Fecha de creación**: `fecha_creacion` (`d/m/Y H:i`)
  - **Estado general**: `get_estado_display`
  - **Pruebas completadas**: `<pruebas_completadas> / <total_pruebas>`
  - **Acción**: enlace **"Ver estudio"** a `estudios:detalle`
- Si la muestra no tiene estudios asignados: alerta `alert-info` *"Esta muestra aún no tiene estudios asignados."*
- Botón/enlace **"Crear estudio"** hacia `estudios:crear`.

## 4. Puntos de acceso en la interfaz

- `templates/base.html`: enlace **"Buscar estudio"** en la barra de navegación.
- `templates/inicio.html`: botón **"Buscar estudio"**.
