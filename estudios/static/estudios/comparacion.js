// Gráficos de la comparación histórica (US 8.1) con Chart.js local (static/vendor/chart.umd.min.js),
// con el patrón de informes/dashboard.js: lee el json_script "datos-comparacion". Sin Chart.js (o
// sin JavaScript) quedan los textos de la franja, la variación y las tablas «Ver datos».
// Las funciones puras quedan en window.AqualabComparacion para los tests de Node.
(function () {
  "use strict";

  // Banda alrededor de 0 que marca «Ausente» como permitido en las pruebas A/P.
  var BANDA_PRESENCIA = 0.25;

  function numero(texto) {
    return texto === null || texto === undefined ? null : Number(texto);
  }

  // Datasets de la franja del límite: dos líneas fijas sin puntos y el relleno entre ellas.
  // Con un solo borde, el relleno va hasta el borde del gráfico ("start" o "end").
  function franja(prueba, cantidad, color) {
    var f = prueba.franja || {};
    if (!f.comparable || cantidad === 0) {
      return [];
    }
    function linea(etiqueta, valor, relleno) {
      var datos = [];
      for (var i = 0; i < cantidad; i += 1) {
        datos.push(valor);
      }
      return {
        label: etiqueta,
        data: datos,
        borderColor: color,
        borderWidth: 1,
        borderDash: [4, 4],
        backgroundColor: color + "26",
        pointRadius: 0,
        pointHitRadius: 0,
        fill: relleno,
        franja: true,
      };
    }
    if (prueba.presencia) {
      return [
        linea("Límite (Ausente)", -BANDA_PRESENCIA, false),
        linea("Límite (Ausente)", BANDA_PRESENCIA, "-1"),
      ];
    }
    var minimo = numero(f.min);
    var maximo = numero(f.max);
    if (minimo !== null && maximo !== null) {
      return [linea("Límite mínimo", minimo, false), linea("Límite máximo", maximo, "-1")];
    }
    if (maximo !== null) {
      return [linea("Límite máximo", maximo, "start")];
    }
    if (minimo !== null) {
      return [linea("Límite mínimo", minimo, "end")];
    }
    return [];
  }

  // La línea de los validados (con null donde está el estudio actual) y el punto destacado.
  function datasets(prueba, colores) {
    var puntos = prueba.puntos;
    var referencia = null;
    var validados = puntos.map(function (p) {
      if (p.referencia) {
        referencia = p;
        return null;
      }
      return numero(p.valor);
    });
    var lista = [
      {
        label: "Validados",
        data: validados,
        borderColor: colores.linea,
        backgroundColor: colores.linea,
        spanGaps: true,
        tension: 0,
        pointRadius: 4,
      },
    ];
    if (referencia) {
      lista.push({
        label: "Este estudio (" + (referencia.validado ? "Validado" : "Sin validar") + ")",
        data: puntos.map(function (p) {
          return p.referencia ? numero(p.valor) : null;
        }),
        borderColor: colores.referencia,
        backgroundColor: colores.referencia,
        pointStyle: "rectRot",
        pointRadius: 8,
        pointHoverRadius: 10,
        showLine: false,
      });
    }
    return lista.concat(franja(prueba, puntos.length, colores.franja));
  }

  // Eje Y: en las pruebas A/P, solo las marcas «Ausente» (0) y «Presente» (1).
  function ejeY(prueba) {
    if (!prueba.presencia) {
      return { title: { display: true, text: prueba.unidad || "" } };
    }
    return {
      min: -0.5,
      max: 1.5,
      afterBuildTicks: function (eje) {
        eje.ticks = [{ value: 0 }, { value: 1 }];
      },
      ticks: {
        callback: function (valor) {
          return valor === 0 ? "Ausente" : valor === 1 ? "Presente" : "";
        },
      },
    };
  }

  // Texto del tooltip de un punto: valor con unidad y estado de validación.
  function textoPunto(prueba, punto) {
    var valor = punto.texto;
    if (!prueba.presencia && prueba.unidad && prueba.unidad !== "--") {
      valor += " " + prueba.unidad;
    }
    return valor + " · " + (punto.validado ? "Validado" : "Sin validar");
  }

  // Atajos «Todas» / «Ninguna» del selector de pruebas (sin JS quedan ocultos).
  function activarAtajos(raiz) {
    var botones = raiz.querySelectorAll("[data-atajo]");
    Array.prototype.forEach.call(botones, function (boton) {
      boton.hidden = false;
      boton.addEventListener("click", function () {
        var marcar = boton.getAttribute("data-atajo") === "todas";
        var grupo = boton.closest("fieldset") || raiz;
        Array.prototype.forEach.call(
          grupo.querySelectorAll('input[type="checkbox"]'),
          function (casilla) {
            casilla.checked = marcar;
          },
        );
      });
    });
  }

  function color(nombre, respaldo) {
    var valor = getComputedStyle(document.documentElement).getPropertyValue(nombre).trim();
    return valor || respaldo;
  }

  function dibujar() {
    activarAtajos(document);
    var nodo = document.getElementById("datos-comparacion");
    if (!nodo || typeof window.Chart === "undefined") {
      return;
    }
    var datos = JSON.parse(nodo.textContent);
    var colores = {
      linea: color("--color-marino", "#0f2744"),
      referencia: color("--color-cian", "#0ea5e9"),
      franja: color("--color-exito", "#15803d"),
    };
    window.Chart.defaults.font.family = "Inter, ui-sans-serif, system-ui, sans-serif";
    window.Chart.defaults.color = color("--color-tinta-suave", "#475569");

    datos.pruebas.forEach(function (prueba) {
      var lienzo = document.getElementById("grafico-" + prueba.codigo);
      if (!lienzo) {
        return;
      }
      new window.Chart(lienzo, {
        type: "line",
        data: {
          labels: prueba.puntos.map(function (p) {
            return p.etiqueta;
          }),
          datasets: datasets(prueba, colores),
        },
        options: {
          maintainAspectRatio: false,
          scales: { y: ejeY(prueba) },
          plugins: {
            legend: {
              labels: {
                filter: function (item, datos) {
                  var ds = datos.datasets[item.datasetIndex];
                  // De la franja con dos bordes se muestra una sola entrada.
                  return !(ds.franja && ds.fill === false && prueba.franja.min !== null);
                },
              },
            },
            tooltip: {
              filter: function (item) {
                return !item.dataset.franja && item.raw !== null;
              },
              callbacks: {
                label: function (item) {
                  return textoPunto(prueba, prueba.puntos[item.dataIndex]);
                },
              },
            },
          },
        },
      });
    });
  }

  window.AqualabComparacion = {
    datasets: datasets,
    franja: franja,
    ejeY: ejeY,
    textoPunto: textoPunto,
    activarAtajos: activarAtajos,
  };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", dibujar);
  } else {
    dibujar();
  }
})();
