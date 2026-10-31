---

description: "Lista de tareas de SCRUM-64 – Precargar las pruebas definidas por el científico"
---

# Tasks: Precargar el catálogo de pruebas de agua

**Input**: `specs/014-precargar-catalogo-pruebas/` (`plan.md`, `spec.md`, `research.md`,
`data-model.md`, `contracts/importar-catalogo-pruebas.md`, `contracts/admin-pruebas.md`,
`quickstart.md`)

**Prerequisites**: `plan.md` y `spec.md` commiteados en la rama `014-precargar-catalogo-pruebas`, igual
que `pruebas/datos/catalogo_pruebas_agua.csv` (90 filas) y `pruebas/datos/limites_vertido.csv` (18
filas).

**Tests**: SÍ. La constitution (Principio III) exige al menos un test con pytest-django por cada
escenario de aceptación. Los tests siguen el "Mapa de tests" de `plan.md` y se escriben **antes** de
la implementación de cada historia (deben fallar primero).

**Organization**: tres user stories de la spec: US1 (P1, importar el catálogo), US2 (P2, reimportar
sin duplicar ni romper el historial) y US3 (P3, admin). Se implementan en **dos tandas**:

| Tanda | Fases | Entrega | Cierre |
|---|---|---|---|
| **Tanda 1: datos e importación** | 1, 2, 3 (US1), 4 (US2) | Modelo ampliado, migración y comando `importar_catalogo_pruebas` completo | T026: suite en verde + commit `feat(pruebas): SCRUM-64 – Modelo e importación del catálogo de pruebas` |
| **Tanda 2: admin y cierre** | 5 (US3), 6 (Polish) | Admin de pruebas, nota en `CLAUDE.md` y validación con el quickstart | T036: suite en verde + commit `feat(pruebas): SCRUM-64 – Admin del catálogo de pruebas` |

## Format: `[ID] [P?] [Story] Description`

- **[P]**: se puede ejecutar en paralelo (archivos distintos, sin dependencias pendientes)
- **[Story]**: user story a la que pertenece la tarea (`[US1]`, `[US2]`, `[US3]`)
- Rutas relativas a la raíz del repo

## Convenciones para todas las tareas

- Textos, etiquetas (`verbose_name`) y mensajes en **español** (Principio VI). Los mensajes del comando
  se copian **literalmente** de `contracts/importar-catalogo-pruebas.md`.
- Todo vive en la app `pruebas`. `estudios` **no se modifica**: sigue referenciando `Prueba` con
  `PROTECT` (`TipoEstudioPrueba.prueba`, `PruebaEstudio.prueba`).
- Sin dependencias nuevas: `csv`, `dataclasses`, `re` y `pathlib` de la biblioteca estándar.
- Estilo de `pruebas/models.py` actual: `CheckConstraint(condition=...)`, `strip()` en `save()` y en
  `clean()`, `verbose_name` en minúsculas.
- Comandos dentro de Docker: `docker compose exec web pytest pruebas`,
  `docker compose exec web ruff check .`, `docker compose exec web ruff format --check .`.
- Los tests que necesitan una prueba "en uso" usan las fixtures de `pruebas/tests/conftest.py` (T003);
  las de `estudios/tests/conftest.py` no son visibles desde `pruebas/tests/`.

---

# Tanda 1: datos e importación

## Phase 1: Setup (Shared Infrastructure)

- [X] T001 Verificar el punto de partida en la rama `014-precargar-catalogo-pruebas`: `git ls-files pruebas/datos` lista los dos CSV, y `docker compose exec web pytest` y `docker compose exec web python manage.py makemigrations --check --dry-run` pasan en verde y sin cambios pendientes.
- [X] T002 [P] Crear los paquetes vacíos `pruebas/management/__init__.py` y `pruebas/management/commands/__init__.py`.

---

## Phase 2: Foundational (Blocking Prerequisites)

**⚠️ CRITICAL**: ninguna historia empieza antes de terminar esta fase. Cubre el modelo
([data-model.md](./data-model.md)), que usan las tres historias.

### Tests del modelo (escribir primero, deben fallar)

- [X] T003 [P] Crear `pruebas/tests/conftest.py` con estas fixtures, copiando la forma de `estudios/tests/conftest.py`:
  - `empleado(django_user_model)`: usuario activo `test-pruebas@ejemplo.com`.
  - `muestra(empleado)`: un `Cliente` DNI `30123457`, un `Origen` y una `Muestra` con `numero_pi=200001`.
  - `prueba_en_tipo()`: `Prueba(codigo="USO-T", nombre="Prueba en tipo")` asignada a un `TipoEstudio` nuevo con `tipo.pruebas.set([...])`.
  - `prueba_en_estudio(muestra, empleado)`: `Prueba(codigo="USO-E", nombre="Prueba en estudio")` y un estudio creado con `estudios.servicios.crear_estudio({"clave": str(uuid4()), "muestra": muestra.pk, "tipo": tipo.pk, "version": tipo.version}, empleado)`, que crea su `PruebaEstudio`. Después se vacía el tipo con `TipoEstudioPrueba.objects.filter(tipo=tipo).delete()`, así la prueba queda en uso **solo** por el estudio.
  - `prueba_libre()`: `Prueba(codigo="LIBRE", nombre="Prueba libre")` sin asignaciones.
- [X] T004 [P] Ampliar `pruebas/tests/test_modelo.py`, manteniendo `test_prueba_minima` y `test_validacion`, con:
  - `test_defaults_prueba_nueva` (FR-015): `Prueba.objects.create(codigo="X", nombre="Y")` queda con `tipo_calculo == TipoCalculo.DIRECTO`, `formula == ""`, `es_calculada is False`, `activa is True`, textos en `""` y pasa `full_clean()`.
  - `test_limites_se_guardan_como_texto` (FR-002), parametrizado con `"Ausente"`, `"NE"`, `"SOE"`, `"Ph-0,2"`, `"3.0"` y `" 45 "`: tras `full_clean()` + `save()` + `refresh_from_db()`, `limite_max` es el valor con `strip()` (`"3.0"` sigue siendo `"3.0"`). Lo mismo para `LimiteVertido.limite_max`.
  - `test_formula_segun_tipo_calculo` (FR-003): `DIRECTO` con fórmula y `FORMULA` sin fórmula fallan en `full_clean()`; `FORMULA` con `"x*20"` pasa.
  - `test_constraints_formula_en_base`: `Prueba.objects.create(...)` con `DIRECTO` y fórmula, con `FORMULA` y fórmula vacía, y con `es_calculada=True` y `DIRECTO` lanza `IntegrityError` (cada caso en `transaction.atomic()`).
  - `test_es_calculada_coherente_con_referencias` (R3): `FORMULA` `"{COND}*0.54"` con `es_calculada=False` falla; `"x*20"` con `es_calculada=True` falla; los dos casos coherentes pasan.
  - `test_formula_no_se_referencia_a_si_misma`: `codigo="SDT"` con fórmula `"{SDT}*2"` falla en `full_clean()`.
  - `test_referencias_formula`, parametrizado: `"{NA}/sqrt(({CA}+{MG})/2)"` → `{"NA", "CA", "MG"}`; `"({NTK-T}-{NH4})"` → `{"NTK-T", "NH4"}`; `"({DUREZA-T}-{CA}*2.5)*0.243"` → `{"DUREZA-T", "CA"}`; `"x*20"` → `set()`; `""` → `set()`.
  - `test_limite_vertido_unico_por_tipo` (FR-004): un segundo `LimiteVertido` con la misma prueba y `tipo_vertido` lanza `IntegrityError`; uno `cloacal` y uno `canal` conviven. `tipo_vertido="otro"` falla en `full_clean()`.
  - `test_esta_en_uso_por_tipo_o_estudio` (R6): `prueba_en_tipo.esta_en_uso()` y `prueba_en_estudio.esta_en_uso()` son `True`; `prueba_libre.esta_en_uso()` es `False`.

### Implementación del modelo

- [X] T005 En `pruebas/models.py` agregar:
  - `class TipoCalculo(models.TextChoices)` con `DIRECTO = "DIRECTO", "Directo"` y `FORMULA = "FORMULA", "Fórmula"`.
  - `class TipoVertido(models.TextChoices)` con `CLOACAL = "cloacal", "Cloacal"` y `CANAL = "canal", "Canal"`.
  - `REFERENCIA = re.compile(r"\{([^{}]+)\}")` y `def referencias_formula(formula) -> set[str]`, que devuelve los códigos entre llaves con `strip()`.
- [X] T006 En `pruebas/models.py`, ampliar `Prueba` con estos campos (data-model.md), en este orden después de `nombre`:
  - `unidad = models.CharField("unidad del resultado", max_length=50, blank=True, default="")`
  - `unidad_medicion = models.CharField("unidad de medición", max_length=50, blank=True, default="")`
  - `tipo_calculo = models.CharField("tipo de cálculo", max_length=10, choices=TipoCalculo.choices, default=TipoCalculo.DIRECTO)`
  - `formula = models.CharField("fórmula", max_length=255, blank=True, default="", help_text="x es el valor medido; {CODIGO} es el resultado de otra prueba.")`
  - `es_calculada = models.BooleanField("calculada a partir de otras pruebas", default=False)`
  - `norma = models.CharField("norma", max_length=150, blank=True, default="")`
  - `limite_min`, `limite_max` y `limite_deteccion`: `models.CharField("límite mínimo" / "límite máximo" / "límite de detección", max_length=50, blank=True, default="")`
  - `activa = models.BooleanField("activa", default=True)`
  - `observacion = models.TextField("observación", blank=True, default="")`
- [X] T007 En `Prueba.Meta.constraints` (pruebas/models.py), conservar las dos existentes y agregar:
  - `CheckConstraint(condition=Q(tipo_calculo=TipoCalculo.DIRECTO, formula="") | (Q(tipo_calculo=TipoCalculo.FORMULA) & ~Q(formula="")), name="prueba_formula_segun_tipo")`
  - `CheckConstraint(condition=Q(es_calculada=False) | Q(tipo_calculo=TipoCalculo.FORMULA), name="prueba_calculada_es_formula")`
- [X] T008 En `Prueba` (pruebas/models.py):
  - Reemplazar el `strip()` de `save()` y `clean()` por un helper `_normalizar(self)` que recorte todos los campos de texto (`codigo`, `nombre`, `unidad`, `unidad_medicion`, `formula`, `norma`, `limite_min`, `limite_max`, `limite_deteccion`, `observacion`).
  - En `clean()`, después de normalizar, lanzar `ValidationError` por campo: `{"formula": "Una prueba de tipo Directo no lleva fórmula."}` / `{"formula": "Una prueba de tipo Fórmula necesita una fórmula."}` (mismas condiciones que T007); `{"formula": "La prueba no puede referenciarse a sí misma."}` si `self.codigo in referencias_formula(self.formula)`; `{"es_calculada": "Marcala solo si la fórmula referencia otras pruebas ({CODIGO})."}` si `es_calculada != bool(referencias_formula(self.formula))`.
  - Agregar `def esta_en_uso(self) -> bool`, que devuelve `self.pk is not None and (self.tipoestudioprueba_set.exists() or self.pruebaestudio_set.exists())`.
- [X] T009 En `pruebas/models.py`, crear `LimiteVertido`:
  - Campos: `prueba = models.ForeignKey(Prueba, on_delete=models.CASCADE, related_name="limites_vertido", verbose_name="prueba")`; `tipo_vertido = models.CharField("tipo de vertido", max_length=10, choices=TipoVertido.choices)`; `limite_min` y `limite_max` como `CharField(max_length=50, blank=True, default="")`; `norma = models.CharField("norma", max_length=150, blank=True, default="")`.
  - `Meta`: `verbose_name = "límite por tipo de vertido"`, `verbose_name_plural = "límites por tipo de vertido"`, `ordering = ("prueba__codigo", "tipo_vertido")`, `constraints = [models.UniqueConstraint(fields=("prueba", "tipo_vertido"), name="limite_vertido_unico")]`.
  - `__str__` devuelve `f"{self.prueba.codigo} · {self.get_tipo_vertido_display()}"`, y `save()`/`clean()` aplican `strip()` a los textos.
- [X] T010 Generar `pruebas/migrations/0002_catalogo_pruebas.py` con `docker compose exec web python manage.py makemigrations pruebas --name catalogo_pruebas` y revisar que solo tenga `AddField`, `CreateModel(LimiteVertido)` y `AddConstraint`, sin `RunPython` (depende de T005–T009).
- [X] T011 Correr `docker compose exec web python manage.py migrate` y `docker compose exec web pytest`: T004 en verde y la suite completa en verde **sin tocar** tests de otras apps (FR-015).

**Checkpoint**: modelo listo; las pruebas DEMO y los tests existentes siguen siendo válidos.

---

## Phase 3: User Story 1 - Importar el catálogo real de pruebas (Priority: P1) 🎯 MVP

**Goal**: con un comando, cargar las 90 pruebas y los 18 límites por tipo de vertido de
`pruebas/datos/`.

**Independent Test**: sobre una base sin las pruebas del catálogo, correr
`importar_catalogo_pruebas` y verificar 90 pruebas y 18 límites con los valores de los archivos.

### Tests for User Story 1 ⚠️ (escribir primero, deben fallar)

- [X] T012 [P] [US1] Crear `pruebas/tests/test_importacion.py` (`pytestmark = pytest.mark.django_db`) con:
  - Un helper `escribir_csv(tmp_path, nombre, encabezado, filas)` que escribe un CSV UTF-8 y devuelve la ruta.
  - Constantes `CATALOGO` y `LIMITES` con `settings.BASE_DIR / "pruebas/datos/..."`.
  - Un helper `importar_real()` que llama a `call_command("importar_catalogo_pruebas", stdout=StringIO())` y devuelve el texto.
- [X] T013 [US1] En `pruebas/tests/test_importacion.py`, agregar `test_importa_catalogo_real` (US1 Esc. 1–3, 6, 7; SC-001). Tras `importar_real()`:
  - `Prueba.objects.count() == 90` y `LimiteVertido.objects.count() == 18`.
  - `PH` tiene `nombre "pH"`, `unidad "UpH"`, `unidad_medicion "UpH"`, `DIRECTO`, `formula ""`, `es_calculada False`, `norma "4500• H+ B"`, `limite_min "6.4"`, `limite_max "8.5"`, `limite_deteccion "0.1"` y `activa True`.
  - `TEMPERATURA` tiene `limite_min ""` (límite vacío queda vacío) y `limite_max "45"`.
  - `COLOR` tiene `limite_max "5.0"`.
  - `SDT` tiene `FORMULA`, `formula "{COND}*0.54"` y `es_calculada True`.
  - El límite `CL2-LIB` `cloacal` tiene `limite_max "NE"` y `norma "(AGOSBA) 389/98"`; `CL2-LIB` `canal` tiene `limite_max "0.5"`.
  - Alguna prueba con `limite_max` o `limite_deteccion` en `{"Ausente", "Ausencia", "SOE", "Ph+0,2"}` conserva el texto exacto: compararlo contra la fila leída del CSV con `csv.DictReader`.
- [X] T014 [P] [US1] En `pruebas/tests/test_importacion.py`, agregar:
  - `test_pruebas_sin_tipo_quedan_directo_con_observacion` (US1 Esc. 4, SC-006): 17 pruebas con `observacion` que empieza con `"Sin tipo de cálculo en el sistema original"`, todas `DIRECTO`; `TURBIDEZ` entre ellas.
  - `test_magnesio_con_formula_corregida` (US1 Esc. 5): `MG.formula == "({DUREZA-T}-{CA}*2.5)*0.243"`, `es_calculada True` y `observacion` que menciona `{CA*2.5}`.
  - `test_formulas_se_guardan_sin_evaluar` (US1 Esc. 7): para cada fila `FORMULA` del CSV, la fórmula guardada es igual a la del archivo, y `referencias_formula` de cada una está incluido en los códigos importados.

### Implementación de User Story 1

- [X] T015 [US1] Crear `pruebas/importacion.py` con:
  - `COLUMNAS_CATALOGO = ("codigo", "nombre", "unidad", "unidad_medicion", "tipo_calculo", "formula", "es_calculada", "norma", "limite_min", "limite_max", "limite_deteccion", "activa", "observacion")` y `COLUMNAS_LIMITES = ("codigo", "tipo_vertido", "limite_min", "limite_max", "norma")`.
  - `class ErrorImportacion(Exception)` con el atributo `errores: list[str]`.
  - `@dataclass class Resumen` con `pruebas_creadas`, `pruebas_actualizadas`, `limites_creados`, `limites_actualizados` (int, en 0) y `avisos: list[str]` (`field(default_factory=list)`).
  - `def leer(ruta, columnas, errores) -> list[tuple[int, dict]]`: abre con `open(ruta, encoding="utf-8-sig", newline="")` y lee con `csv.DictReader`. Devuelve `(número de línea, fila con valores strip())`, con la línea de datos inicial en 2 (`reader.line_num`). Si falta alguna columna agrega `f"{ruta.name}: faltan las columnas: {', '.join(faltantes)}."` y si no puede leer el archivo agrega `f"no se puede leer {ruta}."`.
- [X] T016 [US1] En `pruebas/importacion.py`, implementar `def importar(ruta_catalogo, ruta_limites) -> Resumen`. En esta tarea cubre el camino feliz con las dos fases de research R5:
  - **Fase 1 (sin escribir)**: por cada fila del catálogo, buscar la `Prueba` existente por `codigo` (o crear una instancia nueva), asignar los campos convirtiendo `si`/`no` a bool, y llamar a `full_clean(validate_unique=False)`. Por cada fila de límites, armar el `LimiteVertido` (existente por `(prueba, tipo_vertido)` o nuevo) y llamar a `full_clean(exclude=["prueba"], validate_unique=False)`.
  - **Fase 2**: si `errores` no está vacío, `raise ErrorImportacion(errores)`. Si no, dentro de `transaction.atomic()` guardar las pruebas, resolver `limite.prueba` por código y guardar los límites, contando creadas y actualizadas según `pk is None` antes de guardar.
- [X] T017 [US1] Crear `pruebas/management/commands/importar_catalogo_pruebas.py`:
  - `help = "Importa el catálogo de pruebas de agua y sus límites por tipo de vertido."`
  - Opciones `--catalogo` y `--limites` (`type=Path`), con defaults `settings.BASE_DIR / "pruebas" / "datos" / "catalogo_pruebas_agua.csv"` y `... / "limites_vertido.csv"`.
  - Llama a `importar`. Si termina bien, escribe con `self.style.SUCCESS` la línea literal del contrato: `Catálogo importado: {n} pruebas ({c} creadas, {a} actualizadas) y {m} límites por tipo de vertido ({c} creados, {a} actualizados).`; después escribe cada aviso con `self.style.WARNING`.
  - `ErrorImportacion` se convierte en `CommandError("No se importó nada: el archivo tiene {N} errores.\n" + "\n".join(errores))`, con singular `1 error` cuando corresponde.
- [X] T018 [US1] Correr `docker compose exec web pytest pruebas/tests/test_importacion.py` y dejar T013–T014 en verde.

**Checkpoint**: MVP. El catálogo real se carga con un comando.

---

## Phase 4: User Story 2 - Volver a importar sin duplicar ni romper el historial (Priority: P2)

**Goal**: la importación es repetible, actualiza por código, protege las pruebas en uso y rechaza
completo un archivo con errores.

**Independent Test**: importar tres veces y verificar que no hay duplicados; con una prueba en uso,
cambiar su nombre en una copia del CSV y verificar el aviso; con un CSV inválido, verificar que la base
no cambia.

### Tests for User Story 2 ⚠️ (escribir primero, deben fallar)

- [X] T019 [P] [US2] En `pruebas/tests/test_importacion.py`, agregar:
  - `test_reimportar_no_duplica` (US2 Esc. 1, FR-007, SC-002): tres `importar_real()` seguidas dejan 90 y 18. La segunda y la tercera informan `(0 creadas, 90 actualizadas)` y `(0 creados, 18 actualizados)`. `Prueba.objects.values()` es igual después de la primera y de la tercera.
  - `test_reimportar_actualiza_por_codigo` (US2 Esc. 2, FR-006): importar un CSV con `PH` y `limite_max "8.5"` y otro límite. Reimportar con `limite_max "9"`, otra norma y otro `limite_max` de vertido. Queda el mismo `pk`, los valores nuevos y ninguna fila de más.
- [X] T020 [P] [US2] En `pruebas/tests/test_importacion.py`, agregar:
  - `test_prueba_en_uso_conserva_nombre_y_asignaciones` (US2 Esc. 3–4, FR-008/008a, SC-003), parametrizado con las fixtures `prueba_en_tipo` y `prueba_en_estudio` (`request.getfixturevalue`). Se importa un CSV con el mismo código, `nombre "Nombre nuevo"` y `unidad "mg/l"`. Resultado: el nombre no cambia, `unidad == "mg/l"`, las asignaciones (`TipoEstudioPrueba` / `PruebaEstudio`) siguen iguales y la salida contiene `Aviso: la prueba {codigo} está en uso; se conserva el nombre «{viejo}» (el archivo dice «Nombre nuevo»).`
  - `test_prueba_libre_actualiza_nombre`: con `prueba_libre`, el nombre del archivo se aplica y no hay aviso.
  - `test_pruebas_fuera_del_archivo_no_se_tocan` (US2 Esc. 5, FR-008): `prueba_libre`, `prueba_en_tipo` y un `LimiteVertido` de `prueba_libre` siguen existiendo con los mismos valores (incluido `activa True`) después de `importar_real()`.
- [X] T021 [P] [US2] En `pruebas/tests/test_importacion.py`, agregar `test_archivo_invalido_no_cambia_nada` (US2 Esc. 6, FR-009/010, SC-004):
  - Primero `importar_real()` y se toma una foto: `list(Prueba.objects.values())` y `list(LimiteVertido.objects.values())`.
  - Después, parametrizado por caso, un `call_command` con CSV de `tmp_path` lanza `CommandError` cuyo texto contiene `No se importó nada` y el fragmento esperado. La foto queda igual.
  - Casos (archivo afectado → fragmento esperado):
    - catálogo sin `formula` → `faltan las columnas: formula`
    - código repetido en las líneas 2 y 3 → `línea 3: el código «PH» está repetido (también en la línea 2)`
    - `tipo_calculo "CURVA"` → `línea 2: tipo de cálculo «CURVA» inválido (DIRECTO o FORMULA)`
    - `activa "quizas"` → `activa: «quizas» inválido (si o no)`
    - `FORMULA` con fórmula vacía → `Una prueba de tipo Fórmula necesita una fórmula.`
    - fórmula `"{NOEXISTE}*2"` con `es_calculada si` → `la fórmula referencia «NOEXISTE», que no existe en el catálogo`
    - nombre de 151 caracteres → `línea 2:`
    - límites con `tipo_vertido "rio"` → `tipo de vertido «rio» inválido (cloacal o canal)`
    - límites de `"XX"` → `la prueba «XX» no existe en el catálogo`
    - límite repetido `PH`/`canal` → `límite repetido para «PH» (canal)`
    - ruta inexistente → `no se puede leer`
- [X] T022 [P] [US2] En `pruebas/tests/test_importacion.py`, agregar:
  - `test_reporta_todos_los_errores`: un catálogo con dos filas inválidas informa `el archivo tiene 2 errores` y ambas líneas.
  - `test_normaliza_espacios_y_acepta_bom`: CSV escrito con `encoding="utf-8-sig"` y valores `" PH "`, `" pH "`, `" SI "`. Se importa `PH` con `nombre "pH"` y `activa True`.
  - `test_referencia_valida_en_archivo_o_base`: `A` con fórmula `"{B}*2"` en la línea 2 y `B` en la línea 3 se importan juntas. Después, un CSV solo con `C` = `"{B}+1"` también se importa, porque `B` ya está en la base.
  - `test_error_de_base_revierte_todo` (FR-009): con `mock.patch.object(LimiteVertido, "save", side_effect=DatabaseError("falla"))`, `importar_real()` lanza `DatabaseError` y `Prueba.objects.filter(codigo="PH").exists()` es `False`.
  - `test_comando_informa_resumen_y_avisos` (US2 Esc. 7, FR-011): la primera salida contiene la línea literal `Catálogo importado: 90 pruebas (90 creadas, 0 actualizadas) y 18 límites por tipo de vertido (18 creados, 0 actualizados).`

### Implementación de User Story 2

- [X] T023 [US2] En la fase 1 de `pruebas/importacion.py`, agregar estas validaciones, juntando **todos** los errores con el formato `f"{ruta.name}, línea {n}: {motivo}."` y los motivos literales de la tabla de `contracts/importar-catalogo-pruebas.md`:
  - si/no con `valor.lower() in {"si", "no"}`;
  - `tipo_calculo in TipoCalculo.values` y `tipo_vertido in TipoVertido.values`, validados antes de `full_clean`;
  - códigos repetidos (catálogo) y `(codigo, tipo_vertido)` repetidos (límites);
  - mensajes de `full_clean` aplanados con `"; ".join(e.messages)`;
  - referencias y códigos de límites contra `códigos del archivo ∪ set(Prueba.objects.values_list("codigo", flat=True))`.
- [X] T024 [US2] En `pruebas/importacion.py`, proteger las pruebas en uso (R6):
  - Calcular `en_uso = set(TipoEstudioPrueba.objects.values_list("prueba_id", flat=True)) | set(PruebaEstudio.objects.values_list("prueba_id", flat=True))`.
  - Si una prueba existente está en `en_uso` y el nombre del archivo es distinto, conservar el nombre guardado y agregar a `Resumen.avisos` el texto literal `Aviso: la prueba {codigo} está en uso; se conserva el nombre «{guardado}» (el archivo dice «{archivo}»).`
  - Confirmar que el código nunca llama a `delete()` ni toca `activa` de pruebas fuera del archivo.
- [X] T025 [US2] Correr `docker compose exec web pytest pruebas` y dejar T019–T022 en verde junto con lo anterior.
- [X] T026 **Cierre de la tanda 1**:
  - `docker compose exec web pytest`, `docker compose exec web ruff check .` y `docker compose exec web ruff format --check .` en verde.
  - Pasos 1 y 2 de `quickstart.md` ejecutados a mano contra la base de desarrollo.
  - Commit `feat(pruebas): SCRUM-64 – Modelo e importación del catálogo de pruebas` con `pruebas/` y `specs/014-precargar-catalogo-pruebas/tasks.md`, marcando T001–T026 como `[X]`.

**Checkpoint**: la importación es completa y segura. La tanda 2 puede hacerse en otra sesión.

---

# Tanda 2: admin y cierre

## Phase 5: User Story 3 - Consultar y mantener las pruebas en el admin (Priority: P3)

**Goal**: ver, buscar, filtrar y agregar pruebas en `/admin/pruebas/prueba/`, con código y nombre de
solo lectura en las pruebas en uso.

**Independent Test**: con `admin_client`, buscar una prueba, abrir su detalle con los límites,
agregar una nueva y verificar que una prueba en uso no deja cambiar código ni nombre ni eliminarla.

### Tests for User Story 3 ⚠️ (escribir primero, deben fallar)

- [X] T027 [P] [US3] Crear `pruebas/tests/test_admin.py` (`pytestmark = pytest.mark.django_db`) con las URLs `reverse("admin:pruebas_prueba_changelist")`, `..._add` y `..._change`, y estos tests:
  - `test_admin_listado_busqueda_y_filtros` (US3 Esc. 1–3, FR-012): crea `PH`/`pH` DIRECTO, `SDT`/`Sólidos disueltos` FORMULA y `TURB`/`Turbidez` con observación. La respuesta del listado contiene las columnas `Código`, `Nombre`, `Unidad del resultado`, `Tipo de cálculo` y `Activa`. `?q=sól` devuelve solo SDT; `?q=ph` devuelve solo PH; `?tipo_calculo__exact=FORMULA` devuelve solo SDT; `?activa__exact=0` devuelve 0 resultados; `?observacion=con` devuelve solo TURB y `?observacion=sin` las otras dos. Se compara con `response.context["cl"].result_list`.
  - `test_admin_detalle_muestra_limites` (US3 Esc. 4): una prueba con límites `cloacal` y `canal` muestra ambos en el formulario inline (`limites_vertido-TOTAL_FORMS` = 2 y los valores en el HTML).
- [X] T028 [P] [US3] En `pruebas/tests/test_admin.py`, agregar:
  - `test_admin_alta_prueba` (US3 Esc. 5): POST a add con `codigo "NUEVA"`, `nombre "Prueba nueva"`, `tipo_calculo "FORMULA"`, `formula "x*2"`, `activa "on"` y el management form del inline vacío. Resultado: 302 y la prueba existe.
  - `test_admin_alta_rechaza_invalidas` (FR-014), parametrizado: código existente, código vacío, nombre vacío, `DIRECTO` con fórmula, fórmula `"{NOEXISTE}*2"` con `es_calculada "on"` (el error contiene `«NOEXISTE»`) y dos límites `canal`. En todos: 200 con errores en `response.context["adminform"]` o en los inline formsets, y ninguna prueba nueva.
- [X] T029 [P] [US3] En `pruebas/tests/test_admin.py`, agregar:
  - `test_admin_prueba_en_uso_codigo_nombre_solo_lectura` (US3 Esc. 6, FR-013), parametrizado con `prueba_en_tipo` y `prueba_en_estudio`. El GET del change no tiene `name="codigo"` ni `name="nombre"` pero muestra sus valores. Un POST que manda `codigo "OTRO"`, `nombre "Otro"` y `unidad "mg/l"` guarda la unidad y deja código y nombre igual.
  - `test_admin_prueba_libre_editable` (US3 Esc. 7): con `prueba_libre`, el GET tiene `name="codigo"` y `name="nombre"`, y el POST cambia ambos.
  - `test_admin_no_elimina_prueba_en_uso` (US3 Esc. 8): para la prueba en uso, el change no muestra el enlace de borrar y el GET a `admin:pruebas_prueba_delete` responde 403. La acción `delete_selected` con su pk, confirmada con `post="yes"`, no la borra. `prueba_libre` sí se borra desde su delete, junto con sus `LimiteVertido`.
  - `test_admin_requiere_staff_y_permiso` (US3 Esc. 9): un usuario activo sin `is_staff` es redirigido al login; un `is_staff` sin permisos recibe 403 en el changelist; con `pruebas.view_prueba` ve el listado pero recibe 403 en add.

### Implementación de User Story 3

- [X] T030 [US3] Crear `pruebas/admin.py` con `PruebaAdminForm(forms.ModelForm)` (`model = Prueba`, `fields = "__all__"`). Su `clean()` llama a `super().clean()` y, si existe `formula`, valida que cada código de `referencias_formula(formula)` (sin el propio) exista con `Prueba.objects.filter(codigo__in=...)`. Si falta alguno, `self.add_error("formula", f"La fórmula referencia «{codigo}», que no existe en el catálogo.")`.
- [X] T031 [US3] En `pruebas/admin.py`, crear `ConObservacionFilter(admin.SimpleListFilter)`: `title = "observación"`, `parameter_name = "observacion"`, opciones `("con", "Con observación")` y `("sin", "Sin observación")`. Filtra con `~Q(observacion="")` o `Q(observacion="")`.
- [X] T032 [US3] En `pruebas/admin.py`, crear `LimiteVertidoInline(admin.TabularInline)` con `model = LimiteVertido`, `extra = 0`, `max_num = len(TipoVertido)`, `fields = ("tipo_vertido", "limite_min", "limite_max", "norma")` y `verbose_name_plural = "límites por tipo de vertido"`.
- [X] T033 [US3] En `pruebas/admin.py`, registrar `@admin.register(Prueba) class PruebaAdmin(admin.ModelAdmin)` según `contracts/admin-pruebas.md`:
  - `form = PruebaAdminForm`, `inlines = [LimiteVertidoInline]`.
  - `list_display = ("codigo", "nombre", "unidad", "tipo_calculo", "activa")`, `search_fields = ("codigo", "nombre")`, `list_filter = ("tipo_calculo", "activa", "es_calculada", ConObservacionFilter)`.
  - `fieldsets`: `("Identificación", codigo, nombre, activa)`, `("Cálculo", tipo_calculo, formula, es_calculada, unidad_medicion, unidad)`, `("Límites", norma, limite_min, limite_max, limite_deteccion)` y `("Observación", observacion)`.
  - `get_readonly_fields(request, obj=None)` agrega `("codigo", "nombre")` si `obj is not None and obj.esta_en_uso()`.
  - `has_delete_permission(request, obj=None)` devuelve `False` si `obj is not None and obj.esta_en_uso()`; si no, `super()`.
- [X] T034 [US3] Correr `docker compose exec web pytest pruebas/tests/test_admin.py` y dejar T027–T029 en verde. Si la acción masiva sobre una prueba en uso no muestra los objetos protegidos de `PROTECT`, ajustar el test al comportamiento real de Django 5.2 (la página "no se puede borrar") sin agregar código propio.

---

## Phase 6: Polish & Cross-Cutting Concerns

- [X] T035 [P] Agregar a `CLAUDE.md` una sección `## Catálogo de pruebas (SCRUM-64)` con 4–6 viñetas:
  - el comando `importar_catalogo_pruebas` y sus CSV en `pruebas/datos/`;
  - es todo o nada, actualiza por código y nunca borra ni desactiva;
  - conserva el nombre de una prueba en uso y avisa;
  - límites y fórmulas son texto sin evaluar (`x` = medido, `{CODIGO}` = otra prueba) y `referencias_formula` es la única forma de leer las referencias;
  - `Prueba.esta_en_uso()` es la regla de uso para el admin y la importación;
  - **Epic 6:** convertir los límites a número y evaluar fórmulas; las 17 pruebas DIRECTO asumidas siguen a confirmar con el laboratorio.
- [ ] T036 **Cierre de la tanda 2**:
  - `docker compose exec web pytest`, `docker compose exec web ruff check .`, `docker compose exec web ruff format --check .` y `docker compose exec web python manage.py makemigrations --check --dry-run` en verde.
  - Paso 3 de `quickstart.md` ejecutado en el navegador con un superusuario. **Pendiente (2026-10-31)**: lo valida el usuario en el navegador; el resto del cierre (suite, ruff, `makemigrations --check` y commit) ya está hecho.
  - Commit `feat(pruebas): SCRUM-64 – Admin del catálogo de pruebas` con `pruebas/admin.py`, `pruebas/tests/test_admin.py`, `CLAUDE.md` y `tasks.md`, marcando T027–T036 como `[X]`.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Fase 1)** → **Foundational (Fase 2)** → bloquea todas las historias.
- **US1 (Fase 3)** depende de la Fase 2.
- **US2 (Fase 4)** depende de US1: amplía `pruebas/importacion.py` y el mismo archivo de tests.
- **US3 (Fase 5)** depende solo de la Fase 2. Podría hacerse en paralelo con US1/US2, pero por las dos
  tandas acordadas va después de T026.
- **Polish (Fase 6)** va al final.

### Dentro de cada fase

- Tests primero (deben fallar), después la implementación y por último la corrida en verde.
- T005 → T006 → T007 → T008 → T009 (mismo archivo) → T010 → T011.
- T015 → T016 → T017; T023 y T024 modifican `importacion.py` en serie.
- T030 → T031 → T032 → T033 (mismo archivo).

### Parallel Opportunities

- T002, T003 y T004 (archivos distintos).
- T012 y T014 se escriben juntas con T013 en el mismo archivo; si se reparten entre personas, conviene
  que una sola persona edite `test_importacion.py`.
- T019–T022 son el mismo archivo: [P] respecto de la implementación (T023–T024), no entre sí si las
  edita la misma persona.
- T027–T029 (`test_admin.py`) en paralelo con T035 (`CLAUDE.md`).

## Parallel Example: Foundational

```text
Tarea: "T003 Crear pruebas/tests/conftest.py con fixtures de pruebas en uso"
Tarea: "T004 Ampliar pruebas/tests/test_modelo.py con tests del modelo"
Tarea: "T002 Crear paquetes pruebas/management/"
```

## Parallel Example: User Story 3

```text
Tarea: "T027–T029 Tests del admin en pruebas/tests/test_admin.py"
Tarea: "T035 Nota en CLAUDE.md"
```

## Implementation Strategy

### MVP (Tanda 1, hasta T018)

1. Fases 1 y 2: modelo y migración.
2. Fase 3 (US1): el comando carga el catálogo real.
3. **Validar**: `importar_catalogo_pruebas` sobre una base limpia → 90/18.

### Entrega incremental

1. **Tanda 1** (T001–T026): modelo + importación completa (US1 + US2) → commit 1.
2. **Tanda 2** (T027–T036): admin (US3) + `CLAUDE.md` + quickstart → commit 2 → PR «SCRUM-64 –
   Precargar las pruebas definidas por el científico».
