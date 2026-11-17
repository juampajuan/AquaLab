import pytest
from django.db import connection
from django.template import Context, Template
from django.test.utils import CaptureQueriesContext

from informes import conclusion_hechos, conclusion_ia
from informes.conclusiones import proponer_conclusion
from pruebas.models import Prueba

pytestmark = pytest.mark.django_db


def test_consultas_acotadas_y_template_sin_orm(conclusion_estudio):
    conteos = []
    for cantidad in (1, 30):
        valores = {}
        for indice in range(cantidad):
            codigo = f"US102-{cantidad}-{indice}"
            Prueba.objects.create(
                codigo=codigo,
                nombre=f"Prueba sintética {indice}",
                unidad="mg/l",
                unidad_medicion="mg/l",
                limite_max="1",
            )
            valores[codigo] = "2"
        estudio = conclusion_estudio(valores)
        with CaptureQueriesContext(connection) as consultas:
            hechos = conclusion_hechos.recolectar(estudio)
        conteos.append(len(consultas))
        template = Template("{% for prueba in hechos.pruebas %}{{ prueba.norma }}{% endfor %}")
        with CaptureQueriesContext(connection) as consultas_template:
            template.render(Context({"hechos": hechos}))
        assert len(consultas_template) == 0
    assert conteos[0] == conteos[1]
    assert conteos[1] <= 4


@pytest.mark.django_db(transaction=True)
def test_redaccion_fuera_de_transaccion(conclusion_estudio, bioquimico, monkeypatch):
    estudio = conclusion_estudio()
    hechos = conclusion_hechos.recolectar(estudio)
    llamadas = []

    def redactar(datos):
        assert not connection.in_atomic_block
        assert datos == hechos
        llamadas.append(datos)
        return conclusion_ia.Propuesta(
            conclusion_ia.plantilla(datos), "plantilla", "sin_configuracion"
        )

    monkeypatch.setattr(conclusion_ia, "proponer", redactar)
    proponer_conclusion(estudio.pk, bioquimico, 0, conclusion_hechos.huella(hechos))
    assert llamadas == [hechos]
