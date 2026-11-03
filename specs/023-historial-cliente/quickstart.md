# Quickstart: Consultar historial del cliente

**Feature**: `023-historial-cliente` | **Plan**: [plan.md](./plan.md)

Guía para comprobar la historia de punta a punta. Rutas, parámetros y mensajes en
[contracts/historial-cliente-ui.md](./contracts/historial-cliente-ui.md); datos que se leen en
[data-model.md](./data-model.md).

## Preparación

```bash
docker compose up -d --build
docker compose exec web python manage.py migrate          # sin migraciones nuevas
docker compose exec web python manage.py importar_catalogo_pruebas
```

Datos (DEMO), con un empleado con sesión:

1. Cliente **A** con tres muestras: M1 ingresada el 15/09, M2 el 10/10 y M3 el 25/10.
   - M1: un estudio con informe emitido (US 6.4 + US 7.2).
   - M2: dos estudios, uno En proceso y otro Pendiente de análisis.
   - M3: sin estudios.
2. Cliente **B** con una muestra. Cliente **C** sin muestras.

## Recorrido

3. Buscar el cliente A → ficha → **Historial**. Se ven M3, M2 y M1 en ese orden, con N° PI, fecha
   de ingreso y origen; M3 dice «Sin estudios»; M2 muestra sus dos estudios con su estado; M1
   muestra «Informe generado» y **Ver informe INF-…**. No aparece la muestra del cliente B.
4. **Ver informe** abre el informe emitido; volver. El N° PI de M2 abre la ficha de la muestra;
   un estudio de M2 abre su detalle.
5. Filtrar **Ingreso desde** 01/10 → quedan M3 y M2. Agregar **hasta** 15/10 → queda M2.
6. **Limpiar filtros**; elegir **Estado** «En proceso» → queda solo M2 con un solo estudio.
   Agregar desde 20/10 → «Ninguna muestra coincide con los filtros.» con «Limpiar filtros».
7. Poner desde 20/10 y hasta 01/10 → error junto a «Ingreso desde» y se ve el historial completo.
8. Historial del cliente C → «Este cliente no tiene muestras registradas.»
9. Desactivar el cliente B en el admin y abrir `/clientes/<pk B>/historial/` → vuelve a la búsqueda
   con «El cliente no está disponible.»

## Tests y calidad

```bash
docker compose exec web pytest clientes
docker compose exec web pytest
docker compose exec web ruff check . && docker compose exec web ruff format --check .
```

Resultado esperado: todos los tests en verde (mapa en [plan.md](./plan.md#mapa-de-tests)) y ruff
sin errores; si el template agregó clases de Tailwind, el CSS compilado de `static/css/aqualab.css`
está actualizado.
