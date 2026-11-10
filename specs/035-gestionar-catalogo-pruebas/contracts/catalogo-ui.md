# Contrato de interfaz: Gestión del catálogo de pruebas

Acceso: grupo «Administradores» + permiso del panel (`administracion_requerida`); sin permiso → 403;
sin sesión → login.

| Método | URL | Nombre | Resultado |
|---|---|---|---|
| GET | `/administracion/pruebas/` | `administracion:pruebas` | Listado (existente) + «Nueva prueba», «Ver ficha», marca de dependencias |
| GET/POST | `/administracion/pruebas/nueva/` | `catalogo:nueva` | Formulario → resumen |
| GET | `/administracion/pruebas/<pk>/` | `catalogo:ficha` | Datos, uso, «Creada por… · Modificada por…», acciones |
| GET/POST | `/administracion/pruebas/<pk>/editar/` | `catalogo:editar` | Formulario → resumen |
| GET | `/administracion/pruebas/<pk>/desactivar/` | `catalogo:desactivar` | Resumen con avisos |
| GET | `/administracion/pruebas/<pk>/reactivar/` | `catalogo:reactivar` | Resumen |
| GET | `/administracion/pruebas/<pk>/eliminar/` | `catalogo:eliminar` | Resumen (o 302 a ficha con el motivo si no se puede) |
| POST | `/administracion/pruebas/confirmar/` | `catalogo:confirmar` | Ejecuta; «Cancelar» vuelve al formulario con los datos |

## Mensajes

- Éxito: «Prueba creada.», «Prueba actualizada.», «Prueba desactivada.», «Prueba reactivada.»,
  «Prueba eliminada.», «No hubo cambios.»
- Bloqueo en uso (en la ficha y el formulario): «Esta prueba ya se usa en tipos de estudio o
  estudios: su método no se puede cambiar. Para cambiarlo, creá una prueba nueva y desactivá esta.»
- Referenciada: «La usan en su fórmula: <códigos>. No se puede eliminar ni cambiar su código.»
- Aviso al desactivar (fórmulas): «La usan en su fórmula: <códigos>. En los estudios nuevos no se van
  a poder calcular hasta que la reemplacen.»
- Aviso al desactivar (tipos): «Los estudios nuevos de estos tipos no la van a incluir: <tipos>.»;
  junto a cada tipo sin otra prueba activa: «Este tipo no se va a poder usar».
- Aviso al reactivar: «Usa en su fórmula una prueba inactiva: <códigos>.»
- Listado: «Depende de una prueba inactiva: <códigos>».
- Concurrencia: «La prueba cambió mientras la editabas. Revisá los datos actuales.»
- Límites: «Escribí un número o “Ausente”.», «El mínimo no puede superar al máximo.»
- Código: «Ya existe una prueba con ese código.»
- Crear estudio con tipo sin activas: «El tipo de estudio no tiene pruebas activas.»

## Formulario

Secciones: Identificación (código, nombre) · Cálculo (tipo, fórmula, unidad de medición, unidad del
resultado) · Límites (generales mín/máx, norma, límite de detección; Cloacal y Canal mín/máx/norma)
· Observación. Ayuda (US 9.1) en fórmula (`x` y `{CODIGO}`), límites («Ausente» vs máx. 0) y límite
de detección.
