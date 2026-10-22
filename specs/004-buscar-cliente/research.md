# Research: Buscar cliente registrado

**Feature**: `004-buscar-cliente` | **Plan**: [plan.md](./plan.md)

## R1 — Búsqueda sin distinguir tildes

- **Decision**: usar el lookup `unaccent` de PostgreSQL combinado con `icontains`
  (`nombre__unaccent__icontains`, `razon_social__unaccent__icontains`). Requiere agregar
  `django.contrib.postgres` a `INSTALLED_APPS` y una migración `UnaccentExtension()` en `clientes`.
- **Rationale**: FR-003 exige ignorar mayúsculas **y tildes**; `icontains` solo cubre mayúsculas.
  `unaccent` es parte de Django y de PostgreSQL 16 (contrib incluido en la imagen oficial), así que
  no suma dependencias. El usuario de la base (`POSTGRES_USER`) es superusuario en Docker y en CI,
  por lo que `CREATE EXTENSION` funciona; pytest-django la aplica al crear la base de tests.
- **Alternatives**: (a) `icontains` puro — incumple FR-003; (b) normalizar en Python y filtrar en
  memoria — no escala y duplica lógica; (c) columna auxiliar normalizada — agrega estado y migración
  de datos sin necesidad para cientos de clientes. Riesgo a vigilar: un entorno de deploy sin
  permisos para crear extensiones (Render, semana 5); se resuelve habilitándola una vez.

## R2 — Un solo campo y filtro por documento

- **Decision**: campo único `q`. Se calcula `q_doc = normalizar_numero_documento(q)` (función ya
  existente en `clientes.models`). Si `q_doc` es no vacío y solo dígitos, se agrega
  `Q(numero_documento__contains=q_doc)` al OR; si no, solo se filtra por nombre/razón social.
- **Rationale**: `numero_documento` se guarda normalizado (US 2.1), así que comparar con el texto
  normalizado cumple FR-004 y la búsqueda parcial por dígitos. Exigir solo dígitos evita que un
  texto como `"ab"` produzca falsos filtros, y no obliga a elegir tipo de documento (Assumptions).
- **Alternatives**: campo de tipo de búsqueda (select) — más fricción, la spec lo descarta; filtrar
  por `tipo_documento` — la spec indica que no se exige.

## R3 — Solo clientes activos

- **Decision**: `Cliente.objects.filter(activo=True)` siempre. En `detalle`, si el cliente existe
  pero está inactivo se muestra un mensaje "El cliente no está disponible." y se redirige a la
  búsqueda; si no existe sigue el 404 de US 2.1.
- **Rationale**: lo pide el planteo del plan y el edge case de la spec (cliente desactivado entre
  búsqueda y selección). Hoy no hay baja, así que no cambia el comportamiento actual en la práctica.
- **Alternatives**: listar inactivos marcados como tales (Assumptions lo permite) — descartado por
  el requisito explícito de listar solo activos; YAGNI.

## R4 — Validación, método y paginación

- **Decision**: `BuscarClienteForm(forms.Form)` con `q = CharField(min_length=2, strip=True)`,
  instanciado con `request.GET`. Sin `q` en la URL → formulario vacío sin resultados ni error. Con
  `q` inválido (vacío/1 carácter) → error junto al campo y sin resultados. Resultados con
  `Paginator(queryset, 20)` y el orden de `Cliente.Meta.ordering` (`razon_social, nombre, id`),
  consistente gracias al `id` como desempate.
- **Rationale**: validaciones en el `Form` (Principio IV), GET idempotente y enlazable; reutiliza el
  orden del modelo. Los enlaces de paginación conservan `q`.
- **Alternatives**: POST — no es idempotente y rompe "volver atrás"; paginar con JS — contradice
  Principio II.

## R5 — Identificación del cliente seleccionado

- **Decision**: la selección es el enlace a `clientes:detalle` con el `pk`; la ficha ya muestra todos
  los datos vigentes leídos de la base en cada consulta (FR-009, FR-010). Otros flujos reutilizarán
  `pk` (o `clientes:detalle`) en iteraciones futuras.
- **Rationale**: `pk` es inequívoco (FR-011) y no requiere código extra; la integración queda fuera
  de alcance (FR-013).
- **Alternatives**: guardar la selección en sesión — estado innecesario hoy (YAGNI).
