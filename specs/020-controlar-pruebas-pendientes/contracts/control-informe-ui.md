# Contrato de interfaz: Seleccionar estudio y controlar pruebas pendientes

**Feature**: `020-controlar-pruebas-pendientes` | **Plan**: [plan.md](../plan.md)

Todas las rutas requieren sesión (`LoginRequiredMiddleware`). Prefijo `informes/` en `config/urls.py`.

## `GET /informes/` — `informes:listar`

- Parámetros: `q` (mismo `BuscarEstudioForm` y criterios que `estudios:buscar`), `listos=1`
  (solo listos para informar), `page`.
- Encabezado: sección «Informes», título «Seleccionar estudio a informar».
- Casilla «Solo listos para informar» que se conserva al buscar y paginar.
- Tabla: N° de estudio, N° PI, cliente, tipo de estudio, estado (`ui/estado.html`), avance
  «N de M pruebas completadas» y la acción «Seleccionar» → `informes:control`.
- Sin resultados: `ui/estado_vacio.html` con «No se encontraron estudios».
- Error del formulario (más de 100 caracteres): el mismo mensaje que `estudios:buscar`.

## `GET /informes/estudios/<pk>/` — `informes:control`

- 404 si el estudio no existe.
- Encabezado: «Controlar pruebas del estudio N», con enlace «Volver al listado» y «Ver detalle del
  estudio» (`estudios:detalle`).
- Ficha: N° PI, muestra, cliente, tipo de estudio (snapshot) y estado del estudio.
- Resumen: «N de M pruebas completadas».
- Tabla de **todas** las pruebas ordenadas por código: código, nombre, estado (`ui/estado.html`
  con `tipo_estado`) y, si bloquea, la etiqueta «Incompleta» (Pendiente) o «Sin validar» (Cargada).
- Aviso según `motivo_para_no_informar`:
  - listo: aviso de éxito «El estudio está listo para informar: todas sus pruebas están completadas.»;
  - con pruebas sin completar: aviso de advertencia con el motivo («Hay N pruebas sin completar.»);
  - con informe emitido: aviso informativo «El informe de este estudio ya fue generado.».
- Botón «Generar informe»:
  - listo: `<form method="post" action="{% url 'informes:generar' pk %}">` con CSRF y botón primario;
  - con pruebas sin completar o sin pruebas: `<button type="button" disabled aria-describedby="motivo-bloqueo">`;
  - con informe emitido: no se muestra.

## `POST /informes/estudios/<pk>/generar/` — `informes:generar`

- Solo POST (GET → 405). 404 si el estudio no existe.
- Llama a `informes.servicios.comprobar_generacion(pk)`:
  - `InformeNoDisponible(motivo)` → `messages.error(motivo)`;
  - `DatabaseError` → `messages.error("No se pudo verificar el estudio. Intentá nuevamente.")`;
  - pasa → `messages.info("La generación del informe estará disponible próximamente.")` (lo
    reemplaza US 7.2).
- Siempre redirige a `informes:control`.

## Cambios en pantallas existentes

- `templates/ui/menu.html`: sección «Informes» con «Seleccionar estudio» (activa en
  `informes:listar` e `informes:control`).
- `templates/inicio.html`: acceso rápido «Informes».
- `estudios/templates/estudios/detalle.html`: enlace «Controlar para informe» → `informes:control`.

## Servicio

```text
informes.servicios.motivo_para_no_informar(estudio, asignaciones) -> str | None
informes.servicios.comprobar_generacion(estudio_pk) -> Estudio   # bloquea; lanza InformeNoDisponible
informes.servicios.estudios_para_informar(q: str, solo_listos: bool) -> QuerySet[Estudio]
    # anotado con total_pruebas y pruebas_completadas
estudios.busqueda.filtro_busqueda(q: str) -> Q                     # extraído de estudios:buscar
```
