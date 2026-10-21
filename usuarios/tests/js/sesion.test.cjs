// Regresiones de lógica de sesión con APIs estándar de Node; no simulan un navegador real.
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const fuente = fs.readFileSync(path.join(__dirname, "../../static/usuarios/sesion.js"), "utf8");
const procesar = () => new Promise((resolve) => setImmediate(resolve));

function entorno() {
  const eventos = {}, clases = new Set(), timers = new Map(), peticiones = [], destinos = [];
  let id = 0, foco = true;
  const mensaje = { textContent: "" };
  const boton = { disabled: false, addEventListener: (tipo, fn) => eventos["boton:" + tipo] = fn };
  const config = { dataset: {
    huella: "original", verificar: "/usuarios/sesion/", login: "/usuarios/login/",
  } };
  const document = {
    hidden: false, hasFocus: () => foco,
    documentElement: { classList: { add: (c) => clases.add(c), remove: (c) => clases.delete(c) } },
    querySelector: () => config,
    getElementById: (nombre) => nombre === "sesion-mensaje" ? mensaje : boton,
    addEventListener: (tipo, fn) => eventos[tipo] = fn,
  };
  const location = { origin: "http://localhost:8000", replace: (url) => destinos.push(url) };
  vm.runInNewContext(fuente, {
    document, location, URL, AbortController,
    window: { addEventListener: (tipo, fn) => eventos[tipo] = fn },
    setTimeout: (fn, ms) => { timers.set(++id, { fn, ms }); return id; },
    clearTimeout: (n) => timers.delete(n),
    fetch: (url, opciones) => new Promise((resolve, reject) => {
      // No resolver automáticamente al abortar permite reproducir respuestas tardías.
      peticiones.push({ url, opciones, resolve, reject });
    }),
  });
  function ejecutar(ms) {
    for (const [n, timer] of [...timers]) {
      if (timer.ms === ms) { timers.delete(n); timer.fn(); }
    }
  }
  function ocultar() { foco = false; eventos.blur(); }
  function volver() { foco = true; eventos.focus(); ejecutar(0); }
  return { eventos, clases, timers, peticiones, destinos, document, boton, mensaje,
    ejecutar, ocultar, volver, oculto: () => clases.has("sesion-oculta") };
}

function respuesta(status, redirected = false, ruta = "/usuarios/sesion/") {
  return { status, redirected, url: "http://localhost:8000" + ruta };
}

for (const [nombre, valor, muestra, navega] of [
  ["204 directo válido", respuesta(204), true, false],
  ["200 inesperado", respuesta(200), false, false],
  ["login seguido", respuesta(200, true, "/usuarios/login/?next=/admin/"), false, true],
  ["redirección desconocida", respuesta(200, true, "/otra/"), false, false],
  ["204 redirigido", respuesta(204, true), false, false],
  ["409 directo", respuesta(409), false, true],
  ["403", respuesta(403), false, false],
  ["500", respuesta(500), false, false],
]) {
  test(nombre, async () => {
    const e = entorno(); e.ocultar(); e.volver();
    e.peticiones[0].resolve(valor); await procesar();
    assert.equal(e.oculto(), !muestra);
    assert.equal(e.destinos.length, navega ? 1 : 0);
    if (navega) assert.equal(e.destinos[0], "http://localhost:8000/usuarios/login/");
    assert.equal(e.boton.disabled, false);
  });
}

test("timeout seguido de 204 tardío no revela contenido", async () => {
  const e = entorno(); e.ocultar(); e.volver();
  e.ejecutar(10000);
  assert.equal(e.peticiones[0].opciones.signal.aborted, true);
  e.peticiones[0].resolve(respuesta(204)); await procesar();
  assert.equal(e.oculto(), true);
  assert.equal(e.boton.disabled, false);
  assert.match(e.mensaje.textContent, /No se pudo/);
});

test("204 de una generación anterior no revela ni libera una petición nueva", async () => {
  const e = entorno(); e.ocultar(); e.volver();
  e.ocultar(); e.volver();
  assert.equal(e.peticiones[0].opciones.signal.aborted, true);
  e.peticiones[0].resolve(respuesta(204)); await procesar();
  assert.equal(e.oculto(), true);
  e.eventos.focus(); e.ejecutar(0);
  assert.equal(e.peticiones.length, 2);
  e.peticiones[1].resolve(respuesta(204)); await procesar();
  assert.equal(e.oculto(), false);
});

test("eventos duplicados se agrupan sin revalidaciones concurrentes", async () => {
  const e = entorno(); e.ocultar();
  e.eventos.focus(); e.eventos.visibilitychange(); e.eventos.focus();
  e.volver();
  assert.equal(e.peticiones.length, 1);
  e.eventos.focus(); e.eventos.visibilitychange(); e.ejecutar(0);
  assert.equal(e.peticiones.length, 1);
  e.peticiones[0].resolve(respuesta(204)); await procesar();
  assert.equal(e.oculto(), false);
});

test("oculta o sin foco no acepta respuestas y revalida al volver", async () => {
  const e = entorno(); e.ocultar(); e.volver();
  e.document.hidden = true; e.eventos.visibilitychange();
  e.peticiones[0].resolve(respuesta(204)); await procesar();
  assert.equal(e.oculto(), true);
  e.eventos.focus(); e.ejecutar(0);
  assert.equal(e.peticiones.length, 1);
  e.document.hidden = false; e.eventos.visibilitychange(); e.ejecutar(0);
  assert.equal(e.peticiones.length, 2);
  e.peticiones[1].resolve(respuesta(204)); await procesar();
  assert.equal(e.oculto(), false);
});

test("fallo de red conserva ocultamiento y permite reintentar", async () => {
  const e = entorno(); e.ocultar(); e.volver();
  e.peticiones[0].reject(new Error("sin conexión")); await procesar();
  assert.equal(e.oculto(), true); assert.equal(e.boton.disabled, false);
  e.eventos["boton:click"](); e.ejecutar(0);
  e.peticiones[1].resolve(respuesta(204)); await procesar();
  assert.equal(e.oculto(), false);
});

test("pageshow persistido exige revalidación, carga inicial no", async () => {
  const e = entorno(); e.eventos.pageshow({ persisted: false }); e.ejecutar(0);
  assert.equal(e.peticiones.length, 0);
  e.eventos.pagehide(); e.eventos.pageshow({ persisted: true }); e.ejecutar(0);
  assert.equal(e.oculto(), true); assert.equal(e.peticiones.length, 1);
  e.peticiones[0].resolve(respuesta(204)); await procesar();
  assert.equal(e.oculto(), false);
});
