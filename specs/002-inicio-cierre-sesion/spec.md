# Feature Specification: Inicio y cierre de sesión

**Feature Branch**: `002-inicio-cierre-sesion`

**Created**: 2026-10-18

**Status**: Draft

**Input**: User description: "SCRUM-42 / US 1.2 - Como usuario del sistema quiero iniciar sesión con mis credenciales y poder cerrarla al terminar para operar de forma segura en la plataforma y resguardar la información."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Iniciar y cerrar sesión (Priority: P1)

Como usuario del sistema, quiero iniciar sesión con mis credenciales y poder cerrarla al terminar para operar de forma segura en la plataforma y resguardar la información.

**Why this priority**: Es el acceso necesario para utilizar de forma segura todas las funciones protegidas del sistema.

**Independent Test**: Se puede probar con credenciales válidas e inválidas, intentando acceder a pantallas protegidas sin sesión y cerrando una sesión desde distintas pantallas; solamente una sesión válida debe permitir el acceso.

**Acceptance Scenarios**:

1. **Given** una cuenta activa y una persona sin sesión iniciada, **When** ingresa el usuario o correo y la contraseña correctos, **Then** el sistema inicia la sesión, muestra la pantalla principal e identifica a la persona por su nombre.
2. **Given** una persona que ya inició sesión, **When** intenta acceder nuevamente a la pantalla de inicio de sesión, **Then** el sistema la dirige a la pantalla principal.
3. **Given** el formulario de inicio de sesión, **When** falta el identificador o la contraseña, **Then** el sistema solicita completar ambos campos sin intentar el ingreso.
4. **Given** credenciales que no corresponden a una cuenta activa, **When** la persona intenta ingresar, **Then** el sistema no inicia sesión y muestra el mensaje genérico "Usuario o contraseña incorrectos".
5. **Given** una persona sin sesión, **When** solicita cualquier pantalla protegida, **Then** el sistema la redirige al inicio de sesión sin mostrar el contenido solicitado.
6. **Given** una persona con sesión activa en cualquier pantalla protegida, **When** elige cerrar sesión, **Then** el sistema finaliza la sesión y la redirige al inicio de sesión.
7. **Given** una sesión cerrada, **When** la persona usa Atrás, actualiza una página anterior o intenta reutilizar su dirección, **Then** el sistema no muestra contenido protegido y vuelve a exigir el inicio de sesión.

### Edge Cases

- Un identificador con espacios laterales se evalúa sin esos espacios; la contraseña se evalúa exactamente como fue ingresada.
- Una cuenta inexistente, una contraseña incorrecta y una cuenta no habilitada producen el mismo mensaje genérico.
- Abrir varias pestañas no mantiene acceso en ninguna de ellas después de cerrar la misma sesión.
- Repetir la acción de cerrar sesión no expone un error ni vuelve a habilitar la sesión anterior.
- Solicitar directamente una dirección protegida sin sesión nunca muestra parcialmente su contenido.
- Una falla al validar credenciales no deja a la persona identificada ni crea una sesión parcial.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: El sistema MUST ofrecer un formulario de inicio de sesión accesible a personas no autenticadas.
- **FR-002**: El sistema MUST solicitar el identificador de acceso y la contraseña.
- **FR-003**: El sistema MUST validar que ambos campos estén completos antes de intentar autenticar.
- **FR-004**: El sistema MUST permitir el ingreso únicamente cuando las credenciales correspondan a una cuenta activa.
- **FR-005**: El sistema MUST mostrar "Usuario o contraseña incorrectos" para cualquier combinación inválida, sin identificar el dato que falló ni confirmar la existencia de una cuenta.
- **FR-006**: El sistema MUST dirigir a la pantalla principal después de un ingreso correcto.
- **FR-007**: La pantalla principal MUST mostrar el nombre de la persona autenticada.
- **FR-008**: El sistema MUST exigir una sesión activa para todas las pantallas excepto registro e inicio de sesión.
- **FR-009**: El sistema MUST redirigir al inicio de sesión cualquier solicitud de una pantalla protegida realizada sin una sesión activa.
- **FR-010**: La opción de cerrar sesión MUST estar disponible desde toda pantalla protegida.
- **FR-011**: Al cerrar sesión, el sistema MUST invalidar la sesión y dirigir a la pantalla de inicio de sesión.
- **FR-012**: Después del cierre, el sistema MUST impedir el acceso a pantallas protegidas mediante Atrás, actualización o acceso directo a una dirección previamente visitada.
- **FR-013**: El cierre de una sesión MUST afectar todas las pestañas que utilicen esa misma sesión.
- **FR-014**: Esta feature MUST limitarse al inicio, protección de acceso y cierre de sesión; recuperación de contraseña, autenticación multifactor y administración de roles quedan fuera de alcance.

### Key Entities *(include if feature involves data)*

- **Usuario autenticable**: Cuenta activa creada por la US 1.1, identificada por usuario o correo y asociada al nombre que se muestra después del ingreso.
- **Sesión**: Estado temporal que representa que una persona fue autenticada y puede acceder a funciones protegidas hasta que cierre la sesión o esta deje de ser válida.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Una persona con credenciales válidas puede acceder a la pantalla principal en menos de 30 segundos.
- **SC-002**: El 100% de los intentos con campos vacíos o credenciales inválidas son rechazados sin crear una sesión.
- **SC-003**: El 100% de las pantallas protegidas redirigen al inicio de sesión cuando se solicitan sin una sesión activa.
- **SC-004**: El 100% de las sesiones cerradas dejan de permitir acceso mediante Atrás, actualización o direcciones previamente visitadas.
- **SC-005**: Al menos el 90% de usuarios representativos puede iniciar y cerrar sesión en el primer intento, sin asistencia externa.

## Assumptions

- Las cuentas y credenciales válidas provienen de la US 1.1.
- "Usuario/email" significa el mismo identificador elegido al registrar la cuenta.
- El criterio de Jira que menciona mostrar el rol se corrige para mostrar únicamente el nombre: los roles fueron retirados de la US 1.1 y no están definidos para el Sprint 1.
- Registro e inicio de sesión son las únicas pantallas públicas del alcance actual.
- El cierre invalida la sesión utilizada por todas las pestañas del mismo navegador; cerrar otras sesiones abiertas en otros dispositivos queda fuera de alcance.
- No se incluyen recuperación de contraseña, recordatorio de sesión, autenticación multifactor ni bloqueo por intentos fallidos.
