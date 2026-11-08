# Quickstart: Panel del laboratorio

Comprobación de punta a punta de la US 8.3. Pantalla en
[contracts/dashboard-ui.md](./contracts/dashboard-ui.md); reglas en [data-model.md](./data-model.md).

## Preparación

1. Rama `027-panel-laboratorio` (sale de `026-datos-demo`). `docker compose up -d` y `migrate`
   (aplica `informes.0004`).
2. Con `AQUALAB_ENTORNO=desarrollo`: `docker compose exec web python manage.py cargar_demo` (si la
   demo no está cargada).

## Recorrido

1. Entrar como `bioquimico@demo.aqualab` / `Demo-1234`: «Dashboard» aparece debajo de «Inicio».
2. Abrirlo: período «Este mes»; los 4 indicadores con su variación en color con flecha y signo.
3. Elegir «Últimos 6 meses»: cambian los indicadores; los dos gráficos y las alertas no.
4. Gráfico de tiempo de respuesta con 6 meses y de actividad con 12 semanas; abrir «Ver datos» y
   comprobar que las tablas coinciden.
5. Alertas: «Pozo domiciliario» (mes anterior) en «Estudios sin avanzar» y «Escuela N° 12» en
   «Finalizados sin informe»; «Ver estudio» abre su detalle.
6. Entrar como `tecnico@demo.aqualab`: no ve «Dashboard» y `/informes/dashboard/` da 403.
7. Con el navegador sin conexión a internet, el panel y los gráficos se ven igual (Chart.js local).

## Tests

```bash
docker compose exec web pytest informes/tests/test_tablero.py informes/tests/test_dashboard.py
docker compose exec web pytest
```
