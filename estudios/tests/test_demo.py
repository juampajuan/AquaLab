"""Tests de los datos de demo (SCRUM-78): comando `cargar_demo` y `estudios/demo.py`."""

import datetime as dt
import io
from decimal import Decimal
from unittest import mock

import pytest
from django.contrib.auth import get_user_model
from django.core.management import CommandError, call_command
from django.db import transaction
from django.utils import timezone

from clientes.models import Cliente
from estudios import demo
from estudios.models import (
    EstadoEstudio,
    EstadoPruebaEstudio,
    Estudio,
    Medicion,
    TipoEstudio,
    TipoEstudioPrueba,
    Validacion,
)
from informes.firmas import leer_firma
from informes.models import Informe
from muestras.models import Muestra, Origen
from pruebas.models import Prueba

pytestmark = pytest.mark.django_db

ZONA = dt.timezone(dt.timedelta(hours=-3))


def dia_2_del_mes():
    """Un `ahora` de principio de mes (el caso difícil para las fechas) en el pasado real."""
    hoy = timezone.localtime()
    ahora = hoy.replace(day=2, hour=12, minute=0, second=0, microsecond=0)
    if ahora > hoy:  # Hoy es día 1: se usa el día 2 del mes anterior.
        ahora = (ahora.replace(day=1) - dt.timedelta(days=1)).replace(day=2)
    return ahora


def cargar(ahora=None):
    return demo.cargar_demo(io.StringIO(), ahora=ahora or dia_2_del_mes())


@pytest.fixture
def entorno(settings, monkeypatch):
    settings.DEBUG = True
    monkeypatch.setenv("AQUALAB_ENTORNO", "desarrollo")


@pytest.fixture
def cargada(catalogo):
    ahora = dia_2_del_mes()
    resumen = cargar(ahora)
    return ahora, resumen


def mes_de(ahora, fecha):
    """Meses entre la fecha y `ahora` (0 = mes actual)."""
    return (ahora.year - fecha.year) * 12 + ahora.month - fecha.month


def estudios_de(origen_nombre):
    return Estudio.objects.filter(muestra__origen__nombre=origen_nombre).select_related(
        "muestra", "informe"
    )


def estudio(ahora, origen_nombre, mes, tipo=None):
    candidatos = [
        e
        for e in estudios_de(origen_nombre)
        if mes_de(ahora, e.muestra.fecha_muestreo) == mes
        and (tipo is None or e.tipo_nombre_snapshot == tipo)
    ]
    assert len(candidatos) == 1, (origen_nombre, mes, tipo, candidatos)
    return candidatos[0]


# --- Base: fechas y reloj (T003) -------------------------------------------------------------


@pytest.mark.parametrize("dia", [2, 28])
def test_fechas_ordenadas_y_no_futuras(dia):
    ahora = dt.datetime(2026, 11, dia, 9, 0, tzinfo=ZONA)
    for indice, origen in enumerate(demo.ORIGENES):
        for mes in range(6):
            fechas = demo.Fechas(ahora, origen, indice, mes)
            pasos = [
                fechas.muestreo,
                fechas.ingreso,
                fechas.estudio,
                fechas.carga,
                fechas.validacion,
                fechas.emision,
            ]
            assert pasos == sorted(pasos)
            assert pasos[-1] <= ahora
            assert mes_de(ahora, fechas.muestreo) == mes
    estancado = next(o for o in demo.ORIGENES if o.clave == "pozo-domiciliario")
    indice = demo.ORIGENES.index(estancado)
    assert demo.Fechas(ahora, estancado, indice, 1).carga <= ahora - dt.timedelta(days=10)


def test_reloj(catalogo, empleado, muestra, tipo):
    import uuid

    from estudios.servicios import crear_estudio

    momento = dt.datetime(2026, 5, 4, 10, 0, tzinfo=ZONA)
    datos = {"clave": str(uuid.uuid4()), "muestra": muestra.pk, "tipo": tipo.pk}
    with demo.reloj(momento):
        creado = crear_estudio({**datos, "version": tipo.version}, empleado)
    assert creado.fecha_creacion == momento
    otro = crear_estudio({**datos, "clave": str(uuid.uuid4()), "version": tipo.version}, empleado)
    assert otro.fecha_creacion > momento + dt.timedelta(days=30)


# --- US1: la demo completa --------------------------------------------------------------------


def test_clientes_origenes_y_muestras(cargada):
    ahora, _ = cargada
    clientes = Cliente.objects.filter(email__endswith="@demo.aqualab")
    assert clientes.count() == 3
    assert all("demo" not in c.nombre_completo.lower() for c in clientes)
    assert {c.tipo_documento for c in clientes} == {"CUIT", "DNI"}
    origenes = Origen.objects.filter(cliente__in=clientes)
    assert origenes.count() == 7
    for origen in origenes:
        meses = sorted(
            mes_de(ahora, m.fecha_muestreo) for m in Muestra.objects.filter(origen=origen)
        )
        assert meses == [0, 1, 2, 3, 4, 5], origen.nombre


def test_tipos_demo(cargada):
    for nombre, codigos in demo.TIPOS.items():
        tipo = TipoEstudio.objects.get(nombre=nombre)
        assert set(tipo.pruebas.values_list("codigo", flat=True)) == set(codigos)


def test_estudios_por_estado(cargada):
    ahora, _ = cargada
    estudios = Estudio.objects.filter(muestra__cliente__email__endswith="@demo.aqualab")
    for estado in EstadoEstudio.values:
        assert estudios.filter(estado=estado).count() >= 2, estado
    esperado = {
        EstadoEstudio.PENDIENTE_ANALISIS: [
            ("Tanque domiciliario", 0, None),
            ("Escuela N° 12", 0, None),
        ],
        EstadoEstudio.EN_PROCESO: [
            ("Pozo 2", 0, None),
            ("Salida a colectora", 0, None),
            ("Pozo domiciliario", 1, None),
        ],
        EstadoEstudio.FINALIZADO: [
            ("Pozo 1", 0, None),
            ("Tanque elevado", 0, "Físico-químico básico"),
            ("Escuela N° 12", 1, None),
        ],
        EstadoEstudio.INFORME_GENERADO: [
            ("Pozo domiciliario", 0, None),
            ("Tanque elevado", 0, demo.BACT),
            ("Pozo 1", 3, None),
        ],
    }
    for estado, casos in esperado.items():
        for origen, mes, tipo in casos:
            assert estudio(ahora, origen, mes, tipo).estado == estado, (origen, mes)
    anteriores = [e for e in estudios if mes_de(ahora, e.muestra.fecha_muestreo) >= 1]
    con_informe = [e for e in anteriores if e.estado == EstadoEstudio.INFORME_GENERADO]
    assert len(con_informe) == len(anteriores) - 2


def test_informes_firmados_y_numeracion(cargada):
    informes = list(Informe.objects.order_by("numero"))
    assert informes
    assert [i.numero for i in informes] == list(range(1, len(informes) + 1))
    for informe in informes:
        assert informe.contenido["firma"]["matricula"] == "MP 0000 (DEMO)"
        assert informe.emitido_por.email == "bioquimico@demo.aqualab"
    numeros = sorted(Muestra.objects.values_list("numero_pi", flat=True))
    assert numeros == list(range(numeros[0], numeros[0] + len(numeros)))


def test_fechas_coherentes(cargada):
    ahora, _ = cargada
    meses_con_informe = set()
    respuestas = set()
    for est in Estudio.objects.select_related("muestra").prefetch_related(
        "pruebas_asignadas__medicion", "pruebas_asignadas__validaciones"
    ):
        muestra = est.muestra
        pasos = [muestra.fecha_ingreso, est.fecha_creacion.astimezone(ZONA).date()]
        assert muestra.fecha_muestreo <= muestra.fecha_ingreso
        assert est.fecha_creacion <= ahora
        for asignacion in est.pruebas_asignadas.all():
            medicion = getattr(asignacion, "medicion", None)
            if medicion:
                assert est.fecha_creacion <= medicion.fecha_carga <= ahora
                for validacion in asignacion.validaciones.all():
                    assert medicion.fecha_carga <= validacion.fecha_validacion <= ahora
        informe = Informe.objects.filter(estudio=est).first()
        if informe:
            assert informe.fecha_emision <= ahora
            assert pasos[1] <= informe.fecha_emision.astimezone(ZONA).date()
            meses_con_informe.add(mes_de(ahora, informe.fecha_emision.astimezone(ZONA)))
            respuestas.add((informe.fecha_emision.astimezone(ZONA).date() - pasos[0]).days)
    assert len(meses_con_informe) >= 5
    assert len(respuestas) >= 4


def test_alertas_del_dashboard(cargada):
    ahora, _ = cargada
    estancado = estudio(ahora, "Pozo domiciliario", 1)
    assert estancado.estado == EstadoEstudio.EN_PROCESO
    ultima = Medicion.objects.filter(asignacion__estudio=estancado).latest("fecha_carga")
    assert ultima.fecha_carga <= ahora - dt.timedelta(days=7)
    sin_informe = estudio(ahora, "Escuela N° 12", 1)
    assert sin_informe.estado == EstadoEstudio.FINALIZADO
    assert not Informe.objects.filter(estudio=sin_informe).exists()


def test_fuera_de_norma_ld_y_presencia(cargada):
    ahora, _ = cargada
    fuera = Validacion.objects.filter(anulada=False, evaluacion="fuera_de_norma")
    origenes = set(fuera.values_list("asignacion__estudio__muestra__origen__nombre", flat=True))
    assert len(origenes) >= 3
    colectora = estudio(ahora, "Salida a colectora", 2)
    ss10 = colectora.pruebas_asignadas.get(prueba__codigo="SS10")
    assert ss10.resultado.valor == Decimal("0.05")
    filas = {p["codigo"]: p for p in colectora.informe.contenido["pruebas"]}
    assert filas["SS10"]["resultado_texto"] == "< 0,1"
    tanque = estudio(ahora, "Tanque domiciliario", 3)
    filas = {p["codigo"]: p for p in tanque.informe.contenido["pruebas"]}
    assert filas["ECOLI"]["resultado_texto"] == "Presente"
    assert filas["ECOLI"]["evaluacion"] == "fuera_de_norma"


def test_desvio_en_pozo_2(cargada):
    ahora, _ = cargada

    def cloruro(mes):
        return estudio(ahora, "Pozo 2", mes).pruebas_asignadas.get(prueba__codigo="CL-")

    previos = [cloruro(m) for m in (5, 4, 3, 2)]
    for asignacion in previos:
        assert asignacion.estado == EstadoPruebaEstudio.COMPLETADA
        assert Decimal("118") <= asignacion.resultado.valor <= Decimal("124")
    ultimo = cloruro(1)
    assert ultimo.estado == EstadoPruebaEstudio.COMPLETADA
    assert ultimo.resultado.valor == Decimal("415")
    promedio = sum(a.resultado.valor for a in previos[1:]) / 3
    assert ultimo.resultado.valor >= 3 * promedio
    actual = cloruro(0)
    assert actual.estado == EstadoPruebaEstudio.CARGADA
    assert actual.resultado.valor == Decimal("430")


def resumen_de_valores():
    return {
        "clientes": sorted(
            Cliente.objects.filter(email__endswith="@demo.aqualab").values_list(
                "numero_documento", "razon_social", "nombre"
            )
        ),
        "origenes": sorted(Origen.objects.values_list("cliente__numero_documento", "nombre")),
        "mediciones": sorted(
            (
                m.asignacion.estudio.muestra.origen.nombre,
                m.asignacion.estudio.tipo_nombre_snapshot,
                m.asignacion.prueba.codigo,
                str(m.valor),
            )
            for m in Medicion.objects.select_related(
                "asignacion__prueba", "asignacion__estudio__muestra__origen"
            )
        ),
        "evaluaciones": sorted(
            Validacion.objects.values_list("asignacion__prueba__codigo", "evaluacion")
        ),
    }


def test_valores_reproducibles(catalogo):
    ahora = dia_2_del_mes()
    with transaction.atomic():
        cargar(ahora)
        primera = resumen_de_valores()
        transaction.set_rollback(True)
    assert not Cliente.objects.filter(email__endswith="@demo.aqualab").exists()
    cargar(ahora)
    assert resumen_de_valores() == primera


def test_resumen(catalogo, entorno):
    salida = io.StringIO()
    call_command("cargar_demo", stdout=salida)
    texto = salida.getvalue()
    assert "Demo cargada." in texto
    for etiqueta in EstadoEstudio.labels:
        assert etiqueta in texto
    assert "tecnico@demo.aqualab" in texto
    assert "bioquimico@demo.aqualab" in texto
    assert "Demo-1234" in texto


def test_respeta_datos_existentes(catalogo, cargada_previa):
    cliente, muestra, informe = cargada_previa
    antes = (cliente.nombre, muestra.numero_pi, informe.numero, informe.contenido)
    cargar()
    cliente.refresh_from_db()
    muestra.refresh_from_db()
    informe.refresh_from_db()
    assert (cliente.nombre, muestra.numero_pi, informe.numero, informe.contenido) == antes
    demo_pi = Muestra.objects.exclude(pk=muestra.pk).order_by("numero_pi").first().numero_pi
    assert demo_pi == muestra.numero_pi + 1
    demo_inf = Informe.objects.exclude(pk=informe.pk).order_by("numero").first().numero
    assert demo_inf == informe.numero + 1


@pytest.fixture
def cargada_previa(estudio_de, empleado, bioquimico):
    from estudios.tests.utiles import cargar as cargar_mediciones
    from estudios.tests.utiles import validar
    from informes.servicios import emitir_informe

    est = estudio_de("PH")
    cargar_mediciones(est, empleado, PH="7.4")
    validar(est, bioquimico, "PH")
    informe = emitir_informe(est.pk, bioquimico)
    return est.muestra.cliente, est.muestra, informe


# --- US2: usuarios demo -----------------------------------------------------------------------


def test_usuarios_demo(cargada):
    Usuario = get_user_model()
    tecnico = Usuario.objects.get(email="tecnico@demo.aqualab")
    bioquimico = Usuario.objects.get(email="bioquimico@demo.aqualab")
    for usuario in (tecnico, bioquimico):
        assert usuario.is_active and usuario.aprobada
        assert usuario.check_password("Demo-1234")
    assert not tecnico.groups.exists()
    assert not tecnico.has_perm("estudios.validar_resultados")
    assert not tecnico.has_perm("informes.emitir_informes")
    assert set(bioquimico.groups.values_list("name", flat=True)) == {
        "Bioquímicos",
        "Administradores",
    }
    firma = bioquimico.firma_profesional
    assert firma.matricula == "MP 0000 (DEMO)"
    assert leer_firma(firma.data_url) == bytes(firma.imagen)
    assert set(Medicion.objects.values_list("cargada_por__email", flat=True)) == {tecnico.email}
    assert set(Validacion.objects.values_list("validada_por__email", flat=True)) == {
        bioquimico.email
    }
    estudios = Estudio.objects.all()
    assert estudios.filter(pruebas_asignadas__estado=EstadoPruebaEstudio.PENDIENTE).exists()
    assert estudios.filter(pruebas_asignadas__estado=EstadoPruebaEstudio.CARGADA).exists()
    assert estudios.filter(estado=EstadoEstudio.FINALIZADO, informe__isnull=True).exists()


# --- US3: solo en desarrollo y sin duplicar ---------------------------------------------------


@pytest.mark.parametrize(("variable", "debug"), [(None, True), ("qa", True), ("desarrollo", False)])
def test_rechaza_fuera_de_desarrollo(catalogo, settings, monkeypatch, variable, debug):
    settings.DEBUG = debug
    if variable is None:
        monkeypatch.delenv("AQUALAB_ENTORNO", raising=False)
    else:
        monkeypatch.setenv("AQUALAB_ENTORNO", variable)
    with pytest.raises(CommandError) as error:
        call_command("cargar_demo", stdout=io.StringIO())
    assert str(error.value) == (
        "cargar_demo solo corre en desarrollo: requiere AQUALAB_ENTORNO=desarrollo y DEBUG=True."
    )
    assert not Cliente.objects.exists()


def test_segunda_ejecucion_no_duplica(catalogo, entorno):
    call_command("cargar_demo", stdout=io.StringIO())
    cantidades = (Cliente.objects.count(), Estudio.objects.count(), Informe.objects.count())
    salida = io.StringIO()
    call_command("cargar_demo", stdout=salida)
    assert salida.getvalue().startswith("La demo ya está cargada.")
    assert (Cliente.objects.count(), Estudio.objects.count(), Informe.objects.count()) == (
        cantidades
    )


def test_conflicto_de_usuario(catalogo, entorno, django_user_model):
    django_user_model.objects.create_user(email="tecnico@demo.aqualab", password="x" * 12)
    with pytest.raises(CommandError) as error:
        call_command("cargar_demo", stdout=io.StringIO())
    assert str(error.value) == (
        "Ya existe el usuario tecnico@demo.aqualab y no es de la demo. No se cargó nada."
    )
    assert not Cliente.objects.exists()


def test_conflicto_de_tipo(catalogo, entorno):
    tipo = TipoEstudio.objects.create(nombre="Bacteriológico básico")
    TipoEstudioPrueba.objects.create(tipo=tipo, prueba=Prueba.objects.get(codigo="PH"))
    with pytest.raises(CommandError) as error:
        call_command("cargar_demo", stdout=io.StringIO())
    assert str(error.value) == (
        "Ya existe el tipo de estudio «Bacteriológico básico» con otras pruebas. No se cargó nada."
    )
    assert not Cliente.objects.exists()


def test_reutiliza_tipo_igual(catalogo, entorno):
    tipo = TipoEstudio.objects.create(nombre=demo.BACT)
    for codigo in demo.TIPOS[demo.BACT]:
        TipoEstudioPrueba.objects.create(tipo=tipo, prueba=Prueba.objects.get(codigo=codigo))
    call_command("cargar_demo", stdout=io.StringIO())
    assert TipoEstudio.objects.filter(nombre__iexact=demo.BACT).count() == 1
    tipo.refresh_from_db()
    assert tipo.version == 1
    assert Estudio.objects.filter(tipo=tipo).exists()


def test_tipos_de_la_demo_vieja_no_bloquean(catalogo, entorno):
    """La demo vieja (cargar_demo_us51) creaba «Bacteriológico», «Físico-Químico» y «Vuelco a
    canal» con otras pruebas: no chocan con los nombres de la demo nueva."""
    ph = Prueba.objects.get(codigo="PH")
    for nombre in ("Bacteriológico", "Físico-Químico", "Vuelco a canal"):
        tipo = TipoEstudio.objects.create(nombre=nombre)
        TipoEstudioPrueba.objects.create(tipo=tipo, prueba=ph)
    call_command("cargar_demo", stdout=io.StringIO())
    assert Cliente.objects.filter(email__endswith="@demo.aqualab").count() == 3
    assert set(TipoEstudio.objects.get(nombre="Bacteriológico").pruebas.all()) == {ph}


def test_importa_catalogo_si_falta(entorno):
    assert not Prueba.objects.exists()
    salida = io.StringIO()
    call_command("cargar_demo", stdout=salida)
    assert Prueba.objects.exists()
    assert "catálogo" in salida.getvalue()
    assert Cliente.objects.filter(email__endswith="@demo.aqualab").count() == 3


def test_no_reimporta_catalogo(catalogo, entorno):
    Prueba.objects.filter(codigo="TURBIDEZ").update(nombre="Turbidez (editada)")
    call_command("cargar_demo", stdout=io.StringIO())
    assert Prueba.objects.get(codigo="TURBIDEZ").nombre == "Turbidez (editada)"


def test_falla_no_deja_nada(catalogo, entorno):
    original = demo.emitir_informe
    llamadas = []

    def emitir_y_fallar(*args, **kwargs):
        llamadas.append(1)
        if len(llamadas) == 3:
            raise RuntimeError("falla simulada")
        return original(*args, **kwargs)

    with mock.patch.object(demo, "emitir_informe", emitir_y_fallar):
        with pytest.raises(CommandError) as error:
            call_command("cargar_demo", stdout=io.StringIO())
    assert str(error.value) == ("No se pudo cargar la demo: falla simulada. No se guardó nada.")
    assert not Cliente.objects.exists()
    assert not Muestra.objects.exists()
    assert not Informe.objects.exists()
    assert not get_user_model().objects.filter(email__endswith="@demo.aqualab").exists()


def test_comando_viejo_eliminado():
    with pytest.raises(CommandError, match="Unknown command"):
        call_command("cargar_demo_us51")


# Desvíos sin revisar que deja el guion (US 8.2): solo el Cloruro de Pozo 2 del mes actual. Si un
# cambio del guion suma otro, actualizar este número y quickstart.md.
CANTIDAD_PENDIENTES_DEMO = 1


def test_desvios_de_la_demo(cargada):
    """US 8.2: el Cloruro de Pozo 2 del mes actual es un desvío sin revisar y el del mes
    anterior quedó revisado al validarse, con observación."""
    from estudios import desvios

    ahora, _ = cargada
    actual = estudio(ahora, "Pozo 2", 0).pruebas_asignadas.get(prueba__codigo="CL-")
    pendientes = desvios.pendientes()
    (pozo_2,) = [p for p in pendientes if p.asignacion.pk == actual.pk]
    assert pozo_2.deteccion.valor == Decimal(430)
    assert pozo_2.deteccion.referencia == Decimal(124)
    assert pozo_2.deteccion.porcentaje == Decimal("246.8")

    anterior = estudio(ahora, "Pozo 2", 1).pruebas_asignadas.get(prueba__codigo="CL-")
    validacion = anterior.validaciones.get(anulada=False)
    assert validacion.observacion == "Se repitió la medición: el valor es correcto."
    assert validacion.desvio_referencia == Decimal(121)
    assert validacion.desvio_umbral == Decimal(30)
    assert validacion.validada_por.email == f"bioquimico@{demo.DOMINIO}"

    # Los pendientes son solo de estudios que el guion deja sin validar del todo.
    assert {p.estudio.estado for p in pendientes} <= {EstadoEstudio.EN_PROCESO}
    assert len(pendientes) == CANTIDAD_PENDIENTES_DEMO
