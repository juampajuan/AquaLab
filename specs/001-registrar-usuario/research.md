# Research: Registrar usuario

**Feature**: `001-registrar-usuario` | **Fecha**: 2026-10-18 | **Plan**: [plan.md](./plan.md)

Decisiones técnicas tomadas para resolver el **cómo** de la spec. Cada una indica qué se eligió,
por qué y qué alternativas se descartaron.

---

## R1. Modelo de usuario personalizado

- **Decisión**: modelo `Usuario` en la app `usuarios`, que hereda de `AbstractUser`, elimina el
  campo `username` (`username = None`) y usa `email` como `USERNAME_FIELD`.
  `REQUIRED_FIELDS = ["first_name", "last_name"]`. Se configura `AUTH_USER_MODEL = "usuarios.Usuario"`.
  Manager propio `UsuarioManager` (hereda de `BaseUserManager`) con `create_user` y
  `create_superuser` que reciben `email` en lugar de `username`.
- **Por qué**: FR-003 exige el correo como único identificador. `AbstractUser` conserva todo lo que
  usa el admin y el sistema de autenticación (`is_active`, `is_staff`, permisos, `date_joined`), así
  que solo se cambia lo mínimo. Django recomienda definir el modelo de usuario propio **antes de la
  primera migración**: cambiar `AUTH_USER_MODEL` después obliga a rehacer la base.
- **Alternativas descartadas**:
  - `User` de Django + perfil 1:1: el login seguiría siendo por `username`; habría que duplicar el
    correo en `username` y mantenerlos sincronizados.
  - `AbstractBaseUser` + `PermissionsMixin`: más código propio (campos, admin, formularios) sin
    beneficio para esta feature (principio II).
  - Backend de autenticación por email sobre el `User` estándar: no resuelve la unicidad del correo
    ni la eliminación de `username`.

## R2. Unicidad del correo sin distinguir mayúsculas ni espacios

- **Decisión**: tres capas, cada una con su función:
  1. **Normalización**: el correo se guarda siempre como `email.strip().lower()`. Lo hacen el
     formulario de registro (`clean_email`), el manager (`create_user`/`create_superuser`) y
     `Usuario.clean()` (que usa el admin).
  2. **Validación en el formulario**: `clean_email` rechaza si existe
     `Usuario.objects.filter(email__iexact=...)` con el mensaje "Este correo no está disponible."
  3. **Garantía en la base**: `email` con `unique=True` (requisito de Django para `USERNAME_FIELD`,
     check `auth.E003`) **y** `UniqueConstraint(Lower("email"), name="usuario_email_unico_ci")`.
- **Por qué**: FR-005 y el edge case de duplicados (incluidas cuentas pendientes, que también
  existen en la tabla). El constraint funcional cubre altas que no pasen por el formulario (admin,
  shell, carreras entre requests). El principio IV pide que la regla viva en modelo/formulario, no
  solo en el template.
- **Alternativas descartadas**:
  - Campo `CIText` de PostgreSQL: requiere la extensión `citext` y una migración extra; además
    `django.contrib.postgres` ata los tests a PostgreSQL.
  - Collation no determinística: más compleja de configurar y de entender para el equipo.
  - Solo `unique=True`: no detecta `Ana@x.com` vs `ana@x.com` si alguien saltea la normalización.

## R3. Cuenta "pendiente de aprobación" = cuenta inactiva

- **Decisión**: el estado se representa con el campo estándar `is_active`:
  `is_active=False` → "pendiente de aprobación"; `is_active=True` → "aprobada". El registro crea la
  cuenta con `is_active=False`. No se agrega un campo `estado`.
- **Por qué**: lo pide el input del plan y es lo idiomático (principio II). `ModelBackend` ya
  rechaza usuarios inactivos (`user_can_authenticate`), así que FR-012 / SC-004 se cumplen sin
  código propio. El admin ya sabe filtrar y editar `is_active`.
- **Consecuencia para la US 1.2 (`002-inicio-cierre-sesion`)**: para mostrar "Tu cuenta está
  pendiente de aprobación" solo cuando la contraseña es correcta, esa feature tendrá que distinguir
  "credenciales correctas pero inactiva" de "credenciales incorrectas" (por ejemplo con
  `AuthenticationForm.confirm_login_allowed` + `AllowAllUsersModelBackend`). Es decisión del plan de
  la 002; esta feature solo garantiza que **pendiente ⇔ `is_active=False`**.
- **Limitación conocida**: como el rechazo y la desactivación de cuentas quedan fuera de alcance
  (FR-015), hoy toda cuenta inactiva es una cuenta pendiente. Si una spec futura agrega "rechazada"
  o "desactivada", habrá que introducir un campo de estado.
- **Alternativas descartadas**: campo `estado` con choices (`PENDIENTE`/`APROBADA`): duplicaría
  `is_active` y obligaría a un backend de autenticación propio. YAGNI.

## R4. Aprobación desde el admin de Django

- **Decisión**: `UsuarioAdmin` (hereda de `django.contrib.auth.admin.UserAdmin`, adaptado a email
  sin `username`) con:
  - `list_display`: email, nombre, apellido, estado (`is_active` con etiqueta "Aprobada"),
    fecha de registro.
  - `list_filter`: `is_active` (para ver las pendientes), `is_staff`.
  - Acción masiva **"Aprobar cuentas seleccionadas"** que hace `is_active=True` y avisa cuántas se
    aprobaron.
  - Además, el checkbox `is_active` en la ficha del usuario sigue funcionando.
  - El label de `is_active` se muestra como "Aprobada" para que el administrador entienda el
    concepto del dominio.
- **Por qué**: la spec (Assumptions) define que la aprobación se hace con la herramienta de
  administración; FR-013. La acción masiva evita entrar ficha por ficha y es testeable.
- **Quién es administrador**: un usuario con `is_staff=True` y permiso `usuarios.change_usuario`
  (en la práctica, el superusuario creado con `createsuperuser` en el setup). No es un rol del
  dominio (spec, Assumptions).
- **Alternativas descartadas**: pantalla propia de aprobación (fuera de alcance del Sprint 1 según
  la spec).

## R5. Paso de revisión y confirmación antes de guardar

- **Decisión**: flujo de dos pasos con los datos validados guardados en la **sesión de Django**:
  1. `GET/POST /usuarios/registro/` — formulario. Si es válido, se guarda en
     `request.session["registro_pendiente"]` un dict con `first_name`, `last_name`, `email`
     (normalizados) y `password` **ya hasheada** con `make_password()`. Redirige (PRG) a la
     confirmación. No se crea nada en la base.
  2. `GET /usuarios/registro/confirmar/` — resumen (nombre, apellido, correo; nunca la contraseña)
     con tres acciones: **Confirmar** (POST), **Volver y editar** (GET al formulario con los datos
     precargados) y **Cancelar** (POST que borra los datos de la sesión).
  3. `POST /usuarios/registro/confirmar/` — revalida que el correo siga disponible, crea el
     `Usuario` con `is_active=False` dentro de `transaction.atomic()`, quita los datos de la sesión y
     redirige a `/usuarios/registro/recibido/` con un mensaje de éxito.
- **Por qué**: FR-008/FR-009 piden una revisión explícita y poder volver o cancelar sin crear la
  cuenta. La sesión ya existe (Django la trae), no agrega dependencias y la contraseña nunca viaja de
  vuelta al navegador ni queda en texto plano en el servidor (FR-014, principio V).
- **Alternativas descartadas**:
  - `django-formtools` (`FormPreview`/`FormWizard`): dependencia nueva para un flujo de dos
    pantallas (principio II).
  - Reenviar los datos en campos ocultos del HTML de revisión: la contraseña quedaría en el código
    fuente de la página (viola FR-014).
  - Crear la cuenta en el paso 1 y "confirmarla" en el 2: deja cuentas a medio crear y complica
    FR-009/SC-003.
  - Modal de JavaScript: la confirmación no quedaría del lado del servidor y no sería testeable con
    el test client.

## R6. Contraseña en el formulario y al volver a editar

- **Decisión**:
  - El formulario de registro hereda de `django.contrib.auth.forms.BaseUserCreationForm`, que ya
    trae **contraseña + repetir contraseña** y aplica `AUTH_PASSWORD_VALIDATORS`.
  - Se mantienen los validadores por defecto de `startproject` (similitud con datos del usuario,
    longitud mínima 8, contraseñas comunes, no solo numérica). Con `LANGUAGE_CODE="es-ar"` los
    mensajes salen en español.
  - Al volver desde la revisión o al corregir un error, nombre, apellido y correo se conservan
    (FR-007), pero **la contraseña se vuelve a pedir**: `PasswordInput` no re-renderiza su valor y
    en la sesión solo está el hash.
- **Por qué**: como el resumen no puede mostrar la contraseña (FR-014), el campo de repetición es la
  única forma de que la persona detecte un error de tipeo antes de confirmar. Es el comportamiento
  estándar del formulario de Django, no un dato nuevo del dominio. No reenviar la contraseña al
  navegador prioriza FR-014 sobre FR-007 únicamente para el secreto.
- **Alternativas descartadas**: un solo campo de contraseña (error de tipeo indetectable hasta el
  login); conservar la contraseña al volver (habría que reenviarla en el HTML).
- **Confirmado por el equipo**: el campo "Repetir contraseña", reingresar la contraseña al editar y
  los validadores de contraseña por defecto de Django.

## R7. Confirmación repetida (idempotencia, FR-010)

- **Decisión**:
  - **Caso secuencial** (doble clic, recarga después del éxito): la confirmación quita
    `registro_pendiente` de la sesión al crear la cuenta; un segundo POST no encuentra datos y
    redirige a `/usuarios/registro/recibido/` sin crear nada.
  - **Caso concurrente** (dos POST simultáneos, o el correo tomado por otra persona entre la
    revisión y la confirmación): el segundo `INSERT` falla con `IntegrityError` por el constraint
    de R2 → no se crea una segunda cuenta y se redirige al formulario con "Este correo no está
    disponible.".
  - Además, el botón "Confirmar" se deshabilita al enviar (una línea de JavaScript en el template;
    es solo una ayuda, la garantía está en el servidor).
- **Por qué**: FR-010 y el edge case de reintentos; la garantía final la da la base, no el cliente.
- **Decisión del equipo**: se descartó tratar como éxito el caso concurrente de la misma solicitud
  (comparando el hash de la contraseña). Es un caso muy improbable y agregaba código y tests sin
  valor para el usuario (principio II). FR-010 se cumple igual: nunca se crea más de una cuenta.
- **Alternativas descartadas**: token de un solo uso en la base (tabla nueva sin necesidad);
  `select_for_update` sobre la sesión (acopla la lógica al backend de sesiones); comparar el hash
  de la contraseña para distinguir la misma solicitud (complejidad innecesaria).

## R8. Mensajes de resultado (FR-011)

- **Decisión**: framework de mensajes de Django.
  - Éxito: redirección a `/usuarios/registro/recibido/`, que muestra "Registro recibido. Vas a
    poder ingresar cuando un administrador apruebe tu cuenta."
  - Falla de base de datos (`DatabaseError` distinto del caso de R7): se vuelve a mostrar la
    revisión con "No se pudo completar el registro. Intentá nuevamente." y la cuenta no se presenta
    como creada.
- **Por qué**: lo pide la constitution (sección Interfaz) y el edge case "si el alta no puede
  completarse".

## R9. Acceso público a las vistas de registro

- **Decisión**: en el setup se activa `django.contrib.auth.middleware.LoginRequiredMiddleware`
  (Django 5.1+), que exige sesión en **todas** las vistas por defecto. Las vistas de registro se
  marcan con `@login_not_required`.
- **Por qué**: principio V ("todas las vistas requieren sesión, salvo login y registro") y FR-001.
  Con el middleware, olvidarse un decorador deja una vista protegida en vez de expuesta.
- **Alternativas descartadas**: `@login_required` vista por vista (fácil de olvidar en las features
  siguientes).

## R10. Tests

- **Decisión**: pytest-django con el test client de Django y la base PostgreSQL del
  `docker compose`. Un test por escenario de aceptación (principio III), más tests de modelo
  (normalización, constraint) y de admin (acción de aprobar). Fixtures en `usuarios/tests/conftest.py`.
- **Por qué**: principio III; el test client cubre todo el flujo server-side sin navegador.
- **Alternativas descartadas**: tests end-to-end con navegador (Playwright/Selenium): dependencia
  nueva y no hay JavaScript relevante que probar.
