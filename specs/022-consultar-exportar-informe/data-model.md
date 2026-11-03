# Data Model: Consultar y exportar informe

**Feature**: `022-consultar-exportar-informe` | **Plan**: [plan.md](./plan.md)

## FirmaProfesional (nuevo, `informes/models.py`)

Firma manuscrita y matrícula de un usuario con «Puede emitir informes» (FR-011 a FR-013).

| Campo | Tipo | Reglas |
|---|---|---|
| `usuario` | `OneToOneField(AUTH_USER_MODEL, CASCADE, related_name="firma_profesional")` | Una por usuario. |
| `imagen` | `BinaryField("imagen")` | Bytes de un PNG; ≤ 64 KB; 1–1200 × 1–400 px (validado por `informes/firmas.py:leer_firma`). |
| `matricula` | `CharField("matrícula", max_length=40)` | Obligatoria; se guarda sin espacios al inicio ni al final. |
| `actualizada` | `DateTimeField(auto_now=True)` | Última vez que se guardó. |

- `Meta`: `verbose_name = "firma profesional"`, `verbose_name_plural = "firmas profesionales"`.
- `data_url` (propiedad): `"data:image/png;base64,<...>"`, lo que se muestra y se copia al informe.
- `CASCADE` es seguro: un usuario con informes emitidos no se puede borrar (`Informe.emitido_por`
  es `PROTECT`), y los informes guardan su propia copia de la firma.
- Migración: `informes/migrations/0003_firmaprofesional.py`.

## Informe (cambios, `informes/models.py`)

Sin campos ni migración nuevos.

- `save()`: si el informe ya existe (`not self._state.adding`) lanza `ValueError("Un informe emitido
  no se puede modificar.")`. `delete()`: lanza siempre (FR-017).
- La clave nueva `"firma"` dentro de `contenido` (abajo).

## `Informe.contenido` — clave nueva `firma`

Se agrega a lo que arma `armar_contenido` (US 7.2) cuando hay firmante con firma:

```json
"firma": {
  "nombre": "Ana Pérez",
  "matricula": "MP 1234",
  "imagen": "data:image/png;base64,iVBORw0KGgo..."
}
```

- `nombre`: `usuario.get_full_name()` o `usuario.email`.
- Ausente en los informes emitidos antes de esta historia → «Sin firma registrada».
- El resto de `contenido` no cambia: `laboratorio`, `cliente`, `muestra`, `estudio`, `pruebas`.

## Formularios (`informes/forms.py`, nuevo)

### BuscarInformeForm

| Campo | Tipo | Reglas |
|---|---|---|
| `q` | `CharField(required=False, max_length=100)` | Se limpia de espacios. |
| `desde` | `DateField(required=False)` | Formato `dd/mm/aaaa` o `aaaa-mm-dd` (input `date`). |
| `hasta` | `DateField(required=False)` | Si están las dos, `desde ≤ hasta`; si no, error «La fecha desde no puede ser posterior a la fecha hasta.» |

### FirmaForm

| Campo | Tipo | Reglas |
|---|---|---|
| `firma` | `CharField(required=False, widget=HiddenInput)` | Obligatorio si el usuario no tiene firma («Dibujá tu firma antes de guardar.»); si viene, `leer_firma` → bytes o error («La firma no es una imagen válida.» / «La firma es demasiado grande.»). |
| `matricula` | `CharField(max_length=40)` | Obligatoria. |

## Estados

Sin cambios: el estudio sigue «Informe generado» (US 7.2). Consultar, exportar o imprimir no cambia
nada (FR-018).
