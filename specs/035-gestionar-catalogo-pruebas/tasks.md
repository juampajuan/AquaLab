---

description: "Lista de tareas de SCRUM-73 – Gestionar catálogo de pruebas"
---

# Tasks: Gestionar catálogo de pruebas

**Input**: `specs/035-gestionar-catalogo-pruebas/` (`plan.md`, `spec.md`, `research.md`,
`data-model.md`, `contracts/catalogo-ui.md`, `quickstart.md`)

**Prerequisites**: `main` con el panel 025 (`usuarios/permisos_administracion.py`:
`administracion_requerida`, `autorizar_administracion`; listado `administracion:pruebas`; fixtures
`grupo_administradores` y `administrador_panel` en `usuarios/tests/conftest.py`), la gestión de tipos
de estudio (US 5.5: `estudios/gestion_tipos.py`, `confirmaciones_tipos.py`, `views_tipos.py`,
`forms_tipos.py`), `pruebas/models.py` (`Prueba.clean()`, `esta_en_uso()`, `referencias_formula`,
`LimiteVertido`), `pruebas/limites.py` (`NUMERO`, `TEXTOS_AUSENTE`, `leer_limite`) y las fixtures de
`estudios/tests/conftest.py` (`catalogo`, `estudio_de`, `bioquimico`).

**Tests**: SÍ (constitution, principio III). Siguen el «Mapa de tests» de `plan.md` y se escriben
**antes** de la implementación de cada historia (deben fallar primero).

**Organization**: US1 (P1, alta), US2 (P1, editar o eliminar sin uso), US3 (P1, editar en uso), US4
(P2, desactivar y reactivar), US6 (P2, reemplazar en cascada) y US5 (P2, solo Administradores).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: se puede ejecutar en paralelo (archivos distintos, sin dependencias pendientes)
- **[Story]**: user story a la que pertenece (`[US1]` a `[US6]`)
- Rutas relativas a la raíz del repo

## Convenciones para todas las tareas

- Textos y mensajes en **español**, copiados **literalmente** de `contracts/catalogo-ui.md`.
- Todas las reglas viven en `pruebas/gestion.py:gestionar_prueba` (research R3); las vistas solo
  arman formularios, resúmenes y mensajes. El servicio se revalida siempre, aunque la vista ya haya
  filtrado.
- Confirmación y concurrencia con el patrón de `estudios/confirmaciones_tipos.py` (research R2).
- Componentes de `templates/ui/` (`encabezado`, `campo`, `ayuda`, `estado`, `acciones_confirmacion`);
  si se agregan clases, recompilar el CSS (T027).
- Commits a nombre de la responsable, sin `Co-Authored-By`.
- Comandos dentro de Docker: `docker compose exec web pytest pruebas estudios usuarios`,
  `ruff check .`, `ruff format --check .`.

---

## Phase 1: Setup

- [ ] T001 **Gate de la constitution (principio I)**: confirmar que el equipo aprobó
  `specs/035-gestionar-catalogo-pruebas/spec.md` y actualizar su `**Status**` a «Aprobada (fecha)»;
  confirmar que la rama sale de `main` actualizado y que `pytest` está en verde.
- [ ] T002 Crear `pruebas/urls.py` (`app_name = "catalogo"`, vacío por ahora) e incluirlo en
  `config/urls.py` en `path("administracion/pruebas/", include("pruebas.urls"))`, **después** de
  `administracion/` para no tapar `administracion:pruebas`.

---

## Phase 2: Foundational (bloquea las cinco historias)

- [ ] T003 Modelo y migración (data-model.md): en `pruebas/models.py` agregar a `Prueba`
  «`version = PositiveBigIntegerField(default=1)`» (con `CheckConstraint version >= 1`),
  «`reemplazada_por`: FK a `Prueba`, `on_delete=PROTECT`, `null=True`, `blank=True`, `editable=False`,
  `related_name="reemplaza_a"`»,
  «`creada_por` y `modificada_por`: FK a usuario, `on_delete=PROTECT`, `null=True`, `blank=True`,
  `editable=False`, `related_name="+"`» y «`fecha_creacion` y `fecha_modificacion`:
  `DateTimeField(null=True, blank=True, editable=False)`». Generar
  `pruebas/migrations/0003_gestion_catalogo.py`. Comprobar que `importar_catalogo_pruebas` y sus
  tests siguen pasando sin cambios.
- [ ] T004 [P] `pruebas/formularios.py` (research R4/R8) con `validar_limite(texto)` («Escribí un
  número o “Ausente”.») y `validar_rango(minimo, maximo)` («El mínimo no puede superar al
  máximo.»), `PruebaForm` (código, nombre, tipo de cálculo, fórmula, unidad de medición, unidad del
  resultado, límites generales, norma, límite de detección, observación; `disabled` en los campos del
  método cuando se construye con `bloquear_metodo=True`; ayudas US 9.1 en fórmula, límites y LD) y
  `LimitesVertidoForm` (cloacal y canal: mín, máx, norma). Tests en `pruebas/tests/test_formularios.py`:
  `test_limites_validos` (parametrizado: "", "350", "0,5", "Ausente", "ausencia" válidos; "NE",
  "SOE", "35O", "Ph-0,2" inválidos; mín 10 > máx 5 inválido; mín "Ausente" con máx número válido).
- [ ] T005 [P] `pruebas/confirmaciones.py` adaptando `estudios/confirmaciones_tipos.py` (salts
  propios `"pruebas.contexto.v1"`, `"pruebas.confirmacion.v1"`, clave de sesión
  `"pruebas_pendientes"`): `crear_contexto`, `leer_contexto`, `preparar(request, operacion, prueba_id,
  version, datos, resumen)` y `leer_borrador`.
- [ ] T006 Esqueleto de `pruebas/gestion.py` (research R3/R5): errores `GestionPruebaError`,
  `NoAutorizado`, `PruebaNoExiste`, `DatosInvalidos(errores)`, `VersionDesactualizada`, `PruebaEnUso`,
  `PruebaReferenciada(codigos)`; `dependientes(prueba)` (pruebas cuya fórmula referencia
  `{CODIGO}`); `tipos_afectados(prueba)` (tipos activos que la incluyen y si les queda otra activa);
  `dependencias_inactivas()` (`{prueba_id: [códigos inactivos que referencia]}` para pruebas activas);
  y `gestionar_prueba(*, usuario, operacion, prueba_id=None, version_esperada=None, datos=None)` que
  hace `autorizar_administracion`, `transaction.atomic()`, `select_for_update` y control de versión.
  Tests en `pruebas/tests/test_gestion.py`: `test_dependientes` y `test_version_desactualizada`.

---

## Phase 3: User Story 1 – Dar de alta una prueba (P1) 🎯 MVP

**Goal**: crear pruebas Directas y de Fórmula con límites por vertido, con resumen previo.

**Independent Test**: `quickstart.md` paso 1.

- [ ] T007 [P] [US1] En `pruebas/tests/test_gestion.py`: `test_alta_directa_y_formula` (crea activas,
  `es_calculada` deducido, límites por vertido guardados, `creada_por`/`fecha_creacion` completos,
  `version == 1`) y `test_alta_rechaza` (parametrizado: fórmula inválida, que referencia una prueba
  inexistente o a sí misma; tipo Fórmula sin fórmula; código repetido con otras mayúsculas; límite
  «NE»; mín > máx) → `DatosInvalidos` con el mensaje junto al campo y sin filas nuevas.
- [ ] T008 [P] [US1] En `pruebas/tests/test_vistas.py`: `test_alta_por_pantalla` (GET formulario →
  POST → resumen → confirmar → 302 a la ficha con «Prueba creada.»; «Cancelar» vuelve con los datos;
  tipo Directo descarta la fórmula).
- [ ] T009 [US1] Implementar `crear` en `pruebas/gestion.py` (normaliza, valida límites con
  `formularios`, `full_clean()` para fórmula y código, deduce `es_calculada`, crea `LimiteVertido`
  para los vertidos con algún dato) y las vistas `nueva` y `confirmar` en `pruebas/views.py` +
  `pruebas/urls.py` + `pruebas/templates/pruebas/formulario.html` y `confirmar.html` (resumen con
  `ui/acciones_confirmacion.html`). Hace pasar T007 y T008.
- [ ] T010 [US1] Vista `ficha` en `pruebas/views.py` + `pruebas/templates/pruebas/ficha.html` (datos,
  límites por vertido, «Creada por … el …» / «Modificada por … el …» o «Sin registro», en uso o no,
  acciones según `data-model.md`).

**Checkpoint**: se pueden crear pruebas desde la app.

---

## Phase 4: User Story 2 – Editar o eliminar una prueba sin uso (P1)

**Goal**: editar todo y eliminar pruebas sin uso, respetando las referencias en fórmulas.

**Independent Test**: `quickstart.md` paso 2.

- [ ] T011 [P] [US2] En `pruebas/tests/test_gestion.py`: `test_sin_uso_edita_todo` (cambia código,
  nombre, tipo, fórmula y unidades; `modificada_por`/`fecha_modificacion`; `version` sube; pasar a
  Directo vacía la fórmula), `test_sin_uso_elimina` (borra prueba y `LimiteVertido`) y
  `test_referenciada` (otra prueba la usa: eliminar y cambiar el código → `PruebaReferenciada` con
  los códigos; editar el resto sí).
- [ ] T012 [US2] Implementar `editar` (sin uso) y `eliminar` en `pruebas/gestion.py` y las vistas
  `editar` y `eliminar` (si no se puede, 302 a la ficha con el motivo). Hace pasar T011.

---

## Phase 5: User Story 3 – Editar una prueba en uso sin alterar el historial (P1)

**Goal**: en uso solo se editan límites, norma, LD y observación; el historial no cambia.

**Independent Test**: `quickstart.md` paso 3.

- [ ] T013 [P] [US3] En `pruebas/tests/test_gestion.py`: `test_en_uso_solo_limites` (edita límites
  generales y por vertido, norma, LD y observación), `test_en_uso_bloquea_metodo` (parametrizado:
  código, nombre, tipo, fórmula, unidades → `PruebaEnUso`, sin cambios; también si pasó a estar en
  uso entre abrir y confirmar), `test_en_uso_no_elimina` y `test_historial_intacto` (estudio con
  Cloruro validado e informe emitido; cambiar `limite_max` → `Validacion` y `Informe.contenido`
  iguales; una validación nueva usa el límite nuevo).
- [ ] T014 [P] [US3] En `pruebas/tests/test_vistas.py`: `test_ficha_en_uso` (mensaje de bloqueo,
  campos del método `disabled`, sin «Eliminar») y `test_envio_alterado` (POST con un campo bloqueado
  cambiado → error, sin cambios).
- [ ] T015 [US3] Implementar las reglas «en uso» en `editar` de `pruebas/gestion.py` (compara el
  método actual con el enviado y rechaza cambios) y `bloquear_metodo` en la vista `editar`. Hace pasar
  T013 y T014.

---

## Phase 6: User Story 4 – Desactivar y reactivar (P2)

**Goal**: retirar pruebas sin perder historial, con avisos, y aplicar «activa» en el resto de la app.

**Independent Test**: `quickstart.md` pasos 4–5.

- [ ] T016 [P] [US4] En `estudios/tests/test_catalogo_activas.py`: `test_inactiva_no_se_ofrece`
  (formulario de tipos y `AgregarPruebaForm` sin la inactiva; al editar un tipo que ya la tiene,
  aparece marcada y se conserva; agregarla a un tipo o a un estudio por POST → rechazado),
  `test_estudio_nuevo_solo_activas` (estudio nuevo de un tipo con una inactiva no la incluye; tipo sin
  activas → «El tipo de estudio no tiene pruebas activas.»; reactivar un tipo sin activas → rechazado)
  y `test_estudio_existente_sigue` (estudio con la prueba ya asignada: cargar, calcular, corregir,
  validar y emitir informe después de desactivarla) y `test_confirmacion_vieja_se_rechaza` (abrir la
  confirmación de crear estudio, desactivar una prueba del tipo, confirmar → «el tipo cambió», sin
  estudio nuevo; la `version` de los tipos que la incluyen subió).
- [ ] T017 [P] [US4] En `pruebas/tests/test_vistas.py`: `test_avisos_desactivar` (confirmación lista
  las pruebas activas que la usan en su fórmula y los tipos activos que la incluyen, marcando «Este
  tipo no se va a poder usar»), `test_desactivar_y_reactivar` (mensajes, `modificada_por`, `version`; reactivar una prueba cuya
  fórmula usa una inactiva muestra «Usa en su fórmula una prueba inactiva: …»)
  y `test_listado` (marca «Depende de una prueba inactiva: CA» en `MG`, «Nueva prueba», «Ver ficha»
  en lugar de «Editar en Django Admin»).
- [ ] T018 [US4] Implementar `desactivar` y `reactivar` en `pruebas/gestion.py` y sus vistas con los
  avisos de `dependientes`, `tipos_afectados` y, al reactivar, de las pruebas inactivas que usa en su
  fórmula; en la misma transacción, subir `version` de cada `TipoEstudio` que la incluye
  (`select_for_update`, research R7). Hace pasar la parte de T017 y `test_confirmacion_vieja_se_rechaza`.
- [ ] T019 [US4] Aplicar «activa» en `estudios` (research R7): `estudios/forms_tipos.py` (activas +
  ya incluidas marcadas), `estudios/gestion_tipos.py` (rechaza agregar inactivas; reactivar exige una
  activa), `estudios/forms.py:AgregarPruebaForm`, `estudios/servicios.py:agregar_prueba` y
  `estudios/catalogo.py:configuracion_bloqueada` (solo activas; mensaje nuevo). Hace pasar T016.
- [ ] T020 [US4] Listado en `usuarios/views_administracion.py:pruebas` y
  `usuarios/templates/usuarios/administracion/pruebas.html`: «Nueva prueba», «Ver ficha» a
  `catalogo:ficha` y marca con `gestion.dependencias_inactivas()`. Hace pasar el resto de T017.

---

## Phase 6b: User Story 6 – Reemplazar una prueba en cascada (P2)

**Goal**: al desactivar, «Reemplazar por» actualiza fórmulas y tipos; los estudios viejos calculan igual.

**Independent Test**: spec US6 (MG con `{CA}`, reemplazar CA por CA2).

- [ ] T020a [P] [US6] En `pruebas/tests/test_reemplazo.py`: `test_candidatas` (solo activas, misma
  unidad, ni ella ni sus dependientes directas o indirectas; envío con una incompatible → rechazo),
  `test_cascada` (fórmula de MG pasa de `{CA}` a `{CA2}` aunque MG esté en uso; tipos con CA pasan a
  CA2 o la pierden si ya tenían CA2; `version` de pruebas y tipos sube; `CA.reemplazada_por == CA2`;
  todo en una transacción: si falla un paso, nada cambia) y `test_resumen_reemplazo` (la confirmación
  lista fórmulas y tipos afectados).
- [ ] T020b [P] [US6] En `estudios/tests/test_calculo_reemplazos.py`: `test_recalculo_con_reemplazo`
  (estudio viejo con CA y MG calculado; reemplazar CA por CA2; corregir la medición de CA → MG se
  recalcula con el valor de CA, mismo resultado que antes con el valor nuevo; validaciones e informes
  previos iguales), `test_estudio_nuevo_usa_reemplazo` (estudio nuevo trae CA2 y calcula MG) y
  `test_cadena` (A→B→C: un estudio con A calcula una fórmula que nombra C).
- [ ] T020c [US6] Implementar el reemplazo en `pruebas/gestion.py` (operación `desactivar` con
  `reemplazo_id`, research R11), el selector y el resumen en la vista y el template de desactivar.
  Hace pasar T020a.
- [ ] T020d [US6] Implementar `calculo.resolver_referencias(asignaciones)` en `estudios/calculo.py` y
  usarlo en la evaluación, el orden de dependencias y `calculo.afectadas`. Correr toda la suite de
  `estudios` (cálculo, corrección, borrado, validación). Hace pasar T020b.

---

## Phase 7: User Story 5 – Solo Administradores (P2)

**Goal**: 403 para todos menos «Administradores» con el permiso del panel.

- [ ] T021 [P] [US5] En `pruebas/tests/test_vistas.py`: `test_acceso` (parametrizado sobre las 8 rutas
  del contrato: sin sesión → login; usuario común, bioquímico y superusuario fuera del grupo → 403 sin
  cambios; `administrador_panel` → 200/302) y `test_servicio_revalida` (`gestionar_prueba` con un
  usuario sin permiso → `NoAutorizado`).
- [ ] T022 [US5] `@administracion_requerida` en todas las vistas de `pruebas/views.py` (y
  `require_GET`/`require_POST` según el contrato). Hace pasar T021.

---

## Phase 8: Polish & Cross-Cutting Concerns

- [ ] T023 [P] `test_auditoria` en `pruebas/tests/test_gestion.py` (creada/modificada por y fecha en
  cada operación; ficha con «Sin registro» para una prueba importada).
- [ ] T024 [P] `CLAUDE.md`: sección «Gestión del catálogo (SCRUM-73)» (`gestionar_prueba` única
  escritura con reglas; límites solo números o «Ausente» en la app, no en el CSV; «Ausente» vs máx.
  0; `activa` en tipos, agregar prueba y crear estudio; admin de Django como respaldo; versión y
  tokens como en tipos; reemplazo en cascada y `calculo.resolver_referencias`).
- [ ] T025 Comprobar que los tests existentes de `pruebas` (importación, admin, límites) y de
  `estudios` (tipos, crear estudio, agregar prueba) siguen en verde; ajustar solo los que dependan del
  enlace «Editar en Django Admin» del listado.
- [ ] T026 Ejecutar `ruff check .`, `ruff format --check .` y `python manage.py makemigrations --check
  --dry-run`.
- [ ] T027 Recompilar Tailwind; si `static/css/aqualab.css` cambia, commitearlo.
- [ ] T028 Ejecutar la suite completa `docker compose exec web pytest`: todo en verde.
- [ ] T029 Recorrer `specs/035-gestionar-catalogo-pruebas/quickstart.md` (pasos 1 a 6) y marcar el
  resultado aquí.

---

## Dependencies & Execution Order

- **Setup (T001–T002)** → **Foundational (T003–T006)** → historias.
- **US1 (T007–T010)** crea el formulario, la confirmación y la ficha que usan US2–US4.
- **US2 (T011–T012)** y **US3 (T013–T015)** comparten `editar` en `gestion.py`: van en orden.
- **US4 (T016–T020)**: T019 (cambios en `estudios`) y T020 (listado) son independientes de las
  vistas de pruebas y pueden hacerse en paralelo con T018.
- **US6 (T020a–T020d)** depende de T018 (desactivar) y T019; T020d toca el cálculo: hacerlo con la
  suite de `estudios` a mano.
- **US5 (T021–T022)** puede hacerse en cualquier momento después de T009.
- **Polish (T023–T029)** al final.

## Parallel Example

```text
# Base
T004 (formularios.py), T005 (confirmaciones.py)
# Tests de cada historia
T007 + T008, T013 + T014, T016 + T017, T021
# US4
T018 (pruebas), T019 (estudios), T020 (usuarios)
```

## Implementation Strategy

1. **MVP = US1**: dar de alta pruebas desde la app (reemplaza el admin para lo más común).
2. **US2 y US3** completan la edición segura; **US4** suma desactivar y aplica «activa» en el resto
   de la app; **US5** asegura el acceso (aunque `administracion_requerida` se pone desde T009).
3. Auditoría, documentación, controles del CI, suite completa y recorrido manual.
