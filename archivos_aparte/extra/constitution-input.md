# Insumo para /speckit-constitution — AquaLab

> Este archivo es el texto base para generar `.specify/memory/constitution.md`.
> Proyecto: AquaLab — Grupo 7 — Gestión del Desarrollo de Sistemas Informáticos (FIUBA).
> Escribir la constitution en **español**.

## Contexto del proyecto

AquaLab es una app web para laboratorios de análisis de agua. Centraliza clientes, muestras, estudios, pruebas, resultados e informes; automatiza el cálculo de resultados y la generación del informe final en PDF. Su diferencial es la comparación histórica de resultados de un mismo origen (fuente de agua) y la notificación de desvíos.

Equipo: 6 personas. Duración: 6 sprints de 1 semana. Se planifica sprint a sprint (de demo a demo). Trabajo con Spec-Driven Development (Spec Kit + Claude Code).

## Principios

### I. Spec primero (SDD)
- No se escribe código de producto sin una spec aprobada por el equipo.
- Por defecto, **1 user story = 1 spec**. Se agrupan US solo si son muy chicas y las hace la misma persona.
- Las specs se escriben **sprint a sprint**: solo para las US del sprint actual, nunca todo el backlog de una vez.
- Cada persona trabaja en **una spec a la vez**, para evitar bloqueos entre personas.
- La spec (`spec.md`) describe el **qué** y el **por qué**, sin detalles técnicos. El **cómo** va en `plan.md`.
- Trazabilidad: cada spec indica el número de US del backlog (ej. "US 2.1") y cada PR referencia su spec y su US.
- Si un requisito cambia, se actualiza primero la spec y después el código.

### II. Simplicidad y Django idiomático
- Usar primero lo que Django ya trae: autenticación, admin, ORM, formularios, migraciones, mensajes.
- Pantallas renderizadas en el servidor con templates de Django. **No** se usa un frontend SPA (React, Vue, etc.).
- No se agregan dependencias nuevas sin acuerdo del equipo (se justifica en el `plan.md`).
- YAGNI: no se implementa nada que no pida una spec.
- Una app de Django por módulo: `usuarios`, `clientes`, `muestras`, `estudios`, `pruebas`, `informes`, `comparacion`.

### III. Tests obligatorios (NO NEGOCIABLE)
- Cada escenario de aceptación de la spec (Dado/Cuando/Entonces) tiene al menos un test automatizado con pytest-django.
- Los **cálculos de resultados** (fórmulas, factores, unidades) se prueban con casos conocidos y valores esperados explícitos. Es un riesgo identificado del proyecto.
- No se mergea con tests fallando ni con errores de ruff.

### IV. Integridad de los datos del laboratorio
- Las mediciones y resultados numéricos se guardan con `Decimal`, nunca con `float`.
- Todo resultado se guarda junto con su **unidad**.
- Un resultado validado y un informe emitido no se pueden modificar.
- No se borran registros que tengan historial asociado (clientes, muestras, tipos de estudio usados): se desactivan.
- Toda muestra tiene un código único (N° PI) y queda asociada a su cliente y a su origen.
- Las validaciones de reglas de negocio van en el modelo o en el formulario, no solo en el template.

### V. Seguridad
- Todas las vistas requieren sesión iniciada, salvo login y registro.
- Las contraseñas las maneja el sistema de autenticación de Django (nunca en texto plano).
- Secretos y credenciales solo por variables de entorno (`.env`, que **no** se sube al repo). La base se configura con `DATABASE_URL`.
- Protección CSRF activa en todos los formularios.

### VI. Idioma y consistencia
- Interfaz, mensajes al usuario, specs y documentación: en **español**.
- Los nombres del dominio siguen el **Glosario** del proyecto: Cliente, Muestra, Origen, Estudio, Tipo de estudio, Prueba, Medición, Resultado, Informe.
- Modelos, variables y funciones del dominio se nombran en español con esos términos (ej. `Cliente`, `Muestra`, `tipo_estudio`). Lo propio de Django queda como es.
- Formato de código: ruff (lint + format), sin excepciones.

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
| GitHub + GitHub Actions | Repo, PR y CI (pytest + ruff en cada PR) |
| Jira | Gestión de sprints |

Se agregan **solo cuando lo pida una spec** (semana 5):
- WeasyPrint → informes en PDF (requiere librerías del sistema en el `Dockerfile`).
- Chart.js → gráficos de la comparación histórica.
- Render → deploy (la base gratis vence a los 30 días: crearla recién en la semana 5).

## Interfaz (UI)

- Layout base común (`base.html`) con barra de navegación, usuario logueado y botón de cerrar sesión.
- Componentes de Bootstrap 5.3; sin CSS propio salvo lo mínimo.
- Formularios con mensajes de error claros junto a cada campo.
- Las acciones que guardan o eliminan datos piden **confirmación** antes de ejecutarse (patrón común para todo el sistema).
- Mensajes de éxito/error con el framework de mensajes de Django.
- Orientado a escritorio (uso dentro del laboratorio).

## Flujo de trabajo

- **Ramas:** una rama por spec (la crea Spec Kit, ej. `002-registrar-cliente`). Nadie pushea directo a `main` (protegida en GitHub).
- **Pull Requests:** el título menciona la US (ej. "US 2.1 – Registrar cliente"). Requiere:
  1. CI en verde (pytest + ruff).
  2. Al menos **1 aprobación** de un integrante que no sea el autor, revisando spec y código.
- El autor mergea su propio PR una vez aprobado.
- La spec, el plan y las tareas (`specs/NNN-.../`) se commitean junto con el código: son parte de la entrega.
- **Jira:** columnas TODO → DOING → TEST → DONE.
  - TODO: US en el sprint, sin empezar.
  - DOING: de `specify` a `implement`.
  - TEST: PR abierto, en revisión, con CI corriendo.
  - DONE: PR mergeado.

## Gobierno

- Esta constitution está por encima de cualquier otra práctica del proyecto. Los `plan.md` deben verificar que la cumplen.
- Cambios a la constitution: por PR, aprobado por la mayoría del equipo, con versión actualizada (semver: MAJOR para cambios de principios, MINOR para agregados, PATCH para aclaraciones).
- Cualquier excepción a un principio se justifica por escrito en el `plan.md` de la spec.
