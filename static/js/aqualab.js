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

// Asistente de consultas (US 10.1, contracts/preguntar.md): panel de ui/asistente.html. La
// conversación vive solo en memoria (FR-019); se mandan los últimos 6 mensajes, cada uno recortado
// a 4000 caracteres. Todo texto se agrega con textContent: nunca HTML del servicio.
const ASISTENTE_MAX_HISTORIAL = 6;
const ASISTENTE_MAX_TEXTO = 4000;
const ASISTENTE_NO_DISPONIBLE =
  "El asistente no está disponible en este momento. Probá de nuevo más tarde o usá las pantallas de AquaLab.";
const ASISTENTE_SESION_VENCIDA = "Tu sesión venció; volvé a iniciar sesión";
const asistente = { historial: [], enviando: false };

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

function asistenteAbrir(boton) {
  const panel = document.querySelector("[data-asistente]");
  if (!panel || boton.getAttribute("aria-disabled") === "true") return;
  panel.hidden = false;
  boton.setAttribute("aria-expanded", "true");
  const campo = panel.querySelector("[data-asistente-pregunta]");
  if (campo) campo.focus();
}

function asistenteCerrar() {
  const panel = document.querySelector("[data-asistente]");
  if (!panel || panel.hidden) return false;
  panel.hidden = true;
  // Cerrar el panel borra la conversación (FR-019).
  asistente.historial = [];
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

function asistenteAgregar(panel, rol, texto, enlaces = []) {
  const lista = panel.querySelector("[data-asistente-mensajes]");
  const item = document.createElement("li");
  item.setAttribute("data-asistente-mensaje", rol);
  item.className =
    rol === "usuario"
      ? "ml-8 rounded-lg bg-marino px-3 py-2 text-white"
      : rol === "aviso"
        ? "aviso aviso-error"
        : "mr-4 rounded-lg bg-fondo-hundido px-3 py-2 text-tinta";
  if (rol === "aviso") item.setAttribute("role", "alert");
  const parrafo = document.createElement("p");
  parrafo.className = "whitespace-pre-line";
  parrafo.textContent = texto;
  item.append(parrafo);
  if (enlaces.length) {
    const lista_enlaces = document.createElement("ul");
    lista_enlaces.className = "mt-2 flex flex-wrap gap-x-3 gap-y-1";
    for (const enlace of enlaces) {
      const elemento = document.createElement("li");
      const a = document.createElement("a");
      a.className = "btn-link";
      a.href = enlace.url;
      a.textContent = enlace.etiqueta;
      elemento.append(a);
      lista_enlaces.append(elemento);
    }
    item.append(lista_enlaces);
  }
  lista.append(item);
  if (typeof item.scrollIntoView === "function") item.scrollIntoView({ block: "end" });
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
      asistenteAgregar(panel, "asistente", datos.texto, datos.enlaces || []);
      asistente.historial.push({ rol: "usuario", texto: pregunta });
      asistente.historial.push({ rol: "asistente", texto: datos.texto });
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

document.addEventListener("click", (evento) => {
  const abrir = evento.target.closest("[data-asistente-abrir]");
  if (abrir) {
    const panel = document.querySelector("[data-asistente]");
    if (panel && !panel.hidden) asistenteCerrar();
    else asistenteAbrir(abrir);
    return;
  }
  if (evento.target.closest("[data-asistente-cerrar]")) {
    asistenteCerrar();
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
  if (evento.key === "Escape" && document.querySelector("[data-asistente]")) asistenteCerrar();
});

document.addEventListener("input", (evento) => {
  const campo = evento.target.closest("[data-asistente-pregunta]");
  if (campo) asistenteContar(campo);
});
