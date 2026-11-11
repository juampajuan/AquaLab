from urllib.parse import urlencode

from django.db.models import Count
from django.shortcuts import render
from django.urls import reverse

from estudios.models import Estudio
from estudios.pendientes import estudios_con_mediciones_pendientes, resultados_por_validar
from informes.servicios import estudios_para_informar
from muestras.models import Muestra


def inicio(request):
    """Pendientes del laboratorio según rol profesional; no concede autorizaciones."""
    indicadores = [
        {
            "nombre": "mediciones-pendientes",
            "titulo": "Estudios con mediciones por cargar",
            "valor": estudios_con_mediciones_pendientes(Estudio.objects.all()).count(),
            "icono": "microscope",
            "url": reverse("estudios:buscar") + "?" + urlencode({"pendiente": "mediciones"}),
        }
    ]
    if request.user.groups.filter(name="Bioquímicos").exists():
        indicadores.extend(
            [
                {
                    "nombre": "resultados-por-validar",
                    "titulo": "Resultados por validar",
                    "valor": resultados_por_validar().count(),
                    "icono": "clipboard-list",
                    "url": reverse("estudios:buscar")
                    + "?"
                    + urlencode({"pendiente": "validaciones"}),
                },
                {
                    "nombre": "estudios-listos",
                    "titulo": "Estudios por informar",
                    "valor": estudios_para_informar("", True).count(),
                    "icono": "file-text",
                    "url": reverse("informes:listar") + "?" + urlencode({"listos": "1"}),
                },
            ]
        )
    contexto = {
        "indicadores": indicadores,
        "ultimas_muestras": Muestra.objects.select_related("cliente", "origen")
        .annotate(cantidad_estudios=Count("estudios"))
        .order_by("-numero_pi")[:5],
    }
    return render(request, "inicio.html", contexto)
