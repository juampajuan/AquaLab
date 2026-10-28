# Research: Diseño de la interfaz (013)

Decisiones técnicas para implementar el diseño de Stitch (`stitch/`) sobre las 15 pantallas existentes.

## R1. Cómo compilar Tailwind sin Node

- **Decision**: Tailwind CSS 4 con el **CLI standalone** (un único binario, sin Node). Se descarga en el
  `Dockerfile` a `/usr/local/bin/tailwindcss` (fuera de `/app`, porque Compose monta el repo encima),
  eligiendo el binario según la arquitectura (`linux-x64` o `linux-arm64`, para quien use Mac con chip
  Apple). La versión se fija con `ARG TAILWIND_VERSION` en el `Dockerfile` y en el CI: la última 4.x
  estable al momento de implementar (ver releases de `tailwindlabs/tailwindcss`).
- **Rationale**: la constitution (v1.1.0) pide CSS compilado y sin CDN; el binario evita agregar Node,
  `package.json` y `node_modules` a un proyecto Python.
- **Alternatives considered**: CDN de Tailwind (lo que exporta Stitch; prohibido por la constitution y
  no apto para producción); `django-tailwind` (agrega una dependencia Python y Node); Node en el
  contenedor (más peso y otra cadena de herramientas para el equipo).

## R2. Dónde viven la fuente y el CSS compilado

- **Decision**: carpeta `static/` en la raíz con `STATICFILES_DIRS = [BASE_DIR / "static"]`:
  - `static/src/aqualab.css`: entrada de Tailwind (tema, fuentes y componentes).
  - `static/css/aqualab.css`: salida minificada, **versionada en el repo**.
  Se compila con `docker compose exec web tailwindcss -i static/src/aqualab.css -o static/css/aqualab.css --minify`
  (o `--watch` mientras se trabaja en templates).
- **Rationale**: versionar el CSS compilado permite que la app funcione con un `git pull` sin compilar
  y que el CI no necesite compilar para correr los tests.
- **Riesgo y control**: que alguien cambie clases en un template y no recompile. El CI agrega un paso
  que descarga el mismo binario, recompila y falla si `static/css/aqualab.css` cambió
  (`git diff --exit-code`).
- **Alternatives considered**: compilar en el arranque del contenedor (el CSS no estaría en el repo y
  el CI/Render necesitarían el binario siempre); no versionar y compilar en el deploy (se decide en la
  semana 5 junto con Render, no ahora).

## R3. Qué archivos escanea Tailwind

- **Decision**: `@import "tailwindcss" source(none);` y fuentes explícitas: `templates/`,
  `*/templates/`, `*/forms.py` y `*/static/**/*.js`.
- **Rationale**: sin `source(none)` Tailwind escanearía también `specs/013-diseno-ui/stitch/*.html`
  y metería en el CSS clases de las maquetas que no se usan. Los `forms.py` se incluyen porque ahí se
  asignan clases a los widgets.

## R4. Tema único a partir de Stitch

- **Decision**: un solo bloque `@theme` en `static/src/aqualab.css` con los tokens de
  `stitch/DESIGN.md` (paleta azul marino `#0f2744`, cian `#0ea5e9`, turquesa `#14b8a6`, superficies
  slate, estados verde/ámbar/rojo, tipografía Inter, radios 4–12 px, sombras de nivel 1–3). Las
  pequeñas diferencias entre las configuraciones de cada `code.html` se resuelven a favor de
  `DESIGN.md`.
- **Rationale**: FR-014 y la constitution piden un único sistema visual con tokens definidos una vez.
- **Nota**: de `DESIGN.md` se toman solo los tokens visuales; las funciones que describe (bandejas de
  filtros, métricas PPM, etc.) no forman parte de esta feature.

## R5. Fuentes e íconos sin recursos externos (FR-018)

- **Decision**:
  - **Inter**: archivo `InterVariable.woff2` (licencia OFL) en `static/fuentes/`, declarado con
    `@font-face` en `aqualab.css`.
  - **Íconos**: SVG de **Lucide** (licencia ISC) copiados a `templates/ui/iconos/<nombre>.svg`
    (solo los ~20 que se usan) e insertados con el parcial `ui/icono.html`.
- **Rationale**: Stitch usa Google Fonts y la fuente Material Symbols; la fuente de íconos completa
  pesa varios MB y depende de ligaduras de texto. Los SVG en línea pesan poco, heredan el color del
  texto y no requieren red.
- **Alternatives considered**: seguir con Google Fonts (dependencia externa en tiempo de ejecución);
  auto-hospedar Material Symbols (archivo grande para ~20 íconos).

## R6. Imágenes

- **Decision**: la imagen generada por Stitch (`stitch/imagenes/laboratorio.png`, 1,3 MB) se
  convierte a WebP optimizado (≈ 200 KB, ancho máximo 1600 px) en `static/img/acceso/laboratorio.webp`
  y se usa en el layout de acceso y en el banner del inicio con un degradado azul encima. Los enlaces a
  `lh3.googleusercontent.com` de las maquetas no se usan.
- **Rationale**: los enlaces de Stitch pueden dejar de funcionar y violan FR-018; la imagen es
  generada por IA para el proyecto (sin derechos de terceros).

### R6b. Imágenes que alternan en las pantallas de acceso (FR-022)

- **Decision**: 4 imágenes generadas con Stitch (`stitch/imagenes/`: laboratorio, mesada-muestras,
  toma-de-muestra, tubos-pipeta), convertidas a WebP (≈ 150–200 KB cada una) en `static/img/acceso/`.
  Se apilan en el panel izquierdo de `base_acceso.html` y se alternan **solo con CSS**: una animación
  `@keyframes` de opacidad de 28 s con `animation-delay` escalonado (7 s por imagen, fundido de ~1 s).
  Con `@media (prefers-reduced-motion: reduce)` se desactiva la animación y queda la primera imagen.
  El degradado oscuro y la textura de puntos van encima de todas, así el logo y la frase se leen igual.
  La primera imagen se carga normal; las otras con `loading="lazy"` y `decoding="async"`.
- **Rationale**: sin JavaScript ni librerías; accesible; peso acotado (~700 KB) solo en las pantallas
  de acceso.
- **Alternatives considered**: carrusel con JS (más código, sin beneficio); una sola imagen (decisión
  del equipo de darle más vida a la demo).

## R7. Compatibilidad con las clases que asignan los formularios

- **Decision**: los `forms.py` (usuarios, clientes, muestras, estudios) asignan `form-control`,
  `form-select` e `is-invalid` a los widgets. Se mantienen **esos tres nombres** y se definen como
  componentes en `@layer components` de `aqualab.css`. No se cambia Python para el estilo de los campos.
- **Rationale**: (1) cero cambios en los formularios; (2) `muestras/static/muestras/registro_muestra.js`
  y `muestras/tests/test_registro.py` dependen de `is-invalid`; (3) los formularios de las US 5.2–5.5
  que se están haciendo en paralelo copian el mismo patrón y quedan estilizados sin tocarlos.
- **Alternatives considered**: renombrar a clases propias (`campo`, `campo--error`): más prolijo pero
  obliga a cambiar 4 formularios, el JS y un test, y rompe la adaptación automática de 5.2–5.5.

## R8. Tipo de vertido como control segmentado

- **Decision**: el campo `tipo_vertido` de `RegistroMuestraForm` pasa de `Select` a `RadioSelect`
  y se dibuja como botones segmentados (Agua / Cloacal / Canal), como en Stitch. Mismas opciones,
  mismo valor por defecto (Agua) y mismas validaciones.
- **Impacto en tests**: `muestras/tests/test_registro.py` verifica el valor por defecto buscando un
  `<select>` (línea 87); se adapta la aserción para buscar el radio `agua` marcado como `checked`. La
  regla verificada (Agua por defecto) no cambia. Es el único test que se modifica por marcado.
- **Alternatives considered**: mantener el desplegable (sin cambio de test, pero se pierde una mejora
  clara del diseño aprobado).
- **Mismo criterio para `tipo_documento`** de `RegistroClienteForm` (DNI / CUIT, usado en registrar y
  editar cliente): `RadioSelect` segmentado, sin la opción vacía "---------" (las opciones se fijan a
  DNI y CUIT). Ningún test de clientes depende del `<select>`.

## R9. Menú activo

- **Decision**: el parcial del menú compara `request.resolver_match.namespace` y `url_name` para
  destacar módulo y subítem. Sin context processors nuevos.
- **Rationale**: Django ya expone `resolver_match` en `request`; es la opción más simple.

## R10. Panel de inicio

- **Decision**: la ruta `""` (`name="inicio"`) deja de ser un `TemplateView` y pasa a una vista de
  función `inicio` en `config/views.py`, que arma el contexto del panel con cuatro consultas
  (ver [data-model.md](data-model.md)). La URL y el nombre no cambian.
- **Rationale**: el panel lee datos de `muestras` y `estudios`; ponerlo en una de esas apps crearía
  una dependencia rara (una app mostrando datos de otra). `config/` ya contiene las rutas globales y el
  inicio es una pantalla global, no un módulo del dominio. No se crea una app nueva (YAGNI).
- **Alternatives considered**: nueva app `panel` (más estructura para una sola vista); vista en
  `muestras` (acopla muestras con estudios).

## R11. JavaScript

- **Decision**: se elimina el JS de Bootstrap (`bootstrap.bundle`). Un archivo propio
  `static/js/aqualab.js` (sin dependencias, < 40 líneas) resuelve: cerrar mensajes y abrir/cerrar el
  menú lateral en pantallas angostas. `sesion.js` y `registro_muestra.js` no cambian (usan el atributo
  `hidden` y la clase `sesion-oculta`, que siguen funcionando con Tailwind).
- **Alternatives considered**: Alpine.js (otra dependencia para dos comportamientos triviales).

## R12. Responsive

- **Decision**: menú lateral fijo de 260 px desde `lg` (≥ 1024 px); por debajo, barra superior con un
  botón que despliega el menú. Tablas con desplazamiento horizontal **dentro** de su tarjeta
  (`overflow-x-auto`) para que la página nunca se desplace (FR-016, SC-005).

## R13. Formato del número de documento

- **Decision**: **fuera de alcance**. Las maquetas muestran el CUIT con guiones (30-71234567-8), pero
  hoy se guarda y se muestra sin ellos. Formatearlo cambia lo que ven y verifican varios tests de
  clientes; queda como mejora posible en otra US.

## R14. Aviso de cuenta pendiente en el login

- **Decision**: el error "Tu cuenta está pendiente de aprobación" (código `pendiente_aprobacion`, ya
  existente en `FormularioInicioSesion`) se muestra en ámbar como advertencia; los demás errores del
  login siguen en rojo. Para que el template lo distinga se agrega a `FormularioInicioSesion` una
  propiedad de solo lectura `cuenta_pendiente` (`self.has_error(NON_FIELD_ERRORS, "pendiente_aprobacion")`),
  porque los templates no pueden llamar `has_error` con argumentos. El texto y la lógica del login no
  cambian.
- **Alternatives considered**: comparar el texto del mensaje en el template (frágil ante un cambio de
  redacción).

## R15. Pantalla propia de solicitudes pendientes

- **Decision**: fuera de alcance. Aprobar y rechazar siguen en el admin de Django; una pantalla propia
  se propondrá al equipo como US futura.

## R16. Integración con las US 5.2–5.5 (en paralelo)

- **Decision**: antes de abrir el PR se trae `main` a esta rama. Las pantallas nuevas de 5.2–5.5 que
  ya estén mergeadas se adaptan con los parciales de esta feature como tareas finales; los conflictos
  esperables son en `templates/base.html` (links del menú) y se resuelven agregando los links al
  parcial del menú.
