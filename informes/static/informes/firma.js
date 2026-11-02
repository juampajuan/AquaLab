// Recuadro de firma de «Mi firma» (US 7.3), sin librerías. Pointer Events cubre mouse, dedo y
// lápiz con un solo código. Al enviar, si hubo trazos, el PNG va al campo oculto «firma»; si no,
// queda vacío (el servidor exige la firma solo si todavía no hay una guardada).
(() => {
  const canvas = document.querySelector("[data-firma]");
  if (!canvas) return;
  const formulario = canvas.closest("form");
  const campo = formulario.querySelector('input[name="firma"]');
  const contexto = canvas.getContext("2d");
  let dibujando = false;
  let hayTrazos = false;

  canvas.style.touchAction = "none"; // el dedo dibuja en lugar de desplazar la página
  contexto.lineWidth = 2.5;
  contexto.lineCap = "round";
  contexto.lineJoin = "round";
  contexto.strokeStyle = "#0b1c30";

  // De coordenadas de pantalla a los 600 × 200 px internos del canvas (es responsive en ancho).
  const punto = (evento) => {
    const caja = canvas.getBoundingClientRect();
    return [
      ((evento.clientX - caja.left) * canvas.width) / caja.width,
      ((evento.clientY - caja.top) * canvas.height) / caja.height,
    ];
  };

  canvas.addEventListener("pointerdown", (evento) => {
    evento.preventDefault();
    canvas.setPointerCapture(evento.pointerId);
    dibujando = true;
    const [x, y] = punto(evento);
    contexto.beginPath();
    contexto.moveTo(x, y);
    contexto.lineTo(x + 0.01, y); // un toque deja un punto
    contexto.stroke();
    hayTrazos = true;
  });

  canvas.addEventListener("pointermove", (evento) => {
    if (!dibujando) return;
    const [x, y] = punto(evento);
    contexto.lineTo(x, y);
    contexto.stroke();
  });

  const terminar = () => {
    dibujando = false;
  };
  canvas.addEventListener("pointerup", terminar);
  canvas.addEventListener("pointercancel", terminar);

  formulario.querySelector("[data-firma-borrar]").addEventListener("click", () => {
    contexto.clearRect(0, 0, canvas.width, canvas.height);
    hayTrazos = false;
    campo.value = "";
  });

  formulario.addEventListener("submit", () => {
    campo.value = hayTrazos ? canvas.toDataURL("image/png") : "";
  });
})();
