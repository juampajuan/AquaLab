from django.urls import path

from . import views

app_name = "informes"
urlpatterns = [
    path("", views.listar, name="listar"),
    path("estudios/<int:pk>/", views.control, name="control"),
    path("estudios/<int:pk>/vista-previa/", views.vista_previa, name="vista_previa"),
    path("estudios/<int:pk>/generar/", views.generar, name="generar"),
    path("estudios/<int:pk>/informe/", views.ver, name="ver"),
]
