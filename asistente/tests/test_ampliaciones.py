"""Ampliaciones del asistente al cierre: resumen del laboratorio, informes y envíos en el detalle
de un estudio, listas con datos etiquetados, sugerencias como botones con «Ver …», y el
razonamiento interno del modelo fuera de la respuesta."""

import datetime
import json
import uuid

import pytest
from django.utils import timezone

from asistente import cliente_ia, conversacion, herramientas
from asistente.tests.conftest import ejecutar
from estudios.models import EstadoEstudio, Estudio, Validacion
from muestras.models import Muestra
from pruebas.limites import Evaluacion

pytestmark = pytest.mark.django_db


# --- Listas con datos etiquetados ---


def test_linea_de_muestra_y_de_estudio_con_etiquetas(estudio_completo):
    muestra = estudio_completo.muestra
    linea = herramientas.linea_muestra(muestra.nombre, muestra.origen.nombre, muestra.numero_pi)
    assert linea == (
        f"«{muestra.nombre}»\n  Origen: {muestra.origen.nombre}\n  N° PI {muestra.numero_pi}"
    )
    linea = herramientas.linea_estudio(
        estudio_completo.pk,
        estudio_completo.tipo_nombre_snapshot,
        estudio_completo.get_estado_display(),
        muestra,
    )
    assert linea.splitlines() == [
        f"Estudio N° {estudio_completo.pk}, {estudio_completo.tipo_nombre_snapshot}",
        f"  Estado: {estudio_completo.get_estado_display()}",
        f"  Muestra: «{muestra.nombre}» (origen: {muestra.origen.nombre})",
    ]
    assert str(muestra.numero_pi) not in linea


def test_buscar_muestra_por_cliente_trae_la_linea(empleado, lacteos):
    resultado = ejecutar(empleado, "buscar_muestra", texto="Lácteos del Sur")
    muestras = resultado.salida["datos"]["muestras"]
    assert muestras
    assert all(m["linea"].startswith(f"«{m['nombre']}»") for m in muestras)


def test_estudios_de_cliente_traen_la_linea(empleado, lacteos):
    resultado = ejecutar(empleado, "estudios_de_cliente", cliente="Lácteos del Sur")
    estudios = resultado.salida["datos"]["estudios"]
    assert estudios
    assert all(e["linea"].startswith(f"Estudio N° {e['numero']},") for e in estudios)


# --- Sugerencias: botón con la pregunta y «Ver …» al lado ---


def test_referencias_son_sugerencias_con_ver(estudio_completo, empleado):
    muestra = estudio_completo.muestra
    enlace = herramientas.referencia_muestra(muestra).enlace()
    assert enlace["etiqueta"] == f"¿Cómo está «{muestra.nombre}»?"
    assert enlace["pregunta"] == f"¿Cómo está el PI {muestra.numero_pi}?"
    assert enlace["ver"] == "Ver muestra"
    assert enlace["url"] == f"/muestras/{muestra.pk}/"

    enlace = herramientas.referencia_estudio(estudio_completo).enlace()
    assert enlace["pregunta"] == f"¿Cómo está el estudio N° {estudio_completo.pk}?"
    assert enlace["ver"] == "Ver estudio"

    [cliente] = herramientas.referencia_cliente(empleado, muestra.cliente)
    enlace = cliente.enlace()
    assert enlace["etiqueta"] == enlace["pregunta"]
    assert enlace["pregunta"] == f"¿Qué estudios tiene {muestra.cliente.nombre_completo}?"
    assert enlace["ver"] == "Ver cliente"


def test_sin_herramientas_sugiere_preguntas_como_botones(servicio_simulado):
    respuesta = conversacion.responder(
        None, "Borrá el estudio 31", [], reloj=servicio_simulado.reloj
    )
    assert respuesta.texto.endswith("Probá con alguna de estas preguntas:")
    assert [e["pregunta"] for e in respuesta.enlaces] == list(conversacion.EJEMPLOS)
    assert all(e["etiqueta"] == e["pregunta"] and "url" not in e for e in respuesta.enlaces)


# --- Informe y envíos por correo en el detalle del estudio ---


@pytest.fixture
def estudio_informado(estudio_de, empleado, bioquimico):
    from estudios.tests.utiles import cargar, validar
    from informes.models import EnvioInforme, ResultadoEnvio
    from informes.servicios import emitir_informe

    estudio = estudio_de("PH")
    cargar(estudio, empleado, {"PH": "7.2"})
    validar(estudio, bioquimico, "PH")
    informe = emitir_informe(estudio.pk, bioquimico)
    for resultado in (ResultadoEnvio.FALLIDO, ResultadoEnvio.ENVIADO):
        EnvioInforme.objects.create(
            informe=informe,
            enviado_por=bioquimico,
            destinatario="calidad@cliente.test",
            resultado=resultado,
            clave=uuid.uuid4(),
        )
    estudio.refresh_from_db()
    return estudio


def test_detalle_estudio_con_informe_y_envios_sin_la_direccion(empleado, estudio_informado):
    resultado = ejecutar(empleado, "detalle_estudio", numero=estudio_informado.pk)
    informe = resultado.salida["datos"]["informe"]
    assert informe["numero"] == estudio_informado.informe.numero_mostrado
    assert informe["emitido_por"] == estudio_informado.informe.emitido_por.get_full_name()
    assert informe["total_envios"] == 2
    assert {e["resultado"] for e in informe["envios_por_correo"]} == {"Enviado", "Falló"}
    assert "calidad@cliente.test" not in json.dumps(resultado.salida, ensure_ascii=False)


def test_detalle_estudio_sin_informe(empleado, estudio_completo):
    resultado = ejecutar(empleado, "detalle_estudio", numero=estudio_completo.pk)
    assert resultado.salida["datos"]["informe"] is None


# --- Resumen del laboratorio ---


def test_resumen_sin_fechas_cuenta_todo_el_historial(empleado, estudio_completo, escuela):
    resultado = ejecutar(empleado, "resumen_laboratorio")
    datos = resultado.salida["datos"]
    assert datos["periodo"] == "todo el historial"
    assert datos["muestras_ingresadas"] == Muestra.objects.count()
    assert datos["estudios"] == Estudio.objects.count()
    assert sum(datos["estudios_por_estado"].values()) == Estudio.objects.count()
    assert set(datos["estudios_por_estado"]) == {e.label for e in EstadoEstudio}
    fuera = Validacion.objects.filter(anulada=False, evaluacion=Evaluacion.FUERA_DE_NORMA)
    assert datos["resultados_fuera_de_norma"] == fuera.count() > 0
    ranking = datos["clientes_con_mas_muestras"]
    assert ranking[0]["muestras"] == max(c["muestras"] for c in ranking)
    assert resultado.referencias == []


def test_resumen_con_periodo_futuro_da_cero(empleado, estudio_completo):
    manana = timezone.localdate() + datetime.timedelta(days=1)
    pasado = manana + datetime.timedelta(days=1)
    resultado = ejecutar(
        empleado,
        "resumen_laboratorio",
        desde=manana.strftime("%d/%m/%Y"),
        hasta=pasado.strftime("%d/%m/%Y"),
    )
    datos = resultado.salida["datos"]
    assert datos["periodo"]["desde"] == manana.strftime("%d/%m/%Y")
    assert datos["muestras_ingresadas"] == 0
    assert datos["clientes_con_mas_muestras"] == []


def test_resumen_con_fecha_ilegible(empleado):
    resultado = ejecutar(empleado, "resumen_laboratorio", desde="el día del arquero")
    assert resultado.salida["encontrado"] is False


def test_resumen_esta_entre_las_herramientas():
    nombres = [d["function"]["name"] for d in herramientas.definiciones()]
    assert "resumen_laboratorio" in nombres


# --- El razonamiento interno del modelo no llega a la respuesta ---

RAZONAMIENTO = (
    "The answer: need to respond with client with most samples. According to data, Lácteos "
    "del Sur S.A. with 19 muestras. Must format as per rules. Probably just answer."
)


def test_detecta_el_razonamiento_y_no_una_respuesta_normal():
    assert cliente_ia.parece_razonamiento(RAZONAMIENTO)
    assert not cliente_ia.parece_razonamiento(
        "Lácteos del Sur S.A. es el cliente con más muestras: tiene 19."
    )


def test_si_se_cuela_el_razonamiento_pide_la_respuesta_otra_vez(monkeypatch, config_asistente):
    pedidos = []
    respuestas = [{"content": RAZONAMIENTO}, {"content": "Lácteos del Sur S.A. tiene 19."}]

    def falso(mensajes, herramientas_, timeout, config=None):
        pedidos.append(mensajes)
        return respuestas.pop(0)

    monkeypatch.setattr(cliente_ia, "_enviar", falso)
    mensaje = cliente_ia.enviar([{"role": "user", "content": "¿Quién tiene más?"}], [], 5)
    assert mensaje["content"] == "Lácteos del Sur S.A. tiene 19."
    assert len(pedidos) == 2
    assert pedidos[1][-1]["role"] == "system"


def test_con_herramientas_no_se_reintenta(monkeypatch, config_asistente):
    llamadas = []

    def falso(mensajes, herramientas_, timeout, config=None):
        llamadas.append(1)
        return {"content": RAZONAMIENTO, "tool_calls": [{"id": "x"}]}

    monkeypatch.setattr(cliente_ia, "_enviar", falso)
    cliente_ia.enviar([{"role": "user", "content": "hola"}], [], 5)
    assert len(llamadas) == 1


@pytest.mark.parametrize("modelo, con_parametros", [("openai/gpt-oss-120b", True), ("otro", False)])
def test_gpt_oss_pide_el_razonamiento_aparte(monkeypatch, settings, modelo, con_parametros):
    settings.ASISTENTE = {"clave": "clave-test", "url": "https://ia.test/v1", "modelo": modelo}
    enviados = []

    class Respuesta:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return json.dumps({"choices": [{"message": {"content": "Hola."}}]}).encode()

    def abrir(pedido, timeout):
        enviados.append(json.loads(pedido.data))
        return Respuesta()

    monkeypatch.setattr(cliente_ia.urllib.request, "urlopen", abrir)
    assert cliente_ia.enviar([{"role": "user", "content": "hola"}], [], 5)["content"] == "Hola."
    assert ("include_reasoning" in enviados[0]) is con_parametros
    if con_parametros:
        assert enviados[0]["include_reasoning"] is False
        assert enviados[0]["reasoning_effort"] == "low"


# --- Instrucciones del asistente ---


def test_instrucciones_del_cierre():
    sistema = conversacion.MENSAJE_SISTEMA
    assert "resumen_laboratorio" in sistema
    assert "va más allá de lo que puedo consultar" in sistema
    assert "«linea»" in sistema
    assert "buscar_muestra con el nombre del cliente" in sistema


def test_opciones_con_el_mismo_nombre_suman_la_fecha():
    from asistente.enlaces import Referencia, elegir_enlaces

    def ref(pk, fecha):
        return Referencia(
            "muestra",
            pk,
            f"Salida de la bomba · N° PI {pk}",
            pregunta=f"¿Cómo está el PI {pk}?",
            boton="¿Cómo está «Salida de la bomba»?",
            ver="Ver muestra",
            boton_distinto=f"¿Cómo está «Salida de la bomba» del {fecha}?",
        )

    unica = Referencia(
        "muestra",
        9,
        "Canilla del patio · N° PI 9",
        pregunta="¿Cómo está el PI 9?",
        boton="¿Cómo está «Canilla del patio»?",
        boton_distinto="¿Cómo está «Canilla del patio» del 01/01/2026?",
    )
    enlaces = elegir_enlaces(
        "", [], [], opciones=[ref(1, "06/10/2026"), ref(2, "06/11/2026"), unica]
    )
    assert [e["etiqueta"] for e in enlaces] == [
        "¿Cómo está «Salida de la bomba» del 06/10/2026?",
        "¿Cómo está «Salida de la bomba» del 06/11/2026?",
        "¿Cómo está «Canilla del patio»?",
    ]
