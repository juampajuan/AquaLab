# Quickstart: Validar resultados

**Feature**: `019-validar-resultados` | **Plan**: [plan.md](./plan.md)

Guía para comprobar la historia de punta a punta. Rutas y mensajes en
[contracts/validar-resultados-ui.md](./contracts/validar-resultados-ui.md); reglas de evaluación
en [data-model.md](./data-model.md).

## Preparación

```bash
docker compose up -d --build
docker compose exec web python manage.py migrate          # aplica estudios.0007 y 0008
docker compose exec web python manage.py importar_catalogo_pruebas
docker compose exec web python manage.py createsuperuser  # si no hay uno
```

1. En `/admin/` → Grupos: existe «Bioquímicos» con «Puede validar resultados».
2. Crear (o elegir) un empleado común y agregarlo al grupo «Bioquímicos». Dejar otro empleado sin
   el grupo para el paso 7.

## Recorrido

3. Registrar un cliente y una muestra de **Agua**; crear un tipo de estudio con **PH**, **CL-**,
   **ECOLI** y **OLOR**, y un estudio con ese tipo.
4. Cargar mediciones: pH **7,4**; Cloruro **40** (fórmula `x*10` → 400 mg/l); E. coli **Ausente**;
   Olor **2**.
   En el detalle, antes de validar:
   - pH → «Cumple» (límite 6.4 a 8.5);
   - Cloruro → «Fuera de norma» (máx. 350.0), en rojo;
   - E. coli → «Cumple» (máx. Ausente);
   - Olor → «Sin límite comparable» (máx. SOE).
5. Con el empleado del grupo, **Validar resultados**: vienen marcadas pH y E. coli; Cloruro y Olor
   sin marcar. Probar **Marcar todas**, después desmarcar Olor y **Revisar validación**: el resumen
   avisa «No cumplen: CL- · Cloruro…». Confirmar.
6. El detalle muestra pH, Cloruro y E. coli Completadas con «Validada por …»; el estudio sigue En
   proceso. Validar Olor: el estudio pasa a **Finalizado**.
7. Con el empleado sin el grupo: el detalle no muestra «Validar resultados» y abrir
   `/estudios/<pk>/resultados/validar/` responde 403.
8. Corregir la medición de pH a 9 (US 6.3): pH vuelve a Cargada, pierde «Validada por …», se ve
   «Fuera de norma» y el estudio vuelve a En proceso.
9. Muestra **Cloacal** con pH 7: se evalúa con 7.01 a 10.0 (Cloacal) → «Fuera de norma».

## Verificación automática

```bash
docker compose exec web pytest estudios pruebas
docker compose exec web ruff check . && docker compose exec web ruff format --check .
docker compose exec web python manage.py makemigrations --check --dry-run
```
