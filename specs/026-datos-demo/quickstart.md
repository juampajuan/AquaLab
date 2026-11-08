# Quickstart: Datos de demo

Guía para comprobar SCRUM-78 de punta a punta en desarrollo. Interfaz del comando en
[contracts/cargar-demo-cli.md](./contracts/cargar-demo-cli.md); guion en [data-model.md](./data-model.md).

## Preparación

1. Agregar `AQUALAB_ENTORNO=desarrollo` al `.env` (está en `.env.example`).
2. Base nueva: `docker compose down -v`, `docker compose up -d --build`,
   `docker compose exec web python manage.py migrate`.

## Recorrido

1. `docker compose exec web python manage.py cargar_demo` → resumen con estudios por estado y los dos
   usuarios. Tarda menos de 1 minuto.
2. Repetir el comando → «La demo ya está cargada…», sin cambios.
3. Entrar como `bioquimico@demo.aqualab` / `Demo-1234`: se ve la sección Administración; en
   Estudios hay estudios Finalizados (listos para emitir) y uno En proceso con Cloruro 430 mg/l.
4. Abrir un informe emitido de un mes anterior → membrete, datos, firma y matrícula «MP 0000 (DEMO)»;
   exportar PDF.
5. Historial de «Lácteos del Sur S.A.» → muestras de los 6 meses con sus estados; en «Pozo 2» el
   Cloruro pasa de ~120 a 415 y 430 mg/l.
6. Entrar como `tecnico@demo.aqualab` / `Demo-1234`: no puede validar ni emitir; hay estudios con
   mediciones por cargar.
7. Con `AQUALAB_ENTORNO` vacío o `DEBUG=False`, el comando se rechaza sin cambios.
8. `docker compose exec web python manage.py cargar_demo_us51` → «Unknown command».

## Tests

```bash
docker compose exec web pytest estudios/tests/test_demo.py
docker compose exec web pytest
```
