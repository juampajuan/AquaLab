# Tareas: SCRUM-42 / US 1.2 — Inicio y cierre de sesión

**Rama**: `002-inicio-cierre-sesion` | **Fecha**: 2026-10-20
**Entrada**: [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md),
[data-model.md](data-model.md), [contracts/sesion.md](contracts/sesion.md),
[quickstart.md](quickstart.md), [Constitution](../../.specify/memory/constitution.md).
**Estado actual**: cierre técnico local verificado; T002–T031 completadas (30/32). T001/aprobación formal y T032/cierre formal pendientes. T027 acreditada por pruebas manuales reportadas por el usuario en Chrome; metadatos faltantes registrados expresamente. Historia no declarada completada ni lista para merge.

## Formato y alcance

`- [ ] Tnnn [P opcional] [US1 en fase de historia] Acción con ruta exacta`.
Rutas relativas a la raíz del repositorio. [US1] es la única User Story 1, P1, de la spec,
correspondiente a US 1.2 del backlog. US 1.1/2.1 son regresiones, no historias nuevas.
[P] permite trabajo paralelo solo después de sus prerequisitos y en archivos diferentes.

Esta generación crea solo tasks.md. Todas las acciones descritas abajo son trabajo futuro,
incluidas modificaciones de README/CLAUDE.md y evidencia en este archivo. No regenerar artefactos
existentes. No agregar dependencias, modelos, migraciones, roles, MFA, recuperación, recordatorio,
bloqueo ni cambios de expiración. Reutilizar Django, Usuario y sesiones existentes.

## Fase 1: Preparación — 3 tareas

**Objetivo:** confirmar las condiciones para ejecutar. La aprobación pendiente no bloquea generar
ni revisar tareas; sí bloquea comenzar código de producto. No reinicializar el proyecto.

- [ ] T001 Comprobar aprobación formal del equipo de `specs/002-inicio-cierre-sesion/spec.md` y revisar estas tareas contra `specs/002-inicio-cierre-sesion/plan.md` y la Constitution; registrar referencia verificable en `specs/002-inicio-cierre-sesion/tasks.md`, sin cambiar Draft unilateralmente ni implementar antes de aprobar.
- [x] T002 Validar entorno con `docker-compose.yml`, `Dockerfile`, `.env.example` y `requirements.txt`: Docker Compose, Python 3.12, PostgreSQL 16 y base de tests separada, secretos por entorno; seguir `specs/002-inicio-cierre-sesion/quickstart.md`, instalar/descargar/almacenar solo en E: y registrar bloqueos sin secretos, SQLite o paquetes nuevos. Preparación técnica acreditada antes de T001; la aprobación formal sigue siendo obligatoria antes de implementar.

- [x] T005 Antes de editar cualquier fixture o código, ejecutar baseline PostgreSQL de `usuarios/tests/`, `clientes/tests/` y controles de `.github/workflows/ci.yml`; registrar comandos/resultados en `specs/002-inicio-cierre-sesion/tasks.md` y resolver o escalar fallos previos sin atribuirlos a esta US. Depende de T002.


### Evidencia de T005 y acreditación técnica de T002

**Registrada el 2026-10-20. Fuente:** ejecución local reportada por el usuario en este chat,
realizada antes de modificar código o fixtures. Los comandos y resultados siguientes fueron
informados por el usuario; **el asistente no los ejecutó ni reprodujo sus resultados**.
Los comandos de aplicación se transcriben tal como fueron reportados, sin inventar una forma
concreta de invocación mediante docker compose exec.

| Comando o comprobación reportada | Resultado reportado |
|---|---|
| `docker compose up -d --build` | Correcto |
| PostgreSQL 16 | healthy |
| `python manage.py check` | Sin errores |
| `python manage.py migrate` | Migraciones aplicadas correctamente |
| `python manage.py makemigrations --check --dry-run` | No changes detected |
| `pytest usuarios/tests clientes/tests -q` | 83 passed in 24.71s |
| `pytest -q` | 83 passed in 24.77s |
| `ruff check .` | All checks passed |
| `ruff format --check .` | 57 files already formatted |

**T002:** completada técnicamente sobre el reporte de entorno Docker operativo en E: y los
resultados anteriores. La lectura del repositorio por el asistente confirmó Docker disponible en
`E:/Docker/Program/resources/bin/docker.exe`, existencia de .env (sin leer sus valores), Python
3.12 declarado por Dockerfile y PostgreSQL 16 por docker-compose.yml. Estas comprobaciones no
constituyen una repetición ni inspección independiente de los contenedores/pruebas reportados.

**T005:** completada como línea base local reportada por el usuario. No acredita pruebas de la
nueva US implementada, pruebas visuales ni CI remoto. La revisión Git del asistente encontró rama
`002-inicio-cierre-sesion`, HEAD `c6ad062` y sin diferencias pendientes en archivos de aplicación,
fixtures o configuración de Docker. Quedan pendientes de versionado los artefactos de planificación
y la integración Codex ya existentes. El commit identifica el estado observado al registrar el
reporte, no una referencia de ejecución declarada por el usuario.

**T001 continúa pendiente y sin marcar.** Acreditar preparación técnica y línea base antes de la
aprobación no autoriza modificar código/fixtures ni iniciar implementación. La fase 2 conserva su
condición de entrada T001/T002/T005; después de aprobar, continuar T004 → T003 y repetir la suite
existente tras preparar fixtures, según D1. No se ejecutó ninguna tarea de implementación.

**Control:** no marcar aprobación/herramientas satisfechas sin evidencia. Detener solo el trabajo
que dependa de un requisito faltante.

## Fase 2: Bases y fixtures — 2 tareas

**Objetivo:** inventariar rutas y preparar fixtures después de una línea base sin modificaciones.
Depende de T001/T002/T005. Los IDs se conservan por trazabilidad; el orden físico y las dependencias
expresas prevalecen sobre su orden numérico.

- [x] T004 Inventariar rutas/métodos y layouts desde `config/urls.py`, `usuarios/urls.py`, `clientes/urls.py` y `templates/base.html`, incluidos admin y excepciones públicas; identificar expectativa temporal de `usuarios/tests/test_setup.py` y registrar matriz contra `specs/002-inicio-cierre-sesion/contracts/sesion.md` en `specs/002-inicio-cierre-sesion/tasks.md`. Depende de T005.
- [x] T003 Preparar fixtures en `usuarios/tests/conftest.py` y `clientes/tests/conftest.py` para aprobada común, pendiente, admin, sesiones independientes, cookie compartida y Client CSRF estricto; conservar fixtures existentes y usar credenciales reales para comprobar login, sin force_login que oculte el resultado de autenticación; reutilizar `usuarios.Usuario` sin alterar el modelo. Depende de T004 y de la línea base T005; después de ajustar fixtures, repetir la suite existente y comparar con T005 antes de añadir casos nuevos.

## Fase 3: US1 — Iniciar y cerrar sesión (P1) — 22 tareas

**Objetivo:** completar la única historia y sus ocho escenarios.
**Prueba independiente:** aprobada ingresa al inicio con nombre; pendiente no ingresa; anónimo no
accede a negocio; POST logout invalida la sesión compartida; Atrás y vuelta a pestañas no muestran
DOM de sesión anterior; otra sesión independiente permanece válida.

### Pruebas antes de implementar

Después de T003 (con T005/T004 completadas), escribir T006–T013 en paralelo en archivos distintos. Confirmar fallos de
comportamiento nuevo antes de implementarlo; distinguirlos de errores de importación/fixtures.
Las garantías existentes pueden pasar desde el inicio: no forzar su fallo ni debilitarlas.

- [x] T006 [P] [US1] Crear `usuarios/tests/test_login.py` para escenarios 1/2: login público, POST aprobado con autenticación y 302 inicio/nombre, autenticado abre/envía login y vuelve al inicio; next local/externo en GET/POST nunca altera destino ni genera bucles (FR-001/002/004/006/007).
- [x] T007 [P] [US1] Crear `usuarios/tests/test_formulario_login.py` para escenarios 3/4/8: vacío parcial/total no invoca authenticate/diagnóstico; «El formulario normaliza correo pero nunca transforma la contraseña»; inexistente y activo/pendiente con contraseña incorrecta comparten HTTP 200 y error/código/estructura; solo pendiente correcta muestra mensaje específico, sin user_cache apto/_auth_user_id; no borrar borrador anónimo por fallo (SC-002, S01). Incluir correo Unicode aceptado por RegistroForm, equivalencia exacta con manager/login y flujo registrar/confirmar/aprobar/ingresar sin NFKC ni selección de otra cuenta.
- [x] T008 [P] [US1] Crear `usuarios/tests/test_diagnostico_login.py` (S02–S04): spies en consulta/encode/verify/harden_runtime reales con hasher de producción; cada fallo hace una consulta diagnóstica sin filtro is_active y una verificación real/ficticia, éxito no diagnostica, sin segundo authenticate ni setter; inutilizable/hash no reconocido/factor antiguo y DatabaseError en ambas fases no crean login ni filtran SQL/estado/credenciales en HTML/contexto/logs; distinguir upgrades de diferencias añadidas, sin comparar milisegundos.
- [x] T009 [P] [US1] Crear `usuarios/tests/test_logout.py` para escenario 6 y parte servidor del 7: CSRF real válido/ausente/incorrecto, POST invalida clave y redirige a login ignorando next, GET autenticado 405 sin cerrar, POST repetido válido sin error; cookie compartida invalida dos clientes, sesión independiente persiste, borradores desaparecen y filas confirmadas se conservan (FR-010/011/013, S06). Parametrizar usuarios:logout y admin:logout, next local/externo en query/cuerpo/ambos; ambos terminan en usuarios:login, incluido admin con sesión staff, y mantienen CSRF y GET 405.
- [x] T010 [P] [US1] Crear `usuarios/tests/test_acceso_sesion.py` para escenario 5: matriz GET/POST anónimos de inicio/clientes/revalidación/admin sin HTML sensible ni escrituras; CSRF inválido puede dar 403 y válido redirige, registro/login públicos, no reproducir POST tras login; admin conserva staff/permisos/aprobación (FR-008/009, S05/S07). Comprobar resolve(reverse(admin:logout)) hacia la vista común sin que el alias conceda permisos administrativos al usuario aprobado no staff.
- [x] T011 [P] [US1] Crear `usuarios/tests/test_revalidacion.py` para escenario 7: 204 solo cookie/huella de misma sesión, 409 ausente/distinta, anónimo/cookie vieja redirige y huella sola no autentica; nueva sesión del mismo/otro usuario o rotación cambia huella; otros métodos autenticados 405, sin cuerpo sensible/cambios en datos o expire_date ni exposición de sessionid/hash/secretos (S06/S07).
- [x] T012 [P] [US1] Crear `usuarios/tests/test_cache_sesion.py`: cabeceras private/no-store/no-cache/must-revalidate en HTML autenticado/error/admin y login/revalidación, sin sesión nueva ni huella/guardia en anónimo; layouts autenticados tienen cierre POST+CSRF y guardia; middleware solo cabeceras y función de huella compartida entre contexto/vista (escenarios 5–7, S07).
- [x] T013 [P] [US1] Crear regresiones en `clientes/tests/test_sesion.py`: borrador permanece tras revalidación válida, cierre exige nuevo login y otro usuario no recupera borrador, filas confirmadas se conservan, confirmar/cancelar/doble envío mantienen resultados; reutilizar sin debilitar `clientes/tests/test_registro.py` (S10).

### Implementación y conexión

T014/T016/T018 requieren que T006–T013 estén escritos. No crear entidades/campos; las reglas
citadas son invariantes existentes de data-model.md que deben conservarse.

- [x] T014 [US1] Implementar FormularioInicioSesion en `usuarios/forms.py` sobre AuthenticationForm/manager: «email: identificador único; normalización strip/lower existente y constraint Lower(email)», «is_active: False = pendiente; True = aprobada, según contrato vigente de US 1.1»; campos requeridos, password strip=False, ModelBackend intacto, algoritmo R2 con check_password sin setter en todas las ramas diagnósticas incluida ficticia, errores exactos y DatabaseError uniforme sin filtración ni login parcial. Depende de T006–T013. Redefinir username como forms.CharField sin heredar UsernameField/NFKC; clean_username aplica solo UsuarioManager.normalizar_email, igual que RegistroForm.clean_email, conservando longitud/required sin añadir transformaciones Unicode o IDNA.
- [x] T015 [US1] Implementar InicioSesionView/CerrarSesionView en `usuarios/views.py` con LoginView/LogoutView: login público, redirect_authenticated_user y destino fijo inicio, logout protegido POST/OPTIONS+CSRF con flush/destino login, GET no muta, next ignorado y repetición segura; no escribir manualmente claves de autenticación. Depende de T014. Fijar get_success_url al login en la vista común de cierre, sin delegar a next_page/LOGOUT_REDIRECT_URL como única protección contra next.
- [x] T016 [P] [US1] Implementar context processor y función HMAC compartida en `usuarios/context_processors.py` con salted_hmac y salt propio sobre identidad/clave existente, sin sesión nueva ni token persistido ni sessionid expuesto; «Misma clave e identidad producen la misma huella»; cambia ante nuevo login incluso de la misma persona y solo se renderiza autenticado. Depende de T006–T013; paralelo a T014/T015.
- [x] T017 [US1] Implementar GET usuarios:sesion en `usuarios/views.py` usando función T016 y constant_time_compare: 204 misma huella, 409 ausente/distinta, otros métodos autenticados 405; sin login_not_required, cuerpo sensible, identidad/huella nueva o renovación de sesión; cookie autentica, huella no. Depende de T015/T016; serializar ediciones de views.py.
- [x] T018 [P] [US1] Implementar middleware mínimo en `usuarios/middleware.py` con utilidades Django para no almacenamiento de HTML autenticado sensible, login/revalidación, conservando cabeceras existentes y excluyendo estáticos; no consultas explícitas a BD, manejo de sesiones ni HMAC. Depende de T006–T013; paralelo a T014–T017.
- [x] T019 [US1] Conectar rutas login/logout/sesion en `usuarios/urls.py` y LOGIN_URL, LOGOUT_REDIRECT_URL, middleware/context processor en `config/settings.py`; AuthenticationMiddleware antes de caché y LoginRequiredMiddleware, CSRF/excepciones existentes intactos, sin cambiar backend/expiración/PASSWORD_HASHERS/modelo. Depende de T017/T018. En `config/urls.py`, anteponer la ruta exacta admin/logout/ a admin.site.urls como alias de CerrarSesionView; conservar reverse admin:logout y todos los controles administrativos restantes, sin reemplazar AdminSite.
- [x] T020 [P] [US1] Crear `usuarios/templates/usuarios/login.html` sobre base/Bootstrap: username/password con etiquetas y errores españoles, autocomplete y CSRF, sin reflejar contraseña ni agregar roles/mensajes fuera del contrato, enlace Crear cuenta. Depende de T019.
- [x] T021 [P] [US1] Implementar `usuarios/static/usuarios/sesion.js`: ocultar en pagehide/hidden/blur, revalidar en pageshow.persisted/visible/focus con huella/cookie same-origin sin caché; solo 204 vigente sin redirección y con foco/visibilidad revela; agrupar eventos/cancelar respuestas obsoletas, sin paralelas/bucles/polling/storage/broadcast; fetch redirect=follow: 409 directo o redirected=true con status=200 y URL final del mismo origen/pathname exacto de usuarios:login navegan al login fijo; 200 sin redirección, redirección a otro destino, 403/5xx/timeout/fallo de red mantienen oculto y permiten reintento; solo 204 directo de la URL de revalidación vigente revela; no montar en anónimo, borrar campos o reenviar POST. Depende de T019; paralelo a T020.
- [x] T022 [US1] Integrar huella/guardia en `templates/base.html` con contenido sensible (identidad/campos) y reintento accesible; cierre usuarios:logout POST+CSRF sin diálogo extra, nombre/mensajes existentes, enlace clientes:registrar en navbar y acceso existente de `templates/inicio.html` conservado. Depende de T020/T021.
- [x] T023 [P] [US1] Extender mínimamente `templates/admin/base_site.html` para la guardia compartida y cierre POST+CSRF de AquaLab según plan, sin duplicar JS ni reemplazar permisos/aprobación/nombres de rutas; comprobar cierre propio y alias admin:logout de T019 con destino fijo aunque next llegue por query/POST; LOGOUT_REDIRECT_URL es solo configuración coherente. Depende de T022.
- [x] T024 [P] [US1] Añadir Iniciar sesión en `usuarios/templates/usuarios/registro_recibido.html`, conservando mensaje/flujo de aprobación US 1.1 y navegación anónima sin guardia. Depende de T022; paralelo a T023.
- [x] T025 [P] [US1] Cambiar únicamente expectativa temporal admin:login por usuarios:login en `usuarios/tests/test_setup.py`, manteniendo garantías de `usuarios/tests/test_autenticacion.py` y pruebas existentes de registro/aprobación. Depende de T022; paralelo a T023/T024.
- [x] T026 [US1] Ejecutar y dejar verdes T006–T013 y regresiones `usuarios/tests/test_autenticacion.py`, `usuarios/tests/test_registro.py`, `usuarios/tests/test_admin.py`, `usuarios/tests/test_setup.py` y `clientes/tests/`; corregir defectos sin debilitar garantías ni agregar dependencias, registrar comandos/resultados en `specs/002-inicio-cierre-sesion/tasks.md`. Depende de T023/T024/T025.
- [x] T027 [US1] Ejecutar los diez recorridos de navegador de `specs/002-inicio-cierre-sesion/quickstart.md`: escenarios 1–8, SC-001 <30 s, Atrás/Adelante con/sin bfcache, pestañas, nuevo login mismo/otro usuario, red/500/204 tardío/eventos duplicados, foco/autocompletado/reintento y formularios usuarios/clientes/admin; registrar navegador/versión/entorno/commit/resultados en `specs/002-inicio-cierre-sesion/tasks.md`, sin bibliotecas nuevas ni atribuir DOM/bfcache a pytest; corregir y repetir casos afectados si fallan. Depende de T026. Distinguir en navegador la redirección seguida al login de un 200 inesperado: verificar metadatos/origen/pathname y navegación al login fijo; los demás estados permanecen ocultos con reintento.

**Control de historia:** T026 y T027 deben pasar; login funcional solo no completa FR-012/013.
La garantía visual se valida con JavaScript y navegador del laboratorio; sin JS sigue la
protección del servidor, pero no se certifica SC-004 visual. No cambiar el criterio de aceptación.

## Fase 4: Documentación y validación final — 5 tareas

**Objetivo:** cerrar con evidencia y alcance controlado. Depende de T027.

- [x] T028 [P] Actualizar `README.md` reemplazando referencias temporales de login/logout del admin por el flujo real, conservando Docker/PostgreSQL y comandos de validación; no introducir herramientas/funciones nuevas.
- [x] T029 [P] Resolver únicamente pendientes efectivamente satisfechos de US 1.2/navegación en `CLAUDE.md`, conservando otras historias y la integración Claude/Codex.
- [x] T030 Ejecutar controles finales de `.github/workflows/ci.yml` y `pyproject.toml`: manage.py check, makemigrations --check --dry-run, pytest completo, ruff check y ruff format --check; registrar evidencia en `specs/002-inicio-cierre-sesion/tasks.md` sin generar migraciones ni declarar CI remoto verde por resultados locales. Depende de T028/T029; repetir si cambios/fallos lo justifican.
- [x] T031 Revisar diff final contra `specs/002-inicio-cierre-sesion/spec.md`, `research.md` y `requirements.txt`: ModelBackend/is_active intactos, sin dependencias/tablas/migraciones/tokens persistidos ni secretos expuestos/ámbitos públicos nuevos/regresiones US 1.1/2.1; contrastar los ocho escenarios y S01–S10 y registrar evidencia en `specs/002-inicio-cierre-sesion/tasks.md`. Depende de T030.
- [ ] T032 Registrar cierre y condiciones de revisión en `specs/002-inicio-cierre-sesion/tasks.md`: aprobación formal, pruebas automáticas/visuales, límites reales y trazabilidad SCRUM-42/US 1.2; requerir CI remoto verde y aprobación de un integrante no autor antes del merge, sin marcar controles pendientes ni crear/mergear PR como efecto de esta tarea. Depende de T031.

## Cobertura de escenarios

| Escenario | Test automatizado | Implementación | Complemento |
|---|---|---|---|
| 1. Ingreso aprobado/nombre | T006 | T014/T015/T019/T020/T022 | T027, SC-001 |
| 2. Ya autenticado abre login | T006 | T015/T019 | T026/T027 |
| 3. Campos incompletos | T007/T008 | T014/T020 | Sin authenticate/diagnóstico |
| 4. Credenciales inválidas | T007/T008 | T014/T015 | S01–S04 |
| 5. Ruta protegida anónima | T010/T012 | T017–T019/T022/T023 | T027 |
| 6. Logout desde pantallas | T009/T012/T013 | T015/T019/T022/T023 | T027, misma sesión entre pestañas |
| 7. Atrás/actualizar/URL | T009/T011/T012/T013 | T016–T019/T021–T023 | T027 obligatorio |
| 8. Cuenta pendiente | T007/T008 y suite US 1.1 en T026 | T014/T015 | S01–S05 |

| Seguridad de quickstart | Tareas con evidencia |
|---|---|
| S01 errores uniformes | T007/T014/T026 |
| S02 trabajo comparable | T008/T014/T026 |
| S03 hashers/inutilizables | T008/T014/T026; escalar mezcla real de algoritmos sin cambiarlos |
| S04 DatabaseError sin filtración | T008/T014/T026 |
| S05 regresiones US 1.1 | T010/T025/T026 |
| S06 huella/cookie/otra sesión | T009/T011/T016/T017/T026 |
| S07 no mutación ni excepción pública | T010–T012/T018/T019/T026 |
| S08 respuestas antiguas/errores | T021/T027 |
| S09 bfcache/identidad | T011/T021–T023/T027 |
| S10 regresión US 2.1 | T013/T022/T026/T027 |

FR-014 limita todas las implementaciones y se audita en T031. SC-002/005: T007–T009;
SC-003: T010; SC-004: pruebas de servidor más T027, no solo cabeceras.
Mensajes exactos: «Usuario o contraseña incorrectos» y «Tu cuenta está pendiente de aprobación».
Preservar español, ruff, correo normalizado, contraseña literal y otras sesiones independientes.

## Dependencias y orden de ejecución

```text
Fase 1: T001 → T002 → T005 (suite existente sin cambios)
Fase 2: T004 → T003 (fixtures y nueva ejecución de suite existente)
Fase 3: T006..T013 (pruebas paralelas)
          ├─ T014 → T015 ─┐
          ├─ T016 ───────┴→ T017 ─┐
          └─ T018 ────────────────┴→ T019
                                      ├─ T020 ─┐
                                      └─ T021 ─┴→ T022
                                                  → T023/T024/T025 (paralelas)
                                                    → T026 → T027
Fase 4: T028/T029 (paralelas) → T030 → T031 → T032
```

Cada fase hereda el cierre de la anterior. T002/T005 ya se acreditaron técnicamente antes de
T001; el grafo expresa el bloqueo para avanzar a implementación, no invalida esa evidencia.
Los «Depende de» de las tareas rigen el resto del grafo.
T017 exige T015/T016; T019 exige T017/T018; T022 exige T020/T021; T026 exige T023/T024/T025.
No ejecutar T015/T017 simultáneamente: ambas editan `usuarios/views.py`. No paralelizar ediciones
de fixtures/configuración/layout base ni verificaciones que registran evidencia en este archivo.
Escribir tests en paralelo no autoriza suites simultáneas compitiendo por una misma BD de test.

Solo existe [US1]: depende de US 1.1/2.1 ya integradas; no reimplementar registro/aprobación/clientes.

## Ejemplos de trabajo paralelo de US1

- Después de T005 → T004 → T003: T006 en `usuarios/tests/test_login.py`, T009 en
  `usuarios/tests/test_logout.py` y T013 en `clientes/tests/test_sesion.py`; los otros tests
  T007/T008/T010/T011/T012 también usan archivos distintos y fixtures T003 estables.
- Después de T006–T013: T014 en `usuarios/forms.py`, T016 en
  `usuarios/context_processors.py` y T018 en `usuarios/middleware.py`.
- Después de T019: T020 en `usuarios/templates/usuarios/login.html` y T021 en
  `usuarios/static/usuarios/sesion.js`.
- Después de T022: T023 admin, T024 registro recibido y T025 expectativa del test de inicio.

[P] describe oportunidades; no ordena lanzar agentes ni ejecutar estas tareas ahora.

## Estrategia de implementación y MVP

El MVP es la única historia P1 completa: ocho escenarios, seguridad y regresiones. Incrementos
internos: pruebas → formulario/login/logout → revalidación/cabeceras → interfaces → suite → navegador.
No entregar login solo como si cumpliera toda la historia. Reutilizar entidades existentes; sin
trabajo de crear modelos/campos ni actualizar hash en diagnóstico.

Antes de implementar: revisar tasks.md y ejecutar `$speckit-analyze` cuando se indique. Generar
esta lista no ejecuta análisis, pruebas ni implementación, ni acredita aprobación formal.

**Resumen:** 32 tareas: preparación 3, bases 2, US1 22, validación final 5. Hay 17 tareas [P]
agrupadas por prerequisitos; no todas arrancan a la vez. Hay 27 completadas: T002–T026 y T028/T029,
con T002/T005 acreditadas inicialmente por reporte del usuario. T001, T027 y T030–T032 siguen pendientes.
Las verificaciones ejecutadas por el asistente se distinguen en la evidencia incremental.

## Ejecución incremental del asistente — 2026-10-20

Excepción explícita del usuario: avanzar en esta rama antes de aprobación formal, documentada
en plan.md. T001 sigue pendiente; su bloqueo de proceso se exceptúa para implementar localmente,
sin afirmar aprobación ni autorizar push, PR o merge. T002/T005 conservan evidencia reportada
por el usuario; no se reemplaza por resultados que el asistente no haya ejecutado.

T004: inventario leído: inicio `/`, rutas `usuarios:registro`, `registro_confirmar`,
`registro_recibido` públicas; clientes registrar/confirmar/detalle protegidos por middleware;
admin con staff/permisos propios; login/logout temporales del admin; expectativa temporal en
usuarios/tests/test_setup.py. Se añadirán login/logout/sesion y alias administrativo revisados.
T003: se reutilizan fixtures existentes de aprobada, pendiente, administrador y clientes;
se añade cliente CSRF estricto, sin alterar los datos ni reglas de las fixtures previas.

Estado rojo ejecutado por asistente en Docker/PostgreSQL: nuevas pruebas 41 failed, 11 passed
en 19.61s; rutas/formulario/contexto/cabeceras inexistentes causaron los fallos esperados.
Suite original tras añadir fixture CSRF: 83 passed en 25.58s, ejecutada por el asistente.
Checklist requirements.md: 16/16 revisados, sin alterar marcadores.

### Resultado de implementación y controles ejecutados por el asistente

2026-10-20, rama `002-inicio-cierre-sesion`. T001 se mantiene sin marcar: la excepción explícita
permite desarrollar localmente pero no equivale a aprobación formal del equipo.

- T003/T004: reutilización de fixtures, cliente CSRF y lectura del inventario completados;
  suite original después de la fixture: 83 passed en 25.58s. No se alteraron sus expectativas
  salvo la redirección temporal de test_setup.py contemplada en T025.
- T006–T013: ocho archivos de pruebas añadidos antes de implementar. Estado rojo observado:
  41 failed, 11 passed en 19.61s por funcionalidad ausente; después se reforzaron consultas,
  hashers reales, CSRF de login, rotación/otra identidad y aislamiento de borradores.
- T014/T015: AuthenticationForm sin NFKC, correo con manager existente, contraseña literal,
  diagnóstico sin autenticar pendientes y trabajo real/ficticio Django comprobado. Login/LogoutView
  reutilizados; cierre fijo con POST/CSRF y ModelBackend sin cambios.
- T016/T017: huella HMAC derivada y endpoint protegido de solo lectura; comprobadas rotación,
  nueva sesión, ausencia de autorización por huella y no renovación del registro de sesión.
- T018/T019: cabeceras, configuración y alias administrativo conectados. Permisos de admin
  y modelos conservados. Sin dependencias ni migraciones nuevas.
- T020–T025: login Bootstrap, guardia JS, layouts base/admin, enlace de registro recibido y
  expectativa temporal de inicio actualizados. JS no requiere paquetes ni servicios adicionales.
- T026: `docker compose exec -T web pytest -q --tb=short`: **140 passed in 47.30s**.
  Primera ejecución completa previa al refuerzo: 135 passed in 49.15s.
- `docker compose exec -T web python manage.py check`: sin errores.
- `docker compose exec -T web python manage.py makemigrations --check --dry-run`: No changes detected.
- `docker compose exec -T web ruff check .`: All checks passed.
- `docker compose exec -T web ruff format --check .`: 67 files already formatted.
- `node --check usuarios/static/usuarios/sesion.js` con el Node ya disponible de Codex: correcto.
  Diez comprobaciones adicionales de lógica JS en DOM simulado con ese Node: aprobadas, incluidas
  respuestas obsoletas, red fallida, 200 inesperado, redirección válida/incorrecta y 204/409/403/500.
  No se incorporó Node ni biblioteca alguna a los requisitos del proyecto. No son pruebas de navegador.
- HTTP desde el contenedor al servidor: /usuarios/login/ 200 y /static/usuarios/sesion.js 200.
- Ignore files verificados y completados con patrones de empaquetado/temporales y contexto Docker;
  no se modificó .env ni se imprimieron sus valores. Git diff --check sin errores.

**T027 pendiente:** la herramienta de navegador falló al iniciar con
`windows sandbox failed: helper_unknown_error: setup refresh had errors`.
En ese intento el asistente no obtuvo captura ni evidencia de navegador real. La sintaxis,
respuestas HTTP y simulación JS no demuestran el comportamiento visual. La evidencia manual
reportada posteriormente por el usuario se registra a continuación, sin atribuirla al asistente.

### Evidencia manual de T027 reportada por el usuario

Los estados pendientes de las revisiones anteriores se conservan como historial; el estado
vigente y la resolución de cada faltante se registran en «Cierre técnico local actualizado» al final.

**Registro: 2026-10-20. Fuente:** reporte explícito del usuario en este chat; todas las siguientes
comprobaciones fueron informadas como satisfactorias. El asistente únicamente registra el reporte:
**no las ejecutó ni las observó en un navegador**. El reporte adicional identifica Chrome;
su versión, sistema, hora/fecha efectiva de ejecución y commit/estado exacto probado no fueron
proporcionados y no se inventan.

| N.º del reporte | Comprobación manual informada | Resultado reportado |
|---|---|---|
| 1 | Cambiar de ventana conserva campos del formulario con sesión válida | Satisfactorio |
| 2 | Logout en otra pestaña lleva al login al regresar sin revelar datos antiguos | Satisfactorio |
| 3 | Atrás/Adelante tras logout no muestra el formulario protegido | Satisfactorio |
| 4 | Nueva sesión del mismo usuario descarta contenido de la anterior | Satisfactorio |
| 5 | Nueva sesión de otro usuario descarta contenido anterior | Satisfactorio |
| 6 | Detener web oculta información al regresar; reiniciar y reintentar recupera formulario si sigue válida la sesión | Satisfactorio |
| 7 | Logout desde admin lleva al login AquaLab y el historial no recupera el panel | Satisfactorio |
| 8 | Cliente confirmado permanece; borrador sin confirmar no se crea ni recupera después del logout | Satisfactorio |
| 9 | Login con ?next=/admin/ termina en inicio, no en admin | Satisfactorio |
| 10 | GET /usuarios/logout/?next=/admin/ devuelve 405 sin cerrar; botón POST cierra correctamente | Satisfactorio |
| 11 | Acceso directo a / y /clientes/registrar/ después del logout exige login sin contenido protegido | Satisfactorio |
| 12 | Chrome DevTools: GET /usuarios/sesion/ devuelve 204 con cabeceras de no almacenamiento | Satisfactorio, reportado por el usuario |
| 13 | Interceptar window.fetch solo para /usuarios/sesion/ y simular HTTP 500 mantiene oculto el contenido y permite reintentar; restaurar fetch recupera la sesión válida | Satisfactorio, reportado por el usuario; respuesta simulada en cliente, no fallo 500 del servidor observado |
| 14 | Chrome DevTools mostró «Successfully served from back/forward cache»; con sesión válida, Reintentar permitió recuperar la página | Satisfactorio, reportado por el usuario; acredita esta restauración concreta, no todos los casos de bfcache |
| 15 | Otro perfil de Chrome mantiene una sesión independiente del mismo usuario después de cerrar la primera | Satisfactorio, reportado por el usuario |
| 16 | Alternar ventanas conserva errores y valores; confirmar, cancelar y repetir envíos de clientes conserva el comportamiento sin duplicados | Satisfactorio, reportado por el usuario |
| 17 | Login aprobado tarda menos de 30 s, muestra el nombre correcto y abrir login autenticado redirige al inicio | Satisfactorio, reportado por el usuario |
| 18 | Registro anónimo y autocompletado funcionan al alternar ventanas, sin perder información ni redirecciones indebidas | Satisfactorio, reportado por el usuario |
| 19 | Logout mediante POST funciona con JavaScript deshabilitado; las páginas protegidas siguen exigiendo autenticación | Satisfactorio, reportado por el usuario; no certifica historial visual sin JS |
| 20 | Respuesta 204 retrasada 12 s no revela contenido después del timeout | Satisfactorio, reportado por el usuario; no acredita por sí sola una respuesta de generación anterior |
| 21 | Cambios rápidos entre ventanas sin bucles ni solicitudes simultáneas observables | Satisfactorio, reportado por el usuario; observación de navegador, no prueba exhaustiva de concurrencia |

T027 permanece **pendiente**, sin modificar su checkbox. Se acredita mediante el reporte del
usuario una restauración bfcache con sesión válida y un HTTP 500 simulado en window.fetch limitado
a la revalidación. No se infieren pruebas de todos los casos de bfcache ni de respuestas de una generación
anterior a partir del caso de timeout de 12 segundos; detener web y simular 500 son comprobaciones distintas. Las pruebas automatizadas y la
simulación JS del asistente conservan su atribución y no se convierten en pruebas de navegador.

### Faltantes identificados en la revisión anterior (histórico; resueltos abajo)

La lista siguiente contiene únicamente aspectos no acreditados por el reporte ni por evidencia
visual anterior; no solicita repetir los resultados satisfactorios ya reportados. Los casos de servidor
ya verificados por pytest no se consideran faltantes de evidencia automatizada.

| Prioridad | Referencia de quickstart.md | Evidencia visual todavía faltante |
|---|---|---|
| 1 | Recorrido 6; S09 | En una entrada protegida después de logout/cambio de sesión, documentar con DevTools si Atrás/Adelante restaura bfcache o hace una petición nueva. El bloqueo visual ya se reportó; falta identificar el mecanismo en ese caso. Si Chrome expulsa la entrada, registrarlo sin forzar una restauración. |
| 1 | S08 | Retener un 204, ocultar y volver a la pestaña para iniciar otra generación, liberar solo el 204 anterior: el contenido debe seguir oculto hasta una respuesta válida vigente. El timeout de 12 s y los cambios rápidos ya están acreditados y no se piden de nuevo. |
| 2 | S08 | Simular por separado 200 sin redirección, redirección seguida a destino distinto del login y 403: ocultamiento y Reintentar; restaurar fetch y recuperar la misma sesión. La redirección legítima, 500 y timeout ya fueron reportados. |
| 2 | Recorridos 1 y 3 | Abrir directamente confirmación/detalle de cliente y admin como anónimo; comprobar ausencia de contenido. Probar login vacío, inexistente, contraseña incorrecta y pendiente con contraseña correcta/incorrecta; contrastar mensajes del contrato. Hay tests de servidor, falta reporte de estos recorridos visuales. |
| 2 | S08/S09, párrafo posterior | Recuperar foco desde barra de direcciones o diálogo, también en admin, sin quedar oculto permanentemente. Autocompletado y registro anónimo al alternar ventanas ya están acreditados. |
| 2 | Recorrido 9 | Iniciar registro de usuario sin confirmar, cerrar la sesión y volver: no recuperar el borrador; una cuenta ya confirmada permanece. Los borradores y filas de clientes ya están acreditados. |

**Separación de cobertura:** pytest-django verifica los ocho escenarios en el servidor, S01–S07,
CSRF/next en ambos cierres, aprobación/permisos y regresiones US 1.1/2.1. Las 14 pruebas Node
verifican S08/S09 con DOM, eventos y temporizadores simulados; no prueban renderizado ni bfcache
real. Los reportes 1–21 acreditan exclusivamente las observaciones reales de Chrome descritas.
No se exige repetir manualmente las variantes de CSRF/next ya automatizadas para acreditar T027;
se conservan pendientes solo los recorridos visuales explícitos todavía no reportados.

**Datos de trazabilidad pendientes:** versión de Chrome, sistema, fecha de ejecución, referencia
al commit/estado local probado y resultados por navegador soportado, según el encabezado de la
sección de navegador de quickstart.md. No se infiere compatibilidad universal de este reporte.

No completar T027 ni declarar terminada la historia hasta registrar la evidencia restante y
resolver cualquier fallo observado. T001 sigue pendiente; T028/T029 se completan anticipadamente
por autorización explícita del usuario, según la excepción al orden registrada abajo.

**Cierre final pendiente:** T030–T032 se mantienen sin marcar porque sus condiciones de cierre
siguen sin satisfacerse, incluidas T027 y la revisión final de la entrega. T028/T029 se adelantaron
por autorización expresa del usuario; esto no declara completa la fase de cierre ni la historia.
Los controles técnicos equivalentes a T030 se ejecutaron nuevamente y se registran a continuación;
no acreditan CI remoto, aprobación del equipo ni pruebas visuales no realizadas.

### Revisión técnica y cierre parcial del asistente — 2026-10-20

- Estado inicial/final observado: rama 002-inicio-cierre-sesion. Se conservaron cambios pendientes
  de implementación, planificación e integración Codex; no se descartaron ni cambiaron ramas.
- Revisión de sesion.js: generaciones y abortos al ocultar evitan aceptar respuestas antiguas;
  eventos repetidos se agrupan y una solicitud vigente bloquea otra; la respuesta solo se acepta
  con foco/visibilidad. Se identificó un caso concreto: un proveedor/interceptor de fetch que
  devuelve 204 después del timeout pese al aborto podía revelar contenido de la generación actual.
  El fetch nativo normalmente rechaza al abortarse; esta regresión comprueba defensivamente que
  la guardia no depende de que todos los proveedores/interceptores respeten el aborto.
- Se añadió una comprobación de controller.signal.aborted antes de procesar respuesta, sin cambiar
  el mecanismo. Ahora el caso permanece oculto y presenta mensaje de fallo con reintento.
- Se creó usuarios/tests/js/sesion.test.cjs: 14 regresiones reproducibles con node:test/assert/vm
  estándar, temporizadores y DOM simulados. Primera ejecución: 13 aprobadas y 1 fallida (204 tras
  timeout). Después de la corrección: 14 aprobadas, 0 fallidas. Incluye 204 viejo, eventos duplicados,
  foco/visibilidad, bfcache simulado, red, 200 inesperado, redirecciones legítimas/incorrectas,
  409/403/500 y reintento. No requiere instalar paquetes; no sustituye navegador real ni forma
  parte del CI Python actual.
- Comando JS ejecutado: Node existente de Codex con `--test usuarios/tests/js/sesion.test.cjs`.
- `docker compose exec -T web pytest -q`: **140 passed in 44.27s**, PostgreSQL 16 de Compose.
- `docker compose exec -T web python manage.py check`: System check identified no issues.
- `docker compose exec -T web python manage.py makemigrations --check --dry-run`: No changes detected.
- `docker compose exec -T web ruff check .`: All checks passed.
- `docker compose exec -T web ruff format --check .`: 67 files already formatted.
- `git diff --check`: correcto.
- T028 completada: README describe login propio, aprobación, cierre POST/CSRF, borradores,
  revalidación visual y sus límites; documenta el comando opcional de regresiones JS con Node ya
  disponible, sin convertirlo en dependencia de la app o afirmar que pytest las ejecuta.
- T029 completada: CLAUDE.md ya no presenta como pendientes los cambios integrados de login/logout,
  enlaces y navegación; conserva US 3.1/3.2 y US 4.1 y remite a evidencia/aprobación pendientes.
- Excepción al orden: el usuario autorizó expresamente adelantar T028/T029 antes de completar
  T027. No se marcan T030–T032 ni T001, ni se declara terminada la historia.
- Revisión del diff: cambios de aplicación limitados a autenticación/sesiones/templates/tests,
  junto a ignores y documentación; la configuración de integración Codex era previa. No se
  detectaron archivos temporales/volcados o secretos reales en archivos candidatos. Solo
  .env.example está versionado; .env no se leyó ni se añadió. Modelos, migraciones, requirements,
  Constitution y spec mantienen sus archivos originales; backend y permisos administrativos
  conservados. Las regresiones US 1.1/2.1 están incluidas en los 140 tests.
- No hubo instalación de dependencias, push, PR, merge, edición de main ni borrado de datos/volúmenes.

### Revalidación del cierre técnico local — 2026-10-20

**Cambios de esta revisión:** solo este tasks.md; sin correcciones de código, porque la revisión
no demostró un defecto nuevo. Se registraron siete evidencias adicionales del usuario y se
contrastó T027 contra los diez recorridos y S08–S10 de quickstart.md. T027 permanece pendiente
por los faltantes concretos enumerados arriba y sus datos de trazabilidad.

Controles ejecutados por el asistente sobre HEAD c6ad062 con los cambios locales pendientes,
en la rama 002-inicio-cierre-sesion (no se atribuyen a ese commit los archivos sin confirmar):

| Comando ejecutado | Resultado |
|---|---|
| `docker compose exec -T web pytest -q` | **140 passed in 45.53s** |
| Node existente de Codex: `--test usuarios/tests/js/sesion.test.cjs` | **14 passed, 0 failed**, 106.4487 ms; DOM simulado |
| `docker compose exec -T web python manage.py check` | System check identified no issues (0 silenced) |
| `docker compose exec -T web python manage.py makemigrations --check --dry-run` | No changes detected |
| `docker compose exec -T web ruff check .` | All checks passed! |
| `docker compose exec -T web ruff format --check .` | 67 files already formatted |
| `git diff --check` | Sin errores |
| `docker compose exec -T db postgres --version` | PostgreSQL 16.15 |

El ejecutable Node usado fue el ya disponible en
C:/Users/marti/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node.exe;
no se instaló software. Los controles locales reproducen los controles aplicables de CI,
pero **CI remoto no ejecutado/acreditado**; el workflow Python tampoco ejecuta las pruebas Node.

**Revisión de T031 realizada localmente:** diff de archivos versionados e inventario de todos
los nuevos; código de autenticación, middleware, huella, guardia, layouts y tests contrastados con
spec/Constitution y la trazabilidad de ocho escenarios/S01–S10. ModelBackend predeterminado,
is_active, modelos y permisos administrativos intactos. HMAC no autentica ni se persiste, CSRF
sigue activo, destinos fijos y diagnóstico sin autenticar inactivos. No hay cambios en
requirements.txt, pyproject.toml, Dockerfile/Compose, modelos, migraciones, spec o Constitution.
No se detectaron secretos reales ni archivos accidentales en los cambios revisados; .env no se
leyó ni añadió. Las credenciales ficticias de tests/CI no son secretos de despliegue.
La integración Codex y los ignores/documentación previos se conservaron; no se descartaron cambios.
Las regresiones originales de US 1.1/2.1 permanecen incluidas en la suite completa aprobada.

**T030/T031:** su trabajo local está realizado y registrado, pero ambos checkbox permanecen
pendientes por la condición de entrada de fase 4 (T027). La excepción autorizada al orden cubría
T028/T029; no se presenta este adelanto de controles/revisión como cierre final de la fase.
Repetir controles afectados si aparecen correcciones después de validar T027.

**T032 — síntesis preparada para revisión del equipo:** implementación local cubre ingreso
aprobado, errores/pending sin autenticación, rutas protegidas y logout POST/CSRF propio/admin;
conserva sesiones independientes y descarta DOM/borradores anteriores. Evidencia local actual:
140 tests Python, 14 regresiones de lógica JS, checks/lint/formato/migraciones correctos y
21 reportes manuales de Chrome. Restan los casos y metadatos indicados para T027, aprobación
formal de spec (T001, Draft intacto), cierre secuencial T030/T031 y evidencia final. Antes del
merge se requieren CI remoto verde y revisión/aprobación de un integrante no autor, mediante
PR vinculado a SCRUM-42 / US 1.2 y su spec. No existe aprobación inferida ni PR creado en este
trabajo. T032 sigue pendiente; la historia no se declara completada.

**Estado histórico previo a la nueva evidencia de cierre:** completadas T002–T026, T028 y T029 (27);
pendientes T001, T027, T030, T031 y T032 (5). Sin push, PR, merge, cambio de rama,
dependencias nuevas ni borrado de datos/volúmenes.

### Cierre técnico local actualizado — registro 2026-10-20

Esta sección prevalece sobre los estados históricos anteriores. **Fuente de todas las pruebas
reales de navegador: reportes del usuario; Codex no las ejecutó ni observó.** Se registra el nuevo
reporte de nueve puntos y la respuesta aclaratoria «Sí, está todo testeado», en respuesta explícita
a los casos de campos vacíos, pendiente con contraseña incorrecta y redirección desconocida.

| Evidencia nueva reportada | Resultado informado y alcance |
|---|---|
| Login inexistente/contraseña incorrecta y pendiente con contraseña correcta | Error genérico y mensaje de aprobación pendiente respectivamente; satisfactorio |
| Inicio, confirmación/detalle de clientes y administración anónimos | Sin contenido protegido; satisfactorio |
| Login y registro públicos | Accesibles sin sesión; satisfactorio |
| Borrador de registro de usuario y cuenta confirmada/aprobada | Borrador descartado al cerrar sin confirmar; cuenta persistida; satisfactorio |
| Foco desde barra de direcciones o diálogo en AquaLab/admin | Recuperación sin bloqueo permanente; satisfactorio |
| Historial tras logout inspeccionado con DevTools | Mecanismo de restauración o nueva petición comprobado y sin contenido protegido; el reporte no especifica cuál ocurrió en cada entrada |
| Revalidación simulada 200 inesperada y 403 | Contenido oculto y reintento funcional; satisfactorio |
| 204 de generación anterior durante otra revalidación | No reveló contenido anterior; satisfactorio |
| Resto de verificaciones previamente registradas | Ratificadas como satisfactorias por el usuario |
| Aclaración solicitada: login vacío, pendiente con contraseña incorrecta y redirección distinta del login | Usuario confirma que también fueron testeados satisfactoriamente; no se infieren pasos o capturas adicionales |

**Trazabilidad de navegador:** Chrome **155.0.8059.85 (Official Build), 64-bit**, informado por el
usuario. Sistema operativo: **no proporcionado**. Fecha/hora efectiva de ejecución: **no
proporcionada** (2026-10-20 es la fecha de registro). Commit/estado local exacto probado:
**no proporcionado**; HEAD c6ad062 y cambios sin confirmar son observación de Codex, no una
identificación del estado probado declarada por el usuario. Otros navegadores soportados y sus
resultados: **no proporcionados**. No se certifica compatibilidad fuera del Chrome reportado.
El usuario autorizó registrar expresamente los metadatos no proporcionados; no se inventan.

**Resolución de T027:** completada sobre la cobertura funcional reportada en Chrome, con las
limitaciones de trazabilidad anteriores expresas. No queda un caso funcional de la lista anterior
sin confirmación. No equivale a ejecución por Codex, garantía exhaustiva de bfcache o validación
universal de navegadores. La evidencia combina fuentes sin confundirlas:

| Referencia de quickstart | Cobertura registrada |
|---|---|
| Recorridos 1–3; escenarios 1–5/8 | Público/protegido, nombre, <30 s, login activo y mensajes: reportes anteriores y nuevo reporte/aclaración; pytest verifica los resultados de servidor |
| Recorridos 4–5 | Campos/errores, no reenvíos/duplicados, logout compartido y sesión independiente: reportes anteriores |
| Recorridos 6–7 | Historial, bfcache válido confirmado en DevTools, mecanismo tras logout, nuevo login mismo/otro usuario y admin: reportes anteriores y nuevo reporte |
| Recorrido 8; S08/S09 | Caída/recuperación, 500 simulado, 200/403, redirecciones legítima/desconocida, timeout de 12 s, 204 de generación anterior y eventos rápidos: reportes anteriores/nuevo reporte/aclaración |
| Recorridos 9–10; S10 | Borradores de usuario/cliente, filas confirmadas, POST sin JS y protección del servidor: reportes anteriores/nuevo reporte |
| Párrafo de foco/autocompletado/registro anónimo | Alternancia, autocompletado, barra de direcciones/diálogo y admin: reportes anteriores/nuevo reporte |
| Ocho escenarios y S01–S07 | pytest-django; no certifica comportamiento visual |
| Clasificación y carreras S08/S09 | 14 regresiones Node con DOM/temporizadores simulados; no certifican bfcache real |

**T030 — controles finales ejecutados por Codex:** rama 002-inicio-cierre-sesion, HEAD c6ad062
más modificaciones locales sin confirmar. Suite Python en Docker/PostgreSQL del proyecto;
Node existente, sin instalación de dependencias:

| Comando | Resultado exacto |
|---|---|
| `docker compose exec -T web pytest -q` | **140 passed in 47.19s** |
| `node --test usuarios/tests/js/sesion.test.cjs` (ejecutable existente de Codex indicado arriba) | **14 passed, 0 failed**, 135.7385 ms |
| `docker compose exec -T web python manage.py check` | System check identified no issues (0 silenced) |
| `docker compose exec -T web python manage.py makemigrations --check --dry-run` | No changes detected |
| `docker compose exec -T web ruff check .` | All checks passed! |
| `docker compose exec -T web ruff format --check .` | 67 files already formatted |
| `git diff --check` | Sin errores; repetido después de editar la documentación |

**T031 — revisión final local:** revisados diff versionado e inventario de archivos nuevos contra
spec/Constitution y revisiones previas. ModelBackend, is_active, normalización del registro,
CSRF, permisos del admin y autenticación de rutas conservados; sin modelos, migraciones o
dependencias nuevas. requirements.txt, pyproject.toml, modelos/migraciones, spec y Constitution
sin cambios. La suite incluye regresiones US 1.1/2.1; no se debilitaron sus garantías. Sin defectos
concretos nuevos que justifiquen cambios de código. Revisión de secretos sobre los archivos
candidatos sin leer .env: sin hallazgos de claves/tokens reales; la búsqueda es heurística,
no una garantía exhaustiva. Integración Codex e ignores identificados separadamente abajo.
T027 resuelta y T028/T029 hechas: T030 y T031 se completan ahora en su orden previsto.

**T032 — síntesis preparada, pendiente de cierre formal:** ingreso/logout con Django, aprobación
existente, diagnóstico pendiente sin autenticación, destinos fijos, no-store y revalidación por
misma sesión implementados. Los ocho escenarios tienen tests; 140 Python y 14 JS aprobados,
checks correctos y recorridos reales de Chrome acreditados por reporte del usuario. Riesgos y
límites: metadatos manuales incompletos; compatibilidad certificada solo en Chrome reportado;
protección visual requiere JS; no se exige ocultamiento instantáneo de ventanas que permanecen
visibles; pruebas Node aún fuera del CI Python. T001 sigue pendiente, spec Draft intacta;
la excepción local documentada no equivale a aprobación del equipo. Antes del merge deben
existir CI remoto verde y aprobación de un integrante no autor. No hay evidencia de ninguno,
ni se creó PR. T032 conserva su checkbox pendiente por aprobación formal/evidencia final.

### Preparación del futuro commit y PR (sin staging ni commit en esta revisión)

- **Incluir en la entrega US 1.2:** config/settings.py y config/urls.py; usuarios/forms.py,
  views.py, urls.py, context_processors.py, middleware.py, static/usuarios/sesion.js;
  templates/base.html, templates/admin/base_site.html, templates/includes/estilo_sesion.html,
  templates/includes/guardia_sesion.html; usuarios/templates/usuarios/login.html y
  registro_recibido.html; usuarios/tests/conftest.py, test_setup.py, los ocho archivos nuevos
  de tests Python (siete de usuarios y clientes/tests/test_sesion.py) y usuarios/tests/js/sesion.test.cjs;
  README.md/CLAUDE.md y todos los artefactos nuevos de specs/002-inicio-cierre-sesion/.
  spec.md ya está versionada y no debe modificarse para inventar aprobación.
- **Acordar por separado con el equipo:** .agents/skills/ (diez skills),
  .specify/integration.json y .specify/integrations/codex.manifest.json. Son integración
  de desarrollo Codex, no funcionalidad de la US; mantienen Claude como integración principal.
  El manifiesto contiene metadatos de instalación. Decidir si versionarlos en un commit separado
  de herramientas compartidas o conservarlos locales; no incluirlos accidentalmente con git add .
- **Cambios auxiliares a revisar expresamente:** .gitignore y .dockerignore (artefactos locales,
  empaquetado/contexto y exclusión de .env). Son útiles pero no implementación de login;
  incluirlos solo con alcance explícito o separarlos como mantenimiento. No se descartaron.
- **Excluir:** .env, credenciales reales, caches, logs, volúmenes/volcados y ejecutables locales.
  No se detectaron candidatos accidentales nuevos. No hay paquetes Node ni lockfile que agregar.
- README/CLAUDE se sincronizaron puntualmente con T027 completada para no dejar pendientes
  visuales ya satisfechos; el resto de las historias permanece intacto.
- Antes de preparar el PR: obtener aprobación formal con referencia verificable (T001), acordar
  la selección de integración/ignores, revisar el diff staged y conservar esta evidencia junto
  a código/plan/tests. Futuro título: «US 1.2 — Inicio y cierre de sesión (SCRUM-42)»;
  vincular spec y explicar la excepción de proceso y límites. CI y revisión de compañero
  se verificarán al existir el PR, no se dan por satisfechos con los controles locales.

**Estado vigente exacto: 30/32 completadas, T002–T031. Pendientes T001 y T032.**
No hubo push, PR, merge, staging, commit, cambio de rama ni borrado de datos/volúmenes.
