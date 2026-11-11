// Fechas dd/mm/aaaa: barras automáticas de static/js/aqualab.js con un DOM simulado.
// Corre con `node --test config/tests/js`.
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const fuente = fs.readFileSync(path.join(__dirname, "../../../static/js/aqualab.js"), "utf8");

function entorno() {
  const eventos = {};
  const document = {
    addEventListener: (tipo, fn) => (eventos[tipo] ||= []).push(fn),
    querySelectorAll: () => [],
    querySelector: () => null,
  };
  const contexto = { document };
  vm.runInNewContext(fuente, contexto);
  const campo = (atributos) => ({
    value: "",
    closest: (selector) => (selector === "[data-fecha]" && atributos.fecha ? campoActual : null),
  });
  let campoActual = null;
  const escribir = (valor, { fecha = true, inputType = "insertText" } = {}) => {
    campoActual = campo({ fecha });
    campoActual.value = valor;
    for (const fn of eventos.input || []) fn({ target: campoActual, inputType });
    return campoActual.value;
  };
  return { contexto, escribir };
}

test("agrega las barras mientras se escribe", () => {
  const { escribir } = entorno();
  assert.equal(escribir("1"), "1");
  assert.equal(escribir("120"), "12/0");
  assert.equal(escribir("12/045"), "12/04/5");
  assert.equal(escribir("12042026"), "12/04/2026");
});

test("descarta lo que no son dígitos y corta en 8", () => {
  const { escribir } = entorno();
  assert.equal(escribir("12-04-2026"), "12/04/2026");
  assert.equal(escribir("120420261"), "12/04/2026");
});

test("al borrar no vuelve a poner la barra", () => {
  const { escribir } = entorno();
  assert.equal(escribir("12/0", { inputType: "deleteContentBackward" }), "12/0");
  assert.equal(escribir("12/", { inputType: "deleteContentBackward" }), "12/");
});

test("no toca otros campos", () => {
  const { escribir } = entorno();
  assert.equal(escribir("abc123", { fecha: false }), "abc123");
});
