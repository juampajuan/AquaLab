# AquaLab

Aplicación web para laboratorios de análisis de agua: clientes, muestras, estudios, pruebas,
resultados e informes, con comparación histórica de resultados por origen.

Proyecto del Grupo 7 — Gestión del Desarrollo de Sistemas Informáticos (FIUBA). Las reglas del
proyecto están en la [constitution](.specify/memory/constitution.md).

## Stack

Python 3.12 · Django 5.2 LTS · PostgreSQL 16 · Docker Compose · Tailwind CSS 4 · WeasyPrint (PDF) ·
pytest-django · ruff

## Requisitos

- [Docker](https://docs.docker.com/get-docker/) con Docker Compose.
- Git.

No hace falta instalar Python, PostgreSQL ni las librerías de WeasyPrint (Pango) en la máquina:
todo corre dentro de los contenedores.

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


## Datos de demo

Para mostrar o probar la app con datos realistas (seis meses de muestras, estudios en todos los
estados, informes emitidos, resultados fuera de norma y un desvío en el historial):

1. Tener `AQUALAB_ENTORNO=desarrollo` y `DEBUG=True` en el `.env` (están en `.env.example`; si tu
   `.env` es anterior, agregá la primera línea a mano).
2. Cargar la demo (si el catálogo de pruebas está vacío, lo importa):

   ```bash
   docker compose exec web python manage.py cargar_demo
   ```

3. Entrar con `tecnico@demo.aqualab` o `bioquimico@demo.aqualab`, contraseña `Demo-1234`. El
   bioquímico es Bioquímico y Administrador, y ya tiene firma.

**No hace falta borrar la base**: la demo se suma a los datos que ya tengas, sin modificarlos (la
numeración de muestras e informes sigue desde la última). Después de traer los cambios alcanza con
`git pull`, agregar la línea al `.env`, `docker compose up -d`, `migrate` y `cargar_demo`.

El comando solo corre en desarrollo y no carga dos veces: si la demo ya está, avisa y no hace nada.
Solo si querés una base limpia, solo con la demo, recreala (esto **borra todos tus datos locales**):
`docker compose down -v`, `docker compose up -d`, `migrate` y `cargar_demo`.


## Asistente de consultas (US 10.1)

El botón «Asistente» (abajo a la derecha, con sesión) responde preguntas sobre muestras, estudios
y clientes con datos de AquaLab; no cambia nada. Usa Groq (plan gratuito) por defecto:

1. Crear una clave gratuita en https://console.groq.com.
2. Ponerla en el `.env`: `ASISTENTE_API_KEY=...` (opcionales: `ASISTENTE_URL` y
   `ASISTENTE_MODELO`, ver `.env.example`).
3. Reiniciar: `docker compose up -d web`.

**Sin la clave, AquaLab funciona igual**: el botón aparece deshabilitado con el aviso «El
asistente no está configurado». Los tests nunca llaman a Groq: simulan el servicio.
Al servicio externo no se mandan el correo, el teléfono, el domicilio ni el documento de los
clientes.

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

## Deploy en Render

`render.yaml` (Blueprint) define el servicio web, con el mismo `Dockerfile`, y la base
PostgreSQL 16, ambos en el plan gratis. Para crearlos:

1. En Render: **New → Blueprint**, elegir este repositorio y la rama `main`.
2. Completar las variables que pide: el correo, la contraseña, el nombre y el apellido del
   superusuario inicial (`DJANGO_SUPERUSER_*`) y, si se quiere el asistente, `ASISTENTE_API_KEY`.
   `SECRET_KEY` la genera Render; `DATABASE_URL`, el dominio y la URL pública también los da Render.
3. **Apply**. Cada push a `main` vuelve a desplegar.

En cada arranque, `scripts/iniciar_produccion.sh` corre las migraciones, importa el catálogo de
pruebas solo si la base está vacía, crea el superusuario si no existe (en Administradores y
Bioquímicos) y levanta gunicorn. Repetirlo no cambia nada.

- `AQUALAB_ENTORNO=produccion` activa HTTPS, cookies seguras y HSTS; no admite `DEBUG=True`.
- Los estáticos los sirve WhiteNoise desde `staticfiles/`, que el `Dockerfile` arma con
  `collectstatic`.
- Sin `EMAIL_BACKEND`, los correos quedan en los logs del servicio. Para enviarlos de verdad, se
  agregan las variables de correo en **Environment** (ver `.env.example`).
- El servicio se duerme a los 15 minutos sin uso y tarda cerca de un minuto en despertar: abrirlo
  un rato antes de una demo.
- La base gratis vence a los 30 días de creada; 14 días después se borra con todos los datos.
- `cargar_demo` no corre en producción.

Para probar la imagen de producción en local (con la base de Compose levantada):

```bash
docker build -t aqualab-prod .
docker run --rm --network aqualab_default -p 8010:8000 -e SECRET_KEY=local \
  -e AQUALAB_ENTORNO=produccion -e ALLOWED_HOSTS=localhost \
  -e DATABASE_URL=postgres://aqualab:aqualab@db:5432/aqualab aqualab-prod
```

Con `AQUALAB_ENTORNO=produccion`, todo pedido por HTTP redirige a HTTPS: para navegarla en local,
sacar esa variable y agregar `DEBUG=False`.

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
