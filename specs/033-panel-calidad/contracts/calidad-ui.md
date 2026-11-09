# Contrato de interfaz: sección «Calidad» del Dashboard

## Ruta

Sin rutas nuevas. Va dentro de `GET /informes/dashboard/?periodo=<clave>` (`informes:dashboard`),
con el mismo acceso: sesión + `informes.ver_dashboard`; sin permiso → 403; sin sesión → login.

## Ubicación

Entre «Actividad semanal» y «Comparación histórica». Parcial `informes/calidad.html`, sección con
`data-calidad` y `aria-labelledby="titulo-calidad"`.

## Contenido (de arriba hacia abajo)

1. **Encabezado**: «Calidad» + ayuda (`ui/ayuda.html`, id `ayuda-calidad`): «Resultados con
   validación vigente en el período, según la evaluación guardada al validar. Los que no tienen
   límite comparable no se cuentan.» Subtítulo con el rango del período (el mismo texto de la 8.3).
2. **Indicador** (`data-indicador="calidad"`): «10,0 % fuera de norma», debajo «4 de 40 resultados»
   y la variación con `informes/variacion.html` («▲ +5,0 p. p.», `data-tono`). Sin evaluados en el
   anterior: «Sin datos previos». Si hay `sin_limite`: «3 resultados sin límite comparable, fuera
   del cálculo» (`data-sin-limite`). Sin evaluados: «Sin resultados validados en el período» y el
   resto de la sección con `ui/estado_vacio.html` y el mismo texto.
3. **Pruebas que más fallan** (`data-ranking="pruebas"`): «Solo pruebas con al menos
   {{ minimo_ranking }} resultados evaluados». `<canvas id="grafico-calidad-pruebas" role="img"
   aria-label="Porcentaje de incumplimiento por prueba">` + `<details>` «Ver datos»: tabla Prueba
   (código · nombre) / Incumplimiento («25,0 % (2 de 8)»). «Y N pruebas más» si `restantes`. Vacío:
   «Ninguna prueba con al menos 5 resultados evaluados tuvo incumplimientos en el período.»
4. **Cumplimiento por tipo de vertido** (`data-vertidos`): `<canvas id="grafico-calidad-vertidos"
   role="img" aria-label="Resultados que cumplen y fuera de norma por tipo de vertido">` + tabla
   Tipo / Evaluados / Cumple / Fuera de norma / Cumplimiento (siempre Agua, Cloacal, Canal;
   «Sin resultados» con 0).
5. **Clientes con más incumplimientos** (`data-ranking="clientes"`) y **Orígenes con más
   incumplimientos** (`data-ranking="origenes"`), lado a lado: tabla Cliente (u Origen · Cliente) /
   Fuera de norma («3 de 12 · 25,0 %»). Enlace en el nombre: `clientes:historial` /
   `estudios:comparacion?cliente=&origen=`; inactivo: badge «Inactivo» sin enlace. «Y N más» si
   `restantes`. Vacío: «No hubo resultados fuera de norma en el período.»

## Datos para los gráficos

En el `json_script` `datos-dashboard` existente:

```json
{
  "calidad_pruebas": {"etiquetas": ["ECOLI · E. coli", "CL- · Cloruro"], "porcentajes": ["25.0", "20.0"]},
  "calidad_vertidos": {"etiquetas": ["Agua", "Cloacal", "Canal"], "cumple": [36, 0, 0], "fuera": [4, 0, 0]}
}
```

`dashboard.js` dibuja los dos gráficos si existe su canvas; sin Chart.js o sin JavaScript quedan
las tablas.
