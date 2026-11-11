"""Búsqueda de informes emitidos (US 7.3).

`informes_emitidos` es la única búsqueda de informes. Busca en la copia guardada al emitir
(`Informe.contenido`), no en los datos actuales del cliente o de la muestra: un informe se
encuentra por cómo salió, aunque el cliente se haya editado después.
"""

import re
import unicodedata

from django.contrib.postgres.lookups import Unaccent
from django.db.models import Q
from django.db.models.fields.json import KT

from clientes.models import normalizar_numero_documento

from .models import Informe, ResultadoEnvio

NUMERO_INFORME = re.compile(r"(?:inf-?)?(\d+)", re.IGNORECASE)
MAX_NUMERO_SQL = 2_147_483_647


def informes_emitidos(q, desde, hasta, envio=""):
    """Informes que coinciden con `q` (número, cliente, documento o N° PI) y con el rango de
    fechas de emisión (ambos extremos incluidos, en la zona horaria del proyecto)."""
    qs = Informe.objects.select_related("estudio", "emitido_por").annotate(
        cliente_nombre=Unaccent(KT("contenido__cliente__nombre_completo")),
        cliente_documento=KT("contenido__cliente__numero_documento"),
        numero_pi=KT("contenido__muestra__numero_pi"),
    )
    if q:
        qs = qs.filter(filtro_busqueda(q))
    if desde:
        qs = qs.filter(fecha_emision__date__gte=desde)
    if hasta:
        qs = qs.filter(fecha_emision__date__lte=hasta)
    # Envío por correo (SCRUM-82): si el informe tiene algún envío exitoso.
    enviados = Q(envios__resultado=ResultadoEnvio.ENVIADO)
    if envio == "enviados":
        qs = qs.filter(enviados).distinct()
    elif envio == "sin_enviar":
        qs = qs.exclude(enviados)
    return qs.order_by("-numero")


def sin_tildes(texto):
    """El texto sin tildes ni diéresis, como lo deja `unaccent` de PostgreSQL del otro lado."""
    descompuesto = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in descompuesto if not unicodedata.combining(c))


def filtro_busqueda(q):
    filtro = Q(cliente_nombre__icontains=sin_tildes(q))
    coincidencia = NUMERO_INFORME.fullmatch(q)
    if coincidencia:
        numero = int(coincidencia.group(1))
        if numero <= MAX_NUMERO_SQL:
            filtro |= Q(numero=numero)
    if q.isascii() and q.isdigit():
        filtro |= Q(numero_pi=str(int(q)))
    documento = normalizar_numero_documento(q)
    if len(documento) >= 4 and documento.isascii() and documento.isdigit():
        filtro |= Q(cliente_documento__contains=documento)
    return filtro
