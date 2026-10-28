from concurrent.futures import ThreadPoolExecutor
from io import StringIO
from threading import Barrier

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.db import close_old_connections, connection
from django.test.utils import CaptureQueriesContext

from clientes.models import Cliente
from estudios.management.commands.cargar_demo_us51 import PREFIJO, clave_muestra
from estudios.models import Estudio, TipoEstudio, TipoEstudioPrueba
from muestras.models import Muestra, Origen
from pruebas.models import Prueba

pytestmark = pytest.mark.django_db
MODELOS = (Cliente, Origen, Muestra, Prueba, TipoEstudio, TipoEstudioPrueba, Estudio)


@pytest.fixture
def demo(settings, monkeypatch, empleado):
    settings.DEBUG = True
    monkeypatch.setenv("AQUALAB_ENTORNO", "desarrollo")

    def ejecutar(*args):
        salida = StringIO()
        call_command("cargar_demo_us51", "--usuario", empleado.email, *args, stdout=salida)
        return salida.getvalue()

    return ejecutar


def conteos():
    return tuple(m.objects.count() for m in MODELOS)


@pytest.mark.parametrize("argumentos", [(), ("--dry-run",)])
def test_simulacion_sin_escrituras(demo, argumentos):
    with CaptureQueriesContext(connection) as consultas:
        salida = demo(*argumentos)
    assert "SIMULACIÓN" in salida and conteos() == (0,) * 7
    assert consultas.captured_queries
    # full_clean puede usar savepoints para comprobar constraints; no escribe filas.
    for consulta in consultas:
        sql = consulta["sql"].lstrip().upper()
        assert sql.startswith(("SELECT", "SAVEPOINT", "RELEASE SAVEPOINT"))
        assert "NEXTVAL(" not in sql and "SETVAL(" not in sql


def test_manifiesto_y_segunda_carga(demo, empleado):
    demo("--aplicar")
    assert conteos() == (2, 2, 2, 3, 4, 7, 0)
    assert Cliente.objects.filter(activo=False).count() == 1
    assert TipoEstudio.objects.filter(activo=False).count() == 1
    for letra in "AB":
        m = Muestra.objects.get(clave_borrador=clave_muestra(letra))
        assert m.numero_pi >= 200001 and m.cliente_id == m.origen.cliente_id
        assert m.registrada_por == empleado and m.nombre.startswith(PREFIJO)
    antes = {m: list(m.objects.order_by("pk").values()) for m in MODELOS}
    with CaptureQueriesContext(connection) as consultas:
        demo("--aplicar")
    assert antes == {m: list(m.objects.order_by("pk").values()) for m in MODELOS}
    assert not any(
        c["sql"].lstrip().upper().startswith(("INSERT", "UPDATE", "DELETE")) for c in consultas
    )
    demo("--dry-run")
    assert antes == {m: list(m.objects.order_by("pk").values()) for m in MODELOS}


@pytest.mark.parametrize("aplicar", [False, True])
def test_colision_no_sobrescribe(demo, aplicar):
    ajena = Prueba.objects.create(codigo="DEMO-US51-P03", nombre="Prueba preexistente ajena")
    with pytest.raises(CommandError, match="Colisión"):
        demo(*(["--aplicar"] if aplicar else []))
    assert conteos() == (0, 0, 0, 1, 0, 0, 0)
    ajena.refresh_from_db()
    assert ajena.nombre == "Prueba preexistente ajena"


def test_divergencia_tipo_no_se_restaura(demo):
    demo("--aplicar")
    t = TipoEstudio.objects.filter(activo=True).first()
    t.version += 1
    t.save()
    antes = {m: list(m.objects.order_by("pk").values()) for m in MODELOS}
    with pytest.raises(CommandError, match="divergencia"):
        demo("--aplicar")
    assert antes == {m: list(m.objects.order_by("pk").values()) for m in MODELOS}


def test_composicion_divergente(demo):
    demo("--aplicar")
    t = TipoEstudio.objects.get(nombre=f"{PREFIJO} Bacteriológico")
    t.pruebas.remove(t.pruebas.first())
    with pytest.raises(CommandError, match="composición"):
        demo("--aplicar")
    assert t.pruebas.count() == 1


@pytest.mark.parametrize(
    "entorno,debug", [(None, True), ("produccion", True), ("desarrollo", False), ("qa", False)]
)
def test_rechaza_entorno(demo, monkeypatch, settings, entorno, debug):
    settings.DEBUG = debug
    if entorno is None:
        monkeypatch.delenv("AQUALAB_ENTORNO")
    else:
        monkeypatch.setenv("AQUALAB_ENTORNO", entorno)
    with pytest.raises(CommandError, match="No producción"):
        demo("--aplicar")
    assert conteos() == (0,) * 7


def test_qa_explicito(demo, monkeypatch):
    monkeypatch.setenv("AQUALAB_ENTORNO", "qa")
    assert "SIMULACIÓN" in demo()


@pytest.mark.parametrize("existe", [True, False])
def test_usuario_no_valido(demo, empleado, existe):
    if existe:
        empleado.is_active = False
        empleado.save()
    else:
        empleado.delete()
    with pytest.raises(CommandError, match="usuario debe existir"):
        demo("--aplicar")
    assert conteos() == (0,) * 7


def test_fallo_servicio_revierte_y_se_reutiliza(demo, monkeypatch):
    ruta = "estudios.management.commands.cargar_demo_us51.registrar_muestra"
    from estudios.management.commands import cargar_demo_us51

    original = cargar_demo_us51.registrar_muestra

    def fallar(*args, **kwargs):
        original(*args, **kwargs)
        raise CommandError("fallo controlado después de registrar")

    with monkeypatch.context() as m:
        m.setattr(ruta, fallar)
        with pytest.raises(CommandError, match="fallo controlado"):
            demo("--aplicar")
    assert conteos() == (0,) * 7
    demo("--aplicar")
    assert conteos() == (2, 2, 2, 3, 4, 7, 0)


def test_pi_y_datos_ajenos_preservados(demo, muestra):
    antes = {m: list(m.objects.order_by("pk").values()) for m in (Cliente, Origen, Muestra)}
    demo("--aplicar")
    assert Muestra.objects.count() == 3
    assert (
        Muestra.objects.exclude(pk=muestra.pk).filter(numero_pi__gt=muestra.numero_pi).count() == 2
    )
    for modelo, filas in antes.items():
        assert (
            list(modelo.objects.filter(pk__in=[f["id"] for f in filas]).order_by("pk").values())
            == filas
        )


def test_datos_permiten_t037(demo, cliente_http):
    demo("--aplicar")
    r = cliente_http.get("/estudios/crear/")
    assert PREFIJO in r.content.decode() and "Tipo desactivado" not in r.content.decode()
    m = Muestra.objects.get(clave_borrador=clave_muestra("B"))
    t = TipoEstudio.objects.get(nombre=f"{PREFIJO} Vuelco a canal")
    r = cliente_http.post("/estudios/crear/", {"muestra": m.pk, "tipo": t.pk})
    resumen = cliente_http.get(r.url)
    assert "DEMO-US51-P01" in resumen.content.decode()
    assert not Estudio.objects.exists()
    cliente_http.post(
        "/estudios/crear/confirmar/",
        {
            "accion": "confirmar",
            "token": resumen.context["borrador"]["token"],
        },
    )
    assert Estudio.objects.get().pruebas_asignadas.count() == 2
    m.cliente.refresh_from_db()
    assert not m.cliente.activo


@pytest.mark.django_db(transaction=True)
def test_cargas_concurrentes_postgresql(demo, empleado):
    assert connection.vendor == "postgresql"
    barrera = Barrier(2)

    def cargar():
        close_old_connections()
        try:
            barrera.wait(timeout=10)
            salida = StringIO()
            call_command(
                "cargar_demo_us51", "--usuario", empleado.email, "--aplicar", stdout=salida
            )
        finally:
            connection.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        resultados = [pool.submit(cargar) for _ in range(2)]
        for resultado in resultados:
            resultado.result(timeout=20)
    assert conteos() == (2, 2, 2, 3, 4, 7, 0)
