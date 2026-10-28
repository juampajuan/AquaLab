# Research: Consultar estado del estudio

**Feature**: `009-consultar-estado-estudio` | **Plan**: [plan.md](./plan.md)

## R1 — Estados generales del estudio y estados individuales de cada prueba

- **Decision**:
  1. Completar `EstadoEstudio(models.TextChoices)` en `estudios/models.py` con los cuatro estados del ciclo de vida del estudio definidos en el dominio:
     - `PENDIENTE_ANALISIS = "pendiente_analisis", "Pendiente de análisis"` (valor por defecto al crear el estudio en US 5.1)
     - `EN_PROCESO = "en_proceso", "En proceso"`
     - `FINALIZADO = "finalizado", "Finalizado"`
     - `INFORME_GENERADO = "informe_generado", "Informe generado"`
  2. Agregar `EstadoPruebaEstudio(models.TextChoices)` y el campo `estado` en `PruebaEstudio` (`CharField(max_length=20, choices=EstadoPruebaEstudio.choices, default=EstadoPruebaEstudio.PENDIENTE, editable=False)`):
     - `PENDIENTE = "pendiente", "Pendiente"` (valor por defecto cuando se asignan las pruebas al estudio)
     - `CARGADA = "cargada", "Cargada"`
     - `COMPLETADA = "completada", "Completada"`
  3. Generar la migración `estudios/migrations/0003_estados_estudio_y_prueba.py`.
- **Rationale**: US 5.1 definió únicamente el estado inicial de `Estudio` y dejó sin campo `estado` a `PruebaEstudio` para que US 5.2 estableciera la representación del estado general del estudio y del estado individual de sus pruebas asignadas (FR-009, FR-010, FR-011). Con `default="pendiente"` en `PruebaEstudio.estado`, `bulk_create` en `crear_estudio()` asigna automáticamente `Pendiente` a todas las pruebas sin alterar el flujo de US 5.1.
- **Alternatives**: calcular el estado de la prueba en memoria a partir de mediciones futuras — hoy no existen las columnas de medición/validación (pertenecen al Epic 6), por lo que un campo `estado` explícito con `TextChoices` permite consultar y probar todos los estados desde ahora y será actualizado por las historias del Epic 6 y 7.

## R2 — Búsqueda unificada por identificador, muestra o cliente

- **Decision**: formulario GET `BuscarEstudioForm(forms.Form)` con un único campo `q`.
  - Si `q` (tras `strip()`) es vacío → error `"Ingresá un identificador de estudio, N° PI, muestra o cliente para buscar."`
  - Si `q` no es exclusivamente numérico (`not q.isdigit()`) y tiene menos de 2 caracteres → error `"Ingresá al menos 2 caracteres para buscar."` (en cambio, un número entero de 1 dígito como `"1"` es válido porque busca el estudio con `pk=1`, FR-005).
  - La consulta sobre `Estudio.objects.select_related("muestra", "muestra__cliente", "muestra__origen")` combina con `OR`:
    1. `Q(muestra__nombre__unaccent__icontains=q)`
    2. `Q(muestra__cliente__nombre__unaccent__icontains=q)`
    3. `Q(muestra__cliente__razon_social__unaccent__icontains=q)`
    4. Si `q.isdigit()`: `Q(pk=int(q)) | Q(muestra__numero_pi=int(q))`
    5. Si `q_doc = normalizar_numero_documento(q)` es no vacío y solo dígitos: `Q(muestra__cliente__numero_documento__contains=q_doc)`
- **Rationale**: reutiliza la extensión `unaccent` ya instalada en `clientes/migrations/0002_unaccent.py` y `normalizar_numero_documento` de `clientes.models` (US 3.1). Permite encontrar estudios por su ID numérico, por el N° PI o nombre de su muestra, y por el nombre, razón social o DNI/CUIT (con o sin formato) del cliente desde un solo campo (FR-002 a FR-005). Incluye estudios de clientes inactivos (FR-014 de US 5.1 y edge case de US 5.2).
- **Alternatives**: múltiples campos de filtro separados — mayor fricción para el usuario y descartado en `spec.md`; `numero_pi__icontains` como texto — comparar `numero_pi` como entero cuando `q.isdigit()` es exacto e indexado.

## R3 — Orden, paginación y snapshots históricos del tipo de estudio

- **Decision**: ordenar los resultados por `-pk` (`Estudio._meta.ordering`), paginar de a 20 con `Paginator(queryset, 20)` y mostrar siempre `estudio.tipo_nombre_snapshot` y `estudio.tipo_descripcion_snapshot` en lugar de `estudio.tipo.nombre` / `estudio.tipo.descripcion`.
- **Rationale**: cumple el contrato de inmutabilidad histórica de US 5.1 (si el tipo se renombra o edita en US 5.5, los estudios creados conservan el nombre y descripción vigentes cuando se crearon) y garantiza un orden determinista del más reciente al más antiguo (FR-006, FR-007, FR-009).
- **Alternatives**: leer `estudio.tipo.nombre` en vivo — rompería el snapshot histórico definido en US 5.1.

## R4 — Vista de detalle del estudio y resumen de avance de pruebas

- **Decision**: ruta `GET /estudios/<int:pk>/` (`estudios:detalle`). Obtiene el estudio con `get_object_or_404(Estudio.objects.select_related("muestra", "muestra__cliente", "muestra__origen", "creado_por"), pk=pk)` y sus pruebas asignadas con `estudio.pruebas_asignadas.select_related("prueba").order_by("prueba__codigo", "pk")`. Calcula el total de pruebas asignadas, cuántas están en estado `Completada`, cuántas en `Cargada` y cuántas en `Pendiente`.
- **Rationale**: resuelve la cabecera y la lista de pruebas en 2 consultas SQL sin problema N+1 y expone tanto el estado individual de cada prueba como el resumen de avance (FR-009, FR-010).
- **Alternatives**: sin `select_related` — generaría consultas adicionales por fila.

## R5 — Ficha de la muestra con lista de estudios asignados

- **Decision**: ruta `GET /muestras/<int:pk>/` (`muestras:detalle`) en la app `muestras`. Obtiene la muestra con `get_object_or_404(Muestra.objects.select_related("cliente", "origen", "registrada_por"), pk=pk)` y sus estudios en orden `-pk` anotando en la consulta el total de pruebas asignadas (`Count("pruebas_asignadas")`) y las pruebas completadas (`Count("pruebas_asignadas", filter=Q(pruebas_asignadas__estado=EstadoPruebaEstudio.COMPLETADA))`).
- **Rationale**: mantiene la responsabilidad de cada app (Principio II: la ficha de la muestra vive en `muestras` y enlaza a `estudios:detalle`), evita consultas N+1 al listar los estudios de una muestra y cumple el criterio 4 traído de la US 4.2 (FR-012, FR-013, FR-014).
- **Alternatives**: ubicar la ficha de la muestra dentro de `estudios` — acoplaría la URL de la entidad `Muestra` a otra app.
