// Selector de cliente y origen (US 8.1): estudios/static/estudios/elegir_origen.js con un DOM
// simulado. Corre con `node --test estudios/tests/js`.
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");

const fuente = fs.readFileSync(
  path.join(__dirname, "../../static/estudios/elegir_origen.js"),
  "utf8",
);

const POR_CLIENTE = { 1: [[10, "Pozo 1"], [11, "Pozo 2"]], 2: [[20, "Tanque"]] };

// Un <select> simulado: hijos <option> con value y textContent.
function select(valor) {
  return {
    hijos: [],
    value: valor,
    get firstChild() {
      return this.hijos[0] || null;
    },
    removeChild(hijo) {
      this.hijos.splice(this.hijos.indexOf(hijo), 1);
    },
    appendChild(hijo) {
      this.hijos.push(hijo);
    },
    escuchas: {},
    addEventListener(evento, funcion) {
      this.escuchas[evento] = funcion;
    },
  };
}

function entorno(cliente, origen) {
  const selectCliente = select(cliente);
  const selectOrigen = select(origen);
  const formulario = {
    querySelector: (s) =>
      s === 'select[name="cliente"]' ? selectCliente : s === 'select[name="origen"]' ? selectOrigen : null,
  };
  const documento = {
    readyState: "complete",
    getElementById: (id) =>
      id === "origenes-por-cliente" ? { textContent: JSON.stringify(POR_CLIENTE) } : null,
    querySelector: (s) => (s === "[data-elegir-origen]" ? formulario : null),
    createElement: () => ({ value: "", textContent: "" }),
  };
  const ventana = { document: documento };
  vm.runInContext(fuente, vm.createContext({ window: ventana, document: documento }));
  return { selectCliente, selectOrigen, api: ventana.AqualabElegirOrigen };
}

function textos(selectOrigen) {
  return selectOrigen.hijos.map((o) => o.textContent);
}

test("al cambiar el cliente quedan solo sus orígenes, con la opción vacía primero", () => {
  const { selectCliente, selectOrigen } = entorno("", "");

  selectCliente.value = "1";
  selectCliente.escuchas.change();

  assert.deepEqual(textos(selectOrigen), ["Elegí un origen", "Pozo 1", "Pozo 2"]);
  selectCliente.value = "2";
  selectCliente.escuchas.change();
  assert.deepEqual(textos(selectOrigen), ["Elegí un origen", "Tanque"]);
});

test("conserva el origen elegido si es del cliente; si no, lo limpia", () => {
  const conservado = entorno("1", "11");
  assert.equal(conservado.selectOrigen.value, "11");

  const { selectCliente, selectOrigen } = entorno("1", "11");
  selectCliente.value = "2";
  selectCliente.escuchas.change();
  assert.equal(selectOrigen.value, "");
});

test("un cliente sin orígenes deja solo la opción vacía", () => {
  const { api } = entorno("", "");

  assert.deepEqual(JSON.parse(JSON.stringify(api.opciones(POR_CLIENTE, "9"))), [["", "Elegí un origen"]]);
});
