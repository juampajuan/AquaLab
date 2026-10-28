import re

import pytest
from django.conf import settings
from django.urls import reverse

pytestmark = pytest.mark.django_db

ENLACES_MENU = {
    "Inicio": "inicio",
    "Buscar cliente": "clientes:buscar",
    "Registrar cliente": "clientes:registrar",
    "Registrar muestra": "muestras:registrar",
    "Crear estudio": "estudios:crear",
}
RECURSOS_EXTERNOS = ("cdn.jsdelivr.net", "cdn.tailwindcss.com", "fonts.googleapis.com")
IMAGENES_ACCESO = ("laboratorio", "mesada-muestras", "toma-de-muestra", "tubos-pipeta")


@pytest.fixture
def empleado(django_user_model):
    return django_user_model.objects.create_user(
        email="elena.ramos@example.com",
        password="Clave-Segura-Layout-321",
        first_name="Elena",
        last_name="Ramos",
    )


@pytest.fixture
def cliente_http(client, empleado):
    client.force_login(empleado)
    return client


def menu_de(html):
    encontrado = re.search(r"<nav[^>]*data-menu-navegacion[^>]*>(.*?)</nav>", html, re.S)
    assert encontrado, "La pantalla no tiene el menú lateral"
    return encontrado.group(1)


def enlace_activo(menu):
    return re.findall(r'<a[^>]*aria-current="page"[^>]*>\s*([^<]*?)\s*</a>', menu)


# Layout interno (US1 escenarios 1 a 3)


@pytest.mark.parametrize(
    "ruta", ["inicio", "clientes:buscar", "clientes:registrar", "muestras:registrar"]
)
def test_pantalla_interna_tiene_menu_usuario_y_cerrar_sesion(cliente_http, ruta):
    html = cliente_http.get(reverse(ruta)).content.decode()

    menu = menu_de(html)
    for texto, nombre in ENLACES_MENU.items():
        assert re.search(rf'href="{reverse(nombre)}"[^>]*>\s*{texto}\s*</a>', menu), texto
    assert "Elena Ramos" in html
    assert reverse("usuarios:logout") in html
    assert "Cerrar sesión" in html


@pytest.mark.parametrize(
    ("ruta", "activo"),
    [
        ("inicio", "Inicio"),
        ("clientes:buscar", "Buscar cliente"),
        ("clientes:registrar", "Registrar cliente"),
        ("muestras:registrar", "Registrar muestra"),
        ("estudios:crear", "Crear estudio"),
    ],
)
def test_menu_destaca_la_pantalla_actual(cliente_http, ruta, activo):
    html = cliente_http.get(reverse(ruta)).content.decode()

    assert enlace_activo(menu_de(html)) == [activo]


# Layout de acceso (US1 escenarios 4 y 5)


@pytest.mark.parametrize("ruta", ["usuarios:login", "usuarios:registro"])
def test_pantallas_de_acceso_sin_menu(client, ruta):
    html = client.get(reverse(ruta)).content.decode()

    assert "data-menu-navegacion" not in html
    assert "AquaLab" in html


def test_login_alterna_las_imagenes_del_laboratorio(client):
    html = client.get(reverse("usuarios:login")).content.decode()

    for nombre in IMAGENES_ACCESO:
        assert f"img/acceso/{nombre}.webp" in html


def test_css_compilado_respeta_reducir_movimiento():
    css = (settings.BASE_DIR / "static" / "css" / "aqualab.css").read_text()

    assert "prefers-reduced-motion" in css
    assert "acceso-fundido" in css


# Recursos propios (FR-018)


@pytest.mark.parametrize("ruta", ["usuarios:login", "usuarios:registro"])
def test_acceso_sin_recursos_externos(client, ruta):
    html = client.get(reverse(ruta)).content.decode()

    assert "css/aqualab.css" in html
    assert not [r for r in RECURSOS_EXTERNOS if r in html]


@pytest.mark.parametrize("ruta", list(ENLACES_MENU.values()))
def test_pantallas_internas_sin_recursos_externos(cliente_http, ruta):
    html = cliente_http.get(reverse(ruta)).content.decode()

    assert "css/aqualab.css" in html
    assert not [r for r in RECURSOS_EXTERNOS if r in html]
