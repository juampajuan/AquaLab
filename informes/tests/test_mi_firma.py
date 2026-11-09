import pytest
from django.contrib.messages import get_messages
from django.test import Client
from django.urls import reverse

from informes.firmas import TAMANO_MAXIMO
from informes.models import FirmaProfesional

from .utiles import data_url, png

pytestmark = pytest.mark.django_db

URL = reverse("informes:mi_firma")


def mensajes(respuesta):
    return [str(m) for m in get_messages(respuesta.wsgi_request)]


@pytest.fixture
def cliente_sin_firma(bioquimico_sin_firma):
    c = Client()
    c.force_login(bioquimico_sin_firma)
    return c


def test_mi_firma_muestra_formulario_sin_firma(cliente_sin_firma):
    respuesta = cliente_sin_firma.get(URL)
    assert respuesta.status_code == 200
    html = respuesta.content.decode()
    for texto in (
        "Mi firma",
        "data-firma",
        "Firmá con el mouse o con el dedo",
        "data-firma-borrar",
        "Borrar",
        'name="firma"',
        "Matrícula",
        'placeholder="MP 1234"',
        "Guardar firma",
        "informes/firma.js",
    ):
        assert texto in html, texto
    assert "data:image/png;base64," not in html


def test_mi_firma_muestra_actual(cliente_bioquimico, bioquimico):
    html = cliente_bioquimico.get(URL).content.decode()
    assert bioquimico.firma_profesional.data_url in html
    assert "MP 1234" in html


def test_con_firma_la_matricula_no_es_editable(cliente_bioquimico):
    html = cliente_bioquimico.get(URL).content.decode()
    assert 'name="matricula"' not in html
    assert "pedíselo a un administrador" in html


def test_guarda_firma_y_matricula(cliente_sin_firma, bioquimico_sin_firma):
    datos = png()
    respuesta = cliente_sin_firma.post(URL, {"firma": data_url(datos), "matricula": " MP 9 "})
    assert respuesta.status_code == 302
    assert respuesta.url == URL
    assert mensajes(respuesta) == ["Se guardó tu firma."]
    firma = FirmaProfesional.objects.get(usuario=bioquimico_sin_firma)
    assert bytes(firma.imagen) == datos
    assert firma.matricula == "MP 9"


@pytest.mark.parametrize(
    ("datos", "mensaje"),
    [
        ({"firma": "", "matricula": "MP 1"}, "Dibujá tu firma antes de guardar."),
        ({"firma": data_url(png()), "matricula": ""}, "Este campo es obligatorio."),
        (
            {"firma": data_url(png(), tipo="image/jpeg"), "matricula": "MP 1"},
            "La firma no es una imagen válida.",
        ),
        (
            {"firma": data_url(png(1201, 200)), "matricula": "MP 1"},
            "La firma no es una imagen válida.",
        ),
        (
            {"firma": data_url(png(relleno=b"x" * (TAMANO_MAXIMO + 1))), "matricula": "MP 1"},
            "La firma es demasiado grande.",
        ),
        ({"firma": data_url(png()), "matricula": "M" * 41}, "41"),
    ],
    ids=["vacia", "sin-matricula", "jpeg", "muy-ancha", "muy-grande", "matricula-larga"],
)
def test_rechaza_firma_invalida(cliente_sin_firma, bioquimico_sin_firma, datos, mensaje):
    respuesta = cliente_sin_firma.post(URL, datos)
    assert respuesta.status_code == 200
    assert mensaje in respuesta.content.decode()
    assert not FirmaProfesional.objects.filter(usuario=bioquimico_sin_firma).exists()


def test_rechazo_no_cambia_la_guardada(cliente_bioquimico, bioquimico):
    antes = bytes(bioquimico.firma_profesional.imagen)
    respuesta = cliente_bioquimico.post(
        URL, {"firma": data_url(png(1201, 200)), "matricula": "MP 5"}
    )
    assert respuesta.status_code == 200
    firma = FirmaProfesional.objects.get(usuario=bioquimico)
    assert bytes(firma.imagen) == antes
    assert firma.matricula == "MP 1234"


def test_reemplaza_firma(cliente_bioquimico, bioquimico):
    nueva = png(300, 100)
    respuesta = cliente_bioquimico.post(URL, {"firma": data_url(nueva)})
    assert respuesta.status_code == 302
    assert FirmaProfesional.objects.filter(usuario=bioquimico).count() == 1
    firma = FirmaProfesional.objects.get(usuario=bioquimico)
    assert bytes(firma.imagen) == nueva
    assert firma.matricula == "MP 1234"


@pytest.mark.parametrize("firma", ["", "nueva"], ids=["sin-dibujo", "con-dibujo"])
def test_ignora_matricula_enviada_si_ya_hay_firma(cliente_bioquimico, bioquimico, firma):
    """SCRUM-81: un POST armado a mano no cambia la matrícula guardada."""
    datos = {"firma": data_url(png(300, 100)) if firma else "", "matricula": "MP 777"}
    respuesta = cliente_bioquimico.post(URL, datos)
    assert respuesta.status_code == 302
    assert FirmaProfesional.objects.get(usuario=bioquimico).matricula == "MP 1234"


def test_firma_es_del_usuario(cliente_sin_firma, bioquimico_sin_firma, django_user_model, firma_de):
    otro = django_user_model.objects.create_user(
        email="otro-bioq@ejemplo.com", password="Clave-Valida-123", is_active=True
    )
    firma_otro = firma_de(otro, matricula="MP 2")
    cliente_sin_firma.post(URL, {"firma": data_url(png()), "matricula": "MP 3", "usuario": otro.pk})
    firma_otro.refresh_from_db()
    assert firma_otro.matricula == "MP 2"
    assert FirmaProfesional.objects.get(usuario=bioquimico_sin_firma).matricula == "MP 3"


def test_mi_firma_sin_permiso_403(cliente_http, empleado):
    assert cliente_http.get(URL).status_code == 403
    respuesta = cliente_http.post(URL, {"firma": data_url(png()), "matricula": "MP 1"})
    assert respuesta.status_code == 403
    assert not FirmaProfesional.objects.filter(usuario=empleado).exists()


def test_enlace_mi_firma_solo_con_permiso(cliente_http, django_user_model, firma_de):
    from estudios.tests.conftest import en_grupo_bioquimicos

    assert f'href="{URL}"' not in cliente_http.get(reverse("inicio")).content.decode()
    bioq = en_grupo_bioquimicos(
        django_user_model.objects.create_user(
            email="bioq-enlace@ejemplo.com", password="Clave-Valida-123", is_active=True
        )
    )
    c = Client()
    c.force_login(bioq)
    html = c.get(reverse("inicio")).content.decode()
    assert f'href="{URL}"' in html
    assert "Mi firma" in html
