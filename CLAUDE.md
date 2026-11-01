# Notas para Claude Code — AquaLab

## Pendientes entre features

Cuando una feature resuelva un pendiente, borrar su línea.

- **Envío de informes (SCRUM-39):** el envío de informes por correo usa `Cliente.email`.

## Mensajes de commit

Conventional Commits en español, con la US en el mensaje: `tipo(ámbito): descripción`.

- Spec Kit: `docs(specs): spec de la US 3.2 – Editar cliente` (igual para `plan` y `tasks`).
- Código: `feat(<app>): US 3.2 – Editar cliente`; correcciones `fix(<app>): ...`.
- Infraestructura y configuración: `chore: ...`.

## Avisos por correo (US 1.3)

- Los avisos de `usuarios/notificaciones.py` se llaman explícitamente desde `registro_confirmar`,
  `UsuarioAdmin.aprobar_cuentas`, `UsuarioAdmin.save_model` y `UsuarioAdmin.rechazar_solicitudes`.
  No se usan señales: `queryset.update()` no las dispara.
- Siempre se agendan con `transaction.on_commit`; una falla de envío solo queda en el log
  `usuarios.notificaciones`. Rechazar elimina la cuenta pendiente para liberar el correo.
- En los tests: `django_capture_on_commit_callbacks(execute=True)` y `mailoutbox`.

## Autenticación integrada (US 1.2)

- Login/logout propios en usuarios; LOGIN_URL y ambos cierres llevan al login AquaLab.
- Se mantiene ModelBackend y aprobación mediante is_active. Diagnóstico de pendiente solo con
  contraseña correcta; decisiones en specs/002-inicio-cierre-sesion/research.md.
- Login y registro recibido ya incluyen los enlaces recíprocos; Registrar cliente está en navbar.
- La guardia de sesión comparte lógica entre layouts de AquaLab y admin; los permisos administrativos
  permanecen intactos. No exponer sessionid ni usar la huella HMAC como autorización.
- T027/navegador acreditada por reporte del usuario; T001/aprobación formal y T032 siguen pendientes. Consultar tasks.md antes de
  declarar cerrada la historia; implementación local autorizada por excepción documentada en plan.md.

## Registro de muestras (US 4.1)

- El N° PI lo asigna `muestras/servicios.py:registrar_muestra` (máximo + 1, desde 200001) bajo
  `pg_advisory_xact_lock`. No usar secuencias ni `AutoField`: dejan huecos ante un rollback.
- El origen nuevo se crea (o se reutiliza, sin distinguir mayúsculas) en la misma transacción que la
  muestra, después del lock; cancelar o fallar no deja orígenes huérfanos ni consume N° PI.
- Cada borrador lleva una `clave_borrador` (UUID, `unique` en `Muestra`); bajo el lock, si ya hay una
  muestra con esa clave se devuelve en vez de crear otra. Borrar el borrador de la sesión no alcanza:
  las sesiones de Django no se bloquean y dos confirmaciones simultáneas leen el mismo borrador.
- La ficha del cliente y sus orígenes se actualizan en vivo con
  `muestras/static/muestras/registro_muestra.js`; con un cliente ya elegido (errores o `?volver=1`)
  los renderiza el servidor. No hay buscador de clientes: se quitó tras la prueba manual.

## Consulta de estado del estudio y ficha de la muestra (US 5.2)

- `EstadoEstudio` (`pendiente_analisis`, `en_proceso`, `finalizado`, `informe_generado`) y
  `EstadoPruebaEstudio` (`pendiente`, `cargada`, `completada`) en `estudios/models.py`. Toda
  `PruebaEstudio` inicia en `pendiente`.
- Las vistas de consulta (`estudios:buscar`, `estudios:detalle` y `muestras:detalle`) muestran siempre
  `tipo_nombre_snapshot` y `tipo_descripcion_snapshot` para preservar la historia del estudio frente a
  ediciones posteriores del catálogo.

## Pruebas de un estudio (US 5.3 y US 5.4)

- `agregar_prueba` y `quitar_prueba` (`estudios/servicios.py`) bloquean la fila del estudio
  (`select_for_update`), no el advisory lock global de la creación; así `quitar_prueba` cuenta las
  asignaciones sin carreras y ningún estudio queda sin pruebas.
- `Estudio.admite_modificaciones` es la única regla de estudio modificable: la usan el detalle, la
  vista y el servicio (que la revalida bajo el bloqueo).
- Las vistas `agregar_prueba` y `quitar_prueba` tapan el nombre del servicio: llaman a
  `servicios.<nombre>` y en los tests se parchea `estudios.servicios.<nombre>`.
- Un reenvío de `confirmar` falla el formulario (la prueba ya no está entre las opciones); la vista
  lo detecta con `AgregarPruebaForm.prueba_ya_asignada()` y el servicio lo informa como aviso.
- Las pruebas agregadas nacen en estado Pendiente. Quitar borra la asignación (sin historial) y
  solo se permite si `PruebaEstudio.puede_quitarse()`, es decir, estado Pendiente.
- **Epic 6 (validación, US 6.4):** pasar la prueba a `Completada` al validar su resultado, con el
  estudio bloqueado como en `cargar_mediciones`, y referenciar `PruebaEstudio` con `PROTECT`.
- `motivo_para_no_quitar` es la única fuente de las reglas de quita: la usan la vista (GET) y el
  servicio. `.btn-chico` es el botón para filas de tablas.

## Carga de mediciones (US 6.1)

- `Medicion` es uno a uno con `PruebaEstudio` (`PROTECT`): una medición por prueba del estudio.
  Corregirla (US 6.3) actualiza esa fila; nunca se crea otra.
- El valor va en `numeric(18, 6)` y los decimales escritos en `decimales`; mostrarlo siempre con
  `Medicion.valor_ingresado` (conserva "7,20"). `leer_valor` (`estudios/mediciones.py`) es la única
  lectura del texto: coma o punto, sin miles ni notación científica, hasta 12 enteros y 6 decimales.
- `cargar_mediciones` (`estudios/servicios.py`) bloquea el estudio y después las asignaciones,
  el mismo orden que `quitar_prueba`. No falla por prueba: omite e informa las ya cargadas y las
  calculadas; los `pk` que no son del estudio los ignora y la vista cuenta las quitadas
  (`CargarMedicionesForm.pruebas_quitadas()`). Con la primera medición el estudio pasa a
  "En proceso" y deja de admitir agregar o quitar pruebas.
- `Estudio.admite_mediciones` (Pendiente de análisis o En proceso) es la regla de carga, como
  `admite_modificaciones`. Al confirmar, el formulario usa todas las asignaciones no calculadas
  (no solo las pendientes) para que el servicio informe las que ya se cargaron.
- La confirmación evita el doble envío con `data-enviado`, sin deshabilitar los botones: un botón
  deshabilitado no envía su `accion`.

## Cálculo de resultados (US 6.2)

- `pruebas/formulas.py` es la única forma de evaluar fórmulas: un analizador propio con `Decimal`
  (nunca `eval`, `ast` ni `float`) que acepta solo la gramática del catálogo. `Prueba.clean()` lo
  usa para validar fórmulas en el admin y en la importación.
- `Resultado` es uno a uno con `PruebaEstudio` (`PROTECT`), con 10 decimales y la unidad y la
  fórmula usadas (un cambio del catálogo no lo recalcula). Mostrarlo con `valor_mostrado` (hasta 4
  decimales) y las unidades con el filtro `|unidad` (`--` o vacío → «Sin unidad»).
- `calculo.recalcular(estudio, asignaciones)` exige el estudio bloqueado por el llamador y solo
  toca las cambiadas y sus dependientes, en orden de dependencia. El motivo de una prueba sin
  resultado no se guarda: lo da `calculo.motivo_sin_resultado`.
- Un recálculo deja el resultado en `Cargada` aunque estuviera `Completada` (excepción al
  principio IV, justificada en specs/016-calcular-resultado/plan.md). Con informe emitido
  (`Estudio.admite_correcciones`) no se cambia nada.
- `python manage.py calcular_resultados` completa los resultados de mediciones sin resultado
  (las cargadas antes de US 6.2); es idempotente.

## Corrección de mediciones (US 6.3)

- `servicios.corregir_mediciones` actualiza la misma fila de `Medicion` (`corregida_por`,
  `fecha_correccion`; sin historial de valores) y recalcula con `recalcular_resultados` en la misma
  transacción: si el recálculo se rechaza, también se deshace la corrección. Un estudio Finalizado
  al que le queda alguna prueba sin validar vuelve a En proceso.
- Concurrencia optimista: el formulario lleva `original_<pk>` (el valor que se vio al abrir).
  Bajo el bloqueo del estudio, si el vigente ya es el nuevo se omite con «ya tenía ese valor» y si
  difiere del original, con «cambió mientras se editaba». `CorregirMedicionesForm.cambios()`
  compara con el original, nunca con la base.
- `calculo.afectadas` es la única definición de pruebas afectadas por un cambio: la usan el aviso
  «Perderán la validación» y el recálculo.
- **Borrar (US 6.5):** va en el mismo envío con `nuevo = None` en `cambios`; las omisiones suman
  «ya no tenía medición». Al confirmar, el formulario incluye las asignaciones sin medición (las de
  `original_<pk>` del POST) para que un reenvío lo informe. No tiene reglas propias de cálculo:
  `calculo.descartar` deja sin resultado y en Pendiente a la borrada y a sus dependientes.
  `estado_tras_correccion` devuelve el estudio a Pendiente de análisis si no le queda ninguna
  prueba Cargada ni Completada.

## Catálogo de pruebas (SCRUM-64)

- `python manage.py importar_catalogo_pruebas` carga `pruebas/datos/catalogo_pruebas_agua.csv` y
  `pruebas/datos/limites_vertido.csv` (`pruebas/importacion.py`). Valida todo antes de escribir y
  guarda en una transacción: un error deja la base igual. Actualiza por código; nunca borra ni
  desactiva.
- Si una prueba en uso trae otro nombre en el archivo, conserva el guardado y lo informa como aviso.
- `Prueba.esta_en_uso()` (asignada a un tipo de estudio o a un estudio) es la regla de uso: el admin
  deja código y nombre de solo lectura y no permite borrarla; la importación no le cambia el nombre.
- Los límites son texto sin evaluar; las fórmulas (`x` = valor medido, `{CODIGO}` = otra prueba)
  se evalúan con `pruebas/formulas.py` (US 6.2). `referencias_formula` es la única forma de leer
  las referencias.
- **US 6.4:** convertir los límites a número para comparar resultados. Las 17 pruebas sin tipo en el
  sistema original quedaron DIRECTO y siguen a confirmar con el laboratorio (columna `observacion`).

## Pruebas Ausente/Presente (ajuste a US 6.1 y 6.3)

- Las pruebas con unidad «A/P» (E. coli, Pseudomonas) guardan la medición como 0 (Ausente) o 1
  (Presente): `estudios/mediciones.py` (`leer_valor(..., presencia=True)`, `texto_presencia`).
- En las plantillas se muestran con el filtro `valor_medicion` de `config/ui.py`, nunca el número.
  La US 6.4 interpreta los límites «Ausente»/«Ausencia» del catálogo sobre esos 0 y 1.
