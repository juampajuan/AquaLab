"""Pantalla de comparación histórica (US 8.1): accesos, permisos, gráfico y variación."""

import datetime as dt
import json
import re

import pytest
from django.contrib.auth.models import Group
from django.test import Client
from django.urls import reverse

from estudios.models import Estudio, PruebaEstudio, Validacion
from muestras.models import Origen

pytestmark = pytest.mark.django_db

URL = reverse("estudios:comparacion")
DIA = dt.date(2026, 3, 2)


def dia(n):
    return DIA + dt.timedelta(days=n)


def html_de(respuesta):
    return respuesta.content.decode()


def datos_de(respuesta):
    texto = re.search(
        r'<script id="datos-comparacion" type="application/json">(.*?)</script>',
        html_de(respuesta),
        re.S,
    ).group(1)
    return json.loads(texto)


def tarjeta(html, codigo):
    inicio = html.index(f'data-prueba="{codigo}"')
    fin = html.find("data-prueba=", inicio + 1)
    return html[inicio : fin if fin != -1 else len(html)]


@pytest.fixture
def origen(cliente_a):
    return Origen.objects.create(cliente=cliente_a, nombre="Pozo de la vista")


@pytest.fixture
def historia(origen, estudio_en_origen):
    """Cloruro 100 y 120 validados, Cloruro 400 sin validar y pH sin historial en el actual."""
    estudio_en_origen(origen, dia(0), 400001, {"CL-": "10"})
    estudio_en_origen(origen, dia(1), 400002, {"CL-": "12"})
    return estudio_en_origen(origen, dia(2), 400003, {"CL-": "40", "PH": "7.2"}, validar_todo=False)


def usuario(django_user_model, email, *grupos):
    creado = django_user_model.objects.create_user(
        email=email, password="Clave-Valida-123", is_active=True
    )
    for nombre in grupos:
        creado.groups.add(Group.objects.get(name=nombre))
    cliente = Client()
    cliente.force_login(creado)
    return cliente


# --- Accesos y permisos (FR-001, FR-018) -----------------------------------------------------


def test_boton_en_detalle_solo_con_permiso(historia, cliente_bioquimico, django_user_model):
    detalle = reverse("estudios:detalle", args=[historia.pk])
    enlace = f'href="{URL}?estudio={historia.pk}"'

    con_permiso = html_de(cliente_bioquimico.get(detalle))
    sin_permiso = html_de(usuario(django_user_model, "tecnico-81@ejemplo.com").get(detalle))

    assert enlace in con_permiso and "Comparación histórica" in con_permiso
    assert enlace not in sin_permiso and "Comparación histórica" not in sin_permiso


def test_permisos(historia, cliente_bioquimico, django_user_model, staff_sin_permiso):
    url = f"{URL}?estudio={historia.pk}"

    sin_sesion = Client().get(url)
    sin_permiso = Client()
    sin_permiso.force_login(staff_sin_permiso)
    administrador = usuario(django_user_model, "admin-81@ejemplo.com", "Administradores")

    assert sin_sesion.status_code == 302
    assert sin_sesion["Location"].startswith(reverse("usuarios:login"))
    assert sin_permiso.get(url).status_code == 403
    assert administrador.get(url).status_code == 200
    assert cliente_bioquimico.get(url).status_code == 200


def test_post_405(historia, cliente_bioquimico):
    assert cliente_bioquimico.post(f"{URL}?estudio={historia.pk}").status_code == 405


@pytest.mark.parametrize("valor", ["999999", "abc"])
def test_estudio_inexistente_404(cliente_bioquimico, valor):
    assert cliente_bioquimico.get(f"{URL}?estudio={valor}").status_code == 404


# --- Desde el estudio (US 1) -----------------------------------------------------------------


def test_desde_estudio(historia, origen, cliente_bioquimico):
    respuesta = cliente_bioquimico.get(f"{URL}?estudio={historia.pk}")
    html = html_de(respuesta)

    assert respuesta.status_code == 200
    assert origen.nombre in html and origen.cliente.nombre_completo in html
    assert f"N° PI {historia.muestra.numero_pi}" in html
    assert historia.tipo_nombre_snapshot in html
    assert "Sin iniciar" in html or "En proceso" in html
    assert "Volver al estudio" in html
    assert html.count("data-prueba=") == 2

    cloruro = tarjeta(html, "CL-")
    assert '<canvas id="grafico-CL-"' in cloruro
    assert 'aria-label="Evolución de Cloruro en Pozo de la vista"' in cloruro
    assert "Máximo 350 mg/l · Límite general" in cloruro
    assert "Sin validar" in cloruro
    assert "Fuera de la franja del límite" in cloruro
    assert "▲ +280 mg/l (+233,3 %)" in cloruro  # 400 contra 120
    assert "Contra el promedio de 2 anteriores (110 mg/l)" in cloruro
    assert "▲ +290 mg/l (+263,6 %)" in cloruro

    datos = datos_de(respuesta)
    (cl,) = [p for p in datos["pruebas"] if p["codigo"] == "CL-"]
    assert cl["franja"] == {"min": None, "max": "350.0", "comparable": True}
    assert cl["puntos"][-1] == {
        "etiqueta": f"{dia(2):%d/%m/%Y} · PI 400003",
        "valor": "400.0000000000",
        "texto": "400",
        "validado": False,
        "referencia": True,
    }
    assert [p["referencia"] for p in cl["puntos"]] == [False, False, True]


def test_referencia_validada(origen, estudio_en_origen, cliente_bioquimico):
    estudio_en_origen(origen, dia(0), 400001, {"CL-": "10"})
    actual = estudio_en_origen(origen, dia(1), 400002, {"CL-": "12"})

    cloruro = tarjeta(html_de(cliente_bioquimico.get(f"{URL}?estudio={actual.pk}")), "CL-")

    assert "Validado" in cloruro and "Sin validar" not in cloruro
    assert "Fuera de la franja del límite" not in cloruro


def test_referencia_sin_resultado(origen, estudio_en_origen, cliente_bioquimico):
    estudio_en_origen(origen, dia(0), 400001, {"CL-": "10"})
    actual = estudio_en_origen(origen, dia(1), 400002, {"CL-": None})

    cloruro = tarjeta(html_de(cliente_bioquimico.get(f"{URL}?estudio={actual.pk}")), "CL-")

    assert "Sin resultado en este estudio" in cloruro
    assert '<canvas id="grafico-CL-"' in cloruro


def test_prueba_sin_historial(historia, cliente_bioquimico):
    ph = tarjeta(html_de(cliente_bioquimico.get(f"{URL}?estudio={historia.pk}")), "PH")

    assert "Sin historial para comparar" in ph
    assert "<canvas" not in ph
    assert "7,2" in ph and "Sin validar" in ph


def test_json_sin_float(historia, cliente_bioquimico):
    datos = datos_de(cliente_bioquimico.get(f"{URL}?estudio={historia.pk}"))

    assert [p["codigo"] for p in datos["pruebas"]] == ["CL-"]  # pH no tiene historial
    for prueba in datos["pruebas"]:
        for punto in prueba["puntos"]:
            assert isinstance(punto["valor"], str)
        for borde in prueba["franja"]["min"], prueba["franja"]["max"]:
            assert borde is None or isinstance(borde, str)


def test_solo_lectura(historia, cliente_bioquimico):
    def estado():
        return (
            sorted(Estudio.objects.values_list("pk", "estado")),
            sorted(PruebaEstudio.objects.values_list("pk", "estado")),
            sorted(Validacion.objects.values_list("pk", "anulada")),
        )

    antes = estado()
    cliente_bioquimico.get(f"{URL}?estudio={historia.pk}")

    assert estado() == antes


def test_sin_parametros_ofrece_volver_al_dashboard(cliente_bioquimico):
    html = html_de(cliente_bioquimico.get(URL))

    assert "data-prueba=" not in html
    assert reverse("informes:dashboard") in html


# --- Elegir pruebas (US 3) -------------------------------------------------------------------


@pytest.fixture
def tres_pruebas(origen, estudio_en_origen):
    estudio_en_origen(origen, dia(0), 400001, {"CL-": "10", "COND": "500", "PH": "7.0"})
    return estudio_en_origen(
        origen, dia(1), 400002, {"CL-": "12", "COND": "520", "PH": "7.1"}, validar_todo=False
    )


def casillas_marcadas(html):
    return re.findall(r'<input type="checkbox" name="pruebas" value="([^"]+)"[^>]*checked', html)


def test_seleccion_por_defecto(tres_pruebas, origen, cliente_bioquimico):
    con_estudio = html_de(cliente_bioquimico.get(f"{URL}?estudio={tres_pruebas.pk}"))
    sin_estudio = html_de(
        cliente_bioquimico.get(f"{URL}?cliente={origen.cliente_id}&origen={origen.pk}")
    )

    assert casillas_marcadas(con_estudio) == ["CL-", "COND", "PH"]
    assert re.findall(r'data-prueba="([^"]+)"', con_estudio) == ["CL-", "COND", "PH"]
    # Sin estudio: por nombre (Cloruro, Conductividad, pH).
    assert casillas_marcadas(sin_estudio) == ["CL-", "COND", "PH"]


def test_seleccion_en_url(tres_pruebas, cliente_bioquimico):
    url = f"{URL}?estudio={tres_pruebas.pk}&pruebas=CL-&pruebas=COND&elegir=1"

    html = html_de(cliente_bioquimico.get(url))

    assert re.findall(r'data-prueba="([^"]+)"', html) == ["CL-", "COND"]
    assert casillas_marcadas(html) == ["CL-", "COND"]
    assert [p["codigo"] for p in datos_de(cliente_bioquimico.get(url))["pruebas"]] == [
        "CL-",
        "COND",
    ]


def test_seleccion_vacia(tres_pruebas, cliente_bioquimico):
    html = html_de(cliente_bioquimico.get(f"{URL}?estudio={tres_pruebas.pk}&elegir=1"))

    assert "Elegí al menos una prueba para ver su evolución." in html
    assert "data-prueba=" not in html


def test_codigo_desconocido_ignorado(tres_pruebas, cliente_bioquimico):
    url = f"{URL}?estudio={tres_pruebas.pk}&pruebas=CL-&pruebas=NO-EXISTE&elegir=1"

    respuesta = cliente_bioquimico.get(url)

    assert respuesta.status_code == 200
    assert re.findall(r'data-prueba="([^"]+)"', html_de(respuesta)) == ["CL-"]


def test_selector_accesible(tres_pruebas, origen, cliente_bioquimico):
    html = html_de(cliente_bioquimico.get(f"{URL}?estudio={tres_pruebas.pk}"))
    desde_origen = html_de(
        cliente_bioquimico.get(f"{URL}?cliente={origen.cliente_id}&origen={origen.pk}")
    )

    formulario = re.search(r'<form method="get"[^>]*data-elegir-pruebas.*?</form>', html, re.S)
    assert formulario
    selector = formulario.group(0)
    assert "<fieldset" in selector and "Pruebas a mostrar" in selector and "<legend" in selector
    assert re.search(r'<label[^>]*for="id_pruebas_0"', selector)
    assert f'name="estudio" value="{tres_pruebas.pk}"' in selector
    assert 'name="elegir" value="1"' in selector
    assert "Aplicar" in selector
    assert 'data-atajo="todas"' in selector and 'data-atajo="ninguna"' in selector
    assert re.search(r'data-atajo="todas"[^>]*hidden|hidden[^>]*data-atajo="todas"', selector)
    assert f'name="origen" value="{origen.pk}"' in desde_origen
    assert f'name="cliente" value="{origen.cliente_id}"' in desde_origen


# --- Desde el dashboard (US 4) ---------------------------------------------------------------


def url_origen(origen, cliente=None):
    return f"{URL}?cliente={(cliente or origen.cliente).pk}&origen={origen.pk}"


def test_desde_origen(historia, origen, cliente_bioquimico):
    respuesta = cliente_bioquimico.get(url_origen(origen))
    html = html_de(respuesta)

    assert respuesta.status_code == 200
    assert origen.nombre in html
    assert "Estudio de referencia" not in html and "Volver al estudio" not in html
    assert "Volver al dashboard" in html
    cloruro = tarjeta(html, "CL-")
    assert "Último validado" in cloruro
    assert "▲ +20 mg/l (+20,0 %)" in cloruro  # 120 contra 100
    (cl,) = datos_de(respuesta)["pruebas"]
    assert not any(p["referencia"] for p in cl["puntos"])
    assert len(cl["puntos"]) == 2  # el 400 sin validar no forma parte del historial


def test_origen_de_otro_cliente(origen, historia, cliente_bioquimico):
    from clientes.models import Cliente

    otro = Cliente.objects.create(
        nombre="Otro cliente", tipo_documento="DNI", numero_documento="30999888", email="o@x.com"
    )

    html = html_de(cliente_bioquimico.get(url_origen(origen, cliente=otro)))

    assert "El origen no pertenece al cliente elegido." in html
    assert 'id="id_origen_error"' in html
    assert "data-prueba=" not in html


def test_solo_cliente_paso_dos(origen, cliente_bioquimico):
    from clientes.models import Cliente

    otro = Cliente.objects.create(
        nombre="Otro cliente", tipo_documento="DNI", numero_documento="30999888", email="o@x.com"
    )
    Origen.objects.create(cliente=otro, nombre="Origen ajeno")
    Origen.objects.create(cliente=origen.cliente, nombre="Segundo origen")

    html = html_de(cliente_bioquimico.get(f"{URL}?cliente={origen.cliente_id}"))

    select = re.search(r'<select name="origen".*?</select>', html, re.S).group(0)
    assert "Pozo de la vista" in select and "Segundo origen" in select
    assert "Origen ajeno" not in select and "<optgroup" not in select
    assert re.search(rf'<option value="{origen.cliente_id}" selected>', html)


def test_sin_parametros_selector_agrupado(origen, cliente_bioquimico):
    html = html_de(cliente_bioquimico.get(URL))

    select = re.search(r'<select name="origen".*?</select>', html, re.S).group(0)
    assert f'<optgroup label="{origen.cliente.nombre_completo}">' in select
    assert "data-prueba=" not in html
    assert reverse("informes:dashboard") in html


def test_cliente_inactivo_no_se_ofrece(origen, cliente_bioquimico):
    from clientes.models import Cliente

    Cliente.objects.filter(pk=origen.cliente_id).update(activo=False)

    selector = html_de(cliente_bioquimico.get(URL))
    con_inactivo = html_de(cliente_bioquimico.get(url_origen(origen)))

    assert origen.cliente.nombre_completo not in selector
    assert 'id="id_cliente_error"' in con_inactivo
    assert "data-prueba=" not in con_inactivo


def test_origen_sin_validados(origen, estudio_en_origen, cliente_bioquimico):
    estudio_en_origen(origen, dia(0), 400001, {"CL-": "10"}, validar_todo=False)

    html = html_de(cliente_bioquimico.get(url_origen(origen)))

    assert "Este origen todavía no tiene resultados validados" in html
    assert "Volver al dashboard" in html
    assert "data-elegir-pruebas" not in html


def test_estudio_tiene_prioridad(historia, origen, cliente_a, cliente_bioquimico):
    otro = Origen.objects.create(cliente=cliente_a, nombre="Otro origen del cliente")

    html = html_de(cliente_bioquimico.get(f"{URL}?estudio={historia.pk}&origen={otro.pk}"))

    assert "Pozo de la vista" in html
    assert "Estudio de referencia" in html


# --- Ver datos y lo que ve el cliente (US 5) -------------------------------------------------


def test_tabla_ver_datos(origen, estudio_en_origen, cliente_bioquimico):
    from estudios.models import Resultado

    viejo = estudio_en_origen(origen, dia(0), 400001, {"CL-": "0.001"})  # 0,01 < LD 0,1
    estudio_en_origen(origen, dia(1), 400002, {"CL-": "12"})
    otra_unidad = estudio_en_origen(origen, dia(2), 400003, {"CL-": "13"})
    Resultado.objects.filter(asignacion__estudio=otra_unidad).update(unidad="g/l")
    actual = estudio_en_origen(origen, dia(3), 400004, {"CL-": "40"}, validar_todo=False)

    cloruro = tarjeta(html_de(cliente_bioquimico.get(f"{URL}?estudio={actual.pk}")), "CL-")
    tabla = re.search(r"<details.*?</details>", cloruro, re.S).group(0)

    assert "<summary" in tabla and "Ver datos" in tabla
    for columna in ("Fecha de muestreo", "N° PI", "Resultado", "Evaluación", "Estado"):
        assert f"<th>{columna}</th>" in tabla
    filas = re.findall(r"<tr data-punto.*?</tr>", tabla, re.S)
    assert len(filas) == 4
    assert [re.search(r"PI (\d+)", f).group(1) for f in filas] == [
        "400001",
        "400002",
        "400003",
        "400004",
    ]
    assert reverse("muestras:detalle", args=[viejo.muestra.pk]) in filas[0]
    assert "&lt; 0,1" in filas[0] and "Cumple" in filas[0] and "Validado" in filas[0]
    assert "Otra unidad (g/l), no se compara" in filas[2]
    assert "Este estudio" in filas[3] and "Sin validar" in filas[3]
    assert "Fuera de norma" in filas[3]
    assert reverse("estudios:detalle", args=[actual.pk]) in filas[3]


def test_tabla_presencia_sin_numeros(origen, estudio_en_origen, cliente_bioquimico):
    estudio_en_origen(origen, dia(0), 400001, {"ECOLI": "0"})
    estudio_en_origen(origen, dia(1), 400002, {"ECOLI": "1"})

    ecoli = tarjeta(html_de(cliente_bioquimico.get(url_origen(origen))), "ECOLI")
    tabla = re.search(r"<details.*?</details>", ecoli, re.S).group(0)

    assert "Ausente" in tabla and "Presente" in tabla
    assert "Cambió: Ausente → Presente" in ecoli and "Presente en 0 de 1" in ecoli


def test_no_aparece_en_informe_pdf_ni_correo(
    origen, estudio_en_origen, cliente_bioquimico, bioquimico, monkeypatch, mailoutbox
):
    from informes.envios import enviar_informe
    from informes.servicios import emitir_informe

    estudio_en_origen(origen, dia(0), 400001, {"CL-": "10"})
    actual = estudio_en_origen(origen, dia(1), 400002, {"CL-": "12"}, usuario=bioquimico)
    emitir_informe(actual.pk, bioquimico)
    monkeypatch.setattr("informes.envios.generar_pdf", lambda informe: b"%PDF-1.4")
    enviar_informe(actual.pk, bioquimico, "1d0e9a8e-3333-4f00-9000-000000000003")

    textos = [
        html_de(cliente_bioquimico.get(reverse("informes:ver", args=[actual.pk]))),
        html_de(cliente_bioquimico.get(reverse("informes:imprimir", args=[actual.pk]))),
        mailoutbox[-1].body,
    ]

    for texto in textos:
        assert "Comparación histórica" not in texto
        assert "Contra el anterior" not in texto
        assert "datos-comparacion" not in texto
