// Al volver al dashboard con «atrás», vuelve a donde estaba (ajuste de la revisión del sprint 4).
//
// Dos casos, según el navegador:
// - Lo recarga (las páginas con sesión se sirven sin caché, usuarios/middleware.py): se repone
//   la posición guardada al terminar de cargar.
// - Lo trae de memoria (bfcache): la guardia de sesión (usuarios/static/usuarios/sesion.js)
//   oculta la página mientras verifica la sesión, y al quedar vacía salta arriba. Se espera a
//   que se vuelva a mostrar y recién ahí se repone.
// La posición se guarda mientras se desplaza, nunca con la página oculta (valdría 0). Si se
// entra por el menú o se elige otro período, arranca arriba.
(function () {
  "use strict";
  var clave = "aqualab:dashboard:posicion:" + window.location.search;
  var raiz = document.documentElement;
  var programado = false;

  function oculta() {
    return raiz.classList.contains("sesion-oculta");
  }

  function leer() {
    try {
      return Number(window.sessionStorage.getItem(clave)) || 0;
    } catch (e) {
      return 0; // almacenamiento bloqueado: se comporta como antes
    }
  }

  function guardar() {
    programado = false;
    if (oculta()) return;
    try {
      window.sessionStorage.setItem(clave, String(Math.round(window.scrollY)));
    } catch (e) {
      // almacenamiento bloqueado: no se recuerda la posición
    }
  }

  function alDesplazar() {
    if (programado) return;
    programado = true;
    window.requestAnimationFrame(guardar);
  }

  function reponer() {
    var posicion = leer();
    if (!posicion) return;
    if (!oculta()) {
      window.scrollTo(0, posicion);
      return;
    }
    var observador = new window.MutationObserver(function () {
      if (oculta()) return;
      observador.disconnect();
      window.scrollTo(0, posicion);
    });
    observador.observe(raiz, { attributes: true, attributeFilter: ["class"] });
  }

  function volvioConAtras() {
    var rendimiento = window.performance;
    if (!rendimiento || typeof rendimiento.getEntriesByType !== "function") return false;
    var entradas = rendimiento.getEntriesByType("navigation");
    return entradas.length > 0 && entradas[0].type === "back_forward";
  }

  window.addEventListener("scroll", alDesplazar, { passive: true });
  window.addEventListener("pagehide", guardar);
  window.addEventListener("pageshow", function (evento) {
    if (evento.persisted) reponer(); // vuelve de memoria
  });
  // Recargado: «load» llega después de los gráficos (dashboard.js dibuja en DOMContentLoaded).
  function alCargar() {
    if (volvioConAtras()) reponer();
  }
  if (document.readyState === "complete") {
    alCargar();
  } else {
    window.addEventListener("load", alCargar);
  }
})();
