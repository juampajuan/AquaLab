"""US 6.6 – US3: lectura de los puntos desde .csv y .xlsx (`pruebas/importacion_curvas.py`)."""

import io
from decimal import Decimal

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from openpyxl import Workbook

from pruebas import importacion_curvas as imp

PUNTOS = [
    (Decimal(c), Decimal(a))
    for c, a in [("0", "0"), ("0.1", "0.052"), ("0.2", "0.101"), ("0.3", "0.153"), ("0.4", "0.199")]
]


def csv(texto, nombre="curva.csv", codificacion="utf-8"):
    return SimpleUploadedFile(nombre, texto.encode(codificacion), content_type="text/csv")


def xlsx(filas, nombre="curva.xlsx", hojas=None):
    libro = Workbook()
    hoja = libro.active
    for fila in filas:
        hoja.append(list(fila))
    for titulo, otras in (hojas or {}).items():
        extra = libro.create_sheet(titulo)
        for fila in otras:
            extra.append(list(fila))
    salida = io.BytesIO()
    libro.save(salida)
    return SimpleUploadedFile(nombre, salida.getvalue())


def leer(archivo, columnas=None):
    """Los puntos como Decimal: así «0» y «0,000» son iguales (lo que importa es el valor)."""
    tabla = imp.leer_archivo(archivo)
    puntos = imp.extraer_puntos(tabla, columnas or imp.detectar_columnas(tabla))
    return [(Decimal(c), Decimal(a)) for c, a in puntos]


# --- Formatos y codificaciones ----------------------------------------------------------------


@pytest.mark.parametrize(
    "texto, codificacion",
    [
        (
            "Concentración;Absorbancia\n0;0,000\n0,1;0,052\n0,2;0,101\n0,3;0,153\n0,4;0,199\n",
            "utf-8",
        ),
        (
            "﻿Concentración;Absorbancia\n0;0,000\n0,1;0,052\n0,2;0,101\n0,3;0,153\n0,4;0,199\n",
            "utf-8",
        ),
        (
            "Concentración;Absorbancia\n0;0,000\n0,1;0,052\n0,2;0,101\n0,3;0,153\n0,4;0,199\n",
            "latin-1",
        ),
        (
            "Concentracion,Absorbancia\n0,0.000\n0.1,0.052\n0.2,0.101\n0.3,0.153\n0.4,0.199\n",
            "utf-8",
        ),
        ("Conc\tAbs\n0\t0.000\n0.1\t0.052\n0.2\t0.101\n0.3\t0.153\n0.4\t0.199\n", "utf-8"),
    ],
    ids=["punto y coma, coma decimal", "con BOM", "latin-1", "coma, punto decimal", "tabulador"],
)
def test_leer_csv(texto, codificacion):
    assert leer(csv(texto, codificacion=codificacion)) == PUNTOS


def test_leer_xlsx():
    filas = [
        ("Concentración", "Absorbancia"),
        (0, 0),
        (0.1, 0.052),
        (0.2, 0.101),
        ("0,3", "0,153"),
        (0.4, 0.199),
    ]
    assert leer(xlsx(filas)) == PUNTOS


def test_leer_xlsx_float_a_decimal():
    """Los números de Excel llegan como float: se pasan a Decimal redondeados a 6 decimales."""
    filas = [("Conc", "Abs"), (0, 0.1 + 0.2), (1, 1 / 3), (2, 0.9)]
    assert leer(xlsx(filas)) == [
        (Decimal("0"), Decimal("0.3")),
        (Decimal("1"), Decimal("0.333333")),
        (Decimal("2"), Decimal("0.9")),
    ]


def test_leer_xlsx_primera_hoja():
    filas = [("Conc", "Abs"), (0, 0), (1, 0.5), (2, 1)]
    otra = [("Conc", "Abs"), (9, 9), (8, 8), (7, 7)]
    assert leer(xlsx(filas, hojas={"Otra": otra})) == [
        (Decimal("0"), Decimal("0")),
        (Decimal("1"), Decimal("0.5")),
        (Decimal("2"), Decimal("1")),
    ]


def test_leer_ignora():
    texto = (
        "Curva de nitritos;\n"
        "Laboratorio AquaLab;Equipo: espectro 1\n"
        "\n"
        "Concentración (mg/l);Absorbancia\n"
        "0;0,000\n"
        ";\n"
        "0,1;0,052\n"
        "Blanco repetido;sin dato\n"
        "0,2;0,101\n"
        "0,3;0,153\n"
        "0,4;0,199\n"
        "Observaciones;ninguna\n"
    )
    assert leer(csv(texto)) == PUNTOS


# --- Columnas ---------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "encabezado, esperado",
    [
        ("Concentración (mg/l);ABS", (0, 1)),
        ("Absorbancia;Concentracion", (1, 0)),
        ("Nro;CONC.;Abs 540 nm", (1, 2)),
    ],
)
def test_detectar_columnas(encabezado, esperado):
    tabla = imp.leer_archivo(csv(f"{encabezado}\n0;0;0\n1;1;1\n"))
    assert imp.detectar_columnas(tabla) == esperado


@pytest.mark.parametrize(
    "texto",
    [
        "0;0,000\n0,1;0,052\n0,2;0,101\n",  # sin encabezados
        "A;B\n0;0,000\n0,1;0,052\n0,2;0,101\n",  # encabezados desconocidos
        "Conc;Abs 1;Abs 2\n0;0;0\n1;1;1\n2;2;2\n",  # dos candidatas
    ],
    ids=["sin encabezados", "desconocidos", "dos candidatas"],
)
def test_detectar_columnas_dudosas(texto):
    assert imp.detectar_columnas(imp.leer_archivo(csv(texto))) is None


def test_elegir_columnas():
    tabla = imp.leer_archivo(csv("A;B;C\n1;0;0,000\n2;0,1;0,052\n3;0,2;0,101\n"))
    assert imp.extraer_puntos(tabla, (1, 2)) == [("0", "0.000"), ("0.1", "0.052"), ("0.2", "0.101")]
    with pytest.raises(imp.ArchivoInvalido) as error:
        imp.extraer_puntos(tabla, (1, 1))
    assert str(error.value) == "Elegí dos columnas distintas."


def test_vista_previa():
    tabla = imp.leer_archivo(csv("A;B\n" + "".join(f"{n};{n}\n" for n in range(10))))
    previa = imp.vista_previa(tabla)
    assert len(previa["filas"]) == 5
    assert previa["columnas"] == [(0, "Columna A"), (1, "Columna B")]


# --- Archivos inválidos: motivo y ningún punto ------------------------------------------------


@pytest.mark.parametrize(
    "archivo, motivo",
    [
        (SimpleUploadedFile("curva.ods", b"x"), "Solo se aceptan archivos .csv o .xlsx."),
        (SimpleUploadedFile("curva.xls", b"x"), "Solo se aceptan archivos .csv o .xlsx."),
        (SimpleUploadedFile("curva.csv", b"0;0\n" * 300_000), "El archivo supera 1 MB."),
        (SimpleUploadedFile("curva.xlsx", b"no es un excel"), "No se pudo leer el archivo."),
        (SimpleUploadedFile("curva.csv", b""), "El archivo está vacío."),
        (csv("\n;\n\n"), "El archivo está vacío."),
        (csv("Conc;Abs\n;\n"), "El archivo trae 0 puntos válidos: hacen falta al menos 3."),
    ],
    ids=["ods", "xls viejo", "grande", "ilegible", "vacío", "sin datos", "solo encabezados"],
)
def test_archivo_ilegible(archivo, motivo):
    with pytest.raises(imp.ArchivoInvalido) as error:
        leer(archivo)
    assert str(error.value) == motivo


@pytest.mark.parametrize(
    "texto, motivo",
    [
        ("Conc;Abs\n0;0\n0,1;0,05\n0,2;\n0,3;0,15\n", "La fila 4 no tiene absorbancia."),
        ("Conc;Abs\n0;0\n;0,05\n0,2;0,1\n", "La fila 3 no tiene concentración."),
        ("Conc;Abs\n0;0\n0,1;n/d\n0,2;0,1\n", "La fila 3 tiene un valor inválido: «n/d»."),
        ("Conc;Abs\n0;0\n0,1;-0,05\n0,2;0,1\n", "La fila 3 tiene un valor inválido: «-0,05»."),
        ("Conc;Abs\n0;0\n0,1;0,05\n", "El archivo trae 2 puntos válidos: hacen falta al menos 3."),
    ],
    ids=["sin absorbancia", "sin concentración", "texto", "negativa", "dos puntos"],
)
def test_archivo_invalido(texto, motivo):
    with pytest.raises(imp.ArchivoInvalido) as error:
        leer(csv(texto))
    assert str(error.value) == motivo


def test_limites():
    filas = "Conc;Abs\n" + "".join(f"{n};{n}\n" for n in range(51))
    with pytest.raises(imp.ArchivoInvalido) as error:
        leer(csv(filas))
    assert str(error.value) == "El archivo trae más de 50 puntos."
    muchas = "Conc;Abs\n" + "texto;texto\n" * 1001
    with pytest.raises(imp.ArchivoInvalido) as error:
        leer(csv(muchas))
    assert str(error.value) == "El archivo tiene más de 1000 filas."


# --- Plantilla --------------------------------------------------------------------------------


def test_plantilla_se_importa():
    contenido = imp.plantilla()
    assert contenido.startswith("﻿Concentración;Absorbancia\r\n")
    assert "0,1;0,052" in contenido
    assert leer(csv(contenido)) == PUNTOS
