# Quickstart: Generar informe

**Feature**: `021-generar-informe` | **Plan**: [plan.md](./plan.md)

Guía para comprobar la historia de punta a punta. Rutas y mensajes en
[contracts/generar-informe-ui.md](./contracts/generar-informe-ui.md); estructura del informe en
[data-model.md](./data-model.md).

## Preparación

```bash
docker compose up -d --build
docker compose exec web python manage.py migrate          # aplica informes.0001 y 0002
docker compose exec web python manage.py importar_catalogo_pruebas
```

1. En `/admin/` → Grupos → «Bioquímicos»: tiene «Puede validar resultados» y «Puede emitir
   informes». Tu usuario (o el superusuario) en el grupo; otro empleado común fuera del grupo.

## Recorrido

2. Estudio de **Agua** con **PH**, **CL-**, **ECOLI** y **SS10**. Cargar pH **7,4**, Cloruro **40**
   (400 mg/l), E. coli **Ausente**, Sólidos sedimentables **0,05**. En el detalle, SS10 debe decir
   «Cumple» (por debajo del límite de detección 0,1, FR-016).
3. Validar las cuatro (US 6.4). En `Informes` → Seleccionar el estudio → **Generar informe**.
4. **Vista previa**: aviso «Vista previa…», marca «BORRADOR», datos del laboratorio (DEMO), cliente,
   muestra y estudio; tabla con pH 7,4 «Cumple», Cloruro 400 mg/l «Fuera de norma» (resaltado),
   E. coli «Ausente» «Cumple», Sólidos sedimentables **«< 0,1»** «Cumple». El estudio sigue
   Finalizado.
5. **Emitir informe** → se ve el informe **INF-000001** con fecha y «Emitido por …»; el estudio está
   en «Informe generado»; el control y el detalle del estudio muestran **Ver informe**.
6. Editar el domicilio del cliente y el límite del Cloruro en el admin; **Ver informe** sigue con los
   datos de antes.
7. Con el empleado sin el grupo: ve la vista previa de otro estudio listo pero sin «Emitir
   informe»; un POST a `/informes/estudios/<pk>/generar/` responde 403.
8. Emitir un segundo estudio → **INF-000002**.

## Verificación automática

```bash
docker compose exec web pytest informes estudios pruebas
docker compose exec web ruff check . && docker compose exec web ruff format --check .
docker compose exec web python manage.py makemigrations --check --dry-run
```
