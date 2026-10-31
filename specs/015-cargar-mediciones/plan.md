# Implementation Plan: Cargar mediciones

**Branch**: `015-cargar-mediciones` | **Date**: 2026-10-31 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/015-cargar-mediciones/spec.md` (US 6.1, SCRUM-53)

## Summary

Primera historia del Epic 6, dentro de la app `estudios`. Un modelo nuevo `Medicion` (uno a uno con
`PruebaEstudio`, `PROTECT`) guarda el valor crudo como `Decimal` exacto junto con los decimales
escritos, la unidad de medición copiada del catálogo, el usuario y la fecha y hora. Desde el
detalle del estudio, **Cargar mediciones** abre un formulario con un campo por prueba `Pendiente`
no calculada; los valores se revisan en una pantalla de confirmación y el servicio
`cargar_mediciones` los guarda con el estudio bloqueado: crea las mediciones, pasa esas pruebas a
`Cargada` y el estudio a "En proceso" con la primera, y omite e informa las pruebas que mientras
tanto quedaron cargadas o se quitaron.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: Django 5.2 LTS (ORM, forms, messages), Tailwind CSS 4 y componentes de
`templates/ui/` (SCRUM-67). Sin JavaScript ni dependencias nuevas.

**Storage**: PostgreSQL 16 en Docker. Tabla nueva `estudios_medicion` (migración
`estudios/migrations/0004_medicion.py`); `estudios_estudio` y `estudios_pruebaestudio` sin cambios
de esquema.

**Testing**: pytest 9.1.1 + pytest-django 4.14.0 con el test client de Django; concurrencia con
`transaction=True` e hilos, como `estudios/tests/test_concurrencia_pruebas.py`; ruff 0.17.1.

**Target Platform**: Contenedor Linux (`web`) con Docker Compose; navegador de escritorio.

**Project Type**: Aplicación web Django monolítica con templates en el servidor (sin SPA).

**Performance Goals**: Cargar un estudio de 10 pruebas en menos de 3 minutos con una sola
confirmación (SC-001): una pantalla con todos los campos y una de confirmación.

**Constraints**: `Decimal` exacto con hasta 12 cifras enteras y 6 decimales, conservando los
decimales escritos (Clarifications, principio IV); nada se guarda si un valor es inválido (FR-007);
una medición por prueba y reenvío idempotente bajo bloqueo de la fila del estudio (FR-012);
confirmación antes de guardar (Interfaz); sesión obligatoria (FR-001); textos en español
(principio VI).

**Scale/Scope**: 1 modelo + migración, 1 propiedad de `Estudio`, 1 módulo con `leer_valor`, 1
formulario, 1 servicio + 1 excepción + 1 resultado, 1 vista, 2 templates nuevos, 1 URL, cambios en
`detalle` (vista y template), nota en `CLAUDE.md` y tests en `estudios/tests/`.

Decisiones en [research.md](./research.md) (R1–R8). No hay `NEEDS CLARIFICATION` pendientes.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Cumplimiento | Estado |
|---|---|---|
| **I. Spec primero (SDD)** | Spec de US 6.1 (SCRUM-53) en `specs/015-cargar-mediciones/spec.md`, clarificada el 2026-10-31; una US por spec y por rama. PR: «US 6.1 – Cargar mediciones». El código espera la aprobación de la spec. | ✅ |
| **II. Simplicidad y Django idiomático** | Modelo, formulario y vista de función de Django; revisar/confirmar por POST sin borrador en sesión (R5). Sin JavaScript ni dependencias. No se agrega app nueva (R1). Nada de US 6.2–6.4 (YAGNI). | ✅ |
| **III. Tests obligatorios** | Cada escenario de aceptación, FR y caso límite tiene test (ver [Mapa de tests](#mapa-de-tests)); `leer_valor` se prueba con casos conocidos y valores esperados explícitos. | ✅ |
| **IV. Integridad de datos** | `DecimalField` (nunca `float`), valor exacto con sus decimales y unidad guardada con la medición. `PROTECT` hacia la asignación y el usuario; una medición por asignación por constraint de la base. Reglas en modelo, formulario y servicio, no en el template. Las mediciones no se modifican ni borran en esta US. | ✅ |
| **V. Seguridad** | `LoginRequiredMiddleware`; guardar solo por POST con CSRF; las asignaciones se buscan dentro del estudio de la URL, así que no se puede cargar en otro estudio cambiando un `medicion_<pk>`. El usuario sale de la sesión, no del formulario. | ✅ |
| **VI. Idioma y consistencia** | Términos del glosario: `Medicion`, `cargar_mediciones`, `admite_mediciones`, `leer_valor`, `CargarMedicionesError`. Interfaz y mensajes en español. ruff. | ✅ |
| **Interfaz (UI)** | Extiende `base.html` con `ui/encabezado.html`, resumen, acciones de confirmación, `ui/errores_form.html` y `ui/estado_vacio.html`; errores junto a cada campo; confirmación antes de guardar; mensajes con `messages`. Sin componentes CSS nuevos (se reutilizan `.tabla`, `.btn-chico`, `campo-error`). | ✅ |

**Post-diseño (Phase 1)**: cumple todos los principios sin excepciones en *Complexity Tracking*.

## Diseño

### Flujo

```text
GET  /estudios/<pk>/                       → detalle: «Cargar mediciones» + columna Medición
GET  /estudios/<pk>/mediciones/cargar/     → formulario (302 detalle si el estudio no admite carga)
POST                     accion=revisar    → formulario con errores | confirmación
POST                     accion=editar     → formulario con los valores
POST                     accion=confirmar  → cargar_mediciones() → 302 detalle + mensajes
```

Rutas, condiciones y mensajes exactos en
[contracts/cargar-mediciones-ui.md](./contracts/cargar-mediciones-ui.md); modelo y reglas en
[data-model.md](./data-model.md).

### Lectura del valor (`estudios/mediciones.py`)

```text
leer_valor(texto) -> Decimal | None     # None si está vacío; ValidationError si es inválido (R4)
```

### Formulario (`estudios/forms.py`)

```text
CargarMedicionesForm(data=None, *, asignaciones)
├── campos medicion_<asignacion_pk> (CharField opcional, inputmode="decimal")
├── clean(): leer_valor por campo; error general si no hay ningún valor
├── filas()               -> [(asignacion, bound_field)]   # para la tabla
├── valores()             -> {asignacion_pk: Decimal}      # solo los no vacíos
└── pruebas_quitadas()    -> int    # medicion_<pk> enviados con valor que no son del estudio
```

### Servicio (`estudios/servicios.py`)

```text
CargarMedicionesError(Exception)
ResultadoCarga(guardadas: list[Medicion], omitidas: list[tuple[Prueba, str]])

cargar_mediciones(estudio_pk, valores, usuario) -> ResultadoCarga
```

Sesión activa → `transaction.atomic()` → `select_for_update()` del estudio → `admite_mediciones` →
asignaciones del estudio con `select_for_update(of=("self",))` → por cada una en orden de código:
omitir (no está / no `Pendiente` / calculada) o crear `Medicion` y pasar a `Cargada` → estudio a
"En proceso" si corresponde (R6).

### Vista (`estudios/views.py`)

`cargar_mediciones(request, pk)` según el contrato. Llama a `servicios.cargar_mediciones` (en los
tests se parchea `estudios.servicios.cargar_mediciones`, como en US 5.3/5.4). `detalle` suma
`select_related("medicion", "medicion__cargada_por")` y `pruebas_para_medir` al contexto.

### Mapa de tests

| Escenario / requisito | Test | Archivo |
|---|---|---|
| FR-001, US3 Esc. 6 — sesión obligatoria (GET y POST); estudio inexistente 404 | `test_cargar_mediciones_requiere_sesion`, `test_cargar_mediciones_estudio_inexistente_404` | `test_cargar_mediciones.py` |
| US1 Esc. 1, FR-002 — detalle ofrece «Cargar mediciones» solo si corresponde | `test_detalle_ofrece_cargar_mediciones` (parametrizado: sin pendientes, solo calculadas, estudio cerrado) | `test_cargar_mediciones.py` |
| US1 Esc. 2, FR-004 — lista pendientes con código, nombre y unidad («Sin unidad») | `test_formulario_lista_pendientes_con_unidad` | `test_cargar_mediciones.py` |
| US3 Esc. 1, FR-004 — calculadas sin campo | `test_formulario_muestra_calculadas_sin_campo` | `test_cargar_mediciones.py` |
| US3 Esc. 2 — sin pruebas para medir | `test_formulario_sin_pruebas_para_medir` | `test_cargar_mediciones.py` |
| US1 Esc. 3, FR-008 — revisar muestra resumen sin guardar; editar conserva valores | `test_revisar_muestra_resumen_sin_guardar`, `test_editar_conserva_valores` | `test_cargar_mediciones.py` |
| US1 Esc. 4, FR-009/010/013 — confirmar guarda, pasa a Cargada e informa | `test_confirmar_guarda_mediciones`, `test_cargar_mediciones_guarda_valor_unidad_usuario_y_fecha` | `test_cargar_mediciones.py`, `test_servicio_mediciones.py` |
| US1 Esc. 4–5, FR-005 — carga parcial; la próxima carga ofrece solo pendientes | `test_carga_parcial_deja_pendientes`, `test_formulario_no_ofrece_cargadas` | `test_servicio_mediciones.py`, `test_cargar_mediciones.py` |
| US1 Esc. 5, FR-014 — detalle muestra valor, unidad, usuario y fecha | `test_detalle_muestra_medicion` | `test_cargar_mediciones.py` |
| US1 Esc. 6, FR-011 — primera medición pasa el estudio a En proceso; ya no admite agregar/quitar | `test_primera_medicion_pasa_estudio_a_en_proceso`, `test_estudio_en_proceso_no_ofrece_agregar_ni_quitar` | `test_servicio_mediciones.py`, `test_cargar_mediciones.py` |
| US2 Esc. 1–4, FR-006 — formatos válidos e inválidos, espacios, decimales y tamaño | `test_leer_valor_validos`, `test_leer_valor_invalidos` (parametrizados con la tabla del contrato) | `test_servicio_mediciones.py` |
| US2 Esc. 1, Clarifications — se conservan los decimales escritos (`7,20`) | `test_valor_ingresado_conserva_ceros_finales` | `test_modelos.py` |
| US2 Esc. 2, FR-007 — un valor inválido: error junto al campo, valores conservados, nada guardado | `test_revisar_con_valor_invalido_no_guarda`, `test_confirmar_con_valor_invalido_no_guarda` | `test_cargar_mediciones.py` |
| US2 Esc. 3 — envío vacío | `test_revisar_sin_valores_pide_al_menos_uno` | `test_cargar_mediciones.py` |
| US3 Esc. 3, FR-003 — estudio Finalizado o Informe generado rechaza | `test_estudio_cerrado_rechaza_carga` (parametrizado; servicio y vista) | `test_servicio_mediciones.py`, `test_cargar_mediciones.py` |
| US3 Esc. 4, FR-012 — reenvío: no se reemplaza ni duplica, se informa y el resto se guarda | `test_reenvio_informa_ya_cargada`, `test_omite_cargada_y_guarda_el_resto` | `test_cargar_mediciones.py`, `test_servicio_mediciones.py` |
| US3 Esc. 5 — prueba quitada después de abrir el formulario | `test_confirmar_prueba_quitada_se_informa` | `test_cargar_mediciones.py` |
| FR-004 — el servicio no carga calculadas ni asignaciones de otro estudio | `test_servicio_omite_calculada`, `test_servicio_ignora_asignacion_de_otro_estudio` | `test_servicio_mediciones.py` |
| FR-015 — no cambia muestra, tipo, snapshots, catálogo ni otros estudios; unidad conservada si cambia el catálogo | `test_cargar_no_modifica_otros_datos`, `test_unidad_conservada_tras_cambio_en_catalogo` | `test_servicio_mediciones.py` |
| Edge — cargas simultáneas de la misma prueba guardan una | `test_cargas_concurrentes_misma_prueba` (`transaction=True`, hilos) | `test_concurrencia_mediciones.py` |
| Edge — carga y quita simultáneas: nunca medición de prueba quitada | `test_carga_y_quita_concurrentes` (`transaction=True`, hilos) | `test_concurrencia_mediciones.py` |
| R2 — `PROTECT`: no se borra una asignación con medición | `test_asignacion_con_medicion_protegida` | `test_modelos.py` |
| Falla de base no informa éxito ni guarda nada | `test_error_de_base_al_cargar_no_guarda` | `test_cargar_mediciones.py` |

## Project Structure

### Documentation (this feature)

```text
specs/015-cargar-mediciones/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── cargar-mediciones-ui.md
├── checklists/
│   └── requirements.md
└── tasks.md              # /speckit-tasks
```

### Source Code (repository root)

```text
CLAUDE.md                                   # + sección «Carga de mediciones (US 6.1)»; nota Epic 6 actualizada
estudios/
├── models.py                               # + Medicion, Estudio.admite_mediciones
├── migrations/0004_medicion.py             # nueva
├── mediciones.py                           # nuevo: leer_valor
├── forms.py                                # + CargarMedicionesForm
├── servicios.py                            # + CargarMedicionesError, ResultadoCarga, cargar_mediciones
├── views.py                                # + cargar_mediciones; detalle con medición y pruebas_para_medir
├── urls.py                                 # + <int:pk>/mediciones/cargar/
├── templates/estudios/
│   ├── detalle.html                        # + botón «Cargar mediciones» y columna Medición
│   ├── cargar_mediciones.html              # nuevo
│   └── cargar_mediciones_confirmar.html    # nuevo
└── tests/
    ├── conftest.py                         # + prueba calculada, prueba sin unidad, estudio con ellas
    ├── test_modelos.py                     # + Medicion
    ├── test_servicio_mediciones.py         # nuevo: leer_valor y servicio
    ├── test_cargar_mediciones.py           # nuevo: vistas
    └── test_concurrencia_mediciones.py     # nuevo
```

**Structure Decision**: todo dentro de la app `estudios` (R1), extendiendo los archivos de US 5.2–5.4.
Los tests de la US van en archivos propios.

## Complexity Tracking

Sin violaciones de la constitution.
