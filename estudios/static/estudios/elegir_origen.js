// Selector de cliente y origen de la comparación histórica (US 8.1). Al cambiar el cliente, deja en
// la lista de orígenes solo los suyos (sin grupos). Lee el json_script "origenes-por-cliente":
// {cliente_pk: [[origen_pk, nombre], …]}. Sin JavaScript, los orígenes quedan agrupados por cliente
// y el formulario rechaza uno de otro cliente.
(function () {
  "use strict";

  // Opciones de orígenes para el cliente elegido: [[valor, texto], …] con la opción vacía primero.
  function opciones(porCliente, cliente) {
    var lista = [["", "Elegí un origen"]];
    (porCliente[cliente] || []).forEach(function (origen) {
      lista.push([String(origen[0]), origen[1]]);
    });
    return lista;
  }

  function rearmar(documento, selectOrigen, porCliente, cliente) {
    var elegido = selectOrigen.value;
    var lista = opciones(porCliente, cliente);
    while (selectOrigen.firstChild) {
      selectOrigen.removeChild(selectOrigen.firstChild);
    }
    lista.forEach(function (opcion) {
      var nodo = documento.createElement("option");
      nodo.value = opcion[0];
      nodo.textContent = opcion[1];
      selectOrigen.appendChild(nodo);
    });
    var sigue = lista.some(function (opcion) {
      return opcion[0] === elegido;
    });
    selectOrigen.value = sigue ? elegido : "";
  }

  function activar(documento) {
    var datos = documento.getElementById("origenes-por-cliente");
    var formulario = documento.querySelector("[data-elegir-origen]");
    if (!datos || !formulario) {
      return;
    }
    var porCliente = JSON.parse(datos.textContent);
    var selectCliente = formulario.querySelector('select[name="cliente"]');
    var selectOrigen = formulario.querySelector('select[name="origen"]');
    if (!selectCliente || !selectOrigen) {
      return;
    }
    if (selectCliente.value) {
      rearmar(documento, selectOrigen, porCliente, selectCliente.value);
    }
    selectCliente.addEventListener("change", function () {
      rearmar(documento, selectOrigen, porCliente, selectCliente.value);
    });
  }

  window.AqualabElegirOrigen = { opciones: opciones, rearmar: rearmar, activar: activar };

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () {
      activar(document);
    });
  } else {
    activar(document);
  }
})();
