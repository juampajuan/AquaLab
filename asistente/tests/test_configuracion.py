"""Configuración del asistente por variables de entorno (US 10.1, FR-015)."""

from asistente import configuracion


def test_por_defecto_groq(settings):
    """Con solo la clave se usa Groq con el modelo por defecto (US4 Esc. 4)."""
    settings.ASISTENTE = {"clave": "clave-test"}
    config = configuracion.actual()
    assert config.url == "https://api.groq.com/openai/v1/chat/completions"
    assert config.modelo == "openai/gpt-oss-120b"
    assert config.habilitado


def test_por_defecto_con_valores_vacios(settings):
    settings.ASISTENTE = {"clave": "clave-test", "url": "", "modelo": ""}
    config = configuracion.actual()
    assert config.url == configuracion.URL_GROQ
    assert config.modelo == configuracion.MODELO_POR_DEFECTO


def test_otra_url_y_modelo(settings):
    """Con otra dirección o modelo en la configuración, se usan esos (US4 Esc. 4)."""
    settings.ASISTENTE = {
        "clave": "clave-test",
        "url": "https://otro.test/v1/chat/completions",
        "modelo": "otro-modelo",
    }
    config = configuracion.actual()
    assert config.url == "https://otro.test/v1/chat/completions"
    assert config.modelo == "otro-modelo"


def test_sin_clave_deshabilitado(settings):
    settings.ASISTENTE = {"clave": ""}
    assert not configuracion.actual().habilitado


def test_topes(settings):
    settings.ASISTENTE = {"clave": "clave-test"}
    config = configuracion.actual()
    assert (config.timeout, config.presupuesto) == (15, 20)
    assert (config.max_vueltas, config.max_herramientas) == (6, 8)
