# Contrato UI: Registro de usuario

**Feature**: `001-registrar-usuario` | **Plan**: [../plan.md](../plan.md)

Pantallas renderizadas en el servidor con templates de Django + Bootstrap 5.3, extendiendo
`base.html`. Todas son públicas (`@login_not_required`) y todos los formularios llevan
`{% csrf_token %}`. Prefijo de URLs: `/usuarios/` (namespace `usuarios`).

## Rutas

| Nombre de URL | Método | Ruta | Resultado |
|---|---|---|---|
| `usuarios:registro` | GET | `/usuarios/registro/` | Formulario vacío, o precargado (sin contraseña) si hay `registro_pendiente` en la sesión |
| `usuarios:registro` | POST | `/usuarios/registro/` | Válido → guarda en sesión y **302** a `usuarios:registro_confirmar`. Inválido → **200** con errores junto a cada campo |
| `usuarios:registro_confirmar` | GET | `/usuarios/registro/confirmar/` | Resumen para revisar. Sin datos en sesión → **302** a `usuarios:registro` |
| `usuarios:registro_confirmar` | POST `accion=confirmar` | `/usuarios/registro/confirmar/` | Crea la cuenta pendiente → **302** a `usuarios:registro_recibido` con mensaje de éxito |
| `usuarios:registro_confirmar` | POST `accion=cancelar` | `/usuarios/registro/confirmar/` | Borra los datos de la sesión, no crea nada → **302** a `usuarios:registro` con mensaje "Registro cancelado." |
| `usuarios:registro_recibido` | GET | `/usuarios/registro/recibido/` | Página de resultado que muestra los mensajes |

"Volver y editar" es un link (GET) a `usuarios:registro`: los datos quedan en la sesión y se
precargan.

## Pantalla 1 — Formulario de registro

| Campo (`name`) | Etiqueta | Widget | Obligatorio |
|---|---|---|---|
| `first_name` | Nombre | texto | Sí |
| `last_name` | Apellido | texto | Sí |
| `email` | Correo electrónico | email | Sí |
| `password1` | Contraseña | password (no re-renderiza valor) | Sí |
| `password2` | Repetir contraseña | password (no re-renderiza valor) | Sí |

Botón: **Continuar** (no guarda; lleva a la revisión).

Mensajes de error (junto al campo, con `is-invalid` de Bootstrap):

| Caso | Mensaje |
|---|---|
| Campo vacío | "Este campo es obligatorio." (mensaje estándar de Django en español) |
| Email con formato inválido | "Introduzca una dirección de correo electrónico válida." (estándar de Django) |
| Email ya registrado (cualquier mayúscula/espacio, cuenta pendiente o aprobada) | "Este correo no está disponible." |
| Contraseñas distintas | Mensaje estándar de `BaseUserCreationForm` |
| Contraseña débil | Mensajes de `AUTH_PASSWORD_VALIDATORS` |

Reglas:
- Los valores válidos de nombre, apellido y correo se conservan al mostrar errores (FR-007).
- La contraseña ingresada nunca aparece en el HTML de respuesta ni en los mensajes (FR-014).
- No se crea ningún `Usuario` desde esta pantalla.

## Pantalla 2 — Revisión y confirmación

Muestra: Nombre, Apellido, Correo electrónico. **No** muestra la contraseña ni una máscara de ella.

Texto de aviso: "Revisá tus datos. Al confirmar, tu cuenta quedará pendiente de aprobación por un
administrador."

Acciones:

| Acción | Elemento | Efecto |
|---|---|---|
| Confirmar | `<button name="accion" value="confirmar">` en form POST | Crea la cuenta. El botón se deshabilita al enviar |
| Volver y editar | link GET a `usuarios:registro` | Vuelve al formulario con nombre, apellido y correo precargados; la contraseña se reingresa |
| Cancelar | `<button name="accion" value="cancelar">` en form POST | Descarta los datos sin crear la cuenta |

Comportamiento del POST `confirmar`:

| Situación | Respuesta |
|---|---|
| Datos en sesión y correo disponible | Crea `Usuario(is_active=False)`, borra la sesión de registro, 302 a `registro_recibido` + mensaje de éxito |
| Sin datos en sesión (confirmación repetida después del éxito) | 302 a `registro_recibido`, no crea nada |
| El correo ya existe al confirmar (tomado por otra solicitud o por una confirmación simultánea) | No crea una segunda cuenta; 302 a `registro` con error "Este correo no está disponible." |
| Error de base de datos | 200 con la revisión y el mensaje "No se pudo completar el registro. Intentá nuevamente." |

## Pantalla 3 — Registro recibido

Muestra los mensajes del framework de mensajes. Mensaje de éxito:

> "Registro recibido. Vas a poder ingresar cuando un administrador apruebe tu cuenta."

Si se accede directo sin mensajes, muestra un texto neutro con un link a `usuarios:registro`.
(Cuando exista la US 1.2, se agrega un link a "Iniciar sesión".)
