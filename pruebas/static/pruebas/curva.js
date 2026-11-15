// Gráfico de una curva de calibración (US 6.6) con Chart.js local (static/vendor/chart.umd.min.js):
// lee el json_script "datos-curva" ({puntos: [{concentracion, absorbancia}], recta: {desde, hasta},
// unidad}) y dibuja los estándares y la recta. Los extremos de la recta los calcula el servidor en
// Decimal; acá solo se dibujan. Sin Chart.js (o sin JavaScript) queda la tabla de puntos.
// Las funciones puras quedan en window.AqualabCurva para los tests de Node.
(function () {
  "use strict";

  function punto(concentracion, absorbancia) {
    return { x: Number(concentracion), y: Number(absorbancia) };
  }

  // Los dos extremos de la recta, en el orden de las concentraciones.
  function extremos(datos) {
    if (!datos.recta) {
      return [];
    }
    return [
      punto(datos.recta.desde.concentracion, datos.recta.desde.absorbancia),
      punto(datos.recta.hasta.concentracion, datos.recta.hasta.absorbancia),
    ];
  }

  function datasets(datos, colores) {
    var series = [
      {
        type: "scatter",
        label: "Estándares",
        data: datos.puntos.map(function (p) {
          return punto(p.concentracion, p.absorbancia);
        }),
        backgroundColor: colores.puntos,
        borderColor: colores.puntos,
        pointRadius: 4,
      },
    ];
    var recta = extremos(datos);
    if (recta.length) {
      series.push({
        type: "line",
        label: "Recta",
        data: recta,
        borderColor: colores.recta,
        borderWidth: 2,
        pointRadius: 0,
        fill: false,
      });
    }
    return series;
  }

  function color(nombre, respaldo) {
    var valor = getComputedStyle(document.documentElement).getPropertyValue(nombre).trim();
    return valor || respaldo;
  }

  function dibujar() {
    var nodo = document.getElementById("datos-curva");
    var lienzo = document.getElementById("grafico-curva");
    if (!nodo || !lienzo || typeof window.Chart === "undefined") {
      return;
    }
    var datos = JSON.parse(nodo.textContent);
    var colores = {
      puntos: color("--color-marino", "#0f2744"),
      recta: color("--color-cian", "#0ea5e9"),
    };
    window.Chart.defaults.font.family = "Inter, ui-sans-serif, system-ui, sans-serif";
    window.Chart.defaults.color = color("--color-tinta-suave", "#475569");
    new window.Chart(lienzo, {
      type: "scatter",
      data: { datasets: datasets(datos, colores) },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          x: { type: "linear", title: { display: true, text: "Concentración (" + datos.unidad + ")" } },
          y: { title: { display: true, text: "Absorbancia" } },
        },
      },
    });
  }

  window.AqualabCurva = { datasets: datasets, extremos: extremos };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", dibujar);
  } else {
    dibujar();
  }
})();
