import pytest
from django.test import Client
from django.urls import reverse

from estudios.gestion_tipos import gestionar_tipo_estudio
from estudios.models import TipoEstudio
from estudios.servicios import crear_estudio

pytestmark = pytest.mark.django_db


@pytest.fixture
def navegador(gestor):
    client = Client()
    client.force_login(gestor)
    return client


def preparar_alta(client, catalogo, nombre="DEMO UI", **extra):
    url = reverse("estudios:tipos_crear")
    apertura = client.get(url)
    return client.post(
        url,
        {
            "contexto": apertura.context["contexto"],
            "nombre": nombre,
            "descripcion": "",
            "pruebas": [p.pk for p in catalogo],
            **extra,
        },
    )


def test_alta_resumen_volver_cancelar_y_exito(navegador, pruebas):
    response = preparar_alta(navegador, pruebas)
    assert response.status_code == 302
    resumen = navegador.get(response.url)
    borrador = resumen.context["borrador"]
    assert not TipoEstudio.objects.exists()
    volver = navegador.get(reverse("estudios:tipos_crear"), {"solicitud": borrador["clave"]})
    assert volver.context["form"].initial["nombre"] == "DEMO UI"
    cancelar = navegador.post(
        reverse("estudios:tipos_confirmar"), {"token": borrador["token"], "accion": "cancelar"}
    )
    assert cancelar.status_code == 302
    assert not TipoEstudio.objects.exists()
    response = preparar_alta(navegador, pruebas)
    borrador = navegador.get(response.url).context["borrador"]
    confirmar = navegador.post(
        reverse("estudios:tipos_confirmar"),
        {"token": borrador["token"], "accion": "confirmar", "nombre": "IGNORAR", "pruebas": []},
    )
    assert confirmar.status_code == 302
    assert TipoEstudio.objects.get().nombre == "DEMO UI"
    navegador.post(
        reverse("estudios:tipos_confirmar"), {"token": borrador["token"], "accion": "confirmar"}
    )
    assert TipoEstudio.objects.count() == 1


@pytest.mark.parametrize("ruta", ["tipos_listar", "tipos_crear", "tipos_confirmar"])
@pytest.mark.parametrize("metodo", ["get", "post"])
def test_acceso_sin_permiso(empleado, staff_sin_permiso, ruta, metodo):
    url = reverse("estudios:" + ruta)
    assert getattr(Client(), metodo)(url).status_code == 302
    for usuario in [empleado, staff_sin_permiso]:
        client = Client()
        client.force_login(usuario)
        assert getattr(client, metodo)(url).status_code == 403


def test_formulario_vacio_errores_catalogo_y_csrf(navegador, pruebas, gestor):
    response = preparar_alta(navegador, pruebas, nombre=" ", pruebas=[])
    assert response.status_code == 200
    assert set(response.context["form"].errors) == {"nombre", "pruebas"}
    csrf = Client(enforce_csrf_checks=True)
    csrf.force_login(gestor)
    assert csrf.post(reverse("estudios:tipos_crear"), {}).status_code == 403
    for p in pruebas:
        p.delete()
    assert "No hay pruebas" in navegador.get(reverse("estudios:tipos_crear")).content.decode()


def test_listado_paginado_filtrado_y_navegacion(navegador, tipo_inactivo):
    response = navegador.get(reverse("estudios:tipos_listar"))
    assert response.status_code == 200
    assert tipo_inactivo in response.context["page_obj"]
    assert not navegador.get(reverse("estudios:tipos_listar"), {"estado": "activos"}).context[
        "page_obj"
    ]
    assert "Gestionar tipos" in navegador.get(reverse("inicio")).content.decode()


def abrir_edicion(client, tipo):
    return client.get(reverse("estudios:tipos_editar", args=[tipo.pk]))


def proponer_edicion(client, tipo, contexto, **datos):
    return client.post(
        reverse("estudios:tipos_editar", args=[tipo.pk]),
        {
            "contexto": contexto,
            "nombre": tipo.nombre,
            "descripcion": tipo.descripcion,
            "pruebas": list(tipo.pruebas.values_list("pk", flat=True)),
            **datos,
        },
    )


def test_conflicto_desde_apertura_y_confirmacion(navegador, gestor, tipo):
    apertura = abrir_edicion(navegador, tipo)
    propuesta = proponer_edicion(
        navegador, tipo, apertura.context["contexto"], nombre="Mi propuesta"
    )
    borrador = navegador.get(propuesta.url).context["borrador"]
    gestionar_tipo_estudio(
        usuario=gestor,
        operacion="editar",
        tipo_id=tipo.pk,
        version_esperada=1,
        datos={
            "nombre": "Edición ajena",
            "descripcion": "",
            "prueba_ids": list(tipo.pruebas.values_list("pk", flat=True)),
        },
    )
    conflicto = proponer_edicion(
        navegador, tipo, apertura.context["contexto"], nombre="Mi propuesta"
    )
    assert conflicto.status_code == 200
    assert "Mi propuesta" in conflicto.content.decode()
    assert "Edición ajena" in conflicto.content.decode()
    assert "estudios/tipos/conflicto.html" in [t.name for t in conflicto.templates]
    for _ in range(2):
        response = navegador.post(
            reverse("estudios:tipos_confirmar"), {"token": borrador["token"], "accion": "confirmar"}
        )
        assert "estudios/tipos/conflicto.html" in [t.name for t in response.templates]
    tipo.refresh_from_db()
    assert tipo.nombre == "Edición ajena"
    nuevo = abrir_edicion(navegador, tipo)
    response = proponer_edicion(navegador, tipo, nuevo.context["contexto"], nombre="Revisado")
    borrador = navegador.get(response.url).context["borrador"]
    navegador.post(
        reverse("estudios:tipos_confirmar"), {"token": borrador["token"], "accion": "confirmar"}
    )
    tipo.refresh_from_db()
    assert tipo.nombre == "Revisado"
    assert tipo.version == 3


def test_edicion_volver_y_permiso_revocado(navegador, gestor, tipo_inactivo):
    apertura = abrir_edicion(navegador, tipo_inactivo)
    response = proponer_edicion(
        navegador, tipo_inactivo, apertura.context["contexto"], descripcion="Propuesta"
    )
    resumen = navegador.get(response.url)
    borrador = resumen.context["borrador"]
    volver = navegador.get(resumen.context["volver_url"])
    assert volver.context["form"].initial["descripcion"] == "Propuesta"
    gestor.user_permissions.clear()
    assert (
        navegador.post(
            reverse("estudios:tipos_confirmar"), {"token": borrador["token"], "accion": "confirmar"}
        ).status_code
        == 403
    )
    tipo_inactivo.refresh_from_db()
    assert tipo_inactivo.version == 1


@pytest.mark.parametrize("operacion", ["desactivar", "reactivar", "eliminar"])
def test_operaciones_resumen_cancelacion_y_exito(navegador, tipo, operacion):
    if operacion == "reactivar":
        tipo.activo = False
        tipo.save()
    url = reverse("estudios:tipos_" + operacion, args=[tipo.pk])
    response = navegador.get(url)
    assert response.status_code == 200
    borrador = response.context["borrador"]
    tipo.refresh_from_db()
    assert tipo.version == 1
    navegador.post(
        reverse("estudios:tipos_confirmar"), {"token": borrador["token"], "accion": "cancelar"}
    )
    navegador.post(
        reverse("estudios:tipos_confirmar"), {"token": borrador["token"], "accion": "confirmar"}
    )
    assert TipoEstudio.objects.filter(pk=tipo.pk).exists()
    borrador = navegador.get(url).context["borrador"]
    navegador.post(
        reverse("estudios:tipos_confirmar"),
        {"token": borrador["token"], "accion": "confirmar", "operacion": "eliminar"},
    )
    if operacion == "eliminar":
        assert not TipoEstudio.objects.filter(pk=tipo.pk).exists()
    else:
        tipo.refresh_from_db()
        assert tipo.activo == (operacion == "reactivar")
        assert tipo.version == 2


@pytest.mark.parametrize(
    "ruta", ["tipos_editar", "tipos_desactivar", "tipos_reactivar", "tipos_eliminar"]
)
@pytest.mark.parametrize("metodo", ["get", "post"])
def test_todas_acciones_protegidas(empleado, staff_sin_permiso, tipo, ruta, metodo):
    url = reverse("estudios:" + ruta, args=[tipo.pk])
    assert getattr(Client(), metodo)(url).status_code == 302
    for usuario in [empleado, staff_sin_permiso]:
        client = Client()
        client.force_login(usuario)
        assert getattr(client, metodo)(url).status_code == 403


def test_usado_no_elimina_y_ofrece_desactivacion(navegador, tipo, datos, empleado):
    crear_estudio(datos, empleado)
    response = navegador.get(reverse("estudios:tipos_eliminar", args=[tipo.pk]))
    assert "desactivar" in response.content.decode()
    borrador = response.context["borrador"]
    response = navegador.post(
        reverse("estudios:tipos_confirmar"),
        {"token": borrador["token"], "accion": "confirmar"},
        follow=True,
    )
    assert "desactivarlo" in response.content.decode()
    assert TipoEstudio.objects.filter(pk=tipo.pk).exists()


@pytest.mark.parametrize("ruta", ["tipos_desactivar", "tipos_reactivar", "tipos_eliminar"])
def test_acciones_no_post_y_no_tipo(navegador, tipo, ruta):
    assert navegador.post(reverse("estudios:" + ruta, args=[tipo.pk])).status_code == 405
    assert navegador.get(reverse("estudios:" + ruta, args=[999999])).status_code == 404


def test_confirmar_eliminar_si_aparece_primer_estudio(navegador, tipo, datos, empleado):
    resumen = navegador.get(reverse("estudios:tipos_eliminar", args=[tipo.pk]))
    borrador = resumen.context["borrador"]
    assert borrador["resumen"]["uso"] == 0
    crear_estudio(datos, empleado)
    response = navegador.post(
        reverse("estudios:tipos_confirmar"), {"token": borrador["token"], "accion": "confirmar"}
    )
    assert reverse("estudios:tipos_desactivar", args=[tipo.pk]) in response.content.decode()
    assert TipoEstudio.objects.filter(pk=tipo.pk).exists()


def test_edicion_cancelacion_noop_y_catalogo_preservado(navegador, tipo):
    apertura = abrir_edicion(navegador, tipo)
    response = proponer_edicion(navegador, tipo, apertura.context["contexto"], nombre="No guardar")
    borrador = navegador.get(response.url).context["borrador"]
    navegador.post(
        reverse("estudios:tipos_confirmar"), {"token": borrador["token"], "accion": "cancelar"}
    )
    tipo.refresh_from_db()
    assert tipo.nombre == "Tipo de test" and tipo.version == 1
    apertura = abrir_edicion(navegador, tipo)
    response = proponer_edicion(navegador, tipo, apertura.context["contexto"])
    borrador = navegador.get(response.url).context["borrador"]
    response = navegador.post(
        reverse("estudios:tipos_confirmar"),
        {"token": borrador["token"], "accion": "confirmar"},
        follow=True,
    )
    assert "No hubo cambios" in response.content.decode()
    tipo.refresh_from_db()
    assert tipo.version == 1


def test_get_sin_dml_dominio_y_paginacion(navegador, tipo, django_assert_num_queries):
    from django.db import connection
    from django.test.utils import CaptureQueriesContext

    TipoEstudio.objects.bulk_create([TipoEstudio(nombre=f"Tipo {i:02d}") for i in range(24)])
    with CaptureQueriesContext(connection) as queries:
        response = navegador.get(reverse("estudios:tipos_listar"))
        for ruta in ["tipos_editar", "tipos_desactivar", "tipos_reactivar", "tipos_eliminar"]:
            assert navegador.get(reverse("estudios:" + ruta, args=[tipo.pk])).status_code == 200
    assert len(response.context["page_obj"]) == 20
    assert response.context["page_obj"].paginator.count == 25
    dml = [
        q["sql"]
        for q in queries
        if q["sql"].lstrip().upper().startswith(("INSERT", "UPDATE", "DELETE"))
    ]
    assert not any('"estudios_' in sql or '"pruebas_' in sql for sql in dml)


@pytest.mark.parametrize("ruta", ["tipos_crear", "tipos_confirmar"])
def test_csrf_en_confirmaciones(gestor, ruta):
    client = Client(enforce_csrf_checks=True)
    client.force_login(gestor)
    assert client.post(reverse("estudios:" + ruta), {}).status_code == 403


def test_prueba_desaparece_antes_confirmacion(navegador, pruebas):
    response = preparar_alta(navegador, pruebas)
    borrador = navegador.get(response.url).context["borrador"]
    pruebas[0].delete()
    response = navegador.post(
        reverse("estudios:tipos_confirmar"), {"token": borrador["token"], "accion": "confirmar"}
    )
    assert "ya no existe" in response.content.decode()
    assert not TipoEstudio.objects.exists()


def test_usuario_inactivo_y_enlace_oculto(staff_sin_permiso, gestor, tipo):
    client = Client()
    client.force_login(staff_sin_permiso)
    assert reverse("estudios:tipos_listar") not in client.get(reverse("inicio")).content.decode()
    gestor.is_active = False
    gestor.save(update_fields=["is_active"])
    client.force_login(gestor)
    assert client.get(reverse("estudios:tipos_listar")).status_code == 302
    assert client.post(reverse("estudios:tipos_confirmar"), {}).status_code == 302
    tipo.refresh_from_db()
    assert tipo.version == 1


def test_tipo_eliminado_durante_revision_no_se_recrea(navegador, tipo):
    apertura = abrir_edicion(navegador, tipo)
    response = proponer_edicion(navegador, tipo, apertura.context["contexto"])
    borrador = navegador.get(response.url).context["borrador"]
    tipo.delete()
    response = navegador.post(
        reverse("estudios:tipos_confirmar"), {"token": borrador["token"], "accion": "confirmar"}
    )
    assert response.status_code == 200
    assert "no existe" in response.content.decode()
    assert not TipoEstudio.objects.exists()


@pytest.mark.parametrize("operacion", ["crear", "editar"])
def test_cancelar_desde_formulario_al_volver_invalida_resumen(navegador, tipo, pruebas, operacion):
    cantidad = TipoEstudio.objects.count()
    if operacion == "crear":
        response = preparar_alta(navegador, pruebas)
        ruta = reverse("estudios:tipos_crear")
    else:
        apertura = abrir_edicion(navegador, tipo)
        response = proponer_edicion(
            navegador, tipo, apertura.context["contexto"], nombre="No guardar"
        )
        ruta = reverse("estudios:tipos_editar", args=[tipo.pk])
    resumen = navegador.get(response.url)
    borrador = resumen.context["borrador"]
    form = navegador.get(resumen.context["volver_url"])
    response = navegador.post(
        ruta, {"contexto": form.context["contexto"], "anterior": borrador["clave"], "cancelar": "1"}
    )
    assert response.status_code == 302
    response = navegador.post(
        reverse("estudios:tipos_confirmar"), {"token": borrador["token"], "accion": "confirmar"}
    )
    assert response.status_code == 302
    assert TipoEstudio.objects.count() == cantidad
    tipo.refresh_from_db()
    assert tipo.nombre == "Tipo de test" and tipo.version == 1


@pytest.mark.parametrize("cambio", ["nombre", "descripcion", "pruebas", "desactivar"])
def test_consumidor_ui_exige_reconfirmar_escritor_real(
    navegador, gestor, muestra, tipo, pruebas, cambio
):
    from estudios.models import Estudio

    propuesta = navegador.post(reverse("estudios:crear"), {"muestra": muestra.pk, "tipo": tipo.pk})
    viejo = navegador.get(propuesta.url).context["borrador"]["token"]
    datos = {
        "nombre": tipo.nombre,
        "descripcion": tipo.descripcion,
        "prueba_ids": [p.pk for p in pruebas],
    }
    if cambio == "nombre":
        datos["nombre"] = "Nombre nuevo"
    elif cambio == "descripcion":
        datos["descripcion"] = "Descripción nueva"
    elif cambio == "pruebas":
        datos["prueba_ids"] = [pruebas[0].pk]
    gestionar_tipo_estudio(
        usuario=gestor,
        operacion="desactivar" if cambio == "desactivar" else "editar",
        tipo_id=tipo.pk,
        version_esperada=1,
        datos=datos,
    )
    response = navegador.post(
        reverse("estudios:confirmar"), {"token": viejo, "accion": "confirmar"}
    )
    assert not Estudio.objects.exists()
    if cambio == "desactivar":
        assert response.status_code == 302
        return
    assert response.status_code == 200
    nuevo = response.context["borrador"]["token"]
    assert nuevo != viejo
    navegador.post(reverse("estudios:confirmar"), {"token": viejo, "accion": "confirmar"})
    assert not Estudio.objects.exists()
    navegador.post(reverse("estudios:confirmar"), {"token": nuevo, "accion": "confirmar"})
    estudio = Estudio.objects.get()
    assert estudio.tipo_nombre_snapshot == datos["nombre"]
    assert estudio.tipo_descripcion_snapshot == datos["descripcion"]
    assert (
        list(estudio.pruebas_asignadas.order_by("prueba_id").values_list("prueba_id", flat=True))
        == datos["prueba_ids"]
    )
