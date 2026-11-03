"""Ayuda en formularios (US 9.1): ui/ayuda.html, ui/campo.html y el filtro describir."""

import re
from pathlib import Path

from django import forms
from django.conf import settings
from django.template import Context, Template
from django.template.loader import render_to_string

CSS = Path(settings.BASE_DIR) / "static" / "css" / "aqualab.css"


class FormularioPrueba(forms.Form):
    origen = forms.CharField(label="Origen", help_text="Fuente de agua de la muestra.")
    telefono = forms.CharField(label="Teléfono", required=False)
    vacio = forms.CharField(label="Vacío", required=False, help_text="")
    tipo = forms.ChoiceField(
        label="Tipo de documento",
        choices=[("DNI", "DNI"), ("CUIT", "CUIT")],
        widget=forms.RadioSelect,
        help_text="DNI para personas.",
    )
    pruebas = forms.CharField(label="Pruebas", help_text="Pruebas por defecto.")
    otro = forms.CharField(
        label="Otro",
        help_text="Con descripción propia.",
        widget=forms.TextInput(attrs={"aria-describedby": "otro id_otro_instruccion"}),
    )


def campo(field, **extra):
    return render_to_string("ui/campo.html", {"field": field, **extra})


def etiqueta_de(html, nombre):
    """Contenido del <label> o <legend> de un campo."""
    return re.search(rf'<(label|legend)[^>]*data-campo="{nombre}"[^>]*>(.*?)</\1>', html, re.S)[2]


# --- US 1, escenarios 1 y 2 (FR-001, FR-004) ---


def test_campo_con_ayuda_muestra_el_icono_y_el_tooltip():
    html = campo(FormularioPrueba()["origen"])

    assert "data-ayuda" in html
    assert re.search(
        r'<button type="button" class="ayuda-boton" aria-label="Ayuda: Origen" '
        r'aria-describedby="id_origen_helptext">',
        html,
    )
    tooltip = re.search(r'<span role="tooltip" id="id_origen_helptext"[^>]*>(.*?)</span>', html)
    assert tooltip[1] == "Fuente de agua de la muestra."
    assert 'class="campo-ayuda"' not in html


def test_campo_sin_ayuda_no_muestra_el_icono():
    formulario = FormularioPrueba()
    assert "data-ayuda" not in campo(formulario["telefono"])
    assert "data-ayuda" not in campo(formulario["vacio"])


def test_el_icono_va_al_lado_de_la_etiqueta_y_no_adentro():
    formulario = FormularioPrueba()
    for nombre in ("origen", "tipo"):
        html = campo(formulario[nombre])
        assert "ayuda-boton" not in etiqueta_de(html, nombre)
        assert "ayuda-boton" in html


# --- US 1, escenario 6 (FR-005) ---


def test_el_control_queda_descrito_por_la_ayuda():
    html = campo(FormularioPrueba()["origen"])
    assert re.search(r'<input[^>]*name="origen"[^>]*aria-describedby="id_origen_helptext"', html)


def test_con_error_el_control_queda_descrito_por_la_ayuda_y_el_error():
    formulario = FormularioPrueba(data={})
    formulario.is_valid()
    html = campo(formulario["origen"])
    assert re.search(r'aria-describedby="id_origen_helptext id_origen_error"', html)


def test_en_los_radios_la_ayuda_describe_al_fieldset():
    html = campo(FormularioPrueba()["tipo"])
    assert '<fieldset aria-describedby="id_tipo_helptext">' in html
    assert 'id="id_tipo_helptext"' in html
    assert "campo-leyenda" in html


# --- US 1, escenario 8 (FR-012) ---


def test_con_error_el_mensaje_sigue_visible_y_la_ayuda_tambien():
    formulario = FormularioPrueba(data={})
    formulario.is_valid()
    html = campo(formulario["origen"])
    assert re.search(r'<div class="campo-error" id="id_origen_error">\s*<div>', html)
    assert "data-ayuda" in html


# --- Instrucciones visibles (aclaración de la spec) ---


def test_ayuda_visible_muestra_el_texto_debajo_y_sin_icono():
    html = campo(FormularioPrueba()["origen"], ayuda_visible=True)
    assert (
        '<div class="campo-ayuda" id="id_origen_helptext">Fuente de agua de la muestra.</div>'
        in html
    )
    assert "data-ayuda" not in html


def test_instruccion_visible_y_asociada_al_control():
    html = campo(FormularioPrueba()["pruebas"], instruccion="Usá Ctrl.")
    assert '<p class="campo-ayuda" id="id_pruebas_instruccion">Usá Ctrl.</p>' in html
    assert 'aria-describedby="id_pruebas_helptext id_pruebas_instruccion"' in html
    assert 'role="tooltip" id="id_pruebas_helptext"' in html


def test_describir_conserva_la_descripcion_propia_sin_duplicar():
    html = Template('{% load ui %}{{ field|describir:"id_otro_instruccion" }}').render(
        Context({"field": FormularioPrueba()["otro"]})
    )
    assert 'aria-describedby="otro id_otro_instruccion"' in html


# --- ui/ayuda.html ---


def test_ayuda_alineada_a_la_derecha():
    html = render_to_string(
        "ui/ayuda.html",
        {
            "texto": "Valor leído.",
            "id": "ayuda-medicion",
            "etiqueta": "Medición",
            "lado": "derecha",
        },
    )
    assert 'data-lado="derecha"' in html
    assert 'aria-label="Ayuda: Medición"' in html
    assert (
        '<span role="tooltip" id="ayuda-medicion" class="ayuda-texto">Valor leído.</span>' in html
    )


def test_ayuda_escapa_los_textos_literales():
    html = render_to_string(
        "ui/ayuda.html", {"texto": "<b>x</b>", "id": "a", "etiqueta": "E", "lado": ""}
    )
    assert "&lt;b&gt;x&lt;/b&gt;" in html
    assert 'data-lado="izquierda"' in html


# --- CSS compilado (FR-002, WCAG 1.4.13) ---


def test_el_css_compilado_incluye_la_ayuda_y_se_puede_recorrer_con_el_mouse():
    css = CSS.read_text(encoding="utf-8")
    assert ".ayuda-boton" in css
    assert "data-cerrada" in css
    assert ".ayuda-texto:before" in css
    for regla in re.findall(r"\.ayuda-texto\{[^}]*\}", css):
        assert "pointer-events:none" not in regla
