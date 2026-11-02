from decimal import Decimal

import pytest
from django.utils import timezone

from estudios.models import EstadoEstudio, EstadoPruebaEstudio, Estudio, Validacion
from estudios.servicios import ValidarResultadosError, corregir_mediciones, validar_resultados
from estudios.tests.utiles import asignacion_de, cargar, validar
from pruebas.limites import Evaluacion
from pruebas.models import LimiteVertido, Prueba

pytestmark = pytest.mark.django_db


def validar_a_mano(asignacion, usuario):
    """Validación sin pasar por el servicio de US 6.4 (para probar su pérdida)."""
    Validacion.objects.create(
        asignacion=asignacion, validada_por=usuario, origen_limites="general", evaluacion="cumple"
    )
    asignacion.estado = EstadoPruebaEstudio.COMPLETADA
    asignacion.save(update_fields=["estado"])


def cambiar_medicion(estudio, usuario, codigo, nuevo):
    asignacion = asignacion_de(estudio, codigo)
    original = Decimal(asignacion.medicion.valor_ingresado)
    nuevo = None if nuevo is None else Decimal(nuevo)
    return corregir_mediciones(estudio.pk, {asignacion.pk: (original, nuevo)}, usuario)


def comprobar_anulacion(estudio_de, empleado, nuevo, estado):
    """Corregir (US 6.3) o borrar (US 6.5) una medición validada anula la validación: se
    conserva con su fecha de anulación y no queda ninguna vigente (FR-017)."""
    estudio = estudio_de("CL-")
    cargar(estudio, empleado, CL_="2.35")
    validar_a_mano(asignacion_de(estudio, "CL-"), empleado)
    cambiar_medicion(estudio, empleado, "CL-", nuevo)
    asignacion = asignacion_de(estudio, "CL-")
    assert asignacion.estado == estado
    validacion = asignacion.validaciones.get()
    assert validacion.anulada is True
    assert validacion.fecha_anulacion is not None
    assert not asignacion.validaciones.filter(anulada=False).exists()


def test_correccion_anula_validacion(estudio_de, empleado):
    comprobar_anulacion(estudio_de, empleado, "2.53", EstadoPruebaEstudio.CARGADA)


def test_borrado_anula_validacion(estudio_de, empleado):
    comprobar_anulacion(estudio_de, empleado, None, EstadoPruebaEstudio.PENDIENTE)


def codigos(pruebas):
    return [p.codigo for p in pruebas]


def estado_de(estudio, codigo):
    return asignacion_de(estudio, codigo).estado


@pytest.fixture
def estudio_ph_cloruro(estudio_de, empleado):
    estudio = estudio_de("PH", "CL-")
    cargar(estudio, empleado, PH="7.4", CL_="12")  # Cloruro x*10 → 120
    return estudio


def test_confirmar_valida(estudio_ph_cloruro, bioquimico):
    antes = timezone.now()
    resultado = validar(estudio_ph_cloruro, bioquimico, "PH")
    assert codigos(resultado.validadas) == ["PH"]
    assert resultado.omitidas == []
    assert estado_de(estudio_ph_cloruro, "PH") == EstadoPruebaEstudio.COMPLETADA
    validacion = asignacion_de(estudio_ph_cloruro, "PH").validaciones.get(anulada=False)
    assert validacion.validada_por == bioquimico
    assert validacion.fecha_validacion >= antes


def test_validar_guarda_evaluacion_y_limites(estudio_de, empleado, bioquimico, muestra):
    muestra.tipo_vertido = "cloacal"
    muestra.save(update_fields=["tipo_vertido"])
    estudio = estudio_de("PH")
    cargar(estudio, empleado, PH="7.4")
    validar(estudio, bioquimico, "PH")
    validacion = asignacion_de(estudio, "PH").validaciones.get()
    assert (validacion.limite_min, validacion.limite_max) == ("7.01", "10.0")
    assert validacion.norma == "(AGOSBA) 389/98"
    assert validacion.origen_limites == "cloacal"
    assert validacion.evaluacion == Evaluacion.CUMPLE


def test_fuera_de_norma_se_valida(estudio_de, empleado, bioquimico):
    estudio = estudio_de("CL-")
    cargar(estudio, empleado, CL_="40")  # x*10 → 400
    resultado = validar(estudio, bioquimico, "CL-")
    assert codigos(resultado.validadas) == ["CL-"]
    validacion = asignacion_de(estudio, "CL-").validaciones.get()
    assert validacion.evaluacion == Evaluacion.FUERA_DE_NORMA
    assert (validacion.limite_max, validacion.origen_limites) == ("350.0", "general")


def test_ultima_validacion_finaliza(estudio_ph_cloruro, bioquimico):
    assert validar(estudio_ph_cloruro, bioquimico, "PH").finalizado is False
    resultado = validar(estudio_ph_cloruro, bioquimico, "CL-")
    assert resultado.finalizado is True
    estudio_ph_cloruro.refresh_from_db()
    assert estudio_ph_cloruro.estado == EstadoEstudio.FINALIZADO


def test_con_pendientes_sigue_en_proceso(estudio_de, empleado, bioquimico):
    estudio = estudio_de("PH", "CL-")
    cargar(estudio, empleado, PH="7.4")
    resultado = validar(estudio, bioquimico, "PH")
    assert resultado.finalizado is False
    estudio.refresh_from_db()
    assert estudio.estado == EstadoEstudio.EN_PROCESO


def test_informe_emitido_rechaza(estudio_ph_cloruro, bioquimico):
    Estudio.objects.filter(pk=estudio_ph_cloruro.pk).update(estado=EstadoEstudio.INFORME_GENERADO)
    with pytest.raises(ValidarResultadosError, match="informe emitido"):
        validar(estudio_ph_cloruro, bioquimico, "PH")
    assert not Validacion.objects.exists()
    assert estado_de(estudio_ph_cloruro, "PH") == EstadoPruebaEstudio.CARGADA


def test_estudio_inexistente_rechaza(bioquimico):
    with pytest.raises(ValidarResultadosError, match="El estudio no está disponible."):
        validar_resultados(999999, {}, bioquimico)


def test_omite_ya_validada(estudio_ph_cloruro, bioquimico):
    validar(estudio_ph_cloruro, bioquimico, "PH")
    resultado = validar(estudio_ph_cloruro, bioquimico, "PH")
    assert resultado.validadas == []
    assert [(p.codigo, m) for p, m in resultado.omitidas] == [("PH", "ya estaba validada")]
    assert Validacion.objects.count() == 1


def test_omite_sin_resultado(estudio_de, empleado, bioquimico):
    estudio = estudio_de("PH", "CL-")
    cargar(estudio, empleado, PH="7.4")
    pendiente = asignacion_de(estudio, "CL-")
    resultado = validar_resultados(estudio.pk, {pendiente.pk: "120"}, bioquimico)
    assert [(p.codigo, m) for p, m in resultado.omitidas] == [("CL-", "ya no tenía resultado")]
    assert not Validacion.objects.exists()


def test_omite_si_cambio(estudio_ph_cloruro, bioquimico):
    ph = asignacion_de(estudio_ph_cloruro, "PH")
    resultado = validar_resultados(estudio_ph_cloruro.pk, {ph.pk: "9.9"}, bioquimico)
    assert [(p.codigo, m) for p, m in resultado.omitidas] == [("PH", "cambió mientras se revisaba")]
    assert not Validacion.objects.exists()


def test_reenvio_no_cambia(estudio_ph_cloruro, bioquimico, django_user_model):
    validar(estudio_ph_cloruro, bioquimico, "PH")
    original = Validacion.objects.get()
    otro = django_user_model.objects.create_user(
        email="otro-bioquimico@ejemplo.com", password="Clave-Valida-123", is_active=True
    )
    otro.groups.set(bioquimico.groups.all())
    validar(estudio_ph_cloruro, otro, "PH")
    vigente = Validacion.objects.get()
    assert (vigente.pk, vigente.validada_por, vigente.fecha_validacion) == (
        original.pk,
        bioquimico,
        original.fecha_validacion,
    )


def test_ignora_asignaciones_ajenas(estudio_ph_cloruro, estudio_de, empleado, bioquimico):
    otro = estudio_de("PH")
    cargar(otro, empleado, PH="7.0")
    ajena = asignacion_de(otro, "PH")
    resultado = validar_resultados(estudio_ph_cloruro.pk, {ajena.pk: "7.0"}, bioquimico)
    assert (resultado.validadas, resultado.omitidas) == ([], [])
    assert not Validacion.objects.exists()


def test_validacion_no_modifica_otros_datos(estudio_ph_cloruro, estudio_de, empleado, bioquimico):
    otro = estudio_de("PH")
    cargar(otro, empleado, PH="7.0")
    ph = asignacion_de(estudio_ph_cloruro, "PH")
    antes = (
        ph.resultado.valor,
        ph.medicion.valor,
        estudio_ph_cloruro.muestra.tipo_vertido,
        Prueba.objects.get(codigo="PH").limite_max,
        list(LimiteVertido.objects.values_list("limite_min", "limite_max")),
        Estudio.objects.get(pk=otro.pk).estado,
        asignacion_de(otro, "PH").estado,
    )
    validar(estudio_ph_cloruro, bioquimico, "PH", "CL-")
    ph = asignacion_de(estudio_ph_cloruro, "PH")
    estudio_ph_cloruro.muestra.refresh_from_db()
    despues = (
        ph.resultado.valor,
        ph.medicion.valor,
        estudio_ph_cloruro.muestra.tipo_vertido,
        Prueba.objects.get(codigo="PH").limite_max,
        list(LimiteVertido.objects.values_list("limite_min", "limite_max")),
        Estudio.objects.get(pk=otro.pk).estado,
        asignacion_de(otro, "PH").estado,
    )
    assert antes == despues


def test_revalidar_conserva_anulada(estudio_ph_cloruro, bioquimico):
    validar(estudio_ph_cloruro, bioquimico, "PH")
    cambiar_medicion(estudio_ph_cloruro, bioquimico, "PH", "7.6")
    validar(estudio_ph_cloruro, bioquimico, "PH")
    validaciones = asignacion_de(estudio_ph_cloruro, "PH").validaciones
    assert validaciones.count() == 2
    assert validaciones.filter(anulada=True).count() == 1
    assert validaciones.filter(anulada=False).count() == 1


def test_validar_ausente_bajo_ld_cumple(estudio_de, empleado, bioquimico):
    """FR-016 de la US 7.2: Sólidos sedimentables 0,05 con límite de detección 0,1 cumple."""
    estudio = estudio_de("SS10")
    cargar(estudio, empleado, SS10="0.05")
    validar(estudio, bioquimico, "SS10")
    assert asignacion_de(estudio, "SS10").validaciones.get().evaluacion == Evaluacion.CUMPLE
