---

description: "Lista de tareas de la US 10.3 (SCRUM-85) – Iniciar un estudio desde el asistente"
---

# Tasks: Iniciar un estudio desde el asistente

**Input**: `specs/040-iniciar-estudio-asistente/` (`plan.md`, `spec.md`, `research.md`,
`data-model.md`, `contracts/herramientas.md`, `contracts/enlaces-precargados.md`, `quickstart.md`)

**Prerequisites**: `main` con el asistente de la US 10.1 (`asistente/`: `herramientas.registrar`,
`Salida`, `puede_ver`, `enlaces.Referencia`, `conversacion.responder`, `VERBOS_DE_CAMBIO`), el
registro de muestra (US 4.1: `muestras.forms.RegistroMuestraForm`, `muestras.views.registrar`,
`registrar_confirmar`, `mensaje_exito_muestra`, `armar_resumen`, `muestras.servicios.
registrar_muestra`), crear estudio (US 5.1: `estudios.forms.CrearEstudioForm`,
`estudios.views.crear`) y la búsqueda de clientes (`clientes.views.buscar_clientes`). Fixtures:
`servicio_simulado`, `herramienta`, `texto`, `ejecutar`, `lacteos` (`asistente/tests/conftest.py`);
`empleado`, `cliente_a`, `muestra`, `tipo`, `tipo_inactivo`, `cliente_http`
(`estudios/tests/conftest.py`).

**Tests**: SÍ (constitution, principio III). Se escriben **antes** de la implementación de cada
historia y deben fallar primero. Ningún test llama a Groq: se usa `servicio_simulado` con
respuestas guionadas (`herramienta("preparar_muestra", {...})`, `texto("...")`).

**Organization**: por historia de la spec: US1 (P1, registrar una muestra con su estudio), US2
(P1, estudio para una muestra existente), US3 (P2, datos que no coinciden) y US4 (P2, abandonar
sin dejar nada).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: se puede hacer en paralelo (archivos distintos, sin dependencias pendientes)
- **[Story]**: historia a la que pertenece (`[US1]` a `[US4]`)
- Rutas relativas a la raíz del repo

## Convenciones para todas las tareas

- Textos en **español**, copiados **literalmente** de `contracts/`.
- **El asistente no escribe** (FR-006): `preparar_*` corren con `herramientas.ejecutar`, dentro de
  la transacción `READ ONLY` que siempre se deshace. No se toca la sesión desde el asistente.
- **Lista blanca** (R9): hacia el modelo, del cliente solo `nombre_completo` (y `activo`); del
  origen y del tipo, solo `nombre`. Nunca `email`, `telefono`, `domicilio`, `numero_documento` ni
  `tipo_documento`.
- **Una sola regla por cosa**: clientes con `buscar_clientes`; tipos con
  `TipoEstudio.objects.filter(activo=True)`; fechas, orígenes y la regla muestreo ≤ ingreso con
  `RegistroMuestraForm`; saneo GET con `valores_iniciales` / `valores_iniciales_estudio`.
- Comparaciones de nombres con `asistente.enlaces.normalizar` (sin acentos ni mayúsculas).
- Comandos en Docker: `docker compose exec web pytest …`, `docker compose exec web ruff check .`,
  `docker compose exec web ruff format --check .`.

---

## Phase 1: Setup

- [ ] T001 Verificar la base: `docker compose exec web pytest asistente muestras estudios -q` y
  `node --test asistente/tests/js` pasan en la rama antes de empezar; anotar el resultado en el PR.

---

## Phase 2: Foundational (bloquea todas las historias)

**Objetivo**: referencias sin pk, opciones sin pantalla, lectura de fechas y el pase de los
pedidos de registro por el corte de verbos.

### Tests

- [ ] T002 [P] Tests de `leer_fecha(texto, hoy)` en `asistente/tests/test_fechas.py` con `hoy =
  date(2026, 11, 17)`: «hoy» → 17/11/2026, «ayer» → 16/11, «anteayer» → 15/11, «12/11» →
  12/11/2026, «12/11/2025», «2026-11-12», «12 de noviembre», «3 de marzo de 2025», mayúsculas y
  acentos («Hoy», «Ayer.»); «el martes», «xx», «31/02», «» → `None`.
- [ ] T003 [P] Tests de `Referencia` en `asistente/tests/test_enlaces.py`: `Referencia(
  "registrar_muestra", None, "Revisar y registrar la muestra", parametros=(("cliente", "3"),
  ("fecha_muestreo", "2026-11-16")), minimizar=True).enlace()` →
  `{"etiqueta": …, "url": "/muestras/registrar/?cliente=3&fecha_muestreo=2026-11-16",
  "minimizar": True}`; `Referencia("opcion", None, "Pozo 2", pregunta="El origen es Pozo 2")
  .enlace()` → sin la clave `url`; dos opciones con distinta `pregunta` no se toman como
  duplicadas en `sin_duplicados`; las de la 10.1 siguen igual (tipo desconocido → `ValueError`).
- [ ] T004 [P] Tests de `es_pedido_de_registro` y del corte en
  `asistente/tests/test_conversacion_registro.py`: «Registrá una muestra de…», «Creá un estudio
  para el PI 200417», «cargá una muestra…», «Por favor, registrá un estudio…» **no** se cortan
  (se llama a `cliente_ia.enviar`); «Registrá el cliente Juan Pérez» → `MENSAJE_ALTA_CLIENTE` con
  un enlace a `clientes:registrar`, sin llamar al servicio; «Validá el estudio 42», «Borrá la
  muestra», «Cargá el pH» (sin «muestra» ni «estudio») → `MENSAJE_SOLO_CONSULTA` como en la 10.1.

### Implementación

- [ ] T005 [P] Crear `asistente/fechas.py` con `leer_fecha(texto, hoy) -> date | None` (R4):
  normaliza con `enlaces.normalizar`, quita puntuación final; «hoy»/«ayer»/«anteayer»;
  `d/m[/aaaa]` (sin año → `hoy.year`); `aaaa-mm-dd`; «d de <mes>[ de aaaa]» con los 12 meses en
  español. Fecha imposible → `None`. No valida futuro ni orden (eso lo hace el formulario).
- [ ] T006 [P] Ampliar `asistente/enlaces.py` (R7, data-model): `VISTAS` suma
  `"registrar_muestra": "muestras:registrar"`, `"crear_estudio": "estudios:crear"`,
  `"registrar_cliente": "clientes:registrar"` y `"opcion": None`; `Referencia.pk` admite `None`;
  campos nuevos `parametros: tuple = ()` y `minimizar: bool = False`; `url()` → `None` para
  `opcion`, `reverse` sin `args` si `pk is None` y `?` + `urlencode(parametros)` si hay; `enlace()`
  omite `url` si es `None` y agrega `"minimizar": True` si corresponde; `clave` →
  `(tipo, pk, parametros, pregunta)`. `posicion` no cambia.
- [ ] T007 En `asistente/conversacion.py` (R2): `VERBOS_DE_REGISTRO = {"registra", "crea",
  "agrega", "carga"}`; `es_pedido_de_registro(pregunta)` (empieza con uno de esos verbos y el texto
  normalizado contiene «muestra» o «estudio»); `es_alta_de_cliente(pregunta)` (verbo de registro +
  «cliente», sin «muestra» ni «estudio»). En `responder`: si es alta de cliente →
  `Respuesta(MENSAJE_ALTA_CLIENTE, [Referencia("registrar_cliente", None, "Registrar cliente")
  .enlace()])`; si es pedido de cambio y no de registro → `MENSAJE_SOLO_CONSULTA`. Actualizar
  `MENSAJE_SOLO_CONSULTA` y agregar `MENSAJE_ALTA_CLIENTE` con los textos literales de
  `contracts/herramientas.md`. Ampliar `MENSAJE_SISTEMA`: «También preparás el registro de una
  muestra (preparar_muestra) o de un estudio para una muestra existente (preparar_estudio): llamá
  la herramienta en cada mensaje con todos los datos dichos hasta ahora en la conversación, tal
  como los dijo el empleado (las fechas en sus palabras: «ayer», «12/11»); preguntá solo lo que
  la herramienta diga que falta, de a un dato; si hay opciones, pedí que elijan sin repetirlas.
  No digas que la muestra o el estudio quedaron creados: se crean cuando el empleado confirma en
  el formulario. No cargás mediciones, no validás ni das de alta clientes.»
- [ ] T008 En `static/js/aqualab.js` (`asistenteEnlaces`): una opción sin `url` se dibuja solo como
  botón `[data-asistente-elegir]`, sin el ↗; un enlace con `minimizar` se dibuja como
  `<a class="btn btn-primario btn-chico" data-asistente-minimizar-al-seguir>`, y al hacer clic
  minimiza el panel con la misma función del «–» (la conversación queda en `sessionStorage`)
  antes de navegar. Tests en `asistente/tests/js/asistente.test.cjs`: opción sin URL no tiene
  `<a>`; el enlace con `minimizar` deja el estado minimizado guardado y conserva los mensajes.

**Checkpoint**: la 10.1 sigue pasando completa (`pytest asistente`, `node --test
asistente/tests/js`).

---

## Phase 3: User Story 1 – Registrar una muestra con su estudio (P1) 🎯 MVP

**Objetivo**: del pedido del ejemplo al formulario de registro precargado y, tras confirmar, a
«Crear el estudio <tipo>».

**Prueba independiente**: quickstart pasos 1 a 4.

### Tests

- [ ] T009 [P] [US1] Tests de precarga en `muestras/tests/test_precarga.py`
  (`contracts/enlaces-precargados.md`): GET `muestras:registrar` con `cliente`, `origen`,
  `fecha_muestreo=2026-11-16`, `fecha_ingreso=2026-11-17`, `sitio_extraccion`, `tipo_vertido=
  cloacal`, `nombre`, `responsable_muestreo` y `tipo_estudio` → el HTML muestra cada valor
  (fechas como «16/11/2026»), el cliente elegido con su ficha y sus orígenes dibujados por el
  servidor, el `<input type="hidden" name="tipo_estudio">` y la nota «Después de registrar la
  muestra se ofrecerá crear el estudio «<tipo>».»; con `origen_nuevo=Pozo 3` el campo «Origen
  nuevo» viene completo; el GET no crea nada (conteos de `Muestra` y `Origen` iguales); un GET con
  parámetros borra el borrador de la sesión salvo con `volver=1`, donde gana el borrador.
- [ ] T010 [P] [US1] Tests del flujo con tipo en `muestras/tests/test_precarga.py`: POST del
  formulario con `tipo_estudio=<pk activo>` → el borrador de la sesión tiene `tipo_estudio`; la
  confirmación muestra la nota; al confirmar, el mensaje de éxito es el de siempre más «Crear el
  estudio <tipo>» con `href` a `estudios:crear?muestra=<pk>&tipo=<pk>`; con el tipo desactivado
  entre el formulario y la confirmación, el mensaje es el de siempre; sin `tipo_estudio`, igual que
  hoy; un borrador viejo sin la clave `tipo_estudio` se confirma sin error.
- [ ] T011 [P] [US1] Tests de crear estudio precargado en `estudios/tests/test_crear_precarga.py`:
  GET `estudios:crear?muestra=<pk>&tipo=<pk>` → ambos seleccionados; con `volver=<clave>` gana el
  borrador; el GET no crea `Estudio`.
- [ ] T012 [P] [US1] Tests de `preparar_muestra` en `asistente/tests/test_registro.py` con
  `ejecutar(empleado, "preparar_muestra", …)` y datos como los de `lacteos` (cliente «Lácteos del
  Sur S.A.», origen «Pozo 2», tipo activo): (a) cliente + origen + tipo sin fechas → `listo:
  false`, `faltan: ["fecha de muestreo", "fecha de ingreso"]`, `resuelto` con los tres nombres;
  (b) con `fecha_muestreo: "ayer"`, `fecha_ingreso: "hoy"` (fecha fija parcheando
  `django.utils.timezone.localdate`; no hay freezegun) → `listo: true`, `primeras[0]` es `registrar_muestra` con los
  parámetros del contrato y `minimizar`, y el aviso fijo «La muestra se registra recién cuando
  confirmes en el formulario.»; (c) «pozo 2» en minúsculas resuelve «Pozo 2»; (d) sin tipo →
  `elegir: "tipo_estudio"` y la primera opción es «Solo registrar la muestra»; con `solo_muestra:
  true` → `listo` y el enlace sin `tipo_estudio`; (e) fecha de muestreo posterior al ingreso o
  futura → `problemas` con el mensaje de `RegistroMuestraForm`, sin enlace; (f) fecha ilegible →
  `faltan` con «fecha de muestreo (no entendí «…»)»; (g) `sitio_extraccion` y `tipo_vertido`
  dichos viajan en el enlace; (h) el JSON de `datos` no contiene el email, el teléfono, el
  domicilio ni el documento del cliente.
- [ ] T013 [P] [US1] Test de conversación del ejemplo en
  `asistente/tests/test_conversacion_registro.py` con `servicio_simulado`: mensaje 1 «Registrá una
  muestra de Lácteos del Sur, pozo 2, para un físico-químico básico» → guion con
  `preparar_muestra` y un texto que pregunta las fechas; mensaje 2 «la tomaron ayer, llegó hoy»
  (con el historial) → `preparar_muestra` con todo y el texto final; la respuesta trae primero el
  enlace «Revisar y registrar la muestra» y el aviso fijo, en ≤ 3 mensajes del empleado (SC-001).

### Implementación

- [ ] T014 [US1] En `muestras/forms.py`: `valores_iniciales(query_dict) -> dict`, que sanea cada
  parámetro según `contracts/enlaces-precargados.md` («cliente» activo; «origen» del cliente;
  «origen_nuevo» ≤ 150 y solo sin un origen válido; fechas `aaaa-mm-dd`; «sitio_extraccion» ≤ 200;
  «tipo_vertido» en `TipoVertido.values`; «nombre» ≤ 100; «responsable_muestreo» ≤ 150;
  «tipo_estudio» activo) y descarta lo inválido en silencio. Campo nuevo `tipo_estudio =
  forms.ModelChoiceField(queryset=TipoEstudio.objects.filter(activo=True), required=False,
  widget=forms.HiddenInput)`, con `clean_tipo_estudio` que convierte un valor inválido en `None`
  sin error (sobrescribir `to_python`/capturar `ValidationError`). `datos_para_sesion` suma
  `"tipo_estudio": pk | None`. Propiedad `tipo_estudio_elegido` para la nota.
- [ ] T015 [US1] En `muestras/views.py`: `registrar` (GET sin `volver=1`) arma
  `RegistroMuestraForm(initial=valores_iniciales(request.GET))` si hay parámetros, después de
  descartar el borrador como hoy; con `volver=1` suma `tipo_estudio` del borrador al `initial`.
  `mensaje_exito_muestra(muestra, tipo=None)` agrega « <a href="…">Crear el estudio {tipo}</a>.»
  con `format_html` cuando `tipo` está activo; `registrar_confirmar` lo pasa desde
  `datos.get("tipo_estudio")` (también en la rama `CLAVE_ULTIMO_PI`, sin tipo). `armar_resumen`
  agrega `tipo_estudio` (nombre o `None`).
- [ ] T016 [US1] Plantillas `muestras/templates/muestras/registro_form.html` y
  `registro_confirmar.html`: el campo oculto y la nota «Después de registrar la muestra se ofrecerá
  crear el estudio «<tipo>».» con el estilo de aviso informativo existente (`ui/mensajes.html` o
  la clase de alerta `info`), solo si hay tipo.
- [ ] T017 [US1] En `estudios/forms.py`: `valores_iniciales_estudio(query_dict) -> dict | None`
  («muestra» como hoy; «tipo» solo si es un `TipoEstudio` activo). En `estudios/views.py:crear`,
  en lugar del `initial = {"muestra": …}` actual, usar esa función cuando no hay borrador.
- [ ] T018 [US1] Crear `asistente/registro.py` (contracts/herramientas.md, R3): helpers
  `resolver_cliente(texto)`, `resolver_origen(cliente, texto, nuevo)`, `resolver_tipo(texto)` que
  devuelven `(valor, problema, opciones)`; `PedidoMuestra` (dataclass del data-model) con
  `faltan`, `problemas`, `elegir`, `listo`; validación con `RegistroMuestraForm(data=…)` tomando
  solo los errores de `cliente`, `origen`, `origen_nuevo`, `fecha_muestreo` y `fecha_ingreso`;
  `@registrar` de `preparar_muestra` con la definición literal del contrato (todos los argumentos
  opcionales, tipos JSON del contrato). Con `listo`: `primeras=[Referencia("registrar_muestra",
  None, "Revisar y registrar la muestra", parametros=…, minimizar=True)]` y el aviso fijo. Las
  opciones de tipo con «Solo registrar la muestra» **primero**. Respetar `puede_ver(usuario,
  "registro")`. Importar `asistente.registro` al final de `asistente/herramientas.py` para que
  registre sus herramientas.
- [ ] T019 [US1] En `asistente/herramientas.py:puede_ver`: el tipo `"registro"` exige lo mismo que
  hoy `muestras:registrar` y `estudios:crear` (usuario autenticado y activo; R8), con un comentario
  que diga que si esas pantallas suman un permiso hay que agregarlo acá.

**Checkpoint**: T009–T013 pasan; quickstart pasos 1 a 4 a mano con Groq.

---

## Phase 4: User Story 2 – Estudio para una muestra existente (P1)

**Objetivo**: «Creá un estudio X para el PI N» → enlace a crear estudio precargado.

**Prueba independiente**: quickstart paso 5.

### Tests

- [ ] T020 [P] [US2] Tests de `preparar_estudio` en `asistente/tests/test_registro.py`: N° PI
  existente + tipo activo → `listo`, `primeras` con `crear_estudio` (`?muestra=<pk>&tipo=<pk>`,
  «Revisar y crear el estudio», `minimizar`) y la referencia a la ficha de la muestra; sin tipo →
  `faltan: ["tipo de estudio"]`, `elegir: "tipo_estudio"` con las opciones de tipos activos (sin
  «Solo registrar la muestra»); sin N° PI → `faltan: ["N° PI de la muestra"]`; `resuelto.muestra`
  sin datos de contacto.
- [ ] T021 [P] [US2] Test de conversación en `asistente/tests/test_conversacion_registro.py`: «Creá
  un bacteriológico para el PI <n>» → guion con `preparar_estudio` → respuesta con «Revisar y
  crear el estudio» primero; seguir el enlace con `cliente_http` muestra muestra y tipo
  seleccionados y no hay `Estudio` nuevo.

### Implementación

- [ ] T022 [US2] En `asistente/registro.py`: `PedidoEstudio` y `@registrar` de `preparar_estudio`
  (definición literal del contrato; `numero_pi` integer y `tipo_estudio` string, ambos
  opcionales), con la muestra buscada por N° PI (rango `0 < n ≤ MAX_NUMERO_SQL`, como
  `buscar_muestra`) y `referencia_muestra` de `herramientas.py`.

**Checkpoint**: T020–T021 pasan.

---

## Phase 5: User Story 3 – Datos que no coinciden (P2)

**Objetivo**: avisar y ofrecer las opciones que sí existen.

**Prueba independiente**: quickstart pasos 6 y 9.

### Tests

- [ ] T023 [P] [US3] Tests en `asistente/tests/test_registro.py`: cliente inexistente →
  `problemas: ["No hay ningún cliente activo que coincida con «Acme»."]`, `primeras` con
  `registrar_cliente`, sin enlace de registro; cliente solo inactivo → problema que dice que
  está inactivo; varios activos («Lácteos») → `elegir: "cliente"` con opciones «El cliente es
  <nombre>» (botón + ↗ a la ficha), ≤ 10; nombre exacto entre varios parecidos → se resuelve sin
  preguntar; origen inexistente («pozo 9») → `elegir: "origen"` con los orígenes del cliente y,
  **al final**, «Registrarlo como origen nuevo» con pregunta «Registrar «pozo 9» como origen
  nuevo»; con `origen_nuevo: true` → `resuelto.origen` «pozo 9 (origen nuevo)» y el enlace con
  `origen_nuevo=pozo 9`; varios orígenes parecidos → opciones; tipo inactivo (`tipo_inactivo`) →
  problema «El tipo «…» no está activo.» y opciones de tipos activos parecidos o todos (≤ 10); N°
  PI inexistente → «No hay ninguna muestra con el N° PI ….», sin opciones ni enlace; con el
  cliente sin resolver no se busca el origen.
- [ ] T024 [P] [US3] Tests de saneo en `muestras/tests/test_precarga.py` y
  `estudios/tests/test_crear_precarga.py`: `?cliente=999999`, cliente inactivo, `origen` de otro
  cliente, `fecha_muestreo=xx`, `tipo_vertido=nada`, `nombre` de 101 caracteres,
  `tipo_estudio=<inactivo>`, `tipo=<inactivo>`, valores no numéricos → 200 con esos campos sin
  precargar y sin errores de formulario; un POST con `tipo_estudio=<inactivo>` no muestra error y
  deja `tipo_estudio: None` en el borrador.

### Implementación

- [ ] T025 [US3] Completar en `asistente/registro.py` los textos de `problemas` y las opciones del
  contrato para cliente, origen, tipo y N° PI (si T018 o T022 no los cubrieron), con `MAX_LISTA =
  10` y orden: clientes por `Cliente._meta.ordering`, orígenes por nombre, tipos por nombre.

**Checkpoint**: T023–T024 pasan.

---

## Phase 6: User Story 4 – Abandonar sin dejar nada (P2)

**Prueba independiente**: quickstart paso 8.

- [ ] T026 [P] [US4] Test en `asistente/tests/test_solo_lectura_registro.py`: se recorre el guion
  completo de US1 (incluido el origen nuevo) y de US2 contra `asistente:preguntar` con
  `cliente_http`; antes y después, los conteos de `Muestra`, `Estudio` y `Origen`, el próximo N° PI
  (`muestras.servicios.siguiente_numero_pi` dentro de una transacción) y las claves de la sesión
  son iguales; abrir el enlace precargado (GET) y no enviar tampoco crea nada.
- [ ] T027 [US4] Si T026 detecta alguna escritura, corregirla en `asistente/registro.py` o en las
  vistas GET (no debería haber ninguna: R1, R5).

---

## Phase 7: Polish

- [ ] T028 [P] Recompilar Tailwind si T008 o T016 usaron clases nuevas
  (`static/src/aqualab.css` → `static/css/aqualab.css`, como en la spec 013).
- [ ] T029 [P] `CLAUDE.md`: sección «Iniciar un estudio desde el asistente (US 10.3)» con
  `preparar_muestra`/`preparar_estudio` sin estado y de solo lectura, `leer_fecha`, la validación
  con `RegistroMuestraForm`, `valores_iniciales`/`valores_iniciales_estudio` como único saneo,
  `tipo_estudio` en el borrador y en el mensaje de éxito, `es_pedido_de_registro` y
  `MENSAJE_ALTA_CLIENTE`, y las opciones sin pantalla (`tipo="opcion"`). Actualizar en la sección
  de la 10.1 la frase «El asistente solo consulta».
- [ ] T030 Correr `docker compose exec web pytest`, `ruff check .`, `ruff format --check .` y
  `node --test usuarios/tests/js config/tests/js estudios/tests/js pruebas/tests/js
  asistente/tests/js`; todo en verde.
- [ ] T031 Prueba manual del quickstart completo (pasos 1 a 9) con Groq y la demo; anotar los
  ajustes del mensaje de sistema que hagan falta.

---

## Dependencies & Execution Order

- Phase 1 → Phase 2 (T005–T008 bloquean todo) → US1 → US2 → US3 → US4 → Polish.
- US2 reutiliza `asistente/registro.py` (T018) y `valores_iniciales_estudio` (T017) de US1.
- US3 completa los casos negativos de `registro.py`; puede empezar con los tests (T023–T024) en
  paralelo a US2.
- US4 solo agrega verificación (T026) y depende de US1 y US2.

### Parallel Opportunities

- Phase 2: T002, T003 y T004 (tests) en paralelo; después T005 y T006 en paralelo, y T007 y T008.
- US1: T009, T010, T011, T012 y T013 en paralelo (archivos distintos). T014 → T015 → T016 en
  `muestras`; T017 en `estudios` y T018 en `asistente` en paralelo a esa cadena.
- US3: T023 y T024 en paralelo.

## Implementation Strategy

1. **MVP = Phase 2 + US1**: el ejemplo de la historia completo, con dos confirmaciones. Se puede
   demostrar solo.
2. US2 (estudio para una muestra existente) suma poco código sobre lo de US1.
3. US3 y US4 cierran los criterios «informa y ofrece opciones» y «no queda nada creado».
4. Commits por fase: `feat(asistente): US 10.3 – … (Txxx–Tyyy)`.
