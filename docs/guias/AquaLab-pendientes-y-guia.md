# AquaLab — Pendientes y guía de arranque

> Grupo 7 · GDSI · Resumen de la revisión de artefactos antes de arrancar con Spec Kit (15/10/2026)
>
> Fuente: planilla **Artefactos G7** — https://docs.google.com/spreadsheets/d/1eGwJ34K6d53XkLSv3lYQ4MTsHtI-pTyflUyWavfwTgA/edit

---

## Índice

1. [Checklist de cambios](#1-checklist-de-cambios)
2. [Textos listos para pegar en el backlog](#2-textos-listos-para-pegar-en-el-backlog)
3. [Filas nuevas para el cronograma](#3-filas-nuevas-para-el-cronograma)
4. [USM propuesto (opcional)](#4-usm-propuesto-opcional)
5. [Dashboard y comparación histórica](#5-dashboard-y-comparación-histórica)
6. [Decisiones del grupo](#6-decisiones-del-grupo)
7. [Stack tecnológico](#7-stack-tecnológico)
8. [Qué es Spec Kit y cómo se usa](#8-qué-es-spec-kit-y-cómo-se-usa)
9. [Notas de la charla con la correctora](#9-notas-de-la-charla-con-la-correctora)

---

## 1. Checklist de cambios

### 📋 Backlog (pestaña Backlog-US)

- [ ] Agregar **3.3 Consultar historial del cliente** → texto en la sección 2.
- [ ] Agregar **5.5 Gestionar catálogo de tipos de estudio** → texto en la sección 2.
- [ ] Revisar la **4.1 Registrar muestra**: que la muestra se asocie a un **origen (fuente)** del cliente elegido de una lista, en vez de "lugar de extracción" como texto libre. Sin esto, la 8.1 no puede comparar.
- [ ] Eliminar la **4.2 Seleccionar estudios asociados** (decidido, ver sección 6).
- [ ] Pasar el criterio de la 4.2 "Se debe poder consultar la lista de estudios asignados desde la ficha de la muestra" a la **5.1** o a la **5.2**, para que no se pierda.

### 📅 Cronograma (pestaña Cronograma)

- [ ] Eliminar la fila **"Seleccionar estudio/s asociado/s"** (era la 4.2).
- [ ] Agregar **5.5 Catálogo** → semana 3, junto con la 5.1.
- [ ] Agregar **5.2 Consultar estado del estudio** → semana 3 (existía en el backlog pero no en el cronograma).
- [ ] Agregar **8.1 Comparación histórica** → semana 5.
- [ ] Agregar **8.2 Notificar desvíos** → semana 5 o 6.
- [ ] Agregar **3.3 Historial del cliente** → semana 6 (es lo primero a recortar si falta tiempo).
- [ ] Asignar responsables a las filas nuevas.
- [ ] Revisar la carga de la semana 6, que también es el buffer.

### 🗺️ USM (opcional)

- [ ] Agregar la actividad **"Gestionar estudio"** entre "Registrar muestra" y "Realizar pruebas" (hoy falta todo el bloque 5.1–5.4).
- [ ] Agregar las actividades **"Gestionar catálogo"** y **"Consultar historial del cliente"**.
- [ ] Mover **"Identificar origen"** y **"Detectar desvío"** después de "Realizar pruebas" (no se puede comparar un resultado que todavía no existe).
- [ ] Quitar la tarea **"Seleccionar estudio/s asociado/s"** de "Registrar muestra" (era la 4.2).

### 📖 Glosario

- [ ] Agregar **Origen** → texto en la sección 2.

---

## 2. Textos listos para pegar en el backlog

### Nro: 3.3 · Título: Consultar historial del cliente

**Descripción:**
Como empleado del laboratorio quiero consultar el historial de muestras, estudios e informes de un cliente para conocer sus análisis anteriores y responder sus consultas.

**Criterios de Aceptación:**
- Se debe poder acceder al historial desde la ficha del cliente seleccionado.
- Se deben listar las muestras del cliente con su código (N° PI), fecha de ingreso, estudios asociados y estado de cada estudio.
- El listado debe ordenarse del más reciente al más antiguo.
- Se debe poder filtrar por rango de fechas y por estado del estudio.
- Se debe poder acceder al detalle de cada estudio y, si tiene informe generado, consultarlo.
- Si el cliente no tiene muestras registradas, el sistema debe indicarlo.

> Depende de los módulos de muestras, estudios e informes → ubicarla al final del cronograma.

---

### Nro: 5.5 · Título: Gestionar catálogo de tipos de estudio

**Descripción:**
Como responsable técnico quiero crear y editar tipos de estudio y definir sus pruebas por defecto para mantener el catálogo actualizado sin depender de un desarrollador.

**Criterios de Aceptación:**
- Se debe poder crear un tipo de estudio indicando nombre (obligatorio y único) y descripción.
- Se deben poder seleccionar, del catálogo de pruebas, las pruebas que el tipo incluye por defecto.
- No se debe permitir guardar un tipo de estudio sin al menos una prueba.
- Se debe poder editar un tipo de estudio existente: modificar su nombre, agregar o quitar pruebas.
- Los cambios deben aplicarse solo a los estudios creados después de la modificación; los estudios existentes no deben alterarse.
- No se debe poder eliminar un tipo de estudio que ya fue usado en algún estudio; en ese caso se debe poder desactivar para que no aparezca al crear estudios nuevos.

> La 5.1 "Crear estudio" necesita que existan tipos de estudio → hacer la 5.5 antes o en la misma semana, o arrancar la 5.1 con tipos precargados en la base de datos.
>
> Las **pruebas** (fórmula, unidades, límites) ya las definió el científico y se precargan en la base: esta historia solo arma tipos de estudio a partir de ellas, no crea pruebas nuevas.
>
> Con Django, el panel de administración (`/admin`) puede cubrir buena parte de esta historia casi sin código.

---

### Glosario: Origen

**Origen:** Fuente de agua de un cliente que se analiza de forma periódica (ej: un pozo, un tanque, una toma). Permite comparar los resultados de una muestra con los anteriores de la misma fuente.

---

## 3. Filas nuevas para el cronograma

| Fase | Actividad | Detalle Actividad | Responsable | Semana |
|---|---|---|---|---|
| Gestion de estudio | Gestionar catálogo | Crear y editar tipos de estudio y sus pruebas por defecto | *a definir* | 3 |
| Gestion de estudio | Consultar estado del estudio | Ver estado general y pruebas pendientes/completadas | *a definir* | 3 |
| Comparación histórica | Comparar con historial del origen | Asociar muestra a un origen, comparar con resultados anteriores | *a definir* | 5 |
| Comparación histórica | Notificar desvíos | Generar alerta ante variación relevante, marcar como revisada | *a definir* | 5 o 6 |
| Gestion de cliente | Consultar historial del cliente | Ver muestras, estudios e informes del cliente | *a definir* | 6 |

**Por qué esas semanas:**
- **5.5 en semana 3:** la 5.1 la necesita.
- **8.1 en semana 5:** necesita que ya existan resultados (semana 4).
- **8.2 y 3.3 al final:** dependen de casi todo lo anterior.

⚠️ **La semana 6 queda cargada** (7.3 + 3.3 + posiblemente 8.2, y es el buffer). Si algo se atrasa, recortar primero la **3.3**. La 8.1 y la 8.2 son el diferencial, así que no conviene recortarlas.

---

## 4. USM propuesto (opcional)

🆕 = actividad nueva · ↔️ = actividad que cambia de lugar

| # | Actividad | Tareas | US |
|---|---|---|---|
| 1 | Login/Register | Registrarse → Ingresar información de usuario → Ingresar credenciales → Confirmar registro · Iniciar sesión → Ingresar contraseña → Cerrar sesión | 1.1, 1.2 |
| 2 | 🆕 Gestionar catálogo | Crear tipo de estudio → Seleccionar pruebas por defecto → Editar tipo → Desactivar tipo | 5.5 |
| 3 | Registrar cliente | Ingresar datos personales → Ingresar datos de contacto → Confirmar registro | 2.1 |
| 4 | Editar cliente | Buscar cliente → Visualizar datos actuales → Seleccionar cliente → Modificar datos → Guardar cambios | 3.1, 3.2 |
| 5 | 🆕 Consultar historial del cliente | Seleccionar cliente → Ver muestras y estudios → Filtrar por fecha/estado → Acceder al detalle o informe | 3.3 |
| 6 | Registrar muestra | Seleccionar cliente → Seleccionar origen → Ingresar datos de la muestra → Asignar código (N° PI) → Confirmar registro | 4.1 |
| 7 | 🆕 Gestionar estudio | Seleccionar muestra → Elegir tipo de estudio → Precarga automática de pruebas → Agregar prueba → Quitar prueba → Consultar estado | 5.1–5.4 |
| 8 | Realizar pruebas | Cargar mediciones → Cálculo automático → Visualizar resultados → Modificar datos → Validar y guardar | 6.1–6.4 |
| 9 | ↔️ Identificar origen de la muestra | Consultar historial del origen → Seleccionar prueba comparable → Comparar resultado actual → Visualizar tendencia y variación | 8.1 |
| 10 | ↔️ Detectar desvío relevante | Generar notificación → Visualizar detalle → Acceder al historial comparado → Marcar como revisada | 8.2 |
| 11 | Generar informes | Seleccionar estudio → Visualizar pruebas pendientes → Generar informe → Previsualizar → Exportar | 7.1–7.3 |

**USM vs Backlog:** el backlog es una **lista** para repartir y seguir el trabajo. El USM es un **mapa** del recorrido del usuario, y sirve para ver el producto entero, encontrar huecos (como la gestión de estudios, que faltaba) y cortar entregas (MVP). En SDD también ayuda a decidir qué historias van juntas en una misma spec.

---

## 5. Dashboard y comparación histórica

**Origen de la feature:** la profesora (Pilar) planteó que el programa no llegaba a cumplir los requisitos de la materia. Después de hablar con alguien que trabaja en un laboratorio real, el grupo propuso la comparación histórica + dashboard como diferencial.

**La idea:** identificar que una muestra corresponde al mismo **origen** (ej: la misma fuente que se analiza cada 3 meses) y comparar el resultado nuevo contra el historial de esa fuente. Ejemplo del contacto: *si el arsénico de una fuente siempre da 60 y de golpe da 10, es una observación.*

**Lo que ya está definido:**
- Feature "Dashboard de comparación histórica" (de las mejor puntuadas en la matriz).
- US 8.1 (comparar con el historial del origen) y US 8.2 (notificar desvíos).
- La variación se **indica**, pero el sistema **no valida ni rechaza** el resultado automáticamente.
- "Las reglas de comparación quedan para la spec técnica" (tercera presentación).
- La comparación es **solo para el laboratorio**: el cliente no la ve (decidido, ver sección 6).

**Lo que falta definir (necesario para la spec):**
1. **Qué es un origen** → propuesta en el glosario (sección 2). Tiene que elegirse de una lista; si es texto libre, "Pozo 1" y "pozo 1" quedan como dos orígenes distintos.
2. **Qué es una "variación relevante"** → ¿porcentaje contra el resultado anterior? ¿Contra el promedio de los últimos N? Ojo: según el ejemplo, una **baja** también cuenta, no solo una suba. Si el contacto del laboratorio puede dar un criterio, mejor.
3. **Qué resultados se comparan** → ¿solo los validados? ¿Misma prueba y misma unidad? ¿Cuántos hacia atrás?

⚠️ **Impacto en el Sprint 2:** si el origen se elige de una lista, eso cambia la **4.1 Registrar muestra** (semana 2). Hay que definir qué es un origen **antes** de hacer la spec de la 4.1.

**Nota:** "dashboard" suele entenderse como un panel general de estadísticas, y esto es una vista de comparación para una muestra. La necesidad de Roberto (dueño) de ver *cuántos estudios se hacen y cuánto tardan los informes* no la cubre ninguna feature. Es solo para que lo sepan, no hace falta agregarla.

---

## 6. Decisiones del grupo

| # | Decisión | Respuesta | Estado |
|---|---|---|---|
| 1 | **Stack tecnológico** | Python + Django 5.2 LTS, PostgreSQL, Docker Compose y Render (ver sección 7) | ✅ Decidido |
| 2 | **4.2 vs 5.1** (las dos asocian un estudio a una muestra) | Borrar la 4.2. Su criterio "ver estudios desde la ficha de la muestra" pasa a la 5.1 o a la 5.2 | ✅ Decidido |
| 3 | **¿Quién define las pruebas?** (fórmula, unidades, límites) | Las pruebas ya están definidas por el científico: se precargan en la base y la 5.5 solo arma tipos de estudio con ellas | ✅ Decidido |
| 4 | **¿El cliente ve la evolución de su fuente?** | Por ahora queda afuera (coincide con "No Es": no es una app para clientes) | ✅ Decidido |
| 5 | **Regla de "variación relevante"** | — Se define en la spec de la 8.2. Idealmente, validarla con el contacto del laboratorio | ⏳ Pendiente |

> Las personas de los artefactos son ficticias: las dudas de requisitos se consultan con la **profesora** o con el **contacto del laboratorio real**.

---

## 7. Stack tecnológico

| Herramienta | Para qué |
|---|---|
| **Python + Django 5.2 LTS** | Ya trae login, roles, ORM, migraciones y formularios |
| **PostgreSQL** | Una sola base, corriendo en Docker |
| **Docker Compose** | Dos contenedores: la app y la base |
| **Templates de Django + Bootstrap** | Interfaz |
| **pytest-django + ruff** | Pruebas y formato |
| **Git, GitHub y GitHub Actions** | Repo, pull requests y tests automáticos |
| **Claude Code + Spec Kit** | Flujo de specs |
| **Jira** | Sprints, como ya usan |

**Más adelante, solo cuando toque:**

| Herramienta | Cuándo | Para qué |
|---|---|---|
| **WeasyPrint** | Semana 5 | Informes en PDF |
| **Chart.js** | Semana 5 | Comparación histórica |
| **Render** | Semana 5 | Tener la app online |

### Notas

1. **Fijar la versión de Python** (recomendado: **3.12**) en el `Dockerfile` y en la constitution, para que la IA no use otra.
2. **Fijar la versión de Bootstrap** (5.3) por el mismo motivo.
3. **WeasyPrint necesita librerías del sistema** (Pango, entre otras) dentro de la imagen de Docker. En la semana 5 hay que tocar el `Dockerfile`, no solo `requirements.txt`. Contar con que ese día puede haber algún problema de instalación.
4. **Render (plan gratis):**
   - **App:** gratis, soporta Docker (usa el mismo `Dockerfile`). Se duerme tras **15 min** sin uso y tarda **~1 min** en despertar → abrirla un rato antes de una demo.
   - **Base PostgreSQL:** gratis (1 GB), pero **vence a los 30 días de creada**; después hay 14 días de gracia y se **borra con todos los datos**.
   - **Plan:** crear la base de Render recién en la **semana 5**, así dura hasta después de la entrega. Hasta entonces, todos desarrollan local con Docker Compose.
   - **Alternativa** si quieren la app online desde antes: app en Render + base en **Neon** (PostgreSQL gratis sin vencimiento).
5. **Render no usa Docker Compose:** la base es un servicio aparte y la app se conecta por una variable de entorno (`DATABASE_URL`). No cambia nada para desarrollar, solo el día del deploy.
6. **Jira y Spec Kit no se conectan.** Spec Kit puede convertir tareas en issues de GitHub, no en tickets de Jira. Propuesta: en Jira, las US del sprint; en el repo, el detalle (`tasks.md`).
7. **El panel de administración de Django** cubre casi gratis la 5.5 (catálogo) y sirve para precargar las pruebas definidas por el científico.

---

## 8. Qué es Spec Kit y cómo se usa

**SDD (Spec-Driven Development):** primero se escribe *qué* hay que hacer, el equipo lo revisa, y recién ahí la IA programa a partir de ese texto. La spec pasa a ser la referencia de todo. Ataca directamente el riesgo *"Specs y código con IA inconsistentes"*.

**Spec Kit** ordena ese proceso en pasos. Cada paso es un comando en el agente de IA y genera un archivo en el repo (quedan en `specs/`, así que se entregan junto con el código).

| Comando | Qué genera | Quién decide |
|---|---|---|
| `constitution` | Reglas del proyecto: stack, tests, convenciones. **Se hace una sola vez** | El equipo |
| `specify` | La spec: qué hace la feature y por qué. Sin nada técnico | El equipo, con la IA redactando |
| `clarify` | Preguntas sobre lo que quedó ambiguo | El equipo responde |
| `plan` | Diseño técnico: modelos, vistas, URLs, templates | La IA propone, el equipo revisa |
| `tasks` | Lista de tareas en orden | La IA, a partir del plan |
| `implement` | El código | La IA, siguiendo las tareas |

> En la versión actual los comandos aparecen como skills: `/speckit-constitution` o `/speckit.constitution` (escribir `/speckit` en Claude Code para verlos).

**Regla de oro:** revisar cada archivo antes de pasar al siguiente paso. Si la spec está mal, el código va a estar mal aunque compile.

**Cómo encaja con el proyecto:** un ciclo `specify → plan → tasks → implement` por actividad o grupo de historias. El primero sería el **Sprint 1** (1.1, 1.2, 2.1).

---

## 9. Notas de la charla con Pilar

### Lo que dijo

**Planificación**
- Se planea **sprint a sprint** (de demo a demo).
- **Respetar los límites de cada sprint** (tiempos).
- Hacer una **UI mínima para el Sprint 1** → hay que definir la UI.

**Infraestructura**
- Definir arquitectura y tecnología: repo, lenguaje, Docker, etc.
- **Invitar a Pilar al repo.**

**SDD**
- Iniciar SDD **desde el repo**.
- Cada spec tiene requisitos **funcionales** y **técnicos** (pueden ir separados o juntos).
- **No hacer todas las specs de una vez:** se elige una spec y se hace el ciclo SDD completo.
- Granularidad posible:
  - 1 US → 1 spec
  - N US → 1 spec
  - 1 US → N issues → cada issue, 1 spec
- **Una cosa por vez por persona**, para evitar bloqueos (*deadlocks*) entre issues de distintas personas.

**Jira**
- Respetar las columnas de la pestaña **"Sprint n"** (TODO / DOING / TEST / DONE) para que **todo sea migrable a Jira**.

### Qué implica para nosotros

| Nota | Qué hacer |
|---|---|
| Funcional y técnico separables | Spec Kit ya los separa: `spec.md` = funcional (qué), `plan.md` = técnico (cómo) |
| Granularidad | **Por defecto, 1 US = 1 spec**: coincide con el cronograma (1 responsable por actividad), cada uno trabaja en su rama y la trazabilidad US → spec es directa. Agrupar solo si dos US son muy chicas y las hace la misma persona |
| Una spec por vez, sprint a sprint | Correr `specify` solo para las US del sprint actual, no para todo el backlog |
| Evitar bloqueos | Spec Kit crea **una rama por spec**. Además, lo **compartido** (proyecto Django, Docker, modelo de usuario, layout base) va en una tarea de infraestructura **antes** de las US del Sprint 1, así nadie espera a nadie |
| Infraestructura | Agregar al cronograma una tarea de **setup al inicio de la semana 1**: repo, Docker Compose, proyecto Django vacío, CI, layout base con Bootstrap. No está en ningún artefacto |
| Invitar a Pilar | GitHub → repo → *Settings → Collaborators → Add people* |
| UI mínima | Definir en la constitution las reglas de UI (Bootstrap 5.3, layout base con barra de navegación, textos en español) y armar el layout base en la tarea de setup |
| Columnas de Jira | Usar los mismos estados en Jira. Propuesta de mapeo: **TODO** = US del sprint sin empezar · **DOING** = `specify` → `implement` · **TEST** = PR abierto + revisión de pares + tests en verde · **DONE** = PR mergeado |

### Columnas de Jira

Mapeo propuesto entre las columnas de "Sprint n" y el flujo de Spec Kit:

- **TODO:** la US está en el sprint y nadie la empezó.
- **DOING:** de `specify` a `implement`.
- **TEST:** PR abierto, con revisión de un compañero y tests en verde.
- **DONE:** PR mergeado.

### Checklist

- [ ] Invitar a Pilar al repo de GitHub.
- [ ] Agregar al cronograma la tarea de **setup de infraestructura** (semana 1, antes de las US).
- [ ] Definir la granularidad de las specs (recomendado: 1 US = 1 spec).
- [ ] Definir la UI mínima del Sprint 1 (va en la constitution + layout base).
- [ ] Configurar Jira con las columnas TODO / DOING / TEST / DONE.

---

## Próximo paso

1. ✅ Stack definido.
2. Armar la **constitution** con Spec Kit (incluyendo reglas de UI y de trabajo por spec).
3. Tarea de **setup de infraestructura** (proyecto Django + Docker + CI + layout base).
4. En paralelo, actualizar la planilla con el checklist de la sección 1.
5. Arrancar el ciclo `specify → plan → tasks → implement` con el **Sprint 1**, una spec por persona.
