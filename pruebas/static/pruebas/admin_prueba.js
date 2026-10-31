// Muestra "Fórmula" y "Se calcula a partir de otras pruebas" solo con el tipo de cálculo FORMULA.
// Al ocultarlos no se borra lo escrito: la validación del servidor sigue siendo la que decide.
document.addEventListener("DOMContentLoaded", () => {
  const tipo = document.getElementById("id_tipo_calculo");
  if (!tipo) return;
  const filas = document.querySelectorAll(".field-formula, .field-es_calculada");
  const actualizar = () => {
    const esFormula = tipo.value === "FORMULA";
    filas.forEach((fila) => {
      fila.style.display = esFormula ? "" : "none";
    });
  };
  tipo.addEventListener("change", actualizar);
  actualizar();
});
