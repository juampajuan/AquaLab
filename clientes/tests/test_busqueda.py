import pytest
from django.conf import settings
from django.test import Client
from django.urls import reverse

from clientes.models import Cliente

URL = "clientes:buscar"


def buscar(cliente_http, q, **extra):
    return cliente_http.get(reverse(URL), {"q": q, **extra})


def nombres(respuesta):
    return [c.nombre_completo for c in respuesta.context["page_obj"]]


@pytest.mark.django_db
def test_busca_por_nombre(cliente_autenticado, clientes_busqueda):
    respuesta = buscar(cliente_autenticado, "Pérez")
    assert nombres(respuesta) == ["Juan Pérez"]


@pytest.mark.django_db
def test_busca_por_razon_social(cliente_autenticado, clientes_busqueda):
    respuesta = buscar(cliente_autenticado, "aguas")
    assert nombres(respuesta) == ["Aguas del Sur S.A."]


@pytest.mark.django_db
@pytest.mark.parametrize("texto", ["30123456", "30.123.456", "30-123-456", " 30 123 456 ", "1234"])
def test_busca_por_dni_normalizado_o_parcial(cliente_autenticado, clientes_busqueda, texto):
    respuesta = buscar(cliente_autenticado, texto)
    assert "Juan Pérez" in nombres(respuesta)


@pytest.mark.django_db
@pytest.mark.parametrize("texto", ["20-12345678-6", "20123456786"])
def test_busca_por_cuit(cliente_autenticado, clientes_busqueda, texto):
    assert nombres(buscar(cliente_autenticado, texto)) == ["Aguas del Sur S.A."]


@pytest.mark.django_db
def test_resultado_muestra_datos_para_distinguir(cliente_autenticado, clientes_busqueda):
    contenido = buscar(cliente_autenticado, "aguas").content.decode()
    assert "Aguas del Sur S.A." in contenido
    assert "CUIT 20123456786" in contenido
    assert "cliente1@ejemplo.com" in contenido


@pytest.mark.django_db
def test_sin_coincidencias_informa_y_permite_buscar_de_nuevo(
    cliente_autenticado, clientes_busqueda
):
    respuesta = buscar(cliente_autenticado, "zzzz")
    assert respuesta.status_code == 200
    assert "No se encontraron clientes" in respuesta.content.decode()
    assert 'name="q"' in respuesta.content.decode()


@pytest.mark.django_db
@pytest.mark.parametrize("texto", ["PEREZ", "perez", "pérez", "PÉREZ"])
def test_ignora_mayusculas_y_tildes(cliente_autenticado, clientes_busqueda, texto):
    assert nombres(buscar(cliente_autenticado, texto)) == ["Juan Pérez"]


@pytest.mark.django_db
def test_ignora_tildes_tambien_en_razon_social(cliente_autenticado, clientes_busqueda):
    assert nombres(buscar(cliente_autenticado, "rio claro")) == ["Cooperativa Río Claro"]


@pytest.mark.django_db
@pytest.mark.parametrize("texto", ["", "   "])
def test_busqueda_vacia_lista_todos_los_clientes(cliente_autenticado, clientes_busqueda, texto):
    respuesta = buscar(cliente_autenticado, texto)
    assert respuesta.status_code == 200
    assert not respuesta.context["form"].errors
    assert respuesta.context["page_obj"] is not None
    assert respuesta.context["page_obj"].paginator.count == 6


@pytest.mark.django_db
def test_busqueda_de_un_caracter_pide_minimo(cliente_autenticado, clientes_busqueda):
    respuesta = buscar(cliente_autenticado, "a")
    assert respuesta.context["page_obj"] is None
    assert "Ingresá al menos 2 caracteres para buscar." in respuesta.content.decode()


@pytest.mark.django_db
def test_busqueda_supera_longitud_maxima_muestra_error(cliente_autenticado, clientes_busqueda):
    respuesta = buscar(cliente_autenticado, "a" * 101)
    assert respuesta.status_code == 200
    assert respuesta.context["page_obj"] is None
    assert "Ingresá como máximo 100 caracteres para buscar." in respuesta.content.decode()


@pytest.mark.django_db
def test_sin_parametro_lista_todos_los_clientes(cliente_autenticado, clientes_busqueda):
    respuesta = cliente_autenticado.get(reverse(URL))
    assert respuesta.status_code == 200
    assert not respuesta.context["form"].errors
    assert respuesta.context["page_obj"] is not None
    assert respuesta.context["page_obj"].paginator.count == 6
    html = respuesta.content.decode()
    assert "6 clientes registrados" in html
    assert 'role="tooltip"' in html
    assert "group-hover:visible" in html


@pytest.mark.django_db
def test_sin_clientes_registrados_muestra_estado_vacio(cliente_autenticado):
    respuesta = cliente_autenticado.get(reverse(URL))
    assert respuesta.status_code == 200
    assert respuesta.context["page_obj"] is not None
    assert respuesta.context["page_obj"].paginator.count == 0
    assert "Aún no hay clientes registrados." in respuesta.content.decode()


@pytest.mark.django_db
def test_no_lista_clientes_inactivos(cliente_autenticado, clientes_busqueda):
    Cliente.objects.filter(nombre="Juan Pérez").update(activo=False)
    assert nombres(buscar(cliente_autenticado, "Pérez")) == []


@pytest.mark.django_db
def test_encuentra_clientes_con_solo_nombre_o_solo_razon_social(
    cliente_autenticado, clientes_busqueda
):
    assert nombres(buscar(cliente_autenticado, "Lucía")) == ["Lucía Fernández"]
    assert nombres(buscar(cliente_autenticado, "Cooperativa")) == ["Cooperativa Río Claro"]


@pytest.mark.django_db
def test_paginacion_con_orden_consistente_y_q_conservada(cliente_autenticado):
    for i in range(45):
        Cliente.objects.create(
            nombre=f"Cliente Masivo {i:02d}",
            tipo_documento="DNI",
            numero_documento=f"{10000000 + i}",
            email=f"masivo{i}@ejemplo.com",
        )
    pagina1 = buscar(cliente_autenticado, "masivo")
    pagina2 = buscar(cliente_autenticado, "masivo", page=2)
    pagina3 = buscar(cliente_autenticado, "masivo", page=3)
    assert pagina1.context["page_obj"].paginator.count == 45
    todos = nombres(pagina1) + nombres(pagina2) + nombres(pagina3)
    assert len(todos) == 45
    assert todos == sorted(todos)
    assert len(set(todos)) == 45
    assert "?q=masivo&amp;page=2" in pagina1.content.decode() or "?q=masivo&page=2" in (
        pagina1.content.decode()
    )


@pytest.mark.django_db
def test_sin_sesion_redirige_al_login(clientes_busqueda):
    respuesta = Client().get(reverse(URL), {"q": "Juan"})
    assert respuesta.status_code == 302
    assert respuesta.url.startswith(reverse(settings.LOGIN_URL))


@pytest.mark.django_db
def test_ver_ficha_muestra_datos_vigentes(cliente_autenticado, clientes_busqueda):
    contenido = buscar(cliente_autenticado, "aguas").content.decode()
    cliente = Cliente.objects.get(razon_social="Aguas del Sur S.A.")
    url_ficha = reverse("clientes:detalle", args=[cliente.pk])
    assert url_ficha in contenido

    Cliente.objects.filter(pk=cliente.pk).update(telefono="011 4444-5555", domicilio="Calle 1")
    ficha = cliente_autenticado.get(url_ficha).content.decode()
    for dato in ("Aguas del Sur S.A.", "CUIT", "20123456786", "cliente1@ejemplo.com"):
        assert dato in ficha
    assert "011 4444-5555" in ficha
    assert "Calle 1" in ficha
