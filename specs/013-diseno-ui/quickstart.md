# Quickstart: validar el rediseño (013)

## Preparación

```bash
docker compose up -d --build        # reconstruye la imagen con el binario de Tailwind
docker compose exec web python manage.py migrate
docker compose exec -u "$(id -u):$(id -g)" web tailwindcss -i static/src/aqualab.css -o static/css/aqualab.css --minify
```

Mientras se editan templates: `docker compose exec -u "$(id -u):$(id -g)" web tailwindcss -i static/src/aqualab.css -o static/css/aqualab.css --watch`.

## Controles automáticos

```bash
docker compose exec web pytest
docker compose exec web ruff check .
docker compose exec web ruff format --check .
git diff --exit-code static/css/aqualab.css   # después de recompilar: el CSS versionado está al día
```

Esperado: todos los tests pasan (SC-002), incluidos los nuevos del panel y de layout.

## Recorrido manual (navegador, http://localhost:8000)

1. **Sin sesión**: `/` redirige al login. El login usa la pantalla partida con imagen, sin menú.
   Credenciales inválidas → "Usuario o contraseña incorrectos". Link "Crear cuenta" funciona.
2. **Registro**: completar con errores (correo inválido, contraseñas distintas) → errores junto a cada
   campo; confirmar → "Registro recibido". Aprobar la cuenta desde el admin (en ventana de incógnito).
3. **Inicio**: banner con imagen, 4 accesos rápidos, 3 indicadores y tabla. Con base vacía: indicadores
   en 0 y estado vacío con "Registrar muestra". Comparar los números con los datos cargados (SC-008).
4. **Menú**: recorrer cada sección; la opción actual aparece destacada en todas (FR-002).
5. **Clientes**: registrar (con CUIT inválido para ver el error), confirmar, buscar con y sin
   resultados (estado vacío), paginación (> 1 página), ficha con badge Activo, editar y confirmar.
6. **Muestras**: elegir cliente → aparece la mini-ficha y sus orígenes; "Dar de alta un origen nuevo";
   tipo de vertido segmentado con Agua por defecto; dejar "Sitio de extracción" vacío → error en rojo;
   confirmar → mensaje con el N° PI.
7. **Estudios**: crear con un tipo disponible; resumen con pruebas y badge "Pendiente de análisis";
   volver y editar; cancelar.
8. **Mensajes**: verificar estilos distintos para éxito, error e información y que se pueden cerrar.
9. **Ventana angosta** (DevTools, 375 px): el menú se colapsa en un botón, ninguna pantalla tiene
   desplazamiento horizontal de la página (SC-005).
10. **Sin internet** (DevTools → Network → Offline, recargando con caché vacía salvo localhost): estilos,
    fuente e íconos se ven igual (FR-018).
11. **Guardia de sesión**: cerrar sesión en otra pestaña → la pantalla abierta se oculta como antes.
12. **Teclado**: recorrer un formulario con Tab; el foco es visible en cada campo y botón (FR-017).
13. **Imágenes del acceso**: en el login, las 4 imágenes alternan cada ~7 s con fundido. Con
    "reducir movimiento" activado (DevTools → Rendering → `prefers-reduced-motion: reduce`) queda una
    sola imagen fija (FR-022).
14. **Contraste**: correr Lighthouse (DevTools → Lighthouse → Accesibilidad) en login, inicio, buscar
    cliente y registrar muestra; sin errores de contraste (SC-006).
