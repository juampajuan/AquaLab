from django.contrib import admin
from django.urls import include, path

from usuarios.views import CerrarSesionView

from . import views

urlpatterns = [
    path("admin/logout/", CerrarSesionView.as_view()),
    path("admin/", admin.site.urls),
    path("usuarios/", include("usuarios.urls")),
    path("clientes/", include("clientes.urls")),
    path("muestras/", include("muestras.urls")),
    path("estudios/", include("estudios.urls")),
    path("informes/", include("informes.urls")),
    path("", views.inicio, name="inicio"),
]
