# Quickstart: validar la US 10.3

## Requisitos

- `docker compose up` con la base local y `python manage.py cargar_demo` (clientes como «Lácteos
  del Sur S.A.», origen «Pozo 2» y el tipo «Físico-químico básico»).
- `ASISTENTE_API_KEY` en `.env` para la prueba manual (Groq). Los tests no la necesitan.

## Tests automáticos

```bash
docker compose exec web pytest asistente muestras estudios
docker compose exec web ruff check . && docker compose exec web ruff format --check .
node --test usuarios/tests/js config/tests/js estudios/tests/js pruebas/tests/js asistente/tests/js
```

## Prueba manual (con la demo)

1. **Ejemplo de la historia** (US 1): en el asistente, «Registrá una muestra de Lácteos del Sur,
   pozo 2, para un físico-químico básico». → Pregunta las fechas. Respondé «la tomaron ayer,
   llegó hoy». → Resumen + botón «Revisar y registrar la muestra». Anotá el último N° PI en
   «Buscar estudios» o en la ficha del cliente: **no debe haber cambiado**.
2. Seguí el botón. → El panel se minimiza; el formulario muestra el cliente, el Pozo 2, las dos
   fechas y la nota «Después de registrar la muestra se ofrecerá crear el estudio «Físico-químico
   básico»». Completá el sitio de extracción, enviá y confirmá. → «Muestra registrada con N° PI …»
   y «Crear el estudio Físico-químico básico».
3. Seguí ese enlace. → Crear estudio con la muestra y el tipo elegidos. El estudio no existe hasta
   confirmar.
4. **Sin tipo**: «Registrá una muestra de Lácteos del Sur, pozo 2». → Opciones con «Solo registrar
   la muestra» primera. Elegila; el registro termina sin ofrecer un estudio.
5. **Estudio para muestra existente** (US 2): «Creá un estudio bacteriológico para el PI <uno de la demo>».
   → «Revisar y crear el estudio».
6. **Datos que no coinciden** (US 3): un cliente inexistente («Registrá una muestra de Acme») →
   aviso + «Registrar cliente»; «pozo 9» → orígenes del cliente + «Registrarlo como origen nuevo»;
   un tipo inactivo → tipos activos; un N° PI inexistente → aviso sin enlace.
7. **Fuera de alcance**: «Registrá el cliente Juan Pérez» → mensaje fijo con «Registrar cliente»;
   «Validá el estudio 42» → «solo consulto…» como en la 10.1.
8. **Abandonar** (US 4): cerrá el panel con la ✕ a mitad de la conversación; volvé a contar
   muestras, estudios y orígenes: sin cambios.
9. **Enlace manipulado**: abrí `/muestras/registrar/?cliente=999999&tipo_estudio=999999&fecha_
   muestreo=xx` → formulario vacío normal, sin error.
