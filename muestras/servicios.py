import datetime

from django.db import connection, transaction
from django.db.models import Max

from clientes.models import Cliente

from .models import NUMERO_PI_INICIAL, Muestra, Origen

# Clave fija del advisory lock que serializa la asignación del N° PI (US 4.1).
CLAVE_LOCK_NUMERO_PI = 4_100_001

MENSAJE_CLIENTE_NO_DISPONIBLE = "El cliente no está disponible."
MENSAJE_ORIGEN_AJENO = "El origen no pertenece al cliente seleccionado."


class MuestraNoDisponible(Exception):
    """El cliente o el origen del borrador ya no son válidos al confirmar."""

    def __init__(self, mensaje):
        super().__init__(mensaje)
        self.mensaje = mensaje


def siguiente_numero_pi():
    ultimo = Muestra.objects.aggregate(maximo=Max("numero_pi"))["maximo"]
    return (ultimo or NUMERO_PI_INICIAL - 1) + 1


def nombre_por_defecto(cliente):
    """ "Muestra N", con N = muestras ya registradas del cliente + 1 (tengan o no nombre propio)."""
    return f"Muestra {cliente.muestras.count() + 1}"


def obtener_origen(cliente, datos):
    if datos["origen"]:
        origen = Origen.objects.filter(pk=datos["origen"], cliente=cliente).first()
        if origen is None:
            raise MuestraNoDisponible(MENSAJE_ORIGEN_AJENO)
        return origen
    # Origen nuevo: si el cliente ya tiene uno con ese nombre (sin distinguir mayúsculas), se
    # reutiliza. Corre después del advisory lock, así que no hay carrera entre dos altas iguales.
    nombre = datos["origen_nuevo"].strip()
    existente = Origen.objects.filter(cliente=cliente, nombre__iexact=nombre).first()
    return existente or Origen.objects.create(cliente=cliente, nombre=nombre)


def registrar_muestra(datos, usuario):
    """Registra la muestra del borrador validado.

    Toma un advisory lock de PostgreSQL para que dos registros simultáneos no calculen el mismo
    N° PI ni el mismo "Muestra N" por defecto; el lock se libera al terminar la transacción. Si
    algo falla no queda nada guardado ni se consume un N° PI.

    Si el borrador ya se registró (otra confirmación simultánea leyó la misma sesión antes de que
    se borrara), devuelve esa muestra en lugar de crear otra.
    """
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_advisory_xact_lock(%s)", [CLAVE_LOCK_NUMERO_PI])

        registrada = Muestra.objects.filter(clave_borrador=datos["clave_borrador"]).first()
        if registrada is not None:
            return registrada

        cliente = Cliente.objects.filter(pk=datos["cliente"], activo=True).first()
        if cliente is None:
            raise MuestraNoDisponible(MENSAJE_CLIENTE_NO_DISPONIBLE)
        origen = obtener_origen(cliente, datos)

        return Muestra.objects.create(
            numero_pi=siguiente_numero_pi(),
            nombre=datos["nombre"] or nombre_por_defecto(cliente),
            cliente=cliente,
            origen=origen,
            fecha_muestreo=datetime.date.fromisoformat(datos["fecha_muestreo"]),
            fecha_ingreso=datetime.date.fromisoformat(datos["fecha_ingreso"]),
            sitio_extraccion=datos["sitio_extraccion"],
            tipo_vertido=datos["tipo_vertido"],
            responsable_muestreo=datos["responsable_muestreo"],
            registrada_por=usuario,
            clave_borrador=datos["clave_borrador"],
        )
