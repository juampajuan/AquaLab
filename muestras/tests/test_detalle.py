import uuid

import pytest
from django.conf import settings
from django.urls import reverse

from estudios.models import (
    EstadoEstudio,
    EstadoPruebaEstudio,
    Estudio,
    PruebaEstudio,
    TipoEstudio,
)
from estudios.servicios import crear_estudio
from muestras.models import Origen, TipoVertido
from pruebas.models import Prueba

pytestmark = pytest.mark.django_db


@pytest.fixture
def catalogo_pruebas():
    p1 = Prueba.objects.create(codigo="PH", nombre="Potencial de hidrógeno")
    p2 = Prueba.objects.create(codigo="ALC", nombre="Alcalinidad total")
    p3 = Prueba.objects.create(codigo="COL", nombre="Coliformes totales")
    tipo_fq = TipoEstudio.objects.create(
        nombre="Físico-Químico",
        descripcion="Análisis físico-químico estándar",
    )
    tipo_fq.pruebas.set([p1, p2])
    tipo_bac = TipoEstudio.objects.create(
        nombre="Bacteriológico",
        descripcion="Control microbiológico",
    )
    tipo_bac.pruebas.set([p3])
    return {
        "pruebas": (p1, p2, p3),
        "tipo_fq": tipo_fq,
        "tipo_bac": tipo_bac,
    }


def test_ficha_muestra_exhibe_todos_los_datos_vigentes(
    cliente_autenticado, crear_muestra, empleado
):
    muestra = crear_muestra(
        200001,
        nombre="Pozo N°2 Octubre",
        sitio_extraccion="Planta Luján – canilla sala de elaboración",
        tipo_vertido=TipoVertido.CLOACAL,
        responsable_muestreo="J. Pérez",
    )
    resp = cliente_autenticado.get(reverse("muestras:detalle", args=[muestra.pk]))
    assert resp.status_code == 200
    html = resp.content.decode()

    assert "200001" in html
    assert "Pozo N°2 Octubre" in html
    assert "Ingresada" in html
    assert "Aguas del Sur S.A." in html
    assert "CUIT 20123456786" in html
    assert "contacto@aguassur.com" in html
    assert "Pozo N°2" in html
    assert "Planta Luján – canilla sala de elaboración" in html
    assert "Cloacal" in html
    assert "J. Pérez" in html
    assert "Laura Martínez" in html
    assert muestra.fecha_muestreo.strftime("%d/%m/%Y") in html
    assert muestra.fecha_ingreso.strftime("%d/%m/%Y") in html


@pytest.mark.parametrize(
    ("tipo_vertido", "etiqueta"),
    [
        (TipoVertido.AGUA, "Agua"),
        (TipoVertido.CLOACAL, "Cloacal"),
        (TipoVertido.CANAL, "Canal"),
    ],
)
def test_ficha_muestra_muestra_tipo_de_vertido(
    cliente_autenticado, crear_muestra, tipo_vertido, etiqueta
):
    muestra = crear_muestra(200001, tipo_vertido=tipo_vertido)
    resp = cliente_autenticado.get(reverse("muestras:detalle", args=[muestra.pk]))
    assert resp.status_code == 200
    assert etiqueta in resp.content.decode()


def test_ficha_muestra_lista_estudios_asignados_con_estado_y_avance(
    cliente_autenticado, crear_muestra, empleado, catalogo_pruebas
):
    muestra = crear_muestra(200001)
    tipo_fq = catalogo_pruebas["tipo_fq"]
    tipo_bac = catalogo_pruebas["tipo_bac"]
    p1, _, _ = catalogo_pruebas["pruebas"]

    estudio_1 = crear_estudio(
        {
            "clave": str(uuid.uuid4()),
            "muestra": muestra.pk,
            "tipo": tipo_fq.pk,
            "version": tipo_fq.version,
        },
        empleado,
    )
    Estudio.objects.filter(pk=estudio_1.pk).update(estado=EstadoEstudio.EN_PROCESO)
    PruebaEstudio.objects.filter(estudio=estudio_1, prueba=p1).update(
        estado=EstadoPruebaEstudio.COMPLETADA
    )

    estudio_2 = crear_estudio(
        {
            "clave": str(uuid.uuid4()),
            "muestra": muestra.pk,
            "tipo": tipo_bac.pk,
            "version": tipo_bac.version,
        },
        empleado,
    )
    Estudio.objects.filter(pk=estudio_2.pk).update(estado=EstadoEstudio.FINALIZADO)
    PruebaEstudio.objects.filter(estudio=estudio_2).update(estado=EstadoPruebaEstudio.COMPLETADA)

    resp = cliente_autenticado.get(reverse("muestras:detalle", args=[muestra.pk]))
    assert resp.status_code == 200
    estudios_ctx = list(resp.context["estudios"])
    assert [e.pk for e in estudios_ctx] == [estudio_2.pk, estudio_1.pk]
    assert estudios_ctx[0].pruebas_completadas == 1
    assert estudios_ctx[0].total_pruebas == 1
    assert estudios_ctx[1].pruebas_completadas == 1
    assert estudios_ctx[1].total_pruebas == 2

    html = resp.content.decode()
    assert f"#{estudio_1.pk}" in html
    assert f"#{estudio_2.pk}" in html
    assert "Físico-Químico" in html
    assert "Bacteriológico" in html
    assert "En proceso" in html
    assert "Finalizado" in html
    assert "1 / 2" in html
    assert "1 / 1" in html
    assert reverse("estudios:detalle", args=[estudio_1.pk]) in html
    assert reverse("estudios:detalle", args=[estudio_2.pk]) in html


def test_ficha_muestra_sin_estudios_informa_y_ofrece_crear(cliente_autenticado, crear_muestra):
    muestra = crear_muestra(200001)
    resp = cliente_autenticado.get(reverse("muestras:detalle", args=[muestra.pk]))
    assert resp.status_code == 200
    html = resp.content.decode()
    assert "Esta muestra aún no tiene estudios asignados." in html
    assert reverse("estudios:crear") in html


def test_navegacion_cruzada_entre_estudio_y_ficha_de_muestra(
    cliente_autenticado, crear_muestra, empleado, catalogo_pruebas
):
    muestra = crear_muestra(200001)
    tipo_fq = catalogo_pruebas["tipo_fq"]
    estudio = crear_estudio(
        {
            "clave": str(uuid.uuid4()),
            "muestra": muestra.pk,
            "tipo": tipo_fq.pk,
            "version": tipo_fq.version,
        },
        empleado,
    )

    url_muestra = reverse("muestras:detalle", args=[muestra.pk])
    url_estudio = reverse("estudios:detalle", args=[estudio.pk])

    resp_estudio = cliente_autenticado.get(url_estudio)
    assert resp_estudio.status_code == 200
    assert url_muestra in resp_estudio.content.decode()

    resp_busqueda = cliente_autenticado.get(reverse("estudios:buscar"), {"q": "200001"})
    assert resp_busqueda.status_code == 200
    assert url_muestra in resp_busqueda.content.decode()

    resp_muestra = cliente_autenticado.get(url_muestra)
    assert resp_muestra.status_code == 200
    assert url_estudio in resp_muestra.content.decode()


def test_ficha_muestra_sin_responsable_y_con_cliente_inactivo(
    cliente_autenticado, cliente_inactivo, empleado, hoy
):
    origen = Origen.objects.create(cliente=cliente_inactivo, nombre="Pozo Histórico")
    muestra = cliente_inactivo.muestras.create(
        numero_pi=200005,
        nombre="Muestra Histórica",
        origen=origen,
        fecha_muestreo=hoy,
        fecha_ingreso=hoy,
        sitio_extraccion="Toma antigua",
        responsable_muestreo="",
        registrada_por=empleado,
    )
    resp = cliente_autenticado.get(reverse("muestras:detalle", args=[muestra.pk]))
    assert resp.status_code == 200
    html = resp.content.decode()
    assert "No especificado" in html
    assert "Cooperativa Río Claro" in html
    assert reverse("clientes:detalle", args=[cliente_inactivo.pk]) not in html


def test_ficha_muestra_requiere_sesion_y_valida_existencia(
    client, cliente_autenticado, crear_muestra
):
    muestra = crear_muestra(200001)
    url = reverse("muestras:detalle", args=[muestra.pk])

    resp_anon = client.get(url)
    assert resp_anon.status_code == 302
    assert reverse(settings.LOGIN_URL) in resp_anon["Location"]

    resp_404 = cliente_autenticado.get(reverse("muestras:detalle", args=[999999]))
    assert resp_404.status_code == 404
