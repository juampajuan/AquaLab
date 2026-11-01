# Implementation Plan: Generar informe

**Branch**: `021-generar-informe` | **Date**: 2026-11-01 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/021-generar-informe/spec.md` (US 7.2, Jira a confirmar)

## Summary

Desde el control de la US 7.1, «Generar informe» abre una **vista previa** (borrador) del informe
para cualquier empleado. El documento se arma con `armar_contenido(estudio)`: datos institucionales
de ejemplo (`settings.AQUALAB_LABORATORIO`), cliente, muestra, estudio y, por prueba, resultado
(con «< LD» y Ausente/Presente), unidad, límite, norma y la evaluación de la validación vigente
(US 6.4). Quien tiene «Puede emitir informes» (grupo «Bioquímicos», por migración) confirma
**Emitir informe**: `emitir_informe` bloquea el estudio y revalida con la regla de la 7.1, toma el
lock de numeración, crea el `Informe` (número correlativo `INF-000001`, quién, cuándo y la copia
del contenido en `JSONField`) y pasa el estudio a «Informe generado», todo en una transacción. El
informe emitido se ve desde su copia en `informes:ver`, con enlaces desde el control y el detalle.
Además se ajusta la regla de la 6.4: con límite «Ausente», un resultado por debajo del límite de
detección cumple.

## Technical Context

**Language/Version**: Python 3.12

**Primary Dependencies**: Django 5.2 LTS (ORM con `JSONField` sobre `jsonb`, auth: permisos y
grupos, messages), Tailwind CSS 4 y componentes de `templates/ui/`. Sin dependencias nuevas ni
JavaScript.

**Storage**: PostgreSQL 16 en Docker. Tabla nueva `informes_informe`; migraciones
`informes/migrations/0001_initial.py` y `0002_permiso_bioquimicos.py` (datos).

**Testing**: pytest 9.1.1 + pytest-django 4.14.0; fixtures de `estudios/tests/conftest.py`
(`estudio_de`, `catalogo`, `bioquimico`, `cliente_bioquimico`) y helpers `cargar`, `validar`;
concurrencia con `transaction=True` e hilos; ruff 0.17.1.

**Target Platform**: Contenedor Linux (`web`) con Docker Compose; navegador de escritorio.

**Project Type**: Aplicación web Django monolítica con templates en el servidor (sin SPA).

**Performance Goals**: Del control al informe emitido en menos de 1 minuto con una confirmación
(SC-001); armado en memoria para ≤ 90 pruebas por estudio con consultas acotadas.

**Constraints**: Emitido = vista previa (SC-002, mismo armado y template); copia inmutable (FR-010);
números sin huecos (SC-004, advisory lock); un informe por estudio (FR-012); nada de `float`
(principio IV); CSS compilado al día (CI).

**Scale/Scope**: 1 modelo + 2 migraciones, 1 módulo de armado, 1 servicio de emisión, ajuste de
`pruebas/limites.py`, 2 vistas nuevas + cambios en `generar` y `control`, 3 templates nuevos + 2
cambiados, `settings.AQUALAB_LABORATORIO`, fixture `bioquimico`, actualización de tests de la 7.1,
sección en `CLAUDE.md` y tests.

Decisiones en [research.md](./research.md) (R1–R9). No hay `NEEDS CLARIFICATION` pendientes.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principio | Cumplimiento | Estado |
|---|---|---|
| **I. Spec primero (SDD)** | Spec de US 7.2 con 12 aclaraciones (2026-11-01). PR: «US 7.2 – Generar informe». El código espera la aprobación de la spec. Clave de Jira a confirmar. | ✅ |
| **II. Simplicidad y Django idiomático** | App `informes` prevista en la constitution; `JSONField`, permisos y grupos de Django; un armado y un template para vista previa y emitido; sin JS ni dependencias; datos institucionales en settings (YAGNI). | ✅ |
| **III. Tests obligatorios** | Cada escenario y FR con test (ver [Mapa de tests](#mapa-de-tests)); «< LD» y la regla ajustada con casos conocidos del catálogo. | ✅ |
| **IV. Integridad de datos** | Informe emitido inmodificable (sin pantalla ni admin que lo edite) y con copia de los datos; valores como texto exacto de `Decimal`; número sin huecos; un informe por estudio; con informe emitido no se corrigen mediciones (US 6.3). | ✅ |
| **V. Seguridad** | `LoginRequiredMiddleware`; emisión con `@permission_required(raise_exception=True)` + revalidación en el servicio; POST con CSRF. | ✅ |
| **VI. Idioma y consistencia** | `Informe`, `emitir_informe`, `armar_contenido`, `emitido_por`; interfaz en español; ruff. | ✅ |
| **Interfaz (UI)** | Vista previa antes de emitir (revisar → confirmar), `messages`, componentes de `templates/ui/`. | ✅ |

**Post-diseño (Phase 1)**: cumple todos los principios, sin excepciones nuevas.

## Diseño

### Flujo

```text
GET  /informes/estudios/<pk>/                → control (7.1): «Generar informe» (enlace) | «Ver informe»
GET  /informes/estudios/<pk>/vista-previa/   → 302 control si no listo | documento BORRADOR
                                               (+ «Emitir informe» con permiso)
POST /informes/estudios/<pk>/generar/        → 403 sin permiso | emitir_informe() → 302 ver | 302 control
GET  /informes/estudios/<pk>/informe/        → 404 sin informe | documento desde informe.contenido
emitir_informe (una transacción)
  └─ permiso → estudio_listo_bloqueado() (7.1) → lock numeración → siguiente_numero()
     → armar_contenido(estudio) → Informe.create → estudio «Informe generado»
```

Rutas y mensajes en [contracts/generar-informe-ui.md](./contracts/generar-informe-ui.md);
modelo y contenido en [data-model.md](./data-model.md).

### Mapa de tests

| Escenario / requisito | Test | Archivo |
|---|---|---|
| FR-016 — «Ausente» con resultado < LD cumple; ≥ LD no; LD no numérico no aplica | `test_evaluar` (casos nuevos), `test_limites_aplicables` (deteccion) | `pruebas/tests/test_limites.py` |
| FR-016 — validación y detalle usan la regla ajustada (SS10 0,05) | `test_validar_ausente_bajo_ld_cumple` | `estudios/tests/test_servicio_validacion.py` |
| FR-003/004/005 — armado: laboratorio, cliente, muestra, estudio, pruebas; «< LD»; A/P; evaluación de la validación vigente; vacíos | `test_armar_contenido_*` | `informes/tests/test_contenido.py` |
| US1 Esc. 1–5, FR-001/002 — vista previa con todos los datos y «BORRADOR», sin cambios | `test_vista_previa_muestra_documento`, `test_vista_previa_no_cambia_nada` | `informes/tests/test_vista_previa.py` |
| US1 Esc. 6 — no listo o ya informado → 302 con motivo | `test_vista_previa_rechaza_no_listo` (parametrizado) | `informes/tests/test_vista_previa.py` |
| FR-007, US3 Esc. 2 — «Emitir» solo con permiso; sin permiso 403 y servicio rechaza | `test_emitir_solo_con_permiso`, `test_sin_permiso_403` | `informes/tests/test_emitir.py` |
| US2 Esc. 1–2, FR-009/011/013 — emite, número, quién, cuándo, estado, redirige y muestra | `test_emitir_crea_informe_y_cambia_estado`, `test_emitir_redirige_al_informe` | `informes/tests/test_emitir.py`, `informes/tests/test_servicio_emision.py` |
| US2 Esc. 4–5, SC-004 — correlativo desde 1; falla no deja huecos | `test_numeracion_correlativa`, `test_falla_no_deja_huecos` | `informes/tests/test_servicio_emision.py` |
| US2 Esc. 3, FR-010/SC-002/003 — emitido igual a la vista previa; editar cliente/catálogo no lo cambia | `test_emitido_igual_a_vista_previa`, `test_informe_no_cambia_al_editar` | `informes/tests/test_ver.py` |
| US2 Esc. 6, FR-008/012 — no listo al confirmar; ya informado; doble envío | `test_emitir_revalida`, `test_segundo_intento_rechaza` | `informes/tests/test_servicio_emision.py` |
| Concurrencia — dos emisiones simultáneas: un informe, el otro con motivo | `test_emisiones_concurrentes` (`transaction=True`, hilos) | `informes/tests/test_concurrencia_emision.py` |
| FR-014, US3 Esc. 1 — «Bioquímicos» tiene «Puede emitir informes» | `test_grupo_bioquimicos_puede_emitir` | `informes/tests/test_permisos.py` |
| FR-015 — emitir no modifica pruebas, mediciones, resultados, validaciones, muestra, cliente, catálogo ni otros estudios | `test_emision_no_modifica_otros_datos` | `informes/tests/test_servicio_emision.py` |
| FR-017 — «Ver informe» en control y detalle; ver sin informe → 404 | `test_control_y_detalle_ofrecen_ver_informe`, `test_ver_sin_informe_404` | `informes/tests/test_ver.py` |
| 7.1 actualizado — «Generar informe» abre la vista previa (antes POST «próximamente») | tests de `informes/tests/test_control.py` y `test_generar.py` ajustados | `informes/tests/` |
| Falla de base al emitir | `test_error_de_base_al_emitir` | `informes/tests/test_emitir.py` |

## Project Structure

### Documentation (this feature)

```text
specs/021-generar-informe/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── generar-informe-ui.md
├── checklists/
│   └── requirements.md
└── tasks.md              # /speckit-tasks
```

### Source Code (repository root)

```text
CLAUDE.md                                      # + sección «Generar informe (US 7.2)»; actualizar la nota de la 7.1
config/settings.py                             # + AQUALAB_LABORATORIO (datos de ejemplo)
pruebas/
├── limites.py                                 # LimitesAplicables.deteccion; evaluar: «Ausente» con < LD cumple
└── tests/test_limites.py                      # + casos FR-016
informes/
├── models.py                                  # nuevo: Informe (permiso emitir_informes)
├── migrations/0001_initial.py                 # nueva
├── migrations/0002_permiso_bioquimicos.py     # nueva (datos)
├── contenido.py                               # nuevo: armar_contenido
├── servicios.py                               # estudio_listo_bloqueado, siguiente_numero, emitir_informe, EmitirInformeError
├── views.py                                   # + vista_previa, ver; generar emite; control con enlaces
├── urls.py                                    # + vista-previa/, informe/
├── templates/informes/
│   ├── control.html                           # «Generar informe» enlace; «Ver informe»
│   ├── documento.html                         # nuevo (parcial)
│   ├── vista_previa.html                      # nuevo
│   └── ver.html                               # nuevo
└── tests/                                     # test_contenido, test_vista_previa, test_emitir, test_servicio_emision,
                                               # test_ver, test_permisos, test_concurrencia_emision; ajustar test_control, test_generar
estudios/
├── templates/estudios/detalle.html            # + «Ver informe»
└── tests/conftest.py                          # bioquimico: + emitir_informes
```

**Structure Decision**: el informe vive en la app `informes` (prevista en la constitution y creada
por la US 7.1); la regla de límites sigue en `pruebas/limites.py`.

## Complexity Tracking

Sin violaciones a la constitution: no aplica.
