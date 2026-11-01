import pytest
from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError

from informes.models import Informe

pytestmark = pytest.mark.django_db


def crear(estudio, usuario, numero=1):
    return Informe.objects.create(
        numero=numero, estudio=estudio, emitido_por=usuario, contenido={"pruebas": []}
    )


@pytest.mark.parametrize(("numero", "texto"), [(1, "INF-000001"), (123, "INF-000123")])
def test_numero_mostrado(numero, texto):
    assert Informe(numero=numero).numero_mostrado == texto


def test_un_informe_por_estudio(estudio_de, empleado):
    estudio = estudio_de("PH")
    crear(estudio, empleado)
    with pytest.raises(IntegrityError), transaction.atomic():
        crear(estudio, empleado, numero=2)


def test_numero_unico(estudio_de, empleado):
    crear(estudio_de("PH"), empleado)
    with pytest.raises(IntegrityError), transaction.atomic():
        crear(estudio_de("CL-"), empleado)


def test_numero_positivo(estudio_de, empleado):
    with pytest.raises(IntegrityError), transaction.atomic():
        crear(estudio_de("PH"), empleado, numero=0)


def test_estudio_con_informe_protegido(estudio_de, empleado):
    estudio = estudio_de("PH")
    crear(estudio, empleado)
    with pytest.raises(ProtectedError), transaction.atomic():
        estudio.delete()
