from django.urls import path

from . import views

app_name = "informes"
urlpatterns = [
    path("", views.listar, name="listar"),
    path("emitidos/", views.emitidos, name="emitidos"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("mi-firma/", views.mi_firma, name="mi_firma"),
    path("estudios/<int:pk>/", views.control, name="control"),
    path("estudios/<int:pk>/vista-previa/", views.vista_previa, name="vista_previa"),
    path("estudios/<int:pk>/generar/", views.generar, name="generar"),
    path("estudios/<int:pk>/informe/", views.ver, name="ver"),
    path("estudios/<int:pk>/informe/pdf/", views.pdf_informe, name="pdf"),
    path("estudios/<int:pk>/informe/imprimir/", views.imprimir, name="imprimir"),
]
