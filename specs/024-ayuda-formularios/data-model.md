# Data Model: Ayuda en formularios

No hay entidades, tablas ni migraciones nuevas. La feature solo agrega textos a los formularios y
cambia el marcado.

## Dónde vive cada texto

| Texto | Fuente | Se muestra |
|---|---|---|
| Ayuda de un campo (significado) | `help_text` del campo del **formulario** (`help_text=` o `Meta.help_texts`) | Tooltip de `ui/campo.html` |
| Requisitos de contraseña | `help_text` que trae Django en `password1` y `password2` | Visible (`ayuda_visible=True`) |
| Instrucción de un campo | Parámetro `instruccion` del `include` | Visible debajo del campo |
| Ayuda de la columna «Medición» y de la firma | Literal en el template | Tooltip con `ui/ayuda.html` |
| Formato de la medición | Literal en el aviso de información del template | Visible |

## Reglas

- **No se cambia `help_text` en los modelos.** En un campo de modelo genera una migración
  (`AlterField`) y se vería también en el admin, que no cambia (FR-013). Los `help_text` de modelo
  que ya existen (`Prueba.formula`, `Usuario.is_active`) solo se ven en el admin y quedan igual.
- Los textos son breves (una o dos oraciones), en español, con los términos del Glosario, y no
  repiten la etiqueta (FR-011).
- Un `help_text` vacío o ausente no dibuja ícono (FR-001).
