from django.urls import path

from . import views

app_name = "clientes"

urlpatterns = [
    path("registrar/", views.registrar, name="registrar"),
    path("registrar/confirmar/", views.registrar_confirmar, name="registrar_confirmar"),
    path("<int:pk>/", views.detalle, name="detalle"),
]
