import uuid
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone

from estudios.mediciones import leer_valor
from estudios.models import EstadoEstudio, EstadoPruebaEstudio, Estudio, Medicion
from estudios.servicios import CargarMedicionesError, cargar_mediciones, crear_estudio

FORMATO_INVALIDO = "Ingresá un número válido (usá coma o punto para los decimales)."


@pytest.mark.parametrize(
    "texto,esperado",
    [
        ("7,25", Decimal("7.25")),
        ("7.25", Decimal("7.25")),
        (" 7,20 ", Decimal("7.20")),
        ("-0,013", Decimal("-0.013")),
        ("+3", Decimal("3")),
        ("0", Decimal("0")),
        (",5", Decimal("0.5")),
        ("0,123456", Decimal("0.123456")),
        ("999999999999", Decimal("999999999999")),
        ("0000000000000,5", Decimal("0.5")),
    ],
)
def test_leer_valor_validos(texto, esperado):
    valor = leer_valor(texto)
    assert valor == esperado
    assert valor.as_tuple().exponent == esperado.as_tuple().exponent


@pytest.mark.parametrize("texto", ["", "   ", None])
def test_leer_valor_vacio(texto):
    assert leer_valor(texto) is None


@pytest.mark.parametrize(
    "texto,mensaje",
    [
        *[
            (t, FORMATO_INVALIDO)
            for t in ["abc", "1.234,5", "1,2,3", "1e3", "7 25", "7%", "NaN", "Infinity", "7,", "-"]
        ],
        ("0,1234567", "Ingresá como máximo 6 decimales."),
        ("1234567890123", "El valor es demasiado grande (máximo 12 cifras enteras)."),
    ],
)
def test_leer_valor_invalidos(texto, mensaje):
    with pytest.raises(ValidationError) as exc:
        leer_valor(texto)
    assert exc.value.messages == [mensaje]


def valores(asignaciones, **por_codigo):
    return {asignaciones[c.replace("_", "-")].pk: Decimal(v) for c, v in por_codigo.items()}


@pytest.mark.django_db
def test_cargar_mediciones_guarda_valor_unidad_usuario_y_fecha(
    estudio_mediciones, asignaciones_medicion, empleado
):
    antes = timezone.now()
    resultado = cargar_mediciones(
        estudio_mediciones.pk,
        valores(asignaciones_medicion, TEST_PH="7.20", TEST_VOL="18.5"),
        empleado,
    )
    despues = timezone.now()
    assert len(resultado.guardadas) == 2
    assert resultado.omitidas == []
    ph = Medicion.objects.get(asignacion=asignaciones_medicion["TEST-PH"])
    vol = Medicion.objects.get(asignacion=asignaciones_medicion["TEST-VOL"])
    assert (ph.valor, ph.decimales, ph.unidad) == (Decimal("7.20"), 2, "UpH")
    assert (vol.valor, vol.decimales, vol.unidad) == (Decimal("18.5"), 1, "mL")
    for medicion in (ph, vol):
        assert medicion.cargada_por == empleado
        assert antes <= medicion.fecha_carga <= despues
        medicion.asignacion.refresh_from_db()
        assert medicion.asignacion.estado == EstadoPruebaEstudio.CARGADA


@pytest.mark.django_db
def test_carga_parcial_deja_pendientes(estudio_mediciones, asignaciones_medicion, empleado):
    cargar_mediciones(estudio_mediciones.pk, valores(asignaciones_medicion, TEST_PH="7"), empleado)
    for codigo in ("TEST-VOL", "TEST-SIN", "TEST-CALC"):
        asignacion = asignaciones_medicion[codigo]
        asignacion.refresh_from_db()
        assert asignacion.estado == EstadoPruebaEstudio.PENDIENTE
        assert not Medicion.objects.filter(asignacion=asignacion).exists()


@pytest.mark.django_db
def test_primera_medicion_pasa_estudio_a_en_proceso(
    estudio_mediciones, asignaciones_medicion, empleado
):
    assert estudio_mediciones.estado == EstadoEstudio.PENDIENTE_ANALISIS
    cargar_mediciones(estudio_mediciones.pk, valores(asignaciones_medicion, TEST_PH="7"), empleado)
    estudio_mediciones.refresh_from_db()
    assert estudio_mediciones.estado == EstadoEstudio.EN_PROCESO
    cargar_mediciones(estudio_mediciones.pk, valores(asignaciones_medicion, TEST_VOL="1"), empleado)
    estudio_mediciones.refresh_from_db()
    assert estudio_mediciones.estado == EstadoEstudio.EN_PROCESO


def capturar(estudio, otro):
    estudio.refresh_from_db()
    otro.refresh_from_db()
    campos = (
        "muestra_id",
        "tipo_id",
        "creado_por_id",
        "fecha_creacion",
        "tipo_nombre_snapshot",
        "tipo_descripcion_snapshot",
        "tipo_version_snapshot",
    )
    pruebas = estudio.tipo.pruebas.order_by("codigo")
    return {
        "cabecera": [getattr(estudio, c) for c in campos],
        "tipo": (list(pruebas.values_list("pk", flat=True)), estudio.tipo.version),
        "catalogo": list(pruebas.values_list("codigo", "nombre", "unidad_medicion")),
        "otro": (
            otro.estado,
            list(otro.pruebas_asignadas.order_by("pk").values_list("pk", "estado")),
        ),
    }


@pytest.mark.django_db
def test_cargar_no_modifica_otros_datos(
    estudio_mediciones, asignaciones_medicion, empleado, muestra
):
    otro = crear_estudio(
        {
            "clave": str(uuid.uuid4()),
            "muestra": muestra.pk,
            "tipo": estudio_mediciones.tipo_id,
            "version": estudio_mediciones.tipo.version,
        },
        empleado,
    )
    antes = capturar(estudio_mediciones, otro)
    cargar_mediciones(estudio_mediciones.pk, valores(asignaciones_medicion, TEST_PH="7"), empleado)
    assert capturar(estudio_mediciones, otro) == antes
    assert not Medicion.objects.filter(asignacion__estudio=otro).exists()


@pytest.mark.django_db
def test_unidad_conservada_tras_cambio_en_catalogo(
    estudio_mediciones, asignaciones_medicion, empleado, pruebas_medicion
):
    cargar_mediciones(
        estudio_mediciones.pk, valores(asignaciones_medicion, TEST_VOL="18.5"), empleado
    )
    prueba = pruebas_medicion["TEST-VOL"]
    prueba.unidad_medicion = "L"
    prueba.save()
    assert Medicion.objects.get(asignacion=asignaciones_medicion["TEST-VOL"]).unidad == "mL"


@pytest.mark.django_db
@pytest.mark.parametrize("estado", [EstadoEstudio.FINALIZADO, EstadoEstudio.INFORME_GENERADO])
def test_estudio_cerrado_rechaza_carga(estudio_mediciones, asignaciones_medicion, empleado, estado):
    Estudio.objects.filter(pk=estudio_mediciones.pk).update(estado=estado)
    with pytest.raises(
        CargarMedicionesError, match="Este estudio ya no admite carga de mediciones."
    ):
        cargar_mediciones(
            estudio_mediciones.pk, valores(asignaciones_medicion, TEST_PH="7"), empleado
        )
    assert not Medicion.objects.exists()


@pytest.mark.django_db
def test_omite_cargada_y_guarda_el_resto(estudio_mediciones, asignaciones_medicion, empleado):
    cargar_mediciones(
        estudio_mediciones.pk, valores(asignaciones_medicion, TEST_PH="7.20"), empleado
    )
    resultado = cargar_mediciones(
        estudio_mediciones.pk,
        valores(asignaciones_medicion, TEST_PH="9", TEST_VOL="18.5"),
        empleado,
    )
    assert [m.asignacion.prueba.codigo for m in resultado.guardadas] == ["TEST-VOL"]
    assert [(p.codigo, motivo) for p, motivo in resultado.omitidas] == [
        ("TEST-PH", "ya tenía una medición cargada")
    ]
    ph = Medicion.objects.get(asignacion=asignaciones_medicion["TEST-PH"])
    assert ph.valor_ingresado == Decimal("7.20")


@pytest.mark.django_db
def test_servicio_omite_calculada(estudio_mediciones, asignaciones_medicion, empleado):
    resultado = cargar_mediciones(
        estudio_mediciones.pk, valores(asignaciones_medicion, TEST_CALC="3"), empleado
    )
    assert resultado.guardadas == []
    assert [(p.codigo, motivo) for p, motivo in resultado.omitidas] == [
        ("TEST-CALC", "se calcula a partir de otras pruebas")
    ]
    calc = asignaciones_medicion["TEST-CALC"]
    calc.refresh_from_db()
    assert calc.estado == EstadoPruebaEstudio.PENDIENTE
    assert not Medicion.objects.exists()
    estudio_mediciones.refresh_from_db()
    assert estudio_mediciones.estado == EstadoEstudio.PENDIENTE_ANALISIS


@pytest.mark.django_db
def test_servicio_ignora_asignacion_de_otro_estudio(
    estudio_mediciones, asignaciones_medicion, estudio, asignacion, empleado
):
    resultado = cargar_mediciones(
        estudio_mediciones.pk,
        {asignacion.pk: Decimal("5"), **valores(asignaciones_medicion, TEST_PH="7")},
        empleado,
    )
    assert [m.asignacion.prueba.codigo for m in resultado.guardadas] == ["TEST-PH"]
    assert resultado.omitidas == []
    assert not Medicion.objects.filter(asignacion=asignacion).exists()


@pytest.mark.django_db
def test_cargar_mediciones_requiere_sesion_activa(
    estudio_mediciones, asignaciones_medicion, empleado
):
    from django.contrib.auth.models import AnonymousUser

    empleado.is_active = False
    for usuario in (AnonymousUser(), empleado):
        with pytest.raises(CargarMedicionesError, match="Se requiere una sesión activa."):
            cargar_mediciones(
                estudio_mediciones.pk, valores(asignaciones_medicion, TEST_PH="7"), usuario
            )
    assert not Medicion.objects.exists()
