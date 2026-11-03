from unittest import mock

import pytest

from estudios.models import EstadoEstudio, EstadoPruebaEstudio, Estudio, Medicion, Validacion
from estudios.tests.utiles import cargar, validar
from informes.contenido import armar_contenido
from informes.models import Informe
from informes.servicios import EmitirInformeError, InformeNoDisponible, emitir_informe
from pruebas.models import LimiteVertido, Prueba

from .utiles import png

pytestmark = pytest.mark.django_db


@pytest.fixture
def listo(estudio_de, empleado, bioquimico):
    """Crea estudios listos para informar (pH y Cloruro validados)."""

    def crear():
        estudio = estudio_de("PH", "CL-")
        cargar(estudio, empleado, PH="7.4", CL_="40")  # Cloruro x*10 → 400
        validar(estudio, bioquimico, "PH", "CL-")
        return estudio

    return crear


def test_emitir_crea_informe_y_cambia_estado(listo, bioquimico):
    estudio = listo()
    esperado = armar_contenido(estudio, bioquimico)
    informe = emitir_informe(estudio.pk, bioquimico)
    assert (informe.numero, informe.numero_mostrado) == (1, "INF-000001")
    assert informe.emitido_por == bioquimico
    assert informe.fecha_emision is not None
    assert informe.contenido == esperado
    assert Estudio.objects.get(pk=estudio.pk).estado == EstadoEstudio.INFORME_GENERADO


def test_numeracion_correlativa(listo, bioquimico):
    assert emitir_informe(listo().pk, bioquimico).numero == 1
    assert emitir_informe(listo().pk, bioquimico).numero == 2


def test_falla_no_deja_huecos(listo, bioquimico):
    primero, segundo = listo(), listo()
    with (
        mock.patch("informes.servicios.armar_contenido", side_effect=RuntimeError),
        pytest.raises(RuntimeError),
    ):
        emitir_informe(primero.pk, bioquimico)
    assert not Informe.objects.exists()
    assert Estudio.objects.get(pk=primero.pk).estado == EstadoEstudio.FINALIZADO
    assert emitir_informe(segundo.pk, bioquimico).numero == 1


def test_emitir_revalida(listo, bioquimico):
    estudio = listo()
    # Como una corrección (US 6.3) mientras se revisaba la vista previa.
    estudio.pruebas_asignadas.filter(prueba__codigo="PH").update(estado=EstadoPruebaEstudio.CARGADA)
    with pytest.raises(InformeNoDisponible, match="Hay 1 prueba sin completar."):
        emitir_informe(estudio.pk, bioquimico)
    assert not Informe.objects.exists()


def test_segundo_intento_rechaza(listo, bioquimico):
    estudio = listo()
    emitir_informe(estudio.pk, bioquimico)
    with pytest.raises(InformeNoDisponible, match="El informe de este estudio ya fue generado."):
        emitir_informe(estudio.pk, bioquimico)
    assert Informe.objects.count() == 1


def test_estudio_inexistente(bioquimico):
    with pytest.raises(InformeNoDisponible, match="El estudio no está disponible."):
        emitir_informe(999999, bioquimico)


def test_sin_permiso_rechaza(listo, empleado, django_user_model):
    estudio = listo()
    comun = django_user_model.objects.create_user(
        email="comun-emision@ejemplo.com", password="Clave-Valida-123", is_active=True
    )
    with pytest.raises(EmitirInformeError, match="Se requiere permiso para emitir informes."):
        emitir_informe(estudio.pk, comun)
    assert not Informe.objects.exists()


def test_emision_no_modifica_otros_datos(listo, bioquimico):
    estudio, otro = listo(), listo()

    def foto():
        cliente = Estudio.objects.get(pk=estudio.pk).muestra.cliente
        return (
            sorted(estudio.pruebas_asignadas.values_list("pk", "estado")),
            sorted(Medicion.objects.values_list("pk", "valor")),
            sorted(Validacion.objects.values_list("pk", "anulada", "evaluacion")),
            (cliente.domicilio, cliente.email),
            list(Prueba.objects.order_by("pk").values_list("limite_min", "limite_max")),
            list(LimiteVertido.objects.order_by("pk").values_list("limite_max")),
            Estudio.objects.get(pk=otro.pk).estado,
        )

    antes = foto()
    emitir_informe(estudio.pk, bioquimico)
    assert foto() == antes


SIN_FIRMA = "Cargá tu firma y matrícula en «Mi firma» antes de emitir."


def test_emitir_sin_firma_rechaza(estudio_de, completar, bioquimico_sin_firma):
    estudio = estudio_de("PH")
    completar(estudio)
    estado = estudio.estado
    with pytest.raises(EmitirInformeError) as exc:
        emitir_informe(estudio.pk, bioquimico_sin_firma)
    assert str(exc.value) == SIN_FIRMA
    assert not Informe.objects.exists()
    estudio.refresh_from_db()
    assert estudio.estado == estado != EstadoEstudio.INFORME_GENERADO


def test_emitir_copia_firma(listo, bioquimico):
    informe = emitir_informe(listo().pk, bioquimico)
    firma = bioquimico.firma_profesional
    assert informe.contenido["firma"] == {
        "nombre": bioquimico.get_full_name() or bioquimico.email,
        "matricula": "MP 1234",
        "imagen": firma.data_url,
    }


def test_cambiar_firma_no_cambia_emitidos(listo, bioquimico):
    informe = emitir_informe(listo().pk, bioquimico)
    antes = informe.contenido["firma"]
    firma = bioquimico.firma_profesional
    firma.imagen = png(300, 100)
    firma.matricula = "MP 9999"
    firma.save()
    informe.refresh_from_db()
    assert informe.contenido["firma"] == antes
