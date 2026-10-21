# Modelo de datos: SCRUM-42 / US 1.2

## Usuario existente

Reutilizar `usuarios.Usuario` mediante `get_user_model()` / `AUTH_USER_MODEL`.
- `email`: identificador único; normalización strip/lower existente y constraint Lower(email).
- `first_name`, `last_name`: identificación visible mediante get_full_name en los layouts.
- `password`: hash gestionado por Django; jamás guardar el valor ingresado en sesión o HTML.
- `is_active`: False = pendiente; True = aprobada, según contrato vigente de US 1.1.
- `is_staff`, permisos: permanecen para administración; no son nuevos roles del dominio.
- `last_login`: actualización estándar de Django tras login correcto; no crear auditoría adicional.

No agregar campos, tablas ni migraciones. Una cuenta con contraseña inutilizable no puede ingresar.
El formulario normaliza correo pero nunca transforma la contraseña. Una validación diagnóstica
no cambia is_active ni crea usuario autenticado. Tampoco persiste cambios del hash: usa
check_password sin setter; las operaciones estándar previas de ModelBackend permanecen intactas.

## Sesión existente

Backend DB de Django, tabla django_session, con clave, datos serializados y vencimiento.
El login estándar gestiona rotación de clave y guarda `_auth_user_id`, `_auth_user_backend` y
`_auth_user_hash`. No manipular esas claves manualmente. Conservar la política de expiración
existente; no agregar «recordarme» ni tiempos de inactividad ajenos a la spec.

| Estado inicial | Evento | Resultado |
|---|---|---|
| Anónimo, con o sin borrador | Credenciales aprobadas válidas | Sesión autenticada y destino inicio |
| Anónimo | Campos vacíos o credenciales inválidas | Sigue anónimo, errores; no login |
| Anónimo | Pendiente y contraseña correcta | Sigue anónimo, mensaje específico |
| Pendiente | Administrador aprueba | Usuario activo; podrá iniciar una sesión nueva |
| Autenticado | POST logout con CSRF válido | Flush de la sesión, usuario anónimo y destino login |
| Autenticado | GET logout o CSRF inválido | Sin cierre por esa petición |
| Sesión invalidada | Solicitud protegida con cookie anterior | Sin acceso; redirección al login (o rechazo CSRF en POST inválido) |
| Otra sesión independiente | Logout de la primera | Permanece válida según política existente |

Una sesión anónima ya utilizada por registro o mensajes puede seguir existiendo al fallar un login;
«sin crear sesión» en SC-002 se verifica como ausencia de autenticación y de una nueva sesión de
login, no eliminación del borrador anónimo preexistente. No crear sesiones de autenticación parciales.

## Datos transitorios y datos persistidos

Logout descarta `registro_pendiente`, `cliente_pendiente`, `ultimo_cliente_creado_id` y cualquier
otro contenido de esa sesión. No guardar para recuperarlo después de iniciar como otra persona.
Los usuarios y clientes confirmados permanecen intactos. No afecta otras sesiones de otros
navegadores o dispositivos, aunque pertenezcan al mismo Usuario.

## Huella de revalidación (derivada, no entidad persistida)

HMAC del contexto de sesión autenticada actual (identidad y session_key), con salt exclusivo de
la funcionalidad y SECRET_KEY. Se entrega como atributo de datos de HTML protegido y vuelve en
la cabecera `X-AquaLab-Sesion` del GET de revalidación, no en URL ni almacenamiento local.
No es un token de autenticación; sin cookie/sesión válida no permite acceder. Solo detecta que
el DOM pertenece a la misma sesión. Comparar mediante las utilidades de comparación segura Django.
Misma clave e identidad producen la misma huella; rotar la clave o cerrar e iniciar sesión de
nuevo cambia la huella incluso para el mismo usuario y obliga a descartar el DOM viejo.
Generarla solo para una sesión autenticada con clave existente, sin crear datos de sesión.
Una sola función compartida sirve al context processor y a la vista; el middleware solo pone cabeceras. No compartirla entre
usuarios ni reutilizarla como identificador público. No guardar huella, password o sessionid en logs.

## Estado del navegador

Visible-validado → oculto al abandonar/ocultar/perder foco → revalidando al regresar →
visible-validado si 204, o navegación a login si anónimo/diferente.
Falla de red → oculto con reintento; nunca mostrar por defecto. Conservar los valores del formulario
en DOM solo cuando la revalidación confirma la misma sesión. El servidor es la autoridad de acceso.
