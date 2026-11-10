from django.urls import path

from . import views

app_name = "catalogo"
urlpatterns = [
    path("nueva/", views.nueva, name="nueva"),
    path("confirmar/", views.confirmar, name="confirmar"),
    path("<int:pk>/", views.ficha, name="ficha"),
    path("<int:pk>/editar/", views.editar, name="editar"),
    path("<int:pk>/desactivar/", views.desactivar, name="desactivar"),
    path("<int:pk>/reactivar/", views.reactivar, name="reactivar"),
    path("<int:pk>/eliminar/", views.eliminar, name="eliminar"),
]
