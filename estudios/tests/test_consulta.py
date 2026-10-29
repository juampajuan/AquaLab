import uuid

import pytest
from django.conf import settings
from django.urls import reverse
from django.utils import timezone

from clientes.models import Cliente
from estudios.models import (
    EstadoEstudio,
    EstadoPruebaEstudio,
    Estudio,
    PruebaEstudio,
    TipoEstudio,
)
from estudios.servicios import crear_estudio
from muestras.models import Muestra, Origen
from pruebas.models import Prueba

pytestmark = pytest.mark.django_db


@pytest.fixture
def escenario_consulta(empleado):
    cliente_persona = Cliente.objects.create(
        nombre="Juan Pérez",
        tipo_documento="DNI",
        numero_documento="30123456",
        email="juan.perez@ejemplo.com",
    )
    cliente_empresa = Cliente.objects.create(
        razon_social="Aguas del Sur S.A.",
        tipo_documento="CUIT",
        numero_documento="20123456786",
        email="contacto@aguasdelsur.com",
    )

    origen_pozo = Origen.objects.create(cliente=cliente_persona, nombre="Pozo Sur")
    origen_cisterna = Origen.objects.create(cliente=cliente_empresa, nombre="Cisterna Norte")

    hoy = timezone.localdate()
    muestra_pozo = Muestra.objects.create(
        numero_pi=200101,
        nombre="Pozo Sur Octubre",
        cliente=cliente_persona,
        origen=origen_pozo,
        fecha_muestreo=hoy,
        fecha_ingreso=hoy,
        sitio_extraccion="Canilla de sala de elaboración",
        registrada_por=empleado,
    )
    muestra_planta = Muestra.objects.create(
        numero_pi=200102,
        nombre="Cisterna Central",
        cliente=cliente_empresa,
        origen=origen_cisterna,
        fecha_muestreo=hoy,
        fecha_ingreso=hoy,
        sitio_extraccion="Salida de tanque principal",
        registrada_por=empleado,
    )

    prueba_ph = Prueba.objects.create(codigo="PH", nombre="Potencial de hidrógeno")
    prueba_alc = Prueba.objects.create(codigo="ALC", nombre="Alcalinidad total")
    prueba_no3 = Prueba.objects.create(codigo="NO3", nombre="Nitratos")

    tipo_fq = TipoEstudio.objects.create(
        nombre="Físico-Químico",
        descripcion="Análisis físico-químico general de agua",
    )
    tipo_fq.pruebas.set([prueba_ph, prueba_alc, prueba_no3])

    tipo_basico = TipoEstudio.objects.create(
        nombre="Control Básico",
        descripcion="",
    )
    tipo_basico.pruebas.set([prueba_ph, prueba_alc])

    estudio_pendiente = crear_estudio(
        {
            "clave": str(uuid.uuid4()),
            "muestra": muestra_pozo.pk,
            "tipo": tipo_basico.pk,
            "version": tipo_basico.version,
        },
        empleado,
    )

    estudio_en_proceso = crear_estudio(
        {
            "clave": str(uuid.uuid4()),
            "muestra": muestra_pozo.pk,
            "tipo": tipo_fq.pk,
            "version": tipo_fq.version,
        },
        empleado,
    )
    Estudio.objects.filter(pk=estudio_en_proceso.pk).update(estado=EstadoEstudio.EN_PROCESO)
    estudio_en_proceso.refresh_from_db()
    PruebaEstudio.objects.filter(estudio=estudio_en_proceso, prueba=prueba_alc).update(
        estado=EstadoPruebaEstudio.CARGADA
    )
    PruebaEstudio.objects.filter(estudio=estudio_en_proceso, prueba=prueba_no3).update(
        estado=EstadoPruebaEstudio.COMPLETADA
    )

    estudio_finalizado = crear_estudio(
        {
            "clave": str(uuid.uuid4()),
            "muestra": muestra_planta.pk,
            "tipo": tipo_basico.pk,
            "version": tipo_basico.version,
        },
        empleado,
    )
    Estudio.objects.filter(pk=estudio_finalizado.pk).update(estado=EstadoEstudio.FINALIZADO)
    estudio_finalizado.refresh_from_db()
    PruebaEstudio.objects.filter(estudio=estudio_finalizado).update(
        estado=EstadoPruebaEstudio.COMPLETADA
    )

    estudio_informado = crear_estudio(
        {
            "clave": str(uuid.uuid4()),
            "muestra": muestra_planta.pk,
            "tipo": tipo_fq.pk,
            "version": tipo_fq.version,
        },
        empleado,
    )
    Estudio.objects.filter(pk=estudio_informado.pk).update(estado=EstadoEstudio.INFORME_GENERADO)
    estudio_informado.refresh_from_db()
    PruebaEstudio.objects.filter(estudio=estudio_informado).update(
        estado=EstadoPruebaEstudio.COMPLETADA
    )

    return {
        "cliente_persona": cliente_persona,
        "cliente_empresa": cliente_empresa,
        "muestra_pozo": muestra_pozo,
        "muestra_planta": muestra_planta,
        "tipo_fq": tipo_fq,
        "tipo_basico": tipo_basico,
        "estudio_pendiente": estudio_pendiente,
        "estudio_en_proceso": estudio_en_proceso,
        "estudio_finalizado": estudio_finalizado,
        "estudio_informado": estudio_informado,
    }


def test_buscar_por_identificador_exacto(cliente_http, escenario_consulta):
    estudio = escenario_consulta["estudio_en_proceso"]
    resp = cliente_http.get(reverse("estudios:buscar"), {"q": str(estudio.pk)})
    assert resp.status_code == 200
    resultados = list(resp.context["page_obj"].object_list)
    assert resultados == [estudio]


def test_buscar_por_numero_pi_de_muestra(cliente_http, escenario_consulta):
    resp = cliente_http.get(reverse("estudios:buscar"), {"q": "200101"})
    assert resp.status_code == 200
    resultados = list(resp.context["page_obj"].object_list)
    assert resultados == [
        escenario_consulta["estudio_en_proceso"],
        escenario_consulta["estudio_pendiente"],
    ]


@pytest.mark.parametrize("texto", ["Pozo", "pozo", "OCTUBRE", "pozo sur"])
def test_buscar_por_nombre_de_muestra(cliente_http, escenario_consulta, texto):
    resp = cliente_http.get(reverse("estudios:buscar"), {"q": texto})
    assert resp.status_code == 200
    resultados = list(resp.context["page_obj"].object_list)
    assert resultados == [
        escenario_consulta["estudio_en_proceso"],
        escenario_consulta["estudio_pendiente"],
    ]


@pytest.mark.parametrize(
    "texto",
    ["Físico-Químico", "fisico-quimico", "FISICO", "quimico"],
)
def test_buscar_por_tipo_de_estudio(cliente_http, escenario_consulta, texto):
    resp = cliente_http.get(reverse("estudios:buscar"), {"q": texto})
    assert resp.status_code == 200
    resultados = list(resp.context["page_obj"].object_list)
    assert resultados == [
        escenario_consulta["estudio_informado"],
        escenario_consulta["estudio_en_proceso"],
    ]


def test_buscar_numero_incluye_nombres_de_muestra_y_cliente(
    cliente_http, escenario_consulta, empleado
):
    hoy = timezone.localdate()
    cliente_2026 = Cliente.objects.create(
        razon_social="Logística 2026 S.A.",
        tipo_documento="CUIT",
        numero_documento="30712345620",
        email="logistica@ejemplo.com",
    )
    origen_2026 = Origen.objects.create(cliente=cliente_2026, nombre=" Cisterna")
    muestra_tanque = Muestra.objects.create(
        numero_pi=200201,
        nombre="Tanque 2026",
        cliente=escenario_consulta["cliente_persona"],
        origen=escenario_consulta["muestra_pozo"].origen,
        fecha_muestreo=hoy,
        fecha_ingreso=hoy,
        sitio_extraccion="Toma auxiliar",
        registrada_por=empleado,
    )
    muestra_cliente_num = Muestra.objects.create(
        numero_pi=200202,
        nombre="Muestra General",
        cliente=cliente_2026,
        origen=origen_2026,
        fecha_muestreo=hoy,
        fecha_ingreso=hoy,
        sitio_extraccion="Toma central",
        registrada_por=empleado,
    )
    tipo = escenario_consulta["tipo_basico"]
    estudio_tanque = crear_estudio(
        {
            "clave": str(uuid.uuid4()),
            "muestra": muestra_tanque.pk,
            "tipo": tipo.pk,
            "version": tipo.version,
        },
        empleado,
    )
    estudio_cliente_num = crear_estudio(
        {
            "clave": str(uuid.uuid4()),
            "muestra": muestra_cliente_num.pk,
            "tipo": tipo.pk,
            "version": tipo.version,
        },
        empleado,
    )

    resp = cliente_http.get(reverse("estudios:buscar"), {"q": "2026"})
    assert resp.status_code == 200
    ids = {e.pk for e in resp.context["page_obj"].object_list}
    assert estudio_tanque.pk in ids
    assert estudio_cliente_num.pk in ids


@pytest.mark.parametrize("texto", ["Pérez", "perez", "PEREZ", "PÉREZ", "juan"])
def test_buscar_por_nombre_cliente_sin_tildes_ni_mayusculas(
    cliente_http, escenario_consulta, texto
):
    resp = cliente_http.get(reverse("estudios:buscar"), {"q": texto})
    assert resp.status_code == 200
    resultados = list(resp.context["page_obj"].object_list)
    assert resultados == [
        escenario_consulta["estudio_en_proceso"],
        escenario_consulta["estudio_pendiente"],
    ]


@pytest.mark.parametrize("texto", ["Aguas", "aguas del sur", "AGUAS DEL SUR"])
def test_buscar_por_razon_social_cliente(cliente_http, escenario_consulta, texto):
    resp = cliente_http.get(reverse("estudios:buscar"), {"q": texto})
    assert resp.status_code == 200
    resultados = list(resp.context["page_obj"].object_list)
    assert resultados == [
        escenario_consulta["estudio_informado"],
        escenario_consulta["estudio_finalizado"],
    ]


@pytest.mark.parametrize(
    "texto",
    ["30123456", "30.123.456", "30-123-456", " 30 123 456 ", "1234"],
)
def test_buscar_por_dni_cliente_con_y_sin_formato(cliente_http, escenario_consulta, texto):
    resp = cliente_http.get(reverse("estudios:buscar"), {"q": texto})
    assert resp.status_code == 200
    ids = {e.pk for e in resp.context["page_obj"].object_list}
    assert escenario_consulta["estudio_pendiente"].pk in ids
    assert escenario_consulta["estudio_en_proceso"].pk in ids


@pytest.mark.parametrize("texto", ["20-12345678-6", "20123456786"])
def test_buscar_por_cuit_cliente(cliente_http, escenario_consulta, texto):
    resp = cliente_http.get(reverse("estudios:buscar"), {"q": texto})
    assert resp.status_code == 200
    resultados = list(resp.context["page_obj"].object_list)
    assert resultados == [
        escenario_consulta["estudio_informado"],
        escenario_consulta["estudio_finalizado"],
    ]


def test_columnas_en_resultados_de_busqueda(cliente_http, escenario_consulta):
    resp = cliente_http.get(reverse("estudios:buscar"), {"q": "200101"})
    assert resp.status_code == 200
    html = resp.content.decode()
    estudio_ep = escenario_consulta["estudio_en_proceso"]
    estudio_pe = escenario_consulta["estudio_pendiente"]

    assert f"#{estudio_ep.pk}" in html
    assert f"#{estudio_pe.pk}" in html
    assert "200101" in html
    assert "Pozo Sur Octubre" in html
    assert "Juan Pérez" in html
    assert "DNI 30123456" in html
    assert "Físico-Químico" in html
    assert "Control Básico" in html
    assert "Pendiente de análisis" in html
    assert "En proceso" in html
    assert reverse("estudios:detalle", args=[estudio_ep.pk]) in html


def test_detalle_estudio_cabecera_avance_y_pruebas_ordenadas(
    cliente_http, escenario_consulta, empleado
):
    estudio = escenario_consulta["estudio_en_proceso"]
    resp = cliente_http.get(reverse("estudios:detalle", args=[estudio.pk]))
    assert resp.status_code == 200
    html = resp.content.decode()

    assert f"Estudio #{estudio.pk}" in html
    assert "En proceso" in html
    assert "Físico-Químico" in html
    assert "Análisis físico-químico general de agua" in html
    assert "200101" in html
    assert "Pozo Sur Octubre" in html
    assert "Pozo Sur" in html
    assert "Juan Pérez" in html
    assert "DNI 30123456" in html
    assert empleado.get_full_name() or empleado.email in html

    assert resp.context["total_pruebas"] == 3
    assert resp.context["pruebas_completadas"] == 1
    assert resp.context["pruebas_cargadas"] == 1
    assert resp.context["pruebas_pendientes"] == 1

    codigos = [a.prueba.codigo for a in resp.context["pruebas_asignadas"]]
    assert codigos == ["ALC", "NO3", "PH"]
    estados = [a.get_estado_display() for a in resp.context["pruebas_asignadas"]]
    assert estados == ["Cargada", "Completada", "Pendiente"]
    assert "Alcalinidad total" in html
    assert "Nitratos" in html
    assert "Potencial de hidrógeno" in html


@pytest.mark.parametrize(
    ("clave_estudio", "etiqueta_esperada"),
    [
        ("estudio_pendiente", "Pendiente de análisis"),
        ("estudio_en_proceso", "En proceso"),
        ("estudio_finalizado", "Finalizado"),
        ("estudio_informado", "Informe generado"),
    ],
)
def test_detalle_estudio_muestra_todos_los_estados_generales(
    cliente_http, escenario_consulta, clave_estudio, etiqueta_esperada
):
    estudio = escenario_consulta[clave_estudio]
    resp = cliente_http.get(reverse("estudios:detalle", args=[estudio.pk]))
    assert resp.status_code == 200
    assert etiqueta_esperada in resp.content.decode()


def test_busqueda_sin_coincidencias(cliente_http, escenario_consulta):
    resp = cliente_http.get(reverse("estudios:buscar"), {"q": "zzzz"})
    assert resp.status_code == 200
    html = resp.content.decode()
    assert "No se encontraron estudios para «zzzz»." in html
    assert resp.context["page_obj"] is not None
    assert resp.context["page_obj"].paginator.count == 0


def test_busqueda_sin_parametro_lista_todos_los_estudios(cliente_http, escenario_consulta):
    resp = cliente_http.get(reverse("estudios:buscar"))
    assert resp.status_code == 200
    assert not resp.context["form"].errors
    assert resp.context["page_obj"] is not None
    resultados = list(resp.context["page_obj"].object_list)
    assert resultados == [
        escenario_consulta["estudio_informado"],
        escenario_consulta["estudio_finalizado"],
        escenario_consulta["estudio_en_proceso"],
        escenario_consulta["estudio_pendiente"],
    ]
    html = resp.content.decode()
    assert "4 estudios registrados" in html
    assert 'role="tooltip"' in html
    assert "group-hover:visible" in html


def test_busqueda_sin_estudios_registrados_muestra_estado_vacio(cliente_http):
    resp = cliente_http.get(reverse("estudios:buscar"))
    assert resp.status_code == 200
    assert resp.context["page_obj"] is not None
    assert resp.context["page_obj"].paginator.count == 0
    assert "Aún no hay estudios registrados." in resp.content.decode()


@pytest.mark.parametrize("texto", ["", "   "])
def test_busqueda_vacia_o_espacios_lista_todos_los_estudios(
    cliente_http, escenario_consulta, texto
):
    resp = cliente_http.get(reverse("estudios:buscar"), {"q": texto})
    assert resp.status_code == 200
    assert not resp.context["form"].errors
    assert resp.context["page_obj"] is not None
    assert resp.context["page_obj"].paginator.count == 4


@pytest.mark.parametrize("texto", ["a", "Z", "-"])
def test_busqueda_un_caracter_no_numerico_rechazada(cliente_http, escenario_consulta, texto):
    resp = cliente_http.get(reverse("estudios:buscar"), {"q": texto})
    assert resp.status_code == 200
    assert resp.context["page_obj"] is None
    assert "Ingresá al menos 2 caracteres para buscar." in resp.content.decode()


@pytest.mark.parametrize(
    "texto",
    ["²", "³", "²²", "0", "9999999999999999999999999"],
)
def test_busqueda_numero_invalido_o_fuera_de_rango_muestra_error(
    cliente_http, escenario_consulta, texto
):
    resp = cliente_http.get(reverse("estudios:buscar"), {"q": texto})
    assert resp.status_code == 200
    assert resp.context["page_obj"] is None
    assert "Ingresá un número válido para buscar." in resp.content.decode()


@pytest.mark.parametrize("texto", ["a" * 101, "1" * 101])
def test_busqueda_supera_longitud_maxima_muestra_error(cliente_http, escenario_consulta, texto):
    resp = cliente_http.get(reverse("estudios:buscar"), {"q": texto})
    assert resp.status_code == 200
    assert resp.context["page_obj"] is None
    assert "Ingresá como máximo 100 caracteres para buscar." in resp.content.decode()


def test_busqueda_un_digito_numerico_es_valida(cliente_http, escenario_consulta):
    resp = cliente_http.get(reverse("estudios:buscar"), {"q": "1"})
    assert resp.status_code == 200
    assert not resp.context["form"].errors
    assert resp.context["page_obj"] is not None


def test_conserva_snapshots_tras_editar_o_desactivar_tipo(
    cliente_http, escenario_consulta, cambiar_tipo
):
    estudio_fq = escenario_consulta["estudio_en_proceso"]
    estudio_basico = escenario_consulta["estudio_pendiente"]

    cambiar_tipo(
        escenario_consulta["tipo_fq"],
        nombre="Nombre Nuevo Catálogo",
        descripcion="Descripción modificada en el catálogo",
        activo=False,
    )
    cambiar_tipo(
        escenario_consulta["tipo_basico"],
        nombre="Control Renombrado",
        descripcion="Ahora tiene descripción",
    )

    resp_busqueda = cliente_http.get(reverse("estudios:buscar"), {"q": "200101"})
    html_busqueda = resp_busqueda.content.decode()
    assert "Físico-Químico" in html_busqueda
    assert "Control Básico" in html_busqueda
    assert "Nombre Nuevo Catálogo" not in html_busqueda

    resp_detalle = cliente_http.get(reverse("estudios:detalle", args=[estudio_fq.pk]))
    html_detalle = resp_detalle.content.decode()
    assert "Físico-Químico" in html_detalle
    assert "Análisis físico-químico general de agua" in html_detalle
    assert "Descripción modificada en el catálogo" not in html_detalle

    resp_vacio = cliente_http.get(reverse("estudios:detalle", args=[estudio_basico.pk]))
    assert "Ahora tiene descripción" not in resp_vacio.content.decode()


def test_permite_buscar_y_consultar_estudios_de_cliente_inactivo(cliente_http, escenario_consulta):
    cliente = escenario_consulta["cliente_persona"]
    cliente.activo = False
    cliente.save()

    resp = cliente_http.get(reverse("estudios:buscar"), {"q": "Pérez"})
    assert resp.status_code == 200
    assert resp.context["page_obj"].paginator.count == 2

    estudio = escenario_consulta["estudio_pendiente"]
    resp_det = cliente_http.get(reverse("estudios:detalle", args=[estudio.pk]))
    assert resp_det.status_code == 200
    assert "Juan Pérez" in resp_det.content.decode()


def test_orden_y_paginacion_de_resultados(cliente_http, muestra, tipo, empleado):
    creados = [
        crear_estudio(
            {
                "clave": str(uuid.uuid4()),
                "muestra": muestra.pk,
                "tipo": tipo.pk,
                "version": tipo.version,
            },
            empleado,
        )
        for _ in range(22)
    ]

    resp_p1 = cliente_http.get(reverse("estudios:buscar"), {"q": str(muestra.numero_pi)})
    assert resp_p1.status_code == 200
    page1 = resp_p1.context["page_obj"]
    assert page1.paginator.count == 22
    assert len(page1.object_list) == 20
    assert [e.pk for e in page1.object_list] == [e.pk for e in reversed(creados[2:])]
    assert f"?q={muestra.numero_pi}&page=2" in resp_p1.content.decode()

    resp_p2 = cliente_http.get(
        reverse("estudios:buscar"), {"q": str(muestra.numero_pi), "page": "2"}
    )
    page2 = resp_p2.context["page_obj"]
    assert [e.pk for e in page2.object_list] == [creados[1].pk, creados[0].pk]


def test_acceso_requiere_sesion_activa(client, escenario_consulta):
    estudio = escenario_consulta["estudio_pendiente"]
    for url in [
        reverse("estudios:buscar"),
        reverse("estudios:detalle", args=[estudio.pk]),
    ]:
        resp = client.get(url)
        assert resp.status_code == 302
        assert reverse(settings.LOGIN_URL) in resp["Location"]


def test_detalle_estudio_inexistente_responde_404(cliente_http):
    resp = cliente_http.get(reverse("estudios:detalle", args=[999999]))
    assert resp.status_code == 404
