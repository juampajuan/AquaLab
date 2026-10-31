import pytest
from django.contrib.auth.models import Permission
from django.test import Client
from django.urls import reverse

from pruebas.models import LimiteVertido, Prueba, TipoCalculo, TipoVertido

pytestmark = pytest.mark.django_db

LISTADO = reverse("admin:pruebas_prueba_changelist")
ALTA = reverse("admin:pruebas_prueba_add")
INLINE = "limites_vertido"


def editar(prueba):
    return reverse("admin:pruebas_prueba_change", args=[prueba.pk])


def borrar(prueba):
    return reverse("admin:pruebas_prueba_delete", args=[prueba.pk])


def formulario(limites=(), **cambios):
    datos = {
        "codigo": "NUEVA",
        "nombre": "Prueba nueva",
        "tipo_calculo": TipoCalculo.DIRECTO,
        "activa": "on",
        f"{INLINE}-TOTAL_FORMS": str(len(limites)),
        f"{INLINE}-INITIAL_FORMS": "0",
        f"{INLINE}-MIN_NUM_FORMS": "0",
        f"{INLINE}-MAX_NUM_FORMS": "2",
    }
    for i, limite in enumerate(limites):
        for campo, valor in limite.items():
            datos[f"{INLINE}-{i}-{campo}"] = valor
    datos.update(cambios)
    return {campo: valor for campo, valor in datos.items() if valor is not None}


def formulario_de(prueba, **cambios):
    datos = {
        campo: getattr(prueba, campo)
        for campo in (
            "codigo",
            "nombre",
            "unidad",
            "unidad_medicion",
            "tipo_calculo",
            "formula",
            "norma",
            "limite_min",
            "limite_max",
            "limite_deteccion",
            "observacion",
        )
    }
    if prueba.activa:
        datos["activa"] = "on"
    return formulario(**{**datos, **cambios})


def codigos(respuesta):
    return {prueba.codigo for prueba in respuesta.context["cl"].result_list}


# User Story 3: consultar y mantener las pruebas en el admin


def test_admin_listado_busqueda_y_filtros(admin_client):
    Prueba.objects.create(codigo="PH", nombre="pH")
    Prueba.objects.create(
        codigo="SDT",
        nombre="Sólidos disueltos",
        tipo_calculo=TipoCalculo.FORMULA,
        formula="x*10",
    )
    Prueba.objects.create(codigo="TURB", nombre="Turbidez", observacion="Confirmar tipo.")

    respuesta = admin_client.get(LISTADO)
    contenido = respuesta.content.decode()
    for columna in ("Código", "Nombre", "Unidad del resultado", "Tipo de cálculo", "Activa"):
        assert columna in contenido
    assert codigos(respuesta) == {"PH", "SDT", "TURB"}

    assert codigos(admin_client.get(LISTADO, {"q": "sól"})) == {"SDT"}
    assert codigos(admin_client.get(LISTADO, {"q": "ph"})) == {"PH"}
    assert codigos(admin_client.get(LISTADO, {"tipo_calculo__exact": "FORMULA"})) == {"SDT"}
    assert codigos(admin_client.get(LISTADO, {"activa__exact": "0"})) == set()
    assert codigos(admin_client.get(LISTADO, {"observacion": "con"})) == {"TURB"}
    assert codigos(admin_client.get(LISTADO, {"observacion": "sin"})) == {"PH", "SDT"}


def test_admin_detalle_muestra_limites(admin_client):
    prueba = Prueba.objects.create(codigo="CL2-LIB", nombre="Cloro libre")
    LimiteVertido.objects.create(
        prueba=prueba, tipo_vertido=TipoVertido.CLOACAL, limite_max="NE", norma="(AGOSBA) 389/98"
    )
    LimiteVertido.objects.create(prueba=prueba, tipo_vertido=TipoVertido.CANAL, limite_max="0.5")

    respuesta = admin_client.get(editar(prueba))

    formset = respuesta.context["inline_admin_formsets"][0].formset
    assert formset.total_form_count() == 2
    contenido = respuesta.content.decode()
    assert 'value="NE"' in contenido
    assert 'value="0.5"' in contenido
    assert "(AGOSBA) 389/98" in contenido


def test_admin_alta_prueba(admin_client):
    respuesta = admin_client.post(
        ALTA,
        formulario(
            tipo_calculo=TipoCalculo.FORMULA,
            formula="x*2",
            limites=[{"tipo_vertido": "canal", "limite_max": "Ausente"}],
        ),
    )
    assert respuesta.status_code == 302
    prueba = Prueba.objects.get(codigo="NUEVA")
    assert (prueba.nombre, prueba.formula) == ("Prueba nueva", "x*2")
    assert prueba.limites_vertido.get().limite_max == "Ausente"


CASOS_ALTA_INVALIDA = {
    "código existente": {"codigo": "PH"},
    "código vacío": {"codigo": ""},
    "nombre vacío": {"nombre": ""},
    "directo con fórmula": {"formula": "x*2"},
    "referencia inexistente": {
        "tipo_calculo": TipoCalculo.FORMULA,
        "formula": "{NOEXISTE}*2",
        "es_calculada": "on",
    },
    "límite repetido": {
        "limites": [{"tipo_vertido": "canal"}, {"tipo_vertido": "canal", "limite_max": "1"}]
    },
}


@pytest.mark.parametrize("caso", CASOS_ALTA_INVALIDA)
def test_admin_alta_rechaza_invalidas(admin_client, caso):
    Prueba.objects.create(codigo="PH", nombre="pH")

    respuesta = admin_client.post(ALTA, formulario(**CASOS_ALTA_INVALIDA[caso]))

    assert respuesta.status_code == 200
    errores = respuesta.context["errors"]
    assert errores
    assert set(Prueba.objects.values_list("codigo", flat=True)) == {"PH"}
    if caso == "referencia inexistente":
        assert "«NOEXISTE»" in str(errores)


@pytest.mark.parametrize("fixture", ["prueba_en_tipo", "prueba_en_estudio"])
def test_admin_prueba_en_uso_codigo_nombre_solo_lectura(request, admin_client, fixture):
    prueba = request.getfixturevalue(fixture)
    codigo, nombre = prueba.codigo, prueba.nombre

    contenido = admin_client.get(editar(prueba)).content.decode()
    assert 'name="codigo"' not in contenido
    assert 'name="nombre"' not in contenido
    assert prueba.codigo in contenido and prueba.nombre in contenido

    respuesta = admin_client.post(
        editar(prueba), formulario_de(prueba, codigo="OTRO", nombre="Otro", unidad="mg/l")
    )

    assert respuesta.status_code == 302
    prueba.refresh_from_db()
    assert (prueba.codigo, prueba.nombre, prueba.unidad) == (codigo, nombre, "mg/l")


def test_admin_prueba_libre_editable(admin_client, prueba_libre):
    contenido = admin_client.get(editar(prueba_libre)).content.decode()
    assert 'name="codigo"' in contenido
    assert 'name="nombre"' in contenido

    respuesta = admin_client.post(
        editar(prueba_libre), formulario_de(prueba_libre, codigo="LIBRE-2", nombre="Otro nombre")
    )

    assert respuesta.status_code == 302
    prueba_libre.refresh_from_db()
    assert (prueba_libre.codigo, prueba_libre.nombre) == ("LIBRE-2", "Otro nombre")


def test_admin_no_elimina_prueba_en_uso(admin_client, prueba_en_tipo, prueba_libre):
    assert borrar(prueba_en_tipo) not in admin_client.get(editar(prueba_en_tipo)).content.decode()
    assert admin_client.get(borrar(prueba_en_tipo)).status_code == 403
    admin_client.post(
        LISTADO,
        {"action": "delete_selected", "_selected_action": [prueba_en_tipo.pk], "post": "yes"},
    )
    assert Prueba.objects.filter(pk=prueba_en_tipo.pk).exists()

    LimiteVertido.objects.create(prueba=prueba_libre, tipo_vertido=TipoVertido.CANAL)
    assert borrar(prueba_libre) in admin_client.get(editar(prueba_libre)).content.decode()
    respuesta = admin_client.post(borrar(prueba_libre), {"post": "yes"})
    assert respuesta.status_code == 302
    assert not Prueba.objects.filter(pk=prueba_libre.pk).exists()
    assert not LimiteVertido.objects.exists()


def test_admin_requiere_staff_y_permiso(django_user_model):
    def cliente(email, **datos):
        usuario = django_user_model.objects.create_user(
            email=email, password="Clave-Valida-123", is_active=True, **datos
        )
        c = Client()
        c.force_login(usuario)
        return c, usuario

    sin_staff, _ = cliente("sin-staff-pruebas@ejemplo.com")
    respuesta = sin_staff.get(LISTADO)
    assert respuesta.status_code == 302
    assert "login" in respuesta["Location"]

    staff, usuario = cliente("staff-pruebas@ejemplo.com", is_staff=True)
    assert staff.get(LISTADO).status_code == 403

    usuario.user_permissions.add(Permission.objects.get(codename="view_prueba"))
    assert staff.get(LISTADO).status_code == 200
    assert staff.get(ALTA).status_code == 403
    assert staff.post(ALTA, formulario()).status_code == 403
    assert not Prueba.objects.exists()
