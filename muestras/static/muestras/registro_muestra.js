(() => {
  "use strict";

  const datos = document.getElementById("clientes-muestra");
  const selectCliente = document.getElementById("id_cliente");
  const selectOrigen = document.getElementById("id_origen");
  if (!datos || !selectCliente || !selectOrigen) return;

  const clientes = new Map(JSON.parse(datos.textContent).map((c) => [String(c.id), c]));
  const ficha = document.getElementById("ficha-cliente");
  const origenNuevo = document.getElementById("id_origen_nuevo");
  const bloqueOrigen = document.getElementById("bloque-origen");
  const bloqueOrigenNuevo = document.getElementById("bloque-origen-nuevo");
  const botonOrigenNuevo = document.getElementById("mostrar-origen-nuevo");

  // La lista de orígenes solo se muestra si el cliente elegido tiene orígenes: sin cliente no hay
  // qué elegir y sin orígenes la única opción es uno nuevo (spec 007, casos borde). Se mantiene
  // visible si muestra un error del servidor.
  function actualizarListaOrigenes(cliente, mantenerSiHayError) {
    if (!bloqueOrigen) return;
    const conError = mantenerSiHayError && selectOrigen.classList.contains("is-invalid");
    bloqueOrigen.hidden = !(cliente && cliente.origenes.length > 0) && !conError;
  }

  function mostrarFicha(cliente) {
    ficha.hidden = !cliente;
    if (!cliente) return;
    ficha.querySelector('[data-ficha="razon_social_o_nombre"]').textContent =
      cliente.razon_social_o_nombre;
    ficha.querySelector('[data-ficha="documento"]').textContent =
      `${cliente.tipo_documento} ${cliente.numero_documento}`;
    ficha.querySelector('[data-ficha="email"]').textContent = cliente.email;
  }

  function cargarOrigenes(cliente) {
    // La primera opción es "Elegí un origen"; el resto se reemplaza por los del cliente.
    while (selectOrigen.options.length > 1) selectOrigen.remove(1);
    for (const origen of cliente ? cliente.origenes : []) {
      selectOrigen.add(new Option(origen.nombre, origen.id));
    }
    selectOrigen.value = "";
  }

  // El link solo tiene sentido con un cliente elegido y el campo de origen nuevo oculto.
  function actualizarBotonOrigenNuevo() {
    if (!botonOrigenNuevo) return;
    botonOrigenNuevo.hidden = !clientes.get(selectCliente.value) || !bloqueOrigenNuevo.hidden;
  }

  function mostrarOrigenNuevo() {
    bloqueOrigenNuevo.hidden = false;
    actualizarBotonOrigenNuevo();
    selectOrigen.value = "";
    origenNuevo.focus();
  }

  selectCliente.addEventListener("change", () => {
    const cliente = clientes.get(selectCliente.value);
    mostrarFicha(cliente);
    cargarOrigenes(cliente);
    // Un origen nuevo escrito para otro cliente no debe quedar como origen del elegido.
    if (origenNuevo) origenNuevo.value = "";
    // Sin orígenes, el campo nuevo es la única opción; con orígenes o sin cliente, vuelve a cerrarse.
    bloqueOrigenNuevo.hidden = !(cliente && cliente.origenes.length === 0);
    actualizarListaOrigenes(cliente, false);
    actualizarBotonOrigenNuevo();
  });

  // Sin JavaScript el campo de origen nuevo queda siempre visible; con él, se abre a pedido.
  if (origenNuevo && bloqueOrigenNuevo && botonOrigenNuevo) {
    const elegido = clientes.get(selectCliente.value);
    const sinOrigenes = elegido && elegido.origenes.length === 0;
    const conError = origenNuevo.classList.contains("is-invalid");
    bloqueOrigenNuevo.hidden = !origenNuevo.value && !conError && !sinOrigenes;
    actualizarListaOrigenes(elegido, true);
    actualizarBotonOrigenNuevo();
    botonOrigenNuevo.addEventListener("click", mostrarOrigenNuevo);
    origenNuevo.addEventListener("input", () => {
      if (origenNuevo.value.trim()) selectOrigen.value = "";
    });
    selectOrigen.addEventListener("change", () => {
      if (selectOrigen.value) origenNuevo.value = "";
    });
  }
})();
