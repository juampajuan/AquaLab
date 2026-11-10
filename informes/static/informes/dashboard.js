// Gráficos del dashboard (US 8.3 y 8.4) con Chart.js local (static/vendor/chart.umd.min.js).
// Lee los datos del json_script "datos-dashboard". Sin Chart.js (o sin JavaScript) quedan las
// tablas «Ver datos», que muestran lo mismo.
(function () {
  "use strict";

  function color(nombre, respaldo) {
    var valor = getComputedStyle(document.documentElement).getPropertyValue(nombre).trim();
    return valor || respaldo;
  }

  function dibujar() {
    var nodo = document.getElementById("datos-dashboard");
    if (!nodo || typeof window.Chart === "undefined") {
      return;
    }
    var datos = JSON.parse(nodo.textContent);
    var marino = color("--color-marino", "#0f2744");
    var cian = color("--color-cian", "#0ea5e9");
    var turquesa = color("--color-turquesa", "#14b8a6");
    var tinta = color("--color-tinta-suave", "#475569");
    window.Chart.defaults.font.family = "Inter, ui-sans-serif, system-ui, sans-serif";
    window.Chart.defaults.color = tinta;

    var respuesta = document.getElementById("grafico-respuesta");
    if (respuesta) {
      new window.Chart(respuesta, {
        type: "line",
        data: {
          labels: datos.respuesta.etiquetas,
          datasets: [
            {
              label: "Días promedio",
              // Los días llegan como texto ("11.5"); null deja el mes sin punto.
              data: datos.respuesta.dias.map(function (d) {
                return d === null ? null : Number(d);
              }),
              borderColor: marino,
              backgroundColor: marino,
              spanGaps: false,
              tension: 0,
            },
          ],
        },
        options: {
          maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: { y: { beginAtZero: true, title: { display: true, text: "Días" } } },
        },
      });
    }

    var actividad = document.getElementById("grafico-actividad");
    if (actividad) {
      new window.Chart(actividad, {
        type: "bar",
        data: {
          labels: datos.actividad.etiquetas,
          datasets: [
            { label: "Muestras ingresadas", data: datos.actividad.muestras, backgroundColor: cian },
            { label: "Informes emitidos", data: datos.actividad.informes, backgroundColor: turquesa },
          ],
        },
        options: {
          maintainAspectRatio: false,
          scales: { y: { beginAtZero: true, ticks: { precision: 0 } } },
        },
      });
    }

    // Calidad (US 8.4): pruebas que más fallan, en % fuera de norma.
    var calidadPruebas = document.getElementById("grafico-calidad-pruebas");
    if (calidadPruebas && datos.calidad_pruebas) {
      new window.Chart(calidadPruebas, {
        type: "bar",
        data: {
          labels: datos.calidad_pruebas.etiquetas,
          datasets: [
            {
              label: "% fuera de norma",
              // Los porcentajes llegan como texto ("20.0").
              data: datos.calidad_pruebas.porcentajes.map(Number),
              backgroundColor: color("--color-peligro", "#dc2626"),
            },
          ],
        },
        options: {
          indexAxis: "y",
          maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: {
            x: { min: 0, max: 100, title: { display: true, text: "% fuera de norma" } },
          },
        },
      });
    }

    // Calidad (US 8.4): pruebas que cumplen y fuera de norma por tipo de vertido.
    var calidadVertidos = document.getElementById("grafico-calidad-vertidos");
    if (calidadVertidos && datos.calidad_vertidos) {
      new window.Chart(calidadVertidos, {
        type: "bar",
        data: {
          labels: datos.calidad_vertidos.etiquetas,
          datasets: [
            {
              label: "Pruebas que cumplen",
              data: datos.calidad_vertidos.cumple,
              backgroundColor: color("--color-exito", "#16a34a"),
            },
            {
              label: "Pruebas fuera de norma",
              data: datos.calidad_vertidos.fuera,
              backgroundColor: color("--color-peligro", "#dc2626"),
            },
          ],
        },
        options: {
          maintainAspectRatio: false,
          scales: {
            x: { stacked: true },
            y: { stacked: true, beginAtZero: true, ticks: { precision: 0 } },
          },
        },
      });
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", dibujar);
  } else {
    dibujar();
  }
})();
