# Implementation Plan: US 10.2 — Conclusión asistida del informe

**Branch**: `39-Conclucion-Asistida` | **Date**: 2026-11-16 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/039-conclusion-asistida-informe/spec.md`. Base Git inspeccionada: `c5a0030a06de65fc56949b8716c36506a2e2bf46`.

## Summary

Agregar una conclusión opcional en la vista previa, propuesta con hechos verificables, editable y aprobable por Bioquímicos con permiso efectivo de emisión. La IA de US 10.1 elige variantes de redacción restringidas; AquaLab determina las pruebas fuera de norma e inserta todos los valores, límites y normas desde Resultado y Validacion vigente. Sin información suficiente, conservar hechos conocidos y advertencias explícitas. Sin IA, plantilla completa.

Persistir un borrador compartido por estudio y una aprobación vinculada a texto exacto, revisión y huella de sus fuentes. Cambios de texto, propuesta o fuentes invalidan. Verificar y copiar bajo bloqueos en la emisión existente, conservando identidad del aprobador aunque emita otra persona autorizada. Todas las salidas usan la misma conclusión inmutable; los históricos y la emisión sin conclusión mantienen su comportamiento.

Alcance de esta ejecución: Phase 0 y Phase 1 del skill original, investigación y diseño únicamente. No se genera tasks.md, código, migraciones ni resultados de pruebas. La spec y checklist aprobadas permanecen intactas, incluidos sus textos históricos sobre la fase anterior.

## Technical Context

**Language/Version**: Python 3.12; JavaScript nativo para editor, sin frontend SPA.

**Primary Dependencies**: Django 5.2.18, psycopg 3.3.6, WeasyPrint 70.0 y Tailwind standalone v4.3.3 existentes. Cliente HTTP de biblioteca estándar de US 10.1, Groq y configuración actual; no nuevos SDK, variables obligatorias o dependencias.

**Storage**: PostgreSQL 16. Una tabla nueva futura BorradorConclusion; snapshot JSON opcional en Informe.contenido existente. Decimal y fechas serializados como textos; no backfill ni modificación de modelos clínicos históricos. Migración aditiva necesaria durante implementación, no generada ahora.

**Testing**: pytest 9.1.1/pytest-django 4.14.0, PostgreSQL real para transacciones; node:test sin paquetes para interacción; Ruff 0.17.1, check de Django, migraciones y CSS. CI Node 20; agregar en la futura implementación informes/tests/js a su lista explícita. Cobertura planeada: 38 escenarios, 19 FR, nueve criterios originales y diez SC en [test-matrix](test-matrix.md).

**Target Platform**: Django en Docker/Linux, PostgreSQL 16; escritorio de laboratorio. Desarrollo Windows en E: con Docker Compose y validación aislada, sin modificar instalaciones del sistema.

**Project Type**: Aplicación web renderizada en servidor, extensión del módulo informes.

**Performance Goals**: Consultas por conjunto con select_related/prefetch, número independiente del número de pruebas, sin N+1; IA siempre fuera de transacción. Espera del llamador acotada por presupuesto existente (20 s actual) y timeout de transporte (15 s actual); dos workers daemon máximos por proceso y respaldo inmediato en saturación. Umbrales y prueba de plazo en R4; no prometer una latencia de BD no medida.

**Constraints**: Política conjunta de grupo/permisos solo en función nueva; sesión/CSRF. Ninguna evaluación clínica confiada a IA. Datos personales fuera de sus mensajes. Aprobación exacta sin expiración temporal nueva, invalidación persistente, control optimista y locks al emitir. Emisión sin conclusión nunca depende de Groq o validez del borrador. Texto profesional sin longitud máxima funcional nueva; 64 KiB solo para intercambio IA, exceso usa plantilla completa. Texto escapado en HTML y snapshot de strings compatible.

**Scale/Scope**: Una US y una conclusión compartida por estudio, tres POST nuevos y extensión compatible de vista previa/emisión. Sin nuevos roles/permisos, nuevas apps, cambios de chat, recomendaciones, historial de borradores no solicitado ni edición de emitidos. No quedan decisiones funcionales bloqueantes; limitaciones operativas explícitas en research.

## Constitution Check

GATE antes de Phase 0 y reevaluación tras Phase 1, Constitution 1.2.0 sin cambios:

| Principio / regla | Antes de investigación | Tras diseño y evidencia |
|---|---|---|
| I, spec primero y trazabilidad | PASS: spec aprobada, Q1–Q3 cerradas, US 10.2 | PASS: 19 FR y nueve criterios rastreados; clave Jira propia no informada, no inventada; ninguna modificación funcional. |
| II, simplicidad / Django idiomático | PASS: aplicaciones y dependencias existentes | PASS: una tabla, ORM/formularios/templates, adaptador pequeño; sin SDK, SPA o dependencia nueva. Workers limitados solo para preservar presupuesto de espera del cliente existente. |
| III, escenarios automatizados | PASS para plan: se exige test por escenario | PASS para diseño: 38/38 asociados a pytest-django y oráculos, JS complementario; no afirmar pruebas ejecutadas. Ruff y suite completa exigidos antes del futuro merge. |
| IV, integridad | PASS: resultados y copia existentes identificados | PASS: Decimal sin float, hechos vigentes sin fallback, aprobación exacta y snapshot inmutable, sin actualizar históricos. |
| V, seguridad | PASS: sesión/CSRF y permisos actuales | PASS: guardias servidor/UI, reautorización, escaping, sin secretos en artefactos/logs ni datos personales a IA. |
| VI, idioma / dominio | PASS | PASS: español y nombres del laboratorio; estilo Ruff previsto. |
| UI / stack | PASS: servidor, Tailwind y parciales | PASS: componentes existentes, help_text accesible, confirmaciones, mensajes; CSS compilado futuro, PostgreSQL 16, no instalaciones ahora. |
| Flujo y gobernanza | PASS: una rama de feature y main intacta | PASS: solo documentos propios, no commits/PR/merge/tasks; revisión del plan antes de autorizar la fase siguiente. |

La habilitación del editor requiere confirmación explícita «Editar borrador y conservar cambios», explicando autosave y que editar invalida aprobación; cubre la sesión de edición. Proponer/reemplazar, aprobar y emitir mantienen sus confirmaciones explícitas. No confirmar cada tecla ni confundir autosave con aprobación. Formularios nuevos reutilizan templates/ui/campo.html con help_text para diferenciar texto editorial, advertencias, aprobación e incorporación opcional; errores próximos al campo y framework de mensajes.

No hay excepciones a Constitution. PASS de diseño no equivale a certificación de implementación ni aprobación del equipo del futuro PR.

## Project Structure

### Documentation (this feature)

```text
specs/039-conclusion-asistida-informe/
├── spec.md                         # aprobado, intacto
├── checklists/requirements.md      # aprobado, 16/16, intacto
├── plan.md
├── research.md                     # R1–R10, Phase 0
├── data-model.md                   # Phase 1
├── contracts/
│   ├── conclusiones-ui.md
│   └── redaccion-ia.md
├── test-matrix.md
└── quickstart.md
```

No tasks.md: corresponde a un workflow posterior no autorizado. setup-plan.sh --json original se ejecutó sin modificarlo; su BRANCH lógico es 039-conclusion-asistida-informe por el directorio de feature, mientras la rama Git real sigue siendo la solicitada 39-Conclucion-Asistida. No renombrar ninguna.

### Source Code (repository root)

Rutas siguientes son alcance **propuesto para implementación**, no archivos modificados ni generados ahora:

```text
informes/
├── conclusion_hechos.py             # nuevo: fuentes y huella, sin fallback normativo
├── conclusion_ia.py                 # nuevo: adaptador, gramática y respaldo limitado
├── conclusiones.py                  # nuevo: guardias, persistencia y aprobación
├── forms.py                        # existente: agregar validación de entradas del editor
├── views_conclusiones.py            # nuevo: tres POST
├── models.py                       # nueva entidad, no cambiar Informe
├── servicios.py                    # emisión compatible con opción explícita
├── contenido.py                    # fragmento opcional de copia, no sustituir helpers actuales
├── views.py                        # vista previa y opción en generar
├── urls.py                         # registrar tres POST
├── migrations/                     # migración futura solo de nueva tabla
├── static/informes/conclusion.js   # nuevo, guardado/versiones/sesión
├── templates/informes/             # editor y parcial de conclusión nuevos;
│                                   # integrar vista previa, documentos y dos cuerpos de correo
└── tests/                          # cuatro archivos pytest y js/conclusion.test.cjs nuevos
static/css/                         # compilado Tailwind y estilo de impresión si corresponde
.github/workflows/ci.yml             # futura inclusión del directorio JS nuevo
```

**Structure Decision**: integrar dentro de informes y mantener asistente como proveedor existente. No modificar cliente/configuración, autorización general, cálculo/validación, PDF o servicio de envío para nuevas responsabilidades que no necesitan: PDF ya renderiza la copia y correo ya recibe contenido. Solo sus templates incorporan texto opcional. Separar recolector puro, frontera externa y transacción de aprobación evita duplicar reglas clínicas o de emisión. Ver las interfaces actuales y sus carencias concretas en R1/R2/R7/R10.

## Diseño y fases previstas

Phase 0 completada en [research](research.md): R1 reutilización real; R2 fuentes estrictas y LD auxiliar; R3 redacción restringida; R4 respaldo y deadline; R5 persistencia mínima; R6 huellas e invalidez; R7 atomicidad; R8 permisos; R9 editor durable; R10 snapshot y medios. Alternativas descartadas y evidencia del código registradas por decisión; sin NEEDS CLARIFICATION pendientes.

Phase 1 completada con [modelo](data-model.md), [contratos UI](contracts/conclusiones-ui.md), [contrato IA](contracts/redaccion-ia.md), [pruebas](test-matrix.md) y [validación](quickstart.md). Orden futuro: caracterizar comportamiento existente y escribir tests → hechos y adaptador → persistencia/permisos → emisión atómica → salidas → interacción y regresión. No es una lista de tareas ni autoriza implementar.

La propuesta usa dos transacciones cortas separadas por IA; reserva invalida aprobación y respuesta tardía no puede pisar un borrador nuevo. Locks uniformes Estudio → Borrador → asignaciones por pk → Prueba por pk; advisory de numeración solo después y al emitir. Reconciliar antes de comparar revisiones; conflicto de obsolescencia conserva la invalidación fuera de un rollback accidental. Copia con conclusión se verifica y materializa en la misma transacción de emisión.

Las cuatro dependencias son reales: US 10.1 aporta cliente/configuración y errores, no un servicio de conclusiones; US 7.2 aporta vista previa, condiciones y copia inmutable, no aprobación; US 7.3 parte del snapshot con documento impreso distinto del de pantalla; SCRUM-79 ya pasa contenido a mensajes txt/HTML y adjunta PDF, pero sus cuerpos aún no representan conclusión. Sus APIs se extienden solo donde lo requieren estos contratos. No asumir reutilización directa del fallback al catálogo de contenido.py para hechos de conclusión.

## Riesgos y controles de revisión

- Concurrencia: pérdida de edición y aprobación obsoleta mitigadas por revisión, huellas, tokens y locks; exigir pruebas PostgreSQL independientes y conflicto sin copia parcial. Revalidar fuentes incluso después de espera IA y al emitir.
- Transporte existente: timeout HTTP no garantiza deadline total ni cancelación real de worker. Capacidad dos y respaldo protegen al llamador, pero la lectura HTTP bruta no tiene límite de bytes; registrar y verificar esta limitación sin modificar US 10.1 ni prometer cancelación física.
- Validacion no conserva LD histórico: usar LD solo como presentación auxiliar existente y huellarlo, nunca para evaluación normativa. No puede reconstruirse un cambio auxiliar A→B→A no observado; identidades/fecha sí detectan escrituras normales de resultados/validaciones. Sin cambios a otras historias para inventar historia ausente.
- Navegador: el texto confirmado vive en BD; recovery local cubre cambios sin ack con advertencia, no promete compartir keystrokes nunca confirmados tras pérdida forzada del navegador. Revisión JS y sesión obligatoria.
- Gramática cerrada reduce libertad del proveedor, deliberadamente; el profesional puede reescribir. Verificar que todas las pruebas necesarias y advertencias estén presentes antes de aprobación y que texto extenso no se recorte en PDF/correo.
- Cambio de pertenencia/permisos durante IA se revalida; no introducir reglas retroactivas de caducidad del aprobador no aprobadas por la spec. El emisor actual sí debe cumplir política conjunta si incluye conclusión.
- CI actual no corre futuros tests JS de informes; planificar esa inclusión con Node 20. No trasladar resultados de features anteriores a esta US.

No hay bloqueo funcional abierto. El diseño requiere revisión antes de tasks; ejecución de pruebas, revisión visual y aprobación del equipo quedan para implementación/PR. Clave Jira propia pendiente, sin sustituir US 10.2 por SCRUM-79.

## Complexity Tracking

Sin violaciones de Constitution que justificar. No se agrega una capa genérica, una cola externa ni historial editorial no solicitado: una tabla y biblioteca estándar son suficientes para la persistencia y el aislamiento de la espera.
