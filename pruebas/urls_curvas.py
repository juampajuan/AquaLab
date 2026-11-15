"""Consulta de curvas de calibración para cualquier empleado con sesión (US 6.6)."""

from django.urls import path

from . import views_curvas

app_name = "curvas"
urlpatterns = [
    path("<int:pk>/curvas/", views_curvas.listar, name="listar"),
    path("curvas/<int:pk>/", views_curvas.detalle, name="detalle"),
]
