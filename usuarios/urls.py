from django.urls import path

from . import views

app_name = "usuarios"

urlpatterns = [
    path("registro/", views.registro, name="registro"),
    path("registro/confirmar/", views.registro_confirmar, name="registro_confirmar"),
    path("registro/recibido/", views.registro_recibido, name="registro_recibido"),
]
