# Integración de la identidad AquaLab

Cambio visual solicitado directamente por el usuario sobre `main`, en la rama
`integracion-logo`. Se integra la propuesta aprobada durante este chat: gota cian con
frasco azul marino y nombre AquaLab en el mismo azul.

## Alcance y criterios

- Logo horizontal en el encabezado del menú lateral y en las pantallas de acceso.
- Sobre las fotografías del acceso, una base blanca permite leer el nombre azul marino.
- Símbolo sin texto en el encabezado móvil, donde el menú lateral está cerrado, y en
  el encabezado del administrador de Django.
- Favicon compartido por las pantallas de la app y el administrador.
- La vista de impresión también usa el favicon, sin incluirlo en la generación del PDF.
- El membrete del informe muestra el símbolo chico junto al nombre del laboratorio,
  tanto en la vista previa y el informe emitido como en la impresión y el PDF.
  WeasyPrint carga el PNG directamente desde los estáticos locales, sin peticiones HTTP.
- Cada logo enlaza al inicio correspondiente, conserva su proporción y tiene un nombre
  accesible. El símbolo junto al título del administrador es decorativo.
- No se agregan logos a tarjetas, formularios, botones o pies de página.

## Recursos

Los archivos de producción están en `static/img/marca/`: logo horizontal PNG
de 960 × 320, símbolo PNG de 256 × 256 y favicon ICO con tamaños de 16 a 256 píxeles.
Se exportaron desde los diseños aprobados, preservando el canal alfa. No se necesitan
dependencias nuevas en la app. El parcial `ui/logo.html` centraliza el logo horizontal;
`includes/favicon.html` centraliza los iconos del navegador.

## Alcance del proceso

Esta integración visual acotada se implementa por instrucción expresa del usuario,
sin una nueva historia funcional ni cambios en datos, permisos o lógica de negocio.
Esta nota documenta el alcance y los criterios de aceptación como excepción al flujo
habitual de una spec y una rama numerada por historia.

## Verificación local

- Renderizado aislado con Django de los layouts interno, de acceso, de administración
  y de impresión, sin base de datos ni motor PDF; recursos estáticos encontrados.
- Sintaxis de los parciales y del login comprobada; variantes del logo con y sin base blanca.
- Ruff: lint y formato correctos.
- CSS recompilado con Tailwind 4.3.3 y comparado con una segunda compilación: idéntico.
- `git diff --check` correcto.

No se pudo ejecutar la comprobación completa de Django ni la suite de integración:
Docker no está disponible y la instalación nativa de Windows carece de las bibliotecas
GObject/Pango requeridas por WeasyPrint. No se realizó una revisión visual en navegador.

### Ampliación: logo en los informes

Con Docker disponible, se ejecutaron las pruebas de PDF, impresión y vista previa:
26 pruebas correctas. Se agregó una comprobación para detectar imágenes que WeasyPrint
no logre cargar, ya que ese fallo no impide generar el PDF. También se generó un informe
con datos ficticios, se rasterizó con Poppler y se revisó visualmente el membrete:
logo visible, tamaño discreto y sin solapamientos.
