import pytest
from django.contrib.auth.models import AnonymousUser, Group, Permission
from django.core.exceptions import PermissionDenied

from informes.conclusiones import autorizar_conclusion, puede_concluir

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "grupo,permiso", [(False, False), (True, False), (False, True), (True, True)]
)
def test_politica_conjunta(django_user_model, grupo, permiso):
    usuario = django_user_model.objects.create_user(email="politica@ejemplo.com", is_active=True)
    grupo_bio, _ = Group.objects.get_or_create(name="Bioquímicos")
    grupo_bio.permissions.clear()
    if grupo:
        usuario.groups.add(grupo_bio)
    if permiso:
        usuario.user_permissions.add(
            Permission.objects.get(content_type__app_label="informes", codename="emitir_informes")
        )
    assert puede_concluir(usuario) == (grupo and permiso)
    if grupo and permiso:
        assert autorizar_conclusion(usuario).pk == usuario.pk
    else:
        with pytest.raises(PermissionDenied):
            autorizar_conclusion(usuario)


def test_anonimo_denegado():
    assert not puede_concluir(AnonymousUser())
    with pytest.raises(PermissionDenied):
        autorizar_conclusion(AnonymousUser())


@pytest.mark.parametrize("atributo", ["is_staff", "is_superuser"])
def test_privilegios_sin_grupo_no_habilitan(django_user_model, atributo):
    usuario = django_user_model.objects.create_user(
        email="privilegio@ejemplo.com", is_active=True, **{atributo: True}
    )
    administradores, _ = Group.objects.get_or_create(name="Administradores")
    usuario.groups.add(administradores)
    assert not puede_concluir(usuario)


def test_revocacion_no_usa_cache(bioquimico, django_user_model):
    assert bioquimico.has_perm("informes.emitir_informes")
    assert puede_concluir(bioquimico)
    bioquimico.groups.clear()
    assert not puede_concluir(bioquimico)
    django_user_model.objects.filter(pk=bioquimico.pk).update(is_active=False)
    assert not puede_concluir(bioquimico)


def test_aprobar_no_exige_firma(bioquimico_sin_firma):
    assert autorizar_conclusion(bioquimico_sin_firma).pk == bioquimico_sin_firma.pk


@pytest.mark.parametrize("operacion", ["guardar", "proponer", "aprobar", "emitir"])
@pytest.mark.parametrize("grupo,permiso", [(False, False), (True, False), (False, True)])
def test_cada_operacion_exige_ambas_condiciones(
    conclusion_propuesta, django_user_model, grupo, permiso, operacion
):
    from django.test import Client
    from django.urls import reverse

    from informes import conclusiones
    from informes.models import BorradorConclusion, Informe
    from informes.servicios import emitir_informe

    estudio, estado = conclusion_propuesta
    usuario = django_user_model.objects.create_user(email="operacion@ejemplo.com", is_active=True)
    bio = Group.objects.get(name="Bioquímicos")
    bio.permissions.clear()
    if grupo:
        usuario.groups.add(bio)
    if permiso:
        usuario.user_permissions.add(
            Permission.objects.get(content_type__app_label="informes", codename="emitir_informes")
        )
    antes = list(BorradorConclusion.objects.values())
    with pytest.raises(PermissionDenied):
        if operacion == "guardar":
            conclusiones.guardar_borrador(
                estudio.pk, usuario, estado["revision"], estado["huella_hechos"], "No autorizado"
            )
        elif operacion == "proponer":
            conclusiones.proponer_conclusion(
                estudio.pk, usuario, estado["revision"], estado["huella_hechos"]
            )
        elif operacion == "aprobar":
            conclusiones.aprobar_conclusion(
                estudio.pk,
                usuario,
                estado["revision"],
                estado["huella_hechos"],
                estado["huella_texto"],
                confirmacion=True,
            )
        else:
            emitir_informe(
                estudio.pk, usuario, incluir_conclusion=True, revision_conclusion=estado["revision"]
            )
    cliente = Client()
    cliente.force_login(usuario)
    nombre = "generar" if operacion == "emitir" else f"conclusion_{operacion}"
    respuesta = cliente.post(
        reverse(f"informes:{nombre}", args=[estudio.pk]),
        data='{"incluir_conclusion":true}',
        content_type="application/json",
    )
    assert respuesta.status_code == 403
    assert list(BorradorConclusion.objects.values()) == antes
    assert not Informe.objects.exists()


@pytest.mark.parametrize("cambio", ["grupo", "permiso", "activo"])
def test_reautoriza_despues_de_ia(conclusion_propuesta, bioquimico, monkeypatch, cambio):
    from informes import conclusion_ia, conclusiones
    from informes.models import BorradorConclusion

    estudio, estado = conclusion_propuesta

    def redactar(hechos):
        if cambio == "grupo":
            bioquimico.groups.clear()
        elif cambio == "permiso":
            bioquimico.groups.get(name="Bioquímicos").permissions.clear()
        else:
            type(bioquimico).objects.filter(pk=bioquimico.pk).update(is_active=False)
        return conclusion_ia.Propuesta("Respuesta que no debe instalarse", "ia")

    monkeypatch.setattr(conclusion_ia, "proponer", redactar)
    with pytest.raises(PermissionDenied):
        conclusiones.proponer_conclusion(
            estudio.pk, bioquimico, estado["revision"], estado["huella_hechos"]
        )
    borrador = BorradorConclusion.objects.get(estudio=estudio)
    assert borrador.texto_editorial == estado["texto_editorial"]
    assert borrador.aprobada_por_id is None


@pytest.mark.parametrize(
    "nombre", ["conclusion_proponer", "conclusion_guardar", "conclusion_aprobar"]
)
def test_post_csrf_real_y_get_no_permitido(conclusion_propuesta, bioquimico, nombre):
    from django.test import Client
    from django.urls import reverse

    estudio, _ = conclusion_propuesta
    cliente = Client(enforce_csrf_checks=True)
    cliente.force_login(bioquimico)
    url = reverse(f"informes:{nombre}", args=[estudio.pk])
    assert cliente.get(url).status_code == 405
    assert cliente.post(url, data="{}", content_type="application/json").status_code == 403
