from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

from usuarios.views import CerrarSesionView

urlpatterns = [
    path("admin/logout/", CerrarSesionView.as_view()),
    path("admin/", admin.site.urls),
    path("usuarios/", include("usuarios.urls")),
    path("clientes/", include("clientes.urls")),
    path("muestras/", include("muestras.urls")),
    path("", TemplateView.as_view(template_name="inicio.html"), name="inicio"),
]
