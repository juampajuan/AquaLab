from django.urls import path

from . import views

app_name = "informes"
urlpatterns = [
    path("", views.listar, name="listar"),
    path("estudios/<int:pk>/", views.control, name="control"),
]
