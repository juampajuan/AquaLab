# AquaLab

Aplicación web para laboratorios de análisis de agua: clientes, muestras, estudios, pruebas,
resultados e informes, con comparación histórica de resultados por origen.

Proyecto del Grupo 7 — Gestión del Desarrollo de Sistemas Informáticos (FIUBA). Las reglas del
proyecto están en la [constitution](.specify/memory/constitution.md).

## Stack

Python 3.12 · Django 5.2 LTS · PostgreSQL 16 · Docker Compose · Bootstrap 5.3 · pytest-django · ruff

## Requisitos

- [Docker](https://docs.docker.com/get-docker/) con Docker Compose.
- Git.

No hace falta instalar Python ni PostgreSQL en la máquina: todo corre dentro de los contenedores.

## Levantar el proyecto desde cero

1. Clonar el repo y entrar a la carpeta:

   ```bash
   git clone <url-del-repo> AquaLab
   cd AquaLab
   ```

2. Crear el archivo `.env` a partir del ejemplo (`.env` **no** se sube al repo):

   ```bash
   cp .env.example .env
   ```

   Cambiar `SECRET_KEY` por una propia. Se puede generar con:

   ```bash
   python3 -c "import secrets; print(secrets.token_urlsafe(50))"
   ```

3. Construir y levantar los contenedores (`web` y `db`):

   ```bash
   docker compose up -d --build
   ```

4. Aplicar las migraciones:

   ```bash
   docker compose exec web python manage.py migrate
   ```

5. Crear el primer administrador (pide correo, nombre, apellido y contraseña). Es quien aprueba
   las cuentas nuevas desde el admin:

   ```bash
   docker compose exec web python manage.py createsuperuser
   ```

6. Abrir <http://localhost:8000>. Sin sesión, redirige a
   <http://localhost:8000/usuarios/login/>. El administrador aprueba cuentas desde
   <http://localhost:8000/admin/>.

Para ver los logs: `docker compose logs -f web`. Para apagar: `docker compose down`
(agregar `-v` borra también la base de datos).


## Inicio y cierre de sesión

Las cuentas nuevas se registran en `/usuarios/registro/` y quedan pendientes de aprobación.
Solo una cuenta aprobada puede ingresar con correo y contraseña. El correo usa la misma
normalización del registro; la contraseña se evalúa exactamente como fue ingresada.


## Tests y formato

Correr los tests (pytest crea y borra una base de test aparte):

```bash
docker compose exec web pytest
```

Lint y formato con ruff:

```bash
docker compose exec web ruff check .
docker compose exec web ruff format --check .
```

Para corregir automáticamente: `ruff check --fix .` y `ruff format .`.

El CI (GitHub Actions) corre `ruff check`, `ruff format --check` y `pytest` contra PostgreSQL 16
en cada PR. No se mergea con el CI en rojo.

## Estructura

```text
config/        settings, urls y wsgi/asgi del proyecto
usuarios/      app de usuarios (modelo Usuario con email como login)
templates/     base.html y templates compartidos
specs/         specs de cada user story (Spec Kit)
```

Cada feature crea su propia app de Django (`clientes`, `muestras`, ...). Toda referencia al
usuario se hace con `settings.AUTH_USER_MODEL`, nunca con el `User` de Django.
