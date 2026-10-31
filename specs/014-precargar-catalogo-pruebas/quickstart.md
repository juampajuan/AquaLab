# Quickstart: Precargar el catálogo de pruebas de agua

Guía para validar SCRUM-64 de punta a punta. Contratos: [comando](./contracts/importar-catalogo-pruebas.md)
y [admin](./contracts/admin-pruebas.md).

## Preparación

```bash
docker compose up -d
docker compose exec web python manage.py migrate        # aplica pruebas.0002
```

## 1. Importar (User Story 1)

```bash
docker compose exec web python manage.py importar_catalogo_pruebas
```

Resultado esperado: `90 pruebas (90 creadas, 0 actualizadas) y 18 límites ... (18 creados, 0
actualizados)` sobre una base sin las pruebas del catálogo. Las pruebas DEMO existentes siguen ahí.

Verificación rápida en `docker compose exec web python manage.py shell`:

```python
from pruebas.models import Prueba, LimiteVertido
Prueba.objects.exclude(codigo__startswith="DEMO-").count()  # 90
LimiteVertido.objects.count()                               # 18
Prueba.objects.get(codigo="MG").formula                     # '({DUREZA-T}-{CA}*2.5)*0.243'
Prueba.objects.get(codigo="TURBIDEZ").tipo_calculo          # 'DIRECTO'
Prueba.objects.filter(observacion__startswith="Sin tipo de cálculo").count()  # 17
LimiteVertido.objects.get(prueba__codigo="CL2-LIB", tipo_vertido="cloacal").limite_max  # 'NE'
```

## 2. Reimportar (User Story 2)

1. Correr la importación otra vez. Resultado esperado: `0 creadas, 90 actualizadas` y `0 creados, 18
   actualizados`, con las mismas cantidades en la base.
2. Asignar una prueba del catálogo (por ejemplo `PH`) a un tipo de estudio desde la gestión de tipos.
   Copiar el CSV a un archivo temporal, cambiar el nombre de `PH` en la copia y correr
   `importar_catalogo_pruebas --catalogo <copia>`. Resultado esperado: un aviso, el nombre sin cambios y
   la asignación intacta.
3. En otra copia, poner `CURVA` como tipo de cálculo de una fila e importarla. Resultado esperado: un
   error con el número de línea, código de salida distinto de 0 y ningún cambio en la base.

## 3. Admin (User Story 3)

Con un superusuario en `/admin/pruebas/prueba/`:

- Buscar "dureza" y filtrar por Tipo de cálculo = Fórmula.
- Filtrar por Observación = con observación: aparecen 18 pruebas (las 17 DIRECTO asumidas y el
  Magnesio).
- Abrir `CL2-LIB`: se ven sus dos límites por vertido.
- Abrir `PH` (asignada en el paso 2): código y nombre son de solo lectura y no aparece el botón
  Eliminar.
- Agregar una prueba `FORMULA` con la fórmula `{NOEXISTE}*2`: se rechaza indicando la referencia.

## 4. Tests y lint

```bash
docker compose exec web pytest pruebas
docker compose exec web pytest
docker compose exec web ruff check . && docker compose exec web ruff format --check .
```
