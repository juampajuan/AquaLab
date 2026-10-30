(() => {
  "use strict";
  const config = document.querySelector("script[data-sesion-guardia]");
  if (!config) return;
  const raiz = document.documentElement;
  const mensaje = document.getElementById("sesion-mensaje");
  const reintentar = document.getElementById("sesion-reintentar");
  const urlSesion = new URL(config.dataset.verificar, location.origin);
  const urlLogin = new URL(config.dataset.login, location.origin);
  let pendiente = false;
  let generacion = 0;
  let solicitud = null;
  let programada = null;

  function ocultar() {
    pendiente = true;
    generacion += 1;
    raiz.classList.add("sesion-oculta");
    if (solicitud) solicitud.abort();
    solicitud = null;
    clearTimeout(programada);
    mensaje.textContent = "Comprobando la sesión…";
    reintentar.disabled = false;
  }

  function corresponde(url, esperado) {
    return url.origin === esperado.origin && url.pathname === esperado.pathname;
  }

  async function verificar() {
    if (!pendiente || document.hidden || solicitud) return;
    const turno = generacion;
    const controller = new AbortController();
    solicitud = controller;
    reintentar.disabled = true;
    mensaje.textContent = "Comprobando la sesión…";
    const timeout = setTimeout(() => controller.abort(), 10000);
    try {
      const respuesta = await fetch(urlSesion, {
        credentials: "same-origin", cache: "no-store", redirect: "follow",
        headers: { "X-AquaLab-Sesion": config.dataset.huella }, signal: controller.signal,
      });
      if (turno !== generacion || document.hidden) return;
      if (controller.signal.aborted) throw new Error("La solicitud venció");
      const destino = new URL(respuesta.url);
      if (!respuesta.redirected && corresponde(destino, urlSesion) && respuesta.status === 204) {
        pendiente = false;
        raiz.classList.remove("sesion-oculta");
      } else if (
        (!respuesta.redirected && corresponde(destino, urlSesion) && respuesta.status === 409) ||
        (respuesta.redirected && respuesta.status === 200 && corresponde(destino, urlLogin))
      ) {
        location.replace(urlLogin.href);
      } else {
        mensaje.textContent = "No se pudo comprobar la sesión. Reintentá o volvé al inicio de sesión.";
      }
    } catch {
      if (turno === generacion) {
        mensaje.textContent = "No se pudo comprobar la sesión. Revisá tu conexión y reintentá.";
      }
    } finally {
      clearTimeout(timeout);
      if (solicitud === controller) solicitud = null;
      if (turno === generacion) reintentar.disabled = false;
    }
  }

  function programar() {
    clearTimeout(programada);
    programada = setTimeout(verificar, 0);
  }

  window.addEventListener("pagehide", ocultar);
  window.addEventListener("focus", programar);
  window.addEventListener("pageshow", (evento) => {
    if (evento.persisted) { ocultar(); programar(); }
    else if (pendiente) { programar(); }
  });
  document.addEventListener("visibilitychange", () => {
    if (document.hidden) ocultar(); else programar();
  });
  reintentar.addEventListener("click", programar);
})();
