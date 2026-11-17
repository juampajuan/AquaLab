const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const path = require("node:path");

const codigo = fs.readFileSync(
  path.join(__dirname, "../../static/informes/dashboard_posicion.js"), "utf8");

function cargar({ tipo = "navigate", guardado = null, bloqueado = false, search = "" } = {}) {
  const almacen = new Map(), eventos = {}, saltos = [];
  if (guardado !== null) almacen.set("aqualab:dashboard:posicion:" + search, guardado);
  const sessionStorage = {
    getItem(k) { if (bloqueado) throw new Error("bloqueado"); return almacen.get(k) ?? null; },
    setItem(k, v) { if (bloqueado) throw new Error("bloqueado"); almacen.set(k, v); },
  };
  const window = {
    location: { search }, sessionStorage, scrollY: 0,
    performance: { getEntriesByType: () => [{ type: tipo }] },
    scrollTo: (x, y) => saltos.push(y),
    addEventListener: (nombre, fn) => { eventos[nombre] = fn; },
  };
  vm.runInNewContext(codigo, { window, document: { readyState: "loading" } });
  return { window, eventos, saltos, almacen };
}

test("con «atrás» vuelve a la posición guardada, después de cargar", () => {
  const { eventos, saltos } = cargar({ tipo: "back_forward", guardado: "1840" });
  assert.deepEqual(saltos, []);
  eventos.load();
  assert.deepEqual(saltos, [1840]);
});

test("al entrar por el menú arranca arriba", () => {
  const { eventos, saltos } = cargar({ tipo: "navigate", guardado: "1840" });
  eventos.load();
  assert.deepEqual(saltos, []);
});

test("cada período recuerda su propia posición", () => {
  const { eventos, saltos } = cargar({ tipo: "back_forward", guardado: "900", search: "?periodo=ultimos_3" });
  eventos.load();
  assert.deepEqual(saltos, [900]);
});

test("al salir guarda dónde estaba", () => {
  const { window, eventos, almacen } = cargar();
  window.scrollY = 1234.6;
  eventos.pagehide();
  assert.equal(almacen.get("aqualab:dashboard:posicion:"), "1235");
});

test("sin almacenamiento no falla ni salta", () => {
  const { eventos, saltos } = cargar({ tipo: "back_forward", bloqueado: true });
  eventos.pagehide();
  eventos.load();
  assert.deepEqual(saltos, []);
});
