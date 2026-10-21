from django.urls import path

from . import views

app_name = "usuarios"

urlpatterns = [
    path("login/", views.InicioSesionView.as_view(), name="login"),
    path("logout/", views.CerrarSesionView.as_view(), name="logout"),
    path("sesion/", views.sesion, name="sesion"),
    path("registro/", views.registro, name="registro"),
    path("registro/confirmar/", views.registro_confirmar, name="registro_confirmar"),
    path("registro/recibido/", views.registro_recibido, name="registro_recibido"),
]
