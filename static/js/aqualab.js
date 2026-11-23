// Comportamientos mínimos de la interfaz (sin dependencias).

// Ayuda de los campos (ui/ayuda.html, US 9.1). El CSS ya la muestra con hover y con el foco del
// teclado; acá se suman el toque, Escape y que nunca haya dos abiertas. Estados: data-abierta
// (abierta con un clic o toque) y data-cerrada (cerrada aunque tenga hover o foco).
const AYUDA = "[data-ayuda]";
let ayudaBajoElPuntero = null;

function cerrarOtrasAyudas(actual) {
  for (const ayuda of document.querySelectorAll(AYUDA)) {
    if (ayuda !== actual) {
      ayuda.removeAttribute("data-abierta");
      ayuda.setAttribute("data-cerrada", "");
    }
  }
}

function activarAyuda(ayuda) {
  cerrarOtrasAyudas(ayuda);
  ayuda.removeAttribute("data-cerrada");
}

document.addEventListener("click", (evento) => {
  // Ayuda: un clic o toque en el ícono la abre o la cierra; fuera de toda ayuda, la cierra.
  const ayuda = evento.target.closest(AYUDA);
  if (!ayuda) {
    for (const abierta of document.querySelectorAll("[data-ayuda][data-abierta]")) {
      abierta.removeAttribute("data-abierta");
    }
  } else if (evento.target.closest(".ayuda-boton")) {
    if (ayuda.hasAttribute("data-abierta")) {
      ayuda.removeAttribute("data-abierta");
      ayuda.setAttribute("data-cerrada", "");
    } else {
      activarAyuda(ayuda);
      ayuda.setAttribute("data-abierta", "");
    }
    return;
  }

  // Cerrar un mensaje (ui/mensajes.html).
  const cerrar = evento.target.closest("[data-cerrar-mensaje]");
  if (cerrar) {
    cerrar.closest("[data-nivel]").remove();
    return;
  }

  // Abrir o cerrar el menú lateral en pantallas angostas (base.html).
  const boton = evento.target.closest("[data-menu-boton]");
  if (boton) {
    const menu = document.querySelector("[data-menu]");
    const abierto = menu.classList.toggle("max-lg:hidden") === false;
    for (const b of document.querySelectorAll("[data-menu-boton][aria-expanded]")) {
      b.setAttribute("aria-expanded", String(abierto));
    }
  }
});

// Ayuda: Escape cierra la activa (la enfocada, la que está bajo el mouse o la abierta) sin mover
// el foco. Queda cerrada hasta que el foco o el mouse salgan de ella.
document.addEventListener("keydown", (evento) => {
  if (evento.key !== "Escape") return;
  const activa =
    document.activeElement?.closest?.(AYUDA) ||
    ayudaBajoElPuntero ||
    document.querySelector("[data-ayuda][data-abierta]");
  if (activa) {
    activa.removeAttribute("data-abierta");
    activa.setAttribute("data-cerrada", "");
  }
});

// Ayuda: entrar con el mouse o con el foco la activa y cierra las demás. Moverse entre el ícono
// y el texto de la misma ayuda no cuenta como entrar de nuevo (respeta un Escape previo).
document.addEventListener("pointerover", (evento) => {
  const ayuda = evento.target.closest(AYUDA);
  if (ayuda && ayuda !== ayudaBajoElPuntero) {
    ayudaBajoElPuntero = ayuda;
    activarAyuda(ayuda);
  }
});

document.addEventListener("focusin", (evento) => {
  const ayuda = evento.target.closest(AYUDA);
  if (ayuda) activarAyuda(ayuda);
});

// Ayuda: salir con el mouse del ícono y del texto la cierra; pasar del ícono al texto no
// (WCAG 1.4.13). Al levantar el dedo también hay pointerout: con un toque, la ayuda sigue abierta
// hasta otro toque.
document.addEventListener("pointerout", (evento) => {
  const ayuda = evento.target.closest(AYUDA);
  if (!ayuda || (evento.relatedTarget && ayuda.contains(evento.relatedTarget))) return;
  ayudaBajoElPuntero = null;
  if (evento.pointerType === "mouse") {
    ayuda.removeAttribute("data-abierta");
    ayuda.removeAttribute("data-cerrada");
  }
});

// Ayuda: al salir con el foco (Tab) se cierra y se limpia el Escape para la próxima vez.
document.addEventListener("focusout", (evento) => {
  const ayuda = evento.target.closest(AYUDA);
  if (!ayuda || (evento.relatedTarget && ayuda.contains(evento.relatedTarget))) return;
  ayuda.removeAttribute("data-abierta");
  ayuda.removeAttribute("data-cerrada");
});

// Fechas dd/mm/aaaa (muestras/forms.py:SelectorFecha): mientras se escribe, deja solo dígitos y
// agrega las barras. Si se borra, no las vuelve a poner sobre lo que el usuario sacó.
function formatearFecha(texto) {
  const digitos = texto.replace(/\D/g, "").slice(0, 8);
  if (digitos.length <= 2) return digitos;
  if (digitos.length <= 4) return `${digitos.slice(0, 2)}/${digitos.slice(2)}`;
  return `${digitos.slice(0, 2)}/${digitos.slice(2, 4)}/${digitos.slice(4)}`;
}

document.addEventListener("input", (evento) => {
  const campo = evento.target.closest("[data-fecha]");
  if (!campo || evento.inputType === "deleteContentBackward") return;
  campo.value = formatearFecha(campo.value);
});

// Asistente de consultas (US 10.1, contracts/preguntar.md): panel de ui/asistente.html. Se
// mandan los últimos 6 mensajes, cada uno recortado a 4000 caracteres. Todo texto se agrega con
// textContent: nunca HTML del servicio. La conversación se guarda en sessionStorage de la pestaña
// para seguirla al navegar (FR-019). Minimizar (el «–», el botón flotante o Escape) oculta el panel
// y la conserva; la ✕, una pantalla sin panel (login) o cerrar sesión la borran. Nada va a la base.
const ASISTENTE_MAX_HISTORIAL = 6;
const ASISTENTE_MAX_TEXTO = 4000;
const ASISTENTE_CLAVE = "aqualab.asistente";
const ASISTENTE_NO_DISPONIBLE =
  "El asistente no está disponible en este momento. Probá de nuevo más tarde o usá las pantallas de AquaLab.";
const ASISTENTE_SESION_VENCIDA = "Tu sesión venció; volvé a iniciar sesión";
const asistente = { historial: [], mensajes: [], enviando: false, abierto: false };

function asistenteAlmacen() {
  try {
    return typeof sessionStorage === "undefined" ? null : sessionStorage;
  } catch {
    return null;
  }
}

function asistenteDesplazamiento() {
  const lista = document.querySelector("[data-asistente-mensajes]");
  return lista && typeof lista.scrollTop === "number" ? lista.scrollTop : null;
}

function asistenteGuardar() {
  const almacen = asistenteAlmacen();
  if (!almacen) return;
  try {
    almacen.setItem(
      ASISTENTE_CLAVE,
      JSON.stringify({
        mensajes: asistente.mensajes,
        historial: asistente.historial,
        abierto: asistente.abierto,
        desplazamiento: asistenteDesplazamiento(),
      }),
    );
  } catch {
    // Sin almacenamiento la conversación sigue en la página abierta.
  }
}

function asistenteOlvidar() {
  const almacen = asistenteAlmacen();
  if (!almacen) return;
  try {
    almacen.removeItem(ASISTENTE_CLAVE);
  } catch {
    // Nada que borrar.
  }
}

function asistenteHistorial() {
  return asistente.historial
    .slice(-ASISTENTE_MAX_HISTORIAL)
    .map((m) => ({ rol: m.rol, texto: m.texto.slice(0, ASISTENTE_MAX_TEXTO) }));
}

function asistenteCsrf(panel) {
  const campo = panel.querySelector("[name=csrfmiddlewaretoken]");
  if (campo && campo.value) return campo.value;
  const cookie = (document.cookie || "").split(";").map((c) => c.trim());
  const valor = cookie.find((c) => c.startsWith("csrftoken="));
  return valor ? decodeURIComponent(valor.slice("csrftoken=".length)) : "";
}

function asistenteMostrar(panel, boton) {
  panel.hidden = false;
  asistente.abierto = true;
  if (boton) boton.setAttribute("aria-expanded", "true");
}

// Minimizar: oculta el panel y conserva la conversación (también al navegar).
function asistenteMinimizar() {
  const panel = document.querySelector("[data-asistente]");
  if (!panel || panel.hidden) return false;
  panel.hidden = true;
  asistente.abierto = false;
  asistenteGuardar();
  const boton = document.querySelector("[data-asistente-abrir]");
  if (boton) {
    boton.setAttribute("aria-expanded", "false");
    boton.focus();
  }
  return true;
}

function asistenteAbrir(boton) {
  const panel = document.querySelector("[data-asistente]");
  if (!panel || boton.getAttribute("aria-disabled") === "true") return;
  asistenteMostrar(panel, boton);
  asistenteGuardar();
  const campo = panel.querySelector("[data-asistente-pregunta]");
  if (campo) campo.focus();
}

function asistenteCerrar() {
  const panel = document.querySelector("[data-asistente]");
  if (!panel || panel.hidden) return false;
  panel.hidden = true;
  asistente.abierto = false;
  // Cerrar con la ✕ borra la conversación (FR-019).
  asistente.historial = [];
  asistente.mensajes = [];
  asistenteOlvidar();
  const lista = panel.querySelector("[data-asistente-mensajes]");
  if (lista) {
    for (const mensaje of lista.querySelectorAll("[data-asistente-mensaje]")) mensaje.remove();
  }
  const boton = document.querySelector("[data-asistente-abrir]");
  if (boton) {
    boton.setAttribute("aria-expanded", "false");
    boton.focus();
  }
  return true;
}

// El texto del modelo: una línea en blanco separa párrafos; los bloques de líneas que empiezan
// con «- » van como lista; el resto, como párrafos que conservan sus saltos de línea. Los bloques
// quedan espaciados para que se lean mejor. Siempre con textContent.
function asistenteTexto(item, texto) {
  let parrafo = [];
  let lista = null;
  let ultimo = null;
  const cerrarParrafo = () => {
    if (!parrafo.length) return;
    const p = document.createElement("p");
    p.className = "whitespace-pre-line";
    p.textContent = parrafo.join("\n");
    item.append(p);
    parrafo = [];
  };
  for (const linea of String(texto).split("\n")) {
    if (lista && ultimo && (/^\s{2,}\S/.test(linea) || /^[^\s:-][^:]{0,24}:\s+\S/.test(linea))) {
      // Dato del ítem anterior en su propio renglón («  Estado: …» o «Estado: …» justo debajo).
      ultimo.textContent = `${ultimo.textContent}\n${linea.trim()}`;
    } else if (linea.startsWith("- ")) {
      cerrarParrafo();
      if (!lista) {
        lista = document.createElement("ul");
        lista.className = "list-disc space-y-1 pl-5";
        item.append(lista);
      }
      const li = document.createElement("li");
      li.className = "whitespace-pre-line";
      li.textContent = linea.slice(2);
      lista.append(li);
      ultimo = li;
    } else if (!linea.trim()) {
      cerrarParrafo();
      lista = null;
    } else {
      lista = null;
      parrafo.push(linea);
    }
  }
  cerrarParrafo();
}

// Enlaces de la respuesta: los comunes llevan a su pantalla; las opciones para elegir (con
// `pregunta`, las marca AquaLab) son botones que siguen la conversación, con un ↗ para abrir si
// tienen pantalla (un origen o un tipo de estudio no la tienen: US 10.3). El enlace al formulario
// precargado (`minimizar`) es el botón principal y minimiza el panel al seguirlo.
function asistenteEnlaces(item, enlaces) {
  const lista = document.createElement("ul");
  lista.className = "mt-2 flex flex-wrap gap-x-3 gap-y-1";
  for (const enlace of enlaces) {
    const elemento = document.createElement("li");
    if (enlace.pregunta) {
      elemento.className = "flex w-full min-w-0 items-center gap-2";
      const boton = document.createElement("button");
      boton.type = "button";
      boton.className = "btn btn-secundario btn-chico min-w-0 flex-1 justify-start text-left whitespace-normal";
      boton.setAttribute("data-asistente-elegir", enlace.pregunta);
      boton.setAttribute("title", enlace.pregunta);
      boton.textContent = enlace.etiqueta;
      elemento.append(boton);
      if (enlace.url) {
        const abrir = document.createElement("a");
        abrir.className = "btn-link shrink-0 whitespace-nowrap";
        abrir.href = enlace.url;
        abrir.setAttribute("aria-label", `Abrir ${enlace.etiqueta}`);
        abrir.textContent = enlace.ver || "Ver ficha";
        elemento.append(abrir);
      }
    } else if (enlace.minimizar) {
      const a = document.createElement("a");
      a.className = "btn btn-primario btn-chico";
      a.href = enlace.url;
      a.setAttribute("data-asistente-minimizar-al-seguir", "");
      a.textContent = enlace.etiqueta;
      elemento.append(a);
    } else {
      const a = document.createElement("a");
      a.className = "btn-link";
      a.href = enlace.url;
      a.textContent = enlace.etiqueta;
      elemento.append(a);
    }
    lista.append(elemento);
  }
  item.append(lista);
}

function asistenteAgregar(panel, rol, texto, enlaces = [], { guardar = true } = {}) {
  const lista = panel.querySelector("[data-asistente-mensajes]");
  const item = document.createElement("li");
  item.setAttribute("data-asistente-mensaje", rol);
  item.className =
    rol === "usuario"
      ? "ml-8 rounded-lg bg-marino px-3 py-2 text-white"
      : rol === "aviso"
        ? "aviso aviso-error"
        : "mr-4 space-y-2 rounded-lg bg-fondo-hundido px-3 py-2 leading-relaxed text-tinta";
  if (rol === "aviso") item.setAttribute("role", "alert");
  if (rol === "asistente") {
    asistenteTexto(item, texto);
  } else {
    const parrafo = document.createElement("p");
    parrafo.className = "whitespace-pre-line";
    parrafo.textContent = texto;
    item.append(parrafo);
  }
  if (enlaces.length) asistenteEnlaces(item, enlaces);
  lista.append(item);
  if (typeof item.scrollIntoView === "function") item.scrollIntoView({ block: "end" });
  if (guardar && rol !== "esperando") {
    asistente.mensajes.push({ rol, texto, enlaces });
    asistenteGuardar();
  }
  return item;
}

async function asistentePreguntar(formulario) {
  const panel = formulario.closest("[data-asistente]");
  const campo = formulario.querySelector("[data-asistente-pregunta]");
  const enviar = formulario.querySelector("[data-asistente-enviar]");
  const pregunta = campo.value.trim();
  if (!pregunta || asistente.enviando) return;
  asistente.enviando = true;
  enviar.disabled = true;
  asistenteAgregar(panel, "usuario", pregunta);
  const esperando = asistenteAgregar(panel, "esperando", "Consultando…");
  try {
    const respuesta = await fetch(panel.getAttribute("data-url"), {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json", "X-CSRFToken": asistenteCsrf(panel) },
      body: JSON.stringify({ pregunta, historial: asistenteHistorial() }),
    });
    const tipo = (respuesta.headers && respuesta.headers.get("Content-Type")) || "";
    let datos = null;
    if (!respuesta.redirected && tipo.includes("application/json")) {
      try {
        datos = await respuesta.json();
      } catch {
        datos = null;
      }
    }
    esperando.remove();
    if (!datos) {
      asistenteAgregar(panel, "aviso", ASISTENTE_SESION_VENCIDA);
    } else if (respuesta.ok) {
      asistente.historial.push({ rol: "usuario", texto: pregunta });
      asistente.historial.push({ rol: "asistente", texto: datos.texto });
      asistenteAgregar(panel, "asistente", datos.texto, datos.enlaces || []);
      campo.value = "";
    } else {
      asistenteAgregar(panel, "aviso", datos.mensaje || ASISTENTE_NO_DISPONIBLE);
    }
  } catch {
    esperando.remove();
    asistenteAgregar(panel, "aviso", ASISTENTE_NO_DISPONIBLE);
  } finally {
    asistente.enviando = false;
    enviar.disabled = false;
    asistenteContar(campo);
  }
}

function asistenteContar(campo) {
  const panel = campo.closest("[data-asistente]");
  const contador = panel && panel.querySelector("[data-asistente-contador]");
  if (contador) contador.textContent = `${campo.value.length}/500`;
}

// Al cargar la página: si la pestaña tenía el panel abierto, se reabre con la conversación. Una
// pantalla sin panel (login, registro, asistente sin configurar) la borra.
function asistenteRestaurar() {
  const panel = document.querySelector("[data-asistente]");
  if (!panel) {
    asistenteOlvidar();
    return;
  }
  const almacen = asistenteAlmacen();
  let guardado = null;
  try {
    guardado = almacen && JSON.parse(almacen.getItem(ASISTENTE_CLAVE) || "null");
  } catch {
    guardado = null;
  }
  if (!guardado || !Array.isArray(guardado.mensajes)) return;
  asistente.historial = Array.isArray(guardado.historial) ? guardado.historial : [];
  for (const mensaje of guardado.mensajes) {
    asistenteAgregar(panel, mensaje.rol, mensaje.texto, mensaje.enlaces || [], { guardar: false });
  }
  asistente.mensajes = guardado.mensajes;
  // Se reabre solo si estaba abierto; minimizado, la conversación queda lista para cuando se abra.
  if (guardado.abierto !== false) asistenteMostrar(panel, document.querySelector("[data-asistente-abrir]"));
  const lista = panel.querySelector("[data-asistente-mensajes]");
  if (lista && typeof lista.scrollHeight === "number") {
    const volver = () => {
      lista.scrollTop =
        typeof guardado.desplazamiento === "number" ? guardado.desplazamiento : lista.scrollHeight;
    };
    if (typeof requestAnimationFrame === "function") requestAnimationFrame(volver);
    else volver();
  }
}

// Antes de dejar la pantalla (por ejemplo, con «Ver ficha»), se guarda dónde quedó el scroll.
if (typeof window !== "undefined" && typeof window.addEventListener === "function") {
  window.addEventListener("pagehide", () => {
    if (asistente.mensajes.length) asistenteGuardar();
  });
}

document.addEventListener("click", (evento) => {
  const abrir = evento.target.closest("[data-asistente-abrir]");
  if (abrir) {
    const panel = document.querySelector("[data-asistente]");
    if (panel && !panel.hidden) asistenteMinimizar();
    else asistenteAbrir(abrir);
    return;
  }
  if (evento.target.closest("[data-asistente-minimizar]")) {
    asistenteMinimizar();
    return;
  }
  // El formulario precargado queda a la vista; la conversación se conserva (US 10.3). No se
  // previene la navegación.
  if (evento.target.closest("[data-asistente-minimizar-al-seguir]")) {
    asistenteMinimizar();
    return;
  }
  if (evento.target.closest("[data-asistente-cerrar]")) {
    asistenteCerrar();
    return;
  }
  const elegir = evento.target.closest("[data-asistente-elegir]");
  if (elegir) {
    const panel = elegir.closest("[data-asistente]") || document.querySelector("[data-asistente]");
    const campo = panel.querySelector("[data-asistente-pregunta]");
    campo.value = elegir.getAttribute("data-asistente-elegir");
    asistentePreguntar(campo.closest("[data-asistente-form]"));
    return;
  }
  const ejemplo = evento.target.closest("[data-asistente-ejemplo]");
  if (ejemplo) {
    const panel = ejemplo.closest("[data-asistente]");
    const campo = panel.querySelector("[data-asistente-pregunta]");
    campo.value = ejemplo.textContent.trim();
    asistenteContar(campo);
    campo.focus();
  }
});

document.addEventListener("submit", (evento) => {
  if (evento.target.closest("[data-cerrar-sesion]")) {
    asistenteOlvidar();
    return;
  }
  const formulario = evento.target.closest("[data-asistente-form]");
  if (!formulario) return;
  evento.preventDefault();
  asistentePreguntar(formulario);
});

document.addEventListener("keydown", (evento) => {
  // Enter pregunta; Shift+Enter agrega un salto de línea.
  const campo = evento.target && evento.target.closest && evento.target.closest("[data-asistente-pregunta]");
  if (campo && evento.key === "Enter" && !evento.shiftKey) {
    evento.preventDefault();
    asistentePreguntar(campo.closest("[data-asistente-form]"));
    return;
  }
  if (evento.key === "Escape" && document.querySelector("[data-asistente]")) asistenteMinimizar();
});

document.addEventListener("input", (evento) => {
  const campo = evento.target.closest("[data-asistente-pregunta]");
  if (campo) asistenteContar(campo);
});

asistenteRestaurar();

// Curva de calibración (US 6.6): al elegir el archivo se importan los puntos, sin un botón aparte.
// El botón «Importar puntos» queda solo para navegadores sin JavaScript.
for (const boton of document.querySelectorAll("[data-importar-boton]")) boton.hidden = true;

document.addEventListener("change", (evento) => {
  const campo = evento.target.closest && evento.target.closest("[data-importar-al-elegir]");
  if (!campo || !campo.files || !campo.files.length) return;
  const formulario = campo.closest("form");
  const boton = formulario && formulario.querySelector("[data-importar-boton]");
  if (!boton) return;
  if (formulario.requestSubmit) formulario.requestSubmit(boton);
  else boton.click();
});
