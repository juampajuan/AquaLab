# Quickstart: Comparación histórica por origen (SCRUM-60, US 8.1)

Guía para verificar la historia de punta a punta. Diseño en [plan.md](./plan.md), pantallas en
[contracts/comparacion-ui.md](./contracts/comparacion-ui.md), estructuras en
[data-model.md](./data-model.md) y valores esperados en [research.md](./research.md) (R11, R12).

## Preparación

```bash
docker compose up -d
docker compose exec web python manage.py migrate
docker compose exec web python manage.py importar_catalogo_pruebas
docker compose exec web python manage.py cargar_demo   # AQUALAB_ENTORNO=desarrollo y DEBUG
```

Entrar como `bioquimico@demo.aqualab` (Bioquímicos + Administradores).

## Escenarios

1. **Desde el estudio (Pozo 2, Cloruro sin validar)**: Estudios → buscar «Pozo 2» → estudio
   Físico-químico del mes actual (En proceso) → «Comparación histórica».
   - Cloruro: 5 puntos validados (118, 121, 124, 120, 415) y el 430 destacado «Sin validar»;
     franja hasta 350 mg/l (Límite general); 415 y 430 por encima.
   - Variación: contra el anterior ▲ +15 mg/l (+3,6 %); contra el promedio de 5 anteriores
     (179,6 mg/l) ▲ +250,4 mg/l (+139,4 %); «Fuera de la franja del límite».
   - No cambia nada: el estudio sigue En proceso y Cloruro sigue Cargada.
2. **Elegir pruebas**: desmarcar todas salvo Cloruro y Conductividad → «Aplicar» → solo dos
   tarjetas; copiar la URL en otra pestaña → misma selección. «Ninguna» + «Aplicar» → «Elegí al
   menos una prueba para ver su evolución».
3. **Desde el Dashboard**: Dashboard → «Comparación histórica» → cliente «Lácteos del Sur S.A.» →
   origen «Pozo 2» → «Ver evolución». Sin punto destacado; Cloruro: último 415, contra el anterior
   ▲ +295 mg/l (+245,8 %), contra el promedio (120,75) ▲ +294,25 mg/l (+243,7 %).
4. **Ausente/Presente (Tanque domiciliario, E. Coli)**: Dashboard → «María González» →
   «Tanque domiciliario». E. Coli muestra los niveles «Ausente»/«Presente» con el punto Presente
   del mes 3; «Sin cambios (Ausente)» y «Presente en 1 de 4». Desde el estudio del mes 3:
   «Cambió: Ausente → Presente», «Presente en 0 de 2».
5. **Sin historial**: abrir un estudio de un origen nuevo (registrar una muestra y un estudio) →
   cada prueba muestra «Sin resultado en este estudio» y «Sin historial para comparar», sin
   gráfico.
6. **Sin JavaScript** (desactivarlo en el navegador): las tablas «Ver datos», la franja y la
   variación se leen; el selector del Dashboard muestra los orígenes agrupados por cliente.
7. **Permisos**: como `tecnico@demo.aqualab` el detalle del estudio no tiene el botón y la URL
   `/estudios/comparacion/?estudio=<pk>` responde 403.
8. **Lo ve solo el laboratorio**: el informe emitido, su PDF, la impresión y el correo no muestran
   nada de la comparación.

## Tests

```bash
docker compose exec web pytest estudios/tests/test_comparacion.py \
  estudios/tests/test_comparacion_vista.py estudios/tests/test_comparacion_demo.py \
  informes/tests/test_dashboard.py
node --test usuarios/tests/js config/tests/js estudios/tests/js
docker compose exec web ruff check . && docker compose exec web ruff format --check .
```
