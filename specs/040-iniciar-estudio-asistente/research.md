# Research: Iniciar un estudio desde el asistente (US 10.3)

Decisiones de diseño. Cada una con su motivo y las alternativas descartadas. Las referencias
«R… de 10.1» remiten a `specs/038-asistente-consultas/research.md`.

## R1. La conversación sigue sin estado: una herramienta «preparar» que se llama con todo lo dicho

- **Decisión**: dos herramientas nuevas de solo lectura, `preparar_muestra` y `preparar_estudio`.
  En cada vuelta el modelo las llama con **todos** los datos dichos hasta ese momento en la
  conversación, como texto («Lácteos del Sur», «pozo 2», «ayer»). AquaLab los resuelve contra la
  base y devuelve qué quedó resuelto, qué falta, qué no coincide y, cuando está todo, el enlace
  precargado. Ni AquaLab ni el modelo guardan un «pedido en curso».
- **Motivo**: la US 10.1 no guarda nada (el navegador manda los últimos 6 mensajes). Con 3
  mensajes del empleado (SC-001) el pedido entra entero en el historial. Al resolver todo de nuevo
  en cada vuelta, un dato que cambió (cliente desactivado, tipo desactivado) se detecta solo, y no
  hace falta ningún modelo nuevo.
- **Alternativas**: guardar el pedido en la sesión. Se descartó porque rompe la garantía de que
  el asistente no escribe en la sesión (FR-006 y vista de 10.1) y deja borradores al abandonar.
  Herramientas sueltas por dato (`elegir_cliente`, `elegir_origen`…): son más vueltas, y el
  presupuesto es de 6.

## R2. Pedidos de registro frente al corte por «verbos de cambio»

- **Decisión**: `VERBOS_DE_CAMBIO` ya no corta de entrada `registra`, `crea`, `agrega` ni `carga`
  cuando la pregunta nombra «muestra» o «estudio» (`es_pedido_de_registro`). Sin esas palabras,
  el corte se mantiene. «Registrá el cliente…» recibe un mensaje fijo nuevo
  (`MENSAJE_ALTA_CLIENTE`) con el enlace a «Registrar cliente». `MENSAJE_SISTEMA` y
  `MENSAJE_SOLO_CONSULTA` suman el registro de muestras y estudios, y repiten que cargar
  mediciones, validar o dar de alta clientes no se hace desde el asistente.
- **Motivo**: hoy «Registrá una muestra…» devuelve «solo puedo consultar» sin llamar al
  servicio. Los demás verbos (validá, borrá, emití, corregí…) siguen cortados como en la 10.1.
- **Alternativas**: sacar los verbos de la lista y dejar todo en manos del modelo. Se descartó
  porque el alta de clientes quedaría sujeta a lo que redacte el modelo, en lugar de un mensaje
  fijo y probado.

## R3. Resolver los datos con las reglas de las pantallas

- **Cliente**: `clientes.views.buscar_clientes` (solo activos). Gana la coincidencia exacta de
  `nombre_completo` (sin distinguir mayúsculas ni acentos). Si queda uno, se usa; si quedan varios,
  van como opciones (hasta 10). Si no hay activos, se avisa: si coincide un inactivo, que está
  inactivo; si no, que no se encontró. En los dos casos se agrega la referencia a «Registrar
  cliente» y nunca se crea nada.
- **Origen**: entre los del cliente resuelto. Primero la coincidencia exacta sin mayúsculas ni
  acentos (la misma regla de reutilización de `muestras.servicios.obtener_origen`); si no, las
  que contienen el texto. Una coincidencia se usa; varias van como opciones. Ninguna: opciones con
  los orígenes del cliente más «Registrarlo como origen nuevo» (aclaración del 2026-11-17). Elegido
  (`origen_nuevo: true`), viaja como `origen_nuevo` del formulario.
- **Tipo de estudio**: solo activos (`TipoEstudio.objects.filter(activo=True)`, la misma consulta de
  `CrearEstudioForm`). Coincidencia exacta, si no las que contienen el texto. Si es inactivo o no
  existe, se avisa con las opciones parecidas o, si no hay, todos los activos (hasta 10). Si el
  pedido de muestra no trae tipo, las opciones son «Solo registrar la muestra» (**primera**) y los
  tipos activos.
- **Muestra** (para `preparar_estudio`): por N° PI, como `buscar_muestra`.
- **Motivo**: FR-003, «nunca usa un valor que no salió de esa búsqueda». Las opciones usan el
  mecanismo de la 10.1 (`Referencia.pregunta`).

## R4. Las fechas las interpreta AquaLab, no el modelo

- **Decisión**: `asistente/fechas.py:leer_fecha(texto, hoy)` acepta «hoy», «ayer», «anteayer»,
  `d/m`, `d/m/aaaa`, `aaaa-mm-dd` y «12 de noviembre [de 2026]», con `hoy = timezone.localdate()`
  (fecha del laboratorio). Si un texto no se entiende, la fecha queda en `faltan` con el motivo
  «no entendí la fecha». Las reglas (no futura, muestreo ≤ ingreso) **no se repiten**: la
  herramienta valida los datos reunidos con `RegistroMuestraForm` y devuelve solo los errores de
  los campos que reúne el asistente (cliente, origen, origen nuevo y fechas).
- **Motivo**: el modelo no conoce la fecha del laboratorio, y convertir «ayer» por su cuenta
  sería inventar un dato (FR-010). El formulario sigue siendo la única regla (FR-007).
- **Alternativas**: pasar la fecha de hoy en el mensaje de sistema y dejar que el modelo
  convierta. Se descartó porque no se puede probar de forma determinista. `d/m` sin año toma el
  año actual; si eso da una fecha futura, el formulario la rechaza y el asistente lo informa.

## R5. El enlace precargado es un GET con los valores iniciales, sin firma

- **Decisión**: `muestras:registrar?cliente=<pk>&origen=<pk>|origen_nuevo=<texto>&fecha_muestreo=
  aaaa-mm-dd&fecha_ingreso=aaaa-mm-dd[&sitio_extraccion=…&tipo_vertido=…&nombre=…&responsable_
  muestreo=…][&tipo_estudio=<pk>]` y `estudios:crear?muestra=<pk>&tipo=<pk>`. Las dos vistas toman
  esos parámetros **solo como `initial`** de un formulario sin enviar, a través de una única
  función de saneo por formulario (`muestras.forms.valores_iniciales`,
  `estudios.forms.valores_iniciales_estudio`) que descarta en silencio lo que no existe o no está
  disponible: cliente inactivo, origen de otro cliente, tipo inactivo, fecha ilegible, vertido
  fuera de las opciones o textos más largos que el campo.
- **Motivo**: el enlace no concede nada. Lo que se precarga, cualquiera puede elegirlo a mano en
  la misma pantalla, y todo se revalida al enviar. Firmar no agrega seguridad y complica los
  tests. Abrir `muestras:registrar` sin `volver=1` ya descarta el borrador de la sesión, igual
  que un registro nuevo hecho a mano (caso borde de la spec).
- **Alternativas**: un borrador firmado como el de crear estudio. Se descartó porque el
  asistente no puede escribir en la sesión y un borrador firmado dejaría de ser «el formulario de
  siempre».

## R6. «Crear el estudio <tipo>» después de registrar la muestra

- **Decisión**: `RegistroMuestraForm` suma `tipo_estudio`, un campo oculto opcional
  (`ModelChoiceField` sobre los tipos activos). Viaja en el borrador de la sesión
  (`datos_para_sesion`, que `registrar_muestra` ignora), se muestra como nota en el formulario y
  en la confirmación («Después de registrar la muestra se ofrecerá crear el estudio …») y, al
  registrarse la muestra, `mensaje_exito_muestra` agrega el enlace «Crear el estudio <tipo>» a
  `estudios:crear?muestra=<pk>&tipo=<pk>` si el tipo sigue activo. Si el tipo ya no está activo,
  el mensaje es el de siempre.
- **Motivo**: es la aclaración Q1 (dos confirmaciones). Un tipo inválido en el POST da error de
  campo oculto, y por eso se sanea igual que los demás: si no es válido, se descarta sin error.
- **Alternativas**: pasar el tipo solo en la URL del mensaje. Se descartó porque se perdería al
  volver desde la confirmación (`?volver=1`).

## R7. Enlaces y opciones sin pantalla propia

- **Decisión**: `enlaces.Referencia` admite referencias a pantallas sin `pk` (`registrar_muestra`,
  `crear_estudio`, `registrar_cliente`) con `parametros` (pares que se arman con `urlencode`) y
  opciones sin pantalla (`tipo="opcion"`, sin URL: un botón sin ↗) para orígenes, tipos, «Solo
  registrar la muestra» y «Registrarlo como origen nuevo». El enlace final lleva
  `"minimizar": true`. El panel lo muestra como botón principal «Revisar y registrar la muestra» /
  «Revisar y crear el estudio» y, al seguirlo, minimiza el panel (conserva la conversación, como
  el «–» de la 10.1) para que no tape el formulario.
- **Motivo**: los enlaces los sigue armando solo AquaLab con `reverse` (FR-005). La lista blanca
  de tipos (`VISTAS`) sigue siendo la única puerta.

## R8. Permisos

- **Decisión**: `puede_ver(usuario, "registro")` es la regla para ofrecer los enlaces: usuario
  activo con sesión, lo mismo que hoy exigen `muestras:registrar` y `estudios:crear` (solo
  `LoginRequiredMiddleware`). Si una de esas pantallas suma un permiso, se agrega acá y en la
  pantalla a la vez (FR-009). Las herramientas siguen corriendo en la transacción `READ ONLY` de la
  10.1, así que no pueden crear nada (FR-006, SC-002).

## R9. Datos hacia el servicio externo

- **Decisión**: las salidas de `preparar_*` usan la lista blanca de la 10.1: del cliente, solo
  `nombre` y `activo`; del origen, solo `nombre`; del tipo, solo `nombre`. Nunca el documento, el
  correo, el teléfono ni el domicilio (FR-011). El N° PI, las fechas y los textos que dictó el
  empleado sí viajan, igual que en las consultas.
