# Quickstart: Panel de calidad del agua

## Requisitos

- `docker compose up` con la base local y la demo de SCRUM-78:
  `docker compose exec web python manage.py cargar_demo` (con `AQUALAB_ENTORNO=desarrollo` y
  `DEBUG`; no modifica datos existentes).
- Usuario del grupo «Bioquímicos» (el de la demo) y el técnico de la demo (sin permiso).

## Tests

```bash
docker compose exec web pytest informes estudios
docker compose exec web ruff check . && docker compose exec web ruff format --check .
node --test usuarios/tests/js config/tests/js estudios/tests/js
```

## Prueba manual

1. Entrar como bioquímico → «Dashboard». Debajo de «Actividad semanal» aparece «Calidad» con el
   período «Este mes» (con la demo, el ranking de pruebas casi no tiene filas: solo pH llega a 5
   evaluados en un mes).
2. Elegir «Últimos 6 meses» → «Ver». La sección cambia junto con los indicadores de la 8.3. Los
   pasos 3 a 8 se hacen con este período.
3. Indicador: contar en el admin (o con `Validacion.objects.filter(anulada=False, ...)`) las
   vigentes del período; el porcentaje y «N de M resultados» coinciden. La variación sube en rojo o
   baja en verde, con flecha y «p. p.».
4. Pruebas que más fallan: al menos 3 pruebas, alguna con fuera de norma; ninguna fila con menos
   de 5 evaluados; cada fila «xx,x % (a de b)»;
   orden por porcentaje. Abrir «Ver datos»: mismos valores que el gráfico.
5. Cumplimiento por tipo de vertido: Agua, Cloacal y Canal, con «Sin resultados» en los que no
   tengan.
6. Clientes y orígenes: aparecen «Pozo 2» (Cloruro 415) y «Tanque domiciliario» (E. coli
   Presente). El enlace del cliente abre su historial; el del origen, la comparación histórica.
7. Desactivar un cliente con incumplimientos en el admin → recargar: aparece «Inactivo» sin enlace
   (en clientes y en sus orígenes). Reactivarlo.
8. Cambiar el límite de Cloruro en el admin → recargar: nada cambia (se usa la evaluación guardada).
   Restaurarlo.
9. Desactivar JavaScript: los gráficos no se dibujan y las tablas «Ver datos» muestran todo.
10. Entrar con el técnico a `/informes/dashboard/` → 403.
