# AquaLab

Aplicación web para laboratorios de análisis de agua: clientes, muestras, estudios, pruebas,
resultados e informes, con comparación histórica de resultados por origen.

Proyecto del Grupo 7 — Gestión del Desarrollo de Sistemas Informáticos (FIUBA). Las reglas del
proyecto están en la [constitution](.specify/memory/constitution.md).

## Stack

Python 3.12 · Django 5.2 LTS · PostgreSQL 16 · Docker Compose · Tailwind CSS 4 · pytest-django · ruff

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

Después de traer cambios de `main`: `docker compose up -d --build` si cambió el `Dockerfile` o
`requirements.txt`, y `docker compose exec web python manage.py migrate` si hay migraciones nuevas.


## Inicio y cierre de sesión

Las cuentas nuevas se registran en `/usuarios/registro/` y quedan pendientes de aprobación.
Solo una cuenta aprobada puede ingresar con correo y contraseña. El correo usa la misma
normalización del registro; la contraseña se evalúa exactamente como fue ingresada.


## Estilos (Tailwind)

La interfaz usa **Tailwind CSS 4** con el diseño hecho en Stitch (`specs/013-diseno-ui/stitch/`).
No hace falta Node: el `Dockerfile` instala el ejecutable de Tailwind dentro del contenedor.

- `static/src/aqualab.css`: tema (colores, tipografía, sombras) y componentes (`btn`, `tarjeta`,
  `tabla`, `etiqueta`, `aviso`, `form-control`, etc.).
- `static/css/aqualab.css`: CSS compilado. **Se commitea**; el CI falla si no está al día.
- `templates/ui/`: parciales reutilizables (menú, campo de formulario, resumen, estado, íconos…).
  Las pantallas nuevas se arman con estos parciales en lugar de escribir el HTML desde cero.

Después de cambiar clases en un template o en `static/src/aqualab.css`, recompilar y commitear el
resultado (con `-u` el archivo queda a nombre de tu usuario y no de root):

```bash
docker compose exec -u "$(id -u):$(id -g)" web tailwindcss -i static/src/aqualab.css -o static/css/aqualab.css --minify
```

Mientras se trabaja en templates conviene dejarlo recompilando solo, con `--watch` en lugar de
`--minify` (antes de commitear, compilar una vez con `--minify`).

Los formularios (`forms.py`) siguen asignando las clases `form-control`, `form-select` e
`is-invalid` a los campos: son nombres heredados de Bootstrap que el CSS nuevo define, así que no
hay que cambiarlos.

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

El CI (GitHub Actions) corre `ruff check`, `ruff format --check`, verifica que las migraciones y
el CSS compilado estén al día y corre `pytest` contra PostgreSQL 16 en cada PR. No se mergea con el
CI en rojo.

## Estructura

```text
config/        settings, urls, panel de inicio y filtros de templates compartidos
usuarios/      usuarios (modelo Usuario con email como login), registro, sesión y avisos por correo
clientes/      clientes: alta, búsqueda, ficha y edición
muestras/      muestras y orígenes
pruebas/       catálogo de pruebas
estudios/      tipos de estudio y estudios sobre muestras
templates/     base.html, base_acceso.html y parciales de interfaz (templates/ui/)
static/        CSS (fuente y compilado), fuentes, imágenes y JS compartidos
specs/         specs de cada user story (Spec Kit)
```

Hay una app de Django por módulo del dominio (ver la constitution): las US de un mismo módulo
(por ejemplo, 3.1 y 3.2) se implementan en la misma app. Toda referencia al usuario se hace con
`settings.AUTH_USER_MODEL`, nunca con el `User` de Django.
