import re

import pytest
from django.urls import reverse

from estudios.tests.utiles import cargar, validar
from informes.servicios import emitir_informe
from pruebas.models import Prueba

pytestmark = pytest.mark.django_db


def documento(html):
    """El bloque del documento, sin la marca de borrador ni el encabezado de la página."""
    inicio = html.index('data-componente="informe"')
    cuerpo = html[html.index("<section", inicio) : html.index("<footer", inicio)]
    # El informe emitido enlaza estudio, muestra y cliente (SCRUM-82); el contenido es el mismo.
    return re.sub(r"</?a[^>]*>", "", cuerpo)


@pytest.fixture
def estudio_listo(estudio_de, empleado, bioquimico):
    estudio = estudio_de("PH", "CL-")
    cargar(estudio, empleado, PH="7.4", CL_="40")
    validar(estudio, bioquimico, "PH", "CL-")
    return estudio


def test_emitido_igual_a_vista_previa(cliente_bioquimico, estudio_listo, bioquimico):
    previa = cliente_bioquimico.get(reverse("informes:vista_previa", args=[estudio_listo.pk]))
    emitir_informe(estudio_listo.pk, bioquimico)
    emitido = cliente_bioquimico.get(reverse("informes:ver", args=[estudio_listo.pk]))
    assert emitido.status_code == 200
    html = emitido.content.decode()
    assert documento(html) == documento(previa.content.decode())
    assert "Informe N° INF-000001" in html
    assert "BORRADOR" not in html
    assert "Emitido por " in html


def test_informe_no_cambia_al_editar(cliente_http, estudio_listo, bioquimico):
    cliente = estudio_listo.muestra.cliente
    domicilio_original = "Calle Original 123"
    cliente.domicilio = domicilio_original
    cliente.save(update_fields=["domicilio"])
    emitir_informe(estudio_listo.pk, bioquimico)
    cliente.domicilio = "Otra calle 999"
    cliente.save(update_fields=["domicilio"])
    Prueba.objects.filter(codigo="CL-").update(limite_max="500")
    html = cliente_http.get(reverse("informes:ver", args=[estudio_listo.pk])).content.decode()
    assert domicilio_original in html and "Otra calle 999" not in html
    assert "máx. 350.0" in html and "máx. 500" not in html


def test_ver_sin_informe_404(cliente_http, estudio_listo):
    assert cliente_http.get(reverse("informes:ver", args=[estudio_listo.pk])).status_code == 404


def test_control_y_detalle_ofrecen_ver_informe(cliente_http, estudio_listo, bioquimico):
    ver = reverse("informes:ver", args=[estudio_listo.pk])
    control = reverse("informes:control", args=[estudio_listo.pk])
    detalle = reverse("estudios:detalle", args=[estudio_listo.pk])
    assert ver not in cliente_http.get(control).content.decode()
    assert ver not in cliente_http.get(detalle).content.decode()
    emitir_informe(estudio_listo.pk, bioquimico)
    assert ver in cliente_http.get(control).content.decode()
    assert ver in cliente_http.get(detalle).content.decode()


def test_parcial_firma():
    from django.template.loader import render_to_string

    firma = {"nombre": "Ana Pérez", "matricula": "MP 1234", "imagen": "data:image/png;base64,AAAA"}
    html = render_to_string("informes/firma.html", {"firma": firma})
    assert 'src="data:image/png;base64,AAAA"' in html
    assert 'alt="Firma de Ana Pérez"' in html
    assert "Mat. MP 1234" in html
    assert "Sin firma registrada" not in html

    sin_firma = render_to_string("informes/firma.html", {})
    assert "Sin firma registrada" in sin_firma
    assert "<img" not in sin_firma


def test_ver_vuelve_a_emitidos(cliente_bioquimico, estudio_listo, bioquimico):
    emitir_informe(estudio_listo.pk, bioquimico)
    url = reverse("informes:ver", args=[estudio_listo.pk])
    html = cliente_bioquimico.get(url, {"desde": "emitidos"}).content.decode()
    assert re.search(rf'href="{reverse("informes:emitidos")}"[^>]*>.*?Volver', html, re.S)
    # Sin «desde», vuelve al estudio.
    html = cliente_bioquimico.get(url).content.decode()
    assert re.search(
        rf'href="{reverse("estudios:detalle", args=[estudio_listo.pk])}"[^>]*>.*?Volver', html, re.S
    )


def test_ver_pk_inexistente_404(cliente_http):
    assert cliente_http.get(reverse("informes:ver", args=[999999])).status_code == 404


@pytest.mark.parametrize(
    ("usuario", "ofrece"), [("cliente_bioquimico", True), ("cliente_comun", False)]
)
def test_ver_ofrece_enviar_con_permiso(request, estudio_listo, bioquimico, usuario, ofrece):
    """SCRUM-79 (FR-001): «Enviar por correo» solo para quien puede emitir informes."""
    emitir_informe(estudio_listo.pk, bioquimico)
    cliente = request.getfixturevalue(usuario)

    html = cliente.get(reverse("informes:ver", args=[estudio_listo.pk])).content.decode()

    enlace = f'href="{reverse("informes:enviar", args=[estudio_listo.pk])}"'
    assert (enlace in html) is ofrece
    assert ("Enviar por correo" in html) is ofrece


@pytest.mark.parametrize("usuario", ["cliente_bioquimico", "cliente_comun"])
def test_historial_vacio(request, estudio_listo, bioquimico, usuario):
    """SCRUM-79 (US2 Esc. 1): un informe sin envíos lo indica, para cualquier empleado."""
    emitir_informe(estudio_listo.pk, bioquimico)
    cliente = request.getfixturevalue(usuario)

    html = cliente.get(reverse("informes:ver", args=[estudio_listo.pk])).content.decode()

    assert "Envíos por correo" in html
    assert "Este informe todavía no se envió por correo." in html


def test_historial_ordenado(cliente_comun, estudio_listo, bioquimico):
    """SCRUM-79 (US2 Esc. 3, FR-006): todos los envíos, del más reciente al más antiguo."""
    import re
    import uuid
    from datetime import datetime
    from zoneinfo import ZoneInfo

    from django.conf import settings

    from informes.models import EnvioInforme, ResultadoEnvio

    informe = emitir_informe(estudio_listo.pk, bioquimico)
    bioquimico.first_name, bioquimico.last_name = "Ana", "Pérez"
    bioquimico.save()
    zona = ZoneInfo(settings.TIME_ZONE)
    datos = [
        (datetime(2026, 11, 2, 9, 0, tzinfo=zona), "a@ejemplo.com", ResultadoEnvio.ENVIADO),
        (datetime(2026, 11, 4, 15, 30, tzinfo=zona), "b@ejemplo.com", ResultadoEnvio.FALLIDO),
        (datetime(2026, 11, 3, 10, 15, tzinfo=zona), "c@ejemplo.com", ResultadoEnvio.ENVIADO),
    ]
    for fecha, destinatario, resultado in datos:
        envio = EnvioInforme.objects.create(
            informe=informe,
            enviado_por=bioquimico,
            destinatario=destinatario,
            resultado=resultado,
            clave=uuid.uuid4(),
        )
        EnvioInforme.objects.filter(pk=envio.pk).update(fecha=fecha)

    html = cliente_comun.get(reverse("informes:ver", args=[estudio_listo.pk])).content.decode()
    seccion = html[html.index('data-componente="envios"') :]
    filas = re.findall(r"<tr>(.*?)</tr>", seccion, re.S)[1:]  # sin el encabezado

    assert len(filas) == 3
    esperado = [
        ("04/11/2026 15:30", "b@ejemplo.com", "danger", "Falló"),
        ("03/11/2026 10:15", "c@ejemplo.com", "success", "Enviado"),
        ("02/11/2026 09:00", "a@ejemplo.com", "success", "Enviado"),
    ]
    for fila, (fecha, destinatario, tipo, texto) in zip(filas, esperado, strict=True):
        assert fecha in fila
        assert destinatario in fila
        assert "Ana Pérez" in fila
        assert f'data-estado="{tipo}">{texto}<' in fila
    assert "Este informe todavía no se envió por correo." not in html
