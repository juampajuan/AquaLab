// Al volver al dashboard con «atrás», vuelve a donde estaba (ajuste de la revisión del sprint 4).
// Las páginas con sesión se sirven sin caché (usuarios/middleware.py): al volver, el navegador
// recarga el dashboard y no siempre recupera la posición. Se guarda al salir y se repone solo al
// volver con «atrás» o «adelante»; si se entra por el menú o se elige otro período, arranca arriba.
(function () {
  "use strict";
  var clave = "aqualab:dashboard:posicion:" + window.location.search;

  function leer() {
    try {
      return window.sessionStorage.getItem(clave);
    } catch (e) {
      return null; // almacenamiento bloqueado: se comporta como antes
    }
  }

  function guardar() {
    try {
      window.sessionStorage.setItem(clave, String(Math.round(window.scrollY)));
    } catch (e) {
      // almacenamiento bloqueado: no se recuerda la posición
    }
  }

  function volvioConAtras() {
    var rendimiento = window.performance;
    if (!rendimiento || typeof rendimiento.getEntriesByType !== "function") return false;
    var entradas = rendimiento.getEntriesByType("navigation");
    return entradas.length > 0 && entradas[0].type === "back_forward";
  }

  function reponer() {
    var guardada = Number(leer());
    if (volvioConAtras() && guardada > 0) window.scrollTo(0, guardada);
  }

  window.addEventListener("pagehide", guardar);
  // «load» llega después de los gráficos (dashboard.js dibuja en DOMContentLoaded).
  if (document.readyState === "complete") {
    reponer();
  } else {
    window.addEventListener("load", reponer);
  }
})();
