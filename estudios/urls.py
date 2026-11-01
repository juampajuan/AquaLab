from django.urls import path

from . import views, views_tipos

app_name = "estudios"
urlpatterns = [
    path("tipos/<int:pk>/desactivar/", views_tipos.tipos_desactivar, name="tipos_desactivar"),
    path("tipos/<int:pk>/reactivar/", views_tipos.tipos_reactivar, name="tipos_reactivar"),
    path("tipos/<int:pk>/eliminar/", views_tipos.tipos_eliminar, name="tipos_eliminar"),
    path("tipos/", views_tipos.tipos_listar, name="tipos_listar"),
    path("tipos/crear/", views_tipos.tipos_crear, name="tipos_crear"),
    path("tipos/<int:pk>/editar/", views_tipos.tipos_editar, name="tipos_editar"),
    path("tipos/confirmar/", views_tipos.tipos_confirmar, name="tipos_confirmar"),
    path("buscar/", views.buscar, name="buscar"),
    path("crear/", views.crear, name="crear"),
    path("crear/confirmar/", views.confirmar, name="confirmar"),
    path("<int:pk>/", views.detalle, name="detalle"),
    path("<int:pk>/pruebas/agregar/", views.agregar_prueba, name="agregar_prueba"),
    path(
        "<int:pk>/pruebas/<int:asignacion_pk>/quitar/",
        views.quitar_prueba,
        name="quitar_prueba",
    ),
    path("<int:pk>/mediciones/cargar/", views.cargar_mediciones, name="cargar_mediciones"),
    path("<int:pk>/mediciones/corregir/", views.corregir_mediciones, name="corregir_mediciones"),
]
