# Notas para Claude Code — AquaLab

## Pendientes entre features

Cuando una feature resuelva un pendiente, borrar su línea. Por ahora no hay pendientes.

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
- Correos con logo: `config/correos.py:armar_correo` arma un `CorreoAquaLab` con el texto plano de
  siempre y una alternativa HTML (extiende `templates/correos/base.html`, estilos inline) con
  `static/img/marca/aqualab-horizontal.png` inline por `cid:logo-aqualab` en un
  `multipart/related`; el logo no entra en `attachments`. Lo usan la aprobación de cuenta, el
  envío del informe y el aviso de desvíos; las plantillas `*_cuerpo.html` van junto a las `.txt`.
  En los tests, `config/tests/utiles_correos.py:comprobar_html_con_logo` y, para simular una falla,
  parchear `config.correos.CorreoAquaLab.send`.

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
- Los límites se interpretan solo con `pruebas/limites.py` (US 6.4). Las 17 pruebas sin tipo en el
  sistema original quedaron DIRECTO y siguen a confirmar con el laboratorio (columna `observacion`).

## Pruebas Ausente/Presente (ajuste a US 6.1 y 6.3)

- Las pruebas con unidad «A/P» (E. coli, Pseudomonas) guardan la medición como 0 (Ausente) o 1
  (Presente): `estudios/mediciones.py` (`leer_valor(..., presencia=True)`, `texto_presencia`).
- En las plantillas se muestran con el filtro `valor_medicion` de `config/ui.py`, nunca el número.
  La US 6.4 interpreta los límites «Ausente»/«Ausencia» del catálogo sobre esos 0 y 1.

## Validación de resultados (US 6.4)

- `pruebas/limites.py` es la única interpretación de los límites del catálogo: `leer_limite`
  (número, «Ausente»/«Ausencia», vacío o no comparable), `limites_aplicables` (los del vertido de
  la muestra reemplazan a los generales completos) y `evaluar` (cumple / fuera de norma / sin
  límite comparable; bordes inclusivos; compara el valor completo, no el redondeado). Con
  «Ausente»/«Ausencia» cumple el 0 y todo valor por debajo del límite de detección (US 7.2).
- `Validacion` guarda quién, cuándo, los límites usados y la evaluación. Invariante: hay una
  vigente (`anulada=False`) si y solo si la prueba está Completada. Al salir de Completada,
  `calculo.cambiar_estado` la anula (`anulada`, `fecha_anulacion`); nunca se borra (FR-017).
  Mostrar siempre la vigente (`views.validaciones_vigentes()` + `evaluar_asignaciones`).
- `servicios.validar_resultados` revalida el permiso `estudios.validar_resultados`, bloquea el
  estudio y después las pruebas, omite «ya estaba validada», «ya no tenía resultado» y «cambió
  mientras se revisaba» (`resultado_<pk>` lleva `str(resultado.valor)`), y es el único que pasa el
  estudio a Finalizado. La vuelta a En proceso sigue en `estado_tras_correccion`.
- El grupo «Bioquímicos» lo crea la migración `estudios.0008`. Los tests con `transaction=True`
  vacían la base: el fixture `bioquimico` crea el grupo si falta.
- Cloruro (CL-) es fórmula `x*10`: en los tests, una medición de 40 da un resultado de 400 mg/l.

## Control previo al informe (US 7.1)

- App `informes` (sin modelos todavía): `informes:listar`, `informes:control` e `informes:generar`.
- `informes/servicios.py:motivo_para_no_informar` es la única regla para informar (100% de las
  pruebas Completadas y sin informe emitido): la usan el control y `comprobar_generacion`; el filtro
  «Solo listos» de `estudios_para_informar` la repite en SQL y un test compara las dos.
- `estudio_listo_bloqueado` bloquea el estudio (`select_for_update`) y revalida; lo usan
  `comprobar_generacion` y la emisión de la US 7.2 (ver «Generar informe»).
- `estudios/busqueda.py:filtro_busqueda` es la única búsqueda de estudios (`estudios:buscar` e
  `informes:listar`). Los tests de `informes` importan las fixtures de `estudios/tests/conftest.py`.

## Generar informe (US 7.2)

- `informes/contenido.py:armar_contenido` arma el informe (laboratorio, cliente, muestra, estudio
  y pruebas) solo con textos, sin `float`. Lo usan la vista previa y la emisión, y el parcial
  `informes/documento.html` lo dibuja en los dos casos: el emitido sale igual a lo revisado.
- `Informe.contenido` (`JSONField`) guarda esa copia; `informes:ver` muestra siempre la copia, no
  los datos actuales. Es inalterable: ver «Consultar y exportar informe».
- `servicios.emitir_informe`: permiso `informes.emitir_informes` → `estudio_listo_bloqueado` →
  `pg_advisory_xact_lock(7_200_001)` → número máximo + 1 (sin huecos, como el N° PI) →
  `Informe` → estudio «Informe generado». La migración `informes.0002` da el permiso al grupo
  «Bioquímicos»; el fixture `bioquimico` también lo agrega.
- Las evaluaciones del informe salen de la `Validacion` vigente; sin validación (el atajo
  `completar` de los tests) se evalúa con el catálogo. «< LD» y «Ausente»/«Presente» los decide
  `texto_resultado`.
- Los datos del laboratorio son de ejemplo en `settings.AQUALAB_LABORATORIO`; `logo` es una
  referencia («aqualab» → marca de AquaLab) que se copia al informe.

## Historial del cliente (US 3.3)

- `clientes/historial.py:muestras_del_historial` es la única consulta del historial: pagina muestras
  (`-fecha_ingreso`, `-numero_pi`) y trae los estudios con `Prefetch` en `estudios_historial`
  (`-pk`, con `informe` en `select_related`), así los estudios de una muestra no se cortan entre
  páginas y no hay N+1. El filtro de estado se aplica a las muestras y al prefetch.
- «Ver informe» se decide con `{% if estudio.informe %}` (el `Informe` ya traído), no por el estado.
  El tipo se muestra con `tipo_nombre_snapshot`.
- `clientes:historial` es de solo lectura (`require_GET`) y rechaza clientes inactivos como la ficha.
  «Limpiar filtros» depende de los parámetros recibidos, válidos o no (`hay_filtros` en la vista).
- Los imports de `muestras`, `estudios` e `informes` van en `historial.py`, `views.py` y `forms.py`,
  nunca en `clientes/models.py`. Tests con los fixtures `muestra_de` y `estudio_en`
  (`clientes/tests/conftest.py`).

## Consultar y exportar informe (US 7.3)

- `informes/busqueda.py:informes_emitidos` es la única búsqueda de informes (`informes:emitidos`):
  busca en la copia (`KT()` sobre `contenido`), no en el cliente ni la muestra actuales.
- PDF (`informes/pdf.py`, WeasyPrint 70.0) e impresión (`informes:imprimir`) usan el mismo
  `informes/impreso.html` + `static/css/informe.css`, siempre desde `informe.contenido`. La hoja
  A4 es CSS propio sin Tailwind (CSS 2.1 + Paged Media) y no se compila. WeasyPrint necesita
  `FontConfiguration` para cargar Inter. Las librerías de sistema (Pango) van iguales en el
  `Dockerfile` y en el CI.
- La firma (`FirmaProfesional`) se guarda en la base como PNG (Render borra los archivos), validado
  solo por `informes/firmas.py:leer_firma` (≤ 64 KB, ≤ 1200 × 400 px). La dibuja `firma.js` (Pointer
  Events, sin librerías) en `informes:mi_firma`, solo con `informes.emitir_informes`.
- La matrícula se escribe solo con la primera firma (SCRUM-81): después `FirmaForm` deshabilita el
  campo (ignora lo enviado) y Mi firma la muestra como texto. Se corrige solo en el admin
  (`informes/admin.py`, que no crea ni borra firmas ni cambia la imagen).
- `emitir_informe` exige la firma y la copia en `contenido["firma"]` (nombre, matrícula, imagen);
  los informes anteriores no la tienen y salen con «Sin firma registrada». `informes/firma.html`
  es el bloque compartido por pantalla e impreso.
- `Informe.save()` sobre uno existente y `Informe.delete()` lanzan `ValueError`; no hay admin de
  informes. En los tests, cambiar un informe con `Informe.objects.filter(...).update(...)`.
- Tests: `bioquimico` ya tiene firma («MP 1234»), `bioquimico_sin_firma` no; `firma_de(usuario)`
  crea una. `informes/tests/utiles.py:png()` arma PNG válidos sin Pillow.

## Ayuda en formularios (US 9.1)

- `templates/ui/ayuda.html` es el único componente de ayuda (ícono + `role="tooltip"`); también lo
  usan la columna «Medición», Mi firma y las búsquedas. `ui/campo.html` lo dibuja si hay
  `help_text`, al lado del `<label>`/`<legend>` (nunca adentro).
- El tooltip lleva el id `<auto_id>_helptext`, al que Django 5.2 ya apunta con `aria-describedby`
  (junto con `<auto_id>_error`). En los radios Django no lo pone: `ui/campo.html` lo pone en el
  `<fieldset>`.
- El tooltip explica qué significa el campo; las instrucciones van visibles: `ayuda_visible=True`
  (requisitos de contraseña) e `instruccion="…"` (Ctrl/Cmd en tipos de estudio), que el filtro
  `describir` (`config/ui.py`) suma al `aria-describedby`.
- Los textos van en los formularios (`help_text=` o `Meta.help_texts`), nunca en los modelos:
  generan una migración y se verían en el admin, que no cambia.
- El CSS la muestra con `:hover` y `:has(:focus-visible)` (no `:focus-within`: tras un clic quedaría
  abierta). `static/js/aqualab.js` suma el toque (`data-abierta`), Escape (`data-cerrada`) y una sola
  abierta. Pasar del ícono al texto no la cierra (WCAG 1.4.13): `pointerout` con `relatedTarget`
  dentro de la misma `.ayuda` y el puente `.ayuda-texto::before`; solo el mouse la cierra al salir.
- El JS se prueba con `node --test usuarios/tests/js config/tests/js estudios/tests/js` (DOM
  simulado, sin dependencias), también en el CI.

## Datos de demo (SCRUM-78)

- `python manage.py cargar_demo` (solo con `AQUALAB_ENTORNO=desarrollo` y `DEBUG`) carga 6 meses de
  actividad con los servicios reales; el guion fijo (clientes, orígenes, valores, estado destino) está
  en `estudios/demo.py`. Reemplazó a `cargar_demo_us51`; sus tipos de estudio no se llaman igual que los
  de la demo vieja para no chocar en las bases del equipo.
- Cada paso corre dentro de `demo.reloj(fecha)`, que parchea `timezone.now` para que las fechas
  automáticas nazcan en el pasado. Nunca corregir fechas con `update()` después de crear: modificaría
  validaciones e informes emitidos (principio IV).
- Lo demo se reconoce por el correo `@demo.aqualab`; si ya hay un cliente así, no carga nada. Todo va
  en una transacción con `pg_advisory_xact_lock(7_800_001)`.
- Se suma a los datos existentes sin modificarlos: para cargarla no hace falta `docker compose down -v`
  (borra la base local). Si choca un usuario o un tipo demo, se rechaza sin cambios y lo informa.
- Casos para el dashboard: desvío de Cloruro en «Pozo 2» (~120 → 415 validado → 430 sin validar, para
  8.1 y 8.2), «Pozo domiciliario» del mes anterior estancado y «Escuela N° 12» Finalizado sin informe
  (alertas de 8.3). Si una historia necesita otro caso, agregarlo al guion y a `test_demo.py`.

## Panel del laboratorio (US 8.3)

- `informes/tablero.py` es la única fuente de los cálculos del dashboard (`informes:dashboard`):
  `periodo` (este mes, mes anterior, 3 y 6 meses, con su período anterior), `indicadores`,
  `tiempo_respuesta` (días corridos ingreso → emisión, `Decimal` a 1 decimal), `serie_mensual` (6
  meses), `serie_semanal` (12 semanas lunes–domingo) y `alertas`. Todas reciben `hoy`/`ahora` y
  cuentan en la zona del laboratorio (`TruncDate`/`TruncMonth`/`TruncWeek` con `tzinfo`).
- «Este mes» se compara con los mismos días del mes anterior. `variacion` decide el tono: subir es
  favorable salvo en el tiempo de respuesta; el template siempre muestra flecha y signo.
- Alertas: «sin avanzar» = Pendiente de análisis o En proceso cuya última actividad (creación, carga,
  corrección o validación) tiene más de 7 días; borrar una medición no deja fecha y no cuenta.
  «Finalizados sin informe» cuenta días desde la última validación vigente.
- Permiso `informes.ver_dashboard` (migración `informes.0004` → «Bioquímicos» y «Administradores»;
  el superusuario lo tiene por ser superusuario). El fixture `bioquimico` también lo agrega.
- Chart.js 4.4.7 está en `static/vendor/chart.umd.min.js` (sin CDN) y se carga solo en el dashboard
  y en la comparación histórica (US 8.1);
  `informes/static/informes/dashboard.js` lee `json_script` `datos-dashboard`. Cada gráfico tiene su
  tabla «Ver datos». La sección «Desvíos sin revisar» es de la US 8.2 (ver «Desvíos»).

## Comparación histórica por origen (US 8.1)

- `estudios/comparacion.py` es la única fuente del historial y de la variación (`comparar`,
  `variacion`, `franja`, `pruebas_disponibles`); la US 8.2 la reutiliza. No escribe nada.
- Historial = resultados de asignaciones Completadas (⇔ validación vigente) de muestras del origen,
  sin el estudio de referencia, ordenados por `(fecha_muestreo, numero_pi, estudio)`. «Último» = el
  del estudio de referencia (validado o no) o el validado más reciente; «anteriores» = validados de
  muestras previas a la del último, con la misma unidad (otra unidad: en la tabla, fuera del cálculo);
  `HistorialPrueba.anteriores` los expone para la US 8.2.
- Todo en `Decimal` sobre el valor completo; porcentaje a 0,1 `ROUND_HALF_UP`, base 0 → sin
  porcentaje. A/P: cambio de estado y «Presente en X de N», sin números. Sin tono «favorable»: el
  rojo solo marca un último resultado fuera de norma.
- La franja usa `limites_aplicables` con el vertido de la muestra de referencia; cada punto de la
  tabla muestra la evaluación de su validación vigente.
- `estudios:comparacion` es GET de solo lectura con el permiso `informes.ver_dashboard`: `?estudio=`
  (manda sobre `origen`) o `?cliente=&origen=` (`ElegirOrigenForm`, también en el dashboard), más
  `pruebas` + `elegir=1` (`ElegirPruebasForm`). Nada de esto va al informe, al PDF ni al correo.
- Chart.js sin plugins: franja con datasets constantes y `fill`, eje X de categorías. Las funciones
  puras de `estudios/static/estudios/comparacion.js` y `elegir_origen.js` se prueban con Node.
- Caso A/P de la demo: Tanque domiciliario (E. Coli Presente en el mes 3). Tests con la fábrica
  `estudio_en_origen` (`estudios/tests/conftest.py`).

## Desvíos (US 8.2)

- `estudios/desvios.py` es la única regla y detección (`regla`, `es_desvio`, `mediana`, `detectar`,
  `evaluar_estudio`, `pendientes`). El desvío **no se guarda**: se calcula al vuelo sobre los
  resultados Cargados (detalle, validación y «Desvíos sin revisar»), así una carga o corrección se
  refleja sola. Es de solo lectura; no crear un modelo de desvíos.
- Regla: con al menos N anteriores, desvío si el resultado difiere en más del umbral (%) de la
  **mediana** de los últimos N (no el promedio: un pico aislado no la mueve; ver Detergentes de
  Colectora en la spec). Comparación sin dividir: exactamente el umbral no es desvío. Umbral y N
  solo en `settings.AQUALAB_DESVIOS` (un test verifica que nadie más lo lea).
- Historial = `comparacion.comparar` + `HistorialPrueba.anteriores[-N:]`; diferencia y porcentaje
  con `comparacion.cambio`. A/P: desvío si los últimos N coinciden y el resultado es el otro estado;
  la referencia es ese valor común.
- **Validar es revisar**: no hay pantalla aparte. `ValidarResultadosForm` suma `observacion_<pk>`
  solo en filas con desvío sin revisar; `validar_resultados(..., observaciones)` reevalúa bajo el
  bloqueo y guarda `Validacion.observacion`, `desvio_referencia` y `desvio_umbral` (constancia;
  `CheckConstraint`: ambos o ninguno). Una corrección posterior anula la validación con su
  constancia y la prueba vuelve a evaluarse.
- `estudios:desvios` (lista paginada) y la sección del dashboard: permiso `informes.ver_dashboard`;
  «Validar» solo con `estudios.validar_resultados`. Una evaluación (6 consultas) por estudio con
  resultados sin validar. Nada de esto va al informe, al PDF ni al correo.
- Aviso por correo: `estudios/notificaciones.py`. `calculo.recalcular` compara con los valores
  previos y llama a `avisar_desvios` solo con las pruebas de valor nuevo o distinto (no reenvía);
  evalúa con `desvios`, agenda `transaction.on_commit` y manda un correo por desvío y por
  bioquímico activo, cada uno con un solo destinatario en «Para» (nadie ve a los otros; una falla
  no corta a los demás) (`estudios/correos/desvio_*.txt`). Enlace absoluto con
  `settings.AQUALAB_URL_BASE` (no hay `request`); fallas al logger `estudios.notificaciones`. La
  demo también genera estos correos. Tests: `mailoutbox` + `django_capture_on_commit_callbacks`.
- Demo: Pozo 2 mes 0 (430 contra mediana 124) es el único pendiente; el mes 1 (415) quedó validado
  con observación (`OBSERVACIONES` en `estudios/demo.py`). Tests: `estudios/tests/test_desvios*.py`.

## Panel de calidad (US 8.4)

- `informes/calidad.py` es la única fuente de la sección «Calidad» del dashboard (`calidad.armar`,
  que la vista suma al contexto y a `datos_graficos`). Recibe el `Periodo` de `tablero.periodo`
  (no lo recalcula); `tablero.py` no se toca. Solo lectura, 7 consultas fijas.
- Cuenta solo validaciones vigentes (`anulada=False`) por `fecha_validacion` en la zona del
  laboratorio, con la `evaluacion` guardada: nunca evalúa con `pruebas/limites.py` (de ahí solo
  `Evaluacion`; un test lo verifica). «Sin límite comparable» se muestra aparte, fuera del %.
- `MINIMO_EVALUADOS_RANKING` (5) y `TOPE_LISTA` (10) solo en `calidad.py`; el template usa
  `{{ calidad.minimo_ranking }}`. Porcentajes con `calidad.porcentaje` (`Decimal`, 1 decimal,
  `ROUND_HALF_UP`); el orden usa la fracción exacta (`Conteo.fraccion`), no el redondeado.
- La variación del indicador va en puntos porcentuales («▲ +5,0 p. p.», subir es desfavorable)
  con `tablero.variacion`. Vertidos: siempre Agua, Cloacal y Canal (`TipoVertido.choices`).
- Clientes y orígenes enlazan al historial (3.3) y a la comparación (8.1); con el cliente
  inactivo, «Inactivo» y sin enlace (esas vistas los rechazan).
- Tests: el fixture `evaluadas` (`informes/tests/conftest.py`) crea validaciones con la evaluación
  elegida sin cargar ni validar; para el flujo real, `estudio_en_origen`. Con la demo el ranking se
  verifica con «Últimos 6 meses» (con «Este mes» solo pH llega a 5).

## Filtrar estudios (SCRUM-74)

- `estudios.forms.FiltrosEstudioForm` es la única definición de los filtros `desde`/`hasta`/`estado`
  (mensajes, regla desde ≤ hasta, `is-invalid`): la heredan `HistorialClienteForm` (solo cambia las
  etiquetas) y `FiltrarEstudiosForm` de `estudios:buscar`. `BuscarEstudioForm` sigue solo con `q`
  porque lo usa `informes:listar`.
- `estudios/busqueda.py:filtro_estado_fechas` cuenta los días de `fecha_creacion` en la zona del
  laboratorio: `>= inicio_del_dia(desde)` y `< inicio_del_dia(hasta + 1)`. No usar `__date`.
- Con cualquier valor inválido (también el texto) `estudios:buscar` muestra el error y el listado
  completo sin filtrar, como el historial. La paginación lleva `parametros` (GET sin `page`) y
  «Limpiar filtros» depende de los parámetros recibidos (`hay_filtros`), válidos o no.

## Envío del informe por correo (SCRUM-79)

- `informes/envios.py:enviar_informe` es el único envío (lo llama `informes:enviar` al confirmar):
  sincrónico, con el PDF de `generar_pdf` adjunto y destino el `Cliente.email` vigente (no la copia
  de `contenido`). El texto del correo sale de `contenido` (`informes/correos/`), sin enlaces.
- `EnvioInforme` es inalterable como `Informe` (`save`/`delete` lanzan `ValueError`, sin admin); en
  los tests, cambiarlo con `filter(...).update(...)`. Se crea una sola vez, con el resultado ya
  conocido.
- Un envío por confirmación: la pantalla lleva una `clave` (UUID, `unique`) y el servicio la busca
  bajo `select_for_update()` del `Informe` (que no se modifica). Una falla de correo o de PDF queda
  como «fallido» y en el logger `informes.envios`; nunca da una página de error.
- Permiso `informes.emitir_informes`, en la vista (403) y en el servicio. En los tests, parchear
  `informes.envios.generar_pdf`; para un empleado sin permiso usar `cliente_comun`
  (`informes/tests/conftest.py`): el usuario de `cliente_http` es el mismo que `bioquimico`.

## Gestión del catálogo (SCRUM-73)

- `pruebas/gestion.py:gestionar_prueba` es la única escritura del catálogo desde la app (crear,
  editar, desactivar, reactivar, eliminar): revalida el permiso del panel (`autorizar_administracion`),
  bloquea la prueba (`select_for_update`), compara `version` y registra `creada_por`/`modificada_por`
  con fecha. Las pantallas (`catalogo:*`, `pruebas/views.py`) confirman con un borrador firmado
  (`pruebas/confirmaciones.py`, como los tipos de estudio). El admin de Django queda como respaldo.
- En uso (`esta_en_uso()`): solo se cambian límites, norma, LD y observación; `PruebaForm` con
  `bloquear_metodo` ignora lo enviado. Sin uso: se edita todo, salvo el código si otra fórmula la
  nombra (`dependientes`). Eliminar solo sin uso, sin referencias y sin haber reemplazado a otra.
- Límites en la app: solo número, «Ausente» o «Ausencia» (`gestion.es_limite_valido`, mín ≤ máx); el
  CSV de importación no pasa por esta regla. «Ausente» es «no detectado» (A/P); un conteo usa máx 0.
- `activa`: los estudios nuevos (`catalogo.configuracion_bloqueada`), agregar prueba y los tipos
  (solo para pruebas nuevas en el tipo) usan solo activas. Desactivar o reactivar sube la `version`
  de los tipos que la tienen, así una confirmación vieja de crear estudio se rechaza.
- Reemplazo en cascada (al desactivar, «Reemplazar por» una activa con la misma unidad que no
  dependa de ella): reescribe `{VIEJA}` → `{NUEVA}` en las fórmulas dependientes, cambia la prueba en
  los tipos (sube su versión) y guarda `reemplazada_por`. Los estudios viejos no se tocan:
  `calculo.alias`/`referencias_en_estudio` resuelven el código nuevo a la prueba del estudio
  (cadenas A→B→C incluidas).
- Tests: fixtures `administrador_catalogo`, `cliente_catalogo` y `datos_prueba`
  (`pruebas/tests/conftest.py`, que importa las de `estudios`).
