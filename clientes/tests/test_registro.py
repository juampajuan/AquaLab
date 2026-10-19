import re

import pytest
from django.db import DatabaseError
from django.urls import reverse

from clientes.models import Cliente

pytestmark = pytest.mark.django_db

CLAVE_SESION = "cliente_pendiente"
MENSAJE_EXITO = "Cliente registrado correctamente."
MENSAJE_CANCELADO = "Registro de cliente cancelado."
MENSAJE_DUPLICADO = "Ya existe un cliente registrado con este tipo y número de documento."
MENSAJE_NOMBRE_O_RAZON = "Debés ingresar al menos el nombre o la razón social del cliente."
MENSAJE_DNI_INVALIDO = "El DNI debe tener 7 u 8 dígitos numéricos."
MENSAJE_CUIT_INVALIDO = "El CUIT debe tener 11 dígitos y un dígito verificador válido."
MENSAJE_TELEFONO_INVALIDO = "Ingresá un número de teléfono válido (entre 7 y 15 dígitos)."
AVISO_REVISION = "Revisá los datos del cliente antes de confirmar el registro."


def cantidad_clientes():
    return Cliente.objects.count()


def input_de(html, nombre):
    encontrado = re.search(rf'<input[^>]*name="{nombre}"[^>]*>', html)
    assert encontrado, f"no se encontró el input {nombre}"
    return encontrado.group(0)


# Paso 1: formulario y validaciones


def test_vistas_requieren_sesion_activa(client, cliente_existente):
    url_registrar = reverse("clientes:registrar")
    url_confirmar = reverse("clientes:registrar_confirmar")
    url_detalle = reverse("clientes:detalle", args=[cliente_existente.pk])

    assert client.get(url_registrar).status_code == 302
    assert client.post(url_registrar, {}).status_code == 302
    assert client.get(url_confirmar).status_code == 302
    assert client.post(url_confirmar, {"accion": "confirmar"}).status_code == 302
    assert client.get(url_detalle).status_code == 302


@pytest.mark.parametrize(
    ("campos_vacios", "espera_error_general"),
    [
        (["nombre", "razon_social"], True),
        (["tipo_documento"], False),
        (["numero_documento"], False),
        (["email"], False),
        (
            [
                "nombre",
                "razon_social",
                "tipo_documento",
                "numero_documento",
                "email",
                "telefono",
                "domicilio",
            ],
            True,
        ),
    ],
    ids=["sin_nombre_ni_razon", "tipo_documento", "numero_documento", "email", "todos"],
)
def test_formulario_incompleto_no_avanza(
    cliente_autenticado, datos_cliente_persona, campos_vacios, espera_error_general
):
    datos = {**datos_cliente_persona, **dict.fromkeys(campos_vacios, "")}

    respuesta = cliente_autenticado.post(reverse("clientes:registrar"), datos)

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
    assert CLAVE_SESION not in cliente_autenticado.session
    assert cantidad_clientes() == 0


@pytest.mark.parametrize("dni", ["123456", "123456789", "12A45678"])
def test_dni_formato_invalido_rechazado(cliente_autenticado, datos_cliente_persona, dni):
    datos = {**datos_cliente_persona, "tipo_documento": "DNI", "numero_documento": dni}

    respuesta = cliente_autenticado.post(reverse("clientes:registrar"), datos)

    assert respuesta.status_code == 200
    assert respuesta.context["form"].errors["numero_documento"] == [MENSAJE_DNI_INVALIDO]
    assert CLAVE_SESION not in cliente_autenticado.session
    assert cantidad_clientes() == 0


@pytest.mark.parametrize(
    "cuit",
    ["2012345678", "201234567890", "20-12345678-0", "20-1234567A-6"],
)
def test_cuit_formato_o_digito_verificador_invalido_rechazado(
    cliente_autenticado, datos_cliente_empresa, cuit
):
    datos = {**datos_cliente_empresa, "tipo_documento": "CUIT", "numero_documento": cuit}

    respuesta = cliente_autenticado.post(reverse("clientes:registrar"), datos)

    assert respuesta.status_code == 200
    assert respuesta.context["form"].errors["numero_documento"] == [MENSAJE_CUIT_INVALIDO]
    assert CLAVE_SESION not in cliente_autenticado.session
    assert cantidad_clientes() == 0


@pytest.mark.parametrize(
    "documento",
    ["20123456786", "20-12345678-6", "20.123.456.786", " 20 12345678 6 "],
)
def test_documento_duplicado_con_separadores_rechazado(
    cliente_autenticado, datos_cliente_empresa, cliente_existente, documento
):
    datos = {**datos_cliente_empresa, "numero_documento": documento}

    respuesta = cliente_autenticado.post(reverse("clientes:registrar"), datos)

    assert respuesta.status_code == 200
    assert respuesta.context["form"].errors["numero_documento"] == [MENSAJE_DUPLICADO]
    assert respuesta.content.decode().count(MENSAJE_DUPLICADO) == 1
    assert CLAVE_SESION not in cliente_autenticado.session
    assert cantidad_clientes() == 1


@pytest.mark.parametrize("email", ["cliente@", "cliente.com", "cliente@@lab.com"])
def test_correo_invalido_rechazado(cliente_autenticado, datos_cliente_persona, email):
    respuesta = cliente_autenticado.post(
        reverse("clientes:registrar"), {**datos_cliente_persona, "email": email}
    )

    assert respuesta.status_code == 200
    assert "Introduzca una dirección de email válida." in respuesta.context["form"].errors["email"]
    assert CLAVE_SESION not in cliente_autenticado.session
    assert cantidad_clientes() == 0

    confirmar = cliente_autenticado.get(reverse("clientes:registrar_confirmar"))
    assert confirmar.status_code == 302
    assert confirmar.url == reverse("clientes:registrar")


@pytest.mark.parametrize("telefono", ["12345", "telefono-abc", "+54 11 123456789012345"])
def test_telefono_invalido_rechazado(cliente_autenticado, datos_cliente_persona, telefono):
    respuesta = cliente_autenticado.post(
        reverse("clientes:registrar"), {**datos_cliente_persona, "telefono": telefono}
    )

    assert respuesta.status_code == 200
    assert respuesta.context["form"].errors["telefono"] == [MENSAJE_TELEFONO_INVALIDO]
    assert CLAVE_SESION not in cliente_autenticado.session
    assert cantidad_clientes() == 0


def test_errores_conservan_datos_validos(cliente_autenticado, datos_cliente_persona):
    datos = {
        **datos_cliente_persona,
        "razon_social": "Laboratorio Norte",
        "numero_documento": "123",
    }

    respuesta = cliente_autenticado.post(reverse("clientes:registrar"), datos)

    html = respuesta.content.decode()
    assert respuesta.status_code == 200
    assert 'value="Juan Pérez"' in input_de(html, "nombre")
    assert 'value="Laboratorio Norte"' in input_de(html, "razon_social")
    assert 'value="juan@ejemplo.com"' in input_de(html, "email")
    assert 'value="+54 11 4321-5678"' in input_de(html, "telefono")
    assert 'value="Av. Corrientes 1234"' in input_de(html, "domicilio")


# Paso 2 y 3: revisión, confirmación y ficha de detalle


def test_confirmar_crea_cliente_persona_con_dni(cliente_autenticado, datos_cliente_persona):
    respuesta = cliente_autenticado.post(reverse("clientes:registrar"), datos_cliente_persona)
    assert respuesta.status_code == 302
    assert respuesta.url == reverse("clientes:registrar_confirmar")

    revision = cliente_autenticado.get(reverse("clientes:registrar_confirmar"))
    html = revision.content.decode()
    assert revision.status_code == 200
    for texto in (
        AVISO_REVISION,
        "Juan Pérez",
        "DNI",
        "30123456",
        "juan@ejemplo.com",
        "+54 11 4321-5678",
        "Av. Corrientes 1234",
    ):
        assert texto in html

    confirmacion = cliente_autenticado.post(
        reverse("clientes:registrar_confirmar"), {"accion": "confirmar"}
    )
    cliente = Cliente.objects.get()
    assert confirmacion.status_code == 302
    assert confirmacion.url == reverse("clientes:detalle", args=[cliente.pk])

    assert cliente.nombre == "Juan Pérez"
    assert cliente.razon_social == ""
    assert cliente.tipo_documento == "DNI"
    assert cliente.numero_documento == "30123456"
    assert cliente.email == "juan@ejemplo.com"
    assert cliente.telefono == "+54 11 4321-5678"
    assert cliente.domicilio == "Av. Corrientes 1234"
    assert cliente.activo
    assert CLAVE_SESION not in cliente_autenticado.session

    detalle = cliente_autenticado.get(confirmacion.url)
    assert MENSAJE_EXITO in detalle.content.decode()


def test_confirmar_crea_cliente_empresa_con_cuit(cliente_autenticado, datos_cliente_empresa):
    respuesta = cliente_autenticado.post(reverse("clientes:registrar"), datos_cliente_empresa)
    assert respuesta.status_code == 302

    confirmacion = cliente_autenticado.post(
        reverse("clientes:registrar_confirmar"), {"accion": "confirmar"}
    )
    cliente = Cliente.objects.get()
    assert confirmacion.status_code == 302
    assert confirmacion.url == reverse("clientes:detalle", args=[cliente.pk])
    assert cliente.nombre == ""
    assert cliente.razon_social == "Aguas del Sur S.A."
    assert cliente.tipo_documento == "CUIT"
    assert cliente.numero_documento == "20123456786"
    assert cliente.email == "contacto@aguassur.com"
    assert cliente.telefono == ""
    assert cliente.domicilio == ""
    assert cliente.activo


def test_detalle_muestra_todos_los_datos_registrados(cliente_autenticado):
    cliente = Cliente.objects.create(
        nombre="María Gómez",
        razon_social="Hidrolab S.R.L.",
        tipo_documento="CUIT",
        numero_documento="27234567891",
        email="maria@hidrolab.com",
        telefono="+54 11 5555-1234",
        domicilio="Av. Libertador 500",
    )

    respuesta = cliente_autenticado.get(reverse("clientes:detalle", args=[cliente.pk]))
    html = respuesta.content.decode()
    assert respuesta.status_code == 200
    for texto in (
        "María Gómez",
        "Hidrolab S.R.L.",
        "CUIT",
        "27234567891",
        "maria@hidrolab.com",
        "+54 11 5555-1234",
        "Av. Libertador 500",
        "Activo",
    ):
        assert texto in html

    assert cliente_autenticado.get(reverse("clientes:detalle", args=[99999])).status_code == 404


def test_volver_y_editar_precarga_datos_sin_crear_cliente(en_revision):
    respuesta = en_revision.get(reverse("clientes:registrar"))

    html = respuesta.content.decode()
    assert respuesta.status_code == 200
    assert 'value="Aguas del Sur S.A."' in input_de(html, "razon_social")
    assert 'value="20123456786"' in input_de(html, "numero_documento")
    assert 'value="contacto@aguassur.com"' in input_de(html, "email")
    assert cantidad_clientes() == 0


def test_cancelar_borra_sesion_y_no_crea_cliente(en_revision):
    respuesta = en_revision.post(reverse("clientes:registrar_confirmar"), {"accion": "cancelar"})

    assert respuesta.status_code == 302
    assert respuesta.url == reverse("clientes:registrar")
    assert MENSAJE_CANCELADO in en_revision.get(respuesta.url).content.decode()
    assert CLAVE_SESION not in en_revision.session
    assert cantidad_clientes() == 0

    confirmar = en_revision.get(reverse("clientes:registrar_confirmar"))
    assert confirmar.status_code == 302
    assert confirmar.url == reverse("clientes:registrar")


def test_confirmacion_repetida_crea_un_solo_cliente(en_revision):
    url = reverse("clientes:registrar_confirmar")
    en_revision.post(url, {"accion": "confirmar"})
    cliente = Cliente.objects.get()

    segunda = en_revision.post(url, {"accion": "confirmar"})
    assert segunda.status_code == 302
    assert segunda.url == reverse("clientes:detalle", args=[cliente.pk])
    assert MENSAJE_EXITO in en_revision.get(segunda.url).content.decode()
    assert cantidad_clientes() == 1


def test_integrity_error_al_confirmar_no_duplica_cliente(en_revision):
    Cliente.objects.create(
        razon_social="Otra Empresa",
        tipo_documento="CUIT",
        numero_documento="20123456786",
        email="otra@lab.com",
    )

    respuesta = en_revision.post(reverse("clientes:registrar_confirmar"), {"accion": "confirmar"})

    assert respuesta.status_code == 302
    assert respuesta.url == reverse("clientes:registrar")
    assert MENSAJE_DUPLICADO in en_revision.get(respuesta.url).content.decode()
    assert cantidad_clientes() == 1


def test_error_de_base_al_confirmar_informa_sin_crear(en_revision, monkeypatch):
    def falla(datos):
        raise DatabaseError("base caída")

    monkeypatch.setattr("clientes.views.crear_cliente", falla)

    respuesta = en_revision.post(reverse("clientes:registrar_confirmar"), {"accion": "confirmar"})

    html = respuesta.content.decode()
    assert respuesta.status_code == 200
    assert AVISO_REVISION in html
    assert "No se pudo completar el registro del cliente. Intentá nuevamente." in html
    assert cantidad_clientes() == 0
    assert CLAVE_SESION in en_revision.session
