# Plan de implementación: Inicio y cierre de sesión

**US**: 1.2 / SCRUM-42 | **Rama**: `002-inicio-cierre-sesion` | **Fecha**: 2026-10-20
**Entrada**: [spec.md](spec.md) | **Estado**: diseño preparado para revisión del equipo; no implementado.

## Resumen

Completar el acceso de AquaLab reutilizando `usuarios.Usuario`, autenticación, sesiones, formularios,
mensajes y vistas de Django. Conservar `ModelBackend`, la aprobación mediante `is_active` y los tests
de US 1.1. Login por correo, destino fijo a inicio, logout POST con CSRF y protección global.
Sin modelos, migraciones, paquetes, roles ni mecanismos de recuperación nuevos.

Decisiones confirmadas por el usuario durante esta planificación:
- En otras pestañas se exige login al volver, navegar o actualizar; no se exige ocultamiento
  automático de una ventana que permanece visible sin interacción.
- El botón «Cerrar sesión» basta; no habrá confirmación adicional. El cierre descarta borradores
  transitorios de la sesión, no registros persistidos.
Estas decisiones se documentan aquí sin modificar la spec ni la Constitution.

## Contexto técnico

- Python 3.12, Django 5.2.18, PostgreSQL 16 en Docker Compose.
- Dependencias existentes: psycopg 3.3.6, dj-database-url 3.1.2, pytest 9.1.1,
  pytest-django 4.14.0, ruff 0.17.1; Bootstrap 5.3.8 ya cargado por el layout.
- Aplicación monolítica con templates; JavaScript nativo mínimo para restauración de página.
- Persistencia: usuario existente y sesiones Django en BD. `DATABASE_URL` y secretos por entorno.
- Objetivo SC-001: recorrido de login en menos de 30 segundos, comprobado en navegador; no se
  interpreta como permiso para que una petición tarde 30 segundos. Sin volumen/SLA inventado.
- Alcance: inicio, registro, clientes y rutas administrativas existentes. Sin nuevos módulos.
- Pruebas: pytest-django contra PostgreSQL; verificación real de navegador para caché y pestañas.
- Entorno observado: Git Bash funcional. Docker no localizado en PATH y `.env` ausente en la
  revisión inicial; runtime, instalación de requisitos y ejecución de tests aún no validados.

## Chequeo de Constitution

| Principio | Antes de investigación | Después del diseño |
|---|---|---|
| I. Spec primero | Spec existente y trazable; aún figura Draft | Solo documentación. Aprobación de la spec por el equipo requerida antes de implementar |
| II. Simplicidad | Django y apps existentes | Sin dependencias nuevas; justificación de diagnóstico y revalidación en research |
| III. Tests | Ocho escenarios identificados | Matriz de ocho escenarios y regresiones; ejecución pendiente, no se declara CI verde |
| IV. Integridad | No se alteran datos del laboratorio | Logout descarta borradores, conserva usuarios/clientes persistidos; reglas en formulario/servidor |
| V. Seguridad | Middleware, hash y CSRF existentes | Backend conserva rechazo de inactivos; logout POST, rutas protegidas y no almacenamiento de secretos en JS |
| VI. Idioma | Dominio y documentación en español | Mensajes exactos de la spec, nombres del dominio en español, ruff previsto |
| UI y flujo | Layout Bootstrap compartido | Nombre, enlaces y cierre disponibles; confirmación de cierre resuelta por el usuario |

No se identifica una excepción constitucional en el diseño. No hay aclaraciones funcionales
pendientes de las dos consultadas. Esto no acredita aprobación formal de la spec ni resultados de
pruebas: son condiciones de entrada a implementación y merge respectivamente.

## Diseño y responsabilidades

1. `FormularioInicioSesion` basado en `AuthenticationForm`: normaliza correo con el manager
   existente mediante un campo username redefinido como forms.CharField sin UsernameField/NFKC;
   clean_username usa exactamente la misma normalización que RegistroForm.clean_email, con prueba
   Unicode de equivalencia e ingreso posterior al registro. Mantiene contraseña exacta y valida
   campos antes de autenticar. Diagnóstico de
   pendiente solo tras fallo de autenticación y contraseña comprobada, sin autenticar al inactivo.
   Una consulta sin filtro de aprobación y una comprobación diagnóstica en todas las ramas
   fallidas; hash real o trabajo ficticio estándar, sin setter ni segundo authenticate (research R2).
2. `InicioSesionView` basada en `LoginView`: `redirect_authenticated_user=True`; siempre `inicio`
   tras éxito, aunque se reciba `next` local o externo. Formulario Bootstrap y errores en español.
3. `CerrarSesionView` basada en `LogoutView`: POST/OPTIONS; GET autenticado devuelve 405 y no
   modifica estado. Django invalida la sesión; destino fijo a login, sin seguir `next`.
4. Mantener `LoginRequiredMiddleware`, después de `AuthenticationMiddleware`; cambiar `LOGIN_URL`
   a `usuarios:login`. Mantener las tres vistas públicas del flujo de registro y el login.
   Las redirecciones no preservan ni reproducen automáticamente POST de negocio.
5. Todas las respuestas autenticadas sensibles reciben cabeceras de no almacenamiento mediante
   un middleware pequeño de `usuarios`, situado después de autenticación y antes del middleware
   de login. Solo ajusta cabeceras: no autentica, consulta BD ni calcula huellas. Login y respuestas
   de revalidación también son no-cache.
6. Guardia visual compartida: ocultar antes de abandonar/suspender la página y revalidar al
   restaurar bfcache, volver visible o recuperar foco. Consulta protegida GET `usuarios:sesion`
   compara una huella de la sesión original. Misma sesión: mostrar DOM conservando campos;
   distinta o anónima: navegar a login sin mostrar DOM anterior. Error de red: mantener oculto,
   ofrecer reintento sin afirmar que la sesión sigue válida. Evitar bucles, llamadas concurrentes
   y revalidación innecesaria durante la carga inicial. Un context processor entrega la huella
   solo a páginas autenticadas; comparte una función HMAC pequeña con la vista. No crea sesiones
   anónimas ni activa la guardia en login/registro anónimo. fetch sigue redirecciones: solo
   response.redirected + status 200 + origen/pathname final exactos del login identifican sesión
   anónima; navegar al login fijo sin revelar. Un 200 inesperado/redirección desconocida mantiene
   oculto y permite reintento; solo 204 directo válido permite mostrar (contrato de sesión).
7. Mantener el admin y sus permisos nativos. Su login cuenta como pantalla de inicio de sesión,
   no como pantalla de negocio pública. Ajustar también su layout compartido mediante extensión
   mínima del template del admin para revalidación y enlace POST al cierre de AquaLab; conservar
   la aprobación y nombres de rutas del admin. En config/urls.py registrar admin/logout/ antes
   del include admin.site.urls como alias de CerrarSesionView; reverse admin:logout conserva esa
   URL. Ambos cierres usan get_success_url fijo e ignoran next en query/POST; no basta configurar
   LOGOUT_REDIRECT_URL. Sin mutar AdminSite ni sus controles is_staff/permisos; el alias solo
   cierra la propia sesión y nunca concede acceso administrativo.
8. Enlazar registro e inicio de sesión en ambos sentidos; conservar inicio y acceso a registrar
   cliente. Llevar el enlace de clientes al navbar según pendiente documentado en CLAUDE.md.

## Estructura prevista

Artefactos de esta ejecución: `plan.md`, `research.md`, `data-model.md`,
`contracts/sesion.md`, `quickstart.md`. No se genera `tasks.md`.

Archivos que la implementación posterior podría afectar (no modificados ahora):
- `usuarios/forms.py`, `usuarios/views.py`, `usuarios/urls.py`: autenticación y contratos HTTP.
- `usuarios/middleware.py`: únicamente cabeceras de contenido sensible.
- `usuarios/context_processors.py`: contexto de revalidación solo autenticado; función HMAC
  compartida con la vista, sin servicio, almacén ni ciclo de vida de tokens nuevo.
- `usuarios/static/usuarios/sesion.js`: guardia visual común, sin bibliotecas nuevas.
- `usuarios/templates/usuarios/login.html`, `usuarios/templates/usuarios/registro_recibido.html`.
- `templates/base.html`, `templates/admin/base_site.html`: navegación y guardia visual común.
- `config/settings.py`: destinos de login/logout, middleware y context processor; backend sin cambios.
- `config/urls.py`: alias exacto admin/logout/ a la vista común, antes del include del admin,
  sin alterar su namespace ni permisos.
- `usuarios/tests/test_sesion.py`, `usuarios/tests/test_setup.py`, pruebas pertinentes de clientes.
- README y pendientes de CLAUDE.md solo al implementar, si dejan de reflejar el comportamiento.

## Trazabilidad y verificaciones previstas

Todos los casos tienen al menos una prueba pytest-django. Los nombres son propuestos, no tests creados.

| Escenario | Requisitos | Verificación automatizada prevista | Complemento |
|---|---|---|---|
| 1. Ingreso aprobado | FR-001/002/004/006/007 | POST válido, sesión autenticada, 302 a inicio y nombre en HTML | Medir SC-001, menos de 30 s |
| 2. Login ya autenticado | FR-006 | GET/POST login con sesión redirige a inicio; next no cambia destino | Sin bucle |
| 3. Campos vacíos | FR-003 | Parametrizar ambos/uno vacío; errores de campo; authenticate y diagnóstico no invocados | Validación de servidor además de required |
| 4. Credenciales inválidas | FR-005 | Correo inexistente y password incorrecta de activo/inactivo: mismo mensaje, sin autenticación | Contraseña con espacios preservada |
| 5. Ruta protegida anónima | FR-008/009 | Matriz GET y POST pertinentes de inicio, clientes, sesión y admin; no contenido ni escritura | Registro y login públicos |
| 6. Cierre desde cualquier pantalla | FR-010/011/013 | Botón POST+CSRF en layouts; logout borra sesión vieja y redirige; clientes que comparten cookie pierden acceso | Otra sesión del mismo usuario continúa |
| 7. Atrás/actualizar/URL | FR-012/013 | Reusar cookie vieja no permite acceso; cabeceras; contrato de huella coincidente/distinta | Navegador: bfcache, Atrás/Adelante, foco, red fallida y cambio de usuario |
| 8. Cuenta pendiente | FR-004/015 | Password correcta muestra mensaje exacto; sin _auth_user_id; authenticate/client.login siguen rechazando | Luego de aprobar, puede ingresar |

Adicionales: CSRF real con `Client(enforce_csrf_checks=True)`; token válido/ausente/incorrecto;
logout repetido sin reactivar sesión; GET no muta; next malicioso; normalización de correo;
fallos de autenticación sin sesión parcial; huella no sirve como autorización; registro y aprobación
US 1.1 completos; confirmación/cancelación/doble envío de clientes; registros persistidos intactos
tras logout; borradores de sesión no reaparecen al ingresar otra persona. Sin contraseña ni cookie
sessionid en HTML, mensajes, URLs o logs.

Actualizar únicamente la expectativa temporal `admin:login` de `test_setup.py` al login propio.
No relajar las pruebas de `test_autenticacion.py` ni los controles de aprobación.

## Complejidad y límites

El diagnóstico adicional evita cambiar el backend. La consulta de revalidación evita perder
formularios al volver y evita mostrar datos de la sesión anterior tras cambiar de usuario. Ambos
resuelven requisitos de esta US, sin introducir API pública ni SPA.
La revisión técnica conserva endpoint y HMAC porque evitan recargar formularios o aceptar DOM de
una sesión anterior; limita el middleware a cabeceras y la guardia a layouts autenticados.
Ver research R5 para alternativas descartadas y quickstart S01–S10 para pruebas concretas.
La cobertura visual exige JavaScript y navegador real; pytest no demuestra bfcache ni ausencia de
un destello visual. Registrar navegador/versión en la validación y no aceptar la entrega si falla
el escenario 7 en el entorno del laboratorio. La aprobación del equipo sigue siendo necesaria
antes de implementar una spec aún marcada Draft.

## Excepción de proceso autorizada para esta rama

2026-10-20: el usuario solicitó expresamente implementar en `002-inicio-cierre-sesion` antes
de la aprobación formal de la spec. Se registra como excepción al principio I, conforme a la
regla de excepciones documentadas del gobierno, no como aprobación del equipo. T001 permanece
pendiente. No se autoriza push, PR, merge ni modificación de main; la historia no se declara
completa antes de validar navegador real. No se modifica la Constitution ni la spec.
