"""Pantallas de gestión del catálogo (SCRUM-73)."""

import re

import pytest
from django.contrib.auth.models import Group
from django.test import Client
from django.urls import reverse

from estudios.models import TipoEstudio
from pruebas.models import Prueba

pytestmark = pytest.mark.django_db


def solicitud(respuesta):
    return re.search(r"solicitud=([\w-]+)", respuesta["Location"]).group(1)


def token(html):
    return re.search(r'name="token" value="([^"]+)"', html).group(1)


def contexto(html):
    return re.search(r'name="contexto" value="([^"]+)"', html).group(1)


def confirmar(cliente, respuesta, **extra):
    pagina = cliente.get(respuesta["Location"]).content.decode()
    return cliente.post(
        reverse("catalogo:confirmar"), {"token": token(pagina), "accion": "confirmar", **extra}
    )


def test_alta_por_pantalla(cliente_catalogo, datos_prueba):
    url = reverse("catalogo:nueva")
    html = cliente_catalogo.get(url).content.decode()
    datos = datos_prueba(formula="x*9", contexto=contexto(html))
    respuesta = cliente_catalogo.post(url, datos)
    assert respuesta.status_code == 302
    resumen = cliente_catalogo.get(respuesta["Location"]).content.decode()
    assert "TEST-DIR" in resumen and "Prueba directa" in resumen
    final = confirmar(cliente_catalogo, respuesta)
    prueba = Prueba.objects.get(codigo="TEST-DIR")
    assert final["Location"] == reverse("catalogo:ficha", args=[prueba.pk])
    assert prueba.formula == ""  # Directo descarta la fórmula
    ficha = cliente_catalogo.get(final["Location"]).content.decode()
    assert "Prueba creada." in ficha and "Ana Admin" in ficha


def test_volver_a_editar_conserva_datos(cliente_catalogo, datos_prueba):
    url = reverse("catalogo:nueva")
    datos = datos_prueba(nombre="Guardada en borrador")
    datos["contexto"] = contexto(cliente_catalogo.get(url).content.decode())
    respuesta = cliente_catalogo.post(url, datos)
    html = cliente_catalogo.get(url + "?solicitud=" + solicitud(respuesta)).content.decode()
    assert "Guardada en borrador" in html
    assert not Prueba.objects.exists()


def test_ficha_en_uso(cliente_catalogo, prueba_en_tipo):
    html = cliente_catalogo.get(
        reverse("catalogo:ficha", args=[prueba_en_tipo.pk])
    ).content.decode()
    assert "su método no se puede cambiar" in html
    assert reverse("catalogo:eliminar", args=[prueba_en_tipo.pk]) not in html
    form = cliente_catalogo.get(
        reverse("catalogo:editar", args=[prueba_en_tipo.pk])
    ).content.decode()
    assert re.search(r'name="codigo"[^>]*disabled', form)


def test_envio_alterado(cliente_catalogo, prueba_en_tipo):
    from pruebas import gestion

    url = reverse("catalogo:editar", args=[prueba_en_tipo.pk])
    datos = gestion.datos_de(prueba_en_tipo)
    datos.update(codigo="HACK", limite_max="5")
    datos["contexto"] = contexto(cliente_catalogo.get(url).content.decode())
    confirmar(cliente_catalogo, cliente_catalogo.post(url, datos))
    prueba_en_tipo.refresh_from_db()
    assert prueba_en_tipo.codigo == "USO-T" and prueba_en_tipo.limite_max == "5"


def test_avisos_desactivar(cliente_catalogo):
    ca = Prueba.objects.create(codigo="CA", nombre="Calcio")
    Prueba.objects.create(
        codigo="MG", nombre="Magnesio", tipo_calculo="FORMULA", formula="{CA}*2", es_calculada=True
    )
    solo = TipoEstudio.objects.create(nombre="Solo calcio")
    solo.pruebas.set([ca])
    respuesta = cliente_catalogo.get(reverse("catalogo:desactivar", args=[ca.pk]))
    html = cliente_catalogo.get(respuesta["Location"]).content.decode()
    assert "La usan en su fórmula: MG" in html
    assert "Solo calcio" in html and "Este tipo no se va a poder usar" in html


def test_desactivar_y_reactivar(cliente_catalogo, administrador_catalogo):
    ca = Prueba.objects.create(codigo="CA", nombre="Calcio")
    mg = Prueba.objects.create(
        codigo="MG", nombre="Magnesio", tipo_calculo="FORMULA", formula="{CA}*2", es_calculada=True
    )
    final = confirmar(
        cliente_catalogo, cliente_catalogo.get(reverse("catalogo:desactivar", args=[ca.pk]))
    )
    assert "Prueba desactivada." in cliente_catalogo.get(final["Location"]).content.decode()
    ca.refresh_from_db()
    assert not ca.activa and ca.version == 2 and ca.modificada_por == administrador_catalogo
    confirmar(cliente_catalogo, cliente_catalogo.get(reverse("catalogo:desactivar", args=[mg.pk])))
    respuesta = cliente_catalogo.get(reverse("catalogo:reactivar", args=[mg.pk]))
    assert (
        "Usa en su fórmula una prueba inactiva: CA"
        in cliente_catalogo.get(respuesta["Location"]).content.decode()
    )


def test_listado(cliente_catalogo):
    Prueba.objects.create(codigo="CA", nombre="Calcio", activa=False)
    mg = Prueba.objects.create(
        codigo="MG", nombre="Magnesio", tipo_calculo="FORMULA", formula="{CA}*2", es_calculada=True
    )
    html = cliente_catalogo.get(reverse("administracion:pruebas")).content.decode()
    assert "Depende de una prueba inactiva: CA" in html
    assert reverse("catalogo:nueva") in html
    assert reverse("catalogo:ficha", args=[mg.pk]) in html
    assert "Editar en Django Admin" not in html


RUTAS = [
    ("catalogo:nueva", False),
    ("catalogo:ficha", True),
    ("catalogo:editar", True),
    ("catalogo:desactivar", True),
    ("catalogo:reactivar", True),
    ("catalogo:eliminar", True),
]


@pytest.mark.parametrize(("nombre", "con_pk"), RUTAS)
@pytest.mark.parametrize("quien", ["anonimo", "comun", "bioquimico", "superusuario"])
def test_acceso(django_user_model, prueba_libre, nombre, con_pk, quien):
    url = reverse(nombre, args=[prueba_libre.pk] if con_pk else [])
    cliente = Client()
    if quien != "anonimo":
        usuario = django_user_model.objects.create_user(
            email=f"{quien}@x.com",
            password="Clave-Valida-123",
            is_superuser=quien == "superusuario",
        )
        if quien == "bioquimico":
            usuario.groups.add(Group.objects.get_or_create(name="Bioquímicos")[0])
        cliente.force_login(usuario)
    respuesta = cliente.get(url)
    if quien == "anonimo":
        assert respuesta.status_code == 302 and "login" in respuesta["Location"]
    else:
        assert respuesta.status_code == 403
    assert Prueba.objects.get(pk=prueba_libre.pk).activa


def test_confirmar_sin_permiso(django_user_model):
    usuario = django_user_model.objects.create_user(email="c@x.com", password="Clave-Valida-123")
    cliente = Client()
    cliente.force_login(usuario)
    assert cliente.post(reverse("catalogo:confirmar"), {"accion": "confirmar"}).status_code == 403
