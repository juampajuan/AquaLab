from django.urls import path

from . import views, views_conclusiones

app_name = "informes"
urlpatterns = [
    path(
        "estudios/<int:pk>/conclusion/guardar/",
        views_conclusiones.guardar,
        name="conclusion_guardar",
    ),
    path(
        "estudios/<int:pk>/conclusion/aprobar/",
        views_conclusiones.aprobar,
        name="conclusion_aprobar",
    ),
    path(
        "estudios/<int:pk>/conclusion/proponer/",
        views_conclusiones.proponer,
        name="conclusion_proponer",
    ),
    path("", views.listar, name="listar"),
    path("emitidos/", views.emitidos, name="emitidos"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("mi-firma/", views.mi_firma, name="mi_firma"),
    path("estudios/<int:pk>/", views.control, name="control"),
    path("estudios/<int:pk>/vista-previa/", views.vista_previa, name="vista_previa"),
    path("estudios/<int:pk>/generar/", views.generar, name="generar"),
    path("estudios/<int:pk>/informe/", views.ver, name="ver"),
    path("estudios/<int:pk>/informe/enviar/", views.enviar, name="enviar"),
    path("estudios/<int:pk>/informe/pdf/", views.pdf_informe, name="pdf"),
    path("estudios/<int:pk>/informe/imprimir/", views.imprimir, name="imprimir"),
]
