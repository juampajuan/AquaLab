<!--
Sync Impact Report
==================
Cambio de versión: (plantilla sin completar) → 1.0.0
Motivo: ratificación inicial de la constitution de AquaLab.

Principios definidos (reemplazan los placeholders de la plantilla):
- [PRINCIPLE_1_NAME] → I. Spec primero (SDD)
- [PRINCIPLE_2_NAME] → II. Simplicidad y Django idiomático
- [PRINCIPLE_3_NAME] → III. Tests obligatorios (NO NEGOCIABLE)
- [PRINCIPLE_4_NAME] → IV. Integridad de los datos del laboratorio
- [PRINCIPLE_5_NAME] → V. Seguridad
- (nuevo)            → VI. Idioma y consistencia

Secciones agregadas:
- Stack tecnológico (reemplaza [SECTION_2_NAME])
- Interfaz (UI) (sección adicional a la plantilla)
- Flujo de trabajo (reemplaza [SECTION_3_NAME])
- Gobierno (Governance, completada)

Secciones eliminadas: ninguna.

Plantillas dependientes (leen la constitution en tiempo de ejecución, no se modifican aquí):
- .specify/templates/plan-template.md     ✅ sin cambios necesarios (Constitution Check genérico)
- .specify/templates/spec-template.md     ✅ sin cambios necesarios
- .specify/templates/tasks-template.md    ✅ sin cambios necesarios

TODOs diferidos: ninguno.
-->

# Constitution de AquaLab

AquaLab es una aplicación web para laboratorios de análisis de agua. Centraliza clientes, muestras,
estudios, pruebas, resultados e informes; automatiza el cálculo de resultados y la generación del
informe final en PDF. Su diferencial es la comparación histórica de resultados de un mismo origen
(fuente de agua) y la notificación de desvíos.

Proyecto del Grupo 7 — Gestión del Desarrollo de Sistemas Informáticos (FIUBA). Equipo de 6
personas, 6 sprints de 1 semana, planificados sprint a sprint (de demo a demo), con
Spec-Driven Development (Spec Kit + Claude Code).

## Core Principles

### I. Spec primero (SDD)

- NO se escribe código de producto sin una spec aprobada por el equipo.
- Por defecto, **1 user story = 1 spec**. Solo se agrupan US si son muy chicas y las implementa la
  misma persona.
- Las specs se escriben **sprint a sprint**: únicamente para las US del sprint actual, nunca para
  todo el backlog de una vez.
- Cada persona trabaja en **una spec a la vez**, para evitar bloqueos entre integrantes.
- La spec (`spec.md`) describe el **qué** y el **por qué**, sin detalles técnicos. El **cómo** va
  en `plan.md`.
- Trazabilidad: cada spec DEBE indicar el número de US del backlog (ej. "US 2.1") y cada PR DEBE
  referenciar su spec y su US.
- Si un requisito cambia, se actualiza primero la spec y después el código.

**Justificación**: con 6 personas en sprints de una semana, la spec es el acuerdo común que evita
retrabajo y bloqueos, y permite rastrear cada cambio hasta la US que lo originó.

### II. Simplicidad y Django idiomático

- Se usa primero lo que Django ya trae: autenticación, admin, ORM, formularios, migraciones y
  framework de mensajes.
- Las pantallas se renderizan en el servidor con templates de Django. **NO** se usa un frontend SPA
  (React, Vue, etc.).
- NO se agregan dependencias nuevas sin acuerdo del equipo; toda dependencia nueva se justifica en
  el `plan.md` correspondiente.
- YAGNI: no se implementa nada que no pida una spec.
- Una app de Django por módulo: `usuarios`, `clientes`, `muestras`, `estudios`, `pruebas`,
  `informes`, `comparacion`.

**Justificación**: el tiempo del proyecto es corto; apoyarse en las herramientas integradas de
Django reduce código propio, curva de aprendizaje y superficie de errores.

### III. Tests obligatorios (NO NEGOCIABLE)

- Cada escenario de aceptación de la spec (Dado/Cuando/Entonces) DEBE tener al menos un test
  automatizado con pytest-django.
- Los **cálculos de resultados** (fórmulas, factores, unidades) DEBEN probarse con casos conocidos
  y valores esperados explícitos.
- NO se mergea con tests fallando ni con errores de ruff.

**Justificación**: el cálculo de resultados es un riesgo identificado del proyecto; un error ahí
invalida los informes que recibe el cliente.

### IV. Integridad de los datos del laboratorio

- Las mediciones y resultados numéricos se guardan con `Decimal`, nunca con `float`.
- Todo resultado se guarda junto con su **unidad**.
- Un resultado validado y un informe emitido NO se pueden modificar.
- NO se borran registros con historial asociado (clientes, muestras, tipos de estudio usados): se
  desactivan.
- Toda muestra tiene un código único (N° PI) y queda asociada a su cliente y a su origen.
- Las validaciones de reglas de negocio van en el modelo o en el formulario, nunca solo en el
  template.

**Justificación**: los datos de un laboratorio deben ser exactos, trazables e inalterables una vez
emitidos; la comparación histórica depende de que el historial esté completo.

### V. Seguridad

- Todas las vistas requieren sesión iniciada, salvo login y registro.
- Las contraseñas las maneja el sistema de autenticación de Django; nunca se guardan en texto plano.
- Secretos y credenciales solo por variables de entorno (`.env`, que **NO** se sube al repo). La
  base de datos se configura con `DATABASE_URL`.
- La protección CSRF está activa en todos los formularios.

**Justificación**: la app maneja datos de clientes y resultados de análisis que no deben quedar
expuestos.

### VI. Idioma y consistencia

- Interfaz, mensajes al usuario, specs y documentación: en **español**.
- Los nombres del dominio siguen el **Glosario** del proyecto: Cliente, Muestra, Origen, Estudio,
  Tipo de estudio, Prueba, Medición, Resultado, Informe.
- Modelos, variables y funciones del dominio se nombran en español con esos términos (ej.
  `Cliente`, `Muestra`, `tipo_estudio`). Lo propio de Django queda como es.
- Formato de código: ruff (lint + format), sin excepciones.

**Justificación**: un vocabulario único entre specs, código e interfaz evita ambigüedades entre
los integrantes y con los usuarios del laboratorio.

## Stack tecnológico

| Herramienta | Versión / uso |
|---|---|
| Python | 3.12 |
| Django | 5.2 LTS |
| PostgreSQL | 16, en Docker |
| Docker Compose | Dos servicios: `web` (Django) y `db` (PostgreSQL). Todo el equipo desarrolla con Docker |
| Bootstrap | 5.3 (interfaz) |
| pytest-django | Tests |
| ruff | Lint y formato |
| GitHub + GitHub Actions | Repositorio, PR y CI (pytest + ruff en cada PR) |
| Jira | Gestión de sprints |

Se agregan **solo cuando lo pida una spec** (semana 5):

- **WeasyPrint** → informes en PDF (requiere librerías del sistema en el `Dockerfile`).
- **Chart.js** → gráficos de la comparación histórica.
- **Render** → deploy. La base gratuita vence a los 30 días: crearla recién en la semana 5.

## Interfaz (UI)

- Layout base común (`base.html`) con barra de navegación, usuario logueado y botón de cerrar
  sesión.
- Componentes de Bootstrap 5.3; sin CSS propio salvo lo mínimo indispensable.
- Formularios con mensajes de error claros junto a cada campo.
- Las acciones que guardan o eliminan datos piden **confirmación** antes de ejecutarse (patrón común
  para todo el sistema).
- Mensajes de éxito y error mediante el framework de mensajes de Django.
- Orientada a escritorio (uso dentro del laboratorio).

## Flujo de trabajo

- **Ramas**: una rama por spec (la crea Spec Kit, ej. `002-registrar-cliente`). Nadie pushea
  directo a `main` (protegida en GitHub).
- **Pull Requests**: el título menciona la US (ej. "US 2.1 – Registrar cliente"). Para mergear se
  requiere:
  1. CI en verde (pytest + ruff).
  2. Al menos **1 aprobación** de un integrante que no sea el autor, revisando spec y código.
- El autor mergea su propio PR una vez aprobado.
- La spec, el plan y las tareas (`specs/NNN-.../`) se commitean junto con el código: son parte de
  la entrega.
- **Jira**: columnas TODO → DOING → TEST → DONE.
  - **TODO**: US en el sprint, sin empezar.
  - **DOING**: de `specify` a `implement`.
  - **TEST**: PR abierto, en revisión, con CI corriendo.
  - **DONE**: PR mergeado.

## Governance

- Esta constitution está por encima de cualquier otra práctica del proyecto. Cada `plan.md` DEBE
  verificar su cumplimiento en la sección de chequeo de la constitution.
- Los cambios a la constitution se hacen por PR, aprobado por la mayoría del equipo, con la versión
  actualizada según semver:
  - **MAJOR**: eliminación o redefinición incompatible de principios.
  - **MINOR**: principios o secciones nuevas, o guía ampliada de forma sustancial.
  - **PATCH**: aclaraciones, redacción y correcciones sin cambio de significado.
- Cualquier excepción a un principio se justifica por escrito en el `plan.md` de la spec
  correspondiente.
- En cada revisión de PR se verifica el cumplimiento de estos principios.

**Version**: 1.0.0 | **Ratified**: 2026-10-16 | **Last Amended**: 2026-10-16
