# Guía SDD paso a paso — cómo implementar una user story con Spec Kit

> Basada en lo que hicimos con la **US 1.1 – Registrar usuario** (`specs/001-registrar-usuario/`).
> Sirve como receta para las próximas specs (002, 003, ...).

---

## Resumen del flujo

```text
specify → (revisión) → plan → tasks → analyze → implement (2 tandas) → prueba manual → PR
```

| Paso | Comando | Qué genera | Escribe código |
|---|---|---|---|
| 1 | `/speckit-specify` | `spec.md` — el **qué** y el **por qué** | No |
| 2 | `/speckit-plan` | `plan.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md` — el **cómo** | No |
| 3 | `/speckit-tasks` | `tasks.md` — lista de tareas en orden | No |
| 4 | `/speckit-analyze` | Un **reporte en pantalla** (no crea archivos) | No |
| 5 | `/speckit-implement` | El código y los tests | **Sí** |

**Regla de oro:** revisar cada archivo antes de pasar al siguiente paso. Si la spec está mal, el código va a estar mal aunque los tests pasen.

---

## 0. Antes de empezar

En la terminal de Ubuntu:

```bash
cd ~/proyectos/AquaLab
git switch main && git pull
docker compose up -d
```

- `docker compose ps` tiene que mostrar `web` y `db` corriendo.
- Si nunca levantaste el proyecto, seguí primero el [README](../../README.md).
- Leé el [CLAUDE.md](../../CLAUDE.md): tiene los **pendientes entre features** (por ejemplo, lo que la US 1.2 tiene que resolver).

**Jira:** mové la tarjeta de tu US a **DOING**.

---

## 1. Spec (`/speckit-specify`) y rama

**ESTA PARTE NO PUEDE SER SIMULTANEA, PORQUE SINO LAS SUBCARPETAS DE LA CARPETA SPEC SE ENUMERARIAN CON EL MISMO NUMERO**
**ES O HACERLO POR SEPARADO, O ACLARARLO EN EL PROMPT DEL SPECIFY**

La spec describe **qué** tiene que hacer la US y **por qué**, sin nada técnico. Es lo que revisa todo el equipo (y la correctora).

Hay dos casos:

### Caso A — La spec ya existe (ej. Sprint 1: 001, 002, 003)

Solo hay que crear la rama. El nombre tiene que ser **exactamente** el de la carpeta de la spec: Spec Kit se guía por el nombre de la rama para saber en qué feature estás.

```bash
git switch -c 002-inicio-cierre-sesion
claude
```

(Cambiá `002-inicio-cierre-sesion` por tu spec: `003-registrar-cliente`, etc.) Después seguí desde el paso 2.

### Caso B — La spec no existe (US de los sprints siguientes)

Desde `main` actualizado, abrí Claude Code:

```bash
git switch main && git pull
claude
```

Y corré el comando con la US tal como está en Jira:

```
/speckit-specify US X.Y – Título (SCRUM-NN). Como [rol] quiero [acción] para [beneficio]. Criterios de aceptación: [pegar los criterios de Jira]
```

Spec Kit **crea la rama** (`NNN-nombre`, con el número siguiente) y el archivo `specs/NNN-nombre/spec.md`, con:

- **User Scenarios**: la historia y sus escenarios **Dado / Cuando / Entonces** (cada uno va a ser al menos un test).
- **Edge Cases**: casos borde.
- **Functional Requirements**: reglas numeradas (FR-001, FR-002, ...).
- **Key Entities**: los "objetos" del dominio (sin detalles técnicos).
- **Success Criteria**: cómo saber que funciona, con números.
- **Assumptions**: lo que la IA asumió para no frenar.
- `checklists/requirements.md`: una autoevaluación de calidad que hace la IA (no reemplaza la revisión del equipo).

**Revisar si se creo la rama, no se si lo hace solo, tengo entendido que si**

#### Qué revisar en la spec

- Los escenarios se pueden **probar en este sprint** (no dependen de US futuras, ej. "cuando registra una muestra" si las muestras todavía no existen).
- **Nada técnico**: no menciona Django, tablas, URLs ni pantallas concretas.
- Las **Assumptions**: si alguna decide algo de producto (ej. "el teléfono es opcional"), lo confirma el equipo, no la IA.
- No quedan marcas `[NEEDS CLARIFICATION]`. Si quedan dudas, correr:

  ```
  /speckit-clarify
  ```
  que hace preguntas sobre lo ambiguo y actualiza la spec con las respuestas.

- [ ] Coincide con la US de **Jira** (si la spec cambia un criterio, actualizar también la tarjeta).

#### Commit

```bash
git add specs/ && git commit -m "docs(specs): spec de la US X.Y – Nombre"
git push -u origin NNN-nombre-de-la-rama
```

> En el Sprint 1 las tres specs se hicieron juntas en una rama aparte (`sprint-1-specs`) y se mergearon por PR antes de empezar. Funciona, pero después hay que crear la rama `NNN-...` de cada una (caso A) para seguir con el plan.

---

## 2. Plan (`/speckit-plan`)

Define **cómo** se va a construir la US: modelos, pantallas, URLs, decisiones técnicas.

### Prompt

```
/speckit-plan Stack según la constitution. [Agregá acá las decisiones técnicas que ya tengan tomadas y cualquier dependencia con otras US. Ej. para la 002: "Leé los pendientes de la US 1.2 en CLAUDE.md y la decisión R3 de specs/001-registrar-usuario/research.md".]
```

---

## 3. Tasks (`/speckit-tasks`)

Convierte el plan en una lista de tareas concretas (`T001`, `T002`, ...), cada una con el archivo que toca.

### Prompt

⚠️ La plantilla de Spec Kit trata los tests como **opcionales**. La constitution los exige, así que hay que pedirlos explícitamente.

```
/speckit-tasks Incluí tareas de tests: la constitution exige al menos un test por escenario de aceptación, usá el "Mapa de tests" del plan. El setup de infraestructura ya está hecho (modelo Usuario, settings, LoginRequiredMiddleware, base.html, Docker y CI): no generes tareas para recrearlo.
```

---

## 4. Analyze (`/speckit-analyze`)

Cruza **spec + plan + tasks + constitution** y busca inconsistencias. **No modifica archivos**: muestra un reporte con hallazgos ordenados por gravedad.

```
/speckit-analyze
```

### Qué hacer con el reporte

| Gravedad | Qué hacer |
|---|---|
| **CRITICAL** | Resolver **sí o sí** antes del implement. Suele ser algo que viola la constitution: o se corrige, o se justifica por escrito en **Complexity Tracking** del `plan.md` |
| **MEDIUM** | Resolver casi siempre (son baratos y evitan bugs) |
| **LOW** | Decidir caso por caso; está bien dejarlos |

Si un hallazgo cambia un **requisito**, se corrige **primero en `spec.md`** (principio I de la constitution).

> En la 001 el analyze encontró: 1 crítico (una acción sin confirmación → se justificó), un requisito decidido pero no escrito en la spec (→ FR-016), un test faltante y dos inconsistencias menores.

Opcional: volver a correr `/speckit-analyze` después de corregir, para confirmar que quedó limpio.

---

## 5. Implement (`/speckit-implement`) — en dos tandas

La IA escribe el código siguiendo `tasks.md` y va tildando las tareas (`- [ ]` → `- [X]`). Conviene hacerlo **en dos tandas** para revisar en el medio.

### Tanda 1: fases 1 y 2 (base)

```
/speckit-implement Implementá solo las fases 1 y 2 y frená. Corré todos los comandos dentro de Docker (docker compose exec web ...). No modifiques spec.md, plan.md ni los contratos; en tasks.md solo marcá las tareas completadas. No hagas commit.
```

### Tanda 2: el resto

```
/speckit-implement Continuá con las fases restantes. Escribí primero los tests, corrélos y mostrame que fallan antes de implementar. Después implementá y dejá todos los tests en verde. Corré todos los comandos dentro de Docker (docker compose exec web ...). En la validación manual no abras un navegador: decime qué pasos tengo que probar yo. No modifiques spec.md, plan.md ni los contratos; en tasks.md solo marcá las tareas completadas. No hagas commit.
```

---