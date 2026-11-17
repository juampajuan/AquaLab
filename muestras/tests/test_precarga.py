"""Registro de muestra precargado por GET y tipo de estudio pendiente (US 10.3,
contracts/enlaces-precargados.md)."""

import datetime
import re
from urllib.parse import urlencode

import pytest
from django.urls import reverse

from estudios.models import TipoEstudio
from muestras.models import Muestra, Origen

pytestmark = pytest.mark.django_db

URL_REGISTRAR = reverse("muestras:registrar")
URL_CONFIRMAR = reverse("muestras:registrar_confirmar")
CLAVE_SESION = "muestra_pendiente"


def nota(tipo):
    return f"Después de registrar la muestra se ofrecerá crear el estudio «{tipo}»."


def url(**parametros):
    return f"{URL_REGISTRAR}?{urlencode(parametros)}"


def input_de(html, nombre):
    encontrado = re.search(rf'<input[^>]*name="{nombre}"[^>]*>', html)
    return encontrado.group(0) if encontrado else None


def opcion_elegida(html, nombre):
    select = re.search(rf'<select[^>]*name="{nombre}"[^>]*>(.*?)</select>', html, re.S).group(1)
    elegida = re.search(r'<option value="([^"]*)"[^>]*selected', select)
    return elegida.group(1) or None if elegida else None


@pytest.fixture
def fq():
    return TipoEstudio.objects.create(nombre="Físico-químico básico")


@pytest.fixture
def ayer(hoy):
    return hoy - datetime.timedelta(days=1)


# --- T009: GET precargado ---


def test_get_precarga_todos_los_campos(cliente_autenticado, cliente_a, origen_a, fq, hoy, ayer):
    html = cliente_autenticado.get(
        url(
            cliente=cliente_a.pk,
            origen=origen_a.pk,
            fecha_muestreo=ayer.isoformat(),
            fecha_ingreso=hoy.isoformat(),
            sitio_extraccion="Boca del pozo",
            tipo_vertido="cloacal",
            nombre="Control semanal",
            responsable_muestreo="Pedro Gómez",
            tipo_estudio=fq.pk,
        )
    ).content.decode()
    assert opcion_elegida(html, "cliente") == str(cliente_a.pk)
    assert opcion_elegida(html, "origen") == str(origen_a.pk)
    assert f'value="{ayer.strftime("%d/%m/%Y")}"' in input_de(html, "fecha_muestreo")
    assert f'value="{hoy.strftime("%d/%m/%Y")}"' in input_de(html, "fecha_ingreso")
    assert 'value="Boca del pozo"' in input_de(html, "sitio_extraccion")
    assert re.search(r'<input[^>]*value="cloacal"[^>]*checked', html)
    assert 'value="Control semanal"' in input_de(html, "nombre")
    assert 'value="Pedro Gómez"' in input_de(html, "responsable_muestreo")
    oculto = input_de(html, "tipo_estudio")
    assert 'type="hidden"' in oculto and f'value="{fq.pk}"' in oculto
    assert nota("Físico-químico básico") in html
    # La ficha del cliente la dibuja el servidor.
    assert "Aguas del Sur S.A." in re.search(r'id="ficha-cliente"(.*?)</dl>', html, re.S).group(1)


def test_get_con_origen_nuevo(cliente_autenticado, cliente_a):
    html = cliente_autenticado.get(
        url(cliente=cliente_a.pk, origen_nuevo="Pozo 3")
    ).content.decode()
    assert 'value="Pozo 3"' in input_de(html, "origen_nuevo")
    assert opcion_elegida(html, "origen") is None


def test_get_sin_tipo_no_muestra_nota(cliente_autenticado, cliente_a):
    html = cliente_autenticado.get(url(cliente=cliente_a.pk)).content.decode()
    assert "Después de registrar la muestra" not in html


def test_get_no_crea_nada(cliente_autenticado, cliente_a, fq):
    cliente_autenticado.get(url(cliente=cliente_a.pk, origen_nuevo="Pozo 9", tipo_estudio=fq.pk))
    assert not Muestra.objects.exists()
    assert not Origen.objects.filter(nombre="Pozo 9").exists()


def test_get_con_parametros_descarta_el_borrador(cliente_autenticado, datos_muestra_validos):
    cliente_autenticado.post(URL_REGISTRAR, datos_muestra_validos)
    assert CLAVE_SESION in cliente_autenticado.session
    cliente_autenticado.get(url(cliente=datos_muestra_validos["cliente"]))
    assert CLAVE_SESION not in cliente_autenticado.session


def test_volver_gana_sobre_los_parametros(cliente_autenticado, datos_muestra_validos, fq):
    cliente_autenticado.post(URL_REGISTRAR, {**datos_muestra_validos, "tipo_estudio": fq.pk})
    html = cliente_autenticado.get(
        f"{URL_REGISTRAR}?volver=1&sitio_extraccion=Otro"
    ).content.decode()
    assert 'value="Canilla de salida del tanque"' in input_de(html, "sitio_extraccion")
    assert f'value="{fq.pk}"' in input_de(html, "tipo_estudio")
    assert nota("Físico-químico básico") in html


# --- T010: el tipo viaja hasta el mensaje de éxito ---


def test_tipo_en_borrador_confirmacion_y_exito(cliente_autenticado, datos_muestra_validos, fq):
    cliente_autenticado.post(URL_REGISTRAR, {**datos_muestra_validos, "tipo_estudio": fq.pk})
    assert cliente_autenticado.session[CLAVE_SESION]["tipo_estudio"] == fq.pk
    html = cliente_autenticado.get(URL_CONFIRMAR).content.decode()
    assert nota("Físico-químico básico") in html

    respuesta = cliente_autenticado.post(URL_CONFIRMAR, {"accion": "confirmar"}, follow=True)
    muestra = Muestra.objects.get()
    html = respuesta.content.decode()
    assert f"Muestra registrada con N° PI {muestra.numero_pi}." in html
    enlace = f"{reverse('estudios:crear')}?muestra={muestra.pk}&amp;tipo={fq.pk}"
    assert f'<a href="{enlace}">Crear el estudio Físico-químico básico</a>' in html


def test_tipo_desactivado_antes_de_confirmar(cliente_autenticado, datos_muestra_validos, fq):
    cliente_autenticado.post(URL_REGISTRAR, {**datos_muestra_validos, "tipo_estudio": fq.pk})
    TipoEstudio.objects.filter(pk=fq.pk).update(activo=False)
    html = cliente_autenticado.post(
        URL_CONFIRMAR, {"accion": "confirmar"}, follow=True
    ).content.decode()
    assert Muestra.objects.count() == 1
    assert "Crear el estudio" not in html


def test_sin_tipo_mensaje_de_siempre(cliente_autenticado, datos_muestra_validos):
    cliente_autenticado.post(URL_REGISTRAR, datos_muestra_validos)
    assert cliente_autenticado.session[CLAVE_SESION]["tipo_estudio"] is None
    html = cliente_autenticado.post(
        URL_CONFIRMAR, {"accion": "confirmar"}, follow=True
    ).content.decode()
    assert "Crear el estudio" not in html


def test_borrador_viejo_sin_tipo_se_confirma(cliente_autenticado, datos_muestra_validos):
    cliente_autenticado.post(URL_REGISTRAR, datos_muestra_validos)
    sesion = cliente_autenticado.session
    borrador = dict(sesion[CLAVE_SESION])
    borrador.pop("tipo_estudio")
    sesion[CLAVE_SESION] = borrador
    sesion.save()
    assert cliente_autenticado.get(URL_CONFIRMAR).status_code == 200
    cliente_autenticado.post(URL_CONFIRMAR, {"accion": "confirmar"})
    assert Muestra.objects.count() == 1


# --- T024: saneo en silencio ---


@pytest.mark.parametrize(
    "parametros, campo",
    [
        ({"cliente": "999999"}, "cliente"),
        ({"cliente": "abc"}, "cliente"),
        ({"fecha_muestreo": "xx"}, "fecha_muestreo"),
        ({"fecha_ingreso": "2026-02-31"}, "fecha_ingreso"),
        ({"tipo_vertido": "nada"}, "tipo_vertido"),
        ({"nombre": "x" * 101}, "nombre"),
        ({"sitio_extraccion": "x" * 201}, "sitio_extraccion"),
        ({"responsable_muestreo": "x" * 151}, "responsable_muestreo"),
        ({"origen_nuevo": "x" * 151}, "origen_nuevo"),
        ({"tipo_estudio": "999999"}, "tipo_estudio"),
    ],
)
def test_parametros_invalidos_se_descartan(cliente_autenticado, parametros, campo):
    from django.http import QueryDict

    from muestras.forms import valores_iniciales

    respuesta = cliente_autenticado.get(url(**parametros))
    assert respuesta.status_code == 200
    html = respuesta.content.decode()
    assert "is-invalid" not in html
    assert campo not in valores_iniciales(QueryDict(urlencode(parametros)))


def test_cliente_inactivo_y_origen_ajeno(
    cliente_autenticado, cliente_inactivo, cliente_a, origen_b
):
    from django.http import QueryDict

    from muestras.forms import valores_iniciales

    assert valores_iniciales(QueryDict(f"cliente={cliente_inactivo.pk}")) == {}
    iniciales = valores_iniciales(QueryDict(f"cliente={cliente_a.pk}&origen={origen_b.pk}"))
    assert iniciales == {"cliente": cliente_a.pk}


def test_origen_nuevo_se_descarta_con_origen_valido(cliente_a, origen_a):
    from django.http import QueryDict

    from muestras.forms import valores_iniciales

    iniciales = valores_iniciales(
        QueryDict(f"cliente={cliente_a.pk}&origen={origen_a.pk}&origen_nuevo=Otro")
    )
    assert iniciales == {"cliente": cliente_a.pk, "origen": origen_a.pk}


def test_tipo_inactivo_no_se_precarga(cliente_autenticado, fq):
    TipoEstudio.objects.filter(pk=fq.pk).update(activo=False)
    html = cliente_autenticado.get(url(tipo_estudio=fq.pk)).content.decode()
    assert "Después de registrar la muestra" not in html


def test_post_con_tipo_inactivo_no_da_error(cliente_autenticado, datos_muestra_validos, fq):
    TipoEstudio.objects.filter(pk=fq.pk).update(activo=False)
    respuesta = cliente_autenticado.post(
        URL_REGISTRAR, {**datos_muestra_validos, "tipo_estudio": fq.pk}
    )
    assert respuesta.status_code == 302
    assert cliente_autenticado.session[CLAVE_SESION]["tipo_estudio"] is None
    respuesta = cliente_autenticado.post(
        URL_REGISTRAR, {**datos_muestra_validos, "tipo_estudio": "basura"}
    )
    assert respuesta.status_code == 302
