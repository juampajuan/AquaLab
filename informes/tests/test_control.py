import re
from decimal import Decimal

import pytest
from django.urls import reverse

from estudios import calculo
from estudios.models import EstadoEstudio, EstadoPruebaEstudio, Estudio, Medicion
from estudios.servicios import corregir_mediciones
from estudios.tests.utiles import asignacion_de, cargar, validar

pytestmark = pytest.mark.django_db


def url(estudio):
    return reverse("informes:control", args=[estudio.pk])


def fila(html, codigo):
    """HTML de la fila de la tabla de pruebas con ese código."""
    coincidencia = re.search(rf'<tr data-prueba="{re.escape(codigo)}">(.*?)</tr>', html, re.S)
    assert coincidencia, f"No está la fila de {codigo}"
    return coincidencia.group(1)


def test_control_muestra_ficha_y_pruebas(cliente_http, estudio_de, completar):
    estudio = estudio_de("PH", "CL-", "CA")
    completar(estudio, "CA")
    html = cliente_http.get(url(estudio)).content.decode()
    assert f"Controlar pruebas del estudio {estudio.pk}" in html
    assert "N° PI 200001" in html
    assert "Muestra test" in html
    assert "Cliente de test" in html
    assert estudio.tipo_nombre_snapshot in html
    assert "Pendiente de análisis" in html
    assert "1 de 3 pruebas completadas" in html
    codigos = re.findall(r'<tr data-prueba="([^"]+)">', html)
    assert codigos == ["CA", "CL-", "PH"]
    for codigo in codigos:
        assert asignacion_de(estudio, codigo).prueba.nombre in fila(html, codigo)


def test_control_marca_incompletas_y_sin_validar(cliente_http, empleado, estudio_de, completar):
    estudio = estudio_de("CL-", "PH", "CA")
    cargar(estudio, empleado, {"CL-": "2.35"})
    completar(estudio, "CA")
    html = cliente_http.get(url(estudio)).content.decode()
    assert "Incompleta" in fila(html, "PH")
    assert "Pendiente" in fila(html, "PH")
    assert "Sin validar" in fila(html, "CL-")
    assert "Cargada" in fila(html, "CL-")
    assert "Incompleta" not in fila(html, "CA") and "Sin validar" not in fila(html, "CA")
    assert "Hay 2 pruebas sin completar." in html


def test_control_muestra_motivo_sin_resultado(cliente_http, empleado, estudio_de):
    estudio = estudio_de("CA", "DUREZA-T", "MG")
    cargar(estudio, empleado, {"DUREZA-T": "15"})
    asignaciones = list(estudio.pruebas_asignadas.select_related("prueba", "medicion", "resultado"))
    todas = {a.prueba.codigo: a for a in asignaciones}
    motivo = calculo.motivo_sin_resultado(todas["MG"], todas)
    assert motivo
    html = cliente_http.get(url(estudio)).content.decode()
    assert "Incompleta" in fila(html, "MG")
    assert motivo in fila(html, "MG")
    detalle = cliente_http.get(reverse("estudios:detalle", args=[estudio.pk])).content.decode()
    assert motivo in detalle


def test_boton_deshabilitado_con_pruebas_sin_completar(cliente_http, estudio_de, completar):
    estudio = estudio_de("CL-", "PH")
    completar(estudio, "CL-")
    html = cliente_http.get(url(estudio)).content.decode()
    assert re.search(r'<button type="button" disabled aria-describedby="motivo-bloqueo"', html)
    assert 'id="motivo-bloqueo"' in html
    assert reverse("informes:generar", args=[estudio.pk]) not in html


def test_boton_habilitado_con_todas_completadas(cliente_http, estudio_de, completar):
    estudio = estudio_de("CL-", "PH")
    completar(estudio)
    html = cliente_http.get(url(estudio)).content.decode()
    assert "El estudio está listo para informar: todas sus pruebas están completadas." in html
    accion = reverse("informes:generar", args=[estudio.pk])
    assert re.search(rf'<form method="post" action="{accion}"', html)
    assert "csrfmiddlewaretoken" in html
    assert "disabled" not in html.split(accion)[1].split("</form>")[0]


def test_control_con_informe_emitido(cliente_http, estudio_de, completar, emitir):
    estudio = estudio_de("CL-")
    completar(estudio)
    emitir(estudio)
    html = cliente_http.get(url(estudio)).content.decode()
    assert "El informe de este estudio ya fue generado." in html
    assert "Generar informe" not in html


def test_control_estudio_inexistente_404(cliente_http):
    assert cliente_http.get(reverse("informes:control", args=[999999])).status_code == 404


def test_consultar_no_modifica(cliente_http, empleado, estudio_de, completar):
    estudio = estudio_de("CL-", "PH")
    cargar(estudio, empleado, {"CL-": "2.35"})
    completar(estudio, "PH")

    def foto():
        return (
            Estudio.objects.get(pk=estudio.pk).estado,
            sorted(estudio.pruebas_asignadas.values_list("pk", "estado")),
            Medicion.objects.count(),
        )

    antes = foto()
    cliente_http.get(reverse("informes:listar"))
    cliente_http.get(url(estudio))
    assert foto() == antes


def test_control_y_detalle_muestran_el_mismo_estado(cliente_http, empleado, estudio_de, completar):
    estudio = estudio_de("CL-", "PH", "CA")
    cargar(estudio, empleado, {"CL-": "2.35"})
    completar(estudio, "CA")
    control = cliente_http.get(url(estudio)).content.decode()
    detalle = cliente_http.get(reverse("estudios:detalle", args=[estudio.pk])).content.decode()
    for asignacion in estudio.pruebas_asignadas.all():
        etiqueta = f">{asignacion.get_estado_display()}</span>"
        assert etiqueta in fila(control, asignacion.prueba.codigo)
        assert etiqueta in detalle
    assert {a.estado for a in estudio.pruebas_asignadas.all()} == {
        EstadoPruebaEstudio.PENDIENTE,
        EstadoPruebaEstudio.CARGADA,
        EstadoPruebaEstudio.COMPLETADA,
    }


def test_detalle_enlaza_control(cliente_http, estudio_de):
    estudio = estudio_de("CL-")
    html = cliente_http.get(reverse("estudios:detalle", args=[estudio.pk])).content.decode()
    assert re.search(rf'href="{url(estudio)}"[^>]*>.*?Controlar para informe', html, re.S)


def test_flujo_con_validacion_real(cliente_http, bioquimico, estudio_de):
    """Con US 6.4: validar todas habilita generar; corregir una medición vuelve a bloquear."""
    estudio = estudio_de("CL-", "PH")
    cargar(estudio, bioquimico, {"CL-": "40", "PH": "7.20"})
    validar(estudio, bioquimico, "CL-")
    html = cliente_http.get(url(estudio)).content.decode()
    assert "Hay 1 prueba sin completar." in html
    assert "Sin validar" in fila(html, "PH")

    validar(estudio, bioquimico, "PH")
    assert Estudio.objects.get(pk=estudio.pk).estado == EstadoEstudio.FINALIZADO
    html = cliente_http.get(url(estudio)).content.decode()
    assert "El estudio está listo para informar" in html
    listos = cliente_http.get(reverse("informes:listar"), {"listos": "1"}).content.decode()
    assert url(estudio) in listos

    ph = asignacion_de(estudio, "PH")
    original = Decimal(ph.medicion.valor_ingresado)  # el que vio el formulario (US 6.3)
    corregir_mediciones(estudio.pk, {ph.pk: (original, Decimal("7.30"))}, bioquimico)
    html = cliente_http.get(url(estudio)).content.decode()
    assert "Hay 1 prueba sin completar." in html
    assert re.search(r'<button type="button" disabled', html)
