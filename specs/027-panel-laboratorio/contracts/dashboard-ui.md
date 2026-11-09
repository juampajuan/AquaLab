# Contrato de interfaz: Dashboard

## Ruta

| Método | URL | Nombre | Acceso |
|---|---|---|---|
| GET | `/informes/dashboard/?periodo=<clave>` | `informes:dashboard` | Sesión + `informes.ver_dashboard`; sin permiso → 403; sin sesión → login |

`periodo`: `este_mes` (por defecto, también si es inválido), `mes_anterior`, `ultimos_3`, `ultimos_6`.

## Menú

Enlace «Dashboard» con ícono `chart-column`, justo debajo de «Inicio», solo con
`perms.informes.ver_dashboard`; `aria-current="page"` en el panel.

## Pantalla (de arriba hacia abajo)

1. **Encabezado** (`ui/encabezado.html`): título «Dashboard», subtítulo «Indicadores del
   laboratorio», y selector de período (formulario GET con los 4 períodos; botón «Ver»).
   Texto del rango: «Del dd/mm/aaaa al dd/mm/aaaa · comparado con dd/mm/aaaa al dd/mm/aaaa».
2. **Indicadores** (4 tarjetas, `data-indicador`): «Muestras ingresadas», «Estudios creados»,
   «Informes emitidos», «Tiempo de respuesta» («N,N días» o «Sin informes en el período»). Debajo
   de cada valor, la variación: «▲ +5 (+12 %)», «▼ −2 (−8 %)», «= 0 (0 %)» o «▲ +3 (sin datos
   previos)», con clase `text-exito`, `text-peligro` o `text-tinta-suave` y `data-tono`.
3. **Estudios por estado**: los 4 estados con su cantidad (`ui/estado.html`).
4. **Tiempo de respuesta por mes** (últimos 6 meses): `<canvas id="grafico-respuesta" role="img"
   aria-label="Tiempo de respuesta promedio de los últimos 6 meses">` + `<details>` «Ver datos» con
   tabla Mes / Días promedio («—» sin informes).
5. **Actividad semanal** (últimas 12 semanas): `<canvas id="grafico-actividad" role="img"
   aria-label="Muestras ingresadas e informes emitidos por semana">` + tabla Semana del / Muestras /
   Informes.
6. **Alertas** (2 tarjetas): «Estudios sin avanzar (N)» y «Finalizados sin informe (N)». Tabla
   N° estudio / N° PI / Cliente / Estado / Días, con enlace «Ver estudio» a `estudios:detalle`;
   contenedor con altura máxima y desplazamiento (`data-alerta`). Vacía: «No hay estudios en esta
   situación.» (`ui/estado_vacio.html`).

Scripts: `static/vendor/chart.umd.min.js` y `informes/dashboard.js`, solo en esta página; datos en
`json_script` con id `datos-dashboard`.
