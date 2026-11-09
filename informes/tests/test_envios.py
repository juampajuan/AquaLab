"""Envío del informe por correo (SCRUM-79)."""

import re
import uuid

import pytest
from django.conf import settings
from django.urls import reverse

from clientes.models import Cliente
from estudios.tests.utiles import cargar, validar
from informes.models import EnvioInforme, Informe, ResultadoEnvio
from informes.servicios import emitir_informe

pytestmark = pytest.mark.django_db

PDF_FALSO = b"%PDF-falso"


@pytest.fixture
def informe(estudio_de, empleado, bioquimico):
    estudio = estudio_de("PH")
    cargar(estudio, empleado, PH="7.4")
    validar(estudio, bioquimico, "PH")
    return emitir_informe(estudio.pk, bioquimico)


@pytest.fixture
def pdf_falso(monkeypatch):
    """Reemplaza el PDF de WeasyPrint; guarda los informes con los que se lo llamó."""
    llamados = []

    def generar(informe):
        llamados.append(informe)
        return PDF_FALSO

    monkeypatch.setattr("informes.envios.generar_pdf", generar)
    return llamados


def url_enviar(informe):
    return reverse("informes:enviar", args=[informe.estudio.pk])


def url_ver(informe):
    return reverse("informes:ver", args=[informe.estudio.pk])


def enviar(cliente, informe, clave=None, **extra):
    return cliente.post(url_enviar(informe), {"clave": str(clave or uuid.uuid4())}, **extra)


def correo_del_cliente(informe):
    return informe.estudio.muestra.cliente.email


# --- US1: enviar el informe al cliente ---------------------------------------------------------


def test_confirmacion_muestra_datos_y_no_envia(cliente_bioquimico, informe, mailoutbox):
    resp = cliente_bioquimico.get(url_enviar(informe))

    assert resp.status_code == 200
    html = resp.content.decode()
    numero, email = informe.numero_mostrado, correo_del_cliente(informe)
    assert f"Se enviará el informe {numero} por correo a {email}, con el PDF adjunto." in html
    assert informe.estudio.muestra.cliente.nombre_completo in html
    assert "Nunca se envió" in html
    clave = re.search(r'<input type="hidden" name="clave" value="([^"]+)"', html).group(1)
    uuid.UUID(clave)
    assert "Enviar informe" in html
    assert re.search(rf'<a href="{re.escape(url_ver(informe))}"[^>]*>\s*Cancelar', html)
    assert mailoutbox == []
    assert not EnvioInforme.objects.exists()

    otra = cliente_bioquimico.get(url_enviar(informe)).content.decode()
    assert f'value="{clave}"' not in otra


def test_envia_con_pdf_adjunto(cliente_bioquimico, informe, mailoutbox, pdf_falso):
    resp = enviar(cliente_bioquimico, informe)

    assert resp.status_code == 302
    assert resp.url == url_ver(informe)
    assert len(mailoutbox) == 1
    correo = mailoutbox[0]
    assert correo.to == [correo_del_cliente(informe)]
    assert correo.from_email == settings.DEFAULT_FROM_EMAIL
    assert correo.attachments == [(f"{informe.numero_mostrado}.pdf", PDF_FALSO, "application/pdf")]
    assert pdf_falso == [informe]

    pagina = cliente_bioquimico.get(resp.url).content.decode()
    assert (
        f"Se envió el informe {informe.numero_mostrado} a {correo_del_cliente(informe)}." in pagina
    )


def test_cancelar_no_envia(cliente_bioquimico, informe, mailoutbox):
    html = cliente_bioquimico.get(url_enviar(informe)).content.decode()
    cancelar = re.search(r'<a href="([^"]+)"[^>]*>\s*Cancelar', html).group(1)

    assert cancelar == url_ver(informe)
    assert cliente_bioquimico.get(cancelar).status_code == 200
    assert mailoutbox == []
    assert not EnvioInforme.objects.exists()


def test_contenido_del_correo(cliente_bioquimico, informe, mailoutbox, pdf_falso):
    enviar(cliente_bioquimico, informe)

    correo = mailoutbox[0]
    estudio, muestra = informe.estudio, informe.estudio.muestra
    assert correo.subject == f"Informe {informe.numero_mostrado} – AquaLab"
    cuerpo = correo.body
    assert f"Hola, {muestra.cliente.nombre_completo}:" in cuerpo
    assert (
        f"Le enviamos el informe {informe.numero_mostrado} del estudio N° {estudio.pk} "
        f"({estudio.tipo_nombre_snapshot}) de la muestra N° PI {muestra.numero_pi} "
        f"({muestra.nombre})."
    ) in " ".join(cuerpo.split())
    assert "El informe está adjunto en PDF." in cuerpo
    assert settings.AQUALAB_LABORATORIO["nombre"] in cuerpo
    for prohibido in ("http://", "https://", "contraseña", "&amp;", "&#"):
        assert prohibido not in cuerpo


def test_enviar_no_modifica_informe(cliente_bioquimico, informe, mailoutbox, pdf_falso):
    antes = Informe.objects.values("numero", "contenido", "fecha_emision").get(pk=informe.pk)
    estado = informe.estudio.estado

    enviar(cliente_bioquimico, informe)

    assert (
        Informe.objects.values("numero", "contenido", "fecha_emision").get(pk=informe.pk) == antes
    )
    informe.estudio.refresh_from_db()
    assert informe.estudio.estado == estado


def test_usa_correo_actual_del_cliente(cliente_bioquimico, informe, mailoutbox, pdf_falso):
    cliente = informe.estudio.muestra.cliente
    Cliente.objects.filter(pk=cliente.pk).update(email="nuevo@ejemplo.com")

    assert "nuevo@ejemplo.com" in cliente_bioquimico.get(url_enviar(informe)).content.decode()
    enviar(cliente_bioquimico, informe)

    assert mailoutbox[0].to == ["nuevo@ejemplo.com"]
    assert EnvioInforme.objects.get().destinatario == "nuevo@ejemplo.com"


def test_cliente_inactivo(cliente_bioquimico, informe, mailoutbox, pdf_falso):
    Cliente.objects.filter(pk=informe.estudio.muestra.cliente.pk).update(activo=False)

    assert cliente_bioquimico.get(url_enviar(informe)).status_code == 200
    enviar(cliente_bioquimico, informe)

    assert len(mailoutbox) == 1


def test_informe_sin_firma(cliente_bioquimico, informe, mailoutbox, pdf_falso):
    contenido = {k: v for k, v in informe.contenido.items() if k != "firma"}
    Informe.objects.filter(pk=informe.pk).update(contenido=contenido)

    enviar(cliente_bioquimico, informe)

    assert len(mailoutbox) == 1
    assert EnvioInforme.objects.get().resultado == ResultadoEnvio.ENVIADO


def test_adjunto_es_pdf_real(cliente_bioquimico, informe, mailoutbox):
    enviar(cliente_bioquimico, informe)

    nombre, contenido, tipo = mailoutbox[0].attachments[0]
    assert nombre == f"{informe.numero_mostrado}.pdf"
    assert tipo == "application/pdf"
    assert contenido.startswith(b"%PDF")


def test_confirmacion_usa_componentes(cliente_bioquimico, informe):
    html = cliente_bioquimico.get(url_enviar(informe)).content.decode()

    assert 'data-componente="resumen"' in html
    assert 'data-componente="acciones-confirmacion"' in html
    assert "Enviar informe por correo" in html


# --- US2: historial de envíos ------------------------------------------------------------------


def test_registra_envio(cliente_bioquimico, informe, bioquimico, mailoutbox, pdf_falso):
    clave = uuid.uuid4()

    enviar(cliente_bioquimico, informe, clave)

    envio = EnvioInforme.objects.get()
    assert envio.informe == informe
    assert envio.enviado_por == bioquimico
    assert envio.destinatario == correo_del_cliente(informe)
    assert envio.resultado == ResultadoEnvio.ENVIADO
    assert envio.clave == clave
    assert envio.fecha is not None


def test_reenvio_muestra_ultimo_envio(
    cliente_bioquimico, informe, bioquimico, mailoutbox, pdf_falso
):
    from django.utils import timezone

    enviar(cliente_bioquimico, informe)
    exitoso = EnvioInforme.objects.get()
    EnvioInforme.objects.create(
        informe=informe,
        enviado_por=bioquimico,
        destinatario="fallido@ejemplo.com",
        resultado=ResultadoEnvio.FALLIDO,
        clave=uuid.uuid4(),
    )

    html = cliente_bioquimico.get(url_enviar(informe)).content.decode()
    fecha = timezone.localtime(exitoso.fecha).strftime("%d/%m/%Y %H:%M")
    assert f"{fecha} a {exitoso.destinatario}" in html
    assert "fallido@ejemplo.com" not in html
    assert "Nunca se envió" not in html

    enviar(cliente_bioquimico, informe)
    assert len(mailoutbox) == 2
    assert EnvioInforme.objects.filter(resultado=ResultadoEnvio.ENVIADO).count() == 2


# --- US3: fallas y casos que impiden el envío --------------------------------------------------


def test_falla_de_correo(cliente_bioquimico, informe, mailoutbox, pdf_falso, monkeypatch, caplog):
    from smtplib import SMTPException

    def caido(self, fail_silently=False):
        raise SMTPException("caído")

    monkeypatch.setattr("django.core.mail.EmailMessage.send", caido)

    with caplog.at_level("ERROR", logger="informes.envios"):
        resp = enviar(cliente_bioquimico, informe, follow=True)

    assert resp.redirect_chain == [(url_ver(informe), 302)]
    email = correo_del_cliente(informe)
    assert f"No se pudo enviar el informe a {email}. Intentá nuevamente." in resp.content.decode()
    assert EnvioInforme.objects.get().resultado == ResultadoEnvio.FALLIDO
    assert mailoutbox == []
    registro = next(r for r in caplog.records if r.name == "informes.envios")
    assert registro.levelname == "ERROR"
    assert informe.numero_mostrado in registro.getMessage()


def test_falla_de_pdf(cliente_bioquimico, informe, mailoutbox, monkeypatch, caplog):
    def roto(informe):
        raise RuntimeError("WeasyPrint")

    monkeypatch.setattr("informes.envios.generar_pdf", roto)

    with caplog.at_level("ERROR", logger="informes.envios"):
        resp = enviar(cliente_bioquimico, informe, follow=True)

    assert resp.status_code == 200
    assert "No se pudo enviar el informe a" in resp.content.decode()
    assert EnvioInforme.objects.get().resultado == ResultadoEnvio.FALLIDO
    assert mailoutbox == []
    assert any(r.name == "informes.envios" for r in caplog.records)


@pytest.mark.parametrize("metodo", ["get", "post"])
def test_sin_permiso(cliente_comun, informe, mailoutbox, pdf_falso, metodo):
    resp = getattr(cliente_comun, metodo)(url_enviar(informe), {"clave": str(uuid.uuid4())})

    assert resp.status_code == 403
    assert mailoutbox == []
    assert not EnvioInforme.objects.exists()


def test_servicio_revalida_permiso(informe, django_user_model, mailoutbox, pdf_falso):
    from django.core.exceptions import PermissionDenied

    from informes import envios

    comun = django_user_model.objects.create_user(
        email="comun-servicio-envio@ejemplo.com", password="Clave-Valida-123", is_active=True
    )
    with pytest.raises(PermissionDenied):
        envios.enviar_informe(informe.estudio.pk, comun, uuid.uuid4())

    assert mailoutbox == []
    assert not EnvioInforme.objects.exists()


@pytest.mark.parametrize("metodo", ["get", "post"])
def test_sin_informe_404(cliente_bioquimico, estudio_de, mailoutbox, metodo):
    estudio = estudio_de("PH")

    resp = getattr(cliente_bioquimico, metodo)(
        reverse("informes:enviar", args=[estudio.pk]), {"clave": str(uuid.uuid4())}
    )

    assert resp.status_code == 404
    assert mailoutbox == []


def test_misma_clave_no_reenvia(cliente_bioquimico, informe, mailoutbox, pdf_falso):
    clave = uuid.uuid4()

    enviar(cliente_bioquimico, informe, clave)
    resp = enviar(cliente_bioquimico, informe, clave, follow=True)

    assert len(mailoutbox) == 1
    assert EnvioInforme.objects.count() == 1
    assert (
        f"El informe {informe.numero_mostrado} ya se había enviado con esta confirmación."
        in resp.content.decode()
    )


@pytest.mark.parametrize("datos", [{}, {"clave": "x"}])
def test_clave_invalida(cliente_bioquimico, informe, mailoutbox, pdf_falso, datos):
    resp = cliente_bioquimico.post(url_enviar(informe), datos, follow=True)

    assert resp.redirect_chain == [(url_enviar(informe), 302)]
    assert "La confirmación no es válida. Volvé a intentarlo." in resp.content.decode()
    assert mailoutbox == []
    assert not EnvioInforme.objects.exists()


def test_error_de_base(cliente_bioquimico, informe, mailoutbox, monkeypatch):
    from django.db import DatabaseError

    def caida(*args, **kwargs):
        raise DatabaseError("sin base")

    monkeypatch.setattr("informes.envios.enviar_informe", caida)

    resp = enviar(cliente_bioquimico, informe, follow=True)

    assert resp.redirect_chain == [(url_ver(informe), 302)]
    assert "No se pudo registrar el envío. Intentá nuevamente." in resp.content.decode()
