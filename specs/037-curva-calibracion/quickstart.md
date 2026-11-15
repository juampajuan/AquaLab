# Quickstart: Curva de calibración para pruebas por absorbancia

Pantallas en [contracts/curvas-ui.md](./contracts/curvas-ui.md); reglas en [data-model.md](./data-model.md)
y valores de referencia en [research.md](./research.md) (R2).

## Preparación
1. Rama `037-curva-calibracion`; `docker compose build web` (instala `openpyxl`);
   `docker compose up -d`; `docker compose exec web python manage.py migrate` (aplica `pruebas.0004`
   y `estudios.0012`).
2. Catálogo y demo: `importar_catalogo_pruebas` y `cargar_demo` (con `AQUALAB_ENTORNO=desarrollo`).
3. Entrar como `bioquimico@demo.aqualab` / `Demo-1234` (es Administrador).

## Recorrido
1. Administración → Catálogo de pruebas → «Nueva prueba»: `NO2-C` «Nitritos (curva)», tipo
   «Curva de calibración», unidad del resultado mg/l → la unidad de medición queda «Abs»; la ficha
   dice «Sin curva vigente».
2. Crear un tipo de estudio con `NO2-C` y un estudio de ese tipo; cargar absorbancia 0,126 → sin
   resultado, «Falta curva de calibración.»; «Validar resultados» no la ofrece.
3. Ficha de `NO2-C` → «Nueva curva»: cargar a mano los 5 puntos de R2 con fecha de hoy → «Calcular
   recta»: pendiente 0,499, ordenada 0,0012, R² 0,9996 y el gráfico. Probar fecha de mañana y 2
   puntos → errores.
4. «Guardar» → resumen con «1 medición en 1 estudio espera curva»; marcar «Calcularlas con esta
   curva» y confirmar → el mensaje informa 1 resultado calculado. En el estudio: 0,2501 mg/l y «Curva del
   <hoy> · R² 0,9996».
   Variante sin la casilla: cargar otra absorbancia sin curva en un segundo estudio, guardar una
   curva sin marcarla → el estudio muestra «Se cargó antes de la curva vigente.»; «Calcular con la
   curva vigente» → confirmar → resultado calculado; repetir el envío → «No quedaban mediciones…».
5. «Descargar plantilla», cambiar la absorbancia de 0,4 a 0,250 y agregar una fila de título;
   importarla → 5 puntos en la tabla; quitar la absorbancia de la fila 4 en el archivo → «La fila 4
   no tiene absorbancia.» y la tabla no cambia. Probar un `.ods` → rechazado. Probar un `.xlsx` con
   columnas «A» y «B» → pide elegirlas.
6. Guardar la curva importada (R² bajo → aviso, se guarda igual) → la primera pasa a histórica.
   Corregir la absorbancia del estudio a 0,150 → se recalcula con la **primera** curva (0,2982 mg/l).
7. Borrar la curva nueva (sin usar) → vuelve a quedar vigente la primera. La primera (usada) no
   ofrece «Borrar curva».
8. Cargar 0,300 en otro estudio (calcula con la primera, absorbancias 0–0,199) → «Fuera del rango
   de la curva (0–0,4 mg/l)», se puede validar.
9. Entrar como `tecnico@demo.aqualab` → ve `/pruebas/<pk>/curvas/` y el detalle sin «Nueva curva» ni
   «Borrar»; `/administracion/pruebas/<pk>/curvas/nueva/` da 403.

## Tests
```bash
docker compose exec web pytest pruebas/tests/test_curvas*.py estudios/tests/test_calculo_curva.py
docker compose exec web pytest
node --test usuarios/tests/js config/tests/js estudios/tests/js pruebas/tests/js
```
