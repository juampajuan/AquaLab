# Research: Generar informe

**Feature**: `021-generar-informe` | **Plan**: [plan.md](./plan.md)

No quedan `NEEDS CLARIFICATION`: flujo, copia de datos, numeración, permisos, «< LD», alcance y
enlaces se resolvieron en la sección *Clarifications* de la spec (12 respuestas).

Punto de partida (`main` con la US 7.1, PR #34): app `informes` sin modelos, con
`motivo_para_no_informar` (regla única), `comprobar_generacion` (bloquea el estudio y revalida),
`estudios_para_informar`, las vistas `listar`, `control` y `generar` (POST que hoy solo avisa
«próximamente»), y sus tests. De la US 6.4: `Validacion` vigente con evaluación y límites, grupo
«Bioquímicos» (migración `estudios.0008`), `pruebas/limites.py`. Del ajuste A/P:
`texto_presencia`. Del N° PI (US 4.1): máximo + 1 bajo `pg_advisory_xact_lock`.

## R1 — Modelo `Informe` con la copia de los datos en un `JSONField`

- **Decision**: `informes.Informe` con `numero` (`PositiveIntegerField`, único), `estudio`
  (`OneToOneField(Estudio, on_delete=PROTECT, related_name="informe")`), `emitido_por`,
  `fecha_emision` y `contenido` (`JSONField`) con la copia de todo lo que se muestra. Detalle en
  [data-model.md](./data-model.md).
- **Rationale**: el informe es un documento inmutable: se lee entero y nunca se consulta por sus
  partes. Un `jsonb` guarda la foto completa en una fila, sin repetir el esquema de cliente,
  muestra y pruebas (FR-010, SC-003). El `OneToOneField` garantiza un informe por estudio también
  en la base (FR-012). Los valores numéricos se guardan como texto (`str(Decimal)`), nunca como
  `float` (principio IV).
- **Alternatives**: tablas espejo (`InformeCliente`, `InformeLinea`…: mucho esquema para datos que
  no se consultan); leer en vivo de cliente, muestra y validaciones (cambiaría al editar, contradice
  FR-010 y la US 7.3).

## R2 — Un solo armado y un solo template para la vista previa y el emitido

- **Decision**: `informes/contenido.py:armar_contenido(estudio)` devuelve el diccionario del
  informe (laboratorio, cliente, muestra, estudio, pruebas) ya listo para mostrar. La vista previa
  lo arma en el momento; la emisión lo arma con el estudio bloqueado y lo guarda en `contenido`.
  Ambas pantallas usan el mismo parcial `informes/documento.html` con ese diccionario; la vista
  previa agrega la marca «Borrador».
- **Rationale**: asegura que el emitido muestre exactamente lo mismo que la vista previa (SC-002)
  y que el informe emitido se dibuje solo desde la copia (FR-010).
- **Alternatives**: templates separados (se desincronizan); guardar HTML renderizado (ata la copia
  al diseño de hoy; la US 7.3 necesita los datos para el PDF).

## R3 — Contenido de cada prueba y «< LD»

- **Decision**: por cada asignación del estudio (todas Completadas con validación vigente),
  `armar_contenido` copia código, nombre, unidad del resultado, `resultado` (texto exacto de
  `Resultado.valor`), `resultado_texto` (lo que se muestra), límites, norma, origen y evaluación de
  la `Validacion` vigente (FR-004), y el límite de detección del catálogo. `resultado_texto`:
  - prueba A/P → `texto_presencia` («Ausente»/«Presente»);
  - límite de detección numérico y resultado menor → «< » + el límite con coma (ej. «< 0,1»);
  - si no → `valor_mostrado` con coma decimal.
  El límite se muestra como en el detalle (`texto_limite` de la US 6.4: «6.4 a 8.5», «máx. 350.0»).
- **Rationale**: reutiliza la evaluación y los textos de la 6.4 en lugar de recalcular (supuesto
  «Evaluación» de la spec); el formato decimal con coma es el de la interfaz en es-AR.
- **Alternatives**: recalcular la evaluación con el catálogo actual (contradice FR-004 y FR-012 de
  la US 6.4).

## R4 — Ajuste de la regla de la US 6.4 para «< LD» (FR-016)

- **Decision**: `LimitesAplicables` suma `deteccion: str = ""` (con valor por defecto, así las
  construcciones existentes no cambian). `limites_aplicables` la completa con
  `prueba.limite_deteccion` (los límites por vertido no tienen detección propia). En `evaluar`, con
  límite «Ausente»/«Ausencia»: cumple si `valor == 0` **o** el límite de detección es numérico y
  `valor < deteccion`.
- **Rationale**: la regla sigue en un solo lugar (`pruebas/limites.py`, CLAUDE.md); la validación y
  el detalle la toman sin cambios. Revertirla si el laboratorio opina distinto es una línea.
- **Alternatives**: aplicarla solo en el informe (el detalle y la validación dirían otra cosa).

## R5 — Numeración correlativa sin huecos

- **Decision**: `siguiente_numero()` = máximo + 1 (desde 1), calculado dentro de la transacción de
  emisión después de `pg_advisory_xact_lock(7_200_001)`; `Informe.numero_mostrado` →
  `f"INF-{numero:06d}"`. `numero` es `unique` como red de seguridad.
- **Rationale**: es el mismo mecanismo del N° PI (CLAUDE.md, US 4.1): las secuencias dejan huecos
  ante un rollback (SC-004). El lock es global a los informes, independiente del lock del estudio.
- **Alternatives**: `AutoField` o secuencia (huecos); número = id del estudio (no es correlativo).

## R6 — Servicio `emitir_informe` dentro de la transacción de `comprobar_generacion`

- **Decision**: `informes/servicios.py:emitir_informe(estudio_pk, usuario)`:
  1. sesión activa y `usuario.has_perm("informes.emitir_informes")` («Se requiere permiso para
     emitir informes.»);
  2. `atomic`; `comprobar_generacion` se divide en `estudio_listo_bloqueado(estudio_pk)` (bloquea y
     revalida, lanza `InformeNoDisponible`) que reutilizan `comprobar_generacion` y la emisión;
  3. advisory lock de numeración → `siguiente_numero()`;
  4. `armar_contenido(estudio)` → `Informe.objects.create(...)`;
  5. estudio → «Informe generado».
  Devuelve el `Informe`.
- **Rationale**: es lo que la US 7.1 dejó pedido en CLAUDE.md («crear el informe dentro de esa
  transacción»). Dos emisiones simultáneas se serializan por el bloqueo del estudio; la segunda ve
  el estado «Informe generado» y recibe el motivo de la 7.1 (FR-012, caso borde de doble envío).
  Orden de locks: estudio, después numeración; ninguna otra operación toma el lock de numeración.
- **Alternatives**: confiar solo en el `OneToOneField` (daría un `IntegrityError` en lugar del
  motivo).

## R7 — Permiso «Puede emitir informes» asignado a «Bioquímicos» por migración

- **Decision**: `Informe.Meta.permissions = [("emitir_informes", "Puede emitir informes")]` en
  `informes/migrations/0001_initial.py`; `0002_permiso_bioquimicos.py` (datos, depende de
  `estudios.0008_grupo_bioquimicos`) crea los permisos con `create_permissions` (mismo truco de
  `models_module` que `estudios.0008`), obtiene o crea el grupo «Bioquímicos» y le agrega el
  permiso. Reversa: lo quita del grupo. El fixture `bioquimico` suma el permiso nuevo.
- **Rationale**: mismo patrón que la US 6.4 (FR-014); permiso separado de validar (Clarifications).
- **Alternatives**: reutilizar `validar_resultados` (no permite separarlos después).

## R8 — Pantallas y rutas

- **Decision**:
  - `informes:control` (7.1): el botón «Generar informe» pasa de `POST generar` a un enlace a la
    vista previa; con informe emitido muestra «Ver informe» (FR-017).
  - `informes:vista_previa` (GET, cualquier empleado): si el estudio no está listo, 302 al control
    con el motivo; si está, el documento con la marca «Borrador» y, con el permiso, «Emitir
    informe» (POST a `informes:generar`, `data-enviado`).
  - `informes:generar` (POST, `@permission_required("informes.emitir_informes",
    raise_exception=True)`): llama a `emitir_informe`; éxito → 302 a `informes:ver` con «Se emitió
    el informe INF-000001 del estudio X.»; `InformeNoDisponible` → 302 al control con el motivo.
    Reemplaza el aviso «próximamente» (los tests de la 7.1 se actualizan).
  - `informes:ver` (GET, cualquier empleado): el documento desde `contenido`, sin marca; 404 si el
    estudio no tiene informe.
  - `estudios:detalle`: «Ver informe» si el estudio tiene informe (FR-017).
- **Rationale**: conserva el nombre `informes:generar` que la 7.1 reservó para la emisión y sigue el
  patrón revisar → confirmar del sistema.
- **Alternatives**: vista previa como paso del POST (no se puede volver con el navegador sin
  reenviar).

## R9 — Datos institucionales en `settings.AQUALAB_LABORATORIO`

- **Decision**: un diccionario en `config/settings.py` con `nombre`, `direccion`, `matricula`,
  `responsable_tecnico` y `logo`, de ejemplo (marcados «DEMO»). `logo` es una referencia: hoy
  `"aqualab"` (la marca de AquaLab, `ui/logo.html` en versión para documento); cuando llegue el del
  laboratorio será la ruta de su imagen en `static/`, con un nombre nuevo si cambia, para que los
  informes viejos sigan mostrando el suyo. `armar_contenido` copia estos datos, incluida la
  referencia al logo, al contenido del informe.
- **Rationale**: «un solo lugar» (FR-006); copiarlos al emitir mantiene los informes viejos aunque
  cambien (FR-010).
- **Alternatives**: modelo editable en el admin (YAGNI hasta que el laboratorio pida editarlo);
  variables de entorno (no son secretos).
