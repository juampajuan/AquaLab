"""US 6.6 – servicios de curvas: `guardar_curva` y `borrar_curva` (`pruebas/curvas.py`)."""

import datetime
import uuid
from decimal import Decimal

import pytest
from django.utils import timezone

from pruebas import curvas, gestion
from pruebas.models import CurvaCalibracion, Prueba

pytestmark = pytest.mark.django_db

D = Decimal
REFERENCIA = [
    ["0", "0.000"],
    ["0.1", "0.052"],
    ["0.2", "0.101"],
    ["0.3", "0.153"],
    ["0.4", "0.199"],
]


def datos(**cambios):
    base = {
        "fecha_preparacion": timezone.localdate().isoformat(),
        "observacion": "Estándares nuevos",
        "archivo_origen": "",
        "puntos": REFERENCIA,
    }
    base.update(cambios)
    return base


def guardar(usuario, prueba, clave=None, **cambios):
    return curvas.guardar_curva(
        usuario=usuario, prueba_id=prueba.pk, datos=datos(**cambios), clave=clave or uuid.uuid4()
    )


# --- US2: guardar ------------------------------------------------------------------------------


def test_guardar_curva_crea(administrador_catalogo, prueba_curva):
    guardado = guardar(administrador_catalogo, prueba_curva)
    curva = guardado.curva
    assert guardado.anterior is None
    assert curva.prueba == prueba_curva
    assert curva.vigente is True
    assert curva.usada is False
    assert (curva.pendiente, curva.ordenada, curva.r2) == (
        D("0.499000000000"),
        D("0.001200000000"),
        D("0.9996025692"),
    )
    assert (curva.concentracion_min, curva.concentracion_max) == (D("0"), D("0.4"))
    assert (curva.absorbancia_min, curva.absorbancia_max) == (D("0"), D("0.199"))
    assert curva.cargada_por == administrador_catalogo
    assert curva.fecha_carga is not None
    assert curva.fecha_preparacion == timezone.localdate()
    assert curva.observacion == "Estándares nuevos"
    assert curva.archivo_origen == ""
    assert [(p.orden, str(p.concentracion), str(p.absorbancia)) for p in curva.puntos.all()] == [
        (1, "0.000000", "0.000000"),
        (2, "0.100000", "0.052000"),
        (3, "0.200000", "0.101000"),
        (4, "0.300000", "0.153000"),
        (5, "0.400000", "0.199000"),
    ]


def test_guardar_curva_reemplaza_vigente(administrador_catalogo, prueba_curva, curva_de):
    vieja = curva_de(prueba_curva)
    guardado = guardar(administrador_catalogo, prueba_curva)
    vieja.refresh_from_db()
    assert guardado.anterior == vieja
    assert vieja.vigente is False
    assert prueba_curva.curva_vigente == guardado.curva
    assert prueba_curva.curvas.filter(vigente=True).count() == 1


def test_guardar_curva_archivo_origen(administrador_catalogo, prueba_curva):
    curva = guardar(administrador_catalogo, prueba_curva, archivo_origen="curva_no2.xlsx").curva
    assert curva.archivo_origen == "curva_no2.xlsx"


def test_guardar_curva_prueba_no_curva(administrador_catalogo, prueba_libre):
    with pytest.raises(curvas.NoEsPruebaPorCurva):
        guardar(administrador_catalogo, prueba_libre)
    assert not CurvaCalibracion.objects.exists()


def test_guardar_curva_fecha_futura(administrador_catalogo, prueba_curva):
    manana = timezone.localdate() + datetime.timedelta(days=1)
    with pytest.raises(curvas.CurvaInvalida) as error:
        guardar(administrador_catalogo, prueba_curva, fecha_preparacion=manana.isoformat())
    assert error.value.errores == {"fecha_preparacion": curvas.MENSAJE_FECHA_FUTURA}
    assert not CurvaCalibracion.objects.exists()


@pytest.mark.parametrize(
    "cambios",
    [
        {"puntos": [["0", "0"], ["1", "0.5"]]},
        {"puntos": [["0", "0"], ["1", "x"], ["2", "1"]]},
        {"fecha_preparacion": "no es fecha"},
        {"puntos": "no es una lista"},
    ],
    ids=["dos puntos", "valor inválido", "fecha inválida", "puntos inválidos"],
)
def test_guardar_curva_revalida(administrador_catalogo, prueba_curva, cambios):
    """El servicio revalida todo aunque el formulario ya lo haya hecho (borrador alterado)."""
    with pytest.raises(curvas.CurvaInvalida):
        guardar(administrador_catalogo, prueba_curva, **cambios)
    assert not CurvaCalibracion.objects.exists()


def test_clave_repetida(administrador_catalogo, prueba_curva):
    clave = uuid.uuid4()
    primera = guardar(administrador_catalogo, prueba_curva, clave=clave)
    segunda = guardar(administrador_catalogo, prueba_curva, clave=clave)
    assert segunda.curva == primera.curva
    assert segunda.repetida is True
    assert CurvaCalibracion.objects.count() == 1


def test_guardar_curva_sin_permiso(empleado, prueba_curva):
    with pytest.raises(gestion.NoAutorizado):
        guardar(empleado, prueba_curva)
    assert not CurvaCalibracion.objects.exists()


def test_guardar_curva_prueba_inexistente(administrador_catalogo):
    with pytest.raises(curvas.NoEsPruebaPorCurva):
        curvas.guardar_curva(
            usuario=administrador_catalogo, prueba_id=999999, datos=datos(), clave=uuid.uuid4()
        )
    assert not Prueba.objects.filter(pk=999999).exists()


# --- US4 Esc. 8–10: mediciones que esperan curva (FR-025) --------------------------------------


@pytest.fixture
def dos_pendientes(prueba_curva, estudio_de, empleado):
    from estudios.tests.utiles import cargar

    estudios = [estudio_de("NO2-C"), estudio_de("NO2-C")]
    for estudio in estudios:
        cargar(estudio, empleado, {"NO2-C": "0.126"})
    return estudios


def test_pendientes_resumen(cliente_catalogo, prueba_curva, dos_pendientes):
    from pruebas.tests.test_curvas_vistas import ir_a_confirmar

    assert len(curvas.pendientes_de_curva(prueba=prueba_curva)) == 2
    html = cliente_catalogo.get(ir_a_confirmar(cliente_catalogo, prueba_curva)).content.decode()
    assert "2 mediciones en 2 estudios esperan curva" in html
    assert 'name="calcular_pendientes"' in html
    assert "checked" not in html.split('name="calcular_pendientes"')[1].split(">")[0]


def test_pendientes_calcular(administrador_catalogo, prueba_curva, dos_pendientes):
    from estudios.models import EstadoEstudio, Resultado

    guardado = curvas.guardar_curva(
        usuario=administrador_catalogo,
        prueba_id=prueba_curva.pk,
        datos=datos(),
        clave=uuid.uuid4(),
        calcular_pendientes=True,
    )
    assert guardado.calculadas == 2
    resultados = Resultado.objects.filter(asignacion__prueba=prueba_curva)
    assert resultados.count() == 2
    assert {r.curva_id for r in resultados} == {guardado.curva.pk}
    assert {r.valor for r in resultados} == {D("0.2501002004")}
    for estudio in dos_pendientes:
        estudio.refresh_from_db()
        assert estudio.estado == EstadoEstudio.EN_PROCESO
    guardado.curva.refresh_from_db()
    assert guardado.curva.usada is True


def test_pendientes_calcular_desde_la_pantalla(cliente_catalogo, prueba_curva, dos_pendientes):
    import re

    from pruebas.tests.test_curvas_vistas import ir_a_confirmar

    location = ir_a_confirmar(cliente_catalogo, prueba_curva)
    html = cliente_catalogo.get(location).content.decode()
    token = re.search(r'name="token" value="([^"]+)"', html).group(1)
    respuesta = cliente_catalogo.post(
        location,
        {"token": token, "accion": "confirmar", "calcular_pendientes": "1"},
        follow=True,
    )
    assert "Se calcularon 2 resultados." in respuesta.content.decode()


def test_pendientes_sin_casilla(administrador_catalogo, prueba_curva, dos_pendientes, cliente_http):
    from django.urls import reverse

    from estudios.models import Resultado

    guardado = guardar(administrador_catalogo, prueba_curva)
    assert guardado.calculadas == 0
    assert not Resultado.objects.exists()
    html = cliente_http.get(
        reverse("estudios:detalle", args=[dos_pendientes[0].pk])
    ).content.decode()
    assert "Se cargó antes de la curva vigente." in html


def test_pendientes_excluye_informados(administrador_catalogo, prueba_curva, dos_pendientes):
    from estudios.models import EstadoEstudio, Estudio, Resultado

    cerrado = dos_pendientes[0]
    Estudio.objects.filter(pk=cerrado.pk).update(estado=EstadoEstudio.FINALIZADO)
    assert len(curvas.pendientes_de_curva(prueba=prueba_curva)) == 1
    guardado = curvas.guardar_curva(
        usuario=administrador_catalogo,
        prueba_id=prueba_curva.pk,
        datos=datos(),
        clave=uuid.uuid4(),
        calcular_pendientes=True,
    )
    assert guardado.calculadas == 1
    assert not Resultado.objects.filter(asignacion__estudio=cerrado).exists()


# --- US6: borrar -------------------------------------------------------------------------------


def borrar(usuario, curva):
    return curvas.borrar_curva(usuario=usuario, curva_id=curva.pk)


def test_borrar_curva_vigente(administrador_catalogo, prueba_curva, curva_de):
    from pruebas.models import PuntoCurva

    anterior = curva_de(prueba_curva, fecha=datetime.date(2026, 6, 1))
    otra = curva_de(prueba_curva, fecha=datetime.date(2026, 3, 1), vigente=False)
    curva = curva_de(prueba_curva)
    nueva_vigente = borrar(administrador_catalogo, curva)
    assert not CurvaCalibracion.objects.filter(pk=curva.pk).exists()
    assert not PuntoCurva.objects.filter(curva_id=curva.pk).exists()
    # Vuelve la anterior más reciente (por fecha de carga), no la de fecha de preparación mayor.
    assert nueva_vigente == otra
    otra.refresh_from_db()
    anterior.refresh_from_db()
    assert otra.vigente and not anterior.vigente


def test_borrar_curva_unica(administrador_catalogo, prueba_curva, curva_de):
    assert borrar(administrador_catalogo, curva_de(prueba_curva)) is None
    assert prueba_curva.curva_vigente is None


def test_borrar_curva_historica(administrador_catalogo, prueba_curva, curva_de):
    historica = curva_de(prueba_curva)
    vigente = curva_de(prueba_curva)
    assert borrar(administrador_catalogo, historica) == vigente
    vigente.refresh_from_db()
    assert vigente.vigente


def test_borrar_curva_usada(administrador_catalogo, prueba_curva, curva_de, estudio_de, empleado):
    """Usada aunque su resultado se haya descartado después (US 6.5): no se borra (R6)."""
    from estudios.servicios import corregir_mediciones
    from estudios.tests.utiles import asignacion_de, cargar

    curva = curva_de(prueba_curva)
    estudio = estudio_de("NO2-C")
    cargar(estudio, empleado, {"NO2-C": "0.126"})
    asignacion = asignacion_de(estudio, "NO2-C")
    corregir_mediciones(estudio.pk, {asignacion.pk: (D("0.126"), None)}, empleado)
    curva.refresh_from_db()
    assert curva.usada is True
    with pytest.raises(curvas.CurvaUsada):
        borrar(administrador_catalogo, curva)
    assert CurvaCalibracion.objects.filter(pk=curva.pk).exists()


def test_borrar_curva_sin_permiso(empleado, prueba_curva, curva_de):
    curva = curva_de(prueba_curva)
    with pytest.raises(gestion.NoAutorizado):
        borrar(empleado, curva)
    assert CurvaCalibracion.objects.filter(pk=curva.pk).exists()
