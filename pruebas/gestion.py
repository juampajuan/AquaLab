"""Gestión del catálogo de pruebas desde la app (SCRUM-73).

`gestionar_prueba` es la única escritura: revalida el permiso del panel de administración,
bloquea la fila, controla la versión y aplica todas las reglas (en uso, referencias en fórmulas,
límites, fórmula y reemplazo en cascada). `validar_datos` es la única validación de los datos del
formulario: la usan el formulario (para mostrar los errores junto a cada campo) y el servicio.
Ver specs/035-gestionar-catalogo-pruebas/.
"""

import re
from dataclasses import dataclass

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .formulas import FormulaInvalida, validar_formula
from .limites import NUMERO, TEXTOS_AUSENTE
from .models import LimiteVertido, Prueba, TipoCalculo, TipoVertido, referencias_formula

OPERACIONES = ("crear", "editar", "desactivar", "reactivar", "eliminar", "reemplazar")
CAMPOS_METODO = ("codigo", "nombre", "tipo_calculo", "formula", "unidad_medicion", "unidad")
CAMPOS_TEXTO = (
    "codigo",
    "nombre",
    "formula",
    "unidad_medicion",
    "unidad",
    "limite_min",
    "limite_max",
    "norma",
    "limite_deteccion",
    "observacion",
)
VERTIDOS = tuple(valor for valor, _ in TipoVertido.choices)
MAXIMOS = {
    "codigo": 50,
    "nombre": 150,
    "formula": 255,
    "unidad_medicion": 50,
    "unidad": 50,
    "limite_min": 50,
    "limite_max": 50,
    "norma": 150,
    "limite_deteccion": 50,
}

MENSAJE_EN_USO = (
    "Esta prueba ya se usa en tipos de estudio o estudios: su método no se puede cambiar. Para "
    "cambiarlo, creá una prueba nueva y desactivá esta."
)
MENSAJE_LIMITE = "Escribí un número o “Ausente”."
MENSAJE_RANGO = "El mínimo no puede superar al máximo."
MENSAJE_VERSION = "La prueba cambió mientras la editabas. Revisá los datos actuales."
MENSAJE_REEMPLAZO = "Elegí una prueba activa con la misma unidad que no dependa de esta."
MENSAJE_UNIDAD_REEMPLAZO = "La prueba nueva tiene que tener la misma unidad del resultado."
MENSAJE_FORMULA_REEMPLAZO = (
    "La fórmula no puede usar la prueba que reemplaza ni las que dependen de ella."
)


class GestionPruebaError(Exception):
    pass


class NoAutorizado(GestionPruebaError):
    pass


class PruebaNoExiste(GestionPruebaError):
    pass


class VersionDesactualizada(GestionPruebaError):
    def __init__(self):
        super().__init__(MENSAJE_VERSION)


class PruebaEnUso(GestionPruebaError):
    def __init__(self, mensaje=MENSAJE_EN_USO):
        super().__init__(mensaje)


class PruebaReferenciada(GestionPruebaError):
    def __init__(self, codigos, accion="eliminar ni cambiar su código"):
        self.codigos = sorted(codigos)
        super().__init__(f"La usan en su fórmula: {', '.join(self.codigos)}. No se puede {accion}.")


class DatosInvalidos(GestionPruebaError):
    def __init__(self, errores):
        self.errores = errores
        super().__init__("Revisá los datos de la prueba.")


@dataclass(frozen=True)
class Resultado:
    estado: str
    prueba_id: int | None
    reemplazo: str = ""


# --- Lecturas --------------------------------------------------------------------------------


def dependientes(prueba, *, solo_activas=False):
    """Pruebas cuya fórmula referencia `{CODIGO}` de esta (el catálogo tiene ~100 filas)."""
    consulta = Prueba.objects.filter(tipo_calculo=TipoCalculo.FORMULA).exclude(pk=prueba.pk)
    if solo_activas:
        consulta = consulta.filter(activa=True)
    return [
        p for p in consulta.order_by("codigo") if prueba.codigo in referencias_formula(p.formula)
    ]


def dependientes_transitivas(prueba):
    """Pruebas que la usan directa o indirectamente (para no elegirlas como reemplazo)."""
    encontradas, por_revisar = {}, [prueba]
    while por_revisar:
        actual = por_revisar.pop()
        for otra in dependientes(actual):
            if otra.pk not in encontradas and otra.pk != prueba.pk:
                encontradas[otra.pk] = otra
                por_revisar.append(otra)
    return list(encontradas.values())


def tipos_afectados(prueba):
    """Tipos de estudio activos que la incluyen, con `sin_otra_activa` si no les queda otra."""
    from estudios.models import TipoEstudio

    filas = []
    for tipo in TipoEstudio.objects.filter(activo=True, pruebas=prueba).order_by("nombre", "pk"):
        otras = tipo.pruebas.filter(activa=True).exclude(pk=prueba.pk).exists()
        filas.append({"tipo": tipo, "sin_otra_activa": not otras})
    return filas


def dependencias_inactivas():
    """`{prueba_id: [códigos inactivos que referencia]}` para las pruebas activas."""
    inactivas = set(Prueba.objects.filter(activa=False).values_list("codigo", flat=True))
    if not inactivas:
        return {}
    resultado = {}
    for prueba in Prueba.objects.filter(activa=True, tipo_calculo=TipoCalculo.FORMULA):
        if usadas := sorted(referencias_formula(prueba.formula) & inactivas):
            resultado[prueba.pk] = usadas
    return resultado


def candidatas_reemplazo(prueba):
    """Pruebas activas con la misma unidad del resultado que no son ella ni dependen de ella."""
    excluidas = {prueba.pk} | {p.pk for p in dependientes_transitivas(prueba)}
    return list(
        Prueba.objects.filter(activa=True, unidad=prueba.unidad)
        .exclude(pk__in=excluidas)
        .order_by("codigo")
    )


def datos_de(prueba):
    """Los datos de una prueba con la forma de `validar_datos` (para el formulario de edición)."""
    datos = {campo: getattr(prueba, campo) for campo in CAMPOS_TEXTO}
    datos["tipo_calculo"] = prueba.tipo_calculo
    limites = {lv.tipo_vertido: lv for lv in prueba.limites_vertido.all()}
    for vertido in VERTIDOS:
        fila = limites.get(vertido)
        for campo in ("limite_min", "limite_max", "norma"):
            datos[f"{vertido}_{campo}"] = getattr(fila, campo) if fila else ""
    return datos


# --- Validación ------------------------------------------------------------------------------


def es_limite_valido(texto):
    texto = (texto or "").strip()
    return not texto or texto.casefold() in TEXTOS_AUSENTE or bool(NUMERO.fullmatch(texto))


def numero(texto):
    from decimal import Decimal

    texto = (texto or "").strip()
    return Decimal(texto.replace(",", ".")) if NUMERO.fullmatch(texto) else None


def _validar_limites(datos, errores, prefijo=""):
    minimo, maximo = f"{prefijo}limite_min", f"{prefijo}limite_max"
    for campo in (minimo, maximo):
        if not es_limite_valido(datos[campo]):
            errores[campo] = MENSAJE_LIMITE
    if minimo not in errores and maximo not in errores:
        a, b = numero(datos[minimo]), numero(datos[maximo])
        if a is not None and b is not None and a > b:
            errores[minimo] = MENSAJE_RANGO


def normalizar(datos):
    if not isinstance(datos, dict):
        raise DatosInvalidos({"__all__": "La solicitud no es válida."})
    limpios = {}
    for campo in CAMPOS_TEXTO + tuple(
        f"{v}_{c}" for v in VERTIDOS for c in ("limite_min", "limite_max", "norma")
    ):
        valor = datos.get(campo, "")
        if not isinstance(valor, str):
            raise DatosInvalidos({"__all__": "La solicitud no es válida."})
        limpios[campo] = valor.strip()
    limpios["tipo_calculo"] = datos.get("tipo_calculo", "")
    if limpios["tipo_calculo"] == TipoCalculo.DIRECTO:
        limpios["formula"] = ""  # pasar a Directo descarta la fórmula
    return limpios


def validar_datos(datos, prueba=None):
    """Datos normalizados de una prueba o `DatosInvalidos` con los errores por campo.

    `prueba` es la que se edita (None al crear): no cuenta para el código repetido.
    """
    datos = normalizar(datos)
    errores = {}
    for campo in ("codigo", "nombre"):
        if not datos[campo]:
            errores[campo] = "Este campo es obligatorio."
    for campo, maximo in MAXIMOS.items():
        if len(datos[campo]) > maximo and campo not in errores:
            errores[campo] = f"Usá hasta {maximo} caracteres."
    for vertido in VERTIDOS:
        if len(datos[f"{vertido}_norma"]) > 150:
            errores[f"{vertido}_norma"] = "Usá hasta 150 caracteres."
    if datos["tipo_calculo"] not in TipoCalculo.values:
        errores["tipo_calculo"] = "Elegí un tipo de cálculo."
    elif datos["tipo_calculo"] == TipoCalculo.FORMULA and not datos["formula"]:
        errores["formula"] = "Una prueba de tipo Fórmula necesita una fórmula."
    if datos["codigo"] and "codigo" not in errores:
        repetido = Prueba.objects.filter(codigo__iexact=datos["codigo"])
        if prueba is not None:
            repetido = repetido.exclude(pk=prueba.pk)
        if repetido.exists():
            errores["codigo"] = "Ya existe una prueba con ese código."
    if datos["formula"] and "formula" not in errores:
        _validar_formula(datos, errores)
    _validar_limites(datos, errores)
    for vertido in VERTIDOS:
        _validar_limites(datos, errores, f"{vertido}_")
    if errores:
        raise DatosInvalidos(errores)
    return datos


def _validar_formula(datos, errores):
    try:
        validar_formula(datos["formula"])
    except FormulaInvalida as exc:
        errores["formula"] = " ".join(exc.messages)
        return
    referencias = referencias_formula(datos["formula"])
    if datos["codigo"] in referencias:
        errores["formula"] = "La prueba no puede referenciarse a sí misma."
        return
    existentes = set(Prueba.objects.filter(codigo__in=referencias).values_list("codigo", flat=True))
    if faltantes := sorted(referencias - existentes):
        errores["formula"] = (
            f"La fórmula referencia «{faltantes[0]}», que no existe en el catálogo."
        )


# --- Escritura -------------------------------------------------------------------------------


def autorizar(usuario):
    from usuarios.permisos_administracion import autorizar_administracion

    try:
        return autorizar_administracion(usuario)
    except Exception as exc:
        raise NoAutorizado("Se requiere ser Administrador para gestionar el catálogo.") from exc


def _guardar_limites_vertido(prueba, datos):
    for vertido in VERTIDOS:
        valores = {c: datos[f"{vertido}_{c}"] for c in ("limite_min", "limite_max", "norma")}
        if any(valores.values()):
            LimiteVertido.objects.update_or_create(
                prueba=prueba, tipo_vertido=vertido, defaults=valores
            )
        else:
            LimiteVertido.objects.filter(prueba=prueba, tipo_vertido=vertido).delete()


def _asignar(prueba, datos, campos):
    for campo in campos:
        setattr(prueba, campo, datos[campo])
    prueba.es_calculada = bool(referencias_formula(prueba.formula))


def _marcar(prueba, usuario):
    prueba.modificada_por = usuario
    prueba.fecha_modificacion = timezone.now()
    prueba.version += 1


def _subir_version_tipos(prueba):
    from estudios.models import TipoEstudio

    for tipo in TipoEstudio.objects.select_for_update().filter(pruebas=prueba).order_by("pk"):
        tipo.version += 1
        tipo.save(update_fields=["version"])


def _reemplazar_en_formula(formula, viejo, nuevo):
    patron = re.compile(r"\{\s*" + re.escape(viejo) + r"\s*\}")
    return patron.sub("{" + nuevo + "}", formula)


def _reemplazar(prueba, reemplazo_id, usuario):
    """Cascada del reemplazo (research R11): fórmulas de las dependientes y tipos de estudio."""
    from estudios.models import TipoEstudio, TipoEstudioPrueba

    candidatas = {p.pk: p for p in candidatas_reemplazo(prueba)}
    try:
        nueva = candidatas[int(reemplazo_id)]
    except (KeyError, TypeError, ValueError) as exc:
        raise DatosInvalidos({"reemplazo": MENSAJE_REEMPLAZO}) from exc
    nueva = Prueba.objects.select_for_update().get(pk=nueva.pk)
    if not nueva.activa or nueva.unidad != prueba.unidad:
        raise DatosInvalidos({"reemplazo": MENSAJE_REEMPLAZO})
    prueba.reemplazada_por = nueva
    for dependiente in (
        Prueba.objects.select_for_update()
        .filter(pk__in=[p.pk for p in dependientes(prueba)])
        .order_by("pk")
    ):
        dependiente.formula = _reemplazar_en_formula(
            dependiente.formula, prueba.codigo, nueva.codigo
        )
        dependiente.es_calculada = bool(referencias_formula(dependiente.formula))
        dependiente.full_clean()
        _marcar(dependiente, usuario)
        dependiente.save()
    for tipo in TipoEstudio.objects.select_for_update().filter(pruebas=prueba).order_by("pk"):
        TipoEstudioPrueba.objects.filter(tipo=tipo, prueba=prueba).delete()
        TipoEstudioPrueba.objects.get_or_create(tipo=tipo, prueba=nueva)
        tipo.version += 1
        tipo.save(update_fields=["version"])
    return nueva


def gestionar_prueba(
    *, usuario, operacion, prueba_id=None, version_esperada=None, datos=None, reemplazo_id=None
):
    """Única escritura del catálogo desde la app. Devuelve un `Resultado`."""
    usuario = autorizar(usuario)
    if operacion not in OPERACIONES:
        raise DatosInvalidos({"__all__": "La operación no es válida."})
    with transaction.atomic():
        if operacion == "crear":
            return _crear(usuario, datos)
        prueba = Prueba.objects.select_for_update().filter(pk=prueba_id).first()
        if prueba is None:
            raise PruebaNoExiste("La prueba no existe.")
        if version_esperada != prueba.version:
            raise VersionDesactualizada()
        if operacion == "editar":
            return _editar(prueba, usuario, datos)
        if operacion == "eliminar":
            return _eliminar(prueba)
        if operacion == "reemplazar":
            return _crear_y_reemplazar(prueba, usuario, datos)
        destino = operacion == "reactivar"
        if prueba.activa == destino:
            return Resultado("sin_cambios", prueba.pk)
        nueva = None
        if not destino and reemplazo_id not in (None, ""):
            nueva = _reemplazar(prueba, reemplazo_id, usuario)
        else:
            _subir_version_tipos(prueba)
        prueba.activa = destino
        _marcar(prueba, usuario)
        prueba.save()
        estado = "reactivada" if destino else ("reemplazada" if nueva else "desactivada")
        return Resultado(estado, prueba.pk, nueva.codigo if nueva else "")


def _crear(usuario, datos):
    datos = validar_datos(datos)
    prueba = Prueba(creada_por=usuario, fecha_creacion=timezone.now())
    _asignar(prueba, datos, CAMPOS_TEXTO + ("tipo_calculo",))
    _validar_modelo(prueba)
    prueba.save()
    _guardar_limites_vertido(prueba, datos)
    return Resultado("creada", prueba.pk)


def _crear_y_reemplazar(prueba, usuario, datos):
    """Crea la prueba nueva, desactiva `prueba` y la reemplaza en cascada, todo junto."""
    if not prueba.activa or prueba.reemplazada_por_id:
        raise DatosInvalidos({"__all__": "Solo se puede reemplazar una prueba activa."})
    datos = validar_datos(datos)
    if datos["unidad"] != prueba.unidad:
        raise DatosInvalidos({"unidad": MENSAJE_UNIDAD_REEMPLAZO})
    prohibidas = {prueba.codigo} | {p.codigo for p in dependientes_transitivas(prueba)}
    if referencias_formula(datos["formula"]) & prohibidas:
        raise DatosInvalidos({"formula": MENSAJE_FORMULA_REEMPLAZO})
    creada = _crear(usuario, datos)
    nueva = _reemplazar(prueba, creada.prueba_id, usuario)
    prueba.activa = False
    _marcar(prueba, usuario)
    prueba.save()
    return Resultado("creada_reemplazo", nueva.pk, nueva.codigo)


def _editar(prueba, usuario, datos):
    datos = validar_datos(datos, prueba)
    if prueba.esta_en_uso():
        if any(datos[c] != getattr(prueba, c) for c in CAMPOS_METODO):
            raise PruebaEnUso()
    elif datos["codigo"] != prueba.codigo and (usan := dependientes(prueba)):
        raise PruebaReferenciada([p.codigo for p in usan])
    antes = datos_de(prueba)
    if all(antes[c] == datos[c] for c in antes):
        return Resultado("sin_cambios", prueba.pk)
    _asignar(prueba, datos, CAMPOS_TEXTO + ("tipo_calculo",))
    _validar_modelo(prueba)
    _marcar(prueba, usuario)
    prueba.save()
    _guardar_limites_vertido(prueba, datos)
    return Resultado("actualizada", prueba.pk)


def _eliminar(prueba):
    if prueba.esta_en_uso():
        raise PruebaEnUso(
            "Esta prueba ya se usa en tipos de estudio o estudios: no se puede eliminar, solo "
            "desactivar."
        )
    if usan := dependientes(prueba):
        raise PruebaReferenciada([p.codigo for p in usan])
    if prueba.reemplaza_a.exists():
        raise PruebaEnUso("Otra prueba fue reemplazada por esta: no se puede eliminar.")
    pk = prueba.pk
    prueba.delete()
    return Resultado("eliminada", pk)


def _validar_modelo(prueba):
    try:
        prueba.full_clean(validate_unique=False)
    except ValidationError as exc:
        raise DatosInvalidos(
            {campo: " ".join(mensajes) for campo, mensajes in exc.message_dict.items()}
        ) from exc
