# Contrato: Cálculo automático del resultado

**Feature**: `016-calcular-resultado` | **Plan**: [plan.md](../plan.md)

Esta historia no agrega pantallas: cambia el detalle del estudio y los mensajes de la carga de
mediciones (US 6.1), y deja un servicio para US 6.3.

## Interfaz

### `GET /estudios/<pk>/` — `estudios:detalle` (cambio)

- La tabla de pruebas suma la columna **Resultado**, entre Medición y Estado:
  - con resultado: `valor_mostrado` (coma decimal, hasta 4 decimales, sin ceros finales) y la
    unidad guardada o «Sin unidad»; debajo, en texto chico, «Fórmula: <fórmula>» si no es Directo;
  - sin resultado: el motivo en texto chico (`text-tinta-suave`), uno de:
    - «Falta la medición.»
    - «No forma parte del estudio: COD · nombre.» (una o más, separadas por coma)
    - «Faltan resultados de: COD · nombre, COD · nombre.»
    - «No se pudo calcular: <motivo>.»
- La columna Medición no cambia; para calculadas sigue «Se calcula».

### `POST /estudios/<pk>/mediciones/cargar/` con `accion=confirmar` (cambio)

Además de los mensajes de US 6.1, una advertencia por cada prueba que el cálculo no pudo evaluar
(no por las que esperan otros resultados):

«COD: no se pudo calcular el resultado (<motivo>).»

## Motivos de `CalculoImposible`

| Caso | Motivo |
|---|---|
| División por cero | `división por cero` |
| Raíz de un número negativo | `raíz cuadrada de un número negativo` |
| Resultado con más de 18 cifras enteras | `el resultado es demasiado grande` |
| Referencias circulares entre pruebas del estudio | `referencias circulares` |

## Servicios (para otras historias)

```text
estudios.calculo.recalcular(estudio, asignaciones) -> list[tuple[Prueba, str]]
    # Requiere el estudio bloqueado por el llamador. Devuelve las que no se pudieron evaluar.

estudios.calculo.motivo_sin_resultado(asignacion, por_codigo) -> str | None

estudios.servicios.recalcular_resultados(estudio_pk, asignacion_pks, usuario) -> list[tuple[Prueba, str]]
    # Bloquea el estudio; RecalculoError si no hay sesión activa, si no existe o si
    # not estudio.admite_correcciones («El estudio ya tiene el informe emitido: sus mediciones y
    # resultados no se pueden cambiar.»). US 6.3 lo llama en la misma transacción en que
    # actualiza la medición.

pruebas.formulas.validar_formula(texto)               # FormulaInvalida (ValidationError)
pruebas.formulas.evaluar_formula(texto, x, resultados) -> Decimal   # CalculoImposible
```

## Comando

`python manage.py calcular_resultados` — calcula los resultados de las mediciones que no tienen;
imprime «Resultados calculados: N. Sin calcular: M.» Idempotente.

## Casos conocidos (valores esperados para los tests)

| Prueba (fórmula) | Datos | Resultado guardado | Mostrado |
|---|---|---|---|
| CL- (`x*10`) | x = 2,35 | 23.5 | 23,5 |
| NH4 (`x*0.28*5`) | x = 1,2 | 1.68 | 1,68 |
| NTK-T (`(25*0.05-x*0.05)*0.01408*100/50*10000`) | x = 10 | 211.2 | 211,2 |
| NA (`((x*321.41/140)*10/5*0.51)`) | x = 0,5 | 1.1708507143 | 1,1709 |
| K (`(x*39.1/5)`) | x = 0,4 | 3.128 | 3,128 |
| SDT (`{COND}*0.54`) | COND = 500 | 270 | 270 |
| NTK (`({NTK-T}-{NH4})`) | NTK-T = 211,2; NH4 = 1,68 | 209.52 | 209,52 |
| MG (`({DUREZA-T}-{CA}*2.5)*0.243`) | DUREZA-T = 300; CA = 80 | 24.3 | 24,3 |
| RAS (`{NA}/sqrt(({CA}+{MG})/2)`) | NA = 46; CA = 80; MG = 24,3 | 6.3698715578 | 6,3699 |
| CO3-MEQ (`{CO3}/30`) | CO3 = 0,12 | 0.004 | 0,004 |
| PH (Directo) | x = 7,20 | 7.2 | 7,2 |

Los valores exactos con todos sus decimales se fijan en los tests (calculados aparte con
`Decimal`); el plan exige al menos un caso por fórmula distinta del catálogo (SC-001).
