import threading
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from decimal import Decimal

import pytest
from django.db import DatabaseError, close_old_connections, connection, connections, transaction
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from estudios.models import EstadoEstudio, Estudio
from estudios.servicios import CorregirMedicionesError, corregir_mediciones
from estudios.tests.utiles import validar
from informes import conclusion_ia, conclusiones
from informes.models import BorradorConclusion, Informe
from informes.servicios import InformeNoDisponible, emitir_informe
from pruebas.models import Prueba

pytestmark = pytest.mark.django_db(transaction=True)


def test_dos_guardados_no_se_pisan(conclusion_propuesta, bioquimico):
    assert connection.vendor == "postgresql"
    estudio, estado = conclusion_propuesta
    inicio = threading.Barrier(2)

    def escribir(texto):
        close_old_connections()
        try:
            inicio.wait(timeout=10)
            try:
                return conclusiones.guardar_borrador(
                    estudio.pk, bioquimico, estado["revision"], estado["huella_hechos"], texto
                )
            except conclusiones.ConflictoConclusion:
                return "conflicto"
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        futuros = [pool.submit(escribir, texto) for texto in ("Edición A", "Edición B")]
        resultados = [f.result(timeout=15) for f in futuros]
    assert resultados.count("conflicto") == 1
    assert BorradorConclusion.objects.get(estudio=estudio).texto_editorial in (
        "Edición A",
        "Edición B",
    )


def test_respuesta_ia_tardia_no_pisa_edicion(conclusion_propuesta, bioquimico, monkeypatch):
    estudio, estado = conclusion_propuesta
    empezado, continuar = threading.Event(), threading.Event()

    def redactar(hechos):
        assert not connection.in_atomic_block
        empezado.set()
        assert continuar.wait(timeout=10)
        return conclusion_ia.Propuesta("Respuesta antigua", "ia")

    monkeypatch.setattr(conclusion_ia, "proponer", redactar)

    def pedir():
        close_old_connections()
        try:
            return conclusiones.proponer_conclusion(
                estudio.pk, bioquimico, estado["revision"], estado["huella_hechos"]
            )
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=1) as pool:
        futuro = pool.submit(pedir)
        try:
            assert empezado.wait(timeout=10)
            actual = conclusiones.estado_borrador(BorradorConclusion.objects.get(estudio=estudio))
            guardado = conclusiones.guardar_borrador(
                estudio.pk,
                bioquimico,
                actual["revision"],
                actual["huella_hechos"],
                "Edición posterior",
            )
        finally:
            continuar.set()
        with pytest.raises(conclusiones.ConflictoConclusion):
            futuro.result(timeout=15)
    borrador = BorradorConclusion.objects.get(estudio=estudio)
    assert borrador.texto_editorial == guardado["texto_editorial"] == "Edición posterior"
    assert borrador.aprobada_por_id is None


def test_dos_aprobaciones_solo_una_version(conclusion_propuesta, bioquimico):
    estudio, estado = conclusion_propuesta
    inicio = threading.Barrier(2)

    def aprobar():
        close_old_connections()
        try:
            inicio.wait(timeout=10)
            try:
                return conclusiones.aprobar_conclusion(
                    estudio.pk,
                    bioquimico,
                    estado["revision"],
                    estado["huella_hechos"],
                    estado["huella_texto"],
                    confirmacion=True,
                )
            except conclusiones.ConflictoConclusion:
                return "conflicto"
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        futuros = [pool.submit(aprobar) for _ in range(2)]
        resultados = [f.result(timeout=15) for f in futuros]
    assert resultados.count("conflicto") == 1
    assert (
        BorradorConclusion.objects.get(estudio=estudio).revision_aprobada == estado["revision"] + 1
    )


def test_dos_propuestas_fuera_de_orden(conclusion_propuesta, bioquimico, monkeypatch):
    estudio, estado = conclusion_propuesta
    empezado, continuar = threading.Event(), threading.Event()

    def redactar(hechos):
        if not empezado.is_set():
            empezado.set()
            assert continuar.wait(timeout=10)
            return conclusion_ia.Propuesta("Propuesta anterior", "ia")
        return conclusion_ia.Propuesta("Propuesta posterior", "ia")

    monkeypatch.setattr(conclusion_ia, "proponer", redactar)

    def pedir():
        close_old_connections()
        try:
            return conclusiones.proponer_conclusion(
                estudio.pk, bioquimico, estado["revision"], estado["huella_hechos"]
            )
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=1) as pool:
        primero = pool.submit(pedir)
        try:
            assert empezado.wait(timeout=10)
            actual = conclusiones.estado_borrador(BorradorConclusion.objects.get(estudio=estudio))
            posterior = conclusiones.proponer_conclusion(
                estudio.pk, bioquimico, actual["revision"], actual["huella_hechos"]
            )
        finally:
            continuar.set()
        with pytest.raises(conclusiones.ConflictoConclusion):
            primero.result(timeout=15)
    assert (
        BorradorConclusion.objects.get(estudio=estudio).texto_editorial
        == posterior["texto_editorial"]
    )


def test_interrupcion_tras_reserva_conserva_borrador(conclusion_propuesta, bioquimico, monkeypatch):
    estudio, estado = conclusion_propuesta

    def interrumpir(hechos):
        raise RuntimeError("Interrupción controlada del proceso")

    monkeypatch.setattr(conclusion_ia, "proponer", interrumpir)
    with pytest.raises(RuntimeError):
        conclusiones.proponer_conclusion(
            estudio.pk, bioquimico, estado["revision"], estado["huella_hechos"]
        )
    borrador = BorradorConclusion.objects.get(estudio=estudio)
    assert borrador.texto_editorial == estado["texto_editorial"]
    assert borrador.solicitud_propuesta is not None
    assert borrador.aprobada_por_id is None
    actual = conclusiones.estado_borrador(borrador)
    guardado = conclusiones.guardar_borrador(
        estudio.pk, bioquimico, actual["revision"], actual["huella_hechos"], "Continuar edición"
    )
    assert guardado["texto_editorial"] == "Continuar edición"
    assert BorradorConclusion.objects.get(pk=borrador.pk).solicitud_propuesta is None


def aprobar_para_carrera(estudio, bioquimico, estado):
    return conclusiones.aprobar_conclusion(
        estudio.pk,
        bioquimico,
        estado["revision"],
        estado["huella_hechos"],
        estado["huella_texto"],
        confirmacion=True,
    )


def correr_en_conexiones_independientes(izquierda, derecha):
    """Dos transacciones reales; no se sustituyen los locks del producto."""
    assert connection.vendor == "postgresql"
    inicio = threading.Barrier(2)

    def ejecutar(operacion):
        close_old_connections()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SET lock_timeout TO '5s'")
            inicio.wait(timeout=10)
            return operacion()
        finally:
            connections.close_all()

    with ThreadPoolExecutor(max_workers=2) as pool:
        futuros = [pool.submit(ejecutar, operacion) for operacion in (izquierda, derecha)]
        return [futuro.result(timeout=15) for futuro in futuros]


def intentar_emitir(estudio, bioquimico, aprobado):
    try:
        return emitir_informe(
            estudio.pk,
            bioquimico,
            incluir_conclusion=True,
            revision_conclusion=aprobado["revision"],
        ).pk
    except (conclusiones.ConflictoConclusion, InformeNoDisponible):
        return None


@pytest.mark.parametrize("cambio", ["edicion", "recalculo", "revalidacion"])
def test_edicion_recalculo_revalidacion_vs_emision(conclusion_propuesta, bioquimico, cambio):
    estudio, estado = conclusion_propuesta
    aprobado = aprobar_para_carrera(estudio, bioquimico, estado)
    antes = deepcopy(BorradorConclusion.objects.get(estudio=estudio).hechos)

    def escribir():
        try:
            if cambio == "edicion":
                conclusiones.guardar_borrador(
                    estudio.pk,
                    bioquimico,
                    aprobado["revision"],
                    aprobado["huella_hechos"],
                    "Nueva revisión profesional",
                )
            else:
                # La revalidación conserva el lock de estudio durante ambas operaciones.
                with transaction.atomic():
                    Estudio.objects.select_for_update().get(pk=estudio.pk)
                    fila = estudio.pruebas_asignadas.select_related("medicion").get(
                        prueba__codigo="PH"
                    )
                    resultado = corregir_mediciones(
                        estudio.pk,
                        {fila.pk: (fila.medicion.valor_ingresado, Decimal("7.4"))},
                        bioquimico,
                    )
                    assert len(resultado.corregidas) == 1
                    if cambio == "revalidacion":
                        validar(estudio, bioquimico, "PH")
            return True
        except (conclusiones.ConflictoConclusion, CorregirMedicionesError):
            return False

    escrito, emitido = correr_en_conexiones_independientes(
        escribir, lambda: intentar_emitir(estudio, bioquimico, aprobado)
    )
    assert escrito != bool(emitido)
    if emitido:
        copia = Informe.objects.get(pk=emitido).contenido["conclusion"]
        assert copia["hechos"] == antes
        assert copia["revision"] == str(aprobado["revision"])
        assert copia["texto"] == aprobado["texto_final"]
    else:
        assert not Informe.objects.filter(estudio=estudio).exists()
        borrador = BorradorConclusion.objects.get(estudio=estudio)
        assert borrador.aprobada_por_id is None


@pytest.mark.parametrize("campo,valor", [("limite_deteccion", "0.5"), ("nombre", "pH revisado")])
def test_ld_identidad_vs_snapshot(conclusion_propuesta, bioquimico, campo, valor):
    estudio, estado = conclusion_propuesta
    aprobado = aprobar_para_carrera(estudio, bioquimico, estado)
    antes = deepcopy(BorradorConclusion.objects.get(estudio=estudio).hechos)
    prueba_id = estudio.pruebas_asignadas.get(prueba__codigo="PH").prueba_id

    def catalogo():
        with transaction.atomic():
            prueba = Prueba.objects.select_for_update().get(pk=prueba_id)
            setattr(prueba, campo, valor)
            prueba.save(update_fields=[campo])

    _, emitido = correr_en_conexiones_independientes(
        catalogo, lambda: intentar_emitir(estudio, bioquimico, aprobado)
    )
    if emitido:
        copia = Informe.objects.get(pk=emitido).contenido["conclusion"]
        assert copia["hechos"] == antes
        assert copia["texto"] == aprobado["texto_final"]
        assert copia["aprobacion"]["aprobador_id"] == str(bioquimico.pk)
    else:
        assert not Informe.objects.filter(estudio=estudio).exists()
        assert BorradorConclusion.objects.get(estudio=estudio).aprobada_por_id is None


def test_dos_emisiones_una_copia_completa(conclusion_propuesta, bioquimico):
    estudio, estado = conclusion_propuesta
    aprobado = aprobar_para_carrera(estudio, bioquimico, estado)

    def operacion():
        return intentar_emitir(estudio, bioquimico, aprobado)

    resultados = correr_en_conexiones_independientes(operacion, operacion)
    assert resultados.count(None) == 1
    informe = Informe.objects.get(estudio=estudio)
    copia = informe.contenido["conclusion"]
    assert copia["texto"] == aprobado["texto_final"]
    assert copia["hechos"]["estudio_id"] == str(estudio.pk)
    assert len(copia["hechos"]["pruebas"]) == estudio.pruebas_asignadas.count()
    assert all(f["resultado_id"] and f["validacion_id"] for f in copia["hechos"]["pruebas"])
    assert Informe.objects.filter(estudio=estudio).count() == 1


def test_rollback_emision_no_deja_copia_parcial(conclusion_propuesta, bioquimico, monkeypatch):
    estudio, estado = conclusion_propuesta
    aprobado = aprobar_para_carrera(estudio, bioquimico, estado)
    original = deepcopy(BorradorConclusion.objects.get(estudio=estudio).__dict__)
    save_original = Estudio.save

    def fallo_despues_de_crear_informe(self, *args, **kwargs):
        if self.pk == estudio.pk and self.estado == EstadoEstudio.INFORME_GENERADO:
            assert Informe.objects.filter(estudio=self).exists()
            raise DatabaseError("Fallo controlado después de insertar la copia")
        return save_original(self, *args, **kwargs)

    with monkeypatch.context() as parche:
        parche.setattr(Estudio, "save", fallo_despues_de_crear_informe)
        with pytest.raises(DatabaseError, match="Fallo controlado"):
            intentar_emitir(estudio, bioquimico, aprobado)
    assert not Informe.objects.filter(estudio=estudio).exists()
    estudio.refresh_from_db()
    assert estudio.estado != EstadoEstudio.INFORME_GENERADO
    borrador = BorradorConclusion.objects.get(estudio=estudio)
    for campo in ("revision", "huella_hechos", "texto_final", "aprobada_por_id"):
        assert getattr(borrador, campo) == original[campo]
    assert intentar_emitir(estudio, bioquimico, aprobado)


def test_http409_persiste_invalidacion_sin_copia(
    conclusion_propuesta, bioquimico, cliente_bioquimico
):
    estudio, estado = conclusion_propuesta
    aprobado = aprobar_para_carrera(estudio, bioquimico, estado)
    prueba = estudio.pruebas_asignadas.get(prueba__codigo="PH").prueba
    nombre_original = prueba.nombre
    Prueba.objects.filter(pk=prueba.pk).update(nombre="Identidad posterior")
    respuesta = cliente_bioquimico.post(
        reverse("informes:generar", args=[estudio.pk]),
        {"incluir_conclusion": "1", "revision_conclusion": aprobado["revision"]},
    )
    assert respuesta.status_code == 409
    assert not Informe.objects.filter(estudio=estudio).exists()
    borrador = BorradorConclusion.objects.get(estudio=estudio)
    assert borrador.aprobada_por_id is None and borrador.requiere_revision
    assert borrador.revision > aprobado["revision"]
    Prueba.objects.filter(pk=prueba.pk).update(nombre=nombre_original)
    assert (
        cliente_bioquimico.get(reverse("informes:vista_previa", args=[estudio.pk])).status_code
        == 200
    )
    borrador.refresh_from_db()
    assert borrador.aprobada_por_id is None


def test_emision_ordena_locks_antes_del_advisory(conclusion_propuesta, bioquimico):
    estudio, estado = conclusion_propuesta
    aprobado = aprobar_para_carrera(estudio, bioquimico, estado)
    with CaptureQueriesContext(connection) as consultas:
        assert intentar_emitir(estudio, bioquimico, aprobado)
    sentencias = [consulta["sql"] for consulta in consultas]
    tablas = (
        "estudios_estudio",
        "informes_borradorconclusion",
        "estudios_pruebaestudio",
        "pruebas_prueba",
    )
    posiciones = [
        next(
            i
            for i, sql in enumerate(sentencias)
            if f'FROM "{tabla}"' in sql and "FOR UPDATE" in sql
        )
        for tabla in tablas
    ]
    advisory = next(i for i, sql in enumerate(sentencias) if "pg_advisory_xact_lock" in sql)
    insercion = next(
        i for i, sql in enumerate(sentencias) if 'INSERT INTO "informes_informe"' in sql
    )
    assert posiciones == sorted(posiciones)
    assert max(posiciones) < advisory < insercion
