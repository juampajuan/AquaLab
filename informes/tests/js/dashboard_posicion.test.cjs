const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const path = require("node:path");

const codigo = fs.readFileSync(
  path.join(__dirname, "../../static/informes/dashboard_posicion.js"), "utf8");

function cargar({ tipo = "navigate", guardado = null, bloqueado = false, search = "" } = {}) {
  const almacen = new Map(), eventos = {}, saltos = [], observadores = [];
  if (guardado !== null) almacen.set("aqualab:dashboard:posicion:" + search, guardado);
  const clases = new Set();
  const raiz = { classList: { contains: (c) => clases.has(c) } };
  const sessionStorage = {
    getItem(k) { if (bloqueado) throw new Error("bloqueado"); return almacen.get(k) ?? null; },
    setItem(k, v) { if (bloqueado) throw new Error("bloqueado"); almacen.set(k, v); },
  };
  class MutationObserver {
    constructor(fn) { this.fn = fn; this.activo = false; observadores.push(this); }
    observe() { this.activo = true; }
    disconnect() { this.activo = false; }
  }
  const window = {
    location: { search }, sessionStorage, scrollY: 0, MutationObserver,
    performance: { getEntriesByType: () => [{ type: tipo }] },
    requestAnimationFrame: (fn) => fn(),
    scrollTo: (x, y) => saltos.push(y),
    addEventListener: (nombre, fn) => { eventos[nombre] = fn; },
  };
  vm.runInNewContext(codigo, { window, document: { readyState: "loading", documentElement: raiz } });
  const sesion = {
    ocultar: () => clases.add("sesion-oculta"),
    mostrar: () => { clases.delete("sesion-oculta"); observadores.filter((o) => o.activo).forEach((o) => o.fn()); },
  };
  return { window, eventos, saltos, almacen, sesion };
}

test("recargado con «atrás»: vuelve a la posición guardada al terminar de cargar", () => {
  const { eventos, saltos } = cargar({ tipo: "back_forward", guardado: "1840" });
  assert.deepEqual(saltos, []);
  eventos.load();
  assert.deepEqual(saltos, [1840]);
});

test("de memoria (bfcache): espera a que la guardia de sesión vuelva a mostrar la página", () => {
  const { eventos, saltos, sesion } = cargar({ guardado: "1840" });
  sesion.ocultar(); // sesion.js oculta la página al volver de memoria
  eventos.pageshow({ persisted: true });
  assert.deepEqual(saltos, []);
  sesion.mostrar();
  assert.deepEqual(saltos, [1840]);
  sesion.mostrar();
  assert.deepEqual(saltos, [1840]); // una sola vez
});

test("con la página oculta no guarda la posición (valdría 0)", () => {
  const { window, eventos, almacen, sesion } = cargar({ guardado: "1840" });
  sesion.ocultar();
  window.scrollY = 0;
  eventos.scroll();
  eventos.pagehide();
  assert.equal(almacen.get("aqualab:dashboard:posicion:"), "1840");
});

test("guarda la posición mientras se desplaza", () => {
  const { window, eventos, almacen } = cargar();
  window.scrollY = 1234.6;
  eventos.scroll();
  assert.equal(almacen.get("aqualab:dashboard:posicion:"), "1235");
});

test("al entrar por el menú arranca arriba", () => {
  const { eventos, saltos } = cargar({ tipo: "navigate", guardado: "1840" });
  eventos.load();
  eventos.pageshow({ persisted: false });
  assert.deepEqual(saltos, []);
});

test("cada período recuerda su propia posición", () => {
  const { eventos, saltos } = cargar({ tipo: "back_forward", guardado: "900", search: "?periodo=ultimos_3" });
  eventos.load();
  assert.deepEqual(saltos, [900]);
});

test("sin almacenamiento no falla ni salta", () => {
  const { eventos, saltos } = cargar({ tipo: "back_forward", bloqueado: true });
  eventos.scroll();
  eventos.pagehide();
  eventos.load();
  assert.deepEqual(saltos, []);
});
