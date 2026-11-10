"""Consultas canónicas de lectura de la feature 033."""

from decimal import Decimal

import pytest

from estudios.models import EstadoEstudio, EstadoPruebaEstudio, Estudio, Resultado, Validacion
from estudios.tests.utiles import validar
from informes.servicios import estudios_para_informar, motivo_para_no_informar

pytestmark = pytest.mark.django_db


def test_carga_distinta_y_no_calculadas(crear_pendiente, empleado):
    from estudios.pendientes import estudios_con_mediciones_pendientes

    sin_iniciar = crear_pendiente()
    parcial = crear_pendiente(cargadas=1)
    calculada = crear_pendiente(cantidad=1, cargadas=1, calculada=True)
    crear_pendiente(cantidad=1, cargadas=1, completado=True)
    crear_pendiente(cantidad=1, cargadas=1, informado=True)
    assert set(
        estudios_con_mediciones_pendientes(Estudio.objects.all()).values_list("pk", flat=True)
    ) == {sin_iniciar.pk, parcial.pk}
    assert calculada.pruebas_asignadas.filter(estado="pendiente").count() == 0
    from estudios.views import asignaciones_para_medir

    for estudio in Estudio.objects.all():
        esperado = estudio.admite_mediciones and asignaciones_para_medir(estudio).exists()
        assert (
            estudios_con_mediciones_pendientes(Estudio.objects.filter(pk=estudio.pk)).exists()
            == esperado
        )


def test_resultados_existentes_y_recalculados(crear_pendiente, empleado):
    from estudios.pendientes import estudios_con_resultados_pendientes, resultados_por_validar

    estudio = crear_pendiente(cantidad=1, cargadas=1, calculada=True)
    esperado = set(Resultado.objects.values_list("pk", flat=True))
    crear_pendiente()
    crear_pendiente(cantidad=1, cargadas=1, completado=True)
    crear_pendiente(cantidad=1, cargadas=1, informado=True)
    assert set(resultados_por_validar().values_list("pk", flat=True)) == esperado
    assert list(estudios_con_resultados_pendientes(Estudio.objects.all())) == [estudio]
    asignacion = estudio.pruebas_asignadas.order_by("pk").first()
    profesional = crear_pendiente.profesional
    for valor in ("2", "3", "0"):
        validar(estudio, profesional, asignacion.prueba.codigo)
        from estudios.servicios import corregir_mediciones

        medicion = asignacion.medicion
        corregir_mediciones(
            estudio.pk, {asignacion.pk: (str(medicion.valor_ingresado), Decimal(valor))}, empleado
        )
        asignacion.refresh_from_db()
    assert Validacion.objects.filter(asignacion=asignacion, anulada=True).count() == 3
    assert set(resultados_por_validar().values_list("pk", flat=True)) == esperado
    assert resultados_por_validar().count() == 2
    validar(estudio, profesional, asignacion.prueba.codigo)
    asignacion.estado = EstadoPruebaEstudio.CARGADA
    asignacion.save(update_fields=["estado"])
    assert not resultados_por_validar().filter(asignacion=asignacion).exists()


def test_listos_paridad_regla_existente(crear_pendiente):
    crear_pendiente()
    crear_pendiente(cargadas=1)
    listo = crear_pendiente(cantidad=1, cargadas=1, completado=True)
    crear_pendiente(cantidad=1, cargadas=1, informado=True)
    vacio = crear_pendiente()
    vacio.pruebas_asignadas.all().delete()
    assert list(estudios_para_informar("", True)) == [listo]
    for estudio in Estudio.objects.all():
        esperado = motivo_para_no_informar(estudio, list(estudio.pruebas_asignadas.all())) is None
        assert estudios_para_informar("", True).filter(pk=estudio.pk).exists() == esperado


def test_formula_con_medicion_propia_no_se_excluye(crear_pendiente):
    from estudios.pendientes import estudios_con_mediciones_pendientes

    estudio = crear_pendiente(cantidad=1)
    prueba = estudio.pruebas_asignadas.get().prueba
    prueba.tipo_calculo = "FORMULA"
    prueba.formula = "x*2"
    prueba.save()
    assert estudios_con_mediciones_pendientes(Estudio.objects.all()).get() == estudio


@pytest.mark.parametrize("estado", EstadoEstudio.values)
def test_estados_carga(crear_pendiente, estado):
    from estudios.pendientes import estudios_con_mediciones_pendientes

    estudio = crear_pendiente()
    Estudio.objects.filter(pk=estudio.pk).update(estado=estado)
    estudio.refresh_from_db()
    assert estudios_con_mediciones_pendientes(Estudio.objects.all()).exists() == (
        estudio.admite_mediciones
    )
