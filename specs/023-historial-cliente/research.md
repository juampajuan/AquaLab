# Research: Consultar historial del cliente

**Feature**: `023-historial-cliente` | **Plan**: [plan.md](./plan.md)

## R1. Dónde vive el historial

- **Decision**: App `clientes`: vista `clientes.views.historial`, URL `clientes:historial`
  (`/clientes/<pk>/historial/`), template `clientes/historial.html`; la consulta en
  `clientes/historial.py`.
- **Rationale**: La US 3.3 es del módulo Clientes y se entra desde la ficha (FR-001); la URL anidada
  en el cliente deja claro de quién es el historial. Separar la consulta de la vista permite
  probarla sin HTTP (como `estudios/busqueda.py`).
- **Alternatives considered**: Sección dentro de la ficha (la ficha crece y mezcla datos del
  cliente con un listado paginado y filtrable); vista en `estudios` o `muestras` (la unidad es el
  cliente, no un estudio ni una muestra).

## R2. Unidad del listado y paginación

- **Decision**: Se paginan **muestras** (`Paginator`, 20 por página, igual que
  `RESULTADOS_POR_PAGINA`) y los estudios de cada muestra se traen con
  `Prefetch("estudios", queryset=..., to_attr="estudios_historial")`.
- **Rationale**: Paginar muestras garantiza que los estudios de una muestra quedan juntos (FR-012)
  y que una muestra sin estudios aparece (US1 Esc. 4). El `Prefetch` hace una sola consulta de
  estudios por página, sin N+1 (SC-004).
- **Alternatives considered**: Paginar estudios con `select_related("muestra")` (corta una muestra
  entre páginas y pierde las muestras sin estudios); agrupar en Python todo el historial (no escala
  y rompe la paginación).

## R3. Orden

- **Decision**: Muestras por `-fecha_ingreso, -numero_pi`; estudios por `-pk` (el número del
  estudio es su `pk` y el orden de `Estudio.Meta`).
- **Rationale**: El criterio dice «del más reciente al más antiguo» y la fecha visible es la de
  ingreso; el N° PI desempata de forma estable porque es correlativo (US 4.1).
- **Alternatives considered**: `fecha_registro` (no se muestra y puede diferir de la de ingreso si
  se registra tarde); solo `-numero_pi` (una muestra ingresada antes pero registrada después
  quedaría fuera de orden respecto de la fecha mostrada).

## R4. Filtros

- **Decision**: `HistorialClienteForm` (GET) con `desde` y `hasta` (`DateField`, opcionales,
  formatos `%Y-%m-%d` y `%d/%m/%Y`, widget `SelectorFecha` de `muestras/forms.py`) y `estado`
  (`ChoiceField` con «Todos» + `EstadoEstudio.choices`). `clean()` rechaza `desde > hasta` con el
  error en `desde`. Con el formulario inválido no se filtra (se muestra el historial completo con
  los errores). Fechas: `fecha_ingreso__gte` / `__lte` (inclusivos). Estado: las muestras con
  `estudios__estado=estado` (`.distinct()`) y el mismo filtro en el `Prefetch`.
- **Rationale**: Mismo patrón que la búsqueda de informes de la US 7.3 (`BuscarInformeForm`), lo
  que mantiene mensajes y formatos coherentes. Aplicar el estado a muestras y al prefetch cumple
  FR-007 (la muestra aparece una vez, solo con los estudios coincidentes).
- **Alternatives considered**: Filtrar estudios en el template (paginaría muestras que después
  quedan vacías); `Exists()` en lugar de `distinct()` (equivalente; `distinct()` alcanza y es más
  legible con el orden por columnas de la muestra).

## R5. Informe del estudio

- **Decision**: El `Prefetch` de estudios usa `select_related("informe")` (OneToOne inverso de la
  US 7.2). En el template, `{% if estudio.informe %}` → «Ver informe
  {{ estudio.informe.numero_mostrado }}» → `informes:ver estudio.pk`. Se decide por la existencia
  del `Informe` ya traído, no por el estado.
- **Rationale**: Sin consultas extra por estudio y reutiliza la vista del informe emitido, que lo
  muestra desde su copia (FR-011, principio IV). Con `select_related`, la ausencia de informe queda
  en caché: el template la resuelve como falsa (`RelatedObjectDoesNotExist` es una falla silenciosa
  de variable) sin consultar. El estado «Informe generado» y el `Informe` los crea juntos
  `emitir_informe`, pero decidir por el `Informe` evita un enlace a un 404 si alguna vez no
  coinciden.
- **Alternatives considered**: `hasattr(estudio, "informe")` en el template (lanza
  `RelatedObjectDoesNotExist` sin `select_related` y genera una consulta por estudio); enlazar al
  listado de informes de la US 7.3 (todavía en otra rama y obliga a buscar de nuevo).

## R6. Mensajes vacíos

- **Decision**: Si `cliente.muestras.exists()` es falso → `ui/estado_vacio` «Este cliente no tiene
  muestras registradas.». Si hay muestras pero la página filtrada está vacía → «Ninguna muestra
  coincide con los filtros.» con «Limpiar filtros» (URL del historial sin parámetros).
- **Rationale**: FR-009 pide distinguir los dos casos; `exists()` es una consulta barata y solo se
  necesita cuando el resultado viene vacío.
- **Alternatives considered**: Un único mensaje genérico (no cumple FR-009).

## R7. Cliente inactivo y acceso

- **Decision**: Igual que `clientes.views.detalle`: `get_object_or_404(Cliente, pk=pk)`; si
  `activo` es falso, `messages.warning(MENSAJE_NO_DISPONIBLE)` y redirect a `clientes:buscar`. La
  vista acepta solo GET (`@require_GET`).
- **Rationale**: FR-002 pide el mismo comportamiento que la ficha; `require_GET` hace explícito que
  es de solo lectura (FR-013).
- **Alternatives considered**: Mostrar el historial de clientes inactivos (la ficha no está
  disponible, sería un acceso lateral inconsistente con la US 3.2).
