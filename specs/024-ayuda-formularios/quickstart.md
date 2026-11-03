# Quickstart: Ayuda en formularios

Recorrido para validar la US 9.1 de punta a punta. Los tests automatizados cubren el marcado; este
recorrido cubre la interacción en el navegador (US 1, escenarios 3 a 7), que pytest no ejecuta
(ver la excepción en [plan.md](./plan.md#complexity-tracking)).

## Requisitos

```bash
docker compose up -d
docker compose exec web python manage.py migrate
docker compose exec -u "$(id -u):$(id -g)" web tailwindcss -i static/src/aqualab.css -o static/css/aqualab.css --minify
```

- Un usuario aprobado que pertenezca al grupo «Bioquímicos» (para Mi firma y para corregir
  mediciones).
- Un cliente, una muestra y un estudio con pruebas: al menos una numérica y una Ausente/Presente.

## Tests automatizados

```bash
docker compose exec web pytest config/tests/test_ayuda.py
docker compose exec web pytest
docker compose exec web ruff check . && docker compose exec web ruff format --check .
```

Esperado: todo en verde y `git status static/css/aqualab.css` sin cambios después de recompilar.

## Recorrido en el navegador

1. **Ícono solo donde hay ayuda.** En Registrar muestra, «Origen», «Fecha de muestreo» y
   «Tipo de vertido» muestran el ícono; «Cliente» no. En Registrar cliente, «Teléfono» y
   «Domicilio» no lo muestran.
2. **Mouse.** Pasar el mouse sobre el ícono de «Origen»: aparece el texto y se oculta al
   retirarlo. Hacer clic en la etiqueta «Origen»: el foco va al selector, como antes.
3. **Teclado.** Recorrer el formulario con Tab: al llegar al ícono aparece la ayuda; con Escape se
   oculta y el foco sigue en el ícono; con Tab pasa al campo siguiente y la ayuda se cierra.
4. **Táctil.** Con el modo táctil de las herramientas del navegador (o una tablet): tocar el ícono
   abre la ayuda, volver a tocarlo la cierra y tocar fuera también la cierra. Tocar el ícono no
   envía el formulario.
5. **Una sola abierta.** Abrir la ayuda de «Origen» con un toque y pasar el mouse sobre la de
   «Tipo de vertido»: queda visible solo la segunda.
6. **Lector de pantalla** (NVDA, Orca o VoiceOver). Al llegar con Tab a «Fecha de muestreo», el
   lector lee la etiqueta y la ayuda sin abrirla. En «Tipo de documento» (Registrar cliente), lee la
   ayuda al entrar al grupo de opciones.
7. **Errores.** Enviar Registrar cliente vacío: los errores se ven junto a cada campo, como antes,
   y los íconos de ayuda siguen disponibles.
8. **Instrucciones visibles.**
   - En Registrarse (registro de usuario), los requisitos de contraseña se ven debajo del campo,
     sin ícono.
   - En Tipos de estudio → nuevo, «Pruebas predeterminadas» tiene ícono y debajo, visible, la
     indicación de Ctrl/Cmd.
   - En Registrar muestra, el texto de «Nombre de la muestra» ya no se ve debajo: está en el ícono.
9. **Mediciones.** En Cargar mediciones de un estudio, el aviso de arriba explica el formato (coma
   o punto, sin miles; elegir Ausente/Presente). La ayuda del encabezado «Medición» se ve completa,
   alineada a la derecha, sin desplazamiento horizontal. Repetir en Corregir mediciones.
10. **Mi firma.** El ícono junto a «Firma» explica cómo dibujarla y que se copia en los informes.
    «Matrícula» tiene su ayuda.
11. **Búsquedas.** En Buscar cliente y Buscar estudio, el ícono de ayuda funciona igual que en los
    formularios: mouse, teclado, toque y Escape.
12. **Bordes.** Con la ventana en 1024 px de ancho y en el modo tablet, ninguna ayuda se corta ni
    genera barra de desplazamiento horizontal.
13. **Admin.** En `/admin/clientes/cliente/add/` no aparece ningún ícono de ayuda nuevo.
