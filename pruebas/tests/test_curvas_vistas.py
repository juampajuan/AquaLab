"""US 6.6 – pantallas de curvas: carga, importación, consulta, borrado y acceso."""

import datetime
import re

import pytest
from django.urls import reverse
from django.utils import timezone

from pruebas import curvas
from pruebas.models import CurvaCalibracion

pytestmark = pytest.mark.django_db

REFERENCIA = [
    ("0", "0,000"),
    ("0,1", "0,052"),
    ("0,2", "0,101"),
    ("0,3", "0,153"),
    ("0,4", "0,199"),
]


def url_nueva(prueba):
    return reverse("catalogo:nueva_curva", args=[prueba.pk])


def envio(puntos=REFERENCIA, accion="calcular", **extra):
    """POST del formulario de carga con el formset `puntos`."""
    datos = {
        "accion": accion,
        "fecha_preparacion": timezone.localdate().isoformat(),
        "observacion": "",
        "archivo_origen": "",
        "puntos-TOTAL_FORMS": str(len(puntos)),
        "puntos-INITIAL_FORMS": "0",
        "puntos-MIN_NUM_FORMS": "0",
        "puntos-MAX_NUM_FORMS": "1000",
    }
    for n, (concentracion, absorbancia) in enumerate(puntos):
        datos[f"puntos-{n}-concentracion"] = concentracion
        datos[f"puntos-{n}-absorbancia"] = absorbancia
    datos.update(extra)
    return datos


def ir_a_confirmar(cliente, prueba, **extra):
    respuesta = cliente.post(url_nueva(prueba), envio(accion="guardar", **extra))
    assert respuesta.status_code == 302, respuesta.content.decode()[:2000]
    return respuesta["Location"]


def token(html):
    return re.search(r'name="token" value="([^"]+)"', html).group(1)


# --- US2: carga manual ------------------------------------------------------------------------


def test_carga_manual_formulario(cliente_catalogo, prueba_curva):
    html = cliente_catalogo.get(url_nueva(prueba_curva)).content.decode()
    assert 'name="fecha_preparacion"' in html
    assert 'name="observacion"' in html
    assert html.count('name="puntos-') >= 6  # 3 filas × concentración y absorbancia
    assert 'value="agregar_fila"' in html
    assert "Calcular recta" in html
    assert 'value="guardar"' not in html


def test_carga_manual_prueba_no_curva(cliente_catalogo, prueba_libre):
    respuesta = cliente_catalogo.get(url_nueva(prueba_libre), follow=True)
    assert respuesta.redirect_chain[-1][0] == reverse("catalogo:ficha", args=[prueba_libre.pk])
    assert "Esta prueba no se calcula con curva de calibración." in respuesta.content.decode()


def test_carga_manual_filas(cliente_catalogo, prueba_curva):
    html = cliente_catalogo.post(
        url_nueva(prueba_curva), envio(REFERENCIA[:3], accion="agregar_fila")
    ).content.decode()
    assert 'name="puntos-3-concentracion"' in html
    assert 'value="0,2"' in html  # conserva lo escrito
    html = cliente_catalogo.post(
        url_nueva(prueba_curva), envio(REFERENCIA[:4], accion="quitar_1")
    ).content.decode()
    assert 'name="puntos-3-concentracion"' not in html
    assert 'value="0,052"' not in html
    assert 'value="0,101"' in html


def test_carga_manual_calcular(cliente_catalogo, prueba_curva):
    respuesta = cliente_catalogo.post(url_nueva(prueba_curva), envio())
    assert respuesta.status_code == 302
    assert respuesta["Location"].startswith(
        reverse("catalogo:confirmar_curva", args=[prueba_curva.pk])
    )
    html = cliente_catalogo.get(respuesta["Location"]).content.decode()
    assert "0,499" in html
    assert "0,0012" in html
    assert "0,9996" in html
    assert 'id="datos-curva"' in html
    assert "chart.umd.min.js" in html
    assert 'value="confirmar"' in html
    assert not CurvaCalibracion.objects.exists()


@pytest.mark.parametrize(
    "puntos, extra, mensaje",
    [
        (REFERENCIA[:2], {}, curvas.MENSAJE_POCOS_PUNTOS),
        (REFERENCIA[:3] + [("0,4", "")], {}, curvas.MENSAJE_FALTA_ABSORBANCIA),
        (REFERENCIA[:3] + [("", "0,2")], {}, curvas.MENSAJE_FALTA_CONCENTRACION),
        (REFERENCIA[:3] + [("0,4", "-0,2")], {}, curvas.MENSAJE_NEGATIVO),
        (REFERENCIA[:3] + [("0,4", "abc")], {}, "Ingresá un número válido"),
        (
            REFERENCIA,
            {"fecha_preparacion": (timezone.localdate() + datetime.timedelta(days=1)).isoformat()},
            curvas.MENSAJE_FECHA_FUTURA,
        ),
    ],
    ids=["2 puntos", "sin absorbancia", "sin concentración", "negativa", "texto", "mañana"],
)
def test_carga_manual_errores(cliente_catalogo, prueba_curva, puntos, extra, mensaje):
    html = cliente_catalogo.post(url_nueva(prueba_curva), envio(puntos, **extra)).content.decode()
    assert mensaje in html
    assert 'value="guardar"' not in html


def test_carga_manual_filas_vacias_se_ignoran(cliente_catalogo, prueba_curva):
    html = cliente_catalogo.post(
        url_nueva(prueba_curva), envio(REFERENCIA + [("", "")]), follow=True
    ).content.decode()
    assert "0,9996" in html


def test_carga_manual_r2_bajo(cliente_catalogo, prueba_curva):
    bajos = [("0", "0"), ("1", "0,5"), ("2", "0,7"), ("3", "1,6")]
    respuesta = cliente_catalogo.post(url_nueva(prueba_curva), envio(bajos))
    pagina = cliente_catalogo.get(respuesta["Location"]).content.decode()
    assert curvas.MENSAJE_R2_BAJO in pagina
    assert 'value="confirmar"' in pagina  # se puede guardar igual


def test_carga_manual_resumen(cliente_catalogo, prueba_curva, curva_de):
    curva_de(prueba_curva, fecha=datetime.date(2026, 1, 10))
    location = ir_a_confirmar(cliente_catalogo, prueba_curva, observacion="Lote 12")
    assert location.startswith(reverse("catalogo:confirmar_curva", args=[prueba_curva.pk]))
    html = cliente_catalogo.get(location).content.decode()
    for texto in ("NO2-C", "5 puntos", "0,499", "0,0012", "0,9996", "Lote 12"):
        assert texto in html
    assert "La curva vigente del 10/01/2026 pasa a histórica" in html
    assert "0 a 0,4 mg/l" in html
    assert not CurvaCalibracion.objects.filter(observacion="Lote 12").exists()


def test_carga_manual_confirmar(cliente_catalogo, prueba_curva):
    location = ir_a_confirmar(cliente_catalogo, prueba_curva)
    html = cliente_catalogo.get(location).content.decode()
    respuesta = cliente_catalogo.post(
        location, {"token": token(html), "accion": "confirmar"}, follow=True
    )
    assert respuesta.redirect_chain[-1][0] == reverse("catalogo:ficha", args=[prueba_curva.pk])
    assert "Curva guardada: es la vigente de NO2-C." in respuesta.content.decode()
    curva = CurvaCalibracion.objects.get()
    assert curva.vigente and curva.puntos.count() == 5
    # Reenvío de la misma confirmación: no duplica.
    cliente_catalogo.post(location, {"token": token(html), "accion": "confirmar"})
    assert CurvaCalibracion.objects.count() == 1


def test_carga_manual_cancelar(cliente_catalogo, prueba_curva):
    location = ir_a_confirmar(cliente_catalogo, prueba_curva)
    html = cliente_catalogo.get(location).content.decode()
    respuesta = cliente_catalogo.post(location, {"token": token(html), "accion": "cancelar"})
    assert respuesta.status_code == 302
    assert respuesta["Location"].startswith(url_nueva(prueba_curva))
    formulario = cliente_catalogo.get(respuesta["Location"]).content.decode()
    assert 'value="0,199"' in formulario or 'value="0.199"' in formulario
    assert not CurvaCalibracion.objects.exists()


def test_borrador_invalido(cliente_catalogo, prueba_curva):
    location = ir_a_confirmar(cliente_catalogo, prueba_curva)
    respuesta = cliente_catalogo.post(
        location, {"token": "alterado", "accion": "confirmar"}, follow=True
    )
    assert curvas.MENSAJE_BORRADOR_INVALIDO in respuesta.content.decode()
    assert not CurvaCalibracion.objects.exists()
    otra = cliente_catalogo.get(
        reverse("catalogo:confirmar_curva", args=[prueba_curva.pk]) + "?solicitud=inexistente",
        follow=True,
    )
    assert curvas.MENSAJE_BORRADOR_INVALIDO in otra.content.decode()


def test_ficha_enlaza_nueva_curva(cliente_catalogo, prueba_curva):
    html = cliente_catalogo.get(reverse("catalogo:ficha", args=[prueba_curva.pk])).content.decode()
    assert url_nueva(prueba_curva) in html


# --- US3: importar desde un archivo -----------------------------------------------------------


def archivo_csv(texto, nombre="curva.csv"):
    from django.core.files.uploadedfile import SimpleUploadedFile

    return SimpleUploadedFile(nombre, texto.encode("utf-8"), content_type="text/csv")


PLANTILLA_CSV = "Concentración;Absorbancia\n0;0,000\n0,1;0,052\n0,2;0,101\n0,3;0,153\n0,4;0,199\n"


def importar(cliente, prueba, archivo, filas=(("", ""),) * 3):
    datos = envio(list(filas), accion="importar")
    datos["archivo"] = archivo
    return cliente.post(url_nueva(prueba), datos)


def test_importar_carga_tabla(cliente_catalogo, prueba_curva):
    html = importar(cliente_catalogo, prueba_curva, archivo_csv(PLANTILLA_CSV)).content.decode()
    assert "Se leyeron 5 puntos de curva.csv. Revisalos antes de calcular." in html
    assert 'name="puntos-4-absorbancia"' in html
    assert 'value="0,199"' in html  # en la misma tabla, editable
    assert 'value="guardar"' not in html  # todavía hay que calcular
    assert not CurvaCalibracion.objects.exists()


def test_importar_error_no_cambia_tabla(cliente_catalogo, prueba_curva):
    escritas = [("1", "0,5"), ("2", "1,0"), ("3", "1,5")]
    roto = "Conc;Abs\n0;0\n0,1;0,05\n0,2;\n0,3;0,15\n"
    html = importar(cliente_catalogo, prueba_curva, archivo_csv(roto), escritas).content.decode()
    assert "La fila 4 no tiene absorbancia." in html
    assert 'value="1,5"' in html  # la tabla quedó como estaba
    assert 'name="puntos-3-concentracion"' not in html
    sin_archivo = cliente_catalogo.post(url_nueva(prueba_curva), envio(escritas, accion="importar"))
    assert "Elegí un archivo .csv o .xlsx." in sin_archivo.content.decode()


def test_importar_elegir_columnas(cliente_catalogo, prueba_curva):
    texto = "A;B;C\n1;0;0,000\n2;0,1;0,052\n3;0,2;0,101\n4;0,3;0,153\n5;0,4;0,199\n6;0,5;0,25\n"
    html = importar(cliente_catalogo, prueba_curva, archivo_csv(texto, "sin_titulos.csv"))
    html = html.content.decode()
    assert "Elegí las columnas" in html
    assert html.count("data-vista-previa-fila") == 5
    assert 'name="columna_concentracion"' in html and 'name="columna_absorbancia"' in html
    datos = envio([("", "")] * 3, accion="elegir_columnas")
    datos.update(columna_concentracion="1", columna_absorbancia="1")
    html = cliente_catalogo.post(url_nueva(prueba_curva), datos).content.decode()
    assert "Elegí dos columnas distintas." in html
    datos.update(columna_absorbancia="2")
    html = cliente_catalogo.post(url_nueva(prueba_curva), datos).content.decode()
    assert "Se leyeron 6 puntos de sin_titulos.csv." in html
    assert 'value="0,052"' in html


def test_plantilla(cliente_catalogo, prueba_curva):
    from pruebas import importacion_curvas

    respuesta = cliente_catalogo.get(reverse("catalogo:plantilla_curva"))
    assert respuesta.status_code == 200
    assert respuesta["Content-Type"].startswith("text/csv")
    assert "attachment" in respuesta["Content-Disposition"]
    assert respuesta.content.decode("utf-8") == importacion_curvas.plantilla()
    html = cliente_catalogo.get(url_nueva(prueba_curva)).content.decode()
    assert reverse("catalogo:plantilla_curva") in html
    importada = importar(
        cliente_catalogo, prueba_curva, archivo_csv(respuesta.content.decode("utf-8-sig"))
    )
    assert "Se leyeron 5 puntos" in importada.content.decode()


def test_archivo_origen(cliente_catalogo, prueba_curva):
    html = importar(
        cliente_catalogo, prueba_curva, archivo_csv(PLANTILLA_CSV, "no2_noviembre.csv")
    ).content.decode()
    firmado = re.search(r'name="archivo_origen" value="([^"]+)"', html).group(1)
    assert firmado != "no2_noviembre.csv"  # va firmado: no se puede cambiar a mano
    editados = REFERENCIA[:4] + [("0,4", "0,200")]  # se corrige un punto después de importar
    location = ir_a_confirmar(
        cliente_catalogo, prueba_curva, archivo_origen=firmado, **{"puntos-4-absorbancia": "0,200"}
    )
    resumen = cliente_catalogo.get(location).content.decode()
    assert "no2_noviembre.csv" in resumen
    cliente_catalogo.post(location, {"token": token(resumen), "accion": "confirmar"})
    curva = CurvaCalibracion.objects.get()
    assert curva.archivo_origen == "no2_noviembre.csv"
    assert str(curva.puntos.get(orden=5).absorbancia) == "0.200000"
    assert editados[-1] == ("0,4", "0,200")


def test_archivo_origen_alterado_se_descarta(cliente_catalogo, prueba_curva):
    location = ir_a_confirmar(cliente_catalogo, prueba_curva, archivo_origen="inventado.csv")
    assert "inventado.csv" not in cliente_catalogo.get(location).content.decode()


# --- US6: consulta y borrado ------------------------------------------------------------------


def test_consulta_listar(cliente_http, prueba_curva, curva_de, empleado):
    vieja = curva_de(prueba_curva, fecha=datetime.date(2026, 3, 1), r2="0.991")
    media = curva_de(prueba_curva, fecha=datetime.date(2026, 6, 1), r2="0.993")
    curva_de(prueba_curva, fecha=datetime.date(2026, 9, 1), r2="0.9996")
    CurvaCalibracion.objects.filter(pk=vieja.pk).update(usada=True)
    html = cliente_http.get(reverse("curvas:listar", args=[prueba_curva.pk])).content.decode()
    vigente, historicas = html.split("data-historicas")
    assert "01/09/2026" in vigente and "0,9996" in vigente
    assert historicas.index("01/06/2026") < historicas.index("01/03/2026")  # nueva → vieja
    assert "Usada en resultados" in historicas and "Sin usar" in historicas
    assert (empleado.get_full_name() or empleado.email) in historicas
    assert reverse("curvas:detalle", args=[media.pk]) in historicas


def test_consulta_sin_curva(cliente_http, prueba_curva):
    html = cliente_http.get(reverse("curvas:listar", args=[prueba_curva.pk])).content.decode()
    assert "Sin curva vigente." in html


def test_consulta_detalle(cliente_http, prueba_curva, curva_de):
    curva = curva_de(
        prueba_curva, r2="0.99", archivo_origen="no2.xlsx", fecha=datetime.date(2026, 11, 2)
    )
    CurvaCalibracion.objects.filter(pk=curva.pk).update(observacion="Lote 12")
    html = cliente_http.get(reverse("curvas:detalle", args=[curva.pk])).content.decode()
    for texto in (
        "0,5",
        "0,001",
        "0,99",
        "0 a 0,4 mg/l",
        "no2.xlsx",
        "Lote 12",
        "Vigente",
        "0,201",
        'id="datos-curva"',
        "R² menor que 0,995",
    ):
        assert texto in html, texto


def test_consulta_desde_estudio(cliente_http, prueba_curva, curva_de, estudio_de, empleado):
    from estudios.tests.utiles import cargar

    usada = curva_de(prueba_curva)
    estudio = estudio_de("NO2-C")
    cargar(estudio, empleado, {"NO2-C": "0.126"})
    curva_de(prueba_curva, pendiente="0.25", r2="0.99")  # la usada pasa a histórica
    html = cliente_http.get(reverse("estudios:detalle", args=[estudio.pk])).content.decode()
    enlace = reverse("curvas:detalle", args=[usada.pk])
    assert enlace in html
    detalle = cliente_http.get(enlace).content.decode()
    assert "Histórica" in detalle


def test_consulta_sin_opciones(cliente_http, prueba_curva, curva_de):
    curva = curva_de(prueba_curva)
    listado = cliente_http.get(reverse("curvas:listar", args=[prueba_curva.pk])).content.decode()
    detalle = cliente_http.get(reverse("curvas:detalle", args=[curva.pk])).content.decode()
    assert "Nueva curva" not in listado
    assert "Borrar curva" not in detalle


def test_ficha_enlaza_ver_curvas(cliente_catalogo, prueba_curva):
    html = cliente_catalogo.get(reverse("catalogo:ficha", args=[prueba_curva.pk])).content.decode()
    assert reverse("curvas:listar", args=[prueba_curva.pk]) in html


def test_borrar_curva_pantalla(cliente_catalogo, prueba_curva, curva_de):
    anterior = curva_de(prueba_curva, fecha=datetime.date(2026, 6, 1))
    curva = curva_de(prueba_curva)
    detalle = cliente_catalogo.get(reverse("curvas:detalle", args=[curva.pk])).content.decode()
    url = reverse("catalogo:borrar_curva", args=[curva.pk])
    assert url in detalle
    assert "Borrar curva" in cliente_catalogo.get(url).content.decode()
    respuesta = cliente_catalogo.post(url, {"accion": "confirmar"}, follow=True)
    assert respuesta.redirect_chain[-1][0] == reverse("curvas:listar", args=[prueba_curva.pk])
    assert "Curva borrada. Volvió a quedar vigente la del 01/06/2026." in respuesta.content.decode()
    anterior.refresh_from_db()
    assert anterior.vigente


def test_borrar_curva_usada_pantalla(cliente_catalogo, prueba_curva, curva_de):
    curva = curva_de(prueba_curva)
    CurvaCalibracion.objects.filter(pk=curva.pk).update(usada=True)
    detalle = cliente_catalogo.get(reverse("curvas:detalle", args=[curva.pk])).content.decode()
    assert "Borrar curva" not in detalle
    url = reverse("catalogo:borrar_curva", args=[curva.pk])
    respuesta = cliente_catalogo.get(url, follow=True)
    assert "Esta curva ya se usó en resultados: no se puede borrar." in respuesta.content.decode()
    cliente_catalogo.post(url, {"accion": "confirmar"})
    assert CurvaCalibracion.objects.filter(pk=curva.pk).exists()


# --- US7: solo quien gestiona el catálogo carga curvas ----------------------------------------


def usuario_de(django_user_model, quien):
    from django.contrib.auth.models import Group

    usuario = django_user_model.objects.create_user(
        email=f"{quien}@x.com", password="Clave-Valida-123", is_superuser=quien == "superusuario"
    )
    if quien == "bioquimico":
        usuario.groups.add(Group.objects.get_or_create(name="Bioquímicos")[0])
    return usuario


RUTAS_DE_CARGA = [
    ("catalogo:nueva_curva", "prueba", "GET", {}),
    ("catalogo:nueva_curva", "prueba", "POST", {"accion": "calcular"}),
    ("catalogo:nueva_curva", "prueba", "POST", {"accion": "guardar"}),
    ("catalogo:nueva_curva", "prueba", "POST", {"accion": "importar"}),
    ("catalogo:nueva_curva", "prueba", "POST", {"accion": "agregar_fila"}),
    ("catalogo:confirmar_curva", "prueba", "POST", {"accion": "confirmar", "token": "x"}),
    ("catalogo:plantilla_curva", None, "GET", {}),
    ("catalogo:borrar_curva", "curva", "GET", {}),
    ("catalogo:borrar_curva", "curva", "POST", {"accion": "confirmar"}),
]


@pytest.mark.parametrize("nombre, argumento, metodo, datos", RUTAS_DE_CARGA)
@pytest.mark.parametrize("quien", ["anonimo", "comun", "bioquimico", "superusuario"])
def test_acceso(django_user_model, prueba_curva, curva_de, nombre, argumento, metodo, datos, quien):
    from django.test import Client

    curva = curva_de(prueba_curva)
    args = {"prueba": [prueba_curva.pk], "curva": [curva.pk], None: []}[argumento]
    cliente = Client()
    if quien != "anonimo":
        cliente.force_login(usuario_de(django_user_model, quien))
    url = reverse(nombre, args=args)
    respuesta = cliente.get(url) if metodo == "GET" else cliente.post(url, envio(**datos))
    if quien == "anonimo":
        assert respuesta.status_code == 302 and "login" in respuesta["Location"]
    else:
        assert respuesta.status_code == 403
    assert list(CurvaCalibracion.objects.values_list("pk", flat=True)) == [curva.pk]


@pytest.mark.parametrize("quien", ["comun", "bioquimico"])
def test_acceso_consulta(django_user_model, prueba_curva, curva_de, quien):
    from django.test import Client

    curva = curva_de(prueba_curva)
    cliente = Client()
    cliente.force_login(usuario_de(django_user_model, quien))
    assert cliente.get(reverse("curvas:listar", args=[prueba_curva.pk])).status_code == 200
    assert cliente.get(reverse("curvas:detalle", args=[curva.pk])).status_code == 200
    anonimo = Client().get(reverse("curvas:detalle", args=[curva.pk]))
    assert anonimo.status_code == 302 and "login" in anonimo["Location"]


def test_acceso_administrador(cliente_catalogo, prueba_curva, curva_de):
    curva = curva_de(prueba_curva)
    assert cliente_catalogo.get(url_nueva(prueba_curva)).status_code == 200
    assert cliente_catalogo.get(reverse("catalogo:plantilla_curva")).status_code == 200
    borrar = reverse("catalogo:borrar_curva", args=[curva.pk])
    assert cliente_catalogo.get(borrar).status_code == 200


def test_servicio_revalida(empleado, prueba_curva, curva_de):
    import uuid

    from pruebas import gestion

    curva = curva_de(prueba_curva)
    with pytest.raises(gestion.NoAutorizado):
        curvas.guardar_curva(
            usuario=empleado, prueba_id=prueba_curva.pk, datos={}, clave=uuid.uuid4()
        )
    with pytest.raises(gestion.NoAutorizado):
        curvas.borrar_curva(usuario=empleado, curva_id=curva.pk)
    assert CurvaCalibracion.objects.count() == 1
