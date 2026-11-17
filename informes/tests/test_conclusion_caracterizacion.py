import copy
import uuid

import pytest
from django.contrib.auth.models import Permission
from django.urls import reverse

from estudios.models import Resultado, Validacion
from estudios.tests.utiles import cargar, validar
from informes.contenido import armar_contenido
from informes.envios import enviar_informe
from informes.models import Informe
from informes.pdf import generar_pdf
from informes.servicios import EmitirInformeError, InformeNoDisponible, emitir_informe

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def sin_ia(monkeypatch):
    def prohibido(*args, **kwargs):
        pytest.fail("La caracterización no debe llamar al servicio de IA.")

    monkeypatch.setattr("asistente.cliente_ia.enviar", prohibido)


@pytest.fixture
def listo(estudio_de, empleado, bioquimico):
    estudio = estudio_de("PH", "CL-")
    cargar(estudio, empleado, PH="7.4", CL_="40")
    validar(estudio, bioquimico, "PH", "CL-")
    return estudio


def escalares(valor):
    if isinstance(valor, dict):
        for hijo in valor.values():
            yield from escalares(hijo)
    elif isinstance(valor, list):
        for hijo in valor:
            yield from escalares(hijo)
    else:
        yield valor


def test_previa_general_no_escribe(cliente_comun, listo):
    resultados = list(Resultado.objects.values())
    validaciones = list(Validacion.objects.values())
    respuesta = cliente_comun.get(reverse("informes:vista_previa", args=[listo.pk]))
    assert respuesta.status_code == 200
    assert "BORRADOR" in respuesta.content.decode()
    assert list(Resultado.objects.values()) == resultados
    assert list(Validacion.objects.values()) == validaciones
    assert not Informe.objects.exists()


def test_permiso_directo_emite_sin_grupo(listo, django_user_model, firma_de):
    usuario = django_user_model.objects.create_user(
        email="emisor-caracterizacion@ejemplo.com", is_active=True
    )
    usuario.user_permissions.add(
        Permission.objects.get(content_type__app_label="informes", codename="emitir_informes")
    )
    firma_de(usuario)
    assert not usuario.groups.exists()
    informe = emitir_informe(listo.pk, usuario)
    assert informe.emitido_por == usuario
    assert "conclusion" not in informe.contenido


def test_emision_exige_firma_y_matricula(listo, django_user_model):
    usuario = django_user_model.objects.create_user(email="sin-firma@ejemplo.com", is_active=True)
    usuario.user_permissions.add(
        Permission.objects.get(content_type__app_label="informes", codename="emitir_informes")
    )
    with pytest.raises(EmitirInformeError, match="firma y matrícula"):
        emitir_informe(listo.pk, usuario)
    assert not Informe.objects.exists()


def test_no_emite_estudio_incompleto(estudio_de, bioquimico):
    estudio = estudio_de("PH")
    with pytest.raises(InformeNoDisponible, match="sin completar"):
        emitir_informe(estudio.pk, bioquimico)
    assert not Informe.objects.exists()


def test_contenido_de_solo_textos(listo, bioquimico):
    contenido = armar_contenido(listo, bioquimico)
    assert "conclusion" not in contenido
    assert all(isinstance(valor, str) for valor in escalares(contenido))
    prueba = next(p for p in contenido["pruebas"] if p["codigo"] == "CL-")
    assert prueba["resultado"] == "400.0000000000"
    assert prueba["evaluacion"] == "fuera_de_norma"


def test_copia_historica_inmutable(listo, bioquimico, cliente_comun):
    informe = emitir_informe(listo.pk, bioquimico)
    contenido = copy.deepcopy(informe.contenido)
    listo.muestra.cliente.nombre = "Nombre posterior sintético"
    listo.muestra.cliente.save()
    for nombre in ("informes:ver", "informes:imprimir"):
        respuesta = cliente_comun.get(reverse(nombre, args=[listo.pk]))
        assert respuesta.status_code == 200
        assert respuesta.context["contenido"] == contenido
    informe.refresh_from_db()
    assert informe.contenido == contenido
    assert "conclusion" not in contenido
    with pytest.raises(ValueError):
        informe.save()


def test_pdf_real_desde_copia(listo, bioquimico):
    informe = emitir_informe(listo.pk, bioquimico)
    anterior = copy.deepcopy(informe.contenido)
    assert generar_pdf(informe).startswith(b"%PDF-")
    informe.refresh_from_db()
    assert informe.contenido == anterior


def test_correo_confirmacion_destinatario_e_idempotencia(
    listo, bioquimico, cliente_bioquimico, mailoutbox, monkeypatch
):
    informe = emitir_informe(listo.pk, bioquimico)
    copia = copy.deepcopy(informe.contenido)
    respuesta = cliente_bioquimico.get(reverse("informes:enviar", args=[listo.pk]))
    assert respuesta.status_code == 200
    assert not mailoutbox
    cliente = listo.muestra.cliente
    cliente.email = "destino-sintetico@ejemplo.com"
    cliente.save()
    pdf = b"%PDF-sintetico-caracterizacion"
    monkeypatch.setattr("informes.envios.generar_pdf", lambda informe: pdf)
    clave = uuid.uuid4()
    primero = enviar_informe(listo.pk, bioquimico, clave)
    segundo = enviar_informe(listo.pk, bioquimico, clave)
    assert not primero.duplicado
    assert segundo.duplicado
    assert len(mailoutbox) == 1
    correo = mailoutbox[0]
    assert correo.to == [cliente.email]
    assert informe.numero_mostrado in correo.body
    assert any(alternativa.mimetype == "text/html" for alternativa in correo.alternatives)
    assert correo.attachments == [(f"{informe.numero_mostrado}.pdf", pdf, "application/pdf")]
    informe.refresh_from_db()
    assert informe.contenido == copia
