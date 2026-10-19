# Research: Registrar cliente

**Feature**: `003-registrar-cliente` | **Fecha**: 2026-10-19 | **Plan**: [plan.md](./plan.md)

Decisiones técnicas tomadas para resolver el **cómo** de la spec de la US 2.1 (SCRUM-43). Cada una
indica qué se eligió, por qué y qué alternativas se descartaron.

---

## R1. Nueva app `clientes` y modelo `Cliente`

- **Decisión**: crear la app de Django `clientes` con el modelo `Cliente` (nombres del dominio en
  español según el Principio VI y el Glosario). Además de los datos identificatorios y de contacto,
  el modelo incluye `activo = models.BooleanField("activo", default=True)` y
  `fecha_alta = models.DateTimeField("fecha de alta", auto_now_add=True)`.
- **Por qué**:
  - El Principio II de la constitution establece *"Una app de Django por módulo: `usuarios`,
    `clientes`, `muestras`, `estudios`, `pruebas`, `informes`, `comparacion`"*.
  - El Principio IV exige *"NO se borran registros con historial asociado (clientes, muestras, tipos
    de estudio usados): se desactivan"*, y FR-014 pide que el cliente creado quede disponible de
    inmediato para asociarse a nuevas muestras (`activo=True`). Incluir `activo` desde la migración
    inicial evita alterar la tabla cuando se conecte con la US 4.1.
- **Alternativas descartadas**:
  - Ubicar `Cliente` dentro de la app `usuarios`: viola el Principio II y mezcla conceptos distintos
    (los clientes del laboratorio no son usuarios del sistema).
  - Omitir el campo `activo` en esta iteración: obligaría a una migración extra en las historias
    siguientes para cumplir el Principio IV.

## R2. Identificación por nombre personal y/o razón social (FR-002, FR-003)

- **Decisión**: definir dos campos de texto separados en `Cliente`:
  - `nombre = models.CharField("nombre", max_length=200, blank=True)`
  - `razon_social = models.CharField("razón social", max_length=200, blank=True)`
  Ambos se normalizan quitando espacios laterales (`strip()`). La regla *"al menos uno entre nombre
  personal y razón social es obligatorio"* (FR-003 y primer caso borde) se aplica en tres niveles:
  1. En `RegistroClienteForm.clean()`.
  2. En `Cliente.clean()`.
  3. En la base de datos mediante un `CheckConstraint`:
     `CheckConstraint(condition=~Q(nombre="", razon_social=""), name="cliente_nombre_o_razon_social_obligatorio")`.
- **Por qué**: FR-002, FR-003 y el caso borde *"Una empresa puede tener razón social sin nombre
  personal y una persona puede tener nombre sin razón social; al menos uno de los dos valores es
  obligatorio"*. Tener ambos campos separados permite registrar personas físicas (solo `nombre`),
  empresas (solo `razon_social`) o empresas que además informan el nombre del titular, y facilita la
  búsqueda y edición en las US 3.1 y 3.2.
- **Alternativas descartadas**:
  - Un único campo `nombre_o_razon_social`: impide distinguir si el dato corresponde a un nombre
    personal o a una razón social y no permite cargar ambos cuando existen.
  - Selector "Persona / Empresa" con JavaScript para mostrar u ocultar campos: suma complejidad en el
    cliente sin que la spec lo pida (Principio II, YAGNI).

## R3. Normalización y validación de DNI y CUIT (FR-004, FR-016)

- **Decisión**:
  - `tipo_documento`: `CharField(max_length=4, choices=TipoDocumento.choices)` usando `models.TextChoices`
    con los únicos dos valores del alcance: `DNI = "DNI", "DNI"` y `CUIT = "CUIT", "CUIT"`.
  - **Normalización**: antes de validar formato y unicidad, se eliminan espacios laterales e
    internos, puntos (`.`) y guiones (`-`) mediante `re.sub(r"[\s.\-]", "", valor)`. En la base se
    guarda únicamente el número normalizado (solo dígitos).
  - **Validación según el tipo (FR-016)**:
    - Si tras quitar espacios, puntos y guiones el valor no contiene únicamente dígitos ASCII
      (`not valor.isdigit()`), se rechaza.
    - **DNI**: debe tener exactamente **7 u 8 dígitos** (`len(valor) in (7, 8)`). En caso contrario,
      error en `numero_documento`: `"El DNI debe tener 7 u 8 dígitos numéricos."`.
    - **CUIT**: debe tener exactamente **11 dígitos** y dígito verificador válido según el algoritmo
      módulo 11 estándar (pesos `[5, 4, 3, 2, 7, 6, 5, 4, 3, 2]` sobre los primeros 10 dígitos;
      `resto = suma % 11`; `verificador = 0` si `resto == 0`, `9` si `resto == 1`, o `11 - resto` en
      otro caso, comparando con el undécimo dígito). Si no tiene 11 dígitos o el dígito verificador
      no coincide, error en `numero_documento`:
      `"El CUIT debe tener 11 dígitos y un dígito verificador válido."`.
- **Por qué**: FR-004, FR-016, Escenario 8 y el segundo caso borde (*"Un documento que solo difiere
  por espacios, puntos o guiones se considera el mismo identificador; el formato se valida sobre el
  número sin esos separadores"*). El cálculo del dígito verificador del CUIT ocupa ~10 líneas de
  Python estándar, sin agregar dependencias (Principio II).
- **Alternativas descartadas**:
  - Agregar una librería externa como `python-stdnum`: requiere justificar una dependencia nueva para
    una validación elemental (Principio II).
  - Guardar el documento con separadores formateados (`20-12345678-6`): complica las consultas de
    unicidad y comparación directa en la base.

## R4. Unicidad por tipo y número de documento (FR-007, SC-003)

- **Decisión**: tres capas (mismo patrón que R2 de `001-registrar-usuario`):
  1. **Normalización**: `normalizar_numero_documento()` deja solo los dígitos en el formulario y en
     `Cliente.clean()`.
  2. **Validación en formulario y modelo**: una vez normalizado el documento, se verifica si ya
     existe `Cliente.objects.filter(tipo_documento=tipo, numero_documento=numero)` y se informa el
     error `"Ya existe un cliente registrado con este tipo y número de documento."`.
  3. **Garantía en la base de datos**:
     `UniqueConstraint(fields=["tipo_documento", "numero_documento"], name="cliente_documento_unico", violation_error_message="Ya existe un cliente registrado con este tipo y número de documento.")`.
- **Por qué**: FR-007, Escenario 4 y Principio IV. Así, si existe el CUIT `20123456786` y alguien
  intenta cargar `20-12345678-6` o ` 20.123.456.786 `, la normalización previa produce el mismo par
  `("CUIT", "20123456786")` y tanto el formulario como el constraint de PostgreSQL impiden el
  duplicado.
- **Alternativas descartadas**:
  - Validar unicidad únicamente en el formulario sin `UniqueConstraint`: no protege ante solicitudes
    concurrentes ni cargas desde el admin o shell.

## R5. Datos de contacto: correo electrónico, teléfono y domicilio (FR-005, FR-006)

- **Decisión**:
  - `email`: `EmailField("correo electrónico", max_length=254)` obligatorio. Se normaliza con
    `strip().lower()`. Su formato lo valida el `EmailValidator` estándar de Django. No tiene
    restricción de unicidad porque la spec define la unicidad del cliente exclusivamente por tipo y
    número de documento (FR-007).
  - `telefono`: `CharField("teléfono", max_length=30, blank=True)` opcional (`strip()`). Cuando se
    informa un valor no vacío, `validar_telefono` comprueba que solo contenga dígitos, espacios,
    signo `+`, guiones `-` y paréntesis `()`, y que posea entre **7 y 15 dígitos numéricos**. Si no
    cumple, devuelve `"Ingresá un número de teléfono válido (entre 7 y 15 dígitos)."`.
  - `domicilio`: `CharField("domicilio", max_length=255, blank=True)` opcional (`strip()`).
- **Por qué**: FR-005, FR-006, Escenario 5 y el cuarto caso borde (*"El correo electrónico es
  obligatorio y su formato debe ser válido. Si se informa teléfono, su formato debe ser válido; dejar
  vacíos el teléfono o el domicilio no impide el alta"*).
- **Alternativas descartadas**:
  - `django-phonenumber-field` / `phonenumbers`: dependencia nueva innecesaria (Principio II) y
    demasiado rígida para teléfonos locales sin prefijo internacional.

## R6. Paso de revisión y confirmación en sesión (FR-010, FR-011)

- **Decisión**: flujo en dos pasos renderizado en el servidor guardando los datos validados en
  `request.session["cliente_pendiente"]` (mismo patrón arquitectónico que R5 de
  `001-registrar-usuario`):
  1. `GET/POST /clientes/registrar/` (`clientes:registrar`) — muestra y procesa
     `RegistroClienteForm`. Si el POST es válido, guarda los datos limpios y normalizados en
     `request.session["cliente_pendiente"]` y redirige (302) a `clientes:registrar_confirmar`. No
     crea ningún registro en la base.
  2. `GET /clientes/registrar/confirmar/` (`clientes:registrar_confirmar`) — presenta el resumen de
     los datos a registrar con tres acciones:
     - **Confirmar** (POST con `accion=confirmar`).
     - **Volver y editar** (link GET a `clientes:registrar`, que precarga el formulario desde
       `request.session["cliente_pendiente"]`).
     - **Cancelar** (POST con `accion=cancelar`, que borra `cliente_pendiente` de la sesión y
       redirige a `clientes:registrar` con el mensaje `"Registro de cliente cancelado."`).
  3. `POST /clientes/registrar/confirmar/` con `accion=confirmar` — dentro de `transaction.atomic()`,
     crea el `Cliente`, borra `cliente_pendiente` de la sesión, guarda
     `request.session["ultimo_cliente_creado_id"] = cliente.pk` y redirige a la ficha del cliente
     (`clientes:detalle`).
- **Por qué**: FR-010, FR-011, Escenario 6 y la regla de Interfaz de la constitution (*"Las acciones
  que guardan o eliminan datos piden confirmación antes de ejecutarse"*). Mantiene un patrón idéntico
  al de `usuarios` sin dependencias externas.
- **Alternativas descartadas**:
  - Enviar los datos en campos ocultos en la pantalla de confirmación: obliga a revalidar todo el
    formulario en el segundo POST y duplica lógica.
  - Modal de confirmación en el navegador con JavaScript: no cumple con una instancia de revisión
    verificable del lado del servidor con el test client de Django.

## R7. Confirmación repetida o concurrente (idempotencia, FR-012)

- **Decisión**:
  - **Caso secuencial** (doble clic o reenvío del POST luego de haber confirmado): cuando el primer
    POST crea el cliente, elimina `cliente_pendiente` y guarda `ultimo_cliente_creado_id` en la
    sesión. Un segundo POST `accion=confirmar` sin `cliente_pendiente` detecta
    `ultimo_cliente_creado_id` (verificando que exista en la base) y redirige a `clientes:detalle`
    con el mensaje informativo `"Cliente registrado correctamente."` sin crear un segundo registro.
    Si tampoco hay `ultimo_cliente_creado_id`, redirige a `clientes:registrar`.
  - **Caso concurrente** (dos solicitudes simultáneas o el mismo documento dado de alta por otro
    empleado entre el formulario y la confirmación): el segundo `INSERT` levanta `IntegrityError` por
    el constraint `cliente_documento_unico`. La vista captura `IntegrityError`, no crea un cliente
    duplicado y redirige a `clientes:registrar` con el mensaje de error
    `"Ya existe un cliente registrado con este tipo y número de documento."` (conservando los datos en
    sesión para que el empleado pueda corregirlos).
  - Además, el botón **Confirmar** se deshabilita al enviar el formulario en el template como ayuda
    de interfaz.
- **Por qué**: FR-012, Escenario 7 y el caso borde *"Una confirmación repetida o un reintento por una
  respuesta demorada no crea clientes duplicados"*.
- **Alternativas descartadas**: tabla de tokens de idempotencia en la base de datos (sobreingeniería
  para el volumen del laboratorio, Principio II).

## R8. Consulta del cliente recién creado y mensajes (Escenarios 1 y 2, FR-013)

- **Decisión**:
  - Incluir la vista `GET /clientes/<int:pk>/` (`clientes:detalle`) que muestra todos los datos
    registrados del cliente (nombre, razón social, tipo y número de documento, correo electrónico,
    teléfono, domicilio y estado activo), junto con un botón `"Registrar otro cliente"` hacia
    `clientes:registrar`.
  - Tras confirmar el alta con éxito, se emite `messages.success(request, "Cliente registrado correctamente.")`
    y se redirige a `clientes:detalle`.
  - Si al confirmar ocurre un `DatabaseError` inesperado (distinto de `IntegrityError`), se muestra
    en la misma pantalla de revisión (HTTP 200) el mensaje de error
    `"No se pudo completar el registro del cliente. Intentá nuevamente."` sin crear el cliente ni
    perder los datos en sesión.
  - Agregar en `templates/inicio.html` un acceso directo a `clientes:registrar` ("Registrar cliente")
    para que el empleado pueda navegar desde el inicio.
- **Por qué**: el Escenario 2 pide explícitamente *"Given un cliente creado correctamente, When el
  empleado consulta el cliente recién creado (por ejemplo, desde la confirmación del alta), Then ve
  todos los datos registrados"*, y SC-004 exige que el 100% de los clientes creados pueda consultarse
  de inmediato.
- **Alternativas descartadas**: redirigir a una página estática sin mostrar los datos del cliente (no
  permitiría verificar el Escenario 2 desde la interfaz de la aplicación).

## R9. Seguridad y sesión activa (FR-001, Principio V)

- **Decisión**: todas las vistas de la app `clientes` requieren usuario autenticado. Como el setup ya
  activó `django.contrib.auth.middleware.LoginRequiredMiddleware` en `config/settings.py`, ninguna
  vista de `clientes` lleva `@login_not_required`. Cualquier acceso sin sesión redirige
  automáticamente a `settings.LOGIN_URL`.
- **Por qué**: FR-001 (*"El sistema MUST permitir registrar clientes únicamente a empleados con una
  sesión activa"*) y Principio V de la constitution (*"Todas las vistas requieren sesión iniciada,
  salvo login y registro"*). Además, desacopla esta feature de la US 1.2: funciona hoy con el login
  temporal y seguirá funcionando sin cambios cuando la US 1.2 actualice `LOGIN_URL`.
- **Alternativas descartadas**: agregar decoradores `@login_required` redundantes o depender de las
  rutas de la US 1.2 para testear `clientes` (en los tests se autentica con `client.force_login()`).
