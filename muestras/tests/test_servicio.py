import threading

import pytest
from django.contrib.auth import get_user_model
from django.db import DatabaseError, connection
from django.utils import timezone

from muestras.models import Muestra, Origen
from muestras.servicios import MuestraNoDisponible, registrar_muestra

pytestmark = pytest.mark.django_db


@pytest.fixture
def datos(cliente_a, origen_a, hoy):
    """Borrador de sesión válido, como lo deja el formulario."""
    return {
        "cliente": cliente_a.pk,
        "origen": origen_a.pk,
        "origen_nuevo": "",
        "fecha_muestreo": hoy.isoformat(),
        "fecha_ingreso": hoy.isoformat(),
        "sitio_extraccion": "Canilla de salida del tanque",
        "tipo_vertido": "agua",
        "nombre": "",
        "responsable_muestreo": "",
    }


def test_primera_muestra_recibe_pi_200001(datos, empleado):
    muestra = registrar_muestra(datos, empleado)

    assert muestra.numero_pi == 200001


def test_pi_es_maximo_mas_uno(datos, empleado, crear_muestra):
    crear_muestra(200001)
    crear_muestra(200007)

    muestra = registrar_muestra(datos, empleado)

    assert muestra.numero_pi == 200008


def test_registrar_guarda_estado_usuario_y_fecha(datos, empleado, cliente_a, origen_a, hoy):
    muestra = registrar_muestra(datos, empleado)
    muestra.refresh_from_db()

    assert muestra.estado == "ingresada"
    assert muestra.registrada_por == empleado
    assert abs((timezone.now() - muestra.fecha_registro).total_seconds()) < 60
    assert muestra.cliente == cliente_a
    assert muestra.origen == origen_a
    assert muestra.fecha_muestreo == hoy
    assert muestra.fecha_ingreso == hoy
    assert muestra.sitio_extraccion == "Canilla de salida del tanque"
    assert muestra.tipo_vertido == "agua"


def test_registrar_rechaza_cliente_inactivo_u_origen_ajeno(datos, empleado, cliente_a, origen_b):
    with pytest.raises(MuestraNoDisponible) as error:
        registrar_muestra({**datos, "origen": origen_b.pk}, empleado)
    assert error.value.mensaje == "El origen no pertenece al cliente seleccionado."

    cliente_a.activo = False
    cliente_a.save()
    with pytest.raises(MuestraNoDisponible) as error:
        registrar_muestra(datos, empleado)
    assert error.value.mensaje == "El cliente no está disponible."

    assert not Muestra.objects.exists()


def test_error_al_guardar_no_consume_pi(datos, empleado, monkeypatch):
    def fallar(**kwargs):
        raise DatabaseError("falla simulada")

    with monkeypatch.context() as parche:
        parche.setattr(Muestra.objects, "create", fallar)
        with pytest.raises(DatabaseError):
            registrar_muestra(datos, empleado)

    assert not Muestra.objects.exists()
    assert registrar_muestra(datos, empleado).numero_pi == 200001


@pytest.mark.django_db(transaction=True)
def test_registros_concurrentes_no_repiten_pi(datos, empleado):
    cantidad = 5
    barrera = threading.Barrier(cantidad)
    numeros = []
    nombres = []
    errores = []
    usuario_pk = empleado.pk

    def registrar():
        try:
            usuario = get_user_model().objects.get(pk=usuario_pk)
            barrera.wait(timeout=10)
            muestra = registrar_muestra(dict(datos), usuario)
            numeros.append(muestra.numero_pi)
            nombres.append(muestra.nombre)
        except Exception as exc:  # noqa: BLE001 - se informa en el assert
            errores.append(exc)
        finally:
            connection.close()

    hilos = [threading.Thread(target=registrar) for _ in range(cantidad)]
    for hilo in hilos:
        hilo.start()
    for hilo in hilos:
        hilo.join()

    assert errores == []
    assert sorted(numeros) == list(range(200001, 200001 + cantidad))
    assert sorted(nombres) == [f"Muestra {n}" for n in range(1, cantidad + 1)]


def test_nombre_vacio_numera_por_cliente(datos, empleado, crear_muestra, cliente_b, origen_b):
    for numero_pi, nombre in enumerate(
        ["Muestra 1", "Muestra de Rutina", "Muestra 3", "Muestra 4", "Otra Muestra"], start=200001
    ):
        crear_muestra(numero_pi, nombre=nombre)

    assert registrar_muestra(datos, empleado).nombre == "Muestra 6"
    assert registrar_muestra({**datos, "nombre": "Pozo profundo"}, empleado).nombre == (
        "Pozo profundo"
    )

    datos_b = {**datos, "cliente": cliente_b.pk, "origen": origen_b.pk}
    assert registrar_muestra(datos_b, empleado).nombre == "Muestra 1"


# Origen nuevo (US2)


def test_registrar_con_origen_nuevo_crea_origen(datos, empleado, cliente_a):
    muestra = registrar_muestra({**datos, "origen": None, "origen_nuevo": "Pozo N°3"}, empleado)

    origen = Origen.objects.get(nombre="Pozo N°3")
    assert origen.cliente == cliente_a
    assert muestra.origen == origen


def test_origen_nuevo_repetido_reutiliza_existente(datos, empleado, origen_a):
    muestra = registrar_muestra({**datos, "origen": None, "origen_nuevo": "  pozo n°2 "}, empleado)

    assert Origen.objects.count() == 1
    assert muestra.origen == origen_a


def test_error_al_guardar_no_deja_origen_nuevo(datos, empleado, origen_a, monkeypatch):
    def fallar(**kwargs):
        raise DatabaseError("falla simulada")

    monkeypatch.setattr(Muestra.objects, "create", fallar)

    with pytest.raises(DatabaseError):
        registrar_muestra({**datos, "origen": None, "origen_nuevo": "Pozo N°3"}, empleado)

    assert list(Origen.objects.all()) == [origen_a]
