from django.urls import path

from . import views_administracion as views

app_name = "administracion"
urlpatterns = [
    path("", views.inicio, name="inicio"),
    path("pruebas/", views.pruebas, name="pruebas"),
    path("solicitudes/", views.solicitudes, name="solicitudes"),
    path("solicitudes/<int:pk>/aprobar/", views.aprobar, name="aprobar"),
    path("solicitudes/<int:pk>/rechazar/", views.rechazar, name="rechazar"),
    path("usuarios/", views.usuarios, name="usuarios"),
    path("usuarios/<int:pk>/rol/", views.cambiar_rol, name="cambiar_rol"),
    path("usuarios/<int:pk>/desactivar/", views.desactivar, name="desactivar"),
    path("usuarios/<int:pk>/reactivar/", views.reactivar, name="reactivar"),
]
