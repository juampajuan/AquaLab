from django.urls import path

from . import views

app_name = "estudios"
urlpatterns = [
    path("buscar/", views.buscar, name="buscar"),
    path("crear/", views.crear, name="crear"),
    path("crear/confirmar/", views.confirmar, name="confirmar"),
    path("<int:pk>/", views.detalle, name="detalle"),
]
