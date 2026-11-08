"""Datos de demo (SCRUM-78): seis meses de actividad para mostrar y probar el dashboard.

`cargar_demo` arma la demo con los servicios reales de la aplicación (`registrar_muestra`,
`crear_estudio`, `cargar_mediciones`, `validar_resultados` y `emitir_informe`), así respeta las
mismas reglas que una persona: numeración sin huecos, cálculos, validaciones e informes con su
copia. Cada paso corre dentro de `reloj(fecha)`, que hace que las filas nazcan con la fecha del
guion: nunca se modifica una fila después de creada (principio IV de la constitution).

Los valores salen de un guion fijo (siempre los mismos); las fechas se calculan desde `ahora`.
Lo demo se reconoce por el correo `@demo.aqualab`. Ver specs/026-datos-demo/.
"""

import calendar
import datetime as dt
import struct
import uuid
import zlib
from contextlib import contextmanager
from dataclasses import dataclass
from decimal import Decimal
from unittest import mock

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management import call_command
from django.db import connection, transaction
from django.utils import timezone

from clientes.models import Cliente
from estudios.models import EstadoEstudio, Estudio, TipoEstudio, TipoEstudioPrueba
from estudios.servicios import cargar_mediciones, crear_estudio, validar_resultados
from informes.models import FirmaProfesional
from informes.servicios import emitir_informe
from muestras.models import Origen
from muestras.servicios import registrar_muestra
from pruebas.models import Prueba

DOMINIO = "demo.aqualab"
CONTRASENA = "Demo-1234"
CLAVE_LOCK_DEMO = 7_800_001
MESES = 6
HORA = 10
ESPACIO_CLAVES = uuid.uuid5(uuid.NAMESPACE_URL, "https://aqualab/demo/scrum-78")

MENSAJE_YA_CARGADA = (
    "La demo ya está cargada. Para empezar de cero: docker compose down -v, up -d, migrate y "
    "cargar_demo."
)


class DemoError(Exception):
    pass


# --- Guion -----------------------------------------------------------------------------------

FQ = "Físico-químico básico"
BACT = "Bacteriológico"
VUELCO = "Vuelco a colectora"

TIPOS = {
    FQ: ("PH", "TURBIDEZ", "COND", "CL-", "DUREZA-T", "NH4", "FE"),
    BACT: ("COL-TOT", "MESOFILAS", "ECOLI", "PSEUDO"),
    VUELCO: ("PH", "TEMPERATURA", "SS10", "SSEE", "DET-SAAM"),
}
DESCRIPCIONES = {
    FQ: "Control físico-químico de agua de consumo.",
    BACT: "Control bacteriológico de agua de consumo.",
    VUELCO: "Control de efluentes volcados a colectora cloacal.",
}

USUARIOS = (
    {
        "email": f"tecnico@{DOMINIO}",
        "first_name": "Técnico",
        "last_name": "Demo",
        "grupos": (),
    },
    {
        "email": f"bioquimico@{DOMINIO}",
        "first_name": "Bioquímica",
        "last_name": "Demo",
        "grupos": ("Bioquímicos", "Administradores"),
    },
)
MATRICULA = "MP 0000 (DEMO)"

CLIENTES = {
    "lacteos": {
        "razon_social": "Lácteos del Sur S.A.",
        "nombre": "",
        "tipo_documento": "CUIT",
        "numero_documento": "30700000016",
        "email": f"calidad@{DOMINIO}",
        "telefono": "02342 41-5500",
        "domicilio": "Ruta 5 km 210, Bragado",
    },
    "municipio": {
        "razon_social": "Municipalidad de Villa Verde",
        "nombre": "",
        "tipo_documento": "CUIT",
        "numero_documento": "30700000024",
        "email": f"obras.sanitarias@{DOMINIO}",
        "telefono": "02346 43-1200",
        "domicilio": "Av. San Martín 450, Villa Verde",
    },
    "particular": {
        "razon_social": "",
        "nombre": "María González",
        "tipo_documento": "DNI",
        "numero_documento": "99999901",
        "email": f"maria.gonzalez@{DOMINIO}",
        "telefono": "11 5555-0101",
        "domicilio": "Los Aromos 1234, Villa Verde",
    },
}


@dataclass(frozen=True)
class OrigenDemo:
    clave: str
    cliente: str
    nombre: str
    dia_base: int
    vertido: str
    sitio: str
    responsable: str
    base: dict  # valores medidos habituales por código de prueba


ORIGENES = (
    OrigenDemo(
        "pozo-1",
        "lacteos",
        "Pozo 1",
        8,
        "agua",
        "Grifo de salida del pozo 1",
        "Jorge Ibáñez",
        {
            "PH": "7.3",
            "TURBIDEZ": "0.8",
            "COND": "640",
            "CL-": "9.5",
            "DUREZA-T": "11.0",
            "NH4": "0.06",
            "FE": "0.08",
        },
    ),
    OrigenDemo(
        "pozo-2",
        "lacteos",
        "Pozo 2",
        10,
        "agua",
        "Grifo de salida del pozo 2",
        "Jorge Ibáñez",
        {
            "PH": "7.5",
            "TURBIDEZ": "1.1",
            "COND": "710",
            "CL-": "12.0",
            "DUREZA-T": "12.5",
            "NH4": "0.07",
            "FE": "0.12",
        },
    ),
    OrigenDemo(
        "colectora",
        "lacteos",
        "Salida a colectora",
        12,
        "cloacal",
        "Cámara de toma de muestra del efluente",
        "Jorge Ibáñez",
        {"PH": "8.1", "TEMPERATURA": "24.5", "SS10": "0.05", "SSEE": "32", "DET-SAAM": "4.2"},
    ),
    OrigenDemo(
        "tanque-elevado",
        "municipio",
        "Tanque elevado",
        6,
        "agua",
        "Salida del tanque elevado de la planta",
        "Laura Méndez",
        {
            "PH": "7.1",
            "TURBIDEZ": "0.5",
            "COND": "520",
            "CL-": "6.5",
            "DUREZA-T": "9.0",
            "NH4": "0.05",
            "FE": "0.05",
            "COL-TOT": "0",
            "MESOFILAS": "60",
            "ECOLI": "0",
            "PSEUDO": "0",
        },
    ),
    OrigenDemo(
        "escuela",
        "municipio",
        "Escuela N° 12",
        14,
        "agua",
        "Bebedero del patio",
        "Laura Méndez",
        {"COL-TOT": "0", "MESOFILAS": "85", "ECOLI": "0", "PSEUDO": "0"},
    ),
    OrigenDemo(
        "pozo-domiciliario",
        "particular",
        "Pozo domiciliario",
        5,
        "agua",
        "Canilla de la cocina",
        "María González",
        {
            "PH": "7.8",
            "TURBIDEZ": "1.6",
            "COND": "880",
            "CL-": "15.0",
            "DUREZA-T": "14.0",
            "NH4": "0.09",
            "FE": "0.18",
        },
    ),
    OrigenDemo(
        "tanque-domiciliario",
        "particular",
        "Tanque domiciliario",
        16,
        "agua",
        "Canilla del baño",
        "María González",
        {"COL-TOT": "1", "MESOFILAS": "120", "ECOLI": "0", "PSEUDO": "0"},
    ),
)
POR_CLAVE = {o.clave: o for o in ORIGENES}

# Variación mensual de las mediciones habituales, en múltiplos de su último decimal (mes 0 a 5).
VARIACION = (0, 1, -1, 2, -2, 1)

# Casos especiales: (origen, mes, código) → valor medido.
ESPECIALES = {
    # Desvío de Cloruro en Pozo 2 (research R9): ~120 mg/l → 415 validado → 430 sin validar.
    ("pozo-2", 5, "CL-"): "11.8",
    ("pozo-2", 4, "CL-"): "12.1",
    ("pozo-2", 3, "CL-"): "12.4",
    ("pozo-2", 2, "CL-"): "12.0",
    ("pozo-2", 1, "CL-"): "41.5",
    ("pozo-2", 0, "CL-"): "43.0",
    # Fuera de norma.
    ("pozo-domiciliario", 4, "TURBIDEZ"): "4.2",
    ("pozo-domiciliario", 2, "TURBIDEZ"): "4.2",
    ("tanque-domiciliario", 3, "COL-TOT"): "12",
    ("tanque-domiciliario", 3, "ECOLI"): "1",
    ("colectora", 2, "PH"): "10.6",
    ("colectora", 3, "DET-SAAM"): "14",
}
# Valores que no varían de un mes a otro (A/P, por debajo del límite de detección, conteos 0).
FIJOS = {"ECOLI", "PSEUDO", "SS10", "COL-TOT"}

# Estado destino.
PENDIENTE = "pendiente"  # estudio creado, sin mediciones
PARCIAL = "parcial"  # algunas mediciones (En proceso)
CARGADO = "cargado"  # todas las mediciones, sin validar (En proceso)
FINALIZADO = "finalizado"  # todo validado, sin informe
INFORME = "informe"  # informe emitido

ESTADOS = {
    ("escuela", 1, BACT): FINALIZADO,  # alerta: finalizado sin informe
    ("pozo-domiciliario", 1, FQ): PARCIAL,  # alerta: estancado
    ("tanque-domiciliario", 0, BACT): PENDIENTE,
    ("escuela", 0, BACT): PENDIENTE,
    ("pozo-2", 0, FQ): CARGADO,  # desvío sin validar
    ("colectora", 0, VUELCO): PARCIAL,
    ("pozo-1", 0, FQ): FINALIZADO,
    ("tanque-elevado", 0, FQ): FINALIZADO,
    ("pozo-domiciliario", 0, FQ): INFORME,
    ("tanque-elevado", 0, BACT): INFORME,
}


def tipos_de(origen, mes):
    """Tipos de estudio de la muestra del origen en el mes (el tanque elevado suma el
    bacteriológico en los meses pares)."""
    if origen.clave == "tanque-elevado":
        return (FQ, BACT) if mes % 2 == 0 else (FQ,)
    if origen.vertido == "cloacal":
        return (VUELCO,)
    if "PH" in origen.base:
        return (FQ,)
    return (BACT,)


def estado_de(origen, mes, tipo):
    return ESTADOS.get((origen.clave, mes, tipo), INFORME)


def valor_de(origen, mes, codigo):
    """Valor medido (texto decimal) de la prueba en el mes, según el guion."""
    especial = ESPECIALES.get((origen.clave, mes, codigo))
    if especial is not None:
        return especial
    base = Decimal(origen.base[codigo])
    if codigo in FIJOS:
        return str(base)
    paso = Decimal(1).scaleb(base.as_tuple().exponent)
    return str(base + paso * VARIACION[mes])


# --- Fechas ----------------------------------------------------------------------------------


def menos_meses(fecha, meses):
    total = fecha.year * 12 + fecha.month - 1 - meses
    return total // 12, total % 12 + 1


class Fechas:
    """Fechas de cada paso de la muestra del origen en el mes `mes` (0 = actual), según
    research R3: en orden, nunca después de `ahora` y con tiempos de respuesta distintos."""

    def __init__(self, ahora, origen, indice, mes):
        local = timezone.localtime(ahora) if timezone.is_aware(ahora) else ahora
        anio, numero_mes = menos_meses(local, mes)
        dia = min(origen.dia_base, calendar.monthrange(anio, numero_mes)[1])
        base = local.replace(
            year=anio, month=numero_mes, day=dia, hour=HORA, minute=0, second=0, microsecond=0
        )
        desplazamientos = (
            (indice + mes) % 2,  # ingreso
            0,  # creación del estudio
            2 + (indice * 2 + mes) % 4,  # carga
            1 + (indice + mes) % 3,  # validación
            (indice * 3 + mes * 2) % 7,  # emisión
        )
        pasos = [min(base, local)]
        for dias in desplazamientos:
            pasos.append(min(max(pasos[-1] + dt.timedelta(days=dias), pasos[-1]), local))
        if origen.clave == "pozo-domiciliario" and mes == 1:
            # Estudio estancado: la última carga queda más de 7 días antes de hoy (FR-009).
            tope = local - dt.timedelta(days=10)
            pasos[3] = max(min(pasos[3], tope), pasos[2])
            pasos[4] = max(pasos[4], pasos[3])
            pasos[5] = max(pasos[5], pasos[4])
        (
            self.muestreo,
            self.ingreso,
            self.estudio,
            self.carga,
            self.validacion,
            self.emision,
        ) = pasos


@contextmanager
def reloj(momento):
    """Mientras dura el bloque, `timezone.now()` devuelve `momento`: las fechas automáticas
    (`auto_now_add`/`auto_now`) nacen con la fecha del guion (research R2)."""
    with mock.patch("django.utils.timezone.now", return_value=momento):
        yield


def clave(*partes):
    return str(uuid.uuid5(ESPACIO_CLAVES, ":".join(str(p) for p in partes)))


# --- Firma -----------------------------------------------------------------------------------


def _bloque(tipo, datos):
    crc = zlib.crc32(tipo + datos) & 0xFFFFFFFF
    return struct.pack(">I", len(datos)) + tipo + datos + struct.pack(">I", crc)


def firma_png(ancho=600, alto=200):
    """PNG en escala de grises con un trazo ondulado, armado sin Pillow (≤ 64 KB)."""
    filas = []
    for y in range(alto):
        fila = bytearray(b"\xff" * ancho)
        for x in range(40, ancho - 40):
            centro = alto // 2 + int(35 * ((x // 25) % 2 * 2 - 1) * ((x % 25) / 25))
            if abs(y - centro) <= 2:
                fila[x] = 0x20
        filas.append(b"\x00" + bytes(fila))
    ihdr = struct.pack(">IIBBBBB", ancho, alto, 8, 0, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + _bloque(b"IHDR", ihdr)
        + _bloque(b"IDAT", zlib.compress(b"".join(filas), 9))
        + _bloque(b"IEND", b"")
    )


# --- Carga -----------------------------------------------------------------------------------


@dataclass
class Resumen:
    catalogo_importado: bool
    clientes: int
    origenes: int
    muestras: int
    estudios: dict
    informes: int


def comprobar_conflictos():
    Usuario = get_user_model()
    for datos in USUARIOS:
        if Usuario.objects.filter(email__iexact=datos["email"]).exists():
            raise DemoError(
                f"Ya existe el usuario {datos['email']} y no es de la demo. No se cargó nada."
            )
    for nombre, codigos in TIPOS.items():
        tipo = TipoEstudio.objects.filter(nombre__iexact=nombre).first()
        if tipo and set(tipo.pruebas.values_list("codigo", flat=True)) != set(codigos):
            raise DemoError(
                f"Ya existe el tipo de estudio «{tipo.nombre}» con otras pruebas. No se cargó nada."
            )


def crear_usuarios(inicio):
    Usuario = get_user_model()
    creados = {}
    for datos in USUARIOS:
        usuario = Usuario.objects.create_user(
            email=datos["email"],
            password=CONTRASENA,
            first_name=datos["first_name"],
            last_name=datos["last_name"],
            is_active=True,
            date_joined=inicio,
        )
        for nombre in datos["grupos"]:
            usuario.groups.add(Group.objects.get(name=nombre))
        creados[datos["email"]] = usuario
    tecnico, bioquimico = (creados[d["email"]] for d in USUARIOS)
    with reloj(inicio):
        FirmaProfesional.objects.create(usuario=bioquimico, imagen=firma_png(), matricula=MATRICULA)
    # Releer para no arrastrar una caché de permisos anterior a los grupos.
    return Usuario.objects.get(pk=tecnico.pk), Usuario.objects.get(pk=bioquimico.pk)


def asegurar_tipos():
    tipos = {}
    for nombre, codigos in TIPOS.items():
        tipo = TipoEstudio.objects.filter(nombre__iexact=nombre).first()
        if tipo is None:
            tipo = TipoEstudio.objects.create(nombre=nombre, descripcion=DESCRIPCIONES[nombre])
            pruebas = Prueba.objects.filter(codigo__in=codigos)
            if pruebas.count() != len(codigos):
                raise DemoError("Al catálogo de pruebas le faltan pruebas de la demo.")
            TipoEstudioPrueba.objects.bulk_create(
                [TipoEstudioPrueba(tipo=tipo, prueba=p) for p in pruebas]
            )
        tipos[nombre] = tipo
    return tipos


def crear_clientes_y_origenes(inicio):
    with reloj(inicio):
        clientes = {c: Cliente.objects.create(**datos) for c, datos in CLIENTES.items()}
        origenes = {
            o.clave: Origen.objects.create(cliente=clientes[o.cliente], nombre=o.nombre)
            for o in ORIGENES
        }
    return clientes, origenes


def cargar_estudio(muestra, origen, indice, mes, tipo, fechas, tecnico, bioquimico):
    estado = estado_de(origen, mes, tipo.nombre)
    with reloj(fechas.estudio):
        estudio = crear_estudio(
            {
                "clave": clave(origen.clave, mes, tipo.nombre, "estudio"),
                "muestra": muestra.pk,
                "tipo": tipo.pk,
                "version": tipo.version,
            },
            tecnico,
        )
    if estado == PENDIENTE:
        return estudio
    asignaciones = list(
        estudio.pruebas_asignadas.select_related("prueba").order_by("prueba__codigo")
    )
    if estado == PARCIAL:
        asignaciones = asignaciones[: len(asignaciones) // 2]
    with reloj(fechas.carga):
        cargar_mediciones(
            estudio.pk,
            {a.pk: Decimal(valor_de(origen, mes, a.prueba.codigo)) for a in asignaciones},
            tecnico,
        )
    if estado in (PARCIAL, CARGADO):
        return estudio
    elegidas = {
        a.pk: str(a.resultado.valor) for a in estudio.pruebas_asignadas.select_related("resultado")
    }
    with reloj(fechas.validacion):
        validar_resultados(estudio.pk, elegidas, bioquimico)
    if estado == INFORME:
        with reloj(fechas.emision):
            emitir_informe(estudio.pk, bioquimico)
    return estudio


def cargar_guion(ahora, tecnico, bioquimico, tipos, origenes):
    for mes in range(MESES - 1, -1, -1):
        for indice, origen in enumerate(ORIGENES):
            fechas = Fechas(ahora, origen, indice, mes)
            with reloj(fechas.ingreso):
                muestra = registrar_muestra(
                    {
                        "clave_borrador": clave(origen.clave, mes, "muestra"),
                        "cliente": origenes[origen.clave].cliente_id,
                        "origen": origenes[origen.clave].pk,
                        "nombre": "",
                        "fecha_muestreo": fechas.muestreo.date().isoformat(),
                        "fecha_ingreso": fechas.ingreso.date().isoformat(),
                        "sitio_extraccion": origen.sitio,
                        "tipo_vertido": origen.vertido,
                        "responsable_muestreo": origen.responsable,
                    },
                    tecnico,
                )
            for nombre in tipos_de(origen, mes):
                cargar_estudio(
                    muestra, origen, indice, mes, tipos[nombre], fechas, tecnico, bioquimico
                )


def ya_cargada():
    return Cliente.objects.filter(email__iendswith=f"@{DOMINIO}").exists()


def cargar_demo(salida, ahora=None):
    """Carga la demo en una transacción. Devuelve el `Resumen`, o None si ya estaba cargada."""
    ahora = ahora or timezone.now()
    with transaction.atomic():
        with connection.cursor() as cursor:
            cursor.execute("SELECT pg_advisory_xact_lock(%s)", [CLAVE_LOCK_DEMO])
        if ya_cargada():
            return None
        comprobar_conflictos()
        importado = not Prueba.objects.exists()
        if importado:
            call_command("importar_catalogo_pruebas", stdout=salida)
        inicio = Fechas(ahora, ORIGENES[0], 0, MESES - 1).muestreo - dt.timedelta(days=7)
        tecnico, bioquimico = crear_usuarios(inicio)
        tipos = asegurar_tipos()
        clientes, origenes = crear_clientes_y_origenes(inicio)
        cargar_guion(ahora, tecnico, bioquimico, tipos, origenes)
        estudios = Estudio.objects.filter(muestra__cliente__in=clientes.values())
        return Resumen(
            catalogo_importado=importado,
            clientes=len(clientes),
            origenes=len(origenes),
            muestras=estudios.values("muestra").distinct().count(),
            estudios={
                etiqueta: estudios.filter(estado=valor).count()
                for valor, etiqueta in EstadoEstudio.choices
            },
            informes=estudios.filter(informe__isnull=False).count(),
        )
