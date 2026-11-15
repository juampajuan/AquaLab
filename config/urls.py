from django.contrib import admin
from django.urls import include, path

from usuarios.views import CerrarSesionView

from . import views

urlpatterns = [
    path("admin/logout/", CerrarSesionView.as_view()),
    path("admin/", admin.site.urls),
    path("usuarios/", include("usuarios.urls")),
    path("administracion/", include("usuarios.urls_administracion")),
    path("administracion/pruebas/", include("pruebas.urls")),  # SCRUM-73
    path("pruebas/", include("pruebas.urls_curvas")),  # US 6.6
    path("clientes/", include("clientes.urls")),
    path("muestras/", include("muestras.urls")),
    path("estudios/", include("estudios.urls")),
    path("informes/", include("informes.urls")),
    path("asistente/", include("asistente.urls")),  # US 10.1
    path("", views.inicio, name="inicio"),
]
