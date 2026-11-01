# Contrato de interfaz: Borrar mediciones

**Feature**: `018-borrar-mediciones` | **Plan**: [plan.md](../plan.md)

Cambios sobre las pantallas de US 6.3 (`specs/017-modificar-mediciones/contracts/corregir-mediciones-ui.md`);
lo que no se menciona no cambia.

## `GET /estudios/<pk>/mediciones/corregir/` (cambio)

- Columna nueva **Borrar** al final de la tabla: `<input type="checkbox" name="borrar_<asignacion_pk>">`
  con su `<label>` accesible («Borrar la medición de COD»).
- El aviso informativo suma: «Para quitar una medición cargada por error, marcá Borrar.».

## `POST` con `accion=revisar` (cambio)

- Una fila con «Borrar» marcado no se valida (ni vacía ni formato) y su texto se ignora.
- El resumen incluye las filas marcadas con «Valor nuevo» = «se borra».
- El aviso cuenta correcciones y borrados juntos: «Se aplicarán N cambios en el estudio X
  (muestra PI Y).» («Se aplicará 1 cambio…» con uno). Si solo hay correcciones, se mantiene el
  texto de US 6.3 («Se corregirá(n) …»).
- «Perderán la validación: …» incluye las afectadas por los borrados.
- Los ocultos reenvían también `borrar_<pk>` de las filas marcadas.

## `POST` con `accion=confirmar` (cambio)

- El formulario se arma con las asignaciones del estudio cuyo `original_<pk>` llegó en el POST,
  tengan o no medición.
- Mensajes, además de los de US 6.3:
  - éxito por borrados: «Se borraron N mediciones del estudio X: COD1, COD2.» («Se borró 1
    medición del estudio X: COD1.»), además del de corregidas si las hubo;
  - advertencia por omitida: «COD: ya no tenía medición.» (además de «cambió mientras se editaba»
    y «ya tenía ese valor»).

## Servicio

```text
estudios.servicios.corregir_mediciones(estudio_pk, cambios, usuario) -> ResultadoCorreccion
    # cambios = {asignacion_pk: (original: Decimal, nuevo: Decimal | None)}; None = borrar
    # ResultadoCorreccion(corregidas, borradas: list[Prueba], omitidas, sin_calcular)
```
