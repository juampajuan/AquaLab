# Research: Registrar muestra

**Feature**: `007-registrar-muestra` | **Plan**: [plan.md](./plan.md)

## R1 — App nueva `muestras` con los modelos `Origen` y `Muestra`

- **Decision**: crear la app `muestras` (registrada en `INSTALLED_APPS` y montada en `/muestras/`)
  con dos modelos: `Origen` (FK a `clientes.Cliente`) y `Muestra` (FK a `Cliente`, `Origen` y
  `settings.AUTH_USER_MODEL`). Todas las FK con `on_delete=PROTECT`.
- **Rationale**: la constitution fija una app por módulo (`muestras` está en la lista, Principio II).
  El origen es la base de la comparación histórica por fuente de agua y pertenece a un cliente
  (FR-005); vive en `muestras` porque solo se crea y se usa al registrar muestras. `PROTECT` aplica
  el Principio IV: un cliente, origen o usuario con muestras asociadas no se puede borrar.
- **Alternatives**: `Origen` en la app `clientes` — acopla `clientes` a un concepto que solo usa
  `muestras`; guardar el origen como texto en la muestra — rompe FR-005/FR-006 (no habría lista
  reutilizable por cliente ni unicidad) y la comparación histórica.

## R2 — Asignación del N° PI sin repetidos ni huecos

- **Decision**: el N° PI se calcula al confirmar, dentro de `transaction.atomic()`:
  1. `SELECT pg_advisory_xact_lock(<clave fija de la app>)` serializa los registros concurrentes;
     el lock se libera solo al terminar la transacción (commit o rollback).
  2. `Muestra.objects.aggregate(Max("numero_pi"))` → `ultimo + 1`, o `200001` si no hay muestras.
  3. `numero_pi` tiene `unique=True` y un `CheckConstraint` `numero_pi >= 200001` como red de
     seguridad.
- **Rationale**: cumple FR-012 ("último + 1") y FR-013 (sin repetidos ante registros simultáneos).
  Como el número se calcula después del lock y dentro de la misma transacción que el `INSERT`, un
  rollback (falla al guardar) no consume un número y una cancelación nunca llega a calcularlo
  (SC-005). El proyecto ya depende de PostgreSQL (`django.contrib.postgres`, `unaccent`), así que el
  advisory lock no agrega dependencias.
- **Alternatives**:
  - Secuencia de PostgreSQL / `AutoField` con inicio en 200001 — los valores consumidos por una
    transacción que hace rollback se pierden y dejan huecos, contradiciendo "último + 1".
  - `select_for_update()` sobre la última muestra — no bloquea nada cuando la tabla está vacía (la
    primera muestra queda expuesta a la carrera).
  - Reintentar ante `IntegrityError` sin lock — funciona, pero el lock es más simple de razonar y
    de testear.
  - `LOCK TABLE` — bloquea también lecturas de otras pantallas futuras; el advisory lock solo
    serializa a quienes registran.

## R3 — Selección del cliente con lista filtrable (Clarificación Q2)

- **Decision**: el campo `cliente` es un `<select>` con todos los clientes activos (ordenados como
  `Cliente.Meta.ordering`), precedido por un campo de texto "Buscar cliente". Un script propio y
  chico (`muestras/static/muestras/registro_muestra.js`, sin librerías) oculta las opciones que no
  coinciden con lo escrito. La coincidencia ignora mayúsculas, tildes y separadores del documento,
  igual que `clientes.views.buscar_clientes` (US 3.1). Los datos a mostrar del cliente (razón social o
  nombre, tipo y número de documento, correo) y sus orígenes van en la página con `json_script`.
- **Rationale**: cumple la clarificación Q2 y FR-002/FR-003 sin dependencias nuevas (Principio II) y
  sin pantallas extra. Un laboratorio maneja cientos (no cientos de miles) de clientes: incluirlos en
  la página es liviano. Cuando el formulario se renderiza con un cliente ya elegido (POST con errores o `?volver=1`), el
  servidor muestra la ficha de ese cliente y las opciones de `origen` de ese cliente; el script solo
  los actualiza al cambiar de cliente en vivo. Sin JavaScript se puede elegir el cliente y dar de
  alta un origen nuevo; para elegir un origen existente hay que enviar una vez el formulario (el
  error de origen recarga la página con los orígenes del cliente). La validación real queda en el
  servidor (Principio IV).
- **Alternatives**:
  - `<datalist>` — el filtrado y la presentación dependen del navegador y el valor enviado es el
    texto visible, no el `pk`.
  - Endpoint JSON de búsqueda por cada tecla — más vistas, más tests y latencia, sin beneficio a
    esta escala.
  - Librería de autocompletado (Select2, Tom Select) — dependencia nueva no justificada.

## R4 — Origen existente u origen nuevo en el mismo formulario

- **Decision**: el formulario tiene dos campos: `origen` (`ModelChoiceField`, opcional, cuyo
  queryset se limita a los orígenes del cliente enviado) y `origen_nuevo` (texto, opcional). Debe
  completarse exactamente uno:
  - ninguno → error en `origen`: "Elegí un origen del cliente o ingresá uno nuevo.";
  - ambos → error en `origen_nuevo`: "Elegí un origen existente o ingresá uno nuevo, no ambos.";
  - `origen` de otro cliente → error de opción inválida (no está en el queryset).
  En la interfaz, un enlace "Dar de alta un origen nuevo" muestra el campo de texto y vacía la
  selección. Si el nombre nuevo coincide (sin distinguir mayúsculas ni espacios laterales) con un
  origen existente del cliente, se reutiliza ese origen (FR-006). El resumen indica si el origen es
  nuevo.
- **Rationale**: una regla simple y testeable en el servidor; el origen nuevo se crea recién al
  confirmar, junto con la muestra (FR-018), así que cancelar no deja orígenes huérfanos.
- **Alternatives**: opción especial "nuevo" dentro del `<select>` — mezcla un valor que no es un
  `pk` con un `ModelChoiceField`; pantalla aparte para dar de alta el origen — contradice el
  criterio de aceptación 2 ("desde el mismo formulario").

## R5 — Flujo de dos pasos con borrador en sesión (como clientes)

- **Decision**: mismo patrón que `clientes:registrar` / `registrar_confirmar`:
  - `GET/POST /muestras/registrar/` (`muestras:registrar`): formulario. Válido → guarda en
    `session["muestra_pendiente"]` los datos normalizados (pks como enteros, fechas en ISO) y
    redirige a `muestras:registrar_confirmar`.
  - `GET /muestras/registrar/confirmar/`: resumen con [Confirmar] [Volver y editar] [Cancelar].
  - `POST accion=confirmar`: revalida (cliente activo, origen del cliente), registra con
    `registrar_muestra(datos, usuario)` y redirige a `muestras:registrar` (formulario vacío) con el
    mensaje "Muestra registrada con N° PI 200001." (Clarificación Q5).
  - Doble confirmación: tras guardar se borra el borrador y se guarda
    `session["ultima_muestra_pi"]`; un segundo POST sin borrador no vuelve a escribir y repite el
    mensaje informativo.
  - `GET /muestras/registrar/` sin `?volver=1` descarta el borrador; con `?volver=1` lo precarga.
- **Rationale**: cumple la confirmación con resumen (FR-017, sección Interfaz de la constitution) con
  un patrón que el equipo ya conoce y testea. El `volver=1` es el mismo mecanismo de US 3.2: evita
  que, tras registrar una muestra, el formulario reaparezca con datos viejos.
- **Alternatives**: modal de confirmación en el navegador — la confirmación quedaría solo en el
  template; campos ocultos en la confirmación — obliga a revalidar todo y duplica lógica.

## R6 — Valores por defecto y validaciones de fechas

- **Decision**: `fecha_muestreo` y `fecha_ingreso` usan `initial=timezone.localdate` (fecha del
  laboratorio, `America/Argentina/Buenos_Aires`); `tipo_vertido` usa `initial="agua"`. En
  `clean()`: ninguna fecha posterior a `timezone.localdate()`, y `fecha_muestreo <= fecha_ingreso`
  (además, `CheckConstraint` en el modelo). El nombre vacío se normaliza a `"Muestra 1"`
  (Clarificación Q1) en el formulario, así el resumen ya muestra el valor que se guardará; el
  modelo también lo usa como `default`.
- **Rationale**: FR-008, FR-009, FR-010 y FR-011. La comparación "posterior a hoy" depende del día,
  por eso vive en el formulario y no en la base. Usar la fecha local evita que después de las 21 h
  (UTC-3) "hoy" sea el día siguiente.
- **Alternatives**: `datetime.date.today()` — usa la zona del servidor/contenedor, no la del
  laboratorio.

## R7 — Usuario, fecha de registro y estado automáticos

- **Decision**: `registrada_por` = `request.user` y `fecha_registro` con `auto_now_add=True`; ambos
  `editable=False`, no forman parte del formulario. `estado` es un `TextChoices` con un único valor
  por ahora, `INGRESADA = "ingresada", "Ingresada"`, como `default`.
- **Rationale**: FR-014 y FR-015. No se agregan otros estados ni un campo `activa` hasta que una
  historia los pida (YAGNI); los cambios de estado y la desactivación están fuera de alcance
  (FR-020).
- **Alternatives**: `BooleanField activa` ya en esta historia — sin uso ni tests que lo justifiquen.

## R8 — Acceso a la pantalla

- **Decision**: enlace "Registrar muestra" en la barra de navegación de `templates/base.html` y
  botón en `templates/inicio.html`, junto a los de clientes. Las vistas quedan protegidas por el
  `LoginRequiredMiddleware` existente (FR-001).
- **Rationale**: resuelve el único punto marcado como "Outstanding" en la clarificación, con el
  mismo patrón usado para "Registrar cliente".
