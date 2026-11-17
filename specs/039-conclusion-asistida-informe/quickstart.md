# Validación y cierre — US 10.2

US1–US4 están implementadas. Esta guía conserva los comandos de reproducción y registra al final la evidencia de cierre; las instrucciones de preparación no implican que haya que repetir todas las suites. Ver [contratos](contracts/conclusiones-ui.md), [modelo](data-model.md) y [matriz](test-matrix.md) para los oráculos y la cobertura aprobada. No se modifican requisitos ni escenarios.

## Requisitos y entorno aislado

Docker Desktop/Compose ya disponible, repo en E:, puerto local 8102 libre; Python 3.12, PostgreSQL 16 y WeasyPrint aportados por Dockerfile existente. Para JavaScript usar Node 20 como CI, sin npm ni dependencias nuevas. Si se usa Node 24 local, registrar diferencia y repetir en Node 20 antes de dar paridad con CI. No cambiar la instalación del sistema solo para ejecutar esta guía sin acordarlo.

El primer build puede descargar imágenes y ocupar varios GB. Configurar previamente el almacenamiento de Docker en E: según la instalación existente; no trasladar datos de Docker ni modificar configuración de Windows como parte de esta US. No usar la base habitual ni credenciales reales. El entorno siguiente no publica PostgreSQL y usa solo información sintética.

Para reproducir la validación, usar `.local-validacion/us102/compose.yml` (carpeta ignorada por el repo) con esta configuración de infraestructura:

```yaml
services:
  db:
    image: postgres:16
    environment:
      POSTGRES_DB: aqualab_us102
      POSTGRES_USER: aqualab
      POSTGRES_PASSWORD: solo-demo-local
    tmpfs:
      - /var/lib/postgresql/data
    healthcheck:
      test: [CMD-SHELL, pg_isready -U aqualab -d aqualab_us102]
      interval: 5s
      timeout: 5s
      retries: 10
  web:
    build:
      context: E:/Martino-Codex/AquaLab
    image: aqualab-us102-validacion:local
    command: python manage.py runserver 0.0.0.0:8000
    environment:
      SECRET_KEY: clave-ficticia-validacion-us102
      DEBUG: "True"
      AQUALAB_ENTORNO: desarrollo
      ALLOWED_HOSTS: localhost,127.0.0.1,testserver
      DATABASE_URL: postgres://aqualab:solo-demo-local@db:5432/aqualab_us102
      EMAIL_BACKEND: django.core.mail.backends.console.EmailBackend
      ASISTENTE_API_KEY: ""
    ports:
      - "127.0.0.1:8102:8000"
    volumes:
      - E:/Martino-Codex/AquaLab:/app
    depends_on:
      db:
        condition: service_healthy
```

Las claves de arriba son deliberadamente ficticias y solo para este entorno. tmpfs es efímero: detener/eliminar ese contenedor descarta exclusivamente la demo aislada; exportar evidencias sintéticas necesarias antes. No ejecutar down de otros proyectos ni eliminar volúmenes globales.

PowerShell, desde la raíz indicada:

```powershell
Set-Location E:/Martino-Codex/AquaLab
$us102Compose = 'E:/Martino-Codex/AquaLab/.local-validacion/us102/compose.yml'
docker compose -p aqualab-us102 -f $us102Compose build web
docker compose -p aqualab-us102 -f $us102Compose up -d db
docker compose -p aqualab-us102 -f $us102Compose run --rm web python manage.py migrate
docker compose -p aqualab-us102 -f $us102Compose run --rm web python manage.py cargar_demo
docker compose -p aqualab-us102 -f $us102Compose up -d web
```

Estado esperado del entorno: migración aditiva de BorradorConclusion aplicada en la base aislada; datos ficticios del comando existente cargar_demo y acceso en `http://127.0.0.1:8102`. El comando de demo informa sus usuarios locales; no suponer que crea todas las combinaciones de permisos, firma y estados requeridos por esta US. Preparar dos bioquímicos distintos con firma válida y cuentas negativas mediante administración existente; nunca reutilizar cuentas reales. La demo no reemplaza los fixtures automatizados y sus 38 escenarios. Para anomalías de información incompleta usar fixtures controlados de tests, sin modificar resultados validados por UI/admin para forzar estados imposibles.

## Pruebas automatizadas y controles

Comandos de validación disponibles:

```powershell
docker compose -p aqualab-us102 -f $us102Compose run --rm web pytest informes/tests/test_conclusion_hechos.py informes/tests/test_conclusion_revision.py informes/tests/test_conclusion_emision.py informes/tests/test_conclusion_ia.py
docker compose -p aqualab-us102 -f $us102Compose run --rm web pytest informes asistente estudios/tests
docker compose -p aqualab-us102 -f $us102Compose run --rm web pytest
docker compose -p aqualab-us102 -f $us102Compose run --rm web ruff check .
docker compose -p aqualab-us102 -f $us102Compose run --rm web ruff format --check .
docker compose -p aqualab-us102 -f $us102Compose run --rm web python manage.py check
docker compose -p aqualab-us102 -f $us102Compose run --rm web python manage.py makemigrations --check --dry-run
node --version
node --test usuarios/tests/js config/tests/js estudios/tests/js pruebas/tests/js asistente/tests/js informes/tests/js
```

No es necesario repetir la suite completa si ya se ejecutó sobre exactamente el mismo código y no hay cambios posteriores que la invaliden; conservar SHA/estado de árbol, comandos y resultados reales. La base de tests debe ser test_aqualab_us102 en este PostgreSQL aislado; nunca ejecutar contra datos reales. Fixtures usan backend de correo locmem y proveedor IA simulado para inspeccionar cuerpos/adjunto sin red. Las pruebas de timeout utilizan eventos y doubles controlados, liberando finalmente workers de prueba; no simular fallos llamando Groq real.

Si el Node local no descubre directorios como CI, enumerar archivos explícitos sin instalar paquetes y registrar esa diferencia:

```powershell
$us102JsFiles = @(rg --files usuarios/tests/js config/tests/js estudios/tests/js pruebas/tests/js asistente/tests/js informes/tests/js -g '*.test.cjs' -g '*.test.js')
node --test @us102JsFiles
```

CI incluye `informes/tests/js` una sola vez en el comando explícito y conserva Node 20 y PostgreSQL 16. El Node del sistema local es 24.13.0; para la evidencia de cierre se utilizó Node 20.19.0 portátil, sin paquetes npm ni cambios de instalación del sistema.

Comprobar CSS compilado usando el CLI ya presente en Docker, conservando evidencia del hash antes/después:

```powershell
$us102CssAntes = (Get-FileHash E:/Martino-Codex/AquaLab/static/css/aqualab.css -Algorithm SHA256).Hash
docker compose -p aqualab-us102 -f $us102Compose run --rm web tailwindcss -i static/src/aqualab.css -o static/css/aqualab.css --minify
$us102CssDespues = (Get-FileHash E:/Martino-Codex/AquaLab/static/css/aqualab.css -Algorithm SHA256).Hash
$us102CssAntes -eq $us102CssDespues
git diff --check
git status --short
```

Esperado: igualdad cuando el compilado ya está sincronizado. Si cambia, revisar e incluir el compilado durante implementación; el cierre verificó la compilación sin modificar el archivo versionable. makemigrations --check --dry-run no debe proponer cambios adicionales a la migración aditiva incluida. No exigir ausencia absoluta de migraciones: la persistencia nueva necesita una aditiva.

## Recorridos verificables

1. Con Bioquímicos y permiso efectivo, abrir estudio listo con dos incumplimientos vigentes. «Proponer conclusión» presenta ambos una vez con hechos exactos. Con ASISTENTE_API_KEY vacía se avisa plantilla; no hay aprobación ni emisión automática. Comparar con vigentes, no con catálogo; incluir valores A/P y < LD en tests.
2. Con todas evaluables conformes, plantilla indica cumplimiento. Casos parciales de fixtures identifican ausencia de vigente/límite/norma, preservan hechos y nunca afirman cumplimiento total. Editar/reaprobar no borra advertencias.
3. Editar directamente en el único campo de conclusión, salir y volver/recargar: recupera el borrador mediante autoguardado, sin mensajes redundantes de éxito. Las advertencias de pruebas no evaluables permanecen separadas, visibles y no editables. Aprobar confirma el texto exacto con sus advertencias y espera cualquier guardado pendiente. Recargar sin cambios conserva esa aprobación, sin crear otra. Primera propuesta vacía sin confirmación; reemplazar contenido existente sí requiere confirmación.
4. Editar, regenerar texto idéntico y cambiar fuentes en los fixtures invalida cada aprobación. Probar dos pestañas: conflicto visible sin pisar edición ni recuperar aprobación vieja. Propuesta tardía no se instala sobre una edición nueva. Reaprobación requiere revisión expresa de hechos actuales.
5. Otra persona bioquímica autorizada emite con la revisión aprobada. Snapshot conserva quién aprobó y quién emitió; cambiar catálogo/perfil después no cambia la copia. Probar emisión sin conclusión sin fila/borrador/aprobación inválida y con IA no disponible.
6. Cuentas sin grupo/permiso, solo grupo, solo permiso, inactivas y sin sesión: botones y POST directos guardan la política. Solo permiso sigue pudiendo emitir sin conclusión según reglas actuales. CSRF se prueba con cliente que lo verifica; no deshabilitar protección.
7. Consultar informe, PDF, imprimir, correo txt/HTML y adjunto: mismo texto aprobado, tildes, saltos y caracteres escapados; conclusión extensa se pagina sin recortes. Inspeccionar correo sintético en consola o capturarlo con backend locmem en tests, sin enviar a direcciones reales. El reenviado no llama IA.
8. Informe histórico sin conclusion: sin bloque/título nuevo y JSON idéntico; acciones nuevas sobre emitido rechazadas. No regenerar artefactos históricos.
9. Fallos de red, credenciales, cuota, respuesta inventada y timeout se prueban con dobles del adaptador; todos producen respaldo con los mismos datos o permiten emitir sin conclusión. Revisar que no se registren credenciales, prompts ni datos personales.

La comparación automática de medios asegura el mismo string entregado a templates/WeasyPrint/mail, escaping y adjunto correcto; la revisión del PDF real y la impresión complementa maquetación y no sustituye pytest. Evidencias solo sintéticas en .local-validacion, sin publicar capturas o datos locales accidentalmente.

## Criterio de cierre y limpieza opcional

Registrar los 38 escenarios, resultados de controles complementarios, suite y Node 20, revisión visual/funcional, commit/estado exacto probado y límites encontrados. Los resultados efectivos están en la sección de cierre siguiente. Cerrar únicamente el entorno aislado cuando ya no sea necesario:

```powershell
docker compose -p aqualab-us102 -f $us102Compose down
```

Ningún comando de esta guía autoriza commit, push, PR o merge.

## Evidencia de cierre — 2026-11-16

Rama `39-Conclucion-Asistida`, base y HEAD `c5a0030a06de65fc56949b8716c36506a2e2bf46`. La implementación está en el árbol de trabajo, todavía sin commit. Se conserva localmente el inventario con SHA256 de cada archivo de código probado; no se atribuye la implementación al contenido del commit base.

Funcionalidad final: hechos de validaciones vigentes, redacción mediante el cliente Groq de US10.1, respaldo fijo ante indisponibilidad, borrador persistente y compartido, autorización conjunta, aprobación expresa del texto exacto, invalidación por edición/regeneración/cambios de origen y comprobación transaccional al emitir. Emisión opcional de conclusión con copia inmutable y trazabilidad; consulta, PDF, impresión y correo utilizan esa misma copia. Históricos sin cambios y pruebas no evaluables identificadas sin inventar cumplimiento.

Interfaz definitiva aprobada por el responsable: un único editor siempre editable, bloque protegido de advertencias y estado Pendiente/Aprobada. Acciones Proponer, Aprobar, Emitir con conclusión aprobada y Emitir sin conclusión. Sin modo Editar, botón Guardar manual, casilla adicional, segunda representación del texto, paneles de hechos ni huellas/revisiones/tokens visibles. Persistencia, recuperación y protecciones siguen internas; los errores reales de guardado se informan.

El responsable confirmó expresamente en el pedido de cierre que realizó las pruebas manuales de los recorridos y que todo funciona, incluida la simplificación de interfaz. Esa aprobación funcional se registra como evidencia de T099; no equivale a revisión de PR por otro integrante. La revisión sintética previa incluyó otro emisor, conflicto entre pestañas, conservación al recargar, igualdad consulta/impresión y PDF de cuatro páginas sin recortes. No se repite esa revisión ni se solicita otra confirmación.

Controles finales: 121/121 tests JavaScript con Node 20.19.0, incluidos los 47 del editor; Ruff check PASS, Ruff format PASS (324 archivos), Django check sin incidencias, makemigrations sin cambios y migrate --plan sin operaciones pendientes en el entorno aislado. Tailwind 4.3.3 compilado a un archivo local de comparación: idéntico al CSS versionable. Logs locales `cierre-node20.log` y `cierre-calidad.log`.

Backend: una pasada integral en PostgreSQL 16 terminó con **2634 passed y 2 failed en 1464.36 s**, sin errores ni omitidos. Ambos fallos eran expectativas de interfaz anteriores en `test_vista_previa.py`: el botón «Emitir informe» y el marcador del manejador inline, reemplazados por las dos emisiones y el controlador del editor. Se actualizaron únicamente esas assertions, conservando las comprobaciones de permisos, firma y matrícula. El archivo completo se repitió: **9 passed en 12.83 s**, con Ruff check/format aprobados. No hubo cambios de código funcional ni se repitió innecesariamente la integral.

Resultado consolidado por identificador exacto de test, usando el resultado más reciente: **2636/2636 casos backend aprobados**, sin fallos pendientes. Esto combina la integral y la repetición dirigida; no se presenta la integral original como una ejecución sin fallos ni se suman los nueve casos repetidos. Los 215 tests backend de `asistente` pasaron en la integral. Logs/XML: `cierre-pytest.*` y `cierre-vista-previa.*`, locales e ignorados. Las pasadas históricas interrumpidas no cuentan como aprobación.

Comandos efectivos de la etapa backend final:

```powershell
docker compose -p aqualab-us102 -f $us102Compose run --rm web pytest --create-db -q --junitxml=.local-validacion/us102/cierre-pytest.xml
docker compose -p aqualab-us102 -f $us102Compose run --rm web pytest informes/tests/test_vista_previa.py -q --junitxml=.local-validacion/us102/cierre-vista-previa.xml
```

**38/38 escenarios de aceptación ejecutados y aprobados en la integral**, contrastados por archivo, función y variantes parametrizadas contra su XML; detalle exacto en `cierre-cobertura.csv` y registro local. Los 19 FR y nueve criterios originales tienen la cobertura de la matriz aprobada: Jira 1 → US1.1/5–10; Jira 2 → US1.3–5/US4.4 y privacidad; Jira 3 → US1.2/US4.5; Jira 4 → US2.1/12/15; Jira 5 → US2.1–3/9–14; Jira 6 → US3.1–2/6–7; Jira 7 → US3.3–4; Jira 8 → US4.1–6; Jira 9 → US3.5–6. No son claves Jira.

**Cierre: 101/101 tareas completadas, cero pendientes funcionales o de validación local.** T098 registra los resultados reales anteriores; T099 queda respaldada por la aprobación manual del responsable; T100 y T101 por esta documentación y la auditoría final. La presentación de T056/T065/T066 se ajustó por instrucción expresa del responsable a la interfaz simplificada descrita arriba, sin alterar requisitos, escenarios, IDs o dependencias.

Identidad del árbol probado: los 42 archivos del manifiesto inicial de cambios de código conservaron su SHA256 durante toda la integral. Después solo se adaptó `informes/tests/test_vista_previa.py` y se actualizaron documentos; el nuevo test se ejecutó de nuevo. Manifiesto final de los 43 archivos de código/tests/estilos/configuración cambiados: `.local-validacion/us102/cierre-codigo-final-sha256.txt`, SHA256 `BBC97C382B7B9CDA004CE12D5CEB1FE3ED8CA091BBEDA74302B481089910EC7F`. HEAD sigue siendo el commit base, no un commit de implementación.

Límites de la evidencia: Groq y correo se simulan en tests; no se afirma disponibilidad del proveedor ni entrega externa de correo. Sin clave IA funciona el respaldo previsto, sin bloquear emisión. No se identificó funcionalidad pendiente. La clave Jira propia, publicación, CI remoto y revisión de PR del equipo siguen pendientes; no se inventan aprobaciones ni se declara merge/DONE en Jira. Constitution y US10.1 permanecen intactas.

## Inventario final para el commit

53 archivos: 17 modificados y 36 nuevos respecto de la base. `M` = modificado; `N` = nuevo. Incluir explícitamente estos archivos; no usar `git add .`.

```text
M .dockerignore
M .github/workflows/ci.yml
M informes/contenido.py
M informes/forms.py
M informes/models.py
M informes/servicios.py
M informes/templates/informes/correos/informe_cuerpo.html
M informes/templates/informes/correos/informe_cuerpo.txt
M informes/templates/informes/documento.html
M informes/templates/informes/documento_impreso.html
M informes/templates/informes/vista_previa.html
M informes/tests/conftest.py
M informes/tests/test_vista_previa.py
M informes/urls.py
M informes/views.py
M static/css/aqualab.css
M static/css/informe.css
N informes/conclusion_hechos.py
N informes/conclusion_ia.py
N informes/conclusiones.py
N informes/migrations/0006_borradorconclusion.py
N informes/static/informes/conclusion.js
N informes/templates/informes/_conclusion.html
N informes/templates/informes/_editor_conclusion.html
N informes/templates/informes/conclusion_conflicto.html
N informes/tests/fixtures/us102_historicos/correos/informe_cuerpo.html
N informes/tests/fixtures/us102_historicos/correos/informe_cuerpo.txt
N informes/tests/fixtures/us102_historicos/documento.html
N informes/tests/fixtures/us102_historicos/documento_impreso.html
N informes/tests/js/conclusion.test.cjs
N informes/tests/test_borrador_conclusion.py
N informes/tests/test_conclusion_adaptador.py
N informes/tests/test_conclusion_autorizacion.py
N informes/tests/test_conclusion_caracterizacion.py
N informes/tests/test_conclusion_concurrencia.py
N informes/tests/test_conclusion_consultas.py
N informes/tests/test_conclusion_emision.py
N informes/tests/test_conclusion_forms.py
N informes/tests/test_conclusion_hechos.py
N informes/tests/test_conclusion_ia.py
N informes/tests/test_conclusion_interfaz.py
N informes/tests/test_conclusion_revision.py
N informes/views_conclusiones.py
N specs/039-conclusion-asistida-informe/checklists/requirements.md
N specs/039-conclusion-asistida-informe/contracts/conclusiones-ui.md
N specs/039-conclusion-asistida-informe/contracts/redaccion-ia.md
N specs/039-conclusion-asistida-informe/data-model.md
N specs/039-conclusion-asistida-informe/plan.md
N specs/039-conclusion-asistida-informe/quickstart.md
N specs/039-conclusion-asistida-informe/research.md
N specs/039-conclusion-asistida-informe/spec.md
N specs/039-conclusion-asistida-informe/tasks.md
N specs/039-conclusion-asistida-informe/test-matrix.md
```

Excluir `.env`, `.local-validacion/` completo (resultados, compose, Node portátil, XML, logs, PDFs, capturas y datos sintéticos), bases, cachés y archivos temporales. No hay archivos de esas categorías en el inventario versionable. `.dockerignore` evita enviar evidencias locales al contexto Docker; CI únicamente amplía el comando de tests JavaScript. La única migración es la aditiva `0006_borradorconclusion`, sin backfill ni permisos nuevos. No hay dependencias nuevas.

Propuesta de commit: `feat(informes): agregar conclusión asistida al informe`. No se ejecutó git add, commit, push, PR, merge ni rebase.
