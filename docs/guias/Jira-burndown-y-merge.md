# Jira, burndown/burnup y cuándo se mergea

> Grupo 7 · AquaLab · Guía de cómo organizamos el trabajo durante los sprints

---

## Índice

1. [Cómo funciona Jira](#1-cómo-funciona-jira)
2. [Burndown y burnup](#2-burndown-y-burnup)
3. [Cuándo se mergea](#3-cuándo-se-mergea)
4. [Reglas para la constitution](#4-reglas-para-la-constitution)
5. [Armar Jira paso a paso](#5-armar-jira-paso-a-paso)

---

## 1. Cómo funciona Jira

Jira es una herramienta web para organizar el trabajo de un equipo. Es como la pestaña **"Sprint n"** de la planilla, pero con más funciones.

### Las piezas

| Concepto | Qué es | En AquaLab |
|---|---|---|
| **Proyecto** | El espacio del equipo | "AquaLab" |
| **Issue** | Cualquier tarjeta de trabajo. Hay varios tipos ⬇️ | — |
| ↳ **Epic** | Un bloque grande que agrupa historias | "Gestión de clientes", "Gestión de muestras"… (los módulos del WBS) |
| ↳ **Story** | Una historia de usuario | 1.1 Registrar usuario, 2.1 Registrar cliente… |
| ↳ **Task** | Una tarea que no es historia | "Setup de infraestructura" |
| ↳ **Sub-task** | Una parte de una historia o tarea | Opcional; pueden ser las tareas de `tasks.md` |
| **Backlog** | La lista de todas las historias que todavía no están en un sprint | La pestaña Backlog-US |
| **Sprint** | Un período fijo de trabajo | 1 semana cada uno, 6 en total |
| **Board** | El tablero con columnas donde se mueven las tarjetas | TODO / DOING / TEST / DONE |
| **Story points** | La estimación del esfuerzo de cada historia | La columna "Estimación" del backlog (hoy está vacía) |

### El ciclo de un sprint en Jira

```
BACKLOG  ──(Sprint Planning)──►  SPRINT ACTIVO  ──(fin de semana)──►  CERRAR SPRINT
 todas las US                    TODO → DOING → TEST → DONE           lo que no llegó a DONE
                                                                      vuelve al backlog
```

1. **Sprint Planning** (está en el plan de comunicación): desde el backlog se eligen las US del sprint, por ejemplo la 1.1, la 1.2 y la 2.1, y se meten en el sprint.
2. **Start sprint:** Jira arranca el reloj de la semana.
3. Durante la semana, cada uno **arrastra su tarjeta** de una columna a otra a medida que avanza.
4. **Complete sprint:** al final, Jira cierra el sprint. Lo que no llegó a DONE vuelve al backlog o pasa al sprint siguiente.

### Columnas del tablero

Son las mismas de la pestaña "Sprint n", así todo se puede pasar a Jira (pedido de la correctora):

- **TODO:** la US está en el sprint y nadie la empezó.
- **DOING:** de `specify` a `implement`.
- **TEST:** PR abierto, con revisión de un compañero y tests en verde.
- **DONE:** PR mergeado.

---

## 2. Burndown y burnup

Son dos gráficos que muestran **si el equipo va a llegar o no**. Jira los genera solo, a partir de cómo se mueven las tarjetas y de los **story points**. Por eso es importante completar la estimación de cada historia.

### Burndown: "cuánto falta"

Arranca con todo el trabajo del sprint y va **bajando** a medida que se terminan historias.

```
Puntos
pendientes
 13 │●
    │  ·  ●            ● = real
  9 │     ·  ●         · = ideal (ritmo parejo)
    │        ·  ●
  5 │           ·    ●
    │              ·
  0 │________________·___
     Lun Mar Mié Jue Vie
```

- Línea real **arriba** de la ideal → atrasados.
- Línea real **abajo** de la ideal → adelantados.
- Línea **plana** varios días → hay algo trabado.

### Burnup: "cuánto hicimos"

Muestra dos líneas que **suben**: el trabajo completado y el alcance total. Sirve para ver el proyecto entero, sprint por sprint.

```
Puntos
 60 │                    ___ alcance total
    │________________---‾‾   (subió: agregaron el dashboard)
 40 │                    ●
    │               ●        ● = completado acumulado
 20 │         ●
    │    ●
  0 │●________________________
     S1   S2   S3   S4   S5   S6
```

- Cuando las dos líneas **se juntan**, el proyecto está terminado.
- Ventaja sobre el burndown: se ve cuando **cambia el alcance**. Por ejemplo, al agregar el dashboard (8.1 y 8.2) la línea de alcance sube. En un burndown eso no se distingue de "no avanzamos".

### Lo que ya tenemos

La pestaña **"Avance"** de la planilla ya es la base de un burnup: tiene "Planificado" y "Planificado acumulado" por sprint (del 1 al 7). Falta:

- [ ] Estimar las historias (story points) para que los valores dejen de ser 0 y 10.
- [ ] Agregar una fila **"Real acumulado"** y completarla al cierre de cada sprint.
- [ ] Graficar "Planificado acumulado" vs "Real acumulado".

---

## 3. Cuándo se mergea

### Qué es mergear

En Git, `main` es la rama principal, donde está el código "bueno" que funciona. Nadie trabaja directo ahí. Cada uno trabaja en **su propia rama** y, cuando termina, la **une (mergea)** con `main`.

Spec Kit ya crea una rama por cada spec, por ejemplo `001-registrar-usuario`.

### El recorrido de una US

```
main ──●────────────────────────────────●──── (código con la US 1.1)
        \                              /
         ●───●───●───●───────●───────●       rama 001-registrar-usuario
        specify plan tasks implement  PR → revisión → merge
        └──────── DOING ────────┘   └─ TEST ─┘   DONE
```

1. **DOING:** en tu rama hacés `specify`, `plan`, `tasks` e `implement`, y vas commiteando.
2. Cuando terminás, abrís un **Pull Request (PR)** en GitHub: un pedido de "quiero sumar esto a `main`". La tarjeta pasa a **TEST**.
3. Con el PR abierto pasan dos cosas:
   - **GitHub Actions** corre los tests y ruff automáticamente, y tienen que dar ✅.
   - **Un compañero revisa** el código y la spec. Si encuentra algo, deja comentarios, se corrige en la misma rama y el PR se actualiza solo.
4. **Se mergea cuando se cumplen las dos condiciones:** tests en verde y aprobación de un compañero. Ahí la tarjeta pasa a **DONE**.

---

## 4. Reglas para la constitution

- **Nadie pushea directo a `main`.** Todo entra por PR. GitHub lo puede bloquear desde *Settings → Branches → Branch protection*.
- **Cada PR requiere al menos 1 aprobación** de alguien que no sea el autor.
- **No se mergea con tests en rojo.**
- **El PR menciona la US**, por ejemplo "US 1.1 – Registrar usuario", para que se pueda rastrear.
- **Cada uno mergea su propio PR** después de que lo aprueben, así no queda trabado esperando a otro.

> La revisión de pares ya figura en el análisis de riesgos: *"exigir revisión de pares antes de mergear"*. Con estas reglas queda concreta.

---

## 5. Armar Jira paso a paso

> Jira cambió algunos nombres: los proyectos ahora se llaman **espacios (spaces)**, los issues **work items** y el tipo de issue **work type**. Si ves los nombres viejos, es lo mismo.

### Paso 1 — Crear el proyecto

1. Entrar a https://www.atlassian.com/software/jira/free y crear el sitio (plan **Free**: hasta 10 usuarios, alcanza para los 6 + Pilar).
2. **Crear espacio/proyecto → Software → Scrum.**
3. Tipo: **team-managed** (más simple de configurar).
4. Nombre: **AquaLab**. Clave: **AQL** (los issues quedan AQL-1, AQL-2…).
5. Invitar a los compañeros (y a Pilar, si la cátedra lo pide).

### Paso 2 — Configurar el tablero

1. Activar las estimaciones: **Configuración del proyecto → Funciones (Features) → Estimación → Story points**.
2. Columnas del tablero: por defecto vienen *To Do / In Progress / Done*. Renombrarlas y agregar una:
   **TODO → DOING → TEST → DONE**.
3. En **TEST** y **DONE**, verificar que el estado "DONE" sea el que marca la tarjeta como terminada (si no, los gráficos no la cuentan).

### Paso 3 — Importar el backlog (`jira-import.csv`)

El archivo `jira-import.csv` (en la raíz del repo) tiene **32 items**:

| Tipo | Cantidad | Detalle |
|---|---|---|
| Epic | 7 | Usuarios, Clientes, Muestras, Estudios, Pruebas, Informes, Comparación histórica |
| Story | 21 | Todas las US del backlog actual, **sin la 4.2** (eliminada) y **con la 3.3 y la 5.5** (nuevas). Cada una con sus criterios de aceptación, el responsable del cronograma y notas |
| Task | 4 | Constitution, Setup de infraestructura, Precargar pruebas, Deploy en Render |

Cada fila tiene una etiqueta **`semana-N`** según el cronograma, para armar los sprints rápido.

**Antes de importar:** completar la columna **Story Points** con lo que estime el equipo (hoy está vacía). También se puede cargar después desde Jira.

**Importar:**
1. Hace falta ser **administrador** del sitio (quien lo creó lo es).
2. **⚙ Configuración → Sistema → Importación y exportación → External System Import → CSV.**
3. Subir `jira-import.csv`. En *Advanced*, encoding **UTF-8** y delimitador **coma**.
4. Elegir el proyecto **AquaLab**.
5. Mapear las columnas:

| Columna del CSV | Campo de Jira |
|---|---|
| Work item ID | Work item ID |
| Parent | Parent |
| Work type | Work type |
| Summary | Summary |
| Description | Description |
| Story Points | Story point estimate (o Story Points) |
| Labels | Labels |

6. Importar y revisar que las Stories quedaron dentro de sus Epics.

### Paso 4 — Crear los sprints

1. En **Backlog → Crear sprint**, crear el **Sprint 1** con duración **1 semana**.
2. Filtrar el backlog por la etiqueta `semana-1` y arrastrar esos items al sprint (las 3 US + Constitution + Setup).
3. **Iniciar sprint** el día que arranquen. Los demás sprints se crean de a uno, en cada Sprint Planning (se planifica sprint a sprint).

### Paso 5 — Responsables

El CSV no asigna personas (Jira necesita sus cuentas). El responsable figura en la descripción de cada item: asignarlo a mano una vez que todos estén invitados.

### Cosas a revisar al importar

- **1.2:** el criterio 4 dice "identificado con su nombre **y rol**", pero el rol se sacó de la 1.1. Corregir en la planilla y en Jira.
- **4.1:** tiene una nota de que falta asociar la muestra a un **Origen** (para la 8.1).
- **5.2:** se le agregó el criterio de la 4.2 eliminada ("ver los estudios desde la ficha de la muestra"). Moverlo a la 5.1 si prefieren.
