(() => {
  "use strict";
  const root = document.querySelector("[data-conclusion]");
  if (!root) return;
  const buscar = nombre => root.querySelector("[data-conclusion-" + nombre + "]");
  const editor = buscar("editor"), proponer = buscar("proponer");
  const aprobar = buscar("aprobar"), avisos = buscar("advertencias");
  const bloqueAvisos = buscar("avisos"), errores = buscar("errores"), estado = buscar("estado");
  const respaldo = buscar("respaldo");
  const emitirBoton = buscar("emitir-boton"), revision = buscar("revision");
  const emitir = buscar("emitir"), volver = buscar("volver"), sinConclusion = buscar("sin");
  const csrf = root.querySelector("[data-conclusion-csrf] input");
  const configSesion = document.querySelector("script[data-sesion-guardia]");
  let actual = JSON.parse(buscar("inicial").textContent);
  const prefijo = "aqualab.conclusion.";
  const identidad = root.dataset.usuario + ":" + root.dataset.sesion;
  const clave = prefijo + identidad + ":" + root.dataset.estudio;
  let storage = null, baseLocal = actual.revision;
  let sucio = false, conflicto = false, cerrado = false, generacion = 0, epoca = 0;
  let temporizador = null, ocupado = false, cola = Promise.resolve();
  let permitirEnvio = false, emisionPendiente = false, permitirSin = false;

  class ErrorInterfaz extends Error {}

  function mostrarRespaldo(datos) {
    if (!respaldo) return;
    if (datos.origen_propuesta !== "plantilla") { respaldo.textContent = ""; return; }
    respaldo.textContent = datos.hechos?.clase === "parcial"
      ? "Se usó una plantilla de respaldo parcial." : "Se usó una plantilla de respaldo.";
  }

  function limpiarRecuperacion(todas = false) {
    try {
      if (!storage) return;
      if (!todas) { storage.removeItem(clave); return; }
      for (let i = storage.length - 1; i >= 0; i -= 1) {
        const nombre = storage.key(i);
        if (nombre?.startsWith(prefijo)) storage.removeItem(nombre);
      }
    } catch { /* El servidor sigue siendo la autoridad del borrador. */ }
  }

  function conservar() {
    if (cerrado || !sucio) return;
    try {
      if (!storage) return;
      storage.setItem(clave, JSON.stringify({texto: editor.value, revision: baseLocal}));
    } catch { /* Un error de guardado se informa al intentar persistir en el servidor. */ }
  }

  function controles() {
    root.setAttribute?.("aria-busy", ocupado ? "true" : "false");
    const invalido = cerrado || sucio || conflicto || ocupado;
    if (aprobar) aprobar.disabled = cerrado || ocupado || conflicto ||
      !(editor.value.trim() || actual.advertencias?.length) || (actual.aprobada && !sucio);
    if (proponer) proponer.disabled = cerrado || ocupado;
    if (emitirBoton) emitirBoton.disabled = invalido || !actual.aprobada;
    if (revision) {
      revision.value = actual.revision;
      revision.disabled = invalido || !actual.aprobada;
    }
    estado.textContent = actual.aprobada && !invalido ? "Aprobada" : "Pendiente";
  }

  function cerrar(mensaje = "Revisá tu sesión y autorización antes de continuar.") {
    cerrado = true;
    epoca += 1;
    clearTimeout(temporizador);
    limpiarRecuperacion(true);
    actual = {revision: 0, huella_hechos: "", huella_texto: "", aprobada: false};
    sucio = false;
    if (editor) { editor.value = ""; editor.readOnly = true; }
    for (const elemento of [avisos, respaldo, errores]) {
      if (elemento) elemento.textContent = "";
    }
    controles();
    errores.textContent = mensaje;
  }

  function contextoVigente() {
    if (root.dataset.usuario + ":" + root.dataset.sesion !== identidad) cerrar();
    return !cerrado && root.isConnected !== false;
  }

  function mostrarError(error) {
    if (!cerrado && root.isConnected !== false) {
      errores.textContent = error instanceof ErrorInterfaz
        ? error.message : "No se pudo guardar la conclusión. Revisá tu conexión e intentá nuevamente.";
    }
    controles();
  }

  function mostrarServidor(datos) {
    mostrarRespaldo(datos);
    if (avisos) avisos.textContent = (datos.advertencias || []).join("\n");
    if (bloqueAvisos) bloqueAvisos.hidden = !datos.advertencias?.length;
  }

  async function pedir(url, datos) {
    if (!contextoVigente()) throw new ErrorInterfaz("Revisá tu sesión antes de continuar.");
    const turno = epoca;
    const respuesta = await fetch(url, {
      method: "POST", credentials: "same-origin", cache: "no-store",
      headers: {"Content-Type": "application/json", "X-CSRFToken": csrf.value},
      body: JSON.stringify(datos),
    });
    if (turno !== epoca || !contextoVigente()) throw new ErrorInterfaz("La solicitud ya no está vigente.");
    if (respuesta.status === 401 || respuesta.status === 403 || respuesta.redirected) {
      cerrar();
      throw new ErrorInterfaz("Revisá tu sesión y autorización antes de continuar.");
    }
    if (!respuesta.headers.get("Content-Type")?.includes("application/json")) {
      if (respuesta.ok) {
        cerrar();
        throw new ErrorInterfaz("Revisá tu sesión antes de continuar.");
      }
      throw new ErrorInterfaz("El servidor no confirmó el guardado. Reintentá sin cerrar el borrador.");
    }
    if (respuesta.status === 409) {
      const vigente = await respuesta.json();
      if (turno !== epoca || !contextoVigente()) throw new ErrorInterfaz("La sesión cambió.");
      if (Number.isInteger(vigente.revision) && vigente.revision >= actual.revision) {
        actual = vigente;
        mostrarServidor(vigente);
      }
      conflicto = true;
      conservar();
      throw new ErrorInterfaz("La conclusión cambió. Tu edición no se reemplazó; volvé a proponer para continuar.");
    }
    if (!respuesta.ok) {
      if (errores) errores.textContent = respuesta.status === 400
        ? "Revisá el texto y los datos del borrador antes de reintentar." : "";
      throw new ErrorInterfaz("No se pudo guardar el borrador. Podés reintentar o emitir sin conclusión.");
    }
    const recibido = await respuesta.json();
    if (turno !== epoca || !contextoVigente()) throw new ErrorInterfaz("La sesión cambió.");
    if (!Number.isInteger(recibido.revision) || recibido.revision < actual.revision) {
      conflicto = true;
      throw new ErrorInterfaz("Se descartó una respuesta anterior. Revisá el borrador actual.");
    }
    if (errores) errores.textContent = "";
    return recibido;
  }

  function adoptar(recibido, visto) {
    actual = recibido;
    mostrarServidor(recibido);
    baseLocal = actual.revision;
    if (generacion === visto) {
      editor.value = recibido.texto_editorial || "";
      sucio = false;
      limpiarRecuperacion();
    } else {
      sucio = true;
      conservar();
    }
    controles();
  }

  function encolar(accion) {
    const siguiente = cola.then(accion);
    cola = siguiente.catch(() => {});
    return siguiente;
  }

  async function guardarInterno() {
    if (!contextoVigente()) throw new ErrorInterfaz("Revisá tu sesión antes de guardar.");
    if (conflicto) throw new ErrorInterfaz("La conclusión cambió. Volvé a proponer antes de aprobar.");
    while (sucio) {
      const visto = generacion;
      const recibido = await pedir(root.dataset.urlGuardar, {
        revision_esperada: actual.revision, huella_hechos_vista: actual.huella_hechos,
        texto: editor.value,
      });
      adoptar(recibido, visto);
    }
    controles();
  }

  function barrera() {
    clearTimeout(temporizador);
    return encolar(guardarInterno);
  }

  editor.value = actual.texto_editorial || "";
  editor.readOnly = false;
  mostrarRespaldo(actual);
  try {
    if (root.dataset.usuario && root.dataset.sesion && root.dataset.estudio) {
      storage = window.sessionStorage;
      for (let i = storage.length - 1; i >= 0; i -= 1) {
        const nombre = storage.key(i);
        if (nombre?.startsWith(prefijo) && !nombre.startsWith(prefijo + identidad + ":")) storage.removeItem(nombre);
      }
      const copia = storage.getItem(clave);
      if (copia) {
        const recuperado = JSON.parse(copia);
        if (typeof recuperado.texto === "string" && Number.isInteger(recuperado.revision) &&
            Object.keys(recuperado).every(k => k === "texto" || k === "revision")) {
          editor.value = recuperado.texto;
          sucio = true;
          generacion += 1;
          baseLocal = recuperado.revision;
          conflicto = recuperado.revision !== actual.revision;
          if (conflicto) errores.textContent = "La conclusión cambió. Tu edición no se reemplazó; volvé a proponer para continuar.";
        } else limpiarRecuperacion();
      }
    }
  } catch { /* Se conserva el autoguardado en el servidor aunque storage no esté disponible. */ }
  if (actual.requiere_revision) errores.textContent = "Los resultados cambiaron. Revisá la conclusión antes de aprobar.";
  controles();
  if (sucio && !conflicto) temporizador = setTimeout(() => barrera().catch(mostrarError), 400);

  editor.addEventListener("input", () => {
    if (!contextoVigente() || editor.readOnly) return;
    if (!sucio) baseLocal = actual.revision;
    generacion += 1;
    sucio = true;
    conservar();
    controles();
    clearTimeout(temporizador);
    if (!conflicto) temporizador = setTimeout(() => barrera().catch(mostrarError), 400);
  });

  proponer.addEventListener("click", async () => {
    if (proponer.disabled || !contextoVigente()) return;
    if ((actual.revision > 0 || editor.value) &&
        !window.confirm("Se reemplazará la conclusión existente. ¿Continuar?")) return;
    ocupado = true;
    controles();
    proponer.textContent = "Proponiendo…";
    try {
      await encolar(async () => {
        if (!conflicto) await guardarInterno();
        const visto = generacion;
        const recibido = await pedir(root.dataset.urlProponer, {
          revision_esperada: actual.revision, huella_hechos_vista: actual.huella_hechos,
        });
        conflicto = false;
        adoptar(recibido, visto);
      });
    } catch (error) { mostrarError(error); }
    finally { ocupado = false; proponer.textContent = "Proponer conclusión"; controles(); }
  });

  aprobar.addEventListener("click", async () => {
    if (aprobar.disabled || !contextoVigente()) return;
    ocupado = true;
    controles();
    try {
      await encolar(async () => {
        await guardarInterno();
        if (!window.confirm("¿Aprobás esta conclusión, incluidas las advertencias?")) return;
        const visto = generacion;
        const recibido = await pedir(root.dataset.urlAprobar, {
          revision_esperada: actual.revision, huella_hechos_vista: actual.huella_hechos,
          huella_texto_visto: actual.huella_texto, confirmacion: true,
        });
        adoptar(recibido, visto);
      });
    } catch (error) { mostrarError(error); }
    finally { ocupado = false; controles(); }
  });

  volver?.addEventListener("click", async evento => {
    evento.preventDefault();
    try {
      await barrera();
      window.location.assign(volver.href);
    } catch (error) { mostrarError(error); }
  });

  emitir?.addEventListener("submit", async evento => {
    if (permitirEnvio) return;
    evento.preventDefault();
    if (emisionPendiente) return;
    emisionPendiente = true;
    try {
      await barrera();
      if (!actual.aprobada || sucio || conflicto || cerrado) throw new ErrorInterfaz("La conclusión requiere una nueva aprobación.");
      if (!window.confirm("Se emitirá con la conclusión aprobada. ¿Continuar?")) return;
      controles();
      permitirEnvio = true;
      emitir.requestSubmit();
    } catch (error) { mostrarError(error); }
    finally { emisionPendiente = false; }
  });

  sinConclusion?.addEventListener("submit", async evento => {
    if (permitirSin) return;
    evento.preventDefault();
    if (ocupado) {
      conservar();
      if (!window.confirm("Hay una solicitud de conclusión en curso. ¿Emitir ahora sin conclusión, sin esperar esa solicitud?")) return;
    } else {
      try { await barrera(); }
      catch (error) {
        mostrarError(error);
        if (!window.confirm("No se pudo guardar el borrador. ¿Emitir igualmente sin conclusión?")) return;
      }
    }
    permitirSin = true;
    epoca += 1; // Una respuesta pendiente no se instala después de elegir esta emisión.
    sinConclusion.dataset.confirmado = "1";
    sinConclusion.requestSubmit();
  });

  const salidas = new Set(document.querySelectorAll("[data-cerrar-sesion]"));
  const salida = document.querySelector("[data-cerrar-sesion]");
  if (salida) salidas.add(salida);
  salidas.forEach(form => form.addEventListener("submit", () => cerrar("Cerrando sesión…")));

  async function revisarSesion() {
    if (!contextoVigente() || !configSesion) return;
    try {
      const respuesta = await fetch(configSesion.dataset.verificar, {
        credentials: "same-origin", cache: "no-store",
        headers: {"X-AquaLab-Sesion": configSesion.dataset.huella},
      });
      if (respuesta.redirected || respuesta.status === 409 || respuesta.status === 403) cerrar();
    } catch { return; }
  }
  window.addEventListener("pageshow", revisarSesion);
  window.addEventListener("focus", revisarSesion);
  document.addEventListener("visibilitychange", () => {
    if (!document.hidden) revisarSesion();
  });
})();
