from django.db.models import Q

from clientes.models import normalizar_numero_documento

MAX_NUMERO_PI_SQL = 2_147_483_647


def filtro_busqueda(q):
    """Filtro de la búsqueda de estudios: muestra, cliente, tipo, N° de estudio, N° PI o documento.

    Lo usan `estudios:buscar` (US 5.2) e `informes:listar` (US 7.1).
    """
    filtro = (
        Q(muestra__nombre__unaccent__icontains=q)
        | Q(muestra__cliente__nombre__unaccent__icontains=q)
        | Q(muestra__cliente__razon_social__unaccent__icontains=q)
        | Q(tipo_nombre_snapshot__unaccent__icontains=q)
    )
    if q.isascii() and q.isdigit():
        numero = int(q)
        filtro |= Q(pk=numero)
        if numero <= MAX_NUMERO_PI_SQL:
            filtro |= Q(muestra__numero_pi=numero)
    q_doc = normalizar_numero_documento(q)
    if len(q_doc) >= 4 and q_doc.isascii() and q_doc.isdigit():
        filtro |= Q(muestra__cliente__numero_documento__contains=q_doc)
    return filtro
