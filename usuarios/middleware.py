from django.utils.cache import add_never_cache_headers


class NoAlmacenarSesionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        respuesta = self.get_response(request)
        ruta = getattr(request, "resolver_match", None)
        nombre = ruta.view_name if ruta else ""
        if nombre in {"usuarios:login", "usuarios:sesion"} or (
            request.user.is_authenticated
            and respuesta.get("Content-Type", "").startswith("text/html")
        ):
            add_never_cache_headers(respuesta)
        return respuesta
