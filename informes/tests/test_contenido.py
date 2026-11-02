from datetime import date

import pytest
from django.conf import settings

from estudios.tests.utiles import cargar, validar
from informes.contenido import armar_contenido
from pruebas.models import Prueba

pytestmark = pytest.mark.django_db


@pytest.fixture
def estudio_validado(estudio_de, empleado, bioquimico, muestra):
    muestra.fecha_muestreo = date(2026, 10, 21)
    muestra.fecha_ingreso = date(2026, 10, 22)
    muestra.save(update_fields=["fecha_muestreo", "fecha_ingreso"])
    estudio = estudio_de("PH", "CL-", "ECOLI", "SS10")
    # Cloruro es fórmula x*10: 40 → 400 mg/l. SS10 0,05 queda por debajo del LD 0,1.
    cargar(estudio, empleado, PH="7.4", CL_="40", ECOLI="0", SS10="0.05")
    validar(estudio, bioquimico, "PH", "CL-", "ECOLI", "SS10")
    return estudio


def por_codigo(contenido):
    return {p["codigo"]: p for p in contenido["pruebas"]}


def test_armar_contenido_datos(estudio_validado):
    contenido = armar_contenido(estudio_validado)
    muestra = estudio_validado.muestra
    cliente = muestra.cliente
    assert contenido["laboratorio"] == settings.AQUALAB_LABORATORIO
    assert contenido["laboratorio"]["logo"] == "aqualab"
    assert contenido["cliente"] == {
        "nombre_completo": cliente.nombre_completo,
        "tipo_documento": cliente.tipo_documento,
        "numero_documento": cliente.numero_documento,
        "domicilio": cliente.domicilio,
        "email": cliente.email,
    }
    assert contenido["muestra"] == {
        "numero_pi": str(muestra.numero_pi),
        "nombre": muestra.nombre,
        "origen": muestra.origen.nombre,
        "fecha_muestreo": "21/10/2026",
        "fecha_ingreso": "22/10/2026",
        "sitio_extraccion": muestra.sitio_extraccion,
        "responsable_muestreo": muestra.responsable_muestreo,
        "tipo_vertido": "Agua",
    }
    assert contenido["estudio"] == {
        "numero": str(estudio_validado.pk),
        "tipo": estudio_validado.tipo_nombre_snapshot,
    }


def test_armar_contenido_pruebas(estudio_validado):
    contenido = armar_contenido(estudio_validado)
    assert [p["codigo"] for p in contenido["pruebas"]] == ["CL-", "ECOLI", "PH", "SS10"]
    pruebas = por_codigo(contenido)
    ph, cloruro, ecoli, ss10 = pruebas["PH"], pruebas["CL-"], pruebas["ECOLI"], pruebas["SS10"]
    assert (ph["resultado_texto"], ph["evaluacion"], ph["limite_texto"]) == (
        "7,4",
        "cumple",
        "6.4 a 8.5",
    )
    assert ph["resultado"].startswith("7.4")
    assert (cloruro["resultado_texto"], cloruro["evaluacion"], cloruro["limite_texto"]) == (
        "400",
        "fuera_de_norma",
        "máx. 350.0",
    )
    assert cloruro["evaluacion_texto"] == "Fuera de norma"
    assert (ecoli["resultado_texto"], ecoli["evaluacion"]) == ("Ausente", "cumple")
    assert (ss10["resultado_texto"], ss10["evaluacion"]) == ("< 0,1", "cumple")
    assert ph["nombre"] == "pH"
    assert ph["unidad"] == Prueba.objects.get(codigo="PH").unidad
    assert ph["origen_limites"] == "general"
    assert ss10["limite_deteccion"] == "0.1"


def test_armar_contenido_usa_la_validacion(estudio_validado):
    Prueba.objects.filter(codigo="CL-").update(limite_max="500")
    cloruro = por_codigo(armar_contenido(estudio_validado))["CL-"]
    assert (cloruro["limite_max"], cloruro["evaluacion"]) == ("350.0", "fuera_de_norma")


def test_armar_contenido_sin_validacion_evalua_con_el_catalogo(estudio_de, empleado, completar):
    """El atajo `completar` de los tests no crea la Validacion: se evalúa con el catálogo."""
    estudio = estudio_de("PH")
    cargar(estudio, empleado, PH="9")
    completar(estudio)
    ph = por_codigo(armar_contenido(estudio))["PH"]
    assert (ph["evaluacion"], ph["limite_texto"]) == ("fuera_de_norma", "6.4 a 8.5")


def test_armar_contenido_sin_float(estudio_validado):
    def valores(dato):
        if isinstance(dato, dict):
            for v in dato.values():
                yield from valores(v)
        elif isinstance(dato, list):
            for v in dato:
                yield from valores(v)
        else:
            yield dato

    assert all(isinstance(v, str) for v in valores(armar_contenido(estudio_validado)))


def test_armar_contenido_vacios(estudio_validado):
    cliente = estudio_validado.muestra.cliente
    cliente.domicilio = ""
    cliente.save(update_fields=["domicilio"])
    estudio_validado.muestra.responsable_muestreo = ""
    estudio_validado.muestra.save(update_fields=["responsable_muestreo"])
    estudio_validado.refresh_from_db()
    contenido = armar_contenido(estudio_validado)
    assert contenido["cliente"]["domicilio"] == ""
    assert contenido["muestra"]["responsable_muestreo"] == ""
