---

description: "Lista de tareas de la US 6.1 – Cargar mediciones"
---

# Tasks: Cargar mediciones

**Input**: `specs/015-cargar-mediciones/` (`plan.md`, `spec.md`, `research.md`, `data-model.md`,
`contracts/cargar-mediciones-ui.md`, `quickstart.md`)

**Prerequisites**: `plan.md`, `spec.md` y US 5.2–5.4 y SCRUM-64 en `main`: `estudios:detalle`,
`EstadoEstudio`, `EstadoPruebaEstudio`, `Estudio.admite_modificaciones`, `PruebaEstudio.puede_quitarse()`,
`agregar_prueba`, `quitar_prueba` (captura `ProtectedError`), `Prueba.unidad_medicion` y
`Prueba.es_calculada`; fixtures `empleado`, `muestra`, `datos`, `estudio`, `asignacion` y
`cliente_http` de `estudios/tests/conftest.py`; `capturar_estado` de
`estudios/tests/test_servicio_pruebas.py`; esquema de hilos de
`estudios/tests/test_concurrencia_pruebas.py`.

**Tests**: SÍ. La constitution (principio III) exige al menos un test con pytest-django por cada
escenario de aceptación y casos conocidos con valores esperados para los cálculos numéricos. Los
tests siguen el «Mapa de tests» de `plan.md` y se escriben **antes** de la implementación de cada
historia (deben fallar primero).

**Organization**: tres user stories de la spec — US1 (P1, cargar mediciones), US2 (P2, validar los
valores) y US3 (P3, impedir cargas no permitidas).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: se puede ejecutar en paralelo (archivos distintos, sin dependencias pendientes)
- **[Story]**: user story a la que pertenece la tarea (`[US1]`, `[US2]`, `[US3]`)
- Rutas relativas a la raíz del repo

## Convenciones para todas las tareas

- Textos de UI, mensajes y nombres de dominio en **español** (principio VI).
- Mensajes al usuario copiados **literalmente** de `contracts/cargar-mediciones-ui.md`.
- Mismo estilo que `agregar_prueba` y `agregar_prueba_confirmar.html` (US 5.3): diseño de SCRUM-67
  con `ui/encabezado.html`, `<dl class="resumen" data-componente="resumen">`, botones con
  `data-componente="acciones-confirmacion"`, `.tabla`, `ui/errores_form.html` y `ui/estado_vacio.html`.
  Sin componentes CSS nuevos ni JavaScript.
- La vista `cargar_mediciones` llama a `servicios.cargar_mediciones` y los tests parchean
  `estudios.servicios.cargar_mediciones` (como en US 5.3/5.4).
- Una sola migración: `estudios/migrations/0004_medicion.py` (generada con `makemigrations`).
- Comandos dentro de Docker: `docker compose exec web pytest estudios`,
  `docker compose exec web ruff check .`, `docker compose exec web ruff format --check .`.

---

## Phase 1: Setup (Shared Infrastructure)

- [X] T001 **Gate de la constitution (principio I)**: confirmar que el equipo aprobó `specs/015-cargar-mediciones/spec.md` y actualizar su `**Status**` a «Aprobada por el equipo» con la fecha; sin esa aprobación no se ejecuta ninguna otra tarea. Después, ejecutar `docker compose exec web pytest` y `docker compose exec web python manage.py makemigrations --check --dry-run` y confirmar suite en verde y sin cambios pendientes.

---

## Phase 2: Foundational (Blocking Prerequisites)

**⚠️ CRITICAL**: ninguna historia empieza antes de terminar esta fase.

- [X] T002 [P] Agregar en `estudios/tests/conftest.py`:
  - fixture `pruebas_medicion()`: crea `TEST-PH` («pH de test», `unidad_medicion="UpH"`), `TEST-VOL` («Volumen de test», `unidad_medicion="mL"`), `TEST-SIN` («Sin unidad de test», `unidad_medicion=""`) y `TEST-CALC` («Calculada de test», `tipo_calculo="FORMULA"`, `formula="{TEST-PH} * 2"`, `es_calculada=True`) y las devuelve en un dict por código;
  - fixture `estudio_mediciones(muestra, empleado, pruebas_medicion)`: tipo «Tipo mediciones de test» con las cuatro pruebas y un estudio creado con `crear_estudio` (clave `uuid4`);
  - fixture `asignaciones_medicion(estudio_mediciones)`: dict código → `PruebaEstudio` del estudio.
- [X] T003 [P] Crear `estudios/tests/test_servicio_mediciones.py` (`pytestmark = pytest.mark.django_db` solo en los tests que tocan la base) con los tests de `leer_valor` (research R4, tabla «Mensajes de `leer_valor`» del contrato):
  - `test_leer_valor_validos` (parametrizado): `"7,25"`→`Decimal("7.25")`, `"7.25"`→`Decimal("7.25")`, `" 7,20 "`→`Decimal("7.20")` (verificar también `as_tuple().exponent == -2`), `"-0,013"`→`Decimal("-0.013")`, `"+3"`→`Decimal("3")`, `"0"`→`Decimal("0")`, `",5"`→`Decimal("0.5")`, `"0,123456"`→`Decimal("0.123456")`, `"999999999999"`→`Decimal("999999999999")`, `"0000000000000,5"`→`Decimal("0.5")` (los ceros a la izquierda no cuentan como cifras enteras);
  - `test_leer_valor_vacio` (parametrizado `""`, `"   "`, `None`): devuelve `None`;
  - `test_leer_valor_invalidos` (parametrizado): `"abc"`, `"1.234,5"`, `"1,2,3"`, `"1e3"`, `"7 25"`, `"7%"`, `"NaN"`, `"Infinity"`, `"7,"`, `"-"` → `ValidationError` con «Ingresá un número válido (usá coma o punto para los decimales).»; `"0,1234567"` → «Ingresá como máximo 6 decimales.»; `"1234567890123"` → «El valor es demasiado grande (máximo 12 cifras enteras).».
- [X] T004 [P] Agregar en `estudios/tests/test_modelos.py`:
  - `test_valor_ingresado_conserva_ceros_finales`: una `Medicion` guardada con `valor=Decimal("7.20")`, `decimales=2` releída de la base devuelve `valor_ingresado == Decimal("7.20")` con exponente `-2`; con `decimales=0` y `valor=Decimal("18")`, `Decimal("18")`;
  - `test_una_medicion_por_asignacion`: una segunda `Medicion` para la misma asignación lanza `IntegrityError`;
  - `test_medicion_decimales_validos`: `decimales=7` lanza `IntegrityError` (constraint `medicion_decimales_validos`);
  - `test_asignacion_con_medicion_protegida`: borrar una `PruebaEstudio` con `Medicion` lanza `ProtectedError`;
  - `test_admite_mediciones_por_estado` (parametrizado): `True` en `pendiente_analisis` y `en_proceso`, `False` en `finalizado` e `informe_generado`.
- [X] T005 Agregar en `estudios/models.py` (data-model §1–2):
  - en `Estudio`, la propiedad `admite_mediciones` → `self.estado in (EstadoEstudio.PENDIENTE_ANALISIS, EstadoEstudio.EN_PROCESO)` (research R7);
  - el modelo `Medicion` con `asignacion = models.OneToOneField(PruebaEstudio, on_delete=models.PROTECT, related_name="medicion", editable=False)`, `valor = models.DecimalField("valor", max_digits=18, decimal_places=6)`, `decimales = models.PositiveSmallIntegerField("decimales")`, `unidad = models.CharField("unidad", max_length=50, blank=True, default="")`, `cargada_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="mediciones_cargadas", editable=False)`, `fecha_carga = models.DateTimeField("fecha de carga", auto_now_add=True)`; `Meta.constraints = [models.CheckConstraint(condition=Q(decimales__lte=6), name="medicion_decimales_validos")]`; `verbose_name` «medición» / «mediciones»; propiedad `valor_ingresado` → `self.valor.quantize(Decimal(1).scaleb(-self.decimales))`; `__str__` → `f"{self.asignacion} = {self.valor_ingresado} {self.unidad}".rstrip()`.
  - Actualizar el docstring de `PruebaEstudio.puede_quitarse()`: la carga de mediciones (US 6.1) ya pasa la prueba a `Cargada`.
- [X] T006 Generar la migración con `docker compose exec -u "$(id -u):$(id -g)" web python manage.py makemigrations estudios --name medicion` y verificar que crea solo `estudios/migrations/0004_medicion.py` con el modelo `Medicion` y su constraint (depende de T005).
- [X] T007 [P] Crear `estudios/mediciones.py` con `leer_valor(texto)` (research R4): `None` si `texto` es `None` o queda vacío tras `strip()`; validar con `re.fullmatch(r"[+-]?(?:\d+(?:[.,]\d+)?|[.,]\d+)", texto)` (si no, `ValidationError` «Ingresá un número válido (usá coma o punto para los decimales).»); reemplazar `,` por `.`, construir `Decimal`; más de 6 decimales (`-valor.as_tuple().exponent > 6`) → «Ingresá como máximo 6 decimales.»; más de 12 cifras enteras, contadas sobre el `Decimal` con `max(valor.adjusted() + 1, 0)` (no sobre el texto) → «El valor es demasiado grande (máximo 12 cifras enteras).»; constantes `MAX_DECIMALES = 6` y `MAX_ENTEROS = 12`. Devuelve el `Decimal` con el exponente escrito (`"7,20"` → `Decimal("7.20")`).
- [X] T008 Ejecutar `docker compose exec web pytest estudios` y dejar en verde T003–T004 sin romper los tests existentes (depende de T002–T007).

**Checkpoint**: modelo, migración, regla del estudio y lectura de valores listos.

---

## Phase 3: User Story 1 - Cargar las mediciones de las pruebas pendientes de un estudio (Priority: P1) 🎯 MVP

**Goal**: desde el detalle del estudio, cargar el valor de algunas o todas las pruebas pendientes
con una confirmación; quedan `Cargada` con valor, unidad, usuario y fecha, y el estudio pasa a
"En proceso".

**Independent Test**: con `estudio_mediciones`, cargar `7,20` en TEST-PH y `18.5` en TEST-VOL,
confirmar y verificar que quedan `Cargada` con su medición, que TEST-SIN sigue `Pendiente` y se
ofrece en la próxima carga, y que el estudio está "En proceso".

### Tests for User Story 1 ⚠️ (escribir primero, deben fallar)

- [X] T009 [P] [US1] Agregar en `estudios/tests/test_servicio_mediciones.py` (con `capturar_estado` importado de `estudios.tests.test_servicio_pruebas` donde haga falta):
  - `test_cargar_mediciones_guarda_valor_unidad_usuario_y_fecha`: `cargar_mediciones(estudio.pk, {ph.pk: Decimal("7.20"), vol.pk: Decimal("18.5")}, empleado)` devuelve `ResultadoCarga` con 2 `guardadas` y `omitidas == []`; cada `Medicion` tiene el valor exacto, `decimales` 2 y 1, `unidad` `"UpH"` y `"mL"`, `cargada_por == empleado` y `fecha_carga` entre antes y después de la llamada; ambas asignaciones quedan `cargada`.
  - `test_carga_parcial_deja_pendientes`: cargar solo TEST-PH deja TEST-VOL, TEST-SIN y TEST-CALC en `pendiente` y sin `Medicion`.
  - `test_primera_medicion_pasa_estudio_a_en_proceso`: el estudio pasa de `pendiente_analisis` a `en_proceso`; una segunda carga sobre `en_proceso` lo deja en `en_proceso`.
  - `test_cargar_no_modifica_otros_datos`: con un segundo estudio del mismo tipo, la cabecera (salvo `estado`), los snapshots, el tipo, el catálogo de pruebas y el otro estudio no cambian (FR-015).
  - `test_unidad_conservada_tras_cambio_en_catalogo`: después de cargar TEST-VOL, cambiar `unidad_medicion` de la prueba a `"L"` no cambia `Medicion.unidad` (`"mL"`).
  - `test_estudio_cerrado_rechaza_carga` (parametrizado `finalizado` e `informe_generado`, guardados con `Estudio.objects.filter(...).update(estado=...)`): `CargarMedicionesError` con «Este estudio ya no admite carga de mediciones.» y sin `Medicion` (FR-003; en el MVP).
- [X] T010 [P] [US1] Crear `estudios/tests/test_cargar_mediciones.py` (`pytestmark = pytest.mark.django_db`) con:
  - `test_detalle_ofrece_cargar_mediciones`: el detalle de `estudio_mediciones` tiene el enlace a `estudios:cargar_mediciones`.
  - `test_formulario_lista_pendientes_con_unidad`: GET → 200 con un campo `medicion_<pk>` (`inputmode="decimal"`) por TEST-PH, TEST-SIN y TEST-VOL, en ese orden de código, con «UpH», «mL» y «Sin unidad», y sin campo para TEST-CALC.
  - `test_revisar_muestra_resumen_sin_guardar`: POST `accion=revisar` con `7,20` en TEST-PH y vacío el resto → 200 con `cargar_mediciones_confirmar.html`, «Se guardará 1 medición en el estudio N (muestra PI 200001).», la fila TEST-PH con `7,20` y `UpH`, el campo oculto `medicion_<pk>` con `7,20` y el enlace **Cancelar** al `href` de `estudios:detalle`; no existe ninguna `Medicion` (cancelar no guarda nada, US1 Esc. 3).
  - `test_editar_conserva_valores`: POST `accion=editar` con los mismos datos → 200 con el formulario y `value="7,20"` en el campo de TEST-PH.
  - `test_confirmar_guarda_mediciones`: POST `accion=confirmar` con `7,20` (TEST-PH) y `18.5` (TEST-VOL) → 302 a `detalle`, mensaje de éxito «Se guardaron 2 mediciones del estudio N: TEST-PH, TEST-VOL.», dos `Medicion` y el estudio en `en_proceso`.
  - `test_formulario_no_ofrece_cargadas`: después de cargar TEST-PH, GET del formulario no tiene campo para TEST-PH y sí para TEST-VOL y TEST-SIN.
  - `test_detalle_muestra_medicion`: después de cargar `7,20` en TEST-PH, el detalle muestra «7,20 UpH», el nombre (o correo) del empleado y la fecha y hora `d/m/Y H:i`; TEST-VOL muestra «—» y TEST-CALC «Se calcula».
  - `test_estudio_en_proceso_no_ofrece_agregar_ni_quitar`: después de cargar, el detalle no tiene enlaces a `estudios:agregar_prueba` ni a `estudios:quitar_prueba` y sí a `estudios:cargar_mediciones` (quedan pruebas pendientes).
  - `test_estudio_cerrado_rechaza_carga` (vista, parametrizado `finalizado` e `informe_generado`): GET y POST `revisar` → 302 a `detalle` con «Este estudio ya no admite carga de mediciones.» (FR-003; en el MVP).
  - `test_error_de_base_al_cargar_no_guarda`: con `estudios.servicios.cargar_mediciones` parcheado para lanzar `DatabaseError`, POST `accion=confirmar` → 302 a `detalle` con «No se pudieron guardar las mediciones. Intentá nuevamente.» y sin `Medicion`.

### Implementation for User Story 1

- [X] T011 [US1] Agregar en `estudios/servicios.py` (research R6): `class CargarMedicionesError(Exception)`; `@dataclass class ResultadoCarga` con `guardadas: list` y `omitidas: list` (pares `(Prueba, motivo)`), ambos con `field(default_factory=list)`; y `cargar_mediciones(estudio_pk, valores, usuario)`: misma comprobación de sesión que `agregar_prueba` (`CargarMedicionesError("Se requiere una sesión activa.")`); dentro de `transaction.atomic()`: `Estudio.objects.select_for_update().filter(pk=estudio_pk).first()` (None → «El estudio no está disponible.»); `if not estudio.admite_mediciones: raise CargarMedicionesError("Este estudio ya no admite carga de mediciones.")` (FR-003); asignaciones `estudio.pruebas_asignadas.select_for_update(of=("self",)).select_related("prueba").filter(pk__in=valores).order_by("prueba__codigo", "pk")`; por cada una con estado `Pendiente`: `Medicion.objects.create(asignacion=..., valor=valor, decimales=max(0, -valor.as_tuple().exponent), unidad=asignacion.prueba.unidad_medicion, cargada_por=usuario)`, `asignacion.estado = EstadoPruebaEstudio.CARGADA` y `save(update_fields=["estado"])`; si hubo guardadas y el estudio está en `PENDIENTE_ANALISIS`, pasarlo a `EN_PROCESO` con `save(update_fields=["estado"])`. Devolver `ResultadoCarga` (las reglas de omisión se completan en US3) (depende de T005).
- [X] T012 [US1] Agregar en `estudios/forms.py` `CargarMedicionesForm(forms.Form)` (research R5): `__init__(self, *args, asignaciones, **kwargs)` guarda `self.asignaciones` (lista, con `prueba` cargada) y crea por cada una `forms.CharField(required=False, max_length=40, label=str(asignacion.prueba))` con nombre `medicion_<asignacion.pk>` y `widget.attrs` `{"inputmode": "decimal", "autocomplete": "off", "class": "form-control"}`; `clean()` llama a `leer_valor` por campo y guarda los `Decimal` no vacíos en `self._valores` (los `ValidationError` van con `self.add_error(nombre, ...)` y agregan ` is-invalid` al widget); `filas()` → lista de `(asignacion, self[nombre])`; `valores()` → `{asignacion.pk: Decimal}`; `resumen()` → `[(asignacion, nombre, texto)]` de los campos no vacíos (para la tabla y los ocultos de la confirmación) (depende de T007).
- [X] T013 [US1] Crear la vista `cargar_mediciones(request, pk)` en `estudios/views.py` según `contracts/cargar-mediciones-ui.md`: `get_object_or_404(Estudio.objects.select_related("muestra"), pk=pk)`; helper `asignaciones_para_medir(estudio)` → pendientes con `prueba__es_calculada=False`, `select_related("prueba")`, `order_by("prueba__codigo", "pk")`; en GET, `revisar` y `editar`, si `not estudio.admite_mediciones` → 302 a `detalle` con «Este estudio ya no admite carga de mediciones.» (en `confirmar` lo revalida el servicio bajo el bloqueo); GET → `estudios/cargar_mediciones.html` con el formulario; POST: `accion` fuera de `revisar`/`editar`/`confirmar` → 302 a `detalle` con «La acción no es válida.»; en `confirmar`, el formulario se arma con todas las asignaciones no calculadas del estudio (cualquier estado, research R5) para que el valor de una prueba que mientras tanto quedó Cargada llegue al servicio; formulario inválido → re-render; `revisar` → `estudios/cargar_mediciones_confirmar.html` con `form.resumen()`; `editar` → formulario con los datos; `confirmar` → `servicios.cargar_mediciones(estudio.pk, form.valores(), request.user)`, mensaje de éxito del contrato (singular con una sola medición) y 302 a `detalle`; `CargarMedicionesError` → `messages.error(str(exc))`; `DatabaseError` → «No se pudieron guardar las mediciones. Intentá nuevamente.». Registrar `path("<int:pk>/mediciones/cargar/", views.cargar_mediciones, name="cargar_mediciones")` en `estudios/urls.py` (depende de T011, T012).
- [X] T014 [P] [US1] Crear `estudios/templates/estudios/cargar_mediciones.html`: `ui/encabezado.html` (migas Estudios › Estudio N › Cargar mediciones, título «Cargar mediciones»), aviso informativo con el estudio y la muestra (PI), `<form method="post">` con `{% csrf_token %}` y tabla `.tabla` con **Código**, **Prueba**, **Unidad** (`unidad_medicion` o «Sin unidad») y **Medición** (el campo, con `aria-describedby="<auto_id>_error"` si tiene errores y el bloque `campo-error` con id `<auto_id>_error`, como `ui/campo.html`); botones **Revisar mediciones** (`name="accion" value="revisar"`, `btn btn-primario`) y **Cancelar** (enlace a `detalle`, `btn btn-secundario`) (depende de T013).
- [X] T015 [P] [US1] Crear `estudios/templates/estudios/cargar_mediciones_confirmar.html` como `agregar_prueba_confirmar.html`: encabezado, aviso «Se guardarán N mediciones en el estudio X (muestra PI Y).» o, con N = 1, «Se guardará 1 medición en el estudio X (muestra PI Y).» (contrato), resumen del estudio y la muestra, tabla **Código / Prueba / Valor / Unidad** con el texto ingresado y la unidad, y `data-componente="acciones-confirmacion"`: un `<form method="post">` con `{% csrf_token %}`, un oculto por cada fila de `form.resumen()` y los botones **Guardar mediciones** (`accion=confirmar`, `btn btn-primario`; el `onsubmit` evita el doble envío sin deshabilitar los botones, que si no dejan de enviar la `accion`) y **Volver a editar** (`accion=editar`, `btn btn-secundario`), y el enlace **Cancelar** (`btn btn-peligro sm:ml-auto`) a `detalle` (depende de T013).
- [X] T016 [US1] En `estudios/views.py`, `detalle`: `select_related("prueba", "medicion", "medicion__cargada_por")` en las asignaciones y `pruebas_para_medir` (pendientes no calculadas) en el contexto. En `estudios/templates/estudios/detalle.html`: botón **Cargar mediciones** (`btn btn-primario`, ícono `clipboard-list`) junto a «Agregar prueba» si `estudio.admite_mediciones and pruebas_para_medir`; columna **Medición** antes de Estado con `medicion.valor_ingresado` + unidad (o «Sin unidad») y, debajo en `text-xs text-tinta-suave`, `cargada_por.get_full_name|default:cargada_por.email` y `fecha_carga|date:"d/m/Y H:i"`; sin medición «—»; prueba calculada sin medición «Se calcula» (depende de T005, T013).
- [X] T017 [US1] Ejecutar `docker compose exec web pytest estudios` y dejar en verde T009–T010 sin romper US 5.2–5.4 (depende de T011–T016).

**Checkpoint**: se pueden cargar mediciones con confirmación, solo en estudios abiertos; MVP de la US 6.1.

---

## Phase 4: User Story 2 - Validar los valores ingresados (Priority: P2)

**Goal**: rechazar valores inválidos con el error junto a cada campo, sin guardar nada del envío,
y exigir al menos un valor.

**Independent Test**: enviar `7,25`, `0.418`, `abc`, `1.234,5` y un formulario vacío; verificar los
mensajes junto a cada campo, que los valores se conservan y que no se guarda ninguna medición.

### Tests for User Story 2 ⚠️ (escribir primero, deben fallar)

- [X] T018 [P] [US2] Agregar en `estudios/tests/test_cargar_mediciones.py`:
  - `test_revisar_con_valor_invalido_no_guarda`: POST `accion=revisar` con `7,25` (TEST-PH), `abc` (TEST-VOL) y `1.234,5` (TEST-SIN) → 200 con el formulario, «Ingresá un número válido (usá coma o punto para los decimales).» en el bloque `<auto_id>_error` de TEST-VOL y de TEST-SIN, clase `is-invalid` en esos campos, `value="7,25"` conservado en TEST-PH y sin `Medicion`.
  - `test_confirmar_con_valor_invalido_no_guarda`: el mismo envío con `accion=confirmar` (oculto manipulado) → 200 con el formulario y errores; `estudios.servicios.cargar_mediciones` parcheado no se llama; sin `Medicion`.
  - `test_revisar_sin_valores_pide_al_menos_uno` (parametrizado: todo vacío y todo con espacios) → 200 con «Ingresá al menos una medición.» y sin `Medicion`.
  - `test_valor_con_espacios_y_decimales_se_guarda_como_se_escribio`: confirmar `" 0,4180 "` en TEST-VOL guarda `valor_ingresado == Decimal("0.4180")` y el detalle muestra «0,4180 mL».

### Implementation for User Story 2

- [X] T019 [US2] En `CargarMedicionesForm.clean()` de `estudios/forms.py`: si ningún campo tiene valor y no hay otros errores, `raise forms.ValidationError("Ingresá al menos una medición.")` (FR-005) (depende de T012).
- [X] T020 [US2] En `estudios/templates/estudios/cargar_mediciones.html`: incluir `ui/errores_form.html` para los errores generales arriba de la tabla y verificar que cada campo inválido muestra su error y conserva su valor (FR-006, FR-007) (depende de T014, T019).
- [X] T021 [US2] Ejecutar `docker compose exec web pytest estudios` y dejar en verde T018 junto con US1 (depende de T019–T020).

**Checkpoint**: ningún valor inválido llega a guardarse; los errores se ven junto a cada campo.

---

## Phase 5: User Story 3 - Impedir cargas no permitidas (Priority: P3)

**Goal**: no pedir medición para pruebas calculadas y que reenvíos, cargas simultáneas y quitas
no dupliquen ni reemplacen mediciones. El rechazo de estudios cerrados (US3 Esc. 3) ya lo cubre la
US1 (T009–T013), para que el MVP cumpla FR-003.

**Independent Test**: abrir la carga con una prueba calculada, confirmar dos veces la misma carga y cargar en paralelo; verificar mensajes y que cada
prueba tiene como máximo una medición.

### Tests for User Story 3 ⚠️ (escribir primero, deben fallar)

- [X] T022 [P] [US3] Agregar en `estudios/tests/test_servicio_mediciones.py`:
  - `test_omite_cargada_y_guarda_el_resto`: con TEST-PH ya cargada, `cargar_mediciones` con TEST-PH y TEST-VOL guarda solo TEST-VOL; `omitidas == [(TEST-PH, "ya tenía una medición cargada")]`; la medición original de TEST-PH no cambia.
  - `test_servicio_omite_calculada`: un valor para TEST-CALC se omite con «se calcula a partir de otras pruebas» y la asignación sigue `pendiente`.
  - `test_servicio_ignora_asignacion_de_otro_estudio`: el `pk` de una asignación de otro estudio no se carga ni se informa como guardado; la asignación ajena sigue sin `Medicion`.
  - `test_cargar_mediciones_requiere_sesion_activa`: con `AnonymousUser` o un usuario inactivo → `CargarMedicionesError` con «Se requiere una sesión activa.».
- [X] T023 [P] [US3] Agregar en `estudios/tests/test_cargar_mediciones.py`:
  - `test_cargar_mediciones_requiere_sesion` (GET y POST): sin sesión → 302 al login y sin `Medicion` (FR-001).
  - `test_cargar_mediciones_estudio_inexistente_404` (GET y POST).
  - `test_formulario_muestra_calculadas_sin_campo`: GET → bloque «Se calculan a partir de otras pruebas» con TEST-CALC y sin campo `medicion_<pk>` para su asignación.
  - `test_formulario_sin_pruebas_para_medir`: con TEST-PH, TEST-VOL y TEST-SIN cargadas → GET con «No hay mediciones para cargar en este estudio.», sin botón «Revisar mediciones»; el detalle ya no ofrece «Cargar mediciones».
  - `test_detalle_no_ofrece_cargar_mediciones` (parametrizado): sin enlace a `estudios:cargar_mediciones` si el estudio está `finalizado` o `informe_generado`, ni si solo quedan pruebas calculadas pendientes.
  - `test_reenvio_informa_ya_cargada`: dos POST `accion=confirmar` iguales (el primero con `follow=True`) → el segundo redirige con la advertencia «TEST-PH: ya tenía una medición cargada.» y una sola `Medicion` con el valor del primero.
  - `test_confirmar_prueba_quitada_se_informa`: tras quitar TEST-SIN con `quitar_prueba` (estudio aún en `pendiente_analisis`), POST `accion=confirmar` con valores para TEST-PH y para el `pk` viejo de TEST-SIN → se guarda TEST-PH y se advierte «1 prueba(s) ya no forman parte del estudio; su medición no se guardó.».
- [X] T024 [P] [US3] Crear `estudios/tests/test_concurrencia_mediciones.py` (`pytestmark = pytest.mark.django_db(transaction=True)`, mismo esquema de hilos y `threading.Barrier` que `test_concurrencia_pruebas.py`):
  - `test_cargas_concurrentes_misma_prueba`: dos hilos cargan TEST-PH con `1,1` y `2,2`; queda una sola `Medicion` y exactamente uno de los resultados la tiene en `guardadas` y el otro en `omitidas`.
  - `test_carga_y_quita_concurrentes`: un hilo carga TEST-PH y otro quita la misma asignación; al final, o la asignación no existe y no hay `Medicion`, o existe en `cargada` con su `Medicion` (nunca medición de prueba quitada).

### Implementation for User Story 3

- [X] T025 [US3] Completar `cargar_mediciones` en `estudios/servicios.py`: los `pk` de `valores` que no están entre las asignaciones bloqueadas del estudio no se cargan ni se agregan a `omitidas` (la vista informa las quitadas por cantidad, research R6); asignación no `Pendiente` → `omitidas.append((prueba, "ya tenía una medición cargada"))`; `prueba.es_calculada` → `omitidas.append((prueba, "se calcula a partir de otras pruebas"))` (FR-004, FR-012) (depende de T011).
- [X] T026 [US3] En `estudios/forms.py`, `CargarMedicionesForm.pruebas_quitadas()`: cantidad de claves `medicion_<n>` del `data` con texto no vacío cuyo `n` no es una asignación del formulario (research R5) (depende de T012).
- [X] T027 [US3] En `estudios/views.py`, `cargar_mediciones` (`confirmar`): después del servicio, una advertencia `messages.warning` «COD: motivo.» por cada omitida, la advertencia de `pruebas_quitadas()` si es mayor que cero, y el mensaje de éxito solo si hubo guardadas; pasar al template las pruebas calculadas pendientes (depende de T013, T025, T026).
- [X] T028 [US3] En `estudios/templates/estudios/cargar_mediciones.html`: bloque «Se calculan a partir de otras pruebas» con código y nombre de las calculadas pendientes (sin campos), y si no hay campos, `ui/estado_vacio.html` con «No hay mediciones para cargar en este estudio.» y enlace al estudio, sin botón «Revisar mediciones» (depende de T014, T027).
- [X] T029 [US3] Ejecutar `docker compose exec web pytest estudios` y dejar en verde T022–T024 junto con US1 y US2 (depende de T025–T028).

**Checkpoint**: US 6.1 completa; las reglas resisten reenvíos, quitas y cargas simultáneas.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T030 [P] Ejecutar `docker compose exec web ruff check .`, `docker compose exec web ruff format --check .` y `docker compose exec web python manage.py makemigrations --check --dry-run`, y corregir lo que aparezca (principios III y VI).
- [X] T031 Ejecutar la suite completa `docker compose exec web pytest` y confirmar todo en verde.
- [X] T032 Recorrer los pasos 1 a 7 de `specs/015-cargar-mediciones/quickstart.md` y cronometrar la carga de un estudio de 10 pruebas: menos de 3 minutos con una sola confirmación (SC-001).
- [X] T033 [P] En `CLAUDE.md`: agregar la sección «Carga de mediciones (US 6.1)» con lo no obvio: `Medicion` es uno a uno con `PruebaEstudio` (`PROTECT`); el valor se guarda en `numeric(18, 6)` y los decimales escritos aparte, y se muestra siempre con `valor_ingresado`; `leer_valor` (`estudios/mediciones.py`) es la única lectura del texto; `cargar_mediciones` bloquea el estudio (mismo orden que `quitar_prueba`), omite e informa en vez de fallar, y pasa el estudio a "En proceso" con la primera medición; `Estudio.admite_mediciones` es la regla de carga; al confirmar, el formulario usa todas las asignaciones no calculadas para informar las ya cargadas. Reescribir la nota **Epic 6** de «Pruebas de un estudio» dejando solo lo pendiente (pasar a `Completada` en US 6.4; las mediciones se modifican en US 6.3 actualizando la misma fila) y la nota **Epic 6** del catálogo sin cambios. No tocar el pendiente del envío de informes.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: `T001`.
- **Foundational (Phase 2)**: depende de la fase 1. `T002`, `T003`, `T004` y `T007` en paralelo; `T005` → `T006`; `T008` al final. Bloquea las historias.
- **US1 (Phase 3)**: depende de la fase 2. Es el MVP.
- **US2 (Phase 4)**: depende de US1 (completa su formulario y su template).
- **US3 (Phase 5)**: depende de US1 (completa su servicio, su vista y sus templates); puede hacerse antes o después de US2, pero comparten `test_cargar_mediciones.py` y `cargar_mediciones.html`, así que conviene en secuencia.
- **Polish (Phase 6)**: depende de las tres historias.

### Dentro de cada historia

- Tests primero y fallando; luego servicio → formulario → vista + URL → templates.
- `servicios.py`, `forms.py`, `views.py`, `cargar_mediciones.html`, `test_servicio_mediciones.py` y `test_cargar_mediciones.py` se tocan en varias fases: las tareas que comparten archivo van en secuencia.

### Grafo

```text
T001 → T002, T003, T004, T007 ─┐
       T005 → T006 ────────────┴─→ T008
                                    │
          ┌─────────────────────────┘
          ▼
US1: T009, T010 → T011 → T012 → T013 → T014, T015 → T016 → T017
US2: T018 → T019 → T020 → T021
US3: T022, T023, T024 → T025 → T026 → T027 → T028 → T029
Polish: T030, T031, T032, T033
```

---

## Parallel Example: Foundational

```bash
Task T003: "Tests de leer_valor en estudios/tests/test_servicio_mediciones.py"
Task T004: "Tests de Medicion en estudios/tests/test_modelos.py"
Task T007: "leer_valor en estudios/mediciones.py"
```

## Parallel Example: User Story 1

```bash
Task T009: "Tests del servicio en estudios/tests/test_servicio_mediciones.py"
Task T010: "Tests de vistas en estudios/tests/test_cargar_mediciones.py"
# Después de T013:
Task T014: "estudios/templates/estudios/cargar_mediciones.html"
Task T015: "estudios/templates/estudios/cargar_mediciones_confirmar.html"
```

## Parallel Example: User Story 3

```bash
Task T022: "Reglas del servicio en estudios/tests/test_servicio_mediciones.py"
Task T023: "Reglas de vistas en estudios/tests/test_cargar_mediciones.py"
Task T024: "Concurrencia en estudios/tests/test_concurrencia_mediciones.py"
```

---

## Implementation Strategy

### En dos tandas (según `docs/guias/guia-sdd-paso-a-paso.md`)

1. **Tanda 1 (Fases 1 y 2 — `T001` a `T008`)**: aprobación, modelo `Medicion` con su migración,
   `admite_mediciones` y `leer_valor`; suite en verde. Frenar y revisar.
2. **Tanda 2 (Fases 3 a 6 — `T009` a `T033`)**: US1 (cargar, MVP), US2 (validación) y US3
   (reglas, reenvíos y concurrencia), cada una con sus tests escritos primero; cerrar con `ruff`,
   suite completa, recorrido manual y nota en `CLAUDE.md`.
