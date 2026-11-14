# Contrato de interfaz: Curvas de calibración

## Carga y borrado (panel de administración)

Acceso: `administracion_requerida` (grupo «Administradores» + permiso del panel); sin permiso → 403;
sin sesión → login. Los servicios revalidan el permiso.

| Método | URL | Nombre | Resultado |
|---|---|---|---|
| GET | `/administracion/pruebas/<pk>/` | `catalogo:ficha` | (existente) + sección «Curvas de calibración»: vigente (fecha, R², puntos), «Nueva curva», «Ver curvas» |
| GET/POST | `/administracion/pruebas/<pk>/curvas/nueva/` | `catalogo:nueva_curva` | Formulario con `accion`: `agregar_fila`, `quitar_<n>`, `importar`, `elegir_columnas`, `calcular`, `guardar` (→ 302 a confirmar) |
| GET/POST | `/administracion/pruebas/<pk>/curvas/confirmar/` | `catalogo:confirmar_curva` | GET: resumen del borrador (`?t=<token>`); POST `confirmar` → `guardar_curva` → ficha; POST `cancelar` → formulario con los puntos |
| GET | `/administracion/pruebas/curvas/plantilla.csv` | `catalogo:plantilla_curva` | CSV de ejemplo (R8) |
| GET/POST | `/administracion/pruebas/curvas/<curva>/borrar/` | `catalogo:borrar_curva` | GET: confirmación (o 302 a la consulta con el motivo si está usada); POST → `borrar_curva` |

Una prueba que no es por curva → 302 a la ficha con «Esta prueba no se calcula con curva de calibración.»

## Consulta (cualquier empleado con sesión, solo lectura, `require_GET`)

| URL | Nombre | Contenido |
|---|---|---|
| `/pruebas/<pk>/curvas/` | `curvas:listar` | Prueba, vigente destacada (o «Sin curva vigente») e históricas: fecha de preparación, R², cargada por y cuándo, «Usada en resultados» |
| `/pruebas/curvas/<curva>/` | `curvas:detalle` | Puntos, pendiente, ordenada, R² (con aviso si < 0,995), gráfico, rango, observación, archivo de origen, estado; «Borrar curva» solo con permiso y sin usar |

## Formulario de carga

- Campos: «Fecha de preparación» (ayuda: «Día en que se prepararon los estándares.»),
  «Observación» (opcional), tabla «Puntos de los estándares» (Concentración [<unidad>] · Absorbancia
  [Abs] · Quitar), botón «Agregar fila», «Archivo (.csv o .xlsx)» + «Importar puntos»,
  enlace «Descargar plantilla», «Calcular recta» y «Guardar» (solo después de calcular sin errores).
- Al calcular: «Pendiente: …», «Ordenada al origen: …», «R²: …» y el gráfico. Con R² < 0,995:
  aviso «R² menor que 0,995: revisá los puntos antes de guardar».
- Importación con columnas dudosas: pantalla «Elegí las columnas» con una vista previa de 5 filas y
  dos selectores («Concentración», «Absorbancia»).

## Mensajes

- Puntos: «Hacen falta al menos 3 puntos.», «Falta la concentración.», «Falta la absorbancia.»,
  «No puede ser negativa.», «Las concentraciones son todas iguales: no se puede calcular la recta.»,
  «Las absorbancias son todas iguales: la recta no permite convertir absorbancia en concentración.»
- Fecha: «La fecha de preparación no puede ser posterior a hoy.»
- Archivo: «Solo se aceptan archivos .csv o .xlsx.», «El archivo supera 1 MB.», «No se pudo leer el
  archivo.», «El archivo está vacío.», «La fila N no tiene absorbancia.», «La fila N no tiene
  concentración.», «La fila N tiene un valor inválido: …», «El archivo trae N puntos válidos: hacen
  falta al menos 3.», «Elegí dos columnas distintas.». Con error, la tabla queda como estaba.
- Importación correcta: «Se leyeron N puntos de <archivo>. Revisalos antes de calcular.»
- Resumen: prueba, fecha, cantidad de puntos, rango de concentraciones, pendiente, ordenada, R²
  (+ aviso), observación, «Archivo: <nombre>» si se importó, «La curva vigente del <fecha> pasa a
  histórica» si había, y si hay pendientes: «N mediciones en M estudios esperan curva» + casilla
  «Calcularlas con esta curva».
- Éxito: «Curva guardada: es la vigente de <prueba>.» (+ « Se calcularon N resultados.»).
  Borrado: «Curva borrada.» (+ « Volvió a quedar vigente la del <fecha>.» o « La prueba quedó sin
  curva vigente.»). Usada: «Esta curva ya se usó en resultados: no se puede borrar.»
- Borrador vencido o alterado: «La confirmación venció o no es válida. Volvé a cargar la curva.»

## Estudio (cambios)

- Detalle del estudio (`estudios:detalle`), columna «Resultado» de una prueba por curva:
  «Curva del <dd/mm/aaaa> · R² <0,9996>» enlazado a `curvas:detalle`; si corresponde, el aviso
  «Fuera del rango de la curva (<mín>–<máx> <unidad>)». Sin curva: «Falta curva de calibración.»
- Validar resultados: el mismo aviso de fuera de rango junto al resultado; no bloquea.
