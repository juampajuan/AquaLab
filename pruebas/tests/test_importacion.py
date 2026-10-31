import csv
from io import StringIO
from unittest import mock

import pytest
from django.conf import settings
from django.core.management import CommandError, call_command
from django.db import DatabaseError

from pruebas.importacion import COLUMNAS_CATALOGO, COLUMNAS_LIMITES
from pruebas.models import LimiteVertido, Prueba, TipoCalculo, referencias_formula

pytestmark = pytest.mark.django_db

DATOS = settings.BASE_DIR / "pruebas" / "datos"
CATALOGO = DATOS / "catalogo_pruebas_agua.csv"
LIMITES = DATOS / "limites_vertido.csv"


def escribir_csv(tmp_path, nombre, encabezado, filas, encoding="utf-8"):
    ruta = tmp_path / nombre
    with open(ruta, "w", encoding=encoding, newline="") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=encabezado)
        escritor.writeheader()
        escritor.writerows(filas)
    return ruta


def fila_prueba(**cambios):
    fila = dict.fromkeys(COLUMNAS_CATALOGO, "")
    fila.update(
        codigo="PH",
        nombre="pH",
        tipo_calculo="DIRECTO",
        es_calculada="no",
        activa="si",
        limite_max="8.5",
    )
    fila.update(cambios)
    return fila


def fila_limite(**cambios):
    fila = dict.fromkeys(COLUMNAS_LIMITES, "")
    fila.update(codigo="PH", tipo_vertido="canal", limite_max="9")
    fila.update(cambios)
    return fila


def importar(catalogo, limites):
    salida = StringIO()
    call_command("importar_catalogo_pruebas", catalogo=catalogo, limites=limites, stdout=salida)
    return salida.getvalue()


def importar_filas(tmp_path, pruebas, limites=()):
    catalogo = escribir_csv(tmp_path, "catalogo.csv", COLUMNAS_CATALOGO, pruebas)
    vertidos = escribir_csv(tmp_path, "limites.csv", COLUMNAS_LIMITES, limites)
    return importar(catalogo, vertidos)


def importar_real():
    return importar(CATALOGO, LIMITES)


def filas_csv(ruta):
    with open(ruta, encoding="utf-8", newline="") as archivo:
        return list(csv.DictReader(archivo))


# User Story 1: importar el catálogo real


def test_importa_catalogo_real():
    importar_real()
    assert Prueba.objects.count() == 90
    assert LimiteVertido.objects.count() == 18

    ph = Prueba.objects.get(codigo="PH")
    assert (ph.nombre, ph.unidad, ph.unidad_medicion) == ("pH", "UpH", "UpH")
    assert (ph.tipo_calculo, ph.formula, ph.es_calculada) == (TipoCalculo.DIRECTO, "", False)
    assert ph.norma == "4500• H+ B"
    assert (ph.limite_min, ph.limite_max, ph.limite_deteccion) == ("6.4", "8.5", "0.1")
    assert ph.activa

    temperatura = Prueba.objects.get(codigo="TEMPERATURA")
    assert (temperatura.limite_min, temperatura.limite_max) == ("", "45")
    assert Prueba.objects.get(codigo="COLOR").limite_max == "5.0"

    sdt = Prueba.objects.get(codigo="SDT")
    assert (sdt.tipo_calculo, sdt.formula, sdt.es_calculada) == (
        TipoCalculo.FORMULA,
        "{COND}*0.54",
        True,
    )

    cloacal = LimiteVertido.objects.get(prueba__codigo="CL2-LIB", tipo_vertido="cloacal")
    assert (cloacal.limite_max, cloacal.norma) == ("NE", "(AGOSBA) 389/98")
    canal = LimiteVertido.objects.get(prueba__codigo="CL2-LIB", tipo_vertido="canal")
    assert canal.limite_max == "0.5"

    no_numericos = {"Ausente", "Ausencia", "SOE", "Ph+0,2"}
    filas = [
        fila
        for fila in filas_csv(CATALOGO)
        if {fila["limite_max"], fila["limite_deteccion"]} & no_numericos
    ]
    assert filas
    for fila in filas:
        prueba = Prueba.objects.get(codigo=fila["codigo"])
        assert (prueba.limite_min, prueba.limite_max, prueba.limite_deteccion) == (
            fila["limite_min"],
            fila["limite_max"],
            fila["limite_deteccion"],
        )


def test_pruebas_sin_tipo_quedan_directo_con_observacion():
    importar_real()
    asumidas = Prueba.objects.filter(
        observacion__startswith="Sin tipo de cálculo en el sistema original"
    )
    assert asumidas.count() == 17
    assert set(asumidas.values_list("tipo_calculo", flat=True)) == {TipoCalculo.DIRECTO}
    assert asumidas.filter(codigo="TURBIDEZ").exists()


def test_magnesio_con_formula_corregida():
    importar_real()
    magnesio = Prueba.objects.get(codigo="MG")
    assert magnesio.formula == "({DUREZA-T}-{CA}*2.5)*0.243"
    assert magnesio.es_calculada
    assert "{CA*2.5}" in magnesio.observacion


def test_formulas_se_guardan_sin_evaluar():
    importar_real()
    codigos = set(Prueba.objects.values_list("codigo", flat=True))
    formulas = [fila for fila in filas_csv(CATALOGO) if fila["tipo_calculo"] == "FORMULA"]
    assert len(formulas) == 25
    for fila in formulas:
        assert Prueba.objects.get(codigo=fila["codigo"]).formula == fila["formula"]
        assert referencias_formula(fila["formula"]) <= codigos


# User Story 2: volver a importar sin duplicar ni romper el historial


def test_reimportar_no_duplica():
    importar_real()
    primera = list(Prueba.objects.values())
    for _ in range(2):
        salida = importar_real()
        assert "(0 creadas, 90 actualizadas)" in salida
        assert "(0 creados, 18 actualizados)" in salida
    assert Prueba.objects.count() == 90
    assert LimiteVertido.objects.count() == 18
    assert list(Prueba.objects.values()) == primera


def test_reimportar_actualiza_por_codigo(tmp_path):
    importar_filas(tmp_path, [fila_prueba()], [fila_limite()])
    pk = Prueba.objects.get(codigo="PH").pk
    pk_limite = LimiteVertido.objects.get().pk

    salida = importar_filas(
        tmp_path,
        [fila_prueba(limite_max="9", norma="SM 4500")],
        [fila_limite(limite_max="9.5")],
    )

    assert "(0 creadas, 1 actualizadas)" in salida
    prueba = Prueba.objects.get()
    assert (prueba.pk, prueba.limite_max, prueba.norma) == (pk, "9", "SM 4500")
    limite = LimiteVertido.objects.get()
    assert (limite.pk, limite.limite_max) == (pk_limite, "9.5")


def asignaciones(prueba):
    return (
        list(prueba.tipoestudioprueba_set.values_list("pk", "tipo_id")),
        list(prueba.pruebaestudio_set.values_list("pk", "estudio_id", "estado")),
    )


@pytest.mark.parametrize("fixture", ["prueba_en_tipo", "prueba_en_estudio"])
def test_prueba_en_uso_conserva_nombre_y_asignaciones(request, tmp_path, fixture):
    prueba = request.getfixturevalue(fixture)
    antes = asignaciones(prueba)

    salida = importar_filas(
        tmp_path, [fila_prueba(codigo=prueba.codigo, nombre="Nombre nuevo", unidad="mg/l")]
    )

    actual = Prueba.objects.get(pk=prueba.pk)
    assert (actual.nombre, actual.unidad) == (prueba.nombre, "mg/l")
    assert asignaciones(actual) == antes
    assert (
        f"Aviso: la prueba {prueba.codigo} está en uso; se conserva el nombre "
        f"«{prueba.nombre}» (el archivo dice «Nombre nuevo»)."
    ) in salida


def test_prueba_libre_actualiza_nombre(tmp_path, prueba_libre):
    salida = importar_filas(tmp_path, [fila_prueba(codigo="LIBRE", nombre="Nombre nuevo")])
    assert Prueba.objects.get(pk=prueba_libre.pk).nombre == "Nombre nuevo"
    assert "Aviso" not in salida


def test_pruebas_fuera_del_archivo_no_se_tocan(prueba_libre, prueba_en_tipo):
    LimiteVertido.objects.create(prueba=prueba_libre, tipo_vertido="canal", limite_max="1")
    antes = list(Prueba.objects.filter(codigo__in=["LIBRE", "USO-T"]).values())
    limites_antes = list(LimiteVertido.objects.values())

    importar_real()

    assert list(Prueba.objects.filter(codigo__in=["LIBRE", "USO-T"]).values()) == antes
    assert all(p["activa"] for p in antes)
    assert LimiteVertido.objects.filter(prueba=prueba_libre).count() == 1
    assert limites_antes[0] in list(LimiteVertido.objects.values())


SIN_FORMULA = tuple(c for c in COLUMNAS_CATALOGO if c != "formula")


def caso_columna_faltante(tmp_path):
    fila = {c: v for c, v in fila_prueba().items() if c != "formula"}
    return (
        escribir_csv(tmp_path, "catalogo.csv", SIN_FORMULA, [fila]),
        escribir_csv(tmp_path, "limites.csv", COLUMNAS_LIMITES, []),
    )


def caso(pruebas, limites=()):
    def armar(tmp_path):
        return (
            escribir_csv(tmp_path, "catalogo.csv", COLUMNAS_CATALOGO, pruebas),
            escribir_csv(tmp_path, "limites.csv", COLUMNAS_LIMITES, limites),
        )

    return armar


def caso_ruta_inexistente(tmp_path):
    return tmp_path / "no-existe.csv", escribir_csv(tmp_path, "limites.csv", COLUMNAS_LIMITES, [])


CASOS_INVALIDOS = {
    "columna faltante": (caso_columna_faltante, "faltan las columnas: formula"),
    "código repetido": (
        caso([fila_prueba(), fila_prueba(nombre="Otro pH")]),
        "línea 3: el código «PH» está repetido (también en la línea 2)",
    ),
    "tipo de cálculo": (
        caso([fila_prueba(tipo_calculo="CURVA")]),
        "línea 2: tipo de cálculo «CURVA» inválido (DIRECTO o FORMULA)",
    ),
    "si/no": (caso([fila_prueba(activa="quizas")]), "activa: «quizas» inválido (si o no)"),
    "fórmula vacía": (
        caso([fila_prueba(tipo_calculo="FORMULA")]),
        "Una prueba de tipo Fórmula necesita una fórmula.",
    ),
    "referencia inexistente": (
        caso([fila_prueba(tipo_calculo="FORMULA", formula="{NOEXISTE}*2", es_calculada="si")]),
        "la fórmula referencia «NOEXISTE», que no existe en el catálogo",
    ),
    "nombre largo": (caso([fila_prueba(nombre="x" * 151)]), "línea 2:"),
    "tipo de vertido": (
        caso([fila_prueba()], [fila_limite(tipo_vertido="rio")]),
        "tipo de vertido «rio» inválido (cloacal o canal)",
    ),
    "límite de código inexistente": (
        caso([fila_prueba()], [fila_limite(codigo="XX")]),
        "la prueba «XX» no existe en el catálogo",
    ),
    "límite repetido": (
        caso([fila_prueba()], [fila_limite(), fila_limite(limite_max="1")]),
        "límite repetido para «PH» (canal)",
    ),
    "ruta inexistente": (caso_ruta_inexistente, "no se puede leer"),
}


@pytest.mark.parametrize("nombre", CASOS_INVALIDOS)
def test_archivo_invalido_no_cambia_nada(tmp_path, nombre):
    importar_real()
    pruebas_antes = list(Prueba.objects.values())
    limites_antes = list(LimiteVertido.objects.values())
    armar, fragmento = CASOS_INVALIDOS[nombre]

    with pytest.raises(CommandError) as error:
        importar(*armar(tmp_path))

    assert "No se importó nada" in str(error.value)
    assert fragmento in str(error.value)
    assert list(Prueba.objects.values()) == pruebas_antes
    assert list(LimiteVertido.objects.values()) == limites_antes


def test_reporta_todos_los_errores(tmp_path):
    with pytest.raises(CommandError) as error:
        importar_filas(
            tmp_path,
            [fila_prueba(tipo_calculo="CURVA"), fila_prueba(codigo="OD", activa="tal vez")],
        )
    mensaje = str(error.value)
    assert "el archivo tiene 2 errores" in mensaje
    assert "línea 2:" in mensaje and "línea 3:" in mensaje
    assert not Prueba.objects.exists()


def test_normaliza_espacios_y_acepta_bom(tmp_path):
    catalogo = escribir_csv(
        tmp_path,
        "catalogo.csv",
        COLUMNAS_CATALOGO,
        [fila_prueba(codigo=" PH ", nombre=" pH ", activa=" SI ")],
        encoding="utf-8-sig",
    )
    importar(catalogo, escribir_csv(tmp_path, "limites.csv", COLUMNAS_LIMITES, []))
    prueba = Prueba.objects.get()
    assert (prueba.codigo, prueba.nombre, prueba.activa) == ("PH", "pH", True)


def test_referencia_valida_en_archivo_o_base(tmp_path):
    formula = {"tipo_calculo": "FORMULA", "es_calculada": "si"}
    importar_filas(
        tmp_path,
        [fila_prueba(codigo="A", formula="{B}*2", **formula), fila_prueba(codigo="B")],
    )
    importar_filas(tmp_path, [fila_prueba(codigo="C", formula="{B}+1", **formula)])
    assert set(Prueba.objects.values_list("codigo", flat=True)) == {"A", "B", "C"}


def test_error_de_base_revierte_todo():
    with (
        mock.patch.object(LimiteVertido, "save", side_effect=DatabaseError("falla")),
        pytest.raises(DatabaseError),
    ):
        importar_real()
    assert not Prueba.objects.filter(codigo="PH").exists()


def test_comando_informa_resumen_y_avisos():
    assert (
        "Catálogo importado: 90 pruebas (90 creadas, 0 actualizadas) y 18 límites por tipo de "
        "vertido (18 creados, 0 actualizados)."
    ) in importar_real()


def test_comando_error_sale_con_command_error(tmp_path):
    with pytest.raises(CommandError) as error:
        importar_filas(tmp_path, [fila_prueba(tipo_calculo="CURVA")])
    assert str(error.value).startswith("No se importó nada: el archivo tiene 1 error.\n")
