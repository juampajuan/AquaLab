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
6. [Decisiones pendientes del grupo](#6-decisiones-pendientes-del-grupo)
7. [Stack tecnológico (NO definido)](#7-stack-tecnológico-no-definido)
8. [Qué es Spec Kit y cómo se usa](#8-qué-es-spec-kit-y-cómo-se-usa)
9. [Instalación en WSL](#9-instalación-en-wsl)

---

## 1. Checklist de cambios

### 📋 Backlog (pestaña Backlog-US)

- [ ] Agregar **3.3 Consultar historial del cliente** → texto en la sección 2.
- [ ] Agregar **5.5 Gestionar catálogo de tipos de estudio** → texto en la sección 2.
- [ ] Revisar la **4.1 Registrar muestra**: que la muestra se asocie a un **origen (fuente)** del cliente elegido de una lista, en vez de "lugar de extracción" como texto libre. Sin esto, la 8.1 no puede comparar.
- [ ] Decidir qué hacer con la **4.2 Seleccionar estudios asociados** (ver sección 6). Puede quedar pendiente para el paso `clarify` de Spec Kit.
- [ ] Si se elimina la 4.2: pasar su criterio "ver la lista de estudios desde la ficha de la muestra" a la 5.1 o a la 5.2.

### 📅 Cronograma (pestaña Cronograma)

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
| 6 | Registrar muestra | Seleccionar cliente → Ingresar datos de la muestra → Asignar código (N° PI) → Confirmar registro → *Seleccionar estudio/s* ⚠️ | 4.1, 4.2 |
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

**Lo que falta definir (necesario para la spec):**
1. **Qué es un origen** → propuesta en el glosario (sección 2). Tiene que elegirse de una lista; si es texto libre, "Pozo 1" y "pozo 1" quedan como dos orígenes distintos.
2. **Qué es una "variación relevante"** → ¿porcentaje contra el resultado anterior? ¿Contra el promedio de los últimos N? Ojo: según el ejemplo, una **baja** también cuenta, no solo una suba. Si el contacto del laboratorio puede dar un criterio, mejor.
3. **Qué resultados se comparan** → ¿solo los validados? ¿Misma prueba y misma unidad? ¿Cuántos hacia atrás?

⚠️ **Impacto en el Sprint 2:** si el origen se elige de una lista, eso cambia la **4.1 Registrar muestra** (semana 2). Hay que definir qué es un origen **antes** de hacer la spec de la 4.1.

**Nota:** "dashboard" suele entenderse como un panel general de estadísticas, y esto es una vista de comparación para una muestra. La necesidad de Roberto (dueño) de ver *cuántos estudios se hacen y cuánto tardan los informes* no la cubre ninguna feature. Es solo para que lo sepan, no hace falta agregarla.

---

## 6. Decisiones pendientes del grupo

| # | Decisión | Opciones / Recomendación | ¿Bloquea la constitution? |
|---|---|---|---|
| 1 | **Stack tecnológico** | Ver sección 7 | **Sí** |
| 2 | **4.2 vs 5.1** | Las dos asocian un estudio a una muestra. Según las Personas, la 4.2 podría ser el paso de Diego (recepción anota el estudio pedido) y la 5.1 el de Lucía (arma el estudio con sus pruebas). Opciones: **A)** eliminar la 4.2, **B)** que al registrar la muestra se elija el tipo y eso cree el estudio. Consultarlo con la profesora o dejarlo para `clarify` | No |
| 3 | **¿Quién define las pruebas?** | Cada prueba tiene fórmula, unidades y límites. Recomendación: precargarlas en la base de datos y que la 5.5 solo arme tipos de estudio con esas pruebas. Aclararlo en "No Hace" o en la spec | No |
| 4 | **¿El cliente ve la evolución de su fuente?** | El mail lo menciona, pero "No Es" dice que no es una app para clientes. Recomendación: dejarlo afuera, o incluir un **gráfico del historial en el PDF del informe** sin que el cliente entre al sistema | No |
| 5 | **Regla de "variación relevante"** | Se define en la spec de la 8.2. Idealmente, validarla con el contacto del laboratorio | No |


---

## 8. Qué es Spec Kit y cómo se usa

**SDD (Spec-Driven Development):** primero se escribe *qué* hay que hacer, el equipo lo revisa, y recién ahí la IA programa a partir de ese texto. La spec pasa a ser la referencia de todo. Ataca directamente el riesgo *"Specs y código con IA inconsistentes"*.

**Spec Kit** ordena ese proceso en pasos. Cada paso es un comando en el agente de IA y genera un archivo en el repo (quedan en `specs/`, así que se entregan junto con el código).

| Comando | Qué genera | Quién decide |
|---|---|---|
| `constitution` | Reglas del proyecto: stack, tests, convenciones. **Se hace una sola vez** | El equipo |
| `specify` | La spec: qué hace la feature y por qué. Sin nada técnico | El equipo, con la IA redactando |
| `clarify` | Preguntas sobre lo que quedó ambiguo | El equipo responde |
| `plan` | Diseño técnico: entidades, endpoints, pantallas | La IA propone, el equipo revisa |
| `tasks` | Lista de tareas en orden | La IA, a partir del plan |
| `implement` | El código | La IA, siguiendo las tareas |

> En la versión actual los comandos aparecen como skills: `/speckit-constitution` o `/speckit.constitution` (escribir `/speckit` en Claude Code para verlos).

**Regla de oro:** revisar cada archivo antes de pasar al siguiente paso. Si la spec está mal, el código va a estar mal aunque compile.

**Cómo encaja con el proyecto:** un ciclo `specify → plan → tasks → implement` por actividad o grupo de historias. El primero sería el **Sprint 1** (1.1, 1.2, 2.1).



## Próximo paso

1. El grupo elige el **stack** (sección 7).
2. Se arma la **constitution** con Spec Kit.
3. En paralelo, se actualiza la planilla con el checklist de la sección 1.
4. Arranca el ciclo `specify → plan → tasks → implement` con el **Sprint 1**.
