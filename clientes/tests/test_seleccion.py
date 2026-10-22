import pytest
from django.urls import reverse

from clientes.models import Cliente


@pytest.mark.django_db
def test_cada_resultado_enlaza_a_su_propia_ficha(cliente_autenticado, clientes_busqueda):
    respuesta = cliente_autenticado.get(reverse("clientes:buscar"), {"q": "Gómez"})
    contenido = respuesta.content.decode()
    for cliente in Cliente.objects.filter(nombre="María Gómez"):
        url = reverse("clientes:detalle", args=[cliente.pk])
        assert url in contenido
        ficha = cliente_autenticado.get(url)
        assert ficha.context["cliente"] == cliente
        assert cliente.numero_documento in ficha.content.decode()


@pytest.mark.django_db
def test_homonimos_se_distinguen_por_documento(cliente_autenticado, clientes_busqueda):
    respuesta = cliente_autenticado.get(reverse("clientes:buscar"), {"q": "María Gómez"})
    contenido = respuesta.content.decode()
    assert len(respuesta.context["page_obj"]) == 2
    assert "DNI 20111222" in contenido
    assert "DNI 27333444" in contenido


@pytest.mark.django_db
def test_ficha_de_cliente_inactivo_no_esta_disponible(cliente_autenticado, clientes_busqueda):
    cliente = Cliente.objects.get(nombre="Juan Pérez")
    Cliente.objects.filter(pk=cliente.pk).update(activo=False)
    respuesta = cliente_autenticado.get(reverse("clientes:detalle", args=[cliente.pk]), follow=True)
    assert respuesta.redirect_chain[-1][0] == reverse("clientes:buscar")
    assert "El cliente no está disponible." in respuesta.content.decode()


@pytest.mark.django_db
def test_ficha_de_cliente_inexistente_da_404(cliente_autenticado):
    assert cliente_autenticado.get(reverse("clientes:detalle", args=[999999])).status_code == 404


@pytest.mark.django_db
def test_enlaces_de_navegacion_a_la_busqueda(cliente_autenticado, clientes_busqueda):
    url = reverse("clientes:buscar")
    cliente = Cliente.objects.first()
    assert url in cliente_autenticado.get(reverse("inicio")).content.decode()
    assert (
        url
        in cliente_autenticado.get(reverse("clientes:detalle", args=[cliente.pk])).content.decode()
    )
