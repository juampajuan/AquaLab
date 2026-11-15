// Curvas de calibración (US 6.6): funciones puras de pruebas/static/pruebas/curva.js.
// Corre con `node --test pruebas/tests/js`; carga el archivo con un window simulado, sin Chart.js
// (así no dibuja) y sin DOM real.
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const fuente = fs.readFileSync(path.join(__dirname, "../../static/pruebas/curva.js"), "utf8");

function cargar() {
  const documento = {
    readyState: "complete",
    getElementById: () => null,
    documentElement: {},
  };
  const ventana = { document: documento };
  const contexto = vm.createContext({
    window: ventana,
    document: documento,
    getComputedStyle: () => ({ getPropertyValue: () => "" }),
  });
  vm.runInContext(fuente, contexto);
  return ventana.AqualabCurva;
}

const curva = cargar();
const plano = (valor) => JSON.parse(JSON.stringify(valor));
const COLORES = { puntos: "#0f2744", recta: "#0ea5e9" };

function datos(extra = {}) {
  return {
    unidad: "mg/l",
    puntos: [
      { concentracion: "0", absorbancia: "0.000" },
      { concentracion: "0.2", absorbancia: "0.101" },
      { concentracion: "0.4", absorbancia: "0.199" },
    ],
    recta: {
      desde: { concentracion: "0", absorbancia: "0.0012" },
      hasta: { concentracion: "0.4", absorbancia: "0.2008" },
    },
    ...extra,
  };
}

test("extremos: los dos puntos de la recta que manda el servidor", () => {
  assert.deepEqual(plano(curva.extremos(datos())), [
    { x: 0, y: 0.0012 },
    { x: 0.4, y: 0.2008 },
  ]);
});

test("extremos: sin recta (todavía no se calculó) no hay línea", () => {
  assert.deepEqual(plano(curva.extremos(datos({ recta: null }))), []);
});

test("datasets: estándares como puntos y la recta como línea sin puntos", () => {
  const series = plano(curva.datasets(datos(), COLORES));
  assert.equal(series.length, 2);
  assert.equal(series[0].type, "scatter");
  assert.deepEqual(series[0].data, [
    { x: 0, y: 0 },
    { x: 0.2, y: 0.101 },
    { x: 0.4, y: 0.199 },
  ]);
  assert.equal(series[0].backgroundColor, COLORES.puntos);
  assert.equal(series[1].type, "line");
  assert.equal(series[1].pointRadius, 0);
  assert.equal(series[1].borderColor, COLORES.recta);
});

test("datasets: sin recta solo los estándares", () => {
  assert.equal(curva.datasets(datos({ recta: null }), COLORES).length, 1);
});
