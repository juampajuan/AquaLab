import os
from datetime import date
from uuid import NAMESPACE_URL, uuid5

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import DatabaseError, connection, transaction

from clientes.models import Cliente
from estudios.models import TipoEstudio, TipoEstudioPrueba
from muestras.models import Muestra, Origen
from muestras.servicios import registrar_muestra
from pruebas.models import Prueba

PREFIJO = "[DEMO FIUBA US51]"
DESCRIPCION = f"{PREFIJO} Asociación ficticia para demostrar software, sin validez científica."
FECHA = date(2026, 10, 27)
NAMESPACE_DEMO = NAMESPACE_URL
CLAVE_LOCK_DEMO = 5_100_002
TIPOS = (
    ("Bacteriológico", (1, 2), True),
    ("Físico-Químico", (2, 3), True),
    ("Vuelco a canal", (1, 3), True),
    ("Tipo desactivado", (1,), False),
)


def clave_muestra(letra):
    return uuid5(NAMESPACE_DEMO, f"demo-fiuba-us51:v1:muestra:{letra}")


class Command(BaseCommand):
    help = "Simula o carga explícitamente datos ficticios FIUBA de US 5.1; no crea estudios."

    def add_arguments(self, parser):
        parser.add_argument(
            "--usuario", required=True, help="Correo de un usuario activo existente."
        )
        modo = parser.add_mutually_exclusive_group()
        modo.add_argument("--dry-run", action="store_true", help="Solo inspección, sin escrituras.")
        modo.add_argument(
            "--aplicar", action="store_true", help="Aplicar altas demo en desarrollo/QA."
        )

    def handle(self, *args, **options):
        entorno = os.environ.get("AQUALAB_ENTORNO", "").strip().lower()
        if entorno not in {"desarrollo", "qa"} or not settings.DEBUG:
            raise CommandError(
                "Requiere AQUALAB_ENTORNO=desarrollo o qa y DEBUG=True. No producción."
            )
        if connection.vendor != "postgresql":
            raise CommandError("La carga demo requiere PostgreSQL.")
        usuario = (
            get_user_model()
            .objects.filter(email__iexact=options["usuario"].strip(), is_active=True)
            .first()
        )
        if usuario is None:
            raise CommandError("El usuario debe existir y estar activo; no se crean cuentas.")
        aplicar = options["aplicar"]
        self.stdout.write(
            f"{'APLICAR' if aplicar else 'SIMULACIÓN'} · entorno={entorno} · "
            f"base={connection.settings_dict['NAME']} · motor={connection.vendor}"
        )
        self.resultados = []
        try:
            if aplicar:
                with transaction.atomic():
                    with connection.cursor() as cursor:
                        cursor.execute("SELECT pg_advisory_xact_lock(%s)", [CLAVE_LOCK_DEMO])
                    # Revalidar el usuario dentro de la transacción, sin modificarlo.
                    usuario.refresh_from_db()
                    if not usuario.is_active:
                        raise CommandError("El usuario ya no está activo.")
                    self.cargar(usuario, guardar=True)
            else:
                self.cargar(usuario, guardar=False)
        except (ValidationError, DatabaseError) as exc:
            # No mostrar SQL, credenciales o detalles de registros ajenos.
            raise CommandError(
                "La demo no pasó la validación o hubo un conflicto de base de datos. "
                "No se aplicaron altas; revisar las identidades y reintentar."
            ) from exc
        for mensaje in self.resultados:
            self.stdout.write(mensaje)
        self.stdout.write(
            self.style.SUCCESS(
                "Carga finalizada; no se crearon estudios."
                if aplicar
                else "Simulación sin escrituras. Para cargar, ejecutar explícitamente --aplicar."
            )
        )

    def resolver(self, modelo, filtro, valores, *, guardar, excluir=()):
        existente = modelo.objects.filter(**filtro).first() if filtro is not None else None
        if existente is not None:
            if any(getattr(existente, campo) != valor for campo, valor in valores.items()):
                raise CommandError(
                    f"Colisión o divergencia en {modelo.__name__}; no se sobrescriben registros."
                )
            existente.full_clean()
            self.resultados.append(f"REUTILIZAR {modelo.__name__} id={existente.pk}")
            return existente, False
        objeto = modelo(**valores)
        objeto.full_clean(exclude=excluir)
        if guardar:
            objeto.save()
        self.resultados.append(f"ALTA {modelo.__name__} {valores.get('nombre', '')}")
        return objeto, True

    def cargar(self, usuario, *, guardar):
        for letra, numero, activo in (("A", "99000001", True), ("B", "99000002", False)):
            self.cargar_muestra(usuario, letra, numero, activo, guardar=guardar)
        pruebas = {}
        for numero, letra in enumerate("ABC", start=1):
            prueba, _ = self.resolver(
                Prueba,
                {"codigo": f"DEMO-US51-P{numero:02}"},
                {"codigo": f"DEMO-US51-P{numero:02}", "nombre": f"{PREFIJO} Prueba {letra}"},
                guardar=guardar,
            )
            pruebas[numero] = prueba
        # Orden determinista para tomar los locks de las filas existentes.
        for nombre, numeros, activo in sorted(TIPOS):
            nombre = f"{PREFIJO} {nombre}"
            if guardar:
                list(TipoEstudio.objects.select_for_update().filter(nombre__iexact=nombre))
            tipo, nuevo = self.resolver(
                TipoEstudio,
                {"nombre__iexact": nombre},
                {"nombre": nombre, "descripcion": DESCRIPCION, "activo": activo, "version": 1},
                guardar=guardar,
            )
            if not nuevo:
                esperadas = {pruebas[n].pk for n in numeros}
                actuales = set(tipo.pruebas.values_list("pk", flat=True))
                if None in esperadas or actuales != esperadas:
                    raise CommandError("Divergencia de composición demo; no se modifica el tipo.")
            elif guardar:
                for numero in numeros:
                    TipoEstudioPrueba.objects.create(tipo=tipo, prueba=pruebas[numero])
            self.resultados.append(f"COMPOSICIÓN {nombre}: {len(numeros)} pruebas ficticias")

    def cargar_muestra(self, usuario, letra, numero, activo, *, guardar):
        cliente, cliente_nuevo = self.resolver(
            Cliente,
            {"tipo_documento": "DNI", "numero_documento": numero},
            {
                "tipo_documento": "DNI",
                "numero_documento": numero,
                "nombre": f"{PREFIJO} Cliente {'activo' if activo else 'inactivo'}",
                "razon_social": "",
                "telefono": "",
                "domicilio": "",
                "email": f"demo-us51-{'activo' if activo else 'inactivo'}@example.invalid",
                "activo": activo,
            },
            guardar=False,
        )
        if guardar and cliente_nuevo:
            cliente.activo = True
            cliente.save()
        origen, _ = self.resolver(
            Origen,
            {"cliente_id": cliente.pk, "nombre__iexact": f"{PREFIJO} Origen {letra}"}
            if cliente.pk
            else None,
            {"cliente_id": cliente.pk, "nombre": f"{PREFIJO} Origen {letra}"},
            guardar=guardar,
            excluir=() if cliente.pk else ("cliente",),
        )
        valores = {
            "clave_borrador": clave_muestra(letra),
            "cliente_id": cliente.pk,
            "origen_id": origen.pk,
            "nombre": f"{PREFIJO} Muestra {letra}",
            "fecha_muestreo": FECHA,
            "fecha_ingreso": FECHA,
            "sitio_extraccion": f"{PREFIJO} Sitio {letra}",
            "responsable_muestreo": f"{PREFIJO} Muestreador ficticio",
            "tipo_vertido": "agua",
            "estado": "ingresada",
            "registrada_por_id": usuario.pk,
        }
        muestra, nueva = self.resolver(
            Muestra,
            {"clave_borrador": clave_muestra(letra)},
            valores,
            guardar=False,
            excluir=("numero_pi",)
            + tuple(campo for campo in ("cliente", "origen") if valores[f"{campo}_id"] is None),
        )
        if nueva and not cliente_nuevo and not cliente.activo:
            raise CommandError("Cliente demo inactivo sin su muestra esperada; no se reactiva.")
        if guardar and nueva:
            muestra = registrar_muestra(
                {
                    "clave_borrador": clave_muestra(letra),
                    "cliente": cliente.pk,
                    "origen": origen.pk,
                    "origen_nuevo": "",
                    "nombre": valores["nombre"],
                    "fecha_muestreo": FECHA.isoformat(),
                    "fecha_ingreso": FECHA.isoformat(),
                    "sitio_extraccion": valores["sitio_extraccion"],
                    "tipo_vertido": "agua",
                    "responsable_muestreo": valores["responsable_muestreo"],
                },
                usuario,
            )
            # Otro escritor con el mismo UUID nunca puede apropiarse del manifiesto.
            if any(getattr(muestra, c) != v for c, v in valores.items()):
                raise CommandError("Colisión concurrente de muestra demo; carga revertida.")
            muestra.full_clean()
        if guardar and cliente_nuevo and not activo:
            cliente.activo = False
            cliente.save(update_fields=["activo"])
        if muestra.pk:
            self.resultados.append(f"MUESTRA {letra}: PI {muestra.numero_pi}")
