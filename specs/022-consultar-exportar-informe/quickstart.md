# Quickstart: Consultar y exportar informe

**Feature**: `022-consultar-exportar-informe` | **Plan**: [plan.md](./plan.md)

Guía para comprobar la historia de punta a punta. Rutas y mensajes en
[contracts/consultar-exportar-informe-ui.md](./contracts/consultar-exportar-informe-ui.md); modelo
en [data-model.md](./data-model.md).

## Preparación

```bash
docker compose up -d --build        # la imagen instala Pango y WeasyPrint
docker compose exec web python -c "import weasyprint; weasyprint.HTML(string='<p>ok</p>').write_pdf()"
docker compose exec web python manage.py migrate          # aplica informes.0003
```

1. Tener al menos un informe emitido con la US 7.2 **antes** de migrar (sin firma), un bioquímico
   (grupo «Bioquímicos») y un empleado común.

## Recorrido

2. Con el bioquímico, abrir la vista previa de un estudio listo: en lugar de «Emitir informe» aparece
   el aviso con **Cargar mi firma**.
3. En la barra superior → **Mi firma**: dibujar con el mouse, **Borrar**, volver a dibujar; guardar
   sin matrícula → error; con matrícula «MP 1234» → «Se guardó tu firma.». Probar también desde un
   celular o con el modo táctil de las herramientas del navegador.
4. Volver a la vista previa: se ve la firma; **Emitir informe** → el informe muestra firma, nombre y
   «Mat. MP 1234».
5. Menú **Informes → Informes emitidos**: buscar por `INF-000002`, por `2`, por parte del nombre del
   cliente sin tildes, por su documento y por el N° PI; filtrar por fechas (y probar «desde» >
   «hasta» → error).
6. Abrir el informe → **Descargar PDF**: se descarga `INF-00000N.pdf`, A4, con membrete, datos,
   tabla y firma; pie «INF-… · Página 1 de 1».
7. **Imprimir**: se abre otra pestaña y el diálogo de impresión, A4, sin menú ni botones.
8. Informe con muchas pruebas (o un estudio de vertido completo): el PDF tiene más de una hoja, el
   encabezado de la tabla se repite, ninguna fila queda partida y cada hoja lleva el pie.
9. El informe emitido antes de migrar: PDF e impresión con «Sin firma registrada».
10. Volver a **Mi firma**, dibujar otra y guardar: los informes ya emitidos siguen con la firma
    anterior.
11. Con el empleado común: ve **Informes emitidos** y exporta, pero no ve **Mi firma** y
    `/informes/mi-firma/` responde 403.
12. En `/admin/` no aparece «Informes».

## Verificación automática

```bash
docker compose exec web ruff check . && docker compose exec web ruff format --check .
docker compose exec web python manage.py makemigrations --check --dry-run
docker compose exec web pytest informes
docker compose exec web pytest
```

En el PR, el job de CI debe pasar el paso «WeasyPrint instalado» y `pytest` (con
`informes/tests/test_pdf.py` generando PDF reales).
