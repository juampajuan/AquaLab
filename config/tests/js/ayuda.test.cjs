// Ayuda de los campos (US 9.1): comportamiento de static/js/aqualab.js con un DOM simulado.
// Corre con `node --test config/tests/js`; no simula el CSS ni un navegador real.
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const fuente = fs.readFileSync(path.join(__dirname, "../../../static/js/aqualab.js"), "utf8");

// Selector simple: una o más partes «.clase» o «[atributo]», sin espacios.
function coincide(elemento, selector) {
  const partes = selector.match(/\.[\w-]+|\[[\w-]+\]/g) || [];
  return partes.every((parte) =>
    parte[0] === "." ? elemento.clases.has(parte.slice(1)) : elemento.atributos.has(parte.slice(1, -1)),
  );
}

class Elemento {
  constructor({ clases = [], atributos = {}, padre = null } = {}) {
    this.clases = new Set(clases);
    this.atributos = new Map(Object.entries(atributos));
    this.padre = padre;
    this.removido = false;
    this.desenfocado = false;
  }
  hijo(opciones) {
    return new Elemento({ ...opciones, padre: this });
  }
  closest(selector) {
    for (let actual = this; actual; actual = actual.padre) {
      if (coincide(actual, selector)) return actual;
    }
    return null;
  }
  contains(otro) {
    for (let actual = otro; actual; actual = actual.padre) {
      if (actual === this) return true;
    }
    return false;
  }
  hasAttribute(nombre) { return this.atributos.has(nombre); }
  setAttribute(nombre, valor) { this.atributos.set(nombre, String(valor)); }
  removeAttribute(nombre) { this.atributos.delete(nombre); }
  remove() { this.removido = true; }
  blur() { this.desenfocado = true; }
}

function entorno() {
  const eventos = {};
  const cuerpo = new Elemento();
  const formulario = cuerpo.hijo({ atributos: { "data-formulario": "" } });
  const ayudas = [1, 2].map(() => {
    const ayuda = formulario.hijo({ clases: ["ayuda"], atributos: { "data-ayuda": "" } });
    const boton = ayuda.hijo({ clases: ["ayuda-boton"] });
    const texto = ayuda.hijo({ clases: ["ayuda-texto"] });
    return { ayuda, boton, texto };
  });
  const campo = formulario.hijo();
  const document = {
    activeElement: cuerpo,
    addEventListener: (tipo, fn) => (eventos[tipo] ||= []).push(fn),
    querySelectorAll: (selector) =>
      ayudas.map((a) => a.ayuda).filter((elemento) => coincide(elemento, selector)),
    querySelector: (selector) => document.querySelectorAll(selector)[0] || null,
  };
  vm.runInNewContext(fuente, { document });
  const despachar = (tipo, datos) => {
    const evento = { preventDefault() { this.prevenido = true; }, ...datos };
    for (const fn of eventos[tipo] || []) fn(evento);
    return evento;
  };
  return { document, ayudas, campo, formulario, despachar, eventos };
}

const abierta = (elemento) => elemento.hasAttribute("data-abierta");
const cerrada = (elemento) => elemento.hasAttribute("data-cerrada");

test("un toque en el ícono abre la ayuda y otro la cierra (esc. 5)", () => {
  const { ayudas, despachar } = entorno();
  const [{ ayuda, boton }] = ayudas;

  const evento = despachar("click", { target: boton });
  assert.ok(abierta(ayuda));
  assert.ok(!cerrada(ayuda));
  assert.ok(!evento.prevenido, "el botón es type=button: no hace falta frenar ningún envío");

  despachar("click", { target: boton });
  assert.ok(!abierta(ayuda));
  assert.ok(cerrada(ayuda), "la cierra aunque el botón siga con foco o hover");
});

test("un toque fuera de la ayuda la cierra (FR-003)", () => {
  const { ayudas, campo, despachar } = entorno();
  const [{ ayuda, boton }] = ayudas;
  despachar("click", { target: boton });

  despachar("click", { target: campo });
  assert.ok(!abierta(ayuda));
});

test("un toque en el texto de la ayuda no la cierra", () => {
  const { ayudas, despachar } = entorno();
  const [{ ayuda, boton, texto }] = ayudas;
  despachar("click", { target: boton });

  despachar("click", { target: texto });
  assert.ok(abierta(ayuda));
});

test("Escape cierra la ayuda enfocada sin mover el foco (esc. 4)", () => {
  const { document, ayudas, despachar } = entorno();
  const [{ ayuda, boton }] = ayudas;
  despachar("focusin", { target: boton });
  document.activeElement = boton;

  despachar("keydown", { key: "Escape" });
  assert.ok(cerrada(ayuda));
  assert.ok(!boton.desenfocado);

  despachar("focusout", { target: boton, relatedTarget: null });
  assert.ok(!cerrada(ayuda), "al salir con Tab se limpia para la próxima vez");
});

test("otras teclas no cierran la ayuda", () => {
  const { document, ayudas, despachar } = entorno();
  const [{ ayuda, boton }] = ayudas;
  document.activeElement = boton;

  despachar("keydown", { key: "Enter" });
  assert.ok(!cerrada(ayuda));
});

test("con Tab hacia otro campo se cierra la abierta por toque (esc. 4)", () => {
  const { ayudas, campo, despachar } = entorno();
  const [{ ayuda, boton }] = ayudas;
  despachar("click", { target: boton });

  despachar("focusout", { target: boton, relatedTarget: campo });
  assert.ok(!abierta(ayuda));
});

test("pasar el mouse del ícono al texto no la cierra (esc. 9, WCAG 1.4.13)", () => {
  const { ayudas, despachar } = entorno();
  const [{ ayuda, boton, texto }] = ayudas;
  despachar("pointerover", { target: boton, pointerType: "mouse" });
  despachar("click", { target: boton });

  despachar("pointerout", { target: boton, relatedTarget: texto, pointerType: "mouse" });
  despachar("pointerover", { target: texto, pointerType: "mouse" });
  assert.ok(abierta(ayuda));
  assert.ok(!cerrada(ayuda));
});

test("salir del ícono y del texto con el mouse la cierra (esc. 9)", () => {
  const { ayudas, campo, despachar } = entorno();
  const [{ ayuda, boton, texto }] = ayudas;
  despachar("pointerover", { target: boton, pointerType: "mouse" });
  despachar("click", { target: boton });

  despachar("pointerout", { target: texto, relatedTarget: campo, pointerType: "mouse" });
  assert.ok(!abierta(ayuda));
  assert.ok(!cerrada(ayuda));
});

test("Escape con el mouse encima la cierra y moverse adentro no la reabre (esc. 9)", () => {
  const { ayudas, despachar } = entorno();
  const [{ ayuda, boton, texto }] = ayudas;
  despachar("pointerover", { target: boton, pointerType: "mouse" });

  despachar("keydown", { key: "Escape" });
  assert.ok(cerrada(ayuda));

  despachar("pointerout", { target: boton, relatedTarget: texto, pointerType: "mouse" });
  despachar("pointerover", { target: texto, pointerType: "mouse" });
  assert.ok(cerrada(ayuda), "sigue cerrada hasta que el mouse salga");
});

test("al levantar el dedo no se cierra la ayuda abierta con un toque", () => {
  const { ayudas, campo, despachar } = entorno();
  const [{ ayuda, boton }] = ayudas;
  despachar("pointerover", { target: boton, pointerType: "touch" });
  despachar("click", { target: boton });

  despachar("pointerout", { target: boton, relatedTarget: campo, pointerType: "touch" });
  assert.ok(abierta(ayuda));
});

test("abrir una ayuda cierra las demás (esc. 7, FR-006)", () => {
  const { ayudas, despachar } = entorno();
  const [primera, segunda] = ayudas;
  despachar("click", { target: primera.boton });

  despachar("pointerover", { target: segunda.boton, pointerType: "mouse" });
  assert.ok(!abierta(primera.ayuda));
  assert.ok(cerrada(primera.ayuda), "no queda visible ni por hover ni por foco");
  assert.ok(!cerrada(segunda.ayuda));

  despachar("focusin", { target: primera.boton });
  assert.ok(!cerrada(primera.ayuda));
  assert.ok(cerrada(segunda.ayuda));

  despachar("click", { target: segunda.boton });
  assert.ok(abierta(segunda.ayuda));
  assert.ok(cerrada(primera.ayuda));
});

test("los comportamientos anteriores siguen: cerrar un mensaje", () => {
  const { despachar, formulario } = entorno();
  const mensaje = formulario.hijo({ atributos: { "data-nivel": "exito" } });
  const cerrar = mensaje.hijo({ atributos: { "data-cerrar-mensaje": "" } });

  despachar("click", { target: cerrar });
  assert.ok(mensaje.removido);
});
