// Panel del asistente (US 10.1): comportamiento de static/js/aqualab.js con un DOM simulado.
// Corre con `node --test asistente/tests/js`; no simula el CSS ni un navegador real.
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const fuente = fs.readFileSync(path.join(__dirname, "../../../static/js/aqualab.js"), "utf8");

// Selector simple: una o más partes «[atributo]» o «[atributo=valor]», sin espacios.
function coincide(elemento, selector) {
  const partes = selector.match(/\[[\w-]+(?:=[\w-]+)?\]/g) || [];
  return (
    partes.length > 0 &&
    partes.every((parte) => {
      const [nombre, valor] = parte.slice(1, -1).split("=");
      if (nombre === "name") return elemento.name === valor;
      return elemento.atributos.has(nombre) && (valor === undefined || elemento.atributos.get(nombre) === valor);
    })
  );
}

class Elemento {
  constructor(etiqueta = "div", atributos = {}) {
    this.etiqueta = etiqueta;
    this.atributos = new Map(Object.entries(atributos));
    this.hijos = [];
    this.padre = null;
    this.hidden = false;
    this.disabled = false;
    this.value = "";
    this.textContent = "";
    this.className = "";
    this.enfocado = false;
  }
  append(hijo) {
    hijo.padre = this;
    this.hijos.push(hijo);
  }
  remove() {
    if (this.padre) this.padre.hijos = this.padre.hijos.filter((h) => h !== this);
    this.padre = null;
  }
  *recorrer() {
    for (const hijo of this.hijos) {
      yield hijo;
      yield* hijo.recorrer();
    }
  }
  querySelectorAll(selector) {
    return [...this.recorrer()].filter((e) => coincide(e, selector));
  }
  querySelector(selector) {
    return this.querySelectorAll(selector)[0] || null;
  }
  closest(selector) {
    for (let actual = this; actual; actual = actual.padre) {
      if (coincide(actual, selector)) return actual;
    }
    return null;
  }
  getAttribute(nombre) {
    return this.atributos.has(nombre) ? this.atributos.get(nombre) : null;
  }
  setAttribute(nombre, valor) {
    this.atributos.set(nombre, String(valor));
  }
  hasAttribute(nombre) {
    return this.atributos.has(nombre);
  }
  removeAttribute(nombre) {
    this.atributos.delete(nombre);
  }
  focus() {
    this.enfocado = true;
  }
}

function respuestaJson(status, datos, { redirected = false, tipo = "application/json" } = {}) {
  return {
    ok: status >= 200 && status < 300,
    status,
    redirected,
    headers: { get: (nombre) => (nombre.toLowerCase() === "content-type" ? tipo : null) },
    json: async () => (typeof datos === "string" ? JSON.parse(datos) : datos),
  };
}

function entorno({ deshabilitado = false, respuestas = [] } = {}) {
  const eventos = {};
  const cuerpo = new Elemento("body");
  const boton = new Elemento("button", { "data-asistente-abrir": "", "aria-expanded": "false" });
  if (deshabilitado) boton.setAttribute("aria-disabled", "true");
  cuerpo.append(boton);
  const panel = new Elemento("section", { "data-asistente": "", "data-url": "/asistente/preguntar/" });
  panel.hidden = true;
  cuerpo.append(panel);
  const cerrar = new Elemento("button", { "data-asistente-cerrar": "" });
  panel.append(cerrar);
  const mensajes = new Elemento("ol", { "data-asistente-mensajes": "" });
  panel.append(mensajes);
  const ejemplo = new Elemento("button", { "data-asistente-ejemplo": "" });
  ejemplo.textContent = " ¿Cómo está el PI 200417? ";
  mensajes.append(ejemplo);
  const formulario = new Elemento("form", { "data-asistente-form": "" });
  panel.append(formulario);
  const campo = new Elemento("textarea", { "data-asistente-pregunta": "" });
  formulario.append(campo);
  const contador = new Elemento("span", { "data-asistente-contador": "" });
  formulario.append(contador);
  const enviar = new Elemento("button", { "data-asistente-enviar": "" });
  formulario.append(enviar);

  const pedidos = [];
  const pendientes = [...respuestas];
  const document = {
    cookie: "otra=1; csrftoken=token%2Fcsrf",
    addEventListener: (tipo, fn) => (eventos[tipo] ||= []).push(fn),
    querySelector: (selector) => cuerpo.querySelector(selector),
    querySelectorAll: (selector) => cuerpo.querySelectorAll(selector),
    createElement: (etiqueta) => new Elemento(etiqueta),
  };
  const fetch = (url, opciones) => {
    pedidos.push({ url, opciones, cuerpo: JSON.parse(opciones.body) });
    const siguiente = pendientes.shift();
    if (typeof siguiente === "function") return siguiente();
    if (siguiente instanceof Error) return Promise.reject(siguiente);
    return Promise.resolve(siguiente);
  };
  const localStorage = {
    getItem() {
      throw new Error("No debe usar localStorage");
    },
    setItem() {
      throw new Error("No debe usar localStorage");
    },
  };
  vm.runInNewContext(fuente, { document, fetch, localStorage, JSON, Promise });
  const despachar = (tipo, datos) => {
    const evento = { preventDefault() { this.prevenido = true; }, ...datos };
    for (const fn of eventos[tipo] || []) fn(evento);
    return evento;
  };
  const esperar = () => new Promise((resolver) => setImmediate(resolver));
  const preguntar = async (texto) => {
    campo.value = texto;
    despachar("submit", { target: formulario });
    await esperar();
    await esperar();
  };
  const textos = () => mensajes.querySelectorAll("[data-asistente-mensaje]").map((m) => m.hijos[0].textContent);
  return { boton, panel, campo, contador, enviar, ejemplo, cerrar, mensajes, pedidos, despachar, preguntar, textos, esperar };
}

test("el botón abre el panel y Escape lo cierra devolviendo el foco", () => {
  const { boton, panel, campo, despachar } = entorno();
  despachar("click", { target: boton });
  assert.equal(panel.hidden, false);
  assert.equal(boton.getAttribute("aria-expanded"), "true");
  assert.equal(campo.enfocado, true);
  despachar("keydown", { key: "Escape", target: campo });
  assert.equal(panel.hidden, true);
  assert.equal(boton.getAttribute("aria-expanded"), "false");
  assert.equal(boton.enfocado, true);
});

test("el botón «Cerrar» y un segundo clic en el botón cierran el panel", () => {
  const { boton, panel, cerrar, despachar } = entorno();
  despachar("click", { target: boton });
  despachar("click", { target: cerrar });
  assert.equal(panel.hidden, true);
  despachar("click", { target: boton });
  despachar("click", { target: boton });
  assert.equal(panel.hidden, true);
});

test("deshabilitado (sin configuración), el botón no abre el panel", () => {
  const { boton, panel, despachar } = entorno({ deshabilitado: true });
  despachar("click", { target: boton });
  assert.equal(panel.hidden, true);
});

test("un ejemplo completa la pregunta y el contador", () => {
  const { boton, ejemplo, campo, contador, despachar } = entorno();
  despachar("click", { target: boton });
  despachar("click", { target: ejemplo });
  assert.equal(campo.value, "¿Cómo está el PI 200417?");
  assert.equal(contador.textContent, `${campo.value.length}/500`);
});

test("preguntar hace POST con CSRF, pregunta e historial, y muestra la respuesta como texto", async () => {
  const { pedidos, preguntar, textos, mensajes, campo } = entorno({
    respuestas: [
      respuestaJson(200, {
        texto: "La muestra <b>PI 200417</b> está Finalizada.",
        enlaces: [{ etiqueta: "PI 200417", url: "/muestras/7/" }],
      }),
    ],
  });
  await preguntar("¿Cómo está el PI 200417?");
  const [pedido] = pedidos;
  assert.equal(pedido.url, "/asistente/preguntar/");
  assert.equal(pedido.opciones.method, "POST");
  assert.equal(pedido.opciones.headers["X-CSRFToken"], "token/csrf");
  assert.equal(pedido.opciones.headers["Content-Type"], "application/json");
  assert.deepEqual(pedido.cuerpo, { pregunta: "¿Cómo está el PI 200417?", historial: [] });
  assert.deepEqual(textos(), ["¿Cómo está el PI 200417?", "La muestra <b>PI 200417</b> está Finalizada."]);
  const respuesta = mensajes.querySelectorAll("[data-asistente-mensaje=asistente]")[0];
  // <li> → [<p>, <ul>] → <li> → <a>
  const enlace = respuesta.hijos[1].hijos[0].hijos[0];
  assert.equal(enlace.etiqueta, "a");
  assert.equal(enlace.href, "/muestras/7/");
  assert.equal(enlace.textContent, "PI 200417");
  assert.equal(campo.value, "");
});

test("mientras espera muestra «Consultando…» y no permite otro envío", async () => {
  let resolver;
  const { campo, enviar, despachar, pedidos, textos, esperar } = entorno({
    respuestas: [() => new Promise((r) => (resolver = r))],
  });
  campo.value = "hola";
  despachar("submit", { target: campo.closest("[data-asistente-form]") });
  assert.equal(enviar.disabled, true);
  assert.deepEqual(textos(), ["hola", "Consultando…"]);
  despachar("submit", { target: campo.closest("[data-asistente-form]") });
  assert.equal(pedidos.length, 1);
  resolver(respuestaJson(200, { texto: "Listo", enlaces: [] }));
  await esperar();
  await esperar();
  assert.equal(enviar.disabled, false);
  assert.deepEqual(textos(), ["hola", "Listo"]);
});

test("Enter pregunta y Shift+Enter no", async () => {
  const { campo, despachar, pedidos, esperar } = entorno({ respuestas: [respuestaJson(200, { texto: "Ok", enlaces: [] })] });
  campo.value = "hola";
  const conShift = despachar("keydown", { key: "Enter", shiftKey: true, target: campo });
  assert.equal(conShift.prevenido, undefined);
  assert.equal(pedidos.length, 0);
  const enter = despachar("keydown", { key: "Enter", shiftKey: false, target: campo });
  assert.equal(enter.prevenido, true);
  await esperar();
  assert.equal(pedidos.length, 1);
});

test("manda los últimos 6 mensajes, cada uno recortado a 4000 caracteres", async () => {
  const largo = "x".repeat(5000);
  const respuestas = [
    respuestaJson(200, { texto: largo, enlaces: [] }),
    ...Array.from({ length: 4 }, () => respuestaJson(200, { texto: "ok", enlaces: [] })),
  ];
  const { pedidos, preguntar } = entorno({ respuestas });
  await preguntar("primera");
  await preguntar("segunda");
  assert.deepEqual(pedidos[1].cuerpo.historial, [
    { rol: "usuario", texto: "primera" },
    { rol: "asistente", texto: "x".repeat(4000) },
  ]);
  await preguntar("tercera");
  await preguntar("cuarta");
  await preguntar("quinta");
  const historial = pedidos[4].cuerpo.historial;
  assert.equal(historial.length, 6);
  assert.deepEqual(historial[0], { rol: "usuario", texto: "segunda" });
  assert.deepEqual(historial[5], { rol: "asistente", texto: "ok" });
});

for (const [status, mensaje] of [
  [400, "Escribí una pregunta de hasta 500 caracteres."],
  [429, "Se alcanzó el límite de consultas del asistente. Probá más tarde; el resto de AquaLab funciona normalmente."],
  [503, "El asistente no está configurado."],
]) {
  test(`un error ${status} muestra su mensaje como aviso sin cerrar el panel`, async () => {
    const { boton, panel, preguntar, textos, mensajes, despachar, pedidos } = entorno({
      respuestas: [respuestaJson(status, { error: "x", mensaje }), respuestaJson(200, { texto: "ok", enlaces: [] })],
    });
    despachar("click", { target: boton });
    await preguntar("hola");
    assert.equal(panel.hidden, false);
    assert.equal(mensajes.querySelectorAll("[data-asistente-mensaje=aviso]").length, 1);
    assert.equal(textos().at(-1), mensaje);
    await preguntar("de nuevo");
    assert.deepEqual(pedidos[1].cuerpo.historial, []);
  });
}

test("una falla de red muestra el aviso «no disponible»", async () => {
  const { preguntar, textos } = entorno({ respuestas: [new Error("sin red")] });
  await preguntar("hola");
  assert.equal(
    textos().at(-1),
    "El asistente no está disponible en este momento. Probá de nuevo más tarde o usá las pantallas de AquaLab.",
  );
});

for (const [nombre, respuesta] of [
  ["redirigida al login", respuestaJson(200, "<html>", { redirected: true, tipo: "text/html" })],
  ["en HTML", respuestaJson(200, "<html>", { tipo: "text/html; charset=utf-8" })],
  ["con JSON roto", respuestaJson(200, "{roto", {})],
]) {
  test(`una respuesta ${nombre} avisa que la sesión venció y no agrega nada a la conversación`, async () => {
    const { preguntar, textos, pedidos } = entorno({
      respuestas: [respuesta, respuestaJson(200, { texto: "ok", enlaces: [] })],
    });
    await preguntar("hola");
    assert.equal(textos().at(-1), "Tu sesión venció; volvé a iniciar sesión");
    await preguntar("otra");
    assert.deepEqual(pedidos[1].cuerpo.historial, []);
  });
}

test("cerrar el panel borra la conversación y no usa localStorage", async () => {
  const { boton, preguntar, despachar, pedidos, textos } = entorno({
    respuestas: [respuestaJson(200, { texto: "ok", enlaces: [] }), respuestaJson(200, { texto: "ok", enlaces: [] })],
  });
  despachar("click", { target: boton });
  await preguntar("hola");
  despachar("keydown", { key: "Escape" });
  assert.deepEqual(textos(), []);
  despachar("click", { target: boton });
  await preguntar("otra");
  assert.deepEqual(pedidos[1].cuerpo.historial, []);
});
