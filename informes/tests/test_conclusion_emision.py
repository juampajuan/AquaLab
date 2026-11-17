from copy import deepcopy
from decimal import Decimal
from hashlib import sha256
from html.parser import HTMLParser
from pathlib import Path
from uuid import uuid4

import pytest
from django.contrib.auth.models import Group
from django.core import mail
from django.db import connection
from django.template import engines
from django.template.loader import render_to_string
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django.utils import timezone

from estudios.servicios import corregir_mediciones
from estudios.tests.utiles import validar
from informes import conclusion_hechos, conclusion_ia, conclusiones, envios, pdf
from informes.models import BorradorConclusion, Informe, ResultadoEnvio
from informes.servicios import emitir_informe
from pruebas.models import Prueba

pytestmark = pytest.mark.django_db


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


def emitir(estudio, usuario, estado):
    return emitir_informe(
        estudio.pk, usuario, incluir_conclusion=True, revision_conclusion=estado["revision"]
    )


def test_emite_texto_reescrito_aprobado(conclusion_propuesta, bioquimico):
    estudio, estado = conclusion_propuesta
    guardado = guardar(estudio, bioquimico, estado, "Conclusión profesional revisada")
    aprobado = aprobar(estudio, bioquimico, guardado)
    informe = emitir(estudio, bioquimico, aprobado)
    assert informe.contenido["conclusion"]["texto"] == guardado["texto_final"]


@pytest.mark.parametrize("caso", ["sin_fila", "borrador", "editado", "invalidado"])
def test_emitir_sin_conclusion(conclusion_estudio, bioquimico, caso):
    estudio = conclusion_estudio()
    if caso != "sin_fila":
        estado = conclusiones.proponer_conclusion(
            estudio.pk,
            bioquimico,
            0,
            conclusion_hechos.huella(conclusion_hechos.recolectar(estudio)),
        )
        if caso == "invalidado":
            estado = aprobar(estudio, bioquimico, estado)
        if caso in ("editado", "invalidado"):
            guardar(estudio, bioquimico, estado, "Texto no aprobado")
    informe = emitir_informe(estudio.pk, bioquimico)
    assert "conclusion" not in informe.contenido


def cambiar_fuentes(estudio, bioquimico):
    asignacion = estudio.pruebas_asignadas.select_related("medicion").get(prueba__codigo="PH")
    resultado = corregir_mediciones(
        estudio.pk,
        {asignacion.pk: (asignacion.medicion.valor_ingresado, Decimal("7.4"))},
        bioquimico,
    )
    assert len(resultado.corregidas) == 1
    validar(estudio, bioquimico, "PH")


def test_cambio_fuentes_impide_conclusion_obsoleta(conclusion_propuesta, bioquimico):
    estudio, estado = conclusion_propuesta
    aprobado = aprobar(estudio, bioquimico, estado)
    cambiar_fuentes(estudio, bioquimico)
    with pytest.raises(conclusiones.ConflictoConclusion):
        emitir(estudio, bioquimico, aprobado)
    assert BorradorConclusion.objects.get(estudio=estudio).aprobada_por_id is None
    assert "conclusion" not in emitir_informe(estudio.pk, bioquimico).contenido


def test_reaprobacion_explicita_fuentes_actuales(conclusion_propuesta, bioquimico):
    estudio, estado = conclusion_propuesta
    aprobado = aprobar(estudio, bioquimico, estado)
    cambiar_fuentes(estudio, bioquimico)
    with pytest.raises(conclusiones.ConflictoConclusion):
        aprobar(estudio, bioquimico, aprobado)
    actual = conclusiones.estado_borrador(BorradorConclusion.objects.get(estudio=estudio))
    revisado = guardar(estudio, bioquimico, actual, "Texto revisado contra las fuentes actuales")
    nuevo = aprobar(estudio, bioquimico, revisado)
    assert (
        emitir(estudio, bioquimico, nuevo).contenido["conclusion"]["texto"]
        == revisado["texto_final"]
    )


def test_editar_aprobar_parcial_conserva_advertencias(conclusion_estudio, bioquimico):
    estudio = conclusion_estudio(sin_norma=("PH",))
    estado = conclusiones.proponer_conclusion(
        estudio.pk, bioquimico, 0, conclusion_hechos.huella(conclusion_hechos.recolectar(estudio))
    )
    revisado = guardar(estudio, bioquimico, estado, "Conclusión parcial revisada")
    aprobado = aprobar(estudio, bioquimico, revisado)
    texto = emitir(estudio, bioquimico, aprobado).contenido["conclusion"]["texto"]
    assert "PH" in texto and "sin norma" in texto
    assert texto == revisado["texto_final"]


class TextoConclusion(HTMLParser):
    """Oráculo HTML sin normalizar espacios ni desescapar entidades dos veces."""

    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.textos = []
        self.profundidad = 0
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        if self.profundidad:
            self.profundidad += 1
        elif "data-conclusion-texto-informe" in dict(attrs):
            self.profundidad = 1
            self.textos.append("")

    def handle_endtag(self, tag):
        if self.profundidad:
            self.profundidad -= 1

    def handle_data(self, data):
        if self.profundidad:
            self.textos[-1] += data


def emitir_texto(estudio, usuario, estado, texto):
    revisado = guardar(estudio, usuario, estado, texto)
    return emitir(estudio, usuario, aprobar(estudio, usuario, revisado))


def comprobar_escalares_texto(valor):
    if isinstance(valor, dict):
        for item in valor.values():
            comprobar_escalares_texto(item)
    elif isinstance(valor, list):
        for item in valor:
            comprobar_escalares_texto(item)
    else:
        assert isinstance(valor, str)


@pytest.mark.parametrize("ausencia", [None, "sin_norma", "sin_limite", "sin_validacion"])
def test_snapshot_texto_y_trazabilidad(conclusion_estudio, bioquimico, ausencia):
    opciones = {ausencia: ("PH",)} if ausencia in ("sin_norma", "sin_limite") else {}
    estudio = conclusion_estudio(**opciones)
    if ausencia == "sin_validacion":
        # Anomalía persistida sin eliminar la restricción de unicidad de vigente.
        estudio.pruebas_asignadas.get(prueba__codigo="PH").validaciones.filter(
            anulada=False
        ).update(anulada=True, fecha_anulacion=timezone.now())
    hechos = conclusion_hechos.recolectar(estudio)
    estado = conclusiones.proponer_conclusion(
        estudio.pk, bioquimico, 0, conclusion_hechos.huella(hechos)
    )
    aprobado = aprobar(estudio, bioquimico, estado)
    copia = emitir(estudio, bioquimico, aprobado).contenido["conclusion"]
    comprobar_escalares_texto(copia)
    assert copia["hechos"] == hechos
    assert copia["hechos"]["estudio_id"] == str(estudio.pk)
    assert copia["revision"] == str(aprobado["revision"])
    assert copia["huella_hechos"] == conclusion_hechos.huella(hechos)
    assert copia["huella_texto"] == sha256(copia["texto"].encode()).hexdigest()
    assert copia["aprobacion"]["aprobador_id"] == str(bioquimico.pk)
    assert copia["aprobacion"]["fecha"]
    for fila in copia["hechos"]["pruebas"]:
        asignacion = estudio.pruebas_asignadas.get(pk=fila["asignacion_id"])
        assert fila["prueba_id"] == str(asignacion.prueba_id)
        assert fila["resultado_id"] == str(asignacion.resultado.pk)
        vigente = (
            asignacion.validaciones.filter(anulada=False).get() if fila["validacion_id"] else None
        )
        if vigente:
            assert fila["validacion_id"] == str(vigente.pk)
            assert fila["norma"] == vigente.norma
        else:
            assert ausencia == "sin_validacion" and fila["codigo"] == "PH"
            assert fila["validacion_id"] == fila["norma"] == fila["limite_min"] == ""
    if ausencia:
        assert copia["advertencias"]


def test_snapshot_no_cambia_con_origen(conclusion_propuesta, bioquimico):
    estudio, estado = conclusion_propuesta
    informe = emitir(estudio, bioquimico, aprobar(estudio, bioquimico, estado))
    original = deepcopy(informe.contenido)
    Prueba.objects.filter(pk__in=estudio.pruebas_asignadas.values("prueba_id")).update(
        nombre="Nombre posterior", norma="Norma posterior", limite_max="99"
    )
    bioquimico.first_name = "Nombre posterior"
    bioquimico.save(update_fields=["first_name"])
    bioquimico.firma_profesional.matricula = "MP posterior"
    bioquimico.firma_profesional.save()
    informe.refresh_from_db()
    assert informe.contenido == original
    html = render_to_string(
        "informes/documento.html", {"contenido": informe.contenido, "informe": informe}
    )
    assert TextoConclusion(html).textos == [original["conclusion"]["texto"]]


def texto_pdf(documento):
    # Se inspecciona el árbol de maquetación real, sin instalar un parser de PDF.
    return " ".join(
        caja.text
        for pagina in documento.pages
        for caja in pagina._page_box.descendants()
        if hasattr(caja, "text")
        and caja.element is not None
        and "data-conclusion-texto-informe" in caja.element.attrib
    )


def test_misma_conclusion_todos_los_medios(
    conclusion_propuesta, bioquimico, cliente_bioquimico, monkeypatch
):
    estudio, estado = conclusion_propuesta
    texto = "Conclusión sintética: pH 9,2.\nCloruro > límite; norma y revisión profesional."
    informe = emitir_texto(estudio, bioquimico, estado, texto)
    for ruta in ("ver", "imprimir"):
        respuesta = cliente_bioquimico.get(reverse(f"informes:{ruta}", args=[estudio.pk]))
        assert respuesta.status_code == 200
        assert TextoConclusion(respuesta.content.decode()).textos == [texto]
    html_pdf = []
    render_original = pdf.render_to_string

    def render(*args, **kwargs):
        html = render_original(*args, **kwargs)
        html_pdf.append(html)
        return html

    monkeypatch.setattr(pdf, "render_to_string", render)
    documento = pdf.documento(informe)
    assert TextoConclusion(html_pdf[-1]).textos == [texto]
    assert " ".join(texto_pdf(documento).split()) == " ".join(texto.split())
    assert documento.write_pdf().startswith(b"%PDF-")
    respuesta = cliente_bioquimico.get(reverse("informes:pdf", args=[estudio.pk]))
    assert respuesta.status_code == 200 and respuesta.content.startswith(b"%PDF-")
    adjuntos = []
    generar_original = envios.generar_pdf

    def generar(copia):
        assert copia.contenido == informe.contenido
        generado = generar_original(copia)
        adjuntos.append(generado)
        return generado

    monkeypatch.setattr(envios, "generar_pdf", generar)
    resultado = envios.enviar_informe(estudio.pk, bioquimico, uuid4())
    assert resultado.envio.resultado == ResultadoEnvio.ENVIADO
    mensaje = mail.outbox[-1]
    assert mensaje.body.count(texto) == 1
    assert TextoConclusion(mensaje.alternatives[0][0]).textos == [texto]
    assert mensaje.attachments[0][1] == adjuntos[0]
    assert adjuntos[0].startswith(b"%PDF-")


def test_salidas_y_reenvio_no_llaman_ia(
    conclusion_propuesta, bioquimico, cliente_bioquimico, monkeypatch, mailoutbox
):
    from asistente import cliente_ia

    estudio, estado = conclusion_propuesta
    informe = emitir(estudio, bioquimico, aprobar(estudio, bioquimico, estado))
    original = deepcopy(informe.contenido)

    def prohibido(*args, **kwargs):
        pytest.fail("Una salida de un informe emitido invocó IA o fuentes vivas")

    monkeypatch.setattr(conclusion_ia, "proponer", prohibido)
    monkeypatch.setattr(cliente_ia, "enviar", prohibido)
    monkeypatch.setattr(conclusion_hechos, "recolectar", prohibido)
    for ruta in ("ver", "imprimir", "pdf", "enviar"):
        assert (
            cliente_bioquimico.get(reverse(f"informes:{ruta}", args=[estudio.pk])).status_code
            == 200
        )
    assert not mailoutbox  # GET confirma; no envía.
    cliente = estudio.muestra.cliente
    cliente.email = "destino-actual@ejemplo.com"
    cliente.save(update_fields=["email"])
    clave = uuid4()
    primero = envios.enviar_informe(estudio.pk, bioquimico, clave)
    repetido = envios.enviar_informe(estudio.pk, bioquimico, clave)
    reenvio = envios.enviar_informe(estudio.pk, bioquimico, uuid4())
    assert primero.envio.resultado == reenvio.envio.resultado == ResultadoEnvio.ENVIADO
    assert repetido.duplicado and repetido.envio.pk == primero.envio.pk
    assert len(mail.outbox) == 2
    for mensaje in mail.outbox:
        assert mensaje.to == [cliente.email]
        assert mensaje.body.count(original["conclusion"]["texto"]) == 1
    informe.refresh_from_db()
    assert informe.contenido == original


def test_historicos_sin_conclusion_intactos(conclusion_estudio, bioquimico, cliente_bioquimico):
    estudio = conclusion_estudio()
    informe = emitir_informe(estudio.pk, bioquimico)
    original = deepcopy(informe.contenido)
    assert "conclusion" not in original
    contexto = {"informe": informe, "contenido": original, "numero": informe.numero_mostrado}
    referencias = Path(__file__).parent / "fixtures" / "us102_historicos"
    for nombre in (
        "documento.html",
        "documento_impreso.html",
        "correos/informe_cuerpo.txt",
        "correos/informe_cuerpo.html",
    ):
        anterior = (
            engines["django"]
            .from_string((referencias / nombre).read_text(encoding="utf-8"))
            .render(contexto)
        )
        actual = render_to_string(f"informes/{nombre}", contexto)
        assert actual == anterior
        assert "data-conclusion" not in actual
    with CaptureQueriesContext(connection) as consultas:
        for ruta in ("ver", "imprimir", "pdf"):
            assert (
                cliente_bioquimico.get(reverse(f"informes:{ruta}", args=[estudio.pk])).status_code
                == 200
            )
    assert not any(
        q["sql"].lstrip().upper().startswith(("UPDATE", "INSERT", "DELETE"))
        and '"informes_informe"' in q["sql"]
        for q in consultas
    )
    informe.refresh_from_db()
    assert informe.contenido == original
    assert not BorradorConclusion.objects.filter(estudio=estudio).exists()


def test_emitido_rechaza_mutar_conclusion(conclusion_propuesta, bioquimico, cliente_bioquimico):
    estudio, estado = conclusion_propuesta
    aprobado = aprobar(estudio, bioquimico, estado)
    informe = emitir(estudio, bioquimico, aprobado)
    original = deepcopy(informe.contenido)
    datos = {
        "revision_esperada": aprobado["revision"],
        "huella_hechos_vista": aprobado["huella_hechos"],
        "huella_texto_visto": aprobado["huella_texto"],
        "texto": "Intento posterior",
        "confirmacion": True,
    }
    for accion in ("proponer", "guardar", "aprobar"):
        respuesta = cliente_bioquimico.post(
            reverse(f"informes:conclusion_{accion}", args=[estudio.pk]),
            datos,
            content_type="application/json",
        )
        assert respuesta.status_code == 409
    informe.contenido["conclusion"]["texto"] = "Intento posterior"
    with pytest.raises(ValueError, match="no se puede modificar"):
        informe.save()
    with pytest.raises(ValueError, match="no se puede borrar"):
        informe.delete()
    informe.refresh_from_db()
    assert informe.contenido == original
    assert Informe.objects.filter(estudio=estudio).count() == 1


def test_otro_bioquimico_emite(conclusion_propuesta, bioquimico, django_user_model, firma_de):
    estudio, estado = conclusion_propuesta
    aprobado = aprobar(estudio, bioquimico, estado)
    nombre_original = bioquimico.get_full_name() or bioquimico.email
    otro = django_user_model.objects.create_user(email="otro-bio@ejemplo.com", is_active=True)
    otro.groups.add(Group.objects.get(name="Bioquímicos"))
    firma_de(otro)
    informe = emitir(estudio, otro, aprobado)
    assert informe.emitido_por_id == otro.pk != bioquimico.pk
    assert informe.contenido["conclusion"]["aprobacion"]["aprobador_id"] == str(bioquimico.pk)
    assert informe.contenido["conclusion"]["aprobacion"]["nombre"] == nombre_original


@pytest.mark.parametrize("aprobada", [False, True])
def test_previa_separa_editor_de_copia_emitida(
    conclusion_propuesta, bioquimico, cliente_bioquimico, aprobada
):
    estudio, estado = conclusion_propuesta
    if aprobada:
        aprobar(estudio, bioquimico, estado)
    respuesta = cliente_bioquimico.get(reverse("informes:vista_previa", args=[estudio.pk]))
    assert respuesta.status_code == 200
    assert TextoConclusion(respuesta.content.decode()).textos == []
    assert not Informe.objects.filter(estudio=estudio).exists()


@pytest.mark.parametrize("extenso", [False, True])
def test_escaping_unicode_lf_advertencias_y_pdf_real(
    conclusion_estudio, bioquimico, extenso, monkeypatch
):
    estudio = conclusion_estudio(sin_norma=("PH",))
    estado = conclusiones.proponer_conclusion(
        estudio.pk, bioquimico, 0, conclusion_hechos.huella(conclusion_hechos.recolectar(estudio))
    )
    texto = 'Ácido ≤ límite & revisión <script>alert("sintético")</script>\n\nSegunda línea &lt;'
    if extenso:
        texto += "\n" + "\n".join(f"Línea {i}: revisión profesional sintética." for i in range(160))
        texto += "\n" + "x" * 400 + "\nFIN-CONCLUSION"
    informe = emitir_texto(estudio, bioquimico, estado, texto)
    final = informe.contenido["conclusion"]["texto"]
    assert final.startswith(texto)
    assert final.count("Advertencias de información insuficiente:") == 1
    contexto = {"contenido": informe.contenido, "informe": informe}
    for nombre in ("documento.html", "documento_impreso.html", "correos/informe_cuerpo.html"):
        html = render_to_string(f"informes/{nombre}", contexto)
        assert TextoConclusion(html).textos == [final]
        assert "<script>" not in html
        assert "&lt;script&gt;" in html and "&amp;lt;" in html
    render_original = pdf.render_to_string

    def render(*args, **kwargs):
        html = render_original(*args, **kwargs)
        assert TextoConclusion(html).textos == [final]
        return html

    monkeypatch.setattr(pdf, "render_to_string", render)
    mensaje = envios.mensaje_de_correo(informe, "sintetico@ejemplo.com", pdf.generar_pdf(informe))
    assert mensaje.body.count(final) == 1
    assert mensaje.attachments[0][1].startswith(b"%PDF-")
    documento = pdf.documento(informe)
    # Los saltos de maquetación pueden partir incluso una palabra muy larga.
    # HTML y TXT se comparan arriba sin eliminar ni normalizar ningún carácter.
    assert "".join(texto_pdf(documento).split()) == "".join(final.split())
    if extenso:
        assert len(documento.pages) > 1
        assert "FIN-CONCLUSION" in texto_pdf(documento)
    for pagina in documento.pages:
        for caja in pagina._page_box.descendants():
            if (
                hasattr(caja, "text")
                and caja.element is not None
                and "data-conclusion-texto-informe" in caja.element.attrib
            ):
                assert caja.position_x >= 0
                assert caja.position_x + caja.width <= pagina.width + 1
