# Quickstart: Cálculo automático del resultado

**Feature**: `016-calcular-resultado` | **Plan**: [plan.md](./plan.md)

## Requisitos previos

- Rama `016-calcular-resultado` y Docker Compose levantado.
- Migraciones aplicadas: `docker compose exec web python manage.py migrate` (incluye
  `estudios.0005_resultado`).
- Catálogo cargado: `docker compose exec web python manage.py importar_catalogo_pruebas`
  (SCRUM-64). Con la validación nueva de fórmulas, debe terminar sin errores.
- Resultados de las mediciones cargadas antes de esta historia:
  `docker compose exec web python manage.py calcular_resultados`. Una segunda corrida informa
  «Resultados calculados: 0».

## Validación automática

```bash
docker compose exec web pytest pruebas estudios
docker compose exec web pytest
docker compose exec web ruff check .
docker compose exec web ruff format --check .
docker compose exec web python manage.py makemigrations --check --dry-run
```

Resultado esperado: todos los tests en verde (incluidos los casos conocidos de
[contracts/calculo-resultado.md](./contracts/calculo-resultado.md)), `ruff` sin errores y sin
migraciones pendientes.

## Recorrido manual

Mensajes y formato exactos en [contracts/calculo-resultado.md](./contracts/calculo-resultado.md).

1. **Preparar**: crear un tipo de estudio con PH, CL-, CA, DUREZA-T y MG, y un estudio de ese tipo.
2. **Resultado directo y por fórmula (US 1)**: cargar PH = 7,20 y CL- = 2,35. En el detalle, la
   columna Resultado muestra «7,2 UpH» y «23,5 mg/l», con la fórmula `x*10` debajo de Cloruro.
3. **Calculada que espera (US 2)**: cargar CA = 80. MG muestra «Faltan resultados de: DUREZA-T ·
   Dureza Total.» y sigue Pendiente.
4. **Calculada completa**: cargar DUREZA-T = 300. MG muestra «24,3 mg/l» y pasa a Cargada.
5. **Referencia ausente**: en otro estudio con MG y CA pero sin DUREZA-T, cargar CA. MG muestra
   «No forma parte del estudio: DUREZA-T · Dureza Total.»
6. **Recálculo (US 3)**: no hay pantalla hasta US 6.3; lo cubren los tests automáticos
   (`recalcular_resultados`).
