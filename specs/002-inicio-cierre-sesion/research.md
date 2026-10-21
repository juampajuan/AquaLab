# Investigación: SCRUM-42 / US 1.2

Fecha: 2026-10-20. Diseño para revisión, sin ejecución de código de aplicación.

## R1. Mantener identidad, backend y aprobación

**Decisión:** reutilizar `usuarios.Usuario` y `ModelBackend`. `is_active=False` sigue significando
pendiente, como en US 1.1. Sin campos ni migraciones nuevas.
**Motivo:** los tests actuales exigen que authenticate y client.login rechacen cuentas pendientes.
**Alternativas:** `AllowAllUsersModelBackend` global rompería esa garantía; no se adopta la
posibilidad mencionada, pero no impuesta, por research de US 1.1. Un estado de aprobación adicional
sería redundante y está fuera del alcance.

## R2. Formulario y diagnóstico de pendiente

**Decisión:** extender AuthenticationForm, conservar su campo interno `username` con etiqueta
«Correo electrónico» y normalizarlo con `UsuarioManager.normalizar_email`. No recortar contraseña
(`strip=False`). Redefinir el campo interno username como forms.CharField, sin heredar
UsernameField ni su normalización NFKC. En clean_username llamar exactamente a
UsuarioManager.normalizar_email, igual que RegistroForm.clean_email; no aplicar NFC/NFKC,
casefold, conversión IDNA ni otras transformaciones adicionales. Conservar longitud/required y
widget de correo/autocomplete; no añadir una política nueva de validación al identificador.
Los campos requeridos se validan antes de cualquier autenticación. Probar igualdad de resultado
entre el campo de registro, el campo de login y el manager con correos Unicode aceptados por el
registro; por ejemplo un dominio con carácter de ancho completo que NFKC modificaría. Crear por
registro/confirmación, aprobar e ingresar con ese correo; verificar que no se sustituye por su
variante NFKC ni se selecciona otra cuenta. No ampliar validadores para aceptar el fixture.
Solo `authenticate()` con el ModelBackend existente puede proporcionar el usuario apto para
LoginView. Nunca autenticar directamente al objeto recuperado por el diagnóstico ni llamar al
backend permisivo de Django, siquiera como alternativa configurada.

**Secuencia del diagnóstico (solo cuando authenticate devuelve None):**
1. Realizar una consulta por el correo normalizado usando el mismo criterio de identidad del
   backend. No filtrar por is_active ni hacer primero exists/count y luego una segunda consulta.
2. Para cualquier cuenta encontrada, activa o inactiva, ejecutar
   `django.contrib.auth.hashers.check_password` sobre su hash, sin setter. Para cuenta inexistente,
   ejecutar la misma utilidad con un valor de contraseña inutilizable de Django: Django 5.2.18
   efectúa trabajo ficticio con el hasher predeterminado. Crear ese valor no equivale a hacer un
   hash costoso; no generar primero un hash real y verificarlo después en la rama inexistente.
3. Solo después de comprobar la contraseña, evaluar is_active. Únicamente coincidencia correcta
   más cuenta pendiente produce «Tu cuenta está pendiente de aprobación». El resto produce
   «Usuario o contraseña incorrectos» con igual código HTTP, código de error y estructura de
   errores del formulario. No devolver indicadores de existencia/estado en contexto, HTML o JSON.
4. Devolver exclusivamente un error de validación. No asignar user_cache, llamar login, aprobar
   cuenta ni escribir claves de autenticación. El diagnóstico no actualiza hashes porque no usa
   setter; las actualizaciones estándar que pudiera hacer ModelBackend no se reimplementan.

**Motivo:** mantener en las ramas fallidas una consulta y una verificación diagnóstica comparable,
además del trabajo normal de ModelBackend. No hacer una segunda verificación solo para pendientes,
ni omitirla para activos o inexistentes. No repetir authenticate como parte del diagnóstico.
Campos vacíos no llegan a ninguna de estas operaciones; éxito aprobado no ejecuta el diagnóstico.

**Límite del control temporal:** con el hasher y factor de trabajo actuales, evitar diferencias
introducidas por nuestras ramas. Usar la compensación de trabajo que ya ofrece Django para hashes
antiguos del mismo algoritmo. Hashers distintos, upgrades de hash, BD y sistema operativo impiden
prometer tiempos idénticos. Django no iguala todos los algoritmos entre sí; si la base real mezcla
algoritmos con costes distintos, registrar el hallazgo para revisión antes de declarar esta
verificación satisfecha. No cambiar PASSWORD_HASHERS ni migrar contraseñas dentro de esta US.
Las pruebas observan operaciones reales mediante spies, no solo mocks de una función contenedora,
y no comparan milisegundos ni intentan fijar una cantidad universal de hashes ante upgrades.

**Alternativas:** cambiar solo confirm_login_allowed no alcanza porque ModelBackend no devuelve
inactivos. Backend propio o AllowAllUsersModelBackend global rompería la garantía existente o
ampliaría alcance. No añadir esperas artificiales, throttling ni bloqueos fuera de spec.

**Falla técnica:** un fallo de BD en cualquiera de las dos fases termina sin login y con la misma
respuesta general de operación, independiente del correo; no renderizar excepción, SQL ni estado
de cuenta. No transformar errores de programación en éxitos ni capturar indiscriminadamente toda
excepción. Los registros técnicos excluyen credenciales, hashes y cuerpos de formularios. Un error
operativo puede diferir del error de credenciales, pero no debe variar según existencia o aprobación.

## R3. Redirecciones y rutas

**Decisión:** login correcto o acceso al login ya autenticado siempre termina en `inicio`.
Ignorar next, incluso local, en el login de AquaLab y en logout. LoginRequiredMiddleware puede
seguir agregando next en su redirección, pero no se reenvían POST de negocio después de ingresar.
**Motivo:** FR-006 es explícito. Evita redirecciones abiertas y reenvíos involuntarios de altas.
**Alternativa:** retorno automático a URL inicial contradice el destino especificado.
Mantener admin y su autorización nativa; sus pantallas de login son excepciones de la categoría
login. El resto de sus pantallas sigue exigiendo sesión y permisos administrativos.

## R4. Logout, CSRF y borradores

**Decisión:** LogoutView de Django con POST y CSRF, destino fijo al login. Mantenerlo protegido por
LoginRequiredMiddleware: un anónimo redirige al login sin ejecutar la vista. GET autenticado no
cierra sesión. Usar logout/flush, no solo borrar cookie o limpiar claves selectivamente.
La misma CerrarSesionView determina get_success_url con el destino fijo usuarios:login, sin
consultar parámetros GET/POST; next_page/LOGOUT_REDIRECT_URL por sí solos no anulan next.
En config/urls.py registrar la ruta exacta admin/logout/ antes de incluir admin.site.urls,
resolviendo a esa misma vista protegida, como alias del cierre de AquaLab. Conservar el include y
namespace admin:logout, que sigue generando /admin/logout/; no duplicar nombre de ruta ni mutar
AdminSite, sus permisos o sus formularios. Probar resolve(reverse('admin:logout')) y POST real.
El alias realiza solo cierre, nunca autoriza acceso al admin; un usuario común puede cerrar su
propia sesión por cualquiera de los dos alias, pero no adquiere staff ni permisos administrativos.
El resto de rutas del admin mantiene sus verificaciones nativas. LOGOUT_REDIRECT_URL queda como
valor consistente de configuración, no como garantía suficiente de destino fijo.
**Motivo:** invalidar la clave anterior también cuando otra pestaña conserva su cookie; conservar
otras sesiones independientes del mismo usuario. Los borradores `registro_pendiente`,
`cliente_pendiente` y `ultimo_cliente_creado_id` desaparecen junto con la sesión; las filas Usuario
 y Cliente ya creadas no se borran.
**Confirmación del usuario:** botón suficiente, sin diálogo adicional.
**Repetición:** POST repetido con token CSRF válido redirige a login sin error de aplicación. Token
inválido/ausente conserva 403; idempotencia no justifica desactivar CSRF. Un POST de clientes
anónimo sin CSRF válido también puede devolver 403 antes del middleware de login, sin contenido.
**Alternativas:** logout por GET, csrf_exempt o purgar todas las sesiones no cumplen el alcance.

## R5. Caché y múltiples pestañas

**Decisión confirmada:** exigir login al volver/navegar/actualizar; no señal ni ocultamiento
inmediato en otras ventanas que continúan visibles. No usar polling, localStorage ni BroadcastChannel.
Combinar cabeceras `private, no-cache, no-store, must-revalidate` con guardia visual nativa.
**Motivo:** Chrome permite bfcache en determinadas páginas no-store; no basta con cabeceras.
Ocultar el contenido sensible al perder visibilidad/foco y en pagehide; en pageshow.persisted,
visibilitychange a visible y recuperación de foco, consultar la validez de la sesión original antes
de mostrar. Unificar eventos en un único manejador de revalidación, con estado oculto/validando y
una generación de solicitud, para no generar bucles ni solicitudes paralelas. No ocultar una página inicial indefinidamente ni disparar un reload continuo.
La consulta GET protegida devuelve 204 si coincide una huella de sesión; 409 si hay otra sesión;
si no hay autenticación, el middleware redirige al login. El cliente considera válida exclusivamente
una respuesta 204 sin redirección, con URL final de revalidación del mismo origen.
Usar fetch con redirect='follow', credentials='same-origin' y cache='no-store'. Identificar el
login seguido solo cuando response.redirected es true, status es 200 y new URL(response.url)
tiene el mismo origen y pathname exacto de usuarios:login, resuelto por Django en el layout;
la query next no altera esa identificación ni el destino de navegación. En ese caso mantener
oculto y usar location.replace con la URL fija propia de login, nunca una URL recibida libremente.
Un 200 sin redirección, una redirección a otro destino, un estado no reconocido o error de red
mantienen oculto y permiten reintentar. No inspeccionar texto HTML para reconocer el login.
El 409 directo conserva su conducta de descartar DOM y navegar al login fijo. No confundir un
HTML de login seguido con autenticación válida ni tratarlo como fallo operativo.
**Huella:** derivación HMAC con `django.utils.crypto.salted_hmac`, salt propio y SECRET_KEY, sobre
identidad y clave de sesión; renderizada solo en páginas autenticadas. No publicar sessionid,
password, hash de contraseña ni SECRET_KEY. Se compara en el servidor con la sesión actual, nunca
sustituye a la cookie ni autoriza un acceso. Sin tabla ni estado adicional. Evita resucitar DOM
sensible de A cuando B inició sesión en el mismo navegador.
**Alternativas:** recargar siempre al volver pierde los campos no enviados de usuarios/clientes;
verificar solo is_authenticated expone DOM de la identidad anterior; señales entre pestañas no
son necesarias para el alcance confirmado.
**Límite de aceptación:** navegadores de escritorio con JavaScript habilitado, a validar en el
entorno del laboratorio. Sin JS sigue vigente la protección del servidor, pero no se promete el
control visual de páginas ya cargadas; no declarar SC-004 aprobado solo por tests del servidor.
Si el equipo requiere garantía visual sin JS, ampliar navegadores soportados o alterar la conducta
confirmada, se requiere una nueva decisión antes de implementar ese cambio.

### Evaluación de mínima complejidad (revisión técnica)

Se conserva esta combinación porque cada pieza tiene una responsabilidad distinta:

| Pieza | Necesidad | Alcance mínimo |
|---|---|---|
| Django logout y LoginRequiredMiddleware | Invalidar y denegar acceso real | Reutilizar sin segundo sistema de autenticación |
| Cabeceras de caché | Evitar almacenamiento HTTP de respuestas sensibles | Un middleware de respuesta con utilidades Django, sin consultar BD ni administrar sesiones |
| JavaScript compartido | Revalidar DOM restaurado o al volver sin petición de navegación | Un archivo para layouts autenticados, sin polling, bus de eventos o biblioteca |
| GET de sesión | Consultar al servidor sin perder campos ni reenviar POST | Una vista de solo lectura; no endpoint adicional de usuario/estado/permisos |
| HMAC | Distinguir la sesión original de otra del mismo o distinto usuario | Una función con salted_hmac y constant_time_compare; sin token almacenado, firma genérica ni tabla |

Recargar por GET al volver eliminaría el endpoint y HMAC, pero perdería campos/errores no enviados;
no se adopta porque degradaría los flujos existentes de registro/clientes. Comprobar solo una sesión
activa o el ID de usuario permitiría reutilizar DOM anterior después de logout y nuevo login incluso
del mismo usuario. Una marca aleatoria persistida requeriría gestionar su creación en cada login,
incluido admin, y su ciclo de vida; no simplifica el diseño global frente a la huella derivada.
No sustituir la huella por el token CSRF: su función y ciclo de vida son diferentes.

**Acotación:** el middleware no calcula ni compara HMAC. La misma función pequeña produce la huella
en el render de páginas protegidas (context processor) y en la vista de comprobación. El context
processor no crea una sesión para visitantes anónimos. La guardia se activa únicamente si hay
usuario autenticado y huella; no se monta en login ni registro anónimo, que debe seguir funcionando
al cambiar de pestaña. Nada de esto añade una excepción a LoginRequiredMiddleware.

Un cambio de foco hacia controles del navegador puede disparar la guardia; probar que no produce
un bucle al volver ni borra entradas, interfiere con autocompletado o deja inaccesible el reintento.
La generación de solicitud evita revelar el DOM por una respuesta vieja luego de ocultar otra vez.
La respuesta 204 solo se acepta si la solicitud sigue vigente, la página volvió a estar visible y
el documento tiene foco. Las respuestas 200, 403 u otros estados inesperados nunca revelan DOM.
No se pretende atomicidad con un logout concurrente posterior a la comprobación: al próximo regreso
o acceso se verifica nuevamente, conforme al alcance confirmado sin difusión en tiempo real.

## R6. Regresiones y validación

**Decisión:** conservar suite de usuarios/clientes, agregar pruebas de autenticación y sesión con
pytest-django y CSRF explícito. Complementar escenario 7 con navegador real, sin añadir Playwright
ni Selenium como dependencia del proyecto. Revisar admin, registro y clientes, no solo inicio.
**Motivo:** test client no ejecuta JS ni reproduce bfcache. Campos en formularios deben conservarse
al cambiar pestaña con sesión válida, incluidos errores y la revisión previa a confirmar.
**Alternativas:** probar solo una URL o solo cabeceras deja requisitos sin evidencia.

## Fuentes y evidencia

- Código local: `usuarios/models.py`, `usuarios/tests/test_autenticacion.py`,
  `usuarios/tests/test_setup.py`, `clientes/tests/test_registro.py`, `config/settings.py`,
  `specs/001-registrar-usuario/research.md`, `specs/003-registrar-cliente/plan.md`, `CLAUDE.md`.
- [Backend Django 5.2](https://github.com/django/django/blob/stable/5.2.x/django/contrib/auth/backends.py).
- [Formularios Django 5.2](https://github.com/django/django/blob/stable/5.2.x/django/contrib/auth/forms.py).
- [Vistas Django 5.2](https://github.com/django/django/blob/stable/5.2.x/django/contrib/auth/views.py).
- [Hashers Django 5.2.18](https://github.com/django/django/blob/5.2.18/django/contrib/auth/hashers.py).
- [CSRF](https://docs.djangoproject.com/en/5.2/ref/csrf/).
- [Sesiones y flush](https://docs.djangoproject.com/en/5.2/topics/http/sessions/#django.contrib.sessions.backends.base.SessionBase.flush).
- [Chrome: bfcache y no-store](https://developer.chrome.com/docs/web-platform/bfcache-ccns).
- [pageshow](https://developer.mozilla.org/en-US/docs/Web/API/Window/pageshow_event).
- [visibilitychange](https://developer.mozilla.org/en-US/docs/Web/API/Document/visibilitychange_event).

Las decisiones son diseño derivado de estas fuentes y del código, no certificación de seguridad
ni pruebas ejecutadas. Las dos aclaraciones funcionales consultadas quedaron resueltas en el chat.
