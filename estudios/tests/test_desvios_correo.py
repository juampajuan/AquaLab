"""Aviso por correo de los desvíos recién calculados (US 8.2): `estudios/notificaciones.py`."""

import datetime as dt
import logging
from decimal import Decimal
from smtplib import SMTPException
from unittest import mock

import pytest
from django.contrib.auth.models import Group
from django.db import transaction
from django.urls import reverse

from estudios import calculo
from estudios.models import Estudio, Medicion, Resultado
from estudios.servicios import corregir_mediciones
from estudios.tests.conftest import en_grupo_bioquimicos
from estudios.tests.utiles import asignacion_de, cargar, validar
from muestras.models import Origen

pytestmark = pytest.mark.django_db

DIA = dt.date(2026, 3, 1)


def dia(n):
    return DIA + dt.timedelta(days=n)


@pytest.fixture
def origen(cliente_a):
    return Origen.objects.create(cliente=cliente_a, nombre="Pozo del aviso")


@pytest.fixture
def historia(origen, estudio_en_origen):
    """Cloruro validado 100, 110 y 120 mg/l y pH 7,0 en tres muestras anteriores."""
    for n, valor in enumerate(["10", "11", "12"]):
        estudio_en_origen(origen, dia(n), 301001 + n, {"CL-": valor, "PH": "7.0"})


@pytest.fixture
def sin_cargar(origen, historia, estudio_en_origen):
    """Estudio del 4 de marzo con Cloruro y pH, todavía sin mediciones."""
    return estudio_en_origen(origen, dia(3), 301010, {"CL-": None, "PH": None})


@pytest.fixture
def destinatarios(bioquimico, django_user_model):
    """Dos bioquímicos activos (`bioquimico` y otro), uno inactivo y un usuario de otro grupo."""
    otro = en_grupo_bioquimicos(
        django_user_model.objects.create_user(
            email="otra-bioquimica@ejemplo.com", password="Clave-Valida-123", is_active=True
        )
    )
    en_grupo_bioquimicos(
        django_user_model.objects.create_user(
            email="bioquimico-inactivo@ejemplo.com", password="Clave-Valida-123", is_active=False
        )
    )
    administrador = django_user_model.objects.create_user(
        email="admin-aviso@ejemplo.com", password="Clave-Valida-123", is_active=True
    )
    administrador.groups.add(Group.objects.get_or_create(name="Administradores")[0])
    return sorted([bioquimico.email, otro.email])


def test_uno_por_desvio_y_por_bioquimico_activo(
    sin_cargar, empleado, destinatarios, mailoutbox, django_capture_on_commit_callbacks
):
    with django_capture_on_commit_callbacks(execute=True):
        cargar(sin_cargar, empleado, {"CL-": "16", "PH": "9.5"})  # los dos en desvío
    assert len(mailoutbox) == 4  # 2 desvíos × 2 bioquímicos activos
    enviados = sorted((m.subject.split(" – ")[0], *m.to) for m in mailoutbox)
    assert enviados == sorted(
        (asunto, email)
        for asunto in ["Desvío en Cloruro (CL-)", "Desvío en pH (PH)"]
        for email in destinatarios
    )
    for mensaje in mailoutbox:
        # Cada uno va solo a su destinatario: nadie ve las direcciones de los otros.
        assert len(mensaje.to) == 1
        assert mensaje.cc == [] and mensaje.bcc == []


def test_falla_con_un_destinatario_no_corta_a_los_otros(
    sin_cargar, empleado, destinatarios, mailoutbox, caplog, django_capture_on_commit_callbacks
):
    from config.correos import CorreoAquaLab

    enviar_real = CorreoAquaLab.send

    def send(mensaje, *args, **kwargs):
        if mensaje.to == [destinatarios[0]]:
            raise SMTPException("rechazado")
        return enviar_real(mensaje, *args, **kwargs)

    with mock.patch("config.correos.CorreoAquaLab.send", autospec=True, side_effect=send):
        with caplog.at_level(logging.ERROR, logger="estudios.notificaciones"):
            with django_capture_on_commit_callbacks(execute=True):
                cargar(sin_cargar, empleado, {"CL-": "16"})
    assert [m.to for m in mailoutbox] == [[destinatarios[1]]]
    assert "No se pudo enviar el aviso de desvío de Cloruro (CL-)" in caplog.text
    assert destinatarios[0] in caplog.text


def test_dependiente(
    origen,
    estudio_en_origen,
    pruebas_division,
    empleado,
    mailoutbox,
    django_capture_on_commit_callbacks,
):
    for n in range(3):
        previo = estudio_en_origen(
            origen, dia(n), 301001 + n, {"DIV-A": "20", "DIV-B": "2", "DIV": None}
        )
        validar(previo, en_grupo_bioquimicos(empleado), "DIV")
    actual = estudio_en_origen(origen, dia(3), 301010, {"DIV-A": None, "DIV-B": None, "DIV": None})
    with django_capture_on_commit_callbacks(execute=True):
        # DIV-A +10 % y DIV-B −20 % no se desvían; el cociente (13,75 contra 10) sí.
        cargar(actual, empleado, {"DIV-A": "22", "DIV-B": "1.6"})
    (mensaje,) = mailoutbox
    assert mensaje.subject.startswith("Desvío en Cociente (DIV)")
    assert "Valor observado: 13,75 u" in mensaje.body


def test_correccion_sigue_en_desvio(
    sin_cargar, empleado, bioquimico, mailoutbox, django_capture_on_commit_callbacks
):
    with django_capture_on_commit_callbacks(execute=True):
        cargar(sin_cargar, empleado, {"CL-": "16"})
    cl = asignacion_de(sin_cargar, "CL-")
    with django_capture_on_commit_callbacks(execute=True):
        corregir_mediciones(sin_cargar.pk, {cl.pk: (Decimal("16"), Decimal("20"))}, empleado)
    assert len(mailoutbox) == 2
    assert "Valor observado: 200 mg/l" in mailoutbox[1].body


def test_sin_desvio_no_envia(
    origen, sin_cargar, empleado, estudio_en_origen, mailoutbox, django_capture_on_commit_callbacks
):
    with django_capture_on_commit_callbacks(execute=True):
        cargar(sin_cargar, empleado, {"CL-": "14.3", "PH": "7.0"})
    nuevo = Origen.objects.create(cliente=origen.cliente, nombre="Pozo nuevo")
    with django_capture_on_commit_callbacks(execute=True):
        estudio_en_origen(nuevo, dia(0), 301020, {"CL-": "90"}, validar_todo=False)
    assert mailoutbox == []


def test_mismo_valor_no_reenvia(
    sin_cargar, empleado, bioquimico, mailoutbox, django_capture_on_commit_callbacks
):
    with django_capture_on_commit_callbacks(execute=True):
        cargar(sin_cargar, empleado, {"CL-": "16"})
    assert len(mailoutbox) == 1
    cl = asignacion_de(sin_cargar, "CL-")
    with django_capture_on_commit_callbacks(execute=True):
        with transaction.atomic():
            estudio = Estudio.objects.select_for_update().get(pk=sin_cargar.pk)
            calculo.recalcular(estudio, [cl])
        validar(sin_cargar, bioquimico, "CL-")
    assert len(mailoutbox) == 1


def test_contenido_y_enlace_absoluto(
    sin_cargar, empleado, bioquimico, mailoutbox, settings, django_capture_on_commit_callbacks
):
    settings.AQUALAB_URL_BASE = "https://aqualab.ejemplo.com/"
    with django_capture_on_commit_callbacks(execute=True):
        cargar(sin_cargar, empleado, {"CL-": "16"})
    (mensaje,) = mailoutbox
    muestra = sin_cargar.muestra
    assert mensaje.subject == f"Desvío en Cloruro (CL-) – muestra N° PI {muestra.numero_pi}"
    cuerpo = mensaje.body
    assert f"N° PI {muestra.numero_pi}" in cuerpo
    assert muestra.cliente.nombre_completo in cuerpo
    assert "Pozo del aviso" in cuerpo
    assert "Cloruro (CL-)" in cuerpo
    assert "Valor observado: 160 mg/l" in cuerpo
    assert "Mediana de los últimos 3: 110 mg/l" in cuerpo
    assert "▲ +50 mg/l (+45,5 %)" in cuerpo
    enlace = "https://aqualab.ejemplo.com" + reverse("estudios:detalle", args=[sin_cargar.pk])
    assert enlace in cuerpo
    assert "más de un 30 % respecto de la mediana" in cuerpo
    assert "&lt;" not in cuerpo and "&#x27;" not in cuerpo


def test_transaccion_fallida_no_envia(
    sin_cargar, empleado, bioquimico, mailoutbox, django_capture_on_commit_callbacks
):
    with django_capture_on_commit_callbacks(execute=True):
        with pytest.raises(RuntimeError), transaction.atomic():
            cargar(sin_cargar, empleado, {"CL-": "16"})
            raise RuntimeError("falla después de calcular")
    assert mailoutbox == []
    assert not Resultado.objects.filter(asignacion__estudio=sin_cargar).exists()


def test_falla_de_envio_queda_en_log(
    sin_cargar, empleado, bioquimico, mailoutbox, caplog, django_capture_on_commit_callbacks
):
    with mock.patch("config.correos.CorreoAquaLab.send", side_effect=SMTPException("sin servidor")):
        with caplog.at_level(logging.ERROR, logger="estudios.notificaciones"):
            with django_capture_on_commit_callbacks(execute=True):
                cargar(sin_cargar, empleado, {"CL-": "16"})
    assert "No se pudo enviar el aviso de desvío" in caplog.text
    cl = asignacion_de(sin_cargar, "CL-")
    assert Medicion.objects.filter(asignacion=cl).exists()
    assert Resultado.objects.get(asignacion=cl).valor == Decimal(160)


def test_sin_bioquimicos_activos(
    sin_cargar, django_user_model, mailoutbox, caplog, django_capture_on_commit_callbacks
):
    Group.objects.get(name="Bioquímicos").user_set.update(is_active=False)
    tecnico = django_user_model.objects.create_user(
        email="tecnico-aviso@ejemplo.com", password="Clave-Valida-123", is_active=True
    )
    with caplog.at_level(logging.WARNING, logger="estudios.notificaciones"):
        with django_capture_on_commit_callbacks(execute=True):
            cargar(sin_cargar, tecnico, {"CL-": "16"})
    assert mailoutbox == []
    assert "sin bioquímicos activos" in caplog.text


def test_html_con_logo(
    sin_cargar, empleado, bioquimico, mailoutbox, settings, django_capture_on_commit_callbacks
):
    from config.tests.utiles_correos import comprobar_html_con_logo

    settings.AQUALAB_URL_BASE = "https://aqualab.ejemplo.com"
    with django_capture_on_commit_callbacks(execute=True):
        cargar(sin_cargar, empleado, {"CL-": "16"})
    (mensaje,) = mailoutbox
    html = comprobar_html_con_logo(mensaje)
    enlace = "https://aqualab.ejemplo.com" + reverse("estudios:detalle", args=[sin_cargar.pk])
    assert f'href="{enlace}"' in html
    assert "Cloruro (CL-)" in html and "160 mg/l" in html and "110 mg/l" in html
    # El texto plano sigue siendo texto: sin etiquetas HTML.
    assert "<" not in mensaje.body.replace("<AQUALAB", "")
    assert mensaje.body.startswith("Hola:\n\nSe calculó un resultado")
