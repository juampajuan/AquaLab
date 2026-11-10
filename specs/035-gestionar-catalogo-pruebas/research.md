# Research: Gestionar catálogo de pruebas

Decisiones técnicas de SCRUM-73. Formato: decisión, motivo y alternativas descartadas.

## R1 – Dónde vive y cómo se accede
- **Decisión**: vistas, formularios y servicio en la app `pruebas`, URLs `/administracion/pruebas/...`
  con namespace `catalogo` (`config/urls.py` incluye `pruebas.urls` en `administracion/pruebas/`,
  después de `administracion:`). Acceso con `usuarios.permisos_administracion.administracion_requerida`
  y revalidación en el servicio con `autorizar_administracion`.
- **Motivo**: «una app por módulo» (constitution II); mismo acceso que el resto del panel 025
  (grupo «Administradores» + permiso, 403, sin excepción para superusuarios), como pide FR-015.
- **Alternativas**: vistas en `usuarios/views_administracion.py` (mezcla el catálogo con cuentas);
  permiso nuevo `gestionar_pruebas` (la responsable eligió el del panel).

## R2 – Confirmación y concurrencia
- **Decisión**: mismo esquema que tipos de estudio (US 5.5): el formulario guarda un borrador firmado
  (`django.core.signing`, atado a usuario y sesión, TTL 1 h) con `operacion`, `prueba_id`,
  `version` vista y datos; la pantalla de resumen hace POST a `catalogo:confirmar`. Nuevo campo
  `Prueba.version`: el servicio bloquea la fila (`select_for_update`) y si la versión cambió
  rechaza con «La prueba cambió mientras la editabas. Revisá los datos actuales».
- **Motivo**: FR-004 y FR-016; un patrón ya probado en el proyecto, sin JavaScript.
- **Alternativas**: comparar campo por campo (más frágil); bloqueo pesimista al abrir (bloquea a
  otros administradores).

## R3 – Servicio único
- **Decisión**: `pruebas/gestion.py:gestionar_prueba(usuario, operacion, prueba_id, version_esperada,
  datos)` con operaciones `crear`, `editar`, `desactivar`, `reactivar`, `eliminar`; dentro de
  `transaction.atomic()` revalida permiso, existencia, versión, «en uso» (`esta_en_uso()`),
  referencias (R5), límites (R4) y `full_clean()` (fórmula), guarda `Prueba` y `LimiteVertido`,
  completa auditoría (R6) y sube `version`. Errores tipados (`PruebaEnUso`, `PruebaReferenciada`,
  `VersionDesactualizada`, `DatosInvalidos`).
- **Motivo**: un solo lugar con todas las reglas (como `gestion_tipos`), así un envío alterado no
  saltea ninguna (US3 Esc. 3).

## R4 – Límites
- **Decisión**: `formularios.validar_limite(texto)` acepta vacío, número (`pruebas.limites.NUMERO`,
  coma o punto) o «Ausente»/«Ausencia» (`TEXTOS_AUSENTE`); si ambos son números, mín ≤ máx. Vale
  para generales y por vertido. Se aplica solo en los formularios y el servicio de esta historia, no
  en `Prueba.clean()`, para que la importación por CSV siga aceptando su contenido (FR-017).
- **Motivo**: aclaración 1; reutiliza la misma lectura que la evaluación (`leer_limite`).

## R5 – Referencias en fórmulas
- **Decisión**: `dependientes(prueba)` = pruebas cuya fórmula referencia `{CODIGO}` de esta
  (con `referencias_formula`, sobre las pruebas con `tipo_calculo=FORMULA`, en memoria: el catálogo
  tiene ~100 filas). Eliminar o cambiar el código se rechaza si hay alguna dependiente; desactivar
  avisa listando las dependientes activas. El listado calcula, para cada prueba activa, las
  referencias a pruebas inactivas.
- **Motivo**: FR-006, FR-009, FR-013 y la decisión previa de permitir desactivar con aviso.

## R6 – Auditoría mínima
- **Decisión**: `creada_por`, `fecha_creacion`, `modificada_por`, `fecha_modificacion` en `Prueba`
  (nulos para las existentes y para las de la importación). Los completa solo `gestionar_prueba`.
  La ficha muestra «Sin registro» si faltan.
- **Motivo**: aclaración 2 (solo la última modificación).
- **Alternativas**: tabla de historial (fuera de alcance).

## R7 – Prueba activa en el resto de la app
- **Decisión**:
  - `estudios/forms_tipos.py`: el selector ofrece pruebas activas más las inactivas que el tipo ya
    tiene (marcadas «inactiva»), para poder editar el tipo sin perderlas.
  - `estudios/gestion_tipos.py:validar_datos`: rechaza agregar una prueba inactiva que el tipo no
    tenía; «reactivar» exige al menos una prueba activa.
  - `estudios/forms.py:AgregarPruebaForm` y `servicios.agregar_prueba`: solo activas.
  - `estudios/catalogo.py:configuracion_bloqueada`: solo pruebas activas (estudios nuevos); sin
    ninguna, el error existente «El tipo de estudio no está disponible o no tiene pruebas» pasa a
    «El tipo de estudio no tiene pruebas activas».
  - Carga, cálculo, corrección, validación e informe no miran `activa` (FR-012): no se tocan.
  - **Versión de los tipos**: `desactivar` y `reactivar` (en `gestionar_prueba`, en la misma
    transacción) suben `version` de cada `TipoEstudio` que incluye la prueba, con `select_for_update`
    en el mismo orden (prueba → tipos por pk). Así `crear_estudio`, que ya compara la versión del tipo
    con la de la confirmación (`VersionDesactualizada`), rechaza una confirmación abierta antes del
    cambio y nunca crea un estudio con otras pruebas que las confirmadas (hallazgo U1 del análisis).
- **Motivo**: FR-010/011/012 y la decisión previa (estudios nuevos solo con activas).

## R8 – Formulario y campos bloqueados
- **Decisión**: el campo fórmula queda siempre visible con la ayuda «Solo si el tipo de cálculo es
  Fórmula» (sin JavaScript; hallazgo I1). `PruebaForm` (código, nombre, tipo de cálculo, fórmula, unidades, límites generales,
  norma, límite de detección, observación) + `LimitesVertidoForm` (cloacal y canal: mín, máx,
  norma). En uso: los campos del método se renderizan `disabled` con el mensaje de US3 Esc. 1, y el
  servicio ignora o rechaza cualquier cambio a ellos. `es_calculada` se deduce de la fórmula. Pasar a
  «Directo» vacía la fórmula. La ayuda de límites explica «Ausente» vs máx. 0 (US 9.1).
- **Motivo**: FR-001, FR-003, FR-007, aclaración 1.

## R9 – Listado, admin e importación
- **Decisión**: el listado (`administracion:pruebas`) suma «Nueva prueba», enlace «Ver ficha» a
  `catalogo:ficha` en lugar de «Editar en Django Admin» y la marca «Depende de una prueba inactiva:
  <códigos>». El admin de Django (`pruebas/admin.py`) y `importar_catalogo_pruebas` no cambian.
- **Motivo**: FR-013, FR-014, FR-017 y la decisión de dejar el admin como respaldo.

## R11 – Reemplazo en cascada
- **Decisión**: campo `Prueba.reemplazada_por` (FK a `Prueba`, `PROTECT`, nulo). `gestionar_prueba`
  operación `desactivar` con `reemplazo_id` opcional: valida (activa, misma `unidad`, distinta, no
  dependiente directa ni indirecta), bloquea en orden prueba vieja → pruebas dependientes (por pk) →
  tipos (por pk), y en la misma transacción: `activa=False` + `reemplazada_por`; en cada dependiente
  reescribe la fórmula cambiando `{VIEJO}` por `{NUEVO}` con una sustitución sobre las referencias de
  `referencias_formula` (no texto libre), `full_clean()` y `version += 1`; en cada `TipoEstudio`
  que la incluye cambia la `TipoEstudioPrueba` (o la borra si ya estaba la nueva) y sube `version`.
- **Cálculo** (`estudios/calculo.py`): al armar los valores de una fórmula, si una referencia
  `{X}` no está entre las pruebas del estudio, se busca una asignación del estudio cuya prueba llegue
  a `X` siguiendo `reemplazada_por` (en cadena, con tope para evitar ciclos) y se usa su valor; el
  orden de dependencias y `calculo.afectadas` usan la misma resolución. Una función única,
  `calculo.resolver_referencias(asignaciones)`, devuelve `{codigo_en_formula: asignacion}`.
- **Motivo**: aclaración 4; los resultados ya calculados guardan su fórmula y no cambian, pero el
  recálculo usa la fórmula vigente de la prueba, así que sin la resolución un estudio viejo perdería
  el resultado de las dependientes al corregir una medición.
- **Alternativas**: recrear las dependientes (lo que pide el criterio original; descartado por la
  responsable); copiar la fórmula en cada `PruebaEstudio` (migración grande y duplica datos).

## R10 – Reactivar con dependencias inactivas
- **Decisión**: se permite reactivar una prueba cuya fórmula usa otra inactiva; la confirmación lo
  avisa («Usa en su fórmula una prueba inactiva: <códigos>») y el listado la sigue marcando.
- **Motivo**: hallazgo U2 del análisis; mismo criterio que desactivar con aviso.
