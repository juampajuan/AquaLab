"""Fixtures comunes a toda la suite."""

import pytest


@pytest.fixture(autouse=True)
def asistente_sin_clave(settings):
    """Los tests no dependen del `.env` de quien los corre: sin clave, el asistente queda
    deshabilitado como en el CI. Los tests del asistente lo configuran con `config_asistente`."""
    settings.ASISTENTE = {**settings.ASISTENTE, "clave": ""}
