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
