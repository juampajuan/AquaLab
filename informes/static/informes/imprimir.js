// Impresión del informe en A4 (US 7.3): abre el diálogo al cargar y desde el botón «Imprimir».
window.addEventListener("load", () => window.print());
document.addEventListener("click", (evento) => {
  if (evento.target.closest("[data-imprimir]")) {
    window.print();
  }
});
