"""Contratos GET y correspondencia de los pendientes con Inicio (033)."""

import re

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from estudios.models import Resultado
from estudios.tests.utiles import cargar, validar
from informes.servicios import emitir_informe

pytestmark = pytest.mark.django_db


def buscar(client, usuario, pendiente="mediciones", **filtros):
    client.force_login(usuario)
    return client.get(reverse("estudios:buscar"), {"pendiente": pendiente, **filtros})


def ids_estudios(response):
    return {e.pk for e in response.context["page_obj"]}


def ids_resultados(response):
    return [int(v) for v in re.findall(r'data-resultado="(\d+)"', response.content.decode())]


def test_enlace_carga_conjunto_exacto(client, empleado, crear_pendiente):
    esperado = {crear_pendiente().pk, crear_pendiente(cargadas=1).pk}
    crear_pendiente(cantidad=1, cargadas=1)
    crear_pendiente(cantidad=1, cargadas=1, completado=True)
    client.force_login(empleado)
    inicio = client.get("/")
    indicador = inicio.context["indicadores"][0]
    assert indicador["valor"] == 2
    assert ids_estudios(client.get(indicador["url"])) == esperado


def test_resultados_identificables(client, crear_pendiente):
    a = crear_pendiente(cantidad=5, cargadas=5)
    b = crear_pendiente(cantidad=1, cargadas=1)
    crear_pendiente()
    crear_pendiente(cantidad=1, cargadas=1, informado=True)
    esperado = set(
        Resultado.objects.filter(asignacion__estudio__in=[a, b]).values_list("pk", flat=True)
    )
    r = buscar(client, crear_pendiente.profesional, "validaciones")
    assert ids_estudios(r) == {a.pk, b.pk}
    assert set(ids_resultados(r)) == esperado
    assert len(ids_resultados(r)) == 6
    assert r.context["total_resultados"] == 6
    assert r.context["page_obj"].paginator.count == 2
    for asignacion in a.pruebas_asignadas.select_related("prueba"):
        assert asignacion.prueba.codigo in r.content.decode()
        assert asignacion.prueba.nombre in r.content.decode()
    assert "mg/L" in r.content.decode()
    assert 'href="/estudios/' in r.content.decode()


def test_paginacion_conserva_filtros(client, crear_pendiente):
    esperado = {crear_pendiente(cantidad=1, cargadas=1).pk for _ in range(23)}
    hoy = timezone.localdate().isoformat()
    filtros = {"q": "Tipo US33", "desde": hoy, "hasta": hoy, "estado": "en_proceso"}
    r = buscar(client, crear_pendiente.profesional, "validaciones", **filtros)
    assert len(r.context["page_obj"]) == 20
    assert r.context["total_resultados"] == 23
    href = re.search(r'href="(\?[^"<>]+page=2)"', r.content.decode()).group(1)
    for campo in ("q=", "desde=", "hasta=", "estado=", "pendiente=validaciones"):
        assert campo in href
    segunda = client.get(reverse("estudios:buscar") + href.replace("&amp;", "&"))
    assert ids_estudios(r) | ids_estudios(segunda) == esperado
    assert not (ids_estudios(r) & ids_estudios(segunda))


def test_union_resultados_todas_paginas(client, crear_pendiente):
    estudios = [crear_pendiente(cantidad=2, cargadas=2) for _ in range(22)]
    esperado = set(Resultado.objects.values_list("pk", flat=True))
    primero = buscar(client, crear_pendiente.profesional, "validaciones")
    segundo = client.get("/estudios/buscar/", {"pendiente": "validaciones", "page": 2})
    ids = ids_resultados(primero) + ids_resultados(segundo)
    assert len(ids) == len(set(ids)) == 44
    assert set(ids) == esperado
    total_inicio = {i["nombre"]: i["valor"] for i in client.get("/").context["indicadores"]}
    assert total_inicio["resultados-por-validar"] == len(ids)
    filtrado = client.get(
        "/estudios/buscar/",
        {"pendiente": "validaciones", "q": estudios[-1].tipo_nombre_snapshot},
    )
    esperados_filtrados = set(
        Resultado.objects.filter(asignacion__estudio=estudios[-1]).values_list("pk", flat=True)
    )
    assert set(ids_resultados(filtrado)) == esperados_filtrados
    assert filtrado.context["total_resultados"] == len(ids_resultados(filtrado)) == 2


@pytest.mark.parametrize("modo", ["mediciones", "validaciones", "listos"])
def test_cambio_entre_requests(client, crear_pendiente, empleado, modo):
    estudio = crear_pendiente(
        cantidad=1, cargadas=int(modo != "mediciones"), completado=modo == "listos"
    )
    client.force_login(crear_pendiente.profesional)
    nombres = {
        "mediciones": "mediciones-pendientes",
        "validaciones": "resultados-por-validar",
        "listos": "estudios-listos",
    }
    indicador = next(
        i for i in client.get("/").context["indicadores"] if i["nombre"] == nombres[modo]
    )
    assert indicador["valor"] == 1
    codigo = estudio.pruebas_asignadas.get().prueba.codigo
    if modo == "mediciones":
        cargar(estudio, empleado, {codigo: "1"})
    elif modo == "validaciones":
        validar(estudio, crear_pendiente.profesional, codigo)
    else:
        emitir_informe(estudio.pk, crear_pendiente.profesional)
    assert client.get(indicador["url"]).context["page_obj"].paginator.count == 0
    assert (
        next(i for i in client.get("/").context["indicadores"] if i["nombre"] == nombres[modo])[
            "valor"
        ]
        == 0
    )


def test_listas_vacias(client, empleado):
    for modo in ("mediciones", "validaciones"):
        r = buscar(client, empleado, modo)
        assert r.context["page_obj"].paginator.count == 0
        assert "Ningún estudio" in r.content.decode()


def test_prefetch_no_crece_por_fila(client, crear_pendiente):
    crear_pendiente(cantidad=1, cargadas=1)
    buscar(client, crear_pendiente.profesional, "validaciones")
    with CaptureQueriesContext(connection) as pocas:
        client.get("/estudios/buscar/?pendiente=validaciones")
    for _ in range(5):
        crear_pendiente(cantidad=5, cargadas=5)
    with CaptureQueriesContext(connection) as muchas:
        client.get("/estudios/buscar/?pendiente=validaciones")
    assert len(pocas) == len(muchas)
    for consulta in muchas:
        assert "SELECT" in consulta["sql"]


def test_historial_no_duplica_lista(client, crear_pendiente, empleado):
    from decimal import Decimal

    from estudios.servicios import corregir_mediciones

    estudio = crear_pendiente(cantidad=1, cargadas=1)
    a = estudio.pruebas_asignadas.get()
    for valor in ("2", "3"):
        validar(estudio, crear_pendiente.profesional, a.prueba.codigo)
        a.refresh_from_db()
        corregir_mediciones(
            estudio.pk, {a.pk: (a.medicion.valor_ingresado, Decimal(valor))}, empleado
        )
    r = buscar(client, crear_pendiente.profesional, "validaciones")
    assert len(ids_resultados(r)) == r.context["total_resultados"] == 1


def test_busqueda_general_no_precarga_resultados(client, empleado, crear_pendiente):
    crear_pendiente(cargadas=1)
    r = buscar(client, empleado, "")
    assert "total_resultados" not in r.context
    assert not ids_resultados(r)
