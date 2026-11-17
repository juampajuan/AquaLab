import re
from html import unescape

import pytest
from django.urls import reverse

from informes import conclusion_hechos, conclusiones
from informes.models import BorradorConclusion

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("aprobada", [False, True])
def test_editor_unico_editable_y_estado_simple(
    conclusion_propuesta, bioquimico, cliente_bioquimico, aprobada
):
    estudio, estado = conclusion_propuesta
    if aprobada:
        conclusiones.aprobar_conclusion(
            estudio.pk,
            bioquimico,
            estado["revision"],
            estado["huella_hechos"],
            estado["huella_texto"],
            confirmacion=True,
        )
    respuesta = cliente_bioquimico.get(reverse("informes:vista_previa", args=[estudio.pk]))
    assert respuesta.status_code == 200
    html = respuesta.content.decode()
    assert len(re.findall(r"<textarea\b[^>]*data-conclusion-editor", html)) == 1
    assert "readonly" not in respuesta.context["conclusion_form"].fields["texto"].widget.attrs
    assert respuesta.context["conclusion_form"].initial["texto"] == estado["texto_editorial"]
    for eliminado in (
        "Editar borrador",
        "Último texto editorial conservado",
        "Hechos de origen registrados",
        "Texto final que se aprobará",
        "Guardar borrador",
        "data-conclusion-final",
        "data-conclusion-incluir",
    ):
        assert eliminado not in html
    indicador = re.search(r"data-conclusion-estado>\s*(.*?)\s*</p>", html, re.S)
    assert indicador.group(1).strip() == ("Aprobada" if aprobada else "Pendiente")
    boton_emitir = re.search(r"<button\b[^>]*data-conclusion-emitir-boton[^>]*>", html)
    assert ("disabled" in boton_emitir.group()) == (not aprobada)
    assert 'name="incluir_conclusion" value="1"' in html
    assert "Aprobar conclusión" in html
    assert "Emitir con conclusión aprobada" in html
    assert "Emitir sin conclusión" in html


def test_advertencias_visibles_separadas_del_texto_editable(
    conclusion_estudio, bioquimico, cliente_bioquimico
):
    estudio = conclusion_estudio(sin_norma=("PH",))
    hechos = conclusion_hechos.recolectar(estudio)
    estado = conclusiones.proponer_conclusion(
        estudio.pk, bioquimico, 0, conclusion_hechos.huella(hechos)
    )
    respuesta = cliente_bioquimico.get(reverse("informes:vista_previa", args=[estudio.pk]))
    html = respuesta.content.decode()
    bloque = re.search(r"<div[^>]*data-conclusion-advertencias>(.*?)</div>", html, re.S)
    assert unescape(bloque.group(1)) == "\n".join(estado["advertencias"])
    assert "Pruebas no evaluables" in html
    assert respuesta.context["conclusion_form"].initial["texto"] == estado["texto_editorial"]
    assert "Advertencias de información insuficiente:" not in estado["texto_editorial"]
    assert "Advertencias de información insuficiente:" in estado["texto_final"]


def test_abrir_editor_vacio_no_crea_borrador(conclusion_estudio, cliente_bioquimico):
    estudio = conclusion_estudio()
    respuesta = cliente_bioquimico.get(reverse("informes:vista_previa", args=[estudio.pk]))
    assert respuesta.status_code == 200
    assert "readonly" not in respuesta.context["conclusion_form"].fields["texto"].widget.attrs
    assert not BorradorConclusion.objects.filter(estudio=estudio).exists()
