from urllib.parse import urlencode

from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import render

from estudios.forms import BuscarEstudioForm
from estudios.views import RESULTADOS_POR_PAGINA

from . import servicios


def listar(request):
    page_obj = None
    q = ""
    solo_listos = request.GET.get("listos") == "1"
    form = BuscarEstudioForm(request.GET or None)
    if not form.is_bound or form.is_valid():
        q = form.cleaned_data.get("q", "") if form.is_bound else ""
        qs = servicios.estudios_para_informar(q, solo_listos)
        page_obj = Paginator(qs, RESULTADOS_POR_PAGINA).get_page(request.GET.get("page"))
    parametros = urlencode({"q": q} | ({"listos": "1"} if solo_listos else {}))
    return render(
        request,
        "informes/listar.html",
        {
            "form": form,
            "page_obj": page_obj,
            "q": q,
            "solo_listos": solo_listos,
            "parametros": parametros,
        },
    )


def control(request, pk):
    return HttpResponse()  # Provisoria: la reemplaza T015.
