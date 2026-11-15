from . import configuracion


def asistente(request):
    """Si el asistente está configurado (US 10.1): sin clave, el botón aparece deshabilitado."""
    return {"asistente_habilitado": configuracion.actual().habilitado}
