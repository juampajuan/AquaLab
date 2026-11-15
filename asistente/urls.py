from django.urls import path

from . import views

app_name = "asistente"
urlpatterns = [
    path("preguntar/", views.preguntar, name="preguntar"),
]
