const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const path = require("node:path");

const codigo = fs.readFileSync(path.join(__dirname, "../../static/informes/conclusion.js"), "utf8");

function entorno(fetch, opciones = {}) {
  const elementos = {};
  const temporizadores = new Map(), almacen = opciones.almacen || new Map(), eventos = {};
  const navegaciones = [];
  const confirmaciones = [];
  let secuencia = 0;
  for (const nombre of ["proponer", "advertencias", "estado", "csrf", "editor",
                        "aprobar", "emitir", "volver", "emitir-boton",
                        "sin", "errores", "revision", "respaldo", "avisos"]) {
    elementos[nombre] = { textContent: "", value: nombre === "csrf" ? "csrf-test" : "",
      disabled: false, focus() {}, addEventListener(evento, fn) { this[evento] = fn; } };
  }
  const root = { dataset: { urlProponer: "/proponer/", urlGuardar: "/guardar/",
                           urlAprobar: "/aprobar/", estudio: "1", usuario: "10",
                           sesion: opciones.sesion || "s1" },
    querySelector(selector) { return elementos[selector.match(/data-conclusion-([\w-]+)/)?.[1]]; } };
  const inicial = opciones.inicial || { revision: 0, huella_hechos: "h" };
  root.querySelector = (selector) => selector === "[data-conclusion-inicial]"
    ? {textContent: JSON.stringify(inicial)} : elementos[selector.match(/data-conclusion-([\w-]+)/)?.[1]];
  const storage = { getItem: k => almacen.get(k) ?? null, setItem: (k,v) => {
      if (opciones.sinStorage) throw new Error("Storage deshabilitado");
      almacen.set(k,v);
    },
    removeItem: k => almacen.delete(k), key: i => Array.from(almacen.keys())[i],
    get length() { return almacen.size; } };
  const logout = {addEventListener: (nombre, fn) => {eventos.logout = fn;}};
  elementos.volver.href = "/estudio/1/";
  elementos.emitir.requestSubmit = () => {eventos.enviado = true;};
  elementos.sin.dataset = {};
  elementos.sin.requestSubmit = () => {eventos.sinConclusion = true;};
  root.setAttribute = (nombre, valor) => {eventos[nombre] = valor;};
  vm.runInNewContext(codigo, {document: {querySelector: selector => selector === "[data-conclusion]"
    ? root : selector === "[data-cerrar-sesion]" ? logout : null,
    querySelectorAll: () => [], addEventListener: (evento, fn) => {eventos[evento] = fn;}}, fetch,
    window: {confirm: mensaje => {
      confirmaciones.push(mensaje);
      return opciones.confirmar ? opciones.confirmar(mensaje) : true;
    }, addEventListener: (evento, fn) => {eventos[evento] = fn;},
             sessionStorage: storage, location: {assign: destino => navegaciones.push(destino)}},
    sessionStorage: storage,
    setTimeout: fn => {const id = ++secuencia; temporizadores.set(id, fn); return id;},
    clearTimeout: id => temporizadores.delete(id), console});
  elementos.procesar = async () => {
    const pendientes = [...temporizadores.values()]; temporizadores.clear();
    for (const fn of pendientes) await fn();
    await new Promise(resolve => setImmediate(resolve));
  };
  elementos.almacen = almacen;
  elementos.eventos = eventos;
  elementos.navegaciones = navegaciones;
  elementos.confirmaciones = confirmaciones;
  return elementos;
}

test("propuesta POST envía CSRF y revisión y muestra borrador sin aprobar", async () => {
  let pedido;
  const ui = entorno(async (url, opciones) => {
    pedido = {url, opciones};
    return {ok: true, redirected: false, headers: {get: () => "application/json"},
      json: async () => ({revision: 2, huella_hechos: "h", texto_editorial: "Borrador",
        texto_final: "Borrador\nAdvertencias", advertencias: ["Advertencia sintética"],
        origen_propuesta: "plantilla", aprobada: false})};
  });
  await ui.proponer.click();
  assert.equal(pedido.opciones.method, "POST");
  assert.equal(pedido.opciones.headers["X-CSRFToken"], "csrf-test");
  assert.equal(JSON.parse(pedido.opciones.body).revision_esperada, 0);
  assert.equal(ui.editor.value, "Borrador");
  assert.match(ui.advertencias.textContent, /Advertencia/);
  assert.equal(ui.estado.textContent, "Pendiente");
  assert.match(ui.respaldo.textContent, /plantilla/);
  assert.doesNotMatch(ui.estado.textContent, /Aprobada/);
});

test("HTML de login no se interpreta como propuesta guardada", async () => {
  const ui = entorno(async () => ({ok: true, redirected: true,
    headers: {get: () => "text/html"}}));
  await ui.proponer.click();
  assert.match(ui.errores.textContent, /sesión/);
  assert.equal(ui.editor.value, "");
});

test("conflicto no pisa el texto visible y respuesta no JSON no es éxito", async () => {
  const ui = entorno(async () => ({ok: false, status: 409, redirected: false,
    headers: {get: () => "application/json"}, json: async () => ({texto_editorial: "Ajeno"})}));
  ui.editor.value = "Texto previo";
  await ui.proponer.click();
  assert.equal(ui.editor.value, "Texto previo");
  assert.match(ui.errores.textContent, /cambió/);
});

test("una propuesta en vuelo impide otra que pueda sustituir su respuesta", async () => {
  let completar;
  let llamadas = 0;
  const ui = entorno(() => {
    llamadas += 1;
    return new Promise(resolve => { completar = resolve; });
  });
  const pendiente = ui.proponer.click();
  await ui.proponer.click();
  assert.equal(llamadas, 1);
  completar({ok: false, status: 409, redirected: false,
    headers: {get: () => "application/json"}});
  await pendiente;
  assert.equal(ui.editor.value, "");
});

function exito(datos = {}) {
  return {ok: true, redirected: false, headers: {get: () => "application/json"},
    json: async () => ({revision: 1, huella_hechos: "h", huella_texto: "t",
      texto_editorial: "Texto editado", texto_final: "Texto editado", advertencias: [],
      aprobada: false, ...datos})};
}

test("autoguardado serial y recuperación local hasta recibir confirmación", async () => {
  const pedidos = [];
  const ui = entorno(async (url, opciones) => {pedidos.push({url, opciones}); return exito();});
  ui.editor.value = "Texto editado";
  ui.editor.input();
  assert.equal(ui["emitir-boton"].disabled, true);
  assert.ok(ui.almacen.size > 0);
  await ui.procesar();
  assert.equal(pedidos[0].url, "/guardar/");
  assert.equal(JSON.parse(pedidos[0].opciones.body).texto, "Texto editado");
  assert.equal(ui.almacen.size, 0);
});

test("aprobar espera guardado y usa huella exacta devuelta por servidor", async () => {
  const pedidos = [];
  const ui = entorno(async (url, opciones) => {pedidos.push({url, opciones}); return exito();});
  ui.editor.value = "Texto editado";
  ui.editor.input();
  await ui.aprobar.click();
  assert.deepEqual(pedidos.map(p => p.url), ["/guardar/", "/aprobar/"]);
  assert.equal(JSON.parse(pedidos[1].opciones.body).huella_texto_visto, "t");
});

test("conflicto al guardar conserva texto local y no habilita aprobación", async () => {
  const ui = entorno(async () => ({ok: false, status: 409, redirected: false,
    headers: {get: () => "application/json"}, json: async () => ({texto_editorial: "Ajeno"})}));
  ui.editor.value = "Texto local";
  ui.editor.input();
  await ui.procesar();
  assert.equal(ui.editor.value, "Texto local");
  assert.ok(ui.almacen.size > 0);
  assert.equal(ui.aprobar.disabled, true);
});

test("fallo de red conserva estado sin guardar y no se presenta como aprobado", async () => {
  const ui = entorno(async () => {throw new Error("Sin conexión");});
  ui.editor.value = "Texto recuperable";
  ui.editor.input();
  await ui.procesar();
  assert.ok(ui.almacen.size > 0);
  assert.equal(ui["emitir-boton"].disabled, true);
  assert.match(ui.errores.textContent, /guardar|conexión/i);
});

test("recargar recupera pendiente local sin declararlo guardado ni aprobado", async () => {
  const almacen = new Map();
  const primero = entorno(async () => {throw new Error("Sin conexión");}, {almacen});
  primero.editor.value = "Pendiente local tras recarga";
  primero.editor.input();
  const nuevo = entorno(async () => exito(), {almacen});
  assert.equal(nuevo.editor.value, "Pendiente local tras recarga");
  assert.equal(nuevo["emitir-boton"].disabled, true);
  assert.equal(nuevo.estado.textContent, "Pendiente");
});

test("logout y cambio de sesión limpian recuperación sin aplicarla al nuevo usuario", () => {
  const almacen = new Map();
  const primero = entorno(async () => exito(), {almacen});
  primero.editor.value = "Pendiente de sesión previa";
  primero.editor.input();
  assert.ok(almacen.size > 0);
  const nuevo = entorno(async () => exito(), {almacen, sesion: "s2"});
  assert.equal(nuevo.editor.value, "");
  assert.equal(almacen.size, 0);
  nuevo.editor.value = "Pendiente actual";
  nuevo.editor.input();
  nuevo.eventos.logout({});
  assert.equal(almacen.size, 0);
});

test("storage deshabilitado avisa y sigue permitiendo guardar por servidor", async () => {
  const pedidos = [];
  const ui = entorno(async (url) => {pedidos.push(url); return exito();}, {sinStorage: true});
  ui.editor.value = "Texto sin recovery local";
  assert.doesNotThrow(() => ui.editor.input());
  await ui.procesar();
  assert.deepEqual(pedidos, ["/guardar/"]);
});

test("Volver espera el guardado antes de navegar", async () => {
  const pedidos = [];
  const ui = entorno(async (url) => {pedidos.push(url); return exito();});
  ui.editor.value = "Texto antes de salir";
  ui.editor.input();
  await ui.volver.click({preventDefault() {}});
  assert.deepEqual(pedidos, ["/guardar/"]);
  assert.deepEqual(ui.navegaciones, ["/estudio/1/"]);
});

test("editar revoca inmediatamente opción de incorporar aprobación anterior", () => {
  const ui = entorno(async () => exito(), {inicial: {revision: 1, huella_hechos: "h",
    huella_texto: "t", aprobada: true, texto_editorial: "Texto aprobado", texto_final: "Texto aprobado",
    advertencias: []}});
  assert.equal(ui["emitir-boton"].disabled, false);
  ui.editor.value = "Texto distinto";
  ui.editor.input();
  assert.equal(ui.revision.disabled, true);
  assert.equal(ui["emitir-boton"].disabled, true);
  assert.notEqual(ui.emitir.disabled, true);
});

test("proponer espera edición guardada antes de reemplazar y usa revisión nueva", async () => {
  const pedidos = [];
  const ui = entorno(async (url, opciones) => {pedidos.push({url, opciones}); return exito();});
  ui.editor.value = "Edición pendiente";
  ui.editor.input();
  await ui.proponer.click();
  assert.deepEqual(pedidos.map(p => p.url), ["/guardar/", "/proponer/"]);
  assert.equal(JSON.parse(pedidos[1].opciones.body).revision_esperada, 1);
});

test("pérdida de autorización elimina recuperación y no instala respuesta", async () => {
  const ui = entorno(async () => ({ok: false, status: 403, redirected: false,
    headers: {get: () => "application/json"}, json: async () => ({error: "Sin permiso"})}));
  ui.editor.value = "No debe quedar recuperable tras revocar acceso";
  ui.editor.input();
  await ui.procesar();
  assert.equal(ui.almacen.size, 0);
  assert.equal(ui.aprobar.disabled, true);
});

test("emisión con conclusión rechaza la aprobación invalidada por el guardado", async () => {
  const pedidos = [];
  const ui = entorno(async (url) => {pedidos.push(url); return exito();});
  ui.editor.value = "Texto conservado antes de emitir";
  ui.editor.input();
  await ui.emitir.submit({preventDefault() {}});
  assert.deepEqual(pedidos, ["/guardar/"]);
  assert.notEqual(ui.eventos.enviado, true);
  assert.match(ui.errores.textContent, /nueva aprobación/);
});

test("edición durante guardado serializa solicitudes y no pierde el texto nuevo", async () => {
  const pedidos = [];
  let completar;
  const ui = entorno((url, opciones) => {
    pedidos.push(JSON.parse(opciones.body));
    if (pedidos.length === 1) return new Promise(resolve => {completar = resolve;});
    return Promise.resolve(exito({revision: 2, texto_editorial: "Segundo texto"}));
  });
  ui.editor.value = "Primer texto";
  ui.editor.input();
  const primero = ui.procesar();
  await new Promise(resolve => setImmediate(resolve));
  ui.editor.value = "Segundo texto";
  ui.editor.input();
  const segundo = ui.procesar();
  assert.equal(pedidos.length, 1);
  completar(exito({revision: 1, texto_editorial: "Primer texto"}));
  await primero;
  await segundo;
  await ui.procesar();
  assert.equal(pedidos.length, 2);
  assert.equal(pedidos[1].revision_esperada, 1);
  assert.equal(pedidos[1].texto, "Segundo texto");
  assert.equal(ui.editor.value, "Segundo texto");
});

for (const motivo of ["sin_configuracion", "no_disponible", "cuota", "respuesta_invalida",
                       "plazo", "capacidad", "tamano"]) {
  for (const parcial of [false, true]) {
    test(`plantilla ${motivo}, parcial=${parcial}: editable y nunca autoaprobada`, async () => {
      const pedidos = [];
      const ui = entorno(async (url) => {
        pedidos.push(url);
        return exito({origen_propuesta: "plantilla", motivo_respaldo: motivo,
          aviso_respaldo: "SECRETO-HTTP-NO-MOSTRAR", texto_editorial: "Plantilla sintética",
          texto_final: parcial ? "Plantilla sintética\nAdvertencia" : "Plantilla sintética",
          advertencias: parcial ? ["Advertencia"] : [],
          hechos: {clase: parcial ? "parcial" : "con_incumplimientos", pruebas: []}});
      });
      assert.equal(ui.editor.readOnly, false);
      await ui.proponer.click();
      assert.equal(ui.estado.textContent, "Pendiente");
      assert.match(ui.respaldo.textContent, /plantilla/i);
      assert.doesNotMatch(ui.respaldo.textContent, /SECRETO/);
      assert.equal(ui["emitir-boton"].disabled, true);
      assert.equal(ui["emitir-boton"].disabled, true);
      assert.deepEqual(pedidos, ["/proponer/"]);
      assert.equal(ui.eventos["aria-busy"], "false");
      assert.equal(ui.proponer.disabled, false);
      assert.notEqual(ui.sin.disabled, true);
      if (parcial) assert.match(ui.respaldo.textContent, /parcial/i);
      assert.equal(ui.editor.readOnly, false);
      ui.editor.value = "Texto de plantilla corregido";
      ui.editor.input();
      assert.equal(ui["emitir-boton"].disabled, true);
      assert.ok(ui.almacen.size > 0);
    });
  }
}

test("timeout del proveedor termina espera al recibir plantilla y permite continuar", async () => {
  let terminar;
  const ui = entorno(() => new Promise(resolve => {terminar = resolve;}));
  const pendiente = ui.proponer.click();
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(ui.eventos["aria-busy"], "true");
  assert.equal(ui.proponer.textContent, "Proponiendo…");
  assert.notEqual(ui.sin.disabled, true);
  terminar(exito({origen_propuesta: "plantilla", motivo_respaldo: "plazo"}));
  await pendiente;
  assert.equal(ui.eventos["aria-busy"], "false");
  assert.match(ui.respaldo.textContent, /plantilla/);
  assert.equal(ui.proponer.disabled, false);
});

for (const tipo of ["red", "json", "html", "respuesta_malformada"]) {
  test(`error ${tipo} finaliza espera sin divulgar detalles ni perder texto`, async () => {
    const secreto = "SECRETO-HTTP-NO-MOSTRAR";
    const ui = entorno(async () => {
      if (tipo === "red") throw new Error(secreto);
      if (tipo === "json") return {ok: false, status: 500,
        headers: {get: () => "application/json"},
        json: async () => ({error: secreto, errores: {texto: [secreto]}})};
      if (tipo === "respuesta_malformada") return {ok: true,
        headers: {get: () => "application/json"}, json: async () => {throw new Error(secreto);}};
      return {ok: false, status: 502, headers: {get: () => "text/html"}};
    }, {inicial: {revision: 1, huella_hechos: "h", texto_editorial: "Texto conservado"}});
    await ui.proponer.click();
    assert.equal(ui.editor.value, "Texto conservado");
    assert.doesNotMatch(ui.estado.textContent + ui.errores.textContent, /SECRETO/);
    assert.equal(ui.eventos["aria-busy"], "false");
    assert.equal(ui.proponer.disabled, false);
    assert.notEqual(ui.sin.disabled, true);
    assert.equal(ui.respaldo.textContent, "");
  });
}

test("409 tardío conserva edición local sin instalar plantilla ni aprobación", async () => {
  let terminar;
  const ui = entorno(() => new Promise(resolve => {terminar = resolve;}));
  const pendiente = ui.proponer.click();
  await new Promise(resolve => setImmediate(resolve));
  ui.editor.value = "Edición local más reciente";
  ui.editor.input();
  terminar({ok: false, status: 409, headers: {get: () => "application/json"},
    json: async () => ({revision: 3, huella_hechos: "h", texto_editorial: "Otra revisión",
      texto_final: "Otra revisión", aprobada: false})});
  await pendiente;
  assert.equal(ui.editor.value, "Edición local más reciente");
  assert.ok(ui.almacen.size > 0);
  assert.equal(ui.aprobar.disabled, true);
  assert.equal(ui["emitir-boton"].disabled, true);
  assert.match(ui.errores.textContent, /cambió/);
  assert.equal(ui.eventos["aria-busy"], "false");
});

test("emisión sin conclusión no espera una propuesta de IA en curso", async () => {
  let terminar;
  const ui = entorno(() => new Promise(resolve => {terminar = resolve;}));
  const pendiente = ui.proponer.click();
  await new Promise(resolve => setImmediate(resolve));
  await ui.sin.submit({preventDefault() {}});
  assert.equal(ui.eventos.sinConclusion, true);
  terminar(exito({origen_propuesta: "plantilla", motivo_respaldo: "plazo"}));
  await pendiente;
  assert.equal(ui["emitir-boton"].disabled, true);
});

test("403 durante propuesta es autorización perdida y jamás plantilla", async () => {
  const ui = entorno(async () => ({ok: false, status: 403,
    headers: {get: () => "application/json"}, json: async () => ({error: "SECRETO"})}));
  await ui.proponer.click();
  assert.match(ui.errores.textContent, /autorización/);
  assert.doesNotMatch(ui.errores.textContent, /plantilla|SECRETO/);
  assert.equal(ui.respaldo.textContent, "");
  assert.equal(ui.proponer.disabled, true);
});

test("fallback permite recovery de edición pendiente tras recarga sin aprobación", async () => {
  const almacen = new Map();
  const inicial = {revision: 2, huella_hechos: "h", texto_editorial: "Plantilla",
    texto_final: "Plantilla", origen_propuesta: "plantilla", motivo_respaldo: "capacidad",
    aprobada: false, advertencias: [], hechos: {clase: "parcial", pruebas: []}};
  const ui = entorno(async () => exito(inicial), {almacen});
  await ui.proponer.click();
  ui.editor.value = "Edición de plantilla pendiente";
  ui.editor.input();
  const recargado = entorno(async () => exito(inicial), {almacen, inicial});
  assert.equal(recargado.editor.value, "Edición de plantilla pendiente");
  assert.equal(recargado["emitir-boton"].disabled, true);
  assert.equal(recargado.estado.textContent, "Pendiente");
  assert.match(recargado.respaldo.textContent, /parcial/i);
});

test("respuesta de propuesta no reemplaza una edición local posterior", async () => {
  let terminar;
  const ui = entorno(() => new Promise(resolve => {terminar = resolve;}));
  const pendiente = ui.proponer.click();
  await new Promise(resolve => setImmediate(resolve));
  ui.editor.value = "Texto local posterior a la solicitud";
  ui.editor.input();
  terminar(exito({revision: 2, texto_editorial: "Plantilla del servidor",
    origen_propuesta: "plantilla", motivo_respaldo: "plazo"}));
  await pendiente;
  assert.equal(ui.editor.value, "Texto local posterior a la solicitud");
  assert.ok(ui.almacen.size > 0);
  assert.equal(ui["emitir-boton"].disabled, true);
  assert.equal(ui["emitir-boton"].disabled, true);
  assert.equal(ui.estado.textContent, "Pendiente");
});

test("primera propuesta vacía no pide confirmación", async () => {
  let llamadas = 0;
  const ui = entorno(async () => {llamadas += 1; return exito();}, {confirmar: () => false});
  await ui.proponer.click();
  assert.equal(llamadas, 1);
  assert.deepEqual(ui.confirmaciones, []);
});

test("cancelar reemplazo de un borrador conserva su texto sin llamar al servidor", async () => {
  const ui = entorno(async () => {assert.fail("No debe reemplazar el borrador");}, {
    inicial: {revision: 3, huella_hechos: "h", texto_editorial: "Conclusión previa"},
    confirmar: () => false,
  });
  await ui.proponer.click();
  assert.equal(ui.editor.value, "Conclusión previa");
  assert.equal(ui.confirmaciones.length, 1);
});

test("aprobar guarda la edición directa y confirma texto y advertencias sin panel duplicado", async () => {
  const pedidos = [];
  const ui = entorno(async (url, opciones) => {
    pedidos.push({url, datos: JSON.parse(opciones.body)});
    return exito({revision: pedidos.length, texto_editorial: "Edición directa",
      texto_final: "Edición directa\n\nAdvertencia protegida", advertencias: ["Advertencia protegida"],
      aprobada: url === "/aprobar/"});
  });
  ui.editor.value = "Edición directa";
  ui.editor.input();
  await ui.aprobar.click();
  assert.deepEqual(pedidos.map(p => p.url), ["/guardar/", "/aprobar/"]);
  assert.equal(pedidos[0].datos.texto, "Edición directa");
  assert.equal(pedidos[1].datos.huella_texto_visto, "t");
  assert.equal(pedidos[1].datos.confirmacion, true);
  assert.equal(ui.advertencias.textContent, "Advertencia protegida");
  assert.equal(ui.estado.textContent, "Aprobada");
});

test("conflicto solo se reemplaza mediante nueva propuesta confirmada", async () => {
  const pedidos = [];
  const ui = entorno(async (url, opciones) => {
    pedidos.push({url, datos: JSON.parse(opciones.body)});
    if (url === "/guardar/") return {ok: false, status: 409,
      headers: {get: () => "application/json"}, json: async () => ({revision: 3,
        huella_hechos: "actual", texto_editorial: "De otra pestaña", aprobada: false})};
    return exito({revision: 4, texto_editorial: "Nueva propuesta"});
  });
  ui.editor.value = "Edición local conservada";
  ui.editor.input();
  await ui.procesar();
  assert.equal(ui.editor.value, "Edición local conservada");
  assert.equal(ui.aprobar.disabled, true);
  await ui.proponer.click();
  assert.equal(pedidos.length, 2);
  assert.equal(pedidos[1].url, "/proponer/");
  assert.equal(pedidos[1].datos.revision_esperada, 3);
  assert.equal(ui.editor.value, "Nueva propuesta");
  assert.equal(ui.confirmaciones.length, 1);
});

test("emisión aprobada usa la revisión vigente sin casilla adicional", async () => {
  const ui = entorno(async () => {assert.fail("No necesita guardar ni regenerar");}, {
    inicial: {revision: 3, huella_hechos: "h", aprobada: true,
      texto_editorial: "Conclusión aprobada", texto_final: "Conclusión aprobada"},
  });
  assert.equal(ui["emitir-boton"].disabled, false);
  await ui.emitir.submit({preventDefault() {}});
  assert.equal(ui.eventos.enviado, true);
  assert.equal(ui.revision.value, 3);
  assert.equal(ui.revision.disabled, false);
  assert.equal(ui.confirmaciones.length, 1);
});

test("recuperación silenciosa vuelve a autoguardar sin aprobar", async () => {
  const almacen = new Map();
  const anterior = entorno(async () => {throw new Error("Sin conexión");}, {almacen});
  anterior.editor.value = "Texto pendiente de la recarga";
  anterior.editor.input();
  const pedidos = [];
  const nuevo = entorno(async (url, opciones) => {
    pedidos.push({url, datos: JSON.parse(opciones.body)});
    return exito({texto_editorial: "Texto pendiente de la recarga"});
  }, {almacen});
  assert.equal(nuevo.estado.textContent, "Pendiente");
  assert.equal(nuevo.errores.textContent, "");
  await nuevo.procesar();
  assert.equal(pedidos[0].url, "/guardar/");
  assert.equal(pedidos[0].datos.texto, "Texto pendiente de la recarga");
  assert.equal(nuevo.almacen.size, 0);
  assert.equal(nuevo["emitir-boton"].disabled, true);
});
