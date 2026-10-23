import re

import pytest
from django.db import DatabaseError
from django.urls import reverse

from clientes.models import Cliente

pytestmark = pytest.mark.django_db

MENSAJE_EDICION_EXITO = "Datos del cliente actualizados correctamente."
MENSAJE_EDICION_CANCELADA = "Edición de cliente cancelada."
MENSAJE_DUPLICADO = "Ya existe un cliente registrado con este tipo y número de documento."
MENSAJE_NO_DISPONIBLE = "El cliente no está disponible."
MENSAJE_NOMBRE_O_RAZON = "Debés ingresar al menos el nombre o la razón social del cliente."
MENSAJE_DNI_INVALIDO = "El DNI debe tener 7 u 8 dígitos numéricos."
MENSAJE_CUIT_INVALIDO = "El CUIT debe tener 11 dígitos y un dígito verificador válido."
MENSAJE_TELEFONO_INVALIDO = "Ingresá un número de teléfono válido (entre 7 y 15 dígitos)."
MENSAJE_ERROR_BD_EDICION = "No se pudo actualizar el cliente. Intentá nuevamente."
AVISO_REVISION_EDICION = "Revisá los datos modificados del cliente antes de confirmar los cambios."


def clave_sesion_edicion(pk):
    return f"cliente_edicion_{pk}"


def input_de(html, nombre):
    encontrado = re.search(rf'<input[^>]*name="{nombre}"[^>]*>', html)
    assert encontrado, f"no se encontró el input {nombre}"
    return encontrado.group(0)


# Paso 1: acceso, precarga y validaciones del formulario de edición (T004)


def test_vistas_edicion_requieren_sesion_activa(client, cliente_existente):
    url_editar = reverse("clientes:editar", args=[cliente_existente.pk])
    url_confirmar = reverse("clientes:editar_confirmar", args=[cliente_existente.pk])

    assert client.get(url_editar).status_code == 302
    assert client.post(url_editar, {}).status_code == 302
    assert client.get(url_confirmar).status_code == 302
    assert client.post(url_confirmar, {"accion": "confirmar"}).status_code == 302


def test_editar_cliente_inexistente_devuelve_404(cliente_autenticado):
    url_editar = reverse("clientes:editar", args=[99999])
    url_confirmar = reverse("clientes:editar_confirmar", args=[99999])

    assert cliente_autenticado.get(url_editar).status_code == 404
    assert cliente_autenticado.post(url_editar, {}).status_code == 404
    assert cliente_autenticado.get(url_confirmar).status_code == 404
    assert cliente_autenticado.post(url_confirmar, {"accion": "confirmar"}).status_code == 404


def test_editar_cliente_inactivo_redirige_con_advertencia(
    cliente_autenticado, cliente_existente, datos_edicion_validos
):
    sesion = cliente_autenticado.session
    sesion[clave_sesion_edicion(cliente_existente.pk)] = datos_edicion_validos
    sesion.save()

    cliente_existente.activo = False
    cliente_existente.save()

    url_editar = reverse("clientes:editar", args=[cliente_existente.pk])
    url_confirmar = reverse("clientes:editar_confirmar", args=[cliente_existente.pk])
    url_buscar = reverse("clientes:buscar")

    for respuesta in (
        cliente_autenticado.get(url_editar),
        cliente_autenticado.post(url_editar, datos_edicion_validos),
        cliente_autenticado.get(url_confirmar),
        cliente_autenticado.post(url_confirmar, {"accion": "confirmar"}),
    ):
        assert respuesta.status_code == 302
        assert respuesta.url == url_buscar

    assert clave_sesion_edicion(cliente_existente.pk) not in cliente_autenticado.session
    html_buscar = cliente_autenticado.get(url_buscar).content.decode()
    assert MENSAJE_NO_DISPONIBLE in html_buscar


def test_get_editar_precarga_datos_vigentes_y_ficha_tiene_link(cliente_autenticado, otro_cliente):
    url_detalle = reverse("clientes:detalle", args=[otro_cliente.pk])
    url_editar = reverse("clientes:editar", args=[otro_cliente.pk])

    ficha = cliente_autenticado.get(url_detalle)
    html_ficha = ficha.content.decode()
    assert ficha.status_code == 200
    assert f'href="{url_editar}"' in html_ficha
    assert "Editar cliente" in html_ficha

    # Si había un borrador viejo en sesión y se entra sin ?volver=1, se descarta y se precarga la BD
    sesion = cliente_autenticado.session
    sesion[clave_sesion_edicion(otro_cliente.pk)] = {
        "nombre": "Borrador Viejo",
        "razon_social": "",
        "tipo_documento": "DNI",
        "numero_documento": "30123456",
        "email": "viejo@ejemplo.com",
        "telefono": "",
        "domicilio": "",
    }
    sesion.save()

    respuesta = cliente_autenticado.get(url_editar)
    html = respuesta.content.decode()
    assert respuesta.status_code == 200
    assert clave_sesion_edicion(otro_cliente.pk) not in cliente_autenticado.session
    assert 'value="Juan Pérez"' in input_de(html, "nombre")
    assert 'value="30123456"' in input_de(html, "numero_documento")
    assert 'value="juan@ejemplo.com"' in input_de(html, "email")
    assert 'value="+54 11 4321-5678"' in input_de(html, "telefono")
    assert 'value="Av. Corrientes 1234"' in input_de(html, "domicilio")
    assert f'href="{url_detalle}"' in html


@pytest.mark.parametrize(
    ("campos_vacios", "espera_error_general"),
    [
        (["nombre", "razon_social"], True),
        (["tipo_documento"], False),
        (["numero_documento"], False),
        (["email"], False),
    ],
    ids=["sin_nombre_ni_razon", "tipo_documento", "numero_documento", "email"],
)
def test_edicion_campos_obligatorios_faltantes_no_modifica(
    cliente_autenticado,
    cliente_existente,
    datos_edicion_validos,
    campos_vacios,
    espera_error_general,
):
    datos = {**datos_edicion_validos, **dict.fromkeys(campos_vacios, "")}
    url_editar = reverse("clientes:editar", args=[cliente_existente.pk])

    respuesta = cliente_autenticado.post(url_editar, datos)

    assert respuesta.status_code == 200
    errores = respuesta.context["form"].errors
    html = respuesta.content.decode()
    if espera_error_general:
        assert MENSAJE_NOMBRE_O_RAZON in errores["__all__"]
        assert MENSAJE_NOMBRE_O_RAZON in html
    for campo in campos_vacios:
        if campo in ("tipo_documento", "numero_documento", "email"):
            assert "Este campo es obligatorio." in errores[campo]
            assert "Este campo es obligatorio." in html

    assert clave_sesion_edicion(cliente_existente.pk) not in cliente_autenticado.session
    cliente_existente.refresh_from_db()
    assert cliente_existente.email == "contacto@aguassur.com"


@pytest.mark.parametrize(
    ("cambios", "campo_error", "mensaje_esperado"),
    [
        ({"email": "mal@"}, "email", "Introduzca una dirección de email válida."),
        ({"telefono": "123"}, "telefono", MENSAJE_TELEFONO_INVALIDO),
        (
            {"tipo_documento": "DNI", "numero_documento": "12345"},
            "numero_documento",
            MENSAJE_DNI_INVALIDO,
        ),
        (
            {"tipo_documento": "CUIT", "numero_documento": "20-12345678-0"},
            "numero_documento",
            MENSAJE_CUIT_INVALIDO,
        ),
    ],
    ids=["email_invalido", "telefono_invalido", "dni_invalido", "cuit_invalido"],
)
def test_edicion_formatos_invalidos_rechazados_y_conserva_datos(
    cliente_autenticado,
    cliente_existente,
    datos_edicion_validos,
    cambios,
    campo_error,
    mensaje_esperado,
):
    datos = {**datos_edicion_validos, **cambios}
    url_editar = reverse("clientes:editar", args=[cliente_existente.pk])

    respuesta = cliente_autenticado.post(url_editar, datos)

    html = respuesta.content.decode()
    assert respuesta.status_code == 200
    assert mensaje_esperado in respuesta.context["form"].errors[campo_error]
    assert 'value="Roberto Gómez"' in input_de(html, "nombre")
    assert 'value="Av. Paseo Colón 850"' in input_de(html, "domicilio")
    assert clave_sesion_edicion(cliente_existente.pk) not in cliente_autenticado.session
    cliente_existente.refresh_from_db()
    assert cliente_existente.nombre == ""


@pytest.mark.parametrize(
    "documento_ajeno",
    ["30123456", "30.123.456", "30-123-456", " 30 123 456 "],
)
def test_edicion_documento_de_otro_cliente_rechazado(
    cliente_autenticado,
    cliente_existente,
    otro_cliente,
    datos_edicion_validos,
    documento_ajeno,
):
    datos = {
        **datos_edicion_validos,
        "tipo_documento": "DNI",
        "numero_documento": documento_ajeno,
    }
    url_editar = reverse("clientes:editar", args=[cliente_existente.pk])

    respuesta = cliente_autenticado.post(url_editar, datos)

    assert respuesta.status_code == 200
    assert respuesta.context["form"].errors["numero_documento"] == [MENSAJE_DUPLICADO]
    assert respuesta.content.decode().count(MENSAJE_DUPLICADO) == 1
    assert clave_sesion_edicion(cliente_existente.pk) not in cliente_autenticado.session
    cliente_existente.refresh_from_db()
    assert cliente_existente.numero_documento == "20123456786"


@pytest.mark.parametrize(
    "mismo_cuit",
    ["20123456786", "20-12345678-6", "20.123.456.786", " 20 12345678 6 "],
)
def test_edicion_mismo_documento_propio_con_o_sin_separadores_permitido(
    cliente_autenticado,
    cliente_existente,
    datos_edicion_validos,
    mismo_cuit,
):
    datos = {**datos_edicion_validos, "numero_documento": mismo_cuit}
    url_editar = reverse("clientes:editar", args=[cliente_existente.pk])

    respuesta = cliente_autenticado.post(url_editar, datos)

    assert respuesta.status_code == 302
    assert respuesta.url == reverse("clientes:editar_confirmar", args=[cliente_existente.pk])
    borrador = cliente_autenticado.session[clave_sesion_edicion(cliente_existente.pk)]
    assert borrador["numero_documento"] == "20123456786"
    assert borrador["email"] == "nuevo@aguassur.com"


# Paso 2: revisión, confirmación, cancelación, idempotencia y errores de BD (T005)


def test_confirmar_edicion_actualiza_cliente_y_refleja_en_detalle(
    cliente_autenticado, cliente_existente, datos_edicion_validos
):
    url_editar = reverse("clientes:editar", args=[cliente_existente.pk])
    url_confirmar = reverse("clientes:editar_confirmar", args=[cliente_existente.pk])
    url_detalle = reverse("clientes:detalle", args=[cliente_existente.pk])

    paso1 = cliente_autenticado.post(url_editar, datos_edicion_validos)
    assert paso1.status_code == 302
    assert paso1.url == url_confirmar

    revision = cliente_autenticado.get(url_confirmar)
    html_revision = revision.content.decode()
    assert revision.status_code == 200
    for texto in (
        AVISO_REVISION_EDICION,
        "Roberto Gómez",
        "Aguas del Sur S.A.",
        "CUIT",
        "20123456786",
        "nuevo@aguassur.com",
        "+54 11 5555-6666",
        "Av. Paseo Colón 850",
    ):
        assert texto in html_revision

    confirmacion = cliente_autenticado.post(url_confirmar, {"accion": "confirmar"})
    assert confirmacion.status_code == 302
    assert confirmacion.url == url_detalle
    assert clave_sesion_edicion(cliente_existente.pk) not in cliente_autenticado.session

    cliente_existente.refresh_from_db()
    assert cliente_existente.nombre == "Roberto Gómez"
    assert cliente_existente.razon_social == "Aguas del Sur S.A."
    assert cliente_existente.tipo_documento == "CUIT"
    assert cliente_existente.numero_documento == "20123456786"
    assert cliente_existente.email == "nuevo@aguassur.com"
    assert cliente_existente.telefono == "+54 11 5555-6666"
    assert cliente_existente.domicilio == "Av. Paseo Colón 850"
    assert Cliente.objects.count() == 1

    ficha = cliente_autenticado.get(url_detalle)
    html_ficha = ficha.content.decode()
    assert MENSAJE_EDICION_EXITO in html_ficha
    assert "Roberto Gómez" in html_ficha
    assert "nuevo@aguassur.com" in html_ficha
    assert "+54 11 5555-6666" in html_ficha
    assert "Av. Paseo Colón 850" in html_ficha

    busqueda = cliente_autenticado.get(reverse("clientes:buscar"), {"q": "Roberto"})
    assert "Roberto Gómez" in busqueda.content.decode()


def test_edicion_permite_vaciar_telefono_y_domicilio(cliente_autenticado, otro_cliente):
    url_editar = reverse("clientes:editar", args=[otro_cliente.pk])
    url_confirmar = reverse("clientes:editar_confirmar", args=[otro_cliente.pk])

    datos = {
        "nombre": otro_cliente.nombre,
        "razon_social": "",
        "tipo_documento": "DNI",
        "numero_documento": otro_cliente.numero_documento,
        "email": otro_cliente.email,
        "telefono": "",
        "domicilio": "",
    }
    assert cliente_autenticado.post(url_editar, datos).status_code == 302
    assert cliente_autenticado.post(url_confirmar, {"accion": "confirmar"}).status_code == 302

    otro_cliente.refresh_from_db()
    assert otro_cliente.telefono == ""
    assert otro_cliente.domicilio == ""


def test_volver_y_editar_conserva_borrador_sin_modificar_bd(
    cliente_autenticado, cliente_existente, datos_edicion_validos
):
    url_editar = reverse("clientes:editar", args=[cliente_existente.pk])
    cliente_autenticado.post(url_editar, datos_edicion_validos)

    respuesta = cliente_autenticado.get(f"{url_editar}?volver=1")
    html = respuesta.content.decode()
    assert respuesta.status_code == 200
    assert 'value="Roberto Gómez"' in input_de(html, "nombre")
    assert 'value="nuevo@aguassur.com"' in input_de(html, "email")
    assert 'value="+54 11 5555-6666"' in input_de(html, "telefono")
    assert 'value="Av. Paseo Colón 850"' in input_de(html, "domicilio")

    cliente_existente.refresh_from_db()
    assert cliente_existente.email == "contacto@aguassur.com"


def test_cancelar_en_confirmacion_borra_sesion_y_no_modifica_cliente(
    cliente_autenticado, cliente_existente, datos_edicion_validos
):
    url_editar = reverse("clientes:editar", args=[cliente_existente.pk])
    url_confirmar = reverse("clientes:editar_confirmar", args=[cliente_existente.pk])
    url_detalle = reverse("clientes:detalle", args=[cliente_existente.pk])

    cliente_autenticado.post(url_editar, datos_edicion_validos)

    respuesta = cliente_autenticado.post(url_confirmar, {"accion": "cancelar"})
    assert respuesta.status_code == 302
    assert respuesta.url == url_detalle
    assert clave_sesion_edicion(cliente_existente.pk) not in cliente_autenticado.session
    assert MENSAJE_EDICION_CANCELADA in cliente_autenticado.get(url_detalle).content.decode()

    cliente_existente.refresh_from_db()
    assert cliente_existente.email == "contacto@aguassur.com"

    sin_borrador = cliente_autenticado.get(url_confirmar)
    assert sin_borrador.status_code == 302
    assert sin_borrador.url == url_editar


def test_confirmacion_repetida_es_idempotente(
    cliente_autenticado, cliente_existente, datos_edicion_validos
):
    url_editar = reverse("clientes:editar", args=[cliente_existente.pk])
    url_confirmar = reverse("clientes:editar_confirmar", args=[cliente_existente.pk])
    url_detalle = reverse("clientes:detalle", args=[cliente_existente.pk])

    cliente_autenticado.post(url_editar, datos_edicion_validos)
    cliente_autenticado.post(url_confirmar, {"accion": "confirmar"})

    segunda = cliente_autenticado.post(url_confirmar, {"accion": "confirmar"})
    assert segunda.status_code == 302
    assert segunda.url == url_detalle
    assert MENSAJE_EDICION_EXITO in cliente_autenticado.get(url_detalle).content.decode()


def test_integrity_error_al_confirmar_edicion_informa_duplicado(
    cliente_autenticado, cliente_existente, datos_edicion_validos
):
    url_editar = reverse("clientes:editar", args=[cliente_existente.pk])
    url_confirmar = reverse("clientes:editar_confirmar", args=[cliente_existente.pk])

    datos = {
        **datos_edicion_validos,
        "tipo_documento": "DNI",
        "numero_documento": "31222333",
    }
    cliente_autenticado.post(url_editar, datos)

    Cliente.objects.create(
        nombre="Otro Cliente Concurrente",
        tipo_documento="DNI",
        numero_documento="31222333",
        email="otro@lab.com",
    )

    respuesta = cliente_autenticado.post(url_confirmar, {"accion": "confirmar"})
    assert respuesta.status_code == 302
    assert respuesta.url == f"{url_editar}?volver=1"
    assert clave_sesion_edicion(cliente_existente.pk) in cliente_autenticado.session
    assert MENSAJE_DUPLICADO in cliente_autenticado.get(respuesta.url).content.decode()

    cliente_existente.refresh_from_db()
    assert cliente_existente.numero_documento == "20123456786"


def test_error_de_base_al_confirmar_edicion_informa_sin_modificar(
    cliente_autenticado, cliente_existente, datos_edicion_validos, monkeypatch
):
    url_editar = reverse("clientes:editar", args=[cliente_existente.pk])
    url_confirmar = reverse("clientes:editar_confirmar", args=[cliente_existente.pk])

    cliente_autenticado.post(url_editar, datos_edicion_validos)

    def falla(cliente, datos):
        raise DatabaseError("base caída")

    monkeypatch.setattr("clientes.views.actualizar_cliente", falla)

    respuesta = cliente_autenticado.post(url_confirmar, {"accion": "confirmar"})
    html = respuesta.content.decode()
    assert respuesta.status_code == 200
    assert AVISO_REVISION_EDICION in html
    assert MENSAJE_ERROR_BD_EDICION in html
    assert clave_sesion_edicion(cliente_existente.pk) in cliente_autenticado.session

    cliente_existente.refresh_from_db()
    assert cliente_existente.email == "contacto@aguassur.com"
