# Quickstart: Buscar cliente registrado

**Feature**: `004-buscar-cliente` | Contrato: [contracts/busqueda-cliente-ui.md](./contracts/busqueda-cliente-ui.md) | Datos: [data-model.md](./data-model.md)

## Prerrequisitos

```bash
cp .env.example .env            # si aún no existe
docker compose up -d --build
docker compose exec web python manage.py migrate   # aplica 0002_unaccent
```

Crear un empleado activo (`createsuperuser` o admin) y algunos clientes desde `/clientes/registrar/`:
una persona (`Juan Pérez`, DNI `30.123.456`), una empresa (`Aguas del Sur S.A.`, CUIT
`20-12345678-6`) y dos clientes con el mismo nombre y distinto documento.

## Validación manual

1. Iniciar sesión y abrir `/clientes/buscar/` → formulario vacío, sin resultados.
2. Buscar `perez` (sin tilde, minúsculas) → aparece `Juan Pérez` (escenarios 1 y 7).
3. Buscar `aguas` → aparece la empresa por razón social (escenario 2).
4. Buscar `30123456`, `30.123.456` y `123` → aparece el cliente por documento (escenario 3 y parcial).
5. Verificar columnas nombre/razón social, documento y correo; los homónimos se distinguen por
   documento (escenarios 4, US2-2).
6. Clic en **Ver ficha** → `/clientes/<id>/` con todos los datos (escenario 5, US2-1).
7. Buscar `zzzz` → mensaje "No se encontraron clientes…" (escenario 6).
8. Buscar vacío o `a` → error junto al campo, sin listar clientes (edge cases).
9. Cerrar sesión y abrir `/clientes/buscar/` → redirige al login.
10. (Con >20 clientes) verificar paginación conservando `q`.

## Tests automatizados

```bash
docker compose exec web pytest clientes/tests/test_busqueda.py
docker compose exec web pytest && docker compose exec web ruff check . && docker compose exec web ruff format --check .
```

Cobertura esperada en `test_busqueda.py`: un test por escenario de aceptación (US1 1–7, US2 1–2),
más: solo activos, vacío/1 carácter, orden y paginación, sin sesión → login, detalle de cliente
inactivo → redirección con mensaje.
