# Contrato de interfaz: Envío del informe por correo

**Feature**: `029-enviar-informe` | **Plan**: [plan.md](../plan.md)

Todas las rutas requieren sesión (`LoginRequiredMiddleware`). `<pk>` es el del **estudio** (como
`informes:ver`); estudio sin informe emitido → **404**.

## `GET /informes/estudios/<pk>/informe/` — `informes:ver` (cambio)

- Con `perms.informes.emitir_informes`: botón **Enviar por correo** (`btn btn-secundario`, ícono
  `mail`) → `informes:enviar`, junto a «Descargar PDF».
- Sección **Envíos por correo** (tarjeta, para cualquier empleado):
  - Sin envíos: «Este informe todavía no se envió por correo.»
  - Con envíos: tabla con **Fecha** (`d/m/Y H:i`), **Enviado a**, **Enviado por**
    (`get_full_name` o correo) y **Resultado** (`ui/estado.html`: «Enviado» con `tipo="success"`,
    «Falló» con `tipo="danger"`), del más reciente al más antiguo.

## `GET /informes/estudios/<pk>/informe/enviar/` — `informes:enviar`

- Requiere `informes.emitir_informes` (sin permiso → **403**).
- Pantalla de confirmación (`informes/enviar_confirmar.html`):
  - Encabezado: sección «Informes», anterior «Informe INF-…» → `informes:ver`, miga «Enviar por
    correo», título «Enviar informe por correo».
  - Aviso: «Se enviará el informe {numero} por correo a {email}, con el PDF adjunto.»
  - Resumen (`ui/dato.html`): Informe, Cliente, Correo, Último envío («{d/m/Y H:i} a {destinatario}»
    o «Nunca se envió»).
  - Formulario POST con `csrf_token` y `<input type="hidden" name="clave" value="<uuid nuevo>">`;
    botón **Enviar informe** (`btn btn-primario`, ícono `mail`, se deshabilita al enviar) y enlace
    **Cancelar** (`btn btn-secundario`) → `informes:ver`.

## `POST /informes/estudios/<pk>/informe/enviar/`

- Requiere `informes.emitir_informes` (403). `clave` faltante o inválida → redirige a
  `informes:enviar` con «La confirmación no es válida. Volvé a intentarlo.» (sin enviar).
- Resultado → 302 a `informes:ver` con un mensaje:

| Caso | Mensaje (nivel) | Correo | Registro |
|---|---|---|---|
| Enviado | «Se envió el informe {numero} a {email}.» (éxito) | 1 | `enviado` |
| Falla de correo o de PDF | «No se pudo enviar el informe a {email}. Intentá nuevamente.» (error) | 0 | `fallido` + log `informes.envios` |
| Clave ya usada (doble envío) | «El informe {numero} ya se había enviado con esta confirmación.» (información) | 0 | ninguno nuevo |
| Error de base | «No se pudo registrar el envío. Intentá nuevamente.» (error) | — | — |

## Correo

- De: `DEFAULT_FROM_EMAIL`. Para: `Cliente.email` vigente. Adjunto: `{numero}.pdf`
  (`application/pdf`, de `informes.pdf.generar_pdf`).
- Asunto: «Informe {numero} – AquaLab».
- Cuerpo (texto plano, español): saludo a `contenido.cliente.nombre_completo`; «Le enviamos el
  informe {numero} del estudio N° {estudio.numero} ({estudio.tipo}) de la muestra N° PI
  {muestra.numero_pi} ({muestra.nombre}).»; «El informe está adjunto en PDF.»; firma
  `contenido.laboratorio.nombre`. Sin enlaces a la aplicación ni contraseñas.
