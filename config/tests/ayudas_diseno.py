"""Ayudas compartidas por los tests de estructura de la interfaz (US2 y US3 de SCRUM-67)."""

import re


def etiqueta_de(html, campo):
    """Contenido de la etiqueta (label o legend) del campo, marcada con data-campo."""
    encontrado = re.search(rf'<(label|legend)[^>]*data-campo="{campo}"[^>]*>(.*?)</\1>', html, re.S)
    assert encontrado, f"no se encontró la etiqueta de {campo}"
    return encontrado.group(2)


def es_obligatorio(html, campo):
    return "data-obligatorio" in etiqueta_de(html, campo)


def tiene_componentes_de_confirmacion(html):
    return 'data-componente="resumen"' in html and 'data-componente="acciones-confirmacion"' in html


def radios_de(html, nombre):
    """Valores de los radios del campo, con True si están marcados."""
    return {
        valor: "checked" in resto
        for valor, resto in re.findall(
            rf'<input type="radio" name="{nombre}" value="([^"]*)"([^>]*)>', html
        )
    }
