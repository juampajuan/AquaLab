// Comportamientos mínimos de la interfaz (sin dependencias).
document.addEventListener("click", (evento) => {
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
    boton.setAttribute("aria-expanded", String(abierto));
  }
});
