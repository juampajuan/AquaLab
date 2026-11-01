# Contrato de interfaz: Modificar las mediciones

**Feature**: `017-modificar-mediciones` | **Plan**: [plan.md](../plan.md)

Todas las rutas requieren sesión iniciada (sin sesión → 302 al login) y llevan CSRF en los POST.
Pantallas con `base.html` y los componentes de `templates/ui/`, como la carga de mediciones
(US 6.1, `contracts/cargar-mediciones-ui.md` de la spec 015). `<pk>` inexistente → **404**.

## `GET /estudios/<pk>/` — `estudios:detalle` (cambio)

- Botón **Corregir mediciones** (`btn btn-secundario`, ícono `pencil`) junto a «Cargar
  mediciones», solo si `estudio.admite_correcciones` y alguna prueba tiene medición.
- Columna Medición: si la medición fue corregida, una línea más en `text-xs text-tinta-suave`:
  «Corregida por <nombre o correo> · <d/m/Y H:i>».

## `GET /estudios/<pk>/mediciones/corregir/` — `estudios:corregir_mediciones`

- Estudio con informe emitido → 302 a `detalle` + error «El estudio ya tiene el informe emitido:
  sus mediciones y resultados no se pueden cambiar.»
- Sin mediciones → `ui/estado_vacio.html` con «Este estudio no tiene mediciones para corregir.» y
  enlace al estudio.
- Tabla de las pruebas con medición, por código: **Código**, **Prueba**, **Unidad** (`|unidad`),
  **Cargada por** (nombre o correo y fecha `d/m/Y H:i`; si fue corregida, también «Corregida por
  …») y **Medición**: `<input type="text" inputmode="decimal" name="medicion_<asignacion_pk>"
  value="<valor tal como se escribió, con coma>">` y oculto `original_<asignacion_pk>` con el
  mismo valor en texto canónico (punto decimal). Errores junto al campo como en la carga.
- Acciones: **Revisar cambios** (`accion=revisar`) y **Cancelar** (enlace al detalle).

## `POST /estudios/<pk>/mediciones/corregir/`

`accion` no reconocida → 302 a `detalle` + «La acción no es válida.». En `revisar` y `editar`,
informe emitido → 302 a `detalle` con el error de arriba.

### `accion=revisar`

- Inválido → 200 con el formulario, valores conservados y errores:
  - campo vacío: «La medición no puede quedar vacía.»;
  - formato: los mensajes de `leer_valor` (US 6.1);
  - sin cambios: error general «No hay cambios para guardar.».
- Válido → 200 `estudios/corregir_mediciones_confirmar.html`: aviso «Se corregirán N mediciones en
  el estudio X (muestra PI Y).» («Se corregirá 1 medición…» con una), tabla **Código / Prueba /
  Valor anterior / Valor nuevo / Unidad** solo con las que cambian y, si corresponde, aviso de
  advertencia «Perderán la validación: COD · nombre, COD · nombre.». Ocultos `medicion_<pk>` y
  `original_<pk>` de todas las filas. Botones **Guardar correcciones** (`accion=confirmar`, evita
  el doble envío con `data-enviado`), **Volver a editar** (`accion=editar`) y **Cancelar**.

### `accion=editar`

200 con el formulario y los valores reenviados.

### `accion=confirmar`

- Formulario inválido → 200 con el formulario y errores (nada cambia).
- Válido → `servicios.corregir_mediciones(...)` y 302 a `detalle` con:
  - éxito, si hubo corregidas: «Se corrigieron N mediciones del estudio X: COD1, COD2.» («Se
    corrigió 1 medición del estudio X: COD1.»);
  - advertencia por cada omitida: «COD: cambió mientras se editaba.» o «COD: ya tenía ese valor.»;
  - advertencia por cada resultado que no se pudo calcular: «COD: no se pudo calcular el resultado
    (<motivo>).» (US 6.2);
  - `CorregirMedicionesError` → error con su mensaje; `DatabaseError` → «No se pudieron guardar las
    correcciones. Intentá nuevamente.» (nada cambia).

## Servicio

```text
estudios.servicios.corregir_mediciones(estudio_pk, cambios, usuario) -> ResultadoCorreccion
    # cambios = {asignacion_pk: (original: Decimal, nuevo: Decimal)}
    # ResultadoCorreccion(corregidas: list[Medicion], omitidas: list[(Prueba, motivo)],
    #                     sin_calcular: list[(Prueba, motivo)])
    # CorregirMedicionesError: sin sesión, estudio inexistente, informe emitido.

estudios.calculo.afectadas(todas, codigos) -> set[str]   # cambiadas + dependientes
```
