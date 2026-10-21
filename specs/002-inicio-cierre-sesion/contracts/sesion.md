# Contratos de sesión: SCRUM-42 / US 1.2

Propuesta de interfaz HTTP y HTML para revisión. No es una API pública nueva.
Los nombres de rutas son los previstos para implementación. Todas las URLs son del mismo origen.

## Rutas

| Método y ruta | Nombre | Resultado |
|---|---|---|
| GET /usuarios/login/ | usuarios:login | Anónimo: 200 formulario; autenticado: 302 a / |
| POST /usuarios/login/ | usuarios:login | CSRF válido y aprobada válida: 302 a /; errores de formulario: 200 sin login |
| POST /usuarios/logout/ | usuarios:logout | Autenticado y CSRF válido: invalidar sesión y 302 a /usuarios/login/ |
| GET /usuarios/logout/ | usuarios:logout | Autenticado: 405, sesión intacta; anónimo: redirección del middleware |
| GET /usuarios/sesion/ | usuarios:sesion | Protegida: 204 misma huella; 409 huella ausente/diferente; anónimo 302 login |
| GET / | inicio | Protegida, 200 con nombre y navegación |

LoginView conserva GET/POST/HEAD/OPTIONS según Django; el contrato funcional se verifica con GET/POST.
LogoutView admite POST/OPTIONS, nunca GET para mutar. Revalidación es de solo lectura y no prolonga
expiración deliberadamente ni crea una sesión; métodos de escritura devuelven 405 si autenticado.

### Formulario de login

- Campo interno `username`, etiqueta «Correo electrónico», autocomplete username; redefinirlo
  como forms.CharField sin heredar UsernameField/NFKC. clean_username usa exactamente
  UsuarioManager.normalizar_email, igual que RegistroForm.clean_email, sin transformaciones
  Unicode/IDNA adicionales; conservar restricciones de longitud y required. Probar equivalencia
  con correos Unicode admitidos actualmente por registro y su ingreso posterior a aprobación.
- Campo `password`, autocomplete current-password, no re-renderizar su valor.
- Ambos requeridos; errores de campo en español antes de llamar authenticate.
- Normalizar correo con strip/lower; contraseña literal.
- Error general exacto: «Usuario o contraseña incorrectos».
- Solo pendiente con contraseña correcta: «Tu cuenta está pendiente de aprobación».
- Inexistente, activo con contraseña incorrecta y pendiente con contraseña incorrecta usan el mismo
  estado HTTP 200, error general y código de validación. No incluir banderas de existencia/estado
  ni distinguirlos con enlaces, cabeceras o contexto adicional. CSRF y valores reflejados del
  formulario pueden variar: no exigir identidad byte a byte del HTML.
- El diagnóstico ejecuta la misma consulta y ruta de comprobación para todos los fallos, sin
  filtro previo por is_active, sin setter y sin autenticar al objeto encontrado (research R2).
- Enlace «Crear cuenta» a usuarios:registro. En registro_recibido, «Iniciar sesión» al login propio.
- CSRF presente. Un token ausente/incorrecto devuelve 403 antes de validar credenciales.
- `next`, `redirect_to` u otros valores aportados por el usuario no cambian el destino de éxito.
- Errores de credenciales son errores del formulario; mensajes de operaciones usan el framework
  existente. No inventar un mensaje de éxito obligatorio para login/logout.

### Logout

Formulario POST con csrf_token disponible en todas las pantallas autenticadas de AquaLab y del
admin mediante su layout. El botón es la confirmación suficiente acordada. No crear pantalla
intermedia ni cerrar sesión por enlaces GET. No usar JavaScript como sustituto de POST/CSRF.
El cierre invalidará la sesión en BD antes de la redirección. No mostrar contenido protegido en
la respuesta. Repetición con CSRF válido termina en login; con CSRF inválido se conserva 403.
Los dos endpoints /usuarios/logout/ y /admin/logout/ resuelven a la misma CerrarSesionView con
get_success_url fijo a usuarios:login, ignorando next en query y cuerpo POST. En config/urls.py,
la ruta exacta admin/logout/ precede al include admin.site.urls; mantener el namespace y reverse
admin:logout, sin reemplazar permisos del admin ni modificar AdminSite. LOGOUT_REDIRECT_URL
se configura coherentemente, pero no basta por sí solo para anular next. GET autenticado en
ambos endpoints devuelve 405 y no cierra; POST sin CSRF sigue devolviendo 403. El alias no concede
acceso administrativo: los controles staff/permisos de todas las demás rutas permanecen intactos.

### Protección de rutas

`LoginRequiredMiddleware` exige sesión por defecto. Excepciones: login AquaLab, las tres rutas del
flujo de registro y login administrativo existente (categoría login). No marcar públicas clientes,
inicio, logout ni revalidación. El admin conserva su autorización adicional de staff/permisos.
Rutas de clientes a verificar: /clientes/registrar/, /clientes/registrar/confirmar/ y detalle según
clientes.urls. Inventariar la resolución real de rutas en pruebas; no confiar solo en esta lista.
Solicitud GET anónima protegida: 302 a login con next permitido como información, sin HTML sensible.
POST anónimo con CSRF válido: 302 sin ejecutar la operación. CSRF inválido: 403 sin efectos.
No reproducir automáticamente el cuerpo de un POST después del login.

### Caché y revalidación

Respuestas sensibles: Cache-Control privado/no-store/no-cache/must-revalidate, incluidas las
respuestas HTML autenticadas del admin y errores de formularios; añadir cabeceras mediante utilidades
Django, conservando las existentes. No caché también en login y respuestas 204/409 de sesión.
No aplicar lógica de DOM a archivos estáticos ni abrir rutas nuevas como excepción de autenticación.

La guardia lleva `X-AquaLab-Sesion` con la huella original y cookies same-origin en GET de sesión,
con fetch redirect='follow', credentials='same-origin' y cache='no-store'. El servidor exige
  autenticación normal antes de comparar. URLs de revalidación y login se resuelven por Django
  en el layout; no derivar destinos de parámetros next ni del contenido de una respuesta.
- 204 sin redirección y URL final del mismo origen/pathname de revalidación: misma sesión;
  revelar DOM solo si la solicitud sigue vigente y la página tiene visibilidad/foco.
- 409: otra sesión o huella faltante; descartar DOM y navegar mediante replace al login.
- Redirección legítima al login: response.redirected === true, status === 200 y URL final con
  origen y pathname exactos del login propio. Admitir su query next como información, pero
  navegar con location.replace a la URL fija de login de Django. Mantener oculto mientras se navega.
- Un 200 sin redirección, un HTML que solo se parece a login o una redirección a otro destino
  no prueban sesión anónima: mantener oculto y permitir reintentar; no navegar a destinos arbitrarios.
- 5xx, timeout o fallo de red: mantener contenido oculto con mensaje general y botón de reintento.
No confundir un 200 de login seguido por fetch con sesión válida. No exponer huella por query string.
No permitir que una respuesta antigua de revalidación revele el DOM tras un evento posterior:
invalidar respuestas obsoletas mediante contador/cancelación, y comprobar visibilidad y foco
actuales. Solo una petición vigente; agrupar eventos duplicados. Un 200 reconocido como login
seguido navega al login fijo sin revelar DOM; un 200 inesperado, 403 u otro estado no reconocido
mantiene oculto y ofrece reintento. Ni error de red ni timeout validan sesión.
La vista no modifica ni renueva la sesión y no devuelve identidad, huella nueva ni datos sensibles.
La política de expiración y SESSION_SAVE_EVERY_REQUEST existentes no cambian.

Ocultar contenido sensible en pagehide, pérdida de foco y transición a hidden. Revalidar en
pageshow.persisted y al recuperar visibilidad/foco. Solo revelar al confirmar la misma sesión.
El ocultamiento debe incluir campos y navegación con identidad, sin quitar el control de reintento.
Montar la guardia y renderizar la huella solo para usuarios autenticados; login y registro
anónimo no consultan esta ruta ni entran en un ciclo de redirecciones. El context processor es
de solo lectura y comparte la función HMAC con la vista; el middleware solo aplica cabeceras.
No usar unload ni deshabilitar bfcache como única estrategia. Evitar reenvío de POST y recargas
que pierdan los campos de un formulario válido al cambiar de pestaña.

## Alcance visual acordado y aceptación

No hay difusión de logout ni refresco periódico en ventanas que permanecen visibles. Al volver,
actualizar, navegar o restaurar historial se exige sesión válida. Navegación real siempre pasa
por el servidor; restauración usa la guardia. Validar con y sin bfcache en navegador real con JS.
No prometer retirar información que una persona ya vio o una captura del navegador.
Las garantías del servidor siguen activas sin JS; la garantía visual de restauración requiere JS.

La matriz de ocho escenarios está en [plan.md](../plan.md). La guía ejecutable de comprobación,
incluidos CSRF, pestañas y errores de red, está en [quickstart.md](../quickstart.md).
