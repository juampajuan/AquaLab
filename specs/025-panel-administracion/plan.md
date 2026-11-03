# Implementation Plan: Panel de administración

**Branch**: `025-Panel-Administracion` | **Date**: 2026-11-03 | **Spec**: [spec.md](spec.md)

**Input**: `specs/025-panel-administracion/spec.md`, FR-001 a FR-017, tres decisiones iniciales y aclaración aprobada sobre rechazo histórico, checklist 16/16. Diseño aprobado y ejecutado; evidencia de implementación y validación en quickstart.md.

**Trazabilidad**: Jira «Panel de administración». Clave Jira y número de US no proporcionados: no se inventan y deben completarse antes del PR. Los seis criterios originales se relacionan con pruebas en [contracts/testing-matrix.md](contracts/testing-matrix.md).

## Summary

Agregar vistas HTML bajo `/administracion/` dentro de usuarios, con autorización central de grupo y permiso, reutilizando Usuario, grupos, permisos y avisos. Separar aprobación previa de habilitación mediante un booleano y mantener is_active como control de autenticación. Compartir transiciones entre panel y Django Admin con autorizaciones distintas por canal, bloqueo de filas y confirmaciones versionadas.

Catálogo nuevo: solo consulta y enlace al admin existente. Tipos conserva URLs, servicios y autorización: solo cambia su enlace en el menú. No crear otra app, API, SPA, editor de pruebas ni dependencias.

Phase 0: decisiones y alternativas en [research.md](research.md). Phase 1: [data-model.md](data-model.md), [contratos HTTP](contracts/administracion.md), [matriz](contracts/testing-matrix.md) y [quickstart.md](quickstart.md).

## Technical Context

**Language/Version**: Python 3.12.

**Primary Dependencies**: Django 5.2.18, psycopg 3.3.6 y Tailwind CSS 4.3.3 standalone ya fijados en requirements, Dockerfile y CI. Sin dependencias nuevas.

**Storage**: PostgreSQL 16, mismo Usuario y tablas auth; sesión Django para confirmaciones; sin tablas nuevas de solicitudes o avisos.

**Testing**: pytest 9.1.1, pytest-django 4.14.0, cliente Django, mailoutbox, callbacks de commit y carreras PostgreSQL; ruff 0.17.1.

**Target Platform**: Web de escritorio, servicios web/db del Compose actual. No se presupone .env, contenedores, volúmenes o bases de otra computadora.

**Project Type**: Monolito Django, HTML de servidor y sistema visual común.

**Performance Goals**: SC-005: máximo tres acciones desde listado hasta completar operación; páginas de 20 y roles sin N+1. Sin agregar SLA de latencia o volumen ajeno a Jira.

**Constraints**: Grupo y permiso real en panel, sin bypass de superusuario; tipos solo con su permiso vigente. Confirmaciones, integridad histórica y avisos existentes. Sin creación de usuarios ni edición interna de pruebas.

**Scale/Scope**: Un laboratorio, tres listados y confirmaciones por cuenta; 35 escenarios de aceptación, incluido US2.9 de rechazo impedido. Sin suponer cantidades no informadas.

## Constitution Check

Se revisó `.specify/memory/constitution.md` 1.1.0 antes de Phase 0 y nuevamente después de Phase 1.

| Gate | Antes de investigación | Después del diseño |
| --- | --- | --- |
| I. Spec primero y una historia | Pasa: decisiones aprobadas, solicitud autoriza planificar | Pasa: sin código, tasks ni cambios a otras specs |
| I. Número de US | Excepción documental justificada por la instrucción de no inventar identificadores | Título y descripción trazados; obtener identificador real antes del PR |
| II. Simplicidad Django | Pasa: reutilizar auth, admin y mensajes | Pasa: misma app, servicios de dominio, sin dependencias nuevas |
| III. Tests obligatorios | Pasa para diseño: cada escenario exige prueba futura | Pasa: matriz 35/35, carreras y regresiones; no implica tests implementados |
| IV. Integridad | Pasa: no borrar aprobados | Pasa: migración conservadora, PROTECT, revisión bajo bloqueo; resultados e informes intactos |
| V. Seguridad | Pasa: sesión, CSRF, secretos por entorno | Pasa: autorización de vistas y servicios, firma y actor recargado |
| VI. Idioma y UI | Pasa: español y diseño común | Pasa: componentes Tailwind y confirmaciones existentes |

Sin violaciones técnicas sin justificar ni decisiones funcionales abiertas. La reserva de trazabilidad es documental y no habilita inventar claves. Revisar el plan antes de tasks.

## Project Structure

### Documentation (this feature)

```text
specs/025-panel-administracion/
├── spec.md                       # Existente, sin cambios
├── checklists/requirements.md     # Existente, sin cambios
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── administracion.md
    └── testing-matrix.md
```

### Source Code (repository root)

Árbol previsto, no creado en esta fase:

```text
usuarios/
├── models.py                         # Aprobación, revisión, estados y permiso
├── admin.py                          # Adaptadores a servicios compartidos
├── forms.py                          # Login y ficha admin
├── views.py                          # Registro crea pendiente explícita
├── permisos_administracion.py         # Nuevo: política central
├── servicios_administracion.py        # Nuevo: transiciones y avisos
├── confirmaciones_administracion.py   # Nuevo: patrón firmado existente
├── forms_administracion.py            # Nuevo: campos restringidos
├── views_administracion.py            # Nuevo: HTML
├── urls_administracion.py             # Nuevo: namespace administracion
├── context_processors.py             # Contexto de navegación
├── migrations/                       # Previstas 0003 y 0004, sin generarlas
├── templates/usuarios/administracion/ # Listados, rol y confirmación
└── tests/                            # Cobertura nueva y regresiones propias
config/urls.py                        # Include /administracion/
templates/ui/menu.html                # Sección nueva y traslado de tipos
templates/base.html                   # Reutilizar
templates/inicio.html                 # Conservar tarjeta de tipos
pruebas/models.py y admin.py          # Reutilizar, sin otro editor
estudios/views_tipos.py y gestion_tipos.py # Conservar
static/css/aqualab.css                # Recompilar durante implementación
```

**Structure Decision**: Funciones administrativas en usuarios; pruebas se consulta por su modelo actual. No trasladar tipos ni envolver sus rutas con el permiso nuevo. Agregar el booleano de navegación al procesador existente, sin cambiar settings, backend o middleware.

### Autorización y servicios

`tiene_acceso_administracion` comprueba autenticación, cuenta activa, membresía explícita Administradores y asignación real de `usuarios.administrar_panel` por grupos o permisos individuales. Consulta las tablas auth existentes para que el atajo de has_perm tampoco permita un superusuario sin grupo o sin asignación. Vistas, contexto y servicios comparten política.

Las escrituras recargan actor y objetivo, revalidan autorización dentro de atomic y bloquean filas por PK ascendente; la cuenta propia se bloquea una vez. Acciones masivas siguen el mismo orden. Django Admin conserva is_staff y change_usuario/delete_usuario, con semántica normal de superusuarios; no requiere Administradores.

Adaptadores públicos separados de panel y admin verifican sus políticas antes del núcleo privado común. No aceptar banderas de POST para elegir canal ni eludir autorización. Aprobar, rechazar, activar, desactivar y cambiar rol concentran invariantes; vistas sin escrituras directas. Una resolución efectiva agenda un callback existente con on_commit; reactivar no agenda aprobación. Sin señales ni otro sistema de correo.

La elegibilidad de rechazo de FR-008 está formalmente aclarada: una pendiente histórica con referencias protegidas o firma se conserva sin resolverla ni enviar aviso; informar el motivo y permitir revisión y aprobación normal posterior si corresponde. No activar automáticamente, asumir aprobación previa ni relajar PROTECT o borrar referencias/firmas. US2.9 se verifica mediante T006 y T034, sin cambiar el diseño de servicios.

La revisión administrativa por usuario y la instantánea firmada de estado, rol e identidad evitan confirmaciones obsoletas. Incrementar revisión al cambiar estado/rol y ante cambios de grupos/permisos de la ficha admin. groups.add/remove(Bioquímicos) conserva lo demás; nunca set. Permitir rol propio y prohibir desactivación propia también en el servicio.

### Compatibilidad de Django Admin y login

Acciones admin filtran el estado pendiente completo y delegan en servicios. La ficha mantiene aprobación mediante is_active: activar pendiente marca aprobación y agenda aviso; activar desactivada no lo reenvía. Campos internos nuevos no se editan libremente. Alta admin sigue activa/aprobada sin avisos.

Envolver POST de changeform_view en transacción/bloqueo antes de cargar y bindear objeto. La revisión/instantánea firmada al abrir se valida en el formulario contra lo vigente; preparar estado coherente antes de validar constraints. Conflictos como error de formulario antes de save_model; no usar ese hook como veto tardío. save_model y núcleo común persisten la propuesta sobre estado bloqueado sin guardar después una instancia antigua encima. save_related mantiene M2M en la misma transacción e incrementa revisión al cambiar grupos/permisos. Probar ficha frente a panel y acciones masivas.

Login conserva ModelBackend e is_active. Diagnóstico con contraseña correcta distingue pendiente/desactivada; con contraseña incorrecta conserva el trabajo real/ficticio y no revela estado. Huella de sesión no sustituye autorización. Suspender impide acceso en siguientes peticiones con sesiones existentes mediante la comprobación actual de cuenta activa.

### Interfaz y confirmaciones

Formularios con campos/acciones cerrados, sin ModelForm general de Usuario. Firma ligada a actor, sesión, objetivo, operación, revisión, instantánea original y propuesta; TTL una hora, hasta 20 borradores, siguiendo confirmaciones_tipos con salts/claves propios y sin modificar tipos. Revisar/cancelar no escribe dominio ni avisa; confirmar vuelve al listado con mensaje.

Reutilizar base, encabezado, campo, tabla, badges, vacío, mensajes, acciones_confirmacion y paginacion. Menú usa política central y muestra tipos solo con permiso específico; Inicio conserva tarjeta independiente. Catálogo busca código/nombre con icontains, incluye inactivas, ordena código/PK y usa get_tipo_calculo_display y filtro unidad. Enlace admin:pruebas_prueba_change sin conceder acceso.

### Validación y riesgos

[Matriz](contracts/testing-matrix.md): 35 escenarios, 17 FR y seis criterios Jira; MigrationExecutor, mailoutbox/callbacks y carreras transaction=True. No ejecutar tests de implementación inexistente durante el plan.

Riesgos: históricos ambiguos; pendientes heredadas con referencias/firma no eliminables; ficha admin y M2M; caché de permisos; SMTP tras commit sin entrega exactamente una vez frente a caídas; bloqueo cruzado; clases Tailwind fuera del escaneo. Mitigaciones en research, modelo y contratos.

Estado al cerrar la planificación (histórico): Phase 0 y Phase 1 completas. No existe extensions.yml: sin hooks previos/posteriores registrados. Detenerse para revisión; próximo comando sugerido, sin ejecutarlo: `$speckit-tasks`.

## Complexity Tracking

| Excepción | Justificación | Alternativa descartada |
| --- | --- | --- |
| Trazabilidad temporal sin número de US | Usuario proporcionó título y criterios, autorizó continuar y prohíbe inventar claves | Usar 025 como US o inventar SCRUM daría trazabilidad falsa; completar antes del PR |

Booleano: dato mínimo para separar pendiente/desactivada manteniendo autenticación. Contador adicional: detecta confirmaciones obsoletas para FR-017, sin historial ni tablas nuevas.

## Estado de ejecución

Las fases de diseño anteriores se conservan como decisiones aprobadas. La implementación posterior está en la misma feature; progreso verificado en tasks.md, trazabilidad real en contracts/testing-matrix.md y resultados/recorridos/capturas en quickstart.md. No se cambió la arquitectura, los requisitos ni la Constitution.
