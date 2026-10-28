# Implementation Plan: Diseño de la interfaz

**Branch**: `013-diseno-ui` | **Date**: 2026-10-28 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/013-diseno-ui/spec.md`

## Summary

Reemplazar Bootstrap 5.3 por **Tailwind CSS 4** (compilado con el CLI standalone, sin Node) e
implementar el diseño aprobado en Stitch (`stitch/`) en las 15 pantallas existentes, con dos layouts
(interno y de acceso), parciales reutilizables en `templates/ui/` y un tema único tomado de
`stitch/DESIGN.md`. El inicio pasa a ser un panel con accesos rápidos, tres indicadores y la tabla de
últimas muestras (única lógica nueva: una vista de solo lectura). Fuentes, íconos e imágenes se sirven
desde el repo. No cambian modelos, URLs, formularios (salvo el widget de tipo de vertido) ni textos.

## Technical Context

**Language/Version**: Python 3.12, Django 5.2 LTS; Tailwind CSS 4 (CLI standalone, versión fijada en
`Dockerfile` y CI).

**Primary Dependencies**: Django (templates, staticfiles, messages). Sin dependencias Python nuevas.
Recursos estáticos nuevos versionados: Inter (`InterVariable.woff2`, OFL), íconos SVG de Lucide (ISC),
imagen generada por Stitch.

**Storage**: PostgreSQL 16 (sin cambios de esquema; el panel solo lee).

**Testing**: pytest-django + ruff. CI: nuevo paso que recompila el CSS y falla si difiere del versionado.

**Target Platform**: navegador de escritorio (Chrome/Firefox/Edge actuales), usable desde 375 px.

**Project Type**: web server-rendered (Django templates).

**Performance Goals**: CSS compilado y minificado < 60 KB; imagen de fondo ≈ 200 KB (WebP); el inicio
hace 4 consultas.

**Constraints**: sin CDN ni recursos externos (FR-018); sin cambios de comportamiento (FR-012); los
ganchos de JS y tests se conservan ([contracts/componentes-ui.md](contracts/componentes-ui.md)).

**Scale/Scope**: 15 templates de pantalla, 2 layouts, ~13 parciales, 1 vista nueva, 1 widget cambiado.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio / sección | Cumplimiento | Estado |
|---|---|---|
| **I. Spec primero** | Spec 013 escrita; trazabilidad SCRUM-67; el panel con datos se agregó primero a la spec | ✅ |
| **II. Simplicidad / Django idiomático** | Templates de Django, sin SPA. Sin dependencias Python. Tailwind es la herramienta de UI fijada en la constitution v1.1.0. La vista del inicio va en `config/views.py` (pantalla global, no módulo; sin app nueva). JS propio mínimo | ✅ |
| **III. Tests obligatorios** | Tests nuevos para el panel (cada escenario de la US 4), menú activo, layouts y ausencia de CDN. Suite existente sin cambios salvo una aserción de marcado (research R8) | ✅ |
| **IV. Integridad de datos** | Sin cambios de modelos; el panel es de solo lectura | ✅ |
| **V. Seguridad** | El inicio sigue protegido por `LoginRequiredMiddleware`; CSRF sin cambios; sin recursos de terceros | ✅ |
| **VI. Idioma** | Textos en español; nombres de parciales en español | ✅ |
| **Interfaz (UI)** | Diseño de Stitch, tokens en un único `@theme`, parciales con `{% include %}`, CSS compilado y versionado, sin CDN | ✅ |
| **Flujo de trabajo** | Rama `013-diseno-ui`, PR con CI y una aprobación; la enmienda de la constitution viaja en el mismo PR (requiere mayoría del equipo) | ✅ |

**Post-design re-check**: sin violaciones nuevas. Ver decisiones en [research.md](research.md).

## Project Structure

### Documentation (this feature)

```text
specs/013-diseno-ui/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── componentes-ui.md
│   └── pantallas.md
├── checklists/requirements.md
├── stitch/                  # exportación de Stitch (referencia visual, no se sirve)
└── tasks.md                 # /speckit-tasks
```

### Source Code (repository root)

```text
Dockerfile                    # + binario tailwindcss (ARG TAILWIND_VERSION, según arquitectura)
.github/workflows/ci.yml      # + paso "CSS compilado al día"
config/
├── settings.py               # + STATICFILES_DIRS = [BASE_DIR / "static"]
├── urls.py                   # "" → views.inicio (mismo name="inicio")
├── views.py                  # NUEVO: vista del panel de inicio
└── tests/                    # NUEVO: test_inicio.py, test_layout.py
static/
├── src/aqualab.css           # NUEVO: @import tailwindcss, @theme, @font-face, @layer components
├── css/aqualab.css           # NUEVO: compilado y versionado
├── fuentes/InterVariable.woff2
├── img/acceso/*.webp         # 4 imágenes de Stitch que alternan en el acceso (la primera también en el banner del inicio)
└── js/aqualab.js             # NUEVO: cerrar mensajes, menú en pantallas angostas
templates/
├── base.html                 # reescrito: layout interno
├── base_acceso.html          # NUEVO: layout de acceso
├── inicio.html               # reescrito: panel
├── includes/guardia_sesion.html   # solo clases del botón
└── ui/                       # NUEVO: menu, mensajes, encabezado, campo, errores_form, seccion_form,
    │                         #   resumen, acciones_confirmacion, estado_vacio, paginacion, estado,
    │                         #   icono, iniciales
    └── iconos/*.svg          # Lucide
usuarios/forms.py             # + propiedad FormularioInicioSesion.cuenta_pendiente (research R14)
usuarios/templates/usuarios/  # login, registro_form, registro_confirmar, registro_recibido → base_acceso
clientes/forms.py             # tipo_documento: Select → RadioSelect (DNI / CUIT)
clientes/templates/clientes/  # 6 templates
muestras/forms.py             # tipo_vertido: Select → RadioSelect
muestras/templates/muestras/  # 2 templates; _campo.html se reemplaza por ui/campo.html
muestras/tests/test_registro.py   # aserción del valor por defecto: <select> → radio checked
estudios/templates/estudios/  # 2 templates
README.md                     # stack, "Estilos (Tailwind)", estructura y "una app por módulo"
```

**Structure Decision**: proyecto Django único existente. Lo nuevo de la UI vive en `static/` y
`templates/ui/` (compartido por todas las apps); cada app conserva sus templates.

## Orden de implementación sugerido

1. **Infraestructura**: binario en Docker, `static/src/aqualab.css` con el tema, `STATICFILES_DIRS`,
   compilación y paso de CI.
2. **Layouts y parciales** (US 1): `base.html`, `base_acceso.html`, menú, mensajes, encabezado, íconos.
3. **Formularios y confirmaciones** (US 2): `campo`, `errores_form`, `seccion_form`, `resumen`,
   `acciones_confirmacion`; migrar las 11 pantallas de formularios y confirmaciones.
4. **Consulta** (US 3): buscar cliente, ficha, `estado`, `estado_vacio`, `paginacion`.
5. **Panel de inicio** (US 4): tests primero, vista y template.
6. **Cierre**: README, recorrido del quickstart, merge de `main` y adaptación de las
   pantallas de 5.2–5.5 que ya estén integradas.

## Complexity Tracking

Sin violaciones de la constitution que justificar.
