# Quickstart: Notificar desvíos relevantes (SCRUM-61, US 8.2)

## Prerrequisitos

```bash
docker compose up -d
docker compose exec web python manage.py migrate          # aplica estudios.0009_desvio
docker compose exec web python manage.py cargar_demo      # base de desarrollo sin la demo
docker compose exec web python manage.py evaluar_desvios  # si la base ya tenía datos previos
```

Ingresar con el bioquímico demo (`bioquimico@demo.aqualab`, ver `estudios/demo.py`).

## Escenarios

1. **Pendiente en el dashboard** (US 3): `/informes/dashboard/` → «Desvíos sin revisar» muestra el
   contador e incluye Cloruro de «Pozo 2» (430 mg/l, promedio 219,67 mg/l, ▲ +95,8 %).
   «Comparación histórica» abre la 8.1 de ese estudio con solo Cloruro; «Validar» abre la
   validación del estudio.
2. **Marca en estudio y validación** (US 1, US 4): «Ver estudio» → la fila de Cloruro tiene la
   marca «Desvío»; «Validar resultados» muestra «1 prueba con desvío», la fila de Cloruro
   destacada con observado, promedio, enlace a la comparación y el campo «Observación» (las demás
   pruebas del guion varían menos del 30 %, lo fija `test_demo.py`).
3. **Revisado en la demo** (FR-020): sección «Desvíos» del estudio de Pozo 2 del mes anterior →
   Cloruro 415 «Revisado por Bioquímica … – Se repitió la medición: el valor es correcto.»
4. **Corrección** (US 2): en el estudio de Pozo 2, «Corregir mediciones» Cloruro 43,0 → 20,0
   (resultado 200, −9 % del promedio) → la marca desaparece, el dashboard cuenta uno menos y la
   sección «Desvíos» muestra «Resuelto por corrección». Corregir a 50,0 → desvío nuevo, sin
   revisar.
5. **Revisar al validar** (US 4): en la validación, escribir una observación en Cloruro, marcarlo
   y «Revisar» → la confirmación dice «1 de los N resultados elegidos tiene desvío: quedará revisado
   al validar» con la observación → confirmar → éxito y «Se revisó 1 desvío: CL-»; el contador del
   dashboard baja y el detalle muestra «Desvío revisado · Revisado por … – observación». Reenviar
   la confirmación → «CL-: ya estaba validada» y la observación original no cambia.
   Una observación de más de 500 caracteres muestra el error junto al campo.
6. **No bloquea** (US 5): validar otra prueba con desvío sin escribir observación → se valida igual,
   con el mismo valor, y el desvío queda revisado «Sin observación». El informe y su PDF no
   mencionan desvíos.
7. **Regla configurable** (US 6): en `config/settings.py` poner `AQUALAB_DESVIOS["umbral"] = "50"`,
   reiniciar, corregir un valor a +45 % → sin desvío; los existentes siguen diciendo «umbral 30 %».

## Tests

```bash
docker compose exec web pytest estudios/tests/test_desvios.py estudios/tests/test_desvios_vista.py \
  estudios/tests/test_demo.py informes/tests -q
docker compose exec web ruff check . && docker compose exec web ruff format --check .
```
