from django.urls import path

from . import views

app_name = "estudios"
urlpatterns = [
    path("crear/", views.crear, name="crear"),
    path("crear/confirmar/", views.confirmar, name="confirmar"),
]
