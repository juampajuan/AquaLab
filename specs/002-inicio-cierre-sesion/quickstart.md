# Guía de validación: SCRUM-42 / US 1.2

Esta guía se ejecutará después de implementar. Hoy no existen los nuevos endpoints/tests.
No se instalaron dependencias, ejecutaron migraciones ni iniciaron servicios en esta planificación.
Ver [contrato](contracts/sesion.md), [modelo](data-model.md) y [matriz de escenarios](plan.md).

## Preparación

Requisitos: Docker con Compose operativo, PostgreSQL 16 del proyecto, puertos disponibles y
`.env` local configurado desde `.env.example` con SECRET_KEY propia y DATABASE_URL válida.
No mostrar secretos en logs ni subir .env. Toda instalación y almacenamiento local nuevo debe
ubicarse en E: por preferencia del usuario; comprobar también la ubicación del disco de Docker
antes de instalarlo o descargar imágenes. No sustituir PostgreSQL por SQLite para validar.

Desde la raíz del repositorio, una vez habilitado el entorno:

```text
docker compose up -d --build
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
```

Crear por el flujo existente dos usuarios de prueba (A y B); aprobar A con el administrador,
dejar B pendiente. Usar datos ficticios. Crear un cliente de prueba para consultar el detalle.
No convertir a todos los usuarios en staff: un usuario aprobado común debe poder operar AquaLab.

## Verificación automatizada prevista

```text
docker compose exec web python manage.py check
docker compose exec web python manage.py makemigrations --check --dry-run
docker compose exec web pytest usuarios/tests clientes/tests
docker compose exec web pytest
docker compose exec web ruff check .
docker compose exec web ruff format --check .
```

Esperado: checks sin errores, sin migraciones nuevas requeridas, suite completa en verde, ruff
sin errores de lint ni formato. Si la suite dirigida pasa no omitir la completa, como exige CI.
No usar `--fix` ni generar migraciones como parte de la validación. Revisar failures antes de avanzar.

Antes de modificar fixtures o código, ejecutar la suite existente y controles con el entorno
preparado y registrar la línea base en tasks.md (T005). Después inventariar rutas (T004), preparar
fixtures (T003) y volver a ejecutar la suite existente para detectar regresiones de los fixtures.
Solo entonces redactar las pruebas nuevas. Conservar IDs históricos: el orden es
T001 → T002 → T005 → T004 → T003 → T006–T013.

Las pruebas nuevas deben incluir los ocho escenarios de plan.md y estas verificaciones:
- `Client(enforce_csrf_checks=True)` obtiene token real; POST sin token o incorrecto no cierra.
- Dos clientes comparten una cookie de sesión, uno cierra y el otro pierde acceso con esa misma
  cookie antigua. Un tercer cliente con otra sesión del mismo usuario sigue autenticado.
- Revalidación 204 con huella correcta, 409 con huella distinta/faltante y redirección sin sesión.
  Una huella conocida sin cookie no autentica. Cabeceras no-store también en respuestas de error.
- Authenticate/client.login de usuarios inactivos siguen devolviendo None/False; no relajar tests.
- Campos incompletos no llaman authenticate; pending incorrecto e inexistente muestran igual error;
  cuentas pendientes con password correcta jamás adquieren _auth_user_id.
- Correo con espacios/mayúsculas y Unicode admitido por el registro: igual valor normalizado en
  RegistroForm, formulario de login y manager, sin NFKC adicional. Registrar/confirmar/aprobar e
  ingresar con ese correo; no mapearlo a una cuenta distinta por normalización implícita.
- Contraseña con espacios exactos; next local/externo ignorado. En ambos endpoints de cierre,
  probar next en query y cuerpo, incluyendo ambos simultáneamente; destino fijo usuarios:login,
  sesión invalidada, GET 405 y CSRF inválido 403; resolve(reverse('admin:logout')) usa la vista común
  y usuarios no staff siguen sin acceder a pantallas administrativas.
- Registro, aprobación, confirmación/cancelación de clientes y duplicados mantienen comportamiento.
- Logout borra borradores pero no filas persistidas. GET logout no cambia sesión. POST válido
  repetido termina en login; token inválido sigue rechazado.

## Verificación de navegador (obligatoria para escenario 7)

Usar navegador de escritorio del laboratorio con JavaScript. Registrar nombre, versión, sistema,
fecha, commit y resultado; repetir en cada navegador que el equipo vaya a soportar. No inferir
compatibilidad universal a partir de una única ejecución. Verificar historial con bfcache cuando
esté disponible y con navegación que haga petición nueva, usando herramientas del navegador.

1. Anónimo: entrar al inicio, alta/confirmación/detalle de cliente y admin. No debe aparecer contenido
   protegido. Registro y login accesibles; admin conserva controles administrativos.
2. Ingresar como A; destino inicio y nombre correcto. Medir desde completar/usar el formulario hasta
   ver inicio: menos de 30 segundos. Login con sesión activa vuelve a inicio. next no cambia destino.
3. Probar vacío, inexistente, password incorrecta, B pendiente correcta/incorrecta. Comparar mensajes
   exactos del contrato y ausencia de sesión autenticada cuando corresponde.
4. Abrir dos pestañas de A y una sesión independiente (otro perfil) del mismo usuario. Completar
   parcialmente un formulario de clientes, cambiar de pestaña y volver sin cerrar: se mantienen
   valores y errores; la revalidación no reenvía POST ni crea clientes.
5. Cerrar desde la otra pestaña con el botón, sin diálogo extra. Al volver a la primera, contenido
   anterior oculto y login requerido. La sesión independiente permanece válida. No se exige que
   una ventana que sigue visible reciba ocultamiento automático mientras no se vuelva a ella.
6. Usar Atrás/Adelante, actualizar y pegar direcciones anteriores de inicio, revisión y detalle.
   No reaparece contenido sensible ni identidad anterior. Registrar si hubo restauración bfcache;
   no aceptar solo comprobar cabeceras. Repetir desde pantallas administrativas.
7. Tras cerrar A, ingresar como otro usuario aprobado en una pestaña y volver a una página vieja de
   A: no mostrar el DOM de A aunque exista una nueva sesión autenticada. Se descarta y pasa por login
   (que puede dirigir al inicio del nuevo usuario).
8. Ocultar una pestaña, desconectar red y volver: contenido oculto y posibilidad de reintento.
   Recuperar red: se muestra solo si continúa la misma sesión. Un 500 simulado no revela contenido.
9. Iniciar alta de usuario/cliente sin confirmar y cerrar sesión: al ingresar de nuevo no recuperar
   borradores anteriores; verificar que usuarios/clientes ya confirmados permanecen guardados.
10. Comprobar que el botón cierre funciona sin depender de JS; sin JS la protección del servidor
    sigue vigente, pero esta prueba no certifica el comportamiento visual de historial.

## Verificaciones de seguridad concretas de la revisión

Son comprobaciones previstas, no tareas generadas ni pruebas ejecutadas. S01–S06 y la parte de
servidor de S07–S09 se automatizan con pytest-django; la parte visual exige navegador real.

| ID | Caso | Resultado observable exigido |
|---|---|---|
| S01 (esc. 4/8) | Inexistente, activo incorrecto, pendiente incorrecto, pendiente correcto | Los tres primeros comparten HTTP/error/código y no revelan estado; solo el cuarto muestra pendiente; los cuatro carecen de autenticación |
| S02 (esc. 3/4/8) | Instrumentar backend y diagnóstico con spies sobre consulta y hasher real | Campos vacíos: ninguna llamada. Éxito: sin diagnóstico. Cada fallo: una consulta diagnóstica sin filtro is_active y una verificación real o ficticia, sin segundo authenticate ni hash ficticio duplicado |
| S03 (esc. 4/8) | Password inutilizable, hash no reconocido por Django, hash del mismo algoritmo con factor anterior | Rechazo genérico salvo pendiente con contraseña realmente correcta; usar rutas ficticias/compensación de Django, sin atajos nuevos por estado; diagnóstico sin setter ni escritura de hash |
| S04 (esc. 4/8) | Inyectar DatabaseError en backend y consulta diagnóstica | Respuesta general de operación sin excepción/SQL/correo/estado; no login, user_cache apto ni claves de autenticación; logs sin password, hash o cuerpo POST |
| S05 (esc. 1/8) | Ejecutar tests existentes US 1.1 sin debilitarlos | authenticate y client.login rechazan inactivos; aprobación permite ingresar; registro y confirmación/cancelación conservan sus reglas |
| S06 (esc. 6/7) | Revalidación con cookie vieja, otra sesión y huella conocida sin cookie | Cookie invalidada no accede; huella no autentica. Misma sesión: 204; otra clave/identidad: 409, incluso al volver a iniciar como el mismo usuario |
| S07 (esc. 5/7) | Petición a sesión y render de login/registro anónimo | Sin excepción pública en sesión; sin sesión nueva o renovación por revalidar; sin guardia/huella en páginas anónimas; GET de sesión no cambia expire_date ni contenido de sesión |
| S08 (esc. 7) | 204 retrasado/eventos duplicados y clasificación de respuestas | Solo 204 directo válido/vigente revela con foco/visibilidad. Redirección seguida con redirected=true, status=200 y origen/pathname exactos del login navega al login fijo; query next no modifica destino. 200 sin redirección, redirección a otro destino, 403, 5xx, timeout/red fallida mantienen oculto y permiten reintentar, sin paralelas ni bucles |
| S09 (esc. 6/7) | Navegar Atrás/Adelante y volver a pestaña con sesión igual/distinta | No destello de DOM antiguo tras logout; misma sesión conserva campos/errores; distinto usuario o nuevo login del mismo usuario descarta DOM; no reenviar POST |
| S10 (regresión US 2.1) | Alternar pestañas/foco en formulario y revisión de clientes | Con sesión válida conserva campos y errores; confirmar crea una sola fila, cancelar no crea y doble envío no duplica; logout elimina borrador pero conserva filas ya confirmadas |

Para S02/S03 usar el hasher predeterminado de producción en pruebas focalizadas. Contar trabajo de
encode/verify/harden_runtime, no solo invocaciones a un wrapper mockeado que no calcula hashes.
No fijar umbrales de milisegundos ni afirmar igualdad temporal universal. Las diferencias de
upgrades estándar deben identificarse separadamente de ramas añadidas por la aplicación.
Si aparecen hashers distintos en datos reales, elevar la limitación para revisión del equipo;
no cambiar el algoritmo ni agregar dependencias dentro de esta historia.

S08/S09 se prueban también desde admin, y recuperando foco desde barra de direcciones o un diálogo:
la guardia no debe dejar la página oculta permanentemente ni inutilizar formularios/autocompletado.
En registro anónimo, cambiar de pestaña no debe disparar login ni borrar los datos (US 1.1).

## Condiciones para avanzar

Antes de implementación: aprobación del equipo de la spec (actualmente Draft) y revisión de este
diseño. Las dos decisiones consultadas ya se registran en plan.md; no implican aprobación del resto.
Antes de merge: todas las pruebas, validación visual y CI en verde; aprobación de un integrante
no autor; PR vinculado a SCRUM-42, US 1.2 y su spec. Si la validación visual falla, corregir el diseño
antes de afirmar cumplimiento de FR-012/013; no reducir el criterio silenciosamente.
