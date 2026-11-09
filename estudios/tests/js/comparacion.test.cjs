// Comparación histórica (US 8.1): funciones puras de estudios/static/estudios/comparacion.js.
// Corre con `node --test estudios/tests/js`; carga el archivo con un window simulado, sin Chart.js
// (así no dibuja) y sin DOM real.
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const fuente = fs.readFileSync(
  path.join(__dirname, "../../static/estudios/comparacion.js"),
  "utf8",
);

function cargar() {
  const documento = {
    readyState: "complete",
    getElementById: () => null,
    querySelectorAll: () => [],
    documentElement: {},
  };
  const ventana = { document: documento };
  const contexto = vm.createContext({
    window: ventana,
    document: documento,
    getComputedStyle: () => ({ getPropertyValue: () => "" }),
  });
  vm.runInContext(fuente, contexto);
  return ventana.AqualabComparacion;
}

const comparacion = cargar();
// Los arrays creados dentro del contexto de vm son de otro realm: se comparan como JSON.
const plano = (valor) => JSON.parse(JSON.stringify(valor));
const COLORES = { linea: "#0f2744", referencia: "#0ea5e9", franja: "#047857" };

function prueba(extra = {}) {
  return {
    codigo: "CL-",
    nombre: "Cloruro",
    unidad: "mg/l",
    presencia: false,
    franja: { min: null, max: "350.0", comparable: true },
    puntos: [
      { etiqueta: "a", valor: "118.0000000000", texto: "118", validado: true, referencia: false },
      { etiqueta: "b", valor: "430.0000000000", texto: "430", validado: false, referencia: true },
      { etiqueta: "c", valor: "121.0000000000", texto: "121", validado: true, referencia: false },
    ],
    ...extra,
  };
}

test("la línea de validados deja null en el estudio actual y el punto destacado va aparte", () => {
  const [validados, actual] = comparacion.datasets(prueba(), COLORES);

  assert.deepEqual(validados.data, [118, null, 121]);
  assert.equal(validados.spanGaps, true);
  assert.deepEqual(actual.data, [null, 430, null]);
  assert.equal(actual.pointStyle, "rectRot");
  assert.equal(actual.label, "Este estudio (Sin validar)");
  assert.equal(actual.showLine, false);
});

test("sin estudio actual no hay punto destacado", () => {
  const sinReferencia = prueba({
    puntos: [{ etiqueta: "a", valor: "1", texto: "1", validado: true, referencia: false }],
  });

  const lista = comparacion.datasets(sinReferencia, COLORES).filter((d) => !d.franja);

  assert.equal(lista.length, 1);
  assert.equal(lista[0].label, "Validados");
});

test("estudio actual validado", () => {
  const validada = prueba();
  validada.puntos[1].validado = true;

  assert.equal(comparacion.datasets(validada, COLORES)[1].label, "Este estudio (Validado)");
});

test("franja con mínimo y máximo: relleno entre las dos líneas", () => {
  const ds = comparacion.franja(prueba({ franja: { min: "6.4", max: "8.5", comparable: true } }), 3, "#047857");

  assert.equal(ds.length, 2);
  assert.deepEqual(plano(ds[0].data), [6.4, 6.4, 6.4]);
  assert.equal(ds[0].fill, false);
  assert.deepEqual(plano(ds[1].data), [8.5, 8.5, 8.5]);
  assert.equal(ds[1].fill, "-1");
  assert.ok(ds.every((d) => d.pointRadius === 0 && d.franja));
});

test("franja con solo máximo va hasta el borde inferior; con solo mínimo, hasta el superior", () => {
  const maximo = comparacion.franja(prueba(), 2, "#047857");
  const minimo = comparacion.franja(prueba({ franja: { min: "100", max: null, comparable: true } }), 2, "#047857");

  assert.equal(maximo.length, 1);
  assert.equal(maximo[0].fill, "start");
  assert.deepEqual(plano(maximo[0].data), [350, 350]);
  assert.equal(minimo.length, 1);
  assert.equal(minimo[0].fill, "end");
});

test("sin límite comparable no hay franja", () => {
  const ds = comparacion.franja(prueba({ franja: { min: null, max: null, comparable: false } }), 3, "#047857");

  assert.deepEqual(plano(ds), []);
});

test("presencia: banda alrededor de 0 y eje con Ausente/Presente", () => {
  const ap = prueba({ presencia: true, unidad: "A/P", franja: { min: null, max: null, comparable: true } });

  const ds = comparacion.franja(ap, 2, "#047857");
  const eje = comparacion.ejeY(ap);
  const marcas = { ticks: [] };
  eje.afterBuildTicks(marcas);

  assert.deepEqual(plano(ds[0].data), [-0.25, -0.25]);
  assert.deepEqual(plano(ds[1].data), [0.25, 0.25]);
  assert.equal(ds[1].fill, "-1");
  assert.deepEqual(plano(marcas.ticks.map((t) => t.value)), [0, 1]);
  assert.equal(eje.ticks.callback(0), "Ausente");
  assert.equal(eje.ticks.callback(1), "Presente");
  assert.equal(eje.ticks.callback(0.5), "");
});

test("eje numérico con la unidad como título", () => {
  assert.equal(comparacion.ejeY(prueba()).title.text, "mg/l");
});

test("tooltip: valor con unidad y estado; en A/P sin unidad", () => {
  const p = prueba();
  const ap = prueba({ presencia: true, unidad: "A/P" });

  assert.equal(comparacion.textoPunto(p, p.puntos[1]), "430 mg/l · Sin validar");
  assert.equal(
    comparacion.textoPunto(ap, { texto: "Presente", validado: true }),
    "Presente · Validado",
  );
});
