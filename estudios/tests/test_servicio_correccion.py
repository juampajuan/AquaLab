import uuid
from decimal import Decimal

import pytest
from django.utils import timezone

from estudios.models import EstadoEstudio, Estudio, Medicion, Resultado
from estudios.servicios import CorregirMedicionesError, corregir_mediciones, crear_estudio
from estudios.tests.utiles import asignacion_de, cargar

pytestmark = pytest.mark.django_db


def medicion(estudio, codigo):
    return Medicion.objects.get(asignacion=asignacion_de(estudio, codigo))


def resultado(estudio, codigo):
    return Resultado.objects.get(asignacion=asignacion_de(estudio, codigo))


def corregir(estudio, usuario, originales=None, **por_codigo):
    """Corrige mediciones por código (`_` se lee como `-`), con el valor vigente como original."""
    originales = originales or {}
    cambios = {}
    for nombre, texto in por_codigo.items():
        codigo = nombre.replace("_", "-")
        original = originales.get(codigo, medicion(estudio, codigo).valor_ingresado)
        cambios[asignacion_de(estudio, codigo).pk] = (Decimal(original), Decimal(texto))
    return corregir_mediciones(estudio.pk, cambios, usuario)


@pytest.fixture
def otro_empleado(django_user_model):
    return django_user_model.objects.create_user(
        email="otro-correccion@ejemplo.com", password="Clave-Valida-123", is_active=True
    )


def test_corregir_mediciones_actualiza_la_misma_fila(estudio_de, empleado, otro_empleado):
    estudio = estudio_de("CL-")
    cargar(estudio, empleado, CL_="2.35")
    original = medicion(estudio, "CL-")
    antes = timezone.now()
    resultado_correccion = corregir(estudio, otro_empleado, CL_="2.53")
    despues = timezone.now()
    corregida = medicion(estudio, "CL-")
    assert corregida.pk == original.pk
    assert (corregida.valor, corregida.decimales) == (Decimal("2.53"), 2)
    assert (corregida.cargada_por, corregida.fecha_carga) == (empleado, original.fecha_carga)
    assert corregida.corregida_por == otro_empleado
    assert antes <= corregida.fecha_correccion <= despues
    assert [m.pk for m in resultado_correccion.corregidas] == [corregida.pk]
    assert resultado(estudio, "CL-").valor == Decimal("25.3")


def test_confirmar_recalcula_dependientes(estudio_de, empleado):
    estudio = estudio_de("CA", "DUREZA-T", "MG")
    cargar(estudio, empleado, CA="80", DUREZA_T="15")
    dureza = resultado(estudio, "DUREZA-T")
    corregir(estudio, empleado, CA="40")
    assert resultado(estudio, "CA").valor == Decimal("40")
    assert resultado(estudio, "MG").valor == Decimal("48.6")
    despues = resultado(estudio, "DUREZA-T")
    assert (despues.valor, despues.fecha_calculo) == (dureza.valor, dureza.fecha_calculo)


def test_corregir_en_estudio_finalizado(estudio_de, empleado):
    estudio = estudio_de("CL-")
    cargar(estudio, empleado, CL_="2.35")
    Estudio.objects.filter(pk=estudio.pk).update(estado=EstadoEstudio.FINALIZADO)
    corregir(estudio, empleado, CL_="2.53")
    assert medicion(estudio, "CL-").valor == Decimal("2.53")


def test_informe_emitido_rechaza(estudio_de, empleado):
    estudio = estudio_de("CL-")
    cargar(estudio, empleado, CL_="2.35")
    Estudio.objects.filter(pk=estudio.pk).update(estado=EstadoEstudio.INFORME_GENERADO)
    with pytest.raises(
        CorregirMedicionesError,
        match="El estudio ya tiene el informe emitido: sus mediciones y resultados no se "
        "pueden cambiar.",
    ):
        corregir(estudio, empleado, CL_="2.53")
    assert medicion(estudio, "CL-").valor == Decimal("2.35")


def test_omite_si_cambio_mientras_se_editaba(estudio_de, empleado):
    estudio = estudio_de("CA", "CL-")
    cargar(estudio, empleado, CA="80", CL_="2.35")
    Medicion.objects.filter(pk=medicion(estudio, "CA").pk).update(valor=Decimal("90"))
    resultado_correccion = corregir(estudio, empleado, originales={"CA": "80"}, CA="40", CL_="3")
    assert medicion(estudio, "CA").valor == Decimal("90")
    assert medicion(estudio, "CL-").valor == Decimal("3")
    assert [(p.codigo, m) for p, m in resultado_correccion.omitidas] == [
        ("CA", "cambió mientras se editaba")
    ]


def test_omite_si_ya_tenia_ese_valor(estudio_de, empleado):
    estudio = estudio_de("CA")
    cargar(estudio, empleado, CA="80")
    corregir(estudio, empleado, CA="40")
    fecha = medicion(estudio, "CA").fecha_correccion
    resultado_correccion = corregir(estudio, empleado, originales={"CA": "80"}, CA="40")
    assert medicion(estudio, "CA").fecha_correccion == fecha
    assert [(p.codigo, m) for p, m in resultado_correccion.omitidas] == [
        ("CA", "ya tenía ese valor")
    ]


def test_correccion_no_modifica_otros_datos(estudio_de, empleado, muestra, catalogo):
    estudio = estudio_de("CL-", "PH")
    cargar(estudio, empleado, CL_="2.35", PH="7.20")
    otro = crear_estudio(
        {
            "clave": str(uuid.uuid4()),
            "muestra": muestra.pk,
            "tipo": estudio.tipo_id,
            "version": estudio.tipo.version,
        },
        empleado,
    )
    cargar(otro, empleado, CL_="2.35")
    ph = medicion(estudio, "PH")
    corregir(estudio, empleado, CL_="2.53")
    assert medicion(estudio, "PH").valor_ingresado == ph.valor_ingresado
    assert medicion(estudio, "PH").corregida_por is None
    assert medicion(otro, "CL-").valor == Decimal("2.35")
    catalogo["CL-"].refresh_from_db()
    assert catalogo["CL-"].formula == "x*10"


def test_correccion_quita_validacion_y_reabre_estudio(estudio_de, empleado):
    from estudios.models import EstadoPruebaEstudio, PruebaEstudio

    estudio = estudio_de("CA", "DUREZA-T", "MG")
    cargar(estudio, empleado, CA="80", DUREZA_T="15")
    PruebaEstudio.objects.filter(estudio=estudio).update(estado=EstadoPruebaEstudio.COMPLETADA)
    Estudio.objects.filter(pk=estudio.pk).update(estado=EstadoEstudio.FINALIZADO)
    corregir(estudio, empleado, CA="40")
    assert asignacion_de(estudio, "CA").estado == EstadoPruebaEstudio.CARGADA
    assert asignacion_de(estudio, "MG").estado == EstadoPruebaEstudio.CARGADA
    assert asignacion_de(estudio, "DUREZA-T").estado == EstadoPruebaEstudio.COMPLETADA
    estudio.refresh_from_db()
    assert estudio.estado == EstadoEstudio.EN_PROCESO
