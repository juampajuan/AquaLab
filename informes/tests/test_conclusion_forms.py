import pytest

from informes import forms


@pytest.mark.parametrize("texto", ["\x00", "a\x00b"])
def test_rechaza_nul(texto):
    form = forms.GuardarConclusionForm(
        {"revision_esperada": 0, "huella_hechos_vista": "a" * 64, "texto": texto}
    )
    assert not form.is_valid()
    assert "texto" in form.errors


def test_preserva_texto_y_normaliza_lf():
    form = forms.GuardarConclusionForm(
        {"revision_esperada": 0, "huella_hechos_vista": "a" * 64, "texto": "  Texto\r\nexacto  "}
    )
    assert form.is_valid()
    assert form.cleaned_data["texto"] == "  Texto\nexacto  "


@pytest.mark.parametrize("revision", [True, -1, "no", None])
def test_revision_invalida(revision):
    form = forms.GuardarConclusionForm(
        {"revision_esperada": revision, "huella_hechos_vista": "a" * 64, "texto": "Texto"}
    )
    assert not form.is_valid()
