---

description: "Lista de tareas de SCRUM-78 – Datos de demo"
---

# Tasks: Datos de demo

**Input**: `specs/026-datos-demo/` (`plan.md`, `spec.md`, `research.md`, `data-model.md`,
`contracts/cargar-demo-cli.md`, `quickstart.md`)

**Prerequisites**: `main` con la US 7.3 (firma `FirmaProfesional`, `emitir_informe` que exige firma
y la copia en `contenido["firma"]`), el panel 025 (grupo «Administradores», migración
`usuarios.0004`), el grupo «Bioquímicos» con `validar_resultados` y `emitir_informes`, el
importador `importar_catalogo_pruebas` y los servicios `registrar_muestra`, `crear_estudio`,
`cargar_mediciones`, `validar_resultados` y `emitir_informe`. Fixture `catalogo` en
`estudios/tests/conftest.py`.

**Tests**: SÍ. La constitution (principio III) exige un test por escenario. Siguen el «Mapa de
tests» de `plan.md` y se escriben **antes** de la implementación de cada historia (deben fallar
primero).

**Organization**: US1 (P1, la demo completa), US2 (P1, usuarios demo) y US3 (P2, solo en desarrollo
y sin duplicar).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: se puede ejecutar en paralelo (archivos distintos, sin dependencias pendientes)
- **[Story]**: user story a la que pertenece la tarea (`[US1]`, `[US2]`, `[US3]`)
- Rutas relativas a la raíz del repo

## Convenciones para todas las tareas

- Mensajes del comando en **español**, copiados **literalmente** de `contracts/cargar-demo-cli.md`.
- Guion, valores y fechas exactamente como `data-model.md` y `research.md` (R3, R4, R8, R9).
- Los datos se crean **solo** con los servicios reales, cada paso dentro de `reloj(fecha)` para que
  las filas nazcan con su fecha (R2). **Nunca** se modifica una fila después de creada (principio IV). Nunca `float`: valores como texto de
  `Decimal`.
- Los tests llaman a la función `estudios.demo.cargar_demo(...)` o a
  `call_command("cargar_demo")` con `settings.DEBUG = True` y
  `monkeypatch.setenv("AQUALAB_ENTORNO", "desarrollo")`; un fixture `demo` en
  `estudios/tests/test_demo.py` carga una vez por test.
- Commits a nombre de la responsable, sin `Co-Authored-By`.
- Comandos dentro de Docker: `docker compose exec web pytest estudios/tests/test_demo.py`,
  `docker compose exec web ruff check .`, `docker compose exec web ruff format --check .`.

---

## Phase 1: Setup

- [ ] T001 **Gate de la constitution (principio I)**: confirmar que el equipo aprobó
  `specs/026-datos-demo/spec.md` y actualizar su `**Status**` a «Aprobada (fecha)». Confirmar que
  la rama `026-datos-demo` sale de `main` actualizado y que `docker compose exec web pytest` está en
  verde.
- [ ] T002 [P] Agregar `AQUALAB_ENTORNO=desarrollo` a `.env.example` con un comentario: «Habilita
  comandos solo de desarrollo, como cargar_demo. No definir en producción.».

---

## Phase 2: Foundational (bloquea las tres historias)

- [ ] T003 Crear `estudios/demo.py` con el esqueleto según research R2–R5: constantes
  `DOMINIO = "demo.aqualab"`, `CONTRASENA = "Demo-1234"`, `CLAVE_LOCK_DEMO = 7_800_001`, la
  excepción `DemoError`, `class Fechas` (calcula muestreo, ingreso, estudio, carga, validación y
  emisión de un `(origen, mes)` con los desplazamientos fijos del guion, hora 10:00 de
  `America/Argentina/Buenos_Aires`, cada fecha `≤ ahora` y `≥` la anterior; recibe `ahora` para
  poder probarla; el estancado recorta su carga a `ahora − 10 días`), `clave(origen, mes, paso)` con
  `uuid5`, y el administrador de contexto `reloj(fecha)` que, con `unittest.mock.patch`, hace que
  `django.utils.timezone.now` devuelva `fecha` mientras dura el bloque. Agregar en
  `estudios/tests/test_demo.py` `test_fechas_ordenadas_y_no_futuras` (para `Fechas` con un `ahora`
  de día 2 y otro de fin de mes; el estancado queda ≥ 10 días antes de `ahora`) y `test_reloj` (un
  `Estudio` creado dentro de `reloj(f)` tiene `fecha_creacion == f`; fuera del bloque se usa la
  hora real).

---

## Phase 3: User Story 1 – Cargar una demo completa con un comando (P1) 🎯 MVP

**Goal**: con la base de desarrollo migrada, `cargar_demo` deja 6 meses de actividad con estudios en
los cuatro estados, informes firmados, fuera de norma y el desvío de «Pozo 2».

**Independent Test**: base recién migrada → ejecutar el comando → verificar clientes, orígenes,
muestras por mes, estados, informes, fuera de norma y el desvío (ver `quickstart.md` pasos 1, 4 y 5).

### Tests (escribir primero; deben fallar)

- [ ] T004 [P] [US1] En `estudios/tests/test_demo.py`: `test_clientes_origenes_y_muestras` (3
  clientes con correo `@demo.aqualab`, nombres sin «DEMO»; 7 orígenes; por origen una muestra en cada
  uno de los últimos 6 meses, incluido el actual), `test_tipos_demo` (los 3 tipos con exactamente
  las pruebas de research R8), `test_estudios_por_estado` (cada estado con ≥ 2 estudios; estados por
  origen y mes iguales a la tabla «Estado destino por mes» de `data-model.md`) y
  `test_informes_firmados_y_numeracion` (cada informe con `contenido["firma"]` del bioquímico y
  matrícula «MP 0000 (DEMO)»; N° PI e INF correlativos sin huecos).
- [ ] T005 [P] [US1] En `estudios/tests/test_demo.py`: `test_fechas_coherentes` (para cada estudio:
  ingreso ≤ creación ≤ carga ≤ validación ≤ emisión ≤ ahora; muestras repartidas en 6 meses
  calendario distintos; al menos 5 meses con informes; tiempos ingreso → emisión distintos entre
  sí), `test_alertas_del_dashboard` (con `ahora` en el día 2 del mes: «Pozo domiciliario» mes −1 En
  proceso con última carga hace > 7 días; «Escuela N° 12» mes −1 Finalizado sin informe), `test_fuera_de_norma_ld_y_presencia`
  (validaciones fuera de norma en ≥ 3 orígenes; SS10 de «Salida a colectora» con resultado 0.05 y
  texto «< 0,1» en su informe; E. coli Presente en «Tanque domiciliario» mes −3) y
  `test_desvio_en_pozo_2` (Cloruro de «Pozo 2»: validados 118–124 en meses −5 a −2, 415 validado en
  −1 con ≥ 3 × el promedio de los 3 anteriores; mes actual 430 calculado y sin validar).
- [ ] T006 [P] [US1] En `estudios/tests/test_demo.py`: `test_valores_reproducibles` (cargar dentro de un
  `transaction.atomic()` que termina con `transaction.set_rollback(True)`, tomar el resumen de
  clientes, orígenes, valores de medición y evaluaciones; volver a cargar y comparar los resúmenes), `test_resumen` (salida con
  «Demo cargada.», cantidades por estado y los dos usuarios con `Demo-1234`) y
  `test_respeta_datos_existentes` (un cliente, una muestra y un informe previos quedan iguales; los
  N° PI e INF de la demo continúan desde los existentes).

### Implementation

- [ ] T007 [US1] En `estudios/demo.py`, el guion fijo de `data-model.md`: clientes (nombre, tipo y
  número de documento del rango ficticio, correo `@demo.aqualab`), orígenes con su `dia_base`,
  tipo de vertido y tipo(s) de estudio, valores por prueba y mes (texto decimal; A/P como 0/1) y
  estado destino por `(origen, mes)`, incluidos los casos especiales (fuera de norma, SS10 0.05,
  E. coli Presente, desvío R9, estancado y Finalizado sin informe).
- [ ] T008 [US1] En `estudios/demo.py`, `asegurar_tipos()` (crea los 3 tipos con
  `TipoEstudio` + `TipoEstudioPrueba` o reutiliza uno igual) y `cargar_estudio(origen, mes, ...)`:
  `registrar_muestra` → `crear_estudio` → `cargar_mediciones` (técnico; todas o solo algunas según
  el estado destino) → `validar_resultados` con `{pk: str(resultado.valor)}` (bioquímico) →
  `emitir_informe` (bioquímico), cada paso dentro de `reloj(fecha del paso)`. Hace pasar T004 y T005.
- [ ] T009 [US1] En `estudios/demo.py`, `cargar_demo(stdout)` que recorre el guion en orden de mes
  (del más antiguo al actual) y devuelve el resumen; crear
  `estudios/management/commands/cargar_demo.py` (delgado: entorno, `transaction.atomic()`,
  `pg_advisory_xact_lock(CLAVE_LOCK_DEMO)`, llama a `cargar_demo` e imprime el resumen del
  contrato). Hace pasar T006.

**Checkpoint**: la demo se carga completa en una base nueva (sin las validaciones de US3 todavía).

---

## Phase 4: User Story 2 – Usuarios demo para cada rol (P1)

**Goal**: técnico y bioquímico demo con sus permisos, firma y trabajo pendiente.

**Independent Test**: iniciar sesión con cada uno y verificar permisos, firma y pendientes
(`quickstart.md` pasos 3 y 6).

- [ ] T010 [P] [US2] En `estudios/tests/test_demo.py`: `test_usuarios_demo` (técnico sin grupos y sin
  `validar_resultados`/`emitir_informes`; bioquímico en «Bioquímicos» y «Administradores» con
  `FirmaProfesional` válida para `informes.firmas.leer_firma` y matrícula «MP 0000 (DEMO)»; ambos
  activos, aprobados y con `check_password("Demo-1234")`; mediciones `cargada_por` = técnico,
  validaciones e informes del bioquímico; hay estudios con pruebas Pendientes y Cargadas y
  estudios Finalizados sin informe).
- [ ] T011 [US2] En `estudios/demo.py`, `crear_usuarios()` según research R7: los dos usuarios con
  `set_password(CONTRASENA)`, grupos, y la firma PNG de 600 × 200 en escala de grises con un trazo
  armada con `zlib`/`struct` (≤ 64 KB); volver a leer el bioquímico de la base antes de usarlo.
  Hace pasar T010.

---

## Phase 5: User Story 3 – Solo en desarrollo y sin duplicar (P2)

**Goal**: el comando nunca corre fuera de desarrollo, no duplica, no toma datos ajenos y no deja
nada a medias.

**Independent Test**: los casos de rechazo y repetición del contrato (`quickstart.md` pasos 2, 7 y 8).

- [ ] T012 [P] [US3] En `estudios/tests/test_demo.py`: `test_rechaza_fuera_de_desarrollo`
  (parametrizado: sin `AQUALAB_ENTORNO`, con `qa`, con `DEBUG=False` → `CommandError` con el
  mensaje del contrato y sin filas nuevas), `test_segunda_ejecucion_no_duplica` (mensaje «La demo
  ya está cargada…» y mismas cantidades), `test_conflicto_de_usuario`, `test_conflicto_de_tipo`,
  `test_reutiliza_tipo_igual`, `test_importa_catalogo_si_falta` (sin pruebas → se importa y la demo
  carga), `test_no_reimporta_catalogo` (una prueba editada a mano conserva su nombre),
  `test_falla_no_deja_nada` (parchear `estudios.demo.emitir_informe` para que falle en la tercera
  llamada → `CommandError` «No se pudo cargar la demo…» y ninguna fila de demo) y
  `test_comando_viejo_eliminado` (`call_command("cargar_demo_us51")` → `CommandError` de comando
  desconocido).
- [ ] T013 [US3] En `estudios/management/commands/cargar_demo.py` y `estudios/demo.py`: validación
  de entorno (`AQUALAB_ENTORNO == "desarrollo"`, `settings.DEBUG`, `connection.vendor ==
  "postgresql"`), demo ya cargada (cliente con correo `@demo.aqualab`), conflictos de usuario y de
  tipo, importación del catálogo si `Prueba` está vacía (`call_command("importar_catalogo_pruebas")`),
  y conversión de cualquier error en `CommandError` con los mensajes del contrato. Hace pasar T012.
- [ ] T014 [US3] Borrar `estudios/management/commands/cargar_demo_us51.py` y
  `estudios/tests/test_demo_us51.py`; buscar otras referencias (`grep -rn cargar_demo_us51`) fuera de
  `specs/` y actualizarlas.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [ ] T015 [P] `README.md`: sección «Datos de demo» (agregar `AQUALAB_ENTORNO=desarrollo` al `.env`,
  `docker compose exec web python manage.py cargar_demo`, usuarios y contraseña, cómo empezar de
  cero con `docker compose down -v`).
- [ ] T016 [P] `CLAUDE.md`: sección «Datos de demo (SCRUM-78)» (servicios reales bajo
  `reloj(fecha)`, nunca `update()` de fechas, guion fijo en `estudios/demo.py`, marca `@demo.aqualab`, `AQUALAB_ENTORNO=desarrollo` +
  `DEBUG`, lock `7_800_001`, desvío de «Pozo 2» que usan 8.1 y 8.2).
- [ ] T017 Medir la carga en una base nueva (SC-001: < 1 minuto) y ejecutar
  `docker compose exec web ruff check .`, `ruff format --check .` y
  `python manage.py makemigrations --check --dry-run` (no debe haber migraciones).
- [ ] T018 Ejecutar la suite completa `docker compose exec web pytest`: todo en verde.
- [ ] T019 Recorrer `specs/026-datos-demo/quickstart.md` (pasos 1 a 8) y marcar el resultado aquí.

---

## Dependencies & Execution Order

- **Setup (T001–T002)** → **Foundational (T003)** → historias.
- **US1 (T004–T009)** necesita usuarios para cargar mediciones y emitir: T011 (US2) se implementa
  junto con T008; los tests de US2 (T010) pueden escribirse en paralelo con los de US1.
- **US3 (T012–T014)** depende de T009 (el comando existe); T014 es independiente.
- **Polish (T015–T019)** al final.

```text
T001 → T002 ─┐
             T003 → T004/T005/T006/T010 (tests, [P]) → T007 → T011 → T008 → T009 → T012 → T013 → T014
                                                                                         → T015/T016 → T017 → T018 → T019
```

## Parallel Example

```text
# Tests de US1 y US2 a la vez (mismo archivo, secciones distintas: escribir en una sola pasada)
T004, T005, T006, T010
# Documentación
T015 (README.md), T016 (CLAUDE.md)
```

## Implementation Strategy

1. **MVP = US1 + US2** (las dos P1): sin usuarios no se pueden cargar mediciones ni emitir, así que
   van juntas. Con eso el equipo ya puede mostrar el dashboard.
2. **US3** agrega las protecciones (entorno, repetición, conflictos, rollback) y el reemplazo del
   comando viejo.
3. Documentación, controles del CI, suite completa y recorrido manual.
