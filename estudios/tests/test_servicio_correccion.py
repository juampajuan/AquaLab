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


def corregir(estudio, usuario, originales=None, borrar=(), **por_codigo):
    """Corrige mediciones por código (`_` se lee como `-`) y borra las de `borrar`, con el valor
    vigente como original salvo que `originales` diga otro."""
    originales = originales or {}

    def original(codigo):
        if codigo in originales:
            return Decimal(originales[codigo])
        return Decimal(medicion(estudio, codigo).valor_ingresado)

    cambios = {
        asignacion_de(estudio, nombre.replace("_", "-")).pk: (
            original(nombre.replace("_", "-")),
            Decimal(texto),
        )
        for nombre, texto in por_codigo.items()
    }
    for codigo in borrar:
        cambios[asignacion_de(estudio, codigo).pk] = (original(codigo), None)
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


def sin_medicion(estudio, codigo):
    return not Medicion.objects.filter(asignacion=asignacion_de(estudio, codigo)).exists()


def sin_resultado(estudio, codigo):
    return not Resultado.objects.filter(asignacion=asignacion_de(estudio, codigo)).exists()


def test_borrar_medicion(estudio_de, empleado):
    from estudios.models import EstadoPruebaEstudio

    estudio = estudio_de("CL-", "PH")
    cargar(estudio, empleado, CL_="2.35", PH="7.20")
    resultado_correccion = corregir(estudio, empleado, borrar=("CL-",))
    assert sin_medicion(estudio, "CL-") and sin_resultado(estudio, "CL-")
    assert asignacion_de(estudio, "CL-").estado == EstadoPruebaEstudio.PENDIENTE
    assert [p.codigo for p in resultado_correccion.borradas] == ["CL-"]
    assert medicion(estudio, "PH").valor_ingresado == Decimal("7.20")


def test_borrar_y_corregir_en_un_envio(estudio_de, empleado):
    estudio = estudio_de("CL-", "PH")
    cargar(estudio, empleado, CL_="2.35", PH="7.20")
    corregir(estudio, empleado, borrar=("CL-",), PH="7.30")
    assert sin_medicion(estudio, "CL-")
    assert medicion(estudio, "PH").valor == Decimal("7.30")


def test_borrar_y_corregir_referencias_de_la_misma_calculada(estudio_de, empleado):
    from estudios.models import EstadoPruebaEstudio

    estudio = estudio_de("CA", "DUREZA-T", "MG")
    cargar(estudio, empleado, CA="80", DUREZA_T="15")
    corregir(estudio, empleado, borrar=("CA",), DUREZA_T="20")
    assert medicion(estudio, "DUREZA-T").valor == Decimal("20")
    assert resultado(estudio, "DUREZA-T").valor == Decimal("400")
    assert sin_medicion(estudio, "CA")
    assert asignacion_de(estudio, "CA").estado == EstadoPruebaEstudio.PENDIENTE
    assert sin_resultado(estudio, "MG")
    assert asignacion_de(estudio, "MG").estado == EstadoPruebaEstudio.PENDIENTE


def test_borrar_omite_si_cambio(estudio_de, empleado):
    estudio = estudio_de("CL-")
    cargar(estudio, empleado, CL_="2.35")
    Medicion.objects.filter(pk=medicion(estudio, "CL-").pk).update(valor=Decimal("2.60"))
    resultado_correccion = corregir(estudio, empleado, originales={"CL-": "2.35"}, borrar=("CL-",))
    assert medicion(estudio, "CL-").valor == Decimal("2.60")
    assert [(p.codigo, m) for p, m in resultado_correccion.omitidas] == [
        ("CL-", "cambió mientras se editaba")
    ]


def test_borrar_omite_si_ya_no_existe(estudio_de, empleado):
    estudio = estudio_de("CL-")
    cargar(estudio, empleado, CL_="2.35")
    corregir(estudio, empleado, borrar=("CL-",))
    resultado_correccion = corregir(estudio, empleado, originales={"CL-": "2.35"}, borrar=("CL-",))
    assert resultado_correccion.borradas == []
    assert [(p.codigo, m) for p, m in resultado_correccion.omitidas] == [
        ("CL-", "ya no tenía medición")
    ]


@pytest.fixture
def estudio_magnesio(estudio_de, empleado):
    estudio = estudio_de("CA", "DUREZA-T", "MG")
    cargar(estudio, empleado, CA="80", DUREZA_T="15")
    return estudio


def validar_todo(estudio):
    from estudios.models import EstadoPruebaEstudio, PruebaEstudio

    PruebaEstudio.objects.filter(estudio=estudio).update(estado=EstadoPruebaEstudio.COMPLETADA)


def test_borrar_deja_dependientes_pendientes(estudio_magnesio, empleado):
    from estudios.models import EstadoPruebaEstudio

    dureza = resultado(estudio_magnesio, "DUREZA-T")
    corregir(estudio_magnesio, empleado, borrar=("CA",))
    assert sin_resultado(estudio_magnesio, "MG")
    assert asignacion_de(estudio_magnesio, "MG").estado == EstadoPruebaEstudio.PENDIENTE
    despues = resultado(estudio_magnesio, "DUREZA-T")
    assert (despues.valor, despues.fecha_calculo) == (dureza.valor, dureza.fecha_calculo)
    estudio_magnesio.refresh_from_db()
    assert estudio_magnesio.estado == EstadoEstudio.EN_PROCESO


def test_borrar_validada(estudio_magnesio, empleado):
    from estudios.models import EstadoPruebaEstudio

    validar_todo(estudio_magnesio)
    corregir(estudio_magnesio, empleado, borrar=("CA",))
    assert asignacion_de(estudio_magnesio, "CA").estado == EstadoPruebaEstudio.PENDIENTE
    assert asignacion_de(estudio_magnesio, "MG").estado == EstadoPruebaEstudio.PENDIENTE
    assert asignacion_de(estudio_magnesio, "DUREZA-T").estado == EstadoPruebaEstudio.COMPLETADA


def test_borrar_todo_vuelve_a_pendiente_de_analisis(estudio_magnesio, empleado):
    corregir(estudio_magnesio, empleado, borrar=("CA", "DUREZA-T"))
    estudio_magnesio.refresh_from_db()
    assert estudio_magnesio.estado == EstadoEstudio.PENDIENTE_ANALISIS
    assert estudio_magnesio.admite_modificaciones


def test_borrar_en_finalizado_reabre(estudio_magnesio, empleado):
    validar_todo(estudio_magnesio)
    Estudio.objects.filter(pk=estudio_magnesio.pk).update(estado=EstadoEstudio.FINALIZADO)
    corregir(estudio_magnesio, empleado, borrar=("CA",))
    estudio_magnesio.refresh_from_db()
    assert estudio_magnesio.estado == EstadoEstudio.EN_PROCESO


def test_borrar_con_informe_emitido_rechaza(estudio_magnesio, empleado):
    Estudio.objects.filter(pk=estudio_magnesio.pk).update(estado=EstadoEstudio.INFORME_GENERADO)
    with pytest.raises(CorregirMedicionesError, match="informe emitido"):
        corregir(estudio_magnesio, empleado, borrar=("CA",))
    assert not sin_medicion(estudio_magnesio, "CA")


def test_falla_en_recalculo_no_borra(estudio_magnesio, empleado):
    from unittest import mock

    from estudios.servicios import RecalculoError

    with (
        mock.patch("estudios.servicios.recalcular_resultados", side_effect=RecalculoError("x")),
        pytest.raises(CorregirMedicionesError, match="x"),
    ):
        corregir(estudio_magnesio, empleado, borrar=("CA",))
    assert not sin_medicion(estudio_magnesio, "CA")
    assert not sin_resultado(estudio_magnesio, "CA")


def test_borrado_no_modifica_otros_datos(estudio_magnesio, empleado, muestra):
    otro = crear_estudio(
        {
            "clave": str(uuid.uuid4()),
            "muestra": muestra.pk,
            "tipo": estudio_magnesio.tipo_id,
            "version": estudio_magnesio.tipo.version,
        },
        empleado,
    )
    cargar(otro, empleado, CA="80", DUREZA_T="15")
    corregir(estudio_magnesio, empleado, borrar=("CA",))
    assert medicion(otro, "CA").valor == Decimal("80")
    assert resultado(otro, "MG").valor == Decimal("24.3")
