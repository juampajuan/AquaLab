# Research: Envío del informe por correo

**Feature**: `029-enviar-informe` | **Plan**: [plan.md](./plan.md)

No había `NEEDS CLARIFICATION`: el alcance lo decidió el autor (spec → Input). Estas son las
decisiones técnicas.

## R1. Envío sincrónico desde la confirmación

- **Decision**: El envío ocurre en el POST de la confirmación, dentro del request, con
  `django.core.mail.EmailMessage` y el PDF adjunto (`attach(f"{numero}.pdf", pdf, "application/pdf")`).
  El tiempo máximo lo acota `EMAIL_TIMEOUT` (10 s, ya configurado).
- **Rationale**: Es una acción manual y el usuario necesita saber en el momento si salió (FR-008,
  SC-003). Sin colas ni dependencias nuevas (principio II).
- **Alternatives considered**: `transaction.on_commit` como en la US 1.3 (sirve para avisos
  secundarios, pero el resultado no llegaría a la pantalla ni al historial); Celery u otra cola
  (dependencia nueva sin necesidad).

## R2. Un solo envío por confirmación (FR-010)

- **Decision**: La pantalla de confirmación lleva un campo oculto `clave` (UUID nuevo en cada GET).
  `EnvioInforme.clave` es `unique`. El servicio bloquea la fila del `Informe` con
  `select_for_update()` y, bajo ese bloqueo, si ya existe un envío con esa clave lo devuelve sin
  volver a enviar (como `clave_borrador` de la US 4.1). Además el botón se deshabilita al enviar
  (patrón `onsubmit` de las confirmaciones).
- **Rationale**: El bloqueo serializa dos POST simultáneos del mismo informe; el segundo encuentra
  la clave ya registrada. `Informe` nunca se actualiza (es inalterable), así que bloquear su fila
  solo frena otros envíos de ese mismo informe, no la consulta ni la descarga.
- **Riesgo aceptado**: si el correo sale y la transacción falla al guardar el registro (por ejemplo,
  la base se cae en ese instante), el cliente recibe el correo sin que quede en el historial. Es poco
  probable y no tiene arreglo sin un sistema de mensajería transaccional (fuera de alcance).
- **Alternatives considered**: Guardar primero un envío «en curso» y actualizarlo después (suma un
  tercer estado visible si el proceso se corta); solo deshabilitar el botón (no cubre reenvíos ni
  pestañas duplicadas).

## R3. Modelo `EnvioInforme`, inalterable

- **Decision**: Modelo nuevo en `informes` (ver [data-model.md](./data-model.md)). Como `Informe`,
  `save()` sobre uno existente y `delete()` lanzan `ValueError`, y no tiene admin (FR-005). El FK al
  informe es `PROTECT`.
- **Rationale**: El historial es la prueba de qué se mandó y a quién; no debe poder editarse
  (principio IV). Un solo `save()` por registro: el servicio arma el registro con el resultado ya
  conocido.

## R4. Destinatario y contenido del correo

- **Decision**: Destino = `informe.estudio.muestra.cliente.email` leído al confirmar (la ficha
  actual, no la copia de `contenido`). El texto del correo sale de `informe.contenido` (número,
  N° PI, nombre de la muestra, número y tipo de estudio, nombre del cliente y del laboratorio), con
  plantillas `informes/correos/informe_asunto.txt` e `informe_cuerpo.txt` (texto plano, como la
  US 1.3). Sin enlaces a la aplicación (FR-004: requerirían sesión). Remitente
  `DEFAULT_FROM_EMAIL`.
- **Rationale**: Spec → Edge cases (correo cambiado) y FR-004. Usar la copia para el texto mantiene
  el correo coherente con el PDF adjunto.

## R5. PDF adjunto idéntico al descargable (SC-004)

- **Decision**: El adjunto se genera con `informes.pdf.generar_pdf(informe)`, la misma función que
  usa `informes:pdf`. Una falla al generarlo se trata como envío fallido (R6).
- **Rationale**: Una sola fuente del PDF. WeasyPrint agrega la fecha de creación en los metadatos,
  así que «idéntico» se verifica en los tests como «misma función, misma copia»: se parchea
  `generar_pdf` y se compara el adjunto con lo que devolvió.

## R6. Fallas: registro, mensaje y log

- **Decision**: Cualquier excepción al generar el PDF o al enviar (`EmailMessage.send(fail_silently=False)`)
  se captura en el servicio: se guarda el envío con `resultado = fallido`, se registra con
  `logger.exception` en el logger nuevo `informes.envios` (agregado a `LOGGING`) y la vista muestra
  «No se pudo enviar el informe a {correo}. Intentá nuevamente.». Un error de base (`DatabaseError`)
  muestra «No se pudo registrar el envío. Intentá nuevamente.».
- **Rationale**: FR-008 y SC-003; mismo criterio que la US 1.3 (la falla de correo nunca rompe la
  operación).

## R7. Permiso

- **Decision**: `informes.emitir_informes` (ya lo tienen «Bioquímicos», migración `informes.0002`).
  La vista lleva `@permission_required(..., raise_exception=True)` (403) y el servicio lo revalida
  (`PermissionDenied`), como `emitir_informe`. La pantalla del informe muestra el botón solo con
  `perms.informes.emitir_informes`. Ver el historial: cualquier empleado con sesión (como ver el
  informe).
- **Rationale**: Decisión del autor; sin migración de permisos.

## R8. Pantallas

- **Decision**: `informes:enviar` (`/informes/estudios/<pk>/informe/enviar/`): GET muestra la
  confirmación (aviso, resumen con informe, cliente, correo y último envío exitoso, botones
  «Enviar informe» y «Cancelar» → informe); POST envía y redirige a `informes:ver` con el mensaje.
  Template propio como `estudios/quitar_prueba_confirmar.html`, porque `ui/acciones_confirmacion.html`
  no lleva campos ocultos extra. `informes/ver.html` suma el botón y la sección «Envíos por correo».
- **Rationale**: Patrón de confirmación común (sección Interfaz de la constitution); cancelar no
  hace POST (no hay nada que descartar).
