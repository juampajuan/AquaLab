import uuid

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError

from estudios.models import TipoEstudio, TipoEstudioPrueba

pytestmark = pytest.mark.django_db


def test_nombre_tipo_unico(tipo):
    otro = TipoEstudio(nombre="  TIPO DE TEST ")
    with pytest.raises(ValidationError):
        otro.full_clean()
    with pytest.raises(IntegrityError), transaction.atomic():
        TipoEstudio.objects.create(nombre="TIPO DE TEST")


def test_descripcion_opcional_y_nombres_distintos():
    for nombre in ["Canal", "Cánal", "Ca nal", "Ca  nal"]:
        t = TipoEstudio(nombre=nombre)
        t.full_clean()
        t.save()
        assert t.descripcion == "" and t.version == 1


def test_version_positiva(tipo):
    with pytest.raises(IntegrityError), transaction.atomic():
        TipoEstudio.objects.filter(pk=tipo.pk).update(version=0)


def test_asociacion_tipo_unica_y_protegida(tipo, pruebas):
    with pytest.raises(IntegrityError), transaction.atomic():
        TipoEstudioPrueba.objects.create(tipo=tipo, prueba=pruebas[0])
    with pytest.raises(ProtectedError):
        pruebas[0].delete()


def test_modelos_estudio(datos, empleado, tipo, muestra):
    from estudios.models import Estudio, PruebaEstudio
    from estudios.servicios import crear_estudio

    e = crear_estudio(datos, empleado)
    with pytest.raises(IntegrityError), transaction.atomic():
        PruebaEstudio.objects.create(estudio=e, prueba=tipo.pruebas.first())
    with pytest.raises(ProtectedError):
        muestra.delete()
    with pytest.raises(ProtectedError):
        tipo.delete()
    with pytest.raises(IntegrityError), transaction.atomic():
        Estudio.objects.create(
            muestra=muestra,
            tipo=tipo,
            creado_por=empleado,
            tipo_nombre_snapshot="Test",
            tipo_version_snapshot=1,
            clave_idempotencia=uuid.UUID(datos["clave"]),
        )


@pytest.mark.parametrize(
    ("campo", "valor"),
    [
        ("tipo_nombre_snapshot", "x" * 151),
        ("tipo_version_snapshot", 0),
    ],
)
def test_validaciones_estudio(datos, empleado, campo, valor):
    from estudios.servicios import crear_estudio

    e = crear_estudio(datos, empleado)
    e.full_clean()
    setattr(e, campo, valor)
    with pytest.raises(ValidationError):
        e.full_clean()


def test_uuid_obligatorio_y_identificador_propio(muestra, tipo, empleado):
    from estudios.models import Estudio, PruebaEstudio
    from estudios.servicios import crear_estudio

    with pytest.raises(IntegrityError), transaction.atomic():
        Estudio.objects.create(
            muestra=muestra,
            tipo=tipo,
            creado_por=empleado,
            tipo_nombre_snapshot=tipo.nombre,
            tipo_version_snapshot=1,
        )
    datos = {
        "clave": str(uuid.uuid4()),
        "muestra": muestra.pk,
        "tipo": tipo.pk,
        "version": tipo.version,
    }
    e = crear_estudio(datos, empleado)
    assert e.pk != muestra.numero_pi
    campo = Estudio._meta.get_field("estado")
    assert not campo.editable
    assert list(campo.choices) == [
        ("pendiente_analisis", "Pendiente de análisis"),
        ("en_proceso", "En proceso"),
        ("finalizado", "Finalizado"),
        ("informe_generado", "Informe generado"),
    ]
    assert not Estudio._meta.get_field("clave_idempotencia").null
    campo_prueba = PruebaEstudio._meta.get_field("estado")
    assert not campo_prueba.editable
    assert campo_prueba.default == "pendiente"
    assert list(campo_prueba.choices) == [
        ("pendiente", "Pendiente"),
        ("cargada", "Cargada"),
        ("completada", "Completada"),
    ]
    assert list(e.pruebas_asignadas.values_list("estado", flat=True)) == ["pendiente", "pendiente"]


def test_admite_modificaciones_solo_pendiente_analisis(estudio):
    from estudios.models import EstadoEstudio

    assert estudio.admite_modificaciones
    for estado in EstadoEstudio.values:
        estudio.estado = estado
        assert estudio.admite_modificaciones == (estado == EstadoEstudio.PENDIENTE_ANALISIS)


def test_puede_quitarse_solo_pendiente(asignacion):
    from estudios.models import EstadoPruebaEstudio

    assert asignacion.puede_quitarse()
    for estado in (EstadoPruebaEstudio.CARGADA, EstadoPruebaEstudio.COMPLETADA):
        asignacion.estado = estado
        assert not asignacion.puede_quitarse()


def crear_medicion(asignacion, usuario, valor="7.20", decimales=2):
    from decimal import Decimal

    from estudios.models import Medicion

    return Medicion.objects.create(
        asignacion=asignacion,
        valor=Decimal(valor),
        decimales=decimales,
        unidad="UpH",
        cargada_por=usuario,
    )


def test_valor_ingresado_conserva_ceros_finales(asignaciones_medicion, empleado):
    from decimal import Decimal

    from estudios.models import Medicion

    crear_medicion(asignaciones_medicion["TEST-PH"], empleado)
    crear_medicion(asignaciones_medicion["TEST-VOL"], empleado, valor="18", decimales=0)
    ph = Medicion.objects.get(asignacion=asignaciones_medicion["TEST-PH"])
    vol = Medicion.objects.get(asignacion=asignaciones_medicion["TEST-VOL"])
    assert ph.valor_ingresado == Decimal("7.20")
    assert ph.valor_ingresado.as_tuple().exponent == -2
    assert vol.valor_ingresado == Decimal("18")
    assert vol.valor_ingresado.as_tuple().exponent == 0


def test_una_medicion_por_asignacion(asignacion, empleado):
    crear_medicion(asignacion, empleado)
    with pytest.raises(IntegrityError), transaction.atomic():
        crear_medicion(asignacion, empleado, valor="8")


def test_medicion_decimales_validos(asignacion, empleado):
    with pytest.raises(IntegrityError), transaction.atomic():
        crear_medicion(asignacion, empleado, valor="1", decimales=7)


def test_asignacion_con_medicion_protegida(asignacion, empleado):
    crear_medicion(asignacion, empleado)
    with pytest.raises(ProtectedError), transaction.atomic():
        asignacion.delete()


@pytest.mark.parametrize(
    "estado,admite",
    [
        ("pendiente_analisis", True),
        ("en_proceso", True),
        ("finalizado", False),
        ("informe_generado", False),
    ],
)
def test_admite_mediciones_por_estado(estudio, estado, admite):
    estudio.estado = estado
    assert estudio.admite_mediciones is admite


def crear_resultado(asignacion, valor="23.5"):
    from decimal import Decimal

    from estudios.models import Resultado

    return Resultado.objects.create(
        asignacion=asignacion, valor=Decimal(valor), unidad="mg/l", formula="x*10"
    )


@pytest.mark.parametrize(
    "valor,esperado",
    [
        ("23.5", "23.5"),
        ("0.00412", "0.0041"),
        ("1234.5", "1234.5"),
        ("1.17085", "1.1709"),
        ("0", "0"),
        ("-0.00001", "0"),
        ("-2.5", "-2.5"),
        ("80", "80"),
        ("6000", "6000"),
        ("300.0000000000", "300"),
    ],
)
def test_valor_mostrado(asignacion, valor, esperado):
    from decimal import Decimal

    from estudios.models import Resultado

    crear_resultado(asignacion, valor)
    mostrado = Resultado.objects.get(asignacion=asignacion).valor_mostrado
    assert mostrado == Decimal(esperado)
    assert str(mostrado) == esperado


def test_valor_mostrado_entero_sin_exponente(asignacion):
    from django.utils.formats import localize

    from estudios.models import Resultado

    crear_resultado(asignacion, "1000")
    assert localize(Resultado.objects.get(asignacion=asignacion).valor_mostrado) == "1000"


def test_un_resultado_por_asignacion(asignacion):
    crear_resultado(asignacion)
    with pytest.raises(IntegrityError), transaction.atomic():
        crear_resultado(asignacion, "1")


def test_asignacion_con_resultado_protegida(asignacion):
    crear_resultado(asignacion)
    with pytest.raises(ProtectedError), transaction.atomic():
        asignacion.delete()


@pytest.mark.parametrize(
    "estado,admite",
    [
        ("pendiente_analisis", True),
        ("en_proceso", True),
        ("finalizado", True),
        ("informe_generado", False),
    ],
)
def test_admite_correcciones_por_estado(estudio, estado, admite):
    estudio.estado = estado
    assert estudio.admite_correcciones is admite


@pytest.mark.parametrize(
    "texto,esperado",
    [
        ("mg/l", "mg/l"),
        ("", "Sin unidad"),
        ("--", "Sin unidad"),
        (" -- ", "Sin unidad"),
        (None, "Sin unidad"),
    ],
)
def test_filtro_unidad(texto, esperado):
    from config.ui import unidad

    assert unidad(texto) == esperado


def test_medicion_correccion_completa(asignacion, empleado):
    from django.utils import timezone

    from estudios.models import Medicion

    medicion = crear_medicion(asignacion, empleado)
    for cambios in ({"corregida_por": empleado}, {"fecha_correccion": timezone.now()}):
        with pytest.raises(IntegrityError), transaction.atomic():
            Medicion.objects.filter(pk=medicion.pk).update(**cambios)
    Medicion.objects.filter(pk=medicion.pk).update(
        corregida_por=empleado, fecha_correccion=timezone.now()
    )
