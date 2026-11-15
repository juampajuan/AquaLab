"""US 6.6 – resultados de pruebas por curva de calibración (US4 y US5 de la spec 037)."""

from decimal import Decimal

import pytest
from django.urls import reverse

from estudios.models import EstadoEstudio, EstadoPruebaEstudio, Resultado, Validacion
from estudios.servicios import corregir_mediciones, validar_resultados
from estudios.tests.utiles import asignacion_de, cargar, validar
from pruebas.models import Prueba, TipoCalculo

pytestmark = pytest.mark.django_db

D = Decimal
NO2 = "NO2-C"


def resultado(estudio, codigo=NO2):
    return (
        Resultado.objects.select_related("curva")
        .filter(asignacion__estudio=estudio, asignacion__prueba__codigo=codigo)
        .first()
    )


def corregir(estudio, usuario, codigo, nuevo):
    asignacion = asignacion_de(estudio, codigo)
    original = asignacion.medicion.valor_ingresado
    return corregir_mediciones(
        estudio.pk, {asignacion.pk: (D(original), None if nuevo is None else D(nuevo))}, usuario
    )


@pytest.fixture
def estudio_curva(prueba_curva, estudio_de):
    return estudio_de(NO2)


def detalle(cliente, estudio):
    return cliente.get(reverse("estudios:detalle", args=[estudio.pk])).content.decode()


# --- US4 Esc. 1–2: el resultado sale de la curva vigente y la guarda -------------------------


def test_calculo_con_curva(estudio_curva, prueba_curva, curva_de, empleado):
    curva = curva_de(prueba_curva)  # pendiente 0,5 · ordenada 0,001
    cargar(estudio_curva, empleado, {NO2: "0.126"})
    calculado = resultado(estudio_curva)
    assert calculado.valor == D("0.25")
    assert calculado.unidad == "mg/l"
    assert calculado.formula == ""
    assert calculado.curva == curva
    curva.refresh_from_db()
    assert curva.usada is True


def test_calculo_con_curva_de_referencia(estudio_curva, prueba_curva, curva_de, empleado):
    referencia = [
        ("0", "0"),
        ("0.1", "0.052"),
        ("0.2", "0.101"),
        ("0.3", "0.153"),
        ("0.4", "0.199"),
    ]
    curva_de(prueba_curva, referencia, pendiente="0.499", ordenada="0.0012", r2="0.9996025692")
    cargar(estudio_curva, empleado, {NO2: "0.126"})
    assert resultado(estudio_curva).valor == D("0.2501002004")


def test_detalle_muestra_curva(
    estudio_curva, prueba_curva, curva_de, empleado, cliente_http, django_assert_max_num_queries
):
    import datetime

    curva = curva_de(prueba_curva, r2="0.9996025692", fecha=datetime.date(2026, 11, 2))
    cargar(estudio_curva, empleado, {NO2: "0.126"})
    html = detalle(cliente_http, estudio_curva)
    assert "Curva del 02/11/2026 · R² 0,9996" in html
    assert reverse("curvas:detalle", args=[curva.pk]) in html
    # Sin N+1: con varias pruebas por curva el detalle no hace una consulta por cada una.
    with django_assert_max_num_queries(40):
        cliente_http.get(reverse("estudios:detalle", args=[estudio_curva.pk]))


# --- US4 Esc. 3–4: sin curva vigente ----------------------------------------------------------


def test_sin_curva(estudio_curva, empleado, cliente_http, bioquimico):
    cargar(estudio_curva, empleado, {NO2: "0.126"})
    asignacion = asignacion_de(estudio_curva, NO2)
    assert asignacion.medicion.valor == D("0.126")
    assert resultado(estudio_curva) is None
    assert "Falta curva de calibración." in detalle(cliente_http, estudio_curva)
    respuesta = validar_resultados(estudio_curva.pk, {asignacion.pk: "0.25"}, bioquimico)
    assert not Validacion.objects.exists()
    assert respuesta.omitidas  # «ya no tenía resultado»


# --- US4 Esc. 5: fuera del rango de la curva --------------------------------------------------


@pytest.mark.parametrize(
    "absorbancia, fuera",
    [("0.0005", True), ("0.25", True), ("0.001", False), ("0.201", False), ("0.126", False)],
    ids=["debajo", "encima", "borde mínimo", "borde máximo", "dentro"],
)
def test_fuera_de_rango(
    estudio_curva,
    prueba_curva,
    curva_de,
    empleado,
    cliente_bioquimico,
    bioquimico,
    absorbancia,
    fuera,
):
    curva_de(prueba_curva)  # absorbancias 0,001–0,201; concentraciones 0–0,4
    cargar(estudio_curva, empleado, {NO2: absorbancia})
    aviso = "Fuera del rango de la curva (0–0,4 mg/l)"
    assert (aviso in detalle(cliente_bioquimico, estudio_curva)) is fuera
    validacion = cliente_bioquimico.get(
        reverse("estudios:validar_resultados", args=[estudio_curva.pk])
    ).content.decode()
    assert (aviso in validacion) is fuera
    validar(estudio_curva, bioquimico, NO2)  # no bloquea
    assert asignacion_de(estudio_curva, NO2).estado == EstadoPruebaEstudio.COMPLETADA


def test_concentracion_negativa(estudio_curva, prueba_curva, curva_de, empleado):
    """Absorbancia menor que la ordenada: concentración negativa, fuera de rango y «< LD»."""
    from informes.contenido import texto_resultado
    from pruebas import curvas
    from pruebas.limites import limites_aplicables

    prueba_curva.limite_deteccion = "0.01"
    prueba_curva.save()
    curva_de(prueba_curva)
    cargar(estudio_curva, empleado, {NO2: "0"})
    calculado = resultado(estudio_curva)
    assert calculado.valor == D("-0.002")
    assert curvas.fuera_de_rango(asignacion_de(estudio_curva, NO2)) is True
    assert texto_resultado(calculado, limites_aplicables(prueba_curva, "")) == "< 0,01"


def test_prueba_desactivada_sigue_calculando(
    estudio_curva, prueba_curva, curva_de, empleado, cliente_http
):
    curva = curva_de(prueba_curva)
    Prueba.objects.filter(pk=prueba_curva.pk).update(activa=False)
    cargar(estudio_curva, empleado, {NO2: "0.126"})
    assert resultado(estudio_curva).curva == curva
    html = cliente_http.get(reverse("curvas:listar", args=[prueba_curva.pk])).content.decode()
    assert curva.fecha_preparacion.strftime("%d/%m/%Y") in html


# --- US4 Esc. 6–7 -----------------------------------------------------------------------------


def test_formula_usa_concentracion(prueba_curva, curva_de, estudio_de, empleado):
    Prueba.objects.create(
        codigo="NO2-X",
        nombre="Doble de nitritos",
        tipo_calculo=TipoCalculo.FORMULA,
        formula="{NO2-C}*2",
        es_calculada=True,
        unidad="mg/l",
    )
    curva_de(prueba_curva)
    estudio = estudio_de(NO2, "NO2-X")
    cargar(estudio, empleado, {NO2: "0.126"})
    assert resultado(estudio, "NO2-X").valor == D("0.5")


def test_curva_nueva_no_recalcula(estudio_curva, prueba_curva, curva_de, empleado, bioquimico):
    from informes.models import Informe
    from informes.servicios import emitir_informe

    curva_a = curva_de(prueba_curva)
    cargar(estudio_curva, empleado, {NO2: "0.126"})
    validar(estudio_curva, bioquimico, NO2)
    informe = emitir_informe(estudio_curva.pk, bioquimico)
    antes = (resultado(estudio_curva).valor, Validacion.objects.get().pk, informe.contenido)
    curva_de(prueba_curva, pendiente="0.25", r2="0.99")  # curva B
    despues = resultado(estudio_curva)
    assert despues.curva == curva_a
    assert (despues.valor, Validacion.objects.get(anulada=False).pk) == antes[:2]
    assert Informe.objects.get(pk=informe.pk).contenido == antes[2]


# --- US4 Esc. 11–12: «Calcular con la curva vigente» (FR-026) --------------------------------


def url_calcular(estudio):
    return reverse("estudios:calcular_con_curva", args=[estudio.pk])


def test_calcular_con_curva_motivo(estudio_curva, prueba_curva, curva_de, empleado, cliente_http):
    cargar(estudio_curva, empleado, {NO2: "0.126"})
    html = detalle(cliente_http, estudio_curva)
    assert "Falta curva de calibración." in html
    assert url_calcular(estudio_curva) not in html
    curva_de(prueba_curva)
    html = detalle(cliente_http, estudio_curva)
    assert "Se cargó antes de la curva vigente." in html
    assert "Falta curva de calibración." not in html
    assert url_calcular(estudio_curva) in html
    assert "Calcular con la curva vigente" in html


def test_calcular_con_curva_confirmar(prueba_curva, curva_de, estudio_de, empleado, cliente_http):
    Prueba.objects.create(
        codigo="NO2-X",
        nombre="Doble de nitritos",
        tipo_calculo=TipoCalculo.FORMULA,
        formula="{NO2-C}*2",
        es_calculada=True,
        unidad="mg/l",
    )
    estudio = estudio_de(NO2, "NO2-X")
    cargar(estudio, empleado, {NO2: "0.126"})
    curva = curva_de(prueba_curva)
    pagina = cliente_http.get(url_calcular(estudio)).content.decode()
    assert "Se van a calcular con la curva vigente: NO2-C" in pagina
    respuesta = cliente_http.post(url_calcular(estudio), {"accion": "confirmar"}, follow=True)
    # Calcula NO2-C (y su dependiente NO2-X): cuenta las mediciones calculadas.
    assert "Se calculó 1 resultado con la curva vigente." in respuesta.content.decode()
    assert resultado(estudio).curva == curva
    assert resultado(estudio, "NO2-X").valor == D("0.5")  # con sus dependientes
    estudio.refresh_from_db()
    assert estudio.estado == EstadoEstudio.EN_PROCESO


def test_calcular_con_curva_reenvio(estudio_curva, prueba_curva, curva_de, empleado, cliente_http):
    cargar(estudio_curva, empleado, {NO2: "0.126"})
    curva_de(prueba_curva)
    cliente_http.post(url_calcular(estudio_curva), {"accion": "confirmar"})
    valor = resultado(estudio_curva).valor
    respuesta = cliente_http.post(url_calcular(estudio_curva), {"accion": "confirmar"}, follow=True)
    assert "No quedaban mediciones para calcular: ya se calcularon." in respuesta.content.decode()
    assert resultado(estudio_curva).valor == valor
    assert Resultado.objects.count() == 1


def test_calcular_con_curva_estudio_cerrado(
    estudio_curva, prueba_curva, curva_de, empleado, cliente_http
):
    from estudios import servicios
    from estudios.models import Estudio

    cargar(estudio_curva, empleado, {NO2: "0.126"})
    curva_de(prueba_curva)
    Estudio.objects.filter(pk=estudio_curva.pk).update(estado=EstadoEstudio.FINALIZADO)
    respuesta = cliente_http.get(url_calcular(estudio_curva))
    assert respuesta.status_code == 302
    assert respuesta["Location"] == reverse("estudios:detalle", args=[estudio_curva.pk])
    with pytest.raises(servicios.CalcularConCurvaError):
        servicios.calcular_con_curva(estudio_curva.pk, empleado)
    assert resultado(estudio_curva) is None


def test_calcular_con_curva_sin_sesion(client, estudio_curva):
    respuesta = client.get(url_calcular(estudio_curva))
    assert respuesta.status_code == 302
    assert reverse("usuarios:login") in respuesta["Location"]


# --- US5: corrección con la misma curva -------------------------------------------------------


def test_correccion_misma_curva(estudio_curva, prueba_curva, curva_de, empleado):
    curva_a = curva_de(prueba_curva)  # pendiente 0,5 · ordenada 0,001
    cargar(estudio_curva, empleado, {NO2: "0.126"})
    curva_de(prueba_curva, pendiente="0.25", r2="0.99")  # B vigente
    corregir(estudio_curva, empleado, NO2, "0.151")
    corregido = resultado(estudio_curva)
    assert corregido.curva == curva_a
    assert corregido.valor == D("0.3")  # (0,151 − 0,001) / 0,5


def test_correccion_sin_resultado_previo(estudio_curva, prueba_curva, curva_de, empleado):
    cargar(estudio_curva, empleado, {NO2: "0.126"})
    vigente = curva_de(prueba_curva)
    corregir(estudio_curva, empleado, NO2, "0.151")
    assert resultado(estudio_curva).curva == vigente


def test_correccion_borrada_y_recargada(estudio_curva, prueba_curva, curva_de, empleado):
    curva_de(prueba_curva)
    cargar(estudio_curva, empleado, {NO2: "0.126"})
    corregir(estudio_curva, empleado, NO2, None)  # US 6.5
    assert resultado(estudio_curva) is None
    curva_b = curva_de(prueba_curva, pendiente="0.25", r2="0.99")
    cargar(estudio_curva, empleado, {NO2: "0.126"})
    assert resultado(estudio_curva).curva == curva_b
    assert resultado(estudio_curva).valor == D("0.5")  # (0,126 − 0,001) / 0,25


def test_correccion_pierde_validacion(estudio_curva, prueba_curva, curva_de, empleado, bioquimico):
    curva_de(prueba_curva)
    cargar(estudio_curva, empleado, {NO2: "0.126"})
    validar(estudio_curva, bioquimico, NO2)
    corregir(estudio_curva, empleado, NO2, "0.151")
    assert asignacion_de(estudio_curva, NO2).estado == EstadoPruebaEstudio.CARGADA
    assert Validacion.objects.get().anulada is True


def test_recalculo_dependencias_misma_curva(prueba_curva, curva_de, estudio_de, empleado):
    """Corregir otra prueba de la fórmula recalcula la que usa la curva con la misma curva."""
    Prueba.objects.create(codigo="FAC", nombre="Factor", unidad="u", unidad_medicion="u")
    Prueba.objects.create(
        codigo="NO2-X",
        nombre="Nitritos por factor",
        tipo_calculo=TipoCalculo.FORMULA,
        formula="{NO2-C}*{FAC}",
        es_calculada=True,
        unidad="mg/l",
    )
    curva_a = curva_de(prueba_curva)
    estudio = estudio_de(NO2, "FAC", "NO2-X")
    cargar(estudio, empleado, {NO2: "0.126", "FAC": "2"})
    curva_de(prueba_curva, pendiente="0.25", r2="0.99")
    corregir(estudio, empleado, "FAC", "3")
    assert resultado(estudio).curva == curva_a
    assert resultado(estudio, "NO2-X").valor == D("0.75")
