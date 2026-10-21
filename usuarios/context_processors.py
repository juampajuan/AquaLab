from django.utils.crypto import salted_hmac


def huella_para(request):
    if not request.user.is_authenticated or not request.session.session_key:
        return ""
    contexto = f"{request.user.pk}:{request.session.session_key}"
    return salted_hmac("aqualab.revalidacion.sesion", contexto, algorithm="sha256").hexdigest()


def contexto_sesion(request):
    return {"huella_sesion": huella_para(request)}
