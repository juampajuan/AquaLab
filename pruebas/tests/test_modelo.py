import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from pruebas.models import Prueba

pytestmark = pytest.mark.django_db


def test_prueba_minima():
    p = Prueba(codigo=" TEST-A ", nombre=" Prueba A ")
    p.full_clean()
    p.save()
    assert (p.codigo, p.nombre) == ("TEST-A", "Prueba A")
    with pytest.raises(IntegrityError), transaction.atomic():
        Prueba.objects.create(codigo="TEST-A", nombre="Otra")


@pytest.mark.parametrize(
    "campo,valor", [("codigo", " "), ("nombre", " "), ("codigo", "x" * 51), ("nombre", "x" * 151)]
)
def test_validacion(campo, valor):
    p = Prueba(codigo="TEST-A", nombre="Prueba A")
    setattr(p, campo, valor)
    with pytest.raises(ValidationError):
        p.full_clean()
