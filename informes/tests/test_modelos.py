import base64

import pytest
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError

from informes.models import FirmaProfesional, Informe

from .utiles import png

pytestmark = pytest.mark.django_db


def crear(estudio, usuario, numero=1):
    return Informe.objects.create(
        numero=numero, estudio=estudio, emitido_por=usuario, contenido={"pruebas": []}
    )


@pytest.mark.parametrize(("numero", "texto"), [(1, "INF-000001"), (123, "INF-000123")])
def test_numero_mostrado(numero, texto):
    assert Informe(numero=numero).numero_mostrado == texto


def test_un_informe_por_estudio(estudio_de, empleado):
    estudio = estudio_de("PH")
    crear(estudio, empleado)
    with pytest.raises(IntegrityError), transaction.atomic():
        crear(estudio, empleado, numero=2)


def test_numero_unico(estudio_de, empleado):
    crear(estudio_de("PH"), empleado)
    with pytest.raises(IntegrityError), transaction.atomic():
        crear(estudio_de("CL-"), empleado)


def test_numero_positivo(estudio_de, empleado):
    with pytest.raises(IntegrityError), transaction.atomic():
        crear(estudio_de("PH"), empleado, numero=0)


def test_estudio_con_informe_protegido(estudio_de, empleado):
    estudio = estudio_de("PH")
    crear(estudio, empleado)
    with pytest.raises(ProtectedError), transaction.atomic():
        estudio.delete()


def test_firma_data_url(empleado):
    datos = png()
    firma = FirmaProfesional.objects.create(usuario=empleado, imagen=datos, matricula="MP 1")
    firma.refresh_from_db()
    prefijo = "data:image/png;base64,"
    assert firma.data_url.startswith(prefijo)
    assert base64.b64decode(firma.data_url[len(prefijo) :]) == datos


def test_una_firma_por_usuario(empleado):
    FirmaProfesional.objects.create(usuario=empleado, imagen=png(), matricula="MP 1")
    with pytest.raises(IntegrityError), transaction.atomic():
        FirmaProfesional.objects.create(usuario=empleado, imagen=png(), matricula="MP 2")


def test_informe_no_registrado_en_admin(estudio_de, empleado, django_user_model):
    from django.contrib import admin
    from django.test import Client

    assert Informe not in admin.site._registry
    informe = crear(estudio_de("PH"), empleado)
    admin_user = django_user_model.objects.create_superuser("admin-us73@ejemplo.com", "Clave-123!")
    c = Client()
    c.force_login(admin_user)
    assert c.get("/admin/informes/informe/").status_code == 404
    assert c.get(f"/admin/informes/informe/{informe.pk}/change/").status_code == 404


def test_informe_no_se_modifica(estudio_de, empleado):
    informe = crear(estudio_de("PH"), empleado)
    informe.contenido = {"pruebas": ["cambiado"]}
    with pytest.raises(ValueError, match="Un informe emitido no se puede modificar."):
        informe.save()
    assert Informe.objects.get(pk=informe.pk).contenido == {"pruebas": []}


def test_informe_no_se_borra(estudio_de, empleado):
    informe = crear(estudio_de("PH"), empleado)
    with pytest.raises(ValueError, match="Un informe emitido no se puede borrar."):
        informe.delete()
    assert Informe.objects.filter(pk=informe.pk).exists()


def test_no_se_borran_estudio_muestra_ni_cliente(estudio_de, empleado):
    estudio = estudio_de("PH")
    crear(estudio, empleado)
    muestra = estudio.muestra
    for objeto in (estudio, muestra, muestra.cliente):
        with pytest.raises(ProtectedError), transaction.atomic():
            objeto.delete()


def test_envio_no_se_modifica_ni_borra(estudio_de, empleado):
    """SCRUM-79 (FR-005): el historial de envíos no se edita ni se borra, y no está en el admin."""
    import uuid

    from django.contrib import admin

    from informes.models import EnvioInforme, ResultadoEnvio

    informe = crear(estudio_de("PH"), empleado)
    envio = EnvioInforme.objects.create(
        informe=informe,
        enviado_por=empleado,
        destinatario="cliente@ejemplo.com",
        resultado=ResultadoEnvio.ENVIADO,
        clave=uuid.uuid4(),
    )

    envio.destinatario = "otro@ejemplo.com"
    with pytest.raises(ValueError, match="Un envío de informe no se puede modificar."):
        envio.save()
    with pytest.raises(ValueError, match="Un envío de informe no se puede borrar."):
        envio.delete()
    assert EnvioInforme.objects.get(pk=envio.pk).destinatario == "cliente@ejemplo.com"
    assert not admin.site.is_registered(EnvioInforme)
    with pytest.raises(IntegrityError), transaction.atomic():
        EnvioInforme.objects.create(
            informe=informe,
            enviado_por=empleado,
            destinatario="cliente@ejemplo.com",
            resultado=ResultadoEnvio.FALLIDO,
            clave=envio.clave,
        )
    # Aunque se saltee Informe.delete(), el FK PROTECT impide borrar un informe con envíos.
    with pytest.raises(ProtectedError):
        super(Informe, informe).delete()
