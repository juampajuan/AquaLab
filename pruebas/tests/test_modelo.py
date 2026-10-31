import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from pruebas.models import LimiteVertido, Prueba, TipoCalculo, TipoVertido, referencias_formula

pytestmark = pytest.mark.django_db


def test_prueba_minima():
    p = Prueba(codigo=" TEST-A ", nombre=" Prueba A ")
    p.full_clean()
    p.save()
    assert (p.codigo, p.nombre) == ("TEST-A", "Prueba A")
    with pytest.raises(IntegrityError), transaction.atomic():
        Prueba.objects.create(codigo="TEST-A", nombre="Otra")


@pytest.mark.parametrize(
    "campo,valor", [("codigo", " "), ("nombre", " "), ("codigo", "x" * 51), ("nombre", "x" * 151)]
)
def test_validacion(campo, valor):
    p = Prueba(codigo="TEST-A", nombre="Prueba A")
    setattr(p, campo, valor)
    with pytest.raises(ValidationError):
        p.full_clean()


def test_defaults_prueba_nueva():
    p = Prueba.objects.create(codigo="X", nombre="Y")
    p.refresh_from_db()
    assert p.tipo_calculo == TipoCalculo.DIRECTO
    assert (p.formula, p.es_calculada, p.activa) == ("", False, True)
    textos = ("unidad", "unidad_medicion", "norma", "limite_min", "limite_max", "limite_deteccion")
    assert all(getattr(p, campo) == "" for campo in textos)
    assert p.observacion == ""
    p.full_clean()


@pytest.mark.parametrize(
    "valor,esperado",
    [
        ("Ausente", "Ausente"),
        ("NE", "NE"),
        ("SOE", "SOE"),
        ("Ph-0,2", "Ph-0,2"),
        ("3.0", "3.0"),
        (" 45 ", "45"),
    ],
)
def test_limites_se_guardan_como_texto(valor, esperado):
    p = Prueba(codigo="TEST-A", nombre="Prueba A", limite_max=valor)
    p.full_clean()
    p.save()
    p.refresh_from_db()
    assert p.limite_max == esperado
    limite = LimiteVertido(prueba=p, tipo_vertido=TipoVertido.CANAL, limite_max=valor)
    limite.full_clean()
    limite.save()
    limite.refresh_from_db()
    assert limite.limite_max == esperado


def test_formula_segun_tipo_calculo():
    with pytest.raises(ValidationError) as error:
        Prueba(codigo="A", nombre="A", formula="x*20").full_clean()
    assert "formula" in error.value.message_dict
    with pytest.raises(ValidationError) as error:
        Prueba(codigo="A", nombre="A", tipo_calculo=TipoCalculo.FORMULA).full_clean()
    assert "formula" in error.value.message_dict
    Prueba(codigo="A", nombre="A", tipo_calculo=TipoCalculo.FORMULA, formula="x*20").full_clean()


@pytest.mark.parametrize(
    "datos",
    [
        {"formula": "x*20"},
        {"tipo_calculo": TipoCalculo.FORMULA},
        {"es_calculada": True},
    ],
)
def test_constraints_formula_en_base(datos):
    with pytest.raises(IntegrityError), transaction.atomic():
        Prueba.objects.create(codigo="A", nombre="A", **datos)


def test_es_calculada_coherente_con_referencias():
    def prueba(formula, es_calculada):
        return Prueba(
            codigo="A",
            nombre="A",
            tipo_calculo=TipoCalculo.FORMULA,
            formula=formula,
            es_calculada=es_calculada,
        )

    for formula, es_calculada in (("{COND}*0.54", False), ("x*20", True)):
        with pytest.raises(ValidationError) as error:
            prueba(formula, es_calculada).full_clean()
        assert "es_calculada" in error.value.message_dict
    prueba("{COND}*0.54", True).full_clean()
    prueba("x*20", False).full_clean()


def test_formula_no_se_referencia_a_si_misma():
    p = Prueba(
        codigo="SDT",
        nombre="Sólidos",
        tipo_calculo=TipoCalculo.FORMULA,
        formula="{SDT}*2",
        es_calculada=True,
    )
    with pytest.raises(ValidationError) as error:
        p.full_clean()
    assert error.value.message_dict["formula"] == ["La prueba no puede referenciarse a sí misma."]


@pytest.mark.parametrize(
    "formula,esperado",
    [
        ("{NA}/sqrt(({CA}+{MG})/2)", {"NA", "CA", "MG"}),
        ("({NTK-T}-{NH4})", {"NTK-T", "NH4"}),
        ("({DUREZA-T}-{CA}*2.5)*0.243", {"DUREZA-T", "CA"}),
        ("x*20", set()),
        ("", set()),
    ],
)
def test_referencias_formula(formula, esperado):
    assert referencias_formula(formula) == esperado


def test_limite_vertido_unico_por_tipo():
    p = Prueba.objects.create(codigo="A", nombre="A")
    LimiteVertido.objects.create(prueba=p, tipo_vertido=TipoVertido.CLOACAL, limite_max="NE")
    LimiteVertido.objects.create(prueba=p, tipo_vertido=TipoVertido.CANAL, limite_max="0.5")
    with pytest.raises(IntegrityError), transaction.atomic():
        LimiteVertido.objects.create(prueba=p, tipo_vertido=TipoVertido.CANAL)
    with pytest.raises(ValidationError):
        LimiteVertido(prueba=p, tipo_vertido="otro").full_clean(validate_unique=False)


def test_esta_en_uso_por_tipo_o_estudio(prueba_en_tipo, prueba_en_estudio, prueba_libre):
    assert prueba_en_tipo.esta_en_uso()
    assert prueba_en_estudio.esta_en_uso()
    assert not prueba_libre.esta_en_uso()
    assert not Prueba(codigo="NUEVA", nombre="Nueva").esta_en_uso()
