import datetime
import json
import re
import uuid

import pytest
from django.conf import settings
from django.db import DatabaseError
from django.shortcuts import resolve_url
from django.urls import reverse

from muestras.models import Muestra, Origen
from muestras.servicios import registrar_muestra

pytestmark = pytest.mark.django_db

CLAVE_SESION = "muestra_pendiente"
MENSAJE_CANCELADO = "Registro de muestra cancelado."
MENSAJE_ERROR_BD = "No se pudo registrar la muestra. Intentá nuevamente."
MENSAJE_NO_DISPONIBLE = "El cliente no está disponible."
AVISO_REVISION = "Revisá los datos de la muestra antes de confirmar el registro."
URL_REGISTRAR = reverse("muestras:registrar")
URL_CONFIRMAR = reverse("muestras:registrar_confirmar")


def mensaje_exito(numero_pi):
    return f"Muestra registrada con N° PI {numero_pi}."


def clientes_del_json(html):
    encontrado = re.search(
        r'<script id="clientes-muestra" type="application/json">(.*?)</script>', html, re.S
    )
    assert encontrado, "no se encontró el json_script clientes-muestra"
    return {cliente["id"]: cliente for cliente in json.loads(encontrado.group(1))}


def select_de(html, nombre):
    encontrado = re.search(rf'<select[^>]*name="{nombre}"[^>]*>(.*?)</select>', html, re.S)
    assert encontrado, f"no se encontró el select {nombre}"
    return encontrado.group(1)


def input_de(html, nombre):
    encontrado = re.search(rf'<input[^>]*name="{nombre}"[^>]*>', html)
    assert encontrado, f"no se encontró el input {nombre}"
    return encontrado.group(0)


def ficha_de(html):
    encontrado = re.search(r'id="ficha-cliente"(.*?)</dl>', html, re.S)
    assert encontrado, "no se encontró la ficha del cliente"
    return encontrado.group(1)


@pytest.fixture
def en_revision(cliente_autenticado, datos_muestra_validos):
    """Deja el registro en revisión: los datos quedan en `session["muestra_pendiente"]`."""
    respuesta = cliente_autenticado.post(URL_REGISTRAR, datos_muestra_validos)
    assert respuesta.status_code == 302
    return cliente_autenticado


# Acceso y formulario (US1)


def test_vistas_registro_muestra_requieren_sesion(client):
    login = resolve_url(settings.LOGIN_URL)
    for respuesta in (
        client.get(URL_REGISTRAR),
        client.post(URL_REGISTRAR, {}),
        client.get(URL_CONFIRMAR),
        client.post(URL_CONFIRMAR, {"accion": "confirmar"}),
    ):
        assert respuesta.status_code == 302
        assert respuesta.url.startswith(login)


def test_formulario_inicial_propone_hoy_y_agua(cliente_autenticado, hoy):
    respuesta = cliente_autenticado.get(URL_REGISTRAR)
    html = respuesta.content.decode()

    assert respuesta.status_code == 200
    assert f'value="{hoy.isoformat()}"' in input_de(html, "fecha_muestreo")
    assert f'value="{hoy.isoformat()}"' in input_de(html, "fecha_ingreso")
    assert re.search(
        r'<option value="agua" selected>Agua</option>', select_de(html, "tipo_vertido")
    )
    assert "value=" not in input_de(html, "nombre")
    assert "value=" not in input_de(html, "responsable_muestreo")


def test_formulario_lista_solo_clientes_activos_con_sus_datos(
    cliente_autenticado, cliente_a, cliente_b, cliente_inactivo
):
    html = cliente_autenticado.get(URL_REGISTRAR).content.decode()
    opciones = select_de(html, "cliente")

    assert f'value="{cliente_a.pk}"' in opciones
    assert f'value="{cliente_b.pk}"' in opciones
    assert f'value="{cliente_inactivo.pk}"' not in opciones

    clientes = clientes_del_json(html)
    assert set(clientes) == {cliente_a.pk, cliente_b.pk}
    assert clientes[cliente_a.pk]["razon_social_o_nombre"] == "Aguas del Sur S.A."
    assert clientes[cliente_a.pk]["tipo_documento"] == "CUIT"
    assert clientes[cliente_a.pk]["numero_documento"] == "20123456786"
    assert clientes[cliente_a.pk]["email"] == "contacto@aguassur.com"
    assert clientes[cliente_b.pk]["razon_social_o_nombre"] == "Juan Pérez"


def test_formulario_ofrece_solo_origenes_del_cliente(
    cliente_autenticado, datos_muestra_validos, cliente_a, cliente_b, origen_a, origen_b
):
    clientes = clientes_del_json(cliente_autenticado.get(URL_REGISTRAR).content.decode())
    assert clientes[cliente_a.pk]["origenes"] == [{"id": origen_a.pk, "nombre": "Pozo N°2"}]
    assert clientes[cliente_b.pk]["origenes"] == [{"id": origen_b.pk, "nombre": "Tanque elevado"}]

    datos = {**datos_muestra_validos, "sitio_extraccion": ""}
    html = cliente_autenticado.post(URL_REGISTRAR, datos).content.decode()
    opciones = select_de(html, "origen")
    assert f'value="{origen_a.pk}"' in opciones
    assert f'value="{origen_b.pk}"' not in opciones


def test_formulario_con_cliente_elegido_muestra_ficha_y_origenes(
    en_revision, datos_muestra_validos, origen_a, origen_b
):
    datos = {**datos_muestra_validos, "sitio_extraccion": ""}
    html_error = en_revision.post(URL_REGISTRAR, datos).content.decode()
    # El POST inválido no toca el borrador que dejó `en_revision`.
    html_volver = en_revision.get(f"{URL_REGISTRAR}?volver=1").content.decode()

    for html in (html_error, html_volver):
        ficha = ficha_de(html)
        assert "hidden" not in ficha.split(">", 1)[0]
        for dato in ("Aguas del Sur S.A.", "CUIT", "20123456786", "contacto@aguassur.com"):
            assert dato in ficha
        opciones = select_de(html, "origen")
        assert f'value="{origen_a.pk}"' in opciones
        assert f'value="{origen_b.pk}"' not in opciones


# Revisión y confirmación (US1)


def test_post_valido_guarda_borrador_y_muestra_resumen(
    cliente_autenticado, datos_muestra_validos, cliente_a, origen_a, hoy
):
    respuesta = cliente_autenticado.post(URL_REGISTRAR, datos_muestra_validos)

    assert respuesta.status_code == 302
    assert respuesta.url == URL_CONFIRMAR
    borrador = dict(cliente_autenticado.session[CLAVE_SESION])
    assert uuid.UUID(borrador.pop("clave_borrador"))
    assert borrador == {
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

    html = cliente_autenticado.get(URL_CONFIRMAR).content.decode()
    for texto in (
        AVISO_REVISION,
        "Aguas del Sur S.A.",
        "CUIT 20123456786",
        "contacto@aguassur.com",
        "Pozo N°2",
        hoy.strftime("%d/%m/%Y"),
        "Canilla de salida del tanque",
        "Agua",
        "Muestra 1 (el número se confirma al guardar)",
        "El N° PI se asigna al confirmar.",
    ):
        assert texto in html
    assert not Muestra.objects.exists()


def test_confirmar_registra_muestra_con_pi_siguiente_y_datos_automaticos(
    en_revision, crear_muestra, cliente_a, origen_a, empleado
):
    crear_muestra(200001)

    respuesta = en_revision.post(URL_CONFIRMAR, {"accion": "confirmar"})

    assert respuesta.status_code == 302
    assert respuesta.url == URL_REGISTRAR
    muestra = Muestra.objects.get(numero_pi=200002)
    assert muestra.cliente == cliente_a
    assert muestra.origen == origen_a
    assert muestra.estado == "ingresada"
    assert muestra.registrada_por == empleado
    assert CLAVE_SESION not in en_revision.session

    html = en_revision.get(respuesta.url).content.decode()
    assert mensaje_exito(200002) in html
    assert 'value="Canilla de salida del tanque"' not in html
    assert "hidden" in ficha_de(html).split(">", 1)[0]


def test_volver_y_editar_conserva_borrador(en_revision):
    html = en_revision.get(f"{URL_REGISTRAR}?volver=1").content.decode()

    assert 'value="Canilla de salida del tanque"' in input_de(html, "sitio_extraccion")
    assert CLAVE_SESION in en_revision.session

    html = en_revision.get(URL_REGISTRAR).content.decode()
    assert "value=" not in input_de(html, "sitio_extraccion")
    assert CLAVE_SESION not in en_revision.session


def test_cancelar_no_registra_ni_consume_pi(en_revision, datos_muestra_validos):
    respuesta = en_revision.post(URL_CONFIRMAR, {"accion": "cancelar"})

    assert respuesta.status_code == 302
    assert respuesta.url == URL_REGISTRAR
    assert MENSAJE_CANCELADO in en_revision.get(respuesta.url).content.decode()
    assert not Muestra.objects.exists()
    assert CLAVE_SESION not in en_revision.session

    en_revision.post(URL_REGISTRAR, datos_muestra_validos)
    en_revision.post(URL_CONFIRMAR, {"accion": "confirmar"})
    assert Muestra.objects.get().numero_pi == 200001


def test_confirmacion_repetida_registra_una_sola_muestra(en_revision):
    en_revision.post(URL_CONFIRMAR, {"accion": "confirmar"})
    segunda = en_revision.post(URL_CONFIRMAR, {"accion": "confirmar"})

    assert Muestra.objects.count() == 1
    assert segunda.status_code == 302
    assert segunda.url == URL_REGISTRAR
    assert mensaje_exito(200001) in en_revision.get(segunda.url).content.decode()


def test_confirmacion_de_borrador_ya_registrado_no_duplica(en_revision, empleado):
    # Lo que ve la segunda de dos confirmaciones simultáneas: el borrador sigue en su sesión, pero
    # la primera ya lo registró.
    registrar_muestra(en_revision.session[CLAVE_SESION], empleado)

    respuesta = en_revision.post(URL_CONFIRMAR, {"accion": "confirmar"})

    assert Muestra.objects.count() == 1
    assert respuesta.status_code == 302
    assert respuesta.url == URL_REGISTRAR
    assert CLAVE_SESION not in en_revision.session
    assert mensaje_exito(200001) in en_revision.get(respuesta.url).content.decode()


def test_cliente_desactivado_antes_de_confirmar_no_registra(en_revision, cliente_a):
    cliente_a.activo = False
    cliente_a.save()

    respuesta = en_revision.post(URL_CONFIRMAR, {"accion": "confirmar"})

    assert respuesta.status_code == 302
    assert respuesta.url == f"{URL_REGISTRAR}?volver=1"
    assert MENSAJE_NO_DISPONIBLE in en_revision.get(respuesta.url).content.decode()
    assert not Muestra.objects.exists()
    assert CLAVE_SESION in en_revision.session


def test_error_de_base_al_confirmar_informa_sin_registrar(en_revision, monkeypatch):
    def fallar(datos, usuario):
        raise DatabaseError("falla simulada")

    monkeypatch.setattr("muestras.views.registrar_muestra", fallar)

    respuesta = en_revision.post(URL_CONFIRMAR, {"accion": "confirmar"})

    assert respuesta.status_code == 200
    assert MENSAJE_ERROR_BD in respuesta.content.decode()
    assert CLAVE_SESION in en_revision.session
    assert not Muestra.objects.exists()


def test_navbar_tiene_enlace_registrar_muestra(cliente_autenticado):
    html = cliente_autenticado.get(reverse("inicio")).content.decode()

    assert re.search(rf'<a[^>]*href="{URL_REGISTRAR}"[^>]*>\s*Registrar muestra\s*</a>', html)


# Origen nuevo (US2)

MENSAJE_SIN_ORIGEN = "Elegí un origen del cliente o ingresá uno nuevo."
MENSAJE_DOS_ORIGENES = "Elegí un origen existente o ingresá uno nuevo, no ambos."


def test_confirmar_con_origen_nuevo_crea_origen_del_cliente(
    cliente_autenticado, datos_muestra_validos, cliente_a
):
    datos = {**datos_muestra_validos, "origen": "", "origen_nuevo": "Pozo N°3"}
    respuesta = cliente_autenticado.post(URL_REGISTRAR, datos)
    assert respuesta.status_code == 302

    html = cliente_autenticado.get(URL_CONFIRMAR).content.decode()
    assert "Pozo N°3 (nuevo)" in html
    assert not Origen.objects.filter(nombre="Pozo N°3").exists()

    cliente_autenticado.post(URL_CONFIRMAR, {"accion": "confirmar"})

    origen = Origen.objects.get(nombre="Pozo N°3")
    assert origen.cliente == cliente_a
    assert Muestra.objects.get().origen == origen


def test_origen_nuevo_disponible_solo_para_su_cliente(
    cliente_autenticado, datos_muestra_validos, cliente_a, cliente_b
):
    datos = {**datos_muestra_validos, "origen": "", "origen_nuevo": "Pozo N°3"}
    cliente_autenticado.post(URL_REGISTRAR, datos)
    cliente_autenticado.post(URL_CONFIRMAR, {"accion": "confirmar"})

    clientes = clientes_del_json(cliente_autenticado.get(URL_REGISTRAR).content.decode())
    assert "Pozo N°3" in [origen["nombre"] for origen in clientes[cliente_a.pk]["origenes"]]
    assert "Pozo N°3" not in [origen["nombre"] for origen in clientes[cliente_b.pk]["origenes"]]


def test_cancelar_con_origen_nuevo_no_crea_origen(cliente_autenticado, datos_muestra_validos):
    datos = {**datos_muestra_validos, "origen": "", "origen_nuevo": "Pozo N°3"}
    cliente_autenticado.post(URL_REGISTRAR, datos)

    cliente_autenticado.post(URL_CONFIRMAR, {"accion": "cancelar"})

    assert not Origen.objects.filter(nombre="Pozo N°3").exists()
    assert not Muestra.objects.exists()


def test_origen_o_origen_nuevo_exactamente_uno(cliente_autenticado, datos_muestra_validos):
    sin_origen = {**datos_muestra_validos, "origen": "", "origen_nuevo": ""}
    ambos = {**datos_muestra_validos, "origen_nuevo": "Pozo N°3"}

    for datos, campo, mensaje in (
        (sin_origen, "origen", MENSAJE_SIN_ORIGEN),
        (ambos, "origen_nuevo", MENSAJE_DOS_ORIGENES),
    ):
        respuesta = cliente_autenticado.post(URL_REGISTRAR, datos)
        html = respuesta.content.decode()
        assert respuesta.status_code == 200
        assert re.search(rf'id="id_{campo}_error">\s*<div>{mensaje}</div>', html)
        assert CLAVE_SESION not in cliente_autenticado.session


# Validaciones y valores por defecto (US3)

MENSAJE_OBLIGATORIO = "Este campo es obligatorio."
MENSAJE_FECHA_FUTURA = "La fecha no puede ser posterior a hoy."
MENSAJE_MUESTREO_POSTERIOR = "La fecha de muestreo no puede ser posterior a la fecha de ingreso."


def error_en(html, campo, mensaje=None):
    """Indica si el campo tiene error (y, si se pasa, que sea `mensaje`) junto al control."""
    bloque = re.search(rf'id="id_{campo}_error">\s*((?:<div>.*?</div>\s*)+)</div>', html, re.S)
    if not bloque:
        return False
    control = re.search(rf'<(?:input|select)[^>]*name="{campo}"[^>]*>', html)
    marcado = bool(control) and "is-invalid" in control.group(0)
    return marcado and (mensaje is None or f"<div>{mensaje}</div>" in bloque.group(1))


def registrar_y_confirmar(cliente_http, datos):
    respuesta = cliente_http.post(URL_REGISTRAR, datos)
    assert respuesta.status_code == 302, respuesta.content.decode()
    cliente_http.post(URL_CONFIRMAR, {"accion": "confirmar"})
    return Muestra.objects.order_by("-numero_pi").first()


@pytest.mark.parametrize(
    "campo", ["cliente", "fecha_muestreo", "fecha_ingreso", "sitio_extraccion", "tipo_vertido"]
)
def test_campos_obligatorios_faltantes_indican_cada_campo(
    cliente_autenticado, datos_muestra_validos, campo
):
    datos = {**datos_muestra_validos, campo: "", "responsable_muestreo": "Carlos Ruiz"}

    respuesta = cliente_autenticado.post(URL_REGISTRAR, datos)
    html = respuesta.content.decode()

    assert respuesta.status_code == 200
    assert error_en(html, campo, MENSAJE_OBLIGATORIO)
    assert 'value="Carlos Ruiz"' in input_de(html, "responsable_muestreo")
    if campo != "sitio_extraccion":
        assert 'value="Canilla de salida del tanque"' in input_de(html, "sitio_extraccion")
    assert CLAVE_SESION not in cliente_autenticado.session
    assert not Muestra.objects.exists()


def test_textos_solo_espacios_son_vacios(cliente_autenticado, datos_muestra_validos):
    html = cliente_autenticado.post(
        URL_REGISTRAR, {**datos_muestra_validos, "sitio_extraccion": "   "}
    ).content.decode()
    assert error_en(html, "sitio_extraccion", MENSAJE_OBLIGATORIO)

    html = cliente_autenticado.post(
        URL_REGISTRAR, {**datos_muestra_validos, "origen": "", "origen_nuevo": "   "}
    ).content.decode()
    assert error_en(html, "origen", MENSAJE_SIN_ORIGEN)


def test_nombre_vacio_se_numera_segun_muestras_del_cliente(
    cliente_autenticado, datos_muestra_validos, cliente_b, origen_b
):
    muestra = registrar_y_confirmar(cliente_autenticado, datos_muestra_validos)
    assert muestra.nombre == "Muestra 1"

    muestra = registrar_y_confirmar(
        cliente_autenticado, {**datos_muestra_validos, "nombre": "Muestra cisterna"}
    )
    assert muestra.nombre == "Muestra cisterna"

    cliente_autenticado.post(URL_REGISTRAR, datos_muestra_validos)
    resumen = cliente_autenticado.get(URL_CONFIRMAR).content.decode()
    assert "Muestra 3 (el número se confirma al guardar)" in resumen
    cliente_autenticado.post(URL_CONFIRMAR, {"accion": "confirmar"})
    assert Muestra.objects.order_by("-numero_pi").first().nombre == "Muestra 3"

    datos_b = {**datos_muestra_validos, "cliente": cliente_b.pk, "origen": origen_b.pk}
    muestra = registrar_y_confirmar(cliente_autenticado, datos_b)
    assert muestra.nombre == "Muestra 1"


def test_responsable_opcional_texto_libre(cliente_autenticado, datos_muestra_validos):
    muestra = registrar_y_confirmar(cliente_autenticado, datos_muestra_validos)
    assert muestra.responsable_muestreo == ""

    muestra = registrar_y_confirmar(
        cliente_autenticado,
        {**datos_muestra_validos, "responsable_muestreo": "Carlos Ruiz (externo)"},
    )
    assert muestra.responsable_muestreo == "Carlos Ruiz (externo)"


@pytest.mark.parametrize(
    ("dias_muestreo", "dias_ingreso", "campo", "mensaje"),
    [
        (1, 0, "fecha_muestreo", MENSAJE_FECHA_FUTURA),
        (0, 1, "fecha_ingreso", MENSAJE_FECHA_FUTURA),
        (0, -1, "fecha_muestreo", MENSAJE_MUESTREO_POSTERIOR),
        (-30, -1, None, None),
    ],
)
def test_fechas_invalidas_rechazadas(
    cliente_autenticado, datos_muestra_validos, hoy, dias_muestreo, dias_ingreso, campo, mensaje
):
    datos = {
        **datos_muestra_validos,
        "fecha_muestreo": (hoy + datetime.timedelta(days=dias_muestreo)).isoformat(),
        "fecha_ingreso": (hoy + datetime.timedelta(days=dias_ingreso)).isoformat(),
    }

    respuesta = cliente_autenticado.post(URL_REGISTRAR, datos)

    if campo is None:
        assert respuesta.status_code == 302
        return
    assert respuesta.status_code == 200
    assert error_en(respuesta.content.decode(), campo, mensaje)
    assert CLAVE_SESION not in cliente_autenticado.session


def test_origen_de_otro_cliente_rechazado(cliente_autenticado, datos_muestra_validos, origen_b):
    respuesta = cliente_autenticado.post(
        URL_REGISTRAR, {**datos_muestra_validos, "origen": origen_b.pk}
    )

    assert respuesta.status_code == 200
    assert error_en(respuesta.content.decode(), "origen")
    assert CLAVE_SESION not in cliente_autenticado.session


def test_cliente_inactivo_o_inexistente_rechazado(
    cliente_autenticado, datos_muestra_validos, cliente_inactivo
):
    for pk in (cliente_inactivo.pk, 99999):
        respuesta = cliente_autenticado.post(
            URL_REGISTRAR, {**datos_muestra_validos, "cliente": pk}
        )

        assert respuesta.status_code == 200
        assert error_en(respuesta.content.decode(), "cliente")
    assert CLAVE_SESION not in cliente_autenticado.session


def test_tipo_vertido_fuera_de_opciones_rechazado(cliente_autenticado, datos_muestra_validos):
    respuesta = cliente_autenticado.post(
        URL_REGISTRAR, {**datos_muestra_validos, "tipo_vertido": "pluvial"}
    )

    assert respuesta.status_code == 200
    assert error_en(respuesta.content.decode(), "tipo_vertido")
