import copy

import pytest
from django.db import IntegrityError, transaction
from django.urls import reverse
from django.utils import timezone

from estudios.models import Validacion
from informes import conclusion_hechos, conclusion_ia
from pruebas.models import Prueba

pytestmark = pytest.mark.django_db


def datos(estudio):
    hechos = conclusion_hechos.recolectar(estudio)
    return hechos, conclusion_ia.plantilla(hechos)


def test_dos_incumplimientos_exactos(conclusion_estudio, cliente_bioquimico):
    estudio = conclusion_estudio()
    hechos, texto = datos(estudio)
    assert len(hechos["pruebas"]) == 2
    por_codigo = {p["codigo"]: p for p in hechos["pruebas"]}
    assert por_codigo["PH"]["resultado_texto"] == "9,2"
    assert por_codigo["CL-"]["resultado_texto"] == "400"
    assert por_codigo["CL-"]["limite_texto"] == "máx. 350.0"
    assert texto.count("CL- —") == texto.count("PH —") == 1
    for prueba in hechos["pruebas"]:
        vigente = Validacion.objects.get(pk=prueba["validacion_id"])
        assert prueba["norma"] == vigente.norma
        assert prueba["limite_max"] == vigente.limite_max
        assert prueba["evaluacion"] == vigente.evaluacion
        assert prueba["norma"] in texto
    respuesta = cliente_bioquimico.get(reverse("informes:vista_previa", args=[estudio.pk]))
    assert "Proponer conclusión" in respuesta.content.decode()


def test_todas_evaluables_cumplen(conclusion_estudio):
    hechos, texto = datos(conclusion_estudio({"PH": "7.4"}))
    assert hechos["clase"] == "todas_cumplen"
    assert "Todas las pruebas" in texto
    assert "fuera de norma" not in texto
    assert "tratamiento" not in texto


def test_solo_validacion_vigente(conclusion_estudio, bioquimico):
    estudio = conclusion_estudio({"PH": "7.4"})
    anterior = Validacion.objects.get(asignacion__estudio=estudio)
    Validacion.objects.filter(pk=anterior.pk).update(anulada=True, fecha_anulacion=timezone.now())
    nueva = Validacion.objects.create(
        asignacion=anterior.asignacion,
        validada_por=bioquimico,
        limite_min="6.4",
        limite_max="8.5",
        norma="Norma vigente sintética",
        origen_limites=anterior.origen_limites,
        evaluacion="cumple",
    )
    hechos, _ = datos(estudio)
    assert len(hechos["pruebas"]) == 1
    assert hechos["pruebas"][0]["validacion_id"] == str(nueva.pk)
    assert hechos["pruebas"][0]["norma"] == nueva.norma


def test_catalogo_no_reemplaza_validacion(conclusion_estudio):
    estudio = conclusion_estudio()
    antes = conclusion_hechos.recolectar(estudio)
    Prueba.objects.filter(codigo__in=["PH", "CL-"]).update(
        limite_min="0", limite_max="1", norma="Otra norma", version=99
    )
    despues = conclusion_hechos.recolectar(estudio)
    assert antes == despues
    assert conclusion_hechos.huella(antes) == conclusion_hechos.huella(despues)


@pytest.mark.parametrize(
    "codigo,valor,mostrado",
    [
        ("ECOLI", "0", "Ausente"),
        ("ECOLI", "1", "Presente"),
        ("SS10", "0.05", "< 0,1"),
        ("PH", "9.2", "9,2"),
    ],
)
def test_presentaciones_resultado(conclusion_estudio, codigo, valor, mostrado):
    estudio = conclusion_estudio({codigo: valor})
    hechos, _ = datos(estudio)
    prueba = hechos["pruebas"][0]
    assert prueba["resultado_texto"] == mostrado
    assert prueba["evaluacion"] == Validacion.objects.get(asignacion__estudio=estudio).evaluacion


def test_parcial_sin_vigente(conclusion_estudio):
    estudio = conclusion_estudio()
    Validacion.objects.filter(asignacion__estudio=estudio, asignacion__prueba__codigo="PH").update(
        anulada=True, fecha_anulacion=timezone.now()
    )
    hechos, texto = datos(estudio)
    prueba = next(p for p in hechos["pruebas"] if p["codigo"] == "PH")
    assert hechos["clase"] == "parcial"
    assert prueba["motivos"] == ["sin_validacion"]
    assert prueba["norma"] == prueba["limite_max"] == prueba["evaluacion"] == ""
    assert "CL- —" in texto
    assert "PH" in "\n".join(conclusion_hechos.advertencias(hechos))


def test_parcial_sin_limite(conclusion_estudio):
    hechos, texto = datos(conclusion_estudio({"PH": "7.4"}, sin_limite=("PH",)))
    assert hechos["clase"] == "parcial"
    assert hechos["pruebas"][0]["motivos"] == ["sin_limite_comparable"]
    assert "Todas las pruebas" not in texto


def test_parcial_sin_norma(conclusion_estudio):
    hechos, _ = datos(conclusion_estudio({"PH": "9.2"}, sin_norma=("PH",)))
    prueba = hechos["pruebas"][0]
    assert hechos["clase"] == "parcial"
    assert prueba["motivos"] == ["sin_norma"]
    assert prueba["resultado_texto"] == "9,2"
    assert prueba["limite_texto"] == "6.4 a 8.5"
    assert prueba["evaluacion"] == "fuera_de_norma"
    advertencia = "\n".join(conclusion_hechos.advertencias(hechos))
    assert all(texto in advertencia for texto in ("PH", "9,2", "6.4 a 8.5", "norma"))


def test_todas_no_evaluables(conclusion_estudio):
    hechos, texto = datos(conclusion_estudio(sin_norma=("PH", "CL-")))
    assert hechos["clase"] == "parcial"
    assert len(conclusion_hechos.advertencias(hechos)) == 2
    assert "Todas las pruebas" not in texto


def test_parcial_mixta_conserva_incumplimientos_y_ausencias(conclusion_estudio):
    estudio = conclusion_estudio({"PH": "9.2", "CL-": "40", "COND": "1"}, sin_norma=("COND",))
    hechos, texto = datos(estudio)
    assert hechos["clase"] == "parcial"
    assert texto.count("PH —") == texto.count("CL- —") == 1
    advertencias = conclusion_hechos.advertencias(hechos)
    assert len(advertencias) == 1 and "COND" in advertencias[0]
    assert "Todas las pruebas" not in texto


def test_vigentes_duplicadas_no_se_eligen(conclusion_estudio, bioquimico):
    estudio = conclusion_estudio({"PH": "7.4"})
    asignacion = list(conclusion_hechos.asignaciones(estudio))[0]
    vigente = asignacion.validaciones_vigentes[0]
    with pytest.raises(IntegrityError), transaction.atomic():
        Validacion.objects.create(
            asignacion=asignacion,
            validada_por=bioquimico,
            origen_limites="general",
            evaluacion="cumple",
        )
    asignacion.validaciones_vigentes = [vigente, copy.copy(vigente)]
    with pytest.raises(conclusion_hechos.FuentesAmbiguas):
        conclusion_hechos.desde_asignaciones(estudio.pk, [asignacion])
