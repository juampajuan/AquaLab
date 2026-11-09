# Quickstart: Notificar desvíos relevantes (SCRUM-61, US 8.2)

## Prerrequisitos

```bash
docker compose up -d
docker compose exec web python manage.py migrate          # aplica estudios.0009_validacion_desvio
docker compose exec web python manage.py cargar_demo      # base de desarrollo sin la demo
```

Ingresar con el bioquímico demo (`bioquimico@demo.aqualab`, ver `estudios/demo.py`). No hace falta
ningún comando para datos previos: el desvío se calcula al mostrar.

## Escenarios

1. **Pendiente en el dashboard** (US 2): `/informes/dashboard/` → «Desvíos sin revisar» muestra el
   contador («1 pendiente»: el guion deja solo este) con Cloruro de «Pozo 2» (430 mg/l, mediana 124 mg/l, ▲ +246,8 %).
   «Comparación histórica» abre la 8.1 de ese estudio con solo Cloruro; «Validar» abre la
   validación del estudio.
2. **Marca en el estudio** (US 1): «Ver estudio» → la fila de Cloruro tiene la marca «Desvío» (las
   demás pruebas del guion varían menos del 30 %, lo fija `test_demo.py`).
3. **Validación con desvío de la demo** (FR-015): detalle del estudio de Pozo 2 del mes anterior →
   Cloruro 415 «Desvío revisado · Validado por Bioquímica … – Se repitió la medición: el valor es
   correcto. · mediana 121 mg/l, umbral 30 %».
4. **Corrección** (US 1): en el estudio de Pozo 2, «Corregir mediciones» Cloruro 43,0 → 12,5
   (resultado 125, +0,8 % de la mediana) → la marca desaparece y el dashboard cuenta uno menos.
   Corregir a 50,0 → vuelve a aparecer.
5. **Revisar al validar** (US 3): «Validar resultados» muestra «1 prueba con desvío» y la fila de
   Cloruro destacada con observado, mediana, «Comparación histórica» y el campo «Observación».
   Escribir una observación, marcar Cloruro y «Revisar» → «1 de los N resultados elegidos tiene
   desvío: quedará revisado al validar» con la observación → confirmar → éxito y «Se revisó 1
   desvío: CL-.»; el contador del dashboard baja y el detalle muestra «Desvío revisado». Reenviar la
   confirmación → «CL-: ya estaba validada». Una observación de más de 500 caracteres muestra el
   error junto al campo.
6. **No bloquea** (US 4): validar otra prueba con desvío sin observación → se valida igual, con el
   mismo valor, y queda «Desvío revisado · Sin observación». El informe y su PDF no mencionan
   desvíos.
7. **Regla configurable** (US 5): en `config/settings.py` poner `AQUALAB_DESVIOS["umbral"] = "50"`,
   reiniciar → un pendiente de +45 % deja de figurar; las validaciones con desvío anteriores siguen
   diciendo «umbral 30 %».

## Tests

```bash
docker compose exec web pytest estudios informes -q
node --test usuarios/tests/js config/tests/js estudios/tests/js
docker compose exec web ruff check . && docker compose exec web ruff format --check .
```
