"""Preparar el registro de una muestra o de un estudio desde el asistente (US 10.3,
contracts/herramientas.md).

Las herramientas no crean nada: corren como las de consulta, en la transacción de solo lectura de
`herramientas.ejecutar`. El modelo las llama en cada mensaje con todo lo que dijo el empleado;
AquaLab lo resuelve con las reglas de las pantallas y devuelve qué falta, qué no coincide (con
opciones para elegir) o, con todo completo, el enlace al formulario de siempre precargado
(research R1, R3, R5). Nada del pedido se guarda.
"""

from dataclasses import dataclass, field, replace

from django.utils import timezone

from .enlaces import Referencia, normalizar
from .fechas import leer_fecha
from .herramientas import (
    FORMATO_FECHA,
    MAX_LISTA,
    MAX_NUMERO_SQL,
    Salida,
    no_encontrado,
    puede_ver,
    referencia_cliente,
    referencia_muestra,
    registrar,
)

AVISO_MUESTRA = "La muestra se registra recién cuando confirmes en el formulario."
AVISO_ESTUDIO = "El estudio se crea recién cuando confirmes en la pantalla de crear estudio."
SOLO_MUESTRA = Referencia(
    "opcion", None, "Solo registrar la muestra", pregunta="Solo registrar la muestra, sin estudio"
)
REGISTRAR_CLIENTE = Referencia("registrar_cliente", None, "Registrar cliente")
# Campos que reúne el asistente: solo sus errores del formulario se informan (research R4).
CAMPOS_DEL_ASISTENTE = (
    "cliente",
    "origen",
    "origen_nuevo",
    "fecha_muestreo",
    "fecha_ingreso",
    "sitio_extraccion",
    "tipo_vertido",
)
# Datos opcionales: se precargan si se dijeron, sin preguntarlos, con el largo del formulario.
OPCIONALES = (("nombre", 100), ("responsable_muestreo", 150))


@dataclass
class Resolucion:
    """Resultado de buscar un dato: el valor encontrado, un problema o las opciones a elegir."""

    valor: object = None
    problema: str = ""
    opciones: list = field(default_factory=list)


def con_punto(texto):
    """Cierra la oración sin duplicar el punto de «S.A.»."""
    return texto if texto.endswith(".") else f"{texto}."


def _iguales(a, b):
    return normalizar(a).strip() == normalizar(b).strip()


def _contiene(texto, nombre):
    return normalizar(texto).strip() in normalizar(nombre)


def resolver_cliente(usuario, texto):
    from clientes.models import Cliente
    from clientes.views import buscar_clientes, filtro_clientes

    activos = list(buscar_clientes(texto)[: MAX_LISTA + 1])
    exactos = [c for c in activos if _iguales(texto, c.nombre_completo)]
    if len(exactos) == 1 or len(activos) == 1:
        return Resolucion(valor=(exactos or activos)[0])
    if activos:
        return Resolucion(
            opciones=[
                replace(r, pregunta=f"El cliente es {c.nombre_completo}")
                for c in activos[:MAX_LISTA]
                for r in referencia_cliente(usuario, c)
            ]
        )
    inactivo = (
        Cliente.objects.filter(filtro_clientes(texto), activo=False)
        .order_by(*Cliente._meta.ordering)
        .first()
    )
    if inactivo is not None:
        return Resolucion(problema=f"El cliente «{inactivo.nombre_completo}» está inactivo.")
    return Resolucion(problema=f"No hay ningún cliente activo que coincida con «{texto}».")


def _opciones_de_origenes(origenes, texto):
    return [
        *(
            Referencia("opcion", None, o.nombre, pregunta=f"El origen es {o.nombre}")
            for o in origenes
        ),
        Referencia(
            "opcion",
            None,
            "Registrarlo como origen nuevo",
            pregunta=f"Registrar «{texto}» como origen nuevo",
        ),
    ]


def resolver_origen(cliente, texto, nuevo):
    """Un origen existente (sin distinguir mayúsculas ni acentos, como la reutilización de
    `muestras.servicios`) o el texto como origen nuevo, si el empleado lo eligió."""
    origenes = list(cliente.origenes.order_by("nombre", "pk"))
    exactos = [o for o in origenes if _iguales(texto, o.nombre)]
    if exactos:
        return Resolucion(valor=exactos[0])
    if nuevo:
        return Resolucion(valor=texto.strip())
    parecidos = [o for o in origenes if _contiene(texto, o.nombre)]
    if len(parecidos) == 1:
        return Resolucion(valor=parecidos[0])
    if parecidos:
        return Resolucion(opciones=_opciones_de_origenes(parecidos[: MAX_LISTA - 1], texto))
    return Resolucion(
        problema=con_punto(f"«{texto}» no es un origen de {cliente.nombre_completo}"),
        opciones=_opciones_de_origenes(origenes[: MAX_LISTA - 1], texto),
    )


def resolver_vertido(texto):
    """Agua, Cloacal o Canal (por valor o etiqueta). Nunca se supone (aclaración de la prueba
    manual): sin texto o con uno desconocido, se ofrece elegir."""
    from muestras.models import TipoVertido

    opciones = [
        Referencia("opcion", None, etiqueta, pregunta=f"El tipo de vertido es {etiqueta}")
        for _, etiqueta in TipoVertido.choices
    ]
    if not texto:
        return Resolucion(opciones=opciones)
    normal = normalizar(texto).strip()
    for valor, etiqueta in TipoVertido.choices:
        if normal in (valor, normalizar(etiqueta)):
            return Resolucion(valor=TipoVertido(valor))
    return Resolucion(
        problema=f"No reconozco el tipo de vertido «{texto}»: elegí Agua, Cloacal o Canal.",
        opciones=opciones,
    )


def _opciones_de_tipos(tipos, con_solo_muestra):
    opciones = [SOLO_MUESTRA] if con_solo_muestra else []
    tope = MAX_LISTA - len(opciones)
    return opciones + [
        Referencia("opcion", None, t.nombre, pregunta=f"El tipo de estudio es {t.nombre}")
        for t in tipos[:tope]
    ]


def resolver_tipo(texto, con_solo_muestra):
    from estudios.models import TipoEstudio

    activos = list(TipoEstudio.objects.filter(activo=True))
    if not texto:
        return Resolucion(opciones=_opciones_de_tipos(activos, con_solo_muestra))
    exactos = [t for t in activos if _iguales(texto, t.nombre)]
    parecidos = exactos or [t for t in activos if _contiene(texto, t.nombre)]
    if len(parecidos) == 1:
        return Resolucion(valor=parecidos[0])
    if parecidos:
        return Resolucion(opciones=_opciones_de_tipos(parecidos, con_solo_muestra))
    inactivo = next(
        (
            t
            for t in TipoEstudio.objects.filter(activo=False)
            if _iguales(texto, t.nombre) or _contiene(texto, t.nombre)
        ),
        None,
    )
    problema = (
        f"El tipo «{inactivo.nombre}» no está activo."
        if inactivo
        else f"No hay ningún tipo de estudio activo que coincida con «{texto}»."
    )
    return Resolucion(problema=problema, opciones=_opciones_de_tipos(activos, con_solo_muestra))


@dataclass
class Pedido:
    """Estado de una vuelta de `preparar_*`. Se arma en cada llamada y nunca se guarda."""

    resuelto: dict = field(default_factory=dict)
    faltan: list = field(default_factory=list)
    problemas: list = field(default_factory=list)
    elegir: str | None = None
    opciones: list = field(default_factory=list)
    primeras: list = field(default_factory=list)
    # Cómo se nombra un dato en el resumen «Hasta ahora», si difiere de `resuelto`.
    breve: dict = field(default_factory=dict)

    @property
    def listo(self):
        return not (self.faltan or self.problemas or self.elegir)

    def anotar(self, campo, resolucion):
        """Registra un problema o las opciones (solo las de la primera elección pendiente)."""
        if resolucion.problema:
            self.problemas.append(resolucion.problema)
        if resolucion.opciones and self.elegir is None:
            self.elegir = campo
            self.opciones = resolucion.opciones

    def resumen(self, etiquetas):
        partes = [
            f"{etiqueta}: {self.breve.get(c, self.resuelto[c])}"
            for c, etiqueta in etiquetas
            if c in self.resuelto
        ]
        return f"Hasta ahora: {' · '.join(partes)}." if partes else None

    def salida(self, aviso_listo, etiquetas):
        datos = {
            "encontrado": True,
            "listo": self.listo,
            "resuelto": self.resuelto,
            "faltan": self.faltan,
            "problemas": self.problemas,
            "elegir": self.elegir,
        }
        if self.elegir:
            datos["opciones_para_elegir"] = len(self.opciones)
        if self.listo:
            avisos = [aviso_listo]
        else:
            avisos = [r] if (r := self.resumen(etiquetas)) else []
        return Salida(datos, avisos=avisos, primeras=self.primeras, opciones=self.opciones)


ETIQUETAS_MUESTRA = (
    ("cliente", "Cliente"),
    ("origen", "Origen"),
    ("tipo_estudio", "Tipo de estudio"),
    ("tipo_vertido", "Vertido"),
    ("fecha_muestreo", "Muestreo"),
    ("fecha_ingreso", "Ingreso"),
    ("sitio_extraccion", "Sitio"),
)
ETIQUETAS_ESTUDIO = (("muestra", "Muestra"), ("tipo_estudio", "Tipo de estudio"))


def _errores_del_formulario(cliente, origen, fechas, sitio, vertido):
    """Errores de `RegistroMuestraForm` en los campos que reúne el asistente: la única regla de
    fechas, orígenes y largos (FR-007)."""
    from muestras.forms import RegistroMuestraForm

    form = RegistroMuestraForm(
        data={
            "cliente": cliente.pk,
            "origen": origen.pk if hasattr(origen, "pk") else "",
            "origen_nuevo": "" if hasattr(origen, "pk") else origen,
            "fecha_muestreo": fechas["fecha_muestreo"].isoformat(),
            "fecha_ingreso": fechas["fecha_ingreso"].isoformat(),
            "sitio_extraccion": sitio,
            "tipo_vertido": vertido.value,
        }
    )
    form.is_valid()
    return [str(e) for campo in CAMPOS_DEL_ASISTENTE for e in form.errors.get(campo, [])]


def _parametros_opcionales(argumentos):
    """Los opcionales dichos que el formulario acepta; el resto no viaja (FR-007)."""
    parametros = []
    for campo, largo in OPCIONALES:
        valor = (argumentos.get(campo) or "").strip()
        if 0 < len(valor) <= largo:
            parametros.append((campo, valor))
    return parametros


TEXTO = {"type": "string"}


@registrar(
    {
        "type": "function",
        "function": {
            "name": "preparar_muestra",
            "description": (
                "Prepara el registro de una muestra. Llamala con todos los datos que el empleado "
                "dijo hasta ahora en la conversación, como texto, aunque ya la hayas llamado. "
                "AquaLab los busca en el sistema y dice qué falta o qué no coincide. No crea "
                "nada: cuando está todo, AquaLab agrega el enlace al formulario."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "cliente": {**TEXTO, "description": "Nombre o razón social."},
                    "origen": {**TEXTO, "description": "Origen, como «pozo 2»."},
                    "origen_nuevo": {
                        "type": "boolean",
                        "description": "true solo si eligió «Registrarlo como origen nuevo».",
                    },
                    "fecha_muestreo": {**TEXTO, "description": "Tal cual: «ayer», «12/11»."},
                    "fecha_ingreso": {**TEXTO, "description": "Tal cual: «hoy», «12/11»."},
                    "tipo_estudio": {**TEXTO, "description": "Nombre del tipo de estudio."},
                    "solo_muestra": {
                        "type": "boolean",
                        "description": "true si eligió «Solo registrar la muestra».",
                    },
                    "sitio_extraccion": {**TEXTO, "description": "Tal cual lo dijo."},
                    "tipo_vertido": {**TEXTO, "description": "Agua, Cloacal o Canal."},
                    "nombre": TEXTO,
                    "responsable_muestreo": TEXTO,
                },
            },
        },
    }
)
def preparar_muestra(usuario, **argumentos):
    if not puede_ver(usuario, "registro"):
        return no_encontrado("No se pudo consultar.")
    pedido = Pedido()
    texto_cliente = (argumentos.get("cliente") or "").strip()
    texto_origen = (argumentos.get("origen") or "").strip()
    texto_tipo = (argumentos.get("tipo_estudio") or "").strip()
    solo_muestra = argumentos.get("solo_muestra") is True

    cliente = origen = tipo = None
    if not texto_cliente:
        pedido.faltan.append("cliente")
    else:
        resolucion = resolver_cliente(usuario, texto_cliente)
        pedido.anotar("cliente", resolucion)
        if resolucion.valor is not None:
            cliente = resolucion.valor
            pedido.resuelto["cliente"] = cliente.nombre_completo
        elif resolucion.problema:
            pedido.primeras.append(REGISTRAR_CLIENTE)

    if not texto_origen:
        pedido.faltan.append("origen")
    elif cliente is not None:
        resolucion = resolver_origen(cliente, texto_origen, argumentos.get("origen_nuevo") is True)
        pedido.anotar("origen", resolucion)
        origen = resolucion.valor
        if hasattr(origen, "pk"):
            pedido.resuelto["origen"] = origen.nombre
        elif origen:
            pedido.resuelto["origen"] = f"{origen} (origen nuevo)"

    if solo_muestra:
        pedido.resuelto["tipo_estudio"] = "sin estudio"
    else:
        resolucion = resolver_tipo(texto_tipo, con_solo_muestra=True)
        if not texto_tipo:
            pedido.faltan.append("tipo de estudio")
        pedido.anotar("tipo_estudio", resolucion)
        if resolucion.valor is not None:
            tipo = resolucion.valor
            pedido.resuelto["tipo_estudio"] = tipo.nombre

    texto_vertido = (argumentos.get("tipo_vertido") or "").strip()
    resolucion = resolver_vertido(texto_vertido)
    if not texto_vertido:
        pedido.faltan.append("tipo de vertido")
    pedido.anotar("tipo_vertido", resolucion)
    vertido = resolucion.valor
    if vertido is not None:
        pedido.resuelto["tipo_vertido"] = vertido.label

    hoy = timezone.localdate()
    fechas = {}
    for campo, etiqueta in (("fecha_muestreo", "muestreo"), ("fecha_ingreso", "ingreso")):
        texto = (argumentos.get(campo) or "").strip()
        if not texto:
            pedido.faltan.append(f"fecha de {etiqueta}")
        elif (fecha := leer_fecha(texto, hoy)) is None:
            pedido.faltan.append(f"fecha de {etiqueta} (no entendí «{texto}»)")
        else:
            fechas[campo] = fecha
            pedido.resuelto[campo] = fecha.strftime(FORMATO_FECHA)

    sitio = (argumentos.get("sitio_extraccion") or "").strip()
    if sitio:
        pedido.resuelto["sitio_extraccion"] = sitio
    else:
        pedido.faltan.append("sitio de extracción")

    if cliente is not None and origen and len(fechas) == 2 and sitio and vertido is not None:
        pedido.problemas.extend(_errores_del_formulario(cliente, origen, fechas, sitio, vertido))

    if pedido.listo:
        parametros = [("cliente", str(cliente.pk))]
        if hasattr(origen, "pk"):
            parametros.append(("origen", str(origen.pk)))
        else:
            parametros.append(("origen_nuevo", origen))
        parametros += [(c, fechas[c].isoformat()) for c in ("fecha_muestreo", "fecha_ingreso")]
        parametros += [("sitio_extraccion", sitio), ("tipo_vertido", vertido.value)]
        parametros += _parametros_opcionales(argumentos)
        if tipo is not None:
            parametros.append(("tipo_estudio", str(tipo.pk)))
        pedido.primeras.append(
            Referencia(
                "registrar_muestra",
                None,
                "Revisar y registrar la muestra",
                parametros=tuple(parametros),
                minimizar=True,
            )
        )
    return pedido.salida(AVISO_MUESTRA, ETIQUETAS_MUESTRA)


@registrar(
    {
        "type": "function",
        "function": {
            "name": "preparar_estudio",
            "description": (
                "Prepara la creación de un estudio para una muestra ya registrada. Llamala con el "
                "N° PI y el tipo de estudio que dijo el empleado. No crea nada."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "numero_pi": {"type": "integer", "description": "N° PI de la muestra."},
                    "tipo_estudio": {**TEXTO, "description": "Nombre del tipo de estudio."},
                },
            },
        },
    }
)
def preparar_estudio(usuario, numero_pi=None, tipo_estudio=None):
    from muestras.models import Muestra

    if not puede_ver(usuario, "registro"):
        return no_encontrado("No se pudo consultar.")
    pedido = Pedido()
    muestra = tipo = None
    if numero_pi is None:
        pedido.faltan.append("N° PI de la muestra")
    else:
        if 0 < numero_pi <= MAX_NUMERO_SQL:
            muestra = (
                Muestra.objects.select_related("cliente", "origen")
                .filter(numero_pi=numero_pi)
                .first()
            )
        if muestra is None:
            pedido.problemas.append(f"No hay ninguna muestra con el N° PI {numero_pi}.")
        else:
            pedido.resuelto["muestra"] = (
                f"PI {muestra.numero_pi} · {muestra.cliente.nombre_completo} · "
                f"{muestra.origen.nombre}"
            )
            pedido.breve["muestra"] = f"PI {muestra.numero_pi}"
    texto_tipo = (tipo_estudio or "").strip()
    if muestra is not None or numero_pi is None:
        resolucion = resolver_tipo(texto_tipo, con_solo_muestra=False)
        if not texto_tipo:
            pedido.faltan.append("tipo de estudio")
        pedido.anotar("tipo_estudio", resolucion)
        if resolucion.valor is not None:
            tipo = resolucion.valor
            pedido.resuelto["tipo_estudio"] = tipo.nombre
    if pedido.listo:
        pedido.primeras += [
            Referencia(
                "crear_estudio",
                None,
                "Revisar y crear el estudio",
                parametros=(("muestra", str(muestra.pk)), ("tipo", str(tipo.pk))),
                minimizar=True,
            ),
            referencia_muestra(muestra),
        ]
    return pedido.salida(AVISO_ESTUDIO, ETIQUETAS_ESTUDIO)
