# Implementation Plan: Datos de demo

**Branch**: `026-datos-demo` | **Date**: 2026-11-08 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/026-datos-demo/spec.md` (SCRUM-78, tarea técnica)

## Summary

`python manage.py cargar_demo` carga, en una transacción y solo con `AQUALAB_ENTORNO=desarrollo` y
`DEBUG=True`, un laboratorio con seis meses de actividad: 3 clientes con nombres realistas
(correo `@demo.aqualab`), 7 orígenes, una muestra mensual por origen, estudios de 3 tipos demo
armados con el catálogo real, en los cuatro estados, con informes emitidos y firmados, resultados
fuera de norma, un «< LD», pruebas Ausente/Presente y un desvío claro de Cloruro en «Pozo 2». Los
datos se crean con los **servicios reales** (`registrar_muestra`, `crear_estudio`,
`cargar_mediciones`, `validar_resultados`, `emitir_informe`) y después se **corren las fechas hacia
atrás** con `QuerySet.update()`, en orden coherente y nunca en el futuro. Los valores salen de un
guion fijo (siempre iguales); las fechas se calculan desde el día de ejecución. Crea un técnico y
un bioquímico demo (con firma) y reemplaza a `cargar_demo_us51`.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: Django 5.2 LTS (management command, auth: grupos y permisos). Sin
dependencias nuevas: la firma demo es un PNG armado con `zlib` y `struct` (como
`informes/tests/utiles.py`).

**Storage**: PostgreSQL 16 en Docker. Sin modelos ni migraciones nuevas.

**Testing**: pytest + pytest-django; fixtures existentes (`catalogo`); `settings`/`monkeypatch`
para el entorno; ruff.

**Target Platform**: Contenedor `web` de Docker Compose (desarrollo).

**Project Type**: Aplicación web Django monolítica; esta historia agrega un comando de consola.

**Performance Goals**: Demo completa en menos de 1 minuto (SC-001): unos 50 estudios con ~5
pruebas cada uno, consultas acotadas.

**Constraints**: Solo desarrollo (FR-002); atómico (FR-016); mismas reglas que la app (FR-007);
valores fijos (FR-001a); fechas coherentes y nunca futuras (FR-008); sin tocar datos ajenos (FR-019).

**Scale/Scope**: `estudios/demo.py` (guion y carga), `estudios/management/commands/cargar_demo.py`,
`estudios/tests/test_demo.py`; se borran `cargar_demo_us51.py` y `test_demo_us51.py`;
`.env.example`, `README.md` y `CLAUDE.md`.

Decisiones en [research.md](./research.md) (R1–R9). No hay `NEEDS CLARIFICATION` pendientes.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Cumplimiento | Estado |
|---|---|---|
| **I. Spec primero (SDD)** | Spec de SCRUM-78 con 3 aclaraciones (2026-11-08). El código espera la aprobación de la spec por el equipo. | ✅ |
| **II. Simplicidad y Django idiomático** | Un management command delgado y un módulo con el guion; reutiliza los servicios existentes en vez de duplicar reglas; sin modelos, dependencias ni JS. | ✅ |
| **III. Tests obligatorios** | Cada FR y escenario con test (ver [Mapa de tests](#mapa-de-tests)): entorno, carga completa, estados, desvío, determinismo, idempotencia, conflictos, rollback, catálogo y fechas. | ✅ |
| **IV. Integridad de datos** | Los datos pasan por los servicios: N° PI e INF sin huecos, cálculos, validaciones e informes con copia. Las fechas se ajustan solo en filas creadas por la demo, dentro de la misma transacción. No se modifica ningún dato existente. | ✅ |
| **V. Seguridad** | Rechaza fuera de desarrollo o sin `DEBUG`; la contraseña conocida solo existe en desarrollo; no toma cuentas ajenas (conflicto de correo → rechazo). | ✅ |
| **VI. Idioma y consistencia** | `cargar_demo`, `estudios/demo.py`, mensajes en español; ruff. | ✅ |

**Post-diseño (Phase 1)**: cumple todos los principios, sin excepciones.

## Diseño

### Flujo del comando

```text
cargar_demo
  ├─ entorno: AQUALAB_ENTORNO == "desarrollo" y DEBUG, motor PostgreSQL  → si no: CommandError
  └─ transaction.atomic()
       ├─ pg_advisory_xact_lock(7_800_001)          (dos ejecuciones simultáneas no se pisan)
       ├─ ¿hay clientes @demo.aqualab?  → aviso «La demo ya está cargada…», sin cambios
       ├─ conflictos: correo de usuario demo o tipo demo con otras pruebas → CommandError
       ├─ catálogo vacío → call_command("importar_catalogo_pruebas")
       ├─ usuarios demo (técnico; bioquímico + grupos + FirmaProfesional) y tipos demo
       ├─ por cada (origen, mes) del guion:
       │    registrar_muestra → crear_estudio → cargar_mediciones (técnico)
       │    → validar_resultados / emitir_informe (bioquímico) según el estado destino
       │    → correr fechas de las filas creadas (Muestra, Estudio, Medicion, Resultado,
       │      Validacion, Informe) con QuerySet.update()
       └─ resumen: cantidades por estado, informes, usuarios y contraseña
```

Detalle del guion y las fechas en [data-model.md](./data-model.md); interfaz del comando en
[contracts/cargar-demo-cli.md](./contracts/cargar-demo-cli.md).

### Mapa de tests

| Escenario / requisito | Test | Archivo |
|---|---|---|
| FR-002, US3 Esc. 1 — fuera de desarrollo, sin DEBUG o sin variable → rechazo sin cambios | `test_rechaza_fuera_de_desarrollo` (parametrizado) | `estudios/tests/test_demo.py` |
| FR-003/004, US1 Esc. 1 — 3 clientes, 7 orígenes, una muestra por mes y origen en 6 meses | `test_clientes_origenes_y_muestras` | idem |
| FR-005 — 3 tipos demo con pruebas del catálogo | `test_tipos_demo` | idem |
| FR-006, SC-003, US1 Esc. 2 — estados (≥ 2 cada uno), meses anteriores con informe | `test_estudios_por_estado` | idem |
| FR-007, US1 Esc. 3 — informes con copia y firma; N° PI e INF correlativos | `test_informes_firmados_y_numeracion` | idem |
| FR-008, SC-002 — fechas en orden, nunca futuras, repartidas en 6 meses | `test_fechas_coherentes` | idem |
| FR-009 — estancado > 7 días y Finalizado sin informe | `test_alertas_del_dashboard` | idem |
| FR-010, US1 Esc. 4 — fuera de norma, «< LD», Ausente y Presente | `test_fuera_de_norma_ld_y_presencia` | idem |
| FR-011, SC-004, US1 Esc. 5–6 — desvío validado ≥ 3× y desvío actual sin validar | `test_desvio_en_pozo_2` | idem |
| FR-001a, SC-007 — valores iguales en dos cargas | `test_valores_reproducibles` | idem |
| FR-012, US2 — técnico y bioquímico, grupos, firma, autoría y pendientes por rol | `test_usuarios_demo` | idem |
| FR-013, US3 Esc. 3 — importa el catálogo si falta; no reimporta | `test_importa_catalogo_si_falta`, `test_no_reimporta_catalogo` | idem |
| FR-014, US3 Esc. 2 — segunda ejecución no crea nada | `test_segunda_ejecucion_no_duplica` | idem |
| FR-015 — correo demo ocupado por otra cuenta | `test_conflicto_de_usuario` | idem |
| FR-005 (aclaración) — tipo con mismo nombre y otras pruebas | `test_conflicto_de_tipo`, `test_reutiliza_tipo_igual` | idem |
| FR-016, US3 Esc. 4 — falla a mitad → nada | `test_falla_no_deja_nada` | idem |
| FR-019 — datos previos intactos; numeración continúa | `test_respeta_datos_existentes` | idem |
| FR-017, US1 Esc. 7 — resumen con usuarios y contraseña | `test_resumen` | idem |
| FR-018 — `cargar_demo_us51` ya no existe | `test_comando_viejo_eliminado` | idem |

## Project Structure

### Documentation (this feature)

```text
specs/026-datos-demo/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── cargar-demo-cli.md
├── checklists/
│   └── requirements.md
└── tasks.md              # /speckit-tasks
```

### Source Code (repository root)

```text
.env.example                                   # + AQUALAB_ENTORNO=desarrollo
README.md                                      # + «Datos de demo»
CLAUDE.md                                      # + sección «Datos de demo (SCRUM-78)»
estudios/
├── demo.py                                    # nuevo: guion fijo, fechas, cargar_demo()
├── management/commands/cargar_demo.py         # nuevo: entorno, transacción, resumen
├── management/commands/cargar_demo_us51.py    # se borra
└── tests/
    ├── test_demo.py                           # nuevo
    └── test_demo_us51.py                      # se borra
```

**Structure Decision**: el comando vive en `estudios`, como el anterior, porque el estudio es el
centro de la demo; la lógica va en `estudios/demo.py` para probarla sin la consola.

## Complexity Tracking

Sin violaciones a la constitution: no aplica.
