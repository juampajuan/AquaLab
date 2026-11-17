import json

import pytest
from django.urls import reverse

from estudios.models import Estudio, Resultado, Validacion
from informes import conclusion_hechos, conclusiones
from informes.models import BorradorConclusion, Informe

pytestmark = pytest.mark.django_db


def test_proponer_no_emite_ni_valida(conclusion_estudio, cliente_bioquimico):
    estudio = conclusion_estudio()
    antes = (
        list(Resultado.objects.values()),
        list(Validacion.objects.values()),
        list(Estudio.objects.values()),
    )
    respuesta = cliente_bioquimico.post(
        reverse("informes:conclusion_proponer", args=[estudio.pk]),
        data=json.dumps(
            {
                "revision_esperada": 0,
                "huella_hechos_vista": conclusion_hechos.huella(
                    conclusion_hechos.recolectar(estudio)
                ),
            }
        ),
        content_type="application/json",
    )
    assert respuesta.status_code == 200
    assert respuesta.json()["origen_propuesta"] == "plantilla"
    assert respuesta.json()["aprobada"] is False
    assert "no-store" in respuesta["Cache-Control"]
    borrador = BorradorConclusion.objects.get(estudio=estudio)
    assert borrador.texto_final == respuesta.json()["texto_final"]
    assert borrador.aprobada_por_id is None
    assert borrador.nombre_aprobador == borrador.huella_texto_aprobado == ""
    assert not Informe.objects.exists()
    assert antes == (
        list(Resultado.objects.values()),
        list(Validacion.objects.values()),
        list(Estudio.objects.values()),
    )


def test_proponer_post_csrf_y_autorizacion(
    conclusion_estudio, cliente_comun, cliente_bioquimico, bioquimico
):
    from django.test import Client

    estudio = conclusion_estudio()
    url = reverse("informes:conclusion_proponer", args=[estudio.pk])
    assert cliente_bioquimico.get(url).status_code == 405
    assert cliente_comun.post(url, data="{}", content_type="application/json").status_code == 403
    cliente_csrf = Client(enforce_csrf_checks=True)
    cliente_csrf.force_login(bioquimico)
    assert cliente_csrf.post(url, data="{}", content_type="application/json").status_code == 403


def guardar(estudio, usuario, estado, texto):
    return conclusiones.guardar_borrador(
        estudio.pk, usuario, estado["revision"], estado["huella_hechos"], texto
    )


def aprobar(estudio, usuario, estado):
    return conclusiones.aprobar_conclusion(
        estudio.pk,
        usuario,
        estado["revision"],
        estado["huella_hechos"],
        estado["huella_texto"],
        confirmacion=True,
    )


def test_propuesta_no_aprueba(conclusion_propuesta):
    estudio, estado = conclusion_propuesta
    borrador = BorradorConclusion.objects.get(estudio=estudio)
    assert estado["aprobada"] is False
    assert (borrador.aprobada_por_id, borrador.fecha_aprobacion, borrador.revision_aprobada) == (
        None,
        None,
        None,
    )
    assert (
        borrador.nombre_aprobador,
        borrador.huella_texto_aprobado,
        borrador.huella_hechos_aprobados,
    ) == ("", "", "")


def negar_ambas(usuario, estudio, estado, cliente):
    from django.core.exceptions import PermissionDenied

    with pytest.raises(PermissionDenied):
        conclusiones.proponer_conclusion(
            estudio.pk, usuario, estado["revision"], estado["huella_hechos"]
        )
    with pytest.raises(PermissionDenied):
        aprobar(estudio, usuario, estado)
    for nombre in ("conclusion_proponer", "conclusion_aprobar"):
        respuesta = cliente.post(
            reverse(f"informes:{nombre}", args=[estudio.pk]),
            data="{}",
            content_type="application/json",
        )
        assert respuesta.status_code == 403


def test_sin_grupo_ni_permiso_denegado(conclusion_propuesta, cliente_comun, django_user_model):
    estudio, estado = conclusion_propuesta
    usuario = django_user_model.objects.get(pk=cliente_comun.session["_auth_user_id"])
    negar_ambas(usuario, estudio, estado, cliente_comun)
    assert cliente_comun.get(reverse("informes:vista_previa", args=[estudio.pk])).status_code == 200


@pytest.mark.parametrize("inactivo", [False, True])
def test_sin_sesion_o_inactivo_denegado(conclusion_propuesta, bioquimico, inactivo):
    from django.contrib.auth.models import AnonymousUser
    from django.core.exceptions import PermissionDenied

    estudio, estado = conclusion_propuesta
    if inactivo:
        bioquimico.is_active = False
        bioquimico.save(update_fields=["is_active"])
    with pytest.raises(PermissionDenied):
        aprobar(estudio, bioquimico if inactivo else AnonymousUser(), estado)


def test_solo_grupo_denegado(conclusion_propuesta, bioquimico, cliente_bioquimico):
    estudio, estado = conclusion_propuesta
    bioquimico.groups.get(name="Bioquímicos").permissions.clear()
    negar_ambas(bioquimico, estudio, estado, cliente_bioquimico)


def test_solo_permiso_denegado(conclusion_propuesta, bioquimico, cliente_bioquimico):
    from django.contrib.auth.models import Permission

    from informes.servicios import emitir_informe

    estudio, estado = conclusion_propuesta
    bioquimico.groups.clear()
    bioquimico.user_permissions.add(
        Permission.objects.get(content_type__app_label="informes", codename="emitir_informes")
    )
    negar_ambas(bioquimico, estudio, estado, cliente_bioquimico)
    assert emitir_informe(estudio.pk, bioquimico).pk


def test_grupo_y_permiso_autorizados(conclusion_propuesta, bioquimico):
    estudio, estado = conclusion_propuesta
    aprobado = aprobar(estudio, bioquimico, estado)
    assert aprobado["aprobada"]
    assert aprobado["revision"] > estado["revision"]


def test_edicion_invalida_aprobacion(conclusion_propuesta, bioquimico):
    estudio, estado = conclusion_propuesta
    aprobado = aprobar(estudio, bioquimico, estado)
    editado = guardar(estudio, bioquimico, aprobado, "Revisión profesional sintética")
    assert not editado["aprobada"]
    assert editado["revision"] > aprobado["revision"]
    assert editado["texto_editorial"] == "Revisión profesional sintética"
    borrador = BorradorConclusion.objects.get(estudio=estudio)
    assert borrador.nombre_aprobador == borrador.huella_texto_aprobado == ""


def test_regeneracion_identica_invalida(conclusion_propuesta, bioquimico):
    estudio, estado = conclusion_propuesta
    aprobado = aprobar(estudio, bioquimico, estado)
    nuevo = conclusiones.proponer_conclusion(
        estudio.pk, bioquimico, aprobado["revision"], aprobado["huella_hechos"]
    )
    assert nuevo["texto_final"] == aprobado["texto_final"]
    assert not nuevo["aprobada"]


def test_borrador_persiste_al_volver_y_recargar(
    conclusion_propuesta, bioquimico, cliente_bioquimico
):
    estudio, estado = conclusion_propuesta
    guardado = guardar(estudio, bioquimico, estado, "Texto compartido conservado")
    for _ in range(2):
        respuesta = cliente_bioquimico.get(reverse("informes:vista_previa", args=[estudio.pk]))
        assert (
            respuesta.context["conclusion_estado"]["texto_editorial"] == guardado["texto_editorial"]
        )
        assert respuesta.context["conclusion_estado"]["aprobada"] is False


def test_recarga_preserva_aprobacion_vigente(conclusion_propuesta, bioquimico, cliente_bioquimico):
    estudio, estado = conclusion_propuesta
    aprobado = aprobar(estudio, bioquimico, estado)
    for _ in range(2):
        respuesta = cliente_bioquimico.get(reverse("informes:vista_previa", args=[estudio.pk]))
        assert respuesta.context["conclusion_estado"] == aprobado


def test_get_invalida_solo_borrador_existente(conclusion_propuesta, bioquimico, cliente_bioquimico):
    from pruebas.models import Prueba

    estudio, estado = conclusion_propuesta
    aprobar(estudio, bioquimico, estado)
    Prueba.objects.filter(codigo="PH").update(nombre="Identidad actualizada sintética")
    resultados, validaciones = list(Resultado.objects.values()), list(Validacion.objects.values())
    cliente_bioquimico.get(reverse("informes:vista_previa", args=[estudio.pk]))
    borrador = BorradorConclusion.objects.get(estudio=estudio)
    assert borrador.aprobada_por_id is None
    assert borrador.requiere_revision
    assert list(Resultado.objects.values()) == resultados
    assert list(Validacion.objects.values()) == validaciones
    assert not Informe.objects.exists()


def test_get_repetido_no_escribe(conclusion_propuesta, cliente_bioquimico):
    estudio, _ = conclusion_propuesta
    antes = list(BorradorConclusion.objects.values())
    for _ in range(2):
        cliente_bioquimico.get(reverse("informes:vista_previa", args=[estudio.pk]))
    assert list(BorradorConclusion.objects.values()) == antes


def test_get_sin_borrador_y_empleado_comun_no_escribe(
    conclusion_estudio, bioquimico, cliente_bioquimico, cliente_comun
):
    from pruebas.models import Prueba

    estudio = conclusion_estudio()
    url = reverse("informes:vista_previa", args=[estudio.pk])
    assert cliente_bioquimico.get(url).status_code == 200
    assert not BorradorConclusion.objects.filter(estudio=estudio).exists()
    estado = conclusiones.proponer_conclusion(
        estudio.pk, bioquimico, 0, conclusion_hechos.huella(conclusion_hechos.recolectar(estudio))
    )
    aprobar(estudio, bioquimico, estado)
    Prueba.objects.filter(codigo="PH").update(nombre="Fuente cambiada, pendiente de reconciliar")
    antes = list(BorradorConclusion.objects.values())
    respuesta = cliente_comun.get(url)
    assert respuesta.status_code == 200
    assert "data-conclusion" not in respuesta.content.decode()
    assert list(BorradorConclusion.objects.values()) == antes


def test_borrador_compartido_entre_bioquimicos(conclusion_propuesta, bioquimico, django_user_model):
    from django.test import Client

    estudio, estado = conclusion_propuesta
    guardar(estudio, bioquimico, estado, "Texto de la primera persona")
    otra = django_user_model.objects.create_user(email="otra-bio@ejemplo.com", is_active=True)
    otra.groups.add(bioquimico.groups.get(name="Bioquímicos"))
    cliente = Client()
    cliente.force_login(otra)
    respuesta = cliente.get(reverse("informes:vista_previa", args=[estudio.pk]))
    assert (
        respuesta.context["conclusion_estado"]["texto_editorial"] == "Texto de la primera persona"
    )


def test_fuentes_cambiadas_invalidacion_persiste_en_conflicto(conclusion_propuesta, bioquimico):
    from pruebas.models import Prueba

    estudio, estado = conclusion_propuesta
    aprobado = aprobar(estudio, bioquimico, estado)
    prueba = Prueba.objects.get(codigo="PH")
    nombre_anterior = prueba.nombre
    Prueba.objects.filter(pk=prueba.pk).update(nombre="Identidad de prueba actualizada")
    with pytest.raises(conclusiones.ConflictoConclusion):
        guardar(estudio, bioquimico, aprobado, "Texto que no debe pisar la versión actual")
    borrador = BorradorConclusion.objects.get(estudio=estudio)
    assert borrador.aprobada_por_id is None
    assert borrador.requiere_revision
    assert borrador.texto_editorial == estado["texto_editorial"]
    Prueba.objects.filter(pk=prueba.pk).update(nombre=nombre_anterior)
    actual = conclusiones.estado_borrador(borrador)
    with pytest.raises(conclusiones.ConflictoConclusion):
        aprobar(estudio, bioquimico, actual)
    assert BorradorConclusion.objects.get(pk=borrador.pk).aprobada_por_id is None


def test_aprobacion_exige_texto_y_hechos_vistos(conclusion_propuesta, bioquimico):
    estudio, estado = conclusion_propuesta
    with pytest.raises(conclusiones.ConflictoConclusion):
        conclusiones.aprobar_conclusion(
            estudio.pk,
            bioquimico,
            estado["revision"],
            estado["huella_hechos"],
            "b" * 64,
            confirmacion=True,
        )
    assert BorradorConclusion.objects.get(estudio=estudio).aprobada_por_id is None


def test_aprobacion_sin_firma_y_texto_exacto(conclusion_propuesta, bioquimico):
    from informes.models import FirmaProfesional

    estudio, estado = conclusion_propuesta
    FirmaProfesional.objects.filter(usuario=bioquimico).delete()
    texto = "  Revisión profesional\r\ncon tildes y <datos>  "
    guardado = guardar(estudio, bioquimico, estado, texto)
    assert guardado["texto_editorial"] == texto.replace("\r\n", "\n")
    aprobado = aprobar(estudio, bioquimico, guardado)
    assert aprobado["texto_final"] == guardado["texto_final"]
    assert aprobado["aprobada"]
