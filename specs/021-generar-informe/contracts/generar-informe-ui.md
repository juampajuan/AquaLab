# Contrato de interfaz: Generar informe

**Feature**: `021-generar-informe` | **Plan**: [plan.md](../plan.md)

Todas las rutas requieren sesión (`LoginRequiredMiddleware`; sin sesión → 302 al login) y los POST
llevan CSRF. Prefijo `informes/` (US 7.1). `<pk>` de estudio inexistente → **404**.

## `GET /informes/estudios/<pk>/` — `informes:control` (cambio de la US 7.1)

- Listo para informar: «Generar informe» pasa a ser un **enlace** (`btn btn-primario`, ícono
  `file-text`) a `informes:vista_previa`.
- Con informe emitido: en lugar del aviso solo informativo, botón **Ver informe** (`btn
  btn-primario`) → `informes:ver`.
- Sin listo y sin informe: igual que la US 7.1 (botón deshabilitado con el motivo).

## `GET /informes/estudios/<pk>/vista-previa/` — `informes:vista_previa`

- Cualquier empleado con sesión.
- Estudio no listo o ya informado → 302 a `informes:control` + error con el motivo de
  `motivo_para_no_informar` (US 7.1).
- Listo → 200 `informes/vista_previa.html`:
  - aviso de advertencia arriba: «Vista previa: este informe todavía no fue emitido.»;
  - el documento (`informes/documento.html`) con la marca **«BORRADOR»** en lugar del número;
  - acciones: **Emitir informe** (POST a `informes:generar`, `btn btn-primario`, evita el doble
    envío con `data-enviado`) solo con `perms.informes.emitir_informes`; sin el permiso, el aviso
    «Solo un integrante del grupo Bioquímicos puede emitir el informe.»; **Volver al control**
    (`btn btn-secundario`).

## Documento del informe — `informes/documento.html` (parcial)

Recibe el diccionario `contenido` (data-model) y opcionalmente `numero`/`fecha`/`emitido_por`.

1. **Encabezado institucional**: marca del laboratorio, nombre, dirección, matrícula, teléfono y
   correo; a la derecha «Informe N° INF-000001» (o «BORRADOR») y la fecha de emisión.
2. **Cliente**: nombre o razón social, documento («CUIT 30-…»/«DNI …»), domicilio, correo.
3. **Muestra**: N° PI, nombre, origen, fecha de muestreo, fecha de ingreso, sitio de extracción,
   responsable del muestreo, tipo de vertido.
4. **Estudio**: N° de estudio y tipo de estudio.
5. **Resultados** (tabla): **Prueba** (nombre y código), **Resultado** (`resultado_texto`),
   **Unidad** (`|unidad`; vacía en A/P), **Límite** (`limite_texto` y origen si no es general),
   **Norma**, **Cumple** (etiqueta `ui/estado.html`: «Cumple» `success`, «Fuera de norma» `danger`,
   «Sin límite comparable» `neutral`). Las filas fuera de norma se resaltan.
6. **Pie**: «Responsable técnico: …» y, si está emitido, «Emitido por <nombre o correo> el
   <d/m/Y H:i>».

Datos vacíos se muestran «—».

## `POST /informes/estudios/<pk>/generar/` — `informes:generar` (reemplaza el aviso de la US 7.1)

- Sin el permiso `informes.emitir_informes` → **403** (`@permission_required(...,
  raise_exception=True)`).
- `emitir_informe(...)`:
  - éxito → 302 a `informes:ver` + éxito «Se emitió el informe INF-000001 del estudio X.»;
  - `InformeNoDisponible` → 302 a `informes:control` + error con el motivo (incluye «El informe de
    este estudio ya fue generado.» ante doble envío);
  - `EmitirInformeError` → 302 a `informes:control` + error con su mensaje;
  - `DatabaseError` → 302 a `informes:control` + «No se pudo emitir el informe. Intentá
    nuevamente.»; nada cambia.

## `GET /informes/estudios/<pk>/informe/` — `informes:ver`

- Cualquier empleado con sesión. Sin informe → 404.
- 200 `informes/ver.html`: el documento a partir de `informe.contenido`, con número, fecha y quién
  lo emitió; acciones **Volver al control** y **Ver detalle del estudio**.

## `GET /estudios/<pk>/` — `estudios:detalle` (cambio)

- Si el estudio tiene informe: botón **Ver informe** (`btn btn-secundario`, ícono `file-text`) →
  `informes:ver`.

## Servicio — `informes.servicios.emitir_informe(estudio_pk, usuario)`

- Errores: `EmitirInformeError` («Se requiere una sesión activa.», «Se requiere permiso para emitir
  informes.»); `InformeNoDisponible` (motivo de la US 7.1; estudio inexistente: «El estudio no está
  disponible.»).
- Devuelve el `Informe` creado. Una sola transacción: estudio bloqueado → lock de numeración →
  armado → creación → estudio «Informe generado».
