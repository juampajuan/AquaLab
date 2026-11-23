"""Historial del laboratorio para el sitio publicado (presentación final).

Reusa el guion de la demo (SCRUM-78, `estudios/demo.py`) con datos que parecen reales: un
laboratorio con su personal (las personas de la Lean Inception), más clientes y orígenes, nueve
meses de actividad y ninguna marca de «demo». Además deja preparado el estudio de Nitritos que
espera su curva de calibración (US 6.6), para mostrarla en vivo.

Corre con `python manage.py cargar_historial`; en Render lo llama `scripts/iniciar_produccion.sh`
cuando está definida `AQUALAB_HISTORIAL_CONTRASENA`. No carga dos veces.

Los correos son de Gmail, inventados. El de Lácteos del Sur es una casilla del grupo, para mostrar
en vivo el envío del informe por correo.
"""

import datetime as dt
import os
from decimal import Decimal
from unittest import mock

from django.db import transaction
from django.utils import timezone

from clientes.models import Cliente
from estudios import demo
from estudios.models import Estudio, TipoEstudio, TipoEstudioPrueba
from estudios.servicios import cargar_mediciones, crear_estudio
from muestras.models import Muestra
from pruebas.models import Prueba, TipoCalculo

MESES = 9
VARIACION = (0, 1, -1, 2, -2, 1, 0, -1, 2)
MATRICULA = "MP 4127"
NITRITOS = "Nitritos"
CODIGO_NITRITOS = "NO2"
ABSORBANCIA_NITRITOS = "0.126"


class HistorialError(Exception):
    pass


CORREOS = {
    "lucia": "lucia.fernandez87@gmail.com",
    "martin": "martin.gutierrez72@gmail.com",
    "diego": "diegososa.94@gmail.com",
    "lacteos": "aqualab.real@gmail.com",
    "municipio": "obrassanitariasvv21@gmail.com",
    "mgonzalez": "maria.gonzalez.vv58@gmail.com",
    "cristal": "cristaldelvalle.lab37@gmail.com",
    "pampeana": "lapampeana.ambiente46@gmail.com",
    "club": "clubbragado.intendencia19@gmail.com",
}


def correo(etiqueta):
    return CORREOS[etiqueta]


def usuarios():
    return (
        {
            "email": correo("lucia"),
            "first_name": "Lucía",
            "last_name": "Fernández",
            "grupos": (),
        },
        {
            "email": correo("martin"),
            "first_name": "Martín",
            "last_name": "Gutiérrez",
            "grupos": ("Bioquímicos", "Administradores"),
        },
    )


def recepcion():
    """Usuario sin actividad en el historial: atiende la recepción."""
    return {"email": correo("diego"), "first_name": "Diego", "last_name": "Sosa"}


# Bioquímicos que se suman al laboratorio sin actividad en el historial. Si la cuenta ya existe
# (por ejemplo, el superusuario del deploy), solo se la agrega a Bioquímicos y se le da firma.
BIOQUIMICOS_EXTRA = (
    {
        "email": "juanpidominguez03@gmail.com",
        "first_name": "Juan Pablo",
        "last_name": "Domínguez",
        "matricula": "MP 4389",
    },
)


def clientes():
    return {
        "lacteos": {
            "razon_social": "Lácteos del Sur S.A.",
            "nombre": "",
            "tipo_documento": "CUIT",
            "numero_documento": "30712458905",
            "email": correo("lacteos"),
            "telefono": "02342 41-5500",
            "domicilio": "Ruta 5 km 210, Bragado",
        },
        "municipio": {
            "razon_social": "Municipalidad de Villa Verde",
            "nombre": "",
            "tipo_documento": "CUIT",
            "numero_documento": "30999012341",
            "email": correo("municipio"),
            "telefono": "02346 43-1200",
            "domicilio": "Av. San Martín 450, Villa Verde",
        },
        "particular": {
            "razon_social": "",
            "nombre": "María González",
            "tipo_documento": "DNI",
            "numero_documento": "28417305",
            "email": correo("mgonzalez"),
            "telefono": "11 5555-0101",
            "domicilio": "Los Aromos 1234, Villa Verde",
        },
        "embotelladora": {
            "razon_social": "Aguas Cristal del Valle S.R.L.",
            "nombre": "",
            "tipo_documento": "CUIT",
            "numero_documento": "30715883216",
            "email": correo("cristal"),
            "telefono": "02342 42-8810",
            "domicilio": "Parque Industrial Bragado, Lote 14",
        },
        "frigorifico": {
            "razon_social": "Frigorífico La Pampeana S.A.",
            "nombre": "",
            "tipo_documento": "CUIT",
            "numero_documento": "30689741025",
            "email": correo("pampeana"),
            "telefono": "02342 40-3300",
            "domicilio": "Camino a Mechita km 3, Bragado",
        },
        "club": {
            "razon_social": "Club Social y Deportivo Bragado",
            "nombre": "",
            "tipo_documento": "CUIT",
            "numero_documento": "30527319486",
            "email": correo("club"),
            "telefono": "02342 42-1975",
            "domicilio": "Av. Pellegrini 760, Bragado",
        },
    }


ORIGENES_NUEVOS = (
    demo.OrigenDemo(
        "pozo-captacion",
        "embotelladora",
        "Pozo de captación",
        3,
        "agua",
        "Toma previa al tratamiento",
        "Valeria Ruiz",
        {
            "PH": "7.2",
            "TURBIDEZ": "0.4",
            "COND": "450",
            "CL-": "5.5",
            "DUREZA-T": "8.0",
            "NH4": "0.04",
            "FE": "0.04",
        },
    ),
    demo.OrigenDemo(
        "linea-envasado",
        "embotelladora",
        "Línea de envasado",
        4,
        "agua",
        "Llenadora, después del filtro final",
        "Valeria Ruiz",
        {"COL-TOT": "0", "MESOFILAS": "20", "ECOLI": "0", "PSEUDO": "0"},
    ),
    demo.OrigenDemo(
        "efluente-planta",
        "frigorifico",
        "Efluente de planta",
        18,
        "cloacal",
        "Cámara de salida de la planta de tratamiento",
        "Hernán Acosta",
        {"PH": "7.6", "TEMPERATURA": "27.0", "SS10": "0.08", "SSEE": "45", "DET-SAAM": "3.6"},
    ),
    demo.OrigenDemo(
        "red-club",
        "club",
        "Agua de red del vestuario",
        20,
        "agua",
        "Duchas del vestuario principal",
        "Ricardo Paz",
        {"COL-TOT": "0", "MESOFILAS": "70", "ECOLI": "0", "PSEUDO": "0"},
    ),
)

ESTADOS = {
    **demo.ESTADOS,
    ("linea-envasado", 0, demo.BACT): demo.PENDIENTE,
    ("pozo-captacion", 0, demo.FQ): demo.PARCIAL,
    ("efluente-planta", 0, demo.VUELCO): demo.CARGADO,
    ("red-club", 0, demo.BACT): demo.FINALIZADO,
}


def ya_cargado():
    """El historial ya está si existe su cliente principal o su técnica (aunque después se hayan
    editado el CUIT o el correo desde la app): así un reinicio nunca lo carga dos veces."""
    from django.contrib.auth import get_user_model

    return (
        Cliente.objects.filter(razon_social="Lácteos del Sur S.A.").exists()
        or get_user_model().objects.filter(email__iexact=correo("lucia")).exists()
    )


def crear_personal(inicio):
    from django.contrib.auth import get_user_model
    from django.contrib.auth.models import Group

    from informes.models import FirmaProfesional

    Usuario = get_user_model()
    contrasena = os.environ["AQUALAB_HISTORIAL_CONTRASENA"]
    datos = recepcion()
    if not Usuario.objects.filter(email__iexact=datos["email"]).exists():
        Usuario.objects.create_user(
            password=contrasena, is_active=True, date_joined=inicio, **datos
        )
    bioquimicos = Group.objects.get(name="Bioquímicos")
    for extra in BIOQUIMICOS_EXTRA:
        extra = dict(extra)
        matricula = extra.pop("matricula")
        usuario = Usuario.objects.filter(email__iexact=extra["email"]).first()
        if usuario is None:
            usuario = Usuario.objects.create_user(
                password=contrasena, is_active=True, date_joined=inicio, **extra
            )
        usuario.groups.add(bioquimicos)
        if not FirmaProfesional.objects.filter(usuario=usuario).exists():
            with demo.reloj(inicio):
                FirmaProfesional.objects.create(
                    usuario=usuario, imagen=demo.firma_png(), matricula=matricula
                )


def preparar_nitritos(ahora):
    """Estudio de Nitritos del Pozo 1 con la absorbancia cargada y sin curva vigente: al guardar
    la curva en vivo, «Calcularlas con esta curva» da 0,2501 mg/l."""
    from django.contrib.auth import get_user_model

    prueba, _ = Prueba.objects.get_or_create(
        codigo=CODIGO_NITRITOS,
        defaults={
            "nombre": "Nitritos",
            "tipo_calculo": TipoCalculo.CURVA,
            "unidad": "mg/l",
            "unidad_medicion": "Abs",
            "norma": "Código Alimentario Argentino, art. 982",
            "limite_max": "0.1",
        },
    )
    tipo = TipoEstudio.objects.filter(nombre__iexact=NITRITOS).first()
    if tipo is None:
        tipo = TipoEstudio.objects.create(
            nombre=NITRITOS, descripcion="Nitritos por espectrofotometría (curva de calibración)."
        )
        TipoEstudioPrueba.objects.create(tipo=tipo, prueba=prueba)
    tecnica = get_user_model().objects.get(email=usuarios()[0]["email"])
    muestra = (
        Muestra.objects.filter(
            origen__nombre="Pozo 1", cliente__razon_social="Lácteos del Sur S.A."
        )
        .order_by("-fecha_muestreo")
        .first()
    )
    momento = min(ahora, timezone.now()) - dt.timedelta(hours=3)
    with demo.reloj(momento):
        estudio = crear_estudio(
            {
                "clave": demo.clave("historial", "nitritos", "estudio"),
                "muestra": muestra.pk,
                "tipo": tipo.pk,
                "version": tipo.version,
            },
            tecnica,
        )
        asignacion = estudio.pruebas_asignadas.get(prueba=prueba)
        cargar_mediciones(estudio.pk, {asignacion.pk: Decimal(ABSORBANCIA_NITRITOS)}, tecnica)
    return estudio


# Correcciones de un historial ya cargado: los primeros CUIT tenían mal el dígito verificador (el
# formulario de edición no los acepta y no deja cambiar el documento de un cliente con muestras) y
# Lácteos del Sur debe recibir los correos en la casilla de Resend.
CUIT_CORREGIDOS = {
    "30712458903": "30712458905",
    "30999012347": "30999012341",
    "30527319480": "30527319486",
}


def corregir_historial():
    """Aplica las correcciones sobre un historial ya cargado. Devuelve cuántos clientes cambió."""
    cambiados = 0
    with transaction.atomic():
        for viejo, nuevo in CUIT_CORREGIDOS.items():
            cambiados += Cliente.objects.filter(numero_documento=viejo).update(
                numero_documento=nuevo
            )
        cambiados += (
            Cliente.objects.filter(razon_social="Lácteos del Sur S.A.")
            .exclude(email=correo("lacteos"))
            .update(email=correo("lacteos"))
        )
    return cambiados


def cargar_historial(salida, ahora=None):
    """Carga el historial. Devuelve el resumen de la demo, o None si ya estaba cargado."""
    contrasena = os.environ.get("AQUALAB_HISTORIAL_CONTRASENA", "")
    if len(contrasena) < 8:
        raise HistorialError(
            "Definí AQUALAB_HISTORIAL_CONTRASENA (8 caracteres o más): es la contraseña de los "
            "usuarios del laboratorio."
        )
    if ya_cargado():
        return None
    ahora = ahora or timezone.now()
    origenes = demo.ORIGENES + ORIGENES_NUEVOS
    with (
        transaction.atomic(),
        mock.patch.multiple(
            demo,
            MESES=MESES,
            VARIACION=VARIACION,
            CONTRASENA=contrasena,
            MATRICULA=MATRICULA,
            USUARIOS=usuarios(),
            CLIENTES=clientes(),
            ORIGENES=origenes,
            POR_CLAVE={o.clave: o for o in origenes},
            ESTADOS=ESTADOS,
            ya_cargada=ya_cargado,
        ),
    ):
        resumen = demo.cargar_demo(salida, ahora=ahora)
        if resumen is None:
            return None
        inicio = demo.Fechas(ahora, origenes[0], 0, MESES - 1).muestreo - dt.timedelta(days=7)
        crear_personal(inicio)
        preparar_nitritos(ahora)
    return resumen


def estudios_del_historial():
    return Estudio.objects.filter(
        muestra__cliente__numero_documento__in=[c["numero_documento"] for c in clientes().values()]
    )
