# Contrato UI: Comparación histórica (SCRUM-60, US 8.1)

## `GET /estudios/comparacion/` — `estudios:comparacion`

Acceso: sesión + `informes.ver_dashboard` (sin permiso → 403). Solo `GET` (otro método → 405).

| Parámetro | Obligatorio | Efecto |
|---|---|---|
| `estudio` | uno de `estudio` u `origen` | estudio de referencia; el origen es el de su muestra. Inexistente → 404 |
| `cliente`, `origen` | sin `estudio` | `ElegirOrigenForm`; inválido/incompleto → solo el selector, con errores |
| `pruebas` | no, repetible | códigos a mostrar; los desconocidos se ignoran |
| `elegir` | no | `1` = el usuario aplicó la selección (sin él: todas) |

Respuestas:

- **Sin `estudio` ni `origen` válido**: encabezado «Comparación histórica», tarjeta con el selector
  (paso 1 o 2) y enlace «Volver al dashboard».
- **Con origen**: encabezado con cliente y origen; si hay estudio, ficha con N° PI, tipo, estado y
  «Volver al estudio».
  - Selector de pruebas: `<fieldset>` «Pruebas a mostrar» con casillas, botones «Todas» /
    «Ninguna» (solo con JS) y «Aplicar» (envía GET con `estudio`/`cliente`/`origen`, `pruebas`,
    `elegir=1`).
  - Por cada prueba elegida, una tarjeta `<section data-prueba="CODIGO">` con:
    - título «Nombre (CODIGO)» y unidad (`|unidad`);
    - franja: «Máximo 350 mg/l · Límite general» / «Sin límite comparable»;
    - variación (`estudios/variacion_historica.html`): «Contra el anterior (dd/mm/aaaa): ▲ +15 mg/l
      (+3,6 %)», «Contra el promedio de N anteriores (179,6 mg/l): ▲ +250,4 mg/l (+139,4 %)»; en
      presencia, «Cambió: Ausente → Presente» y «Presente en 1 de 6». Clase de peligro solo si el
      último está fuera de la franja, con el texto «Fuera de la franja del límite» (no solo color);
    - con historial: `<canvas id="grafico-CODIGO" role="img" aria-label="Evolución de …">` y
      `<details>` «Ver datos» con la tabla (Fecha de muestreo, N° PI, Resultado, Evaluación,
      Estado; fila del estudio actual marcada «Este estudio»; filas con otra unidad con aviso);
    - sin historial: valor actual o «Sin resultado en este estudio» + «Sin historial para
      comparar» (`ui/estado_vacio.html`).
  - Origen sin validados y sin referencia: «Este origen todavía no tiene resultados validados» +
    «Volver al dashboard».
  - Selección vacía con `elegir=1`: error del formulario y ninguna tarjeta.
- `{{ datos|json_script:"datos-comparacion" }}`, `static/vendor/chart.umd.min.js` y
  `estudios/comparacion.js` con `defer`.

### `datos-comparacion` (JSON)

```json
{
  "pruebas": [
    {
      "codigo": "CL-",
      "nombre": "Cloruro",
      "unidad": "mg/l",
      "presencia": false,
      "franja": {"min": null, "max": "350", "comparable": true},
      "puntos": [
        {"etiqueta": "10/05/2026 · PI 200004", "valor": "118.0000000000", "texto": "118",
         "validado": true, "referencia": false},
        {"etiqueta": "10/11/2026 · PI 200061", "valor": "430.0000000000", "texto": "430",
         "validado": false, "referencia": true}
      ]
    }
  ]
}
```

Valores como texto (sin `float` en el servidor); el JS los pasa a `Number` solo para dibujar.
Los puntos con `otra_unidad` no van en el JSON.

## Detalle del estudio — `estudios:detalle`

Botón secundario «Comparación histórica» en la barra de acciones, solo con
`perms.informes.ver_dashboard`, → `estudios:comparacion?estudio=<pk>`.

## Dashboard — `informes:dashboard`

Tarjeta «Comparación histórica» con `ElegirOrigenForm` (GET a `estudios:comparacion`), botón
«Ver evolución», y `json_script` `origenes-por-cliente` (`{cliente_pk: [[origen_pk, nombre], …]}`)
que usa `estudios/elegir_origen.js`. Sin JS el `<select>` de orígenes muestra todos agrupados por
cliente (`<optgroup>`), y un origen de otro cliente da el error del formulario.

## Lo que NO cambia

`informes/documento.html`, `informes/impreso.html`, `informes/correos/*`, el PDF y la impresión
no muestran nada de la comparación (FR-017).
