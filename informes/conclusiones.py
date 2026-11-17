import hashlib
import uuid
from copy import deepcopy

from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.http import Http404
from django.utils import timezone

from estudios.models import Estudio
from pruebas.models import Prueba

from . import conclusion_hechos, conclusion_ia
from .forms import AprobarConclusionForm, GuardarConclusionForm
from .models import BorradorConclusion
from .servicios import InformeNoDisponible, motivo_para_no_informar


def autorizar_conclusion(usuario):
    if not usuario.is_authenticated or not usuario.is_active or usuario.pk is None:
        raise PermissionDenied("Se requiere una sesión activa de un bioquímico autorizado.")
    actual = get_user_model().objects.filter(pk=usuario.pk, is_active=True).first()
    if (
        actual is None
        or not actual.groups.filter(name="Bioquímicos").exists()
        or not actual.has_perm("informes.emitir_informes")
    ):
        raise PermissionDenied(
            "Se requiere pertenecer a Bioquímicos y permiso para emitir informes."
        )
    return actual


def puede_concluir(usuario):
    try:
        autorizar_conclusion(usuario)
    except PermissionDenied:
        return False
    return True


class ConflictoConclusion(Exception):
    def __init__(self, mensaje, estado=None):
        super().__init__(mensaje)
        self.estado = estado or {}


def limpiar_aprobacion(borrador):
    borrador.aprobada_por = None
    borrador.fecha_aprobacion = borrador.revision_aprobada = None
    borrador.nombre_aprobador = ""
    borrador.huella_texto_aprobado = borrador.huella_hechos_aprobados = ""
    borrador.solicitud_propuesta = None


def estado_borrador(borrador, hechos=None):
    if borrador is None:
        return {
            "revision": 0,
            "huella_hechos": conclusion_hechos.huella(hechos) if hechos else "",
            "texto_editorial": "",
            "texto_final": "",
            "advertencias": [],
            "huella_texto": hashlib.sha256(b"").hexdigest(),
            "aprobada": False,
            "origen_propuesta": "",
            "motivo_respaldo": "",
            "requiere_revision": False,
            "hechos": deepcopy(hechos) if hechos is not None else {},
        }
    return {
        "revision": borrador.revision,
        "huella_hechos": borrador.huella_hechos,
        "texto_editorial": borrador.texto_editorial,
        "texto_final": borrador.texto_final,
        "advertencias": borrador.advertencias,
        "huella_texto": hashlib.sha256(borrador.texto_final.encode("utf-8")).hexdigest(),
        "aprobada": borrador.aprobada_por_id is not None,
        "origen_propuesta": borrador.origen_propuesta,
        "motivo_respaldo": borrador.motivo_respaldo,
        "requiere_revision": borrador.requiere_revision,
        "hechos": deepcopy(borrador.hechos),
    }


def bloquear(estudio_pk):
    try:
        estudio = Estudio.objects.select_for_update().get(pk=estudio_pk)
    except Estudio.DoesNotExist as exc:
        raise Http404 from exc
    borrador = BorradorConclusion.objects.select_for_update().filter(estudio=estudio).first()
    filas = list(estudio.pruebas_asignadas.select_for_update().order_by("pk"))
    list(
        Prueba.objects.select_for_update()
        .filter(pk__in=[a.prueba_id for a in filas])
        .order_by("pk")
    )
    return estudio, borrador, motivo_para_no_informar(estudio, filas)


def reconciliar(borrador, hechos):
    if borrador is None or borrador.huella_hechos == conclusion_hechos.huella(hechos):
        return False
    limpiar_aprobacion(borrador)
    borrador.revision += 1
    borrador.hechos = hechos
    borrador.huella_hechos = conclusion_hechos.huella(hechos)
    borrador.advertencias = conclusion_hechos.advertencias(hechos)
    borrador.texto_final = conclusion_hechos.texto_final(
        borrador.texto_editorial, borrador.advertencias
    )
    borrador.requiere_revision = True
    borrador.fecha_edicion = timezone.now()
    borrador.save()
    return True


def hechos_actuales(estudio, borrador):
    try:
        hechos = conclusion_hechos.recolectar(estudio)
    except conclusion_hechos.FuentesAmbiguas:
        if borrador and (
            not borrador.requiere_revision
            or borrador.aprobada_por_id
            or borrador.solicitud_propuesta is not None
        ):
            limpiar_aprobacion(borrador)
            borrador.revision += 1
            borrador.requiere_revision = True
            borrador.fecha_edicion = timezone.now()
            borrador.save()
        return None
    reconciliar(borrador, hechos)
    return hechos


def cargar_borrador_previa(estudio_pk, usuario):
    with transaction.atomic():
        autorizar_conclusion(usuario)
        estudio, borrador, motivo = bloquear(estudio_pk)
        if motivo:
            raise InformeNoDisponible(motivo)
        hechos = hechos_actuales(estudio, borrador)
        estado = estado_borrador(borrador, hechos) if hechos is not None else None
    if hechos is None:
        raise conclusion_hechos.FuentesAmbiguas(
            "La conclusión no está disponible: las validaciones son ambiguas."
        )
    return estado


def proponer_conclusion(estudio_pk, usuario, revision_esperada, huella_hechos_vista):
    conflicto = None
    with transaction.atomic():
        actual = autorizar_conclusion(usuario)
        estudio, borrador, motivo = bloquear(estudio_pk)
        hechos = hechos_actuales(estudio, borrador)
        revision = borrador.revision if borrador else 0
        if (
            motivo
            or hechos is None
            or revision != revision_esperada
            or conclusion_hechos.huella(hechos) != huella_hechos_vista
        ):
            conflicto = ConflictoConclusion(
                motivo or "Las fuentes o el borrador cambiaron. Revisá la vista previa.",
                estado_borrador(borrador, hechos),
            )
        else:
            if borrador is None:
                avisos = conclusion_hechos.advertencias(hechos)
                borrador = BorradorConclusion(
                    estudio=estudio,
                    editado_por=actual,
                    fecha_edicion=timezone.now(),
                    origen_propuesta="manual",
                    hechos=hechos,
                    huella_hechos=conclusion_hechos.huella(hechos),
                    advertencias=avisos,
                    texto_final=conclusion_hechos.texto_final("", avisos),
                )
            else:
                borrador.revision += 1
            limpiar_aprobacion(borrador)
            token = uuid.uuid4()
            borrador.solicitud_propuesta = token
            borrador.editado_por = actual
            borrador.fecha_edicion = timezone.now()
            borrador.save()
            revision_reservada = borrador.revision
    if conflicto:
        raise conflicto
    propuesta = conclusion_ia.proponer(hechos)
    with transaction.atomic():
        actual = autorizar_conclusion(usuario)
        estudio, borrador, motivo = bloquear(estudio_pk)
        actuales = hechos_actuales(estudio, borrador)
        if (
            motivo
            or actuales is None
            or borrador is None
            or borrador.solicitud_propuesta != token
            or borrador.revision != revision_reservada
            or conclusion_hechos.huella(actuales) != conclusion_hechos.huella(hechos)
        ):
            conflicto = ConflictoConclusion(
                motivo or "La propuesta quedó obsoleta. Revisá el borrador actual.",
                estado_borrador(borrador, actuales),
            )
        else:
            borrador.revision += 1
            borrador.texto_editorial = propuesta.texto
            borrador.texto_final = conclusion_hechos.texto_final(
                propuesta.texto, borrador.advertencias
            )
            borrador.origen_propuesta = propuesta.origen
            borrador.motivo_respaldo = propuesta.motivo
            borrador.requiere_revision = False
            borrador.solicitud_propuesta = None
            borrador.editado_por = actual
            borrador.fecha_edicion = timezone.now()
            borrador.save()
            resultado = estado_borrador(borrador)
    if conflicto:
        raise conflicto
    return resultado


def validar_entrada(formulario, datos):
    form = formulario(datos)
    if not form.is_valid():
        raise ValidationError(dict(form.errors))
    return form.cleaned_data


def comprobar_revision(borrador, hechos, motivo, datos):
    revision = borrador.revision if borrador else 0
    if (
        motivo
        or hechos is None
        or revision != datos["revision_esperada"]
        or conclusion_hechos.huella(hechos) != datos["huella_hechos_vista"]
    ):
        return ConflictoConclusion(
            motivo or "Las fuentes o el borrador cambiaron. Revisá el estado actual.",
            estado_borrador(borrador, hechos),
        )
    return None


def guardar_borrador(estudio_pk, usuario, revision_esperada, huella_hechos_vista, texto):
    autorizar_conclusion(usuario)
    datos = validar_entrada(
        GuardarConclusionForm,
        {
            "revision_esperada": revision_esperada,
            "huella_hechos_vista": huella_hechos_vista,
            "texto": texto,
        },
    )
    with transaction.atomic():
        actual = autorizar_conclusion(usuario)
        estudio, borrador, motivo = bloquear(estudio_pk)
        hechos = hechos_actuales(estudio, borrador)
        conflicto = comprobar_revision(borrador, hechos, motivo, datos)
        if conflicto is None:
            texto = datos["texto"]
            if borrador is None:
                borrador = BorradorConclusion(
                    estudio=estudio,
                    editado_por=actual,
                    fecha_edicion=timezone.now(),
                    origen_propuesta="manual",
                    hechos=hechos,
                    huella_hechos=conclusion_hechos.huella(hechos),
                    advertencias=conclusion_hechos.advertencias(hechos),
                )
            elif borrador.texto_editorial != texto or borrador.solicitud_propuesta is not None:
                borrador.revision += 1
            else:
                return estado_borrador(borrador)
            limpiar_aprobacion(borrador)
            borrador.texto_editorial = texto
            borrador.texto_final = conclusion_hechos.texto_final(texto, borrador.advertencias)
            borrador.editado_por = actual
            borrador.fecha_edicion = timezone.now()
            borrador.full_clean()
            borrador.save()
            resultado = estado_borrador(borrador)
    if conflicto:
        raise conflicto
    return resultado


def aprobar_conclusion(
    estudio_pk,
    usuario,
    revision_esperada,
    huella_hechos_vista,
    huella_texto_visto,
    *,
    confirmacion=False,
):
    autorizar_conclusion(usuario)
    datos = validar_entrada(
        AprobarConclusionForm,
        {
            "revision_esperada": revision_esperada,
            "huella_hechos_vista": huella_hechos_vista,
            "huella_texto_visto": huella_texto_visto,
            "confirmacion": confirmacion,
        },
    )
    with transaction.atomic():
        actual = autorizar_conclusion(usuario)
        estudio, borrador, motivo = bloquear(estudio_pk)
        hechos = hechos_actuales(estudio, borrador)
        conflicto = comprobar_revision(borrador, hechos, motivo, datos)
        if conflicto is None:
            estado = estado_borrador(borrador, hechos)
            if (
                borrador is None
                or not borrador.texto_final.strip()
                or estado["huella_texto"] != datos["huella_texto_visto"]
            ):
                conflicto = ConflictoConclusion(
                    "Guardá y revisá el texto final antes de aprobar.", estado
                )
            else:
                borrador.revision += 1
                borrador.aprobada_por = actual
                borrador.nombre_aprobador = actual.get_full_name() or actual.email
                borrador.fecha_aprobacion = timezone.now()
                borrador.revision_aprobada = borrador.revision
                borrador.huella_texto_aprobado = estado["huella_texto"]
                borrador.huella_hechos_aprobados = borrador.huella_hechos
                borrador.requiere_revision = False
                borrador.solicitud_propuesta = None
                borrador.editado_por = actual
                borrador.fecha_edicion = timezone.now()
                borrador.full_clean()
                borrador.save()
                resultado = estado_borrador(borrador)
    if conflicto:
        raise conflicto
    return resultado


def conclusion_para_emitir_bloqueada(borrador, hechos, revision_solicitada, motivo=None):
    estado = estado_borrador(borrador, hechos)
    if motivo or hechos is None or borrador is None:
        return None, ConflictoConclusion(
            motivo or "No hay una conclusión aprobada con fuentes vigentes.", estado
        )
    if borrador.aprobada_por_id and (
        borrador.requiere_revision
        or borrador.revision_aprobada != borrador.revision
        or borrador.huella_hechos_aprobados != borrador.huella_hechos
        or conclusion_hechos.huella(borrador.hechos) != borrador.huella_hechos
        or borrador.huella_hechos != conclusion_hechos.huella(hechos)
        or borrador.huella_texto_aprobado != estado["huella_texto"]
    ):
        limpiar_aprobacion(borrador)
        borrador.revision += 1
        borrador.requiere_revision = True
        borrador.fecha_edicion = timezone.now()
        borrador.save()
        estado = estado_borrador(borrador)
    if (
        type(revision_solicitada) is not int
        or revision_solicitada != borrador.revision
        or borrador.aprobada_por_id is None
        or borrador.requiere_revision
        or borrador.solicitud_propuesta is not None
        or not borrador.texto_final.strip()
    ):
        return None, ConflictoConclusion(
            "La conclusión no tiene una aprobación vigente para esta revisión. "
            "Revisala nuevamente.",
            estado,
        )
    return {
        "schema": "1",
        "texto": borrador.texto_final,
        "advertencias": deepcopy(borrador.advertencias),
        "hechos": deepcopy(borrador.hechos),
        "revision": str(borrador.revision),
        "huella_texto": borrador.huella_texto_aprobado,
        "huella_hechos": borrador.huella_hechos_aprobados,
        "origen_propuesta": borrador.origen_propuesta,
        "aprobacion": {
            "aprobador_id": str(borrador.aprobada_por_id),
            "nombre": borrador.nombre_aprobador,
            "fecha": borrador.fecha_aprobacion.isoformat(),
        },
    }, None
