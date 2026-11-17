# Contratos de interacción y emisión — US 10.2

Diseño futuro; las tres rutas POST de conclusión y los parámetros opcionales indicados **no existen actualmente**. Se conservan rutas, permisos, firma y confirmaciones actuales fuera de la función nueva. Ver [modelo](../data-model.md) y [redacción](redaccion-ia.md).

## Autorización y respuestas comunes

Proponer, guardar, aprobar y emitir **con** conclusión exigen sesión activa, grupo exacto `Bioquímicos` y permiso efectivo `informes.emitir_informes`, comprobados en backend y UI. No basta is_staff, Administradores, superusuario sin grupo o permiso directo sin grupo. Releer usuario/permisos sin cache obsoleta al entrar y al finalizar una propuesta externa. No agregar permisos ni conceder grupos. Aprobar no exige firma adicional; emitir conserva la firma/matrícula existentes.

Todos los POST tienen CSRF, no aceptan GET (405) y retornan datos privados no almacenables en caché. 403 por falta de política conjunta/CSRF, 404 por estudio inexistente, 400 por forma inválida, 409 por estudio no disponible/emitido, revisión o hechos obsoletos. La sesión sigue el middleware actual: puede redirigir a login; JS verifica redirección/tipo de contenido y nunca interpreta HTML de login como éxito JSON. Un fallo IA normalmente es éxito con plantilla y aviso, no error que bloquee emitir. Un conflicto posterior a IA es 409, no éxito con texto antiguo.

Las respuestas de éxito y conflicto incluyen la revisión actual, texto_editorial, texto_final, advertencias, huella_hechos, huella_texto de texto_final y estado real de aprobación; conflicto identifica su causa y preserva el texto local para revisión. No se aceptan hechos, identidad de aprobador ni aprobación afirmados por el cliente como autoridad.

## Superficie web

| Ruta y nombre | Entrada y comportamiento |
|---|---|
| GET existente `/informes/estudios/<pk>/vista-previa/` | Empleado autenticado conserva consulta. Solo el autorizado ve el editor y su borrador compartido. Sin fila, no crearla. Con fila y autorización, reconciliar fuentes bajo locks; puede materializar la invalidación derivada si cambió la huella. No escribe resultados, validaciones, aprobación positiva ni Informe. |
| POST nuevo `/informes/estudios/<pk>/conclusion/guardar/`, `informes:conclusion_guardar` | revision_esperada entero >=0, huella_hechos_vista y texto editorial. 0 solo crea si no hay fila. Reconciliar fuentes antes de comparar revisión; si cambian, 409 con revisión actual, sin pisar editorial. Guardar edición explícita invalida aprobación y propuesta en vuelo; materializar texto_final con advertencias canónicas, normalizar LF antes de devolver el texto exacto. |
| POST nuevo `/informes/estudios/<pk>/conclusion/proponer/`, `informes:conclusion_proponer` | revision_esperada y huella_hechos_vista; confirmación UI si reemplaza texto. Fase A bloqueada reserva token nuevo y limpia aprobación aun si el texto futuro coincide; conserva editorial anterior. Fuera de transacción llamar al adaptador. Fase B reautoriza, bloquea y compara token/revisión/huella; solo entonces instala propuesta o plantilla. |
| POST nuevo `/informes/estudios/<pk>/conclusion/aprobar/`, `informes:conclusion_aprobar` | revision_esperada, huella_hechos_vista, huella_texto_visto y confirmación expresa. Sin texto nuevo: primero debe guardarse y verse el texto_final confirmado. El servidor recalcula y coteja hashes, verifica fuentes y luego incrementa revisión y registra los seis campos de aprobación para esa revisión. Texto final vacío sin advertencias no es aprobable. |
| POST existente `/informes/estudios/<pk>/generar/` | Agregar opción incluir_conclusion, false por defecto, y revision_conclusion si true. Sin ella, flujo y permisos existentes, sin depender de borrador ni IA. Con ella, política conjunta, revisión exacta aprobada y fuentes vigentes dentro de la transacción de emisión. Si divergen: 409 sin emitir, sin descartar silenciosamente la conclusión ni aprobarla. El usuario conserva acción explícita de emitir sin conclusión. |

Antes del primer guardado/propuesta, la vista entrega revisión 0 y huella de hechos vigente. Los formularios usan JSON para las acciones nuevas; emisión mantiene su formulario/confirmación y respuestas HTML existentes, incluyendo error de conflicto sin Informe creado. Fechas ISO con zona y números de revisión enteros en transporte; escalares del snapshot clínico siempre strings. No cambiar destinatario, idempotencia ni confirmación de envío existente.

## Estado del editor y persistencia

La base es la autoridad compartida; no hay borrador exclusivo por usuario. Habilitar edición con confirmación explícita de conservar cambios automáticamente e invalidar aprobación al editar, según plan; proponer/reemplazar, aprobar y emitir conservan confirmaciones propias. Autosave serializado tras cambios y al abandonar mediante navegación controlada; proponer/aprobar/emitir y Volver esperan el último guardado confirmado. El primer input deshabilita usar aprobación previa. Un 409 nunca sobreescribe automáticamente otra pestaña ni restaura aprobación; presenta diferencias y requiere revisión/guardado explícito sobre la revisión nueva. Una respuesta de propuesta en vuelo se descarta si pierde token o revisión.

sessionStorage conserva solamente edición local aún no confirmada para recuperación por recarga, con clave de pestaña/estudio/usuario/huella de sesión existente. No guarda hechos, contactos ni credenciales y nunca autoriza una aprobación. Limpiar tras confirmación, logout mediante el formulario existente data-cerrar-sesion, cambio de sesión/usuario o pérdida de autorización detectada. No suponer eventos personalizados en usuarios/sesion.js: hoy no los expone; respetar data-sesion-guardia, ocultamiento/revalidación y respuestas de servidor. Sin confirmación de guardado se muestra pendiente/error: una pérdida forzada del navegador o almacenamiento deshabilitado no se presenta como persistencia compartida exitosa.

Las advertencias están fuera del textarea, visibles en texto_final y protegidas; se guardan y aprueban en ese mismo texto. Aprobar nunca elimina advertencias. Editar invalida; otra propuesta invalida incluso idéntica; cambio detectado de hechos invalida persistentemente, aunque después vuelvan a parecer iguales. No agregar vencimiento por tiempo. Puede emitir otro bioquímico autorizado: el snapshot conserva al aprobador original.

## Servicios y atomicidad

Responsabilidades nuevas: recolector `conclusion_hechos`, adaptador `conclusion_ia`, ciclo de vida/guardias `conclusiones`, formularios y vistas POST. La emisión existente se extiende de forma compatible: `emitir_informe(estudio_pk, usuario, *, incluir_conclusion=False, revision_conclusion=None)` y `armar_contenido(estudio, firmante=None, conclusion=None)`. Son interfaces propuestas, no firmas actuales. PDF y envío no reciben nuevos parámetros ni consultan borradores.

Orden uniforme de locks: Estudio → Borrador → asignaciones por pk → Prueba por pk; advisory de numeración existente después, únicamente al emitir. Crear el OneToOne ausente se serializa por Estudio. Consultas de locks separadas, sin outer join nullable. Recolectar resultados/vigentes con select_related/prefetch y evaluar una vez; cantidad de consultas independiente del número de pruebas. No llamar IA ni mantener transacción durante espera externa.

En emisión con conclusión, verificar y copiar hechos, texto final, aprobación y fragmento dentro de la misma transacción que crea Informe y cambia estado. Si se detecta obsolescencia, persistir invalidación derivada sin crear Informe y devolver conflicto; estructurar transacción para que la respuesta de conflicto no revierta esa invalidación con una excepción dentro de atomic. Las mismas reglas aplican a reconciliación que devuelve 409. Otros errores de emisión revierten la emisión completa. No aplicar locks o comprobaciones del borrador al camino sin conclusión.

## Salidas y compatibilidad

Una clave opcional `contenido.conclusion`, definida en data-model, contiene texto final exacto y trazabilidad autosuficiente. Si no hay conclusión aprobada elegida, omitir clave. Nunca backfill, regeneración, edición de emitidos ni lecturas de relaciones vivas para reconstruir la conclusión.

El parcial HTML nuevo `_conclusion.html` representa únicamente snapshot.texto escapado y conserva saltos con CSS; se comparte por documento.html, documento_impreso.html y correo HTML. Correo txt usa el mismo string, sin resumir ni agregar de nuevo advertencias. WeasyPrint/impresión y PDF adjunto siguen su flujo de copia existente. No usar safe sobre texto profesional ni IA. El bloque completo no debe forzarse a una sola página: permitir saltos y verificar conclusión extensa sin recorte. Ausencia de clave no produce título, bloque vacío ni cambios en informes históricos. Reenvío nunca llama IA ni actualiza la copia.
