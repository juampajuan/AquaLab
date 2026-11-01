import uuid
from decimal import Decimal

import pytest

from estudios.models import EstadoPruebaEstudio, Medicion, Resultado
from estudios.servicios import crear_estudio
from estudios.tests.utiles import asignacion_de, cargar

pytestmark = pytest.mark.django_db


def resultado(estudio, codigo):
    return Resultado.objects.filter(asignacion=asignacion_de(estudio, codigo)).first()


def test_carga_calcula_resultado_directo_y_formula(estudio_de, empleado):
    estudio = estudio_de("PH", "CL-", "NTK-T")
    cargar(estudio, empleado, PH="7.20", CL_="2.35", NTK_T="10")
    ph, cl, ntk = (resultado(estudio, c) for c in ("PH", "CL-", "NTK-T"))
    assert (ph.valor, ph.unidad, ph.formula) == (Decimal("7.2"), "UpH", "")
    assert (cl.valor, cl.unidad, cl.formula) == (Decimal("23.5"), "mg/l", "x*10")
    assert ntk.valor == Decimal("211.2")
    for codigo in ("PH", "CL-", "NTK-T"):
        assert asignacion_de(estudio, codigo).estado == EstadoPruebaEstudio.CARGADA


def test_resultado_conserva_formula_y_unidad(estudio_de, empleado, catalogo):
    estudio = estudio_de("CL-")
    cargar(estudio, empleado, CL_="2.35")
    prueba = catalogo["CL-"]
    prueba.formula, prueba.unidad = "x*100", "g/l"
    prueba.save()
    cl = resultado(estudio, "CL-")
    assert (cl.valor, cl.unidad, cl.formula) == (Decimal("23.5"), "mg/l", "x*10")


def test_calculo_no_modifica_otros_datos(estudio_de, empleado, muestra):
    estudio = estudio_de("CL-")
    otro = crear_estudio(
        {
            "clave": str(uuid.uuid4()),
            "muestra": muestra.pk,
            "tipo": estudio.tipo_id,
            "version": estudio.tipo.version,
        },
        empleado,
    )
    cabecera = ("muestra_id", "tipo_id", "tipo_nombre_snapshot", "tipo_version_snapshot")
    antes = [getattr(estudio, c) for c in cabecera]
    cargar(estudio, empleado, CL_="2.35")
    estudio.refresh_from_db()
    medicion = Medicion.objects.get(asignacion__estudio=estudio)
    assert (medicion.valor, medicion.decimales) == (Decimal("2.35"), 2)
    assert [getattr(estudio, c) for c in cabecera] == antes
    assert not Resultado.objects.filter(asignacion__estudio=otro).exists()
    assert not Medicion.objects.filter(asignacion__estudio=otro).exists()


def test_calculada_se_calcula_al_completar_referencias(estudio_de, empleado):
    estudio = estudio_de("CA", "DUREZA-T", "MG")
    cargar(estudio, empleado, CA="80")
    assert resultado(estudio, "MG") is None
    assert asignacion_de(estudio, "MG").estado == EstadoPruebaEstudio.PENDIENTE
    cargar(estudio, empleado, DUREZA_T="15")
    mg = resultado(estudio, "MG")
    assert (mg.valor, mg.unidad, mg.formula) == (
        Decimal("24.3"),
        "mg/l",
        "({DUREZA-T}-{CA}*2.5)*0.243",
    )
    assert asignacion_de(estudio, "MG").estado == EstadoPruebaEstudio.CARGADA


def test_cadena_de_calculadas(estudio_de, empleado):
    codigos = ("NA", "K", "CA", "DUREZA-T", "MG", "NA-MEQ", "K-MEQ", "CA-MEQ", "MG-MEQ", "CATIONES")
    estudio = estudio_de(*codigos)
    cargar(estudio, empleado, NA="0.5", K="0.4", CA="80", DUREZA_T="15")
    # Cada eslabón se guarda con 10 decimales y el siguiente parte de ese valor guardado.
    esperados = {
        "NA": "1.1708507143",
        "MG": "24.3",
        "NA-MEQ": "0.0509065528",
        "K-MEQ": "0.08",
        "CA-MEQ": "4",
        "MG-MEQ": "1.9918032787",
        "CATIONES": "6.1227098315",
    }
    for codigo, valor in esperados.items():
        assert resultado(estudio, codigo).valor == Decimal(valor), codigo
    for codigo in codigos:
        assert asignacion_de(estudio, codigo).estado == EstadoPruebaEstudio.CARGADA


def motivo(estudio, codigo):
    from estudios.calculo import motivo_sin_resultado, por_codigo

    return motivo_sin_resultado(asignacion_de(estudio, codigo), por_codigo(estudio))


def test_motivo_falta_medicion(estudio_de, empleado):
    estudio = estudio_de("PH", "CL-")
    cargar(estudio, empleado, CL_="1")
    assert motivo(estudio, "PH") == "Falta la medición."
    assert motivo(estudio, "CL-") is None


def test_motivo_faltan_resultados(estudio_de, empleado):
    estudio = estudio_de("CA", "DUREZA-T", "MG")
    cargar(estudio, empleado, CA="80")
    assert motivo(estudio, "MG") == "Faltan resultados de: DUREZA-T · Dureza Total."


def test_motivo_referencia_fuera_del_estudio(estudio_de, empleado):
    estudio = estudio_de("CA", "MG")
    cargar(estudio, empleado, CA="80")
    assert motivo(estudio, "MG") == "No forma parte del estudio: DUREZA-T · Dureza Total."


def test_motivo_division_por_cero(estudio_de, empleado, pruebas_division):
    estudio = estudio_de("DIV-A", "DIV-B", "DIV")
    cargar(estudio, empleado, DIV_A="5", DIV_B="0")
    assert motivo(estudio, "DIV") == "No se pudo calcular: división por cero."


def test_falla_de_calculo_no_impide_guardar(estudio_de, empleado, pruebas_division):
    estudio = estudio_de("DIV-A", "DIV-B", "DIV")
    carga = cargar(estudio, empleado, DIV_A="5", DIV_B="0")
    for codigo in ("DIV-A", "DIV-B"):
        assert Medicion.objects.filter(asignacion=asignacion_de(estudio, codigo)).exists()
        assert resultado(estudio, codigo) is not None
    assert resultado(estudio, "DIV") is None
    assert asignacion_de(estudio, "DIV").estado == EstadoPruebaEstudio.PENDIENTE
    assert [(p.codigo, m) for p, m in carga.sin_calcular] == [("DIV", "división por cero")]


def test_referencias_circulares(estudio_de, empleado):
    from pruebas.models import Prueba, TipoCalculo

    for codigo, otra in (("CIRC-A", "CIRC-B"), ("CIRC-B", "CIRC-A")):
        Prueba.objects.create(
            codigo=codigo,
            nombre=codigo,
            tipo_calculo=TipoCalculo.FORMULA,
            formula=f"{{{otra}}}*1",
            es_calculada=True,
        )
    estudio = estudio_de("PH", "CIRC-A", "CIRC-B")
    cargar(estudio, empleado, PH="7")
    assert resultado(estudio, "CIRC-A") is None
    assert motivo(estudio, "CIRC-A") == "No se pudo calcular: referencias circulares."


def corregir(estudio, codigo, texto, usuario):
    """Corrige una medición como lo hará US 6.3: actualiza la fila y recalcula en la misma
    transacción."""
    from django.db import transaction

    from estudios.servicios import recalcular_resultados

    asignacion = asignacion_de(estudio, codigo)
    valor = Decimal(texto)
    with transaction.atomic():
        Medicion.objects.filter(asignacion=asignacion).update(
            valor=valor, decimales=max(0, -valor.as_tuple().exponent)
        )
        return recalcular_resultados(estudio.pk, [asignacion.pk], usuario)


def test_recalcular_actualiza_dependientes_y_no_otras(estudio_de, empleado):
    estudio = estudio_de("CA", "DUREZA-T", "MG", "PH")
    cargar(estudio, empleado, CA="80", DUREZA_T="15", PH="7")
    antes = {c: resultado(estudio, c) for c in ("DUREZA-T", "PH")}
    corregir(estudio, "CA", "40", empleado)
    assert resultado(estudio, "CA").valor == Decimal("40")
    assert resultado(estudio, "MG").valor == Decimal("48.6")
    for codigo, previo in antes.items():
        actual = resultado(estudio, codigo)
        assert (actual.valor, actual.fecha_calculo) == (previo.valor, previo.fecha_calculo)


def test_recalculo_quita_validacion(estudio_de, empleado):
    from estudios.models import PruebaEstudio

    estudio = estudio_de("CA", "DUREZA-T", "MG")
    cargar(estudio, empleado, CA="80", DUREZA_T="15")
    PruebaEstudio.objects.filter(estudio=estudio).update(estado=EstadoPruebaEstudio.COMPLETADA)
    corregir(estudio, "CA", "40", empleado)
    assert asignacion_de(estudio, "CA").estado == EstadoPruebaEstudio.CARGADA
    assert asignacion_de(estudio, "MG").estado == EstadoPruebaEstudio.CARGADA
    assert resultado(estudio, "MG").valor == Decimal("48.6")
    assert asignacion_de(estudio, "DUREZA-T").estado == EstadoPruebaEstudio.COMPLETADA


def test_recalcular_con_informe_emitido_rechaza(estudio_de, empleado):
    from estudios.models import EstadoEstudio, Estudio
    from estudios.servicios import RecalculoError

    estudio = estudio_de("CA", "DUREZA-T", "MG")
    cargar(estudio, empleado, CA="80", DUREZA_T="15")
    Estudio.objects.filter(pk=estudio.pk).update(estado=EstadoEstudio.INFORME_GENERADO)
    with pytest.raises(
        RecalculoError,
        match="El estudio ya tiene el informe emitido: sus mediciones y resultados no se "
        "pueden cambiar.",
    ):
        corregir(estudio, "CA", "40", empleado)
    assert Medicion.objects.get(asignacion=asignacion_de(estudio, "CA")).valor == Decimal("80")
    assert resultado(estudio, "CA").valor == Decimal("80")
    assert resultado(estudio, "MG").valor == Decimal("24.3")


def test_calculada_que_deja_de_calcularse_vuelve_a_pendiente(
    estudio_de, empleado, pruebas_division
):
    estudio = estudio_de("DIV-A", "DIV-B", "DIV")
    cargar(estudio, empleado, DIV_A="6", DIV_B="2")
    assert resultado(estudio, "DIV").valor == Decimal("3")
    fallas = corregir(estudio, "DIV-B", "0", empleado)
    assert resultado(estudio, "DIV") is None
    assert asignacion_de(estudio, "DIV").estado == EstadoPruebaEstudio.PENDIENTE
    assert [(p.codigo, m) for p, m in fallas] == [("DIV", "división por cero")]


def test_recalcular_resultados_requiere_sesion_activa(estudio_de, empleado):
    from django.contrib.auth.models import AnonymousUser

    from estudios.servicios import RecalculoError, recalcular_resultados

    estudio = estudio_de("CA")
    with pytest.raises(RecalculoError, match="Se requiere una sesión activa."):
        recalcular_resultados(estudio.pk, [], AnonymousUser())


def test_comando_calcular_resultados(estudio_de, empleado):
    import io

    from django.core.management import call_command

    estudio = estudio_de("CA", "DUREZA-T", "MG")
    for codigo, valor in (("CA", "80"), ("DUREZA-T", "15")):
        # Mediciones como quedaron con US 6.1, sin resultado.
        Medicion.objects.create(
            asignacion=asignacion_de(estudio, codigo),
            valor=Decimal(valor),
            decimales=0,
            cargada_por=empleado,
        )
    salida = io.StringIO()
    call_command("calcular_resultados", stdout=salida)
    assert salida.getvalue().strip() == "Resultados calculados: 3. Sin calcular: 0."
    assert resultado(estudio, "MG").valor == Decimal("24.3")
    salida = io.StringIO()
    call_command("calcular_resultados", stdout=salida)
    assert salida.getvalue().strip() == "Resultados calculados: 0. Sin calcular: 0."


def test_afectadas(estudio_de):
    from estudios.calculo import afectadas, por_codigo

    estudio = estudio_de("CA", "DUREZA-T", "MG", "PH")
    todas = por_codigo(estudio)
    assert afectadas(todas, {"CA"}) == {"CA", "MG"}
    assert afectadas(todas, {"PH"}) == {"PH"}
