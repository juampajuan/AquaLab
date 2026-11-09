"""Pantalla de comparación histórica (US 8.1): accesos, permisos, gráfico y variación."""

import datetime as dt
import json
import re

import pytest
from django.contrib.auth.models import Group
from django.test import Client
from django.urls import reverse

from estudios.models import Estudio, PruebaEstudio, Validacion
from muestras.models import Origen

pytestmark = pytest.mark.django_db

URL = reverse("estudios:comparacion")
DIA = dt.date(2026, 3, 2)


def dia(n):
    return DIA + dt.timedelta(days=n)


def html_de(respuesta):
    return respuesta.content.decode()


def datos_de(respuesta):
    texto = re.search(
        r'<script id="datos-comparacion" type="application/json">(.*?)</script>',
        html_de(respuesta),
        re.S,
    ).group(1)
    return json.loads(texto)


def tarjeta(html, codigo):
    inicio = html.index(f'data-prueba="{codigo}"')
    fin = html.find("data-prueba=", inicio + 1)
    return html[inicio : fin if fin != -1 else len(html)]


@pytest.fixture
def origen(cliente_a):
    return Origen.objects.create(cliente=cliente_a, nombre="Pozo de la vista")


@pytest.fixture
def historia(origen, estudio_en_origen):
    """Cloruro 100 y 120 validados, Cloruro 400 sin validar y pH sin historial en el actual."""
    estudio_en_origen(origen, dia(0), 400001, {"CL-": "10"})
    estudio_en_origen(origen, dia(1), 400002, {"CL-": "12"})
    return estudio_en_origen(origen, dia(2), 400003, {"CL-": "40", "PH": "7.2"}, validar_todo=False)


def usuario(django_user_model, email, *grupos):
    creado = django_user_model.objects.create_user(
        email=email, password="Clave-Valida-123", is_active=True
    )
    for nombre in grupos:
        creado.groups.add(Group.objects.get(name=nombre))
    cliente = Client()
    cliente.force_login(creado)
    return cliente


# --- Accesos y permisos (FR-001, FR-018) -----------------------------------------------------


def test_boton_en_detalle_solo_con_permiso(historia, cliente_bioquimico, django_user_model):
    detalle = reverse("estudios:detalle", args=[historia.pk])
    enlace = f'href="{URL}?estudio={historia.pk}"'

    con_permiso = html_de(cliente_bioquimico.get(detalle))
    sin_permiso = html_de(usuario(django_user_model, "tecnico-81@ejemplo.com").get(detalle))

    assert enlace in con_permiso and "Comparación histórica" in con_permiso
    assert enlace not in sin_permiso and "Comparación histórica" not in sin_permiso


def test_permisos(historia, cliente_bioquimico, django_user_model, staff_sin_permiso):
    url = f"{URL}?estudio={historia.pk}"

    sin_sesion = Client().get(url)
    sin_permiso = Client()
    sin_permiso.force_login(staff_sin_permiso)
    administrador = usuario(django_user_model, "admin-81@ejemplo.com", "Administradores")

    assert sin_sesion.status_code == 302
    assert sin_sesion["Location"].startswith(reverse("usuarios:login"))
    assert sin_permiso.get(url).status_code == 403
    assert administrador.get(url).status_code == 200
    assert cliente_bioquimico.get(url).status_code == 200


def test_post_405(historia, cliente_bioquimico):
    assert cliente_bioquimico.post(f"{URL}?estudio={historia.pk}").status_code == 405


@pytest.mark.parametrize("valor", ["999999", "abc"])
def test_estudio_inexistente_404(cliente_bioquimico, valor):
    assert cliente_bioquimico.get(f"{URL}?estudio={valor}").status_code == 404


# --- Desde el estudio (US 1) -----------------------------------------------------------------


def test_desde_estudio(historia, origen, cliente_bioquimico):
    respuesta = cliente_bioquimico.get(f"{URL}?estudio={historia.pk}")
    html = html_de(respuesta)

    assert respuesta.status_code == 200
    assert origen.nombre in html and origen.cliente.nombre_completo in html
    assert f"N° PI {historia.muestra.numero_pi}" in html
    assert historia.tipo_nombre_snapshot in html
    assert "Pendiente de análisis" in html or "En proceso" in html
    assert "Volver al estudio" in html
    assert html.count("data-prueba=") == 2

    cloruro = tarjeta(html, "CL-")
    assert '<canvas id="grafico-CL-"' in cloruro
    assert 'aria-label="Evolución de Cloruro en Pozo de la vista"' in cloruro
    assert "Máximo 350 mg/l · Límite general" in cloruro
    assert "Sin validar" in cloruro
    assert "Fuera de la franja del límite" in cloruro
    assert "▲ +280 mg/l (+233,3 %)" in cloruro  # 400 contra 120
    assert "Contra el promedio de 2 anteriores (110 mg/l)" in cloruro
    assert "▲ +290 mg/l (+263,6 %)" in cloruro

    datos = datos_de(respuesta)
    (cl,) = [p for p in datos["pruebas"] if p["codigo"] == "CL-"]
    assert cl["franja"] == {"min": None, "max": "350.0", "comparable": True}
    assert cl["puntos"][-1] == {
        "etiqueta": f"{dia(2):%d/%m/%Y} · PI 400003",
        "valor": "400.0000000000",
        "texto": "400",
        "validado": False,
        "referencia": True,
    }
    assert [p["referencia"] for p in cl["puntos"]] == [False, False, True]


def test_referencia_validada(origen, estudio_en_origen, cliente_bioquimico):
    estudio_en_origen(origen, dia(0), 400001, {"CL-": "10"})
    actual = estudio_en_origen(origen, dia(1), 400002, {"CL-": "12"})

    cloruro = tarjeta(html_de(cliente_bioquimico.get(f"{URL}?estudio={actual.pk}")), "CL-")

    assert "Validado" in cloruro and "Sin validar" not in cloruro
    assert "Fuera de la franja del límite" not in cloruro


def test_referencia_sin_resultado(origen, estudio_en_origen, cliente_bioquimico):
    estudio_en_origen(origen, dia(0), 400001, {"CL-": "10"})
    actual = estudio_en_origen(origen, dia(1), 400002, {"CL-": None})

    cloruro = tarjeta(html_de(cliente_bioquimico.get(f"{URL}?estudio={actual.pk}")), "CL-")

    assert "Sin resultado en este estudio" in cloruro
    assert '<canvas id="grafico-CL-"' in cloruro


def test_prueba_sin_historial(historia, cliente_bioquimico):
    ph = tarjeta(html_de(cliente_bioquimico.get(f"{URL}?estudio={historia.pk}")), "PH")

    assert "Sin historial para comparar" in ph
    assert "<canvas" not in ph
    assert "7,2" in ph and "Sin validar" in ph


def test_json_sin_float(historia, cliente_bioquimico):
    datos = datos_de(cliente_bioquimico.get(f"{URL}?estudio={historia.pk}"))

    assert [p["codigo"] for p in datos["pruebas"]] == ["CL-"]  # pH no tiene historial
    for prueba in datos["pruebas"]:
        for punto in prueba["puntos"]:
            assert isinstance(punto["valor"], str)
        for borde in prueba["franja"]["min"], prueba["franja"]["max"]:
            assert borde is None or isinstance(borde, str)


def test_solo_lectura(historia, cliente_bioquimico):
    def estado():
        return (
            sorted(Estudio.objects.values_list("pk", "estado")),
            sorted(PruebaEstudio.objects.values_list("pk", "estado")),
            sorted(Validacion.objects.values_list("pk", "anulada")),
        )

    antes = estado()
    cliente_bioquimico.get(f"{URL}?estudio={historia.pk}")

    assert estado() == antes


def test_sin_parametros_ofrece_volver_al_dashboard(cliente_bioquimico):
    html = html_de(cliente_bioquimico.get(URL))

    assert "data-prueba=" not in html
    assert reverse("informes:dashboard") in html
