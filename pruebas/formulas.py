"""Evaluación de las fórmulas del catálogo con Decimal exacto.

Gramática (la que usa el catálogo; cualquier otra cosa se rechaza):

    expresion := termino (("+" | "-") termino)*
    termino   := factor (("*" | "/") factor)*
    factor    := ("+" | "-") factor | numero | "x" | "{" CODIGO "}"
               | "sqrt" "(" expresion ")" | "(" expresion ")"

`x` es el valor medido de la prueba y `{CODIGO}` el resultado de otra prueba del estudio. Nunca
se usa eval, ast ni float: los números se construyen con Decimal desde el texto.
"""

import re
from decimal import Decimal, DivisionByZero, InvalidOperation, localcontext

from django.core.exceptions import ValidationError

PRECISION = 34
TOKEN = re.compile(r"\s*(\d+(?:\.\d+)?|x|\{[^{}]+\}|sqrt|[-+*/()])")


class FormulaInvalida(ValidationError):
    pass


class CalculoImposible(Exception):
    def __init__(self, motivo):
        super().__init__(motivo)
        self.motivo = motivo


def tokens(texto):
    resultado, posicion, texto = [], 0, (texto or "").rstrip()
    while posicion < len(texto):
        coincidencia = TOKEN.match(texto, posicion)
        if coincidencia is None:
            raise FormulaInvalida(
                f"La fórmula no es válida: no se reconoce «{texto[posicion:].strip()}»."
            )
        resultado.append(coincidencia.group(1))
        posicion = coincidencia.end()
    return resultado


class Analizador:
    """Arma un árbol de tuplas: ("num", Decimal), ("x",), ("ref", codigo), ("neg", a),
    ("sqrt", a) u (operador, a, b)."""

    def __init__(self, texto):
        self.tokens = tokens(texto)
        self.posicion = 0

    def actual(self):
        return self.tokens[self.posicion] if self.posicion < len(self.tokens) else None

    def consumir(self, esperado=None):
        token = self.actual()
        if token is None or (esperado is not None and token != esperado):
            encontrado = f"«{token}»" if token else "el final"
            falta = f"«{esperado}»" if esperado else "un valor"
            raise FormulaInvalida(
                f"La fórmula no es válida: se esperaba {falta} y hay {encontrado}."
            )
        self.posicion += 1
        return token

    def arbol(self):
        arbol = self.expresion()
        if self.actual() is not None:
            raise FormulaInvalida(f"La fórmula no es válida: sobra «{self.actual()}».")
        return arbol

    def expresion(self):
        arbol = self.termino()
        while self.actual() in ("+", "-"):
            arbol = (self.consumir(), arbol, self.termino())
        return arbol

    def termino(self):
        arbol = self.factor()
        while self.actual() in ("*", "/"):
            arbol = (self.consumir(), arbol, self.factor())
        return arbol

    def factor(self):
        token = self.consumir()
        if token in ("+", "-"):
            operando = self.factor()
            return ("neg", operando) if token == "-" else operando
        if token == "x":
            return ("x",)
        if token == "sqrt":
            self.consumir("(")
            operando = self.expresion()
            self.consumir(")")
            return ("sqrt", operando)
        if token == "(":
            arbol = self.expresion()
            self.consumir(")")
            return arbol
        if token.startswith("{"):
            return ("ref", token[1:-1].strip())
        if token[0].isdigit():
            return ("num", Decimal(token))
        raise FormulaInvalida(f"La fórmula no es válida: «{token}» no puede ir ahí.")


def validar_formula(texto):
    if not (texto or "").strip():
        raise FormulaInvalida("La fórmula no es válida: está vacía.")
    Analizador(texto).arbol()


def evaluar_formula(texto, x, resultados):
    """Valor de la fórmula con `x` (Decimal o None) y los resultados `{codigo: Decimal}`."""
    arbol = Analizador(texto).arbol()
    with localcontext() as contexto:
        contexto.prec = PRECISION
        try:
            return evaluar(arbol, x, resultados)
        except DivisionByZero as exc:
            raise CalculoImposible("división por cero") from exc
        except InvalidOperation as exc:
            raise CalculoImposible("operación inválida") from exc


def evaluar(nodo, x, resultados):
    tipo = nodo[0]
    if tipo == "num":
        return nodo[1]
    if tipo == "x":
        if x is None:
            raise CalculoImposible("la fórmula usa el valor medido y la prueba no tiene medición")
        return x
    if tipo == "ref":
        if nodo[1] not in resultados:
            raise CalculoImposible(f"falta el resultado de {nodo[1]}")
        return resultados[nodo[1]]
    if tipo == "neg":
        return -evaluar(nodo[1], x, resultados)
    if tipo == "sqrt":
        valor = evaluar(nodo[1], x, resultados)
        if valor < 0:
            raise CalculoImposible("raíz cuadrada de un número negativo")
        return valor.sqrt()
    a, b = evaluar(nodo[1], x, resultados), evaluar(nodo[2], x, resultados)
    if tipo == "+":
        return a + b
    if tipo == "-":
        return a - b
    if tipo == "*":
        return a * b
    if b == 0:
        raise CalculoImposible("división por cero")
    return a / b
