from django.urls import path

from . import views, views_curvas

app_name = "catalogo"
urlpatterns = [
    path("nueva/", views.nueva, name="nueva"),
    path("confirmar/", views.confirmar, name="confirmar"),
    path("<int:pk>/", views.ficha, name="ficha"),
    path("<int:pk>/editar/", views.editar, name="editar"),
    path("<int:pk>/desactivar/", views.desactivar, name="desactivar"),
    path("<int:pk>/reemplazar/", views.reemplazar, name="reemplazar"),
    path("<int:pk>/reactivar/", views.reactivar, name="reactivar"),
    path("<int:pk>/eliminar/", views.eliminar, name="eliminar"),
    # US 6.6 – curvas de calibración
    path("<int:pk>/curvas/nueva/", views_curvas.nueva_curva, name="nueva_curva"),
    path("<int:pk>/curvas/confirmar/", views_curvas.confirmar_curva, name="confirmar_curva"),
    path("curvas/plantilla.csv", views_curvas.plantilla_curva, name="plantilla_curva"),
    path("curvas/<int:pk>/borrar/", views_curvas.borrar_curva, name="borrar_curva"),
]
